"""Independent event/Decimal/cash verification of the frozen time audit."""
import argparse
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datasets import read_dataset, source_bars, digest
from strategy_verify import audit_portfolio
from strategy_research import write_json
from tools.retest_exit_verify import checked, read, audit_record, close
from tools.retest_variant_verify import audit_variant


def verify(root, data):
    root = Path(root).resolve()
    os.environ["TORI_DATA_DIR"] = str(Path(data).resolve())
    contract = read(root/"contract.json")
    phase = contract["phase"]
    code = Path(__file__).resolve().parents[1]
    assert all(hashlib.sha256((code/n).read_bytes()).hexdigest() == v for n, v in contract["engine"].items())
    frozen, result = checked(root/"signals-frozen.json"), checked(root/"results.json")
    assert result["signalsHash"] == frozen["checksum"] and result["contractHash"] == frozen["contractHash"] == digest(contract)
    sources, records, events = {}, [], 0
    with patch("alpaca._request", side_effect=AssertionError("Offline verification")):
        for symbol in contract["symbols"]:
            identity = contract["datasets"][symbol]["id"]
            sources[identity] = {tf: [b for b in bars if b.end <= phase["endAt"]]
                                 for tf, bars in source_bars(read_dataset(identity)).items()}
            block = checked(root/"results"/(symbol+".json"))
            assert block["contractHash"] == digest(contract)
            expected = []
            for model in contract["models"]:
                key = symbol+"-"+model
                signal = checked(root/"signals"/(key+".json"))
                assert signal["checksum"] == frozen["blocks"][key]
                expected.extend(signal["entries"])
            assert [r["entry"] for r in block["records"]] == expected
            for r in block["records"]:
                e = r["entry"]
                four = sources[identity]["4h"]
                assert phase["startAt"] <= e["entryAt"] <= phase["endAt"]
                assert four[e["signalIndex"]].end == e["signalAt"] < e["entryAt"]
                assert max(e["red"]["b_time"], e["green"]["b_time"]) < e["signalAt"]
                audit_record({**r, "paths": {"fixed": r["paths"]["fixed"]}}, sources[identity], phase["endAt"])
                audit_variant(r, sources[identity], phase["endAt"], "atr_gain_stop")
                records.append(r)
                events += len(r["paths"]["atr_gain_stop"]["events"])
        for key, book in result["portfolios"].items():
            model, variant = key.split("/")
            chosen = [r for r in records if r["entry"]["model"] == model and r["history"]["complete"] and r["calendarFits"]]
            audit_portfolio(book, [r["entry"] for r in chosen], [r["paths"][variant] for r in chosen], sources, phase, contract["costs"])
        for key, group in result["groups"].items():
            model, quality = key.split("/")
            rows = [r for r in records if r["entry"]["model"] == model and r["calendarFits"] and
                    r["history"]["complete"] == (quality == "complete_history")]
            assert len(rows) == group["cases"]
            paired = [r for r in rows if all(r["paths"][v]["status"] == "closed" for v in contract["exits"])]
            assert len(paired) == group["pairedClosed"]
            if paired:
                close(group["meanDeltaR"], sum(Decimal(str(r["paths"]["atr_gain_stop"]["netR"]))-Decimal(str(r["paths"]["fixed"]["netR"])) for r in paired)/len(paired))
            for variant in contract["exits"]:
                closed = [r["paths"][variant] for r in rows if r["paths"][variant]["status"] == "closed"]
                assert len(closed) == group["models"][variant]["closed"]
                if closed:
                    close(group["models"][variant]["meanR"], sum(Decimal(str(p["netR"])) for p in closed)/len(closed))
    output = {"contractHash": digest(contract), "records": len(records), "paths": 2*len(records),
              "exitEvents": events, "portfolios": len(result["portfolios"]),
              "verifierHash": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "meaning": "Independent model arithmetic/timing and ledger verification. Does not establish future profitability."}
    write_json(root/"verification.json", output)
    print(json.dumps(output))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True)
    p.add_argument("--data", required=True)
    a = p.parse_args()
    verify(a.root, a.data)
