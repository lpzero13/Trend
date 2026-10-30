"""Offline JSON candidate scanner for Hermes; no orders or notifications."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from workbench_scanner import scan,journal

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset');p.add_argument('--stream',required=True)
    p.add_argument('--timeframe',choices=['4h','1D'],default='4h')
    p.add_argument('--cutoff',type=int,help='UTC Unix seconds')
    p.add_argument('--from-at',type=int,help='Immutable registration origin, UTC Unix seconds')
    p.add_argument('--mode',choices=['prospective','historical'],default='prospective')
    p.add_argument('--events',help='Optional validated point-in-time coverage/events JSON; absence remains unknown')
    p.add_argument('--journal',action='store_true',help='Read durable fact pages after a lost stdout response')
    p.add_argument('--limit',type=int,default=100);p.add_argument('--cursor')
    a=p.parse_args()
    if a.journal:result=journal(a.stream,a.limit,a.cursor)
    else:
        if not a.dataset or a.cutoff is None:p.error('--dataset and --cutoff required for scanning')
        events=json.loads(Path(a.events).read_text('utf-8')) if a.events else None
        result=scan(a.dataset,a.timeframe,a.cutoff,stream=a.stream,from_at=a.from_at,mode=a.mode,events=events)
    print(json.dumps(result,ensure_ascii=False,allow_nan=False))
