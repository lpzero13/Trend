"""Post-hoc entry strata and paired exits on immutable, already calculated paths.

This module never selects or deploys a strategy, changes signals, or filters
portfolio entries by their later outcome/completeness.
"""
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime
import csv
import hashlib
import math
from pathlib import Path
import statistics

from fan_geometry import stable_id
from models import DataError, NY
from robustness_study import validate_plan, window_root
from screening_portfolio import ledger, compact
from strategy_screen import read, write, load_fold, load_task, task_path

VERSION='tori-entry-exit-comparison-2'
FAMILIES=('breakout','red_retest','safety_bounce')
COHORTS=('qualified','two','three_young')
MODELS=('fixed','original_safety','fan_safety')
GROUPS=tuple((f,c) for f in FAMILIES for c in COHORTS if f!='safety_bounce' or c=='qualified')


def binding():
    root=Path(__file__).parent
    return {name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in
            ('entry_exit_comparison.py','tools/verify_robustness_study.py','tools/verify_strategy_screen.py')}


def prepare(root,source):
    root,source=Path(root),Path(source).resolve();p=validate_plan(read(source/'plan.json'))
    if (root/'plan.json').exists():
        plan=read(root/'plan.json')
        if plan['sourcePlanId']!=p['id'] or plan['analysisCode']!=binding() or plan['id']!=stable_id({k:v for k,v in plan.items() if k!='id'}):
            raise DataError('Vergleichsplan geändert; neuen Ausgabeordner anlegen.',409)
        return plan,p
    plan={'version':VERSION,'sourceRoot':str(source),'sourcePlanId':p['id'],'analysisCode':binding(),
          'groups':[list(g) for g in GROUPS],'models':list(MODELS),'horizon':40,'stopMode':'hard_stop',
          'portfolioCosts':[1,2],'smaFilterApplied':False,
          'classification':'Entry family and contact cohort at signal; no later upgrades; breakout subtypes shown separately',
          'paired':'Only descriptive common-complete cases, identical case IDs for all exits; missing cases explicitly counted',
          'portfolio':'All matching entries including censored paths; finite capital, independent ledger per variant/window',
          'selection':'Post-hoc diagnostic on known periods, no winner selection, no change to frozen candidate',
          'limitations':['Correlated/overlapping episodes, not independent samples','Joint-complete statistics can be completion-biased',
                         'Per-entry R is not additive portfolio return','No holdout, p-value or prospective claim',
                         'SIP/split whole-share historical affordability and dividends remain unresolved',
                         'Only stored hard-stop/40-day models; not a full comparison of all original Tori exit rules']}
    plan['id']=stable_id(plan);write(root/'plan.json',plan);return plan,p


def group_cases(cases,family,cohort,subtype=None):
    return [c for c in cases if c['signal']['family']==family and c['signal']['cohort']==cohort
            and (subtype is None or c['signal']['subtype']==subtype)]


def path_for(case,model):return case['paths'][f'{model}:hard_stop:40']


def validate_case(case):
    s,e=case['signal'],case['entry']
    if (s['family'],s['cohort']) not in GROUPS:raise DataError('Unbekannte Entry-Gruppe; nicht still verwerfen.',422)
    for model in MODELS:
        p=path_for(case,model)
        if p['status']=='closed':
            if e['status']!='filled' or p['exitAt']<e['entryAt'] or e['plannedRisk']<=0:raise AssertionError('Invalid closed entry/path')
            expected=(e['quantity']*(p['exitFill']-e['entryFill'])-2*e['rules']['fee_per_order'])/e['plannedRisk']
            if not math.isfinite(p['netR']) or abs(expected-p['netR'])>1e-8:raise AssertionError('Stored R arithmetic differs')


