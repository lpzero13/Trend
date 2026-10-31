"""Independent 5m replay and accounting checks for unbounded case studies."""
import argparse
from bisect import bisect_left, bisect_right
import json
import hashlib
from functools import lru_cache
import math
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datasets import read_dataset, source_bars
from event_case_study import checked, load_block, scan_episodes
from fan_execution import next_open_time
from fan_study import timestamp
from lab_metrics import expected_grid
from strategy_screen import read, write

next_open_time = lru_cache(maxsize=100000)(next_open_time)


def close(a, b):
    if a is None or b is None:
        assert a == b, (a, b)
    elif isinstance(a, (float, int)) and isinstance(b, (float, int)):
        assert math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-9), (a, b)
    else:
        assert a == b, (a, b)


def reference(case, fine, timeline, cutoff):
    """No segment-tree or recorded stop events: derive decisions bar by bar."""
    s, e = case["signal"], case["entry"]
    if e["status"] != "filled":
        return {}
    r = e["rules"]
    side = r["spread_bps"]/20000+r["slippage_bps"]/10000
    grid = list(expected_grid(e["entryAt"], cutoff+15*86400))
    fine_times = [b.time for b in fine]
    pos = bisect_left(fine_times, e["entryAt"])
    source_ends = [t["closedAt"] for t in timeline]
    ti0 = bisect_right(source_ends, e["entryAt"])
    source_missing = next((t["gapAt"] for t in timeline if t.get("gapAt") is not None and t["gapAt"] > e["entryAt"]), None)
    results = {}
    for model in case["paths"]:
        stop, ti, fi, pending = e["initialStop"], ti0, pos, []
        high, low = e["entryFill"], e["entryFill"]
        last = None
        updates = []
        for stamp in grid:
            if stamp+300 > cutoff:
                break
            if (source_missing is not None and source_missing <= stamp) or fi >= len(fine) or fine[fi].time != stamp or fine[fi].end != stamp+300:
                results[model] = {"status": "censored", "missingAt": min(source_missing, stamp) if source_missing is not None else stamp,
                                  "finalStop": stop, "mfeR": (high-e["entryFill"])/e["initialRisk"],
                                  "maeR": (low-e["entryFill"])/e["initialRisk"]}
                break
            bar = fine[fi]
            fi += 1
            while ti < len(timeline) and timeline[ti]["closedAt"] <= stamp:
                state = timeline[ti]
                ti += 1
                if model == "fixed":
                    continue
                line = s["safety"] if model == "original_safety" else state["green"]
                if not line or line["slope"] <= 0:
                    continue
                level = line["a_price"]+line["slope"]*(state["index"]-line["a_index"])
                if 0 < level < state["close"]:
                    candidate = math.floor(level*(1-r["buffer_pct"]/100)/r["tick"])*r["tick"]
                    if candidate > stop:
                        at = grid[bisect_left(grid, state["closedAt"]+r["latency_seconds"])]
                        pending.append((at, candidate))
            while pending and pending[0][0] <= stamp:
                _, raised = pending.pop(0)
                if raised > stop:
                    stop = raised
                    updates.append((stamp, raised))
            if bar.open <= stop or bar.low <= stop:
                at_open = bar.open <= stop
                raw = bar.open if at_open else stop
                sell = raw*(1-side)
                pnl = e["quantity"]*(sell-e["entryFill"])-2*r["fee_per_order"]
                results[model] = {"status": "closed", "reason": "stop_gap" if at_open else "stop",
                    "exitAt": bar.time if at_open else bar.end, "exitFill": sell, "netPnl": pnl,
                    "netR": pnl/e["plannedRisk"], "finalStop": stop,
                    "mfeR": (max(high, raw)-e["entryFill"])/e["initialRisk"],
                    "maeR": (min(low, raw)-e["entryFill"])/e["initialRisk"]}
                break
            high, low, last = max(high, bar.high), min(low, bar.low), bar
        else:
            raise AssertionError("No data boundary")
        if model not in results:
            results[model] = {"status": "open", "reason": "data_end", "exitAt": None,
                "lastObservedAt": last.end if last else e["entryAt"], "finalStop": stop,
                "mfeR": (high-e["entryFill"])/e["initialRisk"], "maeR": (low-e["entryFill"])/e["initialRisk"]}
    return results


