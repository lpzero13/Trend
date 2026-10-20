"""Inspect pinned RTH coverage by declared phase, without prices/outcomes.

Missing IEX slots are absence of bars, not proof that Alpaca lost observations:
there may have been no eligible IEX prints. No interpolation or data repair.
"""
import argparse
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def inspect(root):
    root = Path(root).resolve()
    os.environ["TORI_DATA_DIR"] = str(root/"data")
    from datasets import read_dataset
    from lab_data import session_bounds
    from lab_splits import sessions_between
    from models import NY
    contract = json.loads((root/"universe-contract.json").read_text("utf-8"))
    imports = json.loads((root/"imports.json").read_text("utf-8"))
    results = []
    for symbol, item in sorted(imports.items()):
        data = read_dataset(item["id"])
        bars = data["material"]["bars"]
        first = datetime.fromtimestamp(bars["4h"][0]["time"], NY).date()+timedelta(days=365)
        ready = int(datetime.combine(first, datetime.min.time(), NY).timestamp())
        for stage, phase in contract["phases"].items():
            sessions = sessions_between(phase["startDate"], phase["endDate"])
            expected_fine = sum((session_bounds(d)[1]-session_bounds(d)[0])//300 for d in sessions)
            expected_four = sum((session_bounds(d)[1]-session_bounds(d)[0]+14399)//14400 for d in sessions)
            count = lambda tf: sum(phase["startAt"] <= b["time"] and b["end"] <= phase["endAt"] for b in bars[tf])
            actual_fine, actual_four, daily = count("5m"), count("4h"), count("1D")
            results.append({"symbol": symbol, "datasetId": item["id"], "stage": stage,
                "fineBars": actual_fine, "expectedFineSlots": expected_fine,
                "fineCoveragePct": actual_fine/expected_fine*100,
                "fourBars": actual_four, "expectedFourSlots": expected_four,
                "fourCoveragePct": actual_four/expected_four*100,
                "dailyBars": daily, "sessions": len(sessions), "dailyCoveragePct": daily/len(sessions)*100,
                "sourceHistoryReadyAt": ready, "historyReadyAfterPhaseStart": ready > phase["startAt"]})
    result = {"version": "safety-coverage-1", "stocksImported": len(imports), "rows": results,
              "meaning": "Counts versus declared XNYS regular-session grid. Not proof of missing provider messages or full-market liquidity; IEX may have no eligible prints. No future prices/returns and no interpolation."}
    (root/"data-quality.json").write_text(json.dumps(result, indent=2), "utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    result = inspect(parser.parse_args().root)
    print(json.dumps({"stocksImported": result["stocksImported"], "delayedHistorySymbols": sorted({r["symbol"] for r in result["rows"] if r["historyReadyAfterPhaseStart"]})}))
