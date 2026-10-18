"""Durable local research queue. One OS-locked worker; transactional checkpoints."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import threading
import time
import uuid
import base64
from functools import lru_cache

from datasets import digest, import_dataset, read_dataset
from models import DataError
from research import DEFAULTS, STUDY_VERSION, causal_events, evaluate_trial, summarize, trial_plan, validate_spec
from settings import ROOT, data_dir
from trendlines import RULES_VERSION


def engine_hash():
    import hashlib
    value = hashlib.sha256()
    for name in ("models.py", "trendlines.py", "analysis_service.py", "research.py", "datasets.py", "jobs.py",
                 "market_calendar.py","data_quality.py","providers.py","requirements.txt", "tori_entries.py", "tori_observations.py"):
        value.update(name.encode()+b"\0"+(ROOT/name).read_bytes())
    return value.hexdigest()


from database import connection


def manifest():
    return {"studyVersion": STUDY_VERSION, "rulesVersion": RULES_VERSION, "engineHash": engine_hash(),
        "signalTimeframe": "4h", "contextTimeframe": "1D", "universeBasis": "present-day listed assets or explicit list; survivorship bias possible",
        "execution": "first provider 4h open at/after signal availability; extended hours possible",
        "dailyFinality": "daily bars use stored end; new Alpaca normalization uses versioned XNYS session close; no historical publication vintages",
        "outcomes": "fixed forward horizons, not portfolio P&L; initial stop is an observation threshold"}


def _insert_job(db, spec, automatic=False):
    identity = uuid.uuid4().hex
    now = time.time()
    metadata = manifest()
    if spec.get("entry_mode") == "tori":
        from tori_entries import VERSION
        metadata.update(studyVersion=VERSION, entryMode="tori", execution="first available 1h open after closed 4h confirmation + configured latency",
                        outcomes="entries only; no exits or forward returns", tori=spec["tori"])
        if spec["tori"].get("observe_forward"):
            from tori_observations import VERSION as observation_version
            metadata.update(observationVersion=observation_version,
                            outcomes="raw close changes after XNYS sessions strictly following entry date; no exits/costs/portfolio P&L",
                            horizons=spec["horizons"], selection="first entry per variant per sampled origin/window" if spec["tori"].get("sampling") in ("random","origins") else "all detected entries")
        if spec["tori"].get("sampling") == "origins":
            from tori_observations import ORIGINS_VERSION
            metadata["samplingVersion"] = ORIGINS_VERSION
    db.execute("INSERT INTO jobs(id,created,updated,status,spec,manifest,automatic) VALUES(?,?,?,?,?,?,?)",
        (identity,now,now,"queued",json.dumps(spec),json.dumps(metadata),int(automatic)))
    return identity


def submit(spec):
    spec = validate_spec(spec)
    from storage import preflight
    pending=len([s for s in spec["symbols"] if s not in spec.get("dataset_ids",{})]) if spec.get("universe")!="all" else 0
    preflight(history_days=spec["history_days"],symbols=pending)
    with connection() as db:
        identity = _insert_job(db,spec)
    return get_job(identity)


def get_job(identity, *, include_plans=True):
    if not isinstance(identity,str) or len(identity)!=32:
        raise DataError("Ungültige Auftrags-ID.",400)
    with connection() as db:
        row = db.execute("SELECT * FROM jobs WHERE id=?",(identity,)).fetchone()
        if row is None:
            raise DataError("Forschungsauftrag nicht gefunden.",404)
        result = dict(row)
        for key in ("spec","manifest","universe"):
            result[key] = json.loads(result[key]) if result[key] else None
        columns = "*" if include_plans else "symbol,dataset_id,done,error"
        result["symbols"] = [dict(r) for r in db.execute(f"SELECT {columns} FROM symbols WHERE job_id=? ORDER BY symbol",(identity,))]
        for item in result["symbols"]:
            item.pop("job_id", None)
            if include_plans:
                item["plan"] = json.loads(item["plan"]) if item["plan"] else None
            else:
                item.pop("plan", None)
            if include_plans and item["dataset_id"]:
                quality=db.execute("SELECT summary FROM dataset_quality WHERE dataset_id=?",(item["dataset_id"],)).fetchone()
                item["dataQuality"]=json.loads(quality[0]) if quality else None
        result["completedTrials"] = db.execute("SELECT count(*) FROM trials WHERE job_id=?",(identity,)).fetchone()[0]
        result["eventCount"] = db.execute("SELECT count(*) FROM events WHERE job_id=?",(identity,)).fetchone()[0]
        progress = db.execute("SELECT * FROM job_progress WHERE job_id=?", (identity,)).fetchone()
        result["progress"] = {**dict(progress), "detail":json.loads(progress["detail"])} if progress else None
        return result


def list_jobs():
    with connection() as db:
        ids = [r[0] for r in db.execute("SELECT id FROM jobs ORDER BY created DESC LIMIT 50")]
    return [get_job(i, include_plans=False) for i in ids]


@lru_cache(maxsize=16)
def _summary(identity,last_row,horizons,root):
    with connection() as db:
        trials=(json.loads(r[0]) for r in db.execute("SELECT result FROM trials WHERE job_id=? AND rowid<=? ORDER BY id",(identity,last_row)))
        return summarize(trials,horizons)


def report(identity,offset=0,limit=250,entry_filter="all"):
    if type(offset) is not int or offset<0 or type(limit) is not int or not 1<=limit<=1000:
        raise DataError("Ungültige Ergebnisseite.",400)
    job = get_job(identity)
    if entry_filter not in ("all","entries") or (entry_filter!="all" and job["spec"].get("entry_mode")!="tori"):
        raise DataError("Ungültiger Einstiegsfilter.",400)
    with connection() as db:
        db.execute("BEGIN")
        total,last_row=db.execute("SELECT count(*),coalesce(max(rowid),0) FROM trials WHERE job_id=?",(identity,)).fetchone()
        where = "job_id=? AND rowid<=?"
        if entry_filter == "entries":
            where += " AND EXISTS(SELECT 1 FROM json_each(json_extract(trials.result,'$.variants')) WHERE json_extract(value,'$.status')='observed')"
        page_total = db.execute(f"SELECT count(*) FROM trials WHERE {where}",(identity,last_row)).fetchone()[0]
        trials = [json.loads(r[0]) for r in db.execute(f"SELECT result FROM trials WHERE {where} ORDER BY json_extract(result,'$.startAt'),id LIMIT ? OFFSET ?",(identity,last_row,limit,offset))] if job["spec"].get("entry_mode")=="tori" else [json.loads(r[0]) for r in db.execute("SELECT result FROM trials WHERE job_id=? AND rowid<=? ORDER BY id LIMIT ? OFFSET ?",(identity,last_row,limit,offset))]
        if job["spec"].get("entry_mode") == "tori":
            from tori_entries import summarize as entry_summary
            # Mutable setup rows and their summary share one SQLite read snapshot.
            summary = entry_summary(json.loads(r[0]) for r in db.execute("SELECT result FROM trials WHERE job_id=? AND rowid<=?", (identity,last_row)))
            if job["spec"]["tori"].get("sampling") == "origins":
                plans = [json.loads(r[0]) for r in db.execute("SELECT plan FROM symbols WHERE job_id=? AND plan IS NOT NULL",(identity,))]
                completed = [w for p in plans for w in p.get("coverage",{}).get("windows",[]) if w["complete"]]
                summary["searches"] = {"planned":sum(p.get("actual_samples",0) for p in plans), "completed":len(completed),
                    "withEntry":sum(bool(w["entryVariants"]) for w in completed),
                    "withoutEntry":sum(not w["entryVariants"] for w in completed),
                    "byVariant":{v:sum(v in w["entryVariants"] for w in completed) for v in ("breakout","horizontal","retest")}}
            if job["spec"]["tori"].get("observe_forward"):
                from tori_observations import summarize_observations
                summary["observations"] = summarize_observations(
                    (json.loads(r[0]) for r in db.execute("SELECT result FROM trials WHERE job_id=? AND rowid<=?", (identity,last_row))), job["spec"]["horizons"])
                summary["interpretation"] = "Einstiege mit getrennter Schlusskursbeobachtung nach Handelstagen; keine Ausstiege, Kosten oder Depot-P/L. Varianten und überlappende Verläufe sind abhängig."
    job["completedTrials"]=total
    if job["spec"].get("entry_mode") != "tori":
        summary = _summary(identity,last_row,tuple(job["spec"]["horizons"]),str(data_dir()))
    return {"job": job, "summary": summary, "trials":trials,
        "page":{"offset":offset,"limit":limit,"total":page_total,"hasMore":offset+len(trials)<page_total}}


def events_for(identity, limit=250, cursor=None):
    """Append-order keyset page, pinned to the first page's committed high-water mark."""
    if not isinstance(identity, str) or len(identity) != 32 or type(limit) is not int or not 1 <= limit <= 1000:
        raise DataError("Ungültige Ereignisseite (Limit 1–1000).", 400)
    after, through = 0, None
    if cursor is not None:
        try:
            if not isinstance(cursor, str) or not 1 <= len(cursor) <= 512:
                raise ValueError()
            token = json.loads(base64.b64decode(cursor, altchars=b"-_", validate=True))
            if set(token) != {"v", "job", "after", "through"} or token["v"] != 1 or token["job"] != identity:
                raise ValueError()
            after, through = token["after"], token["through"]
            if any(type(n) is not int for n in (after, through)) or not 0 <= after <= through <= 9223372036854775807:
                raise ValueError()
        except (ValueError, TypeError, UnicodeError):
            raise DataError("Ungültiger Ereignis-Cursor für diesen Auftrag.", 400) from None
    with connection() as db:
        db.execute("BEGIN")
        if not db.execute("SELECT 1 FROM jobs WHERE id=?", (identity,)).fetchone():
            raise DataError("Forschungsauftrag nicht gefunden.", 404)
        maximum = db.execute("SELECT coalesce(max(rowid),0) FROM events WHERE job_id=?", (identity,)).fetchone()[0]
        if through is None:
            through = maximum
        elif through > maximum:
            raise DataError("Ereignis-Lesestand ist nicht mehr verfügbar.", 409)
        total = db.execute("SELECT count(*) FROM events WHERE job_id=? AND rowid<=?", (identity, through)).fetchone()[0]
        rows = db.execute("SELECT rowid,event FROM events WHERE job_id=? AND rowid>? AND rowid<=? ORDER BY rowid LIMIT ?",
                          (identity, after, through, limit+1)).fetchall()
    more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = base64.urlsafe_b64encode(json.dumps({"v":1,"job":identity,"after":rows[-1][0],"through":through}, separators=(",", ":")).encode()).decode() if more else None
    return {"items":[json.loads(r[1]) for r in rows],
            "page":{"limit":limit,"total":total,"hasMore":more,"nextCursor":next_cursor,"snapshot":through,"order":"append"}}


