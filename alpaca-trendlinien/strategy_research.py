"""Offline strategy experiments and read-only causal candidate scans for Hermes."""
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import sqlite3
import statistics
from unittest.mock import patch

from datasets import digest, read_dataset, source_bars, data_kind
from lab_data import require_convention
from models import DataError, NY
from safety_strategy import (VERSION, MODELS, DEFAULT_RULES, StrategyContext,
                             validate_rules, strategy_path, execution_costs)
from settings import ROOT, data_dir
from strategy_portfolio import DEFAULTS as PORTFOLIO, simulate, validate as validate_portfolio
from tools.exit_study import freeze_cases

ENGINE_FILES = ("safety_strategy.py", "strategy_portfolio.py", "strategy_research.py", "strategy_cli.py",
                "strategy_verify.py", "models.py", "datasets.py", "tori_entries.py", "trendlines.py",
                "lab_engine.py", "lab_profiles.py", "lab_data.py", "lab_metrics.py", "lab_splits.py",
                "market_calendar.py", "exit_research.py", "tools/exit_study.py", "requirements.txt")
RAW_COSTS = {"spread_bps": 5., "slippage_bps": 5., "fee_per_order": 0., "notional": 1000.}


def engine_hashes():
    return {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ENGINE_FILES}


def write_json(path, value):
    temporary = path.with_suffix(path.suffix+".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), "utf-8")
    temporary.replace(path)


def export_entries(job_id, phase, output, validation_job=None):
    if phase not in ("development", "validation"):
        raise DataError("Dieser Werkzeugvertrag öffnet keinen finalen Holdout.", 409)
    jobs = {phase: job_id}
    if validation_job:
        if phase != "development":
            raise DataError("Zweiten Prüfauftrag zusammen mit Entwicklung exportieren.", 400)
        jobs["validation"] = validation_job
    cohorts, phases, provenance = {}, {}, {}
    with sqlite3.connect((data_dir()/"research"/"jobs.sqlite3").as_uri()+"?mode=ro", uri=True) as db:
        for section, identity in jobs.items():
            row = db.execute("SELECT status,spec,manifest FROM jobs WHERE id=?", (identity,)).fetchone()
            if not row or row[0] != "succeeded":
                raise DataError("Abgeschlossener Laborauftrag erforderlich.", 409)
            spec, manifest = json.loads(row[1]), json.loads(row[2])
            if spec.get("entry_mode") != "lab" or spec["lab"]["stage"] != section:
                raise DataError("Quellauftrag und angeforderte Forschungsphase passen nicht zusammen.", 409)
            window = manifest["temporalPlan"]["phases"][section]
            cases = (json.loads(r[0]) for r in db.execute("SELECT result FROM trials WHERE job_id=?", (identity,)))
            cohorts[section] = freeze_cases(cases, window)
            phases[section] = window
            provenance[section] = {"jobId": identity, "archivedEngineHash": manifest["engineHash"]}
    result = {"version": "tori-safety-entry-export-1", "createdAt": datetime.now(timezone.utc).isoformat(),
              "entryJobs": provenance, "phases": phases, "cohorts": cohorts}
    path = Path(output).expanduser().resolve()
    if path.exists():
        raise DataError("Ein vorhandener Einstiegsexport wird nicht überschrieben.", 409)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, result)
    return {"path": str(path), "entries": {k: len(v) for k, v in cohorts.items()}, "digest": digest(result)}


def stats(paths):
    closed = [p for p in paths if p["status"] == "closed"]
    positive = sum(p["netPnl"] > 0 for p in closed)
    gain = sum(max(0, p["netR"]) for p in closed)
    loss = sum(min(0, p["netR"]) for p in closed)
    return {"cases": len(paths), "closed": len(closed), "positive": positive,
            "unresolved": len(paths)-len(closed),
            "winRatePct": positive/len(closed)*100 if closed else None,
            "meanNetPct": statistics.mean(p["netReturnPct"] for p in closed) if closed else None,
            "meanNetR": statistics.mean(p["netR"] for p in closed) if closed else None,
            "medianNetR": statistics.median(p["netR"] for p in closed) if closed else None,
            "meanPnlPer1000USD": statistics.mean(p["netPnl"] for p in closed) if closed else None,
            "profitFactorR": gain/-loss if loss < 0 else None,
            "grossGainR": gain, "grossLossR": loss,
            "meanWinnerR": statistics.mean(p["netR"] for p in closed if p["netR"] > 0) if positive else None,
            "meanLoserR": statistics.mean(p["netR"] for p in closed if p["netR"] <= 0) if len(closed) > positive else None,
            "worstNetR": min((p["netR"] for p in closed), default=None),
            "reasons": dict(Counter(p.get("exitReason", p.get("reason")) for p in paths)),
            "replacements": sum(sum(e["kind"] == "safety_replace" for e in p["events"]) for p in paths)}


