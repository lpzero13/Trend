"""Prioritize held-path gaps from finished books; preview only, no API or dataset writes."""
import argparse
from collections import defaultdict
from datetime import datetime
import json
from pathlib import Path
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from models import NY
from robustness_study import validate_plan, window_root
from strategy_screen import read, write


def plan_repairs(root):
    root=Path(root);p=validate_plan(read(root/'plan.json'));items={}
    for fold in p['folds']['validation']:
        dest=window_root(root,fold)
        for path in list((dest/'ledgers').glob('*.json.gz'))+list((dest/'validation').glob('control-ledger-*.json.gz')):
            value=read(path);halt=value.get('halt')
            if not halt:continue
            for symbol in halt['symbols']:
                day=datetime.fromtimestamp(halt['at'],NY).date().isoformat()
                key=(symbol,day);kind='primary_base' if path.name=='all-base.json.gz' else 'control' if path.name.startswith('control-ledger') else 'secondary_or_cost'
                item=items.setdefault(key,{'symbol':symbol,'dayET':day,'sourceDatasetId':p['datasets'][symbol],
                    'affectedBooks':0,'primaryBaseBooks':0,'controlBooks':0,'firstMissingAt':halt['at'],
                    'causes':set(),'windows':set()})
                item['affectedBooks']+=1;item['primaryBaseBooks']+=kind=='primary_base';item['controlBooks']+=kind=='control'
                item['firstMissingAt']=min(item['firstMissingAt'],halt['at']);item['causes'].add(halt['reason']);item['windows'].add(fold['name'])
    values=[]
    for item in items.values():
        item['causes']=sorted(item['causes']);item['windows']=sorted(item['windows'])
        item['firstMissingET']=datetime.fromtimestamp(item['firstMissingAt'],NY).isoformat();values.append(item)
    values.sort(key=lambda v:(-v['primaryBaseBooks'],-v['affectedBooks'],v['dayET'],v['symbol']))
    by_day=defaultdict(list)
    for item in values:by_day[item['dayET']].append(item['symbol'])
    return {'planId':p['id'],'previewOnly':True,'providerCalls':0,'datasetWrites':0,'items':values,
            'dates':[{'dayET':day,'symbols':sorted(symbols)} for day,symbols in sorted(by_day.items())],
            'nextSteps':['Inspect exact regular-session 5m bars and source metadata for these symbol/day pairs',
                         'Distinguish missing provider bars from verified no-trade intervals or exchange halts',
                         'If importing replacements, use same feed/adjustment and publish NEW immutable datasets; preserve old studies',
                         'Re-register fixed policy and controls before rerun; do not exclude failed trades based on future results'],
            'meaning':'Post-result data-quality triage, never a trading filter or permission to impute candles'}


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--root',required=True);a.add_argument('--output',required=True);args=a.parse_args()
    with patch('alpaca._request',side_effect=AssertionError('Repair planner must stay offline')) as request:
        result=plan_repairs(args.root);write(args.output,result);request.assert_not_called()
    print(json.dumps({'previewOnly':True,'symbolDays':len(result['items']),'dates':result['dates'],'providerCalls':0},ensure_ascii=False))
