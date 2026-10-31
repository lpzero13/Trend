"""Indexed, unbounded hard-stop paths on real 5m bars; no calendar-day exit.

Interval minima find the first stop touch. Max/min queries avoid scanning years
of identical unchanged stops per case. Missing intervals censor, never fill.
"""
from bisect import bisect_left, bisect_right
from dataclasses import asdict, dataclass
import math

from fan_observer import price_at
from lab_metrics import expected_grid

VERSION = "tori-unbounded-hard-path-1"
MODELS = ("fixed", "original_safety", "fan_safety")


@dataclass(frozen=True)
class CaseExecution:
    notional: float = 1000.
    latency_seconds: int = 300
    spread_bps: float = 5.
    slippage_bps: float = 5.
    fee_per_order: float = 0.
    buffer_pct: float = .3
    tick: float = .01

    def __post_init__(self):
        if (any(type(v) not in (int, float) or not math.isfinite(v) for v in asdict(self).values())
            or self.notional <= self.fee_per_order or not 0 <= self.latency_seconds <= 86400
            or type(self.latency_seconds) is not int or not 0 <= self.spread_bps <= 500
            or not 0 <= self.slippage_bps <= 500 or not 0 <= self.fee_per_order
            or not 0 <= self.buffer_pct < 100 or self.tick <= 0):
            raise ValueError("Invalid isolated-case execution")

    @property
    def cost(self):
        return self.spread_bps/20000+self.slippage_bps/10000


class PathIndex:
    def __init__(self, bars, cutoff, *, start=None):
        self.bars = bars
        self.cutoff = cutoff
        self.times = [b.time for b in bars]
        if any(a >= b for a, b in zip(self.times, self.times[1:])):
            raise ValueError("Unsorted fine bars")
        self.grid = list(expected_grid(start if start is not None else bars[0].time, cutoff+15*86400))
        present = {b.time for b in bars if b.end == b.time+300}
        self.gaps = [t for t in self.grid if t+300 <= cutoff and t not in present]
        self.size = 1
        while self.size < len(bars):
            self.size *= 2
        self.low = [math.inf]*(2*self.size)
        self.high = [-math.inf]*(2*self.size)
        for i, b in enumerate(bars):
            self.low[self.size+i], self.high[self.size+i] = b.low, b.high
        for i in range(self.size-1, 0, -1):
            self.low[i] = min(self.low[2*i], self.low[2*i+1])
            self.high[i] = max(self.high[2*i], self.high[2*i+1])

    def next_open(self, at):
        i = bisect_left(self.grid, at)
        return self.grid[i] if i < len(self.grid) else None

    def extrema(self, left, right):
        lo, hi = math.inf, -math.inf
        left, right = left+self.size, right+self.size
        while left < right:
            if left & 1:
                lo, hi = min(lo, self.low[left]), max(hi, self.high[left])
                left += 1
            if right & 1:
                right -= 1
                lo, hi = min(lo, self.low[right]), max(hi, self.high[right])
            left, right = left//2, right//2
        return lo, hi

    def first_touch(self, left, right, stop):
        def find(node, a, b):
            if right <= a or b <= left or self.low[node] > stop:
                return None
            if b-a == 1:
                return a
            mid = (a+b)//2
            first = find(node*2, a, mid)
            return first if first is not None else find(node*2+1, mid, b)
        return find(1, 0, self.size)


def isolated_entry(signal, index, rules=None):
    r = rules or CaseExecution()
    at = index.next_open(signal["signalAt"]+r.latency_seconds)
    result = {"signalId": signal["id"], "signalAt": signal["signalAt"], "entryAt": at,
              "initialStop": signal.get("initialStop"), "rules": asdict(r), "quantity": 0,
              "status": "pending", "reason": "entry_beyond_data_end"}
    if at is None or at+300 > index.cutoff:
        return result
    stop = result["initialStop"]
    if type(stop) not in (int, float) or not math.isfinite(stop) or stop <= 0:
        return {**result, "status": "rejected", "reason": "invalid_signal_stop"}
    i = bisect_left(index.times, at)
    if i == len(index.bars) or index.bars[i].time != at or index.bars[i].end != at+300:
        return {**result, "status": "unavailable", "reason": "missing_expected_entry_open"}
    raw = index.bars[i].open
    if raw <= stop:
        return {**result, "status": "cancelled", "reason": "opening_gap_through_stop", "entryPrice": raw}
    buy = raw*(1+r.cost)
    qty = (r.notional-r.fee_per_order)/buy
    return {**result, "status": "filled", "reason": None, "entryPrice": raw, "entryFill": buy,
            "quantity": qty, "plannedCash": r.notional, "initialRisk": buy-stop,
            "plannedRisk": qty*(buy-stop*(1-r.cost))+2*r.fee_per_order}


