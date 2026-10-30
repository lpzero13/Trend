"""Resumable, date-oriented SIP history collector; no orders and no JSON bar cache.

Monthly 5m checkpoints are immutable Parquet/Zstd. Only one stock is assembled
in memory for publishing the existing 5m/1h/4h/1D dataset plus weekly cache.
"""
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import csv
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import time
import threading
import uuid

import alpaca
from database import connection
from datasets import digest, save_dataset, read_dataset
from lab_data import resample_regular, session_bounds, NORMALIZATION
from models import Bar, DataError, NY
from parquet_store import checksum, connect, FIELDS
from settings import data_dir
from storage import preflight

UTC = timezone.utc
VERSION = 'tori-history-archive-1'
PREFIX = 'archive:job:'


def code_hash():
    # Bind normalization and provider parsing as well as collector code.
    names = ('history_archive.py', 'alpaca.py', 'lab_data.py', 'market_calendar.py', 'parquet_store.py')
    return hashlib.sha256(b''.join((Path(__file__).parent/n).read_bytes() for n in names)).hexdigest()


def stamp(value):
    date = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if date.tzinfo is None:
        raise DataError('Archivdatum braucht eine Zeitzone.', 400)
    return date.astimezone(UTC).replace(microsecond=0)


def months(start, end):
    while start < end:
        following = (start.replace(day=28)+timedelta(days=4)).replace(day=1, hour=0, minute=0, second=0)
        finish = min(following, end)
        yield start, finish
        start = finish


def write_job(job):
    job['updatedAt'] = time.time()
    with connection() as db:
        db.execute('INSERT OR REPLACE INTO settings VALUES(?,?)', (PREFIX+job['id'], json.dumps(job, allow_nan=False)))


def get(identity):
    if not re.fullmatch(r'[a-f0-9]{24}', identity):
        raise DataError('Ungültige Archiv-ID.', 400)
    with connection() as db:
        row = db.execute('SELECT value FROM settings WHERE key=?', (PREFIX+identity,)).fetchone()
    if not row:
        raise DataError('Archivauftrag fehlt.', 404)
    return json.loads(row[0])


def create(spec):
    symbols = spec.get('symbols', [])
    if (not isinstance(symbols, list) or not 1 <= len(symbols) <= 1000 or
            any(not isinstance(s, str) or not re.fullmatch(r'[A-Z][A-Z0-9./-]{0,29}', s) for s in symbols) or
            len(set(symbols)) != len(symbols)):
        raise DataError('Archiv erwartet 1 bis 1000 eindeutige US-Symbole.', 400)
    start = stamp(spec.get('start', '2016-01-01T00:00:00Z'))
    end = stamp(spec['end']) if spec.get('end') else datetime.now(UTC).replace(microsecond=0)-timedelta(minutes=16)
    if start < datetime(2016, 1, 1, tzinfo=UTC) or start >= end or end > datetime.now(UTC)-timedelta(minutes=15):
        raise DataError('Zeitraum: ab 2016, Ende mindestens 15 Minuten alt.', 400)
    if spec.get('feed', 'sip') not in ('sip', 'iex') or spec.get('adjustment', 'split') not in ('split', 'raw', 'all'):
        raise DataError('Unbekannter Feed oder Bereinigung.', 400)
    if not isinstance(spec.get('universe'), dict) or not spec['universe'].get('sources'):
        raise DataError('Eingefrorene Universumsquelle mit Datum erforderlich.', 400)
    preflight(history_days=(end-start).days, symbols=len(symbols))
    config = {**spec, 'symbols': symbols, 'start': start.isoformat(), 'end': end.isoformat(),
              'feed': spec.get('feed', 'sip'), 'adjustment': spec.get('adjustment', 'split'),
              'normalization': NORMALIZATION, 'version': VERSION}
    job = {'id': uuid.uuid4().hex[:24], 'createdAt': time.time(), 'status': 'pending',
           'spec': config, 'engineHash': code_hash(), 'stocks': {}, 'phase': 'pending', 'requests': 0}
    write_job(job)
    return job


@contextmanager
def archive_lock():
    folder = data_dir()/'research'
    folder.mkdir(parents=True, exist_ok=True)
    with (folder/'history-archive.lock').open('a+b') as stream:
        stream.seek(0); stream.write(b'0'); stream.flush(); stream.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise DataError('Ein Archivsammler arbeitet bereits in diesem Datenpfad.', 409) from None
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def chunk_path(root, name):
    if not isinstance(name, str) or not re.fullmatch(r'imports/chunks/[a-f0-9]{64}\.parquet', name):
        raise DataError('Ungültiger Archivblockpfad.', 409)
    path = root/name
    if any(p.is_symlink() for p in (path, path.parent, path.parent.parent)):
        raise DataError('Archivblock darf kein Link sein.', 409)
    return path


