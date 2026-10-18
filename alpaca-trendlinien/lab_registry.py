"""Immutable experiment contracts, append-only attempts and explicit final-test access."""
from copy import deepcopy
import json
import time
import uuid

from database import connection
from datasets import digest
from models import DataError
from lab_profiles import VERSION, profile_manifest


def audit(db,owner,kind,payload):
    old=db.execute("SELECT hash FROM lab_audit WHERE owner=? ORDER BY id DESC LIMIT 1",(owner,)).fetchone()
    previous=old[0] if old else ""
    at=time.time();value=digest({"owner":owner,"kind":kind,"payload":payload,"at":at,"previous":previous})
    db.execute("INSERT INTO lab_audit(owner,created,kind,payload,previous_hash,hash) VALUES(?,?,?,?,?,?)",(owner,at,kind,json.dumps(payload,allow_nan=False),previous,value))


def contract(spec):
    value=deepcopy(spec)
    for key in ("experiment_id","stage","confirm_final_test"):value["lab"].pop(key,None)
    return value


def register(spec,engine_hash):
    fixed=contract(spec);fingerprint=digest(fixed);identity=spec["lab"].get("experiment_id")
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        if identity:
            row=db.execute("SELECT fingerprint,engine_hash FROM lab_experiments WHERE id=?",(identity,)).fetchone()
            if not row:raise DataError("Experiment nicht gefunden.",404)
            if row[0]!=fingerprint or row[1]!=engine_hash:raise DataError("Vorregistrierte Regeln, Universum oder Engine geändert. Eigenes neues Experiment registrieren; alten Vertrag nicht überschreiben.",409)
            return identity
        if spec["lab"]["stage"]!="development":raise DataError("Neue Experimente beginnen in der Entwicklungsphase.",409)
        identity=uuid.uuid4().hex;now=time.time()
        db.execute("INSERT INTO lab_experiments VALUES(?,?,?,?,?,?,?,NULL,NULL,NULL)",(identity,now,now,json.dumps(fixed),fingerprint,engine_hash,"registered"))
        audit(db,identity,"registered",{"fingerprint":fingerprint,"version":VERSION,"profileCount":len(spec["lab"]["profiles"]),"variantBudget":spec["lab"]["variant_budget"]})
    return identity


def get(identity):
    with connection() as db:
        row=db.execute("SELECT * FROM lab_experiments WHERE id=?",(identity,)).fetchone()
        if not row:raise DataError("Experiment nicht gefunden.",404)
        result=dict(row)
        for key in ("spec","datasets","plan","selection"):result[key]=json.loads(result[key]) if result[key] else None
        result["attempts"]=[{**dict(r),"result":json.loads(r["result"]) if r["result"] else None} for r in db.execute("SELECT * FROM lab_attempts WHERE experiment_id=? ORDER BY id",(identity,))]
        result["profiles"]=[profile_manifest(p,result["spec"]["lab"],result["spec"]["tori"]) for p in result["spec"]["lab"]["profiles"]]
        result["finalOpened"]=bool(db.execute("SELECT 1 FROM lab_final_access WHERE experiment_id=?",(identity,)).fetchone())
        return result


def list_experiments():
    with connection() as db:return [{**dict(r),"selection":json.loads(r["selection"]) if r["selection"] else None} for r in db.execute("SELECT id,created,updated,status,fingerprint,selection FROM lab_experiments ORDER BY created DESC LIMIT 100")]


def bind_data(identity,datasets,plan):
    encoded=json.dumps(datasets,sort_keys=True)
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        row=db.execute("SELECT datasets,plan FROM lab_experiments WHERE id=?",(identity,)).fetchone()
        if not row:raise DataError("Experiment nicht gefunden.",404)
        if row[0]:
            if json.loads(row[0])!=datasets or json.loads(row[1])!=plan:raise DataError("Experiment ist an seinen Datenbestand und Phasenplan gebunden.",409)
            return
        db.execute("UPDATE lab_experiments SET datasets=?,plan=?,status='development',updated=? WHERE id=?",(encoded,json.dumps(plan),time.time(),identity))
        audit(db,identity,"data_bound",{"dataset_ids":datasets,"plan":plan})


