"""Memory-bounded inputs to the unchanged descriptive study aggregators.

Raw geometry/timelines and stop-event lists remain in the verified stock files.
The statistics/CSV functions do not read them; discard those unused copies before
retaining cases across the population. No entry, exit or arithmetic rule changes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import event_case_study as events
import exit_followup as follow
from strategy_screen import read,write


def small_case(c):
    return {**{k:c[k] for k in ('id','symbol','window')},
        'signal':{k:c['signal'][k] for k in ('episodeId','family','cohort','signalAt')},
        'entry':c['entry'],
        'features':{k:c['features'][k] for k in ('stopDistancePct','stopDistanceATR4h') if k in c['features']},
        'paths':{m:{k:v for k,v in p.items() if k!='stopEvents'} for m,p in c['paths'].items()}}


def evaluate(kind,root,output=None,compare=False):
    root=Path(root);target=Path(output) if output else root
    if compare and target.resolve()==root.resolve():raise ValueError('Control evaluation requires a separate output directory')
    module=events if kind=='events' else follow
    p=module.checked(read(root/'plan.json'))
    if kind=='events':
        original=events.load_block
        def load(_output,plan,symbol):
            b=original(root,plan,symbol)
            return {'symbol':symbol,'cases':[small_case(c) for c in b['cases']],
                    'eligibility':b['eligibility'],'suppressed':b['suppressed']}
        with patch('event_case_study.load_block',side_effect=load):result=events.evaluate(target,p)
    else:
        sp=events.checked(read(Path(p['sourceRoot'])/'plan.json'))
        assert sp['id']==p['sourcePlanId']
        def load(_output,plan):
            cases=[];diagnostics={}
            for s in plan['symbols']:
                b=events.load_block(plan['sourceRoot'],sp,s);f=follow.load_followup(root,plan,s)
                assert f['sourceChecksum']==b['checksum'] and f['caseIds']==[c['id'] for c in b['cases']]
                for c in b['cases']:
                    cases.append(small_case({**c,'paths':{**c['paths'],**f['newPaths'][c['id']]}}))
                diagnostics.update(f['originalFanDiagnostics'])
            return cases,diagnostics
        with patch('exit_followup.load_cases',side_effect=load):result=follow.evaluate(target,p)
    proof={'planId':p['id'],'kind':kind,'cases':result['cases'],'discardedOnlyUnusedGeometry':True,
           'toolSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    if compare:
        assert result==read(root/'results.json'),'Reduced aggregation changed statistics'
        assert (target/'cases.csv').read_bytes()==(root/'cases.csv').read_bytes(),'Reduced aggregation changed flat CSV'
        proof['identicalBaselineStatisticsAndCsv']=True
    write(target/'evaluation-proof.json',proof)
    return proof


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('kind',choices=('events','followup'));ap.add_argument('root')
    ap.add_argument('--output');ap.add_argument('--compare',action='store_true');a=ap.parse_args()
    print(json.dumps(evaluate(a.kind,a.root,a.output,a.compare)),flush=True)
