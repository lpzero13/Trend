"""Persistent, timestamp-ordered paper ledger. All market decisions commit together."""
from contextlib import contextmanager
from datetime import timedelta
from decimal import Decimal
import hashlib
import json
import re
import sqlite3
import time
import uuid

from market_calendar import CALENDAR_VERSION
from models import DataError
from paper_engine import (
    CHANGES, MAX_ACTIVE_PLANS, MAX_POSITIONS, MAX_SYMBOLS, MODEL, NORMALIZATION, Minute,
    aggregate, bucket, crossed, day_at, entry, exit_at_open, exit_inside_minute,
    integer, line_close, market_minute, normalize_plan, number, previous_bucket, settle,
)
from settings import data_dir

DB_NAME = "paper/paper.sqlite3"
SCHEMA_VERSION = 1
VERSION = "paper-ledger-v1"
ACTIVE = ("watching", "pending", "open")
SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS plans (
    id TEXT PRIMARY KEY, symbol TEXT NOT NULL, spec TEXT NOT NULL, state TEXT NOT NULL,
    created INTEGER NOT NULL, activated INTEGER, updated INTEGER NOT NULL, data TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS bars (
    symbol TEXT NOT NULL, at INTEGER NOT NULL, payload TEXT NOT NULL, fingerprint TEXT NOT NULL,
    received INTEGER NOT NULL, PRIMARY KEY(symbol,at)
);
CREATE TABLE IF NOT EXISTS issues (
    symbol TEXT NOT NULL, at INTEGER NOT NULL, kind TEXT NOT NULL, detail TEXT NOT NULL,
    resolved INTEGER, PRIMARY KEY(symbol,at,kind)
);
CREATE TABLE IF NOT EXISTS events (
    seq INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL UNIQUE,
    plan_id TEXT REFERENCES plans(id), symbol TEXT, at INTEGER NOT NULL,
    recorded INTEGER NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL,
    source_at INTEGER,
    FOREIGN KEY(symbol,source_at) REFERENCES bars(symbol,at)
);
"""


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def require_object(value):
    if not isinstance(value, dict):
        raise DataError("JSON-Objekt erwartet.", 400)
    return value


@contextmanager
def connection(*, write=False):
    root = data_dir()
    path = root / DB_NAME
    if path.is_symlink() or path.parent.is_symlink():
        raise DataError("Paper-Datenbankpfad darf kein Link sein.", 409)
    if write:
        path.parent.mkdir(parents=True, exist_ok=True)
    elif not path.exists():
        yield None
        return
    db = sqlite3.connect(path if write else path.as_uri() + "?mode=ro", uri=not write, timeout=10)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA foreign_keys=ON")
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, SCHEMA_VERSION) or (version == 0 and not write):
            raise DataError("Unbekanntes Paper-Datenbankschema.", 409)
        if write:
            if version == 0:
                db.executescript("BEGIN IMMEDIATE;\n" + SCHEMA +
                                 f"\nPRAGMA user_version={SCHEMA_VERSION};\nCOMMIT;")
            db.execute("BEGIN IMMEDIATE")
        else:
            db.execute("BEGIN")
        yield db
        db.commit()
    finally:
        db.close()


def get_meta(db, key, default=None):
    row = db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return json.loads(row[0]) if row else default


def blocking_issue(db, plan, at):
    return db.execute("""SELECT 1 FROM issues
        WHERE symbol=? AND at<=? AND resolved IS NULL AND kind!='missing_or_no_trade'
          AND (kind NOT LIKE 'corporate_action:%' OR kind=?)
        LIMIT 1""", (plan["symbol"], at, "corporate_action:" + plan["id"])).fetchone() is not None


def set_meta(db, key, value):
    db.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", (key, encode(value)))


def account(db):
    value = get_meta(db, "account")
    if not value:
        raise DataError("Lege zuerst ein Paper-Konto an.", 409)
    if value["engine"] != VERSION or value["calendar"] != CALENDAR_VERSION:
        raise DataError("Paper-Konto gehört einer anderen Engine-/Kalenderkennung.", 409)
    return value


def create_account(raw, now=None):
    raw = require_object(raw)
    if set(raw) - {"capital", "fee", "slippage_bps"}:
        raise DataError("Unbekannte Kontoeinstellung.", 400)
    now = int(time.time()) if now is None else now
    capital = number(raw.get("capital", "10000"), "Startkapital", "1")
    fee = number(raw.get("fee", "0"), "Gebühr", "0", "1000")
    value = {"capital": str(capital), "fee": str(fee),
             "slippage_bps": integer(raw.get("slippage_bps", 5), "Slippage", 0, 500),
             "currency": "USD", "model": MODEL, "engine": VERSION,
             "calendar": CALENDAR_VERSION, "normalization": NORMALIZATION,
             "feed": "sip", "adjustment": "raw", "created_at": now}
    with connection(write=True) as db:
        original = get_meta(db, "account")
        if original:
            if any(original[key] != value[key] for key in value if key != "created_at"):
                raise DataError("Das Paper-Konto wurde bereits angelegt.", 409)
            return original
        set_meta(db, "account", value)
        set_meta(db, "cash", str(capital))
        set_meta(db, "realized", "0")
        record(db, None, now, now, "account_created")
    return value


def as_plan(row):
    if row is None:
        raise DataError("Paper-Plan nicht gefunden.", 404)
    return {**dict(row), "spec": json.loads(row["spec"]), "data": json.loads(row["data"])}


def find(db, identity):
    if not isinstance(identity, str) or not re.fullmatch("[a-f0-9]{32}", identity):
        raise DataError("Ungültige Plan-ID.", 400)
    return as_plan(db.execute("SELECT * FROM plans WHERE id=?", (identity,)).fetchone())


def save(db, plan, now):
    db.execute("UPDATE plans SET state=?,activated=?,updated=?,data=? WHERE id=?",
               (plan["state"], plan["activated"], now, encode(plan["data"]), plan["id"]))
    plan["updated"] = now


def record(db, plan, at, now, kind, payload=None, *, source_at=None, symbol=None):
    identity = plan["id"] if plan else None
    symbol = plan["symbol"] if plan else symbol
    payload = payload or {}
    key = hashlib.sha256(encode((identity, symbol, at, kind, payload)).encode()).hexdigest()
    db.execute("""INSERT OR IGNORE INTO events(event_id,plan_id,symbol,at,recorded,kind,payload,source_at)
                  VALUES (?,?,?,?,?,?,?,?)""", (key, identity, symbol, at, now, kind, encode(payload), source_at))


def write_key(raw):
    key = raw.get("request_id")
    if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,100}", key):
        raise DataError("Ein stabiler request_id ist erforderlich.", 400)
    return key


def draft(raw, now=None):
    raw = require_object(raw)
    now = int(time.time()) if now is None else now
    key = write_key(raw)
    if set(raw) != {"request_id", "setup"}:
        raise DataError("request_id und setup erwartet.", 400)
    identity = uuid.uuid5(uuid.NAMESPACE_URL, "tori-paper:" + key).hex
    with connection(write=True) as db:
        account(db)
        old = db.execute("SELECT * FROM plans WHERE id=?", (identity,)).fetchone()
        if old:
            prior = as_plan(old)
            if normalize_plan(raw["setup"], prior["created"]) != prior["spec"]:
                raise DataError("request_id wurde mit anderen Plandaten verwendet.", 409)
            return prior
        plan = normalize_plan(raw["setup"], now)
        db.execute("INSERT INTO plans VALUES (?,?,?,?,?,?,?,?)",
                   (identity, plan["symbol"], encode(plan), "draft", now, None, now, "{}"))
        result = find(db, identity)
        record(db, result, now, now, "draft_created", {"spec": plan})
        return result


def rows_at(db, ticker, start, end):
    return [Minute.parse(row["at"], json.loads(row["payload"])) for row in db.execute(
        "SELECT at,payload FROM bars WHERE symbol=? AND at>=? AND at<? ORDER BY at", (ticker, start, end))]


def strategy_bar(db, ticker, pair):
    return aggregate(rows_at(db, ticker, *pair), *pair)


def preview(db, plan, now):
    spec = plan["spec"]
    next_at = market_minute(now)
    reference = previous_bucket(next_at, spec["timeframe"])
    bars = strategy_bar(db, plan["symbol"], reference)
    sample = get_meta(db, "preview:" + plan["id"])
    reference_close = bars.close if bars else None
    if not bars and sample and sample["rows"]:
        sampled = next((row for row in sample["rows"]
                        if row["at"] == sample["reference"] and row["ohlc"]), None)
        if sampled:
            reference = sampled["at"], sampled["end"]
            reference_close = Decimal(sampled["ohlc"][-1])
    return {"plan": plan, "account": account(db), "reference_at": reference[1],
            "reference_close": str(reference_close) if reference_close is not None else None,
            "above_action": reference_close > line_close(spec, "action", reference[0])
            if reference_close is not None else None,
            "action_price": str(line_close(spec, "action", reference[0])),
            "safety_price": str(line_close(spec, "safety", reference[0])),
            "sample": sample, "confirmation": confirmation(plan, account(db))}


def confirmation(plan, config):
    return hashlib.sha256(encode((plan["id"], plan["spec"], config)).encode()).hexdigest()


def plan_preview(identity, now=None):
    now = int(time.time()) if now is None else now
    with connection() as db:
        if db is None:
            raise DataError("Paper-Plan nicht gefunden.", 404)
        return preview(db, find(db, identity), now)


def command(identity, action, raw, now=None):
    raw = require_object(raw)
    now = int(time.time()) if now is None else now
    if set(raw) - {"request_id", "confirmation", "expected_updated"}:
        raise DataError("Unbekanntes Befehlsfeld.", 400)
    key = "command:" + write_key(raw)
    signature = [identity, action, raw]
    with connection(write=True) as db:
        config = account(db)
        prior = get_meta(db, key)
        if prior:
            if prior != signature:
                raise DataError("request_id gehört zu einem anderen Befehl.", 409)
            return find(db, identity)
        plan = find(db, identity)
        spec, data = plan["spec"], plan["data"]
        if type(raw.get("expected_updated")) is not int or raw["expected_updated"] != plan["updated"]:
            raise DataError("Der Plan hat sich geändert. Ansicht bitte neu laden.", 409)
        if action == "prepare" and plan["state"] == "draft":
            data["preview_requested"] = now
        elif action == "activate":
            if plan["state"] != "draft":
                raise DataError(CHANGES, 409)
            if raw.get("confirmation") != confirmation(plan, config):
                raise DataError("Bestätige die angezeigte Plan- und Kontovorschau.", 409)
            if max(now, spec["effective_from"] or now) >= spec["expires_at"]:
                raise DataError("Der Plan ist abgelaufen.", 409)
            active_plans = relevant_plans(db)
            active = {item["symbol"] for item in active_plans}
            if len(active | {plan["symbol"]}) > MAX_SYMBOLS:
                raise DataError(f"Maximal {MAX_SYMBOLS} aktive Symbole.", 409)
            if len(active_plans) >= MAX_ACTIVE_PLANS:
                raise DataError(f"Maximal {MAX_ACTIVE_PLANS} aktive Pläne.", 409)
            plan["activated"] = now
            plan["state"] = "watching"
            data["effective_from"] = max(now, spec["effective_from"] or now)
        elif action == "cancel" and plan["state"] == "draft":
            plan["state"] = "cancelled"
        elif action == "cancel" and plan["state"] in ("watching", "pending") and "cancel_at" not in data:
            data["cancel_at"] = now
        elif action == "abandon" and plan["state"] in ("watching", "pending") and "cancel_at" in data:
            ticker = plan["symbol"]
            if not db.execute("SELECT 1 FROM issues WHERE symbol=? AND resolved IS NULL LIMIT 1", (ticker,)).fetchone():
                raise DataError("Nur ein von einem Datenproblem blockierter Plan kann als unvollständig beendet werden.", 409)
            plan["state"] = "unresolved"
        elif action == "exit" and plan["state"] == "open" and "manual_at" not in data:
            data["manual_at"] = now
        elif action == "acknowledge_revision" and plan["state"] in ACTIVE:
            changed = db.execute("UPDATE issues SET resolved=? WHERE symbol=? AND resolved IS NULL AND kind='revision'",
                                 (now, plan["symbol"])).rowcount
            if not changed:
                raise DataError("Für dieses Symbol liegt keine offene Kursrevision vor.", 409)
        elif action in ("resolve_stop", "resolve_target") and plan["state"] == "ambiguous":
            position = data["position"]
            at = data["ambiguity"]["at"]
            minute = rows_at(db, plan["symbol"], at, at+60)[0]
            side = "stop" if action == "resolve_stop" else "target"
            outcome = ("manual_resolution_" + side, Decimal(position[side]))
            cash = close_position(db, plan, minute, outcome, config, now, Decimal(get_meta(db, "cash")))
            set_meta(db, "cash", str(cash))
            db.execute("UPDATE issues SET resolved=? WHERE symbol=? AND at=? AND kind='ambiguous_stop_target'",
                       (now, plan["symbol"], at))
        else:
            raise DataError("Dieser Befehl ist im aktuellen Planstatus nicht möglich.", 409)
        save(db, plan, now)
        payload = {"request_id": raw["request_id"]}
        if action == "activate":
            payload.update(effective_from=data["effective_from"], plan=spec, account=config)
        record(db, plan, now, now, action, payload)
        set_meta(db, key, signature)
        return plan


def issue(db, ticker, at, kind, detail, now):
    payload = encode(detail)
    row = db.execute("SELECT resolved, detail FROM issues WHERE symbol=? AND at=? AND kind=?",
                     (ticker, at, kind)).fetchone()
    if row is None or row["resolved"] is not None or row["detail"] != payload:
        db.execute("INSERT OR REPLACE INTO issues VALUES (?,?,?,?,NULL)", (ticker, at, kind, payload))
        record(db, None, at, now, "data_issue", {"kind": kind, "detail": detail}, symbol=ticker)


def store_minutes(db, ticker, minutes, now):
    cursor = get_meta(db, "cursor", 0)
    for minute in minutes:
        payload = encode(minute.prices())
        fingerprint = hashlib.sha256(encode(("sip", "raw", ticker, minute.at, minute.prices())).encode()).hexdigest()
        original = db.execute("SELECT fingerprint, payload FROM bars WHERE symbol=? AND at=?",
                              (ticker, minute.at)).fetchone()
        if original and original["fingerprint"] == fingerprint:
            continue
        if original and minute.at < cursor:
            acknowledged = db.execute("SELECT detail, resolved FROM issues WHERE symbol=? AND at=? AND kind='revision'",
                                      (ticker, minute.at)).fetchone()
            if acknowledged and acknowledged["resolved"] is not None and json.loads(acknowledged["detail"])["revision"] == payload:
                continue
            issue(db, ticker, minute.at, "revision", {"original": original["payload"], "revision": payload}, now)
            continue
        db.execute("INSERT INTO bars VALUES (?,?,?,?,?) ON CONFLICT(symbol,at) DO UPDATE SET "
                   "payload=excluded.payload,fingerprint=excluded.fingerprint,received=excluded.received",
                   (ticker, minute.at, payload, fingerprint, now))
        db.execute("UPDATE issues SET resolved=? WHERE symbol=? AND at=? AND kind='missing_or_no_trade' AND resolved IS NULL",
                   (now, ticker, minute.at))
        if original:
            record(db, None, minute.at, now, "unprocessed_bar_revised",
                   {"from": original["payload"], "to": payload}, symbol=ticker)


def relevant_plans(db):
    return [as_plan(row) for row in db.execute(
        "SELECT * FROM plans WHERE state IN ('watching','pending','open','ambiguous') ORDER BY activated,id")]


def first_minute(plan):
    # A bar that began immediately before activation can close afterwards.
    return market_minute(plan["data"]["effective_from"] // 60 * 60)


def signal_allowed(plan, close, pair):
    data, spec = plan["data"], plan["spec"]
    validity = min(spec["expires_at"], data.get("cancel_at", spec["expires_at"]))
    return (plan["state"] == "watching" and close == pair[1]
            and data["effective_from"] < close < validity)


def close_position(db, plan, minute, outcome, config, now, cash):
    trade = settle(plan["data"]["position"], minute, outcome, config)
    plan["data"]["exit"] = trade
    plan["state"] = "closed"
    save(db, plan, now)
    record(db, plan, minute.at, now, "exit", {**trade, "entry": plan["data"]["position"]}, source_at=minute.at)
    set_meta(db, "realized", str(Decimal(get_meta(db, "realized")) + Decimal(trade["pnl"])))
    return cash + Decimal(trade["net_proceeds"])


def mark_open(plans):
    return sum((Decimal(p["data"]["position"]["mark"]) * p["data"]["position"]["quantity"]
                for p in plans if p["state"] in ("open", "ambiguous")), Decimal(0))


def record_mark(db, plan, position, at, now):
    age = position["sessions"]
    if age in plan["spec"]["horizons"]:
        pnl = Decimal(position["mark"]) * position["quantity"] - Decimal(position["entry_cost"])
        mark = {"at": at, "kind": "book_pnl", "pnl": str(pnl)}
        plan["data"].setdefault("horizon_marks", {})[str(age)] = mark
        record(db, plan, at, now, "horizon_mark", {"sessions": age, **mark}, source_at=at-60)


def process_minute(db, plans, minutes, at, config, now):
    cash = Decimal(get_meta(db, "cash"))
    for plan in plans:
        if plan["state"] != "open":
            continue
        minute, data = minutes[plan["symbol"]], plan["data"]
        pending = data.get("close_reason")
        if pending is None and "manual_at" in data and at >= market_minute(data["manual_at"] + 1):
            pending = "manual_exit"
        position = data["position"]
        outcome = exit_at_open(plan["spec"], position, minute, pending)
        if outcome:
            cash = close_position(db, plan, minute, outcome, config, now, cash)
        else:
            position.update(mark=str(minute.open), mark_at=at)
    pending_plans = sorted((p for p in plans if p["state"] == "pending"),
                           key=lambda p: (p["spec"]["priority"], p["activated"], p["id"]))
    for plan in pending_plans:
        data = plan["data"]
        minute = minutes[plan["symbol"]]
        open_plans = [p for p in plans if p["state"] == "open"]
        position = None
        if len(open_plans) >= MAX_POSITIONS or any(p["symbol"] == plan["symbol"] for p in open_plans):
            reason = "position_limit"
        else:
            position, reason = entry(plan["spec"], minute, config, cash, cash + mark_open(open_plans))
        if position is None:
            plan["state"] = "rejected"
            record(db, plan, at, now, "entry_rejected", {"reason": reason}, source_at=at)
        else:
            data["position"] = position
            if "cancel_at" in data:
                record(db, plan, at, now, "cancel_superseded_by_entry", source_at=at)
            plan["state"] = "open"
            cash -= Decimal(position["entry_cost"])
            record(db, plan, at, now, "entry", position, source_at=at)
        save(db, plan, now)

    for plan in plans:
        spec, data = plan["spec"], plan["data"]
        minute = minutes[plan["symbol"]]
        pair = bucket(at, spec["timeframe"])
        bucket_done = minute.at + 60 == pair[1]
        if plan["state"] == "open":
            position = data["position"]
            outcome = exit_inside_minute(spec, position, minute)
            if outcome and outcome[1] is None:
                plan["state"] = "ambiguous"
                data["ambiguity"] = {"at": at, "reason": outcome[0]}
                issue(db, plan["symbol"], at, "ambiguous_stop_target", {"plan": plan["id"]}, now)
                save(db, plan, now)
                continue
            if outcome:
                cash = close_position(db, plan, minute, outcome, config, now, cash)
                continue
            position.update(mark=str(minute.close), mark_at=at+60)
            if at+60 == bucket(at, "1D")[1]:
                position["sessions"] += 1
                record_mark(db, plan, position, at+60, now)
                if position["sessions"] == spec["time_exit_sessions"]:
                    data["close_reason"] = "time_exit"
            if bucket_done and minute.close < line_close(spec, "safety", pair[0]):
                data["close_reason"] = "safety_close_exit"
            save(db, plan, now)
        elif signal_allowed(plan, at+60, pair):
            safety = line_close(spec, "safety", pair[0])
            if minute.close < safety:
                plan["state"] = "invalidated"
                record(db, plan, at+60, now, "safety_invalidated", source_at=at)
            elif minute.close > safety:
                prev_pair = previous_bucket(pair[0], spec["timeframe"])
                prev = strategy_bar(db, plan["symbol"], prev_pair)
                current = strategy_bar(db, plan["symbol"], pair)
                if prev is None or current is None:
                    raise DataError("Unvollständiger Strategievorlauf.", 409)
                if crossed(spec, prev, current):
                    plan["state"] = "pending"
                    data["signal_at"] = at+60
                    record(db, plan, at+60, now, "signal", {"close": str(minute.close),
                           "action": str(line_close(spec, "action", pair[0])), "safety": str(safety),
                           "scheduled_at": market_minute(at+60)}, source_at=at)
            save(db, plan, now)
    set_meta(db, "cash", str(cash))


def advance(db, cutoff, now, limit=390):
    config = account(db)
    cursor = get_meta(db, "cursor")
    for _ in range(limit):
        plans = relevant_plans(db)
        if not plans:
            break
        if any(p["state"] == "ambiguous" for p in plans):
            break
        at = market_minute(max(cursor or 0, min(first_minute(p) for p in plans)))
        eligible = []
        ended = False
        for plan in plans:
            end = plan["spec"]["expires_at"]
            cancel = plan["data"].get("cancel_at")
            if cancel is not None:
                end = min(end, cancel)
            if plan["state"] in ("watching", "pending") and end <= min(at, cutoff):
                plan["state"] = "cancelled" if end == cancel else "expired"
                save(db, plan, now)
                record(db, plan, end, now, plan["state"])
                ended = True
            elif first_minute(plan) <= at:
                eligible.append(plan)
        if at+60 > cutoff:
            break
        if not eligible and ended:
            continue
        symbols = sorted({plan["symbol"] for plan in eligible})
        if any(blocking_issue(db, plan, at) for plan in eligible):
            break
        minutes = {}
        for ticker in symbols:
            rows = rows_at(db, ticker, at, at+60)
            if rows:
                minutes[ticker] = rows[0]
            else:
                issue(db, ticker, at, "missing_or_no_trade", {}, now)
        if len(minutes) != len(symbols):
            break
        blocked = False
        for plan in eligible:
            spec = plan["spec"]
            pair = bucket(at, spec["timeframe"])
            if not signal_allowed(plan, at+60, pair):
                continue
            for start, end in (previous_bucket(pair[0], spec["timeframe"]), pair):
                present = {row[0] for row in db.execute(
                    "SELECT at FROM bars WHERE symbol=? AND at>=? AND at<?", (plan["symbol"], start, end))}
                missing = next((t for t in range(start, end, 60) if t not in present), None)
                if missing is not None:
                    issue(db, plan["symbol"], missing, "missing_or_no_trade", {"required_by": at}, now)
                    blocked = True
        if blocked:
            break
        process_minute(db, eligible, minutes, at, config, now)
        cursor = at+60
        set_meta(db, "cursor", cursor)
    return cursor


def status():
    with connection() as db:
        if db is None or not get_meta(db, "account"):
            return {"account": None, "model": MODEL, "plans": [], "issues": [], "worker": {}}
        config = account(db)
        open_plans = relevant_plans(db)
        value = mark_open(open_plans)
        cash = Decimal(get_meta(db, "cash"))
        realized = Decimal(get_meta(db, "realized"))
        open_cost = sum((Decimal(plan["data"]["position"]["entry_cost"]) for plan in open_plans
                         if plan["state"] in ("open", "ambiguous")), Decimal(0))
        issues = [{**dict(row), "kind": row["kind"].split(":")[0]}
                  for row in db.execute("SELECT * FROM issues WHERE resolved IS NULL ORDER BY at DESC LIMIT 100")]
        plans = [as_plan(row) for row in db.execute(
            "SELECT * FROM plans ORDER BY CASE WHEN state IN ('watching','pending','open','ambiguous') THEN 0 ELSE 1 END, "
            "created DESC,id LIMIT 200")]
        worker = get_meta(db, "worker", {})
        worker["heartbeat_stale"] = not worker or time.time() - worker.get("heartbeat", 0) > 180
        cursor = get_meta(db, "cursor")
        pnl = value - open_cost
        for plan in plans:
            if plan["state"] in ACTIVE:
                at = market_minute(max(cursor or 0, first_minute(plan)))
                plan["next_check_at"] = bucket(at, plan["spec"]["timeframe"])[1]
                if plan["state"] == "pending":
                    plan["next_entry_at"] = market_minute(plan["data"]["signal_at"])
        affected = any(blocking_issue(db, plan, 2**63-1) for plan in open_plans)
        return {"account": config, "model": MODEL, "cash": str(cash), "realized_pnl": str(realized),
                "market_value": str(value), "open_pnl": str(pnl), "equity": str(cash+value), "cursor": cursor,
                "valuation_complete": not open_plans or (not affected
                    and worker.get("phase") not in ("error", "catching_up", "attention")
                    and not worker["heartbeat_stale"]),
                "plans": plans, "issues": issues, "worker": worker}


def events(after=0, through=None, limit=100):
    integer(after, "Cursor", 0, 2**63-1)
    integer(limit, "Seitenlänge", 1, 500)
    if through is not None:
        integer(through, "Obergrenze", after, 2**63-1)
    with connection() as db:
        rows = []
        if db is None:
            return {"model": MODEL, "through": through or 0, "next": after, "items": rows}
        upper = db.execute("SELECT COALESCE(MAX(seq),0) FROM events").fetchone()[0]
        through = upper if through is None else min(through, upper)
        for row in db.execute("SELECT * FROM events WHERE seq>? AND seq<=? ORDER BY seq LIMIT ?",
                              (after, through, limit)):
            rows.append({**dict(row), "payload": json.loads(row["payload"]), "model": MODEL})
        return {"model": MODEL, "items": rows, "through": through, "next": rows[-1]["seq"] if rows else after}
