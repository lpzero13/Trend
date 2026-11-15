"""Build a close-of-session list for manual chart review."""

from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from urllib.parse import urlencode, urlsplit

from duckdb import Error as ParquetError

import archive_state
from daily_archive import MISSING_BAR_LIMIT, make_plan, summarize, update
from database import connection
from datasets import digest, path_for, read_dataset
from fan_geometry import analyze, profile
from fan_study import source_gaps
from lab_data import session_bounds
from models import Bar, DataError
from parquet_store import connect, validate_manifest, verified_paths
from settings import data_dir
from strategy_run_lock import study_lock


PREFIX = "daily-review:v1:"
PAGE = "/pruefung#abend-watchlist"
MAX_DISTANCE_ATR = 1.0
RECHECK_SECONDS = 3600


def read_frames(db, dataset_id, cutoff, month):
    """Read the same immutable 4h and 1D source candles used by the chart."""
    path = path_for(dataset_id)
    manifest = json.loads(path.read_text("utf-8"))
    storage = manifest.get("storage")
    frames = {"4h": [], "1D": []}
    if storage is None:
        material = read_dataset(dataset_id)["material"]
        return {tf: [Bar(**bar) for bar in material["bars"][tf] if bar["end"] <= cutoff]
                for tf in frames}
    validate_manifest(manifest)
    if manifest["id"] != dataset_id:
        raise DataError("Kursmanifest passt nicht zum Datensatz.", 409)
    paths = [str(block) for block in verified_paths(
        (entry for entry in storage["blocks"] if entry["month"] <= month), path.parent.parent)]
    if paths:
        rows = db.execute(
            'SELECT timeframe,"time","end",open,high,low,close,volume FROM read_parquet(?) '
            'WHERE timeframe IN (?,?) AND "end"<=? ORDER BY timeframe,"time"',
            [paths, *frames, cutoff]).fetchall()
        for tf, *bar in rows:
            frames[tf].append(Bar(*bar))
    return frames


def review_pair(lane):
    red, green, atr, close = lane["red"], lane["green"], lane["atr"], lane["close"]
    if not (red and green and atr and red["valid"] and green["valid"]
            and min(red["contacts"], green["contacts"]) >= 2
            and red["slope"] < 0 < green["slope"] and green["value"] < close < red["value"]):
        return None
    distance = (red["value"] - close) / atr
    if distance > MAX_DISTANCE_ATR:
        return None
    return {"close": close, "red": red["value"], "green": green["value"], "distanceAtr": distance,
            "distanceToGreenPct": (close - green["value"]) / close * 100,
            "redContacts": red["contacts"], "greenContacts": green["contacts"],
            "redLineId": red["id"], "qualified": red["qualified"] and green["qualified"]}


def changes(candidate, previous, previously_checked):
    if previous is None:
        return "first_report"
    if candidate["symbol"] not in previous:
        return "new" if candidate["symbol"] in previously_checked else "no_comparison"
    older = previous[candidate["symbol"]]
    if older["redLineId"] != candidate["redLineId"]:
        return "redrawn"
    delta = candidate["distanceAtr"] - older["distanceAtr"]
    if delta <= -0.1:
        return "closer"
    return "farther" if delta >= 0.1 else "unchanged"


def build_report(snapshot, previous=None, *, stop=None, progress=None):
    target = snapshot["targetSession"]
    opened, cutoff = session_bounds(target)
    absolute_cutoff = datetime.fromtimestamp(cutoff, timezone.utc).isoformat()
    prior = {item["symbol"]: item for item in previous["candidates"]} if previous else None
    previously_checked = set(previous.get("checkedSymbols", [])) if previous else set()
    rules = profile("master")
    candidates, coverage = [], Counter()
    issues, checked = {}, []
    with connect() as db:
        for symbol, source in snapshot["symbols"].items():
            if stop is not None and stop.is_set():
                raise InterruptedError
            if progress:
                progress({"phase": "reviewing", "symbol": symbol})
            if source["status"] in ("no_local_history", "error"):
                coverage[source["status"]] += 1
                if source["status"] == "error":
                    issues[symbol] = source.get("error", "Kursupdate fehlgeschlagen.")
                continue
            missing = source.get("missingBarsBySession", {}).get(target, 0)
            if missing >= MISSING_BAR_LIMIT:
                coverage["data_problem"] += 1
                issues[symbol] = f"{missing} fehlende 5-Minuten-Kerzen in der Zielsitzung."
                continue
            try:
                frames = read_frames(db, source["datasetId"], cutoff, target[:7])
                rows = frames["4h"]
                if not rows or rows[-1].time < opened:
                    coverage["missing_session_4h"] += 1
                    issues[symbol] = "Keine vollständige 4h-Kerze in dieser Sitzung."
                    continue
                lane = analyze(rows, "4h", rules=rules, symbol=symbol,
                               gaps=source_gaps(rows, cutoff, "4h"))
                pair = review_pair(lane)
                if pair is None:
                    coverage["no_candidate"] += 1
                    checked.append(symbol)
                    continue
                daily_rows = frames["1D"]
                daily_red = None
                daily_close = daily_rows[-1].end if daily_rows else None
                if daily_rows:
                    try:
                        daily = analyze(daily_rows, "1D", rules=rules, symbol=symbol,
                                        gaps=source_gaps(daily_rows, cutoff, "1D"))
                        if daily["red"]:
                            daily_red = daily["red"]["value"]
                    except DataError as exc:
                        if exc.status != 404:
                            raise
            except (DataError, OSError, ValueError, KeyError, TypeError, ParquetError) as exc:
                coverage["analysis_unavailable"] += 1
                issues[symbol] = str(exc) if isinstance(exc, DataError) else "Lokaler Kursdatensatz nicht lesbar."
                continue
            query = urlencode({"symbol": symbol, "dataset": source["datasetId"], "asof": absolute_cutoff,
                               "tf": "4h", "engine": "fan_master", "analysis": "1"})
            candidate = {**pair, "symbol": symbol, "datasetId": source["datasetId"],
                         "closedAt": rows[-1].end, "dailyClosedAt": daily_close, "dailyRed": daily_red,
                         "missing5m": missing,
                         "complete4hClose": rows[-1].end == cutoff, "completeDailyClose": daily_close == cutoff,
                         "chartPath": "/?" + query,
                         "reason": (f"{pair['distanceAtr']:.2f} ATR unter fallendem Rot, "
                                    f"{pair['redContacts']} Kontakte an Rot und "
                                    f"{pair['greenContacts']} an steigendem Grün.")}
            candidate["change"] = changes(candidate, prior, previously_checked)
            coverage["candidate"] += 1
            checked.append(symbol)
            candidates.append(candidate)
    candidates.sort(key=lambda c: (not c["complete4hClose"], not c["qualified"], c["distanceAtr"], c["symbol"]))
    return {"session": target, "cutoff": cutoff, "generatedAt": datetime.now(timezone.utc).isoformat(),
            "previousSession": previous["session"] if previous else None, "path": PAGE,
            "universes": sorted(snapshot["universes"]), "coverage": dict(coverage), "issues": issues,
            "checkedSymbols": checked,
            "dataUpdate": {key: snapshot.get(key) for key in ("alpaca", "counts", "behindTarget")},
            "candidates": candidates}


