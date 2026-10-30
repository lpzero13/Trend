"""Streaming history acquisition with durable monthly checkpoints and shared cache.

The v1 job is never resumed with a new code hash. Verified old files can instead
be explicitly adopted into a new v2 acquisition batch, retaining provenance.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import re
import threading
import time
import uuid

import pandas as pd
import alpaca
import archive_state as state
import history_archive as legacy
from datasets import digest, read_dataset, save_dataset
from history_http import Client
from lab_data import NORMALIZATION, session_bounds, resample_regular
from models import Bar, DataError, NY
from parquet_store import connect, checksum, FIELDS
from storage import preflight

UTC = timezone.utc
VERSION = 'tori-history-archive-2'


def code_hash():
    names = ('history_fast.py', 'archive_state.py', 'history_http.py', 'history_archive.py',
             'alpaca.py', 'provider_budget.py', 'lab_data.py', 'market_calendar.py', 'parquet_store.py')
    return hashlib.sha256(b''.join((Path(__file__).parent/n).read_bytes() for n in names)).hexdigest()


def create(spec):
    # Validate through the old, credential-free contract, without creating a v1 job.
    symbols = spec.get('symbols', [])
    if (not isinstance(symbols, list) or not 1 <= len(symbols) <= 20000
            or any(not isinstance(s, str) or not re.fullmatch(r'[A-Z][A-Z0-9./-]{0,29}', s) for s in symbols)
            or len(set(symbols)) != len(symbols)):
        raise DataError('1 bis 20.000 eindeutige US-Symbole erforderlich.', 400)
    start = legacy.stamp(spec.get('start', '2016-01-01T00:00:00Z'))
    end = legacy.stamp(spec['end']) if spec.get('end') else datetime.now(UTC).replace(microsecond=0)-timedelta(minutes=16)
    if start < datetime(2016, 1, 1, tzinfo=UTC) or start >= end or end > datetime.now(UTC)-timedelta(minutes=15):
        raise DataError('Zeitraum muss ab 2016 liegen und mindestens 15 Minuten alt enden.', 400)
    if spec.get('feed', 'sip') not in ('sip', 'iex') or spec.get('adjustment', 'split') not in ('split', 'raw', 'all'):
        raise DataError('Unbekannter Feed oder Bereinigung.', 400)
    universe = spec.get('universe')
    if not isinstance(universe, dict) or not universe.get('sources'):
        raise DataError('Eingefrorene Universumsquellen erforderlich.', 400)
    workers = spec.get('workers', 8)
    if type(workers) is not int or not 1 <= workers <= 12:
        raise DataError('Parallelität muss zwischen 1 und 12 liegen.', 400)
    rate = spec.get('requests_per_minute', 190)
    if type(rate) is not int or not 1 <= rate <= 190: raise DataError('Abrufbudget: 1 bis 190 pro Minute.', 400)
    vintage = spec.get('vintage', datetime.now(UTC).date().isoformat())
    try: datetime.strptime(vintage, '%Y-%m-%d')
    except (ValueError, TypeError): raise DataError('Datenvintage braucht YYYY-MM-DD.', 400) from None
    asof=spec.get('asof',vintage)
    try:datetime.strptime(asof,'%Y-%m-%d')
    except (ValueError,TypeError):raise DataError('Symbolstand braucht YYYY-MM-DD.',400) from None
    config = {**spec, 'symbols': symbols, 'start': start.isoformat(), 'end': end.isoformat(),
              'feed': spec.get('feed', 'sip'), 'adjustment': spec.get('adjustment', 'split'),
              'normalization': NORMALIZATION, 'asof': asof, 'vintage': vintage,
              'workers': workers, 'requests_per_minute': rate, 'version': VERSION}
    preflight(history_days=(end-start).days, symbols=len(symbols), bytes_per_symbol_day=4000)
    job = {'id': uuid.uuid4().hex[:24], 'spec': config, 'createdAt': time.time(), 'updatedAt': time.time(),
           'status': 'pending', 'phase': 'pending', 'engineHash': code_hash(), 'pauseRequested': False,
           'metrics': {}, 'sourceJob': None}
    state.create(job)
    return job


def write_chunk(bars):
    if not bars: return {'count': 0}
    folder = legacy.data_dir()/'imports/chunks'
    folder.mkdir(parents=True, exist_ok=True)
    temporary = folder/(uuid.uuid4().hex+'.tmp')
    try:
        # Explicit dtypes avoid CSV serialization and numeric inference. Preserve
        # float OHLCV values produced by the provider adapter exactly.
        frame = pd.DataFrame.from_records(
            [(b.time, b.end, b.open, b.high, b.low, b.close, b.volume) for b in bars], columns=FIELDS)
        frame = frame.astype({'time': 'int64', 'end': 'int64', **{k: 'float64' for k in FIELDS[2:]}})
        with connect() as con:
            con.register('incoming', frame)
            con.execute('COPY incoming TO ? (FORMAT PARQUET, COMPRESSION ZSTD, COMPRESSION_LEVEL 3)', [str(temporary)])
        with temporary.open('r+b') as stream: os.fsync(stream.fileno())
        sha = checksum(temporary)
        dest = legacy.chunk_path(legacy.data_dir(), f'imports/chunks/{sha}.parquet')
        try: os.link(temporary, dest)
        except FileExistsError: pass
        entry = {'count': len(bars), 'path': dest.relative_to(legacy.data_dir()).as_posix(),
                 'sha256': sha, 'bytes': dest.stat().st_size}
        if legacy.read_chunk(entry) != bars: raise DataError('Parquet-Rückleseprüfung fehlgeschlagen.', 409)
        return entry
    finally:
        temporary.unlink(missing_ok=True)


def parse_page(raw, start, end):
    if not isinstance(raw, list): raise DataError('Providerkerzenliste fehlt.', 502)
    result = []
    start_at, end_at = int(start.timestamp()), int(end.timestamp())
    previous = None
    for item in raw:
        try:
            dt = datetime.fromisoformat(item['t'].replace('Z', '+00:00'))
            if dt.tzinfo is None: raise ValueError('timezone')
            at = int(dt.timestamp())
            values = tuple(float(item[k]) for k in ('o', 'h', 'l', 'c', 'v'))
            o, h, l, c, v = values
            if (not all(math.isfinite(x) for x in values) or min(o, h, l, c) <= 0 or v < 0
                    or h < max(o, c, l) or l > min(o, c, h) or at < start_at or at >= end_at):
                raise ValueError('OHLCV/range')
            if previous is not None and at < previous: raise ValueError('order')
            previous = at
            if at+300 > end_at: continue
            result.append(Bar(at, at+300, *values))
        except (KeyError, ValueError, TypeError, OverflowError, AttributeError):
            raise DataError('Ungültige/unsortierte Providerkerzen; kein Monatsabschluss.', 422) from None
    return result


def stream(symbol, start, end, spec, request, emit, interrupted, progress):
    """Pagination independent of monthly storage. Emit only proven closed months.

    A next-page token is used only inside this HTTP stream. Resume starts at the
    first missing month, so expired tokens never invalidate persisted progress.
    """
    intervals = list(legacy.months(start, end))
    index = 0
    buffered = {}
    page_count = 0
    token = None
    tokens = set()
    previous_time = None
    previous_bar = None
    outside = duplicates = 0

    def close_month():
        nonlocal index, outside, duplicates
        opened, closed = intervals[index]
        bars = sorted(buffered.values(), key=lambda b: b.time)
        emit(opened.strftime('%Y-%m'), opened, closed, bars,
             {'streamPagesAtCheckpoint': page_count, 'outsideRegular': outside, 'duplicateRows': duplicates,
              'fetchedAt': datetime.now(UTC).isoformat()})
        buffered.clear(); outside = duplicates = 0; index += 1

    while True:
        if interrupted(): raise InterruptedError()
        params = {'symbols': symbol, 'timeframe': '5Min', 'start': start.isoformat(),
                  'end': (end-timedelta(seconds=1)).isoformat(), 'limit': 10000,
                  'sort': 'asc', 'feed': spec['feed'], 'adjustment': spec['adjustment'], 'asof': spec['asof']}
        if token: params['page_token'] = token
        payload = request(params)
        if not isinstance(payload, dict) or not isinstance(payload.get('bars'), dict):
            raise DataError('Providerantwort enthält keine Bars-Struktur.', 502)
        if set(payload['bars'])- {symbol}: raise DataError('Provider lieferte unerwartete Symbole.', 502)
        parsed = parse_page(payload['bars'].get(symbol, []), start, end)
        page_count += 1
        # Validate the whole page and cross-page ordering before publishing a
        # checkpoint based on its high-water mark.
        cursor, prior = previous_time, previous_bar
        for bar in parsed:
            if cursor is not None and (bar.time < cursor or (bar.time == cursor and bar != prior)):
                raise DataError('Widersprüchliche/unsortierte Folgeseite.', 422)
            cursor, prior = bar.time, bar
        for bar in parsed:
            if previous_time == bar.time:
                duplicates += 1; continue
            previous_time, previous_bar = bar.time, bar
            while index < len(intervals) and bar.time >= intervals[index][1].timestamp(): close_month()
            if index >= len(intervals): raise DataError('Kerze nach Streamende.', 422)
            day = datetime.fromtimestamp(bar.time, NY).date().isoformat()
            bounds = session_bounds(day)
            if bounds and bounds[0] <= bar.time < bar.end <= bounds[1] and (bar.time-bounds[0]) % 300 == 0:
                buffered[bar.time] = bar
            else: outside += 1
        progress(page_count)
        next_token = payload.get('next_page_token')
        if not next_token:
            while index < len(intervals): close_month()
            return page_count
        if not isinstance(next_token, str) or next_token in tokens or page_count >= 20000:
            raise DataError('Ungültige Provider-Paginierung.', 502)
        tokens.add(next_token); token = next_token


def missing_runs(intervals, covered):
    opened = closed = None
    for start, end in intervals:
        if start.strftime('%Y-%m') in covered:
            if opened is not None: yield opened, closed
            opened = closed = None
        else:
            if opened is None: opened = start
            closed = end
    if opened is not None: yield opened, closed


def suitable(entry, start, end):
    return entry.get('start') == start.isoformat() and entry.get('end') == end.isoformat()


def check_entry(entry, root=None):
    """Verify immutable bytes already fully round-trip checked at publication.

    Decoding the same Parquet on every cache lookup is unnecessary. New writes
    and final dataset publication still validate the actual typed row values.
    """
    if not entry['count']:
        if entry.get('path'): raise DataError('Widersprüchlicher leerer Checkpoint.',409)
        return
    path=legacy.chunk_path(root or legacy.data_dir(),entry['path'])
    if not path.is_file() or path.stat().st_size!=entry['bytes'] or checksum(path)!=entry['sha256']:
        raise DataError('Checkpoint fehlt oder ist beschädigt.',409)


def windows(start,end):
    intervals=list(legacy.months(start,end))
    for i in range(0,len(intervals),12):
        yield intervals[i][0],intervals[min(i+11,len(intervals)-1)][1]


def publish(symbol, spec, entries):
    fine = [bar for month, entry in sorted(entries.items()) for bar in legacy.read_chunk(entry)]
    if any(a.time >= b.time for a, b in zip(fine, fine[1:])): raise DataError('Überlappende Monate.', 409)
    report = legacy.coverage(fine, legacy.stamp(spec['start']), legacy.stamp(spec['end']))
    frames, quality = resample_regular(fine)
    if any(len(rows) < 3 for rows in frames.values()):
        return {'status': 'unavailable', 'coverage': report, 'error': 'Zu wenig vollständige reguläre Kerzen.'}
    meta = {'feed': spec['feed'], 'adjustment': spec['adjustment'], 'normalization': NORMALIZATION,
            'mode': VERSION, 'cached': True, 'warning': None, 'quality': {'rejected': 0},
            'requestedStart': spec['start'], 'requestedEnd': spec['end'], 'rthQuality': quality,
            'archiveCoverage': report, 'fetchedAt': datetime.now(UTC).isoformat(), 'vintage': spec['vintage'],
            'adjustmentVintage': 'immutable acquisition batch; provider adjustments at retrieval, not point-in-time vintage'}
    sources = {tf: (rows, {**meta, 'count': len(rows), 'first': rows[0].time, 'last': rows[-1].time,
                           'lastClose': rows[-1].end}) for tf, rows in frames.items()}
    identity = save_dataset(symbol, sources, feed=spec['feed'], adjustment=spec['adjustment'],
                            session='XNYS regular; open-anchored buckets; final 4h bucket may be shorter; execution 5m')
    from operations import record_dataset
    record_dataset(read_dataset(identity), imported=True)
    return {'status': 'completed', 'datasetId': identity, 'counts': {tf: len(rows) for tf, rows in frames.items()},
            'coverage': report, 'rthQuality': quality}


def adopt(identity, source_id):
    """Explicit, offline v1 -> v2 adoption with a new job/version binding."""
    job = state.get(identity)
    if job['status'] not in ('pending', 'paused'): raise DataError('Übernahme nur vor dem Lauf.', 409)
    source = legacy.get(source_id)
    spec = job['spec']
    for key in ('start', 'end', 'feed', 'adjustment', 'normalization'):
        if source['spec'][key] != spec[key]: raise DataError('Abweichender Datenvertrag bei Übernahme: '+key, 409)
    if spec['asof']!=legacy.stamp(source['spec']['end']).date().isoformat():
        raise DataError('Übernahme braucht den ursprünglichen Symbolstand des v1-Auftrags.',409)
    if source['spec'].get('version') != legacy.VERSION: raise DataError('Unbekannte Altversion.', 409)
    adopted = 0
    for symbol in spec['symbols']:
        stock = source['stocks'].get(symbol)
        if not stock: continue
        wanted = {s.strftime('%Y-%m'): (s, e) for s, e in legacy.months(legacy.stamp(spec['start']), legacy.stamp(spec['end']))}
        for month, entry in stock['months'].items():
            if state.get(identity).get('pauseRequested'):
                state.update(identity,status='paused',phase='user_paused')
                raise InterruptedError()
            if month not in wanted or not suitable(entry, *wanted[month]): raise DataError('Abweichende Monatsgrenzen.', 409)
            fetched = entry.get('fetchedAt', '')
            if fetched and fetched[:10] != spec['vintage']:
                raise DataError('Übernahme braucht die ursprüngliche Abrufvintage.', 409)
            check_entry(entry)
            state.checkpoint(identity, spec, symbol, month, {**entry, 'adoptedFrom': source_id}, reused=True)
            adopted += 1
        if stock['status'] == 'completed':
            dataset = read_dataset(stock['datasetId'])
            m = dataset['material']
            if (m['symbol'], m['feed'], m['adjustment']) != (symbol, spec['feed'], spec['adjustment']):
                raise DataError('Falscher Altbestand.', 409)
            state.update_stock(identity, symbol, **{k: v for k, v in stock.items() if k not in ('months', 'error')},
                               error=None, adoptedFrom=source_id)
    state.update(identity, sourceJob=source_id, adoptedMonths=adopted)
    return state.status(identity)


def run(identity, stop=None, *, reset_pause=True):
    stop = stop or threading.Event()
    with legacy.archive_lock():
        job = state.get(identity)
        if job['engineHash'] != code_hash(): raise DataError('Archivengine geändert; neuen Auftrag anlegen.', 409)
        if job['status'] == 'completed': return state.status(identity)
        if not reset_pause and job.get('pauseRequested'):
            return state.update(identity,status='paused',phase='user_paused')
        spec = job['spec']
        state.update(identity, status='running', phase='downloading', error=None,
                     **({'pauseRequested':False} if reset_pause else {}))
        control_lock = threading.Lock()
        control_at = [0.]
        def interrupted():
            if stop.is_set(): return True
            with control_lock:
                if time.monotonic()-control_at[0] > .5:
                    control_at[0] = time.monotonic()
                    if state.get(identity).get('pauseRequested'): stop.set()
            return stop.is_set()
        publish_lock = threading.Lock()  # Bound publication RAM to one stock.
        try:
            client = Client(*alpaca.credentials(), budget=spec['requests_per_minute'])
        except Exception as exc:
            state.update(identity, status='failed', phase='credentials', error=str(exc))
            raise
        client.interrupted=interrupted
        previous_metrics = job.get('metrics', {})
        started = time.perf_counter()
        progress_lock = threading.Lock()
        progress_at = [0.]
        last_error = []
        def progress(symbol, pages):
            with progress_lock:
                if time.monotonic()-progress_at[0] >= 2:
                    progress_at[0] = time.monotonic()
                    state.update(identity, currentSymbol=symbol, metrics=totals(), phase='downloading')
        def totals():
            return {k: previous_metrics.get(k, 0)+v for k, v in client.snapshot().items()}
        def prepare(symbol):
            stock=state.stock(identity,symbol)
            if stock['status']=='completed':
                read_dataset(stock['datasetId'])
                return None
            state.update_stock(identity,symbol,status='running',error=None,phase='downloading')
            intervals=list(legacy.months(legacy.stamp(spec['start']),legacy.stamp(spec['end'])))
            existing=state.refs(identity,symbol);cache=state.cached(spec,symbol)
            for start,end in intervals:
                month=start.strftime('%Y-%m')
                if month in existing:
                    if not suitable(existing[month],start,end):raise DataError('Checkpointgrenze verändert.',409)
                    check_entry(existing[month])
                elif month in cache and suitable(cache[month],start,end):
                    check_entry(cache[month])
                    state.checkpoint(identity,spec,symbol,month,cache[month],reused=True)
                    existing[month]=cache[month]
            return [(symbol,s,e) for start,end in missing_runs(intervals,existing) for s,e in windows(start,end)]
        def download(task):
            symbol,start,end=task
            begun=time.perf_counter()
            try:
                def emit(month, start, end, bars, detail):
                    preflight(history_days=35, symbols=1)
                    entry = {**write_chunk(bars), **detail, 'start': start.isoformat(), 'end': end.isoformat()}
                    state.checkpoint(identity, spec, symbol, month, entry)
                pages=stream(symbol,start,end,spec,client.request,emit,interrupted,lambda count:progress(symbol,count))
                state.increment_stock(identity,symbol,downloadedPages=pages,downloadSeconds=time.perf_counter()-begun)
                return True
            except InterruptedError:
                state.update_stock(identity, symbol, status='paused', phase='interrupted')
                return False
            except Exception as exc:
                state.update_stock(identity, symbol, status='failed', error=str(exc), phase='failed')
                last_error.append(symbol)
                return False
        def publish_ready(symbol):
            if interrupted():
                state.update_stock(identity,symbol,status='paused',phase='interrupted');return
            try:
                state.update_stock(identity,symbol,phase='publishing')
                begun=time.perf_counter()
                result=publish(symbol,spec,state.refs(identity,symbol))
                state.update_stock(identity,symbol,**result,phase='finished',publishSeconds=time.perf_counter()-begun)
            except Exception as exc:
                state.update_stock(identity,symbol,status='failed',phase='failed',error=str(exc))
            print(json.dumps({'archive':identity,'symbol':symbol,'status':state.stock(identity,symbol)['status']},ensure_ascii=False),flush=True)
        try:
            task_lists={}
            for symbol in spec['symbols']:
                if interrupted():break
                tasks=prepare(symbol)
                if tasks is not None:task_lists[symbol]=tasks
            from itertools import zip_longest
            tasks=[t for group in zip_longest(*task_lists.values()) for t in group if t is not None]
            remaining={symbol:len(ts) for symbol,ts in task_lists.items()}
            failed=set()
            with ThreadPoolExecutor(max_workers=spec['workers']) as pool, ThreadPoolExecutor(max_workers=1) as publishers:
                publications=[publishers.submit(publish_ready,s) for s,n in remaining.items() if n==0]
                iterator=iter(tasks)
                from concurrent.futures import wait, FIRST_COMPLETED
                pending = {}
                exhausted = False
                while pending or not exhausted:
                    while len(pending) < spec['workers'] and not exhausted and not interrupted():
                        try:
                            task=next(iterator)
                            if task[0] in failed:continue
                            pending[pool.submit(download,task)]=task[0]
                        except StopIteration: exhausted = True
                    if not pending: break
                    done,_=wait(pending,timeout=1,return_when=FIRST_COMPLETED)
                    for future in done:
                        symbol=pending.pop(future)
                        if not future.result():failed.add(symbol)
                        remaining[symbol]-=1
                        if remaining[symbol]==0 and symbol not in failed:
                            publications.append(publishers.submit(publish_ready,symbol))
                    if interrupted(): exhausted = True
                for future in publications:future.result()
            summary = state.status(identity)
            status = 'paused' if stop.is_set() else 'completed' if summary['finished']==summary['total'] else 'partial'
            state.update(identity, status=status, phase='interrupted' if stop.is_set() else 'finished', metrics=totals(),
                         elapsedSeconds=job.get('elapsedSeconds', 0)+time.perf_counter()-started)
        except BaseException as exc:
            state.update(identity, status='failed', phase='failed', error=str(exc), metrics=totals())
            raise
        finally:
            client.close()
        return state.status(identity)


def pause(identity):
    job = state.get(identity)
    if job['status'] in ('pending', 'paused'):
        state.update(identity, status='paused', phase='user_paused', pauseRequested=True)
    elif job['status'] == 'running': state.update(identity, pauseRequested=True)
    return state.status(identity)
