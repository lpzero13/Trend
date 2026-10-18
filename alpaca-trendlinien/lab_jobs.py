"""Durable orchestration for registered lab experiments, using the existing queue."""
import json
import time

from database import connection
from datasets import read_dataset
from lab_data import import_dataset, require_convention
from lab_engine import scan_stock, training_choice
from lab_profiles import VERSION
from lab_registry import bind_data, get as experiment, register, start_attempt
from lab_splits import create, walk_folds
from models import DataError


class Sink:
    """Same transaction stores stable journal events and the newest case state."""
    def __init__(self,job_id,dataset_id):
        self.job_id,self.dataset_id=job_id,dataset_id;self.pending=[]

    def __call__(self,item):
        self.pending.append(item)
        if len(self.pending)>=100:self.flush()

    def flush(self):
        if not self.pending:return
        with connection() as db:
            for item in self.pending:
                if "event" in item:
                    event=item["event"]
                    db.execute("INSERT OR IGNORE INTO events VALUES(?,?,?,?)",(self.job_id,event["id"],self.dataset_id,json.dumps(event,allow_nan=False)))
                else:
                    case=item["trial"]
                    db.execute("INSERT INTO trials VALUES(?,?,?) ON CONFLICT(job_id,id) DO UPDATE SET result=excluded.result",(self.job_id,case["id"],json.dumps(case,allow_nan=False)))
            db.execute("UPDATE jobs SET updated=? WHERE id=?",(time.time(),self.job_id))
        self.pending.clear()


