"""Post-test sensitivity diagnostics; never changes the frozen winner or its gate."""
from dataclasses import replace
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from datasets import read_dataset, source_bars
from fan_execution import entry_contract, ExecutionRules
from pilot_backtest import PilotSpec, execute_path
from screening_portfolio import matches, ledger, compact
from screening_extension import prepare
from strategy_screen import read, write, load_fold, load_task, task_path
from tools.verify_strategy_screen import verify_cash


def stress(root,output=None):
    root=Path(root);plan=read(root/'plan.json');selection_path=root/'selection.json';selection_before=selection_path.read_bytes()
    destination=Path(output) if output else root
    if output and destination.exists():raise ValueError('Choose a new diagnostic output folder; preserve previous results')
    policy=read(selection_path)['primary'];fold=plan['folds']['validation'][0]
    cases,contexts,period=load_fold(root,plan,'validation',fold)
    cases=[c for c in cases if matches(c,policy)]
    result={'planId':plan['id'],'policy':policy,'scope':'Post-test diagnostics on already opened data, not new validation or reselection',
            'leaveOneSymbolOut':[],'holding':[],'latency':[],'halves':[],'fixedFees':[]}
    for symbol in plan['symbols']:
        value=ledger([c for c in cases if c['symbol']!=symbol],contexts,period,policy)
        verify_cash(value,0.);write(destination/'stress'/('without-'+symbol+'.json.gz'),value)
        result['leaveOneSymbolOut'].append({'excluded':symbol,**compact(value)})
    spec=PilotSpec(start=fold['start'],end=fold['end'],outcome_end=fold['outcome_end'])
    _,start,end,cutoff=spec.bounds()
    fine_by_symbol={};timeline_by_symbol={}
    for symbol in plan['symbols']:
        d=read_dataset(plan['datasets'][symbol])
        fine_by_symbol[symbol]=[b for b in source_bars(d)['5m'] if b.time>=start and b.end<=cutoff]
        timeline_by_symbol[symbol]=load_task(task_path(root,'validation',symbol,fold),plan)['pilot']['timeline']
    trials=[('holding',h,300) for h in (20,30,40,50)]+[('latency',40,latency) for latency in (0,600,900)]
    for kind,horizon,latency in trials:
        adjusted=[]
        for c in cases:
            fine=fine_by_symbol[c['symbol']]
            r=replace(ExecutionRules(**c['entry']['rules']),latency_seconds=latency)
            e=entry_contract(c['signal'],fine,cutoff,r)
            p=execute_path(c['signal'],e,fine,timeline_by_symbol[c['symbol']],cutoff,horizon,policy['model'],'hard_stop')
            if horizon==40 and latency==300 and p!=c['paths'][f"{policy['model']}:hard_stop:40"]:
                raise AssertionError('Base path does not reproduce during stress')
            adjusted.append({**c,'entry':e,'paths':{f"{policy['model']}:hard_stop:{horizon}":p}})
        value=ledger(adjusted,contexts,period,{**policy,'horizon':horizon})
        verify_cash(value,0.);write(destination/'stress'/f'{kind}-{horizon}-{latency}.json.gz',value)
        result[kind].append({'horizon':horizon,'latencySeconds':latency,**compact(value)})
    middle=(start+end)//2
    from copy import deepcopy
    for fee in (1.,2.):
        fee_cases=deepcopy(cases)
        for c in fee_cases:c['entry']['rules']['fee_per_order']=fee
        value=ledger(fee_cases,contexts,period,policy)
        verify_cash(value,fee);write(destination/'stress'/f'fee-{fee}.json.gz',value)
        result['fixedFees'].append({'feePerOrderUSD':fee,**compact(value)})
    for name,lo,hi in (('first_half',start,middle),('second_half',middle+1,end)):
        value=ledger([c for c in cases if lo<=c['signal']['signalAt']<=hi],contexts,period,policy)
        verify_cash(value,0.);result['halves'].append({'name':name,'entryStart':lo,'entryEnd':hi,**compact(value)})
    if selection_path.read_bytes()!=selection_before:raise AssertionError('Stress changed selection')
    result['frozenSelectionUnchanged']=True;write(destination/'stress-summary.json',result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',required=True);parser.add_argument('--output');args=parser.parse_args()
    with patch('alpaca._request',side_effect=AssertionError('Offline stress only')) as request:
        result=stress(args.root,args.output);request.assert_not_called()
    print(json.dumps({'holding':[(v['horizon'],v['markedReturnPct']) for v in result['holding']],
                      'latency':[(v['latencySeconds'],v['markedReturnPct']) for v in result['latency']],
                      'leaveOneOut':[(v['excluded'],v['markedReturnPct']) for v in result['leaveOneSymbolOut']],
                      'halves':[(v['name'],v['markedReturnPct']) for v in result['halves']],
                      'fixedFees':[(v['feePerOrderUSD'],v['markedReturnPct']) for v in result['fixedFees']],
                      'frozenSelectionUnchanged':True},ensure_ascii=False))
