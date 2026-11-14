"""Bounded delayed imports, bootstrap and resumable market-time processing."""
from datetime import date, datetime, timedelta
import os
import shutil
import signal
import threading
import time

from models import DataError, NY
from paper_data import AlpacaPaper, cutoff_at
from paper_engine import aggregate, bucket, candle_distance, day_at, line_close, market_minute, previous_bucket, session_buckets
from paper_store import (
    DB_NAME, account, advance, as_plan, connection, first_minute, get_meta, issue, relevant_plans,
    set_meta, store_minutes,
)
from settings import data_dir
from strategy_run_lock import study_lock

OVERLAP = 10 * 60
CATCHUP = 7 * 86400
HEADROOM = 64 * 1024 * 1024


def storage_guard():
    path = data_dir() / DB_NAME
    limit = max(32, int(os.environ.get("TORI_PAPER_STORAGE_MIB", "1024"))) * 1024**2
    used = sum(p.stat().st_size for p in path.parent.glob("paper.sqlite3*") if p.is_file())
    if shutil.disk_usage(path.parent).free < HEADROOM or used >= limit:
        raise DataError("Das Paper-Speicherlimit ist erreicht oder der Datenträger ist fast voll.", 507)
    return used


def has_session(start, end):
    return start < end and any(max(start, a)+60 <= min(end, b)
                               for a, b in session_buckets(day_at(start), day_at(end), "1D"))


def import_windows(db, cutoff):
    cursor = get_meta(db, "cursor")
    starts = {}
    for plan in relevant_plans(db):
        first = first_minute(plan)
        if first + 60 > cutoff:
            continue
        ticker = plan["symbol"]
        tf = plan["spec"]["timeframe"]
        bootstrapped = get_meta(db, "bootstrapped:" + plan["id"])
        if not bootstrapped and plan["state"] == "watching":
            source = bucket(first, tf)
            start = previous_bucket(source[0], tf)[0]
        else:
            start = max(first, (cursor or first) - OVERLAP)
        starts[ticker] = min(start, starts.get(ticker, start))
    if not starts:
        return (), None, cutoff
    # Include a needed bootstrap window even for a newly activated symbol.
    start = min(starts.values())
    end = min(cutoff, start + CATCHUP)
    return tuple(sorted(starts)), start, end


def find_actions(db, plans, actions, end, now):
    end_day = day_at(end)
    for plan in plans:
        if plan["symbol"] not in actions:
            continue
        spec = plan["spec"]
        anchor_day = day_at(min(spec["action"][0]["at"], spec["safety"][0]["at"]))
        keys = set(get_meta(db, "actions_seen:" + plan["id"], []))
        for event in actions[plan["symbol"]]:
            raw_day = event["date"]
            event_day = date.fromisoformat(raw_day) if raw_day else None
            identity = event["id"] + ":" + str(raw_day)
            if identity in keys or (event_day is not None and (event_day < anchor_day or event_day > end_day)):
                continue
            first = first_minute(plan)
            if event_day:
                clock = datetime.combine(event_day, datetime.min.time(), tzinfo=NY)
                at = market_minute(int(clock.timestamp()))
            else:
                at = first
            issue(db, plan["symbol"], max(at, first), "corporate_action:" + plan["id"],
                  {**event, "plan": plan["id"]}, now)
            keys.add(identity)
        set_meta(db, "actions_seen:" + plan["id"], sorted(keys))


def heartbeat(phase, now, **extra):
    with connection() as read:
        if read is None or not get_meta(read, "account"):
            return
    with connection(write=True) as db:
        state = get_meta(db, "worker", {})
        state.update(phase=phase, heartbeat=now, **extra)
        set_meta(db, "worker", state)


def prepare_preview(provider, plan, cutoff):
    spec, ticker = plan["spec"], plan["symbol"]
    tf = spec["timeframe"]
    reference = previous_bucket(market_minute(cutoff), tf)
    pairs = {reference} | {bucket(point["at"], tf) for name in ("safety", "action") for point in spec[name]}
    rows = []
    ordered = sorted(pairs)
    for start, end in ordered:
        data = provider.bars([ticker], start, end)[ticker] if end <= cutoff else []
        bar = aggregate(data, start, end)
        rows.append({"at": start, "end": end, "ordinal": candle_distance(ordered[0][0], start, tf),
                     "ohlc": bar.prices()[:4] if bar else None,
                     "action": str(line_close(spec, "action", start)), "safety": str(line_close(spec, "safety", start))})
    return {"requested": plan["data"]["preview_requested"], "reference": reference[0], "rows": rows}


