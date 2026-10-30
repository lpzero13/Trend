"""Post-signal paper fills. Never imported by the fan or its observer.

Uses the shared XNYS 5m grid. No skipping missing opens, no invented gap fills,
no retrospective tightening, no portfolio-return claim from independent cases.
"""
from bisect import bisect_left
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
import math

from lab_data import session_bounds
from lab_metrics import expected_grid
from lab_splits import sessions_between
from models import DataError, NY

VERSION = "tori-fan-paper-execution-1"


@dataclass(frozen=True)
class ExecutionRules:
    latency_seconds: int = 300
    capital: float = 2000.
    risk_fraction: float = .01
    spread_bps: float = 5.
    slippage_bps: float = 5.
    fee_per_order: float = 0.
    target_r: float = 0.
    pivot_side: int = 2
    trailing_buffer_pct: float = .3
    tick: float = .01

    def __post_init__(self):
        for name, lo, hi in (("latency_seconds", 0, 86400), ("pivot_side", 1, 6)):
            value = getattr(self, name)
            if type(value) is not int or not lo <= value <= hi:
                raise DataError(f"Ungültiger Ausführungsparameter {name}.", 400)
        for name, lo, hi in (("capital", 1, 1e9), ("risk_fraction", .0001, 1),
                             ("spread_bps", 0, 500), ("slippage_bps", 0, 500),
                             ("fee_per_order", 0, 10000), ("target_r", 0, 50),
                             ("trailing_buffer_pct", 0, 10), ("tick", 1e-8, 100)):
            value = getattr(self, name)
            if type(value) not in (float, int) or not math.isfinite(value) or not lo <= value <= hi:
                raise DataError(f"Ungültiger Ausführungsparameter {name}.", 400)


def next_open_time(available_at):
    return next(expected_grid(available_at, available_at+14*86400), None)


def entry_contract(signal, fine, cutoff, rules=None):
    """Conditional next-open paper entry, using no subsequent high/low/return."""
    r = rules or ExecutionRules()
    available = signal["signalAt"]+r.latency_seconds
    at = next_open_time(available)
    result = {"version": VERSION, "signalId": signal["id"], "signalAt": signal["signalAt"],
              "availableAt": available, "entryAt": at, "initialStop": signal.get("initialStop"),
              "status": "unavailable", "entryPrice": None, "entryFill": None, "quantity": 0,
              "rules": asdict(r)}
    if at is None or at+300 > cutoff:
        return {**result, "status": "pending", "reason": "entry_beyond_boundary"}
    stop = signal.get("initialStop")
    if type(stop) not in (int, float) or not math.isfinite(stop) or stop <= 0:
        return {**result, "status": "rejected", "reason": "invalid_signal_stop"}
    times = [b.time for b in fine]
    i = bisect_left(times, at)
    if i >= len(fine) or fine[i].time != at or fine[i].end != at+300:
        return {**result, "reason": "missing_expected_entry_open"}
    bar = fine[i]
    if bar.open <= stop:
        return {**result, "status": "cancelled", "reason": "opening_gap_through_stop", "entryPrice": bar.open}
    side_cost = r.spread_bps/20000+r.slippage_bps/10000
    buy = bar.open*(1+side_cost)
    risk_per_share = buy-stop*(1-side_cost)
    quantity = max(0, math.floor(min((r.capital-r.fee_per_order)/buy,
                                    (r.capital*r.risk_fraction-2*r.fee_per_order)/risk_per_share)))
    return {**result, "entryPrice": bar.open, "entryFill": buy, "initialRisk": buy-stop,
            "quantity": quantity, "plannedCash": quantity*buy+r.fee_per_order,
            "plannedRisk": quantity*risk_per_share+2*r.fee_per_order,
            "status": "filled" if quantity else "rejected",
            "reason": None if quantity else "insufficient_cash_or_risk_budget"}


def holding_close(entry_at, horizon):
    if type(horizon) is not int or not 1 <= horizon <= 250:
        raise DataError("Beobachtungshorizont: 1–250 Handelstage.", 400)
    day = datetime.fromtimestamp(entry_at, NY).date()
    days = sessions_between(str(day+timedelta(days=1)), str(day+timedelta(days=horizon*4+30)))
    return session_bounds(days[horizon-1])[1]


