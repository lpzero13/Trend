"""Causal Watchlist & isolated 1.000-EUR Papertrade tracker for daily Tori setups.

Uses its own SQLite database under TORI_DATA_DIR/paper-watch/watchlist.sqlite3
so existing research databases (jobs.sqlite3) are never modified or migrated.
All signal evaluation and 5m execution reuse the canonical Master fan engine,
signal_path_index (CaseExecution / PathIndex / execute_unbounded) and
exit_followup (r2_fan / qualified_fan) with zero invented candles.
"""
from bisect import bisect_right
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sqlite3
import uuid

from duckdb import Error as ParquetError

from daily_archive import inventory as archive_inventory, trading_day
from datasets import path_for, read_dataset
from exit_followup import policy_timeline
from fan_geometry import profile, stable_id
from fan_observer import WatchRules, price_at
from fan_study import source_gaps
from hermes_scanner import stop_price
from lab_data import session_bounds
from lab_splits import sessions_between
from models import Bar, DataError
from parquet_store import block_path, checksum, connect as duck_connect
from pilot_backtest import PilotObserver
from settings import data_dir
from signal_path_index import CaseExecution, PathIndex, execute_unbounded, isolated_entry

VERSION = "tori-paper-watch-1"
DB_REL = Path("paper-watch") / "watchlist.sqlite3"
DEFAULT_CAPITAL_EUR = 1000.0
DEFAULT_STOP_POLICY = "r2_fan"
VALID_POLICIES = ("r2_fan", "qualified_fan", "original_safety")
ACTIVE_STATUSES = ("watching", "pending_entry", "open")
TRIGGERED_SCENARIOS = ("1A_CLEAN_BREAKOUT", "4A_RETEST_TRIGGER")


def _utc_now():
    return datetime.now(timezone.utc).isoformat()


