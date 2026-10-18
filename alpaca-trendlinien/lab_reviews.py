"""Blind historical review packs; outcome disclosure and later edits are audited."""
import json
import math
import random
import time
import uuid
from bisect import bisect_left, bisect_right

from database import connection
from datasets import digest, read_dataset
from lab_registry import audit
from models import DataError

VERSION="tori-blind-review-1"


def create(job_id,*,count=30,seed=0,profile="reference"):
    from jobs import get_job
    job=get_job(job_id)
    if type(count) is not int or not 1<=count<=100 or type(seed) is not int or not 0<=seed<=2147483647:
        raise DataError("Fallpaket benötigt 1–100 Fälle und einen gültigen Seed.",400)
    if job["status"]!="succeeded" or job["spec"].get("entry_mode")!="lab" or job["spec"]["lab"]["stage"]!="development":
        raise DataError("Verblindete Entwicklungsprüfung benötigt einen abgeschlossenen Labor-Entwicklungslauf. Validierung/Holdout bleiben davon getrennt.",409)
    if profile not in job["spec"]["lab"]["profiles"]:raise DataError("Profil gehört nicht zum Auftrag.",400)
    phase=job["manifest"]["temporalPlan"]["phases"]["development"]
    candidates={};rng=random.Random(f"{VERSION}|{seed}|{job_id}|{profile}")
    with connection() as db:
        for row in db.execute("SELECT result FROM trials WHERE job_id=? AND json_extract(result,'$.profile')=? ORDER BY id",(job_id,profile)):
            case=json.loads(row[0])
            for variant in case["variants"]:
                at=max(variant.get("signalAt",0),case.get("signal",{}).get("closedAt",0))
                if not at or not phase["startAt"]<=at<=phase["endAt"]:continue
                if not variant.get("checks"):continue
                # Confirmation is judged before future execution conditions,
                # never by later profit or whether an opening gap blocks a fill.
                confirmed="availableAt" in variant
                key=(case["datasetId"],at)
                value={"datasetId":case["datasetId"],"symbol":case["symbol"],"cutoff":at,
                       "engine":{"signal":confirmed,"family":variant["variant"],"caseId":case["id"]},"stratum":"confirmed" if confirmed else "rejected"}
                if key not in candidates or confirmed and not candidates[key]["engine"]["signal"]:candidates[key]=value
    # Add random closed source candles independently of their subsequent path.
    random_pool=[];random_seen=0
    for symbol in job["universe"]:
        item=next(s for s in job["symbols"] if s["symbol"]==symbol)
        data=read_dataset(item["dataset_id"])
        for b in data["material"]["bars"]["4h"]:
            if phase["startAt"]<=b["end"]<=phase["endAt"] and (item["dataset_id"],b["end"]) not in candidates:
                value={"datasetId":item["dataset_id"],"symbol":symbol,"cutoff":b["end"],"engine":{"signal":False,"family":None,"case":None},"stratum":"random"}
                random_seen+=1
                if len(random_pool)<count:random_pool.append(value)
                else:
                    position=rng.randrange(random_seen)
                    if position<count:random_pool[position]=value
    strata={name:[v for v in candidates.values() if v["stratum"]==name] for name in ("confirmed","rejected")}
    strata["random"]=random_pool
    for rows in strata.values():rng.shuffle(rows)
    chosen=[]
    while len(chosen)<count and any(strata.values()):
        for name in ("confirmed","rejected","random"):
            if strata[name] and len(chosen)<count:chosen.append(strata[name].pop())
    rng.shuffle(chosen)
    identity=uuid.uuid4().hex
    config={"seed":seed,"requestedCount":count,"profile":profile,"version":VERSION}
    manifest={"createdAt":time.time(),"count":len(chosen),"population":"development only; stratified diagnostic review, not population accuracy",
              "question":"Would the known closed chart justify a confirmed long signal now? Execution at the next available opening is a separate decision.",
              "blindness":"Review endpoints omit engine decisions and future bars until explicit reveal; external knowledge cannot be detected."}
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("INSERT INTO lab_reviews VALUES(?,?,?,?,?)",(identity,time.time(),job_id,json.dumps(config),json.dumps(manifest)))
        for sample in chosen:
            if "caseId" in sample["engine"]:
                case_id=sample["engine"].pop("caseId")
                row=db.execute("SELECT result FROM trials WHERE job_id=? AND id=?",(job_id,case_id)).fetchone()
                if not row:raise DataError("Quellfall ist nicht mehr verfügbar.",409)
                sample["engine"]["case"]=json.loads(row[0])
            case_id=digest({"pack":identity,"datasetId":sample["datasetId"],"cutoff":sample["cutoff"]})[:24]
            db.execute("INSERT INTO lab_review_cases(pack_id,id,sample) VALUES(?,?,?)",(identity,case_id,json.dumps(sample)))
        audit(db,identity,"review_created",{"job":job_id,"config":config,"count":len(chosen)})
    return get(identity)


