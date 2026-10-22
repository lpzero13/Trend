"""Three preregistered isolated exits on frozen Retest entries; no orders."""
from bisect import bisect_left, bisect_right
from collections import Counter
from datetime import datetime
from statistics import mean

from exit_research import horizon_close, ray_value
from lab_data import session_bounds
from lab_metrics import expected_grid, blocked_interval
from lab_splits import sessions_between
from models import NY
from retest_exits import trade_stats, path as reference_path
from tori_entries import atr

VERSION = "retest-exit-variants-1"
VARIANTS = ("failed_retest", "time_no_progress", "atr_gain_stop")
RULES = {"days":10, "progress_days":5, "activation_r":1., "trail_atr":2., "latency":300}


def execution_open(known_at):
    return next(expected_grid(known_at+RULES["latency"], known_at+14*86400))


def source_schedule(at, end):
    first,last = [str(datetime.fromtimestamp(t,NY).date()) for t in (at,end)]
    result=[]
    for day in sessions_between(first,last):
        opened,closed=session_bounds(day)
        result.extend((t,min(t+14400,closed)) for t in range(opened,closed,14400)
                      if at < min(t+14400,closed) <= end)
    return result


def path(context, entry, contract, variant):
    if variant == "fixed":
        return reference_path(context,entry,contract,"fixed")
    if variant not in VARIANTS:
        raise ValueError("Unknown preregistered Retest exit")
    at=entry["entryAt"]
    planned=horizon_close(at,10)
    progress=horizon_close(at,5)
    costs=contract["costs"]
    quantity=(costs["notional"]-costs["fee_per_order"])/contract["entryFill"]
    stop=contract["initialStop"]
    peak=entry["entryPrice"]
    active=False
    pending=None
    events=[]
    result={"version":VERSION,"model":variant,"days":10,"entryId":entry["id"],"entryAt":at,
        "entryPrice":entry["entryPrice"],"entryFill":contract["entryFill"],"initialStop":stop,
        "initialRisk":contract["initialRisk"],"plannedTimeExit":planned,"status":"censored",
        "exitAt":None,"exitFill":None,"events":events,"intrabarAmbiguous":False}
    if not contract["checks"]["known_atr"] or not contract["checks"]["positive_stop"]:
        return {**result,"status":"unavailable","reason":"invalid_or_unknown_initial_safety"}
    bounds=session_bounds(str(datetime.fromtimestamp(at,NY).date()))
    if not bounds or not bounds[0] <= at < bounds[1] or (at-bounds[0]) % 300 or entry["signalAt"] > at or entry.get("availableAt",at) > at:
        return {**result,"status":"invalid","reason":"invalid_entry_knowledge_or_grid"}
    k=bisect_left(context.times,at)
    if k == len(context.times) or context.times[k] != at:
        return {**result,"status":"unavailable","reason":"entry_open_not_available"}
    schedule=source_schedule(at,min(planned,context.cutoff)) if variant != "time_no_progress" else []
    by_source={(b.time,b.end):i for i,b in enumerate(context.four)}
    source_cursor=0

    def closed(bar,base,reason,at_open=False):
        sell=base*(1-costs["side_cost"])
        pnl=quantity*(sell-contract["entryFill"])-2*costs["fee_per_order"]
        return {**result,"status":"closed","exitPrice":base,"exitFill":sell,"exitAt":bar.end,
            "fillBarAt":bar.time,"atOpen":at_open,"exitReason":reason,"quantity":quantity,
            "netPnl":pnl,"netReturnPct":pnl/costs["notional"]*100,
            "netR":pnl/(quantity*contract["initialRisk"]),"finalHardStop":stop}

    for stamp in expected_grid(at,min(planned,context.cutoff)):
        if k == len(context.fine) or context.fine[k].time != stamp:
            return {**result,"reason":"missing_fine_path","missingAt":stamp}
        bar=context.fine[k]
        k+=1
        if stamp == at and bar.open != entry["entryPrice"]:
            return {**result,"status":"invalid","reason":"entry_price_not_source_open"}
        # The previously working stop remains protective before new decisions.
        if bar.open <= stop:
            return closed(bar,bar.open,"hard_stop_gap",True)
        if pending and pending["effectiveAt"] <= stamp:
            return closed(bar,bar.open,pending["reason"],True)
        while source_cursor < len(schedule) and schedule[source_cursor][1]+RULES["latency"] <= stamp:
            slot=schedule[source_cursor]
            source_cursor+=1
            if slot not in by_source:
                return {**result,"reason":"missing_source_path","missingSourceAt":slot[1],"missingAt":stamp}
            i=by_source[slot]
            current=context.four[i]
            if variant == "failed_retest":
                level=ray_value(entry["red"],i)-entry["signalWidth"]
                if current.close < level:
                    pending={"reason":"failed_retest","effectiveAt":execution_open(current.end)}
                    events.append({"kind":"failed_retest","knownAt":current.end,"effectiveAt":pending["effectiveAt"],
                        "sourceIndex":i,"close":current.close,"lowerZone":level})
                    break
            else:
                peak=max(peak,current.close)
                net_per_unit=current.close*(1-costs["side_cost"])-contract["entryFill"]-2*costs["fee_per_order"]/quantity
                if not active and net_per_unit >= RULES["activation_r"]*contract["initialRisk"]:
                    active=True
                    events.append({"kind":"gain_activate","knownAt":current.end,"effectiveAt":execution_open(current.end),
                        "sourceIndex":i,"close":current.close,"netR":net_per_unit/contract["initialRisk"]})
                if active:
                    volatility=atr(context.four[:i+1])
                    if volatility is None:
                        return {**result,"reason":"unknown_atr","missingAt":stamp}
                    proposed=max(stop,peak-RULES["trail_atr"]*volatility)
                    if proposed > stop+1e-8:
                        events.append({"kind":"atr_stop_raise","knownAt":current.end,"effectiveAt":execution_open(current.end),
                            "sourceIndex":i,"peakClose":peak,"atr":volatility,"previousHardStop":stop,"hardStop":proposed})
                        stop=proposed
        if bar.open <= stop:
            return closed(bar,bar.open,"hard_stop_gap",True)
        if pending and pending["effectiveAt"] <= stamp:
            return closed(bar,bar.open,pending["reason"],True)
        if bar.low <= stop:
            return closed(bar,stop,"hard_stop")
        if bar.end == planned:
            return closed(bar,bar.close,"time")
        if variant == "time_no_progress" and bar.end == progress:
            pnl=quantity*(bar.close*(1-costs["side_cost"])-contract["entryFill"])-2*costs["fee_per_order"]
            decision=pnl <= 0
            effective=execution_open(bar.end) if decision else None
            events.append({"kind":"progress_check","knownAt":bar.end,"effectiveAt":effective,"netPnl":pnl,"exit":decision})
            if decision:
                pending={"reason":"time_no_progress","effectiveAt":effective}
    return {**result,"reason":"phase_boundary" if planned > context.cutoff else "missing_time_exit_bar"}


