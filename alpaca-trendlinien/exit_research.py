"""Paired, offline exit experiments on frozen historical entry contracts.

Separate from signal selection and the existing paper-execution defaults. Every
decision has a knowledge time. No provider, account or order operation exists.
"""
from bisect import bisect_left
from collections import Counter
from datetime import datetime, timedelta
import math
import statistics

from lab_data import session_bounds
from lab_metrics import expected_grid
from lab_splits import sessions_between
from models import NY
from trendlines import pair, rules_for

VERSION = "tori-paired-exits-1"
MODELS = ("time", "safety", "target_2r", "fakeout", "trailing", "resistance", "tori_combined")
DEFAULT_COSTS = {"spread_bps": 5, "slippage_bps": 5, "fee_per_order": 0,
                 "notional": 1000, "latency_seconds": 300, "tick": .01}


def ray_value(ray, index):
    if ray.get("basis") != "bars":
        raise ValueError("Frozen source-candle ray required")
    return ray["a_price"] + ray["slope"] * (index-ray["a_index"])


def horizon_close(at, days):
    if days not in (5, 10, 20):
        raise ValueError("Use separate 5/10/20 session horizons")
    day = datetime.fromtimestamp(at, NY).date()
    sessions = sessions_between(str(day+timedelta(days=1)), str(day+timedelta(days=days*4+30)))
    return session_bounds(sessions[days-1])[1]


class ExitSources:
    """Phase-bounded bars; causal green selections cached per closed 4h bar."""
    def __init__(self, sources, cutoff):
        self.cutoff = cutoff
        self.fine = [b for b in sources.get("5m", []) if b.end <= cutoff]
        self.times = [b.time for b in self.fine]
        self.four = [b for b in sources["4h"] if b.end <= cutoff]
        self.ends = [b.end for b in self.four]
        self.greens = {}

    def green(self, i):
        if i not in self.greens:
            bar = self.four[i]
            ray = pair(self.four[:i+1], rules_for("4h"))["green"]
            self.greens[i] = ray.output(bar.time) if ray and ray.valid else None
        return self.greens[i]


