"""Frozen prospective observation: register, run locally, inspect, stop."""
import argparse
import json
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from forward_watch import register, worker, status, stop, get_run, events_page

SYMBOLS = "AAPL,ADBE,AMD,AMZN,AVGO,BAC,CAT,COST,CVX,GOOGL,GS,HD,JNJ,JPM,KO,MA,META,MSFT,NVDA,ORCL,PG,UNH,V,WMT,XOM"


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command",choices=("init","run","status","stop","events"))
    p.add_argument("--id")
    p.add_argument("--symbols",default=SYMBOLS)
    p.add_argument("--once",action="store_true")
    p.add_argument("--after",type=int,default=0)
    p.add_argument("--limit",type=int,default=100)
    a = p.parse_args()
    # Separate process: conservative provider budget, not a broker connection.
    os.environ.setdefault("TORI_API_REQUESTS_PER_MINUTE","40")
    if a.command == "init":
        result = {"id":register(a.symbols.split(",")),"registered":True}
    elif a.command == "status":
        result = status()
    else:
        identity = a.id or get_run()["id"]
        if a.command == "run":
            worker(identity,once=a.once)
            result = status()
        elif a.command == "events":
            result = events_page(identity,after=a.after,limit=a.limit)
        else:
            result = stop(identity)
    print(json.dumps(result,ensure_ascii=False,allow_nan=False))
