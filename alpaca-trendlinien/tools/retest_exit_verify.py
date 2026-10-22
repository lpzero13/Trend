"""Independent stop/Decimal oracle and reuse of the separate cash-ledger auditor."""
from bisect import bisect_right
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datasets import read_dataset, source_bars, digest
from lab_data import session_bounds
from lab_splits import sessions_between
from models import NY
from strategy_verify import grid, audit_portfolio
from strategy_research import write_json


def read(path):
    return json.loads(path.read_text("utf-8"))


def checked(path):
    data = read(path)
    assert data["checksum"] == digest({k:v for k,v in data.items() if k != "checksum"})
    return data


def close(a, b):
    assert abs(float(a)-float(b)) <= max(1e-7, abs(float(b))*1e-9), (a,b)


def volatility(rows):
    return sum(max(b.high-b.low, abs(b.high-a.close), abs(b.low-a.close)) for a,b in zip(rows[-15:-1], rows[-14:]))/14 if len(rows) >= 15 else None


def audit_record(record, sources, end):
    entry, contract = record["entry"], record["contract"]
    four, fine = sources["4h"], {b.time:b for b in sources["5m"]}
    at = entry["entryAt"]
    n = bisect_right([b.end for b in four], entry["signalAt"])
    vol = volatility(four[:n])
    close(contract["initialStop"], entry["rawSafety"]-max(.01, vol*.25))
    close(contract["initialStop"], entry["initialStop"])
    # Independent causal history check, including the 15-bar ATR prefix.
    start = min(entry["red"]["a_time"], entry["green"]["a_time"], four[n-15].time)
    expected_source = set()
    lo, hi = [str(datetime.fromtimestamp(t, NY).date()) for t in (start, entry["signalAt"])]
    for day in sessions_between(lo, hi):
        opened, closed = session_bounds(day)
        expected_source.update((t,min(t+14400,closed)) for t in range(opened,closed,14400)
                               if start <= t and min(t+14400,closed) <= entry["signalAt"])
    actual_source = {(b.time,b.end) for b in four if b.end <= entry["signalAt"]}
    assert record["history"]["complete"] == (expected_source <= actual_source)
    day = datetime.fromtimestamp(at, NY).date()
    days = sessions_between(str(day+timedelta(days=1)), str(day+timedelta(days=80)))
    planned = session_bounds(days[9])[1]
    assert record["calendarFits"] == (planned <= end)
    assert record["fullHorizonPath"] == (planned <= end and all(t in fine for t in grid(at,planned)))
    for model, reported in record["paths"].items():
        assert reported["plannedTimeExit"] == planned
        stop, ray, peak = contract["initialStop"], dict(entry["green"]), contract["referenceHigh"]
        j = bisect_right([b.end for b in four], at)
        events, expected, missing = [], None, None
        for stamp in grid(at,min(planned,end)):
            if stamp not in fine:
                missing = stamp
                break
            b = fine[stamp]
            assert stamp != at or b.open == entry["entryPrice"]
            while j < len(four) and four[j].end+300 <= stamp:
                current, z = four[j], j-2
                old_level = ray["a_price"]+ray["slope"]*(j-ray["a_index"])
                if model == "higher_low_stop" and current.close >= old_level and z >= 2 and four[z].time > at and four[z].time > ray["b_time"]:
                    a, low = ray["b_index"], four[z].low
                    neighbors = [four[k].low for k in range(z-2,z+3)]
                    highs = [four[k].high for k in range(a+1,z) if four[k].time >= at]
                    if neighbors.count(low) == 1 and low == min(neighbors) and low > four[a].low and highs and max(highs) > peak:
                        slope = (low-four[a].low)/(z-a)
                        level = four[a].low+slope*(j-a)
                        valid = all(four[k].low+1e-7 >= four[a].low+slope*(k-a) for k in range(a,j+1))
                        vol = volatility(four[:j+1])
                        if valid and old_level+.01 < level < current.close and vol is not None:
                            new_ray = {"basis":"bars","a_index":a,"b_index":z,"a_time":four[a].time,"b_time":four[z].time,
                                       "a_price":four[a].low,"b_price":low,"slope":slope,"valid":True,"confirmedAt":current.end}
                            new_stop = max(stop,low-max(.01,.25*vol))
                            events.append({"kind":"safety_replace","knownAt":current.end,"effectiveAt":stamp,
                                "previousRay":dict(ray),"ray":new_ray,"previousHardStop":stop,"hardStop":new_stop,
                                "higherHigh":max(highs),"atr":vol})
                            stop, ray, peak = new_stop, new_ray, max(highs)
                j += 1
            if b.open <= stop:
                expected = (b,b.open,"hard_stop_gap",True)
            elif b.low <= stop:
                expected = (b,stop,"hard_stop",False)
            elif b.end == planned:
                expected = (b,b.close,"time",False)
            if expected:
                break
        assert len(events) == len(reported["events"])
        for a,b in zip(events,reported["events"]):
            assert set(a) == set(b)
            for key,value in a.items():
                if type(value) in (int,float):
                    close(value,b[key])
                else:
                    assert value == b[key]
        if expected is None:
            assert reported["status"] == "censored"
            if missing is not None:
                assert reported["reason"] == "missing_fine_path" and reported["missingAt"] == missing
            else:
                assert reported["reason"] == "phase_boundary" and planned > end
            continue
        b,price,reason,at_open = expected
        assert reported["status"] == "closed" and reported["fillBarAt"] == b.time and reported["exitAt"] == b.end
        assert reported["exitReason"] == reason and reported["atOpen"] == at_open
        close(reported["exitPrice"], price)
        costs = contract["costs"]
        side = Decimal(str(costs["spread_bps"]))/20000+Decimal(str(costs["slippage_bps"]))/10000
        buy = Decimal(str(entry["entryPrice"]))*(1+side)
        sell = Decimal(str(price))*(1-side)
        quantity = (Decimal(str(costs["notional"]))-Decimal(str(costs["fee_per_order"])))/buy
        pnl = quantity*(sell-buy)-2*Decimal(str(costs["fee_per_order"]))
        close(reported["netPnl"],pnl)
        close(reported["netReturnPct"],pnl/Decimal(str(costs["notional"]))*100)
        close(reported["netR"],pnl/(quantity*(buy-Decimal(str(contract["initialStop"])))))


