"""Persist both frozen Retest exit hypotheses; preview JSON, no external actions."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datasets import read_dataset
from retest_observation import observe
from strategy_run_lock import study_lock
from tools.retest_exit_study import checked, save


def scan(dataset_id, start_at, from_at, asof, state_path, seed_path=None):
    output = Path(state_path).resolve()
    with study_lock(output), patch("alpaca._request", side_effect=AssertionError("Offline observer only")):
        prior = checked(output) if output.exists() else None
        seed = checked(Path(seed_path))["state"] if seed_path and not prior else None
        state, events = observe(read_dataset(dataset_id), start_at, from_at, asof, prior, seed)
        save(output, state)
        return {"symbol": state["watch"]["symbol"], "asOf": asof, "records": len(state["records"]),
                "newEvents": events, "state": str(output),
                "meaning": "Independent-position model observation; journal retained. No orders, delivery or scheduler."}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset", required=True)
    p.add_argument("--start-at", required=True, type=int)
    p.add_argument("--from-at", required=True, type=int)
    p.add_argument("--asof", required=True, type=int)
    p.add_argument("--state", required=True)
    p.add_argument("--seed", help="Optional checked archived watch block, at/before from-at")
    a = p.parse_args()
    print(json.dumps(scan(a.dataset, a.start_at, a.from_at, a.asof, a.state, a.seed), ensure_ascii=False, allow_nan=False))
