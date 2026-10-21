"""Independent arithmetic/path checks plus known-prefix blind/stability packages."""
import argparse
from bisect import bisect_left, bisect_right
from collections import Counter
from copy import deepcopy
from datetime import datetime, timedelta
from decimal import Decimal
import json
import os
from pathlib import Path
import random
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datasets import read_dataset, source_bars, digest
from entry_geometry import Geometry, MODELS
from entry_watch import WatchReplay, engine_signature
from entry_blind import blind_case, candle_svg, stability, compare_reviews
from lab_data import session_bounds
from lab_splits import sessions_between
from models import NY
from strategy_research import write_json


def read(path):
    return json.loads(path.read_text("utf-8"))


def close(a, b):
    assert abs(a-b) <= max(1e-8, abs(b)*1e-10), (a, b)


def slots(start, end):
    """Independent calendar iteration (does not call expected_grid/evaluate)."""
    lo = str(datetime.fromtimestamp(start, NY).date())
    hi = str(datetime.fromtimestamp(end, NY).date())
    for day in sessions_between(lo, hi):
        opened, closed = session_bounds(day)
        for t in range(opened, closed, 300):
            if start <= t and t+300 <= end:
                yield t


def source_slots(start, end, step):
    lo = str(datetime.fromtimestamp(start, NY).date())
    hi = str(datetime.fromtimestamp(end, NY).date())
    for day in sessions_between(lo, hi):
        opened, closed = session_bounds(day)
        for t in range(opened, closed, step):
            stop = min(t+step, closed)
            if start <= t and stop <= end:
                yield t, stop


