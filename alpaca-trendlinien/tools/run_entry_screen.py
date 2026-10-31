"""Outcome-blind signal screening, then descriptive frozen-path comparison."""
import argparse
from collections import Counter,defaultdict
from concurrent.futures import ProcessPoolExecutor,as_completed
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import statistics
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from datasets import read_dataset
from models import Bar,DataError
from entry_screen import Context,features,select,decisions,PROFILES,DEFAULT,VERSION
from event_case_study import checked as check_base,load_block
from exit_followup import checked as check_follow,load_followup,binding as follow_binding,summarize,terminal
from fan_geometry import stable_id
from strategy_screen import read,write
from strategy_run_lock import study_lock

POLICIES=('original_safety','fan_safety','qualified_fan','r2_fan')


def binding():
    base=Path(__file__).resolve().parents[1]
    return {**follow_binding(),**{n:hashlib.sha256((base/n).read_bytes()).hexdigest() for n in ('entry_screen.py','tools/run_entry_screen.py')}}


def checked(p):
    if p['id']!=stable_id({k:v for k,v in p.items() if k!='id'}) or p['engine']!=binding():
        raise DataError('Filterplan oder Producer geändert; neuer Studienordner erforderlich.',409)
    return p


def prepare(root,source):
    path=Path(root)/'plan.json'
    if path.exists():return checked(read(path))
    follow=check_follow(read(Path(source)/'plan.json'))
    p={'version':VERSION,'createdAt':datetime.now(timezone.utc).isoformat(),'sourceRoot':str(Path(source).resolve()),
       'sourcePlanId':follow['id'],'baseRoot':follow['sourceRoot'],'basePlanId':follow['sourcePlanId'],
       'symbols':follow['symbols'],'datasets':follow['datasets'],'windows':follow['windows'],'cutoff':follow['cutoff'],
       'profiles':PROFILES,'defaultProfile':DEFAULT,'policies':list(POLICIES),'engine':binding(),
       'contract':{'selection':'Only signal-close geometry, raw signalClose-to-initialStop distance, and last closed daily close/SMA200 from clean 200-session prefix. No fill, win/loss, MFE, path or future line filter.',
                   'unknown':'Required unknown excludes; reported separately, never filled using future data.',
                   'regime':'Last completed DAILY close > its SMA200, not unfinished signal-day daily close.',
                   'structure':'Contact spans >=14d action, >=20d Safety; positive geometric width ratio <=.5 since common anchor start. Not an earlier historically available drawing.',
                   'comparison':'All frozen entries/outcomes unchanged. No time exits or shared portfolio constraints. Per-profile same observable cases across four policies; open MTM separate from realized.',
                   'default':'balanced chosen before results; do not select historical winner or force 200–300 cases.'},
       'limitations':['All windows already known; post-hoc hypotheses and multiple comparisons, no independent validation',
                      'Universe survivorship, dependent episodes, informative gap censoring, different exposure durations',
                      'Outcome-blind features are not guaranteed profitable signals; no chart winner filter']}
    p['id']=stable_id(p)
    for n in p['engine']:
        dest=Path(root)/'engine'/n;dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes((Path(__file__).resolve().parents[1]/n).read_bytes())
    write(path,p);return p


def stock(task):
    root,p,symbol=task;checked(p);dest=Path(root)/'stocks'/(symbol+'.json.gz')
    if dest.exists():
        value=read(dest);assert value['planId']==p['id'] and value['checksum']==stable_id({k:v for k,v in value.items() if k!='checksum'})
        return {'symbol':symbol,'cached':True}
    base=check_base(read(Path(p['baseRoot'])/'plan.json'));b=load_block(p['baseRoot'],base,symbol)
    states={s['closedAt']:s['index'] for s in b['timeline']};rows=[]
    with patch('alpaca._request',side_effect=AssertionError('Offline screen')):
        if b['cases']:
            d=read_dataset(p['datasets'][symbol]);frames=d['material']['bars']
            ctx=Context([Bar(**v) for v in frames['4h']],[Bar(**v) for v in frames['1D']])
            for c in b['cases']:
                f=features(c['signal'],ctx)
                assert f['sourceIndex']==states[c['signal']['signalAt']],(symbol,c['id'],'Source index mismatch')
                rows.append({'caseId':c['id'],'features':f,'checks':decisions(f),
                             'selection':{name:select(f,name) for name in PROFILES}})
    value={'planId':p['id'],'symbol':symbol,'sourceChecksum':b['checksum'],'cases':rows}
    value['checksum']=stable_id(value);write(dest,value)
    return {'symbol':symbol,'cases':len(rows),'balanced':sum(v['selection'][DEFAULT]['accepted'] for v in rows)}


