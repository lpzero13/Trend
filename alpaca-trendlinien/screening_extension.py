"""Explicit second study: longer holding, prior test now known, later block sealed."""
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
import hashlib
import math
from pathlib import Path
import random
from unittest.mock import patch

from datasets import read_dataset, source_bars
from fan_execution import entry_contract, ExecutionRules
from fan_geometry import stable_id
from fan_study import source_gaps
from models import DataError, NY
from pilot_backtest import PilotSpec, run, execute_path, audit
from screening_portfolio import candidates, matches, ledger, compact, test_gate
from strategy_screen import read, write, load_task, load_fold, task_path, select, engine_binding

VERSION='tori-screening-extension-1'


def binding():
    return {'base':engine_binding(),'extension':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def prepare(root,base):
    root=Path(root);path=root/'plan.json'
    if path.exists():
        p=read(path)
        if stable_id({k:v for k,v in p.items() if k!='id'})!=p['id'] or p['engine']!=binding():raise DataError('Changed follow-up contract; use a new directory.',409)
        return p
    source=read(Path(base)/'plan.json')
    if source['engine']!=engine_binding():raise DataError('Original study engine changed.',409)
    original=read(Path(base)/'validation-summary.json')
    if original['primaryPassed']:raise DataError('Follow-up protocol is specifically for the failed original validation.',409)
    p={**deepcopy(source),'version':VERSION,'baseRoot':str(Path(base).resolve()),'basePlanId':source['id'],
       'engine':binding(),'folds':{'development':source['folds']['development'],'validation':source['folds']['confirmation']},
       'policies':[{**c,'id':c['id']+':h40','horizon':40} for c in candidates()],
       'knownPriorTest':'2024 is development information for this revision, not a fresh test',
       'changedAxis':'max holding 40 instead of 20 trading sessions; cumulative 60 candidates across both rounds'}
    p.pop('id',None);p['id']=stable_id(p);write(path,p);return p


def _work(task):
    root,plan,phase,symbol,fold=task;path=task_path(root,phase,symbol,fold)
    if path.exists():load_task(path,plan);return {'symbol':symbol,'fold':fold['name'],'cached':True}
    with patch('alpaca._request',side_effect=AssertionError('Offline only')):
        dataset=read_dataset(plan['datasets'][symbol])
        spec=PilotSpec(start=fold['start'],end=fold['end'],outcome_end=fold['outcome_end'],horizons=(40,),stop_modes=('hard_stop',))
        _,start,_,cutoff=spec.bounds();fine=[b for b in source_bars(dataset)['5m'] if start<=b.time and b.end<=cutoff]
        if phase=='development':
            source_plan=read(Path(plan['baseRoot'])/'plan.json')
            old=load_task(task_path(plan['baseRoot'],'development',symbol,fold),source_plan)
            pilot=deepcopy(old['pilot']);timeline=pilot['timeline']
            for c in pilot['cases']:
                c['paths']={f'{model}:hard_stop:40':execute_path(c['signal'],c['entry'],fine,timeline,cutoff,40,model,'hard_stop')
                            for model in ('fixed','original_safety','fan_safety')}
                c['observations']={}
            extension={'sourcePilotRunId':pilot['runId'],'addedHorizon':40,'meaning':'Original signals/entries, new post-entry paths only'}
            extension['audit']=audit(pilot['cases'],spec.bounds()[1],spec.bounds()[2])
            if not extension['audit']['passed']:raise AssertionError(extension['audit'])
        else:
            pilot=run(dataset,spec,ExecutionRules(capital=1_000_000.,risk_fraction=.01));extension=None
        marks=[b for b in source_bars(dataset)['5m'] if start-86400<=b.end<=cutoff]
        payload={'planId':plan['id'],'symbol':symbol,'datasetId':dataset['id'],'fold':fold,'pilot':pilot,'extension':extension,
                 'marks':{'ends':[b.end for b in marks],'closes':[b.close for b in marks]}}
        payload['checksum']=stable_id(payload);write(path,payload)
    return {'symbol':symbol,'fold':fold['name'],'cases':len(pilot['cases']),'cached':False}


def build(root,plan,phase,progress):
    tasks=[(str(root),plan,phase,s,f) for f in plan['folds'][phase] for s in plan['symbols']]
    with ProcessPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(_work,t) for t in tasks]):progress(future.result())


def development(root,plan,progress):
    build(root,plan,'development',progress)
    results={p['id']:[] for p in plan['policies']}
    for fold in plan['folds']['development']:
        cases,contexts,phase=load_fold(root,plan,'development',fold)
        for p in plan['policies']:
            value=ledger(cases,contexts,phase,p);results[p['id']].append(value)
            write(Path(root)/'development-ledgers'/(fold['name']+'-'+p['id'].replace(':','_')+'.json.gz'),value)
        progress({'phase':'development-ledgers','fold':fold['name']})
    result=select(results,plan['policies']);result.update(planId=plan['id'],purpose='40-session selection before the later block')
    result['id']=stable_id(result);write(Path(root)/'selection.json',result);return result


