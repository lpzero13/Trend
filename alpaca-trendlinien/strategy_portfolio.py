"""Chronological cash/risk ledger for versioned strategy paths; no orders."""
from bisect import bisect_right
from collections import defaultdict
import math

from lab_metrics import expected_grid

DEFAULTS = {"capital": 2000., "risk_fraction": .01, "allocation_fraction": .25,
            "max_positions": 5, "fractional": True}


def validate(value=None):
    if value is not None and (not isinstance(value, dict) or set(value)-set(DEFAULTS)):
        raise ValueError("Unknown portfolio assumptions")
    result = {**DEFAULTS, **(value or {})}
    for name, lo, hi in (("capital", 1, 1e9), ("risk_fraction", .0001, .25), ("allocation_fraction", .001, 1)):
        if type(result[name]) not in (int, float) or not math.isfinite(result[name]) or not lo <= result[name] <= hi:
            raise ValueError("Invalid portfolio assumption: "+name)
    if type(result["max_positions"]) is not int or not 1 <= result["max_positions"] <= 100 or type(result["fractional"]) is not bool:
        raise ValueError("Invalid portfolio position count or unit convention")
    return result


def simulate(entries, paths, contexts, phase, costs, options=None):
    options = validate(options)
    by_id = {e["id"]: e for e in entries}
    ordered = sorted(paths, key=lambda p: (p["entryAt"], by_id[p["entryId"]]["symbol"], p["entryId"]))
    by_time = defaultdict(list)
    for p in ordered:
        by_time[p["entryAt"]].append(p)
    stamps = set(t+300 for t in expected_grid(phase["startAt"], phase["endAt"])) if ordered else set()
    stamps.update(by_time)
    stamps.add(phase["endAt"])
    fine_ends = {key: [b.end for b in context.fine] for key, context in contexts.items()}
    cash, fee = options["capital"], costs["fee_per_order"]
    side_cost = costs["spread_bps"]/20000+costs["slippage_bps"]/10000
    active, trades, skipped, equity = [], [], [], []
    peak, worst, halt = cash, 0., None

    def mark(at):
        total = cash
        for position in active:
            e, p = position["entry"], position["path"]
            key = e["datasetId"]
            i = bisect_right(fine_ends[key], at)-1
            bar = contexts[key].fine[i] if i >= 0 else None
            price = bar.close if bar and bar.end > p["entryAt"] else e["entryPrice"]
            total += position["quantity"]*price
        return total

    def release(at):
        nonlocal cash
        for position in list(active):
            path = position["path"]
            if path["status"] == "closed" and path["exitAt"] <= at:
                cash += position["quantity"]*path["exitFill"]-fee
                position["netPnl"] = position["quantity"]*(path["exitFill"]-path["entryFill"])-2*fee
                position["exitAt"] = path["exitAt"]
                active.remove(position)

    last_at = phase["startAt"]
    for at in sorted(stamps):
        release(at)
        missing = [p for p in active if p["path"].get("missingAt", math.inf) <= at]
        if missing:
            halt = {"reason": "held_position_missing_market_path", "at": min(p["path"]["missingAt"] for p in missing),
                    "symbols": sorted({p["entry"]["symbol"] for p in missing})}
            last_at = halt["at"]
            value = mark(last_at)
            peak = max(peak, value)
            worst = min(worst, (value/peak-1)*100)
            equity.append({"at": last_at, "value": value, "cash": cash, "positions": len(active)})
            break
        for path in by_time.get(at, []):
            e = by_id[path["entryId"]]
            reason = None
            if path["status"] in ("unavailable", "invalid"):
                reason = path.get("reason", "entry_unavailable")
            elif any(p["entry"]["symbol"] == e["symbol"] for p in active):
                reason = "already_holding_symbol"
            elif len(active) >= options["max_positions"]:
                reason = "max_positions"
            if reason:
                skipped.append({"entryId": e["id"], "at": at, "symbol": e["symbol"], "reason": reason})
                continue
            value = mark(at)
            unit_risk = path["entryFill"]-path["initialStop"]*(1-side_cost)
            qty = min(max(0, cash-fee)/path["entryFill"], value*options["allocation_fraction"]/path["entryFill"],
                      max(0, value*options["risk_fraction"]-2*fee)/unit_risk)
            qty = math.floor(qty*1e6)/1e6 if options["fractional"] else math.floor(qty)
            if qty <= 0:
                skipped.append({"entryId": e["id"], "at": at, "symbol": e["symbol"], "reason": "no_affordable_units"})
                continue
            cash -= qty*path["entryFill"]+fee
            position = {"entry": e, "path": path, "quantity": qty, "openedAt": at,
                        "cashAfterEntry": cash, "equityAtEntry": value,
                        "plannedRiskUSD": qty*unit_risk+2*fee, "plannedUnitRisk": unit_risk, "netPnl": None}
            trades.append(position)
            active.append(position)
        value = mark(at)
        peak = max(peak, value)
        drawdown = (value/peak-1)*100
        new_low = drawdown < worst
        worst = min(worst, drawdown)
        if at in by_time or new_low or at == phase["endAt"] or any(p.get("exitAt") == at for p in trades):
            equity.append({"at": at, "value": value, "cash": cash, "positions": len(active)})
        last_at = at
    final = mark(last_at)
    compact = [{"entryId": p["entry"]["id"], "symbol": p["entry"]["symbol"],
                "openedAt": p["openedAt"], "entryFill": p["path"]["entryFill"],
                "initialStop": p["path"]["initialStop"], "initialRisk": p["path"]["initialRisk"],
                "quantity": p["quantity"], "plannedRiskUSD": p["plannedRiskUSD"],
                "plannedUnitRisk": p["plannedUnitRisk"],
                "cashAfterEntry": p["cashAfterEntry"], "equityAtEntry": p["equityAtEntry"],
                "exitAt": p.get("exitAt"), "exitFill": p["path"]["exitFill"] if p.get("exitAt") else None,
                "netPnl": p["netPnl"], "exitReason": p["path"].get("exitReason") if p.get("exitAt") else None}
               for p in trades]
    return {"options": options, "status": "incomplete" if halt else "marked_to_phase_end",
            "observedThrough": last_at, "halt": halt, "initialCapital": options["capital"],
            "markedEquity": final, "cash": cash, "marketValue": final-cash,
            "markedReturnPct": (final/options["capital"]-1)*100 if not halt else None,
            "prefixReturnPct": (final/options["capital"]-1)*100,
            "realizedNetPnl": sum(p["netPnl"] for p in trades if p["netPnl"] is not None),
            "accepted": len(trades), "closed": sum(p["netPnl"] is not None for p in trades),
            "open": len(active), "max5mSampledDrawdownPct": worst,
            "trades": compact, "skipped": skipped, "equity": equity,
            "meaning": "USD cash-constrained fractional paper portfolio. Complete closed 5m marks; missing held paths halt all further decisions. Capital released at fine-bar end. Phase-end open positions marked, not realized profit."}
