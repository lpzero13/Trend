"""Extend existing SIP archives through the last available regular US session."""

from collections import Counter, defaultdict
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
import time

import alpaca
import archive_state
from database import connection
from daily_delta import SplitConflict, extend, trading_day
from datasets import digest, path_for, register_quality
from duckdb import Error as ParquetError
from history_fast import parse_page
from history_http import Client
from lab_data import NORMALIZATION, session_bounds
from lab_splits import sessions_between
from models import Bar, DataError, NY
from parquet_store import FORMAT, INCREMENTAL_FORMAT, block_path, connect
from settings import data_dir
from storage import preflight
from strategy_run_lock import study_lock
from universe_catalog import read

UTC = timezone.utc
DELAY = timedelta(minutes=16)
PREFIX = "daily-archive:v1:"
FRAMES = ("5m", "1h", "4h", "1D")
BATCH_SIZE = 100
RETRY_SESSIONS = 5
NIGHTLY_SESSIONS = 2
MAX_SESSIONS = 20
DEFAULT_UNIVERSES = ("nasdaq100", "dow30", "sp500")
CACHE_PREFIX = "daily-download:v1:"
MISSING_BAR_LIMIT = 10


def available_session(now):
    day = now.astimezone(NY).date()
    sessions = sessions_between((day - timedelta(days=14)).isoformat(), day.isoformat())
    cutoff = (now - DELAY).timestamp()
    return next(day for day in reversed(sessions) if session_bounds(day)[1] <= cutoff)


def inventory(symbols, root):
    """Choose the freshest version of each longest compatible history."""
    result = {}
    for path in (root / "datasets").glob("*.json"):
        try:
            if path.is_symlink():
                continue
            manifest = json.loads(path.read_text("utf-8"))
            material = manifest["material"]
            store = manifest.get("storage", {})
            if (manifest["id"] != path.stem or store.get("format") not in (FORMAT, INCREMENTAL_FORMAT)
                    or material.get("bars") != {}):
                continue
            symbol = material["symbol"]
            if (symbol not in symbols or material.get("provider") != "Alpaca"
                    or material.get("feed") != "sip" or material.get("adjustment") != "split"
                    or material.get("dataKind") == "synthetic"
                    or any(material.get("normalization", {}).get(tf) != NORMALIZATION for tf in FRAMES)):
                continue
            sources = manifest["sources"]
            if any(sources[tf].get("mode") == "synthetic-offline-fixture" for tf in FRAMES):
                continue
            first = sources["5m"]["first"]
            end = sources["1D"]["lastClose"]
            tail = sources["5m"]["lastClose"]
            if not all(type(value) is int and value > 0 for value in (first, end, tail)):
                continue
            rank = (trading_day(first), tail, end, -first, sources["5m"].get("count", 0),
                    manifest.get("importedAt", ""), path.stem)
            current = result.get(symbol)
            if (current is None or rank[0] < current["rank"][0]
                    or rank[0] == current["rank"][0] and rank[1:] >= current["rank"][1:]):
                result[symbol] = {"datasetId": path.stem, "lastSession": trading_day(end),
                                  "lastBarSession": trading_day(tail),
                                  "lastClose": end, "firstSession": trading_day(first), "rank": rank,
                                  "blocks": store["blocks"],
                                  "checkpoint": manifest.get("dailyArchive", {})}
        except (OSError, ValueError, KeyError, TypeError, OverflowError):
            continue
    return result


def missing_bars(day, timestamps):
    start, end = session_bounds(day)
    return sum(stamp not in timestamps for stamp in range(start, end, 300))


def gap_status(missing):
    if any(count >= MISSING_BAR_LIMIT for count in missing.values()):
        return "problem"
    return "tolerated" if missing else "complete"


