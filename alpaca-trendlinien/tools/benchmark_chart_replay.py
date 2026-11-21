"""Offline, real-HTTP chart replay benchmark. No browser/provider/worker required.

Run from the app root with its normal TORI_DATA_DIR. Writes timings only, not
quotes or credentials. Canonical calculations independently audit sampled views.
"""
import argparse
from bisect import bisect_right
from copy import deepcopy
from datetime import datetime, timezone
import gzip
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import statistics
import sys
import threading
from time import perf_counter
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analysis_service import build_chart
from chart_sources import sources_for, clear as clear_sources
from chart_lane_cache import clear as clear_lanes
from chart_replay import clear as clear_sessions
from fan_chart import apply
from random_replay import candidates
from server import Handler
from snapshots import remember
from weekly_chart import add_weekly


def stats(values):
    values = sorted(values)
    return {'n': len(values), 'meanMs': statistics.mean(values)*1000,
            'medianMs': statistics.median(values)*1000,
            'p95Ms': values[min(len(values)-1, int(len(values)*.95))]*1000,
            'maxMs': max(values)*1000}


def hydrate(p, window):
    p = deepcopy(p)
    for tf, n in p.pop('chartCounts').items():
        bars = window['bars'][tf][:n]
        assert all(b['end'] <= p['analysisCutoff'] for b in bars)
        p['charts'][tf].update(bars=bars, axis=[b['time'] for b in bars])
        if tf in p['lanes']:
            lane = p['lanes'][tf]
            lane['sourceTimes'] = [b['time'] for b in bars]
            if 'context' in lane:
                lane['context']['series'] = {n: window['smas'][tf][n][:count]
                    for n, count in lane['context'].pop('seriesCounts').items()}
    p.update(p['charts'][p['timeframe']])
    p['drawingAxes'] = {tf: p['charts'][tf]['axis']+tail for tf, tail in p.pop('drawingAxisTails').items()}
    return p


class QuietHandler(Handler):
    def log_message(self, *args):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='artifacts/replay-window-benchmark-20261101.json')
    parser.add_argument('--symbols', nargs='+', default=['AAPL', 'MSFT', 'AMZN', 'JPM', 'XOM'])
    args = parser.parse_args()
    report = {'version': 1, 'browser': False, 'providerRequests': 0,
              'scope': 'local verified market archives; HTTP + gzip + JSON decode; no DOM/GPU rendering',
              'symbols': [], 'measurements': [], 'checks': 0}
    server = ThreadingHTTPServer(('127.0.0.1', 0), QuietHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    root = f'http://127.0.0.1:{server.server_port}'
    def request(path, **query):
        started = perf_counter()
        with urlopen(Request(root+path+'?'+urlencode(query), headers={'Accept-Encoding': 'gzip'}), timeout=120) as response:
            raw = response.read(); size = len(raw)
            p = json.loads(gzip.decompress(raw) if response.headers.get('Content-Encoding') == 'gzip' else raw)
        return p, perf_counter()-started, size
    pool = candidates()
    try:
        with patch('alpaca._request', side_effect=AssertionError('Benchmark must stay offline')):
            for symbol in args.symbols:
                clear_sources(); clear_lanes(); clear_sessions()
                identity = pool[symbol][0]
                # Opening includes full initial dataset checksum verification, not a prewarmed read.
                opened, elapsed, size = request('/api/replay/open', dataset=identity, symbol=symbol,
                    timeframe='4h', asof='2026-05-29T20:00:00Z', analysis='0')
                window = opened['window']; session_id = window['id']
                inputs, meta = sources_for(identity)
                inputs = {tf: (rows, {**m, 'mode': 'immutable-dataset', 'cached': True, 'warning': None})
                          for tf, (rows, m) in inputs.items()}
                ends = {tf: [b['end'] for b in rows] for tf, rows in window['bars'].items()}
                row = {'symbol': symbol, 'datasetId': identity, 'feed': meta['feed'], 'adjustment': meta['adjustment'],
                       'openSeconds': elapsed, 'initialGzipBytes': size,
                       'bars': {tf: len(rows) for tf, rows in window['bars'].items()}}
                report['symbols'].append(row)
                print(symbol, 'open', round(elapsed, 3), 'seconds', flush=True)
                def view(at, tf, engine, category):
                    p, seconds, size = request('/api/replay/view', session=session_id, timeframe=tf,
                        asof=datetime.fromtimestamp(at, timezone.utc).isoformat(), analysis='1', engine=engine)
                    report['measurements'].append({'symbol': symbol, 'engine': engine, 'category': category,
                        'timeframe': tf, 'cutoff': at, 'seconds': seconds, 'gzipBytes': size})
                    return p
                def audit(p, engine):
                    at = datetime.fromtimestamp(p['analysisCutoff'], timezone.utc)
                    tf = p['timeframe']
                    started = perf_counter()
                    expected = build_chart(inputs, symbol, '1D' if tf == '1W' else tf, at,
                        datetime.now(timezone.utc), historical=True, include_analysis=engine == 'legacy')
                    expected.update({k: v for k, v in meta.items() if k != 'normalization'})
                    add_weekly(expected, tf)
                    if engine != 'legacy': apply(expected, engine)
                    remember(expected)
                    raw = json.dumps(expected).encode()
                    json.loads(gzip.decompress(gzip.compress(raw, compresslevel=3)))
                    report['measurements'].append({'symbol': symbol, 'engine': engine, 'category': 'old_full_response',
                        'timeframe': tf, 'cutoff': p['analysisCutoff'], 'seconds': perf_counter()-started})
                    actual = hydrate(p, window)
                    for key in ('bars', 'axis', 'latest', 'sources', 'charts', 'lanes', 'fingerprint', 'drawingAxes', 'rulesVersion'):
                        assert actual[key] == expected[key], (symbol, engine, tf, key)
                    report['checks'] += 1
                for engine in ('legacy', 'fan_master'):
                    for date in ('2024-03-01T20:00:00+00:00', '2025-08-01T20:00:00+00:00', '2026-05-29T20:00:00+00:00'):
                        wanted = int(datetime.fromisoformat(date).timestamp())
                        index = bisect_right(ends['4h'], wanted)-1
                        at = ends['4h'][index]
                        p = view(at, '4h', engine, 'date_jump')
                        audit(p, engine)
                        for offset in range(1, 9):
                            p = view(ends['4h'][index+offset], '4h', engine, 'forward_new')
                        audit(p, engine)
                        for offset in range(7, -1, -1):
                            view(ends['4h'][index+offset], '4h', engine, 'back_visited')
                        for tf in ('1h', '1D', '1W'):
                            j = bisect_right(ends[tf], at)-1
                            for offset in range(1, 4):
                                p = view(ends[tf][j+offset], tf, engine, 'interval_forward')
                            audit(p, engine)
                        print(symbol, engine, date[:10], 'OK', flush=True)
                Path(args.output).parent.mkdir(parents=True, exist_ok=True)
                Path(args.output).write_text(json.dumps(report, indent=2), encoding='utf-8')
    finally:
        server.shutdown(); server.server_close(); thread.join()
    groups = {}
    for p in report['measurements']:
        groups.setdefault((p['engine'], p['category']), []).append(p['seconds'])
    report['summary'] = {engine+' / '+category: stats(values) for (engine, category), values in groups.items()}
    Path(args.output).write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'opens': stats([s['openSeconds'] for s in report['symbols']]),
                      'summary': report['summary'], 'checks': report['checks']}, indent=2), flush=True)


if __name__ == '__main__':
    main()