def get_trial(identity,trial_id,variant):
    get_job(identity)
    with connection() as db:
        row=db.execute("SELECT result FROM trials WHERE job_id=? AND id=?",(identity,trial_id)).fetchone()
    if row is None:
        raise DataError("Forschungsfall nicht gefunden.",404)
    trial=json.loads(row[0])
    entry=next((e for e in trial["variants"] if e["variant"]==variant),None)
    if entry is None:
        raise DataError("Einstiegsvariante nicht gefunden.",404)
    return trial,entry


def cancel(identity):
    get_job(identity)
    with connection() as db:
        db.execute("UPDATE jobs SET status=CASE WHEN status='queued' THEN 'cancelled' ELSE 'cancel_requested' END,updated=? WHERE id=? AND status IN ('queued','running')",(time.time(),identity))
    return get_job(identity)


def schedule(value=None):
    with connection() as db:
        row = db.execute("SELECT value FROM settings WHERE key='schedule'").fetchone()
        current = json.loads(row[0]) if row else {"enabled":False,"interval_hours":24,"spec":validate_spec({}),"next_run":None}
        if value is not None:
            if not isinstance(value,dict) or set(value)-{"enabled","interval_hours","spec"}:
                raise DataError("Ungültige Zeitplan-Einstellungen.",400)
            enabled = value.get("enabled",current["enabled"])
            interval = value.get("interval_hours",current["interval_hours"])
            if type(enabled) is not bool or type(interval) is not int or not 1<=interval<=168:
                raise DataError("Zeitplan: aktiviert ja/nein und 1–168 Stunden.",400)
            current = {"enabled":enabled,"interval_hours":interval,"spec":validate_spec(value.get("spec",current["spec"])),
                "next_run":time.time() if enabled else None}
            db.execute("INSERT OR REPLACE INTO settings VALUES('schedule',?)",(json.dumps(current),))
        return current


