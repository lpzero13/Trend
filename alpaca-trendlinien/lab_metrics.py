"""Post-decision outcomes, causal control matching and dependent-sample reports.

Nothing in this module may be fed back to historical signal selection.
"""
from bisect import bisect_left, bisect_right
from copy import deepcopy
from datetime import datetime
import math
import random
import statistics

from datasets import source_bars
from lab_data import session_bounds
from market_calendar import calendar
from models import NY
from tori_entries import atr
from tori_observations import forward_closes

VERSION="tori-lab-outcomes-1"


def expected_grid(start,end,step=300):
    first,last=datetime.fromtimestamp(start,NY).date(),datetime.fromtimestamp(end,NY).date()
    for year in range(first.year,last.year+1):
        lo=max(str(first),f"{year}-01-01");hi=min(str(last),f"{year}-12-31")
        for session in calendar(year).sessions_in_range(lo,hi):
            opened,closed=session_bounds(str(session.date()))
            yield from (t for t in range(opened,closed,step) if start<=t and t+step<=end)


def evaluate(dataset,entry,horizons,cutoff,*,prepared=None):
    sources=prepared.sources if prepared else source_bars(dataset)
    price,at=entry["entryPrice"],entry["entryAt"]
    stop=entry.get("initialStop");risk=price-stop if stop and 0<stop<price else None
    fine=sources.get("5m",sources["1h"])
    result=forward_closes(sources["1D"],at,price,horizons,cutoff)
    for h,outcome in result.items():
        if not outcome["complete"]:continue
        if prepared:
            path=fine[bisect_left(prepared.fine_times,at):bisect_right(prepared.fine_ends,outcome["closedAt"])]
        else:path=[b for b in fine if b.time>=at and b.end<=outcome["closedAt"]]
        available={b.time for b in path}
        complete=all(t in available for t in expected_grid(at,outcome["closedAt"])) if "5m" in sources else None
        outcome.update(pathComplete=complete,pathResolution="5m" if "5m" in sources else "1h-native-unverified",
                       intrabarTiming="bar interval only",initialRisk=risk)
        if not path:
            outcome.update(pathComplete=False,pathReason="no_post_entry_intraday_data")
            continue
        high=max(path,key=lambda b:b.high);low=min(path,key=lambda b:b.low)
        outcome.update(mfe_pct=max(0,(high.high/price-1)*100),mae_pct=min(0,(low.low/price-1)*100),
                       mfeAt={"from":high.time,"until":high.end},maeAt={"from":low.time,"until":low.end},
                       terminal_r=(outcome["close"]-price)/risk if risk else None)
        if risk:
            crossed=lambda level,upper:next((i for i,b in enumerate(path) if (b.high>=level if upper else b.low<=level)),None)
            safety=crossed(stop,False);one=crossed(price+risk,True);two=crossed(price+2*risk,True)
            before=lambda touch:None if touch is not None and safety==touch else (touch is not None and (safety is None or touch<safety)) if complete else None
            outcome.update(safetyTouched=True if safety is not None else False if complete else None,
                           safetyAt={"from":path[safety].time,"until":path[safety].end} if safety is not None else None,
                           oneRBeforeSafety=before(one),twoRBeforeSafety=before(two),
                           intrabarAmbiguous=safety is not None and safety in (one,two))
    return result


