"""Real-source replay prefixes and shocked future daily context against full-run alerts."""
import argparse
from dataclasses import replace
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datasets import read_dataset, source_bars
from early_warning import Radar, Rules
from early_warning_study import checked, load_block
from entry_screen import Context
from fan_study import source_gaps, timestamp
from strategy_screen import read, write


def verify(root, symbols):
    root = Path(root); plan = checked(read(root/'plan.json')); checks = []
    first = min(timestamp(w['start']) for w in plan['windows'])
    last = max(timestamp(w['end'], upper=True) for w in plan['windows'])
    config = {**plan['rules'], 'thresholds': tuple(plan['rules']['thresholds']), 'variants': tuple(plan['rules']['variants'])}
    with patch('alpaca._request', side_effect=AssertionError('Offline prefix check')):
        for symbol in symbols:
            block = load_block(root, plan, symbol)
            window = next(w for w in plan['windows'] if block['eligibility'][w['name']])
            begin = timestamp(window['start']); cutoff = min(timestamp(window['end'], upper=True), begin+180*86400)
            frames = source_bars(read_dataset(plan['datasets'][symbol]))
            rows = [b for b in frames['4h'] if b.time >= first-plan['warmupDays']*86400 and b.end <= last]
            daily = [b for b in frames['1D'] if b.end <= last]
            gaps = source_gaps(rows, rows[-1].end, '4h')
            def alerts(records):
                return sorted((r['id'], w['id'], {k: v for k, v in w.items() if k != 'chartUrl'})
                    for r in records for w in r['warnings'] if begin <= w['at'] <= cutoff)
            expected = alerts(block['records'])
            assert expected, symbol
            for shocked in (False, True):
                context_rows = [replace(b, open=b.open*7, high=b.high*7, low=b.low*7, close=b.close*7)
                                if shocked and b.end > cutoff else b for b in daily]
                radar = Radar(symbol, rules=Rules(**config), daily_context=Context(rows, context_rows))
                for i, b in enumerate(rows):
                    if b.end > cutoff: break
                    radar.push(b, gap=i in gaps)
                assert alerts(radar.result()['records']) == expected, (symbol, shocked)
            checks.append({'symbol': symbol, 'cutoff': cutoff, 'alerts': len(expected), 'futureDailyShockUnchanged': True})
            print(symbol, len(expected), 'prefix alerts identical', flush=True)
    receipt = {'planId': plan['id'], 'checks': checks, 'providerCalls': 0}
    write(root/'prefix-verification.json', receipt)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--root', required=True)
    parser.add_argument('--symbols', nargs='+', default=['AAPL', 'MSFT', 'AMZN', 'JPM', 'XOM'])
    args = parser.parse_args(); verify(args.root, args.symbols)