def stats(paths):
    comparable=[{**p,"events":[e for e in p["events"] if "hardStop" in e]} for p in paths]
    result=trade_stats(comparable)
    result["eventCounts"]=dict(Counter(e["kind"] for p in paths for e in p["events"]))
    return result


def summarize(records,variant):
    groups={}
    for geometry in ("hull_exact","swing_zone"):
        for quality in ("complete_history","gapped_history"):
            rows=[r for r in records if r["entry"]["model"] == geometry and r["calendarFits"] and
                  r["history"]["complete"] == (quality == "complete_history")]
            paired=[r for r in rows if all(r["paths"][m]["status"] == "closed" for m in ("fixed",variant))]
            deltas=[{"symbol":r["entry"]["symbol"],"entryAt":r["entry"]["entryAt"],
                     "deltaR":r["paths"][variant]["netR"]-r["paths"]["fixed"]["netR"]} for r in paired]
            groups[geometry+"/"+quality]={"cases":len(rows),"pairedClosed":len(paired),
                "models":{m:stats([r["paths"][m] for r in rows]) for m in ("fixed",variant)},
                "pairedModels":{m:stats([r["paths"][m] for r in paired]) for m in ("fixed",variant)},
                "meanDeltaR":mean(d["deltaR"] for d in deltas) if deltas else None,
                "deltaInterval":blocked_interval(deltas,"deltaR",seed=20261022),
                "fullHorizonPaired":{m:stats([r["paths"][m] for r in paired if r["fullHorizonPath"]]) for m in ("fixed",variant)}}
    return groups