def get(identity,*,offset=0,limit=50):
    if type(offset) is not int or offset<0 or type(limit) is not int or not 1<=limit<=100:raise DataError("Ungültige Fallpaketseite.",400)
    with connection() as db:
        db.execute("BEGIN")
        row=db.execute("SELECT * FROM lab_reviews WHERE id=?",(identity,)).fetchone()
        if not row:raise DataError("Fallpaket nicht gefunden.",404)
        total=db.execute("SELECT count(*) FROM lab_review_cases WHERE pack_id=?",(identity,)).fetchone()[0]
        cases=[]
        for r in db.execute("SELECT * FROM lab_review_cases WHERE pack_id=? ORDER BY id LIMIT ? OFFSET ?",(identity,limit,offset)):
            sample=json.loads(r["sample"])
            cases.append({"id":r["id"],"symbol":sample["symbol"],"cutoff":sample["cutoff"],"labelled":bool(r["label"]),"revealed":bool(r["revealed"]),"tainted":bool(r["tainted"])})
    return {"id":identity,"manifest":json.loads(row["manifest"]),"cases":cases,
            "page":{"offset":offset,"limit":limit,"total":total,"hasMore":offset+len(cases)<total}}


def _case(db,pack_id,case_id):
    row=db.execute("SELECT * FROM lab_review_cases WHERE pack_id=? AND id=?",(pack_id,case_id)).fetchone()
    if not row:raise DataError("Prüffall nicht gefunden.",404)
    return row,json.loads(row["sample"])


def view(pack_id,case_id,*,limit=750):
    from datasets import data_kind
    if type(limit) is not int or not 50<=limit<=1500:raise DataError("Chartumfang: 50–1500 Quellkerzen.",400)
    with connection() as db:row,sample=_case(db,pack_id,case_id)
    data=read_dataset(sample["datasetId"])
    sources={tf:[b for b in data["material"]["bars"][tf] if b["end"]<=sample["cutoff"]][-limit:] for tf in ("4h","1D")}
    result={"id":case_id,"packId":pack_id,"symbol":sample["symbol"],"cutoff":sample["cutoff"],"bars":sources,
            "feed":data["material"]["feed"],"adjustment":data["material"]["adjustment"],"dataKind":data_kind(data),
            "label":json.loads(row["label"]) if row["label"] else None,"revealed":bool(row["revealed"]),"tainted":bool(row["tainted"])}
    if row["revealed"]:result["engine"]=sample["engine"]
    return result


def label(pack_id,case_id,value):
    if not isinstance(value,dict) or set(value)!={"entry","red","green","reason"} or value["entry"] not in ("yes","no","wait") or not isinstance(value["reason"],str) or not 3<=len(value["reason"].strip())<=3000:
        raise DataError("Beurteilung benötigt entry yes/no/wait, rote/grüne Anker (oder null) und Begründung.",400)
    with connection() as db:
        db.execute("BEGIN IMMEDIATE");row,sample=_case(db,pack_id,case_id)
        bars=read_dataset(sample["datasetId"])["material"]["bars"]["4h"]
        known={b["time"] for b in bars if b["end"]<=sample["cutoff"]}
        for color in ("red","green"):
            ray=value[color]
            if ray is None:continue
            if not isinstance(ray,dict) or set(ray)!={"a_time","a_price","b_time","b_price"}:raise DataError("Linie benötigt genau zwei bekannte Anker.",400)
            if any(type(ray[k]) is not int or ray[k] not in known for k in ("a_time","b_time")) or ray["a_time"]>=ray["b_time"]:
                raise DataError("Anker müssen verschiedene, chronologisch bekannte Quellkerzen sein.",400)
            if any(type(ray[k]) not in (int,float) or not math.isfinite(ray[k]) or ray[k]<=0 for k in ("a_price","b_price")):
                raise DataError("Ankerpreise müssen endlich und positiv sein.",400)
        changed=row["label"] is None or json.loads(row["label"])!=value
        tainted=bool(row["tainted"] or row["revealed"] and changed)
        if changed:
            db.execute("UPDATE lab_review_cases SET label=?,tainted=? WHERE pack_id=? AND id=?",(json.dumps(value,allow_nan=False),int(tainted),pack_id,case_id))
            audit(db,pack_id,"review_label",{"case":case_id,"before":json.loads(row["label"]) if row["label"] else None,"label":value,"tainted":tainted})
    return view(pack_id,case_id)