def recent_gaps(bases, recent, root):
    """Read only trailing 5m timestamps of archives without a checkpoint."""
    start = session_bounds(min(recent))[0]
    end = session_bounds(max(recent))[1]
    months = {day[:7] for day in recent}
    result, errors = {}, set()
    with connect() as db:
        for symbol, base in bases.items():
            try:
                files = [block_path(root, entry["path"]).as_posix() for entry in base["blocks"]
                         if entry["month"] in months]
                present = set()
                if files:
                    rows = db.execute(
                        'SELECT "time" FROM read_parquet(?) WHERE timeframe=? AND "time">=? AND "time"<?',
                        [files, "5m", start, end]).fetchall()
                    present.update(stamp for stamp, in rows)
                result[symbol] = {day: missing_bars(day, present) for day in sorted(recent)
                                  if base["firstSession"] <= day <= base["lastBarSession"]}
            except (OSError, ValueError, KeyError, TypeError, ParquetError):
                errors.add(symbol)
    return result, errors


def make_plan(keys=None, now=None, *, mode="daily", max_sessions=None, repair_days=()):
    now = now or datetime.now(UTC)
    if now.utcoffset() is None:
        raise DataError("Zeitpunkt braucht eine Zeitzone.", 400)
    if mode not in ("daily", "catchup", "repair") or repair_days and mode != "repair":
        raise DataError("Ungültiger Update-Modus oder Reparaturdatum.", 400)
    if max_sessions is None:
        max_sessions = NIGHTLY_SESSIONS if mode == "daily" else MAX_SESSIONS
    if not 1 <= max_sessions <= (NIGHTLY_SESSIONS if mode == "daily" else MAX_SESSIONS):
        raise DataError("Sitzungslimit außerhalb des erlaubten Bereichs.", 400)
    target = available_session(now)
    for day in repair_days:
        try:
            valid = datetime.fromisoformat(day).date().isoformat() == day and day <= target and session_bounds(day)
        except ValueError:
            valid = False
        if not valid:
            raise DataError("Reparaturdatum muss eine abgeschlossene XNYS-Sitzung sein.", 400)
    keys = list(dict.fromkeys(keys or DEFAULT_UNIVERSES))
    universes, symbols = {}, set()
    for key in keys:
        if key not in DEFAULT_UNIVERSES:
            raise DataError("Der Tageslauf unterstützt Nasdaq-100, Dow-30 und S&P 500.", 400)
        universe = read(key)
        if universe:
            members = sorted({member["symbol"] for member in universe["members"]})
            universes[key] = {"asOf": universe["asOf"], "symbols": members}
            symbols.update(members)
        else:
            universes[key] = {"status": "membership_not_cached"}
    root = data_dir()
    bases = inventory(symbols, root)
    with connection() as db:
        saved = {symbol: archive_state.value(db, PREFIX + symbol, {}) for symbol in bases}
    checkpoints = {symbol: saved[symbol] if saved[symbol].get("datasetId") == base["datasetId"]
                   else base["checkpoint"] for symbol, base in bases.items()}
    recent = set(sessions_between(
        (datetime.fromisoformat(target).date() - timedelta(days=14)).isoformat(), target)[-RETRY_SESSIONS:])
    unchecked = {symbol: base for symbol, base in bases.items() if not checkpoints[symbol]}
    gaps, errors = recent_gaps(unchecked, recent, root) if unchecked else ({}, set())
    items = {}
    for symbol in sorted(symbols):
        base = bases.get(symbol)
        if base is None:
            items[symbol] = {"status": "no_local_history"}
            continue
        checkpoint = checkpoints[symbol]
        missing = {day: count for day, count in {
            **checkpoint.get("missingBarsBySession", {}), **gaps.get(symbol, {})}.items() if count}
        tail = base["lastBarSession"]
        through = max(tail, checkpoint.get("checkedThrough", tail))
        backlog = sessions_between(through, target)[1:] if through < target else []
        if mode == "repair":
            work = [day for day in sorted(set(repair_days or missing))
                    if base["firstSession"] <= day <= through][:max_sessions]
        else:
            work = backlog[:max_sessions] if mode == "catchup" or len(backlog) <= max_sessions else []
        overlap = tail if work else None
        quality = gap_status(missing)
        status = ("backlog" if backlog else "gaps" if quality == "problem"
                  else "tolerated_gaps" if missing else "current")
        if symbol in errors:
            status = "error"
            work = []
        items[symbol] = {k: base[k] for k in ("datasetId", "lastSession", "lastBarSession", "lastClose")}
        items[symbol].update(status="pending" if work else status,
                             sessions=sorted(set(work + [overlap])) if work else [],
                             overlapSession=overlap if work else None, gapStatus=quality,
                             backlogSessions=len(backlog), missingBarsBySession=missing,
                             missingSessions=sorted(missing), checkedThrough=through)
        if status == "error":
            items[symbol].update(errorKind="local_data",
                                 error="5-Minuten-Zeitstempel im lokalen Kursbestand sind nicht lesbar.")
    return {"targetSession": target, "targetCloseUtc": datetime.fromtimestamp(
        session_bounds(target)[1], UTC).isoformat(), "mode": mode, "universes": universes, "symbols": items}