def read_chunk(entry, root=None):
    root = root or data_dir()
    if entry['count'] == 0:
        if entry.get('path'):
            raise DataError('Widersprüchlicher leerer Archivblock.', 409)
        return []
    path = chunk_path(root, entry['path'])
    if not path.is_file() or path.stat().st_size != entry['bytes'] or checksum(path) != entry['sha256']:
        raise DataError('Archivblock fehlt oder ist beschädigt; keine stille Wiederverwendung.', 409)
    with connect() as con:
        rows = con.execute('SELECT * FROM read_parquet(?) ORDER BY "time"', [str(path)]).fetchall()
    if len(rows) != entry['count']:
        raise DataError('Archivblock hat eine falsche Zeilenzahl.', 409)
    return [Bar(*row) for row in rows]


def write_chunk(bars):
    if not bars:
        return {'count': 0}
    folder = data_dir()/'imports/chunks'
    folder.mkdir(parents=True, exist_ok=True)
    temporary = folder/(uuid.uuid4().hex+'.tmp')
    csv_path = temporary.with_suffix('.csv')
    try:
        with csv_path.open('w', newline='', encoding='utf-8') as out:
            csv.writer(out).writerows(tuple(asdict(b).values()) for b in bars)
        with connect() as con:
            columns = {'time': 'BIGINT', 'end': 'BIGINT', **{k: 'DOUBLE' for k in FIELDS[2:]}}
            con.execute("COPY (SELECT * FROM read_csv(?,header=false,columns=?)) TO ? (FORMAT PARQUET,COMPRESSION ZSTD,COMPRESSION_LEVEL 3)",
                        [str(csv_path), columns, str(temporary)])
        with temporary.open('r+b') as stream:
            os.fsync(stream.fileno())
        sha = checksum(temporary)
        dest = chunk_path(data_dir(), f'imports/chunks/{sha}.parquet')
        if not dest.exists():
            os.link(temporary, dest)
        entry = {'count': len(bars), 'path': dest.relative_to(data_dir()).as_posix(),
                 'sha256': sha, 'bytes': dest.stat().st_size}
        if read_chunk(entry) != bars:
            raise DataError('Archiv-Parquet-Rundlauf stimmt nicht.', 409)
        return entry
    finally:
        temporary.unlink(missing_ok=True); csv_path.unlink(missing_ok=True)


def fetch_month(symbol, start, end, spec, key, secret, tick, interrupted):
    rows, tokens, token = {}, set(), None
    pages = outside = duplicates = unfinished = 0
    while True:
        if interrupted():
            raise InterruptedError()
        params = {'symbols': symbol, 'timeframe': '5Min', 'start': start.isoformat(),
                  'end': (end-timedelta(seconds=1)).isoformat(), 'limit': 10000, 'sort': 'asc',
                  'feed': spec['feed'], 'adjustment': spec['adjustment'],
                  'asof': stamp(spec['end']).date().isoformat()}
        if token:
            params['page_token'] = token
        payload = alpaca._request(params, key, secret)
        pages += 1
        if not isinstance(payload.get('bars'), dict):
            raise DataError('Providerantwort enthält keine gültige Bars-Struktur.', 502)
        raw = payload['bars'].get(symbol, [])
        if not isinstance(raw, list):
            raise DataError('Providerantwort enthält keine Kerzenliste.', 502)
        # Compare each validated original record before deduplication can hide
        # conflicting OHLCV values (including conflicts on the same page).
        for item in raw:
            single, q = alpaca.parse_bars([item], '5m', int(end.timestamp()))
            if q['rejected']:
                raise DataError('Ungültige Providerkerzen; Monatscheckpoint nicht veröffentlicht.', 422)
            unfinished += q['unfinished']
            if not single:
                continue
            bar = single[0]
            if not int(start.timestamp()) <= bar.time < int(end.timestamp()):
                raise DataError('Providerkerze außerhalb des angefragten Monats.', 422)
            old = rows.get(bar.time)
            if old and old != bar:
                raise DataError('Widersprüchliche doppelte Providerkerzen.', 422)
            duplicates += old is not None
            rows[bar.time] = bar
        tick(pages, len(rows))
        token = payload.get('next_page_token')
        if not token:
            break
        if not isinstance(token, str) or token in tokens or pages >= 4096:
            raise DataError('Ungültige oder wiederholte Provider-Paginierung.', 502)
        tokens.add(token)
    fine = []
    for bar in sorted(rows.values(), key=lambda b: b.time):
        bounds = session_bounds(datetime.fromtimestamp(bar.time, NY).date().isoformat())
        if bounds and bounds[0] <= bar.time < bar.end <= bounds[1] and (bar.time-bounds[0]) % 300 == 0:
            fine.append(bar)
        else:
            outside += 1
    return fine, {'pages': pages, 'outsideRegular': outside, 'duplicateRows': duplicates,
                  'unfinished': unfinished, 'fetchedAt': datetime.now(UTC).isoformat()}


