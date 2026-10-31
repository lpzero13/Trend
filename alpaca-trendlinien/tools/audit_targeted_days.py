"""Explicit bounded network check or publication of new immutable datasets."""
import argparse,json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from targeted_data_audit import check,publish
from strategy_run_lock import study_lock

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True);p.add_argument('--source');p.add_argument('--preview')
    p.add_argument('--asof',default='2026-10-29');p.add_argument('--phase',choices=('check','publish'),default='check');a=p.parse_args()
    with study_lock(a.root):
        if a.phase=='check':
            if not a.source or not a.preview:p.error('--source and --preview required for network check')
            result=check(a.root,a.source,a.preview,asof=a.asof)
        else:result=publish(a.root)
    print(json.dumps({k:v for k,v in result.items() if k not in ('datasets','changes')},ensure_ascii=False))
