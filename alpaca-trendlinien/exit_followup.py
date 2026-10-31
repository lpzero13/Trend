"""Paired exit follow-up on immutable entry episodes; no new entry selection.

Source studies stay intact. Two causal Safety admission rules feed the existing
unbounded 5m execution engine. MTM is valuation, never a forced time exit.
"""
from bisect import bisect_right
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy
from datetime import datetime, timezone
import csv
import hashlib
import math
from pathlib import Path
import statistics
from unittest.mock import patch

from datasets import read_dataset, source_bars
from event_case_study import binding as base_binding, checked as check_source, load_block, statistics_for
from fan_geometry import stable_id
from fan_observer import price_at
from models import DataError
from signal_path_index import CaseExecution, PathIndex, execute_unbounded
from strategy_screen import read, write

VERSION = 'tori-causal-exit-followup-1'
BASE = ('fixed', 'original_safety', 'fan_safety')
NEW = ('qualified_fan', 'r2_fan')
POLICIES = BASE+NEW


def binding():
    root = Path(__file__).parent
    return {**base_binding(), **{n: hashlib.sha256((root/n).read_bytes()).hexdigest() for n in
            ('exit_followup.py', 'tools/run_exit_followup.py')}}


def checked(p):
    if p['id'] != stable_id({k:v for k,v in p.items() if k != 'id'}) or p['engine'] != binding():
        raise DataError('Plan oder Code verändert: neuen Folge-Studienordner verwenden.',409)
    return p


def prepare(root, source, symbols=None):
    path = Path(root)/'plan.json'
    if path.exists():
        p = checked(read(path))
        if symbols and sorted(symbols) != p['symbols']:
            raise DataError('Auswahl kann beim Wiederaufnehmen nicht geändert werden.',409)
        return p
    sp = check_source(read(Path(source)/'plan.json'))
    selected = sorted(symbols or sp['symbols'])
    if set(selected)-set(sp['symbols']):
        raise DataError('Aktie nicht in Quellstudie.',400)
    p = {'version':VERSION, 'createdAt':datetime.now(timezone.utc).isoformat(),
         'sourceRoot':str(Path(source).resolve()), 'sourcePlanId':sp['id'], 'symbols':selected,
         'datasets':{s:sp['datasets'][s] for s in selected}, 'engine':binding(),
         'cutoff':sp['outcomeCutoff'], 'policies':list(POLICIES), 'windows':sp['windows'],
         'contracts':{
             'entries':'Exactly the source cases, entry geometry, initial Safety, fills, quantities and costs. No additional filter or capital/slot limit.',
             'qualified_fan':'Keep raising original Safety; also admit current Safety only if already qualified at this 4h close. Choose higher valid candidate, never lower the stop.',
             'r2_fan':'Original Safety until a closed 4h candle reaches net unrealized +2 initial planned R including modeled exit costs. Latch permanently, then admit current Safety. Existing stop never lowered.',
             'execution':'Shared unbounded 5m hard-stop engine; source close plus 300s, expected next open; actual gap-open fills; no time exit or TP.',
             'valuation':'Closed net result plus open net liquidation mark at source dataset cutoff; censored cases stay unknown. Not a portfolio return or comparable capital-use duration.',
             'stopMark':'Hypothetical net fill at last active stop, not guaranteed locked profit. Censored values refer only to last continuous observation.',
             'bins':'Descriptive predeclared percent [0,1,2,4,infinity] and ATR [0,.5,1,2,infinity]; use all filled entries, show every outcome status. No optimized minimum stop.'},
         'limitations':['Known historical data and survivor universe; exploratory, no new independent validation',
                        'Different holding durations and dependent episodes; MTM is not realized portfolio profit',
                        'Missing paths may be informative; never assume censored cases were winners',
                        'No change to initial stop selection; lower fan alternatives require a separate causal rescan']}
    p['id'] = stable_id(p)
    for n in p['engine']:
        dest = Path(root)/'engine'/n; dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((Path(__file__).parent/n).read_bytes())
    write(path,p)
    return p


def unrealized_r(entry, close):
    r = CaseExecution(**entry['rules'])
    return (entry['quantity']*(close*(1-r.cost)-entry['entryFill'])-2*r.fee_per_order)/entry['plannedRisk']


