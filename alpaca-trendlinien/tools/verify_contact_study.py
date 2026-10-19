"""Independent arithmetic/calendar/fill audit of a completed contact study export."""
import argparse
from datetime import datetime, timedelta
from decimal import Decimal
from functools import lru_cache
import json
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def verify(root,label):
    os.environ["TORI_DATA_DIR"]=str(root/"data")
    from datasets import read_dataset, data_kind
    from models import NY
    from market_calendar import calendar
    from database import connection
    with connection() as db:
        opened=db.execute("SELECT COUNT(*) FROM lab_final_access").fetchone()[0]
        attempts=db.execute("SELECT COUNT(*) FROM lab_attempts WHERE stage='holdout'").fetchone()[0]
    assert opened==attempts==0,"Holdout was opened in the supposedly reserved research root"
    report=json.loads((root/(label+".json")).read_text("utf-8"))
    stage=report["spec"]["lab"]["stage"]
    phase=report["manifest"]["temporalPlan"]["phases"][stage]
    data={s:read_dataset(i) for s,i in report["spec"]["dataset_ids"].items()}
    assert all(data_kind(d)=="market" and "5m" in d["material"]["bars"] for d in data.values())
    daily={s:{str(datetime.fromtimestamp(b["time"],NY).date()):b for b in d["material"]["bars"]["1D"]} for s,d in data.items()}
    fine={s:{b["time"]:b for b in d["material"]["bars"]["5m"]} for s,d in data.items()}
    @lru_cache(maxsize=None)
    def independent(symbol,at,price,h):
        day=datetime.fromtimestamp(at,NY).date();end=day+timedelta(days=100);days=[]
        for year in range(day.year,end.year+1):
            lo=max(day+timedelta(days=1),day.replace(year=year,month=1,day=1))
            hi=min(end,day.replace(year=year,month=12,day=31))
            if lo<=hi:days += [str(s.date()) for s in calendar(year).sessions_in_range(str(lo),str(hi))]
        rows=daily[symbol];target=days[h-1]
        complete=all(d in rows and rows[d]["end"]<=phase["labelEndAt"] for d in days[:h])
        value=(Decimal(str(rows[target]["close"]))/Decimal(str(price))-1)*100 if complete else None
        return target,complete,value
    entries=0;outcomes=0;incomplete=0
    controls_checked=0;pooled={}
    for profile,families in report["points"].items():
        for family,points in families.items():
            assert len({(p["symbol"],p["entryAt"]) for p in points})==len(points)
            counts={h:{"n":0,"positive":0,"negative":0,"flat":0,"sum":Decimal(0)} for h in (5,10,20)}
            for p in points:
                entries+=1
                pooled.setdefault(profile,{}).setdefault((p["symbol"],p["entryAt"]),p)
                assert phase["startAt"]<=p["entryAt"]<=phase["endAt"]
                assert p["entryAt"]>=p["signalAt"]+report["spec"]["latency_seconds"]
                assert p["entryPrice"]==fine[p["symbol"]][p["entryAt"]]["open"]
                for control in p.get("controls",[]):
                    assert control["entryPrice"]==fine[p["symbol"]][control["entryAt"]]["open"]
                    assert phase["startAt"]<=control["entryAt"]<=phase["endAt"]
                    for ch in (5,10,20):
                        target,complete,value=independent(p["symbol"],control["entryAt"],control["entryPrice"],ch)
                        got=control["forward"][str(ch)]
                        assert got["targetDate"]==target and got["complete"]==complete
                        if complete:assert abs(float(value)-got["return_pct"])<1e-10
                        controls_checked+=1
                day=datetime.fromtimestamp(p["entryAt"],NY).date();end=day+timedelta(days=100)
                days=[]
                for year in range(day.year,end.year+1):
                    lo=max(day+timedelta(days=1),day.replace(year=year,month=1,day=1))
                    hi=min(end,day.replace(year=year,month=12,day=31))
                    if lo<=hi:days += [str(s.date()) for s in calendar(year).sessions_in_range(str(lo),str(hi))]
                for h in (5,10,20):
                    o=p["forward"][str(h)];target=days[h-1];rows=daily[p["symbol"]]
                    complete=all(d in rows and rows[d]["end"]<=phase["labelEndAt"] for d in days[:h])
                    assert o["targetDate"]==target and o["complete"]==complete
                    if not complete:incomplete+=1;continue
                    outcomes+=1
                    value=(Decimal(str(rows[target]["close"]))/Decimal(str(p["entryPrice"]))-1)*100
                    assert abs(float(value)-o["return_pct"])<1e-10
                    bucket=counts[h];bucket["n"]+=1;bucket["sum"]+=value
                    bucket["positive" if value>0 else "negative" if value<0 else "flat"]+=1
            reported=next(r for r in report["rows"] if r["profile"]==profile and r["family"]==family)
            for h,c in counts.items():
                got=reported["horizons"][str(h)]
                for key in ("n","positive","negative","flat"):assert got[key]==c[key]
                if c["n"]:assert abs(got["mean_pct"]-float(c["sum"]/c["n"]))<1e-10
                assert got["incomplete"]==len(points)-c["n"]
    for c in report["contactObservations"]:
        if c["measurement"]:
            assert c["measurement"]["knownAt"]<c["signalAt"]
            a=c["measurement"]["atrAtSetup"]
            assert c["measurement"]["tolerance"]==max(.01,a*c["measurement"]["atrFraction"]) if a else c["measurement"]["tolerance"] is None
    union_path=root/"stock-time-summary.json";union_checks=0
    if union_path.exists():
        summaries=json.loads(union_path.read_text("utf-8"))
        for profile,points in pooled.items():
            row=next(r for r in summaries if r["run"]==label and r["profile"]==profile)
            assert row["n"]==len(points)
            for h in (5,10,20):
                values=[v for p in points.values() if (v:=independent(p["symbol"],p["entryAt"],p["entryPrice"],h)[2]) is not None]
                got=row["horizons"][str(h)]
                assert got["n"]==len(values) and got["positive"]==sum(v>0 for v in values)
                assert got["incomplete"]==len(points)-len(values)
                if values:assert abs(got["mean_pct"]-float(sum(values)/len(values)))<1e-10
                union_checks+=1
    result={"label":label,"entriesCheckedAcrossProfilesAndFamilies":entries,"completeHorizonsRecomputed":outcomes,
            "incompleteHorizonsChecked":incomplete,"controlHorizonsChecked":controls_checked,"pooledHorizonSummariesChecked":union_checks,
            "priceArithmetic":"independent Decimal on pinned daily closes",
            "fillCheck":"stored 5m opening price after confirmed signal plus latency", "holdoutOpened":bool(opened or attempts),
            "passed":True}
    (root/(label+".verification.json")).write_text(json.dumps(result,indent=2),"utf-8")
    print(json.dumps(result))


