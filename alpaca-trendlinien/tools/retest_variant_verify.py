"""Independent event/Decimal oracle for three exits and cash/risk auditing."""
from datetime import datetime,timedelta
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from datasets import read_dataset,source_bars,digest
from lab_data import session_bounds
from lab_splits import sessions_between
from strategy_research import write_json
from strategy_verify import grid,audit_portfolio
from models import NY
from tools.retest_exit_verify import read,checked,close,audit_record


def next_open(known):
    day=datetime.fromtimestamp(known,NY).date()
    for d in sessions_between(str(day),str(day+timedelta(days=14))):
        opened,closed=session_bounds(d)
        for t in range(opened,closed,300):
            if t >= known+300:
                return t
    raise AssertionError("No next session")


def audit_variant(record,sources,phase_end,variant):
    e,c=record["entry"],record["contract"]
    actual=record["paths"][variant]
    at=e["entryAt"]
    day=datetime.fromtimestamp(at,NY).date()
    days=sessions_between(str(day+timedelta(days=1)),str(day+timedelta(days=80)))
    planned,progress=[session_bounds(days[n-1])[1] for n in (10,5)]
    fine={b.time:b for b in sources["5m"]}
    slots=[]
    if variant != "time_no_progress":
        for d in sessions_between(str(day),str(datetime.fromtimestamp(min(planned,phase_end),NY).date())):
            opened,closed=session_bounds(d)
            for start in range(opened,closed,14400):
                stop=min(start+14400,closed)
                if at < stop <= min(planned,phase_end):
                    slots.append((start,stop))
    source_index={(b.time,b.end):i for i,b in enumerate(sources["4h"])}
    stop=c["initialStop"]
    highest=e["entryPrice"]
    active=False
    pending=None
    j=0
    events=[]
    expected=None
    missing=None
    source_missing=None
    costs=c["costs"]
    qty=(costs["notional"]-costs["fee_per_order"])/c["entryFill"]
    for stamp in grid(at,min(planned,phase_end)):
        if stamp not in fine:
            missing=("missing_fine_path",stamp)
            break
        b=fine[stamp]
        if b.open <= stop:
            expected=(b,b.open,"hard_stop_gap",True)
            break
        if pending and pending[0] <= stamp:
            expected=(b,b.open,pending[1],True)
            break
        while j < len(slots) and slots[j][1]+300 <= stamp:
            slot=slots[j]
            j+=1
            if slot not in source_index:
                missing=("missing_source_path",stamp)
                source_missing=slot[1]
                break
            i=source_index[slot]
            bar=sources["4h"][i]
            effective=next_open(bar.end)
            if variant == "failed_retest":
                red=e["red"]
                boundary=red["a_price"]+red["slope"]*(i-red["a_index"])-e["signalWidth"]
                if bar.close < boundary:
                    pending=(effective,"failed_retest")
                    events.append({"kind":"failed_retest","knownAt":bar.end,"effectiveAt":effective,
                        "sourceIndex":i,"close":bar.close,"lowerZone":boundary})
                    break
            else:
                highest=max(highest,bar.close)
                liquidation=bar.close*(1-costs["side_cost"])-c["entryFill"]-2*costs["fee_per_order"]/qty
                if not active and liquidation >= c["initialRisk"]:
                    active=True
                    events.append({"kind":"gain_activate","knownAt":bar.end,"effectiveAt":effective,
                        "sourceIndex":i,"close":bar.close,"netR":liquidation/c["initialRisk"]})
                if active:
                    rows=sources["4h"][max(0,i-14):i+1]
                    vol=sum(max(z.high-z.low,abs(z.high-a.close),abs(z.low-a.close)) for a,z in zip(rows,rows[1:]))/14 if len(rows)==15 else None
                    if vol is None:
                        missing=("unknown_atr",stamp)
                        break
                    raised=max(stop,highest-2*vol)
                    if raised > stop+1e-8:
                        events.append({"kind":"atr_stop_raise","knownAt":bar.end,"effectiveAt":effective,
                            "sourceIndex":i,"peakClose":highest,"atr":vol,"previousHardStop":stop,"hardStop":raised})
                        stop=raised
        if missing:
            break
        if b.open <= stop:
            expected=(b,b.open,"hard_stop_gap",True)
        elif pending and pending[0] <= stamp:
            expected=(b,b.open,pending[1],True)
        elif b.low <= stop:
            expected=(b,stop,"hard_stop",False)
        elif b.end == planned:
            expected=(b,b.close,"time",False)
        if expected:
            break
        if variant == "time_no_progress" and b.end == progress:
            pnl=qty*(b.close*(1-costs["side_cost"])-c["entryFill"])-2*costs["fee_per_order"]
            exit_now=pnl <= 0
            effective=next_open(b.end) if exit_now else None
            events.append({"kind":"progress_check","knownAt":b.end,"effectiveAt":effective,"netPnl":pnl,"exit":exit_now})
            if exit_now:
                pending=(effective,"time_no_progress")
    assert len(events)==len(actual["events"])
    for expected_event,reported in zip(events,actual["events"]):
        assert set(expected_event)==set(reported)
        for k,value in expected_event.items():
            if type(value) in (float,int):close(reported[k],value)
            else:assert reported[k]==value,k
    if expected is None:
        assert actual["status"]=="censored"
        if missing:
            assert (actual["reason"],actual["missingAt"])==missing
            if source_missing:assert actual["missingSourceAt"]==source_missing
        else:
            assert actual["reason"]=="phase_boundary" and planned>phase_end
        return
    b,price,reason,at_open=expected
    assert actual["status"]=="closed" and actual["exitReason"]==reason and actual["atOpen"]==at_open
    assert actual["fillBarAt"]==b.time and actual["exitAt"]==b.end
    close(actual["exitPrice"],price)
    side=Decimal(str(costs["spread_bps"]))/20000+Decimal(str(costs["slippage_bps"]))/10000
    buy=Decimal(str(e["entryPrice"]))*(1+side)
    sell=Decimal(str(price))*(1-side)
    quantity=(Decimal(str(costs["notional"]))-Decimal(str(costs["fee_per_order"])))/buy
    pnl=quantity*(sell-buy)-2*Decimal(str(costs["fee_per_order"]))
    close(actual["netPnl"],pnl)
    close(actual["netReturnPct"],pnl/Decimal(str(costs["notional"]))*100)
    close(actual["netR"],pnl/(quantity*(buy-Decimal(str(c["initialStop"])))))
    close(actual["finalHardStop"],stop)


