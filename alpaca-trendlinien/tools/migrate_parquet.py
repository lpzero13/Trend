"""Migrate only existing local datasets; never import market data or resume jobs."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from datasets import read_dataset
from parquet_store import migrate
from settings import data_dir


def run():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--apply',action='store_true',help='Convert existing JSON; keep legacy-json rollback copies')
    p.add_argument('--dataset',action='append',default=[],help='Limit to these existing dataset IDs')
    p.add_argument('--workers',type=int,default=1,choices=range(1,5),help='Local conversion processes (1–4), no provider calls')
    a=p.parse_args()
    ids=a.dataset or sorted(f.stem for f in (data_dir()/'datasets').glob('*.json'))
    if a.apply and a.workers>1:
        with ProcessPoolExecutor(max_workers=a.workers) as pool:
            for i,result in enumerate(pool.map(migrate,ids),1):
                print(json.dumps({'index':i,'total':len(ids),**result}),flush=True)
        return
    for i,identity in enumerate(ids,1):
        if a.apply:result=migrate(identity)
        else:
            read_dataset(identity)
            result={'id':identity,'status':'verified_preview','writes':False}
        print(json.dumps({'index':i,'total':len(ids),**result}),flush=True)


if __name__=='__main__':run()