def run(job,stop=None):
    from jobs import engine_hash
    from operations import phase, record_dataset
    identity=job["id"];spec=job["spec"];lab=spec["lab"]
    # Scheduled jobs are registered here; interactive submit already registers.
    if not lab["experiment_id"]:
        lab["experiment_id"]=register(spec,engine_hash())
        with connection() as db:
            db.execute("UPDATE jobs SET spec=? WHERE id=?",(json.dumps(spec),identity))
    record=experiment(lab["experiment_id"])
    if record["engine_hash"]!=engine_hash():raise DataError("Experiment benötigt seine ursprüngliche Engine-Version.",409)
    if job["universe"] is None:
        if record["datasets"]:universe=sorted(record["plan"]["dataset_ids"])
        elif spec.get("universe")=="all":
            from assets import directory
            catalog,stale=directory()
            if stale:raise DataError("Aktienkatalog ist veraltet; Labor pausiert den Import.",422)
            universe=sorted({item["symbol"] for item in catalog["items"]})
        else:universe=spec["symbols"]
        with connection() as db:db.execute("UPDATE jobs SET universe=? WHERE id=?",(json.dumps(universe),identity))
    else:universe=job["universe"]
    if record["datasets"]:
        expected=set(universe)|({lab["benchmark_symbol"]} if lab["benchmark_symbol"] else set())
        if set(record["datasets"])!=expected:raise DataError("Universum weicht vom gebundenen Experiment ab.",409)
    last=[0,False];progress_at=[0]
    def interrupted():
        if stop and stop.is_set():return True
        if time.monotonic()-last[0]>.5:
            with connection() as db:
                status=db.execute("SELECT status FROM jobs WHERE id=?",(identity,)).fetchone()[0]
                db.execute("UPDATE jobs SET updated=? WHERE id=?",(time.time(),identity))
            last[:]=[time.monotonic(),status=="cancel_requested"]
        return last[1]
    def progress(**detail):
        if time.monotonic()-progress_at[0]>=2:
            phase(identity,"lab_scan",**detail);progress_at[0]=time.monotonic()
    symbols=sorted(set(universe)|({lab["benchmark_symbol"]} if lab["benchmark_symbol"] else set()))
    pinned=record["datasets"] or {};datasets={};conventions={}
    from storage import preflight
    preflight(history_days=spec["history_days"]*4,symbols=sum(s not in pinned and s not in spec.get("dataset_ids",{}) for s in symbols))
    for symbol in symbols:
        if interrupted():return False
        with connection() as db:
            saved=db.execute("SELECT * FROM symbols WHERE job_id=? AND symbol=?",(identity,symbol)).fetchone()
            db.execute("INSERT OR IGNORE INTO symbols(job_id,symbol) VALUES(?,?)",(identity,symbol))
            db.execute("UPDATE jobs SET current_symbol=? WHERE id=?",(symbol,identity))
        dataset_id=pinned.get(symbol) or (saved["dataset_id"] if saved else None) or spec.get("dataset_ids",{}).get(symbol)
        if not dataset_id:
            phase(identity,"lab_import",symbol=symbol)
            dataset_id=import_dataset(symbol,spec["history_days"],feed=lab["feed"],adjustment=lab["adjustment"],
                progress=lambda tf,pages,rows:progress(symbol=symbol,interval=tf,pages=pages,rows=rows))
        data=read_dataset(dataset_id)
        if data["material"]["symbol"]!=symbol:raise DataError("Dataset gehört zu einem anderen Symbol.",422)
        conventions[symbol]=require_convention(data,allow_native=lab["allow_native"])
        if not lab["allow_native"] and (data["material"]["feed"]!=lab["feed"] or data["material"]["adjustment"]!=lab["adjustment"]):
            raise DataError("Dataset weicht von Feed/Kursbereinigung des Experiments ab.",422)
        record_dataset(data)
        rows=data["material"]["bars"]["4h"]
        datasets[symbol]={"id":data["id"],"material":{"symbol":symbol,"bars":{"4h":[rows[0],rows[-1]]}},"descriptorOnly":True}
        del data
        with connection() as db:db.execute("UPDATE symbols SET dataset_id=?,error=NULL WHERE job_id=? AND symbol=?",(dataset_id,identity,symbol))
    plan=record["plan"] or create([datasets[s] for s in universe],spec)
    ids={s:datasets[s]["id"] for s in symbols}
    bind_data(lab["experiment_id"],ids,plan)
    start_attempt(lab["experiment_id"],identity,lab["stage"],confirm_final_test=lab["confirm_final_test"])
    with connection() as db:
        metadata=json.loads(db.execute("SELECT manifest FROM jobs WHERE id=?",(identity,)).fetchone()[0])
        metadata.update(labVersion=VERSION,experimentId=lab["experiment_id"],temporalPlan=plan,dataConventions=conventions,
                        universe={"symbols":universe,"basis":"explicit historical membership" if lab["membership"] else "present-day list; survivorship bias possible","membership":lab["membership"]},
                        execution="first available fine-bar open after closed source confirmation + latency; simulated fills")
        db.execute("UPDATE jobs SET manifest=? WHERE id=?",(json.dumps(metadata),identity))
    from lab_metrics import OutcomeEvaluator
    benchmark=OutcomeEvaluator(read_dataset(datasets[lab["benchmark_symbol"]]["id"])) if lab["benchmark_symbol"] else None
    if lab["stage"]=="walk_forward":
        folds=walk_folds(plan,lab)
        if not folds:raise DataError("Zu wenig gemeinsame Historie für die vorregistrierten Walk-forward-Fenster.",422)
        for fold in folds:
            choice_key=f"walk:{fold['id']}:choice"
            for section in ("training","evaluation"):
                section_id=f"walk:{fold['id']}:{section}"
                if section=="evaluation":
                    with connection() as db:
                        rows=[json.loads(r[0]) for r in db.execute("SELECT result FROM trials WHERE job_id=? AND json_extract(result,'$.labPhase')=?",(identity,f"walk:{fold['id']}:training"))]
                    choice=training_choice(rows,spec)
                    # A choice is fully derived from training and journalled before evaluation.
                    with connection() as db:
                        event={"id":choice_key,"kind":"lab_walk_selection","time":fold["training"]["endAt"],"closedAt":fold["training"]["endAt"],"fold":fold["id"],"choice":choice}
                        db.execute("INSERT OR IGNORE INTO events VALUES(?,?,?,?)",(identity,choice_key,None,json.dumps(event)))
                    if choice["profile"] is None:continue
                    profiles=[choice["profile"]]
                else:profiles=lab["profiles"]
                if not _scan(universe,datasets,spec,{**fold[section],"historyStartAt":plan["phases"]["development"]["startAt"]},section_id,profiles,benchmark,identity,interrupted,progress):return False
    else:
        selected=[record["selection"]["profile"]] if lab["stage"]=="holdout" else lab["profiles"]
        if not _scan(universe,datasets,spec,{**plan["phases"][lab["stage"]],"historyStartAt":plan["phases"]["development"]["startAt"]},lab["stage"],selected,benchmark,identity,interrupted,progress):return False
    with connection() as db:db.execute("UPDATE symbols SET done=1 WHERE job_id=?",(identity,))
    return True