def eligible(line, state):
    return bool(line and line['slope'] > 0 and line['knownAt'] <= state['closedAt']
                and 0 < price_at(line,state['index']) < state['close'])


def policy_timeline(case, timeline, policy):
    if policy not in NEW:
        raise ValueError('Unknown follow-up policy')
    original, e = case['signal']['safety'], case['entry']
    r=CaseExecution(**e['rules'])
    start = bisect_right([s['closedAt'] for s in timeline], e['entryAt'])
    projected, activation = [], None
    for state in timeline[start:]:
        current = state['green']
        if policy == 'r2_fan':
            net_r=(e['quantity']*(state['close']*(1-r.cost)-e['entryFill'])-2*r.fee_per_order)/e['plannedRisk']
            if activation is None and net_r >= 2:
                activation = state['closedAt']
            chosen = current if activation is not None else original
            if not eligible(chosen,state):chosen=None
        else:
            options = [ln for ln in (original,current if current and current.get('qualified') else None) if eligible(ln,state)]
            chosen = max(options,key=lambda ln:price_at(ln,state['index'])) if options else None
        projected.append({**state,'green':chosen})
    return projected, activation


def execute_policy(case, index, timeline, policy):
    if policy not in NEW:
        raise ValueError('New policies only; original results remain immutable')
    if case['entry']['status'] != 'filled':
        return {'model':policy,'status':case['entry']['status'],'reason':case['entry'].get('reason'),
                'exitAt':None,'netPnl':None,'netR':None,'netReturnPct':None,'stopEvents':[],'gateAt':None}
    projected, gate = policy_timeline(case,timeline,policy)
    result = execute_unbounded(case['signal'],case['entry'],index,projected,'fan_safety')
    observed = result['exitAt'] if result['status']=='closed' else result['lastObservedAt']
    result.update(model=policy,gateAt=gate if gate is not None and gate<=observed else None)
    states = {s['closedAt']:s for s in projected}
    for change in result['stopEvents']:
        line = states[change['knownAt']]['green']
        change.update(contacts=line['contacts'],qualified=line['qualified'],ageDays=line['span_days'],
                      source='original' if line['id']==case['signal']['safety']['id'] else 'current')
    return result


def stop_diagnostic(case, path, timeline):
    if case['entry']['status'] != 'filled':
        return None
    e = case['entry']; original = case['signal']['safety'];r=CaseExecution(**e['rules'])
    states = {s['closedAt']:s for s in timeline}
    replacements = []
    for ev in path['stopEvents']:
        if ev['lineId'] == original['id']:
            continue
        state = states[ev['knownAt']];line=state['green']
        if not line or line['id'] != ev['lineId']:
            raise AssertionError('Stop update lacks matching historical source line')
        old_level=price_at(original,state['index'])
        old_stop=math.floor(old_level*(1-r.buffer_pct/100)/r.tick)*r.tick if eligible(original,state) else None
        replacements.append({**ev,'daysAfterEntry':(ev['knownAt']-e['entryAt'])/86400,
            'netRAtKnownClose':unrealized_r(e,state['close']),'qualified':line['qualified'],
            'contacts':line['contacts'],'ageDays':line['span_days'],
            'aboveOriginalCandidate':old_stop is not None and ev['newStop']>old_stop+1e-9})
    return {'firstDifferentLine':replacements[0] if replacements else None,
            'firstTighterThanOriginal':next((v for v in replacements if v['aboveOriginalCandidate']),None),
            'replacementCount':len(replacements)}


