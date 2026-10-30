"""One rolling Alpaca request budget across processes sharing TORI_DATA_DIR.

No credentials are stored. Other applications/data directories cannot share this
budget; retain headroom and respect provider throttling even with reservations.
"""
import json
import os
import time
from database import connection

KEY = 'provider:alpaca:budget:v1'


def budget():
    try:
        return max(1, min(200, int(os.environ.get('TORI_API_REQUESTS_PER_MINUTE', '150'))))
    except ValueError:
        return 150


def effective_budget(limit=None):
    if limit is None:return budget()
    requested=max(1,min(200,int(limit)))
    # An explicitly configured account ceiling also constrains fast callers.
    return min(requested,budget()) if os.environ.get('TORI_API_REQUESTS_PER_MINUTE') else requested


def reserve(now=None, limit=None):
    """Atomically reserve an attempt, or return the required delay (seconds)."""
    now = time.time() if now is None else now
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT value FROM settings WHERE key=?', (KEY,)).fetchone()
        state = json.loads(row[0]) if row else {}
        stamps = [t for t in state.get('attempts', []) if now-60 < t]
        delay = max(0, state.get('cooldown', 0)-now)
        allowed = effective_budget(limit)
        if len(stamps) >= allowed:
            delay = max(delay, min(stamps)+60-now)
        if delay <= 0:
            stamps.append(now)
            state.update(attempts=stamps)
            db.execute('INSERT OR REPLACE INTO settings VALUES(?,?)', (KEY, json.dumps(state)))
        return max(0, delay)


def wait(limit=None, interrupted=None):
    while True:
        if interrupted and interrupted(): raise InterruptedError()
        delay = reserve(limit=limit)
        if delay <= 0:
            return
        time.sleep(min(.25, max(.05, delay)))


def cooldown(seconds):
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT value FROM settings WHERE key=?', (KEY,)).fetchone()
        state = json.loads(row[0]) if row else {}
        state['cooldown'] = max(state.get('cooldown', 0), time.time()+max(1, min(300, seconds)))
        db.execute('INSERT OR REPLACE INTO settings VALUES(?,?)', (KEY, json.dumps(state)))