def fetch_session(symbols, day, target, request):
    opened, closed = session_bounds(day)
    start, end = (datetime.fromtimestamp(at, UTC) for at in (opened, closed))
    result = {symbol: {} for symbol in symbols}
    params = {"symbols": ",".join(symbols), "timeframe": "5Min", "feed": "sip", "adjustment": "split",
              "asof": target, "start": start.isoformat(), "end": (end - timedelta(seconds=1)).isoformat(),
              "sort": "asc", "limit": 10000}
    tokens = set()
    while True:
        page = request(params)
        bars = page.get("bars") if isinstance(page, dict) else None
        if not isinstance(bars, dict) or set(bars) - result.keys():
            raise DataError("Unerwartete Symbolantwort von Alpaca.", 502)
        for symbol, rows in bars.items():
            for bar in parse_page(rows, start, end):
                if (bar.time - opened) % 300 or result[symbol].get(bar.time, bar) != bar:
                    raise DataError("Widersprüchliche oder nicht bündige 5-Minuten-Kerze.", 502)
                result[symbol][bar.time] = bar
        token = page.get("next_page_token")
        if token is None:
            return result
        if not isinstance(token, str) or not token or token in tokens or len(tokens) >= 1000:
            raise DataError("Ungültige Alpaca-Paginierung.", 502)
        tokens.add(token)
        params["page_token"] = token


def cache_key(mode, target, day, symbol):
    return f"{CACHE_PREFIX}{mode}:{target}:{day}:{symbol}"


def cached_download(db, key):
    raw = archive_state.value(db, key)
    if raw is None:
        return None
    rows = raw["rows"]
    if raw["sha256"] != digest(rows):
        raise ValueError("gespeicherter Download hat eine ungültige Prüfsumme")
    return [Bar(**row) for row in rows]


