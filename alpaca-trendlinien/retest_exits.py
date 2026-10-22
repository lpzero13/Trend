"""Isolated stop-only Retest experiment; no signal reselection or provider calls."""
from bisect import bisect_left, bisect_right
from collections import Counter
from copy import deepcopy
from datetime import datetime
from statistics import mean

from exit_research import horizon_close, ray_value
from lab_data import session_bounds
from lab_metrics import expected_grid, blocked_interval
from lab_splits import sessions_between
from models import NY
from safety_strategy import SafetyState, strategy_path

VERSION = "retest-stop-comparison-1"
MODELS = ("fixed", "higher_low_stop")


class HigherLowStop(SafetyState):
    """Reuse strict connected pivots without adding a diagonal close-exit.

    A replacement must be above the old ray and below current close. If close
    is below the old ray, no such replacement can exist on that bar anyway.
    """
    def step(self, i, effective_at):
        if i != self.last_index+1:
            raise ValueError("Stop state must process each closed source bar once")
        if self.context.four[i].close < ray_value(self.ray, i):
            self.last_index = i
            self.diagnostics["diagonal_close_not_a_stop_exit"] = self.diagnostics.get("diagonal_close_not_a_stop_exit", 0)+1
            return
        super().step(i, effective_at)
        if self.exit_signal is not None:
            raise AssertionError("Stop-only model cannot create diagonal exits")


def contract_for(context, entry, costs):
    # Archive already has a buffered initialStop. Reconstruct from raw once.
    raw = {**entry, "initialStop": entry["rawSafety"]}
    contract = context.entry_contract(raw, costs)
    if abs(contract["initialStop"]-entry["initialStop"]) > 1e-8:
        raise ValueError("Reconstructed stop differs from frozen entry")
    return contract


def complete_history(sources, entry):
    four = sources["4h"]
    n = bisect_right([b.end for b in four], entry["signalAt"])
    if n < 15 or four[n-1].end != entry["signalAt"]:
        return {"complete": False, "reason": "missing_signal_atr_history"}
    start = min(entry["red"]["a_time"], entry["green"]["a_time"], four[n-15].time)
    actual = {(b.time, b.end) for b in four if start <= b.time and b.end <= entry["signalAt"]}
    first, last = [str(datetime.fromtimestamp(t, NY).date()) for t in (start, entry["signalAt"])]
    expected = set()
    for day in sessions_between(first, last):
        opened, closed = session_bounds(day)
        expected.update((t, min(t+14400, closed)) for t in range(opened, closed, 14400)
                        if start <= t and min(t+14400, closed) <= entry["signalAt"])
    return {"complete": expected <= actual, "expected": len(expected), "missing": len(expected-actual),
            "startAt": start, "knownAt": entry["signalAt"]}


def path(context, entry, contract, model):
    if model == "fixed":
        return strategy_path(context, entry, contract, "fixed", 10)
    if model != "higher_low_stop":
        raise ValueError("Unknown internal stop model")
    state = HigherLowStop(context, entry, contract, "structure")
    planned = horizon_close(entry["entryAt"], 10)
    result = {"version": VERSION, "entryId": entry["id"], "model": model, "days": 10,
        "status": "censored", "entryAt": entry["entryAt"], "entryPrice": entry["entryPrice"],
        "entryFill": contract["entryFill"], "initialStop": contract["initialStop"],
        "initialRisk": contract["initialRisk"], "plannedTimeExit": planned,
        "targetPrice": None, "exitAt": None, "exitFill": None, "events": state.events,
        "structureDiagnostics": state.diagnostics, "intrabarAmbiguous": False}
    if not contract["checks"]["known_atr"] or not contract["checks"]["positive_stop"]:
        return {**result, "status": "unavailable", "reason": "invalid_or_unknown_initial_safety"}
    at = entry["entryAt"]
    bounds = session_bounds(str(datetime.fromtimestamp(at, NY).date()))
    if not bounds or not bounds[0] <= at < bounds[1] or (at-bounds[0]) % 300 or entry["signalAt"] > at or entry.get("availableAt", at) > at:
        return {**result, "status": "invalid", "reason": "invalid_entry_knowledge_or_grid"}
    fine_i = bisect_left(context.times, entry["entryAt"])
    if fine_i == len(context.times) or context.times[fine_i] != at:
        return {**result, "status": "unavailable", "reason": "entry_open_not_available"}
    source_i = contract["entryIndex"]+1
    costs = contract["costs"]
    qty = (costs["notional"]-costs["fee_per_order"])/contract["entryFill"]
    for stamp in expected_grid(entry["entryAt"], min(planned, context.cutoff)):
        if fine_i >= len(context.fine) or context.fine[fine_i].time != stamp:
            return {**result, "reason": "missing_fine_path", "missingAt": stamp}
        bar = context.fine[fine_i]
        fine_i += 1
        if stamp == entry["entryAt"] and bar.open != entry["entryPrice"]:
            return {**result, "status": "invalid", "reason": "entry_price_not_source_open"}
        while source_i < len(context.four) and context.four[source_i].end+context.rules["latency_seconds"] <= stamp:
            state.step(source_i, stamp)
            source_i += 1
        base, reason, at_open = None, None, False
        if bar.open <= state.hard_stop:
            base, reason, at_open = bar.open, "hard_stop_gap", True
        elif bar.low <= state.hard_stop:
            base, reason = state.hard_stop, "hard_stop"
        elif bar.end == planned:
            base, reason = bar.close, "time"
        if reason:
            sell = base*(1-costs["side_cost"])
            pnl = qty*(sell-contract["entryFill"])-2*costs["fee_per_order"]
            return {**result, "status": "closed", "exitPrice": base, "exitFill": sell,
                "exitAt": bar.end, "fillBarAt": bar.time, "atOpen": at_open, "exitReason": reason,
                "quantity": qty, "netPnl": pnl, "netReturnPct": pnl/costs["notional"]*100,
                "netR": pnl/(qty*contract["initialRisk"]), "finalHardStop": state.hard_stop,
                "activeRay": deepcopy(state.ray)}
    return {**result, "reason": "phase_boundary" if planned > context.cutoff else "missing_time_exit_bar"}


