"""Local prospective watch lifecycle, atomic checkpoints and paginated review queue."""
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import re
import sqlite3
import time
import uuid

from datasets import read_dataset, source_bars, digest, data_kind
from forward_data import refresh, closed_cutoff, expected_last
from forward_engine import advance, signature, MODELS, VERSION
from lab_data import import_dataset
from models import DataError
from settings import data_dir
from strategy_run_lock import study_lock

PHASES = ("near", "breakout", "pullback", "retest", "bounce")


@contextmanager
def connection():
    folder = data_dir()/"forward"
    folder.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(folder/"watch.sqlite3", timeout=20)
    db.row_factory = sqlite3.Row
    try:
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0,1):
            raise DataError("Unbekanntes Beobachtungs-Datenbankschema; nicht verändert.",409)
        db.execute("PRAGMA busy_timeout=20000")
        db.executescript("""
        CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,config TEXT NOT NULL,enabled INTEGER NOT NULL,
          heartbeat INTEGER,phase TEXT NOT NULL,progress INTEGER NOT NULL DEFAULT 0,error TEXT);
        CREATE TABLE IF NOT EXISTS lanes(run TEXT,symbol TEXT,model TEXT,state TEXT NOT NULL,checksum TEXT NOT NULL,
          PRIMARY KEY(run,symbol,model));
        CREATE TABLE IF NOT EXISTS imports(run TEXT,symbol TEXT,dataset TEXT,checked INTEGER,updated INTEGER,status TEXT,error TEXT,
          PRIMARY KEY(run,symbol));
        CREATE TABLE IF NOT EXISTS cases(seq INTEGER PRIMARY KEY AUTOINCREMENT,id TEXT UNIQUE NOT NULL,run TEXT NOT NULL,
          symbol TEXT,model TEXT,phase TEXT,known INTEGER,dataset TEXT,body TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS cases_run_seq ON cases(run,seq);
        CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,id TEXT UNIQUE NOT NULL,run TEXT NOT NULL,body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS reviews(seq INTEGER PRIMARY KEY AUTOINCREMENT,case_id TEXT NOT NULL,verdict TEXT NOT NULL,
          note TEXT NOT NULL,unblinded INTEGER NOT NULL,updated INTEGER NOT NULL);
        CREATE INDEX IF NOT EXISTS reviews_case ON reviews(case_id,seq);
        CREATE TABLE IF NOT EXISTS reveals(case_id TEXT PRIMARY KEY,seen INTEGER NOT NULL);
        """)
        if version == 0:
            db.execute("PRAGMA user_version=1")
        with db:
            yield db
    finally:
        db.close()