def latest():
    with connection() as db:
        key = archive_state.value(db, PREFIX + "latest")
        return archive_state.value(db, key) if key else None


def report_signature(snapshot, previous):
    from chart_sources import signature
    from market_calendar import CALENDAR_VERSION
    source_hashes = [digest(Path(__file__).with_name(name).read_text("utf-8")) for name in
                     ("daily_review.py", "fan_geometry.py", "fan_study.py", "market_calendar.py", "parquet_store.py")]
    target = snapshot["targetSession"]
    inputs = []
    for symbol, source in snapshot["symbols"].items():
        identity = source.get("datasetId")
        stamp = signature(identity) if identity else None
        inputs.append([symbol, stamp, source.get("error"), source["status"] == "error",
                       source.get("missingBarsBySession", {}).get(target, 0)])
    return digest([target, source_hashes, CALENDAR_VERSION, asdict(profile("master")),
                   sorted(snapshot["universes"]), inputs, previous])


def run(keys=None, *, scan_only=False, base_url=None, workers=1, max_minutes=55,
        stop=None, progress=None, budget=90):
    origin = base_url.rstrip("/") if base_url else ""
    parsed = urlsplit(origin)
    if base_url and (parsed.scheme not in ("http", "https") or not parsed.hostname
                     or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment):
        raise DataError("Serveradresse als HTTP(S)-Origin ohne Pfad oder Zugangsdaten angeben.", 400)
    with study_lock(data_dir() / "research" / "daily-review"):
        snapshot = (summarize(make_plan(keys), {}) if scan_only
                    else update(keys, workers=workers, max_minutes=max_minutes,
                                stop=stop, progress=progress, budget=budget))
        if stop is not None and stop.is_set():
            return {"interrupted": True, "session": snapshot["targetSession"], "dataUpdate": snapshot}
        scope = PREFIX + "runs:" + ",".join(sorted(snapshot["universes"])) + ":"
        key = scope + snapshot["targetSession"]
        with connection() as db:
            row = db.execute("SELECT value FROM settings WHERE key GLOB ? AND key < ? ORDER BY key DESC LIMIT 1",
                             (scope + "????-??-??", key)).fetchone()
            previous = json.loads(row[0]) if row else None
            memo = archive_state.value(db, PREFIX + "memo", {})
            latest_key = archive_state.value(db, PREFIX + "latest")
            old_report = archive_state.value(db, key) if memo.get("key") == key else None
        try:
            fingerprint = report_signature(snapshot, previous)
        except (DataError, OSError, ValueError, KeyError, TypeError):
            fingerprint = None
        reused = bool(fingerprint and old_report and fingerprint == memo.get("signature")
                      and 0 <= time.time() - memo["checkedAt"] < RECHECK_SECONDS)
        try:
            report = dict(old_report) if reused else build_report(snapshot, previous, stop=stop, progress=progress)
        except InterruptedError:
            return {"interrupted": True, "session": snapshot["targetSession"], "dataUpdate": snapshot}
        report["dataUpdate"] = {field: snapshot.get(field)
                                for field in ("alpaca", "counts", "behindTarget", "backlogSymbols")}
        report["cachedAnalysis"] = False
        if report != old_report or latest_key != key or not reused:
            with connection() as db:
                if report != old_report:
                    archive_state.put(db, key, report)
                if not reused:
                    if report["coverage"].get("analysis_unavailable") or report["coverage"].get("error"):
                        fingerprint = None
                    archive_state.put(db, PREFIX + "memo", {"key": key, "signature": fingerprint,
                                                            "checkedAt": time.time()})
                if latest_key != key:
                    archive_state.put(db, PREFIX + "latest", key)
    report["cachedAnalysis"] = reused
    if origin:
        report["url"] = origin + report["path"]
        for item in report["candidates"]:
            item["chartUrl"] = origin + item["chartPath"]
    return report