def run(root,data):
    root=Path(root).resolve()
    os.environ["TORI_DATA_DIR"]=str(Path(data).resolve())
    contract=read(root/"contract.json")
    code=Path(__file__).resolve().parents[1]
    assert all(hashlib.sha256((code/n).read_bytes()).hexdigest()==v for n,v in contract["engine"].items())
    counts={"records":0,"uniqueFixedPaths":0,"candidatePaths":0,"portfolios":0,"events":0}
    reference={}
    for variant in contract["variants"]:
        for stage,phase in contract["phases"].items():
            results=checked(root/variant/(stage+"-results.json"))
            sources={}
            records=[]
            with patch("alpaca._request",side_effect=AssertionError("Offline verifier")):
                for file in sorted((root/variant/stage).glob("*.json")):
                    block=checked(file)
                    assert block["contractHash"]==digest(contract)
                    for record in block["records"]:
                        identity=record["entry"]["datasetId"]
                        if identity not in sources:
                            sources[identity]={tf:[b for b in rows if b.end<=phase["endAt"]] for tf,rows in source_bars(read_dataset(identity)).items()}
                        key=(stage,record["entry"]["id"])
                        if key not in reference:
                            audit_record({**record,"paths":{"fixed":record["paths"]["fixed"]}},sources[identity],phase["endAt"])
                            reference[key]=record["paths"]["fixed"]
                            counts["uniqueFixedPaths"]+=1
                        else:assert record["paths"]["fixed"]==reference[key]
                        audit_variant(record,sources[identity],phase["endAt"],variant)
                        records.append(record)
                        counts["records"]+=1
                        counts["candidatePaths"]+=1
                        counts["events"]+=len(record["paths"][variant]["events"])
                for key,portfolio in results["portfolios"].items():
                    geometry,model=key.split("/")
                    selected=[r for r in records if r["entry"]["model"]==geometry and r["history"]["complete"] and r["calendarFits"]]
                    audit_portfolio(portfolio,[r["entry"] for r in selected],[r["paths"][model] for r in selected],sources,phase,contract["costs"])
                    counts["portfolios"]+=1
            for key,group in results["groups"].items():
                geometry,quality=key.split("/")
                chosen=[r for r in records if r["entry"]["model"]==geometry and r["calendarFits"] and r["history"]["complete"]==(quality=="complete_history")]
                assert len(chosen)==group["cases"]
                paired=[r for r in chosen if all(r["paths"][m]["status"]=="closed" for m in ("fixed",variant))]
                assert len(paired)==group["pairedClosed"]
                if paired:close(group["meanDeltaR"],sum(Decimal(str(r["paths"][variant]["netR"]))-Decimal(str(r["paths"]["fixed"]["netR"])) for r in paired)/len(paired))
                for model in ("fixed",variant):
                    closed=[r["paths"][model] for r in chosen if r["paths"][model]["status"]=="closed"]
                    assert len(closed)==group["models"][model]["closed"]
                    if closed:close(group["models"][model]["meanR"],sum(Decimal(str(p["netR"])) for p in closed)/len(closed))
    output={"contractHash":digest(contract),"verified":counts,"verifierHash":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "meaning":"Model timing/arithmetic and cash/risk consistency, not independent unseen-market replication."}
    write_json(root/"verification.json",output)
    print(json.dumps(output))


if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",required=True)
    p.add_argument("--data",required=True)
    args=p.parse_args()
    run(args.root,args.data)