def ensure_default_schedule():
    with connection() as db:
        exists = db.execute("SELECT 1 FROM settings WHERE key='schedule'").fetchone()
    if not exists:
        schedule({"enabled":True,"interval_hours":24,"spec":DEFAULTS})


def schedule_due():
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT value FROM settings WHERE key='schedule'").fetchone()
        if not row:
            return
        value = json.loads(row[0])
        if not value["enabled"] or value["next_run"] > time.time():
            return
        if db.execute("SELECT 1 FROM jobs WHERE automatic=1 AND status IN ('queued','running','cancel_requested')").fetchone():
            return
        _insert_job(db,validate_spec(value["spec"]),automatic=True)
        value["next_run"] = time.time()+value["interval_hours"]*3600
        db.execute("UPDATE settings SET value=? WHERE key='schedule'",(json.dumps(value),))


@contextmanager
def worker_lock():
    path = data_dir()/"research"/"worker.lock"
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a+b") as stream:
        # Windows byte-range locks also prevent reads of a locked byte.
        stream.seek(0,2)
        if stream.tell()==0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        locked = False
        try:
            import os
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
            locked = True
        except (OSError,BlockingIOError):
            pass
        try:
            yield locked
        finally:
            if locked:
                stream.seek(0)
                if os.name == "nt":
                    msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
                else:
                    fcntl.flock(stream.fileno(),fcntl.LOCK_UN)


