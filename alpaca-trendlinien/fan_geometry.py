"""Causal, provider-independent port of the corrected Pine Master fan geometry.

No orders, HTTP, database or outcome access. ``lag=2`` reproduces the Pine
snapshot's excluded breakout window. A live observer must discover with lag=0;
it may never backdate a newly discovered line to a previous breakout.
"""
from collections import deque
from dataclasses import asdict, dataclass, replace
import hashlib
import json
import math

from models import Bar, DataError

VERSION = "tori-fan-geometry-1"


@dataclass(frozen=True)
class FanRules:
    pivot_side: int = 2
    atr_length: int = 14
    contact_gap: int = 5
    contact_atr: float = .45
    wick_atr: float = .15
    reaction_atr: float = .5
    min_age_days: float = 7.
    lookback_days: int = 320
    max_bars: int = 1800
    max_pivots: int = 80
    levels: int = 4
    breakout_window: int = 2
    roots: str = "extreme"
    tick: float = .01
    algorithm: str = "classic"
    action_lookback_days: int = 150
    body_atr: float = .05

    def __post_init__(self):
        ranges = {"pivot_side": (1, 6), "atr_length": (2, 200), "contact_gap": (2, 50),
                  "lookback_days": (10, 1500), "max_bars": (50, 10000),
                  "max_pivots": (2, 150), "levels": (1, 5), "breakout_window": (0, 10)}
        ranges["action_lookback_days"] = (10, 1500)
        for k, (low, high) in ranges.items():
            if type(getattr(self, k)) is not int or not low <= getattr(self, k) <= high:
                raise DataError(f"Fächer: ungültiger Parameter {k}.", 400)
        for k, low, high in (("contact_atr", 0., 2.), ("wick_atr", 0., 1.),
                             ("reaction_atr", 0., 5.), ("min_age_days", 0., 365.),
                             ("body_atr", 0., .5),
                             ("tick", 1e-8, 100.)):
            v = getattr(self, k)
            if type(v) not in (int, float) or not math.isfinite(v) or not low <= v <= high:
                raise DataError(f"Fächer: ungültiger Parameter {k}.", 400)
        if self.roots not in ("extreme", "local"):
            raise DataError("Fächer-Startanker: extreme oder local.", 400)
        if self.algorithm not in ("classic", "master"):
            raise DataError("Fächer-Algorithmus: classic oder master.", 400)


def profile(variant, geometry=None):
    if variant not in ("extreme", "local", "master"):
        raise DataError("Unbekannte Fächer-Variante.", 400)
    return FanRules(**{**(geometry or {}), "roots": "local" if variant == "local" else "extreme",
                       "algorithm": "master" if variant == "master" else "classic"})


def create_engine(symbol, timeframe, rules=None):
    r = rules or FanRules()
    if r.algorithm == "master":
        from fan_master import MasterEngine
        return MasterEngine(symbol, timeframe, r)
    return FanEngine(symbol, timeframe, r)


