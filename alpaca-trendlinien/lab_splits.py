"""One common chronological plan for every study stock. Labels stop at phase ends."""
from datetime import datetime, timedelta
from models import DataError, NY
from market_calendar import calendar
from lab_data import session_bounds
from datasets import source_bars, digest


def sessions_between(first,last):
    rows=[]
    for year in range(int(first[:4]),int(last[:4])+1):
        lo=max(first,f"{year}-01-01");hi=min(last,f"{year}-12-31")
        if lo<=hi:rows.extend(str(d.date()) for d in calendar(year).sessions_in_range(lo,hi))
    return rows


def create(datasets,spec):
    rows=[source_bars(d)["4h"] for d in datasets]
    if not rows or any(not b for b in rows):raise DataError("Keine gemeinsamen Forschungsdaten.",422)
    first=max(datetime.fromtimestamp(b[0].time,NY).date()+timedelta(days=365) for b in rows)
    last=min(datetime.fromtimestamp(b[-1].end,NY).date() for b in rows)
    lab=spec["lab"]
    if lab["analysis_start"]:first=max(first,datetime.fromisoformat(lab["analysis_start"]).date())
    if lab["analysis_end"]:last=min(last,datetime.fromisoformat(lab["analysis_end"]).date())
    days=sessions_between(str(first),str(last)) if first<=last else []
    if len(days)<30:raise DataError("Mindestens 30 gemeinsame Sitzungen nach einem Jahr Vorlauf für drei Forschungsphasen erforderlich.",422)
    if lab["development_end"]:
        dev,val=lab["development_end"],lab["validation_end"]
        if not str(first)<=dev<val<str(last):raise DataError("Phasengrenzen müssen chronologisch im gemeinsamen Datenbestand liegen.",422)
        ndev=sum(d<=dev for d in days);nval=sum(d<=val for d in days)
    else:
        ndev=max(1,int(len(days)*lab["development_fraction"]))
        nval=int(len(days)*(1-spec["holdout_fraction"]))
    if not 1<=ndev<nval<len(days):raise DataError("Entwicklung, Validierung und Holdout benötigen getrennte Sitzungen.",422)
    phases={}
    for name,section in (("development",days[:ndev]),("validation",days[ndev:nval]),("holdout",days[nval:])):
        phases[name]={"startDate":section[0],"endDate":section[-1],"startAt":session_bounds(section[0])[0],
                      "endAt":session_bounds(section[-1])[1],"labelEndAt":session_bounds(section[-1])[1],"sessions":len(section)}
    return {"version":"tori-temporal-plan-1","phases":phases,"sessions":days,
            "dataset_ids":{d["material"]["symbol"]:d["id"] for d in datasets},
            "purge":"No outcome beyond phase end. Boundary entries remain censored; no future labels are used. Signal state replays from the common development start, including prior expired setup identities.",
            "fingerprint":digest({"days":days,"phases":phases})}


def walk_folds(plan,lab):
    days=[d for d in plan["sessions"] if d<=plan["phases"]["validation"]["endDate"]]
    train,test=lab["walk_train_sessions"],lab["walk_test_sessions"]
    folds=[]
    for boundary in range(train,len(days)-test+1,test):
        before,after=days[boundary-train:boundary],days[boundary:boundary+test]
        section=lambda seq:{"startDate":seq[0],"endDate":seq[-1],"startAt":session_bounds(seq[0])[0],"endAt":session_bounds(seq[-1])[1],"labelEndAt":session_bounds(seq[-1])[1]}
        folds.append({"id":len(folds)+1,"training":section(before),"evaluation":section(after)})
    return folds


def member(symbol,at,lab):
    if not lab["membership"]:return True
    day=str(datetime.fromtimestamp(at,NY).date())
    return any(r["symbol"]==symbol and (not r["start"] or r["start"]<=day) and (not r["end"] or day<=r["end"]) for r in lab["membership"])
