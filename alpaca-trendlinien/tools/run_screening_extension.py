"""Explicit follow-up after documented first-round failure; no web changes."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from screening_extension import prepare, development, validate


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True);p.add_argument('--base',required=True)
    p.add_argument('--phase',choices=('prepare','development','validation','all'),default='prepare');args=p.parse_args()
    plan=prepare(args.root,args.base)
    def progress(v):print(json.dumps(v,ensure_ascii=False),flush=True)
    progress({'planId':plan['id'],'phase':args.phase,'candidates':len(plan['policies'])})
    if args.phase in ('development','all'):
        selected=development(args.root,plan,progress);progress({'primary':selected['primary']})
    if args.phase in ('validation','all'):
        result=validate(args.root,plan,progress)
        progress({'opened':result['opened'],'passed':result.get('primaryPassed'),'primary':result.get('primary',{}).get('base')})


if __name__=='__main__':
    with patch('alpaca._request',side_effect=AssertionError('Follow-up stays offline')) as request:
        main();request.assert_not_called()