def exit_path(source, entry, model, days, costs=None):
    if model not in MODELS:
        raise ValueError("Unknown exit model")
    costs = {**DEFAULT_COSTS, **(costs or {})}
    if any(not math.isfinite(costs[k]) or costs[k] < 0 for k in costs):
        raise ValueError("Finite, non-negative execution assumptions required")
    if costs["notional"] <= 2*costs["fee_per_order"]:
        raise ValueError("Notional must cover fees")
    at, price, stop = entry["entryAt"], entry["entryPrice"], entry["initialStop"]
    spread_cost = costs["spread_bps"]/20000 + costs["slippage_bps"]/10000
    if spread_cost >= 1:
        raise ValueError("Execution cost must be below 100%")
    buy = price*(1+spread_cost)
    planned = horizon_close(at, days)
    resistance = entry.get("resistanceAtSignal")
    resistance = resistance if resistance and resistance > price else None
    result = {"version": VERSION, "model": model, "days": days, "status": "censored",
              "entryAt": at, "entryPrice": price, "entryFill": buy, "initialStop": stop,
              "plannedTimeExit": planned, "targetPrice": None, "exitAt": None,
              "exitFill": None, "intrabarAmbiguous": False, "stopUpdates": [],
              "fakeoutObservedAt": None, "knownResistance": resistance}
    if not math.isfinite(price) or not math.isfinite(stop) or not 0 < stop < price:
        return {**result, "status": "invalid", "reason": "invalid_initial_risk"}
    if entry["signalAt"] > at or entry.get("availableAt", at) > at:
        return {**result, "status": "invalid", "reason": "entry_before_knowledge"}
    bounds = session_bounds(str(datetime.fromtimestamp(at, NY).date()))
    if not bounds or not bounds[0] <= at < bounds[1] or (at-bounds[0]) % 300:
        return {**result, "status": "invalid", "reason": "entry_not_on_regular_grid"}
    risk = buy-stop
    target = buy+2*risk if model == "target_2r" else resistance if model in ("resistance", "tori_combined") else None
    result.update(initialRisk=risk, targetPrice=target)
    quantity = (costs["notional"]-costs["fee_per_order"])/buy

    def close(bar, base, reason, *, market=False, ambiguous=False):
        sell = base*(1-spread_cost)
        pnl = quantity*(sell-buy)-2*costs["fee_per_order"]
        return {**result, "status": "closed", "exitAt": bar.end, "fillBarAt": bar.time,
                "exitPrice": base, "exitFill": sell, "exitReason": reason,
                "intrabarAmbiguous": ambiguous, "quantity": quantity,
                "netPnl": pnl, "netReturnPct": pnl/costs["notional"]*100,
                "netR": pnl/(quantity*risk), "finalStop": stop,
                "fillTiming": "fine-bar open" if market else "within fine bar; time exit at close"}

    fine, four = source.fine, source.four
    k = bisect_left(source.times, at)
    if k == len(fine) or fine[k].time != at:
        return {**result, "status": "unavailable", "reason": "entry_open_not_available"}
    j = bisect_left(source.ends, at+1)
    pending = []
    for stamp in expected_grid(at, min(planned, source.cutoff)):
        if k == len(fine) or fine[k].time != stamp:
            return {**result, "reason": "missing_fine_path", "missingAt": stamp}
        bar = fine[k]
        k += 1
        if stamp == at and bar.open != price:
            return {**result, "status": "invalid", "reason": "entry_price_not_source_open"}
        # Closed source bars become usable only after the execution latency.
        while j < len(four) and four[j].end+costs["latency_seconds"] <= stamp:
            current = four[j]
            if current.close < ray_value(entry["red"], j):
                if result["fakeoutObservedAt"] is None:
                    result["fakeoutObservedAt"] = current.end
                if model in ("fakeout", "tori_combined"):
                    pending.append((current.end, "fakeout"))
            if model in ("trailing", "tori_combined"):
                ray = source.green(j)
                # A later anchor must have its confirming pullback in the prefix.
                if ray and ray["b_time"] > entry["green"]["b_time"]:
                    level = ray_value(ray, j)-costs["tick"]
                    if stop < level < current.close:
                        result["stopUpdates"].append({"knownAt": current.end,
                            "effectiveAt": stamp, "price": level, "ray": ray})
                        stop = level
            j += 1
        use_stop = model != "time"
        # An already active stop has priority at a gap; no idealized stop fill.
        if use_stop and bar.open <= stop:
            return close(bar, bar.open, "trailing_gap" if result["stopUpdates"] else "stop_gap", market=True)
        if pending:
            return close(bar, bar.open, "fakeout", market=True)
        if target is not None and bar.open >= target:
            return close(bar, target, "target_at_open", market=True)
        hit_stop = use_stop and bar.low <= stop
        hit_target = target is not None and bar.high >= target
        if hit_stop:
            return close(bar, stop, "trailing_stop" if result["stopUpdates"] else "stop", ambiguous=hit_target)
        if hit_target:
            return close(bar, target, "target")
        if bar.end == planned:
            return close(bar, bar.close, "time")
    return {**result, "reason": "phase_boundary" if planned > source.cutoff else "missing_time_exit_bar"}


def summarize(paths):
    closed = [p for p in paths if p["status"] == "closed"]
    values = [p["netReturnPct"] for p in closed]
    return {"cases": len(paths), "closed": len(closed), "unresolved": len(paths)-len(closed),
            "positive": sum(v > 0 for v in values), "negative": sum(v < 0 for v in values),
            "winRatePct": sum(v > 0 for v in values)/len(values)*100 if values else None,
            "meanNetPct": statistics.mean(values) if values else None,
            "medianNetPct": statistics.median(values) if values else None,
            "meanPnlPer1000USD": statistics.mean(p["netPnl"] for p in closed) if closed else None,
            "meanNetR": statistics.mean(p["netR"] for p in closed) if closed else None,
            "exitReasons": dict(Counter(p["exitReason"] for p in closed)),
            "unresolvedReasons": dict(Counter(p.get("reason") for p in paths if p["status"] != "closed")),
            "ambiguous": sum(p["intrabarAmbiguous"] for p in closed),
            "fakeoutExitsAtLoss": sum(p["exitReason"] == "fakeout" and p["netPnl"] < 0 for p in closed),
            "withKnownResistance": sum(p["knownResistance"] is not None for p in paths)}
