"""Versioned long-only paper execution, capital constraints and marked equity.

The signal engine never imports this module. OHLC fills are assumptions, not
broker fills; missing fine data leaves positions unresolved rather than inventing
an exit. No account, order, or provider-write operation exists here.
"""
from bisect import bisect_left, bisect_right
from collections import OrderedDict
from datetime import datetime, timedelta
import math

from datasets import read_dataset
from lab_data import session_bounds
from lab_metrics import expected_grid
from lab_splits import sessions_between
from models import NY

VERSION="tori-paper-execution-1"


class SourceCache:
    """Load only stocks actually considered or held; bounded independent of universe size."""
    def __init__(self,datasets,limit):
        self.datasets=datasets;self.limit=max(1,min(32,limit));self.cache=OrderedDict();self.peak=0;self.conventions={}

    def get(self,key):
        if key not in self.cache:
            value=self.datasets[key]
            if value.get("descriptorOnly"):value=read_dataset(value["id"])
            self.conventions[key]={"feed":value["material"].get("feed","unknown"),"adjustment":value["material"].get("adjustment","unknown")}
            # Only execution bars are needed for fills and equity marks.
            from models import Bar
            frames={tf:[Bar(**b) for b in rows] for tf,rows in value["material"]["bars"].items() if tf in ("5m","1h")}
            bars=frames.get("5m",frames["1h"])
            self.cache[key]=(frames,bars,[b.end for b in bars])
            while len(self.cache)>self.limit:self.cache.popitem(last=False)
            self.peak=max(self.peak,len(self.cache))
        self.cache.move_to_end(key)
        return self.cache[key]


def trade_path(sources,entry,options,cutoff):
    price,at,stop=entry["entryPrice"],entry["entryAt"],entry.get("initialStop")
    cost=options["spread_bps"]/20000+options["slippage_bps"]/10000
    buy=price*(1+cost)
    result={"version":VERSION,"entryAt":at,"entryPrice":price,"entryFill":buy,"initialStop":stop,
            "status":"censored","exitAt":None,"exitFill":None,"intrabarAmbiguous":False}
    if not stop or not 0<stop<buy:return {**result,"reason":"invalid_initial_risk","status":"invalid"}
    if "5m" not in sources:return {**result,"reason":"fine_execution_data_required","status":"unavailable"}
    day=datetime.fromtimestamp(at,NY).date()
    sessions=sessions_between(str(day+timedelta(days=1)),str(day+timedelta(days=options["holding_days"]*4+30)))
    target_close=session_bounds(sessions[options["holding_days"]-1])[1]
    bounds=session_bounds(str(day))
    if not bounds or not bounds[0]<=at<bounds[1] or (at-bounds[0])%300:return {**result,"reason":"entry_not_on_regular_fine_grid","status":"unavailable"}
    result.update(plannedTimeExit=target_close,initialRisk=buy-stop)
    target=buy+options["target_r"]*(buy-stop)
    result["targetPrice"]=target if options["exit"]=="stop_target_time" else None
    until=min(target_close,cutoff);fine=sources["5m"]
    times=[b.time for b in fine];i=bisect_left(times,at)
    if i>=len(fine) or fine[i].time!=at:return {**result,"status":"unavailable","reason":"entry_open_not_available"}
    def close(bar,base,reason,ambiguous=False):
        return {**result,"status":"closed","exitAt":bar.end,"exitPrice":base,"exitFill":base*(1-cost),
                "exitReason":reason,"intrabarAmbiguous":ambiguous,"timing":"intrabar fill; release capital only at fine-bar end"}
    use_stop=options["exit"]!="time";use_target=options["exit"]=="stop_target_time"
    last=None
    for stamp in expected_grid(at,until):
        if i>=len(fine) or fine[i].time!=stamp:
            return {**result,"reason":"missing_fine_path","missingAt":stamp,"lastObservedAt":last.end if last else at}
        bar=fine[i];i+=1;last=bar
        if stamp==at and bar.open!=price:return {**result,"status":"invalid","reason":"entry_price_not_source_open"}
        if use_stop and bar.open<=stop:return close(bar,bar.open,"stop_gap")
        if use_target and bar.open>=target:return close(bar,target,"target_at_open")
        hit_stop=use_stop and bar.low<=stop;hit_target=use_target and bar.high>=target
        if hit_stop:return close(bar,stop,"stop",hit_target)
        if hit_target:return close(bar,target,"target")
        if bar.end==target_close:return close(bar,bar.close,"time")
    return {**result,"reason":"observation_boundary" if cutoff<target_close else "missing_time_exit_bar", "lastObservedAt":last.end if last else at}


