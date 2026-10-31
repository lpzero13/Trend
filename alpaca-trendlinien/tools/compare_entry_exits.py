"""Compare all stored entry families and exits; no new providers or strategy selection."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from entry_exit_comparison import run
from strategy_run_lock import study_lock


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',required=True);parser.add_argument('--root',required=True);args=parser.parse_args()
    with study_lock(args.root),patch('alpaca._request',side_effect=AssertionError('Comparison must stay offline')) as request:
        result=run(args.root,args.source,lambda v:print(json.dumps(v,ensure_ascii=False),flush=True));request.assert_not_called()
    print(json.dumps(result['audit'],ensure_ascii=False))
