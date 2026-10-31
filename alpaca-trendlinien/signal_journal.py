"""Transactional closed-candle signal journal; no fills, orders or notifications.

Replays and prospective watches are explicitly separate. Inputs are immutable
local datasets; append-only 4h revisions are verified before cursor advancement.
"""
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
import time

from datasets import data_kind, read_dataset, source_bars
from fan_geometry import stable_id
from lab_data import require_convention
from models import DataError, NY
from pilot_backtest import code_digest, scan
from robustness_study import POLICY
from screening_portfolio import matches
from settings import data_dir

VERSION = 'tori-candle-journal-1'


def state_path(name):
    if not isinstance(name,str) or not name or len(name)>80 or not all(c.isalnum() or c in '-_' for c in name):
        raise DataError('Journalname: nur Buchstaben, Zahlen, Bindestrich und Unterstrich.',400)
    return data_dir()/'signal-journals'/(name+'.sqlite3')


def connection(path):
    path = Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    db = sqlite3.connect(path,timeout=30,isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA synchronous=FULL')
    return db


def binding():
    import hashlib
    return {'pilot':code_digest(),'files':{n:hashlib.sha256((Path(__file__).parent/n).read_bytes()).hexdigest()
            for n in ('signal_journal.py','screening_portfolio.py')},'policy':POLICY}


def _rows(dataset,warm,cutoff):
    require_convention(dataset)
    m = dataset['material']
    if data_kind(dataset) != 'market' or m['feed']!='sip' or m['adjustment']!='split':
        raise DataError('Signaljournal benötigt echte normalisierte SIP/split-Daten.',422)
    return [b for b in source_bars(dataset)['4h'] if b.time>=warm and b.end<=cutoff]


def _fingerprint(rows):return stable_id([asdict(b) for b in rows])


def initialize(path,datasets,start,*,mode='replay',now=None):
    now = int(time.time()) if now is None else now
    if mode not in ('replay','prospective') or type(start) is not int or start<=0 or not datasets:
        raise DataError('Journalmodus, Startzeit und Dataset-Zuordnung erforderlich.',400)
    if start>now or mode=='prospective' and start<now-300:
        raise DataError('Prospektiver Start muss jetzt liegen; historische Starts sind Replay.',400)
    warm = int((datetime.fromtimestamp(start,NY)-timedelta(days=400)).timestamp())
    identity = {'version':VERSION,'mode':mode,'startAt':start,'warmupFrom':warm,
                'datasets':dict(sorted(datasets.items())),'engine':binding(),
                'meaning':'Signal observation only; not a fill, recommendation, portfolio or profitability proof'}
    identity['id'] = stable_id(identity)
    cursors = []
    for symbol,did in sorted(datasets.items()):
        dataset = read_dataset(did)
        if dataset['material']['symbol']!=symbol:raise DataError('Symbol passt nicht zum Dataset.',422)
        rows = _rows(dataset,warm,start)
        if not rows or rows[0].end>start-320*86400:raise DataError('Zu wenig Journal-Vorgeschichte.',422)
        cursors.append((symbol,did,start,_fingerprint(rows),rows[-1].end))
    db = connection(path)
    try:
        db.execute('BEGIN IMMEDIATE')
        existing = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contract'").fetchone()
        if existing:raise DataError('Journal existiert bereits; neues Journal anlegen.',409)
        db.execute('CREATE TABLE contract (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL, cursor INTEGER NOT NULL, heartbeat REAL NOT NULL)')
        db.execute('CREATE TABLE cursors (symbol TEXT PRIMARY KEY, dataset_id TEXT NOT NULL, through_at INTEGER NOT NULL, prefix_hash TEXT NOT NULL, data_last_close INTEGER NOT NULL)')
        db.execute('CREATE TABLE events (seq INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT UNIQUE NOT NULL, symbol TEXT NOT NULL, signal_at INTEGER NOT NULL, observed_at REAL NOT NULL, payload TEXT NOT NULL)')
        db.execute('CREATE INDEX event_time ON events(signal_at,seq)')
        db.execute('PRAGMA user_version=1')
        db.execute('INSERT INTO contract VALUES(1,?,?,?)',(json.dumps(identity,ensure_ascii=False),start,now))
        db.executemany('INSERT INTO cursors VALUES(?,?,?,?,?)',cursors)
        db.commit()
    except Exception:
        db.rollback();raise
    finally:db.close()


def dataset_references(path):
    """Read-only backup/cleanup integration; old engine versions remain archivable."""
    from contextlib import closing
    path=Path(path).resolve()
    with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
        db.execute('BEGIN')
        if db.execute('PRAGMA user_version').fetchone()[0]!=1 or db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
            raise ValueError('Unknown or broken journal schema')
        raw=db.execute('SELECT payload FROM contract WHERE id=1').fetchone()
        p=json.loads(raw[0])
        if stable_id({k:v for k,v in p.items() if k!='id'})!=p['id']:raise ValueError('Changed journal contract')
        refs=set(p['datasets'].values())
        refs.update(row[0] for row in db.execute('SELECT dataset_id FROM cursors'))
        for row in db.execute('SELECT payload FROM events'):
            refs.add(json.loads(row[0])['datasetId'])
        return refs
    return {'journalId':identity['id'],'mode':mode,'cursor':start,'eventsAdded':0,'symbols':len(datasets)}


def advance(path,*,datasets=None,as_of=None,step=False,now=None):
    now = int(time.time()) if now is None else now
    if (as_of is None)==(not step):raise DataError('Genau --asof oder --step angeben.',400)
    if not Path(path).is_file():raise DataError('Signaljournal fehlt.',404)
    db = connection(path)
    try:
        db.execute('BEGIN IMMEDIATE')
        stored = db.execute('SELECT * FROM contract WHERE id=1').fetchone()
        p = json.loads(stored['payload']);cursor = stored['cursor']
        if p['engine'] != binding() or stable_id({k:v for k,v in p.items() if k!='id'})!=p['id']:
            raise DataError('Journalcode geändert; altes Journal bleibt erhalten, neues Journal erforderlich.',409)
        checkpoints = db.execute('SELECT * FROM cursors ORDER BY symbol').fetchall()
        ids = datasets or {c['symbol']:c['dataset_id'] for c in checkpoints}
        if set(ids)!=set(p['datasets']):raise DataError('Journaluniversum darf sich nicht ändern.',409)
        prepared = {};next_closes = []
        for c in checkpoints:
            dataset = read_dataset(ids[c['symbol']])
            if dataset['material']['symbol'] != c['symbol']:raise DataError('Symbol/Dataset stimmt nicht überein.',422)
            rows = _rows(dataset,p['warmupFrom'],now)
            before = [b for b in rows if b.end<=cursor]
            if c['through_at'] != cursor or _fingerprint(before)!=c['prefix_hash']:
                raise DataError('Bereits beobachtete 4h-Historie geändert; keine stille Neuberechnung.',409)
            prepared[c['symbol']] = rows
            later = [b.end for b in rows if b.end>cursor]
            if later:next_closes.append(later[0])
        cutoff = min(next_closes) if step and next_closes else cursor if step else as_of
        if type(cutoff) is not int or cutoff<cursor or cutoff>now:
            raise DataError('Journal nur vorwärts und bis zu abgeschlossenen Zeitpunkten.',400)
        if cutoff==cursor:
            db.commit();return {'journalId':p['id'],'mode':p['mode'],'cursor':cursor,'eventsAdded':0,'noNewCandle':True}
        # Never checkpoint beyond a lagging input and silently lose its later arrivals.
        if any(not rows or rows[-1].end<cutoff for rows in prepared.values()):
            raise DataError('Mindestens ein Dataset noch nicht bis zum gewünschten Schluss aktualisiert.',422)
        added = 0
        for symbol,rows in prepared.items():
            prefix = [b for b in rows if b.end<=cutoff]
            signals,_,_,diagnostics = scan(symbol,prefix,p['startAt']+1,cutoff)
            for signal in signals:
                if signal['signalAt']<=cursor or not matches({'signal':signal},POLICY):continue
                if signal.get('knownAt',signal['signalAt'])>signal['signalAt']:raise AssertionError('Future signal')
                payload = {'signal':signal,'policy':POLICY,'datasetId':ids[symbol],
                           'status':'candidate' if signal.get('validRisk') else 'rejected_invalid_safety',
                           'mode':p['mode'],'sourceTimeframe':'4h','linesFrozenAt':signal['signalAt'],
                           'meaning':'Observed signal; actual next-open fill and portfolio acceptance not evaluated'}
                eid = stable_id([p['id'],symbol,signal['id']])
                db.execute('INSERT INTO events(event_id,symbol,signal_at,observed_at,payload) VALUES(?,?,?,?,?)',
                           (eid,symbol,signal['signalAt'],now,json.dumps(payload,ensure_ascii=False,allow_nan=False)))
                added += 1
            db.execute('UPDATE cursors SET dataset_id=?,through_at=?,prefix_hash=?,data_last_close=? WHERE symbol=?',
                       (ids[symbol],cutoff,_fingerprint(prefix),prefix[-1].end,symbol))
        db.execute('UPDATE contract SET cursor=?,heartbeat=? WHERE id=1',(cutoff,now));db.commit()
        return {'journalId':p['id'],'mode':p['mode'],'cursor':cutoff,'eventsAdded':added,'symbols':len(prepared)}
    except Exception:
        db.rollback();raise
    finally:db.close()


def status(path,*,after=0,limit=100,upper_seq=None,now=None):
    if type(after) is not int or after<0 or type(limit) is not int or not 1<=limit<=1000:
        raise DataError('Ungültige Journalseite.',400)
    now = time.time() if now is None else now
    if not Path(path).is_file():raise DataError('Signaljournal fehlt.',404)
    db = connection(path)
    try:
        db.execute('BEGIN')
        c = db.execute('SELECT * FROM contract WHERE id=1').fetchone();p = json.loads(c['payload'])
        # Capture a stable upper bound; callers retain upperSeq while paging an active journal.
        upper = db.execute('SELECT COALESCE(MAX(seq),0) FROM events').fetchone()[0]
        if upper_seq is not None:
            if type(upper_seq) is not int or upper_seq<0 or upper_seq>upper:raise DataError('Ungültige Journalobergrenze.',400)
            upper = upper_seq
        events = db.execute('SELECT * FROM events WHERE seq>? AND seq<=? ORDER BY seq LIMIT ?', (after,upper,limit)).fetchall()
        sources = [dict(row) for row in db.execute('SELECT symbol,dataset_id,data_last_close FROM cursors ORDER BY symbol')]
        return {'journalId':p['id'],'mode':p['mode'],'cursor':c['cursor'],'heartbeatAgeSeconds':max(0,now-c['heartbeat']),
                'engineMatches':p['engine']==binding(),'upperSeq':upper,'nextAfter':events[-1]['seq'] if events else after,
                'sources':sources,'hasMore':bool(events and events[-1]['seq']<upper),
                'events':[dict(e) | {'payload':json.loads(e['payload'])} for e in events],
                'meaning':p['meaning'],'daemonInstalled':False,'providerCalls':0}
    finally:db.close()