def matched_controls(dataset,entry,plan,spec,*,prepared=None):
    """Same stock/clock/quarter and prior trend; nearest prior volatility pool.

    Matching never uses a candidate's subsequent return, coverage or extremes.
    Missing matching data produces fewer controls, never a looser silent match.
    """
    sources=prepared.sources if prepared else source_bars(dataset);daily=sources["1D"];bars=sources["4h"]
    fine=sources.get("5m",sources["1h"])
    de=[b.end for b in daily];be=[b.end for b in bars]
    def features(at,price):
        count=bisect_right(de,at)
        if count<20:return None
        known=daily[count-20:count]
        trend=1 if known[-1].close>=statistics.mean(b.close for b in known) else -1
        count4=bisect_right(be,at)
        vol=atr(bars[max(0,count4-15):count4])
        return (trend,vol/price) if vol else None
    target=datetime.fromtimestamp(entry["entryAt"],NY)
    wanted=features(entry["entryAt"],entry["entryPrice"])
    if not wanted:return []
    pool=[]
    candidates=prepared.clock_pool(target) if prepared else fine
    for b in candidates:
        if not plan["startAt"]<=b.time<=plan["endAt"] or b.time==entry["entryAt"]:continue
        local=datetime.fromtimestamp(b.time,NY)
        if (local.hour,local.minute)!=(target.hour,target.minute) or (local.year,(local.month-1)//3)!=(target.year,(target.month-1)//3):continue
        got=features(b.time,b.open)
        if got and got[0]==wanted[0]:pool.append((abs(got[1]-wanted[1]),b))
    pool.sort(key=lambda item:(item[0],item[1].time))
    # Predeclared nearest-volatility candidate pool; random subset independent of outcomes.
    near=[b for _,b in pool[:max(20,spec["lab"]["random_controls"])]]
    rng=random.Random(f"{VERSION}|{spec['seed']}|{dataset['id']}|{entry['entryAt']}")
    chosen=sorted(rng.sample(near,min(len(near),spec["lab"]["random_controls"])),key=lambda b:b.time)
    return [{"entryAt":b.time,"entryPrice":b.open,"matching":"same NY clock/quarter/prior daily MA20 side; nearest prior ATR/price pool",
             "forward":prepared.evaluate({"entryAt":b.time,"entryPrice":b.open},spec["horizons"],plan["labelEndAt"]) if prepared else evaluate(dataset,{"entryAt":b.time,"entryPrice":b.open},spec["horizons"],plan["labelEndAt"])} for b in chosen]


class OutcomeEvaluator:
    """Parse once per stock; reuse paths/control results across profiles and anchor clones."""
    def __init__(self,dataset,sources=None):
        self.dataset=dataset;self.sources=sources if sources is not None else source_bars(dataset)
        self.fine=self.sources.get("5m",self.sources["1h"])
        self.fine_times=[b.time for b in self.fine];self.fine_ends=[b.end for b in self.fine]
        self.cache={};self.pools={}
        for b in self.fine:
            day=datetime.fromtimestamp(b.time,NY)
            self.pools.setdefault((day.year,(day.month-1)//3,day.hour,day.minute),[]).append(b)

    def clock_pool(self,day):
        return self.pools.get((day.year,(day.month-1)//3,day.hour,day.minute),[])

    def evaluate(self,entry,horizons,cutoff):
        key=(entry["entryAt"],entry["entryPrice"],entry.get("initialStop"),tuple(horizons),cutoff)
        if key not in self.cache:self.cache[key]=evaluate(self.dataset,entry,horizons,cutoff,prepared=self)
        return deepcopy(self.cache[key])

    def controls(self,entry,plan,spec):
        key=("controls",entry["entryAt"],entry["entryPrice"],plan["startAt"],plan["endAt"],plan["labelEndAt"],tuple(spec["horizons"]),spec["seed"],spec["lab"]["random_controls"])
        if key not in self.cache:self.cache[key]=matched_controls(self.dataset,entry,plan,spec,prepared=self)
        return deepcopy(self.cache[key])

    def benchmark(self,entry,horizons,cutoff):
        i=bisect_left(self.fine_times,entry["entryAt"])
        if i==len(self.fine) or self.fine[i].time!=entry["entryAt"]:
            return {str(h):{"complete":False,"reason":"benchmark_clock_missing"} for h in horizons}
        return forward_closes(self.sources["1D"],entry["entryAt"],self.fine[i].open,horizons,cutoff)


def benchmark_outcomes(dataset,entry,horizons,cutoff):
    sources=source_bars(dataset);fine=sources.get("5m",sources["1h"])
    times=[b.time for b in fine];i=bisect_left(times,entry["entryAt"])
    if i==len(fine) or fine[i].time!=entry["entryAt"]:
        return {str(h):{"complete":False,"reason":"benchmark_clock_missing"} for h in horizons}
    return forward_closes(sources["1D"],entry["entryAt"],fine[i].open,horizons,cutoff)


def percentile(values,p):
    if not values:return None
    ordered=sorted(values);at=(len(ordered)-1)*p;lo=int(at);hi=min(len(ordered)-1,lo+1)
    return ordered[lo]+(ordered[hi]-ordered[lo])*(at-lo)


def blocked_interval(observations,metric,*,seed=0,samples=200):
    """Resample symbol/calendar-quarter blocks; no independent-trade claim."""
    blocks={}
    for row in observations:
        if row.get(metric) is None:continue
        day=datetime.fromtimestamp(row["entryAt"],NY)
        key=(row["symbol"],day.year,(day.month-1)//3)
        blocks.setdefault(key,[]).append(row[metric])
    if len(blocks)<3:return {"low":None,"high":None,"blocks":len(blocks),"reason":"too_few_dependence_blocks"}
    rng=random.Random(f"lab-bootstrap-1|{seed}|{metric}");values=list(blocks.values());means=[]
    for _ in range(samples):
        sample=[v for _ in values for v in rng.choice(values)]
        means.append(statistics.mean(sample))
    return {"low":percentile(means,.025),"high":percentile(means,.975),"blocks":len(blocks),
            "method":"symbol-quarter block bootstrap; descriptive, not adjusted for profile selection"}


def summarize(records,horizons,*,seed=0,samples=200):
    groups={};seen=set();diagnostics={};cohorts={};unique_all=set()
    for case in records:
        for entry in case.get("variants",[]):
            profile=case["profile"]
            # One diagnostic evaluation per physical signal/family/check combination, not per anchor clone.
            checks=entry.get("checks",[])+entry.get("executionChecks",[])
            diagnostic_key=(profile,case["datasetId"],entry["variant"],entry.get("signalAt"),tuple(sorted((c["name"],c["state"]) for c in checks)))
            if entry.get("inPhase",True) and diagnostic_key not in seen:
                seen.add(diagnostic_key);d=diagnostics.setdefault(profile,{"evaluations":0,"failed":{},"unknown":{},"soleBlocker":{},"combinations":{},"terminalReasons":{}})
                d["evaluations"]+=1;failed=[]
                if entry.get("reason"):
                    reason=entry["reason"];d["terminalReasons"][reason]=d["terminalReasons"].get(reason,0)+1
                for c in checks:
                    if c["state"] in ("fail","unknown"):
                        area=d["unknown" if c["state"]=="unknown" else "failed"]
                        area[c["name"]]=area.get(c["name"],0)+1
                        if c["required"]:failed.append(c["name"])
                if failed:
                    key=",".join(sorted(set(failed)));d["combinations"][key]=d["combinations"].get(key,0)+1
                    if len(set(failed))==1:d["soleBlocker"][failed[0]]=d["soleBlocker"].get(failed[0],0)+1
            observed=entry["status"]=="observed"
            kind="entries" if observed else "hypothetical_rejected"
            if not observed and not entry.get("hypothetical"):continue
            point=entry if observed else entry["hypothetical"]
            key=(profile,entry["variant"],entry["quality"],kind)
            group=groups.setdefault(key,{"rawRecords":0,"points":{}});group["rawRecords"]+=1
            identity=(case["datasetId"],point["entryAt"])
            group["points"].setdefault(identity,{**point,"symbol":case["symbol"],"datasetId":case["datasetId"],"checks":checks})
            if observed:unique_all.add(identity)
    output={}
    for (profile,family,quality,kind),group in groups.items():
        evaluated={}
        for h in horizons:
            observations=[];incomplete=0
            for point in group["points"].values():
                o=point.get("forward",{}).get(str(h),{})
                if not o.get("complete"):incomplete+=1;continue
                control=[c["forward"][str(h)]["return_pct"] for c in point.get("controls",[]) if c.get("forward",{}).get(str(h),{}).get("complete")]
                bench=point.get("benchmark",{}).get(str(h),{})
                observations.append({"entryAt":point["entryAt"],"symbol":point["symbol"],"return_pct":o["return_pct"],
                    "excess_pct":o["return_pct"]-statistics.mean(control) if control else None,
                    "market_excess_pct":o["return_pct"]-bench["return_pct"] if bench.get("complete") else None,
                    "mfe_pct":o.get("mfe_pct") if o.get("pathComplete") is True else None,
                    "mae_pct":o.get("mae_pct") if o.get("pathComplete") is True else None,"terminal_r":o.get("terminal_r"),
                    "pathComplete":o.get("pathComplete"),"controlN":len(control),"closedAt":o["closedAt"],
                    "safetyTouched":o.get("safetyTouched"),"oneRBeforeSafety":o.get("oneRBeforeSafety"),
                    "twoRBeforeSafety":o.get("twoRBeforeSafety"),"intrabarAmbiguous":o.get("intrabarAmbiguous",False),
                    "datasetId":point["datasetId"]})
            values=[o["return_pct"] for o in observations]
            mean=lambda name:statistics.mean(v) if (v:=[o[name] for o in observations if o.get(name) is not None]) else None
            evaluated[str(h)]={"n":len(values),"incomplete":incomplete,"mean_return_pct":mean("return_pct"),
                "median_return_pct":statistics.median(values) if values else None,"p10_pct":percentile(values,.1),"p90_pct":percentile(values,.9),
                "positive":sum(v>0 for v in values),"negative":sum(v<0 for v in values),"mean_excess_pct":mean("excess_pct"),
                "mean_market_excess_pct":mean("market_excess_pct"),"controlMatchedEntries":sum(o["controlN"]>0 for o in observations),
                "marketMatchedEntries":sum(o["market_excess_pct"] is not None for o in observations),
                "mean_mfe_pct":mean("mfe_pct"),"mean_mae_pct":mean("mae_pct"),"mean_terminal_r":mean("terminal_r"),
                "completePaths":sum(o["pathComplete"] is True for o in observations),
                "controlObservations":sum(o["controlN"] for o in observations),
                "safetyTouched":sum(o["safetyTouched"] is True for o in observations),
                "safetyTouchKnown":sum(o["safetyTouched"] is not None for o in observations),
                "oneRBeforeSafety":sum(o["oneRBeforeSafety"] is True for o in observations),
                "twoRBeforeSafety":sum(o["twoRBeforeSafety"] is True for o in observations),
                "intrabarAmbiguous":sum(o["intrabarAmbiguous"] for o in observations),
                "dependence":dependence(observations),
                "interval":blocked_interval(observations,"excess_pct",seed=seed,samples=samples)}
            for point in group["points"].values():
                o=point.get("forward",{}).get(str(h),{})
                if not o.get("complete"):continue
                measurements={c["name"]:c.get("value") for c in point["checks"]}
                for dimension,band in cohort_bands(measurements).items():
                    identity="|".join((profile,family,quality,kind,str(h),dimension,band))
                    cohorts.setdefault(identity,[]).append(o["return_pct"])
        output["|".join((profile,family,quality,kind))]={"profile":profile,"family":family,"quality":quality,"kind":kind,
            "rawRecords":group["rawRecords"],"uniqueEntries":len(group["points"]),"horizons":evaluated}
    return {"version":VERSION,"groups":output,"diagnostics":diagnostics,"uniqueTimesAcrossProfiles":len(unique_all),
            "cohorts":{k:{"n":len(v),"mean_return_pct":statistics.mean(v),"median_return_pct":statistics.median(v)} for k,v in cohorts.items()},
            "cohortPolicy":"Predeclared descriptive bins, not optimal thresholds; families/profiles/quality groups can share times. Incomplete path extrema excluded from aggregate MFE/MAE.",
            "interpretation":"Hypothetical rejected cases are separate. Reused times, families, profiles and overlapping paths are dependent. Returns are not portfolio profits."}


def dependence(rows):
    ends={};episodes=0;overlapping=0
    for row in sorted(rows,key=lambda r:(r["entryAt"],r["datasetId"])):
        previous=ends.get(row["datasetId"])
        if previous is not None and row["entryAt"]<=previous:overlapping+=1
        else:episodes+=1
        ends[row["datasetId"]]=max(previous or 0,row["closedAt"])
    return {"sameStockOverlappingEntries":overlapping,"sameStockEpisodes":episodes,
            "note":"Episodes merge overlapping paths of one dataset. Different stocks may remain market-correlated."}


def cohort_bands(values):
    def number(name,bands):
        value=values.get(name)
        if type(value) not in (int,float) or not math.isfinite(value):return "unknown"
        return next((label for boundary,label in bands if value<boundary),bands[-1][1])
    result = {"red_contacts":number("red_contacts",[(3,"2"),(4,"3"),(math.inf,"4+")]),
            "green_contacts":number("green_contacts",[(3,"2"),(4,"3"),(math.inf,"4+")]),
            "age_days":number("line_age",[(7,"under7"),(21,"7to20"),(42,"21to41"),(math.inf,"42+")]),
            "safety_pct":number("safety_distance_pct",[(1,"under1"),(3,"1to3"),(math.inf,"3+")]),
            "context":str(values.get("context",{}).get("1D","unknown")) if isinstance(values.get("context",{}),dict) else "unknown"}
    if "zone_red_contacts" in values:
        for side in ("red","green"):
            result["zone_"+side+"_contacts"]=number("zone_"+side+"_contacts",[(2,"under2"),(3,"2"),(4,"3"),(math.inf,"4+")])
        red,green=values.get("zone_red_contacts"),values.get("zone_green_contacts")
        result["zone_both3"]="unknown" if red is None or green is None else "yes" if min(red,green)>=3 else "no"
    return result
