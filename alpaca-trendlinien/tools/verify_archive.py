"""Offline audit of a historical collection, optionally while it is running.

No credentials/provider requests. Outputs are local artifacts, not source files.
"""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import history_archive as archive
import archive_state
from datasets import path_for, digest, source_bars
from lab_data import session_bounds
from models import NY
from parquet_store import hydrate
from settings import data_dir
from weekly_chart import weeks


def verify_stock(symbol, stock, spec):
    path = path_for(stock['datasetId'])
    manifest = json.loads(path.read_text('utf-8'))
    dataset, weekly = hydrate(manifest, data_dir(), include_weekly=True)
    material = dataset['material']
    assert digest(material) == stock['datasetId'], 'Dataset checksum'
    assert material['symbol'] == symbol and material['feed'] == spec['feed'] and material['adjustment'] == spec['adjustment']
    frames = source_bars(dataset)
    fine = {bar.time: bar for bar in frames['5m']}
    # Independently check every published OHLCV aggregation against its exact
    # source interval. Incomplete buckets must not appear as usable candles.
    for tf, rows in frames.items():
        assert all(b.end <= archive.stamp(spec['end']).timestamp() for b in rows), 'future bar'
        assert all(a.time < b.time and a.end <= b.time for a, b in zip(rows, rows[1:])), 'overlap/order'
        if tf == '5m': continue
        seconds = {'1h': 3600, '4h': 14400, '1D': 86400}[tf]
        for bar in rows:
            opened, closed = session_bounds(datetime.fromtimestamp(bar.time, NY).date().isoformat())
            assert (bar.time-opened) % seconds == 0 and bar.end == min(bar.time+seconds, closed), 'session anchoring'
            base = [fine[t] for t in range(bar.time, bar.end, 300)]
            assert (bar.open, bar.high, bar.low, bar.close, bar.volume) == (
                base[0].open, max(b.high for b in base), min(b.low for b in base), base[-1].close, sum(b.volume for b in base)), 'OHLCV aggregation'
    expected = [asdict(b) for b in weeks(frames['1D'], max(b.end for b in frames['1D']))]
    assert weekly == expected, 'weekly cache'
    assert all(len(rows) == stock['counts'][tf] for tf, rows in frames.items()), 'counts'
    for checkpoint in stock['months'].values(): archive.read_chunk(checkpoint)
    blocks = manifest['storage']['blocks']
    return {'symbol': symbol, 'datasetId': stock['datasetId'], 'verifiedAt': datetime.now(timezone.utc).isoformat(),
            'counts': {**stock['counts'], '1W': len(weekly)}, 'coverage': stock['coverage'],
            'firstDate': datetime.fromtimestamp(frames['5m'][0].time, NY).date().isoformat(),
            'lastDate': datetime.fromtimestamp(frames['5m'][-1].end, NY).date().isoformat(),
            'datasetBytes': path.stat().st_size+sum(b['bytes'] for b in blocks),
            'checkpointBytes': sum(e.get('bytes', 0) for e in stock['months'].values()),
            'missingBuckets': stock['rthQuality']['missingBuckets']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--watch', action='store_true')
    args = parser.parse_args()
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
    report = json.loads(output.read_text('utf-8')) if output.exists() else {'archiveId': args.id, 'stocks': {}, 'errors': {}}
    if report['archiveId'] != args.id: raise ValueError('Report belongs to another archive')
    while True:
        job = archive_state.full(args.id) if archive_state.exists(args.id) else archive.get(args.id)
        for symbol, stock in job['stocks'].items():
            if stock['status'] != 'completed' or symbol in report['stocks'] or symbol in report['errors']: continue
            try:
                report['stocks'][symbol] = verify_stock(symbol, stock, job['spec'])
                print(json.dumps({'verified': symbol, 'count': len(report['stocks'])}), flush=True)
            except Exception as exc:
                report['errors'][symbol] = f'{type(exc).__name__}: {exc}'
                print(json.dumps({'failed': symbol, 'error': report['errors'][symbol]}), flush=True)
            report.update(status=job['status'], expected=len(job['spec']['symbols']), updatedAt=time.time())
            output.write_text(json.dumps(report, indent=2), encoding='utf-8')
        report.update(status=job['status'], expected=len(job['spec']['symbols']), updatedAt=time.time())
        output.write_text(json.dumps(report, indent=2), encoding='utf-8')
        if not args.watch or job['status'] not in ('pending', 'running'): break
        time.sleep(10)
    return 1 if report['errors'] else 0


if __name__ == '__main__': sys.exit(main())