def evaluate(root,p):
    checked(p);base=check_base(read(Path(p['baseRoot'])/'plan.json'));follow=check_follow(read(Path(p['sourceRoot'])/'plan.json'))
    assert base['id']==p['basePlanId'] and follow['id']==p['sourcePlanId']
    cases=[];screen={}
    for symbol in p['symbols']:
        b=load_block(p['baseRoot'],base,symbol);f=load_followup(p['sourceRoot'],follow,symbol);x=read(Path(root)/'stocks'/(symbol+'.json.gz'))
        assert x['planId']==p['id'] and x['sourceChecksum']==f['sourceChecksum']==b['checksum']
        assert x['checksum']==stable_id({k:v for k,v in x.items() if k!='checksum'})
        assert [c['id'] for c in b['cases']]==[v['caseId'] for v in x['cases']]==f['caseIds']
        screen.update({v['caseId']:v for v in x['cases']})
        cases.extend({**c,'paths':{**c['paths'],**f['newPaths'][c['id']]}} for c in b['cases'])
    results={}
    for profile in PROFILES:
        chosen=[c for c in cases if screen[c['id']]['selection'][profile]['accepted']]
        groups={}
        for family in ('all','breakout','red_retest','safety_bounce'):
            cs=[c for c in chosen if family=='all' or c['signal']['family']==family]
            common=[c for c in cs if all(terminal(c,m) is not None for m in POLICIES)]
            groups[family]={'signals':len(cs),'uniqueEpisodes':len({(c['symbol'],c['signal']['episodeId']) for c in cs}),
                           'statuses':dict(Counter(c['entry']['status'] for c in cs)),
                           'policies':{m:summarize(cs,m) for m in POLICIES},
                           'commonCount':len(common),'common':{m:summarize(common,m) for m in POLICIES},
                           'commonCaseIdsHash':stable_id(sorted(c['id'] for c in common)),
                           'windows':{w['name']:{m:summarize([c for c in cs if c['window']==w['name']],m) for m in POLICIES} for w in p['windows']}}
        results[profile]={'groups':groups,'unknown':dict(Counter(k for c in cases for k in screen[c['id']]['selection'][profile]['unknown'])),
                          'failed':dict(Counter(k for c in cases for k in screen[c['id']]['selection'][profile]['failed']))}
    output={'planId':p['id'],'cases':len(cases),'profiles':results,'limitations':p['limitations']}
    write(Path(root)/'results.json',output)
    # Signal-close playlist has no subsequent outcomes; suitable for blind review.
    write(Path(root)/'playlist.json',{'planId':p['id'],'profile':DEFAULT,'items':[
        {'caseId':c['id'],'symbol':c['symbol'],'datasetId':c['datasetId'],'signalAt':c['signal']['signalAt'],
         'family':c['signal']['family'],'episodeId':c['signal']['episodeId'],'features':screen[c['id']]['features']}
        for c in cases if screen[c['id']]['selection'][DEFAULT]['accepted']]})
    return output


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('root');ap.add_argument('--source')
    ap.add_argument('--workers',type=int,default=3);ap.add_argument('--phase',choices=('prepare','build','evaluate','all'),default='all');a=ap.parse_args()
    if not 1<=a.workers<=4:ap.error('1–4 workers')
    with study_lock(a.root):
        if a.phase in ('prepare','all'):
            if not a.source:ap.error('--source required')
            p=prepare(a.root,a.source)
        else:p=checked(read(Path(a.root)/'plan.json'))
        print(json.dumps({'planId':p['id'],'phase':a.phase}),flush=True)
        if a.phase in ('build','all'):
            with ProcessPoolExecutor(max_workers=a.workers) as pool:
                for f in as_completed([pool.submit(stock,(a.root,p,s)) for s in p['symbols']]):print(json.dumps(f.result()),flush=True)
        if a.phase in ('evaluate','all'):
            r=evaluate(a.root,p);print(json.dumps({'cases':r['cases'],'results':str(Path(a.root)/'results.json')}),flush=True)


if __name__=='__main__':main()
