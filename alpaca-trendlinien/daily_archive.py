"""Extend existing SIP archives through the last available regular US session."""

from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
import time

import alpaca
import archive_state
from database import connection
from datasets import read_dataset, save_dataset
from history_fast import parse_page
from history_http import Client
from lab_data import NORMALIZATION, resample_regular, session_bounds
from lab_splits import sessions_between
from models import Bar, DataError, NY
from parquet_store import block_path, connect
from settings import data_dir
from storage import preflight
from strategy_run_lock import study_lock
from universe_catalog import DEFINITIONS, read

UTC = timezone.utc
DELAY = timedelta(minutes=16)
PREFIX = "daily-archive:v1:"
FRAMES = ("5m", "1h", "4h", "1D")
BATCH_SIZE = 100
RETRY_SESSIONS = 5
CATCHUP_SESSIONS = 20
MISSING_BAR_LIMIT = 10


def trading_day(stamp):
    return datetime.fromtimestamp(stamp, NY).date().isoformat()


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
            rank = (trading_day(first), end, tail, -first, sources["5m"].get("count", 0),
                    manifest.get("importedAt", ""), path.stem)
            current = result.get(symbol)
            if (current is None or rank[0] < current["rank"][0]
                    or rank[0] == current["rank"][0] and rank[1:] >= current["rank"][1:]):
                result[symbol] = {"datasetId": path.stem, "lastSession": trading_day(end),
                                  "lastBarSession": trading_day(tail),
                                  "lastClose": end, "firstSession": trading_day(first), "rank": rank,
                                  "blocks": manifest.get("storage", {}).get("blocks"),
                                  "fine": material.get("bars", {}).get("5m", [])}
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
    """Count expected 5m candles against the actual stored timestamps."""
    start = session_bounds(min(recent))[0]
    months = {day[:7] for day in recent}
    files, present = {}, defaultdict(set)
    for symbol, base in bases.items():
        for entry in base["blocks"] or []:
            if entry["month"] in months:
                path = block_path(root, entry["path"])
                if path.is_file():
                    files.setdefault(path.as_posix(), []).append(symbol)
        present[symbol].update(bar["time"] for bar in base["fine"] if bar["time"] >= start)
    with connect() as db:
        for offset in range(0, len(files), 250):
            paths = list(files)[offset:offset + 250]
            rows = db.execute(
                'SELECT filename, "time" FROM read_parquet(?, filename=true) WHERE timeframe=? AND "time">=?',
                [paths, "5m", start]).fetchall()
            for path, stamp in rows:
                for symbol in files[path]:
                    present[symbol].add(stamp)
    return {symbol: {day: missing_bars(day, present[symbol]) for day in sorted(recent)
                     if base["firstSession"] <= day <= base["lastBarSession"]}
            for symbol, base in bases.items()}


def make_plan(keys=None, now=None, extra_symbols=None):
    now = now or datetime.now(UTC)
    if now.utcoffset() is None:
        raise DataError("Zeitpunkt braucht eine Zeitzone.", 400)
    target = available_session(now)
    keys = list(dict.fromkeys(keys or DEFINITIONS))
    universes, symbols = {}, set()
    for key in keys:
        universe = read(key)
        if universe:
            members = sorted({member["symbol"] for member in universe["members"]})
            universes[key] = {"asOf": universe["asOf"], "symbols": members}
            symbols.update(members)
        else:
            universes[key] = {"status": "membership_not_cached"}
    root = data_dir()
    if extra_symbols:
        extra = {s.upper().strip() for s in extra_symbols if s and s.strip()} - symbols
        if extra:
            symbols.update(inventory(extra, root).keys())
    bases = inventory(symbols, root)
    recent = set(sessions_between(
        (datetime.fromisoformat(target).date() - timedelta(days=14)).isoformat(), target)[-RETRY_SESSIONS:])
    gaps = recent_gaps(bases, recent, root)
    items = {}
    with connection() as db:
        for symbol in sorted(symbols):
            base = bases.get(symbol)
            if base is None:
                items[symbol] = {"status": "no_local_history"}
                continue
            saved = archive_state.value(db, PREFIX + symbol, {})
            matching = saved.get("datasetId") == base["datasetId"]
            missing = dict(saved.get("missingBarsBySession", {})) if matching else {}
            if matching and "missingBarsBySession" not in saved:
                older = set(saved.get("missingSessions", [])) - gaps[symbol].keys()
                if older:
                    dataset = read_dataset(base["datasetId"])
                    timestamps = {row["time"] for row in dataset["material"]["bars"]["5m"]}
                    missing.update({day: missing_bars(day, timestamps) for day in older})
            missing.update(gaps[symbol])
            missing = {day: count for day, count in missing.items() if count}
            pending = missing.keys() & recent
            last = base["lastSession"]
            through = max(last, saved.get("checkedThrough", last)) if matching else last
            if through < target:
                pending.update(sessions_between(through, target)[1:CATCHUP_SESSIONS + 1])
            if pending:
                # Fetch one already closed session as a split-adjustment check.
                pending.add(last)
            items[symbol] = {k: base[k] for k in ("datasetId", "lastSession", "lastClose")}
            quality = gap_status(missing)
            status = "gaps" if quality == "problem" else "tolerated_gaps" if missing else "current"
            items[symbol].update(status="pending" if pending else status, sessions=sorted(pending),
                                 gapStatus=quality, missingBarsBySession=missing,
                                 missingSessions=sorted(missing), checkedThrough=through)
    return {"targetSession": target, "targetCloseUtc": datetime.fromtimestamp(
        session_bounds(target)[1], UTC).isoformat(), "universes": universes, "symbols": items}


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


