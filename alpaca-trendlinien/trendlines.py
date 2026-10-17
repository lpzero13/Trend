"""Automatic wick envelopes derived from Tori v5, using source candle positions.

The server supplies completed bars up to its explicit cutoff. Snapshot storage and
chart projections are separate from this deterministic calculation. No order logic.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from bisect import bisect_right

from models import Bar, NY

DAY = 86400
RULES_VERSION = "tori-candle-axis-0.2"


@dataclass(frozen=True)
class Rules:
    basis: str = "bars"
    lookback_days: int = 365
    selection: str = "quality"
    pullback_bars: int = 1
    min_touches: int = 3
    min_span_days: float = 7
    tick: float = 0.01
    tolerance_ticks: int = 1
    event_bars: int = 12


@dataclass
class Ray:
    a_time: int
    a_price: float
    b_time: int
    b_price: float
    slope: float
    contacts: int
    span_days: float
    valid: bool
    qualified: bool
    a_index: int = 0
    b_index: int = 0
    source_times: tuple[int, ...] = ()
    basis: str = "time"

    def value(self, timestamp: int, position: float | None = None) -> float:
        if self.basis == "bars":
            x = position if position is not None else position_at(self.source_times, timestamp)
            return self.a_price + self.slope * (x - self.a_index)
        return self.a_price + self.slope * (timestamp - self.a_time)

    def output(self, reference: int, axis: tuple[int, ...] | None = None) -> dict:
        result = {name: getattr(self, name) for name in self.__dataclass_fields__ if name != "source_times"}
        result["value"] = self.value(reference, position_at(axis, reference) if axis and self.basis == "bars" else None)
        return result


def position_at(axis, timestamp):
    if len(axis) < 2:
        return 0.0
    if timestamp >= axis[-1]:
        tail = axis[-64:]
        step = sorted(b-a for a,b in zip(tail, tail[1:]) if b > a)
        normal = step[len(step)//2] if step else 1
        return len(axis)-1+(timestamp-axis[-1])/normal
    i = max(0, min(len(axis)-2, bisect_right(axis, timestamp)-1))
    return i + (timestamp-axis[i])/(axis[i+1]-axis[i])


def epsilon(price: float, tick: float) -> float:
    return max(tick * 0.000001, abs(price) * 0.0000000001)


def cut(wick: float, level: float, upper: bool, rules: Rules) -> bool:
    return wick > level + epsilon(level, rules.tick) if upper else wick < level - epsilon(level, rules.tick)


def touch(wick: float, level: float, rules: Rules) -> bool:
    return abs(wick - level) <= max(rules.tick * rules.tolerance_ticks, epsilon(level, rules.tick))


def window_start(source_close: int, days: int) -> int:
    local = datetime.fromtimestamp(source_close, NY).replace(hour=0, minute=0, second=0, microsecond=0)
    # Pine subtracts elapsed calendar-day milliseconds from exchange-local midnight.
    return int(local.timestamp()) - days * DAY


def build(bars: list[Bar], upper: bool, rules: Rules) -> list[Ray]:
    if len(bars) < 2:
        return []
    cutoff = window_start(bars[-1].end, rules.lookback_days)
    start = next((i for i, bar in enumerate(bars) if bar.time >= cutoff), len(bars))
    if start >= len(bars) - 1:
        return []
    level = lambda i: bars[i].high if upper else bars[i].low
    coordinate = lambda i: i if rules.basis == "bars" else bars[i].time
    axis = tuple(bar.time for bar in bars)
    anchor = start
    for i in range(start, len(bars)):
        if level(i) > level(anchor) if upper else level(i) < level(anchor):
            anchor = i
    hull = [anchor]
    for i in range(anchor + 1, len(bars)):
        while len(hull) >= 2:
            a, b = hull[-2:]
            old = (level(b) - level(a)) / (coordinate(b) - coordinate(a))
            new = (level(i) - level(b)) / (coordinate(i) - coordinate(b))
            if not (new >= old if upper else new <= old):
                break
            hull.pop()
        hull.append(i)
    rays = []
    for a, b in zip(hull, hull[1:]):
        at, bt, av, bv = bars[a].time, bars[b].time, level(a), level(b)
        slope = (bv - av) / (coordinate(b) - coordinate(a))
        direction_ok = slope < 0 if upper else slope > 0
        pullback_ok = len(bars) - 1 - b >= rules.pullback_bars
        if pullback_ok:
            for k in range(1, rules.pullback_bars + 1):
                if level(b + k) >= level(b) if upper else level(b + k) <= level(b):
                    pullback_ok = False
        if not direction_ok or not pullback_ok:
            break
        contacts = []
        valid = direction_ok
        for i in range(a, b + 1):
            projected = av + slope * (coordinate(i) - coordinate(a))
            valid = valid and not cut(level(i), projected, upper, rules)
            if touch(level(i), projected, rules):
                contacts.append(bars[i].time)
        span = (contacts[-1] - contacts[0]) / DAY if contacts else 0
        rays.append(Ray(at, av, bt, bv, slope, len(contacts), span, valid,
                        valid and len(contacts) >= rules.min_touches and span >= rules.min_span_days,
                        a, b, axis, rules.basis))
    return rays


def choose(rays: list[Ray], rules: Rules) -> Ray | None:
    chosen = None
    best_score = -1.0
    qualified_found = False
    for ray in rays:
        score = min(ray.contacts / rules.min_touches, 1) + min(ray.span_days / rules.min_span_days, 1)
        if rules.selection == "inner":
            chosen = ray
        elif ray.qualified:
            chosen, qualified_found = ray, True
        elif not qualified_found and score >= best_score:
            chosen, best_score = ray, score
    return chosen


def pair(bars: list[Bar], rules: Rules) -> dict:
    reds, greens = build(bars, True, rules), build(bars, False, rules)
    return {"reds": reds, "greens": greens, "red": choose(reds, rules), "green": choose(greens, rules)}


def outer_rays(rays: list[Ray], active: Ray | None) -> list[Ray]:
    if active is None:
        return []
    index = rays.index(active)
    return rays[max(0, index - 3):index]


def rules_for(timeframe: str) -> Rules:
    return Rules(lookback_days=60, selection="inner") if timeframe == "1h" else Rules()


def detect_break(previous: dict, before: Bar, current: Bar, position: int,
                 rules: Rules, *, partial=False, data_errors=False):
    """One causal step against lines selected BEFORE the new bar was known."""
    red, green = previous["red"], previous["green"]
    red_break = red is not None and red.valid and current.close > red.value(current.time, position) and before.close <= red.value(before.time, position-1)
    green_break = green is not None and current.close < green.value(current.time, position) and before.close >= green.value(before.time, position-1)
    event = None
    if green_break:
        event = {"kind": "green_break", "time": current.time, "closedAt": current.end, "price": current.close}
    elif red_break:
        ordered = green is not None and 0 < green.value(current.time, position) < red.value(current.time, position)
        safety_cut = green is None or not green.valid or cut(current.low, green.value(current.time, position), False, rules)
        qualified = ordered and not safety_cut and red.qualified and green.qualified and not partial and not data_errors
        event = {"kind": "long_break" if qualified else "red_break", "time": current.time, "closedAt": current.end, "price": current.close}
    return event, red_break


def analyze(bars: list[Bar], timeframe: str, reference: int, *, data_errors: bool = False) -> dict:
    rules = rules_for(timeframe)
    ending = len(bars) - 1
    start = window_start(bars[-1].end, rules.lookback_days)
    window_size = sum(bar.time >= start for bar in bars)
    budget = min(rules.event_bars, max(1, 4000 // max(1, window_size)))
    first = max(1, ending - budget)
    previous = pair(bars[:first + 1], rules)
    broken = None
    event = None
    for i in range(first + 1, len(bars)):
        current, before = bars[i], bars[i - 1]
        red = previous["red"]
        step_event, red_break = detect_break(previous, before, current, i, rules,
            partial=bars[0].time > window_start(before.end, rules.lookback_days), data_errors=data_errors)
        if step_event:
            event = step_event
        if red_break:
            broken = {"ray": red, "time": current.time, "closedAt": current.end}
        previous = pair(bars[:i + 1], rules)
    red, green = previous["red"], previous["green"]
    partial = bars[0].time > start
    if red and green:
        status = "Qualifiziert" if red.qualified and green.qualified else "Vorläufig"
    else:
        status = "Linienpaar fehlt"
    if red and green and green.value(reference) >= red.value(reference):
        status = "Linien gekreuzt"
    if green and bars[-1].close < green.value(bars[-1].time):
        status = "Grün unterschritten"
    distance = (bars[-1].close - green.value(bars[-1].time)) / bars[-1].close * 100 if green else None
    axis = tuple(bar.time for bar in bars)
    return {
        "basis": "bars", "sourceTimes": list(axis),
        "timeframe": timeframe, "red": red.output(reference, axis) if red else None,
        "green": green.output(reference, axis) if green else None,
        "outerRed": [r.output(reference, axis) for r in outer_rays(previous["reds"], red)],
        "outerGreen": [r.output(reference, axis) for r in outer_rays(previous["greens"], green)],
        "retest": ({"ray": broken["ray"].output(reference, axis), "time": broken["time"], "closedAt": broken["closedAt"]}
                   if broken and bars[-1].end - broken["closedAt"] <= 30 * DAY else None),
        "event": event, "status": status, "distance": distance, "partial": partial,
        "lookbackDays": rules.lookback_days, "selection": rules.selection,
        "sourceClose": bars[-1].end, "sourceFirst": bars[0].time,
        "searchedBars": ending - first, "dataErrors": data_errors,
        "rules": asdict(rules),
    }
