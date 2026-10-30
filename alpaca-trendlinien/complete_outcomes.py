"""Post-signal no-target exits; never imported by the entry selection engine."""
from bisect import bisect_left, bisect_right
from copy import deepcopy
from datetime import datetime
from functools import lru_cache

from complete_strategy import RULES, source_grid
from datasets import digest, source_bars
from entry_geometry import at
from lab_data import session_bounds
from lab_metrics import expected_grid
from lab_splits import sessions_between
from models import NY
from safety_strategy import StrategyContext
from tori_entries import atr

EXITS = ('fixed', 'higher_low', 'higher_low_green', 'friday')


def confirmed_higher_low(rows, i, entry_at, last_low):
    """Returns an already confirmed pullback; no diagonal connection required."""
    side, j = RULES['pivotSide'], i-RULES['pivotSide']
    if j < side or rows[j].time <= entry_at: return None
    if not all(rows[j].low < rows[k].low for k in range(j-side, j+side+1) if k != j): return None
    vol = atr(rows[max(0, i-14):i+1])
    if vol is None or rows[j].low <= last_low or rows[i].close-rows[j].low < RULES['reactionATR']*vol:
        return None
    return {'low': rows[j].low, 'pivotAt': rows[j].time, 'knownAt': rows[i].end,
            'stop': rows[j].low-max(RULES['tick'], RULES['stopATR']*vol)}