def trade_stats(paths):
    closed = sorted((p for p in paths if p["status"] == "closed"), key=lambda p: (p["exitAt"], p["entryId"]))
    values = [p["netR"] for p in closed]
    wins, losses = [v for v in values if v > 0], [v for v in values if v < 0]
    streak = longest = 0
    cumulative = peak = worst = 0.
    for v in values:
        streak = streak+1 if v < 0 else 0
        longest = max(longest, streak)
        cumulative += v
        peak = max(peak, cumulative)
        worst = min(worst, cumulative-peak)
    return {"cases": len(paths), "closed": len(closed), "unknown": len(paths)-len(closed),
        "meanR": mean(values) if values else None, "meanReturnPct": mean(p["netReturnPct"] for p in closed) if closed else None,
        "winPct": 100*len(wins)/len(values) if values else None,
        "meanWinR": mean(wins) if wins else None, "meanLossR": mean(losses) if losses else None,
        "profitFactorR": sum(wins)/-sum(losses) if losses else None,
        "longestLossStreak": longest, "maxCumulativeTradeRDrawdown": worst,
        "exitReasons": dict(Counter(p["exitReason"] for p in closed)),
        "structureUpdates": sum(len(p["events"]) for p in paths),
        "stopRaises": sum(e["hardStop"] > e["previousHardStop"]+1e-8 for p in paths for e in p["events"]),
        "withoutBestMeanR": mean(sorted(values)[:-1]) if len(values) > 1 else None,
        "meaning": "Overlapping independent-position outcomes; cumulative R drawdown is not a portfolio drawdown."}


def summarize(records):
    output = {}
    for geometry in ("hull_exact", "swing_zone"):
        for group in ("complete_history", "gapped_history"):
            rows = [r for r in records if r["entry"]["model"] == geometry and
                    r["history"]["complete"] == (group == "complete_history") and r["calendarFits"]]
            paired = [r for r in rows if all(r["paths"][m]["status"] == "closed" for m in MODELS)]
            deltas = [{"symbol": r["entry"]["symbol"], "entryAt": r["entry"]["entryAt"],
                       "deltaR": r["paths"][MODELS[1]]["netR"]-r["paths"]["fixed"]["netR"]} for r in paired]
            output[geometry+"/"+group] = {"cases": len(rows), "pairedClosed": len(paired),
                "models": {m: trade_stats([r["paths"][m] for r in rows]) for m in MODELS},
                "pairedModels": {m: trade_stats([r["paths"][m] for r in paired]) for m in MODELS},
                "meanDeltaR": mean(d["deltaR"] for d in deltas) if deltas else None,
                "deltaInterval": blocked_interval(deltas, "deltaR", seed=20261022),
                "fullHorizonPaired": {m: trade_stats([r["paths"][m] for r in paired if r["fullHorizonPath"]]) for m in MODELS}}
    return output