def _work(task):
    root,p,symbol = task;checked(p)
    out = Path(root)/'stocks'/(symbol+'.json.gz')
    if out.exists():
        load_followup(root,p,symbol);return {'symbol':symbol,'cached':True}
    sp=check_source(read(Path(p['sourceRoot'])/'plan.json'))
    if sp['id']!=p['sourcePlanId']:
        raise DataError('Quellstudie wurde geändert.',409)
    source=load_block(p['sourceRoot'],sp,symbol)
    cases=source['cases'];timeline=source['timeline'];new={};diagnostics={}
    with patch('alpaca._request',side_effect=AssertionError('Follow-up stays offline')):
        if cases:
            frames=source_bars(read_dataset(p['datasets'][symbol]))
            fine=[b for b in frames['5m'] if b.end<=p['cutoff']]
            index=PathIndex(fine,p['cutoff'])
            for case in cases:
                new[case['id']]={m:execute_policy(case,index,timeline,m) for m in NEW}
                diagnostics[case['id']]=stop_diagnostic(case,case['paths']['fan_safety'],timeline)
    value={'planId':p['id'],'symbol':symbol,'sourceChecksum':source['checksum'],
           'caseIds':[c['id'] for c in cases],'newPaths':new,'originalFanDiagnostics':diagnostics}
    value['checksum']=stable_id(value);write(out,value)
    return {'symbol':symbol,'cases':len(cases),'newPaths':2*len(cases)}


def load_followup(root,p,symbol):
    value=read(Path(root)/'stocks'/(symbol+'.json.gz'))
    if value['planId']!=p['id'] or value['checksum']!=stable_id({k:v for k,v in value.items() if k!='checksum'}):
        raise DataError('Folge-Ergebnisblock verändert.',409)
    return value


def build(root,p,workers=2,progress=print):
    checked(p)
    if type(workers) is not int or not 1<=workers<=4:raise ValueError('1–4 Worker')
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for done in as_completed([pool.submit(_work,(str(root),p,s)) for s in p['symbols']]):
            progress(done.result())


def terminal(case, policy):
    e,p=case['entry'],case['paths'][policy]
    if e['status']!='filled':return None
    if p['status']=='closed':return {'pct':p['netReturnPct'],'r':p['netR'],'realized':True}
    if p['status']=='open':return {'pct':p['markNetReturnPct'],'r':p['markNetPnl']/e['plannedRisk'],'realized':False}
    return None


def stop_mark(case,policy):
    e,p=case['entry'],case['paths'][policy]
    if e['status']!='filled':return None
    r=CaseExecution(**e['rules'])
    return (e['quantity']*(p['finalStop']*(1-r.cost)-e['entryFill'])-2*r.fee_per_order)/e['plannedRisk']


def summarize(cases,policy):
    value=statistics_for(cases,policy)
    observed=[(c,terminal(c,policy)) for c in cases if terminal(c,policy) is not None]
    pct=[v['pct'] for _,v in observed];rs=[v['r'] for _,v in observed]
    value.update(observedClosedOrOpen=len(observed),
        meanTerminalPct=statistics.mean(pct) if pct else None,medianTerminalPct=statistics.median(pct) if pct else None,
        meanTerminalR=statistics.mean(rs) if rs else None,medianTerminalR=statistics.median(rs) if rs else None,
        positiveTerminalPct=100*sum(v>0 for v in pct)/len(pct) if pct else None,
        meanTerminalPctWithoutBest3=statistics.mean(sorted(pct,reverse=True)[3:]) if len(pct)>3 else None)
    return value


def paired(cases,a,b):
    available=[c for c in cases if terminal(c,a) is not None and terminal(c,b) is not None]
    deltas=[terminal(c,b)['pct']-terminal(c,a)['pct'] for c in available]
    return {'common':len(available),'excluded':len(cases)-len(available),
        'firstMeanPct':statistics.mean(terminal(c,a)['pct'] for c in available) if available else None,
        'secondMeanPct':statistics.mean(terminal(c,b)['pct'] for c in available) if available else None,
        'medianDeltaPct':statistics.median(deltas) if deltas else None,
        'secondBetter':sum(d>1e-9 for d in deltas),'secondWorse':sum(d< -1e-9 for d in deltas),
        'equal':sum(abs(d)<=1e-9 for d in deltas),'caseIdsHash':stable_id(sorted(c['id'] for c in available))}


def load_cases(root,p):
    sp=check_source(read(Path(p['sourceRoot'])/'plan.json'))
    if sp['id']!=p['sourcePlanId']:raise DataError('Falsche Quellstudie.',409)
    cases=[];diagnostics={}
    for symbol in p['symbols']:
        base=load_block(p['sourceRoot'],sp,symbol);follow=load_followup(root,p,symbol)
        if follow['sourceChecksum']!=base['checksum'] or follow['caseIds']!=[c['id'] for c in base['cases']]:
            raise AssertionError('Source case selection changed')
        for c in base['cases']:
            cases.append({**c,'paths':{**c['paths'],**follow['newPaths'][c['id']]}})
        diagnostics.update(follow['originalFanDiagnostics'])
    return cases,diagnostics


