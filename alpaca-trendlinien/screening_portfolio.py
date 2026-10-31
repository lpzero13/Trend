"""Adapt causal pilot paths to the existing finite-cash ledger; no outcome filters."""
from collections import Counter, defaultdict
from copy import deepcopy
import math

from strategy_portfolio import simulate

VERSION="tori-screening-portfolio-1"
OPTIONS={"capital":2000.,"risk_fraction":.01,"allocation_fraction":.25,"max_positions":3,"fractional":False}


def candidates():
    result=[]
    for family in ("breakout","red_retest","safety_bounce"):
        for quality in (("all","qualified") if family!="safety_bounce" else ("qualified",)):
            for model in ("fixed","original_safety","fan_safety"):
                for sma in (False,True):
                    result.append({"id":f"{family}:{quality}:{model}:sma{int(sma)}","family":family,
                                   "quality":quality,"model":model,"sma200":sma,"horizon":20,"stopMode":"hard_stop"})
    return result


def matches(case,policy):
    signal=case["signal"]
    if signal["family"]!=policy["family"] or policy["quality"]=="qualified" and signal["cohort"]!="qualified":return False
    if policy["sma200"]:
        c=case.get("context",{})
        if c.get("dailySma200") is None or c.get("dailyClose") is None or c["dailyClose"]<c["dailySma200"]:return False
    return True


def adapt(case,policy,cost_multiplier=1):
    e=case["entry"];p=case["paths"][f"{policy['model']}:{policy['stopMode']}:{policy['horizon']}"]
    costs={key:e["rules"][key] for key in ("spread_bps","slippage_bps","fee_per_order")}
    costs["spread_bps"]*=cost_multiplier;costs["slippage_bps"]*=cost_multiplier
    side=costs["spread_bps"]/20000+costs["slippage_bps"]/10000
    buy=e["entryPrice"]*(1+side) if e.get("entryPrice") is not None else None
    entry={"id":case["id"],"symbol":case["symbol"],"datasetId":case["datasetId"],"entryAt":e["entryAt"],
           "entryPrice":e.get("entryPrice")}
    path={"entryId":case["id"],"entryAt":e["entryAt"],"entryFill":buy,"initialStop":e["initialStop"],
          "initialRisk":buy-e["initialStop"] if buy and e.get("initialStop") else None,
          "exitAt":p.get("exitAt"),"exitFill":p["exitPrice"]*(1-side) if p.get("exitPrice") is not None else None,
          "exitReason":p.get("reason"),"status":p["status"],"reason":p.get("reason")}
    if e["status"]!="filled":path.update(status="unavailable",reason=e.get("reason") or e["status"])
    if path["status"]=="censored":path["missingAt"]=p.get("missingAt",p.get("lastObservedAt",e["entryAt"])+300)
    return entry,path,costs


def cash_audit(value,costs):
    """Separate cash movements and concurrency check; not a second simulate()."""
    moves=[];errors=[]
    for i,t in enumerate(value["trades"]):
        if t["quantity"]!=math.floor(t["quantity"]) or t["quantity"]<=0:errors.append("non_integer_quantity")
        if t["plannedRiskUSD"]>t["equityAtEntry"]*value["options"]["risk_fraction"]+1e-7:errors.append("risk_budget")
        if t["quantity"]*t["entryFill"]>t["equityAtEntry"]*value["options"]["allocation_fraction"]+1e-7:errors.append("allocation")
        moves.append((t["openedAt"],1,i,-t["quantity"]*t["entryFill"]-costs["fee_per_order"],t["symbol"]))
        if t["exitAt"] is not None:
            moves.append((t["exitAt"],0,i,t["quantity"]*t["exitFill"]-costs["fee_per_order"],t["symbol"]))
            expected=t["quantity"]*(t["exitFill"]-t["entryFill"])-2*costs["fee_per_order"]
            if abs(expected-t["netPnl"])>1e-7:errors.append("trade_cash")
    cash=value["initialCapital"];active={}
    for at,kind,i,amount,symbol in sorted(moves):
        if kind:
            if symbol in active.values():errors.append("duplicate_symbol")
            active[i]=symbol
        else:active.pop(i,None)
        cash+=amount
        if cash < -1e-7:errors.append("negative_cash")
        if len(active)>value["options"]["max_positions"]:errors.append("position_limit")
    if abs(cash-value["cash"])>1e-7:errors.append("terminal_cash")
    return {"passed":not errors,"errors":errors,"tradesChecked":len(value["trades"])}


def ledger(cases,contexts,phase,policy,*,cost_multiplier=1,options=None):
    selected=[c for c in cases if matches(c,policy)]
    triples=[adapt(c,policy,cost_multiplier) for c in selected]
    entries=[x[0] for x in triples];paths=[x[1] for x in triples]
    costs=triples[0][2] if triples else {"spread_bps":5.*cost_multiplier,"slippage_bps":5.*cost_multiplier,"fee_per_order":0.}
    if any(x[2]!=costs for x in triples):raise ValueError("Mixed execution costs")
    value=simulate(entries,paths,contexts,phase,costs,{**OPTIONS,**(options or {})})
    pnl=defaultdict(float)
    for trade in value["trades"]:pnl[trade["symbol"]]+=trade["netPnl"] or 0.
    positive=[v for v in pnl.values() if v>0]
    value.update(policy=deepcopy(policy),costMultiplier=cost_multiplier,eligibleSignals=len(selected),
        skippedReasons=dict(Counter(t["reason"] for t in value["skipped"])),pnlBySymbol=dict(pnl),
        positiveSymbols=len(positive),positiveProfitConcentration=max(positive)/sum(positive) if positive else None,
        meaning="Finite USD cash ledger, whole shares, one position per symbol; pilot fill times and costs. No future-path filtering.")
    value["audit"]=cash_audit(value,costs)
    if not value["audit"]["passed"]:raise AssertionError(value["audit"])
    return value


def compact(value):
    return {k:v for k,v in value.items() if k not in ("trades","skipped","equity")}


def development_gate(folds):
    complete=all(v["status"]!="incomplete" and not v["open"] for v in folds)
    returns=[v["markedReturnPct"] for v in folds]
    return (complete and sum(v["accepted"] for v in folds)>=20 and
            all(r is not None for r in returns) and sum(r>0 for r in returns)>=2 and
            sum(returns)>0 and min(v["max5mSampledDrawdownPct"] for v in folds)>=-10)


def test_gate(base,stress):
    checks={"complete":base["status"]!="incomplete" and not base["open"] and stress["status"]!="incomplete" and not stress["open"],
        "enoughTrades":base["accepted"]>=10,"netPositive":(base["markedReturnPct"] or 0)>0,
        "drawdown":base["max5mSampledDrawdownPct"]>=-10,"broadContributions":base["positiveSymbols"]>=4,
        "concentration":base["positiveProfitConcentration"] is not None and base["positiveProfitConcentration"]<=.5,
        "costStressPositive":(stress["markedReturnPct"] or 0)>0}
    return {"passed":all(checks.values()),"checks":checks}
