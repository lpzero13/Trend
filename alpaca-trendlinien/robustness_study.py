"""Fixed-candidate, manifest-driven offline robustness study. Never selects a winner."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import statistics
from unittest.mock import patch

from datasets import path_for, read_dataset, source_bars
from fan_execution import ExecutionRules
from fan_geometry import stable_id
from models import DataError
from pilot_backtest import PilotSpec, run
from robustness_quality import check_frames
from screening_extension import binding as prior_binding, controls
from screening_portfolio import ledger, compact, test_gate, OPTIONS
from strategy_screen import read, write, load_task, load_fold, task_path

VERSION = 'tori-fixed-robustness-2'
POLICY = {'id':'breakout:qualified:fixed:sma0:h40','family':'breakout','quality':'qualified',
          'model':'fixed','sma200':False,'horizon':40,'stopMode':'hard_stop'}
DEFAULT_FOLDS = [
    {'name':str(y),'start':f'{y}-01-01','end':f'{y}-12-31','outcome_end':f'{y+1}-03-31'}
    for y in (2018,2021,2023)
] + [{'name':'2025-2026','start':'2025-04-01','end':'2026-03-31','outcome_end':'2026-06-30'}]
PRIOR16 = ('AAPL','JPM','JNJ','XOM','KO','CAT','HD','NEE','IBM','GS','MRK','CVX','PG','HON','MCD','VZ')


def binding():
    root = Path(__file__).parent
    return {'prior':prior_binding(),'files':{n:hashlib.sha256((root/n).read_bytes()).hexdigest()
            for n in ('robustness_study.py','robustness_quality.py')}}


def validate_plan(plan):
    if stable_id({k:v for k,v in plan.items() if k != 'id'}) != plan['id'] or plan['engine'] != binding():
        raise DataError('Robustheitsplan oder Engine geändert; neuer Versuchsordner erforderlich.',409)
    return plan


def prepare(root, source, datasets, folds=None, *, cache_source=None):
    """Inputs are explicit dataset IDs, portable across hosts; no archive-job coupling."""
    root = Path(root)
    if (root/'plan.json').exists():
        p = validate_plan(read(root/'plan.json'))
        if p['datasets'] != dict(sorted(datasets.items())) or p['folds']['validation'] != (folds or DEFAULT_FOLDS):
            raise DataError('Andere Eingaben benötigen einen neuen Studienordner.',409)
        return p
    old = read(Path(source)/'plan.json'); selected = read(Path(source)/'selection.json')
    if old['engine'] != prior_binding() or selected['planId'] != old['id'] or stable_id({k:v for k,v in selected.items() if k!='id'}) != selected['id']:
        raise DataError('Ungeprüfte oder geänderte Quellenauswahl.',409)
    if selected['primary'] != POLICY:
        raise DataError('Diese Untersuchung prüft ausschließlich den vorher festgelegten 40-Tage-Kandidaten.',409)
    if not datasets or len(set(datasets.values())) != len(datasets):
        raise DataError('Eindeutige Symbol-/Dataset-Zuordnung erforderlich.',400)
    # Verify metadata now, full immutable content checksum in workers before use.
    for symbol, identity in datasets.items():
        m = read(path_for(identity))['material']
        if m['symbol'] != symbol or m['feed'] != 'sip' or m['adjustment'] != 'split':
            raise DataError('Dataset-Provenienz passt nicht zum Versuchsplan.',422)
    chosen_folds = deepcopy(folds or DEFAULT_FOLDS)
    if len({f['name'] for f in chosen_folds}) != len(chosen_folds):
        raise DataError('Doppelte Zeitfensternamen.',400)
    for f in chosen_folds:
        if not f['name'].replace('-','').isalnum():raise DataError('Ungültiger Zeitfenstername.',400)
        PilotSpec(start=f['start'],end=f['end'],outcome_end=f['outcome_end']).bounds()
    p = {'version':VERSION,'createdAt':datetime.now(timezone.utc).isoformat(),'datasets':dict(sorted(datasets.items())),
         'symbols':sorted(datasets),'folds':{'validation':chosen_folds},'policies':[deepcopy(POLICY)],
         'portfolio':deepcopy(OPTIONS),'controls':39,'seed':20261030,'engine':binding(),
         'sourceSelectionId':selected['id'],'sourcePlanId':old['id'],
         'costs':{'spread_bps':5.,'slippage_bps':5.,'fee_per_order':0.},
         'costScenarios':[{'name':'base','multiplier':1,'fee':0.},{'name':'double_cost','multiplier':2,'fee':0.},
                          {'name':'fee_1','multiplier':1,'fee':1.},{'name':'fee_2','multiplier':1,'fee':2.}],
         'cohorts':{'all':sorted(datasets),'previous16':[s for s in sorted(datasets) if s in PRIOR16],
                    'additional':[s for s in sorted(datasets) if s not in PRIOR16]},
         'acceptance':{'base':'>=10 trades, positive net and doubled costs, DD >=-10%, >=4 positive contributors, concentration <=50%',
                       'controls':'strictly above 90th percentile of 39 complete conditional controls in each window',
                       'allWindows':'All windows must pass; unavailable symbols and incomplete books remain visible',
                       'execution':'Historical whole-share price / split-factor reconciliation still required'},
         'limitations':['Present-day survivors; no delisted-universe claim','Historical windows may have been seen in earlier project work',
                        '2025-2026 partly consumed in prior studies; no pristine holdout claim',
                        'Separate reset-capital windows; do not compound or add returns',
                        'Split-adjusted prices, missing dividends/FX/interest; no exact historical whole-share execution claim',
                        'Fixed policy, no new parameter selection; controls exploratory, not corrected p-values']}
    if cache_source:
        old_cache = read(Path(cache_source)/'plan.json')
        if stable_id({k:v for k,v in old_cache.items() if k!='id'})!=old_cache['id'] or old_cache['engine']['prior']!=prior_binding():
            raise DataError('Cachequelle verwendet eine andere Signal-/Ausführungsengine.',409)
        if old_cache['datasets']!=p['datasets'] or old_cache['folds']!=p['folds'] or old_cache['policies']!=p['policies']:
            raise DataError('Cachequelle hat andere wissenschaftliche Eingaben.',409)
        p['reusedBuild']={'root':str(Path(cache_source).resolve()),'planId':old_cache['id'],
                         'reason':'New evaluation code for unavailable symbols; unchanged pilot signals/paths, old run preserved'}
    p['id'] = stable_id(p);write(root/'plan.json',p)
    frozen = {'planId':p['id'],'primary':deepcopy(POLICY),'selectedByFamily':{'breakout':deepcopy(POLICY)},
              'sourceSelectionId':selected['id'],'purpose':'Inherited fixed hypothesis; never selected on these results'}
    frozen['id'] = stable_id(frozen);write(root/'selection.json',frozen)
    return p


def reuse_blocks(root,plan):
    """Explicit audited import into a NEW plan; never resume old jobs with changed code."""
    validate_plan(plan)
    origin=Path(plan['reusedBuild']['root']);old=read(origin/'plan.json')
    if old['id']!=plan['reusedBuild']['planId'] or old['engine']['prior']!=prior_binding():raise DataError('Cachequelle geändert.',409)
    for name,checksum in old['engine']['files'].items():
        if hashlib.sha256((origin/'engine'/name).read_bytes()).hexdigest()!=checksum:raise DataError('Archivierter Quellcode geändert.',409)
    count=0
    for fold in plan['folds']['validation']:
        for symbol in plan['symbols']:
            source=task_path(window_root(origin,fold),'validation',symbol,fold)
            payload=deepcopy(load_task(source,old))
            if payload['datasetId']!=plan['datasets'][symbol] or payload['fold']!=fold:raise DataError('Cacheeingaben geändert.',409)
            pilot_code=payload['pilot'].get('manifest',{}).get('code')
            if payload['availability']=='available' and pilot_code!=plan['engine']['prior']['base']['pilot']:
                raise DataError('Pilotengine stimmt nicht überein.',409)
            dest=task_path(window_root(root,fold),'validation',symbol,fold)
            if dest.exists():load_task(dest,plan);continue
            provenance={'planId':old['id'],'checksum':payload['checksum']}
            payload.pop('checksum');payload.update(planId=plan['id'],reusedFrom=provenance)
            payload['checksum']=stable_id(payload);write(dest,payload);count+=1
    return count


def window_root(root, fold):return Path(root)/'windows'/fold['name']


def _symbol_task(task):
    root, plan, symbol = task
    validate_plan(plan)
    folders = [(f,task_path(window_root(root,f),'validation',symbol,f)) for f in plan['folds']['validation']]
    pending = [(f,p) for f,p in folders if not p.exists()]
    for _,p in folders:
        if p.exists():load_task(p,plan)
    if not pending:return {'symbol':symbol,'cached':True,'windows':len(folders)}
    with patch('alpaca._request',side_effect=AssertionError('Robustness study is offline')):
        dataset = read_dataset(plan['datasets'][symbol]);all_frames = source_bars(dataset)
        results = []
        for fold,path in pending:
            spec = PilotSpec(start=fold['start'],end=fold['end'],outcome_end=fold['outcome_end'],horizons=(40,),stop_modes=('hard_stop',))
            warm,start,end,cutoff = spec.bounds()
            frames = {tf:[b for b in rows if b.time >= warm and b.end <= cutoff] for tf,rows in all_frames.items()}
            from fan_study import schedule
            expected = list(schedule(start,end,'4h'))
            usable = (all(frames.get(tf) for tf in ('5m','4h','1D')) and expected
                      and frames['4h'][0].end <= start-320*86400
                      and frames['4h'][-1].end >= expected[-1][1]
                      and frames['5m'][-1].end >= expected[-1][1])
            quality = check_frames(frames,warm,cutoff)
            if not quality['passedStructural']:raise DataError(f'{symbol}/{fold["name"]}: strukturell fehlerhafte Daten.',422)
            if usable:
                # Existing engine unchanged. Full scan, all families retained for audit, no re-ranking.
                pilot = run(dataset,spec,ExecutionRules(capital=1_000_000.,risk_fraction=.01))
                if not pilot['audit']['passed']:raise AssertionError(pilot['audit'])
            else:
                pilot = {'cases':[],'timeline':[],'audit':{'passed':True},'manifest':{'spec':asdict(spec)},
                         'unavailable':'Insufficient warmup or entry-window coverage; not replaced or treated as no signal'}
            marks = [b for b in frames.get('5m',[]) if b.end >= start-86400]
            payload = {'planId':plan['id'],'symbol':symbol,'datasetId':dataset['id'],'fold':fold,'pilot':pilot,
                       'availability':'available' if usable else 'unavailable','quality':quality,
                       'marks':{'ends':[b.end for b in marks],'closes':[b.close for b in marks]}}
            payload['checksum'] = stable_id(payload);write(path,payload)
            results.append({'fold':fold['name'],'available':bool(usable),'cases':len(pilot['cases']),
                            'missingFineBars':quality['missingFineBars']})
    return {'symbol':symbol,'windows':results}


def build(root,plan,workers=2,progress=lambda v:None):
    validate_plan(plan)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_symbol_task,(str(root),plan,s)) for s in plan['symbols']]
        for f in as_completed(futures):progress(f.result())


def _cost_ledger(cases,contexts,period,scenario):
    if scenario['fee']:
        cases = deepcopy(cases)
        for c in cases:c['entry']['rules']['fee_per_order'] = scenario['fee']
    return ledger(cases,contexts,period,POLICY,cost_multiplier=scenario['multiplier'])


def evaluate(root,plan,progress=lambda v:None):
    from tools.verify_strategy_screen import verify_cash
    validate_plan(plan)
    selection_bytes = (Path(root)/'selection.json').read_bytes()
    frozen = read(Path(root)/'selection.json')
    if frozen['planId'] != plan['id'] or frozen['primary'] != POLICY or stable_id({k:v for k,v in frozen.items() if k!='id'}) != frozen['id']:
        raise DataError('Fixierte Strategie oder Auswahl geändert.',409)
    rows = []
    for fold in plan['folds']['validation']:
        dest = window_root(root,fold)
        # Resumable results, bound to immutable inputs and complete code digest.
        result_file = dest/'result.json'
        if result_file.exists():
            result = read(result_file)
            if result.get('planId') != plan['id'] or result.get('checksum') != stable_id({k:v for k,v in result.items() if k!='checksum'}):raise DataError('Ergebnis geändert.',409)
            rows.append(result);progress({'fold':fold['name'],'cachedResult':True});continue
        cases,contexts,period = load_fold(dest,plan,'validation',fold)
        availability = {s:load_task(task_path(dest,'validation',s,fold),plan)['availability'] for s in plan['symbols']}
        quality = {s:load_task(task_path(dest,'validation',s,fold),plan)['quality'] for s in plan['symbols']}
        cohorts = {}
        for name,symbols in plan['cohorts'].items():
            subset = [c for c in cases if c['symbol'] in symbols];values = {}
            for scenario in plan['costScenarios']:
                value = _cost_ledger(subset,contexts,period,scenario);verify_cash(value,scenario['fee'])
                write(dest/'ledgers'/f'{name}-{scenario["name"]}.json.gz',value);values[scenario['name']] = compact(value)
            cohorts[name] = {'symbols':symbols,'availableSymbols':[s for s in symbols if availability[s]=='available'],
                             'scenarios':values,'baseGate':test_gate(values['base'],values['double_cost'])}
        # No signal pool exists before an IPO or without warmup. These symbols
        # have zero desired entries and are explicitly unavailable, never replacements.
        control_plan = {**plan,'symbols':[s for s,a in availability.items() if a=='available'],
                        'folds':{'validation':[fold]}}
        control = controls(dest,control_plan,POLICY,cohorts['all']['scenarios']['base'])
        result = {'planId':plan['id'],'fold':fold,'availability':availability,'quality':quality,'cohorts':cohorts,'controls':control,
                  'statisticalScreenPassed':cohorts['all']['baseGate']['passed'] and control['aboveQ90'],
                  'operationallyApproved':False,'executionBlocker':'Historical split factors, real fees and dividends not reconciled'}
        result['checksum'] = stable_id(result);write(result_file,result);rows.append(result)
        progress({'fold':fold['name'],'all':cohorts['all']['scenarios']['base'],
                  'controlsQ90':control['q90ReturnPct'],'screenPassed':result['statisticalScreenPassed']})
    if (Path(root)/'selection.json').read_bytes() != selection_bytes:raise AssertionError('Selection changed')
    returns = [r['cohorts']['all']['scenarios']['base']['markedReturnPct'] for r in rows]
    result = {'planId':plan['id'],'policy':POLICY,'windows':[{'fold':r['fold']['name'],'returnPct':v,
              'screenPassed':r['statisticalScreenPassed'],'unavailableSymbols':[s for s,a in r['availability'].items() if a!='available']}
              for r,v in zip(rows,returns)],'positiveWindows':sum(v is not None and v>0 for v in returns),
              'meanResetWindowReturnPct':statistics.mean(returns) if all(v is not None for v in returns) else None,
              'allStatisticalScreensPassed':all(r['statisticalScreenPassed'] for r in rows),'operationallyApproved':False,
              'frozenSelectionUnchanged':True,'limitations':plan['limitations'],'providerCalls':0}
    write(Path(root)/'summary.json',result);return result