def stats(cases,model):
    if not cases:return {'n':0,'meanNetR':None,'medianNetR':None,'winPct':None,'meanPriceReturnPct':None,
                         'profitFactorR':None,'medianCalendarDays':None,'oneRThenNonpositivePct':None,'exitReasons':{}}
    paths=[path_for(c,model) for c in cases];rs=[p['netR'] for p in paths]
    wins=[r for r in rs if r>0];loss=-sum(r for r in rs if r<0)
    gaveback=0
    for c,p in zip(cases,paths):
        e=c['entry'];mfe=p.get('mfeR',0)*e['initialRisk']*e['quantity']/e['plannedRisk']
        gaveback+=mfe>=1 and p['netR']<=0
    return {'n':len(cases),'meanNetR':statistics.mean(rs),'medianNetR':statistics.median(rs),
            'winPct':100*len(wins)/len(rs),'meanPriceReturnPct':statistics.mean(100*(p['exitFill']/c['entry']['entryFill']-1) for c,p in zip(cases,paths)),
            'profitFactorR':sum(wins)/loss if loss else None,
            'medianCalendarDays':statistics.median((datetime.fromtimestamp(p['exitAt'],NY).date()-datetime.fromtimestamp(c['entry']['entryAt'],NY).date()).days for c,p in zip(cases,paths)),
            'oneRThenNonpositivePct':100*gaveback/len(cases),'exitReasons':dict(Counter(p['reason'] for p in paths))}


def analyze_group(cases):
    filled=[c for c in cases if c['entry']['status']=='filled']
    common=[c for c in filled if all(path_for(c,m)['status']=='closed' for m in MODELS)]
    by_model={}
    for m in MODELS:
        closed=[c for c in filled if path_for(c,m)['status']=='closed']
        by_model[m]={'pathStatuses':dict(Counter(path_for(c,m)['status'] for c in filled)),
                     'allObservedClosed':stats(closed,m),'sameEntries':stats(common,m)}
    differences={}
    for m in MODELS[1:]:
        values=[(c,path_for(c,m)['netR']-path_for(c,'fixed')['netR']) for c in common]
        symbols=sorted({c['symbol'] for c in common});clusters=defaultdict(list)
        for c,d in values:clusters[c['symbol'],c['foldName']].append(d)
        loo=[statistics.mean(d for c,d in values if c['symbol']!=s) for s in symbols if any(c['symbol']!=s for c,d in values)]
        differences[m]={'n':len(values),'meanDeltaR':statistics.mean(d for _,d in values) if values else None,
            'medianDeltaR':statistics.median(d for _,d in values) if values else None,
            'betterPct':100*sum(d>1e-10 for _,d in values)/len(values) if values else None,
            'equalPct':100*sum(abs(d)<=1e-10 for _,d in values)/len(values) if values else None,
            'equalStockWindowMeanDeltaR':statistics.mean(statistics.mean(ds) for ds in clusters.values()) if clusters else None,
            'leaveOneSymbolOutDeltaRange':[min(loo),max(loo)] if loo else None}
    return {'signals':len(cases),'entryStatuses':dict(Counter(c['entry']['status'] for c in cases)),
            'entryReasons':dict(Counter(c['entry'].get('reason') or c['entry']['status'] for c in cases)),
            'filled':len(filled),'commonComplete':len(common),'incompleteForPaired':len(filled)-len(common),
            'symbolsWithCommon':len({c['symbol'] for c in common}),'models':by_model,'pairedAgainstFixed':differences,
            'sameEntryIdsHash':stable_id(sorted(c['id'] for c in common))}


def case_rows(cases):
    for c in sorted(cases,key=lambda c:(c['signal']['signalAt'],c['symbol'],c['id'])):
        s,e=c['signal'],c['entry']
        common=e['status']=='filled' and all(path_for(c,m)['status']=='closed' for m in MODELS)
        for m in MODELS:
            p=path_for(c,m)
            yield {'caseId':c['id'],'symbol':c['symbol'],'window':c['foldName'],'family':s['family'],'cohort':s['cohort'],
                'subtype':s['subtype'],'signalET':datetime.fromtimestamp(s['signalAt'],NY).isoformat(),
                'entryStatus':e['status'],'entryAt':e['entryAt'],'entryFill':e.get('entryFill'),
                'initialStop':e['initialStop'],'commonComplete':common,'exitModel':m,'pathStatus':p['status'],
                'exitAt':p.get('exitAt'),'exitReason':p.get('reason'),'netR':p.get('netR')}