def controls(root,plan,policy,actual):
    fold=plan['folds']['validation'][0];original,contexts,phase=load_fold(root,plan,'validation',fold)
    desired=defaultdict(lambda:defaultdict(int))
    for c in original:
        if matches(c,policy):desired[c['symbol']][datetime.fromtimestamp(c['signal']['signalAt'],NY).strftime('%Y-%m')]+=1
    streams=[[] for _ in range(39)];short=[]
    for symbol in plan['symbols']:
        payload=load_task(task_path(root,'validation',symbol,fold),plan);timeline=payload['pilot']['timeline']
        dataset=read_dataset(plan['datasets'][symbol]);spec=PilotSpec(start=fold['start'],end=fold['end'],outcome_end=fold['outcome_end'])
        _,start,end,cutoff=spec.bounds();frames=source_bars(dataset)
        fine=[b for b in frames['5m'] if start<=b.time and b.end<=cutoff];daily=[b for b in frames['1D'] if b.end<=cutoff]
        from bisect import bisect_right
        dends=[b.end for b in daily];gaps=source_gaps(daily,cutoff,'1D');pools=defaultdict(list)
        for s in timeline:
            green=s['green']
            if not start<=s['closedAt']<=end or not green or not 0<green['value']<s['close']:continue
            if policy['family']=='safety_bounce' and not green['qualified']:continue
            n=bisect_right(dends,s['closedAt']);known=daily[:n];last=known[-1].close if known else None
            sma=sum(b.close for b in known[-200:])/200 if n>=200 and not any(n-200<i<n for i in gaps) else None
            if policy['sma200'] and (sma is None or last<sma):continue
            pools[datetime.fromtimestamp(s['closedAt'],NY).strftime('%Y-%m')].append((s,last,sma))
        cache={};execution=ExecutionRules(capital=1_000_000.,risk_fraction=.01)
        for i in range(39):
            rng=random.Random(f"{plan['seed']}|followup|{policy['id']}|{symbol}|{i}")
            for month,count in sorted(desired[symbol].items()):
                pool=pools.get(month,[])
                if not pool:short.append([symbol,month,i,count]);continue
                for serial in range(count):
                    s,last,sma=rng.choice(pool);at=s['closedAt']
                    if at not in cache:
                        green=deepcopy(s['green']);stop=math.floor(green['value']*.997/.01)*.01
                        signal={'id':stable_id([VERSION,'control',symbol,at]),'signalAt':at,'initialStop':stop,'family':policy['family'],
                            'cohort':'qualified' if green['qualified'] else 'two','control':True,'signalClose':s['close'],'line':green,'safety':green}
                        entry=entry_contract(signal,fine,cutoff,execution)
                        path=execute_path(signal,entry,fine,timeline,cutoff,40,policy['model'],'hard_stop')
                        cache[at]={'id':signal['id'],'symbol':symbol,'datasetId':dataset['id'],'signal':signal,
                                   'context':{'dailyClose':last,'dailySma200':sma},'entry':entry,'paths':{f"{policy['model']}:hard_stop:40":path}}
                    c=deepcopy(cache[at]);c['id']=stable_id([c['id'],i,month,serial]);streams[i].append(c)
    out=[]
    for i,cases in enumerate(streams):
        value=ledger(cases,contexts,phase,{**policy,'quality':'all'})
        write(Path(root)/'validation'/f'control-ledger-{i}.json.gz',value);out.append(compact(value))
    returns=[v['markedReturnPct'] for v in out if v['markedReturnPct'] is not None]
    threshold=sorted(returns)[math.ceil(.9*len(returns))-1] if returns else None
    return {'items':out,'shortfalls':short,'complete':not short and len(returns)==39,'q90ReturnPct':threshold,
            'actualReturnPct':actual['markedReturnPct'],
            'aboveQ90':not short and len(returns)==39 and actual['markedReturnPct'] is not None and actual['markedReturnPct']>threshold,
            'interpretation':'Exploratory matched month/asset/valid Safety comparison; red contact quality unmatched; no corrected p-value'}


def validate(root,plan,progress):
    selection=read(Path(root)/'selection.json')
    if selection['planId']!=plan['id'] or stable_id({k:v for k,v in selection.items() if k!='id'})!=selection['id']:raise DataError('Changed selection.',409)
    if not selection['primary']:return {'opened':False,'reason':'No development candidate passed'}
    build(root,plan,'validation',progress)
    cases,contexts,phase=load_fold(root,plan,'validation',plan['folds']['validation'][0]);items=[];primary=None
    for p in selection['selectedByFamily'].values():
        base=ledger(cases,contexts,phase,p);stress=ledger(cases,contexts,phase,p,cost_multiplier=2)
        write(Path(root)/'validation'/(p['id'].replace(':','_')+'-ledger.json.gz'),base)
        write(Path(root)/'validation'/(p['id'].replace(':','_')+'-stress.json.gz'),stress)
        r={'policy':p,'base':compact(base),'doubleCosts':compact(stress),'gate':test_gate(base,stress)};items.append(r)
        if p['id']==selection['primary']['id']:primary=r
    control=controls(root,plan,selection['primary'],primary['base'])
    result={'opened':True,'planId':plan['id'],'selectionId':selection['id'],'items':items,'primary':primary,'controls':control,
            'primaryPassed':primary['gate']['passed'] and control['aboveQ90'],'phase':'later block 2025-2026'}
    write(Path(root)/'validation-summary.json',result);return result