def aggregate_results(manifest, stage, entries, contracts, paths, contexts):
    features = {e["id"]: c for e, c in zip(entries, contracts)}
    grouped = defaultdict(list)
    for p in paths:
        grouped[(p["profile"], p["family"])].append(p)
    rows, portfolios = [], []
    for (profile, family), pool in sorted(grouped.items()):
        members = [e for e in entries if e["profile"] == profile and e["family"] == family]
        for cohort in ("all", "eligible"):
            allowed = {e["id"] for e in members if cohort == "all" or features[e["id"]]["eligible"]}
            selected = [p for p in pool if p["entryId"] in allowed]
            all_complete = Counter(p["entryId"] for p in selected if p["status"] == "closed")
            fixed_ids = {k for k, n in all_complete.items() if n == len(MODELS)*len(manifest["horizons"])}
            lookup = {(p["entryId"], p["days"], p["model"]): p for p in selected}
            for days in manifest["horizons"]:
                one = [p for p in selected if p["days"] == days]
                complete = Counter(p["entryId"] for p in one if p["status"] == "closed")
                paired_ids = {k for k, n in complete.items() if n == len(MODELS)}
                for model in MODELS:
                    subset = [p for p in one if p["model"] == model]
                    paired = [p for p in subset if p["entryId"] in paired_ids]
                    fixed = [p for p in subset if p["entryId"] in fixed_ids]
                    delta = [p["netR"]-lookup[p["entryId"], days, "fixed"]["netR"] for p in paired]
                    rows.append({"stage": stage, "profile": profile, "family": family, "cohort": cohort,
                        "days": days, "model": model, "all": stats(subset), "paired": stats(paired),
                        "constant": stats(fixed), "constantIds": sorted(fixed_ids),
                        "meanPairedDeltaR": statistics.mean(delta) if delta else None,
                        "pairedStocks": sorted({p["symbol"] for p in paired}),
                        "stocks": {s: stats([p for p in paired if p["symbol"] == s]) for s in sorted({e["symbol"] for e in members})}})
                    portfolio = simulate(members, subset, contexts, manifest["phases"][stage], manifest["costs"], manifest["portfolio"])
                    portfolios.append({"stage": stage, "profile": profile, "family": family, "cohort": cohort,
                                       "days": days, "model": model, **portfolio})
    return {"version": VERSION, "manifestHash": digest(manifest), "stage": stage,
            "entries": entries, "contracts": contracts, "paths": paths, "rows": rows, "portfolios": portfolios,
            "blockedBy": dict(Counter(k for c in contracts for k in c["blockedBy"])),
            "eligible": sum(c["eligible"] for c in contracts),
            "meaning": "Paired per-entry USD/R outcomes and separate cash-constrained portfolios. Dependent cases; previously examined validation; no final holdout access."}


def selection(result):
    # Exactly one primary entry/profile/family/horizon; never a best-of-18 search.
    rows = [r for r in result["rows"] if (r["profile"], r["family"], r["cohort"], r["days"]) == ("momentum_two", "breakout", "eligible", 10)
            and r["model"] != "fixed"]
    candidates = []
    for row in rows:
        s = row["paired"]
        enough = s["closed"] >= 20 and len(row["pairedStocks"]) >= 3
        positive = s["meanNetR"] is not None and s["meanNetR"] > 0 and row["meanPairedDeltaR"] > 0
        candidates.append({"model": row["model"], "completeCases": s["closed"], "stocks": row["pairedStocks"],
                           "enoughEvidence": enough, "positiveAndBeatsFixed": positive,
                           "eligibleForLaterIndependentTest": enough and positive})
    # Simplicity order preregistered; validation cannot change this decision.
    chosen = next((model for model in MODELS if any(c["model"] == model and c["eligibleForLaterIndependentTest"] for c in candidates)), None)
    return {"decisionBeforeValidation": True, "chosen": chosen, "primary": {"profile": "momentum_two", "family": "breakout", "cohort": "eligible", "days": 10},
            "candidates": candidates, "rule": "At least 20 complete development cases and 3 stocks, mean net R positive and paired gain over fixed; first eligible model in simplicity order. No replacement based on validation."}