def _db_path(root=None):
    base = Path(root) if root else data_dir()
    path = base / DB_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def db_conn(root=None):
    path = _db_path(root)
    conn = sqlite3.connect(str(path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS watchlist_items (
            id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            dataset_id TEXT NOT NULL,
            added_at TEXT NOT NULL,
            source_session TEXT NOT NULL,
            source_cutoff INTEGER NOT NULL,
            source_scenario TEXT NOT NULL,
            score INTEGER NOT NULL,
            strategy_tag TEXT NOT NULL,
            capital_eur REAL NOT NULL,
            stop_policy TEXT NOT NULL,
            max_watch_sessions INTEGER NOT NULL,
            status TEXT NOT NULL,
            status_reason TEXT,
            note TEXT NOT NULL DEFAULT '',
            geometry_json TEXT NOT NULL,
            trade_json TEXT NOT NULL DEFAULT '{}',
            last_evaluated_at TEXT,
            last_session TEXT,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS watch_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            evaluated_at TEXT NOT NULL,
            session TEXT NOT NULL,
            status TEXT NOT NULL,
            event_type TEXT NOT NULL,
            close_price REAL,
            stop_price REAL,
            pnl_eur REAL,
            pnl_pct REAL,
            r_multiple REAL,
            summary TEXT NOT NULL,
            FOREIGN KEY (item_id) REFERENCES watchlist_items(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_watch_updates_item ON watch_updates(item_id, id DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_watchlist_status ON watchlist_items(status, symbol)")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _row_to_item(row):
    d = dict(row)
    d["geometry"] = json.loads(d.pop("geometry_json"))
    d["trade"] = json.loads(d.pop("trade_json") or "{}")
    return d


def load_latest_scan(root=None):
    base = Path(root) if root else data_dir()
    path = base / "paper-watch" / "latest-scan.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text("utf-8"))
    except (OSError, ValueError):
        return None


def add_candidate(
    candidate,
    *,
    capital_eur=DEFAULT_CAPITAL_EUR,
    stop_policy=DEFAULT_STOP_POLICY,
    max_watch_sessions=20,
    note="",
    root=None,
):
    """Add a scanner candidate to the Watchlist with its own isolated capital (default 1.000 EUR)."""
    if stop_policy not in VALID_POLICIES:
        raise DataError(f"Ungültiges Stop-Modell: {stop_policy}. Erlaubt: {', '.join(VALID_POLICIES)}", 400)
    if not isinstance(capital_eur, (int, float)) or not math.isfinite(capital_eur) or capital_eur < 50:
        raise DataError("Kapital pro Aktie muss mindestens 50 EUR betragen.", 400)
    if type(max_watch_sessions) is not int or not 1 <= max_watch_sessions <= 90:
        raise DataError("Beobachtungsdauer: 1 bis 90 Handelstage.", 400)

    sym = str(candidate["symbol"]).upper().strip()
    source_session = str(candidate["session"])
    cutoff = int(candidate["cutoff"])
    dataset_id = str(candidate["dataset_id"])
    geometry = candidate.get("geometry")
    if not geometry or not geometry.get("red") or not geometry.get("green"):
        raise DataError("Kandidat enthält keine vollständige Original-Geometrie.", 400)

    now_iso = _utc_now()
    with db_conn(root) as conn:
        existing = conn.execute(
            "SELECT * FROM watchlist_items WHERE symbol=? AND status IN ('watching','pending_entry','open')",
            (sym,),
        ).fetchone()
        if existing is not None:
            return {"created": False, "reason": "already_active", "item": _row_to_item(existing)}

        item_id = uuid.uuid4().hex[:16]
        init_trade = {
            "capitalEur": float(capital_eur),
            "currencyNote": "1.000 EUR nominal auf USD-Kursbasis (ohne Live-FX-Umrechnung; inkl. 5 bps Spread + 5 bps Slippage je Seite)",
            "lastClose": candidate.get("close_4h"),
            "triggerNext1": candidate.get("clean_trigger_next1"),
            "initialStopPlanned": candidate.get("stop_0_3_pct"),
            "targetPlus2R": candidate.get("target_plus_2r_price"),
            "chartPath": candidate.get("chart_path"),
        }
        conn.execute(
            """
            INSERT INTO watchlist_items (
                id, symbol, dataset_id, added_at, source_session, source_cutoff,
                source_scenario, score, strategy_tag, capital_eur, stop_policy,
                max_watch_sessions, status, status_reason, note, geometry_json,
                trade_json, last_evaluated_at, last_session, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                item_id, sym, dataset_id, now_iso, source_session, cutoff,
                str(candidate["scenario"]), int(candidate.get("score", 0)),
                str(candidate.get("strategy_tag", "UNKNOWN")),
                float(capital_eur), stop_policy, max_watch_sessions,
                "watching", "added_to_watchlist", str(note or "")[:1000],
                json.dumps(geometry, ensure_ascii=False, allow_nan=False),
                json.dumps(init_trade, ensure_ascii=False, allow_nan=False),
                now_iso, source_session, now_iso,
            ),
        )
        summary = (
            f"Auf Watchlist aufgenommen ({candidate['scenario']}, Score {candidate.get('score', 0)}/10, "
            f"Kapital {capital_eur:.0f} EUR, Stop-Modell {stop_policy})."
        )
        conn.execute(
            """
            INSERT INTO watch_updates (
                item_id, symbol, evaluated_at, session, status, event_type,
                close_price, stop_price, pnl_eur, pnl_pct, r_multiple, summary
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                item_id, sym, now_iso, source_session, "watching", "added",
                candidate.get("close_4h"), candidate.get("stop_0_3_pct"),
                0.0, 0.0, 0.0, summary,
            ),
        )
        row = conn.execute("SELECT * FROM watchlist_items WHERE id=?", (item_id,)).fetchone()
        return {"created": True, "item": _row_to_item(row)}


def update_note(item_id, note, *, root=None):
    now_iso = _utc_now()
    with db_conn(root) as conn:
        cur = conn.execute(
            "UPDATE watchlist_items SET note=?, updated_at=? WHERE id=?",
            (str(note or "")[:1000], now_iso, item_id),
        )
        if cur.rowcount == 0:
            raise DataError("Watchlist-Eintrag nicht gefunden.", 404)
        row = conn.execute("SELECT * FROM watchlist_items WHERE id=?", (item_id,)).fetchone()
        return _row_to_item(row)


def archive_item(item_id, *, root=None):
    now_iso = _utc_now()
    with db_conn(root) as conn:
        row = conn.execute("SELECT * FROM watchlist_items WHERE id=?", (item_id,)).fetchone()
        if row is None:
            raise DataError("Watchlist-Eintrag nicht gefunden.", 404)
        conn.execute(
            "UPDATE watchlist_items SET status='archived', status_reason='user_archived', updated_at=? WHERE id=?",
            (now_iso, item_id),
        )
        conn.execute(
            """
            INSERT INTO watch_updates (
                item_id, symbol, evaluated_at, session, status, event_type, summary
            ) VALUES (?,?,?,?,?,?,?)
            """,
            (item_id, row["symbol"], now_iso, row["last_session"] or row["source_session"],
             "archived", "archived", "Manuell archiviert / aus aktiver Beobachtung entfernt."),
        )
        updated = conn.execute("SELECT * FROM watchlist_items WHERE id=?", (item_id,)).fetchone()
        return _row_to_item(updated)


def delete_item(item_id, *, root=None):
    with db_conn(root) as conn:
        cur = conn.execute("DELETE FROM watchlist_items WHERE id=?", (item_id,))
        if cur.rowcount == 0:
            raise DataError("Watchlist-Eintrag nicht gefunden.", 404)
    return {"deleted": item_id}


def _read_symbol_bars(dataset_id, cutoff, *, source_cutoff=None, root=None):
    """Read immutable 4h (with 450d warmup) and 5m (from source_cutoff-7d) bars <= cutoff."""
    path = path_for(dataset_id) if root is None else Path(root) / "datasets" / f"{dataset_id}.json"
    if not path.is_file():
        raise DataError(f"Dataset {dataset_id} nicht vorhanden.", 404)
    manifest = json.loads(path.read_text("utf-8"))
    storage = manifest.get("storage")
    min_4h = (source_cutoff - 450 * 86400) if source_cutoff else 0
    min_5m = (source_cutoff - 7 * 86400) if source_cutoff else 0
    if storage is None:
        material = manifest["material"]
        return (
            [Bar(**b) for b in material["bars"]["4h"] if min_4h <= b["end"] <= cutoff],
            [Bar(**b) for b in material["bars"]["5m"] if min_5m <= b["end"] <= cutoff],
        )
    if manifest["id"] != dataset_id:
        raise DataError("Kursmanifest passt nicht zur Dataset-ID.", 409)
    month_limit = datetime.fromtimestamp(cutoff, timezone.utc).strftime("%Y-%m")
    min_month = datetime.fromtimestamp(min_4h, timezone.utc).strftime("%Y-%m") if min_4h > 0 else "0000-00"
    ds_root = path.parent.parent
    paths = []
    for entry in storage.get("blocks", []):
        if entry["month"] < min_month or entry["month"] > month_limit:
            continue
        bp = block_path(ds_root, entry["path"])
        if bp.stat().st_size != entry["bytes"] or checksum(bp) != entry["sha256"]:
            raise DataError("Parquet-Prüfsumme ungültig.", 409)
        paths.append(str(bp))
    bars_4h, bars_5m = [], []
    if paths:
        with duck_connect() as db:
            rows = db.execute(
                'SELECT timeframe,"time","end",open,high,low,close,volume FROM read_parquet(?) '
                'WHERE ((timeframe=? AND "end">=? AND "end"<=?) OR (timeframe=? AND "end">=? AND "end"<=?)) '
                'ORDER BY timeframe,"time"',
                [paths, "4h", min_4h, cutoff, "5m", min_5m, cutoff],
            ).fetchall()
        for tf, *bar in rows:
            if tf == "4h":
                bars_4h.append(Bar(*bar))
            else:
                bars_5m.append(Bar(*bar))
    return bars_4h, bars_5m


def _project_line_by_time(line, bars_4h, current_bar_pos):
    """Project a frozen line using exact 4h bar offset from its anchor time."""
    a_time = line["a_time"]
    for pos, b in enumerate(bars_4h):
        if b.time == a_time:
            return line["a_price"] + line["slope"] * (current_bar_pos - pos)
    return None


def _evaluate_path(item, bars_4h, bars_5m, eval_cutoff, dataset_id):
    """Pure causal evaluation of one watchlist/papertrade item up to eval_cutoff."""
    symbol = item["symbol"]
    source_cutoff = int(item["source_cutoff"])
    source_session = item["source_session"]
    scenario = item["source_scenario"]
    geom = item["geometry"]
    watched_red = geom["red"]
    watched_green = geom["green"]
    capital_eur = float(item["capital_eur"])
    stop_policy = item["stop_policy"]
    max_watch = int(item["max_watch_sessions"])

    if not bars_4h or not bars_5m:
        return {
            "status": item["status"],
            "status_reason": "no_bars_available",
            "last_session": item["last_session"] or source_session,
            "trade": {**item["trade"], "datasetId": dataset_id},
            "events": [],
        }

    latest_4h = bars_4h[-1]
    latest_session = trading_day(latest_4h.end)
    rules = profile("master")
    watch_rules = WatchRules(arm_bars=2, retest_bars=16, stop_buffer_pct=0.3)
    gaps_4h = source_gaps(bars_4h, latest_4h.end, "4h")
    observer = PilotObserver(symbol, rules=rules, watch=watch_rules)

    # Run Master observer causally across all 4h bars <= eval_cutoff to produce exact timeline
    timeline = []
    entry_signal = None
    invalidated_reason = None
    watch_sessions_elapsed = 0
    seen_watch_days = set()
    prev_bar = None

    # If candidate was already in a confirmed trigger state at addition, construct causal entry signal at source_cutoff
    if scenario in TRIGGERED_SCENARIOS:
        init_stop = geom.get("stop_0_3_pct") or stop_price(watched_green["value"])
        entry_signal = {
            "id": stable_id([VERSION, item["id"], "direct_trigger", source_cutoff]),
            "symbol": symbol,
            "family": "breakout" if scenario == "1A_CLEAN_BREAKOUT" else "red_retest",
            "signalAt": source_cutoff,
            "signalClose": item["trade"].get("lastClose"),
            "line": deepcopy(watched_red),
            "safety": deepcopy(watched_green),
            "initialStop": init_stop,
            "triggerReason": f"direkter_trigger_{scenario}",
        }

    # Build timeline & watch for post-addition causal entry triggers
    for i, bar in enumerate(bars_4h):
        gap_here = i in gaps_4h
        if gap_here:
            observer.gap(bar)
        events, signals, snap = observer.push(bar)
        if not snap or not snap.get("ready"):
            prev_bar = bar
            continue

        idx = snap["referenceIndex"]
        atr = snap["atr"]
        state_entry = {
            "closedAt": bar.end,
            "index": idx,
            "close": bar.close,
            "green": deepcopy(snap.get("green")),
            "gapAt": bar.time if gap_here else None,
        }
        timeline.append(state_entry)

        if entry_signal is None and invalidated_reason is None and bar.end > source_cutoff:
            bar_day = trading_day(bar.end)
            if bar_day > source_session:
                seen_watch_days.add(bar_day)
                watch_sessions_elapsed = len(seen_watch_days)

            # Check if green safety broke before any entry trigger
            green_proj = _project_line_by_time(watched_green, bars_4h, i)
            cur_green = snap.get("green")
            if green_proj is not None and bar.close <= green_proj * 0.997:
                invalidated_reason = "safety_broken_before_entry"
                prev_bar = bar
                continue

            # Check canonical observer entry signals first (breakout / red_retest with valid risk)
            matched_sig = None
            for sig in signals:
                if sig["family"] in ("breakout", "red_retest") and sig.get("validRisk") and sig.get("safety"):
                    stop_val = sig["initialStop"]
                    risk_pct = 100.0 * (bar.close - stop_val) / bar.close
                    risk_atr = (bar.close - stop_val) / atr if atr and atr > 0 else 0.0
                    if risk_pct >= 1.8 and risk_pct <= 9.5 and risk_atr >= 0.8:
                        matched_sig = {
                            "id": sig["id"],
                            "symbol": symbol,
                            "family": sig["family"],
                            "signalAt": bar.end,
                            "signalClose": bar.close,
                            "line": deepcopy(sig["line"]),
                            "safety": deepcopy(sig["safety"]),
                            "initialStop": stop_val,
                            "triggerReason": f"tori_signal_{sig['family']}",
                        }
                        break

            # Fallback: direct clean breakout or confirmed retest on the frozen watched red line
            if matched_sig is None:
                red_proj = _project_line_by_time(watched_red, bars_4h, i)
                use_green = (
                    cur_green
                    if (cur_green and cur_green["slope"] > 0 and 0 < price_at(cur_green, idx) < bar.close)
                    else (watched_green if (green_proj is not None and 0 < green_proj < bar.close) else None)
                )
                g_val = (
                    price_at(use_green, idx)
                    if (use_green is cur_green and use_green is not None)
                    else green_proj
                )
                stop_val = stop_price(g_val, buffer_pct=0.3, tick=rules.tick) if g_val else None
                if red_proj is not None and use_green is not None and stop_val and 0 < stop_val < bar.close and atr and atr > 0:
                    risk_pct = 100.0 * (bar.close - stop_val) / bar.close
                    risk_atr = (bar.close - stop_val) / atr
                    risk_ok = 1.8 <= risk_pct <= 9.5 and risk_atr >= 1.0
                    if risk_ok:
                        if scenario == "4B_RETEST_APPROACH":
                            prev_low = prev_bar.low if prev_bar else bar.low
                            touched = min(bar.low, prev_low) <= red_proj + 0.30 * atr
                            if touched and bar.close >= red_proj and bar.close > bar.open:
                                matched_sig = {
                                    "id": stable_id([VERSION, item["id"], "watched_retest", bar.end]),
                                    "symbol": symbol,
                                    "family": "red_retest",
                                    "signalAt": bar.end,
                                    "signalClose": bar.close,
                                    "line": deepcopy(watched_red),
                                    "safety": deepcopy(use_green),
                                    "initialStop": stop_val,
                                    "triggerReason": "watched_red_retest_confirmed",
                                }
                        else:
                            clean_thresh = red_proj + 0.15 * atr
                            if bar.close >= clean_thresh:
                                matched_sig = {
                                    "id": stable_id([VERSION, item["id"], "watched_breakout", bar.end]),
                                    "symbol": symbol,
                                    "family": "breakout",
                                    "signalAt": bar.end,
                                    "signalClose": bar.close,
                                    "line": deepcopy(watched_red),
                                    "safety": deepcopy(use_green),
                                    "initialStop": stop_val,
                                    "triggerReason": "watched_red_clean_breakout",
                                }

            if matched_sig is not None:
                entry_signal = matched_sig
            elif watch_sessions_elapsed >= max_watch:
                invalidated_reason = "watch_window_expired"
        prev_bar = bar

    # Still watching or expired without entry
    if entry_signal is None:
        red_now = _project_line_by_time(watched_red, bars_4h, len(bars_4h) - 1)
        green_now = _project_line_by_time(watched_green, bars_4h, len(bars_4h) - 1)
        last_atr = observer.snapshot["atr"] if observer.snapshot and observer.snapshot.get("ready") else geom.get("atr_4h")
        trig_now = (red_now + 0.15 * last_atr) if (red_now and last_atr) else None
        status = "expired" if invalidated_reason else "watching"
        reason = invalidated_reason or "waiting_for_tori_trigger"
        trade_info = {
            **item["trade"],
            "datasetId": dataset_id,
            "lastClose": round(latest_4h.close, 4),
            "lastCloseAt": latest_4h.end,
            "lastSession": latest_session,
            "watchSessionsElapsed": watch_sessions_elapsed,
            "redProjected": round(red_now, 4) if red_now else None,
            "greenProjected": round(green_now, 4) if green_now else None,
            "triggerProjected": round(trig_now, 4) if trig_now else None,
            "distToTriggerPct": round(100.0 * (trig_now - latest_4h.close) / latest_4h.close, 2) if trig_now else None,
            "stopCurrent": stop_price(green_now) if green_now else item["trade"].get("initialStopPlanned"),
            "pnlEur": 0.0,
            "pnlPct": 0.0,
            "rMultiple": 0.0,
        }
        return {
            "status": status,
            "status_reason": reason,
            "last_session": latest_session,
            "trade": trade_info,
        }

    # --- Entry signal exists! Execute isolated 1.000-EUR papertrade on real 5m bars ---
    exec_rules = CaseExecution(
        notional=capital_eur,
        latency_seconds=300,
        spread_bps=5.0,
        slippage_bps=5.0,
        fee_per_order=0.0,
        buffer_pct=0.3,
        tick=0.01,
    )
    # Build PathIndex covering from signal time through eval_cutoff
    fine_window = [b for b in bars_5m if b.time >= entry_signal["signalAt"] - 86400 and b.end <= eval_cutoff]
    if not fine_window:
        return {
            "status": "pending_entry",
            "status_reason": "awaiting_next_session_open",
            "last_session": latest_session,
            "trade": {
                **item["trade"],
                "datasetId": dataset_id,
                "signalAt": entry_signal["signalAt"],
                "signalSession": trading_day(entry_signal["signalAt"]),
                "triggerReason": entry_signal["triggerReason"],
                "initialStop": entry_signal["initialStop"],
                "lastClose": round(latest_4h.close, 4),
                "pnlEur": 0.0,
                "pnlPct": 0.0,
                "rMultiple": 0.0,
            },
        }

    path_idx = PathIndex(fine_window, eval_cutoff, start=entry_signal["signalAt"])
    entry = isolated_entry(entry_signal, path_idx, exec_rules)

    if entry["status"] == "pending":
        return {
            "status": "pending_entry",
            "status_reason": "entry_next_open_pending",
            "last_session": latest_session,
            "trade": {
                **item["trade"],
                "datasetId": dataset_id,
                "signalAt": entry_signal["signalAt"],
                "signalSession": trading_day(entry_signal["signalAt"]),
                "triggerReason": entry_signal["triggerReason"],
                "plannedEntryAt": entry["entryAt"],
                "initialStop": entry_signal["initialStop"],
                "lastClose": round(latest_4h.close, 4),
                "pnlEur": 0.0,
                "pnlPct": 0.0,
                "rMultiple": 0.0,
            },
        }
    if entry["status"] in ("cancelled", "rejected"):
        return {
            "status": "cancelled",
            "status_reason": entry.get("reason") or entry["status"],
            "last_session": latest_session,
            "trade": {
                **item["trade"],
                "datasetId": dataset_id,
                "signalAt": entry_signal["signalAt"],
                "triggerReason": entry_signal["triggerReason"],
                "entryAt": entry.get("entryAt"),
                "entryPrice": entry.get("entryPrice"),
                "initialStop": entry.get("initialStop"),
                "lastClose": round(latest_4h.close, 4),
                "pnlEur": 0.0,
                "pnlPct": 0.0,
                "rMultiple": 0.0,
            },
        }
    if entry["status"] != "filled":
        return {
            "status": "censored",
            "status_reason": entry.get("reason") or "missing_expected_entry_open",
            "last_session": latest_session,
            "trade": {
                **item["trade"],
                "datasetId": dataset_id,
                "signalAt": entry_signal["signalAt"],
                "triggerReason": entry_signal["triggerReason"],
                "lastClose": round(latest_4h.close, 4),
                "pnlEur": None,
                "pnlPct": None,
                "rMultiple": None,
            },
        }

    # Align frozen safety line anchor index to timeline index space for policy projection
    sig_for_exec = deepcopy(entry_signal)
    if sig_for_exec.get("safety"):
        safety_a_time = sig_for_exec["safety"]["a_time"]
        # Find exact matching bar index in observer's coordinate system
        for pos, b in enumerate(bars_4h):
            if b.time == safety_a_time:
                sig_for_exec["safety"]["a_index"] = pos
                break

    r2_activated_at = None
    if stop_policy in ("r2_fan", "qualified_fan"):
        case_stub = {"signal": sig_for_exec, "entry": entry}
        proj_timeline, r2_activated_at = policy_timeline(case_stub, timeline, stop_policy)
        path_res = execute_unbounded(sig_for_exec, entry, path_idx, proj_timeline, "fan_safety")
    else:
        path_res = execute_unbounded(sig_for_exec, entry, path_idx, timeline, "original_safety")

    if r2_activated_at is not None and path_res.get("exitAt") is not None and r2_activated_at >= path_res["exitAt"]:
        r2_activated_at = None
    final_status = path_res["status"]  # 'open', 'closed', 'censored'
    if final_status == "closed":
        pnl_eur = round(path_res["netPnl"], 2)
        pnl_pct = round(path_res["netReturnPct"], 2)
        r_mult = round(path_res["netR"], 2)
        mark_price = round(path_res["exitPrice"], 4)
        hold_days = round(path_res["holdingCalendarDays"], 1)
    else:
        pnl_eur = round(path_res["markNetPnl"], 2) if path_res.get("markNetPnl") is not None else None
        pnl_pct = round(path_res["markNetReturnPct"], 2) if path_res.get("markNetReturnPct") is not None else None
        r_mult = (
            round(path_res["markNetPnl"] / entry["plannedRisk"], 2)
            if (path_res.get("markNetPnl") is not None and entry.get("plannedRisk"))
            else None
        )
        mark_price = round(path_res["markPrice"], 4) if path_res.get("markPrice") is not None else round(latest_4h.close, 4)
        hold_days = round(((path_res.get("lastObservedAt") or eval_cutoff) - entry["entryAt"]) / 86400.0, 1)

    trade_info = {
        **item["trade"],
        "datasetId": dataset_id,
        "stopPolicy": stop_policy,
        "signalAt": entry_signal["signalAt"],
        "signalSession": trading_day(entry_signal["signalAt"]),
        "triggerReason": entry_signal["triggerReason"],
        "entryAt": entry["entryAt"],
        "entrySession": trading_day(entry["entryAt"]),
        "entryPrice": round(entry["entryPrice"], 4),
        "entryFill": round(entry["entryFill"], 4),
        "quantity": round(entry["quantity"], 6),
        "capitalEur": capital_eur,
        "plannedRiskEur": round(entry["plannedRisk"], 2),
        "initialStop": round(entry["initialStop"], 2),
        "stopCurrent": round(path_res["finalStop"], 2) if path_res.get("finalStop") else round(entry["initialStop"], 2),
        "r2ActivatedAt": r2_activated_at,
        "r2ActivatedSession": trading_day(r2_activated_at) if r2_activated_at else None,
        "stopEventsCount": len(path_res.get("stopEvents", [])),
        "lastStopEvent": path_res["stopEvents"][-1] if path_res.get("stopEvents") else None,
        "exitAt": path_res.get("exitAt"),
        "exitSession": trading_day(path_res["exitAt"]) if path_res.get("exitAt") else None,
        "exitPrice": round(path_res["exitPrice"], 4) if path_res.get("exitPrice") is not None else None,
        "exitFill": round(path_res["exitFill"], 4) if path_res.get("exitFill") is not None else None,
        "exitReason": path_res.get("reason"),
        "lastClose": mark_price,
        "lastSession": latest_session,
        "pnlEur": pnl_eur,
        "pnlPct": pnl_pct,
        "rMultiple": r_mult,
        "mfeR": round(path_res["mfeR"], 2) if path_res.get("mfeR") is not None else None,
        "maeR": round(path_res["maeR"], 2) if path_res.get("maeR") is not None else None,
        "holdingCalendarDays": hold_days,
        "missingAt": path_res.get("missingAt"),
    }
    return {
        "status": final_status,
        "status_reason": path_res.get("reason") or final_status,
        "last_session": latest_session,
        "trade": trade_info,
    }


def _describe_transition(old_item, new_status, new_trade):
    old_status = old_item["status"]
    old_trade = old_item["trade"]
    sym = old_item["symbol"]
    exit_labels = {"stop": "Hard-Stop ausgelöst", "stop_gap": "Stop-Gap zur Eröffnung"}
    if old_status != new_status:
        if new_status == "pending_entry":
            return "signal_triggered", f"{sym}: Tori-Einstiegssignal ausgelöst! Kauf am nächsten US-Open (Stop {new_trade.get('initialStop')} $)."
        if new_status == "open":
            return (
                "papertrade_opened",
                f"{sym}: Papertrade eröffnet ({new_trade['capitalEur']:.0f} € @ {new_trade.get('entryPrice')} $, "
                f"Start-Stop {new_trade.get('initialStop')} $, aktuell {new_trade.get('pnlEur'):+.2f} € / {new_trade.get('pnlPct'):+.2f} %).",
            )
        if new_status == "closed":
            reason_de = exit_labels.get(new_trade.get("exitReason"), new_trade.get("exitReason"))
            return (
                "papertrade_closed",
                f"{sym}: Papertrade geschlossen ({reason_de}) @ {new_trade.get('exitPrice')} $ -> "
                f"Realisiert {new_trade.get('pnlEur'):+.2f} € ({new_trade.get('pnlPct'):+.2f} %, {new_trade.get('rMultiple'):+.2f} R).",
            )
        if new_status == "expired":
            return "watch_expired", f"{sym}: Beobachtung beendet ohne Einstieg ({new_trade.get('watchSessionsElapsed', 0)} Handelstage)."
        if new_status == "cancelled":
            return "entry_cancelled", f"{sym}: Einstieg abgesagt (Eröffnungskurs unter Stop {new_trade.get('initialStop')} $)."
        if new_status == "censored":
            return "data_gap_censored", f"{sym}: Pfad wegen fehlender 5m-Kerzen ehrlich als Datenlücke markiert."

    # Same status: check milestone updates (R2 activation, stop raise, or new session progress)
    if new_status == "open":
        if new_trade.get("r2ActivatedAt") and not old_trade.get("r2ActivatedAt"):
            return (
                "r2_activated",
                f"{sym}: +2R-Meilenstein erreicht! Nachziehender Stop aktiviert bei {new_trade.get('stopCurrent')} $ "
                f"(Buch-Ergebnis {new_trade.get('pnlEur'):+.2f} € / {new_trade.get('rMultiple'):+.2f} R).",
            )
        old_stop = old_trade.get("stopCurrent")
        new_stop = new_trade.get("stopCurrent")
        if new_stop and old_stop and new_stop > old_stop:
            return (
                "stop_raised",
                f"{sym}: Stop nachgezogen von {old_stop} $ auf {new_stop} $ "
                f"(Kurs {new_trade.get('lastClose')} $, Buch-Ergebnis {new_trade.get('pnlEur'):+.2f} € / {new_trade.get('pnlPct'):+.2f} %).",
            )
        return (
            "daily_update",
            f"{sym}: Tages-Update {new_trade.get('lastSession')} – Kurs {new_trade.get('lastClose')} $, "
            f"Stop {new_trade.get('stopCurrent')} $, Buch-Ergebnis {new_trade.get('pnlEur'):+.2f} € ({new_trade.get('pnlPct'):+.2f} %, {new_trade.get('rMultiple'):+.2f} R).",
        )
    if new_status == "watching":
        return (
            "watch_update",
            f"{sym}: Weiter auf Watchlist ({new_trade.get('lastSession')}) – Kurs {new_trade.get('lastClose')} $, "
            f"Abstand zur Einstiegsschwelle {new_trade.get('distToTriggerPct')} %.",
        )
    return "status_update", f"{sym}: Status {new_status}."


def evaluate_all(*, asof_session=None, root=None, datasets_root=None, include_closed=False):
    """Evaluate all active watchlist & papertrade items against local SIP data and log updates."""
    base = Path(root) if root else data_dir()
    ds_base = Path(datasets_root) if datasets_root else base
    now_iso = _utc_now()
    asof_cutoff = session_bounds(asof_session)[1] if asof_session else None

    with db_conn(base) as conn:
        if include_closed:
            rows = conn.execute("SELECT * FROM watchlist_items WHERE status != 'archived' ORDER BY added_at DESC").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM watchlist_items WHERE status IN ('watching','pending_entry','open') ORDER BY added_at DESC"
            ).fetchall()
        items = [_row_to_item(r) for r in rows]

    if not items:
        return {"evaluated": 0, "newUpdates": [], "summary": portfolio_summary(root=base)}

    symbols = {it["symbol"] for it in items}
    bases = archive_inventory(symbols, ds_base)
    new_updates = []

    with db_conn(base) as conn:
        for item in items:
            sym = item["symbol"]
            inv = bases.get(sym)
            dataset_id = inv["datasetId"] if inv else item["dataset_id"]
            eval_cutoff = asof_cutoff or (inv["lastClose"] if inv else item["source_cutoff"])
            if eval_cutoff < item["source_cutoff"]:
                continue
            try:
                bars_4h, bars_5m = _read_symbol_bars(
                    dataset_id, eval_cutoff, source_cutoff=item["source_cutoff"], root=ds_base
                )
                res = _evaluate_path(item, bars_4h, bars_5m, eval_cutoff, dataset_id)
            except (DataError, ParquetError, OSError, ValueError, KeyError) as exc:
                res = {
                    "status": item["status"],
                    "status_reason": f"eval_error:{exc}",
                    "last_session": item["last_session"] or item["source_session"],
                    "trade": {**item["trade"], "lastError": str(exc)},
                }

            new_status = res["status"]
            new_session = res["last_session"]
            new_trade = res["trade"]
            changed = (
                new_status != item["status"]
                or new_session != item["last_session"]
                or new_trade.get("stopCurrent") != item["trade"].get("stopCurrent")
                or new_trade.get("r2ActivatedAt") != item["trade"].get("r2ActivatedAt")
            )
            conn.execute(
                """
                UPDATE watchlist_items
                SET dataset_id=?, status=?, status_reason=?, trade_json=?,
                    last_evaluated_at=?, last_session=?, updated_at=?
                WHERE id=?
                """,
                (
                    dataset_id, new_status, res["status_reason"],
                    json.dumps(new_trade, ensure_ascii=False, allow_nan=False),
                    now_iso, new_session, now_iso, item["id"],
                ),
            )
            if changed:
                ev_type, summary_txt = _describe_transition(item, new_status, new_trade)
                conn.execute(
                    """
                    INSERT INTO watch_updates (
                        item_id, symbol, evaluated_at, session, status, event_type,
                        close_price, stop_price, pnl_eur, pnl_pct, r_multiple, summary
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        item["id"], sym, now_iso, new_session, new_status, ev_type,
                        new_trade.get("lastClose"), new_trade.get("stopCurrent"),
                        new_trade.get("pnlEur"), new_trade.get("pnlPct"),
                        new_trade.get("rMultiple"), summary_txt,
                    ),
                )
                new_updates.append({
                    "itemId": item["id"],
                    "symbol": sym,
                    "session": new_session,
                    "status": new_status,
                    "eventType": ev_type,
                    "pnlEur": new_trade.get("pnlEur"),
                    "pnlPct": new_trade.get("pnlPct"),
                    "rMultiple": new_trade.get("rMultiple"),
                    "summary": summary_txt,
                })

    return {
        "evaluated": len(items),
        "newUpdates": new_updates,
        "summary": portfolio_summary(root=base),
    }


def list_items(*, include_archived=False, root=None):
    with db_conn(root) as conn:
        if include_archived:
            rows = conn.execute("SELECT * FROM watchlist_items ORDER BY updated_at DESC").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM watchlist_items WHERE status != 'archived' ORDER BY "
                "CASE status WHEN 'open' THEN 0 WHEN 'pending_entry' THEN 1 WHEN 'watching' THEN 2 WHEN 'closed' THEN 3 ELSE 4 END, "
                "updated_at DESC"
            ).fetchall()
    return [_row_to_item(r) for r in rows]


def recent_updates(limit=50, *, item_id=None, root=None):
    with db_conn(root) as conn:
        if item_id:
            rows = conn.execute(
                "SELECT * FROM watch_updates WHERE item_id=? ORDER BY id DESC LIMIT ?",
                (item_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM watch_updates ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [dict(r) for r in rows]


def portfolio_summary(*, root=None):
    items = list_items(include_archived=False, root=root)
    counts = Counter(it["status"] for it in items)
    open_items = [it for it in items if it["status"] == "open"]
    closed_items = [it for it in items if it["status"] == "closed"]

    open_capital = sum(it["capital_eur"] for it in open_items)
    open_pnl = sum(it["trade"].get("pnlEur") or 0.0 for it in open_items)
    realized_capital = sum(it["capital_eur"] for it in closed_items)
    realized_pnl = sum(it["trade"].get("pnlEur") or 0.0 for it in closed_items)
    wins = sum(1 for it in closed_items if (it["trade"].get("pnlEur") or 0.0) > 0)
    r_values = [it["trade"]["rMultiple"] for it in closed_items if it["trade"].get("rMultiple") is not None]

    return {
        "totalItems": len(items),
        "counts": dict(counts),
        "openCapitalEur": round(open_capital, 2),
        "openPnlEur": round(open_pnl, 2),
        "openReturnPct": round(100.0 * open_pnl / open_capital, 2) if open_capital > 0 else 0.0,
        "closedCount": len(closed_items),
        "closedWinRatePct": round(100.0 * wins / len(closed_items), 1) if closed_items else None,
        "realizedCapitalEur": round(realized_capital, 2),
        "realizedPnlEur": round(realized_pnl, 2),
        "avgClosedR": round(sum(r_values) / len(r_values), 2) if r_values else None,
        "totalPnlEur": round(open_pnl + realized_pnl, 2),
        "capitalPerStockDefaultEur": DEFAULT_CAPITAL_EUR,
        "modelNote": "Jede Aktie startet mit separat 1.000 EUR (nominal auf USD-Kursbasis, 5 bps Spread + 5 bps Slippage je Seite, Hard-Stop 0,3 % Puffer, r2_fan-Nachführung).",
    }