def coverage(fine, start, end):
    """Count whole missing sessions too; leading/trailing emptiness is not an IPO claim."""
    present = {b.time for b in fine}
    first = fine[0].time if fine else None
    last = fine[-1].end if fine else None
    missing = internal = leading = trailing = sessions = 0
    examples = []
    day = start.astimezone(NY).date()
    while day <= end.astimezone(NY).date():
        bounds = session_bounds(day.isoformat())
        if bounds:
            wanted = [t for t in range(*bounds, 300) if start.timestamp() <= t and t+300 <= end.timestamp()]
            absent = [t for t in wanted if t not in present]
            missing += len(absent)
            if wanted and not any(t in present for t in wanted):
                sessions += 1
                if first is not None and bounds[1] <= first: leading += 1
                elif last is not None and bounds[0] >= last: trailing += 1
                else: internal += 1
            if absent and len(examples) < 10:
                examples.append({'date': day.isoformat(), 'missing5m': len(absent)})
        day += timedelta(days=1)
    return {'missing5m': missing, 'emptySessions': sessions, 'internalEmptySessions': internal,
            'leadingEmptySessions': leading, 'trailingEmptySessions': trailing, 'examples': examples,
            'first': first, 'lastClose': last,
            'policy': 'No filling. Leading/trailing empty history may reflect listing/feed coverage; not classified as IPO/delisting.'}


def publish(symbol, stock, spec):
    fine = [bar for entry in stock['months'].values() for bar in read_chunk(entry)]
    fine.sort(key=lambda b: b.time)
    if any(a.time >= b.time for a, b in zip(fine, fine[1:])):
        raise DataError('Überlappende Archivmonate.', 409)
    report = coverage(fine, stamp(spec['start']), stamp(spec['end']))
    sources, quality = resample_regular(fine)
    if any(len(rows) < 3 for rows in sources.values()):
        return {'status': 'unavailable', 'coverage': report, 'error': 'Zu wenig vollständige reguläre Kerzen.'}
    meta = {'feed': spec['feed'], 'adjustment': spec['adjustment'], 'normalization': NORMALIZATION,
            'mode': VERSION, 'cached': True, 'warning': None, 'quality': {'rejected': 0},
            'requestedStart': spec['start'], 'requestedEnd': spec['end'], 'rthQuality': quality,
            'archiveCoverage': report, 'fetchedAt': datetime.now(UTC).isoformat(),
            'adjustmentVintage': 'provider state at retrieval; not point-in-time corporate-action vintage'}
    material = {tf: (rows, {**meta, 'count': len(rows), 'first': rows[0].time,
                           'last': rows[-1].time, 'lastClose': rows[-1].end}) for tf, rows in sources.items()}
    identity = save_dataset(symbol, material, feed=spec['feed'], adjustment=spec['adjustment'],
                            session='XNYS regular; open-anchored buckets; final 4h bucket may be shorter; execution 5m')
    from operations import record_dataset
    record_dataset(read_dataset(identity), imported=True)
    return {'status': 'completed', 'datasetId': identity, 'counts': {tf: len(b) for tf, b in sources.items()},
            'coverage': report, 'rthQuality': quality}


