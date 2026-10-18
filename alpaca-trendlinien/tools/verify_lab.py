"""Isolated, offline end-to-end lab verification and resource measurements.

Synthetic regular-session stocks only. This does not measure strategy returns
on market data or prove production capacity. No credentials/provider calls.
"""
import argparse
from datetime import datetime
import json
import math
import os
from pathlib import Path
import sys
import threading
import time
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from benchmark_research import peak_rss_bytes


def fixtures(symbol):
    from models import Bar
    from lab_data import NORMALIZATION, resample_regular, session_bounds
    from lab_splits import sessions_between
    from datasets import save_dataset
    days=sessions_between("2023-01-03","2025-01-03");fine=[]
    scale=1 if symbol=="SYNTHA" else 1.3
    for i,day in enumerate(days):
        opened,closed=session_bounds(day)
        for j,stamp in enumerate(range(opened,closed,300)):
            x=i+j/78
            price=lambda x:scale*(110+12*math.sin(x/27)+3*math.sin(x/3.7)+.006*x)
            a,b=price(x),price(x+1/78)
            fine.append(Bar(stamp,stamp+300,a,max(a,b)+.04*scale,min(a,b)-.04*scale,b,100))
    sources,quality=resample_regular(fine)
    metadata={"feed":"iex","adjustment":"split","normalization":NORMALIZATION,"mode":"synthetic-offline-fixture",
              "fetchedAt":"2025-01-04T00:00:00Z","quality":{"rejected":0},"warning":None,"rthQuality":quality}
    identity=save_dataset(symbol,{tf:(bars,metadata) for tf,bars in sources.items()},adjustment="split",session="XNYS regular; synthetic fixture",data_kind="synthetic")
    return identity,{tf:len(rows) for tf,rows in sources.items()}


