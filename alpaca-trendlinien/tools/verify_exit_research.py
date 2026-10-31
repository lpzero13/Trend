"""Source-signal equality, independent path arithmetic and cash verification."""
import argparse,json,math
from pathlib import Path
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from trigger_horizon_research import checked,FAMILIES,MODELS,MODES,HORIZONS,paired
from fan_geometry import stable_id
from robustness_study import window_root,validate_plan
from strategy_screen import read,write,load_task,task_path,load_fold
from tools.verify_strategy_screen import verify_cash
from tools.verify_robustness_study import verify_marks
from screening_portfolio import compact


def verify(root):
    root=Path(root);p=checked(read(root/'plan.json'));source=Path(p['sourceRoot']);sp=validate_plan(read(source/'plan.json'))
    if sp['id']!=p['sourcePlanId'] or sp['engine']!=p['sourceEngine']:raise AssertionError('changed source contract')
    result=read(root/'results.json');count=paths=blocks=books=0;all_cases=[];references=0;expected_entries=0
    for fold in p['folds']['validation']:
        oldfold=next(f for f in p['sourceFolds'] if f['name']==fold['name'])
        for symbol in p['symbols']:
            old=load_task(task_path(window_root(source,oldfold),'validation',symbol,oldfold),sp)
            new=load_task(task_path(root,'validation',symbol,fold),p);blocks+=1
            prior={c['id']:c for c in old['pilot']['cases'] if c['signal']['family'] in FAMILIES and c['signal']['cohort']=='qualified'}
            expected_entries+=len(prior)
            if new['originalBlockChecksum']!=old['checksum'] or new['datasetId']!=old['datasetId']:raise AssertionError('source block changed')
            if set(prior)!=set(c['id'] for c in new['pilot']['cases']):raise AssertionError('different entries')
            for case in new['pilot']['cases']:
                count+=1;before=prior[case['id']];e=case['entry']
                if case['signal']!=before['signal'] or e!=before['entry']:raise AssertionError('signal/entry changed')
                for model in MODELS:
                    if case['paths'][f'{model}:hard_stop:40']!=before['paths'][f'{model}:hard_stop:40']:raise AssertionError('reference path changed')
                for key,path in case['paths'].items():
                    paths+=1
                    model,mode,h=key.split(':')
                    if (path['model'],path['stopMode'],path['horizon'])!=(model,mode,int(h)):raise AssertionError('wrong exit axis')
                    if path['status']!='closed':continue
                    expected=(e['quantity']*(path['exitFill']-e['entryFill'])-2*e['rules']['fee_per_order'])/e['plannedRisk']
                    if abs(expected-path['netR'])>1e-8:raise AssertionError('path R arithmetic')
                    if 'closeDecision' in path:
                        d=path['closeDecision']
                        if not path['exitAt']>=d['effectiveAt']>=d['knownAt']+e['rules']['latency_seconds']:raise AssertionError('retroactive close exit')
        cases,contexts,period=load_fold(root,p,'validation',fold);all_cases+=cases
        w=next(w for w in result['windows'] if w['fold']['name']==fold['name'])
        for file in (root/'ledgers'/fold['name']).glob('*.json.gz'):
            v=read(file);mult=v['costMultiplier'];costs={'spread_bps':5.*mult,'slippage_bps':5.*mult,'fee_per_order':0.}
            verify_cash(v,0.);verify_marks(v,contexts,period,costs,p['datasets']);books+=1
            if compact(v)!=w['books'][v['policy']['id']]['base' if mult==1 else 'doubleCosts']:raise AssertionError('book summary differs')
        # Reproduce original 40-day hard books at their original phase-end.
        # Extending the observation clock must not change original returns.
        from screening_portfolio import ledger
        from pilot_backtest import PilotSpec
        original_cases,original_contexts,original_period=load_fold(window_root(source,oldfold),sp,'validation',oldfold)
        for policy in p['policies']:
            if policy['horizon']!=40 or policy['stopMode']!='hard_stop':continue
            a=ledger(original_cases,original_contexts,original_period,policy)
            b=w['books'][policy['id']]['base']
            for key in ('markedReturnPct','cash','max5mSampledDrawdownPct','accepted','closed','open'):
                if a[key] is None or b[key] is None:
                    if a[key]!=b[key]:raise AssertionError('reference availability changed')
                elif abs(a[key]-b[key])>1e-8:raise AssertionError('original horizon comparison changed')
            references+=1
    for family,comparisons in result['paired'].items():
        cs=[c for c in all_cases if c['signal']['family']==family and c['entry']['status']=='filled']
        for kind,rows in comparisons.items():
            for key,row in rows.items():
                model,axis=key.split(':')
                one,two=(f'{model}:hard_stop:{axis}',f'{model}:close_stop:{axis}') if kind=='trigger' else (f'{model}:{axis}:40',f'{model}:{axis}:80')
                common=[c for c in cs if c['paths'][one]['status']=='closed' and c['paths'][two]['status']=='closed']
                if len(common)!=row['commonComplete'] or stable_id(sorted(c['id'] for c in common))!=row['caseIdsHash']:raise AssertionError('paired membership')
                if common:
                    x=sum(c['paths'][one]['netR'] for c in common)/len(common);y=sum(c['paths'][two]['netR'] for c in common)/len(common)
                    if any(abs(a-b)>1e-9 for a,b in ((x,row['firstMeanR']),(y,row['secondMeanR']),(y-x,row['meanDeltaR']))):raise AssertionError('paired means')
    if books!=len(p['policies'])*len(p['folds']['validation'])*2 or count!=expected_entries or paths!=count*len(MODELS)*len(MODES)*len(HORIZONS):raise AssertionError('incomplete predefined matrix')
    out={'passed':True,'blocks':blocks,'entries':count,'paths':paths,'cashAnd5mValuationBooks':books,
         'originalHard40ComparisonsReproduced':references,'signalsAndEntriesExactlyPreserved':True,
         'closeExitCausalityVerified':True,'providerCallsDuringVerification':0}
    write(root/'verification.json',out);return out


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--root',required=True);args=a.parse_args()
    with patch('alpaca._request',side_effect=AssertionError('Verifier offline')) as request:
        v=verify(args.root);request.assert_not_called()
    print(json.dumps(v,ensure_ascii=False))