class Outcomes:
    def __init__(self, dataset, timeframe, cutoff):
        self.sources = {tf: [b for b in rows if b.end <= cutoff] for tf, rows in source_bars(dataset).items()}
        self.tf, self.cutoff, self.symbol = timeframe, cutoff, dataset['material']['symbol']
        self.rows, self.fine = self.sources[timeframe], self.sources['5m']
        self.times, self.ends = [b.time for b in self.fine], [b.end for b in self.rows]
        self.expected = list(expected_grid(self.fine[0].time, cutoff))
        self.expected_index = {t: i for i, t in enumerate(self.expected)}
        self.source_grid = list(source_grid(self.rows[0].time, cutoff, timeframe))
        self.source_ends = [end for _, end in self.source_grid]
        self.by_end = {b.end: j for j, b in enumerate(self.rows)}
        self.context = StrategyContext(self.sources, cutoff)
        self.days = sessions_between(str(datetime.fromtimestamp(self.fine[0].time, NY).date()),
                                     str(datetime.fromtimestamp(cutoff, NY).date()))
        self.daily_by_day = {str(datetime.fromtimestamp(b.time, NY).date()): b for b in self.sources['1D']}
        self.cache = {}

    def intermediate(self, e):
        day = str(datetime.fromtimestamp(e['entryAt'], NY).date())
        start = bisect_right(self.days, day)
        out = {}
        for horizon in (5, 10, 20, 60):
            index = start+horizon-1
            wanted = self.days[index] if index < len(self.days) else None
            b = self.daily_by_day.get(wanted)
            out[str(horizon)] = {'day': wanted, 'status': 'known' if b else 'unknown',
                'netReturnPct': ((b.close*(1-RULES['sideCost']))/(e['entryPrice']*(1+RULES['sideCost']))-1)*100 if b else None,
                'close': b.close if b else None, 'reason': None if b else 'missing_daily_or_boundary'}
        return out

    def path(self, e, model):
        if model not in EXITS: raise ValueError('Unknown exit variant')
        key = digest([e['entryAt'], e['entryPrice'], e['initialStop'], e['green'], model, self.cutoff])
        if key in self.cache: return deepcopy(self.cache[key])
        if model == 'friday' and self.tf == '1D':
            result = {'status': 'unsupported', 'reason': 'daily_friday_close_not_executable_before_weekend', 'events': []}
        else:
            result = self._path(e, model)
        result.update(outcomeId=key, model=model, entryAt=e['entryAt'], initialStop=e['initialStop'])
        self.cache[key] = result
        return deepcopy(result)

    def _path(self, e, model):
        price, entry_at, stop = e['entryPrice'], e['entryAt'], e['initialStop']
        buy = price*(1+RULES['sideCost'])
        risk = buy-stop
        if not 0 < stop < price or risk <= 0:
            return {'status': 'invalid', 'reason': 'invalid_initial_risk', 'events': []}
        fine_i, expected_i = bisect_left(self.times, entry_at), bisect_left(self.expected, entry_at)
        if fine_i >= len(self.fine) or self.fine[fine_i].time != entry_at or expected_i >= len(self.expected) or self.expected[expected_i] != entry_at:
            return {'status': 'unknown', 'reason': 'missing_entry_open', 'events': []}
        source_i = bisect_right(self.source_ends, entry_at-RULES['latency'])
        last_low, events, exit_signal = e['greenLevel'], [], None
        result = {'status': 'open', 'events': events, 'exitAt': None, 'netR': None, 'netReturnPct': None,
                  'buy': buy, 'initialRisk': risk, 'forcedTimeExit': False}
        for bar in self.fine[fine_i:]:
            if expected_i >= len(self.expected) or bar.time != self.expected[expected_i]:
                return {**result, 'status': 'unknown', 'reason': 'missing_fine_path',
                        'missingAt': self.expected[expected_i] if expected_i < len(self.expected) else bar.time}
            expected_i += 1
            if bar.time == entry_at and bar.open != price:
                return {**result, 'status': 'invalid', 'reason': 'entry_price_mismatch'}
            # All stop changes below become effective at this 5m OPEN, after
            # their source candle closed plus latency, never inside its past.
            while source_i < len(self.source_ends) and self.source_ends[source_i]+RULES['latency'] <= bar.time:
                end = self.source_ends[source_i]
                source_i += 1
                if end <= e['signalAt']: continue
                j = self.by_end.get(end)
                if j is None:
                    return {**result, 'status': 'unknown', 'reason': 'missing_source_close', 'missingAt': end}
                current = self.rows[j]
                if model in ('higher_low_green', 'friday') and current.close < at(e['green'], j):
                    exit_signal = 'green_close'
                if model != 'fixed':
                    update = confirmed_higher_low(self.rows, j, entry_at, last_low)
                    if update:
                        last_low = update['low']
                        if update['stop'] > stop:
                            events.append({**update, 'kind': 'stop_raise', 'effectiveAt': bar.time,
                                           'previousStop': stop, 'newStop': update['stop']})
                            stop = update['stop']
                if model == 'friday' and datetime.fromtimestamp(current.end, NY).weekday() == 4:
                    bounds = session_bounds(str(datetime.fromtimestamp(current.end, NY).date()))
                    # Confirm in time to execute during Friday RTH. A daily
                    # closing candle cannot be acted on before that close.
                    if bounds[1]-3*3600 <= current.end < bounds[1] and bar.time < bounds[1] and current.close*(1-RULES['sideCost']) > buy:
                        market = self.context.known_context(current.end)
                        vol = atr(self.rows[max(0, j-14):j+1]) or 0
                        near = any(z['lower']-.25*vol <= current.close <= z['upper'] for z in market['zones'])
                        if near: exit_signal = 'friday_resistance'
            reason, raw, opened = None, None, False
            if bar.open <= stop: reason, raw, opened = 'stop_gap', bar.open, True
            elif exit_signal: reason, raw, opened = exit_signal, bar.open, True
            elif bar.low <= stop: reason, raw = 'stop', stop
            if reason:
                sell = raw*(1-RULES['sideCost'])
                return {**result, 'status': 'closed', 'reason': reason, 'exitAt': bar.time if opened else bar.end,
                        'fillBarAt': bar.time, 'rawExit': raw, 'sell': sell, 'netR': (sell-buy)/risk,
                        'netReturnPct': (sell/buy-1)*100, 'finalStop': stop, 'atOpen': opened}
        if expected_i < len(self.expected):
            return {**result, 'status': 'unknown', 'reason': 'missing_fine_tail', 'missingAt': self.expected[expected_i]}
        last = self.fine[-1]
        return {**result, 'reason': 'data_boundary', 'markAt': last.end, 'markPrice': last.close,
                'markNetR': (last.close*(1-RULES['sideCost'])-buy)/risk,
                'markNetReturnPct': (last.close*(1-RULES['sideCost'])/buy-1)*100, 'finalStop': stop}