def run_study(entry_path, output, stage="development", resume=False, progress=lambda x: None):
    if stage not in ("development", "validation"):
        raise DataError("Safety-Forschung verwendet Entwicklung und bekannte Validierung; finaler Holdout gesperrt.", 409)
    source = json.loads(Path(entry_path).read_text("utf-8-sig"))
    if set(source["cohorts"])-{"development", "validation"} or stage not in source["cohorts"]:
        raise DataError("Ungültiger Einstiegsexport oder reservierte Phase.", 409)
    root = Path(output).expanduser().resolve()
    manifest_path = root/"manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text("utf-8"))
        if manifest["sourceContractHash"] != digest(source) or manifest["engineFiles"] != engine_hashes():
            raise DataError("Datenvertrag oder Engine geändert; neues Experiment statt alter Wiederaufnahme.", 409)
        if (root/(stage+".json")).exists():
            raise DataError("Abgeschlossene Phase wird nicht überschrieben.", 409)
        if stage == "development" and not resume:
            raise DataError("Vorhandener Versuch; Wiederaufnahme ausdrücklich wählen.", 409)
    else:
        if stage != "development" or root.exists():
            raise DataError("Neuen Versuch mit Entwicklung in frischem Ausgabeordner starten.", 409)
        root.mkdir(parents=True)
        manifest = {"version": VERSION, "createdAt": datetime.now(timezone.utc).isoformat(),
                    "sourceContractHash": digest(source), "entryJobs": source.get("entryJobs", {}),
                    "phases": source["phases"], "cohorts": source["cohorts"],
                    "rules": validate_rules(), "costs": RAW_COSTS, "portfolio": validate_portfolio(),
                    "models": list(MODELS), "horizons": [5,10,20], "engineFiles": engine_hashes(),
                    "primary": {"profile": "momentum_two", "family": "breakout", "cohort": "eligible", "days": 10},
                    "holdout": "unopened; only previously examined development/validation",
                    "loopPolicy": "Correct demonstrable implementation faults with new versioned attempts; no parameter search until profitable."}
        write_json(manifest_path, manifest)
    if stage == "validation" and not ((root/"decision-before-validation.json").exists() and (root/"development.json").exists()):
        raise DataError("Entwicklungsbilanz zuerst abschließen und Entscheidung einfrieren.", 409)
    entries = manifest["cohorts"][stage]
    contexts, contracts, paths = {}, [], []
    checkpoint_dir = root/"checkpoints"
    checkpoint_dir.mkdir(exist_ok=True)
    with patch("alpaca._request", side_effect=AssertionError("Safety research is offline")):
        for identity in sorted({e["datasetId"] for e in entries}):
            data = read_dataset(identity)
            if data_kind(data) != "market" or data["material"]["feed"] != "iex" or data["material"]["adjustment"] != "split":
                raise DataError("Gepinnte echte splitbereinigte IEX-Daten erforderlich.", 422)
            require_convention(data)
            context = StrategyContext(source_bars(data), manifest["phases"][stage]["endAt"], manifest["rules"])
            contexts[identity] = context
            members = [e for e in entries if e["datasetId"] == identity]
            checkpoint = checkpoint_dir/(stage+"-"+identity+".json")
            if checkpoint.exists():
                if not resume:
                    raise DataError("Checkpoint vorhanden; explizite Wiederaufnahme erforderlich.", 409)
                block = json.loads(checkpoint.read_text("utf-8"))
                payload = {k: v for k, v in block.items() if k != "checksum"}
                if block.get("checksum") != digest(payload) or block["manifestHash"] != digest(manifest):
                    raise DataError("Checkpoint-Prüfsumme oder Vertrag ungültig.", 409)
            else:
                block = {"manifestHash": digest(manifest), "contracts": [], "paths": []}
                progress({"stage": stage, "symbol": data["material"]["symbol"], "entries": len(members)})
                for e in members:
                    contract = context.entry_contract(e, manifest["costs"])
                    block["contracts"].append(contract)
                    for days in manifest["horizons"]:
                        for model in MODELS:
                            p = strategy_path(context, e, contract, model, days)
                            p.update(profile=e["profile"], family=e["family"], symbol=e["symbol"], datasetId=identity)
                            block["paths"].append(p)
                block["checksum"] = digest(block)
                write_json(checkpoint, block)
            contracts.extend(block["contracts"])
            paths.extend(block["paths"])
        # Contracts assembled in dataset order; reorder before zip with entries.
        by_entry = {c["entryId"]: c for c in contracts}
        contracts = [by_entry[e["id"]] for e in entries]
        result = aggregate_results(manifest, stage, entries, contracts, paths, contexts)
        if stage == "development":
            write_json(root/"decision-before-validation.json", selection(result))
        write_json(root/(stage+".json"), result)
    return {"study": str(root), "stage": stage, "entries": len(entries), "eligible": result["eligible"],
            "paths": len(paths), "rows": len(result["rows"]), "portfolios": len(result["portfolios"]),
            "manifestHash": digest(manifest), "decision": selection(result) if stage == "development" else json.loads((root/"decision-before-validation.json").read_text("utf-8"))}


