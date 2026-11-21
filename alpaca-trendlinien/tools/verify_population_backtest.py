"""Parallel independent audits; rule/entry/path producers remain unchanged."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from strategy_screen import read,write
from tools.verify_event_cases import verify as verify_events
from tools.verify_exit_followup import verify as verify_followup


def shard(task):
    kind,root,symbols,samples,prefix=task
    return verify_events(root,samples,prefix,symbols) if kind=='events' else verify_followup(root,samples,symbols)


def verify(kind,root,workers=4,samples=2,prefix=False,output=None):
    if type(workers) is not int or not 1<=workers<=4 or samples<0:raise ValueError('Invalid audit settings')
    from event_case_study import checked as event_plan
    from exit_followup import checked as follow_plan
    p=(event_plan if kind=='events' else follow_plan)(read(Path(root)/'plan.json'))
    chunks=[p['symbols'][i::workers] for i in range(workers)]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        parts=list(pool.map(shard,[(kind,str(root),s,samples,prefix) for s in chunks if s]))
    symbols=[s for part in parts for s in part['verifiedSymbols']]
    assert sorted(symbols)==p['symbols'] and len(symbols)==len(set(symbols))
    assert all(v['planId']==p['id'] and v['passed'] for v in parts)
    names=('cases','fills','accountedPaths','independent5mReplays') if kind=='events' else ('cases','newPaths','independent5mReplays')
    r={'planId':p['id'],'passed':True,'symbols':len(symbols),'workers':workers,
       **{key:sum(part[key] for part in parts) for key in names},'sampleSeed':20261031,
       'verifierSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'shardVerifierSha256':sorted({part['verifierSha256'] for part in parts})}
    if kind=='events':
        ids=[v for part in parts for v in part['allCaseIds']]
        pairs=[tuple(v) for part in parts for v in part['episodeFamilies']]
        assert len(ids)==len(set(ids))==len(pairs)==len(set(pairs))==r['cases']
        r.update(futurePrefixChecked=prefix,samplesPerStock=samples,
                 replayedCaseIds=[s for part in parts for s in part['replayedCaseIds']])
    else:r['sampleIds']=[s for part in parts for s in part['sampleIds']]
    result=read(Path(root)/'results.json')
    assert result['planId']==r['planId'] and result['cases']==r['cases']
    write(Path(output) if output else Path(root)/'verification.json',r)
    return {k:v for k,v in r.items() if k not in ('sampleIds','replayedCaseIds')}


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('kind',choices=('events','followup'))
    ap.add_argument('root');ap.add_argument('--workers',type=int,default=4);ap.add_argument('--samples',type=int,default=2)
    ap.add_argument('--prefix',action='store_true');ap.add_argument('--output',help='Separate receipt for auditing an existing study');a=ap.parse_args()
    print(json.dumps(verify(a.kind,a.root,a.workers,a.samples,a.prefix,a.output)),flush=True)
