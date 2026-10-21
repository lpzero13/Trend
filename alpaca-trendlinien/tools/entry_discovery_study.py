"""Isolated offline study. Does not change web profiles, queue or provider data.

Run development before validation. Artifact directories are private runtime data.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from time import perf_counter
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datasets import digest, read_dataset, data_kind
from entry_geometry import VERSION, MODELS, RULES
from entry_watch import WatchReplay, engine_signature
from entry_study import evaluate_entries, summarize, development_decision, watch_summary, HORIZONS, SEED
from strategy_research import write_json
from strategy_run_lock import study_lock
from tools.safety_universe import history_start


def read(path):
    return json.loads(path.read_text("utf-8"))


def checksum(value):
    return digest({k: v for k, v in value.items() if k != "checksum"})


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    value["checksum"] = checksum(value)
    write_json(path, value)


def run(args):
    root, source = Path(args.root).resolve(), Path(args.source).resolve()
    os.environ["TORI_DATA_DIR"] = str(source/"data")
    universe, imports = read(source/"universe-contract.json"), read(source/"imports.json")
    engine = {**engine_signature(), **{name: hashlib.sha256((Path(__file__).resolve().parents[1]/name).read_bytes()).hexdigest()
        for name in ("entry_study.py", "tools/entry_discovery_study.py", "lab_metrics.py", "lab_data.py", "models.py", "datasets.py", "market_calendar.py", "lab_splits.py", "tori_observations.py", "exit_research.py")}}
    contract = {"version": VERSION, "engine": engine, "rules": RULES, "models": list(MODELS), "horizons": list(HORIZONS),
        "seed": SEED, "symbols": universe["symbols"], "datasets": imports, "phases": universe["phases"],
        "sourceUniverseHash": digest(universe),
        "preregistrationHash": hashlib.sha256((Path(__file__).resolve().parents[1]/"EINSTIEGSSUCHE-INTERN.md").read_bytes()).hexdigest()}
    with study_lock(root), patch("alpaca._request", side_effect=AssertionError("Internal study is offline")):
        root.mkdir(parents=True, exist_ok=True)
        if (root/"contract.json").exists():
            if read(root/"contract.json") != contract:
                raise ValueError("Changed engine/contract: use a new study directory")
        else:
            write_json(root/"contract.json", contract)
        if args.stage == "validation" and not (root/"development-decision.json").exists():
            raise ValueError("Freeze development decision before validation labels")
        phase = universe["phases"][args.stage]
        blocks, entries, started = [], [], perf_counter()
        for symbol in universe["symbols"]:
            data = read_dataset(imports[symbol]["id"])
            if data_kind(data) != "market" or data["material"]["symbol"] != symbol:
                raise ValueError("Pinned real market dataset required")
            start = history_start(data, universe["phases"]["development"]["startAt"])
            for model in MODELS:
                path = root/args.stage/(symbol+"-"+model+".json")
                if path.exists():
                    block = read(path)
                    if block["checksum"] != checksum(block) or block["contractHash"] != digest(contract):
                        raise ValueError("Corrupt/mismatched checkpoint")
                else:
                    before = perf_counter()
                    replay = WatchReplay(data, model, start, phase["endAt"])
                    if args.stage == "validation":
                        prior = read(root/"development"/(symbol+"-"+model+".json"))
                        if checksum(prior) != prior["checksum"] or prior["contractHash"] != digest(contract):
                            raise ValueError("Corrupt development state")
                        replay.restore(prior["state"])
                    result = replay.run()
                    # Entry state is frozen and saved before the outcome evaluator is invoked.
                    state = replay.state()
                    save(root/"signal-state"/args.stage/(symbol+"-"+model+".json"), {"contractHash": digest(contract), "state": state})
                    observed = evaluate_entries(data, result["entries"], phase)
                    block = {"contractHash": digest(contract), "symbol": symbol, "model": model,
                        "stage": args.stage, "state": state, "observations": observed,
                        "seconds": perf_counter()-before}
                    save(path, block)
                blocks.append(block["state"])
                entries.extend(block["observations"])
                print(json.dumps({"stage": args.stage, "symbol": symbol, "model": model,
                    "entries": len(block["observations"]), "seconds": round(block["seconds"], 2)}), flush=True)
        summary = summarize(entries, MODELS)
        summary.update(stage=args.stage, watches=watch_summary(blocks, phase), contractHash=digest(contract))
        scientific_hash = digest(summary)
        summary.update(scientificHash=scientific_hash,
                       seconds=perf_counter()-started, createdAt=datetime.now(timezone.utc).isoformat())
        save(root/(args.stage+"-summary.json"), summary)
        if args.stage == "development":
            decision = {**development_decision(summary), "summaryHash": scientific_hash,
                        "createdAt": datetime.now(timezone.utc).isoformat()}
            if (root/"development-decision.json").exists():
                old = read(root/"development-decision.json")
                if old["summaryHash"] != scientific_hash or any(old.get(k) != v for k, v in development_decision(summary).items()):
                    raise ValueError("Development decision changed")
            else:
                save(root/"development-decision.json", decision)
        print(json.dumps({"done": args.stage, "entries": len(entries), "summary": str(root/(args.stage+"-summary.json"))}), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", required=True, help="Pinned safety-universe directory; no provider import")
    p.add_argument("--root", required=True, help="New isolated private artifact directory")
    p.add_argument("--stage", required=True, choices=("development", "validation"))
    run(p.parse_args())
