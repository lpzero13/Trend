"""Causal, versioned Safety-Line strategies; no provider or broker operations.

The initial trade contract uses known data only. The active ray owns its anchors;
global chart line reselection cannot modify it. A 4h close is checked against the
previous active ray BEFORE a newly confirmed higher-low ray can replace it.
"""
from bisect import bisect_left, bisect_right
from copy import deepcopy
from datetime import datetime, timedelta
import math

from datasets import digest
from exit_research import DEFAULT_COSTS, horizon_close, ray_value
from lab_data import session_bounds
from lab_metrics import expected_grid
from lab_splits import sessions_between
from models import NY, DataError
from tori_entries import aggregate, atr, structure

VERSION = "tori-safety-structure-1"
MODELS = ("fixed", "original", "structure", "structure_target")
DEFAULT_RULES = {"source_timeframe": "4h", "pivot_side": 2, "initial_buffer_atr": .25,
                 "zone_width_atr": .10, "daily_prominence_atr": 1.,
                 "min_room_r": 2., "max_risk_atr": 2., "min_age_days": 7.,
                 "tick": .01, "latency_seconds": 300}


def validate_rules(value=None):
    if value is not None and not isinstance(value, dict):
        raise DataError("Strategieregeln als Objekt angeben.", 400)
    if set(value or {})-set(DEFAULT_RULES):
        raise DataError("Unbekannte Strategieregel.", 400)
    result = {**DEFAULT_RULES, **(value or {})}
    if result["source_timeframe"] != "4h" or type(result["pivot_side"]) is not int or not 1 <= result["pivot_side"] <= 5:
        raise DataError("Safety-Strategie verwendet 4h und 1–5 Pivotnachbarn.", 400)
    for key in ("initial_buffer_atr", "zone_width_atr", "daily_prominence_atr", "min_room_r", "max_risk_atr", "min_age_days", "tick"):
        v = result[key]
        if type(v) not in (int, float) or not math.isfinite(v) or not 0 < v <= (365 if key == "min_age_days" else 10):
            raise DataError("Ungültiger Strategieparameter: "+key, 400)
    if type(result["latency_seconds"]) is not int or not 300 <= result["latency_seconds"] <= 86400 or result["latency_seconds"] % 300:
        raise DataError("Strategielatenz in ganzen 5m-Schritten ab fünf Minuten.", 400)
    return result


def pivot_indices(bars, upper, side=2):
    values = [b.high if upper else b.low for b in bars]
    return [i for i in range(side, len(bars)-side)
            if all(values[i] > values[j] if upper else values[i] < values[j]
                   for j in range(i-side, i+side+1) if j != i)]


def latest_session_close(at):
    day = datetime.fromtimestamp(at, NY).date()
    days = sessions_between(str(day-timedelta(days=12)), str(day))
    return max((session_bounds(d)[1] for d in days if session_bounds(d)[1] <= at), default=None)


def latest_week_close(at):
    day = datetime.fromtimestamp(at, NY).date()
    weeks = {}
    for d in sessions_between(str(day-timedelta(days=35)), str(day+timedelta(days=7))):
        date = datetime.fromisoformat(d).date()
        week = date-timedelta(days=date.weekday())
        weeks[week] = max(weeks.get(week, 0), session_bounds(d)[1])
    return max((end for end in weeks.values() if end <= at), default=None)


