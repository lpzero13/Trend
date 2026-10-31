"""Offline signal episodes, independent nominal cases and rule-only exits.

This is deliberately separate from capital-constrained portfolio studies.
The plan and engine are immutable; a code change requires a new output folder.
"""
from bisect import bisect_right
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import platform
import statistics
import time
from unittest.mock import patch

from datasets import data_kind, path_for, read_dataset, source_bars
from fan_geometry import stable_id
from fan_study import source_gaps, timestamp
from lab_data import require_convention
from models import DataError
from pilot_backtest import PilotObserver, code_digest
from setup_episodes import Episodes
from signal_path_index import CaseExecution, MODELS, PathIndex, execute_unbounded, isolated_entry
from strategy_screen import read, write

VERSION = "tori-event-case-study-1"


def binding():
    base = code_digest()["files"]
    names = ("event_case_study.py", "setup_episodes.py", "signal_path_index.py", "datasets.py",
             "strategy_screen.py", "strategy_run_lock.py", "tools/run_event_cases.py")
    return {**base, **{n: hashlib.sha256((Path(__file__).parent/n).read_bytes()).hexdigest() for n in names}}


def checked(plan):
    if plan["id"] != stable_id({k: v for k, v in plan.items() if k != "id"}):
        raise DataError("Studienplan wurde verändert.", 409)
    if plan["engine"] != binding():
        raise DataError("Engine verändert: neuer Studienordner erforderlich.", 409)
    return plan


def prepare(root, source, symbols=None, windows=None):
    root = Path(root)
    if (root/"plan.json").exists():
        old = checked(read(root/"plan.json"))
        if (symbols and sorted(symbols) != old["symbols"]) or (windows and sorted(windows) != sorted(f["name"] for f in old["windows"])):
            raise DataError("Keine Änderung der Auswahl beim Wiederaufnehmen.", 409)
        return old
    prior = read(source)
    if prior["id"] != stable_id({k: v for k, v in prior.items() if k != "id"}):
        raise DataError("Quellmanifest verändert.", 409)
    selected = sorted(symbols or prior["symbols"])
    if set(selected)-set(prior["datasets"]):
        raise DataError("Aktie nicht im lokalen Referenzuniversum.", 400)
    folds = [{k: f[k] for k in ("name", "start", "end")} for f in prior["folds"]["validation"]
             if windows is None or f["name"] in windows]
    if not folds or (windows and set(windows)-{f["name"] for f in folds}):
        raise DataError("Unbekanntes Entryfenster.", 400)
    # Use declared import boundary, never shorten each case to its last present
    # bar: missing trailing bars must remain detectable as missing data.
    ends = {read(path_for(prior["datasets"][s]))["sources"]["5m"]["requestedEnd"] for s in selected}
    if len(ends) != 1:
        raise DataError("Unterschiedliche Importgrenzen: expliziten gemeinsamen Bestand herstellen.", 422)
    requested = datetime.fromisoformat(next(iter(ends)).replace("Z", "+00:00"))
    cutoff = int(requested.timestamp())//300*300
    plan = {"version": VERSION, "createdAt": datetime.now(timezone.utc).isoformat(),
            "sourcePlanId": prior["id"], "symbols": selected,
            "datasets": {s: prior["datasets"][s] for s in selected}, "windows": folds,
            "outcomeCutoff": cutoff, "warmupDays": 400, "execution": asdict(CaseExecution()),
            "models": list(MODELS), "engine": binding(), "python": platform.python_version(),
            "sampling": "All causal entries in named windows; warmup and intervening history also pass episode registry",
            "episodeRule": "One family per fan-origin episode; child anchors inherit ancestry; two confirmed post-trigger contacts rearm; red retest retains breakout scenario episode",
            "exits": "Hard stop only; fixed / original rising Safety / current rising Safety. Ratchet up, 0.3% buffer, 300s activation latency. No time exit, take profit or shared budget.",
            "limitations": ["Known historical/current-survivor universe, not independent holdout",
                            "Episode construction is an experimental causal definition, not proven manual equivalence",
                            "Dependent cases, split-adjusted SIP prices, no dividends/FX",
                            "Open and gap-censored cases are not closed trades; closed-only estimates may be selected",
                            "Fractional equal notional cases, no executable portfolio return or capital curve"]}
    plan["id"] = stable_id(plan)
    for name in plan["engine"]:
        dest = root/"engine"/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((Path(__file__).parent/name).read_bytes())
    write(root/"plan.json", plan)
    return plan


def load_block(root, plan, symbol):
    block = read(Path(root)/"stocks"/(symbol+".json.gz"))
    if block["planId"] != plan["id"] or block["checksum"] != stable_id({k: v for k, v in block.items() if k != "checksum"}):
        raise DataError("Ergebnisblock verändert.", 409)
    return block


