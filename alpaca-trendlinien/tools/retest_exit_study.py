"""Reproducible offline paired stop comparison on frozen Retest entries."""
import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datasets import digest, read_dataset, source_bars, data_kind
from exit_research import horizon_close
from lab_metrics import expected_grid
from retest_exits import VERSION, MODELS, contract_for, complete_history, path, summarize
from safety_strategy import StrategyContext, execution_costs
from strategy_portfolio import simulate, DEFAULTS
from strategy_research import write_json, RAW_COSTS
from strategy_run_lock import study_lock


def read(path):
    return json.loads(path.read_text("utf-8"))


def checked(path):
    data = read(path)
    if data["checksum"] != digest({k: v for k, v in data.items() if k != "checksum"}):
        raise ValueError("Corrupt research block: "+path.name)
    return data


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    value["checksum"] = digest({k: v for k, v in value.items() if k != "checksum"})
    write_json(path, value)


def run(args):
    root, archive, source = [Path(p).resolve() for p in (args.root, args.entries, args.data)]
    os.environ["TORI_DATA_DIR"] = str(source)
    prior = read(archive/"contract.json")
    code = Path(__file__).resolve().parents[1]
    names = ("retest_exits.py", "tools/retest_exit_study.py", "safety_strategy.py", "strategy_portfolio.py",
             "models.py", "datasets.py", "market_calendar.py", "lab_splits.py", "lab_metrics.py", "lab_data.py",
             "tori_entries.py", "trendlines.py", "exit_research.py")
    signature = {n: hashlib.sha256((code/n).read_bytes()).hexdigest() for n in names}
    with study_lock(root), patch("alpaca._request", side_effect=AssertionError("Retest study is offline")):
        root.mkdir(parents=True, exist_ok=True)
        frozen = {}
        source_blocks = {}
        for stage in prior["phases"]:
            frozen[stage] = []
            for symbol in prior["symbols"]:
                for geometry in ("hull_exact", "swing_zone"):
                    p = archive/stage/(symbol+"-"+geometry+".json")
                    block = checked(p)
                    if block["contractHash"] != digest(prior):
                        raise ValueError("Source contract mismatch")
                    source_blocks[stage+"/"+symbol+"/"+geometry] = block["checksum"]
                    for e in block["observations"]:
                        if e["family"] == "retest":
                            frozen[stage].append({k: deepcopy(v) for k, v in e.items() if k not in ("forward", "controls")})
            identities = [(e["model"], e["symbol"], e["entryAt"]) for e in frozen[stage]]
            if len(identities) != len(set(identities)):
                raise ValueError("Duplicate physical retest within geometry")
        contract = {"version": VERSION, "engine": signature, "entryContractHash": digest(prior),
            "sourceBlocks": source_blocks, "entryHashes": {s: digest(v) for s, v in frozen.items()},
            "entryCounts": {s: len(v) for s, v in frozen.items()}, "datasets": prior["datasets"], "phases": prior["phases"],
            "models": list(MODELS), "costs": RAW_COSTS, "portfolio": DEFAULTS,
            "preregistrationHash": hashlib.sha256((code/"RETEST-EXIT-TEST.md").read_bytes()).hexdigest()}
        manifest = root/"contract.json"
        if manifest.exists() and read(manifest) != contract:
            raise ValueError("Changed code/inputs: start a new study generation")
        if not manifest.exists():
            write_json(manifest, contract)
            write_json(root/"frozen-entries.json", frozen)
        elif read(root/"frozen-entries.json") != frozen:
            raise ValueError("Changed frozen entries")
        if args.stage == "prepare":
            print(json.dumps({"prepared": contract["entryCounts"], "contractHash": digest(contract)}))
            return
        if args.stage == "validation":
            decision = checked(root/"development-decision.json")
            if decision["contractHash"] != digest(contract):
                raise ValueError("Development decision contract mismatch")
        phase = prior["phases"][args.stage]
        entries = frozen[args.stage]
        records, contexts = [], {}
        costs = execution_costs(RAW_COSTS)
        for symbol in prior["symbols"]:
            selected = [e for e in entries if e["symbol"] == symbol]
            if not selected:
                continue
            identity = prior["datasets"][symbol]["id"]
            data = read_dataset(identity)
            if data_kind(data) != "market" or data["material"]["symbol"] != symbol:
                raise ValueError("Matching pinned market data required")
            sources = source_bars(data)
            context = StrategyContext(sources, phase["endAt"])
            contexts[identity] = context
            p = root/args.stage/(symbol+".json")
            if p.exists():
                block = checked(p)
                if block["contractHash"] != digest(contract):
                    raise ValueError("Checkpoint contract mismatch")
            else:
                rows = []
                available_fine = set(context.times)
                for e in selected:
                    initial = contract_for(context, e, RAW_COSTS)
                    planned = horizon_close(e["entryAt"], 10)
                    fits = planned <= phase["endAt"]
                    rows.append({"entry": e, "contract": initial, "history": complete_history(context.sources, e),
                        "calendarFits": fits,
                        "fullHorizonPath": fits and all(t in available_fine for t in expected_grid(e["entryAt"], planned)),
                        "paths": {m: path(context, e, initial, m) for m in MODELS}})
                block = {"contractHash": digest(contract), "records": rows}
                save(p, block)
            records.extend(block["records"])
            print(json.dumps({"stage": args.stage, "symbol": symbol, "entries": len(block["records"])}), flush=True)
        summary = summarize(records)
        portfolios = {}
        for geometry in ("hull_exact", "swing_zone"):
            selected = [r for r in records if r["entry"]["model"] == geometry and r["history"]["complete"] and r["calendarFits"]]
            for model in MODELS:
                portfolios[geometry+"/"+model] = simulate([r["entry"] for r in selected], [r["paths"][model] for r in selected], contexts, phase, costs, DEFAULTS)
        result = {"contractHash": digest(contract), "stage": args.stage, "groups": summary,
            "portfolios": portfolios, "rawEntries": len(records),
            "calendarCensored": sum(not r["calendarFits"] for r in records),
            "causalHistoryComplete": sum(r["history"]["complete"] for r in records)}
        save(root/(args.stage+"-results.json"), result)
        if args.stage == "development":
            decision = {"contractHash": digest(contract), "resultHash": result["checksum"],
                "geometry": {g: {k: result["groups"][g+"/complete_history"][k] for k in ("cases", "pairedClosed", "meanDeltaR", "deltaInterval")} for g in ("hull_exact", "swing_zone")},
                "decision": "Keep fixed rules; compare later known phase without tuning. No promotion or orders from this run."}
            save(root/"development-decision.json", decision)
        print(json.dumps({"done": args.stage, "rawEntries": len(records), "contractHash": digest(contract)}))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--entries", required=True, help="Frozen entry-discovery study directory")
    p.add_argument("--data", required=True, help="Exact existing TORI_DATA_DIR containing datasets/")
    p.add_argument("--root", required=True, help="New isolated runtime study directory")
    p.add_argument("--stage", required=True, choices=("prepare", "development", "validation"))
    run(p.parse_args())
