"""Frozen Retest reference/risk hypothesis and resumable offline observation.

Independent-position observations, not orders or a capital allocation service.
Historical validation is single use; feature diagnostics never select entries.
"""
from copy import deepcopy
import hashlib
from pathlib import Path
from statistics import mean, median

from datasets import digest, source_bars
from entry_watch import WatchReplay, engine_signature
from exit_research import horizon_close
from lab_metrics import expected_grid
from retest_exits import complete_history, contract_for
from retest_variants import path, RULES
from safety_strategy import StrategyContext
from strategy_research import RAW_COSTS

VERSION = "retest-observation-1"
EXITS = ("fixed", "atr_gain_stop")
# Research decision assumptions, fixed before opening the reserved time window.
ACCEPTANCE = {"minimum_pairs": 30, "minimum_symbols": 8,
              "maximum_mean_r_sacrifice": .05, "minimum_relative_drawdown_reduction": .20}
FEATURES = ("contacts", "reactionEpisodes", "contactSpanDays", "lineAgeDays",
            "projectionSensitivityATR", "signalRiskATR", "netRoomR", "safetyDistancePct")


def signature():
    root = Path(__file__).parent
    names = ("retest_observation.py", "retest_variants.py", "retest_exits.py", "datasets.py",
             "models.py", "lab_data.py", "lab_metrics.py", "lab_splits.py", "market_calendar.py",
             "exit_research.py", "strategy_portfolio.py", "strategy_research.py", "settings.py")
    return {**engine_signature(), **{n: hashlib.sha256((root/n).read_bytes()).hexdigest() for n in names}}


def record(context, entry, costs=RAW_COSTS):
    contract = contract_for(context, entry, costs)
    planned = horizon_close(entry["entryAt"], RULES["days"])
    return {"entry": deepcopy(entry), "contract": contract,
            "history": complete_history(context.sources, entry),
            "calendarFits": planned <= context.cutoff,
            # Diagnostic only: never use this future coverage for entry selection.
            "fullHorizonPath": planned <= context.cutoff and
                all(t in context.times_set for t in expected_grid(entry["entryAt"], planned)),
            "paths": {v: path(context, entry, contract, v) for v in EXITS}}


def context_for(dataset, cutoff):
    context = StrategyContext(source_bars(dataset), cutoff)
    context.times_set = set(context.times)
    return context


def assessment(records, portfolios):
    primary = [r for r in records if r["entry"]["model"] == "swing_zone" and
               r["history"]["complete"] and r["calendarFits"]]
    paired = [r for r in primary if all(r["paths"][v]["status"] == "closed" for v in EXITS)]
    symbols = len({r["entry"]["symbol"] for r in paired})
    delta = mean(r["paths"]["atr_gain_stop"]["netR"]-r["paths"]["fixed"]["netR"] for r in paired) if paired else None
    fixed, atr = [portfolios["swing_zone/"+v] for v in EXITS]
    dd = "max5mSampledDrawdownPct"
    reduction = 1-abs(atr[dd])/abs(fixed[dd]) if fixed[dd] else None
    checks = {"sample": len(paired) >= ACCEPTANCE["minimum_pairs"] and symbols >= ACCEPTANCE["minimum_symbols"],
              "complete_paths": len(paired) == len(primary),
              "mean_r_budget": delta is not None and delta >= -ACCEPTANCE["maximum_mean_r_sacrifice"],
              "drawdown": reduction is not None and reduction >= ACCEPTANCE["minimum_relative_drawdown_reduction"],
              "uninterrupted_portfolios": all(p["status"] == "marked_to_phase_end" and p["open"] == 0 for p in (fixed, atr))}
    return {"pairs": len(paired), "symbols": symbols, "meanDeltaR": delta,
            "relativeDrawdownReduction": reduction, "checks": checks,
            "decision": "risk_hypothesis_passed_descriptive_gate" if all(checks.values()) else "not_established_keep_fixed_reference",
            "meaning": "A predeclared research gate, not a significance test, strategy validation or deployment approval."}


def feature_values(entry):
    result = {k: entry.get("features", {}).get(k) for k in FEATURES}
    for key in ("signalRiskATR", "netRoomR"):
        result[key] = entry.get(key)
    price = entry["entryPrice"]
    result["safetyDistancePct"] = 100*(price-entry["initialStop"])/price if price > 0 else None
    result["daily"] = entry.get("context", {}).get("daily", "unknown")
    result["weekly"] = entry.get("context", {}).get("weekly", "unknown")
    return result


