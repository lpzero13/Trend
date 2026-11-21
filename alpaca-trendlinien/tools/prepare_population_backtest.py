"""Freeze an offline population replication without changing the entry/exit engine.

Use an explicit previously selected dataset map, cached universe rosters and the
baseline's common outcome boundary. Never import data or mutate existing studies.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datasets import path_for
from event_case_study import checked, load_block, binding
from exit_followup import checked as checked_follow, load_followup
from fan_geometry import stable_id
from settings import data_dir
from strategy_screen import read, write
from strategy_run_lock import study_lock


def prepare(root, source, baseline):
    root, baseline = Path(root), Path(baseline)
    if (root/'plan.json').exists():
        raise ValueError('Use a new output directory; existing plans are immutable')
    old = checked(read(baseline/'plan.json'))
    proof = read(baseline/'verification.json')
    assert proof['planId'] == old['id'] and proof['passed']
    chosen = read(source)
    assert chosen['id'] == stable_id({k:v for k,v in chosen.items() if k != 'id'})
    assert chosen['windows'] == old['windows']
    assert set(chosen['symbols']) == set(chosen['datasets'])
    members = {}
    dbfile = (data_dir()/'research'/'jobs.sqlite3').resolve()
    with sqlite3.connect(dbfile.as_uri()+'?mode=ro', uri=True) as db:
        for key in ('dow30','nasdaq100','sp500'):
            row = db.execute('select value from settings where key=?',('universe:v1:'+key,)).fetchone()
            if row is None: raise ValueError('Missing cached roster: '+key)
            members[key] = json.loads(row[0])
    union = {m['symbol'] for u in members.values() for m in u['members']}
    excluded = {v['symbol'] for v in chosen['excluded']}
    assert union == set(chosen['symbols']) | excluded
    boundaries = {}
    for symbol, identity in chosen['datasets'].items():
        m = read(path_for(identity))
        assert m['material']['symbol'] == symbol
        assert m['material']['feed'] == 'sip' and m['material']['adjustment'] == 'split'
        end = m['sources']['5m']['requestedEnd']
        assert int(datetime.fromisoformat(end.replace('Z','+00:00')).timestamp()) >= old['outcomeCutoff']
        boundaries[symbol] = end
    controls = sorted(set(old['symbols']) & set(chosen['symbols']))
    assert all(old['datasets'][s] == chosen['datasets'][s] for s in controls)
    for symbol in set(old['symbols'])-set(controls):
        assert not any(load_block(baseline,old,symbol)['eligibility'].values())
    p = deepcopy(old)
    p.pop('id')
    p.update(createdAt=datetime.now(timezone.utc).isoformat(), sourcePlanId=chosen['id'],
             symbols=sorted(chosen['symbols']), datasets=chosen['datasets'],
             populationReplication={'baselinePlanId':old['id'],
                'universeKeys':list(members),'dataRoot':str(data_dir().resolve()),
                'cutoffRule':'Keep baseline outcome cutoff; later imported bars are excluded',
                'universeMembership':'Frozen current ETF holdings, not historical index constituents'})
    assert p['engine'] == binding()
    p['id'] = stable_id(p)
    for name in p['engine']:
        dest=root/'engine'/name;dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes((Path(__file__).resolve().parents[1]/name).read_bytes())
    write(root/'plan.json',p)
    receipt={'planId':p['id'],'sourcePlanId':chosen['id'],'baselinePlanId':old['id'],
        'catalogSymbols':len(union),'eligibleSymbols':len(p['symbols']),
        'excluded':chosen['excluded'],'universes':members,'requestedEnds':boundaries,
        'outcomeCutoff':p['outcomeCutoff'],'unchangedControls':controls,
        'newSymbols':len(set(p['symbols'])-set(controls)),'selectionUsesOutcomes':False}
    for symbol in controls:
        original=load_block(baseline,old,symbol)
        b=deepcopy(original);b.pop('checksum');b['planId']=p['id']
        b['reusedFrom']={'planId':old['id'],'checksum':original['checksum']}
        b['checksum']=stable_id(b);write(root/'stocks'/(symbol+'.json.gz'),b)
    write(root/'population.json',receipt)
    return {'planId':p['id'],'stocks':len(p['symbols']),'reused':len(controls),'new':receipt['newSymbols']}


def reuse_followup(root, baseline):
    root, baseline = Path(root), Path(baseline)
    p=checked_follow(read(root/'plan.json'));old=checked_follow(read(baseline/'plan.json'))
    old_proof=read(baseline/'verification.json')
    assert old_proof['passed'] and old_proof['planId']==old['id']
    source=checked(read(Path(p['sourceRoot'])/'plan.json'))
    prior=checked(read(Path(old['sourceRoot'])/'plan.json'))
    for field in ('engine','policies','cutoff','windows','contracts'):
        assert p[field]==old[field], field
    controls=read(Path(p['sourceRoot'])/'population.json')['unchangedControls']
    for s in controls:
        old_base=load_block(old['sourceRoot'],prior,s);new_base=load_block(p['sourceRoot'],source,s)
        assert old['datasets'][s]==p['datasets'][s]
        for field in ('cases','timeline','eligibility','suppressed'):
            assert old_base[field]==new_base[field],(s,field)
        original=load_followup(baseline,old,s)
        assert original['sourceChecksum']==old_base['checksum']
        b=deepcopy(original);b.pop('checksum');b['planId']=p['id'];b['sourceChecksum']=new_base['checksum']
        b['reusedFrom']={'planId':old['id'],'checksum':original['checksum']}
        b['checksum']=stable_id(b);write(root/'stocks'/(s+'.json.gz'),b)
    write(root/'reuse-proof.json',{'planId':p['id'],'baselinePlanId':old['id'],'unchangedControls':controls})
    return {'reusedFollowups':len(controls)}


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('root');ap.add_argument('--source');ap.add_argument('--baseline',required=True)
    ap.add_argument('--reuse-followup',action='store_true');a=ap.parse_args()
    with study_lock(a.root):
        if a.reuse_followup:r=reuse_followup(a.root,a.baseline)
        else:
            if not a.source:ap.error('--source required')
            r=prepare(a.root,a.source,a.baseline)
    print(json.dumps(r),flush=True)