class StrategyContext:
    def __init__(self, sources, cutoff, rules=None):
        self.rules = validate_rules(rules)
        self.cutoff = cutoff
        self.sources = {tf: [b for b in rows if b.end <= cutoff] for tf, rows in sources.items()}
        self.fine = self.sources.get("5m", [])
        self.four = self.sources["4h"]
        self.daily = self.sources["1D"]
        self.weekly = aggregate(self.daily)
        self.times = [b.time for b in self.fine]
        self.ends = [b.end for b in self.four]
        self.daily_ends = [b.end for b in self.daily]
        self.week_ends = [b.end for b in self.weekly]
        self.context_cache = {}

    def known_context(self, at):
        nd, nw = bisect_right(self.daily_ends, at), bisect_right(self.week_ends, at)
        key = (nd, nw)
        if key not in self.context_cache:
            daily, weekly = self.daily[:nd], self.weekly[:nw]
            width = max(self.rules["tick"], (atr(daily) or 0)*self.rules["zone_width_atr"])
            levels = []
            side = self.rules["pivot_side"]
            for tf, rows in (("1D", daily), ("1W", weekly)):
                for i in pivot_indices(rows, True, side):
                    known_at = rows[i+side].end
                    volatility = atr(rows[:i+side+1])
                    prominence = rows[i].high-max(min(b.low for b in rows[i-side:i]), min(b.low for b in rows[i+1:i+side+1]))
                    if tf == "1D" and (volatility is None or prominence < self.rules["daily_prominence_atr"]*volatility):
                        continue
                    upper = rows[i].high+width
                    # Do not resurrect an already closed-through resistance just
                    # because the price later fell back below the old pivot.
                    if any(b.close > upper for b in daily if b.end > known_at):
                        continue
                    levels.append({"timeframe": tf, "pivotAt": rows[i].time,
                                   "knownAt": known_at, "price": rows[i].high,
                                   "lower": rows[i].high-width, "upper": upper,
                                   "prominence": prominence})
            zones = []
            for level in sorted(levels, key=lambda p: (p["lower"], p["timeframe"], p["pivotAt"])):
                if zones and level["lower"] <= zones[-1]["upper"]:
                    zone = zones[-1]
                    zone["upper"] = max(zone["upper"], level["upper"])
                    zone["sources"].append(level)
                else:
                    zones.append({"lower": level["lower"], "upper": level["upper"], "sources": [level]})
            for zone in zones:
                zone["id"] = digest(zone)
            self.context_cache[key] = {"daily": structure(daily), "weekly": structure(weekly),
                "monthly": structure(aggregate(daily, True)), "dailyATR": atr(daily),
                "lastDailyClose": daily[-1].end if daily else None,
                "lastWeeklyClose": weekly[-1].end if weekly else None, "zones": zones}
        return deepcopy(self.context_cache[key])

    def entry_contract(self, entry, costs=None):
        costs = execution_costs(costs)
        e = deepcopy(entry)
        at, price = e["entryAt"], e["entryPrice"]
        n = bisect_right(self.ends, at)
        known = self.four[:n]
        volatility = atr(known)
        buffer = max(self.rules["tick"], volatility*self.rules["initial_buffer_atr"]) if volatility is not None else None
        stop = e["initialStop"]-buffer if buffer is not None else None
        context = self.known_context(at)
        fresh = context["lastDailyClose"] == latest_session_close(at)
        week_fresh = context["lastWeeklyClose"] == latest_week_close(at)
        buy = price*(1+costs["side_cost"])
        risk = buy-stop if stop is not None else None
        zones = context["zones"] if context["dailyATR"] is not None else []
        zone = next((z for z in zones if z["upper"] > price), None)
        target = zone["lower"] if zone and zone["lower"] > price else None
        room = (zone["lower"]*(1-costs["side_cost"])-buy)/risk if zone and risk and risk > 0 else None
        age = (at-e["red"]["a_time"])/86400
        checks = {"known_atr": volatility is not None,
                  "positive_stop": bool(stop is not None and 0 < stop < price),
                  "risk_atr": None if volatility is None or not risk else risk/volatility <= self.rules["max_risk_atr"],
                  "line_age": age >= self.rules["min_age_days"],
                  "fresh_daily": fresh,
                  "fresh_weekly": week_fresh,
                  "daily_context": None if context["daily"] == "unknown" else context["daily"] != "down",
                  "weekly_context": None if context["weekly"] == "unknown" else context["weekly"] != "down",
                  "net_room": None if room is None else room >= self.rules["min_room_r"]}
        result = {"version": VERSION, "entryId": e.get("id"), "entryAt": at,
                  "entryPrice": price, "entryFill": buy, "initialStop": stop,
                  "originalSafetyPrice": e["initialStop"], "initialRisk": risk,
                  "atr": volatility, "buffer": buffer, "entryIndex": n-1,
                  "referenceHigh": known[-1].high if known else None,
                  "red": e["red"], "green": e["green"], "context": context,
                  "zone": zone, "targetPrice": target, "netRoomR": room,
                  "checks": checks, "eligible": all(v is True for v in checks.values()),
                  "blockedBy": [k for k, v in checks.items() if v is not True],
                  "redContacts": e["red"].get("contacts"), "greenContacts": e["green"].get("contacts"),
                  "knownAt": at, "costs": costs, "rules": self.rules}
        result["id"] = digest(result)
        return result


