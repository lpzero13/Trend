"""Immutable historical entry index, blind reviews and offline on-demand search.

No orders, provider fetches or alternate chart signal engine. Entries use the
same structural episode scan as event_case_study; drawings stay user-owned.
"""
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
from functools import lru_cache
import json
import hashlib
from pathlib import Path
import re
import threading
import time
import uuid

from database import connection
from datasets import chart_dataset, data_kind, read_dataset, source_bars
from event_case_study import binding, load_block, scan_episodes
from fan_geometry import stable_id
from fan_study import timestamp
from lab_data import require_convention
from models import DataError, Bar
from settings import data_dir
from datasets import path_for
from analysis_service import build_chart
from signal_path_index import CaseExecution, PathIndex, isolated_entry
from strategy_screen import read
from weekly_chart import add_weekly, CHART_TIMEFRAMES
from entry_screen import Context as ScreenContext,features as screen_features,select as screen_select,PROFILES as SCREEN_PROFILES

VERSION = "tori-chart-entry-index-1"
FAMILIES = ("breakout", "red_retest", "safety_bounce")
COHORTS = ("qualified", "two", "three_young")
VERDICTS = ("plausible", "wrong_line", "too_late", "duplicate", "unclear")


def search_binding():
    return {**binding(), 'entry_history.py':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def identity(value):
    if not isinstance(value, str) or not re.fullmatch("[a-f0-9]{64}", value):
        raise DataError("Ungültige Entry-/Versions-ID.", 400)
    return value


def symbol_name(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Z][A-Z0-9./-]{0,29}", value):
        raise DataError("Ungültige Aktie.", 400)
    return value


def store_run(manifest, cases):
    """One atomic immutable symbol/run. Re-registration never erases reviews."""
    manifest = deepcopy(manifest)
    manifest.setdefault("version", VERSION)
    run = stable_id(manifest)
    manifest["id"] = run
    pairs = set()
    prepared = []
    for case in cases:
        s = case["signal"]
        pair = s["episodeId"], s["family"]
        if pair in pairs or s["family"] not in FAMILIES or s["cohort"] not in COHORTS:
            raise DataError("Doppelte Episode/Entryfamilie oder unbekannte Kriterien.", 409)
        pairs.add(pair)
        if s['line']['knownAt'] >= s['signalAt']:
            raise DataError('Signallinie war vor dem Schluss noch nicht bekannt.',409)
        for ln in (s["line"], s.get("safety")):
            if ln and (ln["knownAt"] > s["signalAt"] or any(p["known_at"] > s["signalAt"] for p in ln.get("contactPoints", []))):
                raise DataError("Fall enthält zukünftig bekannte Linienkontakte.", 409)
        if case["symbol"] != manifest["symbol"] or case["datasetId"] != manifest["datasetId"]:
            raise DataError("Fall und Datenbestand passen nicht zusammen.", 409)
        identity(case["id"])
        # No outcome cache is required for blind drawing review.
        value = {k: deepcopy(case[k]) for k in ("id", "symbol", "datasetId", "signal", "entry", "features")}
        prepared.append((run, value["id"], s["episodeId"], s["family"], s["cohort"], s["signalAt"],
                         json.dumps(value, allow_nan=False), stable_id(value)))
    with connection() as db:
        old = db.execute("SELECT manifest FROM entry_runs WHERE id=?", (run,)).fetchone()
        if old:
            current = dict(db.execute("SELECT id,checksum FROM entry_cases WHERE run_id=?", (run,)).fetchall())
            if current != {row[1]: row[-1] for row in prepared}:
                raise DataError("Bereits gespeicherte Version hat andere Fälle.", 409)
            return run
        db.execute("INSERT INTO entry_runs VALUES(?,?,?,?,?)", (run, manifest["symbol"], manifest["datasetId"], time.time(), json.dumps(manifest)))
        db.executemany("INSERT INTO entry_cases VALUES(?,?,?,?,?,?,?,?)", prepared)
    return run


def register_study(root):
    """Explicit local CLI registration; no arbitrary filesystem path in HTTP."""
    p = read(Path(root)/"plan.json")
    if p["id"] != stable_id({k: v for k, v in p.items() if k != "id"}):
        raise DataError("Studienplan-Prüfsumme ungültig.", 409)
    runs = []
    for symbol in p["symbols"]:
        b = load_block(root, p, symbol)
        # Validate referenced dataset, but never rerun historical detection with
        # today's engine or silently substitute a newer provider/feed version.
        d = read_dataset(b["datasetId"])
        if d["material"]["symbol"] != symbol:
            raise DataError("Dataset gehört zu anderer Aktie.", 409)
        m = {"source": "event_case_study", "sourcePlanId": p["id"], "sourceEngine": p["engine"],
             "symbol": symbol, "datasetId": b["datasetId"], "timeframe": "4h", "windows": p["windows"],
             "eligibility": b["eligibility"], "cutoff": p["outcomeCutoff"], "execution": p["execution"],
             "caseCount": len(b["cases"]), "feed": d["material"]["feed"], "adjustment": d["material"]["adjustment"]}
        runs.append({"symbol": symbol, "runId": store_run(m, b["cases"]), "cases": len(b["cases"])})
    return runs


def run_info(run):
    with connection() as db:
        row = db.execute("SELECT manifest FROM entry_runs WHERE id=?", (identity(run),)).fetchone()
    if not row:
        raise DataError("Entryversion nicht gefunden.", 404)
    m = json.loads(row[0])
    if m["id"] != stable_id({k: v for k, v in m.items() if k != "id"}):
        raise DataError("Entryversion ist beschädigt.", 409)
    return m


def case_value(run, case):
    with connection() as db:
        row = db.execute("SELECT payload,checksum FROM entry_cases WHERE run_id=? AND id=?", (identity(run), identity(case))).fetchone()
    if not row:
        raise DataError("Entryfall nicht gefunden.", 404)
    value = json.loads(row[0])
    if stable_id(value) != row[1]:
        raise DataError("Entryfall-Prüfsumme ungültig.", 409)
    return value


def at_time(value, default):
    if value is None:
        return default
    at = timestamp(value)
    if at is None:
        raise DataError("Ungültiger Zeitpunkt.", 400)
    return min(at, default)


def quality_name(value):
    if value not in SCREEN_PROFILES:
        raise DataError('Unbekanntes Strukturprofil.',400)
    return value


def screened_run(m):
    path=path_for(m['datasetId'])
    try:stamp=(path.stat().st_mtime_ns,path.stat().st_size)
    except OSError:raise DataError('Gespeicherter Kursbestand fehlt.',404) from None
    return _screen_features(str(data_dir()),m['id'],m['datasetId'],stamp)


@lru_cache(maxsize=4)
def _screen_features(root,run,dataset,stamp):
    # Same immutable inputs and predicate as offline research; outcomes are not stored here.
    with connection() as db:
        rows=db.execute('SELECT payload,checksum FROM entry_cases WHERE run_id=?',(run,)).fetchall()
    if not rows:return {}
    sources,_=_chart_sources(root,dataset,stamp)
    ctx=ScreenContext(sources['4h'][0],sources['1D'][0])
    out={}
    for row in rows:
        c=json.loads(row[0])
        if stable_id(c)!=row[1]:raise DataError('Entryfall-Prüfsumme ungültig.',409)
        out[c['id']]=screen_features(c['signal'],ctx)
    return out


def cases_page(run, cutoff=None, offset=0, limit=100, family="all", cohort="all", filled=True, quality="all"):
    m = run_info(run)
    quality_name(quality)
    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 250:
        raise DataError("Ungültige Seite.", 400)
    if family not in ("all",)+FAMILIES or cohort not in ("all",)+COHORTS:
        raise DataError("Ungültiger Entryfilter.", 400)
    where, args = "run_id=? AND signal_at<=?", [run, at_time(cutoff, m["cutoff"])]
    if family != "all":
        where += " AND family=?"; args.append(family)
    if cohort != "all":
        where += " AND cohort=?"; args.append(cohort)
    # Stored execution status is entry-only, never a subsequent win/loss filter.
    if filled:
        where += " AND (json_extract(payload,'$.entry.status')='filled' OR (json_extract(payload,'$.entry.entryAt')>? AND json_extract(payload,'$.signal.initialStop')>0))"
        args.append(at_time(cutoff, m["cutoff"]))
    screening=screened_run(m) if quality!='all' else None
    with connection() as db:
        unfiltered=db.execute('SELECT count(*) FROM entry_cases WHERE '+where,args).fetchone()[0]
        if screening is not None:
            accepted={k for k,f in screening.items() if screen_select(f,quality)['accepted']}
            db.create_function('entry_selected',1,lambda key:int(key in accepted))
            where+=' AND entry_selected(id)=1'
        count = db.execute("SELECT count(*) FROM entry_cases WHERE "+where, args).fetchone()[0]
        rows = db.execute("SELECT id,episode_id,family,cohort,signal_at FROM entry_cases WHERE "+where+
                          " ORDER BY signal_at,id LIMIT ? OFFSET ?", (*args, limit, offset)).fetchall()
    return {"run": m, "items": [dict(r) for r in rows], "total": count, "offset": offset,
            "hasMore": offset+len(rows) < count,
            "screen":{"profile":quality,'label':SCREEN_PROFILES[quality]['label'],
                      'beforeProfile':unfiltered,'excluded':unfiltered-count,'experimental':quality!='all'}}


def detail(run, case, cutoff=None, quality="all"):
    m, c = run_info(run), case_value(run, case)
    quality_name(quality)
    at = at_time(cutoff, m["cutoff"])
    if c["signal"]["signalAt"] > at:
        return {"id": c["id"], "state": "before_signal"}
    value = deepcopy(c)
    if quality!='all':
        f=screened_run(m)[case];selection=screen_select(f,quality)
        if not selection['accepted']:return {'id':case,'state':'filtered_out'}
        value['screen']={**selection,'label':SCREEN_PROFILES[quality]['label'],'features':f}
    e = value["entry"]
    if e.get("entryAt") is None or e["entryAt"] > at:
        value["entry"] = {"status": "pending", "reason": "entry_not_yet_known"}
        value["features"] = {"signalFeatures": deepcopy(value["signal"]["features"])}
    value["state"] = "available"
    value["timeframe"] = "4h"
    with connection() as db:
        row = db.execute("SELECT verdict,note,updated FROM entry_reviews WHERE run_id=? AND case_id=?", (run, case)).fetchone()
    value["review"] = dict(row) if row else None
    return value


@lru_cache(maxsize=2)
def _chart_sources(root, dataset_id, stamp):
    # Immutable verified input, at most two stocks; no future prices are sent.
    # Retain only chart intervals, never the large 5m execution dictionary.
    d = read_dataset(dataset_id)
    frames = {tf: ([Bar(**b) for b in rows],deepcopy(d['sources'][tf]))
              for tf,rows in d['material']['bars'].items() if tf in ('1h','4h','1D')}
    meta = {k: d['material'][k] for k in ('symbol','provider','feed','adjustment','session')}
    meta.update(datasetId=dataset_id,dataKind=data_kind(d))
    return frames,meta


def chart(run, timeframe, cutoff=None):
    m = run_info(run)
    if timeframe not in CHART_TIMEFRAMES:
        raise DataError("Ungültiges Chartintervall.", 400)
    at = at_time(cutoff, m["cutoff"])
    path=path_for(m['datasetId'])
    try: stamp=(path.stat().st_mtime_ns,path.stat().st_size)
    except OSError: raise DataError('Gespeicherter Kursbestand fehlt.',404) from None
    sources,meta=_chart_sources(str(data_dir()),m['datasetId'],stamp)
    payload=build_chart(sources,m['symbol'],'1D' if timeframe=='1W' else timeframe,
                        datetime.fromtimestamp(at,timezone.utc),datetime.now(timezone.utc),historical=True,include_analysis=False)
    payload.update(meta)
    add_weekly(payload, timeframe)
    payload["entryHistory"] = {"runId": run, "sourceTimeframe": "4h", "fixed": True}
    return payload


def review(run, case, verdict=None, note="", delete=False):
    case_value(run, case)
    if not delete and (verdict not in VERDICTS or not isinstance(note, str) or len(note) > 4000):
        raise DataError("Ungültige Bewertung oder Notiz zu lang.", 400)
    with connection() as db:
        if delete:
            db.execute("DELETE FROM entry_reviews WHERE run_id=? AND case_id=?", (run, case))
        else:
            db.execute("INSERT OR REPLACE INTO entry_reviews VALUES(?,?,?,?,?)", (run, case, verdict, note, time.time()))
    return {"saved": not delete}


def _progress(job, phase, done=0, total=0):
    with connection() as db:
        db.execute("UPDATE entry_searches SET updated=?,progress=? WHERE id=?", (time.time(), json.dumps({"phase": phase, "done": done, "total": total}), job))


def search_status(job):
    with connection() as db:
        db.execute("UPDATE entry_searches SET status='interrupted',error='Auftrag unterbrochen; bitte ausdrücklich neu starten.' WHERE status IN ('queued','running','cancelling') AND updated<?", (time.time()-90,))
        row = db.execute("SELECT * FROM entry_searches WHERE id=?", (identity(job),)).fetchone()
    if not row:
        raise DataError("Suchauftrag nicht gefunden.", 404)
    return {**dict(row), "request": json.loads(row["request"]), "progress": json.loads(row["progress"])}


def _calculate(job, request, engine):
    stop = threading.Event()
    def beat():
        while not stop.wait(3):
            with connection() as db:
                db.execute("UPDATE entry_searches SET updated=? WHERE id=? AND status IN ('queued','running','cancelling')", (time.time(), job))
    heartbeat = threading.Thread(target=beat, daemon=True)
    heartbeat.start()
    def cancelled():
        return search_status(job)["status"] == "cancelling"
    try:
        with connection() as db:
            db.execute("UPDATE entry_searches SET status='running' WHERE id=? AND status='queued'", (job,))
        if search_binding() != engine:
            raise DataError("Engine seit Auftrag geändert. Neuer Auftrag erforderlich.", 409)
        _progress(job, "Lokale Daten prüfen")
        dataset = read_dataset(request["datasetId"])
        require_convention(dataset)
        mat = dataset["material"]
        if data_kind(dataset) != "market" or mat["feed"] != "sip" or mat["adjustment"] != "split" or mat["symbol"] != request["symbol"]:
            raise DataError("Benötigt lokale reguläre SIP/split-Daten dieser Aktie. Kein automatischer Download.", 422)
        frames = source_bars(dataset)
        fine = frames["5m"]
        cutoff = fine[-1].end
        start = timestamp(request.get("start")) if request.get("start") else frames["4h"][0].time+400*86400
        end = min(timestamp(request["end"], upper=True), cutoff) if request.get("end") else cutoff
        if not frames["4h"][0].time+320*86400 <= start < end <= cutoff:
            raise DataError("Zeitraum benötigt mindestens 320 Tage Vorgeschichte und muss im lokalen Dataset liegen.", 400)
        rows = [b for b in frames["4h"] if b.time >= start-400*86400 and b.end <= end]
        _progress(job, "Kausale Linien und Episoden berechnen", 0, len(rows))
        signals, _, suppressed, diagnostics = scan_episodes(request["symbol"], rows, start, end)
        index = PathIndex(fine, cutoff)
        cases = []
        for i, s in enumerate(signals):
            if cancelled():
                break
            e = isolated_entry(s, index)
            c = {"id": stable_id([VERSION, dataset["id"], s["episodeId"], s["family"], s["id"]]),
                 "symbol": request["symbol"], "datasetId": dataset["id"], "signal": s, "entry": e,
                 "features": {"atr4h": s["features"].get("atr"), "filterApplied": False}}
            cases.append(c)
            if i % 20 == 0:
                _progress(job, "Einstiege speichern", i, len(signals))
        if search_binding() != engine:
            raise DataError("Engine während Auftrag geändert; Ergebnis nicht veröffentlicht.", 409)
        if cancelled():
            with connection() as db:
                db.execute("UPDATE entry_searches SET status='cancelled',updated=? WHERE id=?", (time.time(), job))
            return
        m = {"source": "offline_entry_scan", "sourceEngine": engine, "symbol": request["symbol"],
             "datasetId": dataset["id"], "timeframe": "4h", "windows": [{"name": "frei", "start": start, "end": end}],
             "cutoff": cutoff, "execution": asdict(CaseExecution()), "caseCount": len(cases),
             "suppressed": len(suppressed), "feed": mat["feed"], "adjustment": mat["adjustment"]}
        run = store_run(m, cases)
        with connection() as db:
            db.execute("UPDATE entry_searches SET status='completed',run_id=?,updated=?,progress=? WHERE id=?", (run, time.time(), json.dumps({"phase": "Fertig", "done": len(cases), "total": len(cases)}), job))
    except Exception as exc:
        message = str(exc) if isinstance(exc, DataError) else "Berechnung fehlgeschlagen. Lokalen Datenbestand und Serverprotokoll prüfen."
        with connection() as db:
            db.execute("UPDATE entry_searches SET status='failed',error=?,updated=? WHERE id=?", (message, time.time(), job))
    finally:
        stop.set(); heartbeat.join(timeout=4)


def submit(request):
    symbol = symbol_name(request.get("symbol"))
    dataset = request.get("datasetId")
    if not dataset:
        from random_replay import candidates
        choices = candidates().get(symbol, [])
        if not choices:
            raise DataError("Keine lokale Historie vorhanden. Zuerst im Datensammler importieren.", 404)
        dataset = choices[0]
    identity(dataset)
    req = {"symbol": symbol, "datasetId": dataset, "start": request.get("start"), "end": request.get("end")}
    for key in ("start", "end"):
        if req[key] is not None:
            timestamp(req[key])
    engine = search_binding()
    job = stable_id([VERSION, req, engine, uuid.uuid4().hex])
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        active = db.execute("SELECT id FROM entry_searches WHERE status IN ('queued','running','cancelling') AND updated>?", (time.time()-90,)).fetchone()
        if active:
            raise DataError("Es läuft bereits eine historische Entriesuche. Bitte fertig werden lassen oder abbrechen.", 409)
        db.execute("INSERT INTO entry_searches VALUES(?,?,?,?,?,?,?)", (job, "queued", time.time(), json.dumps(req), json.dumps({"phase": "Wartet", "done": 0, "total": 0}), None, None))
    threading.Thread(target=_calculate, args=(job, req, engine), daemon=True, name="tori-entry-search").start()
    return search_status(job)


def get(path, query):
    q = lambda name, default=None: query.get(name, [default])[0]
    if path == "/api/entries/runs":
        symbol = symbol_name(q("symbol"))
        with connection() as db:
            rows = db.execute("SELECT manifest FROM entry_runs WHERE symbol=? ORDER BY created DESC,id", (symbol,)).fetchall()
        return {"items": [json.loads(r[0]) for r in rows]}
    if path == "/api/entries/cases":
        return cases_page(q("run"), q("asof"), int(q("offset", "0")), int(q("limit", "100")), q("family", "all"), q("cohort", "all"), q("filled", "1") == "1",q('quality','all'))
    if path == "/api/entries/case":
        return detail(q("run"), q("case"), q("asof"),q('quality','all'))
    if path == "/api/entries/chart":
        return chart(q("run"), q("timeframe", "4h"), q("asof"))
    if path == "/api/entries/search":
        return search_status(q("id"))
    raise DataError("Unbekannte Entryroute.", 404)


def post(path, body):
    if path == "/api/entries/review":
        return review(body.get("run"), body.get("case"), body.get("verdict"), body.get("note", ""), body.get("delete") is True)
    if path == "/api/entries/search":
        return submit(body)
    if path == "/api/entries/cancel":
        job = identity(body.get("id"))
        with connection() as db:
            db.execute("UPDATE entry_searches SET status='cancelling' WHERE id=? AND status IN ('queued','running')", (job,))
        return search_status(job)
    raise DataError("Unbekannte Entryschreibroute.", 404)
