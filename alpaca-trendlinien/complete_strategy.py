"""Isolated causal operationalization of the supplied Tori criteria.

Shares source-bar geometry primitives with the existing scanner, but never
changes its running rules or state. Outcomes are in complete_outcomes.py.
"""
from bisect import bisect_left, bisect_right
from collections import Counter
from copy import deepcopy
from datetime import datetime, timedelta
from itertools import combinations

from datasets import digest, source_bars
from entry_geometry import at, episodes, equivalent, violation, RULES as GEOMETRY_RULES
from entry_watch import execution_time
from lab_data import require_convention, session_bounds
from lab_metrics import expected_grid
from lab_splits import sessions_between
from models import NY
from safety_strategy import StrategyContext, latest_session_close, latest_week_close
from tori_entries import atr, aggregate, structure

VERSION = 'tori-complete-1'
RULES = {'contactATR': .10, 'reactionATR': .50, 'pivotSide': 2, 'stopATR': .25,
         'momentumATR': .25, 'maxRiskATR': 2., 'maxRiskFraction': .10,
         'roomR': 2., 'latency': 300, 'tick': .01, 'sideCost': .00075,
         'eventSessions': 3, 'warmupDays': 365, 'randomOrigins': 100,
         'windowsDays': [30, 90, 365], 'maxPivots': 10}
PROFILES = ('two', 'three', 'age7', 'momentum', 'safety', 'context_room', 'all_events',
            'age14', 'green3', 'whole_body', 'exact3')
EXTRA_PROFILES = {'age14', 'green3', 'whole_body', 'exact3'}


def source_grid(start, end, timeframe):
    first, last = [str(datetime.fromtimestamp(t, NY).date()) for t in (start, end)]
    for day in sessions_between(first, last):
        opened, closed = session_bounds(day)
        for t in range(opened, closed, 14400 if timeframe == '4h' else 86400):
            b_end = min(t+(14400 if timeframe == '4h' else 86400), closed)
            if start <= t and b_end <= end:
                yield t, b_end


class EventCalendar:
    """Explicit point-in-time coverage. An empty/retrospective list is not proof."""
    def __init__(self, payload=None):
        self.payload = payload or {'coverage': [], 'events': []}

    def check(self, symbol, at_time):
        day = datetime.fromtimestamp(at_time, NY).date()
        future = sessions_between(str(day+timedelta(days=1)), str(day+timedelta(days=15)))[:RULES['eventSessions']]
        end = session_bounds(future[-1])[1]
        covered = any(c['symbol'] == symbol and c['knownAt'] <= at_time and
                      c['fromAt'] <= at_time and c['throughAt'] >= end for c in self.payload['coverage'])
        if not covered:
            return None
        return not any(e['symbol'] == symbol and e['knownAt'] <= at_time and
                       at_time < e['at'] <= end and e['kind'] in ('earnings', 'dividend_announcement')
                       for e in self.payload['events'])


def qualified(checks, profile):
    keys = ['two']
    if profile != 'two': keys += ['three']
    if profile not in ('two', 'three'): keys += ['age7']
    if profile not in ('two', 'three', 'age7'): keys += ['momentum']
    if profile not in ('two', 'three', 'age7', 'momentum'): keys += ['safety']
    if profile in ('context_room', 'all_events') or profile in EXTRA_PROFILES: keys += ['context', 'room']
    if profile == 'all_events': keys += ['events']
    if profile in EXTRA_PROFILES: keys += [profile]
    return all(checks.get(k) is True for k in keys)


