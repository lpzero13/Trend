"""Causal pre-entry radar. No provider, orders, portfolio or future outcomes.

Each policy observes the same canonical PilotObserver stream. Episode identity
starts at candidate discovery; red retests retain their breakout's parent.
"""
from collections import deque
from copy import deepcopy
from dataclasses import asdict, dataclass
import math

from fan_geometry import stable_id
from fan_observer import price_at
from pilot_backtest import PilotObserver, FAMILIES
from setup_episodes import Episodes

VERSION = 'tori-pre-entry-radar-1'
VARIANTS = ('distance', 'active', 'compression', 'combined')


@dataclass(frozen=True)
class Rules:
    thresholds: tuple = (1.5, 1., .5)
    variants: tuple = VARIANTS
    urgent_atr: float = .5
    away_atr: float = 2.5
    approach_bars: int = 3

    def __post_init__(self):
        if not self.thresholds or len(set(self.thresholds)) != len(self.thresholds) or any(type(x) not in (int, float) or not math.isfinite(x) or not .1 <= x <= 5 for x in self.thresholds):
            raise ValueError('Eindeutige Annäherungsschwellen von 0,1 bis 5 ATR erforderlich.')
        if not self.variants or len(set(self.variants)) != len(self.variants) or set(self.variants)-set(VARIANTS):
            raise ValueError('Unbekannte/mehrfache Warnvariante.')
        if type(self.approach_bars) is not int or not 1 <= self.approach_bars <= 20:
            raise ValueError('Annäherungsfenster: 1–20 Kerzen.')
        if any(type(x) not in (int, float) or not math.isfinite(x) for x in (self.urgent_atr, self.away_atr)) or not 0 < self.urgent_atr <= min(self.thresholds) or self.away_atr <= max(self.thresholds):
            raise ValueError('Dringlichkeits-/Entfernungsschwellen sind ungeordnet.')

    def policies(self):
        return [(f'{variant}:{threshold:g}', variant, threshold)
                for threshold in self.thresholds for variant in self.variants]


def quality(line):
    return 'qualified' if line.get('qualified') else 'two' if line['contacts'] == 2 else 'three_young'


def allows(features, variant):
    return (variant == 'distance' or variant == 'active' and features['activeApproach'] is True or
            variant == 'compression' and features['compressed'] is True or
            variant == 'combined' and features['activeApproach'] is True and features['compressed'] is True)


