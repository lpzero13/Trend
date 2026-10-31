"""Verify completed study evidence; no new market block or provider access."""
import argparse
from collections import Counter
import math
from pathlib import Path
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fan_geometry import stable_id
from screening_portfolio import ledger, compact
from strategy_screen import read, load_task, load_fold, select, engine_binding


def verify_cash(value,fee):
    # Independent arithmetic instead of importing the producer's cash_audit.
    changes=[];profit=0.
    for i,t in enumerate(value['trades']):
        if t['quantity']<=0 or t['quantity']!=int(t['quantity']):raise AssertionError('units')
        if t['plannedRiskUSD']>value['options']['risk_fraction']*t['equityAtEntry']+1e-7:raise AssertionError('risk')
        changes.append((t['openedAt'],1,i,-t['quantity']*t['entryFill']-fee,t['symbol']))
        if t['exitAt'] is not None:
            changes.append((t['exitAt'],0,i,t['quantity']*t['exitFill']-fee,t['symbol']))
            pnl=t['quantity']*(t['exitFill']-t['entryFill'])-2*fee
            if abs(pnl-t['netPnl'])>1e-7:raise AssertionError('fill P/L')
            profit+=pnl
    cash=value['initialCapital'];active={}
    for stamp,kind,i,amount,symbol in sorted(changes):
        if kind:
            if symbol in active.values():raise AssertionError('same symbol twice')
            active[i]=symbol
        else:active.pop(i,None)
        cash+=amount
        if cash < -1e-7 or len(active)>value['options']['max_positions']:raise AssertionError('cash/position cap')
    if abs(cash-value['cash'])>1e-7 or abs(profit-value['realizedNetPnl'])>1e-7:raise AssertionError('terminal accounting')


def verify(root):
    root=Path(root);p=read(root/'plan.json')
    if stable_id({k:v for k,v in p.items() if k!='id'})!=p['id']:raise AssertionError('plan checksum')
    if p['version'] in ('tori-screening-extension-1','tori-fixed-external-basket-1'):
        from screening_extension import binding
        if p['engine']!=binding():raise AssertionError('extension engine changed')
    elif p['engine']!=engine_binding():raise AssertionError('engine changed')
    selection=read(root/'selection.json')
    if stable_id({k:v for k,v in selection.items() if k!='id'})!=selection['id']:raise AssertionError('selection checksum')
    ledgers=[];results={policy['id']:[] for policy in p['policies']}
    for file in (root/'development-ledgers').glob('*.json.gz'):
        value=read(file);verify_cash(value,p['costs']['fee_per_order']);ledgers.append(value)
        results[value['policy']['id']].append(value)
    if p['version']=='tori-fixed-external-basket-1':
        original=read(Path(p['sourceStudyRoot'])/'selection.json')
        if original['id']!=p['sourceSelectionId'] or original['primary']!=selection['primary']:
            raise AssertionError('fixed external policy differs from the source selection')
    else:
        repeated=select(results,p['policies'])
        if repeated['primary']!=selection['primary'] or repeated['selectedByFamily']!=selection['selectedByFamily']:
            raise AssertionError('selection does not match development')
    task_count=0;case_count=0
    for phase,folds in p['folds'].items():
        for fold in folds:
            for symbol in p['symbols']:
                file=root/phase/(symbol+'-'+fold['name']+'.json.gz')
                if file.exists():
                    block=load_task(file,p);task_count+=1;case_count+=len(block['pilot']['cases'])
    for phase in ('validation','confirmation'):
        files=set((root/phase).glob('*ledger*.json.gz'))|set((root/phase).glob('*-stress.json.gz'))
        for file in files:
            value=read(file);verify_cash(value,p['costs']['fee_per_order']);ledgers.append(value)
        summary=root/(phase+'-summary.json')
        if not summary.exists():continue
        values=read(summary)
        for row in values['items']:
            if row['policy'] not in selection['selectedByFamily'].values():raise AssertionError('test selected new candidate')
        if selection['primary']:
            cases,contexts,period=load_fold(root,p,phase,p['folds'][phase][0])
            fresh=ledger(cases,contexts,period,selection['primary'])
            if compact(fresh)!=values['primary']['base']:raise AssertionError('later primary ledger not reproducible')
    for file in root.glob('combined*.json.gz'):
        value=read(file);verify_cash(value,p['costs']['fee_per_order']);ledgers.append(value)
    return {'passed':True,'planId':p['id'],'ledgersCashVerified':len(ledgers),'cacheBlocksVerified':task_count,
            'signalCasesAcrossSavedBlocks':case_count,'developmentSelectionOrInheritanceReproduced':True,'laterPrimaryLedgerReproduced':True,
            'providerCalls':0,'caseCountsIncludeRepeatedSignalsAcrossHoldingExperiments':True}


if __name__=='__main__':
    import json
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',required=True);args=parser.parse_args()
    with patch('alpaca._request',side_effect=AssertionError('Verifier must be offline')) as request:
        value=verify(args.root);request.assert_not_called()
    print(json.dumps(value,ensure_ascii=False))