def verify(output):
    import jobs
    from lab_api import post
    import lab_registry as registry
    import lab_reviews as reviews
    from maintenance import backup, verify as verify_backup, restore
    from database import connection
    from storage import cleanup_preview
    started=time.perf_counter();phases=[]
    def worker(identity,expected="succeeded"):
        before=time.perf_counter();jobs.worker_loop(threading.Event(),once=True)
        value=jobs.get_job(identity)
        if value["status"]!=expected:raise AssertionError(f"{value['spec']['lab']['stage']}: {value['status']}: {value['error']}")
        phases.append({"stage":value["spec"]["lab"]["stage"],"status":value["status"],"seconds":time.perf_counter()-before,
                       "cases":value["completedTrials"],"events":value["eventCount"],"peakRssBytes":peak_rss_bytes()})
        print(json.dumps(phases[-1]),flush=True)
        return value
    os.environ.update(TORI_DATA_DIR=str(output/"data"),TORI_AUTO_ENABLED="0")
    with patch("alpaca._request",side_effect=AssertionError("Offline verification must never call a provider")):
        jobs.schedule({"enabled":False,"spec":{}})
        ids={};counts={}
        for symbol in ("SYNTHA","SYNTHB"):ids[symbol],counts[symbol]=fixtures(symbol)
        spec={"entry_mode":"lab","symbols":list(ids),"dataset_ids":ids,"latency_seconds":300,
              "lab":{"benchmark_symbol":"","profiles":["reference","baseline","retest_hold"],"bootstrap_samples":50,
                     "hypothesis":"Synthetic technical verification; no market-data or human-labelled performance claim.",
                     "primary_metric":"median_return_pct","walk_train_sessions":60,"walk_test_sessions":60,"min_train_events":1,
                     "execution":{"enabled":True,"holding_days":5}}}
        initial=jobs.submit(spec);experiment_id=initial["spec"]["lab"]["experiment_id"]
        development=worker(initial["id"])
        report_start=time.perf_counter();report=jobs.report(initial["id"],limit=25);report_ms=(time.perf_counter()-report_start)*1000
        if not report["summary"]["sections"].get("development",{}).get("uniqueTimesAcrossProfiles",0):raise AssertionError("Synthetic test needs actual observed signals")
        pack=reviews.create(initial["id"],count=12,seed=17,profile="baseline")
        first=pack["cases"][0]["id"];blind=reviews.view(pack["id"],first)
        if "engine" in blind or any(b["end"]>blind["cutoff"] for rows in blind["bars"].values() for b in rows):raise AssertionError("Blindness violation")
        label={"entry":"wait","red":None,"green":None,"reason":"Automated synthetic integration test, not a human judgement"}
        reviews.label(pack["id"],first,label);reviews.reveal(pack["id"],first)
        label["entry"]="no";reviews.label(pack["id"],first,label)
        if reviews.compare(pack["id"])["counts"]["tainted"]!=1:raise AssertionError("Post-reveal edits must be excluded")
        validation=post(f"/api/lab/experiments/{experiment_id}/run",{"stage":"validation"})[0];worker(validation["id"])
        registry.seal(experiment_id,"baseline","Predefined technical-test candidate; not selected by final outcomes")
        final=post(f"/api/lab/experiments/{experiment_id}/run",{"stage":"holdout","confirm_final_test":True})[0];worker(final["id"])
        final_report=jobs.report(final["id"],limit=1)
        if any(g["profile"]!="baseline" for s in final_report["summary"]["sections"].values() for g in s["groups"].values()):raise AssertionError("Final test evaluated an unsealed profile")
        repeated=post(f"/api/lab/experiments/{experiment_id}/run",{"stage":"holdout","confirm_final_test":True})[0];worker(repeated["id"],"failed")
        walk=post(f"/api/lab/experiments/{experiment_id}/run",{"stage":"walk_forward"})[0];worker(walk["id"])
        walk_report=jobs.report(walk["id"],limit=1)
        if not walk_report["summary"]["walkSelections"]:raise AssertionError("No fold selections recorded")
        with connection() as db:
            for row in db.execute("SELECT result FROM trials WHERE job_id=?",(walk["id"],)):
                case=json.loads(row[0])
                for entry in case["variants"]:
                    for result in entry.get("forward",{}).values():
                        if result.get("complete") and result["closedAt"]>=registry.get(experiment_id)["plan"]["phases"]["holdout"]["startAt"]:raise AssertionError("Walk-forward reached holdout labels")
        if cleanup_preview()["candidates"]:raise AssertionError("Referenced data proposed for cleanup")
        snapshot=output/"backup";backup(snapshot);verify_backup(snapshot);restore(snapshot,output/"restored")
        with patch.dict(os.environ,{"TORI_DATA_DIR":str(output/"restored")}):
            if not registry.get(experiment_id)["finalOpened"]:raise AssertionError("Final access lost on restore")
            if not reviews.view(pack["id"],first)["tainted"]:raise AssertionError("Review state lost on restore")
        output_report={"synthetic":True,"productionCapacityProven":False,"providerCalls":0,"experimentId":experiment_id,"developmentJob":development["id"],
                       "reviewPack":pack["id"],"sourceCounts":counts,"phases":phases,"seconds":time.perf_counter()-started,"peakRssBytes":peak_rss_bytes(),
                       "firstReportMilliseconds":report_ms,"reportPageBytes":len(json.dumps(report).encode()),"backupRestoreVerified":True,
                       "groups":report["summary"]["sections"]["development"]["groups"],"walkSelections":walk_report["summary"]["walkSelections"]}
        (output/"verification.json").write_text(json.dumps(output_report,ensure_ascii=False,indent=2),"utf-8")
        return {k:v for k,v in output_report.items() if k not in ("groups","walkSelections")}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",required=True);args=parser.parse_args()
    output=Path(args.output).expanduser().resolve()
    if output.exists():parser.error("Output must be a new directory; existing runtime data is never overwritten")
    output.mkdir(parents=True)
    print(json.dumps(verify(output),indent=2))


if __name__=="__main__":main()