def cycle(provider=None, now=None):
    now = int(time.time()) if now is None else now
    cutoff = cutoff_at(now)
    with connection() as db:
        if db is None or not get_meta(db, "account"):
            return {"phase": "no_account"}
        account(db)
        plans = relevant_plans(db)
        symbols, start, end = import_windows(db, cutoff)
        checked = get_meta(db, "actions_checked", {})
        prior = get_meta(db, "worker", {})
        awaiting = []
        for row in db.execute("SELECT * FROM plans WHERE state='draft' ORDER BY updated"):
            candidate = as_plan(row)
            requested = candidate["data"].get("preview_requested")
            sample = get_meta(db, "preview:" + candidate["id"], {})
            if requested and requested != sample.get("requested"):
                awaiting.append(candidate)
                break
    if not plans and not awaiting:
        heartbeat("waiting", now, error=None)
        return {"phase": "waiting"}
    heartbeat("polling", now, error=None)
    provider = AlpacaPaper() if provider is None else provider
    imported = {}
    actions = {}
    try:
        storage_guard()
        # Overlap detects revisions during normal updates. Avoid network traffic
        # when no new regular minute has become available since a successful poll.
        last_end = prior.get("queried_end", 0)
        needs_retry = prior.get("phase") in ("error", "attention", "catching_up")
        new_symbol = tuple(prior.get("queried_symbols", ())) != symbols
        if symbols and has_session(start, end) and (needs_retry or new_symbol or not last_end or has_session(last_end, end)):
            active = [p for p in plans if p["symbol"] in symbols]
            needed = {
                p["symbol"] for p in active
                if not isinstance(checked.get(p["id"]), dict)
                or checked[p["id"]].get("market_day") != day_at(end).isoformat()
                or now - checked[p["id"]].get("at", 0) >= 900
            }
            if needed:
                anchor = min(day_at(min(p["spec"]["action"][0]["at"], p["spec"]["safety"][0]["at"]))
                             for p in active if p["symbol"] in needed)
                actions = provider.actions(needed, cutoff, since=anchor)
            imported = provider.bars(symbols, start, end)
        sample = None
        if awaiting:
            try:
                sample = prepare_preview(provider, awaiting[0], cutoff)
            except DataError as error:
                sample = {"requested": awaiting[0]["data"]["preview_requested"], "rows": [], "error": str(error)}
        with connection(write=True) as db:
            if sample:
                set_meta(db, "preview:" + awaiting[0]["id"], sample)
            original_cursor = get_meta(db, "cursor", 0)
            # An activation after the read above is outside this poll's decision window.
            matching = [p for p in relevant_plans(db) if p["id"] in {old["id"] for old in plans}]
            if actions:
                for ticker, reports in actions.items():
                    cache_key = "actions_feed:" + ticker
                    cached = {item["id"]: item for item in get_meta(db, cache_key, [])}
                    cached.update({item["id"]: item for item in reports})
                    set_meta(db, cache_key, list(cached.values()))
                for p in matching:
                    if p["symbol"] in actions:
                        checked[p["id"]] = {"at": now, "market_day": day_at(end).isoformat()}
                set_meta(db, "actions_checked", checked)
            if imported:
                checked_actions = {ticker: get_meta(db, "actions_feed:" + ticker, []) for ticker in symbols}
                find_actions(db, matching, checked_actions, end, now)
            for ticker, rows in imported.items():
                store_minutes(db, ticker, rows, now)
            if imported:
                for plan in matching:
                    tf = plan["spec"]["timeframe"]
                    source = bucket(first_minute(plan), tf)
                    boot_start = previous_bucket(source[0], tf)[0]
                    # Simply having a successful HTTP response doesn't prove the prefix.
                    # Check the entire relevant range once it is available.
                    if (plan["symbol"] in imported and start <= boot_start and end >= first_minute(plan)
                            and not get_meta(db, "bootstrapped:" + plan["id"])):
                        count = db.execute("SELECT count(*) FROM bars WHERE symbol=? AND at>=? AND at<?",
                                           (plan["symbol"], boot_start, first_minute(plan))).fetchone()[0]
                        expected = sum((min(b, first_minute(plan))-max(a, boot_start))//60
                                       for a, b in session_buckets(day_at(boot_start), day_at(first_minute(plan)), "1D")
                                       if b > boot_start and a < first_minute(plan))
                        if count == expected:
                            set_meta(db, "bootstrapped:" + plan["id"], True)
            cursor = advance(db, end, now, limit=1200)
            selected = relevant_plans(db)
            phase = "waiting"
            if selected:
                if any(p["state"] == "ambiguous" for p in selected):
                    phase = "attention"
                else:
                    next_at = market_minute(max(cursor or 0, min(first_minute(p) for p in selected)))
                    if next_at+60 <= cutoff:
                        phase = "catching_up" if cursor and cursor > original_cursor else "attention"
                    elif day_at(cutoff) != day_at(next_at):
                        phase = "market_closed"
            worker = get_meta(db, "worker", {})
            worker.update(heartbeat=now, phase=phase, error=None, cutoff=cutoff, processed=cursor,
                          market_lag_seconds=now-cursor if cursor is not None else None,
                          rows=sum(len(data) for data in imported.values()), attempts=provider.attempts)
            if imported:
                worker["last_import"] = now
                worker.update(queried_end=end, queried_symbols=list(symbols))
            set_meta(db, "worker", worker)
            return worker
    except (DataError, OSError) as error:
        message = str(error) if isinstance(error, DataError) else "Minutenimport oder Persistenz fehlgeschlagen."
        heartbeat("error", now, error=message, cutoff=cutoff)
        raise


def run(*, once=False):
    stop = threading.Event()
    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGTERM, lambda *_: stop.set())
        signal.signal(signal.SIGINT, lambda *_: stop.set())
    failures = 0
    with study_lock(data_dir() / "paper" / "worker"):
        try:
            while not stop.is_set():
                try:
                    result = cycle()
                    failures = 0
                    interval = 5 if result["phase"] == "catching_up" else 60
                except DataError as error:
                    if once:
                        raise
                    failures += 1
                    # SQLite may be unavailable on disk failure; service restart logs still show it.
                    heartbeat("error", int(time.time()), error=str(error))
                    interval = min(300, 30 * 2**min(failures, 4))
                if once:
                    return result
                stop.wait(interval)
        finally:
            if not once:
                heartbeat("stopped", int(time.time()))
