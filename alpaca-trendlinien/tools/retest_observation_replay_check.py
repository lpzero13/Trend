"""Technical replay proof: resumed observations equal one-shot observations.

Uses fixed AAPL/AMZN examples, not performance-selected cases. This is not a
prospective trading test; the reserved-window audit must already be complete.
"""
import argparse
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datasets import read_dataset, digest
from lab_data import session_bounds
from retest_observation import observe
from tools.retest_exit_study import checked, read, save


def run(root, archive, data):
    root, archive = Path(root), Path(archive)
    os.environ["TORI_DATA_DIR"] = str(Path(data).resolve())
    contract = read(root/"contract.json")
    result = checked(root/"results.json")
    assert result["contractHash"] == digest(contract)
    phase = contract["phase"]
    middle = session_bounds("2026-08-18")[1]
    proof = []
    with patch("alpaca._request", side_effect=AssertionError("Offline replay proof")):
        for symbol in ("AAPL", "AMZN"):
            dataset = read_dataset(contract["datasets"][symbol]["id"])
            seed = checked(archive/"validation"/(symbol+"-swing_zone.json"))["state"]
            first, _ = observe(dataset, seed["startAt"], phase["startAt"], middle, seed=seed)
            # Actual JSON round trip and process-independent state, not object aliasing.
            save(root/"replay-proof"/(symbol+"-mid.json"), first)
            resumed, events = observe(dataset, seed["startAt"], phase["startAt"], phase["endAt"],
                                      checked(root/"replay-proof"/(symbol+"-mid.json")))
            full, _ = observe(dataset, seed["startAt"], phase["startAt"], phase["endAt"], seed=seed)
            assert resumed["records"] == full["records"] and resumed["watch"] == full["watch"]
            assert {e["eventKey"] for e in resumed["journal"]} == {e["eventKey"] for e in full["journal"]}
            again, new = observe(dataset, seed["startAt"], phase["startAt"], phase["endAt"], resumed)
            assert again == resumed and new == []
            archived = checked(root/"results"/(symbol+".json"))
            expected = [r for r in archived["records"] if r["entry"]["model"] == "swing_zone"]
            assert expected == full["records"]
            # Prepared future generation starts without retroactive positions.
            frozen = checked(root/"signals"/(symbol+"-swing_zone.json"))["state"]
            future, messages = observe(dataset, frozen["startAt"], phase["endAt"], phase["endAt"], seed=frozen)
            assert future["records"] == [] and messages == []
            save(root/"forward-ready"/(symbol+".json"), future)
            proof.append({"symbol": symbol, "records": len(full["records"]),
                          "newEventsAfterResume": len(events), "journalEvents": len(full["journal"]),
                          "recordsHash": digest(full["records"]), "quietRepeat": True,
                          "archiveMatched": True, "futureGenerationStartsFlat": True})
            print(json.dumps(proof[-1]), flush=True)
    output = {"contractHash": digest(contract), "examples": proof,
              "meaning": "Historical technical continuation proof, not live forward performance or a running service."}
    save(root/"resume-proof.json", output)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True)
    p.add_argument("--archive", required=True)
    p.add_argument("--data", required=True)
    a = p.parse_args()
    run(a.root, a.archive, a.data)
