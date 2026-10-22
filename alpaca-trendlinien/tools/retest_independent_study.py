"""One frozen reserved-window audit. Prepare, freeze signals, then evaluate."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datasets import digest, read_dataset, data_kind, source_bars
from entry_watch import WatchReplay
from lab_data import session_bounds
from lab_metrics import expected_grid
from lab_splits import sessions_between
from retest_observation import VERSION, ACCEPTANCE, EXITS, signature, context_for, record, assessment
from retest_variants import RULES, summarize
from safety_strategy import execution_costs
from strategy_portfolio import DEFAULTS, simulate
from strategy_research import RAW_COSTS, write_json
from strategy_run_lock import study_lock
from tools.retest_exit_study import checked, read, save

MODELS = ("swing_zone", "hull_exact")


def contract_for(source, archive):
    universe, imports = read(source/"universe-contract.json"), read(source/"imports.json")
    parent = read(archive/"contract.json")
    if parent["datasets"] != imports or parent["symbols"] != universe["symbols"]:
        raise ValueError("Changed source universe")
    dates = sessions_between("2026-07-06", "2026-10-16")
    phase = {"startDate": dates[0], "endDate": dates[-1], "startAt": session_bounds(dates[0])[0],
             "endAt": session_bounds(dates[-1])[1], "sessions": len(dates)}
    expected = set(expected_grid(phase["startAt"], phase["endAt"]))
    inventory, seeds = {}, {}
    for symbol in universe["symbols"]:
        data = read_dataset(imports[symbol]["id"])
        if data_kind(data) != "market" or data["material"]["symbol"] != symbol:
            raise ValueError("Matching real market dataset required")
        sources = source_bars(data)
        present = {b.time for b in sources["5m"] if b.end <= phase["endAt"]}
        inventory[symbol] = {"expected5m": len(expected), "available5m": len(expected & present),
                             "missing5m": len(expected-present),
                             "last5mEnd": sources["5m"][-1].end, "last4hEnd": sources["4h"][-1].end}
        for model in MODELS:
            key = symbol+"-"+model
            block = checked(archive/"validation"/(key+".json"))
            if block["contractHash"] != digest(parent) or block["state"]["asOf"] != parent["phases"]["validation"]["endAt"]:
                raise ValueError("Invalid validation continuation state")
            seeds[key] = block["checksum"]
    code = Path(__file__).resolve().parents[1]
    engine = signature()
    for name in ("tools/retest_independent_study.py", "tools/retest_observe.py"):
        engine[name] = hashlib.sha256((code/name).read_bytes()).hexdigest()
    return {"version": VERSION, "engine": engine, "entryParentHash": digest(parent), "seedHashes": seeds,
            "phase": phase, "models": list(MODELS), "exits": list(EXITS), "costs": RAW_COSTS,
            "portfolio": DEFAULTS, "exitRules": RULES, "acceptance": ACCEPTANCE,
            "symbols": universe["symbols"], "datasets": imports, "inventory": inventory,
            "preregistrationHash": hashlib.sha256((code/"RETEST-BEOBACHTUNG-PLAN.md").read_bytes()).hexdigest()}


def run(args):
    source, archive, root = [Path(p).resolve() for p in (args.source, args.archive, args.root)]
    os.environ["TORI_DATA_DIR"] = str(source/"data")
    with study_lock(root), patch("alpaca._request", side_effect=AssertionError("Offline audit only")):
        root.mkdir(parents=True, exist_ok=True)
        contract = contract_for(source, archive)
        manifest = root/"contract.json"
        if manifest.exists() and read(manifest) != contract:
            raise ValueError("Frozen study changed; never resume under new rules/code/data")
        if args.stage == "prepare":
            if not manifest.exists():
                write_json(manifest, contract)
            print(json.dumps({"prepared": digest(contract), "phase": contract["phase"], "symbols": len(contract["symbols"])}))
            return
        if not manifest.exists():
            raise ValueError("Prepare the contract before signals")
        phase = contract["phase"]
        blocks = {}
        if args.stage == "signals":
            for symbol in contract["symbols"]:
                data = read_dataset(contract["datasets"][symbol]["id"])
                for model in MODELS:
                    key = symbol+"-"+model
                    output = root/"signals"/(key+".json")
                    if output.exists():
                        block = checked(output)
                        if block["contractHash"] != digest(contract):
                            raise ValueError("Signal checkpoint mismatch")
                    else:
                        seed = checked(archive/"validation"/(key+".json"))["state"]
                        replay = WatchReplay(data, model, seed["startAt"], phase["endAt"])
                        replay.restore(seed)
                        replay.run()
                        entries = [e for e in replay.entries if e["family"] == "retest" and phase["startAt"] <= e["entryAt"] <= phase["endAt"]]
                        if len({e["entryAt"] for e in entries}) != len(entries):
                            raise ValueError("Duplicate physical retest")
                        block = {"contractHash": digest(contract), "entries": entries, "state": replay.state()}
                        save(output, block)
                    blocks[key] = block["checksum"]
                    print(json.dumps({"signal": key, "entries": len(block["entries"])}), flush=True)
            save(root/"signals-frozen.json", {"contractHash": digest(contract), "blocks": blocks})
            return
        frozen = checked(root/"signals-frozen.json")
        if frozen["contractHash"] != digest(contract) or len(frozen["blocks"]) != len(contract["symbols"])*len(MODELS):
            raise ValueError("Freeze the full universe before evaluating")
        records, contexts = [], {}
        for symbol in contract["symbols"]:
            identity = contract["datasets"][symbol]["id"]
            context = context_for(read_dataset(identity), phase["endAt"])
            contexts[identity] = context
            entries = []
            for model in MODELS:
                key = symbol+"-"+model
                signal = checked(root/"signals"/(key+".json"))
                if signal["checksum"] != frozen["blocks"][key] or signal["contractHash"] != digest(contract):
                    raise ValueError("Frozen signal list changed")
                entries.extend(signal["entries"])
            output = root/"results"/(symbol+".json")
            if output.exists():
                block = checked(output)
                if block["contractHash"] != digest(contract) or [r["entry"] for r in block["records"]] != entries:
                    raise ValueError("Result checkpoint mismatch")
            else:
                block = {"contractHash": digest(contract), "records": [record(context, e) for e in entries]}
                save(output, block)
            records.extend(block["records"])
            print(json.dumps({"evaluated": symbol, "cases": len(entries)}), flush=True)
        portfolios = {}
        for model in MODELS:
            selected = [r for r in records if r["entry"]["model"] == model and r["history"]["complete"] and r["calendarFits"]]
            for variant in EXITS:
                portfolios[model+"/"+variant] = simulate([r["entry"] for r in selected], [r["paths"][variant] for r in selected],
                    contexts, phase, execution_costs(RAW_COSTS), DEFAULTS)
        result = {"contractHash": digest(contract), "signalsHash": frozen["checksum"], "records": len(records),
                  "groups": summarize(records, "atr_gain_stop"), "portfolios": portfolios,
                  "lateEntries": {m: sum(r["entry"]["model"] == m and not r["calendarFits"] for r in records) for m in MODELS},
                  "assessment": assessment(records, portfolios)}
        save(root/"results.json", result)
        print(json.dumps(result["assessment"]), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", required=True)
    p.add_argument("--archive", required=True)
    p.add_argument("--root", required=True)
    p.add_argument("--stage", required=True, choices=("prepare", "signals", "evaluate"))
    run(p.parse_args())