def audit_entry(e, sources, phase, counts):
    four, fine = sources["4h"], sources["5m"]
    times = [b.time for b in fine]
    n = bisect_right([b.end for b in four], e["signalAt"])
    assert n >= 15 and four[n-1].end == e["signalAt"]
    assert phase["startAt"] <= e["entryAt"] <= phase["endAt"]
    assert e["entryAt"] >= e["signalAt"]+300
    expected = next(slots(e["signalAt"]+300, e["entryAt"]+300))
    assert e["entryAt"] == expected
    b = fine[bisect_left(times, expected)]
    assert b.time == expected
    close(e["entryPrice"], b.open)
    trs = [max(current.high-current.low, abs(current.high-previous.close), abs(current.low-previous.close))
           for previous, current in zip(four[n-15:n-1], four[n-14:n])]
    volatility = sum(trs)/14
    close(e["signalATR"], volatility)
    ray = e["green"]
    assert four[ray["b_index"]+2].end <= e["signalAt"]
    close(e["initialStop"], ray["a_price"]+ray["slope"]*(n-1-ray["a_index"])-max(.01, .25*volatility))
    assert 0 < e["initialStop"] < e["entryPrice"]
    expected_history = set(source_slots(min(e["red"]["a_time"], e["green"]["a_time"]), e["signalAt"], 14400))
    available_history = {(b.time, b.end) for b in four if b.end <= e["signalAt"]}
    counts["entriesWithCompleteSourceHistory"] += expected_history <= available_history
    risk = e["entryPrice"]-e["initialStop"]
    for h, outcome in e["forward"].items():
        if not outcome["complete"]:
            counts["incompleteOutcomes"] += 1
            continue
        assert outcome["closedAt"] <= phase["endAt"]
        target_day = outcome["targetDate"]
        target = next(b for b in sources["1D"] if str(datetime.fromtimestamp(b.time, NY).date()) == target_day)
        close(outcome["close"], target.close)
        price, end = Decimal(str(e["entryPrice"])), Decimal(str(target.close))
        close(outcome["return_pct"], float((end/price-1)*100))
        close(outcome["netPct"], float((end*Decimal('.99925')/(price*Decimal('1.00075'))-1)*100))
        path = fine[bisect_left(times, e["entryAt"]):bisect_right(times, outcome["closedAt"]-300)]
        actual = {b.time for b in path}
        complete = all(t in actual for t in slots(e["entryAt"], outcome["closedAt"]))
        assert complete == outcome["pathComplete"]
        if path:
            close(outcome["mfe_pct"], max(0, (max(b.high for b in path)/e["entryPrice"]-1)*100))
            close(outcome["mae_pct"], min(0, (min(b.low for b in path)/e["entryPrice"]-1)*100))
            stop = next((b.time for b in path if b.low <= e["initialStop"]), None)
            for multiple, key in ((1, "oneRBeforeSafety"), (2, "twoRBeforeSafety")):
                touch = next((b.time for b in path if b.high >= e["entryPrice"]+multiple*risk), None)
                expected_hit = None if not complete or touch is not None and touch == stop else touch is not None and (stop is None or touch < stop)
                assert outcome[key] == expected_hit
        controls = []
        for c in e["controls"]:
            a, d = datetime.fromtimestamp(e["entryAt"], NY), datetime.fromtimestamp(c["entryAt"], NY)
            assert (a.hour, a.minute, a.year, (a.month-1)//3) == (d.hour, d.minute, d.year, (d.month-1)//3)
            f = c["forward"][h]
            if f["complete"] and f.get("pathComplete") is True:
                ratio = Decimal(str(f["close"]))*Decimal('.99925')/(Decimal(str(c["entryPrice"]))*Decimal('1.00075'))
                controls.append(float((ratio-1)*100))
        assert len(controls) == outcome["controlCount"]
        if controls and complete:
            close(outcome["excessPct"], outcome["netPct"]-sum(controls)/len(controls))
        counts["checkedOutcomes"] += 1
    counts["checkedEntries"] += 1


def run(args):
    root, source = Path(args.root).resolve(), Path(args.source).resolve()
    contract = read(root/"contract.json")
    assert all(contract["engine"][name] == value for name, value in engine_signature().items())
    os.environ["TORI_DATA_DIR"] = str(source/"data")
    counts, quality, jitter, cases, private = Counter(), {}, {}, [], []
    blind = root/"blind"
    blind.mkdir(exist_ok=True)
    with patch("alpaca._request", side_effect=AssertionError("No provider access")):
        for symbol in contract["symbols"]:
            data = read_dataset(contract["datasets"][symbol]["id"])
            sources = source_bars(data)
            for stage, phase in contract["phases"].items():
                fine_slots = set(slots(phase["startAt"], phase["endAt"]))
                actual = {b.time for b in sources["5m"] if phase["startAt"] <= b.time and b.end <= phase["endAt"]}
                quality[symbol+"/"+stage] = {"fineExpected": len(fine_slots), "fineAvailable": len(actual & fine_slots),
                    "fineCoveragePct": 100*len(actual & fine_slots)/len(fine_slots)}
                for tf, step in (("4h", 14400), ("1D", 86400)):
                    expected = set(source_slots(phase["startAt"], phase["endAt"], step))
                    available = {(b.time, b.end) for b in sources[tf] if phase["startAt"] <= b.time and b.end <= phase["endAt"]}
                    quality[symbol+"/"+stage][tf+"CoveragePct"] = 100*len(expected & available)/len(expected)
                for model in MODELS:
                    path = root/stage/(symbol+"-"+model+".json")
                    if not path.exists():
                        continue
                    block = read(path)
                    assert block["checksum"] == digest({k: v for k, v in block.items() if k != "checksum"})
                    assert block["contractHash"] == digest(contract)
                    for e in block["observations"]:
                        audit_entry(e, sources, phase, counts)
                    assert len({m["eventKey"] for m in block["state"]["messages"]}) == len(block["state"]["messages"])
                    # Stored signal snapshots agree with the original candidate, not a later reselection.
                    by_id = {c["id"]: c for c in block["state"]["candidates"]}
                    for e in block["observations"]:
                        assert all(e["red"][k] == v for k, v in by_id[e["sourceSetupId"]]["ray"].items())
            dev = contract["phases"]["development"]
            indices = [i for i, b in enumerate(sources["4h"]) if dev["startAt"] <= b.end <= dev["endAt"]]
            chosen = random.Random("entry-prefix-1|"+symbol).sample(indices, min(4, len(indices)))
            for i in chosen:
                for model in MODELS:
                    jitter[symbol+"/"+model+"/"+str(i)] = stability(sources["4h"], symbol, model, i)
            if len(cases) < 24 and chosen:
                # One random prefix and one actual near-event prefix; no outcome-based selection.
                watch = read(root/"development"/(symbol+"-swing_zone.json"))["state"]
                near = [m["knownAt"] for m in watch["messages"] if m["state"] == "near" and dev["startAt"] <= m["knownAt"] <= dev["endAt"]]
                cutoffs = [sources["4h"][chosen[0]].end]
                if near:
                    cutoffs.append(random.Random("entry-near-blind|"+symbol).choice(near))
                for cutoff in dict.fromkeys(cutoffs):
                    known = [b for b in sources["4h"] if b.end <= cutoff]
                    suggestions = {model: Geometry(known, symbol, model).proposals(len(known)-1) for model in MODELS}
                    case, hidden = blind_case(symbol, known, cutoff, suggestions)
                    cases.append(case)
                    private.append(hidden)
                    (blind/(case["caseId"]+".svg")).write_text(candle_svg(known), "utf-8")
            if symbol in ("AAPL", "XOM"):
                # Genuine geometry, full replay vs a persisted earlier-stage checkpoint.
                val = contract["phases"]["validation"]
                for model in MODELS:
                    saved = read(root/"development"/(symbol+"-"+model+".json"))["state"]
                    full = WatchReplay(data, model, saved["startAt"], val["endAt"])
                    resumed = WatchReplay(data, model, saved["startAt"], val["endAt"])
                    resumed.restore(saved)
                    assert full.run() == resumed.run()
                    prefix = WatchReplay(data, model, saved["startAt"], dev["endAt"]).run()
                    changed = deepcopy(data)
                    for rows in changed["material"]["bars"].values():
                        for b in rows:
                            if b["end"] > dev["endAt"]:
                                b.update(open=1, high=10000, low=.01, close=9000)
                    assert prefix == WatchReplay(changed, model, saved["startAt"], dev["endAt"]).run()
                    counts["realPrefixResumeChecks"] += 1
            print(json.dumps({"checked": symbol, **counts}), flush=True)
    write_json(blind/"cases.json", cases)
    write_json(blind/"private-unblind.json", private)
    write_json(blind/"reviews-template.json", [{"caseId": c["caseId"], **c["review"]} for c in cases])
    report = {"counts": dict(counts), "quality": quality, "stability": jitter, "blindCases": len(cases),
              "humanReview": "pending: no human ratings invented", "contractHash": digest(contract)}
    if args.reviews:
        report["humanReview"] = compare_reviews(cases, private, read(Path(args.reviews)))
    write_json(root/"verification.json", report)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--reviews")
    run(p.parse_args())
