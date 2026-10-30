"""Independent journal/price/summary auditor; no call to the exit evaluator."""
import argparse
from bisect import bisect_left
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import mean
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from complete_strategy import RULES
from datasets import digest, read_dataset, source_bars
from lab_data import session_bounds
from lab_metrics import expected_grid
from lab_splits import sessions_between
from models import NY
from tools.complete_study_import import write


def level(ray, i): return ray['a_price']+(i-ray['a_index'])*ray['slope']


def reactions(rows, ray, end, upper, width, volatility):
    # Independent state reconstruction: locate contact runs, requiring a
    # genuinely later departure before permitting the next contact.
    count, last, left = 0, None, False
    for j in range(ray['a_index'], end+1):
        value = level(ray, j)
        wick = rows[j].high if upper else rows[j].low
        if abs(wick-value) <= width+1e-7:
            if last is None or left and j-last >= 2: count += 1
            last, left = j, False
        elif last is not None:
            distance = value-width-rows[j].close if upper else rows[j].close-value-width
            if distance >= .5*volatility: left = True
    return count


def check_path(e, p, fine, rows, cutoff, prepared=None):
    status = p['status']
    if status == 'unsupported':
        assert p['model'] == 'friday' and e['timeframe'] == '1D'
        return 0
    if status == 'invalid': return 0
    assert status in ('closed', 'open', 'unknown')
    buy = e['entryPrice']*(1.00075)
    risk, stop = buy-e['initialStop'], e['initialStop']
    journal = sorted(p['events'], key=lambda v: v['effectiveAt'])
    for v in journal:
        assert v['effectiveAt'] >= v['knownAt']+300
        assert v['newStop'] > v['previousStop']
        j = next(i for i,b in enumerate(rows) if b.end == v['knownAt'])
        k = next(i for i,b in enumerate(rows) if b.time == v['pivotAt'])
        assert j == k+2 and rows[k].time > e['entryAt']
        assert all(rows[k].low < rows[t].low for t in (k-2,k-1,k+1,k+2))
        tr = [max(b.high-b.low, abs(b.high-a.close), abs(b.low-a.close)) for a,b in zip(rows[j-14:j],rows[j-13:j+1])]
        assert len(tr) == 14
        expected_stop = rows[k].low-max(.01,.25*mean(tr))
        assert abs(expected_stop-v['newStop']) < 1e-8
    if prepared is None:
        prepared = {'times': [b.time for b in fine],
                    'expected': list(expected_grid(fine[0].time, fine[-1].end))}
    first = bisect_left(prepared['times'], e['entryAt'])
    assert first < len(fine) and fine[first].time == e['entryAt']
    expected = prepared['expected']
    n, journal_i = bisect_left(expected, e['entryAt']), 0
    visited = 0
    for fine_index in range(first, len(fine)):
        b = fine[fine_index]
        if status == 'closed' and b.time > p['fillBarAt']: break
        if status == 'unknown' and b.time >= p['missingAt']: break
        if status == 'open' and b.end > cutoff: break
        assert n < len(expected) and b.time == expected[n], (e['id'], status, 'gap hidden')
        n += 1; visited += 1
        while journal_i < len(journal) and journal[journal_i]['effectiveAt'] <= b.time:
            v = journal[journal_i]
            assert abs(v['previousStop']-stop) < 1e-8
            stop = v['newStop']; journal_i += 1
        if status == 'closed' and b.time == p['fillBarAt']:
            reason = p['reason']
            if reason == 'stop_gap': assert b.open <= stop and p['rawExit'] == b.open
            elif reason == 'stop': assert b.open > stop and b.low <= stop and abs(p['rawExit']-stop) < 1e-8
            else:
                assert reason in ('green_close', 'friday_resistance') and p['rawExit'] == b.open
                known = [(j,r) for j,r in enumerate(rows) if e['signalAt'] < r.end <= b.time-300]
                if reason == 'green_close':
                    assert any(r.close < level(e['green'], j) for j,r in known)
                else:
                    assert e['timeframe'] == '4h' and datetime.fromtimestamp(b.time, NY).weekday() == 4
                    assert b.time < session_bounds(str(datetime.fromtimestamp(b.time, NY).date()))[1]
            sell = p['rawExit']*.99925
            assert abs(p['netR']-(sell-buy)/risk) < 1e-8
            assert abs(p['netReturnPct']-(sell/buy-1)*100) < 1e-8
            break
        assert b.open > stop and b.low > stop, (e['id'], p['model'], 'missed earlier stop')
    if status == 'unknown': assert p['netR'] is None
    if status == 'closed': assert p['exitAt'] <= cutoff
    if status == 'open':
        assert p['forcedTimeExit'] is False and p['exitAt'] is None
        assert p['markAt'] <= cutoff
        last = next(b for b in reversed(fine) if b.end <= cutoff)
        assert p['markAt'] == last.end and p['markPrice'] == last.close
        assert abs(p['markNetR']-(last.close*.99925-buy)/risk) < 1e-8
        assert abs(p['markNetReturnPct']-(last.close*.99925/buy-1)*100) < 1e-8
    return visited


