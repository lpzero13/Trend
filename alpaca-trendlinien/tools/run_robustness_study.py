"""Prepare/run a fixed strategy on explicit local datasets; no imports or tuning."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from robustness_study import prepare, build, evaluate, validate_plan, reuse_blocks
from strategy_screen import read
from strategy_run_lock import study_lock


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True)
    parser.add_argument('--source',help='Completed 40-day source study; required for prepare')
    parser.add_argument('--datasets',help='JSON object mapping symbol to immutable local dataset ID')
    parser.add_argument('--reuse-build',help='Explicit import from a preserved old build into a new plan; unchanged pilot engine required')
    parser.add_argument('--phase',choices=('prepare','build','evaluate','all'),default='prepare')
    parser.add_argument('--workers',type=int,choices=(1,2,3,4),default=2)
    args = parser.parse_args()
    with study_lock(args.root):
        execute(args,parser)


def execute(args,parser):
    if args.phase in ('prepare','all'):
        if not args.source or not args.datasets:parser.error('--source and --datasets required for preparation')
        plan = prepare(args.root,args.source,read(args.datasets),cache_source=args.reuse_build)
    else:plan = validate_plan(read(Path(args.root)/'plan.json'))
    def progress(v):print(json.dumps(v,ensure_ascii=False),flush=True)
    progress({'planId':plan['id'],'symbols':len(plan['symbols']),'policy':plan['policies'][0],'phase':args.phase})
    if args.reuse_build:progress({'explicitlyReusedBlocks':reuse_blocks(args.root,plan)})
    if args.phase in ('build','all'):build(args.root,plan,args.workers,progress)
    if args.phase in ('evaluate','all'):progress(evaluate(args.root,plan,progress))


if __name__ == '__main__':
    with patch('alpaca._request',side_effect=AssertionError('Robustness CLI stays offline')) as request:
        main();request.assert_not_called()