def extend(symbol, item, downloaded):
    base = read_dataset(item["datasetId"])
    fine = {row["time"]: Bar(**row) for row in base["material"]["bars"]["5m"]}
    overlap = fine.keys() & downloaded.keys()
    if downloaded and not overlap:
        raise DataError("Keine gemeinsame Kerze zur Prüfung der Splitbereinigung.", 409)
    for stamp in overlap:
        old, new = fine[stamp], downloaded[stamp]
        if (old.open, old.high, old.low, old.close) != (new.open, new.high, new.low, new.close):
            raise DataError("Kursrevision oder Split im Überlapp. Historie mit einheitlicher Splitbereinigung neu importieren.", 409)
    added = len(downloaded.keys() - fine.keys())
    revised = sum(fine[stamp].volume != downloaded[stamp].volume for stamp in overlap)
    fine.update(downloaded)
    missing = dict(item["missingBarsBySession"])
    for day in item["sessions"]:
        count = missing_bars(day, fine)
        if count:
            missing[day] = count
        else:
            missing.pop(day, None)
    identity, last_close = base["id"], base["sources"]["1D"]["lastClose"]
    if added or revised:
        sources, quality = resample_regular(sorted(fine.values(), key=lambda bar: bar.time))
        material = {tf: (rows, {"feed": "sip", "adjustment": "split", "normalization": NORMALIZATION,
                                "mode": "scheduled-sip-update", "rthQuality": quality,
                                "sourceDatasetId": base["id"], "volumeRevisions": revised,
                                "count": len(rows), "first": rows[0].time, "last": rows[-1].time,
                                "lastClose": rows[-1].end}) for tf, rows in sources.items()}
        identity = save_dataset(symbol, material, feed="sip", adjustment="split",
                                session=base["material"]["session"])
        last_close = sources["1D"][-1].end
    through = max(item["checkedThrough"], *item["sessions"])
    quality = gap_status(missing)
    status = "gaps" if quality == "problem" else "tolerated_gaps" if missing else "updated"
    return {"datasetId": identity, "lastSession": trading_day(last_close), "lastClose": last_close,
            "status": status, "gapStatus": quality,
            "checkedThrough": through,
            "missingSessions": sorted(missing), "missingBarsBySession": missing,
            "addedBars": added, "volumeRevisions": revised}


def update(keys=None, *, workers=4, max_minutes=55, now=None, client_factory=None, extra_symbols=None):
    if not 1 <= workers <= 8 or not 1 <= max_minutes <= 1440:
        raise DataError("Erwartet werden 1–8 Worker und 1–1440 Minuten Laufzeitbudget.", 400)
    deadline = time.monotonic() + max_minutes * 60

    def expired():
        return time.monotonic() >= deadline

    with study_lock(data_dir() / "research" / "daily-archive"):
        report = make_plan(keys, now, extra_symbols=extra_symbols)
        items = report["symbols"]
        pending = sorted((symbol for symbol in items if items[symbol]["status"] == "pending"),
                         key=lambda symbol: (items[symbol]["checkedThrough"], symbol))
        if not pending:
            return summarize(report, {})
        preflight(symbols=len(pending), history_days=max(len(items[s]["sessions"]) for s in pending),
                  bytes_per_symbol_day=8000)
        client = client_factory() if client_factory else Client(*alpaca.credentials())
        client.interrupted = expired
        try:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                for offset in range(0, len(pending), BATCH_SIZE):
                    if expired():
                        break
                    batch = pending[offset:offset + BATCH_SIZE]
                    process_batch(pool, client, batch, items, report["targetSession"], expired)
        finally:
            client.close()
        return summarize(report, client.snapshot())


def process_batch(pool, client, symbols, items, target, expired):
    by_day, downloaded = defaultdict(list), defaultdict(dict)
    for symbol in symbols:
        for day in items[symbol]["sessions"]:
            by_day[day].append(symbol)
    for day, members in sorted(by_day.items()):
        try:
            for symbol, rows in fetch_session(members, day, target, client.request).items():
                downloaded[symbol].update(rows)
        except InterruptedError:
            return
        except DataError as exc:
            for symbol in members:
                items[symbol].update(status="error", error=str(exc))

    def publish(symbol):
        if expired() or items[symbol]["status"] != "pending":
            return symbol, {}
        try:
            result = extend(symbol, items[symbol], downloaded[symbol])
            with connection() as db:
                archive_state.put(db, PREFIX + symbol, result)
            return symbol, result
        except (DataError, OSError) as exc:
            return symbol, {"status": "error", "error": str(exc)}

    for symbol, result in pool.map(publish, symbols):
        items[symbol].update(result)


def summarize(report, metrics):
    items = report["symbols"]
    for universe in report["universes"].values():
        if "symbols" in universe:
            universe["counts"] = dict(Counter(items[symbol]["status"] for symbol in universe["symbols"]))
    report.update(counts=dict(Counter(item["status"] for item in items.values())), alpaca=metrics,
                  gapCounts=dict(Counter(item["gapStatus"] for item in items.values() if "gapStatus" in item)),
                  missingBarsProblemThreshold=MISSING_BAR_LIMIT,
                  behindTarget=sum(item.get("lastSession", report["targetSession"]) < report["targetSession"]
                                   for item in items.values()))
    return report
