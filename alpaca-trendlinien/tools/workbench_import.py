"""Separate historical SIP import, same declared universe and matched dates."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from alpaca import load_bars
from datasets import save_dataset, read_dataset
from lab_data import resample_regular, NORMALIZATION
from settings import data_dir
from storage import preflight
from tools.complete_study_import import SYMBOLS, END, write

START=datetime(2020,7,27,tzinfo=timezone.utc)
DAYS=(END.date()-START.date()).days


def one(symbol):
    began=time.monotonic()
    try:
        fine,meta=load_bars(symbol,'5m',history_days=DAYS,end=END,feed='sip',adjustment='split')
        if meta.get('warning') or meta.get('quality',{}).get('rejected'):
            return {'symbol':symbol,'error':'stale_or_invalid_provider_rows','quality':meta.get('quality')}
        frames,quality=resample_regular(fine)
        if any(len(b)<3 for b in frames.values()):
            return {'symbol':symbol,'error':'insufficient_complete_regular_sources'}
        inputs={tf:(b,{**meta,'normalization':NORMALIZATION,'rthQuality':quality,'count':len(b),
            'first':b[0].time,'last':b[-1].time,'lastClose':b[-1].end}) for tf,b in frames.items()}
        identity=save_dataset(symbol,inputs,feed='sip',adjustment='split',
            session='XNYS regular; open-anchored buckets; final 4h bucket may be shorter; execution 5m')
        return {'symbol':symbol,'id':identity,'counts':{tf:len(b) for tf,b in frames.items()},
            'first':{tf:b[0].time for tf,b in frames.items()},'last':{tf:b[-1].end for tf,b in frames.items()},
            'missingBuckets':quality['missingBuckets'],'seconds':round(time.monotonic()-began,2)}
    except Exception as e:
        return {'symbol':symbol,'error':str(e),'errorType':type(e).__name__}


def run(root):
    root=Path(root).resolve()
    plan=Path(__file__).resolve().parents[1]/'TORI-WERKBANK-PLAN.md'
    contract={'version':'workbench-sip-import-1','symbols':list(SYMBOLS),'feed':'sip','adjustment':'split',
        'fromAt':int(START.timestamp()),'endAt':int(END.timestamp()),'historyDays':DAYS,'dataDir':str(data_dir()),
        'normalization':NORMALIZATION,'planHash':hashlib.sha256(plan.read_bytes()).hexdigest()}
    cp,ip=root/'import-contract.json',root/'imports.json'
    if cp.exists() and json.loads(cp.read_text('utf-8'))!=contract:
        raise ValueError('Import contract changed; new directory required')
    preflight(history_days=DAYS*4,symbols=len(SYMBOLS))
    write(cp,contract)
    imports=json.loads(ip.read_text('utf-8')) if ip.exists() else {}
    pending=[]
    for s in SYMBOLS:
        if imports.get(s,{}).get('id'):
            d=read_dataset(imports[s]['id'])
            if d['material']['feed']!='sip':raise ValueError('Wrong feed')
        else:pending.append(s)
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(one,s):s for s in pending}
        for f in as_completed(futures):
            s=futures[f];imports[s]=f.result();write(ip,imports)
            print(json.dumps(imports[s]),flush=True)
    print(json.dumps({'done':True,'symbols':len(imports),'available':sum(bool(x.get('id')) for x in imports.values())}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True)
    run(p.parse_args().root)
