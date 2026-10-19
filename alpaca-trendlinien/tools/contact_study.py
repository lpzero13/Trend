"""Reproducible code-only contact experiments on pinned real datasets.

Run each development round before changing the next rule. Never opens holdout.
Runtime artifacts and datasets stay outside Git. No provider access during scans.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import statistics
import sys
import threading
import time
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def statistics_for(points):
    result={}
    for h in (5,10,20):
        valid=[p for p in points if p.get("forward",{}).get(str(h),{}).get("complete")]
        values=[p["forward"][str(h)]["return_pct"] for p in valid]
        excess=[]
        for p in valid:
            control=[c["forward"][str(h)]["return_pct"] for c in p.get("controls",[]) if c.get("forward",{}).get(str(h),{}).get("complete")]
            if control:excess.append(p["forward"][str(h)]["return_pct"]-statistics.mean(control))
        result[str(h)]={"n":len(valid),"incomplete":len(points)-len(valid),"positive":sum(v>0 for v in values),
            "negative":sum(v<0 for v in values),"flat":sum(v==0 for v in values),
            "positive_pct":100*sum(v>0 for v in values)/len(values) if values else None,
            "mean_pct":statistics.mean(values) if values else None,"median_pct":statistics.median(values) if values else None,
            "matched_n":len(excess),"mean_excess_pct":statistics.mean(excess) if excess else None}
    return result


def extract(job_id):
    from database import connection
    points={};pairs={};contacts=Counter();zones=[];seen=set()
    with connection() as db:
        for row in db.execute("SELECT result FROM trials WHERE job_id=? ORDER BY id",(job_id,)):
            c=json.loads(row[0]);profile=c["profile"]
            pairs.setdefault(profile,{})[c["sourceSetupId"]]={"frozen":c["frozen"],"measurement":c.get("contactMeasurement")}
            for e in c["variants"]:
                if profile=="zone_measure" and e["variant"]=="breakout" and e.get("inPhase") and e.get("checks"):
                    # Structural rejection can retain the variant's armed timestamp.
                    # The measured contacts belong to the actual red-break candle.
                    break_at=c["signal"]["closedAt"]
                    k=(c["sourceSetupId"],break_at)
                    if k not in seen:
                        seen.add(k);m={v["name"]:v.get("value") for v in e["checks"]}
                        contacts[str((m.get("red_contacts"),m.get("green_contacts"),m.get("zone_red_contacts"),m.get("zone_green_contacts")))]+=1
                        zones.append({"sourceSetupId":c["sourceSetupId"],"symbol":c["symbol"],"signalAt":break_at,
                                      "centRed":m.get("red_contacts"),"centGreen":m.get("green_contacts"),
                                      "zoneRed":m.get("zone_red_contacts"),"zoneGreen":m.get("zone_green_contacts"),
                                      "measurement":c.get("contactMeasurement")})
                if e["status"]!="observed" or not e.get("inPhase"):continue
                identity=(c["symbol"],e["entryAt"])
                points.setdefault(profile,{}).setdefault(e["variant"],{}).setdefault(identity,{
                    "symbol":c["symbol"],"datasetId":c["datasetId"],"entryAt":e["entryAt"],"entryPrice":e["entryPrice"],
                    "signalAt":e["signalAt"],"initialStop":e["initialStop"],"quality":e["quality"],
                    "checks":e.get("checks",[]),"executionChecks":e.get("executionChecks",[]),
                    "forward":e.get("forward",{}),"controls":e.get("controls",[]),"sourceSetupId":c["sourceSetupId"]})
    isolation={}
    if "zone_measure" in pairs:
        a,b=pairs.get("baseline",{}),pairs["zone_measure"]
        isolation={"comparedPairs":len(a),"sameSourcePairs":a.keys()==b.keys(),
                   "sameAnchors":all(k in b and v["frozen"]==b[k]["frozen"] for k,v in a.items()),
                   "sameEntryTimes":all(points.get("baseline",{}).get(f,{ }).keys()==points.get("zone_measure",{}).get(f,{}).keys() for f in ("breakout","horizontal","retest"))}
        if not all(isolation[k] for k in ("sameSourcePairs","sameAnchors","sameEntryTimes")):
            raise AssertionError("Measurement-only experiment changed geometry or accepted times")
    return points,contacts,zones,isolation


def export(job,root,label):
    import jobs
    points,contacts,zones,isolation=extract(job["id"])
    rows=[]
    for profile in job["spec"]["lab"]["profiles"]:
        for family in ("breakout","horizontal","retest"):
            pool=points.get(profile,{}).get(family,{})
            base=points.get("baseline",{}).get(family,{})
            added=[p for k,p in pool.items() if k not in base]
            rows.append({"profile":profile,"family":family,"unique":len(pool),"added_vs_baseline":len(added),
                         "removed_vs_baseline":len(set(base)-set(pool)),"horizons":statistics_for(list(pool.values())),
                         "added_horizons":statistics_for(added),
                         "stocks":{s:{"unique":len(v:=[p for p in pool.values() if p["symbol"]==s]),"horizons":statistics_for(v)} for s in job["spec"]["symbols"]}})
    report=jobs.report(job["id"],limit=1)
    result={"version":"contact-study-1","jobId":job["id"],"experimentId":job["spec"]["lab"]["experiment_id"],
            "manifest":job["manifest"],"spec":job["spec"],"rows":rows,"summary":report["summary"],
            "contactPairs":dict(contacts),"contactObservations":zones,"isolation":isolation,
            "uniqueStockTimes":{p:len(set().union(*(set(v) for v in families.values()))) for p,families in points.items()},
            "points":{p:{f:list(v.values()) for f,v in families.items()} for p,families in points.items()},
            "meaning":"Raw USD close changes after 5/10/20 XNYS sessions strictly after entry date; no exits, fees or portfolio profit. All hypotheses selected on development; validation separate; holdout unopened."}
    (root/(label+".json")).write_text(json.dumps(result,indent=2,allow_nan=False),"utf-8")
    for r in rows:
        print(json.dumps({"profile":r["profile"],"family":r["family"],"n":r["unique"],"horizons":r["horizons"]}),flush=True)
    return result


def run(args):
    root=Path(args.root).resolve();root.mkdir(parents=True,exist_ok=True)
    os.environ.update(TORI_DATA_DIR=str(root/"data"),TORI_AUTO_ENABLED="0")
    import jobs
    label="round-"+str(args.round)+( "-validation" if args.validation else "")
    contract_path=root/(label+".contract.json")
    if contract_path.exists():raise ValueError("Contract already exists; inspect its saved job rather than silently rerunning")
    imports=json.loads((root/"imports.json").read_text("utf-8"))
    if any("id" not in v for v in imports.values()) or set(imports)!={"MSFT","AMZN","JPM","XOM","KO"}:raise ValueError("Five successful pinned real imports required")
    from datasets import read_dataset, data_kind
    from lab_data import require_convention
    for symbol,item in imports.items():
        data=read_dataset(item["id"]);material=data["material"]
        if material["symbol"]!=symbol or data_kind(data)!="market" or material["feed"]!="iex" or material["adjustment"]!="split":
            raise ValueError("Real pinned split-adjusted IEX datasets required; synthetic or mismatched inputs rejected")
        require_convention(data)
    if args.validation:
        prior=json.loads((root/("round-"+str(args.round)+".json")).read_text("utf-8"))
        decision=json.loads((root/"candidate-before-validation.json").read_text("utf-8"))
        if not decision.get("decisionBeforeValidation") or decision.get("developmentJob")!=prior["jobId"]:
            raise ValueError("Freeze the development selection before opening validation")
        contract_decision=decision
        spec=prior["spec"];spec["lab"]["stage"]="validation"
    else:
        spec={"entry_mode":"lab","symbols":list(imports),"dataset_ids":{s:v["id"] for s,v in imports.items()},
              "history_days":900,"seed":20261019,"horizons":[5,10,20],"latency_seconds":300,
              "lab":{"profiles":args.profiles.split(","),"benchmark_symbol":"","bootstrap_samples":100,
                     "variant_budget":20,"hypothesis":args.hypothesis,"primary_family":"breakout","primary_horizon":10,"primary_metric":"mean_excess_pct"}}
    contract={"createdAt":datetime.now(timezone.utc).isoformat(),"round":args.round,"engineHash":jobs.engine_hash(),
              "spec":spec,"parentFinding":args.finding,"selection":"Only development results may motivate the next round; no holdout access"}
    if args.validation:contract["frozenDecision"]=contract_decision
    contract_path.write_text(json.dumps(contract,indent=2),"utf-8")
    start=time.monotonic()
    with patch("alpaca._request",side_effect=AssertionError("Pinned contact study must not fetch new provider data")):
        job=jobs.submit(spec)
        contract["jobId"]=job["id"];contract_path.write_text(json.dumps(contract,indent=2),"utf-8")
        print(json.dumps({"submitted":job["id"],"profiles":job["spec"]["lab"]["profiles"]}),flush=True)
        jobs.worker_loop(threading.Event(),once=True)
        job=jobs.get_job(job["id"])
        if job["status"]!="succeeded":raise RuntimeError(str({"status":job["status"],"error":job["error"]}))
        export(job,root,label)
    print(json.dumps({"done":label,"seconds":time.monotonic()-start}),flush=True)


def prepare(root):
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=True)
    os.environ.update(TORI_DATA_DIR=str(root/"data"),TORI_AUTO_ENABLED="0")
    from datasets import read_dataset, data_kind
    from lab_data import import_dataset, require_convention
    path=root/"imports.json"
    imports=json.loads(path.read_text("utf-8")) if path.exists() else {}
    for symbol in ("MSFT","AMZN","JPM","XOM","KO"):
        if not imports.get(symbol,{}).get("id"):
            identity=import_dataset(symbol,900,progress=lambda tf,pages,bars:print(json.dumps({"symbol":symbol,"pages":pages,"bars":bars}),flush=True))
            data=read_dataset(identity)
            imports[symbol]={"id":identity,"counts":{tf:len(v) for tf,v in data["material"]["bars"].items()},"quality":data["quality"]}
            path.write_text(json.dumps(imports,indent=2),"utf-8")
        data=read_dataset(imports[symbol]["id"])
        assert data["material"]["symbol"]==symbol and data_kind(data)=="market"
        require_convention(data)
        print(json.dumps({"pinned":symbol,"id":data["id"]}),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",required=True);parser.add_argument("--round",type=int,choices=(1,2,3))
    parser.add_argument("--prepare",action="store_true",help="Import/pin the fixed five-stock universe once, then exit")
    parser.add_argument("--profiles",default="reference,baseline,contacts3,zone_measure,zone_red3,zone_green3,zone_both3,zone_reference")
    parser.add_argument("--hypothesis",default="A frozen 0.05 ATR contact zone on identical selected rays measures additional independent contacts without changing geometry; red and green quality are tested separately.")
    parser.add_argument("--finding",default="Hermes reports mostly two-cent-zone contacts; existing ATR profile confounds measurement with line selection.")
    parser.add_argument("--validation",action="store_true")
    args=parser.parse_args()
    if args.prepare:prepare(args.root)
    elif args.round is None:parser.error("--round or --prepare required")
    else:run(args)
