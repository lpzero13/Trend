"""Small transactional archive records; immutable course files stay in Parquet.

Uses the existing settings table without changing its schema. A checkpoint,
its reusable-cache reference and stock counters commit together, after fsync.
"""
import json
import re
import time
from database import connection
from datasets import digest
from models import DataError

PREFIX = 'archive2:'


def encode(value):
    return json.dumps(value, separators=(',', ':'), allow_nan=False)


def put(db, key, value):
    db.execute('INSERT OR REPLACE INTO settings VALUES(?,?)', (key, encode(value)))


def value(db, key, default=None):
    row = db.execute('SELECT value FROM settings WHERE key=?', (key,)).fetchone()
    return json.loads(row[0]) if row else default


def identity_check(identity):
    if not isinstance(identity, str) or not re.fullmatch('[a-f0-9]{24}', identity):
        raise DataError('Ungültige Archiv-ID.', 400)


def get(identity):
    identity_check(identity)
    with connection() as db:
        job = value(db, PREFIX+'job:'+identity)
    if job is None:
        raise DataError('Schneller Archivauftrag fehlt.', 404)
    return job


def exists(identity):
    identity_check(identity)
    with connection() as db:
        return value(db, PREFIX+'job:'+identity) is not None


def update(identity, **changes):
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        job = value(db, PREFIX+'job:'+identity)
        if job is None: raise DataError('Archivauftrag fehlt.', 404)
        job.update(changes, updatedAt=time.time())
        put(db, PREFIX+'job:'+identity, job)
    return job


def create(job):
    with connection() as db:
        put(db, PREFIX+'job:'+job['id'], job)
        for symbol in job['spec']['symbols']:
            put(db, PREFIX+'stock:'+job['id']+':'+symbol,
                {'status': 'pending', 'checkpointMonths': 0, 'stagingBytes': 0, 'downloadedPages': 0})


def stock(identity, symbol):
    with connection() as db:
        result = value(db, PREFIX+'stock:'+identity+':'+symbol)
    if result is None: raise DataError('Archivaktie fehlt.', 404)
    return result


def update_stock(identity, symbol, **changes):
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        key = PREFIX+'stock:'+identity+':'+symbol
        result = value(db, key)
        if result is None: raise DataError('Archivaktie fehlt.', 404)
        result.update(changes, updatedAt=time.time())
        put(db, key, result)
    return result


def increment_stock(identity, symbol, **increments):
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        key = PREFIX+'stock:'+identity+':'+symbol
        current = value(db,key)
        for name, amount in increments.items(): current[name]=current.get(name,0)+amount
        put(db,key,current)


def rows(db, prefix):
    return [(r[0][len(prefix):], json.loads(r[1])) for r in db.execute(
        'SELECT key,value FROM settings WHERE key GLOB ? ORDER BY key', (prefix+'*',))]


def refs(identity, symbol):
    with connection() as db:
        return dict(rows(db, PREFIX+'ref:'+identity+':'+symbol+':'))


def contract(spec, symbol):
    # A vintage is an explicit immutable acquisition batch, not a claim that
    # Alpaca offers historical corporate-action vintages. Different vintages
    # never silently reuse adjusted price history.
    return digest({'provider': 'Alpaca', 'symbol': symbol, 'feed': spec['feed'],
                   'adjustment': spec['adjustment'], 'normalization': spec['normalization'],
                   'asof': spec['asof'], 'vintage': spec['vintage']})


def cached(spec, symbol):
    with connection() as db:
        return dict(rows(db, PREFIX+'cache:'+contract(spec, symbol)+':'))


def checkpoint(identity, spec, symbol, month, entry, *, reused=False):
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        key = PREFIX+'ref:'+identity+':'+symbol+':'+month
        old = value(db, key)
        put(db, key, entry)
        put(db, PREFIX+'cache:'+contract(spec, symbol)+':'+month, entry)
        skey = PREFIX+'stock:'+identity+':'+symbol
        current = value(db, skey)
        current['checkpointMonths'] += old is None
        current['stagingBytes'] += entry.get('bytes', 0)-(old or {}).get('bytes', 0)
        current['reusedMonths'] = current.get('reusedMonths', 0)+(reused and old is None)
        current['updatedAt'] = time.time()
        put(db, skey, current)


def status(identity):
    job = get(identity)
    with connection() as db:
        stocks = dict(rows(db, PREFIX+'stock:'+identity+':'))
    return {k: v for k, v in job.items() if k != 'spec'} | {
        'total': len(job['spec']['symbols']), 'finished': sum(s['status']=='completed' for s in stocks.values()),
        'checkpointMonths': sum(s['checkpointMonths'] for s in stocks.values()),
        'stagingBytes': sum(s['stagingBytes'] for s in stocks.values()), 'stocks': stocks,
        'universe': job['spec']['universe'], 'start': job['spec']['start'], 'end': job['spec']['end']}


def full(identity):
    job = get(identity)
    job['stocks'] = status(identity)['stocks']
    for symbol, item in job['stocks'].items(): item['months'] = refs(identity, symbol)
    return job


def list_jobs(limit=30):
    with connection() as db:
        items = [v for _, v in rows(db, PREFIX+'job:')]
    return sorted(items, key=lambda v: v['createdAt'], reverse=True)[:limit]


def backup_chunks(db, root):
    from history_fast import check_entry
    entries = {}
    # Include references and reusable cache: both may outlive a running worker.
    for prefix in (PREFIX+'ref:', PREFIX+'cache:'):
        for _, entry in rows(db, prefix):
            if entry.get('path') and entry['path'] not in entries:
                check_entry(entry, root)
                entries[entry['path']] = entry
    return entries
