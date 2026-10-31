"""Fixed-signal, isolated stop-trigger and holding-horizon research; offline only."""
from concurrent.futures import ProcessPoolExecutor,as_completed
from dataclasses import asdict
from datetime import datetime,timedelta,timezone
from bisect import bisect_right
from pathlib import Path
import hashlib
import statistics
from unittest.mock import patch

from datasets import read_dataset,source_bars
from fan_execution import entry_contract,ExecutionRules
from fan_geometry import stable_id
from models import DataError
from pilot_backtest import PilotSpec,scan,execute_path,audit,code_digest,VERSION as PILOT_VERSION
from robustness_study import validate_plan,window_root
from screening_portfolio import ledger,compact
from strategy_screen import read,write,load_task,task_path,load_fold

VERSION='tori-trigger-horizon-2'
FAMILIES=('breakout','red_retest')
MODELS=('fixed','original_safety','fan_safety')
MODES=('hard_stop','close_stop')
HORIZONS=(40,80)


def policies(family):
    return [{'id':f'{family}:qualified:{m}:{mode}:{h}','family':family,'quality':'qualified','sma200':False,
             'model':m,'stopMode':mode,'horizon':h} for m in MODELS for mode in MODES for h in HORIZONS]


def binding():
    root=Path(__file__).parent
    return {'pilot':code_digest(),'files':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in
            ('trigger_horizon_research.py','screening_portfolio.py','strategy_portfolio.py','tools/verify_strategy_screen.py','tools/verify_robustness_study.py')}}


def checked(plan):
    if plan['id']!=stable_id({k:v for k,v in plan.items() if k!='id'}) or plan['engine']!=binding():
        raise DataError('Exit-Prüfcode oder Vertrag geändert; neuen Versuchsordner verwenden.',409)
    return plan


def prepare(root,source,audit_root,*,reuse=None):
    root,source,audit_root=Path(root),Path(source).resolve(),Path(audit_root).resolve()
    sp=validate_plan(read(source/'plan.json'));quality=read(audit_root/'audit-summary.json')
    contract=read(audit_root/'contract.json')
    if quality['contractId']!=contract['id'] or contract['sourcePlanId']!=sp['id']:raise DataError('Datenprüfung gehört zu anderer Quelle.',409)
    if quality['recoveredBars'] or quality['conflictingPairs']:
        raise DataError('Kursänderungen zuerst separat veröffentlichen und Signale neu registrieren; keine Mischung mit eingefrorenen Entries.',409)
    if (root/'plan.json').exists():
        p=checked(read(root/'plan.json'))
        if p['sourcePlanId']!=sp['id'] or p['dataAuditId']!=contract['id']:raise DataError('Andere Versuchsquelle.',409)
        return p
    folds=[]
    for f in sp['folds']['validation']:
        end=datetime.fromisoformat(f['end']);outcome=(end+timedelta(days=160)).date().isoformat()
        folds.append({**f,'outcome_end':outcome})
    p={'version':VERSION,'createdAt':datetime.now(timezone.utc).isoformat(),'sourceRoot':str(source),'sourcePlanId':sp['id'],
       'sourceEngine':sp['engine'],'sourceFolds':sp['folds']['validation'],'datasets':sp['datasets'],'symbols':sp['symbols'],
       'dataAuditId':contract['id'],'dataAudit':quality,'folds':{'validation':folds},'engine':binding(),
       'policies':[p for f in FAMILIES for p in policies(f)],'execution':asdict(ExecutionRules(capital=1_000_000.,risk_fraction=.01)),
       'portfolio':sp['portfolio'],'costs':sp['costs'],'selection':'No reselection; 12 predefined exits per family on identical frozen qualified entries',
       'closeContract':'4h close below previously active buffered ratchet; next expected 5m open after 300 seconds; no hard emergency stop',
       'horizonContract':'40 or 80 trading sessions after entry day; 160 calendar days outcome extension',
       'limitations':['Known periods, exploratory follow-up not fresh validation','Data gaps remain censored, no synthetic candles',
                      'Close-stop losses can exceed planned stop risk substantially','No per-window winner switching or new strategy approval',
                      'Whole-share historical split factors, dividends and FX not reconciled',
                      'This buffered ratchet close rule is not the different Safety-minus-0.15-ATR rule']}
    if reuse:
        old=read(Path(reuse)/'plan.json')
        if old['sourcePlanId']!=sp['id'] or old['dataAuditId']!=contract['id']:raise DataError('Andere Wiederverwendungsquelle.',409)
        p['reusedRun']={'root':str(Path(reuse).resolve()),'planId':old['id'],
                        'reason':'Separate filename after legacy module-name collision; scientific functions unchanged and AST-verified'}
    p['id']=stable_id(p);write(root/'plan.json',p);return p


