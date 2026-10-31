"""Real-data candle-by-candle journal/restart/prefix verification; no provider calls."""
import argparse
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import sys
import subprocess
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from datasets import read_dataset, source_bars
from fan_study import timestamp
from pilot_backtest import scan
from screening_portfolio import matches
from robustness_study import POLICY
from signal_journal import initialize, advance, status
from strategy_screen import read, write


def verify(root,plan_path,symbol):
    root=Path(root)
    if root.exists():raise ValueError('Use a new verification folder; preserve prior journals')
    root.mkdir(parents=True)
    p=read(plan_path);did=p['datasets'][symbol];dataset=read_dataset(did)
    start=timestamp('2025-04-01');frames=source_bars(dataset)
    # Same 400-day warmup as the bounded pilot. Verify at least one actual candidate.
    from datetime import datetime,timedelta
    from models import NY
    warm=int((datetime.fromtimestamp(start,NY)-timedelta(days=400)).timestamp())
    rows=[b for b in frames['4h'] if b.time>=warm and b.end<=timestamp('2025-06-30',upper=True)]
    signals=scan(symbol,rows,start+1,rows[-1].end)[0]
    expected=[s for s in signals if matches({'signal':s},POLICY)]
    if not expected:raise AssertionError('Choose a predeclared verification stock with actual journal candidates')
    cutoff=expected[0]['signalAt'];closes=[b.end for b in rows if start<b.end<=cutoff]
    # Reader is still the real immutable dataset, hydrated once here for repeatable speed.
    with patch('signal_journal.read_dataset',return_value=dataset):
        initialize(root/'step.sqlite3',{symbol:did},start)
        prefix=None
        for _ in closes:
            advance(root/'step.sqlite3',step=True)
        stepped=status(root/'step.sqlite3');prefix=deepcopy(stepped['events'])
        initialize(root/'batch.sqlite3',{symbol:did},start)
        advance(root/'batch.sqlite3',as_of=cutoff)
        batched=status(root/'batch.sqlite3')
        if [e['payload'] for e in stepped['events']] != [e['payload'] for e in batched['events']]:raise AssertionError('step versus batch')
        if [e['payload']['signal'] for e in stepped['events']] != [s for s in expected if s['signalAt']<=cutoff]:raise AssertionError('scan/journal mismatch')
        again=advance(root/'step.sqlite3',as_of=cutoff)
        if again['eventsAdded'] or status(root/'step.sqlite3')['events']!=prefix:raise AssertionError('restart duplicates')
        # A real separate process dies while holding uncommitted changes.
        child="""import os,sqlite3,sys
db=sqlite3.connect(sys.argv[1],isolation_level=None)
db.execute('BEGIN IMMEDIATE')
db.execute('UPDATE contract SET cursor=1 WHERE id=1')
db.execute("INSERT INTO events(event_id,symbol,signal_at,observed_at,payload) VALUES('uncommitted-crash','X',1,1,'{}')")
os._exit(73)
"""
        crashed=subprocess.run([sys.executable,'-c',child,str(root/'step.sqlite3')],capture_output=True)
        if crashed.returncode!=73:raise AssertionError(crashed.stderr.decode('utf-8',errors='replace'))
        recovered=status(root/'step.sqlite3')
        if recovered['events']!=prefix or recovered['cursor']!=cutoff:raise AssertionError('hard crash left partial changes')
        # Mutate only a genuinely future candle, preserving all observed source bars.
        changed=deepcopy(dataset)
        future=next(b for b in changed['material']['bars']['4h'] if b['time']>cutoff)
        future.update(open=900.,high=1000.,low=1.,close=999.)
        with patch('signal_journal.read_dataset',return_value=changed):
            advance(root/'step.sqlite3',step=True)
        if status(root/'step.sqlite3')['events'][:len(prefix)]!=prefix:raise AssertionError('future rewrote frozen event')
    result={'passed':True,'symbol':symbol,'steps':len(closes),'observedCandidates':len(prefix),
            'batchMatchesSingleCandles':True,'restartDuplicateEvents':0,'hardProcessExitRollbackPassed':True,
            'originalSignalsFrozen':True,'futureShockCannotRewritePrefix':True,
            'mode':'historical replay, not prospective profitability evidence','providerCalls':0}
    write(root/'verification.json',result);return result


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--root',required=True);a.add_argument('--plan',required=True);a.add_argument('--symbol',default='AAPL');args=a.parse_args()
    with patch('alpaca._request',side_effect=AssertionError('Journal verification offline')) as request:
        result=verify(args.root,args.plan,args.symbol);request.assert_not_called()
    print(json.dumps(result,ensure_ascii=False))
