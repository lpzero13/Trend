"""Verify explained replay leaves every original entry/attempt unchanged offline."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from datasets import digest,read_dataset
from workbench_scanner import ExplainedReplay,engine_hash
from tools.complete_study_import import write


def verify(root,wait=False):
    root=Path(root).resolve();contract=json.loads((root/'study-contract.json').read_text('utf-8'))
    imports=json.loads((root/'imports.json').read_text('utf-8'))
    cutoff=json.loads((root/'import-contract.json').read_text('utf-8'))['endAt']
    fingerprint=engine_hash();counters=Counter();phases=Counter();candidates=[];deadline=time.monotonic()+1800
    with patch('alpaca._request',side_effect=AssertionError('Offline scanner verification')):
        for symbol,meta in sorted(imports.items()):
            if not meta.get('id'):continue
            data=read_dataset(meta['id'])
            for tf in ('4h','1D'):
                replay=ExplainedReplay(data,tf,'strict',cutoff);result=replay.run()
                p=root/'studies'/f'{symbol}-{tf}-strict.json'
                while not p.exists():
                    if not wait or time.monotonic()>deadline:raise ValueError('Study block not ready')
                    time.sleep(2)
                reference=json.loads(p.read_text('utf-8'))
                assert reference['contractHash']==digest(contract) and reference['datasetId']==data['id']
                assert reference['checksum']==digest({k:v for k,v in reference.items() if k!='checksum'})
                assert result['entries']==[{k:v for k,v in e.items() if k not in ('paths','intermediate')} for e in reference['entries']]
                for key in ('attempts','funnel','pending','sourceBars','expectedSourceBars','candidates','threeContactCandidates'):
                    assert result[key]==reference[key],key
                assert all('entryPrice' not in f and 'paths' not in f and 'netReturnPct' not in f for f in result['watchFacts'])
                facts={'datasetId':data['id'],'symbol':symbol,'timeframe':tf,'asOf':cutoff,
                    'lastSourceClose':replay.rows[-1].end,'facts':result['watchFacts'],'currentNear':result['currentNear'],
                    'engineHash':fingerprint,'studyContract':digest(contract),'meaning':'Known historical source-close facts, not new prospective signals or outcome-selected candidates.'}
                write(root/'candidates'/f'{symbol}-{tf}.json',facts)
                counters['blocks']+=1;counters['unchangedEntries']+=len(result['entries']);counters['facts']+=len(result['watchFacts'])
                phases.update(f['phase'] for f in result['watchFacts'])
                candidates.append({'symbol':symbol,'timeframe':tf,'count':len(result['currentNear']),'lastSourceClose':replay.rows[-1].end})
                print(json.dumps({'symbol':symbol,'tf':tf,'unchangedEntries':len(result['entries']),'facts':len(result['watchFacts'])}),flush=True)
    assert engine_hash()==fingerprint
    out={'passed':True,**dict(counters),'phases':dict(phases),'snapshots':candidates,'engineHash':fingerprint,'studyContract':digest(contract),
        'scope':'Exact equality of source replay entries, attempts, pending and funnel before outcomes; all source-close candidate exports offline. Not proof of profitable entries.'}
    write(root/'scanner-verification.json',out);print(json.dumps(out),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True);p.add_argument('--wait-study',action='store_true');a=p.parse_args();verify(a.root,a.wait_study)
