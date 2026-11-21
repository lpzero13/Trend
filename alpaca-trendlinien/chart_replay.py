"""On-demand chart sessions: transfer quotes once, then only causal analysis states.

Web-only. Research engines/readers and saved personal drawings are unchanged.
Future quotes belong to the separate transport window, never to a visible view.
"""
from bisect import bisect_right
from collections import OrderedDict
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import re
import secrets
import threading

from models import DataError
from weekly_chart import CHART_TIMEFRAMES, add_weekly

MAX_SESSIONS = 2
MAX_BARS = 100000
MAX_STATES = 128
MAX_STATE_BYTES = 24 * 1024 * 1024
HISTORY_DAYS = 1098  # Two navigable years plus approximately one year of warmup.
_sessions = OrderedDict()
_lock = threading.RLock()


def clear():
    with _lock:
        _sessions.clear()


def _latest(rows):
    last, before = rows[-1], rows[-2]
    return dict(close=last['close'], time=last['time'], end=last['end'],
                change=last['close']-before['close'],
                changePercent=(last['close']/before['close']-1)*100)


class Session:
    def __init__(self, sources, meta, *, through=None, guard=None):
        from analysis_service import build_chart
        self.id = secrets.token_hex(16)
        self.guard = guard
        self.lock = threading.RLock()
        self.sources = {tf: (list(rows), deepcopy(m)) for tf, (rows, m) in sources.items()}
        if sum(len(rows) for rows, _ in sources.values()) > MAX_BARS:
            raise DataError('Dieser Kursbestand ist für einen Browser-Replay zu groß.', 422)
        self.through = through or max(rows[-1].end for rows, _ in sources.values())
        now = datetime.now(timezone.utc)
        base = build_chart(self.sources, meta['symbol'], '4h', datetime.fromtimestamp(self.through, timezone.utc),
                           now, historical=True, include_analysis=False)
        base.update(deepcopy(meta))
        if meta.get('dataKind') == 'synthetic':
            base['company'] = meta['symbol']+' · Synthetischer Test'
        add_weekly(base, '4h')
        self.base = base
        self.rows = {tf: c['bars'] for tf, c in base['charts'].items()}
        self.ends = {tf: [b['end'] for b in rows] for tf, rows in self.rows.items()}
        self.times = {tf: [b['time'] for b in rows] for tf, rows in self.rows.items()}
        self.states = OrderedDict()
        self.state_bytes = 0
        self.views = OrderedDict()
        from replay_fan import Feeder
        from replay_legacy import Legacy
        self.feeder = Feeder(meta['symbol'])
        self.legacy = Legacy()
        self.gaps = {}
        self.smas = {}

    def gap_prefix(self, tf, rows):
        if tf not in self.gaps:
            from fan_study import source_gaps
            from models import Bar
            all_rows = [Bar(**b) for b in self.rows[tf]]
            self.gaps[tf] = source_gaps(all_rows, all_rows[-1].end, tf)
        return {i: v for i, v in self.gaps[tf].items() if i < len(rows)}

    def sma_prefix(self, tf, rows, gaps):
        if tf not in self.smas:
            from fan_master import context
            from models import Bar
            all_rows = [Bar(**b) for b in self.rows[tf]]
            regular = self.base['sources'][tf].get('normalization') == 'tori-rth-5m-v1' or tf == '1W' and self.base['sources']['1D'].get('normalization') == 'tori-rth-5m-v1'
            all_gaps = self.gap_prefix(tf, all_rows) if regular else {}
            result = context(all_rows, all_gaps)
            self.smas[tf] = result['series']
        last = rows[-1].time
        series = {n: values[:bisect_right([v['time'] for v in values], last)] for n, values in self.smas[tf].items()}
        return {'sma50': series['50'][-1].get('value') if series['50'] and series['50'][-1]['time'] == last else None,
                'sma200': series['200'][-1].get('value') if series['200'] and series['200'][-1]['time'] == last else None,
                'series': series, 'meaning': 'Nur bekannte Quellkerzen; Kontext, kein Einstiegsausschluss'}

    def validate(self):
        if self.guard:
            self.guard()

    def counts(self, cutoff):
        if type(cutoff) is not int or cutoff > self.through:
            raise DataError('Zeitpunkt liegt außerhalb des vorgeladenen Verlaufs.', 404)
        counts = {tf: bisect_right(ends, cutoff) for tf, ends in self.ends.items()}
        if any(counts.get(tf, 0) < 3 for tf in ('1h', '4h', '1D')):
            raise DataError('Zu wenig abgeschlossene Kerzen zum gewählten Zeitpunkt.', 404)
        return {tf: n for tf, n in counts.items() if n >= 3}

    def descriptor(self, tf, count):
        key = tf, count
        if key not in self.views:
            rows = self.rows[tf][:count]
            self.views[key] = dict(reference=rows[-1]['time'], latest=_latest(rows),
                fingerprint=hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()[:16])
            while len(self.views) > MAX_STATES:
                self.views.popitem(last=False)
        return self.views[key]

    def payload(self, cutoff, timeframe, engine='legacy', analysis=True, *, historical=True):
        """Assemble only known prefixes. Canonical analyzers remain authoritative."""
        from drawing_axes import add_drawing_axes
        from fan_chart import ENGINES, apply
        if timeframe not in CHART_TIMEFRAMES or engine not in ENGINES or type(analysis) is not bool:
            raise DataError('Ungültiger Replay-Modus.', 400)
        counts = self.counts(cutoff)
        if timeframe not in counts:
            raise DataError('Zu wenig vollständige Wochen.', 404)
        p = {k: v for k, v in self.base.items() if k not in
             ('bars', 'axis', 'charts', 'sources', 'lanes', 'drawingAxes')}
        p.update(charts={}, sources={}, lanes={}, analysisCutoff=cutoff, timeframe=timeframe,
                 historical=historical, generatedAt=datetime.now(timezone.utc).isoformat(),
                 analysisEnabled=analysis, replaySession=self.id)
        for tf, count in counts.items():
            rows = self.rows[tf][:count]
            descriptor = self.descriptor(tf, count)
            p['charts'][tf] = {k: v for k, v in descriptor.items() if k != 'fingerprint'}
            p['charts'][tf].update(bars=rows, axis=self.times[tf][:count])
            p['sources'][tf] = {**self.base['sources'][tf], 'count': count, 'first': rows[0]['time'],
                               'last': rows[-1]['time'], 'lastClose': rows[-1]['end']}
        p.update(p['charts'][timeframe], fingerprint=self.descriptor(timeframe, counts[timeframe])['fingerprint'])
        if analysis and engine == 'legacy':
            from models import Bar
            for tf, count in counts.items():
                rows = self.sources[tf][0][:count] if tf != '1W' else [Bar(**b) for b in p['charts'][tf]['bars']]
                errors = tf != '1W' and p['sources'][tf]['quality']['rejected'] > 0
                p['lanes'][tf] = self.legacy.analyze(rows, tf, data_errors=errors)
        elif analysis:
            apply(p, engine, lane_loader=self.feeder.analyze, context_loader=self.sma_prefix, gap_loader=self.gap_prefix)
        # Calendar positions depend only on known clocks, not preloaded future observations.
        add_drawing_axes(p)
        return p

    def view(self, cutoff, timeframe, engine='legacy', analysis=True, *, historical=True, full=False):
        with self.lock:
            self.validate()
            if full:
                return self.payload(cutoff, timeframe, engine, analysis, historical=historical)
            key = cutoff, timeframe, engine, analysis, historical
            if key in self.states:
                self.states.move_to_end(key)
                return deepcopy(self.states[key][0])
            p = self.payload(cutoff, timeframe, engine, analysis, historical=historical)
            compact = {k: v for k, v in p.items() if k not in ('bars', 'axis', 'charts')}
            compact['drawingAxisTails'] = {tf: axis[len(p['charts'][tf]['bars']):]
                                           for tf, axis in compact.pop('drawingAxes').items()}
            compact['chartCounts'] = {tf: len(c['bars']) for tf, c in p['charts'].items()}
            compact['charts'] = {tf: {k: v for k, v in c.items() if k not in ('bars', 'axis')}
                                 for tf, c in p['charts'].items()}
            compact['lanes'] = {tf: dict(lane) for tf, lane in compact['lanes'].items()}
            for lane in compact['lanes'].values():
                lane.pop('sourceTimes', None)  # Rebuilt from the same known prefix by the client.
                if 'context' in lane:
                    lane['context'] = dict(lane['context'])
                    lane['context']['seriesCounts'] = {n: len(v) for n, v in lane['context'].pop('series').items()}
            size = len(json.dumps(compact, separators=(',', ':'), allow_nan=False).encode())
            if size <= MAX_STATE_BYTES:
                self.states[key] = deepcopy(compact), size
                self.state_bytes += size
                while len(self.states) > MAX_STATES or self.state_bytes > MAX_STATE_BYTES:
                    _, (_, removed) = self.states.popitem(last=False)
                    self.state_bytes -= removed
            return compact

    def window(self):
        from models import Bar
        for tf in self.rows:
            if tf not in self.smas:
                self.sma_prefix(tf, [Bar(**b) for b in self.rows[tf]], {})
        return {'id': self.id, 'symbol': self.base['symbol'], 'through': self.through,
                'bars': self.rows, 'smas': self.smas, 'policy': 'transport only; clip every source by end before display/analysis'}


