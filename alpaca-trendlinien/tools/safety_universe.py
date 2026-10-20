"""Predeclared cross-stock replication, unchanged rules, no holdout access.

One import per new symbol, then frozen offline signal discovery. Existing five
stocks are copied by exact dataset ID and checked against archived physical
entries. Raw data and discovery checkpoints belong in ignored artifacts only.
"""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Fixed before imports or additional-stock outcomes; not investment selections.
ADDITIONAL = ("AAPL", "GOOGL", "NVDA", "META", "AMD", "AVGO", "ORCL", "ADBE",
              "V", "MA", "BAC", "GS", "CVX", "CAT", "WMT", "COST", "PG", "JNJ", "UNH", "HD")


def history_start(data, common_start):
    """Availability rule, independent of signal/outcome values."""
    from models import NY
    rows = data["material"]["bars"]["4h"]
    if not rows:
        return None
    ready = datetime.fromtimestamp(rows[0]["time"], NY).date()+timedelta(days=365)
    return max(common_start, int(datetime.combine(ready, datetime.min.time(), NY).timestamp()))


def run(args):
    from datasets import digest, read_dataset, data_kind
    from lab_data import import_dataset, require_convention
    from strategy_research import engine_hashes, scan_candidates, write_json
    root, source_root = Path(args.root).resolve(), Path(args.seed).resolve()
    seed_path = source_root/"contract.json"
    source = json.loads(seed_path.read_text("utf-8"))
    old_data = Path(args.seed_data).resolve()
    os.environ.update(TORI_DATA_DIR=str(root/"data"), TORI_AUTO_ENABLED="0")
    seed_ids = {e["symbol"]: e["datasetId"] for entries in source["cohorts"].values() for e in entries}
    contract = {"version": "safety-cross-stock-2", "symbols": sorted(set(seed_ids)|set(ADDITIONAL)),
                "newSymbols": list(ADDITIONAL), "seedContractHash": digest(source),
                "history_days": 910, "profiles": ["baseline", "momentum_two"],
                "phases": {k: source["phases"][k] for k in ("development", "validation")},
                "engineFiles": engine_hashes(), "discoveryToolHash": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "availabilityRule": "Keep every declared symbol; replay from max(common development start, first complete 4h local date plus 365 days). Report unavailable stages; never infer or fill missing bars.",
                "meaning": "Cross-stock replication on the already-known dates, present-day fixed liquid US symbols; not an untouched temporal validation. No result-based universe changes; no final holdout."}
    path = root/"universe-contract.json"
    if path.exists():
        saved = json.loads(path.read_text("utf-8"))
        if {k: v for k, v in saved.items() if k != "createdAt"} != contract:
            raise ValueError("Universe, code or source changed; use a new replication directory")
    else:
        root.mkdir(parents=True, exist_ok=True)
        write_json(path, {**contract, "createdAt": datetime.now(timezone.utc).isoformat()})
    imports_path = root/"imports.json"
    imports = json.loads(imports_path.read_text("utf-8")) if imports_path.exists() else {}
    reuse = Path(args.reuse).resolve() if args.reuse else None
    reused = json.loads((reuse/"imports.json").read_text("utf-8")) if reuse else {}
    for symbol in contract["symbols"]:
        if symbol not in imports:
            if symbol in reused:
                identity = reused[symbol]["id"]
                if symbol in seed_ids and identity != seed_ids[symbol]:
                    raise ValueError("Original stock must retain its exact pinned seed dataset")
                destination = root/"data"/"datasets"/(identity+".json")
                destination.parent.mkdir(parents=True, exist_ok=True)
                if not destination.exists():
                    shutil.copy2(reuse/"data"/"datasets"/(identity+".json"), destination)
            elif symbol in seed_ids:
                identity = seed_ids[symbol]
                destination = root/"data"/"datasets"/(identity+".json")
                destination.parent.mkdir(parents=True, exist_ok=True)
                if not destination.exists():
                    shutil.copy2(old_data/"datasets"/(identity+".json"), destination)
            else:
                print(json.dumps({"importing": symbol}), flush=True)
                identity = import_dataset(symbol, contract["history_days"])
            data = read_dataset(identity)
            imports[symbol] = {"id": identity, "counts": {tf: len(rows) for tf, rows in data["material"]["bars"].items()}}
            write_json(imports_path, imports)
        data = read_dataset(imports[symbol]["id"])
        if data_kind(data) != "market" or data["material"]["symbol"] != symbol or data["material"]["adjustment"] != "split" or data["material"].get("feed") != "iex":
            raise ValueError("Real matching split-adjusted datasets required")
        require_convention(data)
        print(json.dumps({"pinned": symbol, **imports[symbol]}), flush=True)
    if args.prepare_only:
        return
    output = root/"entries.json"
    if output.exists():
        raise ValueError("Discovery already completed; reuse its fixed entry file")
    cohorts = {stage: [] for stage in contract["phases"]}
    discovery_dir = root/"discovery"
    discovery_dir.mkdir(exist_ok=True)
    with patch("alpaca._request", side_effect=AssertionError("Discovery after pinning is offline")):
        for symbol in contract["symbols"]:
            data = read_dataset(imports[symbol]["id"])
            replay_start = history_start(data, contract["phases"]["development"]["startAt"])
            for stage, window in contract["phases"].items():
                for profile in contract["profiles"]:
                    cache = discovery_dir/(symbol+"-"+stage+"-"+profile+".json")
                    if cache.exists():
                        block = json.loads(cache.read_text("utf-8"))
                        assert block["checksum"] == digest({k: v for k, v in block.items() if k != "checksum"})
                        assert block["universeHash"] == digest(contract)
                    else:
                        available = replay_start is not None and replay_start < window["endAt"]
                        result = scan_candidates(data, window["endAt"], profile, window["startAt"], replay_start) if available else {"observations": [], "setupsReplayed": 0}
                        block = {"universeHash": digest(contract), "symbol": symbol, "stage": stage, "profile": profile,
                                 "entries": [o["entry"] for o in result["observations"]], "setupsReplayed": result["setupsReplayed"],
                                 "historyStartAt": replay_start, "available": available}
                        block["checksum"] = digest(block)
                        write_json(cache, block)
                    if symbol in seed_ids:
                        physical = lambda e: (e["entryAt"], e["entryPrice"], round(e["initialStop"], 9), e["family"])
                        expected = sorted(physical(e) for e in source["cohorts"][stage] if e["symbol"] == symbol and e["profile"] == profile)
                        assert sorted(physical(e) for e in block["entries"]) == expected, (symbol, stage, profile)
                    cohorts[stage].extend(block["entries"])
                    print(json.dumps({"discovered": symbol, "stage": stage, "profile": profile, "entries": len(block["entries"])}), flush=True)
    write_json(output, {"version": "tori-safety-entry-export-1", "createdAt": datetime.now(timezone.utc).isoformat(),
                       "cohorts": cohorts, "phases": contract["phases"],
                       "entryJobs": {"basis": "fresh full causal replay without outcome evaluator", "universeHash": digest(contract), "datasets": imports}})
    print(json.dumps({"done": True, "symbols": len(imports), "entries": {k: len(v) for k, v in cohorts.items()}}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--seed", required=True, help="Previous exit-study directory containing contract.json")
    parser.add_argument("--seed-data", required=True, help="Exact pinned original data directory")
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--reuse", help="Reuse exact immutable datasets from an earlier universe run; no new API calls for those symbols")
    run(parser.parse_args())