def scan_candidates(dataset, cutoff, profile="momentum_two", since=None, history_start=None):
    """Full causal state replay without outcome evaluators; emit recent signals.

    Historical fills are labelled as such. Pending confirmed signals require a
    then-available open before eligibility can be final, never a guessed fill.
    """
    from lab_engine import scan_plan
    from lab_profiles import LabScanner
    from research import validate_spec
    if profile not in ("baseline", "momentum_two"):
        raise DataError("Bekanntes Kandidatenprofil erforderlich.", 400)
    require_convention(dataset)
    view = deepcopy(dataset)
    view["material"]["bars"] = {tf: [b for b in rows if b["end"] <= cutoff] for tf, rows in dataset["material"]["bars"].items()}
    sources = source_bars(view)
    if not sources["4h"] or not sources.get("5m"):
        raise DataError("Keine abgeschlossenen regulären Quell-/5m-Kerzen vor dem Stichtag.", 422)
    day = datetime.fromtimestamp(sources["4h"][0].time, NY).date()+timedelta(days=365)
    first = int(datetime.combine(day, datetime.min.time(), NY).timestamp())
    start = history_start if history_start is not None else first
    if start < first:
        raise DataError("Historischer Scanstart benötigt ein Jahr Vorlauf.", 422)
    if cutoff <= start:
        raise DataError("Ein Jahr Quellhistorie vor dem Kandidatenscan erforderlich.", 422)
    phase = {"startAt": start, "endAt": cutoff}
    plan = scan_plan(view, phase, sources=sources)
    spec = validate_spec({"entry_mode": "lab", "symbols": [dataset["material"]["symbol"]], "latency_seconds": 300,
                          "lab": {"profiles": [profile], "benchmark_symbol": ""}})
    shared = {"sources": sources}
    scanner = LabScanner(view, spec, plan, profile, shared=shared)
    for i in range(plan["scan_start"], plan["discovery_end"]+1):
        scanner.advance(i)
        shared.get("lines", {}).clear()
    for case in scanner.cases.values():
        scanner.executions(case, cutoff)
        case.update(profile=profile, sourceSetupId=case["id"])
        for e in case["variants"]:
            e["inPhase"] = e.get("entryAt", e.get("signalAt", 0)) <= cutoff
    since = since if since is not None else cutoff-7*86400
    entries = freeze_cases(scanner.cases.values(), {"startAt": since, "endAt": cutoff})
    context = StrategyContext(sources, cutoff)
    observations = [{"entry": e, "contract": context.entry_contract(e), "kind": "historical_open_observed",
                     "brokerAction": None} for e in entries]
    pending = []
    for case in scanner.cases.values():
        for e in case["variants"]:
            if e["status"] == "pending" and e["phase"] == "execution" and e.get("availableAt", 0) >= since:
                pending.append({"id": digest({"setup": case["id"], "family": e["variant"], "signalAt": e["signalAt"]}),
                    "symbol": dataset["material"]["symbol"], "family": e["variant"], "signalAt": e["signalAt"],
                    "availableAt": e["availableAt"], "kind": "confirmed_waiting_for_observed_open",
                    "red": case["frozen"]["red"], "green": case["frozen"]["green"],
                    "eligibility": "unknown_until_open", "brokerAction": None})
    return {"version": VERSION, "datasetId": dataset["id"], "symbol": dataset["material"]["symbol"],
            "asOf": cutoff, "since": since, "profile": profile, "rules": validate_rules(),
            "historyStartAt": start, "dataKind": data_kind(dataset), "feed": dataset["material"].get("feed"),
            "latestSourceClose": sources["4h"][-1].end, "latestFineClose": sources["5m"][-1].end,
            "observations": observations, "pending": sorted(pending, key=lambda p: p["id"]),
            "eligibleObservations": sum(o["contract"]["eligible"] for o in observations),
            "setupsReplayed": len(scanner.cases), "meaning": "Read-only historical/pending candidate events; stable IDs for caller deduplication. No outcome access, orders or promised live execution. Dataset freshness remains caller-visible."}