def scan_episodes(symbol, rows, start, end):
    observer, registry = PilotObserver(symbol), Episodes(symbol)
    gaps = source_gaps(rows, rows[-1].end, "4h")
    signals, suppressed, timeline, journal = [], [], [], []
    raw = Counter()
    for i, bar in enumerate(rows):
        events = observer.gap(bar) if i in gaps else []
        emitted, found, snap = observer.push(bar)
        events += emitted
        registry.observe(snap)
        accepted, skipped = registry.accept(found)
        if snap and snap.get("ready"):
            timeline.append({"closedAt": bar.end, "index": snap["referenceIndex"], "close": bar.close,
                             "atr": snap["atr"], "green": deepcopy(snap["green"]), "gapAt": gaps.get(i)})
        elif i in gaps:
            timeline.append({"closedAt": bar.end, "index": observer.red.engine.index, "close": bar.close,
                             "atr": snap.get("atr"), "green": None, "gapAt": gaps[i]})
        if start <= bar.end <= end:
            signals.extend(accepted)
            suppressed.extend(skipped)
            raw.update(s["family"] for s in found)
            journal.extend({k: e[k] for k in ("id", "kind", "knownAt", "scenarioId", "reason") if k in e}
                           for e in events)
    used = {s["episodeId"] for s in signals}
    return signals, timeline, suppressed, {"rawSignals": dict(raw), "sourceGaps": len(gaps),
        "episodes": [v for k, v in registry.records.items() if k in used], "journal": journal}


def _work(task):
    root, plan, symbol = task
    checked(plan)
    path = Path(root)/"stocks"/(symbol+".json.gz")
    if path.exists():
        block = load_block(root, plan, symbol)
        return {"symbol": symbol, "cached": True, "cases": len(block["cases"])}
    started = time.perf_counter()
    with patch("alpaca._request", side_effect=AssertionError("Event study stays offline")):
        dataset = read_dataset(plan["datasets"][symbol])
        require_convention(dataset)
        material = dataset["material"]
        if data_kind(dataset) != "market" or material["symbol"] != symbol or material["feed"] != "sip" or material["adjustment"] != "split":
            raise DataError("Unpassendes Referenzdataset.", 422)
        frames = source_bars(dataset)
        cutoff = plan["outcomeCutoff"]
        first = min(timestamp(f["start"]) for f in plan["windows"])
        last = max(timestamp(f["end"], upper=True) for f in plan["windows"])
        warm = first-plan["warmupDays"]*86400
        rows = [b for b in frames["4h"] if b.time >= warm and b.end <= cutoff]
        fine = [b for b in frames["5m"] if b.time >= warm and b.end <= cutoff]
        if not rows or not fine:
            raise DataError("Keine lokale Historie im Zeitraum.", 422)
        eligibility = {f["name"]: rows[0].end <= timestamp(f["start"])-320*86400 for f in plan["windows"]}
        signals, timeline, suppressed, diagnostics = scan_episodes(symbol, rows, first, last)
        index = PathIndex(fine, cutoff, start=max(warm, fine[0].time))
        daily = frames["1D"]
        daily_ends = [b.end for b in daily]
        def fold_at(at):
            return next((f["name"] for f in plan["windows"] if timestamp(f["start"]) <= at <= timestamp(f["end"], upper=True)), None)
        cases = []
        excluded = Counter()
        for signal in signals:
            fold = fold_at(signal["signalAt"])
            if not fold:
                continue
            if not eligibility[fold]:
                excluded[fold] += 1
                continue
            entry = isolated_entry(signal, index, CaseExecution(**plan["execution"]))
            known = bisect_right(daily_ends, signal["signalAt"])
            context = asdict(daily[known-1]) if known else None
            vol = signal["features"]["atr"]
            features = {"signalATR4h": vol, "dailyLastClosed": context, "dailyFilterApplied": False,
                        "entryKnownGeometry": {"line": deepcopy(signal["line"]), "safety": deepcopy(signal.get("safety"))},
                        "cohort": signal["cohort"], "family": signal["family"], "subtype": signal["subtype"]}
            if entry["status"] == "filled":
                distance = entry["entryFill"]-entry["initialStop"]
                features.update(stopDistanceUSD=distance, stopDistancePct=100*distance/entry["entryFill"],
                                stopDistanceATR4h=distance/vol if vol else None,
                                safetyDistanceUSD=entry["entryFill"]-signal["safety"]["value"])
            case = {"id": stable_id([VERSION, dataset["id"], signal["episodeId"], signal["family"], signal["id"]]),
                    "symbol": symbol, "window": fold, "datasetId": dataset["id"], "signal": signal,
                    "entry": entry, "features": features,
                    "paths": {m: execute_unbounded(signal, entry, index, timeline, m) for m in plan["models"]}}
            cases.append(case)
        relevant_skips = [s for s in suppressed if fold_at(s["signalAt"]) and eligibility[fold_at(s["signalAt"])]]
        # Store the exact causal stop-source timeline, enabling independent
        # replay without rediscovering geometry using future candles.
        block = {"planId": plan["id"], "symbol": symbol, "datasetId": dataset["id"], "cases": cases,
                 "eligibility": eligibility, "excludedWarmupSignals": dict(excluded), "suppressed": relevant_skips,
                 "diagnostics": diagnostics, "timeline": timeline,
                 "dataBounds": {tf: {"count": len(bs), "first": bs[0].time, "lastClose": bs[-1].end}
                                for tf, bs in frames.items() if bs}, "elapsedSeconds": time.perf_counter()-started}
        block["checksum"] = stable_id(block)
        write(path, block)
    return {"symbol": symbol, "cases": len(cases), "suppressed": len(relevant_skips),
            "seconds": round(block["elapsedSeconds"], 2)}