def diagnose(records):
    """Descriptive development-only comparison; no learned cutoffs/rank selection."""
    selected = [r for r in records if r["entry"]["model"] == "swing_zone" and
                r["history"]["complete"] and r["calendarFits"] and r["paths"]["fixed"]["status"] == "closed"]
    groups = {}
    for label, rows in (("all", selected), ("positive", [r for r in selected if r["paths"]["fixed"]["netR"] > 0]),
                        ("nonpositive", [r for r in selected if r["paths"]["fixed"]["netR"] <= 0])):
        values = [feature_values(r["entry"]) for r in rows]
        groups[label] = {"cases": len(rows), "symbols": len({r["entry"]["symbol"] for r in rows}),
            "numeric": {k: {"available": len(present := [v[k] for v in values if v[k] is not None]),
                            "missing": len(values)-len(present), "median": median(present) if present else None}
                        for k in FEATURES},
            "context": {k: {v: sum(f[k] == v for f in values) for v in sorted({f[k] for f in values})}
                        for k in ("daily", "weekly")}}
    return {"features": list(FEATURES), "groups": groups,
            "meaning": "Exploratory development labels only; overlapping trades, confounding and small groups. No new entry threshold or fitted prediction."}


def observe(dataset, start_at, from_at, asof, previous=None, seed=None):
    """Append observations on immutable known prefixes; updates can use a new dataset ID.

    Recomputing short paths from the original entry makes checkpoint recovery
    simple. Old closed paths must stay identical. A data gap stays unresolved;
    revisions need a new generation, never a silent repair of the old history.
    """
    if from_at > asof or start_at > from_at:
        raise ValueError("Invalid observation range")
    config = {"version": VERSION, "engine": signature(), "startAt": start_at,
              "fromAt": from_at, "model": "swing_zone", "costs": RAW_COSTS, "exitRules": RULES}
    context = context_for(dataset, asof)
    prefix = lambda cutoff: digest({tf: [b.__dict__ for b in bars if b.end <= cutoff]
                                   for tf, bars in context.sources.items()})
    replay = WatchReplay(dataset, "swing_zone", start_at, asof)
    if previous:
        if previous["config"] != config or asof < previous["asOf"] or prefix(previous["asOf"]) != previous["prefixHash"]:
            raise ValueError("Changed observation code/config/known data or time reversal; use a new generation")
        replay.restore(previous["watch"])
    elif seed:
        if seed["asOf"] > from_at:
            raise ValueError("Seed contains observations after start")
        replay.restore(seed)
    replay.run()
    records = [record(context, e) for e in replay.entries if e["family"] == "retest" and from_at <= e["entryAt"] <= asof]
    old = {r["entry"]["id"]: r for r in previous["records"]} if previous else {}
    current = {r["entry"]["id"]: r for r in records}
    for identity, prior in old.items():
        if identity not in current or current[identity]["entry"] != prior["entry"]:
            raise ValueError("Previously frozen entry changed")
        for variant in EXITS:
            p = prior["paths"][variant]
            new = current[identity]["paths"][variant]
            if p["status"] == "closed" and p != new:
                raise ValueError("Previously closed observation changed")
            if new["events"][:len(p["events"])] != p["events"]:
                raise ValueError("Previously known exit decision changed")
    journal = deepcopy(previous["journal"]) if previous else []
    keys = {v["eventKey"] for v in journal}
    new_events = []

    def emit(identity, variant, kind, known, detail):
        event = {"eventKey": digest([VERSION, dataset["material"]["symbol"], identity, variant, kind, known, detail]),
                 "entryId": identity, "variant": variant, "kind": kind, "knownAt": known, "detail": detail}
        if event["eventKey"] not in keys:
            keys.add(event["eventKey"])
            journal.append(event)
            new_events.append(event)

    for r in records:
        e = r["entry"]
        emit(e["id"], "both", "entry", e["entryAt"]+300,
             {"entryAt": e["entryAt"], "price": e["entryPrice"], "stop": e["initialStop"], "completeHistory": r["history"]["complete"]})
        for variant in EXITS:
            p = r["paths"][variant]
            for event in p["events"]:
                emit(e["id"], variant, event["kind"], event["knownAt"], event)
            if p["status"] == "closed":
                emit(e["id"], variant, "closed", p["exitAt"], {k: p[k] for k in ("exitAt", "exitFill", "exitReason", "netR", "netReturnPct")})
            elif p.get("reason") != "phase_boundary":
                emit(e["id"], variant, "unresolved", p.get("missingAt", e["entryAt"])+300,
                     {"reason": p.get("reason"), "status": p["status"]})
    state = {"config": config, "asOf": asof, "prefixHash": prefix(asof), "datasetId": dataset["id"],
             "watch": replay.state(), "records": records, "journal": journal}
    return state, sorted(new_events, key=lambda e: (e["knownAt"], e["eventKey"]))
