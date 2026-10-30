"""Frozen complete-criteria replay and exit study. No provider calls after pinning."""
import argparse
from bisect import bisect_left
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
from statistics import mean, median
import sys
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from complete_strategy import CompleteReplay, EventCalendar, VERSION, RULES, PROFILES
from complete_outcomes import Outcomes, EXITS
from datasets import digest, read_dataset
from entry_blind import blind_case, candle_svg
from models import NY
from tools.complete_study_import import write


def engine_hashes():
    root = Path(__file__).resolve().parents[1]
    return {p: hashlib.sha256((root/p).read_bytes()).hexdigest() for p in
        ('complete_strategy.py', 'complete_outcomes.py', 'tools/complete_study.py', 'entry_geometry.py',
         'tori_entries.py', 'safety_strategy.py', 'lab_data.py', 'market_calendar.py', 'entry_watch.py')}


def summarize(blocks):
    groups, coverage, waits = defaultdict(list), [], defaultdict(list)
    for b in blocks:
        coverage.append({k: b[k] for k in ('symbol', 'timeframe', 'geometry', 'sourceBars', 'expectedSourceBars', 'startAt', 'endAt', 'barCounts', 'candidates', 'threeContactCandidates')})
        for e in b['entries']:
            phase = '2021-2023' if datetime.fromtimestamp(e['entryAt'], NY).year <= 2023 else '2024-2026'
            for section in ('all', phase):
                groups[(b['geometry'], b['timeframe'], e['profile'], e['family'], section)].append(e)
        origins = random.Random(f'{VERSION}|{b["symbol"]}|{b["timeframe"]}|{b["geometry"]}').sample(
            range(b['startAt'], b['endAt'], 86400), min(RULES['randomOrigins'], max(0, (b['endAt']-b['startAt'])//86400)))
        for profile in PROFILES:
            times = sorted({e['entryAt'] for e in b['entries'] if e['profile'] == profile})
            for origin in origins:
                j = bisect_left(times, origin)
                waits[(b['geometry'], b['timeframe'], profile)].append((times[j]-origin)/86400 if j < len(times) else None)
    output = {}
    # Include zero groups, otherwise an empty strict calendar profile disappears.
    for geometry in ('strict', 'zone'):
        for tf in ('4h', '1D'):
            for profile in PROFILES:
                for family in ('breakout', 'retest', 'bounce'):
                    for phase in ('all', '2021-2023', '2024-2026'):
                        rows = groups[(geometry, tf, profile, family, phase)]
                        exits = {}
                        for model in EXITS:
                            paths = [e['paths'][model] for e in rows]
                            closed = [p for p in paths if p['status'] == 'closed']
                            values = [p['netR'] for p in closed]
                            gains, losses = sum(v for v in values if v > 0), -sum(v for v in values if v < 0)
                            exits[model] = {'count': len(paths), 'closed': len(closed), 'statuses': dict(Counter(p['status'] for p in paths)),
                                'meanR': mean(values) if values else None, 'medianR': median(values) if values else None,
                                'winPct': 100*sum(v > 0 for v in values)/len(values) if values else None,
                                'meanReturnPct': mean(p['netReturnPct'] for p in closed) if closed else None,
                                'profitFactorR': gains/losses if losses else None,
                                'withoutBestMeanR': mean(sorted(values)[:-1]) if len(values) > 1 else None,
                                'stopRaises': sum(len(p['events']) for p in paths), 'reasons': dict(Counter(p['reason'] for p in paths))}
                        paired = [e for e in rows if all(e['paths'][m]['status'] == 'closed' for m in ('fixed', 'higher_low'))]
                        horizons = {}
                        for h in (5, 10, 20, 60):
                            values = [e['intermediate'][str(h)]['netReturnPct'] for e in rows if e['intermediate'][str(h)]['status'] == 'known']
                            horizons[str(h)] = {'known': len(values), 'unknown': len(rows)-len(values),
                                'meanNetPct': mean(values) if values else None, 'medianNetPct': median(values) if values else None,
                                'positivePct': 100*sum(v > 0 for v in values)/len(values) if values else None}
                        output['/'.join((geometry, tf, profile, family, phase))] = {'entries': len(rows),
                            'stocks': len({e['symbol'] for e in rows}), 'fullyCompliant': sum(e['fullyCompliant'] for e in rows),
                            'years': dict(Counter(str(datetime.fromtimestamp(e['entryAt'], NY).year) for e in rows)),
                            'exits': exits, 'pairedClosed': len(paired),
                            'pairedHigherLowDeltaR': mean(e['paths']['higher_low']['netR']-e['paths']['fixed']['netR'] for e in paired) if paired else None,
                            'intermediate': horizons}
    waiting = {'/'.join(k): {'starts': len(v), 'found': sum(x is not None for x in v),
        'notFoundBeforeEnd': sum(x is None for x in v), 'medianCalendarDaysAmongFound': median(x for x in v if x is not None) if any(x is not None for x in v) else None}
        for k, v in waits.items()}
    return {'groups': output, 'coverage': coverage, 'waiting': waiting,
            'meaning': 'Overlapping case outcomes, not portfolio P/L; zero calendar-qualified entries without point-in-time event coverage. Unknown paths are not losses, wins or zero returns.'}


def run(args):
    root = Path(args.root).resolve()
    imports = json.loads((root/'imports.json').read_text('utf-8'))
    import_contract = json.loads((root/'import-contract.json').read_text('utf-8'))
    calendar = json.loads(Path(args.events).read_text('utf-8')) if args.events else None
    contract = {'version': VERSION, 'rules': RULES, 'profiles': list(PROFILES), 'exits': list(EXITS),
        'importHash': digest(import_contract), 'engine': engine_hashes(), 'timeframes': ['4h', '1D'], 'geometries': ['strict', 'zone'],
        'datasets': {s: v.get('id') for s, v in sorted(imports.items())},
        'events': {'available': calendar is not None, 'hash': digest(calendar) if calendar is not None else None,
                   'meaning': 'Only explicit then-known coverage can pass; absence is unknown, never safe'},
        'outcomePhases': 'Entries <=2023 stop labels at 2023-12-31; later entries at fixed import cutoff. No forced time exit.'}
    cp = root/'study-contract.json'
    if cp.exists() and json.loads(cp.read_text('utf-8')) != contract:
        raise ValueError('Study engine/rules changed; use a new study output directory, explicitly reuse pinned imports')
    write(cp, contract)
    chosen = args.symbols.split(',') if args.symbols else sorted(imports)
    available = [s for s in chosen if imports.get(s, {}).get('id')]
    blocks = []
    with patch('alpaca._request', side_effect=AssertionError('Study is offline after imports')):
        for symbol in available:
            data = read_dataset(imports[symbol]['id'])
            for tf in ('4h', '1D'):
                for geometry in ('strict', 'zone'):
                    destination = root/'studies'/f'{symbol}-{tf}-{geometry}.json'
                    if destination.exists():
                        block = json.loads(destination.read_text('utf-8'))
                        if block['contractHash'] != digest(contract) or block['checksum'] != digest({k: v for k, v in block.items() if k != 'checksum'}):
                            raise ValueError('Changed cached block')
                        if block['datasetId'] != data['id']:
                            raise ValueError('Pinned dataset changed')
                    else:
                        start = time.monotonic()
                        replay = CompleteReplay(data, tf, geometry, import_contract['endAt'], events=EventCalendar(calendar))
                        block = replay.run()
                        # Persist causal entries BEFORE any outcome calculation.
                        write(root/'signals'/f'{symbol}-{tf}-{geometry}.json', {'contractHash': digest(contract), **block})
                        early = int(datetime(2023, 12, 31, 23, 59, tzinfo=timezone.utc).timestamp())
                        evaluators = {False: Outcomes(data, tf, import_contract['endAt']), True: Outcomes(data, tf, early)}
                        for e in block['entries']:
                            evaluator = evaluators[e['entryAt'] < early]
                            e['paths'] = {m: evaluator.path(e, m) for m in EXITS}
                            e['intermediate'] = evaluator.intermediate(e)
                        block.update(contractHash=digest(contract), seconds=time.monotonic()-start)
                        block['checksum'] = digest(block)
                        write(destination, block)
                        # Blind prefix is selected by hash, not by future gain.
                        if geometry == 'strict' and block['entries']:
                            e = min(block['entries'], key=lambda x: digest([symbol, tf, x['id']]))
                            known = replay.rows[:e['signalIndex']+1]
                            public, private = blind_case(symbol, known, e['signalAt'], {})
                            public['timeframe'] = tf
                            private['proposals'] = {'strict': [{'upper': False, 'ray': e['green']}] +
                                ([{'upper': True, 'ray': e['red']}] if e['red'] is not None else [])}
                            write(root/'blind'/f'{symbol}-{tf}.json', public)
                            write(root/'blind-private'/f'{symbol}-{tf}.json', private)
                    blocks.append(block)
                    print(json.dumps({'symbol': symbol, 'tf': tf, 'geometry': geometry, 'entries': len(block['entries']), 'seconds': round(block['seconds'], 2)}), flush=True)
    summary = summarize(blocks)
    summary.update(contractHash=digest(contract), symbols=len(available), requestedSymbols=len(import_contract['symbols']),
                   dataErrors={s: v for s, v in imports.items() if not v.get('id')})
    write(root/('summary.json' if not args.symbols else 'partial-summary.json'), summary)
    print(json.dumps({'done': True, 'blocks': len(blocks), 'symbols': len(available)}), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', required=True)
    p.add_argument('--symbols', help='Explicit technical subset, never rename its summary as full universe')
    p.add_argument('--events', help='Optional then-known event/coverage JSON; omitted means unknown, not event-free')
    run(p.parse_args())