def run_job(identity, stop=None):
    """Called by the single locked worker. Commits after every complete trial."""
    from operations import phase, record_dataset
    phase(identity, "preparing")
    job = get_job(identity)
    if job["manifest"]["engineHash"] != engine_hash():
        raise DataError("Engine-Version hat sich geändert. Bitte neuen Forschungsauftrag starten.",409)
    spec = job["spec"]
    universe = job["universe"]
    if universe is None:
        if spec.get("universe") == "all":
            from assets import directory
            catalog,stale = directory()
            if stale:
                raise DataError("Aktienkatalog ist veraltet; automatischer Lauf ausgesetzt.",422)
            universe = [item["symbol"] for item in catalog["items"]]
        else:
            universe = spec["symbols"]
        from storage import preflight
        preflight(history_days=spec["history_days"],symbols=sum(s not in spec.get("dataset_ids",{}) for s in universe))
        with connection() as db:
            db.execute("UPDATE jobs SET universe=?,updated=? WHERE id=?",(json.dumps(universe),time.time(),identity))
    last_check = [0,False]
    last_progress = [0]
    progress_lock = threading.Lock()
    def advancing(name, **detail):
        with progress_lock:
            if time.monotonic()-last_progress[0] >= 2:
                phase(identity, name, **detail)
                last_progress[0] = time.monotonic()
    def interrupted():
        if stop and stop.is_set():
            return True
        if time.monotonic()-last_check[0]>.5:
            with connection() as db:
                status=db.execute("SELECT status FROM jobs WHERE id=?",(identity,)).fetchone()[0]
                db.execute("UPDATE jobs SET updated=? WHERE id=?",(time.time(),identity))
            last_check[:] = [time.monotonic(),status=="cancel_requested"]
        return last_check[1]
    for symbol in universe:
        if interrupted():
            return False
        with connection() as db:
            saved=db.execute("SELECT * FROM symbols WHERE job_id=? AND symbol=?",(identity,symbol)).fetchone()
            if saved and saved["done"]:
                continue
            db.execute("INSERT OR IGNORE INTO symbols(job_id,symbol) VALUES(?,?)",(identity,symbol))
            db.execute("UPDATE jobs SET current_symbol=?,updated=? WHERE id=?",(symbol,time.time(),identity))
        try:
            dataset_id = saved["dataset_id"] if saved else None
            if not dataset_id:
                dataset_id = spec.get("dataset_ids",{}).get(symbol)
                if not dataset_id:
                    phase(identity, "importing", symbol=symbol)
                    dataset_id = import_dataset(symbol,spec["history_days"],
                        progress=lambda tf,pages,rows: advancing("importing",symbol=symbol,interval=tf,pages=pages,rows=rows))
            phase(identity, "validating", symbol=symbol)
            dataset = read_dataset(dataset_id)
            if dataset["material"]["symbol"] != symbol:
                raise DataError("Dataset gehört zu einer anderen Aktie.",422)
            record_dataset(dataset)
            plan = json.loads(saved["plan"]) if saved and saved["plan"] else trial_plan(dataset,spec)
            with connection() as db:
                db.execute("UPDATE symbols SET dataset_id=?,plan=?,error=NULL WHERE job_id=? AND symbol=?",(dataset_id,json.dumps(plan),identity,symbol))
            if interrupted():
                return False
            if spec.get("entry_mode") == "tori":
                if not run_entries(identity, dataset, spec, plan, interrupted, advancing):
                    return False
                with connection() as db:
                    db.execute("UPDATE symbols SET done=1 WHERE job_id=? AND symbol=?",(identity,symbol))
                continue
            first_index = min(plan["starts"])+1
            phase(identity, "events", symbol=symbol, completed=0, total=plan["discovery_end"]-first_index+1, unit="candles")
            events=list(causal_events(dataset,plan["discovery_end"],first_index=first_index,cancelled=interrupted,
                progress=lambda done,total: advancing("events",symbol=symbol,completed=done,total=total,unit="candles")))
            if interrupted():
                return False
            phase(identity, "saving_events", symbol=symbol, completed=len(events), unit="events")
            with connection() as db:
                db.executemany("INSERT OR IGNORE INTO events VALUES(?,?,?,?)",[(identity,e["id"],dataset_id,json.dumps(e)) for e in events])
                completed={r[0] for r in db.execute("SELECT id FROM trials WHERE job_id=?",(identity,))}
            phase(identity, "trials", symbol=symbol, completed=0, total=len(plan["starts"]), unit="trials")
            for position,index in enumerate(plan["starts"],1):
                if interrupted():
                    return False
                result=evaluate_trial(dataset,spec,plan,index,events)
                if result["id"] not in completed:
                    with connection() as db:
                        db.execute("INSERT OR IGNORE INTO trials VALUES(?,?,?)",(identity,result["id"],json.dumps(result,allow_nan=False)))
                        db.execute("UPDATE jobs SET updated=? WHERE id=?",(time.time(),identity))
                phase(identity, "trials", symbol=symbol, completed=position, total=len(plan["starts"]), unit="trials")
            with connection() as db:
                db.execute("UPDATE symbols SET done=1 WHERE job_id=? AND symbol=?",(identity,symbol))
        except DataError as error:
            phase(identity, "symbol_error", symbol=symbol, error=str(error))
            with connection() as db:
                db.execute("UPDATE symbols SET done=1,error=? WHERE job_id=? AND symbol=?",(str(error),identity,symbol))
    return True