def execution_costs(value=None):
    allowed = {"spread_bps", "slippage_bps", "fee_per_order", "notional"}
    if value is not None and (not isinstance(value, dict) or set(value)-allowed):
        raise DataError("Unbekannte Strategiekosten.", 400)
    c = {k: DEFAULT_COSTS[k] for k in allowed}
    c.update(value or {})
    if any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in c.values()) or c["notional"] <= 2*c["fee_per_order"]:
        raise DataError("Ungültige Strategiekosten.", 400)
    c["side_cost"] = c["spread_bps"]/20000+c["slippage_bps"]/10000
    if c["side_cost"] >= 1:
        raise DataError("Ausführungskosten müssen unter 100 Prozent liegen.", 400)
    return c


class SafetyState:
    """Mutable only through chronological closed source bars; serializable journal."""
    def __init__(self, context, entry, contract, model):
        self.context, self.entry, self.contract, self.model = context, entry, contract, model
        self.ray = deepcopy(contract["green"])
        self.hard_stop = contract["initialStop"]
        self.peak = contract["referenceHigh"]
        self.last_index = contract["entryIndex"]
        self.exit_signal = None
        self.events = []
        self.diagnostics = {}

    def step(self, i, effective_at):
        if i != self.last_index+1:
            raise ValueError("Safety state must advance exactly once in chronological order")
        self.last_index = i
        bars, rules = self.context.four, self.context.rules
        current = bars[i]
        old_level = ray_value(self.ray, i)
        if self.model != "fixed" and current.close < old_level:
            self.exit_signal = {"kind": "safety_close", "knownAt": current.end,
                                "effectiveAt": effective_at, "price": current.close,
                                "level": old_level, "ray": deepcopy(self.ray)}
            self.events.append(self.exit_signal)
            return
        if self.model not in ("structure", "structure_target"):
            return
        side = rules["pivot_side"]
        b = i-side
        if b < side or bars[b].time <= self.entry["entryAt"] or bars[b].time <= self.ray["b_time"]:
            return
        if not all(bars[b].low < bars[j].low for j in range(b-side, b+side+1) if j != b):
            return
        self.diagnostics["confirmed_post_entry_lows"] = self.diagnostics.get("confirmed_post_entry_lows", 0)+1
        a = self.ray["b_index"]
        if bars[b].low <= bars[a].low:
            self.diagnostics["not_higher_than_active_B"] = self.diagnostics.get("not_higher_than_active_B", 0)+1
            return
        preceding = [bar.high for j, bar in enumerate(bars[:b])
                     if j > a and bar.time >= self.entry["entryAt"]]
        if not preceding or max(preceding) <= self.peak:
            self.diagnostics["no_new_higher_high"] = self.diagnostics.get("no_new_higher_high", 0)+1
            return
        slope = (bars[b].low-bars[a].low)/(b-a)
        if any(bar.low+1e-7 < bars[a].low+slope*(j-a) for j, bar in enumerate(bars[a:i+1], a)):
            self.diagnostics["connected_ray_cuts_wick"] = self.diagnostics.get("connected_ray_cuts_wick", 0)+1
            return
        level = bars[a].low+slope*(i-a)
        if not old_level+rules["tick"] < level < current.close:
            self.diagnostics["not_tighter_below_close"] = self.diagnostics.get("not_tighter_below_close", 0)+1
            return
        volatility = atr(bars[:i+1])
        if volatility is None:
            return
        ray = {"basis": "bars", "a_index": a, "b_index": b,
               "a_time": bars[a].time, "b_time": bars[b].time,
               "a_price": bars[a].low, "b_price": bars[b].low, "slope": slope,
               "valid": True, "confirmedAt": current.end}
        stop = max(self.hard_stop, bars[b].low-max(rules["tick"], volatility*rules["initial_buffer_atr"]))
        self.events.append({"kind": "safety_replace", "knownAt": current.end, "effectiveAt": effective_at,
                            "previousRay": deepcopy(self.ray), "ray": ray,
                            "previousHardStop": self.hard_stop, "hardStop": stop,
                            "higherHigh": max(preceding), "atr": volatility})
        self.ray, self.hard_stop, self.peak = ray, stop, max(preceding)