def verify(root, samples_per_stock=2, prefix=False):
    root = Path(root)
    p = checked(read(root/"plan.json"))
    count = fills = paths = replayed = 0
    replay_ids = []
    all_ids, pairs = set(), set()
    rng = random.Random(20261031)
    for symbol in p["symbols"]:
        block = load_block(root, p, symbol)
        timeline = block["timeline"]
        states = {t["closedAt"]: t for t in timeline}
        cases = block["cases"]
        for c in cases:
            count += 1
            assert c["id"] not in all_ids
            all_ids.add(c["id"])
            s, e = c["signal"], c["entry"]
            key = (s["episodeId"], s["family"])
            assert key not in pairs
            pairs.add(key)
            assert s["line"]["knownAt"] < s["signalAt"]
            for ln in (s["line"], s.get("safety")):
                if ln:
                    assert ln["knownAt"] <= s["signalAt"]
                    assert all(v["known_at"] <= s["signalAt"] for v in ln.get("contactPoints", []))
            context = c["features"]["dailyLastClosed"]
            assert context is None or context["end"] <= s["signalAt"]
            if e["status"] != "filled":
                continue
            fills += 1
            r = e["rules"]
            side = r["spread_bps"]/20000+r["slippage_bps"]/10000
            assert e["entryAt"] == next_open_time(s["signalAt"]+r["latency_seconds"])
            close(e["entryFill"], e["entryPrice"]*(1+side))
            close(e["quantity"]*e["entryFill"]+r["fee_per_order"], r["notional"])
            close(e["plannedRisk"], e["quantity"]*(e["entryFill"]-e["initialStop"]*(1-side))+2*r["fee_per_order"])
            for model, path in c["paths"].items():
                paths += 1
                assert "horizon" not in path and "plannedTimeExit" not in path
                assert path["reason"] != "time"
                previous = e["initialStop"]
                for change in path["stopEvents"]:
                    assert model != "fixed"
                    t = states[change["knownAt"]]
                    ln = s["safety"] if model == "original_safety" else t["green"]
                    assert ln["id"] == change["lineId"] and ln["knownAt"] <= t["closedAt"]
                    level = ln["a_price"]+ln["slope"]*(t["index"]-ln["a_index"])
                    assert ln["slope"] > 0 and 0 < level < t["close"]
                    close(change["newStop"], math.floor(level*(1-r["buffer_pct"]/100)/r["tick"])*r["tick"])
                    assert change["newStop"] > previous
                    assert change["effectiveAt"] == next_open_time(change["knownAt"]+r["latency_seconds"])
                    if path["status"] == "closed":
                        assert change["effectiveAt"] <= path["fillBarAt"]
                    previous = change["newStop"]
                close(path["finalStop"], previous)
                if path["status"] == "closed":
                    assert e["entryAt"] <= path["exitAt"] <= p["outcomeCutoff"]
                    close(path["exitFill"], path["exitPrice"]*(1-side))
                    net = e["quantity"]*(path["exitFill"]-e["entryFill"])-2*r["fee_per_order"]
                    close(path["netPnl"], net)
                    close(path["netR"], net/e["plannedRisk"])
                    close(path["netReturnPct"], 100*net/e["plannedCash"])
                else:
                    assert path["status"] in ("open", "censored") and path["exitAt"] is None
                    assert path["netR"] is None and path["netPnl"] is None
        selected = rng.sample([c for c in cases if c["entry"]["status"] == "filled"],
                              min(samples_per_stock, sum(c["entry"]["status"] == "filled" for c in cases)))
        if selected or prefix:
            frames = source_bars(read_dataset(p["datasets"][symbol]))
            fine = [b for b in frames["5m"] if b.end <= p["outcomeCutoff"]]
            for c in selected:
                brute = reference(c, fine, timeline, p["outcomeCutoff"])
                for model, fields in brute.items():
                    for k, v in fields.items():
                        try:
                            close(c["paths"][model].get(k), v)
                        except AssertionError as exc:
                            raise AssertionError((symbol, c["id"], model, k, str(exc))) from exc
                    replayed += 1
                replay_ids.append(c["id"])
            if prefix:
                first = min(timestamp(f["start"]) for f in p["windows"])
                last = max(timestamp(f["end"], upper=True) for f in p["windows"])
                warm = first-p["warmupDays"]*86400
                rows = [b for b in frames["4h"] if b.time >= warm and b.end <= last]
                found = scan_episodes(symbol, rows, first, last)[0]
                expected = {c["signal"]["id"]: c["signal"] for c in cases}
                got = {s["id"]: s for s in found if any(block["eligibility"][f["name"]]
                    and timestamp(f["start"]) <= s["signalAt"] <= timestamp(f["end"], upper=True) for f in p["windows"])}
                assert expected == got, "Future bars changed frozen episode signals"
        print(json.dumps({"verifiedStock": symbol, "cases": len(cases), "replayedPaths": replayed}), flush=True)
    result = {"planId": p["id"], "passed": True, "cases": count, "fills": fills,
              "accountedPaths": paths, "independent5mReplays": replayed,
              "futurePrefixChecked": prefix, "samplesPerStock": samples_per_stock,
              "replayedCaseIds": replay_ids, "sampleSeed": 20261031,
              "verifierSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    write(root/"verification.json", result)
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root")
    ap.add_argument("--samples-per-stock", type=int, default=2)
    ap.add_argument("--prefix", action="store_true")
    args = ap.parse_args()
    print(json.dumps(verify(args.root, args.samples_per_stock, args.prefix)), flush=True)
