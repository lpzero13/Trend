"""Fan experiments in the existing queue, database, backup and reference graph."""
import json
import time

from database import connection
from datasets import read_dataset
from fan_study import run_dataset, summarize
from models import DataError


def run(job, stop=None):
    from operations import phase, record_dataset
    identity, spec = job["id"], job["spec"]
    if job["universe"] is None:
        with connection() as db:
            db.execute("UPDATE jobs SET universe=? WHERE id=?", (json.dumps(spec["symbols"]), identity))
    last_check = [0., False]
    last_progress = [0.]
    pending = []

    def flush():
        if not pending:
            return
        with connection() as db:
            for item in pending:
                if "event" in item:
                    e = item["event"]
                    db.execute("INSERT OR IGNORE INTO events VALUES(?,?,?,?)", (identity, e["id"], e["datasetId"], json.dumps(e, allow_nan=False)))
                else:
                    t = item["trial"]
                    db.execute("INSERT OR IGNORE INTO trials VALUES(?,?,?)", (identity, t["id"], json.dumps(t, allow_nan=False)))
            db.execute("UPDATE jobs SET updated=? WHERE id=?", (time.time(), identity))
        pending.clear()

    def emit(item):
        pending.append(item)
        if len(pending) >= 100:
            flush()

    def interrupted():
        if stop and stop.is_set():
            return True
        if time.monotonic()-last_check[0] >= .5:
            with connection() as db:
                status = db.execute("SELECT status FROM jobs WHERE id=?", (identity,)).fetchone()[0]
                db.execute("UPDATE jobs SET updated=? WHERE id=?", (time.time(), identity))
            last_check[:] = [time.monotonic(), status == "cancel_requested"]
        return last_check[1]

    def progress(**detail):
        if time.monotonic()-last_progress[0] >= 1:
            phase(identity, "fan_scan", **detail)
            last_progress[0] = time.monotonic()

    for symbol in spec["symbols"]:
        if interrupted():
            flush()
            return False
        with connection() as db:
            saved = db.execute("SELECT * FROM symbols WHERE job_id=? AND symbol=?", (identity, symbol)).fetchone()
            if saved and saved["done"]:
                continue
            db.execute("INSERT OR IGNORE INTO symbols(job_id,symbol) VALUES(?,?)", (identity, symbol))
            db.execute("UPDATE jobs SET current_symbol=? WHERE id=?", (symbol, identity))
        try:
            dataset_id = spec["dataset_ids"][symbol]
            dataset = read_dataset(dataset_id)
            if dataset["material"]["symbol"] != symbol:
                raise DataError("Dataset gehört zu einer anderen Aktie.", 422)
            record_dataset(dataset)
            with connection() as db:
                db.execute("UPDATE symbols SET dataset_id=? WHERE job_id=? AND symbol=?", (dataset_id, identity, symbol))
            result = run_dataset(dataset, spec, emit=emit, interrupted=interrupted, progress=progress)
            flush()
            if result is None:
                return False
            with connection() as db:
                db.execute("UPDATE symbols SET plan=?,done=1,error=NULL WHERE job_id=? AND symbol=?", (json.dumps(result), identity, symbol))
        except DataError as exc:
            flush()
            phase(identity, "symbol_error", symbol=symbol, error=str(exc))
            with connection() as db:
                db.execute("UPDATE symbols SET done=1,error=? WHERE job_id=? AND symbol=?", (str(exc), identity, symbol))
    return True


def report(job, offset=0, limit=250, entry_filter="all"):
    if entry_filter not in ("all", "entries", "origins"):
        raise DataError("Fächer-Ergebnisfilter: all, entries oder origins.", 400)
    with connection() as db:
        db.execute("BEGIN")
        total, through = db.execute("SELECT count(*),coalesce(max(rowid),0) FROM trials WHERE job_id=?", (job["id"],)).fetchone()
        where = "job_id=? AND rowid<=?"
        if entry_filter != "all":
            where += " AND json_extract(result,'$.kind')='"+("entry" if entry_filter == "entries" else "origin")+"'"
        page_total = db.execute("SELECT count(*) FROM trials WHERE "+where, (job["id"], through)).fetchone()[0]
        rows = [json.loads(r[0]) for r in db.execute("SELECT result FROM trials WHERE "+where+" ORDER BY rowid LIMIT ? OFFSET ?", (job["id"], through, limit, offset))]
        summary = summarize(json.loads(r[0]) for r in db.execute("SELECT result FROM trials WHERE job_id=? AND rowid<=? ORDER BY rowid", (job["id"], through)))
    return {"job": {**job, "completedTrials": total}, "summary": summary, "trials": rows,
            "page": {"offset": offset, "limit": limit, "total": page_total, "hasMore": offset+len(rows) < page_total,
                     "snapshot": through, "order": "append; immutable rows"}}
