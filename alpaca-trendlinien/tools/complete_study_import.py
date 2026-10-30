"""Pin a declared larger free-IEX universe. Reads market data, never outcomes/orders."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from alpaca import load_bars
from datasets import digest, save_dataset, read_dataset
from lab_data import resample_regular, NORMALIZATION
from settings import data_dir
from storage import preflight

SYMBOLS = tuple(sorted(('AAPL ADBE AMD AMZN AVGO BAC CAT COST CVX GOOGL GS HD JNJ JPM KO MA META MSFT NVDA ORCL PG UNH V WMT XOM '
    'CSCO INTC QCOM TXN IBM NOW CRM INTU AMAT MU DIS NFLX PEP MCD SBUX NKE LOW TGT RTX LMT GE HON UPS DE BA ABBV MRK PFE LLY ABT C WFC MS AXP SCHW').split()))
END = datetime(2026, 10, 21, 20, tzinfo=timezone.utc)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False), 'utf-8')
    temporary.replace(path)


def import_one(symbol):
    started = time.monotonic()
    try:
        fine, meta = load_bars(symbol, '5m', history_days=3650, end=END, feed='iex', adjustment='split')
        if meta.get('warning') or meta.get('quality', {}).get('rejected'):
            raise ValueError('Stale or invalid source')
        frames, quality = resample_regular(fine)
        if any(len(b) < 3 for b in frames.values()):
            raise ValueError('Insufficient complete regular source bars')
        sources = {tf: (bars, {**meta, 'normalization': NORMALIZATION, 'rthQuality': quality,
            'count': len(bars), 'first': bars[0].time, 'last': bars[-1].time, 'lastClose': bars[-1].end}) for tf, bars in frames.items()}
        identity = save_dataset(symbol, sources, feed='iex', adjustment='split',
            session='XNYS regular; open-anchored buckets; final 4h bucket may be shorter; execution 5m')
        return {'id': identity, 'symbol': symbol, 'counts': {tf: len(b) for tf, b in frames.items()},
            'first': {tf: b[0].time for tf, b in frames.items()}, 'last': {tf: b[-1].end for tf, b in frames.items()},
            'missingBuckets': quality['missingBuckets'], 'seconds': round(time.monotonic()-started, 2)}
    except Exception as exc:
        return {'symbol': symbol, 'error': str(exc), 'errorType': type(exc).__name__}


def run(root, workers=3):
    root = Path(root).resolve()
    contract = {'version': 'tori-complete-import-1', 'symbols': list(SYMBOLS), 'historyDays': 3650,
        'endAt': int(END.timestamp()), 'feed': 'iex', 'adjustment': 'split', 'normalization': NORMALIZATION,
        'dataDir': str(data_dir()), 'planHash': __import__('hashlib').sha256((Path(__file__).resolve().parents[1]/'TORI-GESAMTTEST-PLAN.md').read_bytes()).hexdigest()}
    cp, ip = root/'import-contract.json', root/'imports.json'
    if cp.exists() and json.loads(cp.read_text('utf-8')) != contract:
        raise ValueError('Import contract changed; use a new run directory')
    preflight(history_days=3650*4, symbols=len(SYMBOLS))
    write(cp, contract)
    imports = json.loads(ip.read_text('utf-8')) if ip.exists() else {}
    pending = []
    for symbol in SYMBOLS:
        if symbol in imports and imports[symbol].get('id'):
            read_dataset(imports[symbol]['id'])
            continue
        pending.append(symbol)
    # Threads share the adapter's single request budget. Only the main thread
    # writes the manifest; concurrent completions cannot lose pinned entries.
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(import_one, s): s for s in pending}
        for future in as_completed(futures):
            symbol = futures[future]
            imports[symbol] = future.result()
            write(ip, imports)
            print(json.dumps(imports[symbol]), flush=True)
    print(json.dumps({'done': True, 'symbols': len(imports), 'available': sum(bool(v.get('id')) for v in imports.values()), 'contractHash': digest(contract)}), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', required=True)
    p.add_argument('--workers', type=int, choices=(1, 2, 3), default=3)
    args = p.parse_args()
    run(args.root, args.workers)
