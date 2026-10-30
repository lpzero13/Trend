"""Frozen retest feature/control study on pinned SIP datasets; offline only."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from candidate_research import ResearchData,features,summarize,VERSION,SEED,HORIZONS,MODELS
from datasets import digest,read_dataset
from database import connection
from tools.complete_study_import import write
from tools.complete_study import engine_hashes
from workbench_reviews import put


def signature():
    app=Path(__file__).resolve().parents[1]
    return {**engine_hashes(),**{p:hashlib.sha256((app/p).read_bytes()).hexdigest() for p in
        ('candidate_research.py','tools/candidate_study.py','lab_metrics.py','requirements.txt')}}


def run(source,root):
    source,root=Path(source).resolve(),Path(root).resolve()
    source_contract=json.loads((source/'study-contract.json').read_text('utf-8'))
    verification=json.loads((source/'verification.json').read_text('utf-8'))
    imports=json.loads((source/'imports.json').read_text('utf-8'))
    end=json.loads((source/'import-contract.json').read_text('utf-8'))['endAt']
    if not verification['passed'] or verification['contractHash']!=digest(source_contract) or source_contract['engine']!=engine_hashes():raise ValueError('Verified unchanged source study required')
    plan=Path(__file__).resolve().parents[1]/'TORI-KANDIDATEN-PLAN.md'
    contract={'version':VERSION,'engine':signature(),'planHash':hashlib.sha256(plan.read_bytes()).hexdigest(),
        'sourceContract':digest(source_contract),'datasets':{s:v['id'] for s,v in imports.items() if v.get('id')},
        'feed':'sip','seed':SEED,'horizons':list(HORIZONS),'models':list(MODELS),'controls':5,'endAt':end,
        'meaning':'Known historical periods; no new independent holdout.'}
    cp=root/'contract.json'
    if cp.exists() and json.loads(cp.read_text('utf-8'))!=contract:raise ValueError('Contract changed; new output generation required')
    write(cp,contract);records=[]
    early=int(datetime(2023,12,31,23,59,tzinfo=timezone.utc).timestamp())
    with patch('alpaca._request',side_effect=AssertionError('Pinned offline study')):
        for symbol,identity in sorted(contract['datasets'].items()):
            destination=root/'stocks'/f'{symbol}.json'
            if destination.exists():
                result=json.loads(destination.read_text('utf-8'))
                if result['contractHash']!=digest(contract) or result['checksum']!=digest({k:v for k,v in result.items() if k!='checksum'}):raise ValueError('Changed cached research block')
            else:
                start=time.monotonic();data=read_dataset(identity)
                if data['material']['feed']!='sip':raise ValueError('SIP required')
                b=json.loads((source/'studies'/f'{symbol}-4h-strict.json').read_text('utf-8'))
                if b['checksum']!=digest({k:v for k,v in b.items() if k!='checksum'}):raise ValueError('Changed source block')
                originals={e['id']:e for e in b['entries'] if e['profile']=='age7' and e['family']=='retest'}
                entries=[{k:v for k,v in e.items() if k not in ('paths','intermediate')} for e in originals.values()]
                evaluators={True:ResearchData(data,early),False:ResearchData(data,end)}
                selections=[]
                for e in entries:
                    is_early=e['entryAt']<early;ev=evaluators[is_early]
                    controls=ev.controls(e,b['startAt'] if is_early else early+1,early if is_early else end)
                    selections.append({'entry':e,'features':features(e,ev.rows),'controlSelection':controls,
                        'phase':'2021-2023' if is_early else '2024-2026'})
                # This file has no future labels and exists before any outcome call.
                selection={'contractHash':digest(contract),'symbol':symbol,'datasetId':identity,'selections':selections}
                selection['checksum']=digest(selection);write(root/'selections'/f'{symbol}.json',selection)
                rows=[]
                for selected in selections:
                    e=selected['entry'];ev=evaluators[e['entryAt']<early]
                    controls=[{**c,'outcomes':{str(h):ev.outcome(c,h) for h in HORIZONS},
                        'naturalPaths':{m:ev.base.path(c,m) for m in MODELS}} for c in selected['controlSelection']['items']]
                    rows.append({'id':e['id'],'symbol':symbol,'datasetId':identity,'entryAt':e['entryAt'],
                        'entry':e,'phase':selected['phase'],'features':selected['features'],
                        'controlSelection':{k:v for k,v in selected['controlSelection'].items() if k!='items'},
                        'controls':controls,'outcomes':{str(h):ev.outcome(e,h) for h in HORIZONS},
                        'naturalPaths':{m:originals[e['id']]['paths'][m] for m in MODELS}})
                result={'contractHash':digest(contract),'selectionHash':selection['checksum'],'symbol':symbol,
                    'datasetId':identity,'records':rows,'seconds':time.monotonic()-start}
                result['checksum']=digest(result);write(destination,result)
            records.extend(result['records'])
            print(json.dumps({'symbol':symbol,'entries':len(result['records']),'seconds':round(result['seconds'],2)}),flush=True)
    result=summarize(records);result.update(contractHash=digest(contract),datasets=contract['datasets'])
    write(root/'summary.json',result)
    identity=digest(contract)[:32]
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        put(db,'cw:research:'+identity,{'id':identity,'contract':contract,'summary':result,'createdAt':int(time.time())})
        for r in records:put(db,'cw:record:'+identity+':'+r['id'],r)
    print(json.dumps({'done':True,'researchId':identity,'entries':len(records)}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True);p.add_argument('--root',required=True);a=p.parse_args();run(a.source,a.root)