def run(root):
    root = Path(root).resolve()
    contract = json.loads((root/'study-contract.json').read_text('utf-8'))
    imports = json.loads((root/'imports.json').read_text('utf-8'))
    assert contract['datasets'] == {s: v.get('id') for s,v in sorted(imports.items())}
    counters, prices = Counter(), Counter()
    grouped = defaultdict(list)
    cached_id, cached_sources, cached_prepared = None, None, None
    for destination in sorted((root/'studies').glob('*.json')):
        block = json.loads(destination.read_text('utf-8'))
        assert block['contractHash'] == digest(contract)
        assert block['checksum'] == digest({k:v for k,v in block.items() if k != 'checksum'})
        assert block['datasetId'] == imports[block['symbol']]['id']
        if cached_id != block['datasetId']:
            cached_sources = source_bars(read_dataset(block['datasetId']))
            cached_id = block['datasetId']
            cached_fine = cached_sources['5m']
            cached_prepared = {'times': [b.time for b in cached_fine],
                               'expected': list(expected_grid(cached_fine[0].time, cached_fine[-1].end))}
        sources = cached_sources
        rows, fine = sources[block['timeframe']], sources['5m']
        by_end = {b.end: i for i,b in enumerate(rows)}
        signals = json.loads((root/'signals'/destination.name).read_text('utf-8'))
        assert [{k:v for k,v in e.items() if k not in ('paths','intermediate')} for e in block['entries']] == signals['entries']
        assert len({e['id'] for e in block['entries']}) == len(block['entries'])
        counters['blocks'] += 1
        audited = set()
        for e in block['entries']:
            assert e['entryAt'] >= e['signalAt']+300
            assert rows[e['signalIndex']].end == e['signalAt']
            assert e['geometryStrict'] == (block['geometry'] == 'strict')
            if not contract['events']['available']:
                assert e['fullyCompliant'] is False and e['checks']['events'] is None
                assert e['profile'] != 'all_events'
            q = by_end[e['info']['qualifiedAt']]
            ray = e['green'] if e['family'] == 'bounce' else e['red']
            assert reactions(rows, ray, q, e['family'] != 'bounce', e['actionWidth'], e['actionATRAtCreation']) == e['info']['contacts']
            assert q < e['signalIndex']
            if e['family'] == 'retest': assert q < e['breakIndex'] < e['signalIndex']
            if block['geometry'] == 'strict':
                for j in range(ray['a_index'], q+1):
                    price = rows[j].low if e['family'] == 'bounce' else rows[j].high
                    assert price+1e-7 >= level(ray,j) if e['family'] == 'bounce' else price <= level(ray,j)+1e-7
                for j in range(e['green']['a_index'], e['signalIndex']+1):
                    assert rows[j].low+1e-7 >= level(e['green'],j)
            green_end = by_end[e['greenInfo']['qualifiedAt']]
            assert reactions(rows, e['green'], green_end, False, e['greenWidth'], e['greenATRAtCreation']) == e['greenInfo']['contacts']
            assert abs(e['initialStop']-(e['greenLevel']-max(.01,.25*e['signalATR']))) < 1e-8
            early = datetime.fromtimestamp(e['entryAt'], NY).year <= 2023
            cutoff = int(datetime(2023,12,31,23,59,tzinfo=timezone.utc).timestamp()) if early else block['endAt']
            for model,p in e['paths'].items():
                if p['outcomeId'] not in audited:
                    counters['auditedFineBars'] += check_path(e,p,fine,rows,cutoff,cached_prepared)
                    audited.add(p['outcomeId']); counters['uniquePaths'] += 1
            counters['entries'] += 1
            for phase in ('all','2021-2023' if early else '2024-2026'):
                grouped['/'.join((e['geometry'],e['timeframe'],e['profile'],e['family'],phase))].append(e)
        print(json.dumps({'audited': destination.name, 'entries': counters['entries'], 'uniquePaths': counters['uniquePaths']}), flush=True)
    summary = json.loads((root/'summary.json').read_text('utf-8'))
    for key,g in summary['groups'].items():
        entries = grouped[key]
        assert g['entries'] == len(entries)
        for model,stats in g['exits'].items():
            known = [e['paths'][model]['netR'] for e in entries if e['paths'][model]['status'] == 'closed']
            assert stats['closed'] == len(known)
            assert stats['meanR'] is None if not known else abs(stats['meanR']-mean(known)) < 1e-10
    result = {'passed': True, **dict(counters), 'contractHash': digest(contract),
              'scope': 'Frozen signal files, independent reaction reconstruction, strict wick geometry, temporal execution, stop journals and price path fills, R and summary arithmetic. Not human line agreement or a profitability validation.'}
    write(root/'verification.json', result)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True)
    run(p.parse_args().root)