def _scan(universe,datasets,spec,phase,section_id,profiles,benchmark,job_id,interrupted,progress):
    for symbol in universe:
        if interrupted():return False
        with connection() as db:
            row=db.execute("SELECT plan FROM symbols WHERE job_id=? AND symbol=?",(job_id,symbol)).fetchone()
            saved=json.loads(row[0]) if row[0] else {}
        key=f"{section_id}|{','.join(profiles)}"
        if saved.get("sections",{}).get(key,{}).get("complete"):continue
        sink=Sink(job_id,datasets[symbol]["id"])
        result=scan_stock(read_dataset(datasets[symbol]["id"]),spec,phase,phase_id=section_id,profiles=profiles,benchmark=benchmark,emit=sink,cancelled=interrupted,progress=progress)
        sink.flush()
        saved.setdefault("sections",{})[key]=result
        with connection() as db:db.execute("UPDATE symbols SET plan=? WHERE job_id=? AND symbol=?",(json.dumps(saved),job_id,symbol))
        if not result["complete"]:return False
    if spec["lab"]["execution"]["enabled"]:
        from lab_execution import simulate
        for profile in profiles:
            for family in ("breakout","horizontal","retest"):
                if interrupted():return False
                with connection() as db:
                    if db.execute("SELECT 1 FROM lab_simulations WHERE job_id=? AND section=? AND profile=? AND family=?",(job_id,section_id,profile,family)).fetchone():continue
                    cases=[json.loads(r[0]) for r in db.execute("SELECT result FROM trials WHERE job_id=? AND json_extract(result,'$.labPhase')=? AND json_extract(result,'$.profile')=? ORDER BY id",(job_id,section_id,profile))]
                progress(symbol="portfolio",profile=profile,section=section_id,family=family)
                result=simulate(cases,{v["id"]:v for v in datasets.values()},spec["lab"]["execution"],phase,profile=profile,family=family)
                with connection() as db:db.execute("INSERT OR IGNORE INTO lab_simulations VALUES(?,?,?,?,?)",(job_id,section_id,profile,family,json.dumps(result,allow_nan=False)))
    return True


def report(job,offset=0,limit=250,entry_filter="all"):
    from lab_metrics import summarize
    if entry_filter not in ("all","entries"):raise DataError("Ungültiger Einstiegsfilter.",400)
    identity=job["id"];spec=job["spec"]
    with connection() as db:
        db.execute("BEGIN")
        where="job_id=?"
        if entry_filter=="entries":where+=" AND EXISTS(SELECT 1 FROM json_each(json_extract(trials.result,'$.variants')) WHERE json_extract(value,'$.status')='observed')"
        total=db.execute(f"SELECT count(*) FROM trials WHERE {where}",(identity,)).fetchone()[0]
        rows=[json.loads(r[0]) for r in db.execute(f"SELECT result FROM trials WHERE {where} ORDER BY json_extract(result,'$.labPhase'),json_extract(result,'$.startAt'),id LIMIT ? OFFSET ?",(identity,limit,offset))]
        sections=[r[0] for r in db.execute("SELECT DISTINCT json_extract(result,'$.labPhase') FROM trials WHERE job_id=? ORDER BY 1",(identity,))]
        summaries={}
        for section in sections:
            records=(json.loads(r[0]) for r in db.execute("SELECT result FROM trials WHERE job_id=? AND json_extract(result,'$.labPhase')=? ORDER BY id",(identity,section)))
            summaries[section]=summarize(records,spec["horizons"],seed=spec["seed"],samples=spec["lab"]["bootstrap_samples"])
        choices=[json.loads(r[0]) for r in db.execute("SELECT event FROM events WHERE job_id=? AND json_extract(event,'$.kind')='lab_walk_selection' ORDER BY json_extract(event,'$.fold')",(identity,))]
        portfolios=[{"section":r[0],"profile":r[1],"family":r[2],"summary":json.loads(r[3])} for r in db.execute("SELECT section,profile,family,json_extract(result,'$.summary') FROM lab_simulations WHERE job_id=? ORDER BY section,profile,family",(identity,))]
    return {"job":job,"summary":{"labVersion":VERSION,"stage":spec["lab"]["stage"],"sections":summaries,
            "walkSelections":choices,"portfolios":portfolios,"complete":job["status"]=="succeeded",
            "interpretation":"Each section is separate; training, validation and holdout are never pooled. Partial jobs are not completed experiments."},
            "trials":rows,"page":{"offset":offset,"limit":limit,"total":total,"hasMore":offset+len(rows)<total}}


def portfolio(job_id,section,profile,family,*,offset=0,limit=100):
    if type(offset) is not int or offset<0 or type(limit) is not int or not 1<=limit<=1000:raise DataError("Ungültige Simulationsseite.",400)
    with connection() as db:
        row=db.execute("SELECT result FROM lab_simulations WHERE job_id=? AND section=? AND profile=? AND family=?",(job_id,section,profile,family)).fetchone()
    if not row:raise DataError("Simulation nicht gefunden.",404)
    result=json.loads(row[0]);pages={}
    for key in ("trades","skipped","equity"):
        total=len(result[key]);result[key]=result[key][offset:offset+limit]
        pages[key]={"offset":offset,"limit":limit,"total":total,"hasMore":offset+len(result[key])<total}
    result["pages"]=pages
    return result