def update(keys=None, *, workers=1, max_minutes=55, now=None, client_factory=None,
           mode="daily", max_sessions=None, repair_days=(), progress=None, stop=None, budget=90):
    if not 1 <= workers <= 8 or not 1 <= max_minutes <= 1440 or not 1 <= budget <= 190:
        raise DataError("Erwartet werden 1–8 Worker, 1–1440 Minuten und ein Budget von 1–190.", 400)
    from history_archive import archive_lock
    deadline = time.monotonic() + max_minutes * 60

    def expired():
        return (stop is not None and stop.is_set()) or time.monotonic() >= deadline

    def tick(phase, **fields):
        if progress:
            progress({"phase": phase, **fields})

    # Same interprocess lock as the v1/v2 bulk collector, across all update modes.
    with archive_lock(), study_lock(data_dir() / "research" / "daily-archive"):
        tick("planning", mode=mode)
        report = make_plan(keys, now, mode=mode, max_sessions=max_sessions, repair_days=repair_days)
        items = report["symbols"]
        pending = sorted((symbol for symbol in items if items[symbol]["status"] == "pending"),
                         key=lambda symbol: (items[symbol]["checkedThrough"], symbol))
        report["interrupted"] = expired()
        if not pending or expired():
            return summarize(report, {})
        preflight(symbols=len(pending), history_days=max(len(items[s]["sessions"]) for s in pending),
                  bytes_per_symbol_day=8000)
        client = None

        def request(params):
            nonlocal client
            if expired():
                raise InterruptedError
            if client is None:
                client = client_factory() if client_factory else Client(*alpaca.credentials(), budget=budget)
                client.interrupted = expired
            return client.request(params)

        def publish(symbol):
            item = items[symbol]
            cache_keys = [cache_key(mode, report["targetSession"], day, symbol) for day in item["sessions"]]
            try:
                with connection() as db:
                    data = [cached_download(db, key) for key in cache_keys]
                if any(rows is None for rows in data):
                    raise ValueError("Download-Checkpoint unvollständig")
                downloaded = {bar.time: bar for rows in data for bar in rows}
                result = extend(symbol, item, downloaded)
                remaining = sessions_between(result["checkedThrough"], report["targetSession"])
                result["backlogSessions"] = max(0, len(remaining) - 1)
                result["lastBarSession"] = max(item["lastBarSession"],
                                              max((trading_day(stamp) for stamp in downloaded), default=""))
                with connection() as db:
                    if result["datasetId"] != item["datasetId"]:
                        quality = json.loads(path_for(result["datasetId"]).read_text("utf-8"))["quality"]
                        register_quality(db, result["datasetId"], quality)
                    archive_state.put(db, PREFIX + symbol, result)
                    db.executemany("DELETE FROM settings WHERE key=?", [(key,) for key in cache_keys])
                return result
            except SplitConflict as exc:
                return {"status": "error", "errorKind": "split_or_revision", "error": str(exc)}
            except (DataError, OSError, ValueError, KeyError, TypeError, ParquetError) as exc:
                return {"status": "error", "errorKind": "local_data", "error": str(exc)}

        try:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                for offset in range(0, len(pending), BATCH_SIZE):
                    if expired():
                        break
                    batch = pending[offset:offset + BATCH_SIZE]
                    fetch_batch(request, batch, items, report["targetSession"], mode, expired, tick)
                    ready = [symbol for symbol in batch if items[symbol]["status"] == "pending"]
                    # Only submit one bounded wave at once, including on SIGTERM.
                    for start in range(0, len(ready), workers):
                        if expired():
                            break
                        wave = ready[start:start + workers]
                        for symbol in wave:
                            tick("publishing", symbol=symbol)
                        for symbol, result in zip(wave, pool.map(publish, wave)):
                            items[symbol].update(result)
                            tick("symbol", symbol=symbol, status=result["status"])
        except InterruptedError:
            pass
        finally:
            if client is not None:
                client.close()
        report["interrupted"] = expired()
        return summarize(report, client.snapshot() if client is not None else {})


def fetch_batch(request, symbols, items, target, mode, expired, tick):
    by_day = defaultdict(list)
    for symbol in symbols:
        for day in items[symbol]["sessions"]:
            by_day[day].append(symbol)
    for day, members in sorted(by_day.items()):
        if expired():
            raise InterruptedError
        waiting = []
        with connection() as db:
            for symbol in members:
                key = cache_key(mode, target, day, symbol)
                try:
                    if db.execute("SELECT 1 FROM settings WHERE key=?", (key,)).fetchone() is None:
                        waiting.append(symbol)
                    else:
                        cached_download(db, key)
                except (ValueError, KeyError, TypeError):
                    waiting.append(symbol)
        if not waiting:
            continue
        tick("downloading", session=day, symbols=len(waiting))
        try:
            fetched = fetch_session(waiting, day, target, request)
        except DataError as exc:
            for symbol in waiting:
                items[symbol].update(status="error", errorKind="provider", error=str(exc))
            continue
        with connection() as db:
            for symbol, rows in fetched.items():
                packed = [asdict(bar) for bar in rows.values()]
                archive_state.put(db, cache_key(mode, target, day, symbol),
                                  {"rows": packed, "sha256": digest(packed)})


def summarize(report, metrics):
    items = report["symbols"]
    for universe in report["universes"].values():
        if "symbols" in universe:
            universe["counts"] = dict(Counter(items[symbol]["status"] for symbol in universe["symbols"]))
    report.update(counts=dict(Counter(item["status"] for item in items.values())), alpaca=metrics,
                  gapCounts=dict(Counter(item["gapStatus"] for item in items.values() if "gapStatus" in item)),
                  missingBarsProblemThreshold=MISSING_BAR_LIMIT,
                  behindTarget=sum(item.get("checkedThrough", report["targetSession"]) < report["targetSession"]
                                   for item in items.values()),
                  backlogSymbols=sum(bool(item.get("backlogSessions")) for item in items.values()))
    return report