def reveal(pack_id,case_id):
    with connection() as db:
        db.execute("BEGIN IMMEDIATE");row,sample=_case(db,pack_id,case_id)
        if not row["label"]:raise DataError("Vor Offenlegung zuerst eine eigene Beurteilung speichern.",409)
        if not row["revealed"]:
            record=db.execute("SELECT job_id FROM lab_reviews WHERE id=?",(pack_id,)).fetchone()
            job=db.execute("SELECT spec,manifest FROM jobs WHERE id=?",(record[0],)).fetchone()
            spec,metadata=json.loads(job[0]),json.loads(job[1])
            phase=metadata["temporalPlan"]["phases"]["development"]
            sample["engine"]["reviewPath"]=review_path(sample,json.loads(row["label"]),spec,phase)
            db.execute("UPDATE lab_review_cases SET sample=? WHERE pack_id=? AND id=?",(json.dumps(sample,allow_nan=False),pack_id,case_id))
            db.execute("UPDATE lab_review_cases SET revealed=1 WHERE pack_id=? AND id=?",(pack_id,case_id))
            audit(db,pack_id,"review_revealed",{"case":case_id,"labelHash":digest(json.loads(row["label"]))})
    return view(pack_id,case_id)


def review_path(sample,label,spec,phase):
    """A random no-signal case still has an explicitly hypothetical future path.

    This is created only on disclosure, never inserted into accepted trials or
    portfolio candidates. The human line is fixed at the known review cutoff.
    """
    from lab_metrics import OutcomeEvaluator
    evaluator=OutcomeEvaluator(read_dataset(sample["datasetId"]))
    fine=evaluator.fine
    available=sample["cutoff"]+spec["latency_seconds"]
    i=bisect_left(evaluator.fine_times,available)
    note="Hypothetical review path from first available open after cutoff + latency; not an accepted engine entry or portfolio trade"
    if i>=len(fine) or fine[i].time>phase["endAt"]:return {"available":False,"reason":"no_future_opening_in_development_phase","assumption":note}
    stop=None;ray=label["green"]
    if ray:
        bars=evaluator.sources["4h"];times=[b.time for b in bars];ends=[b.end for b in bars]
        a,b=bisect_left(times,ray["a_time"]),bisect_left(times,ray["b_time"])
        last=bisect_right(ends,sample["cutoff"])-1
        stop=ray["a_price"]+(ray["b_price"]-ray["a_price"])*(last-a)/(b-a)
    point={"available":True,"entryAt":fine[i].time,"entryPrice":fine[i].open,"initialStop":stop,"assumption":note}
    point["forward"]=evaluator.evaluate(point,spec["horizons"],phase["labelEndAt"] if "labelEndAt" in phase else phase["endAt"])
    return point


def compare(pack_id):
    get(pack_id,limit=1)
    matrix={"human_yes_engine_yes":0,"human_yes_engine_no":0,"human_no_engine_yes":0,"human_no_engine_no":0}
    counts={"unlabelled":0,"notRevealed":0,"tainted":0,"wait":0,"compared":0};anchors=[]
    with connection() as db:
        for row in db.execute("SELECT * FROM lab_review_cases WHERE pack_id=? ORDER BY id",(pack_id,)):
            if not row["label"]:counts["unlabelled"]+=1;continue
            if row["tainted"]:counts["tainted"]+=1;continue
            if not row["revealed"]:counts["notRevealed"]+=1;continue
            value=json.loads(row["label"]);sample=json.loads(row["sample"])
            if value["entry"]=="wait":counts["wait"]+=1;continue
            matrix[f"human_{value['entry']}_engine_{'yes' if sample['engine']['signal'] else 'no'}"]+=1;counts["compared"]+=1
            engine_case=sample["engine"]["case"]
            if engine_case:
                for color in ("red","green"):
                    actual=engine_case["frozen"].get(color);human=value[color]
                    anchors.append({"caseId":row["id"],"color":color,"engineLinePresent":bool(actual),"exactAnchorMatch":bool(actual) and human is not None and all(human[k]==actual[k] for k in ("a_time","a_price","b_time","b_price"))})
    return {"matrix":matrix,"counts":counts,"anchors":anchors,
            "interpretation":"Descriptive alignment of human and engine in a stratified development pack, not predictive accuracy. Only disclosed, untainted yes/no judgements are compared; approximate line equivalence requires manual inspection."}
