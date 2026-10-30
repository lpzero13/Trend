"""Offline fan research: random origins -> causal scenarios -> separate outcomes.

Only one immutable dataset is held at a time by the queue adapter. First-signal
selection never depends on a future gain, a stop outcome or path completeness.
"""
from bisect import bisect_left
from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import random
from types import SimpleNamespace

from datasets import data_kind, source_bars
from fan_execution import ExecutionRules, entry_contract, path
from fan_geometry import FanRules, profile, stable_id
from fan_observer import FanObserver, WatchRules
from lab_data import require_convention, session_bounds
from lab_metrics import evaluate
from lab_splits import sessions_between
from models import DataError, NY
from weekly_chart import weeks, week_sessions

VERSION = "tori-fan-study-1"
COHORTS = ("two", "three_young", "qualified")
VARIANTS = ("breakout", "retest")
DEFAULTS = {"timeframe": "4h", "geometry_variants": ["extreme"], "sampling": "origins",
            "warmup_bars": 200, "origin_start": None, "origin_end": None,
            "cutoff": None, "models": ["fixed", "higher_low"]}


def timestamp(value, *, upper=False):
    if value is None:
        return None
    try:
        if len(value) == 10:
            d = datetime.fromisoformat(value).replace(tzinfo=NY)
            if upper:
                d += timedelta(days=1)
                return int(d.timestamp())-1
        else:
            d = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if d.tzinfo is None:
                raise ValueError()
        return int(d.timestamp())
    except (ValueError, TypeError, AttributeError, OverflowError):
        raise DataError("Fächer-Datum: YYYY-MM-DD oder ISO-Zeitpunkt mit Zeitzone.", 400) from None


def validate(value):
    if not isinstance(value, dict) or set(value)-set(DEFAULTS)-{"geometry", "watch", "execution"}:
        raise DataError("Unbekannte Fächerparameter.", 400)
    result = deepcopy({**DEFAULTS, **value})
    if result["timeframe"] not in ("1h", "4h", "1D", "1W"):
        raise DataError("Fächer-Intervall: 1h, 4h, 1D oder 1W.", 400)
    if result["sampling"] not in ("origins", "full"):
        raise DataError("Fächer-Auswahl: origins oder full.", 400)
    for name, allowed in (("geometry_variants", ("extreme", "local", "master")), ("models", ("fixed", "higher_low"))):
        if not isinstance(result[name], list) or not result[name] or len(result[name]) > len(allowed) or any(v not in allowed for v in result[name]):
            raise DataError(f"Ungültige Varianten: {name}.", 400)
        result[name] = list(dict.fromkeys(result[name]))
    if type(result["warmup_bars"]) is not int or not 20 <= result["warmup_bars"] <= 10000:
        raise DataError("Fächer-Vorlauf: 20–10000 Quellkerzen.", 400)
    for name in ("origin_start", "origin_end", "cutoff"):
        timestamp(result[name], upper=name != "origin_start")
    if result["origin_start"] and result["origin_end"] and timestamp(result["origin_start"]) > timestamp(result["origin_end"], upper=True):
        raise DataError("Startauswahl hat umgekehrte Datumsgrenzen.", 400)
    try:
        for name, cls in (("geometry", FanRules), ("watch", WatchRules), ("execution", ExecutionRules)):
            if not isinstance(result.get(name, {}), dict):
                raise TypeError()
            result[name] = asdict(cls(**result.get(name, {})))
    except TypeError:
        raise DataError("Unbekannte Geometrie-, Beobachtungs- oder Ausführungsparameter.", 400) from None
    return result


def schedule(first, cutoff, timeframe):
    """Expected regular source candles, including holidays and short sessions."""
    first_day, last_day = [datetime.fromtimestamp(t, NY).date() for t in (first, cutoff)]
    if timeframe == "1W":
        monday = first_day-timedelta(days=first_day.weekday())
        while monday <= last_day:
            sessions = week_sessions(str(monday))
            if sessions and first <= sessions[0][1] and sessions[-1][2] <= cutoff:
                yield sessions[0][1], sessions[-1][2]
            monday += timedelta(days=7)
    else:
        step = {"1h": 3600, "4h": 14400, "1D": 86400}[timeframe]
        for day in sessions_between(str(first_day), str(last_day)):
            opened, closed = session_bounds(day)
            for start in range(opened, closed, step):
                end = min(start+step, closed)
                if first <= start and end <= cutoff:
                    yield start, end


def source_gaps(rows, cutoff, timeframe):
    expected = list(schedule(rows[0].time, cutoff, timeframe))
    positions = {pair: i for i, pair in enumerate(expected)}
    gaps = {}
    previous = None
    for i, bar in enumerate(rows):
        p = positions.get((bar.time, bar.end))
        if p is None:
            raise DataError("Quellkerze liegt nicht auf dem erwarteten regulären Raster.", 422)
        if previous is not None and p != previous+1:
            gaps[i] = expected[previous+1][1]
        previous = p
    return gaps