def run(root,source,progress=lambda v:None):
    from tools.verify_strategy_screen import verify_cash
    from tools.verify_robustness_study import verify_marks
    root=Path(root);plan,p=prepare(root,source);source=Path(plan['sourceRoot'])
    selection=(source/'selection.json').read_bytes();all_cases=[];windows=[];proofs=[];cash_checked=0
    for fold in p['folds']['validation']:
        src=window_root(source,fold);cases,contexts,period=load_fold(src,p,'validation',fold)
        for s in p['symbols']:
            b=load_task(task_path(src,'validation',s,fold),p)
            proofs.append({'symbol':s,'fold':fold['name'],'checksum':b['checksum'],'availability':b['availability']})
        for c in cases:
            c['foldName']=fold['name'];validate_case(c)
        all_cases.extend(cases);groups={};portfolios={}
        for family,cohort in GROUPS:
            key=family+':'+cohort;selected=group_cases(cases,family,cohort)
            groups[key]=analyze_group(selected);portfolios[key]={}
            for model in MODELS:
                policy={'id':key+':'+model+':hard40','family':family,'quality':'all','model':model,
                        'horizon':40,'stopMode':'hard_stop','sma200':False}
                # Selection uses ONLY contemporaneous family/cohort. Censored
                # paths are deliberately kept in the actual cash simulation.
                portfolios[key][model]={}
                for multiplier in (1,2):
                    value=ledger(selected,contexts,period,policy,cost_multiplier=multiplier)
                    verify_cash(value,0.)
                    costs={'spread_bps':5.*multiplier,'slippage_bps':5.*multiplier,'fee_per_order':0.}
                    verify_marks(value,contexts,period,costs,p['datasets']);cash_checked+=1
                    name='base' if multiplier==1 else 'doubleCosts'
                    portfolios[key][model][name]=compact(value)
                    write(root/fold['name']/'ledgers'/(key.replace(':','_')+'-'+model+'-'+name+'.json.gz'),value)
        result={'fold':fold,'groups':groups,'portfolios':portfolios,
                'breakoutSubtypes':{sub:analyze_group(group_cases(cases,'breakout','qualified',sub)) for sub in ('immediate','delayed')}}
        write(root/fold['name']/'result.json',result);windows.append(result)
        progress({'window':fold['name'],'cases':len(cases),'ledgersVerified':cash_checked})
    if len({c['id'] for c in all_cases})!=len(all_cases):raise AssertionError('Duplicate cases across windows')
    groups={f+':'+q:analyze_group(group_cases(all_cases,f,q)) for f,q in GROUPS}
    subtypes={sub:analyze_group(group_cases(all_cases,'breakout','qualified',sub)) for sub in ('immediate','delayed')}
    # Context slices are descriptive; no SMA rule is switched on in the books.
    sma={}
    for family in FAMILIES:
        selected=group_cases(all_cases,family,'qualified');buckets={'above':[],'below':[],'unknown':[]}
        for c in selected:
            ctx=c['context'];a,b=ctx.get('dailyClose'),ctx.get('dailySma200')
            buckets['unknown' if a is None or b is None else 'above' if a>=b else 'below'].append(c)
        sma[family]={k:analyze_group(v) for k,v in buckets.items()}
    result={'planId':plan['id'],'sourcePlanId':p['id'],'inputProofs':proofs,'cases':len(all_cases),
            'groups':groups,'breakoutSubtypes':subtypes,'smaContext':sma,'windows':windows,
            'audit':{'sourceBlocks':len(proofs),'cashAnd5mValuationVerified':cash_checked,
                     'storedPathArithmeticVerified':True,'noDuplicateCases':True,'providerCalls':0,
                     'frozenSourceSelectionUnchanged':(source/'selection.json').read_bytes()==selection},
            'interpretation':plan['selection'],'limitations':plan['limitations']}
    if not result['audit']['frozenSourceSelectionUnchanged']:raise AssertionError('Source selection changed')
    write(root/'comparison.json',result)
    rows=case_rows(all_cases)
    with (root/'entry-exit-cases.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        first=next(rows,None)
        if first:
            writer=csv.DictWriter(stream,fieldnames=list(first));writer.writeheader();writer.writerow(first);writer.writerows(rows)
    return result