def run_entries(identity, dataset, spec, plan, interrupted, advancing):
    """Stable upserts allow deterministic replay after interruption, without duplicate setups."""
    from tori_entries import EntryScanner
    from operations import phase
    pending = []
    def flush():
        if not pending:
            return
        with connection() as db:
            for item in pending:
                if "event" in item:
                    event = item["event"]
                    db.execute("INSERT OR IGNORE INTO events VALUES(?,?,?,?)", (identity,event["id"],dataset["id"],json.dumps(event,allow_nan=False)))
                else:
                    trial = item["trial"]
                    db.execute("INSERT INTO trials VALUES(?,?,?) ON CONFLICT(job_id,id) DO UPDATE SET result=excluded.result",
                               (identity,trial["id"],json.dumps(trial,allow_nan=False)))
            db.execute("UPDATE jobs SET updated=? WHERE id=?",(time.time(),identity))
        pending.clear()
    def emit(item):
        pending.append(item)
        if len(pending) >= 100:
            flush()
    symbol = dataset["material"]["symbol"]
    phase(identity, "entries", symbol=symbol, completed=0, total=plan["candles"], unit="candles")
    windows = plan.get("windows", [None])
    coverage = {"candles":0,"withoutPair":0,"windows":[]}
    complete = True
    for window in windows:
        scan_plan = {**plan, **window, "windowId":window["id"]} if window else plan
        scanner = EntryScanner(dataset,spec,scan_plan,emit)
        previous_count = coverage["candles"]
        def progress(done,total):
            advancing("entries",symbol=symbol,completed=previous_count+done,total=plan["candles"],unit="candles")
        complete = scanner.advance(scan_plan["discovery_end"], interrupted, progress)
        if complete:
            scanner.finish()
            if spec["tori"].get("observe_forward"):
                from tori_observations import observe_cases
                observe_cases(list(scanner.cases.values()),dataset,spec,plan,random_window=window is not None)
                for case in scanner.cases.values():
                    scanner.save(case)
        flush()
        coverage["candles"] += scanner.coverage["candles"]
        coverage["withoutPair"] += scanner.coverage["withoutPair"]
        if window:
            entries = {v["variant"] for c in scanner.cases.values() for v in c["variants"] if v["status"]=="observed"}
            first_entries = {name:min(v["entryAt"] for c in scanner.cases.values() for v in c["variants"]
                                      if v["status"]=="observed" and v["variant"]==name) for name in entries}
            coverage["windows"].append({"id":window["id"],"startAt":window["scanStartAt"],"endAt":window["scanEndAt"],
                                         "searchedUntil":scanner.bars[scanner.last].end,
                                         "candles":scanner.coverage["candles"],"firstEntries":first_entries,
                                         "complete":complete,"setups":len(scanner.cases),"entryVariants":sorted(entries)})
        if not complete:
            break
    with connection() as db:
        stored = json.loads(db.execute("SELECT plan FROM symbols WHERE job_id=? AND symbol=?",(identity,symbol)).fetchone()[0])
        stored["coverage"] = coverage
        db.execute("UPDATE symbols SET plan=? WHERE job_id=? AND symbol=?",(json.dumps(stored),identity,symbol))
    return complete