class Radar:
    def __init__(self, symbol, *, rules=None, observer=None, daily_context=None):
        self.symbol, self.rules = symbol, rules or Rules()
        self.observer = observer or PilotObserver(symbol)
        self.daily_context = daily_context
        self.lineage = Episodes(symbol)
        self.generation = 0
        self.current, self.episodes, self.scenarios, self.first_seen = {}, {}, {}, {}
        self.records = {}
        self.green_records = set()
        self.scenario_lines = {}
        self.history = deque(maxlen=self.rules.approach_bars+1)
        self.last_at = None
        self.raw_signals = 0

    def group(self, line, at, family, scenario=None):
        if scenario in self.scenarios:
            return self.episodes[self.scenarios[scenario]]
        side = 'green' if family == 'safety_bounce' else 'red'
        ancestry = self.lineage.lines.get(line['id']) or self.lineage.anchors.get((side, line['a_time'], line['a_price'])) or stable_id([side, line['a_time'], line['a_price']])
        key = self.generation, side, ancestry
        old = self.current.get(key)
        # Rearm only a distinct new candidate after an earlier structural event,
        # with two confirmed contacts formed after the previous episode began.
        fresh = {p['time'] for p in line.get('contactPoints', [])
                 if old and old['createdAt'] < p['time'] and p['known_at'] < at}
        if old and old['terminalAt'] and len(fresh) >= 2 and scenario not in old['scenarioIds']:
            open_watch = any((r := self.records.get((old['id'], f, p))) and r['warnings'] and r['outcome'] is None
                             for f in FAMILIES for p, _, _ in self.rules.policies())
            if not open_watch: old = None
        if old is None:
            identity = stable_id([VERSION, self.symbol, key, at])
            old = {'id': identity, 'lineageId': ancestry, 'createdAt': at, 'generation': self.generation,
                   'side': side, 'terminalAt': None, 'scenarioIds': [], 'firstLine': deepcopy(line)}
            self.current[key] = old
            self.episodes[identity] = old
        if scenario:
            self.scenarios[scenario] = old['id']
            if scenario not in old['scenarioIds']: old['scenarioIds'].append(scenario)
        return old

    def record(self, episode, family, policy):
        key = episode['id'], family, policy
        if key not in self.records:
            self.records[key] = {'id': stable_id([VERSION, self.symbol, *key]), 'symbol': self.symbol,
                'episodeId': episode['id'], 'lineageId': episode['lineageId'], 'family': family,
                'policy': policy, 'createdAt': episode['createdAt'], 'phase': 'setup',
                'warnings': [], 'outcome': None, 'entry': None, 'rawBreakAt': None,
                'rawBreakIndex': None, 'touchAt': None, 'touchIndex': None, 'lastKnownAt': episode['createdAt']}
        return self.records[key]

    def finish(self, episode, family, at, reason, *, censored=False, line_id=None):
        for policy, _, _ in self.rules.policies():
            r = self.records.get((episode['id'], family, policy))
            if r and r['outcome'] is None and (line_id is None or not r['warnings'] or r['warnings'][0]['snapshot']['line']['id'] == line_id):
                r.update(phase='finished', lastKnownAt=at,
                         outcome={'at': at, 'reason': reason, 'censored': censored})
        episode['terminalAt'] = episode['terminalAt'] or at

    def features(self, bar, snap, line, green, family, seen_at):
        idx, atr = snap['referenceIndex'], snap['atr']
        level = price_at(line, idx)
        above = family != 'breakout'
        distance = bar.close-level if above else level-bar.close
        previous = self.history[0] if len(self.history) == self.history.maxlen else None
        active = shrinking = None
        price_move = line_move = None
        if previous:
            _, past, past_idx = previous
            old_level = price_at(line, past_idx)
            old_distance = past.close-old_level if above else old_level-past.close
            price_move = past.close-bar.close if above else bar.close-past.close
            line_move = level-old_level if above else old_level-level
            shrinking = distance < old_distance
            last_three = [b for _, b, _ in self.history][-3:]
            directional_wicks = len(last_three) == 3 and (all(a.high > b.high for a, b in zip(last_three, last_three[1:])) if above else
                                                         all(a.low < b.low for a, b in zip(last_three, last_three[1:])))
            active = shrinking and (price_move > 0 or directional_wicks)
        red = line if family != 'safety_bounce' else snap.get('red')
        safety = green if family != 'safety_bounce' else line
        compression = width = None
        if red and safety and red['slope'] < 0 and safety['slope'] >= 0:
            start = max(red['a_index'], safety['a_index'])
            beginning = price_at(red, start)-price_at(safety, start)
            current = price_at(red, idx)-price_at(safety, idx)
            if idx > start and beginning > 0 and current > 0:
                compression, width = current/beginning, current/atr
        stop = math.floor(price_at(safety, idx)*.997/self.observer.rules.tick)*self.observer.rules.tick if safety else None
        risk = bar.close-stop if stop and 0 < stop < bar.close else None
        context = self.daily_context.daily_at(bar.end) if self.daily_context else {}
        sma, daily = context.get('dailySma200'), context.get('dailyClose')
        context['dailyPosition'] = 'unknown' if sma is None or daily is None else 'above' if daily > sma else 'not_above'
        return {'knownAt': bar.end, 'sourceIndex': idx, 'close': bar.close, 'atr': atr,
            'distanceATR': distance/atr, 'distancePct': 100*distance/bar.close,
            'activeApproach': active, 'distanceShrinking': shrinking,
            'comparisonFrom': previous[0] if previous else None,
            'lineKnownAtComparison': bool(previous and previous[0] >= seen_at),
            'comparisonGeometry': 'Same CURRENT known line at both past/current indexes; not a historical signal',
            'priceContribution': price_move, 'lineContribution': line_move,
            'compressionRatio': compression, 'widthATR': width,
            'compressed': compression is not None and (compression <= .5 or width <= 3),
            'cohort': quality(line), 'contacts': line['contacts'], 'lineAgeDays': (bar.end-line['a_time'])/86400,
            'greenQualified': bool(safety and safety.get('qualified')), 'provisionalStop': stop,
            'provisionalRiskPct': 100*risk/bar.close if risk is not None else None,
            'provisionalRiskATR': risk/atr if risk is not None else None,
            'experimentalDistanceClass': risk is not None and risk/atr >= 1 and 100*risk/bar.close >= 2,
            'higherConfirmedLows': bool(safety and len(safety.get('contactPoints', [])) >= 2 and
                safety['contactPoints'][-1]['price'] > safety['contactPoints'][-2]['price']),
            'outerResistance': min((price_at(r, idx) for r in snap.get('reds', [])
                if red and r['id'] != red['id'] and price_at(r, idx) > price_at(red, idx)), default=None),
            'daily': context,
            'projection': {'barsAhead': 2, 'lineValue': price_at(line, idx+2),
                'cleanThresholdAtCurrentATR': (price_at(line, idx+2)+self.observer.watch.clean_atr*atr) if family != 'safety_bounce' else None,
                'meaning': 'Unchanged original line and CURRENT ATR; no forecast; Safety bounce has no clean-close threshold'}}

    def consider(self, episode, family, bar, snap, line, green, seen_at):
        if not snap.get('atr') or any(p['known_at'] > bar.end for p in line.get('contactPoints', [])):
            return
        f = self.features(bar, snap, line, green, family, seen_at)
        idx, level = snap['referenceIndex'], price_at(line, snap['referenceIndex'])
        for policy, variant, threshold in self.rules.policies():
            r = self.records.get((episode['id'], family, policy))
            if r and r['outcome'] is not None: continue
            if r and r['warnings']:
                locked = r['warnings'][0]['snapshot']['green']
                if locked and bar.close < price_at(locked, idx):
                    r.update(phase='finished', outcome={'at': bar.end, 'reason': 'original_safety_close', 'censored': False})
                    continue
                original = r['warnings'][0]['snapshot']['line']
                original_distance = (price_at(original, idx)-bar.close if family == 'breakout' else bar.close-price_at(original, idx))/snap['atr']
                if original_distance > self.rules.away_atr:
                    r.update(phase='finished', outcome={'at': bar.end, 'reason': 'moved_away', 'censored': False})
                    continue
            if not 0 <= f['distanceATR'] <= threshold or not allows(f, variant): continue
            # A valid warning needs known support; a rising support is a label,
            # not an unconditional gate excluding horizontal bases.
            if family != 'safety_bounce' and (not green or not 0 < price_at(green, idx) < bar.close): continue
            r = self.record(episode, family, policy)
            if family == 'safety_bounce': self.green_records.add((episode['id'], family, policy))
            r['lastKnownAt'] = bar.end
            if r['entry'] is not None or r['rawBreakAt'] and family == 'breakout': continue
            stages = {w['stage'] for w in r['warnings']}
            touched = bar.high >= level-self.observer.rules.contact_atr*snap['atr'] if family == 'breakout' else bar.low <= level+self.observer.rules.contact_atr*snap['atr']
            for stage in (2, 3):
                if stage in stages or stage == 3 and not (f['distanceATR'] < self.rules.urgent_atr or touched): continue
                # Both stages may be discovered together; this is one briefing,
                # and explicitly not a claimed day of advance preparation.
                warning = {'id': stable_id([r['id'], stage]), 'stage': stage, 'at': bar.end,
                    'features': deepcopy(f), 'snapshot': {'knownAt': bar.end, 'sourceIndex': idx,
                        'line': deepcopy(line), 'green': deepcopy(green),
                        'red': deepcopy(line if family != 'safety_bounce' else snap.get('red')),
                        'meaning': 'Original alert geometry, separate from later chart refits'}}
                r['warnings'].append(warning)
                r['phase'] = 'interesting' if stage == 2 else 'immediate'

    def push(self, bar, *, gap=False):
        if self.last_at is not None and bar.end <= self.last_at:
            raise ValueError('Radar requires strictly increasing closed source bars.')
        old_snap = self.observer.snapshot
        if gap:
            for episode in self.episodes.values():
                for family in FAMILIES: self.finish(episode, family, bar.end, 'source_gap', censored=True)
            self.observer.gap(bar)
            self.lineage = Episodes(self.symbol)
            self.current.clear(); self.scenarios.clear(); self.first_seen.clear(); self.history.clear()
            self.generation += 1
            old_snap = None
        events, signals, snap = self.observer.push(bar)
        self.last_at = bar.end
        if not snap or not snap.get('ready'): return
        self.history.append((bar.end, bar, snap['referenceIndex']))
        self.lineage.observe(snap)
        for line in snap.get('reds', [])+snap.get('greens', []): self.first_seen.setdefault(line['id'], bar.end)
        # Register candidates before interpreting this close's signal transitions.
        for e in events:
            if e['kind'] == 'candidate':
                self.group(e['line'], bar.end, 'breakout', e['scenarioId'])
                self.scenario_lines[e['scenarioId']] = e['line']['id']
        for e in events:
            episode_id = self.scenarios.get(e.get('scenarioId'))
            if episode_id is None: continue
            episode = self.episodes[episode_id]
            if e['kind'] == 'break':
                episode['terminalAt'] = episode['terminalAt'] or bar.end
                for policy, _, _ in self.rules.policies():
                    r = self.record(episode, 'breakout', policy)
                    r['rawBreakAt'] = r['rawBreakAt'] or bar.end
                    if r['rawBreakIndex'] is None: r['rawBreakIndex'] = snap['referenceIndex']
                    if r['outcome'] is None: r['phase'] = 'crossed_waiting_clean'
            elif e['kind'] == 'retest_touch':
                for policy, _, _ in self.rules.policies():
                    r = self.record(episode, 'red_retest', policy)
                    r['touchAt'] = r['touchAt'] or bar.end
                    if r['touchIndex'] is None: r['touchIndex'] = snap['referenceIndex']
            elif e['kind'] in ('invalidated', 'expired'):
                for family in ('breakout', 'red_retest'):
                    self.finish(episode, family, bar.end, e.get('reason', e['kind']), line_id=self.scenario_lines.get(e['scenarioId']))
        for signal in signals:
            self.raw_signals += 1
            family = signal['family']
            episode = self.group(signal['line'], bar.end, family, signal.get('scenarioId'))
            episode['terminalAt'] = episode['terminalAt'] or bar.end
            for policy, _, _ in self.rules.policies():
                r = self.record(episode, family, policy)
                if r['entry'] is not None: continue
                active = r['outcome'] is None
                r['entry'] = {'id': signal['id'], 'at': bar.end, 'sourceIndex': snap['referenceIndex'],
                    'lineId': signal['line']['id'], 'cohort': signal['cohort'], 'validRisk': signal['validRisk'],
                    'activeAtSignal': active, 'initialStop': signal['initialStop']}
                if active:
                    r.update(phase='finished', outcome={'at': bar.end, 'reason': 'entry_signal', 'censored': False})
        # Current active red scenarios retain their original line and timestamps.
        for scenario in self.observer.red.active.values():
            episode = self.group(scenario['line'], bar.end, 'breakout', scenario['id'])
            if scenario['state'] == 'active':
                self.consider(episode, 'breakout', bar, snap, scenario['line'], snap.get('green'), scenario['candidateAt'])
            elif bar.end > scenario['breakAt']:
                self.consider(episode, 'red_retest', bar, snap, scenario['brokenLine'], snap.get('green'), scenario['breakAt'])
        # Bounce candidates must already have been qualified on the PREVIOUS close.
        if old_snap and old_snap.get('ready'):
            for line in old_snap.get('greens', []):
                if not line['qualified'] or line['slope'] <= 0: continue
                episode = self.group(line, bar.end, 'safety_bounce')
                level = price_at(line, snap['referenceIndex'])
                invalid = bar.close < level or bar.low < level-self.observer.rules.wick_atr*snap['atr']
                if invalid:
                    self.finish(episode, 'safety_bounce', bar.end, 'safety_structure_broken', line_id=line['id'])
                else:
                    if bar.low <= level+self.observer.rules.contact_atr*snap['atr']:
                        for policy, _, _ in self.rules.policies():
                            r = self.record(episode, 'safety_bounce', policy)
                            r['touchAt'] = r['touchAt'] or bar.end
                            if r['touchIndex'] is None: r['touchIndex'] = snap['referenceIndex']
                    self.consider(episode, 'safety_bounce', bar, snap, line, line, self.first_seen.get(line['id'], bar.end))
        # Suspended/expired green geometry must not remain an immortal open watch.
        for key in list(self.green_records):
            r = self.records[key]
            if r['outcome'] is not None or not r['warnings']:
                self.green_records.discard(key)
                continue
            line = r['warnings'][0]['snapshot']['line']
            if bar.end-line['a_time'] > self.observer.rules.lookback_days*86400:
                r.update(phase='finished', outcome={'at': bar.end, 'reason': 'line_horizon', 'censored': False})

    def result(self, cutoff=None):
        values = deepcopy(list(self.records.values()))
        for r in values:
            if r['outcome'] is None:
                r['outcome'] = {'at': cutoff or self.last_at, 'reason': 'data_end', 'censored': True}
        return {'version': VERSION, 'symbol': self.symbol, 'rules': asdict(self.rules),
                'episodes': deepcopy(list(self.episodes.values())), 'records': values,
                'rawSignals': self.raw_signals, 'lastClosedAt': self.last_at}