def simulate(records,datasets,options,phase,*,profile,family):
    """Stable chronological selection; sizing uses only then-known cash/equity.

    Each profile/family is an independent hypothetical portfolio. Concurrent
    candidates are ordered by symbol and stable setup ID, never future profit.
    """
    cache=SourceCache(datasets,options["max_positions"]+1)
    candidates={}
    for case in sorted(records,key=lambda c:c["id"]):
        if case["profile"]!=profile:continue
        for entry in case["variants"]:
            if entry["variant"]==family and entry["status"]=="observed" and phase["startAt"]<=entry["entryAt"]<=phase["endAt"]:
                candidates.setdefault((case["datasetId"],entry["entryAt"]),{**entry,"symbol":case["symbol"],"datasetId":case["datasetId"],"setupId":case["id"]})
    ordered=sorted(candidates.values(),key=lambda e:(e["entryAt"],e["symbol"],e["setupId"]))
    cash=options["capital"];active=[];trades=[];skipped=[];equity=[];fees=0
    def marked(at):
        total=cash;stale=0;exposure=0
        for position in active:
            entry=position["entry"];key=entry["datasetId"]
            _,bars,ends=cache.get(key)
            i=bisect_right(ends,at)-1
            bar=bars[i] if i>=0 and bars[i].end>entry["entryAt"] else None
            price=bar.close if bar else entry["entryPrice"]
            value=position["quantity"]*price;total+=value;exposure+=value
            if position["path"]["status"]=="censored" and position["path"].get("missingAt",math.inf)<=at:stale+=1
        return total,exposure,stale
    def exits(at):
        nonlocal cash,fees
        for position in list(active):
            path=position["path"]
            if path["status"]=="closed" and path["exitAt"]<=at:
                cash+=position["quantity"]*path["exitFill"]-options["fee_per_order"];fees+=options["fee_per_order"]
                position["netPnl"]=position["quantity"]*(path["exitFill"]-path["entryFill"])-2*options["fee_per_order"]
                active.remove(position)
    by_time={}
    for entry in ordered:by_time.setdefault(entry["entryAt"],[]).append(entry)
    dates=sessions_between(str(datetime.fromtimestamp(phase["startAt"],NY).date()),str(datetime.fromtimestamp(phase["endAt"],NY).date()))
    timeline=sorted(set(by_time)|{session_bounds(d)[1] for d in dates}|{phase["endAt"]})
    for at in timeline:
        exits(at)
        for entry in by_time.get(at,[]):
            reason=None
            if any(p["entry"]["symbol"]==entry["symbol"] for p in active):reason="symbol_already_held"
            elif len(active)>=options["max_positions"]:reason="position_limit"
            if reason:
                skipped.append({"setupId":entry["setupId"],"entryAt":at,"reason":reason});continue
            path=trade_path(cache.get(entry["datasetId"])[0],entry,options,phase["endAt"])
            if path["status"] in ("invalid","unavailable"):
                skipped.append({"setupId":entry["setupId"],"entryAt":at,"reason":path["reason"]});continue
            total,_,_=marked(at)
            available=max(0,cash-options["fee_per_order"])
            risk=path["entryFill"]-entry["initialStop"]
            units=min(available/path["entryFill"],max(0,total)*options["allocation_fraction"]/path["entryFill"],max(0,total)*options["risk_fraction"]/risk)
            units=math.floor(units*1e6)/1e6 if options["fractional"] else math.floor(units)
            if units<=0:
                skipped.append({"setupId":entry["setupId"],"entryAt":at,"reason":"insufficient_cash_or_size"});continue
            cash-=units*path["entryFill"]+options["fee_per_order"];fees+=options["fee_per_order"]
            position={"entry":entry,"quantity":units,"path":path,"netPnl":None};trades.append(position);active.append(position)
        # A same-bar exit is still not available at the entry's opening.
        exits(at)
        total,exposure,stale=marked(at)
        equity.append({"at":at,"equity":total,"cash":cash,"marketValue":exposure,"openPositions":len(active),"uncertainPaths":stale})
    final,exposure,stale=marked(phase["endAt"])
    peak=options["capital"];drawdown=0
    for point in equity:
        peak=max(peak,point["equity"])
        drawdown=min(drawdown,(point["equity"]/peak-1)*100)
    closed=[t for t in trades if t["netPnl"] is not None]
    pnl=[t["netPnl"] for t in closed];gain=sum(max(0,p) for p in pnl);loss=-sum(min(0,p) for p in pnl)
    return {"version":VERSION,"profile":profile,"family":family,"options":options,"trades":trades,"skipped":skipped,"equity":equity,
            "summary":{"accepted":len(trades),"closed":len(closed),"open":len(active),"skipped":len(skipped),"initialCapital":options["capital"],
                "finalMarkedEquity":final,"cash":cash,"marketValue":exposure,"realizedNetPnl":sum(pnl),"feesPaid":fees,
                "markedReturnPct":(final/options["capital"]-1)*100,"maxMarkedDrawdownPct":drawdown,
                "winRateClosed":sum(p>0 for p in pnl)/len(pnl) if pnl else None,"profitFactor":gain/loss if loss else None,
                "uncertainOpenPaths":stale,"executionSourceCachePeak":cache.peak},
            "assumptions":{"fills":"OHLC model; stop-first when intrabar order unknown; opening gaps before intrabar touches; sell spread/slippage; flat fee per side",
                           "sizing":"current marked equity, available cash, allocation/risk limits; no borrowing; one position per symbol",
                           "marking":"daily closes and entry times; only then-closed bars; unresolved gaps are not invented exits; returns with uncertain open paths are not fully verified",
                           "dataConventions":cache.conventions,"priceUnits":"stored price scale; adjusted-unit quantities need not equal historical original-share lots; cash dividends/corporate-action events are not reconstructed",
                           "ordering":"same-time candidates by symbol then setup ID; families/profiles are separate portfolios"}}
