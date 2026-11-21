"""Independently recompute persisted radar distances, ATR, clocks and result counts."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from bisect import bisect_right
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import math
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datasets import read_dataset, source_bars
from early_warning_study import checked, load_block
from fan_study import source_gaps, schedule, timestamp
from models import NY
from strategy_screen import read, write


def near(a, b):
    assert math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-8), (a, b)


def verify(root, selected=None):
    root = Path(root); plan = checked(read(root/'plan.json')); result = read(root/'results.json')
    if selected is not None:
        assert len(set(selected)) == len(selected) and set(selected) <= set(plan['symbols'])
    counts = defaultdict(Counter); deliveries = defaultdict(Counter)
    warning_count = 0
    first = min(timestamp(w['start']) for w in plan['windows'])
    last = max(timestamp(w['end'], upper=True) for w in plan['windows'])
    with patch('alpaca._request', side_effect=AssertionError('Offline verification')):
        for symbol in (plan['symbols'] if selected is None else selected):
            block = load_block(root, plan, symbol)
            frames = source_bars(read_dataset(plan['datasets'][symbol]))
            rows = [b for b in frames['4h'] if b.time >= first-plan['warmupDays']*86400 and b.end <= last]
            daily = [b for b in frames['1D'] if b.end <= last]
            daily_ends = [b.end for b in daily]
            expected_daily = [end for _, end in schedule(min(rows[0].time, daily[0].time), last, '1D')]
            gaps = source_gaps(rows, rows[-1].end, '4h')
            # Independent Wilder recurrence, including resets at missing source bars.
            atrs = []; seed = []; atr = None; previous = None
            for i, b in enumerate(rows):
                if i in gaps: seed = []; atr = None; previous = None
                tr = b.high-b.low if previous is None else max(b.high-b.low, abs(b.high-previous.close), abs(b.low-previous.close))
                if atr is None:
                    seed.append(tr)
                    if len(seed) == 14: atr = sum(seed)/14
                else: atr = (atr*13+tr)/14
                atrs.append(atr); previous = b
            ids = set()
            for r in block['records']:
                assert r['id'] not in ids; ids.add(r['id'])
                assert len({w['stage'] for w in r['warnings']}) == len(r['warnings'])
                assert len(r['warnings']) <= 2
                for w in r['warnings']:
                    warning_count += 1
                    f, s = w['features'], w['snapshot']
                    idx = f['sourceIndex']; b = rows[idx]
                    assert b.end == w['at'] == s['knownAt'] == f['knownAt']
                    assert idx == s['sourceIndex']
                    near(f['atr'], atrs[idx])
                    line = s['line']
                    level = line['a_price']+line['slope']*(idx-line['a_index'])
                    signed = level-b.close if r['family'] == 'breakout' else b.close-level
                    near(f['distanceATR'], signed/atrs[idx]); near(f['distancePct'], 100*signed/b.close)
                    threshold = float(r['policy'].split(':')[1])
                    assert -.00000001 <= f['distanceATR'] <= threshold+.00000001
                    for ln in (s['line'], s['green'], s['red']):
                        if not ln: continue
                        assert ln['knownAt'] <= w['at']
                        assert rows[ln['a_index']].time == ln['a_time']
                        assert all(p['known_at'] <= w['at'] for p in ln.get('contactPoints', []))
                    for label in ('lineValue', 'cleanThresholdAtCurrentATR'):
                        if label.startswith('clean') and r['family'] == 'safety_bounce':
                            assert f['projection'][label] is None
                            continue
                        target = line['a_price']+line['slope']*(idx+2-line['a_index'])
                        if label.startswith('clean'): target += .15*atrs[idx]
                        near(f['projection'][label], target)
                    n = bisect_right(daily_ends, w['at']); expected = bisect_right(expected_daily, w['at'])
                    clean = n >= 200 and expected >= 200 and daily_ends[n-200:n] == expected_daily[expected-200:expected]
                    wanted = sum(b.close for b in daily[n-200:n])/200 if clean else None
                    actual = f['daily']['dailySma200']
                    if wanted is None: assert actual is None
                    else: near(actual, wanted)
                for window in plan['windows']:
                    if not block['eligibility'][window['name']]: continue
                    a, z = timestamp(window['start']), timestamp(window['end'], upper=True)
                    key = r['policy'], r['family']; counter = counts[key]
                    first_warning = next((w for w in r['warnings'] if w['stage'] == 2), None)
                    e = r['entry']; warning_in = first_warning is not None and a <= first_warning['at'] <= z
                    entry_in = e is not None and a <= e['at'] <= z and e['validRisk']
                    if entry_in:
                        counter['entries'] += 1
                        if warning_in and first_warning['at'] < e['at'] and e['activeAtSignal']:
                            counter['coveredEntries'] += 1
                    for at in set(w['at'] for w in r['warnings'] if a <= w['at'] <= z):
                        deliveries[key][datetime.fromtimestamp(at, NY).date().isoformat()] += 1
                    if warning_in:
                        counter['warnings'] += 1
                        if entry_in and e['activeAtSignal'] and first_warning['at'] < e['at']:
                            counter['confirmed'] += 1
                        elif r['outcome']['at'] > z or r['outcome']['censored'] or r['outcome']['reason'] == 'data_end':
                            counter['censored'] += 1
                        else: counter['fizzled'] += 1
            print(symbol, 'verified', warning_count, flush=True)
    if selected is not None:
        return {'planId': plan['id'], 'symbols': list(selected), 'counts': dict(counts),
                'deliveries': dict(deliveries), 'warningCount': warning_count}
    return finish(root, plan, result, counts, deliveries, warning_count)


def finish(root, plan, result, counts, deliveries, warning_count):
    for g in result['groups']:
        key = g['policy'], g['family']
        for field in ('entries', 'coveredEntries', 'warnings', 'confirmed', 'fizzled', 'censored'):
            assert counts[key][field] == g[field], (key, field, counts[key][field], g[field])
        assert dict(deliveries[key]) == g['daily']
        assert g['warnings'] == g['confirmed']+g['fizzled']+g['censored']
        if g['entries']: near(g['recallPct'], 100*g['coveredEntries']/g['entries'])
        near(g['messagesPerSession'], sum(deliveries[key].values())/result['sessions'])
    receipt = {'planId': plan['id'], 'symbols': len(plan['symbols']), 'warningSnapshotsChecked': warning_count,
               'allGroupCountsChecked': len(result['groups']), 'providerCalls': 0,
               'verifierHash': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    write(root/'verification.json', receipt)
    return receipt


def verify_parallel(root, workers=1):
    if type(workers) is not int or not 1 <= workers <= 4:
        raise ValueError('Use 1–4 independent audit workers.')
    if workers == 1:
        return verify(root)
    root = Path(root); plan = checked(read(root/'plan.json')); result = read(root/'results.json')
    groups = [plan['symbols'][i::workers] for i in range(workers)]
    counts, deliveries = defaultdict(Counter), defaultdict(Counter)
    warning_count = 0; seen = set()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        pending = [pool.submit(verify, root, group) for group in groups if group]
        for completed in as_completed(pending):
            part = completed.result()
            assert part['planId'] == plan['id'] and not seen.intersection(part['symbols'])
            seen.update(part['symbols']); warning_count += part['warningCount']
            for key, values in part['counts'].items(): counts[key].update(values)
            for key, values in part['deliveries'].items(): deliveries[key].update(values)
    assert seen == set(plan['symbols']), 'Incomplete audit coverage'
    return finish(root, plan, result, counts, deliveries, warning_count)


if __name__ == '__main__':
    import json
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--root', required=True)
    parser.add_argument('--workers', type=int, default=1)
    args = parser.parse_args()
    print(json.dumps(verify_parallel(args.root, args.workers)), flush=True)
