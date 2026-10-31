"""Preregistered multi-asset research, finite cash, frozen selection and later tests."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
from types import SimpleNamespace
from unittest.mock import patch

from datasets import read_dataset, source_bars
from fan_execution import ExecutionRules, entry_contract
from fan_geometry import stable_id
from fan_observer import price_at
from history_archive import get as archive_job
from pilot_backtest import PilotSpec, run, code_digest, execute_path
from screening_portfolio import candidates, matches, ledger, compact, development_gate, test_gate, OPTIONS
from models import DataError, NY
from workbench_portfolio import CloseMarks

VERSION="tori-preregistered-screen-1"
SYMBOLS=("AAPL","JPM","JNJ","XOM","KO","CAT","HD","NEE")
FOLDS={"development":[{"name":str(y),"start":f"{y}-01-01","end":f"{y}-12-31","outcome_end":f"{y+1}-03-31"} for y in (2019,2020,2022)],
       "validation":[{"name":"2024","start":"2024-01-01","end":"2024-12-31","outcome_end":"2025-03-31"}],
       "confirmation":[{"name":"2025-2026","start":"2025-04-01","end":"2026-03-31","outcome_end":"2026-06-30"}]}


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    body=json.dumps(value,ensure_ascii=False,allow_nan=False,separators=(",",":")).encode("utf-8")
    temporary=path.with_suffix(path.suffix+".tmp")
    if path.suffix==".gz":
        with gzip.open(temporary,"wb") as f:f.write(body)
    else:temporary.write_bytes(body)
    temporary.replace(path)


def read(path):
    path=Path(path)
    body=gzip.open(path,"rb").read() if path.suffix==".gz" else path.read_bytes()
    return json.loads(body)


def engine_binding():
    root=Path(__file__).parent
    extra={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in
           ("strategy_screen.py","screening_portfolio.py","strategy_portfolio.py","workbench_portfolio.py")}
    return {"pilot":code_digest(),"study":extra}


def prepare(root):
    root=Path(root);path=root/"plan.json"
    if path.exists():
        plan=read(path)
        if stable_id({k:v for k,v in plan.items() if k!="id"})!=plan["id"]:raise DataError("Plan-Prüfsumme geändert.",409)
        if plan["engine"]!=engine_binding():raise DataError("Studiencode geändert: neuen Studienordner anlegen; alte Ergebnisse bleiben erhalten.",409)
        return plan
    stocks=archive_job("3e86a04aa09347caa2295b25")["stocks"]
    if any(stocks.get(s,{}).get("status")!="completed" for s in SYMBOLS):
        raise DataError("Vorab gewählte Aktien nicht vollständig lokal verfügbar. Keine stille Ersetzung.",422)
    plan={"version":VERSION,"date":"2026-10-30","symbols":list(SYMBOLS),
          "datasets":{s:stocks[s]["datasetId"] for s in SYMBOLS},"folds":deepcopy(FOLDS),
          "policies":candidates(),"portfolio":OPTIONS,"controls":39,"seed":20261030,
          "engine":engine_binding(),"costs":{"spread_bps":5.,"slippage_bps":5.,"fee_per_order":0.},
          "selection":"development gates, then mean return, drawdown, stable ID; freeze before validation",
          "gates":{"developmentTrades":20,"positiveDevelopmentFolds":2,"maxDrawdownPct":10,
                   "testTrades":10,"positiveSymbols":4,"maxPositiveConcentration":.5,"controlPercentile":.9},
          "limitations":["Current surviving universe","Historical data used in earlier projects may be known",
                         "Separate reset-capital folds, no compounded full-period performance","Not prospective validation"]}
    plan["id"]=stable_id(plan);write(path,plan)
    return plan


def task_path(root,phase,symbol,fold):return Path(root)/phase/(symbol+"-"+fold["name"]+".json.gz")


def load_task(path,plan):
    payload=read(path)
    if payload["planId"]!=plan["id"] or payload.get("checksum")!=stable_id({k:v for k,v in payload.items() if k!="checksum"}):
        raise DataError("Studiencache geändert oder anderem Plan zugeordnet.",409)
    return payload


def _work(task):
    root,plan,phase,symbol,fold=task
    path=task_path(root,phase,symbol,fold)
    if path.exists():
        payload=load_task(path,plan)
        return {"symbol":symbol,"fold":fold["name"],"cached":True,"cases":len(payload["pilot"]["cases"])}
    with patch('alpaca._request',side_effect=AssertionError('Research screen is strictly offline')):
        dataset=read_dataset(plan["datasets"][symbol])
        spec=PilotSpec(start=fold["start"],end=fold["end"],outcome_end=fold["outcome_end"],horizons=(20,),stop_modes=("hard_stop",))
        # Signal/price paths must remain available even when a small actual
        # account could not afford one share. The ledger below sizes afresh.
        result=run(dataset,spec,ExecutionRules(capital=1_000_000.,risk_fraction=.01))
        if not result["audit"]["passed"]:raise AssertionError(result["audit"])
        fine=[b for b in source_bars(dataset)["5m"] if spec.bounds()[1]-86400<=b.end<=spec.bounds()[3]]
        payload={"planId":plan["id"],"symbol":symbol,"datasetId":dataset["id"],"fold":fold,
                 "pilot":result,"marks":{"ends":[b.end for b in fine],"closes":[b.close for b in fine]}}
        payload["checksum"]=stable_id(payload)
        write(path,payload)
    return {"symbol":symbol,"fold":fold["name"],"cached":False,"cases":len(result["cases"]),"seconds":result["elapsedSeconds"]}


def build(root,plan,phase,*,workers=2,progress=lambda value:None):
    tasks=[(str(root),plan,phase,s,fold) for fold in plan["folds"][phase] for s in plan["symbols"]]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        pending=[pool.submit(_work,t) for t in tasks]
        for task in as_completed(pending):progress(task.result())


def load_fold(root,plan,phase,fold):
    cases=[];contexts={}
    for symbol in plan["symbols"]:
        payload=load_task(task_path(root,phase,symbol,fold),plan)
        for case in payload["pilot"]["cases"]:
            cases.append({**case,"symbol":symbol,"datasetId":payload["datasetId"]})
        marks=payload["marks"]
        context=CloseMarks([])
        from array import array
        context.ends=array('q',marks["ends"]);context.closes=array('d',marks["closes"])
        contexts[payload["datasetId"]]=SimpleNamespace(fine=context)
    spec=PilotSpec(start=fold["start"],end=fold["end"],outcome_end=fold["outcome_end"])
    _,start,_,end=spec.bounds()
    return cases,contexts,{"startAt":start,"endAt":end}


def select(results,policies):
    summaries=[]
    for p in policies:
        folds=results[p["id"]]
        returns=[v["markedReturnPct"] for v in folds]
        complete=all(r is not None for r in returns)
        summaries.append({"policy":p,"eligible":development_gate(folds),
            "meanFoldReturnPct":statistics.mean(returns) if complete else None,
            "worstDrawdownPct":min(v["max5mSampledDrawdownPct"] for v in folds),
            "trades":sum(v["accepted"] for v in folds),"folds":[compact(v) for v in folds]})
    eligible=sorted((r for r in summaries if r["eligible"]),
                    key=lambda r:(-r["meanFoldReturnPct"],-r["worstDrawdownPct"],r["policy"]["id"]))
    chosen={}
    for row in eligible:chosen.setdefault(row["policy"]["family"],row["policy"])
    return {"allDevelopment":summaries,"selectedByFamily":chosen,
            "primary":eligible[0]["policy"] if eligible else None,
            "reason":None if eligible else "No candidate passed preregistered development gates"}


def development(root,plan,progress=lambda v:None):
    build(root,plan,"development",progress=progress)
    results={p["id"]:[] for p in plan["policies"]}
    for fold in plan["folds"]["development"]:
        cases,contexts,phase=load_fold(root,plan,"development",fold)
        for p in plan["policies"]:
            value=ledger(cases,contexts,phase,p)
            results[p["id"]].append(value)
            write(Path(root)/"development-ledgers"/(fold["name"]+"-"+p["id"].replace(":","_")+".json.gz"),value)
        progress({"phase":"development-ledgers","fold":fold["name"],"policies":len(plan["policies"])})
    selection=select(results,plan["policies"])
    selection.update(planId=plan["id"],purpose="Frozen using development only")
    selection["id"]=stable_id(selection);write(Path(root)/"selection.json",selection)
    # Assess fragility without changing the selected primary afterwards.
    if selection["primary"]:
        out=[]
        for excluded in plan["symbols"]:
            folds=[]
            for fold in plan["folds"]["development"]:
                cases,contexts,phase=load_fold(root,plan,"development",fold)
                value=ledger([c for c in cases if c["symbol"]!=excluded],contexts,phase,selection["primary"])
                folds.append(compact(value))
            out.append({"excluded":excluded,"folds":folds,"meanFoldReturnPct":statistics.mean(v["markedReturnPct"] for v in folds)})
        write(Path(root)/"leave-one-symbol-out.json",{"planId":plan["id"],"selectionId":selection["id"],"items":out})
    return selection


def _controls(root,plan,phase_name,policy,actual):
    """Outcome-blind month/asset counts; valid causal Safety pool, same ledger."""
    fold=plan["folds"][phase_name][0]
    originals,contexts,phase=load_fold(root,plan,phase_name,fold)
    matched=[c for c in originals if matches(c,policy)]
    wanted={}
    for symbol in plan["symbols"]:
        wanted[symbol]={}
        for c in matched:
            if c["symbol"]==symbol:
                month=datetime.fromtimestamp(c["signal"]["signalAt"],NY).strftime('%Y-%m')
                wanted[symbol][month]=wanted[symbol].get(month,0)+1
    chosen=[[] for _ in range(plan["controls"])];shortfalls=[]
    for symbol in plan["symbols"]:
        payload=load_task(task_path(root,phase_name,symbol,fold),plan);timeline=payload["pilot"]["timeline"]
        dataset=read_dataset(plan["datasets"][symbol]);spec=PilotSpec(**payload["pilot"]["manifest"]["spec"])
        _,start,end,cutoff=spec.bounds()
        fine=[b for b in source_bars(dataset)["5m"] if start<=b.time and b.end<=cutoff]
        daily=[b for b in source_bars(dataset)["1D"] if b.end<=cutoff]
        from fan_study import source_gaps
        daily_gaps=source_gaps(daily,cutoff,"1D")
        from bisect import bisect_right
        dends=[b.end for b in daily];pools={}
        for state in timeline:
            green=state["green"]
            if not start<=state["closedAt"]<=end or not green or not 0<green["value"]<state["close"]:continue
            if policy["family"]=="safety_bounce" and not green["qualified"]:continue
            known=daily[:bisect_right(dends,state["closedAt"])];last=known[-1].close if known else None
            clean=len(known)>=200 and not any(len(known)-200<i<len(known) for i in daily_gaps)
            sma=sum(b.close for b in known[-200:])/200 if clean else None
            if policy["sma200"] and (sma is None or last<sma):continue
            month=datetime.fromtimestamp(state["closedAt"],NY).strftime('%Y-%m')
            pools.setdefault(month,[]).append((state,last,sma))
        cache={}
        execution=ExecutionRules(capital=1_000_000.,risk_fraction=.01)
        for repetition in range(plan["controls"]):
            rng=random.Random(f"{plan['seed']}|{phase_name}|{policy['id']}|{symbol}|{repetition}")
            for month,count in sorted(wanted[symbol].items()):
                pool=pools.get(month,[])
                if not pool:
                    shortfalls.append({"symbol":symbol,"month":month,"repetition":repetition,"count":count});continue
                for serial in range(count):
                    state,last,sma=rng.choice(pool);key=state["closedAt"]
                    if key not in cache:
                        green=deepcopy(state["green"])
                        stop=math.floor(green["value"]*.997/.01)*.01
                        signal={"id":stable_id([VERSION,"control",symbol,key]),"signalAt":key,"initialStop":stop,
                            "family":policy["family"],"cohort":"qualified" if green["qualified"] else "two","control":True,
                            "signalClose":state["close"],"line":green,"safety":green}
                        entry=entry_contract(signal,fine,cutoff,execution)
                        p=execute_path(signal,entry,fine,timeline,cutoff,20,policy["model"],"hard_stop")
                        cache[key]={"id":signal["id"],"symbol":symbol,"datasetId":dataset["id"],"signal":signal,
                                    "context":{"dailyClose":last,"dailySma200":sma},"entry":entry,
                                    "paths":{f"{policy['model']}:hard_stop:20":p}}
                    case=deepcopy(cache[key]);case["id"]=stable_id([case["id"],repetition,month,serial]);chosen[repetition].append(case)
    values=[]
    control_policy={**policy,"quality":"all"}
    for i,cases in enumerate(chosen):
        # Red contact quality is the treatment, not a claimed property of a
        # random Safety-based control. Never relabel its actual contact count.
        value=ledger(cases,contexts,phase,control_policy)
        write(Path(root)/phase_name/f"control-ledger-{i}.json.gz",value);values.append(compact(value))
    returns=[v["markedReturnPct"] for v in values if v["markedReturnPct"] is not None]
    threshold=sorted(returns)[max(0,math.ceil(.9*len(returns))-1)] if returns else None
    return {"items":values,"shortfalls":shortfalls,"complete":not shortfalls and len(returns)==plan["controls"],
            "q90ReturnPct":threshold,"actualReturnPct":actual["markedReturnPct"],
            "aboveQ90":not shortfalls and len(returns)==plan["controls"] and actual["markedReturnPct"] is not None and actual["markedReturnPct"]>threshold,
            "interpretation":"Exploratory conditional random-entry comparison. Red contact quality is not matched. Not a multiple-testing-corrected p-value"}


def later_test(root,plan,phase_name,progress=lambda v:None):
    selection=read(Path(root)/"selection.json")
    if stable_id({k:v for k,v in selection.items() if k!="id"})!=selection["id"]:raise DataError("Auswahl-Prüfsumme geändert.",409)
    if selection["planId"]!=plan["id"]:raise DataError("Auswahl gehört zu anderem Plan.",409)
    if not selection["primary"]:return {"opened":False,"reason":selection["reason"]}
    if phase_name=="confirmation":
        validation=read(Path(root)/"validation-summary.json")
        if not validation["primaryPassed"]:return {"opened":False,"reason":"Primary failed earlier validation; confirmation remains unopened"}
    # Selection is already persisted before any later cache/data is opened.
    build(root,plan,phase_name,progress=progress)
    fold=plan["folds"][phase_name][0];cases,contexts,phase=load_fold(root,plan,phase_name,fold)
    summaries=[];primary=None
    for policy in selection["selectedByFamily"].values():
        base=ledger(cases,contexts,phase,policy);stress=ledger(cases,contexts,phase,policy,cost_multiplier=2)
        write(Path(root)/phase_name/(policy["id"].replace(":","_")+"-ledger.json.gz"),base)
        write(Path(root)/phase_name/(policy["id"].replace(":","_")+"-stress.json.gz"),stress)
        row={"policy":policy,"base":compact(base),"doubleCosts":compact(stress),"gate":test_gate(base,stress)}
        summaries.append(row)
        if policy["id"]==selection["primary"]["id"]:primary=row
    controls=_controls(root,plan,phase_name,selection["primary"],primary["base"])
    result={"opened":True,"planId":plan["id"],"selectionId":selection["id"],"phase":phase_name,"items":summaries,
            "controls":controls,"primary":primary,"primaryPassed":primary["gate"]["passed"] and controls["aboveQ90"]}
    write(Path(root)/(phase_name+"-summary.json"),result);return result