class IncrementalGeometry:
    """Same confirmed pivot/band mathematics, incremental pivot discovery.

    No future pivot inspection, no 60-bar expiry. All distinct rays survive to
    signal ranking; a weaker cluster representative cannot hide a stronger ray.
    """
    def __init__(self, bars, symbol, timeframe, model, grid):
        self.bars, self.symbol, self.tf, self.model = bars, symbol, timeframe, model
        self.grid = grid
        self.checked, self.pivots = set(), {True: [], False: []}
        self.last_pivot = 1

    def proposals(self, i):
        rows, side = self.bars, RULES['pivotSide']
        for j in range(self.last_pivot+1, i-side+1):
            for upper in (True, False):
                value = lambda k: rows[k].high if upper else rows[k].low
                if all(value(j) > value(k) if upper else value(j) < value(k)
                       for k in range(j-side, j+side+1) if k != j):
                    self.pivots[upper].append(j)
            self.last_pivot = j
        vol = atr(rows[max(0, i-14):i+1])
        if vol is None or vol <= 0: return []
        width, result = max(RULES['tick'], RULES['contactATR']*vol), []
        for upper in (True, False):
            for window in RULES['windowsDays']:
                selected = [p for p in self.pivots[upper] if rows[p].time >= rows[i].end-window*86400][-RULES['maxPivots']:]
                for a, b in combinations(selected, 2):
                    key = (upper, a, b)
                    if key in self.checked: continue
                    self.checked.add(key)
                    av, bv = (rows[a].high, rows[b].high) if upper else (rows[a].low, rows[b].low)
                    slope = (bv-av)/(b-a)
                    if not (slope < 0 if upper else slope > 0): continue
                    # Reject known incomplete source history before drawing it.
                    if self.grid[i]-self.grid[a] != i-a: continue
                    ray = {'a_index': a, 'b_index': b, 'a_time': rows[a].time, 'b_time': rows[b].time,
                           'a_price': av, 'b_price': bv, 'slope': slope, 'basis': 'bars', 'valid': True}
                    if any(violation(ray, rows[j], j, upper, width, self.model == 'zone') for j in range(a, i+1)): continue
                    reactions = episodes(ray, rows, i, upper, width, vol)
                    exact = episodes(ray, rows, i, upper, 1e-7, vol)
                    c = {'id': digest([VERSION, self.symbol, self.tf, self.model, upper, rows[a].time, rows[b].time]),
                         'upper': upper, 'ray': ray, 'width': width, 'atrAtCreation': vol,
                         'knownAt': rows[i].end, 'createdIndex': i, 'active': True, 'breakIndex': None,
                         'emitted': [], 'count': len(reactions), 'exactCount': len(exact),
                         'lastTouch': reactions[-1]['lastIndex'] if reactions else None, 'separated': False,
                         'lastExact': exact[-1]['lastIndex'] if exact else None, 'exactSeparated': False}
                    for k in range((c['lastTouch'] or 0)+1, i+1):
                        level = at(ray, k)
                        away = level-width-rows[k].close if upper else rows[k].close-level-width
                        c['separated'] |= away >= RULES['reactionATR']*vol
                    for k in range((c['lastExact'] or 0)+1, i+1):
                        away = at(ray, k)-rows[k].close if upper else rows[k].close-at(ray, k)
                        c['exactSeparated'] |= away >= RULES['reactionATR']*vol
                    result.append(c)
        return result


def update_contact(c, rows, i):
    level, b = at(c['ray'], i), rows[i]
    wick = b.high if c['upper'] else b.low
    for width, count, last, separated in ((c['width'], 'count', 'lastTouch', 'separated'),
                                          (1e-7, 'exactCount', 'lastExact', 'exactSeparated')):
        if abs(wick-level) <= width+1e-7:
            if c[last] is None or c[separated] and i-c[last] >= GEOMETRY_RULES['contact_gap']:
                c[count] += 1
            c[last], c[separated] = i, False
        elif c[last] is not None:
            away = level-width-b.close if c['upper'] else b.close-level-width
            c[separated] |= away >= RULES['reactionATR']*c['atrAtCreation']