def stable_id(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class Pivot:
    index: int
    time: int
    price: float
    atr: float
    known_index: int
    known_at: int


@dataclass(frozen=True)
class FanLine:
    id: str
    upper: bool
    a_index: int
    a_time: int
    a_price: float
    b_index: int
    b_time: int
    b_price: float
    slope: float
    contacts: tuple[Pivot, ...]
    reactions: int
    level: int

    def at(self, index):
        return self.a_price + self.slope * (index - self.a_index)

    def output(self, index, known_at, rules):
        days = (known_at - self.a_time) / 86400
        return {"id": self.id, "upper": self.upper, "a_index": self.a_index,
                "a_time": self.a_time, "a_price": self.a_price,
                "b_index": self.b_index, "b_time": self.b_time, "b_price": self.b_price,
                "slope": self.slope, "basis": "bars", "value": self.at(index),
                "contacts": len(self.contacts), "contactPoints": [asdict(p) for p in self.contacts],
                "reactionContacts": self.reactions, "span_days": days, "valid": True,
                "qualified": len(self.contacts) >= 3 and days >= rules.min_age_days,
                "knownAt": known_at, "level": self.level}


def violates(line, bar, index, atr, rules):
    price = line.at(index)
    allowance = rules.wick_atr * atr
    epsilon = 1e-9
    return (max(bar.open, bar.close) > price + epsilon or bar.high > price + allowance + epsilon) if line.upper else (
        min(bar.open, bar.close) < price - epsilon or bar.low < price - allowance - epsilon)


class FanEngine:
    """Bounded confirmed-prefix engine; caches geometry, never future outcomes."""
    def __init__(self, symbol, timeframe, rules=None):
        self.symbol, self.timeframe, self.rules = symbol, timeframe, rules or FanRules()
        self.index = -1
        self.rows = deque()
        self.pivots = {True: deque(), False: deque()}
        self.recent = deque(maxlen=2*self.rules.pivot_side+1)
        self.previous = None
        self.tr_seed = []
        self.atr = None
        self.cache = {}
        self.rebuilds = 0

    def reset_history(self):
        index = self.index
        self.__init__(self.symbol, self.timeframe, self.rules)
        self.index = index

    def push(self, bar):
        vals = (bar.open, bar.high, bar.low, bar.close, bar.volume)
        if any(type(v) not in (float, int) or not math.isfinite(v) for v in vals) or not (
            0 < bar.low <= min(bar.open, bar.close) <= max(bar.open, bar.close) <= bar.high
            and bar.volume >= 0 and type(bar.time) is int and type(bar.end) is int and bar.end > bar.time):
            raise DataError("Fächer: ungültige OHLC-Kerze.", 422)
        if self.previous and (bar.time <= self.previous.time or bar.time < self.previous.end):
            raise DataError("Fächer: unsortierte oder überlappende Kerzen.", 422)
        self.index += 1
        tr = bar.high-bar.low if self.previous is None else max(bar.high-bar.low, abs(bar.high-self.previous.close), abs(bar.low-self.previous.close))
        if self.atr is None:
            self.tr_seed.append(tr)
            if len(self.tr_seed) == self.rules.atr_length:
                self.atr = sum(self.tr_seed)/self.rules.atr_length
        else:
            self.atr = (self.atr*(self.rules.atr_length-1)+tr)/self.rules.atr_length
        self.previous = bar
        self.recent.append((self.index, bar, self.atr))
        if self.atr is None:
            return
        self.rows.append((self.index, bar, self.atr))
        days = max(self.rules.lookback_days, self.rules.action_lookback_days) if self.rules.algorithm == "master" else self.rules.lookback_days
        cutoff = bar.end-days*86400
        while self.rows and (len(self.rows) > self.rules.max_bars or self.rows[0][1].end < cutoff):
            self.rows.popleft()
        side = self.rules.pivot_side
        if len(self.recent) == 2*side+1:
            neighbors = list(self.recent)
            i, candidate, vol = neighbors[side]
            if vol is not None:
                for upper in (True, False):
                    values = [b.high if upper else b.low for _, b, _ in neighbors]
                    v = values[side]
                    # Rightmost equal extremum; it becomes known only now.
                    qualifies = (all(v >= x for x in values[:side]) and all(v > x for x in values[side+1:])) if upper else (
                        all(v <= x for x in values[:side]) and all(v < x for x in values[side+1:]))
                    if qualifies:
                        self.pivots[upper].append(Pivot(i, candidate.time, v, vol, self.index, bar.end))
        for pivots in self.pivots.values():
            while pivots and (pivots[0].index < self.rows[0][0] or len(pivots) > self.rules.max_pivots):
                pivots.popleft()

    def _side(self, upper, lag):
        rows = list(self.rows)
        if len(rows) <= lag:
            return []
        valid = rows[:len(rows)-lag] if lag else rows
        until = valid[-1][0]
        pivots = [p for p in self.pivots[upper] if p.known_index <= until]
        signature = tuple(p.index for p in pivots)
        cached = self.cache.get((upper, lag))
        if cached and cached[0] == signature and not any(
            violates(line, bar, i, vol, self.rules) for i, bar, vol in valid if i > cached[1] for line in cached[2]):
            self.cache[upper, lag] = (signature, until, cached[2])
            return cached[2]
        self.rebuilds += 1
        lines = self._build(upper, pivots, valid)
        self.cache[upper, lag] = (signature, until, lines)
        return lines

    def _build(self, upper, pivots, rows):
        if len(pivots) < 2:
            return []
        extreme = max(range(len(pivots)), key=lambda i: pivots[i].price) if upper else min(range(len(pivots)), key=lambda i: pivots[i].price)
        roots = [extreme]
        if self.rules.roots == "local":
            roots += [i for i in range(max(0, len(pivots)-4), len(pivots)-1) if i != extreme][-2:]
        result = {}
        for root in roots:
            current, previous = root, None
            for level in range(self.rules.levels):
                a = pivots[current]
                bounds = [((max(bar.open, bar.close, bar.high-self.rules.wick_atr*vol) if upper else
                            min(bar.open, bar.close, bar.low+self.rules.wick_atr*vol))-a.price)/(i-a.index)
                          for i, bar, vol in rows if i > a.index]
                if not bounds:
                    break
                bound = max(bounds) if upper else min(bounds)
                best = None
                for j in range(current+1, len(pivots)):
                    b = pivots[j]
                    if b.index-a.index < self.rules.contact_gap:
                        continue
                    slope = (b.price-a.price)/(b.index-a.index)
                    if not (slope < 0 if upper else slope > 0) or (previous is not None and not (slope < previous if upper else slope > previous)):
                        continue
                    if not (slope >= bound-1e-10 if upper else slope <= bound+1e-10):
                        continue
                    touches = [a]
                    next_anchor = None
                    for m in range(current+1, len(pivots)):
                        p = pivots[m]
                        if p.index-touches[-1].index >= self.rules.contact_gap and abs(p.price-(a.price+slope*(p.index-a.index))) <= self.rules.contact_atr*p.atr:
                            touches.append(p)
                            next_anchor = m
                    if len(touches) >= 2 and (best is None or (slope > best[0] if upper else slope < best[0]) or (abs(slope-best[0]) < 1e-10 and len(touches) > len(best[2]))):
                        best = slope, b, tuple(touches), next_anchor
                if best is None:
                    break
                slope, b, contacts, next_anchor = best
                reactions = 1
                for left, right in zip(contacts, contacts[1:]):
                    if any(((a.price+slope*(i-a.index)-bar.close) if upper else (bar.close-a.price-slope*(i-a.index))) >= self.rules.reaction_atr*left.atr
                           for i, bar, _ in rows if left.index < i < right.index):
                        reactions += 1
                key = stable_id([VERSION, self.symbol, self.timeframe, asdict(self.rules), upper, a.time, a.price, b.time, b.price])
                result.setdefault(key, FanLine(key, upper, a.index, a.time, a.price, b.index, b.time, b.price, slope, contacts, reactions, level+1))
                previous, current = slope, next_anchor
                if current is None or current >= len(pivots)-1:
                    break
        return list(result.values())

    def snapshot(self, *, pine=False):
        if not self.rows:
            return {"version": VERSION, "ready": False, "reds": [], "greens": []}
        index, bar, vol = self.rows[-1]
        lag = self.rules.breakout_window if pine else 0
        red_until = list(self.rows)[max(0, len(self.rows)-lag-1)][1].end
        reds = [l.output(index, red_until, self.rules) for l in self._side(True, lag)]
        greens = [l.output(index, bar.end, self.rules) for l in self._side(False, 0)]
        red = min(reds, key=lambda l: (abs(l["value"]-bar.close), l["id"]), default=None)
        green = max((l for l in greens if 0 < l["value"] < bar.close), key=lambda l: l["value"], default=None)
        return {"version": VERSION, "ready": True, "timeframe": self.timeframe,
                "mode": "pine_snapshot" if pine else "causal_candidates", "sourceClose": bar.end,
                "referenceIndex": index, "close": bar.close, "atr": vol, "red": red,
                "green": green, "reds": reds, "greens": greens, "rules": asdict(self.rules),
                "searchedBars": len(self.rows), "sourceFirst": self.rows[0][1].time,
                "pivotCounts": {"high": len(self.pivots[True]), "low": len(self.pivots[False])},
                "capped": len(self.rows) >= self.rules.max_bars or any(len(p) >= self.rules.max_pivots for p in self.pivots.values())}


def analyze(bars, timeframe, reference=None, *, data_errors=False, rules=None, pine=False, symbol="CHART", gaps=(), context_clean_atr=.15):
    engine = create_engine(symbol, timeframe, rules)
    for i, bar in enumerate(bars):
        if i in gaps:
            engine.reset_history()
        engine.push(bar)
    state = engine.snapshot(pine=pine)
    if not state["ready"]:
        raise DataError("Zu wenig ATR-Vorlauf für den Fächer.", 404)
    red, green = state["red"], state["green"]
    if engine.rules.algorithm == "master":
        state["checkWindow"] = engine.window_context(context_clean_atr)
    return {**state, "basis": "bars", "sourceTimes": [b.time for b in bars],
            "outerRed": [r for r in state["reds"] if not red or r["id"] != red["id"]],
            "outerGreen": [r for r in state["greens"] if not green or r["id"] != green["id"]],
            "retest": None, "event": None, "status": "Fächer qualifiziert" if red and red["qualified"] else "Fächer vorläufig" if red else "Widerstand fehlt",
            "distance": (bars[-1].close-green["value"])/bars[-1].close*100 if green else None,
            "partial": state["capped"], "lookbackDays": engine.rules.lookback_days,
            "selection": "fan_"+engine.rules.roots, "dataErrors": data_errors}