def start_attempt(identity,job_id,stage,*,confirm_final_test=False):
    if stage not in ("development","validation","holdout","walk_forward"):raise DataError("Unbekannte Forschungsphase.",400)
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        existing=db.execute("SELECT experiment_id,stage FROM lab_attempts WHERE job_id=?",(job_id,)).fetchone()
        if existing:
            if tuple(existing)!=(identity,stage):raise DataError("Versuch ist bereits anders registriert.",409)
            return
        row=db.execute("SELECT * FROM lab_experiments WHERE id=?",(identity,)).fetchone()
        if not row:raise DataError("Experiment nicht gefunden.",404)
        if not row["datasets"]:raise DataError("Daten und Phasengrenzen zuerst binden.",409)
        selection=json.loads(row["selection"]) if row["selection"] else None
        if stage=="validation" and not db.execute("SELECT 1 FROM lab_attempts WHERE experiment_id=? AND stage='development' AND status='succeeded'",(identity,)).fetchone():
            raise DataError("Vor Validierung einen vollständigen Entwicklungslauf abschließen.",409)
        if stage=="holdout":
            if not confirm_final_test or not selection:raise DataError("Finaler Test benötigt eingefrorenen Kandidaten und ausdrückliche Freigabe im Auftrag.",409)
            bound_plan=json.loads(row["plan"]);window=bound_plan["phases"]["holdout"]
            reservation=digest({"datasets":json.loads(row["datasets"]),"holdout":window})
            used=db.execute("SELECT job_id FROM lab_final_access WHERE reservation=?",(reservation,)).fetchone()
            if used:raise DataError("Dieser Holdout wurde bereits als finaler Test geöffnet; neue Tests würden Entwicklungsdaten wiederverwenden.",409)
            for symbol,dataset_id in bound_plan["dataset_ids"].items():
                if db.execute("SELECT 1 FROM lab_final_windows WHERE symbol=? AND start_at<=? AND end_at>=?",(symbol,window["endAt"],window["startAt"])).fetchone():
                    raise DataError("Überlappender Abschlusszeitraum dieser Aktie wurde bereits geöffnet, auch bei anderer Datenrevision oder geändertem Universum.",409)
            db.execute("INSERT INTO lab_final_access VALUES(?,?,?,?)",(reservation,identity,job_id,time.time()))
            db.executemany("INSERT INTO lab_final_windows VALUES(?,?,?,?,?,?)",[(s,window["startAt"],window["endAt"],identity,job_id,d) for s,d in bound_plan["dataset_ids"].items()])
        db.execute("INSERT INTO lab_attempts(experiment_id,job_id,stage,created,status) VALUES(?,?,?,?,?)",(identity,job_id,stage,time.time(),"running"))
        audit(db,identity,"attempt_started",{"job":job_id,"stage":stage,"selection":selection if stage=="holdout" else None})


def finish_attempt(identity,job_id,status,result):
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        previous=db.execute("SELECT status,result FROM lab_attempts WHERE experiment_id=? AND job_id=?",(identity,job_id)).fetchone()
        if previous and previous[0]==status and previous[1] and json.loads(previous[1])==result:return
        if not previous:
            # Even an import, registration gate or queued cancellation failure
            # belongs to the experiment's attempt history.
            db.execute("INSERT INTO lab_attempts(experiment_id,job_id,stage,created,status) VALUES(?,?,?,?,?)",(identity,job_id,result["stage"],time.time(),status))
        db.execute("UPDATE lab_attempts SET status=?,result=? WHERE experiment_id=? AND job_id=?",(status,json.dumps(result,allow_nan=False),identity,job_id))
        db.execute("UPDATE lab_experiments SET updated=?,status=? WHERE id=?",(time.time(),"final_evaluated" if status=="succeeded" and result.get("stage")=="holdout" else status,identity))
        audit(db,identity,"attempt_finished",{"job":job_id,"status":status,"summary":result})


def seal(identity,profile,rationale):
    if not isinstance(rationale,str) or not 10<=len(rationale)<=3000:raise DataError("Begründung für Kandidatenauswahl erforderlich.",400)
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        row=db.execute("SELECT spec,selection,status FROM lab_experiments WHERE id=?",(identity,)).fetchone()
        if not row:raise DataError("Experiment nicht gefunden.",404)
        if row["selection"]:raise DataError("Kandidat ist bereits eingefroren.",409)
        spec=json.loads(row["spec"])
        if profile not in spec["lab"]["profiles"]:raise DataError("Kandidat gehört nicht zur Vorregistrierung.",400)
        if not db.execute("SELECT 1 FROM lab_attempts WHERE experiment_id=? AND stage='validation' AND status='succeeded'",(identity,)).fetchone():raise DataError("Vor Einfrieren einen vollständigen Validierungslauf abschließen.",409)
        selection={"profile":profile,"rationale":rationale,"sealedAt":time.time(),"primaryMetric":spec["lab"]["primary_metric"],"primaryHorizon":spec["lab"]["primary_horizon"],"primaryFamily":spec["lab"]["primary_family"]}
        db.execute("UPDATE lab_experiments SET selection=?,status='sealed',updated=? WHERE id=?",(json.dumps(selection),time.time(),identity))
        audit(db,identity,"candidate_sealed",selection)
    return get(identity)


def journal(identity,*,after=0,through=None,limit=100):
    if type(after) is not int or after<0 or type(limit) is not int or not 1<=limit<=1000 or through is not None and (type(through) is not int or through<after):
        raise DataError("Ungültige Journalseite.",400)
    with connection() as db:
        db.execute("BEGIN")
        maximum=db.execute("SELECT coalesce(max(id),0) FROM lab_audit WHERE owner=?",(identity,)).fetchone()[0]
        if through is None:through=maximum
        if through>maximum:raise DataError("Journal-Lesestand ist nicht verfügbar.",409)
        before=db.execute("SELECT hash FROM lab_audit WHERE owner=? AND id<=? ORDER BY id DESC LIMIT 1",(identity,after)).fetchone()
        rows=[dict(r) for r in db.execute("SELECT * FROM lab_audit WHERE owner=? AND id>? AND id<=? ORDER BY id LIMIT ?",(identity,after,through,limit+1))]
    more=len(rows)>limit;rows=rows[:limit]
    previous=before[0] if before else ""
    for row in rows:
        row["payload"]=json.loads(row["payload"])
        if row["previous_hash"]!=previous or row["hash"]!=digest({"owner":row["owner"],"kind":row["kind"],"payload":row["payload"],"at":row["created"],"previous":previous}):
            raise DataError("Forschungsjournal-Prüfsumme ungültig.",409)
        previous=row["hash"]
    return {"items":rows,"pageChainValid":True,"page":{"limit":limit,"through":through,"hasMore":more,"nextAfter":rows[-1]["id"] if more else None},
            "note":"Checks this page against its preceding stored hash; not a signature, full-history verification or protection against a database administrator."}
