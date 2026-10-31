"""Explicit offline development -> frozen later test; no UI, imports or trades."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from strategy_screen import prepare, development, later_test, read


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True)
    p.add_argument('--phase',choices=('prepare','development','validation','confirmation','all'),default='prepare')
    args=p.parse_args();root=Path(args.root);plan=prepare(root)
    def progress(value):print(json.dumps(value,ensure_ascii=False),flush=True)
    progress({'planId':plan['id'],'phase':args.phase,'symbols':plan['symbols'],'candidates':len(plan['policies'])})
    if args.phase in ('development','all'):
        selection=development(root,plan,progress);progress({'primary':selection['primary'],'selectedByFamily':selection['selectedByFamily']})
    if args.phase in ('validation','all'):
        result=later_test(root,plan,'validation',progress)
        progress({'validationOpened':result['opened'],'passed':result.get('primaryPassed'),
                  'primary':result.get('primary',{}).get('base'),'reason':result.get('reason')})
    if args.phase in ('confirmation','all'):
        result=later_test(root,plan,'confirmation',progress)
        progress({'confirmationOpened':result['opened'],'passed':result.get('primaryPassed'),'reason':result.get('reason')})
    return 0


if __name__=='__main__':
    with patch('alpaca._request',side_effect=AssertionError('Study parent must remain offline')) as provider:
        status=main()
        provider.assert_not_called()
        print(json.dumps({'parentProviderCalls':0}),flush=True)
    sys.exit(status)