class CompleteReplay:
    def __init__(self, dataset, timeframe='4h', model='strict', cutoff=None, events=None):
        require_convention(dataset)
        if timeframe not in ('4h', '1D') or model not in ('strict', 'zone'):
            raise ValueError('Declared source timeframe and geometry required')
        self.dataset = dataset
        self.symbol, self.tf, self.model = dataset['material']['symbol'], timeframe, model
        self.cutoff = cutoff or max(b['end'] for b in dataset['material']['bars']['5m'])
        self.sources = {tf: [b for b in rows if b.end <= self.cutoff] for tf, rows in source_bars(dataset).items()}
        self.rows, self.fine = self.sources[timeframe], self.sources['5m']
        self.fine_by_time = {b.time: b for b in self.fine}
        self.grid_pairs = list(source_grid(self.rows[0].time, self.cutoff, timeframe))
        grid_map = {pair: n for n, pair in enumerate(self.grid_pairs)}
        self.grid = [grid_map[(b.time, b.end)] for b in self.rows]
        self.geometry = IncrementalGeometry(self.rows, self.symbol, timeframe, model, self.grid)
        self.context = StrategyContext(self.sources, self.cutoff)
        self.monthly = aggregate(self.sources['1D'], True)
        self.month_ends = [b.end for b in self.monthly]
        self.events = events or EventCalendar()
        self.start_at = self.rows[0].time+RULES['warmupDays']*86400
        self.candidates, self.entries, self.pending, self.attempts = [], [], [], []
        self.funnel = Counter()
        self.bar_counts, self.cluster_alternatives = Counter(), 0
        self.last_i = -1
        self.check_cache, self.month_cache = {}, {}

    def green_choices(self, i):
        return sorted((c for c in self.candidates if not c['upper'] and c['active'] and
            c['count'] >= 2 and 0 < at(c['ray'], i) < self.rows[i].close),
            key=lambda c: (-at(c['ray'], i), -c['count'], c['id']))

    def line_info(self, c, i):
        return {'contacts': c['count'], 'exactContacts': c['exactCount'],
                'ageDays': (self.rows[i].end-c['ray']['a_time'])/86400,
                'knownForDays': (self.rows[i].end-c['knownAt'])/86400,
                'qualifiedAt': self.rows[i].end,
                'knownAt': c['knownAt'], 'wholeBody': min(self.rows[i].open, self.rows[i].close) > at(c['ray'], i)+c['width']}

    def details(self, c, green, family, i):
        b, p = self.rows[i], self.rows[i-1]
        vol = atr(self.rows[max(0, i-14):i+1])
        info = deepcopy(c['breakInfo']) if family == 'retest' else self.line_info(c, i-1)
        # Current body is a current signal check, not part of the old contact count.
        body = min(b.open, b.close) > at(c['ray'], i)+c['width']
        if family == 'bounce':
            momentum = b.close-b.open >= RULES['momentumATR']*vol and b.close > p.high
        elif family == 'retest':
            momentum = info['momentum'] and b.close-b.open >= RULES['momentumATR']*vol and b.close > p.high
        else:
            momentum = b.close-b.open >= RULES['momentumATR']*vol and b.close > max(x.high for x in self.rows[max(0, i-6):i])
        g_info = self.line_info(green, i)
        g_info['qualifiedAt'] = self.rows[i if green['createdIndex'] == i else i-1].end
        stop = at(green['ray'], i)-max(RULES['tick'], RULES['stopATR']*vol)
        # Geometry must not span any missing expected source bucket.
        first = min(c['ray']['a_index'], green['ray']['a_index'], max(0, i-14))
        history = self.grid[i]-self.grid[first] == i-first
        return {'info': info, 'greenInfo': g_info, 'momentum': momentum, 'wholeBody': body,
                'initialStop': stop, 'signalATR': vol, 'completeHistory': history}

    def market_checks(self, e, at_time, price):
        context = self.context.known_context(at_time)
        nmonth = bisect_right(self.month_ends, at_time)
        if nmonth not in self.month_cache:
            self.month_cache[nmonth] = structure(self.monthly[:nmonth])
        monthly = self.month_cache[nmonth]
        fresh = context['lastDailyClose'] == latest_session_close(at_time) and context['lastWeeklyClose'] == latest_week_close(at_time)
        directions = (context['daily'], context['weekly'], monthly)
        trend = None if 'unknown' in directions else fresh and all(d != 'down' for d in directions)
        risk = price*(1+RULES['sideCost'])-e['initialStop']
        zones = [z['lower'] for z in context['zones'] if z['upper'] > price]
        # Other live original red rays are known overhead obstacles too.
        zones += e['otherRedLevels']
        known_days = (at_time-self.sources['1D'][0].time)/86400
        nearest = min(zones) if zones else None
        room = (nearest*(1-RULES['sideCost'])-price*(1+RULES['sideCost']))/risk if nearest is not None and risk > 0 else None
        room_pass = None if known_days < 365 else (nearest is None or room is not None and room >= RULES['roomR'])
        return {'context': trend, 'room': room_pass, 'contextDetail': {**{k: context[k] for k in ('daily', 'weekly', 'lastDailyClose', 'lastWeeklyClose')}, 'monthly': monthly, 'fresh': fresh},
                'nearestResistance': nearest, 'netRoomR': room, 'openSky': nearest is None and known_days >= 365}

    def schedule(self, signals, i):
        if self.rows[i].end < self.start_at: return
        self.check_cache = {}
        greens = self.green_choices(i)
        options = []
        for c, family in signals:
            choices = [c] if family == 'bounce' else greens
            # Nearest viable green for ordinary group, plus nearest 3-contact
            # green so a 2-contact representative cannot suppress green3.
            choices = choices[:1]+[g for g in choices if g['count'] >= 3][:1]
            for green in {g['id']: g for g in choices}.values():
                d = self.details(c, green, family, i)
                if d['info']['contacts'] < 2 or not d['completeHistory']:
                    continue
                key = (c['id'], family, green['id'], self.rows[i].end)
                other = [at(p['ray'], i) for p in self.candidates if p['upper'] and p['active'] and
                         p['breakIndex'] is None and p['id'] != c['id'] and
                         not equivalent(c, p, i, d['signalATR']) and at(p['ray'], i) > self.rows[i].close]
                e = {**d, 'symbol': self.symbol, 'timeframe': self.tf, 'geometry': self.model,
                     'signalAt': self.rows[i].end, 'signalIndex': i, 'family': family,
                     'candidateId': c['id'], 'greenId': green['id'], 'red': deepcopy(c['ray']) if family != 'bounce' else None,
                     'actionWidth': c['width'], 'actionATRAtCreation': c['atrAtCreation'],
                     'greenWidth': green['width'], 'greenATRAtCreation': green['atrAtCreation'],
                     'breakIndex': c['breakIndex'],
                     'green': deepcopy(green['ray']), 'greenLevel': at(green['ray'], i),
                     'entryAt': execution_time(self.rows[i].end), 'trigger': at(c['ray'], i)+c['width'],
                     'otherRedLevels': sorted(other), 'knownAt': self.rows[i].end,
                     'geometryStrict': self.model == 'strict'}
                options.append((c, e))
        for profile in PROFILES:
            for family in ('breakout', 'retest', 'bounce'):
                possible = [(c, e) for c, e in options if e['family'] == family and (profile, family) not in c['emitted']]
                if not possible: continue
                # Evaluate each candidate under signal-known prices first. Final
                # open risk/room is checked again; no future ranking is allowed.
                selected = []
                for c, e in possible:
                    checks = self.checks(e, self.rows[i].close, e['signalAt'])
                    if qualified(checks, profile): selected.append((c, e, checks))
                self.funnel[f'{profile}/{family}/signal_bars'] += 1
                if not selected:
                    blockers = Counter(k for _, e in possible for k, v in self.checks(e, self.rows[i].close, e['signalAt']).items() if k in ('three', 'age7', 'momentum', 'safety', 'context', 'room', 'events') and v is not True)
                    for k, n in blockers.items(): self.funnel[f'{profile}/{family}/blocked/{k}'] += 1
                    continue
                selected.sort(key=lambda x: (-x[1]['info']['contacts'], -x[1]['info']['ageDays'], -x[1]['greenLevel'], x[0]['id']))
                c, e, checks = selected[0]
                equivalent_count = sum(equivalent(c, p, i, e['signalATR']) for p, _, _ in selected[1:])
                self.cluster_alternatives += equivalent_count
                c['emitted'].append((profile, family))
                self.pending.append({**deepcopy(e), 'profile': profile, 'signalChecks': checks,
                                     'clusterAlternatives': equivalent_count})

    def checks(self, e, price, at_time):
        key = (e['candidateId'], e['greenId'], e['family'], e['signalAt'], price, at_time)
        if key in self.check_cache: return self.check_cache[key]
        info, green = e['info'], e['greenInfo']
        risk = price*(1+RULES['sideCost'])-e['initialStop']
        market = self.market_checks(e, at_time, price)
        result = {'two': info['contacts'] >= 2 and green['contacts'] >= 2 and e['completeHistory'],
                'three': info['contacts'] >= 3,
                'age7': info['ageDays'] >= 7 and green['ageDays'] >= 7,
                'momentum': bool(e['momentum']),
                'safety': bool(0 < e['initialStop'] < price and 0 < risk <= RULES['maxRiskATR']*e['signalATR'] and risk/price <= RULES['maxRiskFraction']),
                'context': market['context'], 'room': market['room'],
                'events': self.events.check(self.symbol, at_time),
                'age14': info['ageDays'] >= 14 and green['ageDays'] >= 14,
                'green3': green['contacts'] >= 3, 'whole_body': e['wholeBody'],
                'exact3': info['exactContacts'] >= 3}
        self.check_cache[key] = result
        return result

    def resolve(self, known_until):
        for e in list(self.pending):
            if e['entryAt']+300 > known_until: continue
            self.pending.remove(e)
            b = self.fine_by_time.get(e['entryAt'])
            reason = None
            if b is None: reason = 'missing_execution_open'
            elif any(t not in self.fine_by_time for t in expected_grid(e['signalAt'], e['entryAt'])): reason = 'missing_interim_path'
            elif any(self.fine_by_time[t].low <= e['initialStop'] for t in expected_grid(e['signalAt'], e['entryAt'])): reason = 'interim_stop'
            elif b.open <= max(e['initialStop'], e['trigger']): reason = 'open_below_trigger_or_stop'
            if reason is None:
                checks = self.checks(e, b.open, e['entryAt'])
                if not qualified(checks, e['profile']): reason = 'open_checks_failed'
            if reason:
                self.attempts.append({'signalAt': e['signalAt'], 'profile': e['profile'], 'family': e['family'], 'reason': reason})
                continue
            e['entryPrice'], e['checks'] = b.open, checks
            e['id'] = digest([VERSION, self.symbol, self.tf, self.model, e['profile'], e['family'], e['entryAt']])
            e['market'] = self.market_checks(e, e['entryAt'], b.open)
            e['fullyCompliant'] = self.model == 'strict' and qualified(checks, 'all_events')
            self.entries.append(e)

    def run(self):
        for i, b in enumerate(self.rows):
            self.last_i = i
            self.resolve(b.end)
            if i < 14: continue
            if b.end >= self.start_at:
                self.bar_counts[str(datetime.fromtimestamp(b.end, NY).year)] += 1
            signals, old = [], [c for c in self.candidates if c['active']]
            continuous = i == 0 or self.grid[i]-self.grid[i-1] == 1
            for c in old:
                if not continuous:
                    c['active'] = False
                    continue
                level = at(c['ray'], i)
                if not c['upper']:
                    if violation(c['ray'], b, i, False, c['width'], self.model == 'zone'):
                        c['active'] = False
                    elif c['count'] >= 2 and b.low <= level+c['width'] and b.close > level+c['width'] and b.close > b.open and b.close > self.rows[i-1].high:
                        signals.append((c, 'bounce'))
                elif c['breakIndex'] is None:
                    top = level+c['width']
                    if b.close > top and self.rows[i-1].close <= at(c['ray'], i-1)+c['width'] and b.close > b.open and b.close > self.rows[i-1].close:
                        c['breakInfo'] = self.line_info(c, i-1)
                        c['breakInfo']['momentum'] = b.close-b.open >= RULES['momentumATR']*atr(self.rows[i-14:i+1]) and b.close > max(x.high for x in self.rows[max(0, i-6):i])
                        c['breakIndex'] = i
                        signals.append((c, 'breakout'))
                    elif violation(c['ray'], b, i, True, c['width'], self.model == 'zone'):
                        c['active'] = False
                elif b.close < level-c['width']:
                    c['active'] = False
                elif i > c['breakIndex'] and b.low <= level+c['width'] and b.high >= level-c['width'] and b.close > level+c['width'] and b.close > b.open:
                    signals.append((c, 'retest'))
            # Signal uses old action contact counts; current green must already
            # survive this candle. New confirmed greens are usable at the close.
            proposals = self.geometry.proposals(i)
            self.candidates.extend(c for c in proposals if not c['upper'])
            self.schedule(signals, i)
            for c in old:
                if c['active'] and c['breakIndex'] is None: update_contact(c, self.rows, i)
            self.candidates.extend(c for c in proposals if c['upper'])
        self.resolve(self.cutoff)
        return {'version': VERSION, 'symbol': self.symbol, 'datasetId': self.dataset['id'], 'timeframe': self.tf,
                'geometry': self.model, 'entries': self.entries, 'attempts': self.attempts,
                'funnel': dict(self.funnel), 'sourceBars': len(self.rows), 'expectedSourceBars': len(self.grid_pairs),
                'startAt': self.start_at, 'endAt': self.cutoff, 'barCounts': dict(self.bar_counts),
                'candidates': len(self.candidates), 'threeContactCandidates': sum(c['count'] >= 3 for c in self.candidates),
                'clusterAlternatives': self.cluster_alternatives, 'pending': self.pending}