def stop_changes(source, entry, rules):
    """Only pivots formed after entry; effective after confirmation + latency."""
    side = rules.pivot_side
    previous_low = entry["initialStop"]
    stop = entry["initialStop"]
    for j in range(side, len(source)-side):
        pivot = source[j]
        if pivot.time < entry["entryAt"]:
            continue
        if not (all(pivot.low <= b.low for b in source[j-side:j]) and
                all(pivot.low < b.low for b in source[j+1:j+side+1])):
            continue
        known = source[j+side].end
        candidate = math.floor(pivot.low*(1-rules.trailing_buffer_pct/100)/rules.tick)*rules.tick
        if pivot.low > previous_low and candidate > stop:
            yield {"kind": "stop_raise", "pivotAt": pivot.time, "knownAt": known,
                   "effectiveAt": next_open_time(known+rules.latency_seconds),
                   "previousStop": stop, "newStop": candidate}
            previous_low, stop = pivot.low, candidate


def path(entry, fine, source, cutoff, horizon, model="fixed", rules=None):
    if model not in ("fixed", "higher_low"):
        raise DataError("Unbekanntes Fächer-Stopmodell.", 400)
    r = rules or ExecutionRules(**entry["rules"])
    if asdict(r) != entry["rules"]:
        raise DataError("Ausführungspfad muss die Parameter seines Einstiegs verwenden.", 400)
    result = {"version": VERSION, "model": model, "horizon": horizon,
              "entryAt": entry.get("entryAt"), "initialStop": entry.get("initialStop"),
              "status": "unavailable", "exitAt": None, "netPnl": None,
              "netReturnPct": None, "intrabarAmbiguous": False, "stopEvents": []}
    if entry["status"] != "filled":
        return {**result, "status": entry["status"], "reason": entry["reason"]}
    stop, buy, at = entry["initialStop"], entry["entryFill"], entry["entryAt"]
    target_time = holding_close(at, horizon)
    limit = min(cutoff, target_time)
    target = buy+r.target_r*entry["initialRisk"] if r.target_r else None
    result.update(plannedTimeExit=target_time, targetPrice=target)
    times = [b.time for b in fine]
    i = bisect_left(times, at)
    changes = iter(stop_changes(source, entry, r)) if model == "higher_low" else iter(())
    pending = next(changes, None)
    side_cost = r.spread_bps/20000+r.slippage_bps/10000
    last = None

    def finish(bar, raw, reason, ambiguous=False, at_open=False):
        sell = raw*(1-side_cost)
        pnl = entry["quantity"]*(sell-buy)-2*r.fee_per_order
        return {**result, "status": "closed", "reason": reason, "exitAt": bar.end,
                "fillBarAt": bar.time, "atOpen": at_open, "exitPrice": raw,
                "exitFill": sell, "finalStop": stop, "netPnl": pnl,
                "netReturnPct": pnl/(entry["quantity"]*buy+r.fee_per_order)*100, "intrabarAmbiguous": ambiguous,
                "netR": pnl/entry["plannedRisk"] if entry["plannedRisk"] else None}

    for stamp in expected_grid(at, limit):
        if i >= len(fine) or fine[i].time != stamp or fine[i].end != stamp+300:
            return {**result, "status": "censored", "reason": "missing_fine_path", "missingAt": stamp,
                    "lastObservedAt": last.end if last else at, "finalStop": stop}
        bar = fine[i]
        i += 1
        if stamp == at and bar.open != entry["entryPrice"]:
            return {**result, "status": "invalid", "reason": "entry_price_mismatch"}
        while pending and pending["effectiveAt"] is not None and pending["effectiveAt"] <= stamp:
            # Do not read the confirming candle's past low with the new stop.
            stop = max(stop, pending["newStop"])
            result["stopEvents"].append(pending)
            pending = next(changes, None)
        if bar.open <= stop:
            return finish(bar, bar.open, "stop_gap", at_open=True)
        if target and bar.open >= target:
            return finish(bar, target, "target_at_open", at_open=True)
        hit_stop, hit_target = bar.low <= stop, target is not None and bar.high >= target
        if hit_stop:
            return finish(bar, stop, "stop", ambiguous=hit_target)
        if hit_target:
            return finish(bar, target, "target")
        if bar.end == target_time:
            return finish(bar, bar.close, "time")
        last = bar
    return {**result, "status": "open" if cutoff < target_time else "censored",
            "reason": "observation_boundary" if cutoff < target_time else "missing_time_exit_bar",
            "lastObservedAt": last.end if last else at, "markPrice": last.close if last else None,
            "finalStop": stop}
