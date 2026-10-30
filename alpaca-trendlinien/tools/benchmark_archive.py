"""Explicit five-stock live benchmark. No bulk universe import or broker operations.

Separate runtime directories prevent cache hits. One canonical rate-budget DB
is shared by both sequential methods and other local application processes.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import archive_state
import history_archive as old
import history_fast as fast
import provider_budget
from database import connection
from datasets import read_dataset
from settings import data_dir


def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    output = Path(sys.argv[1]).resolve()
    output.mkdir(parents=True,exist_ok=True)
    canonical = data_dir()
    with connection(): pass
    @contextmanager
    def budget_connection():
        db=sqlite3.connect(canonical/'research/jobs.sqlite3',timeout=20)
        try:
            db.execute('PRAGMA busy_timeout=20000');yield db;db.commit()
        except BaseException:db.rollback();raise
        finally:db.close()
    provider_budget.connection=budget_connection
    spec={'symbols':['AAPL','GS','KO','BNY','SNDK'],'start':'2016-01-01T00:00:00Z',
          'end':'2026-10-29T15:25:47+00:00','feed':'sip','adjustment':'split','workers':8,
          'vintage':'2026-10-29','universe':{'name':'Predeclared five-stock throughput benchmark',
          'sources':[{'url':'https://github.com/lpzero13/Trend','asOf':'2026-10-29'}],
          'selection':'AAPL high activity; GS financial; KO defensive; BNY renamed; SNDK short history. No outcome filter.'}}
    fast_only='--fast-only' in sys.argv
    results=json.loads((output/'results.json').read_text('utf-8')) if fast_only else {
        'spec':spec,'runs':{},'canonicalBudgetDir':str(canonical),'startedAt':datetime.now(timezone.utc).isoformat()}
    if fast_only:results['initialFastTrial']=results['runs']['fast']
    for name, creator, runner, getter, rate in (
        ('legacy',old.create,old.run,old.get,150),
        ('fast',fast.create,fast.run,archive_state.full,190)):
        if fast_only and name=='legacy':continue
        root=output/(name+('-final-data' if fast_only else '-data'))
        if root.exists():raise RuntimeError('Fresh benchmark root required: '+str(root))
        os.environ['TORI_DATA_DIR']=str(root);os.environ['TORI_API_REQUESTS_PER_MINUTE']=str(rate)
        job=creator(spec)
        attempts=[0];original=provider_budget.reserve
        def counted(now=None,limit=None):
            delay=original(now,limit)
            if delay<=0:attempts[0]+=1
            return delay
        provider_budget.reserve=counted
        started=time.perf_counter()
        runner(job['id'])
        elapsed=time.perf_counter()-started
        provider_budget.reserve=original
        full=getter(job['id'])
        if full['status']!='completed':raise RuntimeError('Incomplete benchmark: '+json.dumps(full))
        stocks={}
        for symbol,item in full['stocks'].items():
            ds=read_dataset(item['datasetId'])
            fine=ds['material']['bars']['5m']
            stocks[symbol]={'datasetId':item['datasetId'],'counts':item['counts'],
                            'first':fine[0]['time'],'lastClose':fine[-1]['end'],
                            'pages':sum(e.get('pages',0) for e in item['months'].values()) if name=='legacy' else item['downloadedPages'],
                            'coverage':item['coverage']}
        results['runs'][name]={'jobId':job['id'],'dataDir':str(root),'elapsedSeconds':elapsed,
                              'httpAttempts':attempts[0],'metrics':full.get('metrics',{}),'stocks':stocks,
                              'engineHash':full['engineHash']}
        (output/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
        print(json.dumps({'method':name,'elapsedSeconds':round(elapsed,2),'attempts':attempts[0]}),flush=True)
    # Identical material IDs prove every OHLCV and original frame matches; weekly
    # cache is audited separately by the standard verifier in acceptance.
    for symbol in spec['symbols']:
        a,b=(results['runs'][n]['stocks'][symbol] for n in ('legacy','fast'))
        if a['datasetId']!=b['datasetId']:raise RuntimeError('OHLCV identity mismatch: '+symbol)
    results['identicalDatasetIds']=True
    results['speedup']=results['runs']['legacy']['elapsedSeconds']/results['runs']['fast']['elapsedSeconds']
    (output/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps({'identicalDatasetIds':True,'speedup':results['speedup']}),flush=True)


if __name__=='__main__':main()