def reuse_blocks(root,p):
    """Preserve old run; explicitly rebind identical verified paths to NEW plan."""
    import ast
    checked(p);origin=Path(p['reusedRun']['root']);old=read(origin/'plan.json')
    if old['id']!=p['reusedRun']['planId'] or old['id']!=stable_id({k:v for k,v in old.items() if k!='id'}):raise DataError('Geänderte Altquelle.',409)
    if any(old[k]!=p[k] for k in ('sourcePlanId','datasets','folds','policies','execution','dataAuditId')):raise DataError('Wissenschaftliche Eingaben verändert.',409)
    archived=origin/'engine'/'exit_research.py'
    if hashlib.sha256(archived.read_bytes()).hexdigest()!=old['engine']['files']['exit_research.py']:raise DataError('Archivierter Quellcode verändert.',409)
    root_code=Path(__file__).parent
    for name,checksum in old['engine']['files'].items():
        if name!='exit_research.py' and hashlib.sha256((root_code/name).read_bytes()).hexdigest()!=checksum:raise DataError('Gemeinsame Abhängigkeit verändert.',409)
    def functions(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)}
    a,b=functions(archived),functions(Path(__file__))
    if any(a[n]!=b[n] for n in ('policies','_work','paired','evaluate')):raise DataError('Wissenschaftliche Funktionen verändert.',409)
    count=0
    for fold in p['folds']['validation']:
        for symbol in p['symbols']:
            source=load_task(task_path(origin,'validation',symbol,fold),old)
            dest=task_path(root,'validation',symbol,fold)
            if dest.exists():load_task(dest,p);continue
            payload={**source,'planId':p['id'],'reusedFrom':{'planId':old['id'],'checksum':source['checksum']}}
            payload.pop('checksum');payload['checksum']=stable_id(payload);write(dest,payload);count+=1
    return count


def _work(task):
    root,p,symbol=task;checked(p);sp=read(Path(p['sourceRoot'])/'plan.json')
    todo=[]
    for f in p['folds']['validation']:
        path=task_path(root,'validation',symbol,f)
        if path.exists():load_task(path,p)
        else:todo.append((f,path))
    if not todo:return {'symbol':symbol,'cached':True}
    with patch('alpaca._request',side_effect=AssertionError('Exit research stays offline')):
        d=read_dataset(p['datasets'][symbol]);frames=source_bars(d);result=[]
        for fold,path in todo:
            oldfold=next(f for f in p['sourceFolds'] if f['name']==fold['name'])
            original=load_task(task_path(window_root(p['sourceRoot'],oldfold),'validation',symbol,oldfold),sp)
            spec=PilotSpec(start=fold['start'],end=fold['end'],outcome_end=fold['outcome_end'])
            warm,start,end,cutoff=spec.bounds()
            source=[b for b in frames['4h'] if b.time>=warm and b.end<=cutoff]
            fine=[b for b in frames['5m'] if b.time>=warm and b.end<=cutoff]
            if original['availability']=='available':
                signals,timeline,_,diagnostics=scan(symbol,source,start,end)
                chosen=[s for s in signals if s['family'] in FAMILIES and s['cohort']=='qualified']
                old={c['signal']['id']:c for c in original['pilot']['cases'] if c['signal']['family'] in FAMILIES and c['signal']['cohort']=='qualified'}
                if set(s['id'] for s in chosen)!=set(old):raise AssertionError('Extended future changed prior signals')
                cases=[]
                for s in chosen:
                    before=old[s['id']]
                    if s!=before['signal']:raise AssertionError('Frozen signal geometry changed')
                    entry=entry_contract(s,fine,cutoff,ExecutionRules(**p['execution']))
                    if entry!=before['entry']:raise AssertionError('Extended future changed original entry')
                    paths={}
                    for model in MODELS:
                        for mode in MODES:
                            for h in HORIZONS:
                                key=f'{model}:{mode}:{h}'
                                paths[key]=before['paths'][key] if mode=='hard_stop' and h==40 else execute_path(s,entry,fine,timeline,cutoff,h,model,mode)
                    cases.append({**before,'paths':paths,'observations':{}})
                checks=audit(cases,start,end)
                if not checks['passed']:raise AssertionError(checks)
                pilot={'cases':cases,'timeline':timeline,'audit':checks,'diagnostics':diagnostics}
            else:pilot={'cases':[],'timeline':[],'unavailable':original['pilot']['unavailable']}
            marks=[b for b in fine if b.end>=start-86400]
            block={'planId':p['id'],'datasetId':d['id'],'symbol':symbol,'fold':fold,'pilot':pilot,'availability':original['availability'],
                   'originalBlockChecksum':original['checksum'],'originalSignalAndEntryEqualityVerified':True,
                   'marks':{'ends':[b.end for b in marks],'closes':[b.close for b in marks]}}
            block['checksum']=stable_id(block);write(path,block)
            result.append({'window':fold['name'],'cases':len(pilot['cases'])})
    return {'symbol':symbol,'windows':result}