def temporal_plan(dataset, spec):
    config = spec["fan"]
    frames = source_bars(dataset)
    tf = config["timeframe"]
    final = max(b.end for b in frames["5m"])
    if tf == "1W":
        frames[tf] = weeks(frames["1D"], final)
    rows = frames[tf]
    if len(rows) <= config["warmup_bars"]+1:
        raise DataError("Zu wenig Quellhistorie für Fächer-Vorlauf und Suche.", 422)
    # The existing research holdout remains outside both signal and outcome code.
    boundary = int(len(rows)*(1-spec["holdout_fraction"]))-1
    cutoff = rows[boundary].end
    requested = timestamp(config["cutoff"], upper=True)
    if requested is not None:
        cutoff = min(cutoff, requested)
    known = [i for i, b in enumerate(rows) if i >= config["warmup_bars"] and b.end <= cutoff]
    start, end = timestamp(config["origin_start"]), timestamp(config["origin_end"], upper=True)
    eligible = [i for i in known if (start is None or rows[i].end >= start) and (end is None or rows[i].end <= end)]
    if not eligible:
        raise DataError("Keine Startpunkte vor dem reservierten Holdout und innerhalb der gewählten Grenzen.", 422)
    rng = random.Random(f"{spec['seed']}|{dataset['id']}|{tf}|{VERSION}")
    origins = sorted(rng.sample(eligible, min(spec["samples"], len(eligible)))) if config["sampling"] == "origins" else []
    return frames, {"cutoff": cutoff, "holdoutFrom": rows[boundary+1].time,
                    "timeframe": tf, "firstAnalysisAt": rows[known[0]].end,
                    "origins": origins, "eligibleStarts": len(eligible),
                    "sampledWithoutSignalOrOutcomeFilter": True}


def run_dataset(dataset, spec, *, emit=lambda item: None, interrupted=lambda: False, progress=lambda **kw: None):
    require_convention(dataset)
    config = spec["fan"]
    frames, plan = temporal_plan(dataset, spec)
    cutoff, tf = plan["cutoff"], config["timeframe"]
    frames = {k: [b for b in rows if b.end <= cutoff] for k, rows in frames.items()}
    rows = frames[tf]
    gaps = source_gaps(rows, cutoff, tf)
    origin_set = set(plan["origins"])
    execution = ExecutionRules(**config["execution"])
    symbol, dataset_id = dataset["material"]["symbol"], dataset["id"]
    # Post-signal evaluator receives the same cutoff, never the holdout tail.
    prepared = SimpleNamespace(sources=frames, fine_times=[b.time for b in frames["5m"]],
                               fine_ends=[b.end for b in frames["5m"]])
    counts = Counter()
    for roots in config["geometry_variants"]:
        rules = profile(roots, config["geometry"])
        observer = FanObserver(symbol, tf, rules, WatchRules(**config["watch"]))
        cases, origins = [], []
        for i, bar in enumerate(rows):
            if i % 50 == 0:
                if interrupted():
                    return None
                progress(symbol=symbol, geometry=roots, completed=i, total=len(rows), unit="candles")
            events = observer.gap(bar) if i in gaps else []
            events += observer.push(bar)
            grouped_signals = defaultdict(list)
            for event in events:
                event.update(datasetId=dataset_id, geometry=roots)
                emit({"event": event})
                counts[event["kind"]] += 1
                if event["kind"] != "entry_signal" or event["signalAt"] < plan["firstAnalysisAt"] or not event["validRisk"]:
                    continue
                grouped_signals[event["variant"], event["cohort"]].append(event)
            # Multiple rays can explain the SAME close. Choose before reading
            # execution/outcomes; keep all alternatives in the journal.
            for alternatives in grouped_signals.values():
                event = min(alternatives, key=lambda e: (-e["line"]["contacts"], -e["line"]["reactionContacts"], e["candidateAt"], e["id"]))
                contract = entry_contract(event, frames["5m"], cutoff, execution)
                case = {"id": stable_id([VERSION, dataset_id, event["id"]]), "kind": "entry",
                        "symbol": symbol, "datasetId": dataset_id, "dataKind": data_kind(dataset),
                        "timeframe": tf, "geometry": roots, "variant": event["variant"], "cohort": event["cohort"],
                        "startAt": event["signalAt"], "signal": event, "entry": contract, "paths": {},
                        "cutoff": cutoff, "holdoutFrom": plan["holdoutFrom"], "observations": {},
                        "alternativeSignalIds": sorted(e["id"] for e in alternatives if e["id"] != event["id"]),
                        "feed": dataset["material"]["feed"], "adjustment": dataset["material"]["adjustment"]}
                if contract["status"] == "filled":
                    outcome_entry = {**contract, "entryPrice": contract["entryPrice"]}
                    case["observations"] = evaluate(dataset, outcome_entry, spec["horizons"], cutoff, prepared=prepared)
                    for horizon in spec["horizons"]:
                        for model in config["models"]:
                            if interrupted():
                                return None
                            case["paths"][f"{model}:{horizon}"] = path(contract, frames["5m"], rows, cutoff, horizon, model, execution)
                cases.append(case)
                emit({"trial": case})
            if i in origin_set:
                snap = observer.last_snapshot
                origin = {"id": stable_id([VERSION, dataset_id, tf, roots, bar.end, spec["seed"]]),
                          "kind": "origin", "symbol": symbol, "datasetId": dataset_id,
                          "dataKind": data_kind(dataset), "feed": dataset["material"]["feed"],
                          "adjustment": dataset["material"]["adjustment"],
                          "geometry": roots, "timeframe": tf, "startAt": bar.end,
                          "cutoff": cutoff, "sourceIndex": i,
                          "atStart": {"snapshot": deepcopy(snap), "trackedScenarios": len(observer.active)},
                          "selections": []}
                origins.append(origin)
        for origin in origins:
            first_gap = min((t for t in gaps.values() if t > origin["startAt"]), default=None)
            for variant in VARIANTS:
                for group in COHORTS:
                    match = next((c for c in cases if c["variant"] == variant and c["cohort"] == group and c["startAt"] >= origin["startAt"]), None)
                    if first_gap is not None and (match is None or first_gap < match["startAt"]):
                        selection = {"variant": variant, "cohort": group, "status": "unknown_source_gap", "missingAt": first_gap, "entryId": None}
                    else:
                        selection = {"variant": variant, "cohort": group,
                                     "status": match["entry"]["status"] if match else "no_signal_before_boundary",
                                     "entryId": match["id"] if match else None}
                    origin["selections"].append(selection)
            emit({"trial": origin})
    return {**plan, "eventCounts": dict(counts), "sourceGaps": len(gaps),
            "status": "completed", "dataKind": data_kind(dataset)}


