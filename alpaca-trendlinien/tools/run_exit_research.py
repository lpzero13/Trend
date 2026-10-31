"""Register or execute the bounded, fixed-entry trigger/horizon comparison."""
import argparse,json
from pathlib import Path
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from trigger_horizon_research import prepare,build,evaluate,checked,reuse_blocks
from strategy_screen import read
from strategy_run_lock import study_lock

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True);p.add_argument('--source');p.add_argument('--data-audit')
    p.add_argument('--reuse-run',help='Explicit new-plan import of archived identical scientific functions and paths')
    p.add_argument('--phase',choices=('prepare','build','evaluate','all'),default='prepare');p.add_argument('--workers',type=int,choices=(1,2,3),default=2);a=p.parse_args()
    with study_lock(a.root),patch('alpaca._request',side_effect=AssertionError('No provider requests in exit research')) as request:
        if a.phase in ('prepare','all'):
            if not a.source or not a.data_audit:p.error('--source and --data-audit required')
            plan=prepare(a.root,a.source,a.data_audit,reuse=a.reuse_run)
        else:plan=checked(read(Path(a.root)/'plan.json'))
        def progress(v):print(json.dumps(v,ensure_ascii=False),flush=True)
        progress({'planId':plan['id'],'symbols':len(plan['symbols']),'policies':len(plan['policies'])})
        if a.reuse_run:progress({'reusedBlocks':reuse_blocks(a.root,plan)})
        if a.phase in ('build','all'):build(a.root,plan,a.workers,progress)
        if a.phase in ('evaluate','all'):progress(evaluate(a.root,plan,progress)['audit'])
        request.assert_not_called()