def run(identity, stop=None):
    with archive_lock():
        job = get(identity)
        if job['engineHash'] != code_hash():
            raise DataError('Archivcode geändert. Alten Auftrag nicht unter neuer Engine fortsetzen.', 409)
        if job['status'] == 'completed':
            return job
        spec = job['spec']
        key, secret = alpaca.credentials()
        job.update(status='running', phase='preparing', error=None)
        write_job(job)
        interrupted = lambda: bool(stop and stop.is_set())
        try:
            for symbol in spec['symbols']:
                if interrupted(): raise InterruptedError()
                stock = job['stocks'].setdefault(symbol, {'status': 'pending', 'months': {}})
                if stock['status'] == 'completed':
                    # Checkpoint checksums, not provider calls, on every resume.
                    for entry in stock['months'].values(): read_chunk(entry)
                    read_dataset(stock['datasetId'])
                    continue
                stock.update(status='running', error=None)
                job.update(currentSymbol=symbol, phase='downloading')
                collect_stock(job, stock, symbol, spec, key, secret, interrupted)
                if stock['status'] != 'failed':
                    job['phase'] = 'publishing'; write_job(job)
                    stock.update(publish(symbol, stock, spec)); write_job(job)
                print(json.dumps({'archive': identity, 'symbol': symbol, 'status': stock['status'],
                                  'finished': sum(s['status']=='completed' for s in job['stocks'].values()),
                                  'total': len(spec['symbols']), 'requests': job['requests']}, ensure_ascii=False), flush=True)
            job['status'] = 'completed' if all(s['status']=='completed' for s in job['stocks'].values()) else 'partial'
            job['phase'] = 'finished'
        except InterruptedError:
            job.update(status='paused', phase='interrupted')
        except BaseException as exc:
            job.update(status='failed', phase='failed', error=str(exc))
            raise
        finally:
            write_job(job)
        return job


def collect_stock(job, stock, symbol, spec, key, secret, interrupted):
    """At most four monthly responses in flight, all sharing the provider budget.

    Commit in the caller thread; cancellation retains every fully received month.
    Incomplete months are deliberately fetched again rather than trusted partially.
    """
    intervals = iter(months(stamp(spec['start']), stamp(spec['end'])))
    state_lock = threading.RLock()
    counters = {}
    base = job['requests']
    def tick(month, pages, count):
        with state_lock:
            counters[month] = pages
            job.update(requests=base+sum(counters.values()), currentMonth=month, page=pages, monthRows=count)
            write_job(job)
    with ThreadPoolExecutor(max_workers=4) as pool:
        pending = {}
        exhausted = False
        while pending or not exhausted:
            while len(pending) < 4 and not exhausted and not interrupted():
                try:
                    start, end = next(intervals)
                except StopIteration:
                    exhausted = True; break
                month = start.strftime('%Y-%m')
                if month in stock['months']:
                    read_chunk(stock['months'][month]); continue
                preflight(history_days=35, symbols=1)
                future = pool.submit(fetch_month, symbol, start, end, spec, key, secret,
                                     lambda p, c, m=month: tick(m, p, c), interrupted)
                pending[future] = (month, start, end)
            if not pending:
                if interrupted(): raise InterruptedError()
                break
            done, _ = wait(pending, timeout=1, return_when=FIRST_COMPLETED)
            for future in done:
                month, start, end = pending.pop(future)
                try:
                    bars, detail = future.result()
                    entry = {**write_chunk(bars), **detail, 'start': start.isoformat(), 'end': end.isoformat()}
                    with state_lock:
                        stock['months'][month] = entry
                        write_job(job)  # Data durable before checkpoint commit.
                except InterruptedError:
                    pass
                except DataError as exc:
                    with state_lock:
                        stock.update(status='failed', error=str(exc))
                        write_job(job)
            # Provider failures do not cancel other complete checkpoints, but no
            # more months for this stock are scheduled. Resume retries the gaps.
            if stock['status'] == 'failed' or interrupted():
                exhausted = True
    if interrupted(): raise InterruptedError()


def status(identity):
    job = get(identity)
    stocks = job['stocks']
    return {k: job.get(k) for k in ('id', 'status', 'phase', 'currentSymbol', 'currentMonth', 'updatedAt', 'requests', 'error')} | {
        'total': len(job['spec']['symbols']), 'finished': sum(s['status']=='completed' for s in stocks.values()),
        'checkpointMonths': sum(len(s['months']) for s in stocks.values()),
        'stagingBytes': sum(e.get('bytes', 0) for s in stocks.values() for e in s['months'].values()),
        'stocks': {name: {k: v for k, v in s.items() if k != 'months'} for name, s in stocks.items()}}


def backup_chunks(db, root):
    """Resolve only immutable chunks committed in the captured SQLite snapshot."""
    entries = {}
    for row in db.execute('SELECT value FROM settings WHERE key LIKE ?', (PREFIX+'%',)):
        job = json.loads(row[0])
        for stock in job['stocks'].values():
            for entry in stock['months'].values():
                if entry.get('path'):
                    read_chunk(entry, root)
                    entries[entry['path']] = entry
    return entries