def build(root,p,workers=2,progress=lambda v:None):
    checked(p)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for done in as_completed([pool.submit(_work,(str(root),p,s)) for s in p['symbols']]):progress(done.result())


def paired(cases,one,two):
    filled=[c for c in cases if c['entry']['status']=='filled']
    common=[c for c in filled if c['paths'][one]['status']=='closed' and c['paths'][two]['status']=='closed']
    deltas=[c['paths'][two]['netR']-c['paths'][one]['netR'] for c in common]
    return {'filled':len(filled),'commonComplete':len(common),'notCommonComplete':len(filled)-len(common),
            'firstMeanR':statistics.mean(c['paths'][one]['netR'] for c in common) if common else None,
            'secondMeanR':statistics.mean(c['paths'][two]['netR'] for c in common) if common else None,
            'meanDeltaR':statistics.mean(deltas) if deltas else None,
            'secondBetterPct':100*sum(v>1e-10 for v in deltas)/len(deltas) if deltas else None,
            'caseIdsHash':stable_id(sorted(c['id'] for c in common))}


def evaluate(root,p,progress=lambda v:None):
    from tools.verify_strategy_screen import verify_cash
    from tools.verify_robustness_study import verify_marks
    checked(p);root=Path(root);windows=[];all_cases=[];verified=0
    for fold in p['folds']['validation']:
        cases,contexts,period=load_fold(root,p,'validation',fold);all_cases+=cases;books={}
        for policy in p['policies']:
            values={}
            for mult in (1,2):
                value=ledger(cases,contexts,period,policy,cost_multiplier=mult)
                verify_cash(value,0.)
                verify_marks(value,contexts,period,{'spread_bps':5.*mult,'slippage_bps':5.*mult,'fee_per_order':0.},p['datasets']);verified+=1
                name='base' if mult==1 else 'doubleCosts';values[name]=compact(value)
                write(root/'ledgers'/fold['name']/(policy['id'].replace(':','_')+'-'+name+'.json.gz'),value)
            books[policy['id']]=values
        item={'fold':fold,'books':books};windows.append(item);write(root/'window-results'/(fold['name']+'.json'),item)
        progress({'window':fold['name'],'cases':len(cases),'ledgersVerified':verified})
    summaries={};comparisons={}
    from collections import Counter
    for family in FAMILIES:
        cs=[c for c in all_cases if c['signal']['family']==family];summaries[family]={};comparisons[family]={'trigger':{},'horizon':{}}
        for policy in policies(family):
            key=f"{policy['model']}:{policy['stopMode']}:{policy['horizon']}";ps=[c['paths'][key] for c in cs];closed=[v for v in ps if v['status']=='closed']
            summaries[family][key]={'signals':len(cs),'statuses':dict(Counter(v['status'] for v in ps)),
                'closed':len(closed),'meanNetR':statistics.mean(v['netR'] for v in closed) if closed else None,
                'winPct':100*sum(v['netR']>0 for v in closed)/len(closed) if closed else None,
                'worstNetR':min((v['netR'] for v in closed),default=None),
                'lossBeyondOneRPct':100*sum(v['netR']<-1.000001 for v in closed)/len(closed) if closed else None,
                'exitReasons':dict(Counter(v['reason'] for v in closed))}
        for model in MODELS:
            for h in HORIZONS:comparisons[family]['trigger'][f'{model}:{h}']=paired(cs,f'{model}:hard_stop:{h}',f'{model}:close_stop:{h}')
            for mode in MODES:comparisons[family]['horizon'][f'{model}:{mode}']=paired(cs,f'{model}:{mode}:40',f'{model}:{mode}:80')
    result={'planId':p['id'],'cases':len(all_cases),'summaries':summaries,'paired':comparisons,'windows':windows,
            'audit':{'cashAndValuationBooks':verified,'sourceSignalAndEntryPreserved':True,'providerCallsDuringResearch':0},
            'limitations':p['limitations'],'selection':p['selection']}
    write(root/'results.json',result);return result