def summarize(records):
    # Stream immutable rows; do not retain large origin snapshots or OHLC paths.
    groups = {}
    seen, origin_count = set(), 0

    def group(record, variant, cohort):
        key = tuple(record.get(k, "unknown") for k in ("geometry", "dataKind", "feed", "adjustment")) + (variant, cohort)
        return groups.setdefault(key, {"entries": Counter(), "origins": Counter(), "selected": set(), "paths": {}})

    for record in records:
        if record["id"] in seen:
            continue
        seen.add(record["id"])
        if record["kind"] == "origin":
            origin_count += 1
            for variant in VARIANTS:
                for cohort in COHORTS:
                    group(record, variant, cohort)
            for selection in record["selections"]:
                g = group(record, selection["variant"], selection["cohort"])
                g["origins"][selection["status"]] += 1
                if selection["entryId"]:
                    g["selected"].add(selection["entryId"])
        elif record["kind"] == "entry":
            g = group(record, record["variant"], record["cohort"])
            g["entries"][record["entry"]["status"]] += 1
            for name, model in record["paths"].items():
                p = g["paths"].setdefault(name, {"states": Counter(), "sum": 0., "closed": 0, "ambiguous": 0})
                p["states"][model["status"]] += 1
                p["ambiguous"] += model["intrabarAmbiguous"]
                if model["status"] == "closed":
                    p["sum"] += model["netReturnPct"]
                    p["closed"] += 1
    result = []
    for (geometry, data_kind_name, feed, adjustment, variant, cohort_name), g in sorted(groups.items()):
        result.append({"geometry": geometry, "dataKind": data_kind_name, "feed": feed, "adjustment": adjustment,
                       "variant": variant, "cohort": cohort_name,
                       "uniqueSignals": sum(g["entries"].values()), "entryStates": dict(g["entries"]),
                       "origins": sum(g["origins"].values()), "originStates": dict(g["origins"]),
                       "selectedUniqueSignals": len(g["selected"]),
                       "paths": {name: {"states": dict(p["states"]),
                                          "closedOnlyMeanReturnPct": p["sum"]/p["closed"] if p["closed"] else None,
                                          "ambiguous": p["ambiguous"]} for name, p in g["paths"].items()}})
    return {"version": VERSION, "originCount": origin_count, "uniqueSignals": sum(g["uniqueSignals"] for g in result),
            "dataKinds": sorted({g["dataKind"] for g in result}),
            "groups": result, "interpretation": "Einzelne Modellfälle, kein Portfolio. Ursprünge können denselben Entry treffen; Varianten und Pfade überlappen. Unvollständige Pfade separat; Mittelwerte nur geschlossener Pfade können verzerrt sein. Keine Profitabilitätsfreigabe."}