def register(sources, meta, **kwargs):
    session = Session(sources, meta, **kwargs)
    with _lock:
        _sessions[session.id] = session
        while len(_sessions) > MAX_SESSIONS:
            _sessions.popitem(last=False)
    return session


def session(identity):
    if not isinstance(identity, str) or not re.fullmatch('[a-f0-9]{32}', identity):
        raise DataError('Ungültige Replay-Sitzung.', 400)
    with _lock:
        value = _sessions.get(identity)
        if value is None:
            raise DataError('Replay-Sitzung abgelaufen. Kursfenster neu laden.', 410)
        _sessions.move_to_end(identity)
        return value


def open_window(query):
    """Only the selected stock is loaded. Native and archive feeds stay separate."""
    from server import parse_cutoff
    from fan_chart import selected_engine
    def q(name, default=None):
        values = query.get(name, [default])
        if len(values) != 1:
            raise DataError('Parameter mehrfach angegeben.', 400)
        return values[0]
    now = datetime.now(timezone.utc)
    tf = q('timeframe', '4h')
    if tf not in CHART_TIMEFRAMES:
        raise DataError('Ungültiges Chartintervall.', 400)
    asof = q('asof')
    at = parse_cutoff(asof, now) if asof else now-timedelta(minutes=15)
    analysis = q('analysis', '0')
    if analysis not in ('0', '1'):
        raise DataError('analysis=0/1 erwartet.', 400)
    engine = selected_engine(query)
    guard = None
    dataset_id = q('dataset')
    random_id = q('random')
    if random_id:
        from random_replay import case
        item = case(random_id)
        if dataset_id and dataset_id != item['datasetId']:
            raise DataError('Zufallsfall und Dataset passen nicht zusammen.', 400)
        dataset_id = item['datasetId']
        if not asof:
            at = datetime.fromtimestamp(item['startAt'], timezone.utc)
    if dataset_id:
        from chart_sources import sources_for, signature
        sources, meta = sources_for(dataset_id)
        original = signature(dataset_id)
        def guard():
            # sources_for also repeats full checksum verification at the normal deadline.
            sources_for(dataset_id)
            if signature(dataset_id) != original:
                raise DataError('Replay-Dataset wurde geändert; neu laden.', 409)
        meta.pop('normalization', None)
        sources = {tf: (rows, {**m, 'mode': 'immutable-dataset', 'cached': True, 'warning': None})
                   for tf, (rows, m) in sources.items()}
        if not asof and not random_id:
            at = datetime.fromtimestamp(sources['1D' if tf == '1W' else tf][0][-1].end, timezone.utc)
        if random_id:
            from random_replay import _chart_inputs
            frames, m = _chart_inputs(dataset_id)
            sources = {tf: (rows, {'quality': {'rejected': 0}, 'cached': True, 'mode': 'random-replay',
                                 'normalization': m['normalization'][tf]}) for tf, rows in frames.items()}
            meta['randomCase'] = {k: item[k] for k in ('id', 'startAt', 'selection')}
    else:
        from concurrent.futures import ThreadPoolExecutor
        import alpaca as _alpaca_mod
        from alpaca import load_bars, TIMEFRAMES
        from server import _DEFAULT_LOAD_BARS
        symbol = q('symbol', 'AAPL').strip().upper()
        if not re.fullmatch(r'[A-Z][A-Z0-9./-]{0,29}', symbol):
            raise DataError('Ungültige Aktie.', 400)
        # Historical selections get up to a year of subsequent quotes in the
        # transport window; current selections get two preceding years + warmup.
        end = min(now-timedelta(minutes=15), at+timedelta(days=366))
        force_refresh = q('refresh', '0') == '1'
        live_fast_mode = (load_bars is _DEFAULT_LOAD_BARS and _alpaca_mod.load_bars is _DEFAULT_LOAD_BARS)
        sources = None
        meta = None
        if live_fast_mode and not force_refresh:
            from fast_chart_store import load_local_chart_sources
            local_ds, local_meta = load_local_chart_sources(symbol, int(end.timestamp()))
            if local_ds is not None:
                # Trim to a fast ~3-year window around `end` so JSON serialization stays tiny (~0.2s)
                min_start = int((end - timedelta(days=HISTORY_DAYS + 60)).timestamp())
                trimmed = {}
                for k_tf, (rows, m) in local_ds.items():
                    kept = [b for b in rows if b.end >= min_start]
                    trimmed[k_tf] = (kept if len(kept) >= 220 else rows[-max(220, len(kept)):], m)
                sources = trimmed
                meta = dict(
                    symbol=symbol,
                    feed=local_meta.get('feed', 'sip'),
                    adjustment=local_meta.get('adjustment', 'split'),
                    provider='Alpaca',
                )
                if local_meta.get('session'):
                    meta['session'] = local_meta['session']
                if not asof:
                    latest_end = min(rows[-1].end for rows, _ in sources.values())
                    if int(at.timestamp()) > latest_end:
                        at = datetime.fromtimestamp(latest_end, timezone.utc)
        if sources is None:
            with ThreadPoolExecutor(max_workers=3) as pool:
                jobs = {}
                for k_tf in TIMEFRAMES:
                    h_days = (365 if k_tf == '1h' else 540) if live_fast_mode else HISTORY_DAYS
                    jobs[k_tf] = pool.submit(
                        load_bars, symbol, k_tf, now=now, end=end,
                        history_days=h_days, force=force_refresh,
                    )
                sources = {k_tf: job.result() for k_tf, job in jobs.items()}
            if any(m['quality']['rejected'] for _, m in sources.values()):
                raise DataError('Verworfene Anbieterzeilen: normalen Einzelabruf verwenden.', 422)
            meta = dict(symbol=symbol, feed='iex', adjustment='raw', provider='Alpaca')
    value = register(sources, meta, guard=guard,
                     through=max(int(at.timestamp()), max(rows[-1].end for rows, _ in sources.values())))
    view = value.view(int(at.timestamp()), tf, engine, analysis == '1', historical=bool(asof or dataset_id))
    return {'window': value.window(), 'view': view}


def get(query):
    from server import parse_cutoff
    from fan_chart import selected_engine
    if any(len(values) != 1 for values in query.values()):
        raise DataError('Parameter mehrfach angegeben.', 400)
    value = session(query.get('session', [''])[0])
    at = parse_cutoff(query.get('asof', [''])[0], datetime.now(timezone.utc))
    analysis = query.get('analysis', ['0'])[0]
    if analysis not in ('0', '1'):
        raise DataError('analysis=0/1 erwartet.', 400)
    historical = query.get('historical', ['1'])[0]
    if historical not in ('0', '1'):
        raise DataError('historical=0/1 erwartet.', 400)
    return value.view(int(at.timestamp()), query.get('timeframe', ['4h'])[0], selected_engine(query), analysis == '1', historical=historical == '1')


def freeze(body):
    from snapshots import remember, save_snapshot
    from server import parse_cutoff
    if not isinstance(body, dict) or set(body) != {'session', 'asof', 'timeframe', 'engine'}:
        raise DataError('Ungültiger Replay-Stand.', 400)
    at = parse_cutoff(body['asof'], datetime.now(timezone.utc))
    p = session(body['session']).view(int(at.timestamp()), body['timeframe'], body['engine'], True, full=True)
    return save_snapshot(remember(p))
