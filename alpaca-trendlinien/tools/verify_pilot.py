"""Repeat a saved engineering pilot offline and perturb only future candles."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from datasets import read_dataset, source_bars
from fan_execution import ExecutionRules
from fan_observer import WatchRules
from pilot_backtest import PilotSpec, code_digest, run, scan


def verify(saved):
    m=saved['manifest']
    if m['code']['digest']!=code_digest()['digest']:
        raise ValueError('Pilotcode geändert; neuen Lauf anlegen, alten Stand nicht unter neuer Engine bestätigen.')
    spec=PilotSpec(**m['spec']);execution=ExecutionRules(**m['execution'])
    with patch('alpaca._request',side_effect=AssertionError('Offline-Verifikation darf keinen Provider aufrufen.')) as provider:
        dataset=read_dataset(m['datasetId'])
        repeated=run(dataset,spec,execution)
        equal=all(saved[key]==repeated[key] for key in
                  ('manifest','runId','summary','diagnostics','audit','cases','journal','timeline'))
        warmup,start,end,_=spec.bounds()
        middle=(start+end)//2
        rows=[b for b in source_bars(dataset)['4h'] if b.time>=warmup and b.end<=m['outcomeCutoff']]
        changed=[replace(b,open=b.open*3,high=b.high*3,low=b.low*3,close=b.close*3)
                 if b.end>middle else b for b in rows]
        watch=WatchRules(arm_bars=spec.arm_bars,retest_bars=spec.retest_bars)
        shocked=scan(m['symbol'],changed,start,middle,watch=watch)[0]
        original=[c['signal'] for c in saved['cases'] if c['signal']['signalAt']<=middle]
        prefix_equal=original==shocked
        provider.assert_not_called()
    return {'passed':equal and prefix_equal and repeated['audit']['passed'],
            'identicalOfflineRepeat':equal,'futureShockPrefixEqual':prefix_equal,
            'prefixSignalsChecked':len(original),'casesChecked':len(saved['cases']),
            'pathsChecked':sum(len(c['paths']) for c in saved['cases']),
            'providerCalls':0,'repeatSeconds':repeated['elapsedSeconds']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--result',required=True)
    args=parser.parse_args()
    result=verify(json.loads(Path(args.result).read_text(encoding='utf-8')))
    print(json.dumps(result,ensure_ascii=False,allow_nan=False))
    sys.exit(0 if result['passed'] else 1)