def bins(cases,field,edges):
    result={}
    for low,high in zip(edges,edges[1:]):
        cs=[c for c in cases if c['entry']['status']=='filled' and c['features'].get(field) is not None
            and low<=c['features'][field]<high]
        result[f'{low:g}–{high:g}']={m:summarize(cs,m) for m in POLICIES}
    return result


def evaluate(root,p):
    checked(p);cases,diagnostics=load_cases(root,p)
    groups=defaultdict(list)
    for c in cases:groups[c['signal']['family']+':'+c['signal']['cohort']].append(c)
    grouped={g:{m:summarize(cs,m) for m in POLICIES} for g,cs in groups.items()}
    comparisons={g:{m:paired(cs,'original_safety',m) for m in POLICIES if m not in ('fixed','original_safety')} for g,cs in groups.items()}
    bywindow={w['name']:{g:{m:summarize([c for c in cs if c['window']==w['name']],m) for m in POLICIES} for g,cs in groups.items()} for w in p['windows']}
    distance={g:{'percent':bins(cs,'stopDistancePct',(0,1,2,4,math.inf)),
                 'atr4h':bins(cs,'stopDistanceATR4h',(0,.5,1,2,math.inf))} for g,cs in groups.items()}
    changes={}
    for g,cs in groups.items():
        first=[diagnostics[c['id']]['firstTighterThanOriginal'] for c in cs if diagnostics[c['id']] and diagnostics[c['id']]['firstTighterThanOriginal']]
        changes[g]={'signals':len(cs),'tighterReplacements':len(first),
            'qualified':sum(v['qualified'] for v in first),'twoContacts':sum(v['contacts']==2 for v in first),
            'medianDaysAfterEntry':statistics.median(v['daysAfterEntry'] for v in first) if first else None,
            'medianNetRAtKnownClose':statistics.median(v['netRAtKnownClose'] for v in first) if first else None}
    runners=[]
    for c in cases:
        if c['signal']['cohort']=='qualified' and c['signal']['family'] in ('breakout','red_retest') and c['paths']['original_safety']['status']=='open':
            runners.append({'caseId':c['id'],'symbol':c['symbol'],'family':c['signal']['family'],
                'outcomes':{m:{'status':c['paths'][m]['status'],'terminal':terminal(c,m),'stopMarkR':stop_mark(c,m)} for m in POLICIES},
                'firstTighterCurrentSafety':diagnostics[c['id']]['firstTighterThanOriginal'] if diagnostics[c['id']] else None})
    result={'planId':p['id'],'cases':len(cases),'groups':grouped,'paired':comparisons,'windows':bywindow,
            'distanceBins':distance,'firstUpgrades':changes,'originalOpenQualified':runners,'limitations':p['limitations']}
    write(Path(root)/'results.json',result)
    columns=('caseId','symbol','window','family','cohort','policy','entryStatus','status','stopDistancePct','stopDistanceATR4h',
             'netR','netReturnPct','terminalR','terminalPct','stopMarkR','markAsOf','gateAt')
    with (Path(root)/'cases.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader()
        for c in cases:
            for policy,path in c['paths'].items():
                t=terminal(c,policy)
                writer.writerow({'caseId':c['id'],'symbol':c['symbol'],'window':c['window'],'family':c['signal']['family'],
                    'cohort':c['signal']['cohort'],'policy':policy,'entryStatus':c['entry']['status'],'status':path['status'],
                    'stopDistancePct':c['features'].get('stopDistancePct'),'stopDistanceATR4h':c['features'].get('stopDistanceATR4h'),
                    'netR':path.get('netR'),'netReturnPct':path.get('netReturnPct'),'terminalR':t['r'] if t else None,
                    'terminalPct':t['pct'] if t else None,'stopMarkR':stop_mark(c,policy),
                    'markAsOf':path.get('exitAt') or path.get('lastObservedAt'),'gateAt':path.get('gateAt')})
    return result
