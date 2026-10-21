"""Internal persisted watch scan on an existing immutable dataset; JSON only.

No provider import, broker access, scheduling or actual message delivery. The
saved message list is an inspectable outbox; consumers deduplicate eventKey.
"""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datasets import read_dataset, digest
from entry_geometry import MODELS
from entry_watch import WatchReplay
from strategy_run_lock import study_lock
from strategy_research import write_json


def scan(dataset_id, model, start_at, asof, state_path):
    path = Path(state_path).resolve()
    with study_lock(path), patch("alpaca._request", side_effect=AssertionError("Offline pinned dataset required")):
        engine = WatchReplay(read_dataset(dataset_id), model, start_at, asof)
        old_messages, old_entries = 0, 0
        if path.exists():
            saved = json.loads(path.read_text("utf-8"))
            if saved["checksum"] != digest(saved["state"]):
                raise ValueError("Corrupt scan state")
            if asof < saved["state"]["asOf"]:
                raise ValueError("Use a separate state file for an earlier historical cutoff")
            engine.restore(saved["state"])
            old_messages, old_entries = len(engine.messages), len(engine.entries)
        result = engine.run()
        state = engine.state()
        path.parent.mkdir(parents=True, exist_ok=True)
        write_json(path, {"checksum": digest(state), "state": state})
        return {"version": result["version"], "symbol": result["symbol"], "model": model, "asOf": asof,
                "newMessages": result["messages"][old_messages:], "newEntries": result["entries"][old_entries:],
                "pendingExecutions": result["pending"], "state": str(path),
                "delivery": "preview only; all historical messages retained in state; deduplicate eventKey"}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset", required=True)
    p.add_argument("--model", choices=MODELS, default="swing_envelope")
    p.add_argument("--start-at", required=True, type=int)
    p.add_argument("--asof", required=True, type=int)
    p.add_argument("--state", required=True)
    args = p.parse_args()
    print(json.dumps(scan(args.dataset, args.model, args.start_at, args.asof, args.state), ensure_ascii=False, allow_nan=False))
