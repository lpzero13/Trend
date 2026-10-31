"""Fixed-rule cross-asset transfer; not another parameter search or fresh time test."""
import argparse
from copy import deepcopy
from pathlib import Path
import json
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from history_archive import get
from fan_geometry import stable_id
from screening_extension import binding, validate
from screening_portfolio import ledger, compact
from strategy_screen import read, write, load_fold
from tools.verify_strategy_screen import verify_cash

SYMBOLS=('IBM','GS','MRK','CVX','PG','HON','MCD','VZ')


def prepare(root,source):
    root=Path(root);file=root/'plan.json'
    if file.exists():
        plan=read(file)
        if stable_id({k:v for k,v in plan.items() if k!='id'})!=plan['id'] or plan['engine']!=binding():raise ValueError('Changed fixed-basket plan')
        return plan
    source_plan=read(Path(source)/'plan.json');selection=read(Path(source)/'selection.json')
    if source_plan['engine']!=binding() or stable_id({k:v for k,v in selection.items() if k!='id'})!=selection['id']:
        raise ValueError('Changed source study')
    stocks=get('3e86a04aa09347caa2295b25')['stocks']
    if any(stocks.get(s,{}).get('status')!='completed' for s in SYMBOLS):raise ValueError('Predeclared stocks unavailable')
    policy=deepcopy(selection['primary'])
    p={**deepcopy(source_plan),'version':'tori-fixed-external-basket-1','symbols':list(SYMBOLS),
       'datasets':{s:stocks[s]['datasetId'] for s in SYMBOLS},'policies':[policy],
       'folds':{'validation':source_plan['folds']['validation']},'sourceStudyRoot':str(Path(source).resolve()),
       'sourceSelectionId':selection['id'],'purpose':'Fixed-rule transfer to additional stocks; same known time period'}
    p.pop('id',None);p['id']=stable_id(p);write(file,p)
    frozen={'planId':p['id'],'primary':policy,'selectedByFamily':{policy['family']:policy},
            'sourceSelectionId':selection['id'],'purpose':'Inherited fixed policy, not selected on new basket'}
    frozen['id']=stable_id(frozen);write(root/'selection.json',frozen);return p


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',required=True)
    parser.add_argument('--source',required=True);parser.add_argument('--phase',choices=('prepare','test'),default='prepare');args=parser.parse_args()
    p=prepare(args.root,args.source)
    def progress(v):print(json.dumps(v,ensure_ascii=False),flush=True)
    progress({'planId':p['id'],'symbols':p['symbols'],'purpose':p['purpose']})
    if args.phase=='test':
        result=validate(args.root,p,progress)
        source_plan=read(Path(args.source)/'plan.json');policy=read(Path(args.source)/'selection.json')['primary']
        one,contexts,period=load_fold(args.root,p,'validation',p['folds']['validation'][0])
        two,old_contexts,old_period=load_fold(args.source,source_plan,'validation',source_plan['folds']['validation'][0])
        if period!=old_period:raise ValueError('Different time windows')
        base=ledger(one+two,{**contexts,**old_contexts},period,policy)
        stress=ledger(one+two,{**contexts,**old_contexts},period,policy,cost_multiplier=2)
        verify_cash(base,0.);verify_cash(stress,0.)
        write(Path(args.root)/'combined-16-ledger.json.gz',base);write(Path(args.root)/'combined-16-stress.json.gz',stress)
        write(Path(args.root)/'combined-summary.json',{'base':compact(base),'doubleCosts':compact(stress),
              'purpose':'Same capital over combined 16 stocks; not selection between baskets'})
        progress({'additional8':result['primary']['base'],'additional8FullGate':result['primaryPassed'],
                  'combined16':compact(base),'combined16DoubleCosts':stress['markedReturnPct']})


if __name__=='__main__':
    with patch('alpaca._request',side_effect=AssertionError('Fixed-basket test stays offline')) as request:
        main();request.assert_not_called()