def execute_unbounded(signal, entry, index, timeline, model):
    if model not in MODELS:
        raise ValueError("Unknown unbounded stop model")
    result = {"model": model, "status": entry["status"], "reason": entry.get("reason"),
              "exitAt": None, "netPnl": None, "netR": None, "netReturnPct": None, "stopEvents": []}
    if entry["status"] != "filled":
        return result
    r = CaseExecution(**entry["rules"])
    at, buy, stop = entry["entryAt"], entry["entryFill"], entry["initialStop"]
    pos = bisect_left(index.times, at)
    gap_i = bisect_left(index.gaps, at)
    missing = index.gaps[gap_i] if gap_i < len(index.gaps) else None
    # Also honor explicit source gaps when a malformed aggregate is missing but
    # its fine bars happen to exist. Only actual source closes count as updates.
    for state in timeline:
        if state.get("gapAt") is not None and state["gapAt"] > at:
            stamp = state["gapAt"]
            missing = min(missing, stamp) if missing is not None else stamp
            break
    limit = min(index.cutoff, missing) if missing is not None else index.cutoff
    end = bisect_left(index.times, limit)
    if end and index.bars[end-1].end > limit:
        end -= 1
    low_seen, high_seen = buy, buy
    last_pos = pos

    def finish(raw, bar, reason, at_open):
        sell = raw*(1-r.cost)
        pnl = entry["quantity"]*(sell-buy)-2*r.fee_per_order
        return {**result, "status": "closed", "reason": reason,
                "exitAt": bar.time if at_open else bar.end, "fillBarAt": bar.time, "atOpen": at_open,
                "exitPrice": raw, "exitFill": sell, "netPnl": pnl, "netR": pnl/entry["plannedRisk"],
                "netReturnPct": 100*pnl/entry["plannedCash"], "finalStop": stop,
                "mfeR": (max(high_seen, raw)-buy)/entry["initialRisk"],
                "maeR": (min(low_seen, raw)-buy)/entry["initialRisk"],
                "holdingCalendarDays": ((bar.time if at_open else bar.end)-at)/86400}

    def segment(right):
        nonlocal low_seen, high_seen, last_pos
        hit = index.first_touch(last_pos, right, stop)
        observed_end = hit if hit is not None else right
        if observed_end > last_pos:
            lo, hi = index.extrema(last_pos, observed_end)
            low_seen, high_seen = min(low_seen, lo), max(high_seen, hi)
        last_pos = right
        if hit is not None:
            bar = index.bars[hit]
            # Exit bar high/low sequence unknown: no credit for its later high.
            return finish(bar.open if bar.open <= stop else stop, bar,
                          "stop_gap" if bar.open <= stop else "stop", bar.open <= stop)
        return None

    if model != "fixed":
        ends = [s["closedAt"] for s in timeline]
        for si in range(bisect_right(ends, at), len(timeline)):
            state = timeline[si]
            if state["closedAt"] >= limit:
                break
            safety = signal["safety"] if model == "original_safety" else state["green"]
            if not safety or safety["slope"] <= 0:
                continue
            level = price_at(safety, state["index"])
            if not 0 < level < state["close"]:
                continue
            candidate = math.floor(level*(1-r.buffer_pct/100)/r.tick)*r.tick
            if candidate <= stop:
                continue
            effective = index.next_open(state["closedAt"]+r.latency_seconds)
            if effective is None or effective >= limit:
                break
            right = min(end, bisect_left(index.times, effective))
            closed = segment(right)
            if closed:
                return closed
            change = {"knownAt": state["closedAt"], "effectiveAt": effective, "lineId": safety["id"],
                      "lineKnownAt": safety["knownAt"], "previousStop": stop, "newStop": candidate,
                      "sourceIndex": state["index"], "sourceClose": state["close"]}
            stop = candidate
            result["stopEvents"].append(change)
    closed = segment(end)
    if closed:
        return closed
    last = index.bars[end-1] if end > pos else None
    mark = last.close if last else entry["entryPrice"]
    mark_pnl = entry["quantity"]*(mark*(1-r.cost)-buy)-2*r.fee_per_order
    return {**result, "status": "censored" if missing is not None else "open",
            "reason": "missing_path" if missing is not None else "data_end", "missingAt": missing,
            "lastObservedAt": last.end if last else at, "markPrice": mark,
            "markNetPnl": mark_pnl, "markNetReturnPct": 100*mark_pnl/entry["plannedCash"],
            "finalStop": stop, "mfeR": (high_seen-buy)/entry["initialRisk"],
            "maeR": (low_seen-buy)/entry["initialRisk"]}