def build(root, plan, workers=2, progress=print):
    checked(plan)
    if type(workers) is not int or not 1 <= workers <= 4:
        raise ValueError("Use 1–4 technical workers, unrelated to case slots")
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for done in as_completed([pool.submit(_work, (str(root), plan, s)) for s in plan["symbols"]]):
            progress(done.result())


def statistics_for(cases, model):
    paths = [c["paths"][model] for c in cases]
    closed = [p for p in paths if p["status"] == "closed"]
    vals = [p["netR"] for p in closed]
    pct = [p["netReturnPct"] for p in closed]
    winners = sorted((p["netPnl"] for p in closed if p["netPnl"] > 0), reverse=True)
    positive = sum(winners)
    return {"signals": len(cases), "episodes": len({c["signal"]["episodeId"] for c in cases}),
            "entryStatuses": dict(Counter(c["entry"]["status"] for c in cases)),
            "statuses": dict(Counter(p["status"] for p in paths)), "closed": len(closed),
            "wins": sum(p["netPnl"] > 0 for p in closed), "losses": sum(p["netPnl"] < 0 for p in closed),
            "winPctClosed": 100*sum(v > 0 for v in vals)/len(vals) if vals else None,
            "meanNetR": statistics.mean(vals) if vals else None, "medianNetR": statistics.median(vals) if vals else None,
            "meanNetReturnPct": statistics.mean(pct) if pct else None,
            "medianNetReturnPct": statistics.median(pct) if pct else None,
            "worstNetR": min(vals) if vals else None,
            "medianHoldingCalendarDays": statistics.median(p["holdingCalendarDays"] for p in closed) if closed else None,
            "top3SharePositiveNominalPnlPct": 100*sum(winners[:3])/positive if positive else None,
            "exitReasons": dict(Counter(p["reason"] for p in closed))}


def evaluate(root, plan):
    checked(plan)
    cases, blocks = [], []
    for symbol in plan["symbols"]:
        block = load_block(root, plan, symbol)
        blocks.append(block)
        cases.extend(block["cases"])
    if len({c["id"] for c in cases}) != len(cases):
        raise AssertionError("Duplicate cases")
    groups = defaultdict(list)
    for c in cases:
        groups[(c["signal"]["family"], c["signal"]["cohort"])].append(c)
    results = {"planId": plan["id"], "stocks": len(blocks), "cases": len(cases),
               "episodes": len({c["signal"]["episodeId"] for c in cases}),
               "suppressedRepeatedSignals": sum(len(b["suppressed"]) for b in blocks),
               "unavailableWindows": [{"symbol": b["symbol"], "window": w} for b in blocks for w, ok in b["eligibility"].items() if not ok],
               "groups": {":".join(k): {m: statistics_for(cs, m) for m in plan["models"]} for k, cs in sorted(groups.items())},
               "windows": {f["name"]: {":".join(k): {m: statistics_for([c for c in cs if c["window"] == f["name"]], m)
                            for m in plan["models"]} for k, cs in sorted(groups.items())} for f in plan["windows"]},
               "limitations": plan["limitations"], "providerCalls": 0}
    write(Path(root)/"results.json", results)
    import csv
    fields = ("caseId", "episodeId", "symbol", "window", "family", "cohort", "signalAt", "entryAt",
              "entryStatus", "stopDistancePct", "stopDistanceATR4h", "model", "status", "exitAt", "reason",
              "netR", "netReturnPct", "netPnl", "mfeR", "maeR", "holdingCalendarDays", "markNetReturnPct")
    with (Path(root)/"cases.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for c in cases:
            for model, p in c["paths"].items():
                row = {k: p.get(k) for k in fields}
                row.update(caseId=c["id"], episodeId=c["signal"]["episodeId"], symbol=c["symbol"], window=c["window"],
                           family=c["signal"]["family"], cohort=c["signal"]["cohort"], signalAt=c["signal"]["signalAt"],
                           entryAt=c["entry"].get("entryAt"), entryStatus=c["entry"]["status"], model=model,
                           stopDistancePct=c["features"].get("stopDistancePct"), stopDistanceATR4h=c["features"].get("stopDistanceATR4h"))
                writer.writerow(row)
    return results