def strategy_path(context, entry, contract, model, days):
    if model not in MODELS:
        raise DataError("Unbekannte Safety-Strategie.", 400)
    costs, at, price = contract["costs"], entry["entryAt"], entry["entryPrice"]
    planned = horizon_close(at, days)
    target = contract["targetPrice"] if model == "structure_target" else None
    result = {"version": VERSION, "entryId": entry.get("id"), "contractId": contract["id"],
              "model": model, "days": days, "status": "censored", "entryAt": at,
              "entryPrice": price, "entryFill": contract["entryFill"],
              "initialStop": contract["initialStop"], "initialRisk": contract["initialRisk"],
              "plannedTimeExit": planned, "targetPrice": target, "exitAt": None,
              "exitFill": None, "events": [], "intrabarAmbiguous": False}
    if not contract["checks"]["known_atr"] or not contract["checks"]["positive_stop"]:
        return {**result, "status": "unavailable", "reason": "invalid_or_unknown_initial_safety"}
    bounds = session_bounds(str(datetime.fromtimestamp(at, NY).date()))
    if not bounds or not bounds[0] <= at < bounds[1] or (at-bounds[0]) % 300 or entry["signalAt"] > at or entry.get("availableAt", at) > at:
        return {**result, "status": "invalid", "reason": "invalid_entry_knowledge_or_grid"}
    k = bisect_left(context.times, at)
    if k == len(context.fine) or context.fine[k].time != at:
        return {**result, "status": "unavailable", "reason": "entry_open_not_available"}
    state = SafetyState(context, entry, contract, model)
    n = contract["entryIndex"]+1
    result["events"] = state.events
    result["structureDiagnostics"] = state.diagnostics
    qty = (costs["notional"]-costs["fee_per_order"])/contract["entryFill"]

    def close(bar, base, reason, at_open=False, ambiguous=False):
        sell = base*(1-costs["side_cost"])
        pnl = qty*(sell-contract["entryFill"])-2*costs["fee_per_order"]
        return {**result, "status": "closed", "exitPrice": base, "exitFill": sell,
                "exitAt": bar.end, "fillBarAt": bar.time, "atOpen": at_open,
                "exitReason": reason, "quantity": qty, "netPnl": pnl,
                "netReturnPct": pnl/costs["notional"]*100,
                "netR": pnl/(qty*contract["initialRisk"]),
                "finalHardStop": state.hard_stop, "activeRay": state.ray,
                "intrabarAmbiguous": ambiguous}

    for stamp in expected_grid(at, min(planned, context.cutoff)):
        if k == len(context.fine) or context.fine[k].time != stamp:
            return {**result, "reason": "missing_fine_path", "missingAt": stamp}
        bar = context.fine[k]
        k += 1
        if stamp == at and bar.open != price:
            return {**result, "status": "invalid", "reason": "entry_price_not_source_open"}
        while n < len(context.four) and context.four[n].end+context.rules["latency_seconds"] <= stamp and state.exit_signal is None:
            state.step(n, stamp)
            n += 1
        stop = state.hard_stop
        if bar.open <= stop:
            return close(bar, bar.open, "hard_stop_gap", True)
        if state.exit_signal:
            return close(bar, bar.open, "safety_close", True)
        if target is not None and bar.open >= target:
            return close(bar, target, "resistance_at_open", True)
        hit_target = target is not None and bar.high >= target
        if bar.low <= stop:
            return close(bar, stop, "hard_stop", ambiguous=hit_target)
        if hit_target:
            return close(bar, target, "resistance")
        if bar.end == planned:
            return close(bar, bar.close, "time")
    return {**result, "reason": "phase_boundary" if planned > context.cutoff else "missing_time_exit_bar"}
