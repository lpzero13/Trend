"""Freeze archived entries, compare exits offline; never opens final holdout.

Usage: python tools/exit_study.py --source artifacts/contact-loops-20261019-a
       --output artifacts/exit-study-20261019-a
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from exit_research import DEFAULT_COSTS, MODELS, VERSION, ExitSources, exit_path, summarize

PROFILES = ("baseline", "momentum_two")
FAMILIES = ("breakout", "horizontal", "retest")


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def freeze_cases(cases, phase):
    """Canonical setup chosen from known timestamps/geometry, never returns.

    Physical entries may have several historical line pairs. Within each profile
    and family keep the earliest confirmation, then earliest armed setup, then
    lexical anchor geometry. Preserve the number of alternative setups.
    """
    selected = {}
    alternatives = Counter()
    for c in cases:
        if c["profile"] not in PROFILES:
            continue
        for e in c["variants"]:
            if e["status"] != "observed" or not e.get("inPhase"):
                continue
            if not phase["startAt"] <= e["entryAt"] <= phase["endAt"]:
                continue
            key = (c["profile"], e["variant"], c["symbol"], e["entryAt"])
            alternatives[key] += 1
            entry = {k: e.get(k) for k in ("entryAt", "entryPrice", "initialStop", "signalAt",
                     "availableAt", "resistanceAtSignal", "quality")}
            entry.update(symbol=c["symbol"], datasetId=c["datasetId"], profile=c["profile"],
                         family=e["variant"], sourceSetupId=c["sourceSetupId"], armedAt=c["startAt"],
                         red=c["frozen"]["red"], green=c["frozen"]["green"])
            # Values of these rays are just the archived known signal projection.
            rank = (entry["signalAt"], entry["armedAt"], json.dumps(c["frozen"], sort_keys=True))
            if key not in selected or rank < selected[key][0]:
                selected[key] = (rank, entry)
    result = []
    for key, (_, e) in sorted(selected.items()):
        e["alternativeSetups"] = alternatives[key]
        e["id"] = fingerprint(e)
        result.append(e)
    return result


def read_contract(source):
    # Read only: do not migrate, resume or modify archived jobs.
    database = source/"data"/"research"/"jobs.sqlite3"
    release = json.loads((source/"release-verification-job.json").read_text("utf-8"))
    validation = json.loads((source/"round-3-validation.json").read_text("utf-8"))
    jobs = {"development": release["jobId"], "validation": validation["jobId"]}
    cohorts, phases, metadata = {}, {}, {}
    with sqlite3.connect(database.as_uri()+"?mode=ro", uri=True) as db:
        for phase_name, job in jobs.items():
            row = db.execute("SELECT status,manifest FROM jobs WHERE id=?", (job,)).fetchone()
            if not row or row[0] != "succeeded":
                raise ValueError("Completed archived entry jobs required")
            manifest = json.loads(row[1])
            phase = manifest["temporalPlan"]["phases"][phase_name]
            phase = {**phase, "endAt": min(phase["endAt"], phase["labelEndAt"])}
            cases = (json.loads(row[0]) for row in db.execute(
                "SELECT result FROM trials WHERE job_id=? AND json_extract(result,'$.profile') IN ('baseline','momentum_two')", (job,)))
            cohorts[phase_name] = freeze_cases(cases, phase)
            phases[phase_name] = phase
            metadata[phase_name] = {"jobId": job, "archivedEngineHash": manifest.get("engineHash")}
    return {"version": VERSION, "createdAt": datetime.now(timezone.utc).isoformat(),
            "models": list(MODELS), "horizons": [5, 10, 20], "costs": DEFAULT_COSTS,
            "phases": phases, "entryJobs": metadata, "cohorts": cohorts,
            "selection": "Earliest known confirmation/armed time then lexical frozen geometry; no outcome fields",
            "holdout": "unopened; development and previously examined validation only",
            "engineFiles": {name: hashlib.sha256((Path(__file__).resolve().parents[1]/name).read_bytes()).hexdigest()
                for name in ("exit_research.py", "tools/exit_study.py", "trendlines.py", "lab_metrics.py", "lab_data.py", "lab_splits.py", "market_calendar.py")}}


def compare(contract, datasets):
    from datasets import source_bars
    paths = []
    for phase_name, entries in contract["cohorts"].items():
        by_dataset = defaultdict(list)
        for e in entries:
            by_dataset[e["datasetId"]].append(e)
        for identity, stock_entries in sorted(by_dataset.items()):
            data = datasets[identity]
            source = ExitSources(source_bars(data), contract["phases"][phase_name]["endAt"])
            print(json.dumps({"phase": phase_name, "symbol": data["material"]["symbol"], "entries": len(stock_entries)}), flush=True)
            for e in stock_entries:
                for days in contract["horizons"]:
                    for model in contract["models"]:
                        p = exit_path(source, e, model, days, contract["costs"])
                        p.update(entryId=e["id"], symbol=e["symbol"], phase=phase_name,
                                 profile=e["profile"], family=e["family"], datasetId=identity)
                        paths.append(p)
    grouped = defaultdict(list)
    for p in paths:
        grouped[(p["phase"], p["profile"], p["family"], p["days"])].append(p)
    rows = []
    for key, pool in sorted(grouped.items()):
        complete = Counter(p["entryId"] for p in pool if p["status"] == "closed")
        common = {k for k, count in complete.items() if count == len(contract["models"])}
        by_id = {(p["entryId"], p["model"]): p for p in pool}
        for model in contract["models"]:
            subset = [p for p in pool if p["model"] == model]
            paired = [p for p in subset if p["entryId"] in common]
            stopped_before_gain = sum(p["exitReason"] in ("stop", "stop_gap", "trailing_stop", "trailing_gap", "fakeout")
                                     and p["netPnl"] < 0 and by_id[(p["entryId"], "time")]["netPnl"] > 0 for p in paired)
            rows.append({"phase": key[0], "profile": key[1], "family": key[2], "days": key[3],
                         "model": model, "all": summarize(subset), "paired": summarize(paired),
                         "lossBeforePositiveTimeExit": stopped_before_gain,
                         "stocks": {s: summarize([p for p in paired if p["symbol"] == s]) for s in sorted({p["symbol"] for p in subset})},
                         "knownResistanceOnly": summarize([p for p in paired if p["knownResistance"] is not None])})
    return {"version": VERSION, "contractHash": fingerprint(contract), "rows": rows, "paths": paths,
            "meaning": "Paired net exit study per 1000 USD fractional notional per independent case; no summed portfolio P/L. Costs and all assumptions in contract. Overlapping cases are dependent. Final holdout unopened."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source, output = Path(args.source).resolve(), Path(args.output).resolve()
    if output.exists():
        raise ValueError("Choose a fresh output directory; completed contracts must not be overwritten")
    os.environ.update(TORI_DATA_DIR=str(source/"data"), TORI_AUTO_ENABLED="0")
    contract = read_contract(source)
    from datasets import data_kind, read_dataset
    from lab_data import require_convention
    identities = {e["datasetId"] for entries in contract["cohorts"].values() for e in entries}
    with patch("alpaca._request", side_effect=AssertionError("Exit study must remain offline")):
        datasets = {key: read_dataset(key) for key in identities}
        for data in datasets.values():
            if data_kind(data) != "market" or data["material"]["feed"] != "iex" or data["material"]["adjustment"] != "split":
                raise ValueError("Pinned real split-adjusted IEX data required")
            require_convention(data)
        output.mkdir(parents=True)
        (output/"contract.json").write_text(json.dumps(contract, indent=2, allow_nan=False), "utf-8")
        result = compare(contract, datasets)
        (output/"results.json").write_text(json.dumps(result, indent=2, allow_nan=False), "utf-8")
        print(json.dumps({"done": True, "paths": len(result["paths"]), "rows": len(result["rows"]), "contractHash": result["contractHash"]}), flush=True)


if __name__ == "__main__":
    main()