def claim_next():
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        row=db.execute("SELECT id FROM jobs WHERE status='queued' ORDER BY created LIMIT 1").fetchone()
        if row:
            db.execute("UPDATE jobs SET status='running',updated=? WHERE id=? AND status='queued'",(time.time(),row[0]))
        return row[0] if row else None


def worker_loop(stop, *, once=False):
    from operations import monitor, phase
    with worker_lock() as locked:
        if not locked:
            return False
        # The OS lock proves the previous process no longer owns a running job.
        with connection() as db:
            db.execute("UPDATE jobs SET status='queued' WHERE status='running'")
            db.execute("UPDATE jobs SET status='cancelled' WHERE status='cancel_requested'")
        with monitor() as current_job:
            while not stop.is_set():
                current_job(None)
                schedule_due()
                identity=claim_next()
                if identity:
                    current_job(identity)
                    try:
                        complete=run_job(identity,stop)
                        current=get_job(identity)
                        errors=sum(bool(s["error"]) for s in current["symbols"])
                        finished_status="failed" if errors and errors==len(current["symbols"]) else "partial" if errors else "succeeded"
                        status = "cancelled" if current["status"]=="cancel_requested" else (finished_status if complete else "queued")
                        with connection() as db:
                            db.execute("UPDATE jobs SET status=CASE WHEN status='cancel_requested' THEN 'cancelled' ELSE ? END,current_symbol=NULL,updated=? WHERE id=?",(status,time.time(),identity))
                        phase(identity, status)
                    except Exception as error:
                        message=str(error) if isinstance(error,DataError) else f"Interner Forschungsfehler ({type(error).__name__}); Auftrag bleibt zur Prüfung erhalten."
                        with connection() as db:
                            db.execute("UPDATE jobs SET status=CASE WHEN status='cancel_requested' THEN 'cancelled' ELSE 'failed' END,error=?,updated=? WHERE id=?",(message,time.time(),identity))
                        phase(identity, "failed", error=message)
                    current_job(None)
                if once:
                    return True
                stop.wait(1)
    return True


def start_worker():
    stop=threading.Event()
    thread=threading.Thread(target=worker_loop,args=(stop,),daemon=True,name="tori-research")
    thread.start()
    return stop,thread


def worker_active():
    with worker_lock() as acquired:
        return not acquired