def verify_release(root):
    """Reload immutable original contracts; never mutate their profile lists."""
    os.environ["TORI_DATA_DIR"]=str(root/"data")
    import jobs
    release=json.loads((root/"release-verification.json").read_text("utf-8"))
    assert release["manifest"]["engineHash"]==jobs.engine_hash(),"Release audit must cover current engine code"
    def physical(report,profile):
        return {f:{(v["symbol"],v["entryAt"]):(v["entryPrice"],{h:(o["complete"],o.get("return_pct")) for h,o in v["forward"].items()})
                   for v in points} for f,points in report["points"].get(profile,{}).items()}
    profiles=set();compared=0
    for n in (1,2,3):
        original=json.loads((root/f"round-{n}.json").read_text("utf-8"))
        for profile in original["spec"]["lab"]["profiles"]:
            assert physical(original,profile)==physical(release,profile),(n,profile)
            profiles.add(profile);compared+=1
    result={"passed":True,"profilesReproduced":len(profiles),"profileRoundComparisons":compared,
            "engineHash":jobs.engine_hash(),"jobId":release["jobId"],
            "purpose":"Reproduction of final code; no fourth optimization loop"}
    (root/"release-verification-audit.json").write_text(json.dumps(result,indent=2),"utf-8")
    print(json.dumps(result))


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",required=True)
    group=p.add_mutually_exclusive_group(required=True);group.add_argument("--label");group.add_argument("--release",action="store_true")
    a=p.parse_args()
    if a.release:verify_release(Path(a.root).resolve())
    else:verify(Path(a.root).resolve(),a.label)