def run(root, data):
    root = Path(root).resolve()
    os.environ["TORI_DATA_DIR"] = str(Path(data).resolve())
    contract = read(root/"contract.json")
    code = Path(__file__).resolve().parents[1]
    assert all(hashlib.sha256((code/name).read_bytes()).hexdigest() == value for name,value in contract["engine"].items())
    counts = {"records":0,"paths":0,"portfolios":0,"raiseEvents":0}
    for stage,phase in contract["phases"].items():
        results = checked(root/(stage+"-results.json"))
        records, sources = [], {}
        with patch("alpaca._request", side_effect=AssertionError("Verifier is offline")):
            for file in sorted((root/stage).glob("*.json")):
                block = checked(file)
                assert block["contractHash"] == digest(contract)
                for record in block["records"]:
                    identity = record["entry"]["datasetId"]
                    if identity not in sources:
                        source = source_bars(read_dataset(identity))
                        sources[identity] = {tf:[b for b in rows if b.end <= phase["endAt"]] for tf,rows in source.items()}
                    audit_record(record,sources[identity],phase["endAt"])
                    records.append(record)
                    counts["records"] += 1
                    counts["paths"] += 2
                    counts["raiseEvents"] += len(record["paths"]["higher_low_stop"]["events"])
            for key,portfolio in results["portfolios"].items():
                geometry,model = key.split("/")
                selected = [r for r in records if r["entry"]["model"] == geometry and r["history"]["complete"] and r["calendarFits"]]
                audit_portfolio(portfolio,[r["entry"] for r in selected],[r["paths"][model] for r in selected],sources,phase,contract["costs"])
                counts["portfolios"] += 1
        for key,group in results["groups"].items():
            geometry,quality = key.split("/")
            selected = [r for r in records if r["entry"]["model"] == geometry and r["history"]["complete"] == (quality == "complete_history") and r["calendarFits"]]
            assert len(selected) == group["cases"]
            for model in ("fixed","higher_low_stop"):
                closed = [r["paths"][model] for r in selected if r["paths"][model]["status"] == "closed"]
                actual = group["models"][model]
                assert len(closed) == actual["closed"]
                if closed:
                    close(actual["meanR"],sum(Decimal(str(p["netR"])) for p in closed)/len(closed))
    output = {"contractHash":digest(contract),"verified":counts,
        "verifierHash":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "meaning":"Model arithmetic, source timing and cash/risk consistency; not live execution proof or independent market replication."}
    write_json(root/"verification.json",output)
    print(json.dumps(output))


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",required=True)
    p.add_argument("--data",required=True)
    args = p.parse_args()
    run(args.root,args.data)
