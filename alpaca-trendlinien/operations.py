"""Persistent local telemetry. Status reads never contact a market-data provider."""
from contextlib import contextmanager
from datetime import datetime
import json
import logging
import os
import threading
import time
import uuid


def setting(db, key):
    row = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return json.loads(row[0]) if row else None


def put(db, key, value):
    db.execute("INSERT OR REPLACE INTO settings VALUES(?,?)", (key, json.dumps(value, allow_nan=False)))


def phase(job_id, name, **detail):
    from jobs import connection
    now = time.time()
    with connection() as db:
        db.execute("""INSERT INTO job_progress VALUES(?,?,?,?,?) ON CONFLICT(job_id) DO UPDATE SET
          phase=excluded.phase, phase_started=CASE WHEN phase=excluded.phase THEN phase_started ELSE excluded.phase_started END,
          progress_at=excluded.progress_at, detail=excluded.detail""", (job_id, name, now, now, json.dumps(detail)))


def record_dataset(dataset, *, imported=False):
    """Verified source timestamps, distinct from the time an offline dataset was reused."""
    from jobs import connection
    material = dataset["material"]
    value = {"checkedAt":time.time(), "datasetId":dataset["id"], "symbol":material["symbol"],
             "provider":material["provider"], "feed":material["feed"], "adjustment":material["adjustment"],
             "sources":{tf:{"fetchedAt":dataset["sources"][tf].get("fetchedAt"),
                            "mode":dataset["sources"][tf].get("mode"),
                            "lastClose":max(b["end"] for b in rows), "bars":len(rows)}
                        for tf, rows in material["bars"].items()}}
    with connection() as db:
        put(db, "last_dataset", value)
        if imported:
            put(db, "last_import", value)


def _worker_update(owner, **values):
    from jobs import connection
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        current = setting(db, "worker")
        if current and current["owner"] == owner:
            put(db, "worker", {**current, **values})


@contextmanager
def monitor(interval=5):
    """Only the OS-lock owner starts a monitor. The main loop separately reports progress."""
    from jobs import connection
    owner, now = uuid.uuid4().hex, time.time()
    with connection() as db:
        put(db, "worker", {"owner":owner,"pid":os.getpid(),"startedAt":now,
                           "heartbeatAt":now,"loopAt":now,"jobId":None,"stoppedAt":None})
    stopped = threading.Event()

    def beat():
        while not stopped.wait(interval):
            try:
                _worker_update(owner, heartbeatAt=time.time())
            except Exception as error:
                # Losing telemetry must not invent healthy timestamps or expose provider secrets.
                logging.warning("Worker heartbeat write failed (%s)", type(error).__name__)

    thread = threading.Thread(target=beat, daemon=True, name="tori-heartbeat")
    thread.start()
    try:
        yield lambda identity: _worker_update(owner, jobId=identity, heartbeatAt=time.time(), loopAt=time.time())
    finally:
        stopped.set()
        thread.join(timeout=12)
        _worker_update(owner, stoppedAt=time.time(), jobId=None)


def _seconds(name, default):
    try:
        return max(1, min(86400, int(os.environ.get(name, default))))
    except ValueError:
        return default


def status(*, now=None):
    from jobs import connection, worker_active
    now = time.time() if now is None else now
    lock = worker_active()
    with connection() as db:
        worker = setting(db, "worker") or {}
        imported, dataset = setting(db, "last_import"), setting(db, "last_dataset")
        row = db.execute("SELECT id,status,current_symbol,error FROM jobs WHERE id=?", (worker.get("jobId"),)).fetchone()
        current = dict(row) if row else None
        progress_row = db.execute("SELECT * FROM job_progress WHERE job_id=?", (worker.get("jobId"),)).fetchone()
        progress = {**dict(progress_row),"detail":json.loads(progress_row["detail"])} if progress_row else None
        failure = db.execute("""SELECT j.id,j.updated,j.error,s.symbol,s.error AS symbol_error FROM jobs j
          LEFT JOIN symbols s ON s.job_id=j.id AND s.error IS NOT NULL
          WHERE j.error IS NOT NULL OR s.error IS NOT NULL ORDER BY j.updated DESC LIMIT 1""").fetchone()
    heartbeat_age = max(0, now-worker["heartbeatAt"]) if worker.get("heartbeatAt") else None
    progress_age = max(0, now-progress["progress_at"]) if progress else None
    loop_age = max(0, now-worker["loopAt"]) if worker.get("loopAt") else None
    heartbeat_timeout = _seconds("TORI_HEARTBEAT_TIMEOUT_SECONDS", 30)
    progress_timeout = _seconds("TORI_PROGRESS_WARNING_SECONDS", 300)
    if not lock:
        state = "absent"
    elif not worker or worker.get("stoppedAt") or heartbeat_age is None:
        state = "unverified"
    elif heartbeat_age > heartbeat_timeout:
        state = "unresponsive"
    elif (current and progress_age is not None and progress_age > progress_timeout) or (not current and loop_age is not None and loop_age > progress_timeout):
        state = "stalled"
    else:
        state = "working" if current else "idle"
    source_ages = {}
    if dataset:
        for tf, source in dataset["sources"].items():
            fetched = source.get("fetchedAt")
            try:
                fetched_age = max(0, now-datetime.fromisoformat(fetched.replace("Z", "+00:00")).timestamp()) if fetched else None
            except (ValueError, TypeError, AttributeError):
                fetched_age = None
            source_ages[tf] = {"fetchAgeSeconds":fetched_age,"lastCloseAgeSeconds":max(0, now-source["lastClose"])}
    from storage import usage
    from database import SCHEMA_VERSION
    return {"observedAt":now, "storage":usage(),"databaseVersion":SCHEMA_VERSION,"worker":{"state":state,"lockHeld":lock,
            "heartbeatAt":worker.get("heartbeatAt"),"heartbeatAgeSeconds":heartbeat_age,
            "loopAgeSeconds":loop_age,
            "progressAgeSeconds":progress_age,"heartbeatTimeoutSeconds":heartbeat_timeout,
            "progressWarningSeconds":progress_timeout,"job":current,"progress":progress},
            "lastSuccessfulImport":imported,"lastDataset":dataset,"dataAge":source_ages,
            "lastError":dict(failure) if failure else None,
            "readiness":{"web":True,"worker":state in ("idle","working"),"historicalData":dataset is not None,
                         "providerAuthentication":"not_checked_by_health"}}