def encode(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def get_run(identity=None):
    with connection() as db:
        row = db.execute("SELECT * FROM runs WHERE id=?", (identity,)).fetchone() if identity else db.execute("SELECT * FROM runs ORDER BY rowid DESC LIMIT 1").fetchone()
    if not row:
        raise DataError("Noch keine Beobachtung eingerichtet.", 404)
    return {**dict(row), "config": json.loads(row["config"])}


def register(symbols, *, from_at=None, now=None):
    now = int(time.time()) if now is None else now
    start = now if from_at is None else from_at
    if type(start) is not int or start > now or now-start > 60:
        raise DataError("Prospektiven Beginn jetzt registrieren; keine rückdatierten neuen Versuche.", 400)
    if not isinstance(symbols, list) or not 1 <= len(symbols) <= 100 or len(set(symbols)) != len(symbols) or any(not re.fullmatch(r"[A-Z][A-Z0-9./-]{0,29}", s) for s in symbols):
        raise DataError("Eine eindeutige feste Liste mit 1 bis 100 US-Symbolen angeben.", 400)
    config = {"version": VERSION, "engine": signature(), "registeredAt": now, "fromAt": start,
              "baselineCutoff": closed_cutoff(start), "symbols": sorted(symbols), "models": list(MODELS),
              "historyDays": 910, "pollSeconds": 900, "feed": "iex", "adjustment": "split",
              "meaning": "Frozen prospective hypotheses; independent model positions, review only, no orders."}
    identity = uuid.uuid4().hex
    with connection() as db:
        if db.execute("SELECT 1 FROM runs WHERE enabled=1").fetchone():
            raise DataError("Bestehende Beobachtung zuerst ausdrücklich stoppen.", 409)
        db.execute("INSERT INTO runs(id,config,enabled,phase) VALUES(?,?,1,'registered')", (identity, encode(config)))
    return identity


def heartbeat(identity, phase, progress=0, error=None):
    with connection() as db:
        db.execute("UPDATE runs SET heartbeat=?,phase=?,progress=?,error=? WHERE id=?",
                   (int(time.time()), phase, progress, error, identity))


def stop(identity):
    get_run(identity)
    with connection() as db:
        db.execute("UPDATE runs SET enabled=0 WHERE id=?", (identity,))
    return {"id": identity, "enabled": False}


def load_lane(identity, symbol, model):
    with connection() as db:
        row = db.execute("SELECT state,checksum FROM lanes WHERE run=? AND symbol=? AND model=?", (identity, symbol, model)).fetchone()
    if not row:
        return None
    state = json.loads(row["state"])
    if digest(state) != row["checksum"]:
        raise DataError("Beobachtungszustand beschädigt; keine automatische Fortsetzung.", 409)
    return state


def store_lane(identity, symbol, model, state, cases, events):
    with connection() as db:
        db.execute("INSERT OR REPLACE INTO lanes VALUES(?,?,?,?,?)", (identity, symbol, model, encode(state), digest(state)))
        for item in cases:
            key = digest([identity, item["id"]])
            db.execute("INSERT OR IGNORE INTO cases(id,run,symbol,model,phase,known,dataset,body) VALUES(?,?,?,?,?,?,?,?)",
                       (key, identity, symbol, model, item["phase"], item["knownAt"], state["datasetId"], encode({**item, "id": key})))
        for event in events:
            key = digest([identity,event["id"]])
            body = {**event,"id":key}
            if "caseId" in body:
                body["caseId"] = digest([identity,body["caseId"]])
            db.execute("INSERT OR IGNORE INTO events(id,run,body) VALUES(?,?,?)", (key, identity, encode(body)))


def import_status(identity, symbol, dataset, checked, status, error=None):
    with connection() as db:
        db.execute("INSERT OR REPLACE INTO imports VALUES(?,?,?,?,?,?,?)", (identity, symbol, dataset, checked, int(time.time()), status, error))


def start_time(dataset):
    # One year of source history before replay, chosen solely from timestamps.
    rows = source_bars(dataset)["4h"]
    if not rows or rows[0].end+365*86400 > rows[-1].end:
        raise DataError("Mindestens ein Jahr vollständiger 4h-Vorlauf benötigt.", 422)
    return rows[0].end+365*86400


def cycle(identity, *, now=None):
    now = int(time.time()) if now is None else now
    run = get_run(identity)
    config = run["config"]
    if config["engine"] != signature():
        raise DataError("Engine geändert; neue prospektive Generation registrieren.", 409)
    if not run["enabled"]:
        return {"enabled": False}
    cutoff = closed_cutoff(now)
    errors = []
    for number, symbol in enumerate(config["symbols"]):
        if not get_run(identity)["enabled"]:
            heartbeat(identity, "stopped", number)
            return {"enabled": False}
        heartbeat(identity, "import:"+symbol, number)
        with connection() as db:
            imported = db.execute("SELECT * FROM imports WHERE run=? AND symbol=?", (identity,symbol)).fetchone()
        try:
            lanes = {m: load_lane(identity,symbol,m) for m in MODELS}
            if not all(lanes.values()):
                # A new clean generation imports a complete split-consistent history.
                # It never rebases or resumes a previous experiment's checkpoints.
                dataset_id = imported["dataset"] if imported and imported["dataset"] else import_dataset(symbol, config["historyDays"], feed="iex", adjustment="split",
                    progress=lambda *unused: heartbeat(identity,"import:"+symbol,number))
                data = read_dataset(dataset_id)
                if data_kind(data) != "market":
                    raise DataError("Prospektive Beobachtung verweigert synthetische Technikdaten.",422)
                start = start_time(data)
                for model in MODELS:
                    if lanes[model] is None:
                        heartbeat(identity, "warmup:"+symbol+":"+model, number)
                        state,cases,events = advance(data,model,start,config["fromAt"],config["baselineCutoff"])
                        store_lane(identity,symbol,model,state,cases,events)
                        lanes[model] = state
                import_status(identity,symbol,dataset_id,config["baselineCutoff"],"baseline")
                imported = {"dataset":dataset_id,"checked":config["baselineCutoff"],"status":"baseline"}
            if imported and imported["status"] == "blocked":
                errors.append(symbol+": "+imported["error"])
                continue
            if imported and expected_last(cutoff) <= expected_last(imported["checked"]):
                continue  # weekends/overnight: health/polling never refetch the same market interval.
            data = read_dataset(imported["dataset"])
            if data_kind(data) != "market":
                raise DataError("Prospektive Beobachtung verweigert synthetische Technikdaten.",422)
            known = max(s["asOf"] for s in lanes.values())
            data,asof = refresh(data,known,now)
            for model in MODELS:
                heartbeat(identity,"scan:"+symbol+":"+model,number)
                prior = lanes[model]
                state,cases,events = advance(data,model,prior["config"]["startAt"],config["fromAt"],asof,prior)
                store_lane(identity,symbol,model,state,cases,events)
            import_status(identity,symbol,data["id"],asof,"ready")
        except (DataError,ValueError) as exc:
            message = str(exc)
            # Revisions need deliberate new registration; temporary outages may retry.
            blocked = any(s in message for s in ("Präfix", "Quellkerzen", "Generation", "Kerze fehlt", "Zustand beschädigt"))
            import_status(identity,symbol,imported["dataset"] if imported else None,imported["checked"] if imported else 0,
                          "blocked" if blocked else "error",message)
            errors.append(symbol+": "+message)
        except Exception:
            import_status(identity,symbol,imported["dataset"] if imported else None,imported["checked"] if imported else 0,"error","Interner Beobachtungsfehler; lokalen Prüfstand kontrollieren.")
            errors.append(symbol+": interner Beobachtungsfehler")
    heartbeat(identity,"waiting" if not errors else "attention",len(config["symbols"])," | ".join(errors)[:4000] or None)
    return {"id":identity,"enabled":True,"symbols":len(config["symbols"]),"errors":errors}


def worker(identity, *, once=False):
    with study_lock(data_dir()/"forward"/"worker"):
        while get_run(identity)["enabled"]:
            cycle(identity)
            if once:
                return
            for _ in range(get_run(identity)["config"]["pollSeconds"]//5):
                if not get_run(identity)["enabled"]:
                    heartbeat(identity,"stopped")
                    return
                # Heartbeat remains live even during an overnight wait.
                if _ % 6 == 0:
                    run = get_run(identity)
                    heartbeat(identity,run["phase"],run["progress"],run["error"])
                time.sleep(5)


def status():
    try:
        run = get_run()
    except DataError:
        return {"configured": False, "items": []}
    with connection() as db:
        imports = [dict(r) for r in db.execute("SELECT symbol,dataset,checked,updated,status,error FROM imports WHERE run=? ORDER BY symbol",(run["id"],))]
        count = db.execute("SELECT COUNT(*) FROM cases WHERE run=?",(run["id"],)).fetchone()[0]
        reviewed = db.execute("SELECT COUNT(DISTINCT case_id) FROM reviews WHERE case_id IN(SELECT id FROM cases WHERE run=?)",(run["id"],)).fetchone()[0]
    try:
        with study_lock(data_dir()/"forward"/"worker"):
            held = False
    except DataError:
        held = True
    return {"configured":True,"id":run["id"],"enabled":bool(run["enabled"]),"workerLock":held,
            "heartbeat":run["heartbeat"],"staleHeartbeat":not run["heartbeat"] or time.time()-run["heartbeat"] > 120,
            "phase":run["phase"],"progress":run["progress"],"error":run["error"],
            "fromAt":run["config"]["fromAt"],"symbols":run["config"]["symbols"],"models":list(MODELS),
            "cases":count,"reviewed":reviewed,"items":imports}


def cases_page(identity=None, *, offset=0, limit=50, through=None, model="", phase=""):
    run = get_run(identity)
    if type(offset) is not int or offset < 0 or not 1 <= limit <= 100 or (model and model not in MODELS) or (phase and phase not in PHASES):
        raise DataError("Ungültiger Beobachtungsfilter.",400)
    with connection() as db:
        through = db.execute("SELECT COALESCE(MAX(seq),0) FROM cases WHERE run=?",(run["id"],)).fetchone()[0] if through is None else int(through)
        where,args = "c.run=? AND c.seq<=?",[run["id"],through]
        for key,value in (("model",model),("phase",phase)):
            if value:
                where += " AND c."+key+"=?"
                args.append(value)
        rows = db.execute("SELECT c.*,r.verdict,r.note,r.unblinded,v.seen AS revealed FROM cases c LEFT JOIN reviews r ON r.seq=(SELECT MAX(seq) FROM reviews WHERE case_id=c.id) LEFT JOIN reveals v ON v.case_id=c.id WHERE "+where+" ORDER BY c.seq DESC LIMIT ? OFFSET ?",(*args,limit+1,offset)).fetchall()
    return {"run":run["id"],"through":through,"offset":offset,"nextOffset":offset+limit if len(rows)>limit else None,
        "items":[{**json.loads(r["body"]),"revealed":bool(r["revealed"]),"review": {"verdict":r["verdict"],"note":r["note"],"unblinded":bool(r["unblinded"])} if r["verdict"] else None} for r in rows[:limit]]}


def review(case_id, body):
    if not isinstance(body,dict) or set(body) != {"verdict","note","unblinded"} or body["verdict"] not in ("interesting","unclear","reject") or not isinstance(body["note"],str) or len(body["note"])>2000 or type(body["unblinded"]) is not bool:
        raise DataError("Urteil, Notiz bis 2.000 Zeichen und Verlaufssicht angeben.",400)
    with connection() as db:
        if not db.execute("SELECT 1 FROM cases WHERE id=?",(case_id,)).fetchone():
            raise DataError("Beobachtungsfall fehlt.",404)
        seen = bool(db.execute("SELECT 1 FROM reveals WHERE case_id=?",(case_id,)).fetchone())
        db.execute("INSERT INTO reviews(case_id,verdict,note,unblinded,updated) VALUES(?,?,?,?,?)",(case_id,body["verdict"],body["note"],int(body["unblinded"] or seen),int(time.time())))
    return {"saved":True}


def events_page(identity=None, *, after=0, limit=100, through=None):
    run = get_run(identity)
    if type(after) is not int or after < 0 or not 1 <= limit <= 1000:
        raise DataError("Ungültige Journalseite.",400)
    with connection() as db:
        through = db.execute("SELECT COALESCE(MAX(seq),0) FROM events WHERE run=?",(run["id"],)).fetchone()[0] if through is None else int(through)
        rows = db.execute("SELECT seq,body FROM events WHERE run=? AND seq>? AND seq<=? ORDER BY seq LIMIT ?",(run["id"],after,through,limit)).fetchall()
    return {"through":through,"after":rows[-1]["seq"] if rows else after,
            "items":[{"sequence":r["seq"],**json.loads(r["body"])} for r in rows]}


def case_view(case_id, latest=False):
    with connection() as db:
        row = db.execute("SELECT * FROM cases WHERE id=?",(case_id,)).fetchone()
    if not row:
        raise DataError("Beobachtungsfall fehlt.",404)
    if latest:
        with connection() as db:
            db.execute("INSERT OR IGNORE INTO reveals VALUES(?,?)",(case_id,int(time.time())))
    case = json.loads(row["body"])
    lane = load_lane(row["run"],row["symbol"],row["model"])
    identity = lane["datasetId"] if latest else row["dataset"]
    cutoff = lane["asOf"] if latest else case["knownAt"]
    four = source_bars(read_dataset(identity))["4h"]
    end = next((i for i,b in enumerate(four) if b.end>cutoff),len(four))
    anchors = [ray["a_index"] for ray in (case["red"],case["green"]) if ray]
    first = max(0,min(anchors+[case["sourceIndex"]-80]))
    if end-first > 1600:
        first = end-1600
    records = [r for r in lane["records"] if r["entry"]["sourceSetupId"]==case["candidateId"]] if latest else []
    return {"case":case,"datasetId":identity,"asOf":cutoff,"firstIndex":first,
            "bars":[asdict(b) for b in four[first:end]],"records":records,
            "view":"latest" if latest else "signal","meaning":"Originale 4h-Linien eingefroren; keine neue MTF-Signalauswahl."}
