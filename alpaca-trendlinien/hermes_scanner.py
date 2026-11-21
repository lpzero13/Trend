"""Deterministic, strictly causal daily Tori candidate scanner (Hermes / CT118).

Implements docs/hermes_spezifikation_tori_scanner.md on top of the shared
canonical Master fan engine (lag=0, no invented candles, explicit data audit).
No provider calls unless explicitly requested by the CLI wrapper via daily_archive.
"""
from collections import Counter
from copy import deepcopy
import csv
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import time
from urllib.parse import urlencode

from duckdb import Error as ParquetError

from daily_archive import (
    MISSING_BAR_LIMIT,
    available_session,
    inventory as archive_inventory,
    recent_gaps,
)
from datasets import path_for, read_dataset
from entry_screen import Context as DailyContext
from fan_geometry import analyze, profile
from fan_master import violates_master
from fan_observer import FanObserver, WatchRules, price_at
from fan_study import source_gaps
from lab_data import NORMALIZATION, session_bounds
from lab_splits import sessions_between
from models import Bar, DataError, NY
from parquet_store import block_path, checksum, connect
from pilot_backtest import PilotObserver
from settings import data_dir
from universe_catalog import read as read_universe

VERSION = "tori-hermes-scanner-2"
DEFAULT_UNIVERSES = ("dow30", "nasdaq100", "sp500")
SCENARIO_GROUPS = {
    "all": None,
    "breakout": {"1A_CLEAN_BREAKOUT", "1B_ARMED_WAIT_CLEAN"},
    "immediate": {"2_IMMEDIATE_TEST"},
    "approach": {"3_APPROACH_WATCH"},
    "retest": {"4A_RETEST_TRIGGER", "4B_RETEST_APPROACH"},
    "fast_a": {"5_FAST_A_PLUS"},
    "safety_bounce": {"6_SAFETY_BOUNCE"},
}
SCENARIO_ORDER = {
    "1A_CLEAN_BREAKOUT": 0,
    "1B_ARMED_WAIT_CLEAN": 1,
    "4A_RETEST_TRIGGER": 2,
    "2_IMMEDIATE_TEST": 3,
    "4B_RETEST_APPROACH": 4,
    "3_APPROACH_WATCH": 5,
    "5_FAST_A_PLUS": 6,
    "6_SAFETY_BOUNCE": 7,
}
TIER_ORDER = {
    "C": 1,
    "B": 2,
    "4": 3,
    "A": 4,
    "BASIS": 5,
}
TIER_LABELS = {
    "C": "Stufe C · Premium (Direkt + Aktiv + Reife + Ruhig)",
    "B": "Stufe B · Stark (Aktiv + Reife + Ruhig)",
    "4": "Stufe 4 · Ruhige Vola (<1,5% ATR)",
    "A": "Stufe A · 3/3-Kern (Direkt + Aktiv + Reife)",
    "BASIS": "Basis (übrige qualifizierte)",
}


def classify_tier(*, direct_entry, active_approach, high_maturity, low_daily_volatility):
    """Assign empirically ordered quality tier C -> B -> 4 -> A -> BASIS."""
    if direct_entry and active_approach and high_maturity and low_daily_volatility:
        return "C"
    if active_approach and high_maturity and low_daily_volatility:
        return "B"
    if low_daily_volatility:
        return "4"
    if direct_entry and active_approach and high_maturity:
        return "A"
    return "BASIS"
CSV_COLUMNS = [
    "symbol", "universes", "scenario", "score", "strategy_tag",
    "close_4h", "atr_4h", "atr_1d_pct",
    "red_price_now", "red_price_next1", "red_price_next2",
    "clean_trigger_next1", "clean_trigger_next2",
    "dist_to_red_atr", "dist_to_red_pct",
    "green_price_now", "green_price_next1", "stop_0_3_pct",
    "risk_usd", "risk_pct", "risk_atr",
    "target_plus_2r_price", "ref_shares_10k",
    "red_contacts", "red_age_days", "red_contact_span_days", "red_origin",
    "green_contacts", "green_age_days", "green_origin",
    "active_approach", "compression", "clear_sky",
    "daily_close", "daily_sma50", "daily_sma200", "above_sma200", "overhead_roof_r",
    "overhead_roof_near", "fan_chain_warning", "apex_tight_stop",
    "low_daily_volatility", "earnings_days", "break_bars_ago",
    "dataset_id", "session", "chart_path",
]


def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _round(value, digits=4):
    return round(float(value), digits) if _finite(value) else None


def stop_price(green_value, buffer_pct=0.3, tick=0.01):
    if not _finite(green_value) or green_value <= 0:
        return None
    raw = math.floor(green_value * (1.0 - buffer_pct / 100.0) / tick) * tick
    return round(raw, 4) if raw > 0 else None


def read_frames(db, dataset_id, cutoff, month, *, lookback_calendar_days=500):
    """Read immutable causal 4h and 1D candles in [cutoff-lookback .. cutoff] without loading 5m arrays."""
    path = path_for(dataset_id)
    manifest = json.loads(path.read_text("utf-8"))
    storage = manifest.get("storage")
    min_ts = cutoff - lookback_calendar_days * 86400
    min_month = datetime.fromtimestamp(min_ts, timezone.utc).strftime("%Y-%m")
    frames = {"4h": [], "1D": []}
    if storage is None:
        material = read_dataset(dataset_id)["material"]
        return {
            tf: [Bar(**bar) for bar in material["bars"][tf] if min_ts <= bar["end"] <= cutoff]
            for tf in frames
        }
    if manifest["id"] != dataset_id:
        raise DataError("Kursmanifest passt nicht zum Datensatz.", 409)
    root = path.parent.parent
    paths = []
    for entry in storage.get("blocks", []):
        if entry["month"] < min_month or entry["month"] > month:
            continue
        bp = block_path(root, entry["path"])
        if bp.stat().st_size != entry["bytes"] or checksum(bp) != entry["sha256"]:
            raise DataError("Parquet-Prüfsumme ungültig.", 409)
        paths.append(str(bp))
    if paths:
        rows = db.execute(
            'SELECT timeframe,"time","end",open,high,low,close,volume FROM read_parquet(?) '
            'WHERE timeframe IN (?,?) AND "end">=? AND "end"<=? ORDER BY timeframe,"time"',
            [paths, "4h", "1D", min_ts, cutoff],
        ).fetchall()
        for tf, *bar in rows:
            frames[tf].append(Bar(*bar))
    return frames


def load_earnings_map(path, target_session):
    """Optional offline earnings map (JSON dict {SYM: 'YYYY-MM-DD'} or CSV symbol,date)."""
    if not path:
        return {}
    file_path = Path(path)
    if not file_path.is_file():
        raise DataError(f"Earnings-Datei nicht gefunden: {file_path}", 404)
    target_date = datetime.fromisoformat(target_session).date()
    result = {}
    if file_path.suffix.lower() == ".json":
        raw = json.loads(file_path.read_text("utf-8-sig"))
        if isinstance(raw, dict):
            for sym, day_str in raw.items():
                if not day_str:
                    continue
                try:
                    delta = (datetime.fromisoformat(str(day_str)[:10]).date() - target_date).days
                except ValueError:
                    continue
                if 0 <= delta <= 30:
                    result[str(sym).upper()] = delta
    else:
        with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                sym = (row.get("symbol") or row.get("ticker") or "").strip().upper()
                day_str = (row.get("date") or row.get("earnings_date") or "").strip()
                if not sym or not day_str:
                    continue
                try:
                    delta = (datetime.fromisoformat(day_str[:10]).date() - target_date).days
                except ValueError:
                    continue
                if 0 <= delta <= 30:
                    result[sym] = delta
    return result


def _daily_metrics(daily_bars, cutoff):
    """Causal daily metrics using only fully closed regular sessions <= cutoff."""
    closed = [b for b in daily_bars if b.end <= cutoff]
    if not closed:
        return {
            "daily_close": None,
            "daily_sma50": None,
            "daily_sma200": None,
            "above_sma200": None,
            "avg_vol_20": None,
            "avg_dollar_vol_20": None,
            "atr_1d": None,
            "atr_1d_pct": None,
        }
    gaps = source_gaps(closed, closed[-1].end, "1D")
    # Clean SMA200 via canonical entry_screen.Context
    ctx = DailyContext([], closed)
    daily_info = ctx.daily_at(cutoff)
    # Clean SMA50
    sma50 = None
    if len(closed) >= 50:
        begin50 = len(closed) - 50
        if not any(i in gaps for i in range(begin50 + 1, len(closed))):
            sma50 = sum(b.close for b in closed[begin50:]) / 50.0
    # 20-session average volume and dollar volume
    recent20 = closed[-20:]
    avg_vol_20 = sum(b.volume for b in recent20) / len(recent20)
    avg_dollar_vol_20 = sum(b.volume * b.close for b in recent20) / len(recent20)
    # Wilder 14-day ATR on closed daily bars (reset on gaps)
    atr_1d = None
    tr_seed = []
    prev = None
    for i, bar in enumerate(closed):
        if i in gaps:
            atr_1d = None
            tr_seed.clear()
            prev = None
        tr = (
            bar.high - bar.low
            if prev is None
            else max(bar.high - bar.low, abs(bar.high - prev.close), abs(bar.low - prev.close))
        )
        if atr_1d is None:
            tr_seed.append(tr)
            if len(tr_seed) == 14:
                atr_1d = sum(tr_seed) / 14.0
        else:
            atr_1d = (atr_1d * 13.0 + tr) / 14.0
        prev = bar
    daily_close = daily_info.get("dailyClose")
    daily_sma200 = daily_info.get("dailySma200")
    # Causal fallback: allow up to 2 single-day calendar/holiday gaps in the 200-session window
    # so a single exchange closure (e.g. national day of mourning) does not blank SMA200 for 200 days.
    if daily_sma200 is None and len(closed) >= 200:
        begin200 = len(closed) - 200
        window_gaps = sum(1 for i in range(begin200 + 1, len(closed)) if i in gaps)
        if window_gaps <= 2:
            daily_sma200 = sum(b.close for b in closed[begin200:]) / 200.0
            if daily_close is None:
                daily_close = closed[-1].close
    above_sma200 = (
        None
        if not (_finite(daily_close) and _finite(daily_sma200))
        else bool(daily_close >= daily_sma200)
    )
    return {
        "daily_close": daily_close,
        "daily_sma50": sma50,
        "daily_sma200": daily_sma200,
        "above_sma200": above_sma200,
        "avg_vol_20": avg_vol_20,
        "avg_dollar_vol_20": avg_dollar_vol_20,
        "atr_1d": atr_1d,
        "atr_1d_pct": (100.0 * atr_1d / daily_close) if (_finite(atr_1d) and _finite(daily_close) and daily_close > 0) else None,
    }


def _daily_red_resistance(daily_bars, cutoff, symbol):
    """Causal 1D Master red resistance price at cutoff for overhead-roof check."""
    closed = [b for b in daily_bars if b.end <= cutoff]
    if len(closed) < 20:
        return None
    gaps = source_gaps(closed, closed[-1].end, "1D")
    try:
        lane = analyze(closed, "1D", symbol=symbol, rules=profile("master"), gaps=gaps)
    except DataError:
        return None
    values = [
        line["value"]
        for line in lane.get("reds", [])
        if line.get("valid") and _finite(line.get("value")) and line["value"] > closed[-1].close
    ]
    return min(values) if values else None


def _contact_span_days(line):
    pts = line.get("contactPoints") or []
    if len(pts) < 2:
        return 0.0
    return max(0.0, (pts[-1]["time"] - pts[0]["time"]) / 86400.0)


def _line_age_days(line, at_end):
    return max(0.0, (at_end - line["a_time"]) / 86400.0)


def _has_body_violation(line, rows_with_atr, current_index, rules, *, upper_exclude_tail=2):
    """Gate 3: exact body_atr=0.05 violation check using each bar's historical ATR."""
    a_index = line["a_index"]
    limit = current_index - upper_exclude_tail if line["upper"] else current_index
    for idx, bar, atr in rows_with_atr:
        if idx <= a_index + rules.pivot_side or idx > limit:
            continue
        if not _finite(atr):
            continue
        level = price_at(line, idx)
        tol = rules.body_atr * atr + 1e-9
        if line["upper"]:
            if max(bar.open, bar.close) > level + tol:
                return True
        else:
            if min(bar.open, bar.close) < level - tol:
                return True
    return False


def _fan_chain_warning(line, all_lines):
    """Gate 3: flag if level > 1 pivot line does not start at level-1 endpoint."""
    if line.get("level", 1) <= 1 or line.get("origin") != "pivot":
        return False
    parent = next((ln for ln in all_lines if ln.get("level") == line["level"] - 1), None)
    if parent is None:
        return False
    return line["a_time"] != parent["b_time"]


def _check_green_gate(green, close, at_end, rows_with_atr, current_index, rules):
    """Gate 2 + Gate 3 (lower side): rising >=2 contacts (no both_qualified gate!)."""
    if not green or not green.get("valid"):
        return False
    level = price_at(green, current_index)
    if not (0 < level < close):
        return False
    contacts = green.get("contacts", 0)
    slope = green.get("slope", 0.0)
    age = _line_age_days(green, at_end)
    if slope > 0:
        if contacts < 2:
            return False
    elif abs(slope) <= 1e-12:
        if contacts < 3 or age < 14.0:
            return False
    else:
        return False
    if _has_body_violation(green, rows_with_atr, current_index, rules, upper_exclude_tail=0):
        return False
    return True


def _check_convergence(red, green, eval_index):
    """Gate 4: red falls, green rises, positive width that has narrowed since common start."""
    if not (red and green and red["slope"] < 0 and green["slope"] > 0):
        return False, None, None
    start = max(red["a_index"], green["a_index"])
    width_now = price_at(red, eval_index) - price_at(green, eval_index)
    width_start = price_at(red, start) - price_at(green, start)
    if eval_index <= start or width_now <= 0 or width_start <= 0:
        return False, None, None
    ratio = width_now / width_start
    return ratio < 1.0, ratio, width_now


def _active_approach(red, bars_tail, current_index, atr):
    """Spec section 4 & 6: close_t > close_{t-3} and >=50% of distance reduction from price rise."""
    if len(bars_tail) < 4 or not _finite(atr) or atr <= 0:
        return False
    past_idx, past_bar = bars_tail[-4]
    curr_idx, curr_bar = bars_tail[-1]
    if curr_bar.close <= past_bar.close:
        return False
    dist_past = price_at(red, past_idx) - past_bar.close
    dist_curr = price_at(red, curr_idx) - curr_bar.close
    reduction = dist_past - dist_curr
    if reduction <= 0:
        return False
    price_gain = curr_bar.close - past_bar.close
    return price_gain >= 0.5 * reduction


def _overhead_roof(red, reds, daily_red_val, current_index, trigger, unit_risk):
    """Spec section 5.4 & 6: nearest outer 4h red or 1D red above current red/trigger."""
    if not _finite(unit_risk) or unit_risk <= 0:
        return None, False, True
    candidates = []
    red_now = price_at(red, current_index)
    for other in reds:
        if other["id"] == red["id"]:
            continue
        val = price_at(other, current_index)
        if val > max(red_now, trigger):
            candidates.append(val)
    if _finite(daily_red_val) and daily_red_val > max(red_now, trigger):
        candidates.append(daily_red_val)
    if not candidates:
        return None, False, True
    nearest = min(candidates)
    roof_r = (nearest - trigger) / unit_risk
    return roof_r, roof_r < 1.5, roof_r >= 2.5


def _compute_score(
    *,
    active_approach,
    compression_ratio,
    width_atr,
    red_age_days,
    red_contacts,
    red_origin,
    risk_pct,
    risk_atr,
    universes,
    atr_1d_pct,
    clear_sky,
    direct_entry=False,
):
    """Empirically validated 10-point scoring (PIT 2017-2026 train/val/holdout).

    3/3-split confirmed drivers carry primary weight (active_approach +2, high maturity +2,
    direct_entry +1, low daily volatility <1.5% ATR +1 instead of old -1 penalty).
    """
    score = 0
    if active_approach:
        score += 2
    if red_age_days >= 21.0 or red_contacts >= 4:
        score += 2
    compressed_strong = (
        (_finite(compression_ratio) and compression_ratio <= 0.45)
        or (_finite(width_atr) and width_atr <= 2.2)
    )
    if compressed_strong:
        score += 1
    if direct_entry:
        score += 1
    if red_origin == "pivot":
        score += 1
    if _finite(risk_pct) and _finite(risk_atr) and 2.0 <= risk_pct <= 6.0 and risk_atr >= 1.0:
        score += 1
    low_vol = _finite(atr_1d_pct) and atr_1d_pct < 1.5
    if low_vol:
        score += 1
    if clear_sky:
        score += 1
    return min(10, score), compressed_strong, low_vol


def evaluate_symbol(
    symbol,
    bars_4h,
    bars_1d,
    *,
    target_session,
    cutoff,
    dataset_id,
    universes,
    earnings_days=None,
    include_safety_bounce=False,
):
    """Strictly causal evaluation of one symbol at cutoff (end of target_session).

    Returns (candidates_list, status_reason, debug_info).
    """
    opened, _ = session_bounds(target_session)
    rows_4h = [b for b in bars_4h if b.end <= cutoff]
    if not rows_4h or rows_4h[-1].end <= opened:
        return [], "missing_session_4h", {}
    if (rows_4h[-1].end - rows_4h[0].time) < 320 * 86400:
        return [], "analysis_unavailable", {"reason": "warmup_lt_320d"}

    daily_stats = _daily_metrics(bars_1d, cutoff)
    close_4h = rows_4h[-1].close
    # Gate 6 (liquidity & minimum price)
    if close_4h < 20.0:
        return [], "filtered_gate6_price", {}
    avg_vol = daily_stats["avg_vol_20"] or 0.0
    avg_dvol = daily_stats["avg_dollar_vol_20"] or 0.0
    if avg_vol < 1_000_000 and avg_dvol < 40_000_000:
        return [], "filtered_gate6_liquidity", {}

    rules = profile("master")
    watch = WatchRules(arm_bars=2, retest_bars=16, stop_buffer_pct=0.3)
    gaps_4h = source_gaps(rows_4h, rows_4h[-1].end, "4h")
    observer = PilotObserver(symbol, rules=rules, watch=watch)

    # Track recent closed 4h bars and their engine index + ATR for causal checks
    history = []
    # Also track recently broken qualified red lines (within 1..16 bars) independently
    # so both breakout (1..2 bars) and red retest (2..16 bars) are captured accurately.
    broken_reds = {}
    last_snap = None
    last_signals = []
    prev_bar = None
    prev_snap = None

    for i, bar in enumerate(rows_4h):
        if i in gaps_4h:
            observer.gap(bar)
            history.clear()
            broken_reds.clear()
            prev_bar = None
            prev_snap = None
        events, signals, snap = observer.push(bar)
        if snap and snap.get("ready"):
            idx = snap["referenceIndex"]
            atr = snap["atr"]
            history.append((idx, bar, atr))
            if len(history) > rules.max_bars:
                history.pop(0)
            # Detect breaks of any active FanObserver red scenarios on this close
            for ev in events:
                if ev["kind"] == "break":
                    ln = deepcopy(ev["line"])
                    broken_reds[ev["scenarioId"]] = {
                        "scenarioId": ev["scenarioId"],
                        "line": ln,
                        "breakIndex": idx,
                        "breakAt": bar.end,
                        "breakBarClose": bar.close,
                        "breakAgeDays": _line_age_days(ln, bar.end),
                        "breakContactSpanDays": _contact_span_days(ln),
                        "cleanAt": None,
                    }
            for sig in signals:
                sid = sig.get("scenarioId")
                if sid in broken_reds and sig["family"] == "breakout":
                    broken_reds[sid]["cleanAt"] = bar.end
            # Expire old broken reds (> 16 bars)
            for sid in [k for k, v in broken_reds.items() if idx - v["breakIndex"] > 16]:
                del broken_reds[sid]
            prev_snap = last_snap
            last_snap = snap
            last_signals = signals
        prev_bar = bar

    if not last_snap or not last_snap.get("ready") or not _finite(last_snap.get("atr")) or last_snap["atr"] <= 0:
        return [], "analysis_unavailable", {"reason": "atr_not_ready"}

    idx = last_snap["referenceIndex"]
    atr = last_snap["atr"]
    bar_t = rows_4h[-1]
    green = last_snap.get("green")
    reds = last_snap.get("reds", [])
    greens = last_snap.get("greens", [])

    # Gate 2: green Safety Line must exist and satisfy rising >=2 contacts (no both_qualified gate)
    if not _check_green_gate(green, close_4h, bar_t.end, history, idx, rules):
        return [], "filtered_gate2_green", {}

    green_now = price_at(green, idx)
    green_next1 = green_now + green["slope"]
    stop0 = stop_price(green_now, buffer_pct=0.3, tick=rules.tick)
    if not stop0 or stop0 >= close_4h:
        return [], "filtered_gate5_stop", {}

    daily_red_val = _daily_red_resistance(bars_1d, cutoff, symbol)
    above_sma200 = daily_stats["above_sma200"]
    strategy_tag = (
        "TREND_FOLLOW"
        if above_sma200 is True
        else "REVERSAL"
        if above_sma200 is False
        else "UNKNOWN"
    )
    atr_1d_pct = daily_stats["atr_1d_pct"]
    bars_tail = [(h_idx, h_bar) for h_idx, h_bar, _ in history[-6:]]

    def build_candidate(
        scenario,
        red,
        *,
        eval_ref_price,
        break_bars_ago=None,
        compression_ratio=None,
        width_now=None,
        active_appr=False,
        wait_for_retest_only=False,
        apex_tight=False,
    ):
        red_now = price_at(red, idx)
        red_next1 = red_now + red["slope"]
        red_next2 = red_now + 2.0 * red["slope"]
        trig_next1 = red_next1 + 0.15 * atr
        trig_next2 = red_next2 + 0.15 * atr
        # Entry trigger reference for risk / +2R / share count:
        # For already-broken / retest states use current close; for pre-breakout use Trigger_{t+1}.
        if scenario in ("1A_CLEAN_BREAKOUT", "4A_RETEST_TRIGGER", "6_SAFETY_BOUNCE"):
            entry_ref = close_4h
        else:
            entry_ref = max(trig_next1, close_4h)
        unit_risk = entry_ref - stop0
        if unit_risk <= 0:
            return None
        risk_pct = 100.0 * unit_risk / entry_ref
        risk_atr = unit_risk / atr
        # Apex tight stop uses artificial Min-Risk-Floor of 1.0 * ATR_4h for share sizing
        sizing_risk = max(unit_risk, atr) if apex_tight else unit_risk
        ref_shares = int(math.floor(min(100.0 / sizing_risk, 2500.0 / entry_ref)))
        target_2r = entry_ref + 2.0 * unit_risk

        dist_signed = (close_4h - red_now) if scenario.startswith(("1", "4")) else (red_now - close_4h)
        dist_atr = dist_signed / atr
        dist_pct = 100.0 * dist_signed / close_4h

        width_atr = (width_now / atr) if _finite(width_now) else None
        red_age = _line_age_days(red, bar_t.end)
        red_cspan = _contact_span_days(red)
        green_age = _line_age_days(green, bar_t.end)

        roof_r, roof_near, clear_sky = _overhead_roof(
            red, reds, daily_red_val, idx, entry_ref, unit_risk
        )
        direct_entry = scenario in ("1A_CLEAN_BREAKOUT", "4A_RETEST_TRIGGER")
        score, compressed_flag, low_vol = _compute_score(
            active_approach=active_appr,
            compression_ratio=compression_ratio,
            width_atr=width_atr,
            red_age_days=red_age,
            red_contacts=red["contacts"],
            red_origin=red.get("origin", "pivot"),
            risk_pct=risk_pct,
            risk_atr=risk_atr,
            universes=universes,
            atr_1d_pct=atr_1d_pct,
            clear_sky=clear_sky,
            direct_entry=direct_entry,
        )
        high_maturity = bool(red_age >= 21.0 or red["contacts"] >= 4)
        quality_core = bool(direct_entry and active_appr and high_maturity)
        signal_tier = classify_tier(
            direct_entry=direct_entry,
            active_approach=active_appr,
            high_maturity=high_maturity,
            low_daily_volatility=low_vol,
        )
        fan_warn = _fan_chain_warning(red, reds) or _fan_chain_warning(green, greens)
        asof_iso = datetime.fromtimestamp(cutoff, timezone.utc).isoformat()
        chart_path = "/?" + urlencode(
            {
                "symbol": symbol,
                "dataset": dataset_id,
                "asof": asof_iso,
                "tf": "4h",
                "engine": "fan_master",
                "analysis": "1",
            }
        )
        return {
            "symbol": symbol,
            "universes": "|".join(sorted(universes)),
            "universe_list": sorted(universes),
            "scenario": scenario,
            "score": score,
            "strategy_tag": strategy_tag,
            "close_4h": _round(close_4h, 4),
            "atr_4h": _round(atr, 4),
            "atr_1d_pct": _round(atr_1d_pct, 2),
            "red_price_now": _round(red_now, 4),
            "red_price_next1": _round(red_next1, 4),
            "red_price_next2": _round(red_next2, 4),
            "clean_trigger_next1": _round(trig_next1, 4),
            "clean_trigger_next2": _round(trig_next2, 4),
            "dist_to_red_atr": _round(dist_atr, 3),
            "dist_to_red_pct": _round(dist_pct, 2),
            "green_price_now": _round(green_now, 4),
            "green_price_next1": _round(green_next1, 4),
            "stop_0_3_pct": _round(stop0, 2),
            "risk_usd": _round(unit_risk, 4),
            "risk_pct": _round(risk_pct, 2),
            "risk_atr": _round(risk_atr, 2),
            "target_plus_2r_price": _round(target_2r, 2),
            "ref_shares_10k": ref_shares,
            "red_contacts": int(red["contacts"]),
            "red_age_days": _round(red_age, 1),
            "red_contact_span_days": _round(red_cspan, 1),
            "red_origin": red.get("origin", "pivot"),
            "green_contacts": int(green["contacts"]),
            "green_age_days": _round(green_age, 1),
            "green_origin": green.get("origin", "pivot"),
            "active_approach": bool(active_appr),
            "compression": bool(compressed_flag),
            "compression_ratio": _round(compression_ratio, 3),
            "width_atr": _round(width_atr, 2),
            "clear_sky": bool(clear_sky),
            "daily_close": _round(daily_stats["daily_close"], 4),
            "daily_sma50": _round(daily_stats["daily_sma50"], 4),
            "daily_sma200": _round(daily_stats["daily_sma200"], 4),
            "above_sma200": above_sma200,
            "overhead_roof_r": _round(roof_r, 2),
            "overhead_roof_near": bool(roof_near),
            "fan_chain_warning": bool(fan_warn),
            "apex_tight_stop": bool(apex_tight),
            "wait_for_retest_only": bool(wait_for_retest_only),
            "low_daily_volatility": bool(low_vol),
            "quality_core": bool(quality_core),
            "signal_tier": signal_tier,
            "signal_tier_rank": TIER_ORDER[signal_tier],
            "earnings_days": earnings_days,
            "break_bars_ago": break_bars_ago,
            "dataset_id": dataset_id,
            "session": target_session,
            "cutoff": cutoff,
            "source_index": idx,
            "chart_path": chart_path,
            # Frozen original causal geometry for Watchlist & Papertrade handoff
            "geometry": {
                "red": deepcopy(red),
                "green": deepcopy(green),
                "source_index": idx,
                "bar_end": bar_t.end,
                "atr_4h": atr,
                "stop_0_3_pct": stop0,
                "clean_trigger_next1": trig_next1,
            },
        }

    found = []

    # --- 1) Check broken qualified red lines: Scenario 1 (1..2 bars) & Scenario 4 (2..16 bars) ---
    for b_info in broken_reds.values():
        red = b_info["line"]
        bars_since = idx - b_info["breakIndex"]
        if red["contacts"] < 3 or red["slope"] >= 0:
            continue
        if b_info["breakAgeDays"] < 10.0 or b_info["breakContactSpanDays"] < 7.0:
            continue
        if _has_body_violation(red, history, b_info["breakIndex"] - 1, rules, upper_exclude_tail=0):
            continue
        conv_ok, comp_ratio, width_break = _check_convergence(red, green, b_info["breakIndex"])
        if not conv_ok:
            continue
        red_now = price_at(red, idx)
        # Scenario 1: fresh breakout (0..1 bars after breakIndex, i.e. within last 1-2 closed 4h bars)
        if bars_since <= 1 and close_4h > red_now:
            unit_risk_now = close_4h - stop0
            risk_pct_now = 100.0 * unit_risk_now / close_4h
            risk_atr_now = unit_risk_now / atr
            # Gate 5 corridor for direct breakout
            apex = risk_atr_now < 0.6 and risk_pct_now >= 1.0
            if not apex and not (risk_atr_now >= 1.0 and risk_pct_now >= 2.0):
                continue
            if risk_pct_now > 8.5 or risk_atr_now > 3.8:
                # Overstretched direct breakout -> wait for retest only, never emit as Scenario 1
                continue
            clean_thresh = red_now + 0.15 * atr
            if close_4h >= clean_thresh:
                if close_4h <= red_now + 1.2 * atr:
                    cand = build_candidate(
                        "1A_CLEAN_BREAKOUT",
                        red,
                        eval_ref_price=close_4h,
                        break_bars_ago=bars_since,
                        compression_ratio=comp_ratio,
                        width_now=width_break,
                        active_appr=True,
                        apex_tight=apex,
                    )
                    if cand:
                        found.append(cand)
            else:
                cand = build_candidate(
                    "1B_ARMED_WAIT_CLEAN",
                    red,
                    eval_ref_price=close_4h,
                    break_bars_ago=bars_since,
                    compression_ratio=comp_ratio,
                    width_now=width_break,
                    active_appr=True,
                    apex_tight=apex,
                )
                if cand:
                    found.append(cand)
        # Scenario 4: red retest (2..16 closed 4h bars after break)
        if 2 <= bars_since <= 16:
            dist_from_red = (close_4h - red_now) / atr
            if -0.15 <= dist_from_red <= 0.75:
                unit_risk_now = close_4h - stop0
                risk_pct_now = 100.0 * unit_risk_now / close_4h
                risk_atr_now = unit_risk_now / atr
                apex = risk_atr_now < 0.6 and risk_pct_now >= 1.0
                if not apex and not (risk_atr_now >= 1.0 and risk_pct_now >= 1.8):
                    continue
                if risk_pct_now > 10.0:
                    continue
                prev_low = rows_4h[-2].low if len(rows_4h) >= 2 else bar_t.low
                touched_red = min(bar_t.low, prev_low) <= red_now + 0.30 * atr
                if touched_red and close_4h >= red_now and bar_t.close > bar_t.open:
                    cand = build_candidate(
                        "4A_RETEST_TRIGGER",
                        red,
                        eval_ref_price=close_4h,
                        break_bars_ago=bars_since,
                        compression_ratio=comp_ratio,
                        width_now=width_break,
                        active_appr=True,
                        apex_tight=apex,
                    )
                    if cand:
                        found.append(cand)
                elif len(rows_4h) >= 3 and close_4h < rows_4h[-3].close and 0.20 <= dist_from_red <= 0.75:
                    cand = build_candidate(
                        "4B_RETEST_APPROACH",
                        red,
                        eval_ref_price=close_4h,
                        break_bars_ago=bars_since,
                        compression_ratio=comp_ratio,
                        width_now=width_break,
                        active_appr=False,
                        apex_tight=apex,
                    )
                    if cand:
                        found.append(cand)

    # --- 2) Check active red lines above close: Scenario 2, Scenario 3, Scenario 5 (Fast A+) ---
    for red in reds:
        if not red.get("valid") or red["slope"] >= 0:
            continue
        red_now = price_at(red, idx)
        if not (green_now < close_4h <= red_now):
            continue
        if _has_body_violation(red, history, idx, rules, upper_exclude_tail=2):
            continue
        conv_ok, comp_ratio, width_now = _check_convergence(red, green, idx)
        if not conv_ok:
            continue
        dist_atr = (red_now - close_4h) / atr
        red_age = _line_age_days(red, bar_t.end)
        red_cspan = _contact_span_days(red)

        # Gate 5 risk check at current close and projected breakout point
        risk_close_usd = close_4h - stop0
        risk_close_pct = 100.0 * risk_close_usd / close_4h
        risk_close_atr = risk_close_usd / atr
        trig_break = (red_now + red["slope"]) + 0.15 * atr
        risk_brk_usd = trig_break - stop0
        risk_brk_pct = 100.0 * risk_brk_usd / trig_break if trig_break > 0 else 999.0
        risk_brk_atr = risk_brk_usd / atr

        apex = risk_close_atr < 0.6 and risk_brk_pct >= 1.0
        lower_ok = apex or (risk_close_atr >= 1.0 and risk_close_pct >= 1.8 and risk_brk_pct >= 2.0)
        upper_ok = risk_brk_pct <= 8.5 and risk_brk_atr <= 3.8
        if not (lower_ok and upper_ok):
            continue

        active_appr = _active_approach(red, bars_tail, idx, atr)
        compressed_watch = (
            (_finite(comp_ratio) and comp_ratio <= 0.50)
            or (_finite(width_now) and (width_now / atr) <= 2.5)
        )

        # Qualified A+ red line (Gate 1): >=3 contacts, >=10d age, >=7d contact span
        if red["contacts"] >= 3 and red_age >= 10.0 and red_cspan >= 7.0:
            wick_touch = bar_t.high >= red_now - 0.15 * atr
            if dist_atr <= 0.40 or wick_touch:
                cand = build_candidate(
                    "2_IMMEDIATE_TEST",
                    red,
                    eval_ref_price=trig_break,
                    compression_ratio=comp_ratio,
                    width_now=width_now,
                    active_appr=active_appr,
                    apex_tight=apex,
                )
                if cand:
                    found.append(cand)
            elif 0.40 < dist_atr <= 0.85 and (active_appr or compressed_watch):
                cand = build_candidate(
                    "3_APPROACH_WATCH",
                    red,
                    eval_ref_price=trig_break,
                    compression_ratio=comp_ratio,
                    width_now=width_now,
                    active_appr=active_appr,
                    apex_tight=apex,
                )
                if cand:
                    found.append(cand)
        # Scenario 5 (Fast A+ appendix): exact 2 contacts, >=14d old, last contact >=5 bars ago, <=0.25 ATR
        elif red["contacts"] == 2 and red_age >= 14.0 and dist_atr <= 0.25:
            pts = red.get("contactPoints") or []
            last_contact_idx = pts[-1]["index"] if pts else red["b_index"]
            if idx - last_contact_idx >= rules.contact_gap:
                cand = build_candidate(
                    "5_FAST_A_PLUS",
                    red,
                    eval_ref_price=trig_break,
                    compression_ratio=comp_ratio,
                    width_now=width_now,
                    active_appr=active_appr,
                    apex_tight=apex,
                )
                if cand:
                    found.append(cand)

    # Optional research-only Safety-Bounce (disabled by default per spec)
    if include_safety_bounce and last_signals:
        for sig in last_signals:
            if sig["family"] == "safety_bounce" and sig.get("validRisk"):
                red_ctx = last_snap.get("red") or (reds[0] if reds else None)
                if red_ctx:
                    cand = build_candidate(
                        "6_SAFETY_BOUNCE",
                        red_ctx,
                        eval_ref_price=close_4h,
                        active_appr=True,
                    )
                    if cand:
                        found.append(cand)

    if not found:
        return [], "ok_no_setup", {}

    # Pick the single highest-priority / highest-score scenario for this symbol
    found.sort(
        key=lambda c: (
            SCENARIO_ORDER.get(c["scenario"], 99),
            -c["score"],
            abs(c["dist_to_red_atr"] or 0.0),
        )
    )
    return [found[0]], "candidate", {}


def resolve_target_session(session_arg, bases, now=None):
    """Resolve target session: 'auto' (strict last regular US session), 'latest' (freshest archive), or YYYY-MM-DD."""
    now = now or datetime.now(timezone.utc)
    if not session_arg or session_arg == "auto":
        return available_session(now)
    if session_arg == "latest":
        sessions = [b["lastSession"] for b in bases.values() if b.get("lastSession")]
        if not sessions:
            raise DataError("Keine lokalen SIP-Kursdaten für den Scan gefunden.", 404)
        # Most frequent among the freshest sessions (or absolute max if >= 20 stocks have it)
        counts = Counter(sessions)
        newest = max(counts)
        if counts[newest] >= min(20, max(1, len(sessions) // 10)):
            return newest
        return counts.most_common(1)[0][0]
    # Explicit YYYY-MM-DD
    if session_bounds(session_arg) is None:
        raise DataError(f"{session_arg} ist keine reguläre US-Handelssitzung (XNYS).", 400)
    return session_arg


def _universe_members(universe_arg):
    keys = DEFAULT_UNIVERSES if universe_arg in (None, "all") else (universe_arg,)
    symbol_universes = {}
    loaded = {}
    for key in keys:
        u = read_universe(key)
        if not u:
            loaded[key] = {"status": "membership_not_cached", "count": 0}
            continue
        members = sorted({m["symbol"] for m in u["members"]})
        loaded[key] = {"asOf": u["asOf"], "count": len(members)}
        for sym in members:
            symbol_universes.setdefault(sym, set()).add(key)
    return keys, loaded, symbol_universes


def _scan_corrupted_manifests(root):
    """Explicitly detect unreadable manifest files instead of silently ignoring them."""
    corrupt = []
    ds_dir = root / "datasets"
    if not ds_dir.is_dir():
        return corrupt
    for path in ds_dir.glob("*.json"):
        if path.is_symlink():
            continue
        try:
            json.loads(path.read_text("utf-8"))
        except (OSError, ValueError):
            corrupt.append(path.name)
    return sorted(corrupt)


def market_regime_at(db, cutoff, target_session, *, root=None):
    """Informative, strictly causal US market weather (SPY & QQQ vs SMA200/SMA50).

    Not a hard buy-ban: our 9-year PIT backtest showed post-crash rebounds below SMA200
    can produce strong reversal breakouts, albeit with higher volatility.
    """
    root = Path(root) if root else data_dir()
    bench_bases = archive_inventory({"SPY", "QQQ"}, root)
    items = {}
    for sym in ("SPY", "QQQ"):
        base = bench_bases.get(sym)
        if not base:
            items[sym] = {"available": False}
            continue
        try:
            frames = read_frames(db, base["datasetId"], cutoff, target_session[:7])
        except (DataError, ParquetError, OSError, ValueError):
            items[sym] = {"available": False}
            continue
        closed = [b for b in frames.get("1D", []) if b.end <= cutoff]
        if not closed:
            items[sym] = {"available": False}
            continue
        close = closed[-1].close
        asof_day = datetime.fromtimestamp(closed[-1].time, timezone.utc).date().isoformat()
        sma50 = (sum(b.close for b in closed[-50:]) / 50.0) if len(closed) >= 50 else None
        sma200 = (sum(b.close for b in closed[-200:]) / 200.0) if len(closed) >= 200 else None
        items[sym] = {
            "available": True,
            "asofSession": asof_day,
            "close": _round(close, 2),
            "sma50": _round(sma50, 2),
            "sma200": _round(sma200, 2),
            "aboveSma50": None if sma50 is None else bool(close >= sma50),
            "aboveSma200": None if sma200 is None else bool(close >= sma200),
            "distSma200Pct": _round(100.0 * (close - sma200) / sma200, 2) if (sma200 and sma200 > 0) else None,
        }
    spy = items.get("SPY", {})
    qqq = items.get("QQQ", {})
    if spy.get("aboveSma200") is True and qqq.get("aboveSma200") is True:
        status = "BULL"
        label = "Aufwärtstrend (SPY & QQQ über SMA200)"
        hint = "Normales Trendumfeld. Bewährter Fokus: Direkteinstieg (1A/4A), aktive Annäherung, reife Linie (≥21T/4K), ruhige Vola."
    elif spy.get("aboveSma200") is False and qqq.get("aboveSma200") is False:
        status = "CORRECTION"
        label = "Korrektur / Bärenphase (SPY & QQQ unter SMA200)"
        hint = "Keine harte Sperre: Nach Ausverkäufen entstehen hier starke Trendwende-Ausbrüche, aber mit höherem Ausstopp-Risiko – striktes 1%-Risiko einhalten."
    elif spy.get("available") or qqq.get("available"):
        status = "MIXED"
        label = "Gemischte Marktlage (SPY / QQQ uneinheitlich)"
        hint = "Selektiv vorgehen und besonders auf aktive Annäherung sowie sauberen 4H-Schluss achten."
    else:
        status = "UNAVAILABLE"
        label = "Keine lokalen Benchmark-Daten (SPY/QQQ)"
        hint = "Für die Marktlage-Anzeige können SPY/QQQ optional ins lokale SIP-Archiv geladen werden."
    return {"status": status, "label": label, "hint": hint, "benchmarks": items}


def scan_universe(
    *,
    universe="all",
    session="auto",
    scenario="all",
    min_score=0,
    top_n=10,
    quality_filter="all",
    include_safety_bounce=False,
    earnings_file=None,
    now=None,
    root=None,
):
    """Run the full offline causal scan across the selected universes."""
    started = time.monotonic()
    root = Path(root) if root else data_dir()
    keys, loaded_universes, symbol_universes = _universe_members(universe)
    all_symbols = sorted(symbol_universes)
    bases = archive_inventory(set(all_symbols), root)
    target_session = resolve_target_session(session, bases, now=now)
    _, cutoff = session_bounds(target_session)
    earnings_map = load_earnings_map(earnings_file, target_session)

    # Batched 5m gap audit for target_session across all symbols with local history
    gaps_by_symbol = recent_gaps(bases, {target_session}, root) if bases else {}
    corrupt_manifests = _scan_corrupted_manifests(root)

    coverage = Counter()
    audit_lists = {
        "no_local_history": [],
        "stale_history": [],
        "data_problem": [],
        "missing_session_4h": [],
        "analysis_unavailable": [],
        "error": [],
    }
    candidates = []
    checked = 0

    market_regime = None
    with connect() as db:
        market_regime = market_regime_at(db, cutoff, target_session, root=root)
        for sym in all_symbols:
            base = bases.get(sym)
            if base is None:
                coverage["no_local_history"] += 1
                audit_lists["no_local_history"].append(sym)
                continue
            if base["lastSession"] < target_session:
                coverage["stale_history"] += 1
                audit_lists["stale_history"].append(sym)
                continue
            missing_5m = gaps_by_symbol.get(sym, {}).get(target_session, 0)
            if missing_5m >= MISSING_BAR_LIMIT:
                coverage["data_problem"] += 1
                audit_lists["data_problem"].append(f"{sym}({missing_5m})")
                continue
            try:
                frames = read_frames(db, base["datasetId"], cutoff, target_session[:7])
                found, reason, _ = evaluate_symbol(
                    sym,
                    frames["4h"],
                    frames["1D"],
                    target_session=target_session,
                    cutoff=cutoff,
                    dataset_id=base["datasetId"],
                    universes=symbol_universes[sym],
                    earnings_days=earnings_map.get(sym),
                    include_safety_bounce=include_safety_bounce,
                )
            except (DataError, ParquetError, OSError, ValueError, KeyError) as exc:
                coverage["error"] += 1
                audit_lists["error"].append(f"{sym}:{exc}")
                continue

            if reason in ("missing_session_4h", "analysis_unavailable"):
                coverage[reason] += 1
                audit_lists[reason].append(sym)
                continue
            checked += 1
            coverage[reason] += 1
            candidates.extend(found)

    # Apply scenario, quality_filter & min_score filters
    allowed = SCENARIO_GROUPS.get(scenario)
    tier_allow_map = {
        "all": None,
        "focus": {"C", "B", "4", "A"},
        "quiet": {"C", "B", "4"},
        "core": {"C", "A"},
        "tier_c": {"C"},
    }
    allowed_tiers = tier_allow_map.get(quality_filter)
    filtered = [
        c for c in candidates
        if c["score"] >= min_score
        and (allowed is None or c["scenario"] in allowed)
        and (allowed_tiers is None or c.get("signal_tier") in allowed_tiers or c["scenario"] == "5_FAST_A_PLUS")
    ]

    # Sort deterministically: Tier C -> B -> 4 -> A -> BASIS first, then score desc, scenario, closeness, symbol
    main_candidates = [c for c in filtered if c["scenario"] != "5_FAST_A_PLUS"]
    fast_a_candidates = [c for c in filtered if c["scenario"] == "5_FAST_A_PLUS"]

    main_candidates.sort(
        key=lambda c: (
            c.get("signal_tier_rank", TIER_ORDER.get(c.get("signal_tier", "BASIS"), 5)),
            -c["score"],
            SCENARIO_ORDER.get(c["scenario"], 99),
            abs(c["dist_to_red_atr"] or 0.0),
            c["symbol"],
        )
    )
    fast_a_candidates.sort(
        key=lambda c: (-c["score"], abs(c["dist_to_red_atr"] or 0.0), c["symbol"])
    )

    top_list = main_candidates[:max(0, int(top_n))]
    fast_a_top = fast_a_candidates[:3]
    elapsed = round(time.monotonic() - started, 2)

    return {
        "version": VERSION,
        "session": target_session,
        "cutoff": cutoff,
        "cutoffUtc": datetime.fromtimestamp(cutoff, timezone.utc).isoformat(),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "elapsedSeconds": elapsed,
        "filters": {
            "universe": universe,
            "scenario": scenario,
            "minScore": min_score,
            "topN": top_n,
            "qualityFilter": quality_filter,
            "includeSafetyBounce": include_safety_bounce,
        },
        "marketRegime": market_regime,
        "universes": loaded_universes,
        "counts": {
            "totalSymbols": len(all_symbols),
            "checkedSymbols": checked,
            "qualifiedMain": len(main_candidates),
            "topCount": len(top_list),
            "fastAPlus": len(fast_a_top),
            "byScenario": dict(Counter(c["scenario"] for c in filtered)),
        },
        "audit": {
            "coverage": dict(coverage),
            "corruptManifests": corrupt_manifests,
            "lists": {k: v[:40] for k, v in audit_lists.items() if v},
            "staleCount": coverage["stale_history"],
            "dataProblemCount": coverage["data_problem"],
            "missing4hCount": coverage["missing_session_4h"],
            "warmupShortCount": coverage["analysis_unavailable"],
            "noHistoryCount": coverage["no_local_history"],
            "errorCount": coverage["error"],
        },
        "top10": top_list,
        "candidates": main_candidates,
        "fastAPlus": fast_a_top,
    }


def _fmt_num(val, suffix="", decimals=2):
    if not _finite(val):
        return "–"
    text = f"{val:.{decimals}f}".replace(".", ",")
    return f"{text}{suffix}"


def _earnings_badge(c):
    days = c.get("earnings_days")
    return f" ⚠️ EARNINGS ({days}d)" if days is not None else ""


def _context_label(c):
    tag = c["strategy_tag"]
    if c["above_sma200"] is True:
        sma = ">SMA200"
    elif c["above_sma200"] is False:
        sma = "<SMA200"
    else:
        sma = "SMA200?"
    roof = " ⚠️ DACH" if c.get("overhead_roof_near") else ""
    return f"`{tag}` ({sma}){roof}{_earnings_badge(c)}"


def render_markdown(report):
    """Render deterministic Markdown report matching docs/hermes_spezifikation_tori_scanner.md section 7."""
    counts = report["counts"]
    audit = report["audit"]
    session = report["session"]
    lines = [
        f"# 🎯 Tori Trendlinien-Radar · Zielsitzung: {session}",
        "",
        f"**Geprüfte Aktien:** {counts['checkedSymbols']} / {counts['totalSymbols']} (aus {', '.join(f'`{k}`' for k in report['universes'])})  ",
        f"**Qualifizierte Treffer (Tore 1–6 erfüllt):** {counts['qualifiedMain']} Kandidaten · **Top {report['filters']['topN']}:** {counts['topCount']} (absteigend nach Score 0–10 sortiert)",
        "",
    ]

    if audit["staleCount"] > 0:
        lines.append(
            f"> ⚠️ **Daten-Hinweis:** {audit['staleCount']} Titel haben noch keinen Kursstand für `{session}` (Datenupdate nach US-Börsenschluss erforderlich)."
        )
        lines.append("")

    # Compact Top-10 Overview first (for immediate visual review & watchlist selection)
    lines.extend([
        f"## 🏆 TOP {report['filters']['topN']} DES TAGES (Sofort-Auswahl für Sichtprüfung & Watchlist)",
        "",
    ])
    if not report["top10"]:
        lines.append("_Keine Aktie erfüllt für diese Zielsitzung alle 6 Pflicht-Tore._")
    else:
        lines.extend([
            "| # | Symbol | Szenario | Score | Schluss | Trigger K1 | Stop (0,3%) | Risiko (% / ATR) | +2R Ziel | Kontext (1D) |",
            "| :-: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |",
        ])
        for rank, c in enumerate(report["top10"], 1):
            lines.append(
                f"| {rank} | **{c['symbol']}** | `{c['scenario']}` | **{c['score']}/10** | "
                f"{_fmt_num(c['close_4h'], ' $')} | **{_fmt_num(c['clean_trigger_next1'], ' $')}** | "
                f"**{_fmt_num(c['stop_0_3_pct'], ' $')}** | {_fmt_num(c['risk_pct'], ' %', 1)} / {_fmt_num(c['risk_atr'], ' ATR', 1)} | "
                f"{_fmt_num(c['target_plus_2r_price'], ' $')} | {_context_label(c)} |"
            )
    lines.append("")

    # Scenario 1: Fresh Breakouts
    s1 = [c for c in report["candidates"] if c["scenario"] in ("1A_CLEAN_BREAKOUT", "1B_ARMED_WAIT_CLEAN")]
    lines.extend([
        "---",
        "",
        "## 🚨 SZENARIO 1: Frische Ausbrüche über Rot (Sofort-Prüfung!)",
        "*Die 4H-Kerze hat die qualifizierte rote Widerstandslinie (3+ Kontakte, >= 10d) in der Zielsitzung bereits per Schlusskurs überquert.*",
        "",
    ])
    if not s1:
        lines.append("_Keine Treffer in Szenario 1._")
    else:
        lines.extend([
            "| Symbol | Sub-Status | Score | Schluss | Rot (Bruch) | Clean-Trigger | Grün (Stop 0,3%) | Risiko (% / ATR) | +2R Ziel | Rot (Kont./Alter) | Kontext (1D) |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |",
        ])
        for c in s1:
            sub = "`1A_CLEAN`" if c["scenario"] == "1A_CLEAN_BREAKOUT" else "`1B_ARMED`"
            lines.append(
                f"| **{c['symbol']}** | {sub} | **{c['score']}/10** | {_fmt_num(c['close_4h'], ' $')} | "
                f"{_fmt_num(c['red_price_now'], ' $')} | **{_fmt_num(c['clean_trigger_next1'], ' $')}** | "
                f"{_fmt_num(c['green_price_now'], ' $')} (**{_fmt_num(c['stop_0_3_pct'], ' $')}**) | "
                f"{_fmt_num(c['risk_pct'], ' %', 1)} / {_fmt_num(c['risk_atr'], ' ATR', 1)} | "
                f"{_fmt_num(c['target_plus_2r_price'], ' $')} | {c['red_contacts']}K / {_fmt_num(c['red_age_days'], 'd', 0)} (`{c['red_origin']}`) | "
                f"{_context_label(c)} |"
            )
    lines.append("")

    # Scenario 2: Immediate Test
    s2 = [c for c in report["candidates"] if c["scenario"] == "2_IMMEDIATE_TEST"]
    lines.extend([
        "---",
        "",
        "## 🔥 SZENARIO 2: Unmittelbar vor dem Ausbruch (<= 0,40 ATR / Test läuft)",
        "*Der Kurs drückt unmittelbar von unten gegen das qualifizierte rote Widerstandsdach. Entscheidung in den nächsten 1–2 Kerzen möglich.*",
        "",
    ])
    if not s2:
        lines.append("_Keine Treffer in Szenario 2._")
    else:
        lines.extend([
            "| Symbol | Status / Dynamik | Score | Schluss | Abstand Rot | Trigger (K1 / K2) | Stop-Kurs (0,3%) | Risiko (% / ATR) | +2R Ziel | Rot (Kont./Alter) | Kontext (1D) |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |",
        ])
        for c in s2:
            dyn = "+".join([x for x, ok in (("Aktiv", c["active_approach"]), ("Kompr.", c["compression"])) if ok]) or "Test"
            lines.append(
                f"| **{c['symbol']}** | `2_IMMEDIATE` ({dyn}) | **{c['score']}/10** | {_fmt_num(c['close_4h'], ' $')} | "
                f"**{_fmt_num(c['dist_to_red_atr'], ' ATR')}** ({_fmt_num(c['dist_to_red_pct'], '%', 1)}) | "
                f"**{_fmt_num(c['clean_trigger_next1'], ' $')}** / {_fmt_num(c['clean_trigger_next2'], ' $')} | "
                f"**{_fmt_num(c['stop_0_3_pct'], ' $')}** | {_fmt_num(c['risk_pct'], ' %', 1)} / {_fmt_num(c['risk_atr'], ' ATR', 1)} | "
                f"{_fmt_num(c['target_plus_2r_price'], ' $')} | {c['red_contacts']}K / {_fmt_num(c['red_age_days'], 'd', 0)} (`{c['red_origin']}`) | "
                f"{_context_label(c)} |"
            )
    lines.append("")

    # Scenario 3: Approach Watch
    s3 = [c for c in report["candidates"] if c["scenario"] == "3_APPROACH_WATCH"]
    lines.extend([
        "---",
        "",
        "## 🔭 SZENARIO 3: Vorwarnung 1–2 Handelstage (0,40 bis 0,85 ATR + Aktive Dynamik)",
        "*Frühzeitige Beobachtungsliste: Struktur verengt sich oder Kurs läuft aktiv auf die qualifizierte rote Linie zu.*",
        "",
    ])
    if not s3:
        lines.append("_Keine Treffer in Szenario 3._")
    else:
        lines.extend([
            "| Symbol | Dynamik | Score | Schluss | Abstand Rot | Trigger (K1) | Stop-Kurs (0,3%) | Risiko (% / ATR) | Rot (Kont./Alter) | Grün (Kont./Alter) | Kontext (1D) |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |",
        ])
        for c in s3:
            dyn = "+".join([x for x, ok in (("Aktiv", c["active_approach"]), ("Kompr.", c["compression"])) if ok]) or "–"
            lines.append(
                f"| **{c['symbol']}** | `3_APPROACH` ({dyn}) | **{c['score']}/10** | {_fmt_num(c['close_4h'], ' $')} | "
                f"**{_fmt_num(c['dist_to_red_atr'], ' ATR')}** ({_fmt_num(c['dist_to_red_pct'], '%', 1)}) | "
                f"**{_fmt_num(c['clean_trigger_next1'], ' $')}** | **{_fmt_num(c['stop_0_3_pct'], ' $')}** | "
                f"{_fmt_num(c['risk_pct'], ' %', 1)} / {_fmt_num(c['risk_atr'], ' ATR', 1)} | "
                f"{c['red_contacts']}K / {_fmt_num(c['red_age_days'], 'd', 0)} (`{c['red_origin']}`) | "
                f"{c['green_contacts']}K / {_fmt_num(c['green_age_days'], 'd', 0)} | {_context_label(c)} |"
            )
    lines.append("")

    # Scenario 4: Red Retest
    s4 = [c for c in report["candidates"] if c["scenario"] in ("4A_RETEST_TRIGGER", "4B_RETEST_APPROACH")]
    lines.extend([
        "---",
        "",
        "## 🔵 SZENARIO 4: Roter Retest (Rücklauf von oben auf gebrochenes A+-Rot)",
        "*Qualifizierte rote Linie wurde kürzlich nach oben durchbrochen; Kurs setzt bei intakter grüner Safety von oben auf die rote Linie zurück.*",
        "",
    ])
    if not s4:
        lines.append("_Keine Treffer in Szenario 4._")
    else:
        lines.extend([
            "| Symbol | Sub-Status | Score | Schluss | Gebrochenes Rot | Abstand zu Rot | Stop-Kurs (0,3%) | Risiko (% / ATR) | +2R Ziel | Bruch vor | Kontext (1D) |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |",
        ])
        for c in s4:
            sub = "`4A_TRIGGER` (Grüne Kerze)" if c["scenario"] == "4A_RETEST_TRIGGER" else "`4B_APPROACH`"
            lines.append(
                f"| **{c['symbol']}** | {sub} | **{c['score']}/10** | {_fmt_num(c['close_4h'], ' $')} | "
                f"{_fmt_num(c['red_price_now'], ' $')} | **{_fmt_num(c['dist_to_red_atr'], ' ATR')}** ({_fmt_num(c['dist_to_red_pct'], '%', 1)}) | "
                f"**{_fmt_num(c['stop_0_3_pct'], ' $')}** | {_fmt_num(c['risk_pct'], ' %', 1)} / {_fmt_num(c['risk_atr'], ' ATR', 1)} | "
                f"{_fmt_num(c['target_plus_2r_price'], ' $')} | {c['break_bars_ago']} Kerzen | {_context_label(c)} |"
            )
    lines.append("")

    # Appendix: Fast-A+ (max top 3)
    lines.extend([
        "---",
        "",
        "## 👀 ANHANG: Fast-A+ Watchlist (Max. Top 3 mit 2 Kontakten unmittelbar vor Kontakt Nr. 3)",
        "*(Nur zur Vormerkung: Linien mit >= 14 Tagen Alter und <= 0,25 ATR Abstand, die heute ihren 3. Kontakt ausbilden können)*",
        "",
    ])
    if not report["fastAPlus"]:
        lines.append("_Keine Fast-A+-Kandidaten._")
    else:
        lines.extend([
            "| Symbol | Score | Schluss | Abstand Rot | Trigger (K1) | Stop (0,3%) | Risiko (% / ATR) | Rot (Alter) | Kontext (1D) |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |",
        ])
        for c in report["fastAPlus"]:
            lines.append(
                f"| **{c['symbol']}** | **{c['score']}/10** | {_fmt_num(c['close_4h'], ' $')} | "
                f"{_fmt_num(c['dist_to_red_atr'], ' ATR')} | {_fmt_num(c['clean_trigger_next1'], ' $')} | "
                f"{_fmt_num(c['stop_0_3_pct'], ' $')} | {_fmt_num(c['risk_pct'], ' %', 1)} / {_fmt_num(c['risk_atr'], ' ATR', 1)} | "
                f"2K / {_fmt_num(c['red_age_days'], 'd', 0)} | {_context_label(c)} |"
            )
    lines.append("")

    # Technical & data audit footer (single compact summary per spec section 2.1 & 7)
    missing_4h_list = ", ".join(audit["lists"].get("missing_session_4h", [])[:15])
    data_prob_list = ", ".join(audit["lists"].get("data_problem", [])[:15])
    audit_parts = [
        f"Laufzeit: {_fmt_num(report['elapsedSeconds'], ' s', 1)}",
        f"Geprüft: {counts['checkedSymbols']}/{counts['totalSymbols']}",
        f"Vorlauf <320d: {audit['warmupShortCount']}",
        f"Ohne Historie: {audit['noHistoryCount']}",
        f"Veraltet: {audit['staleCount']}",
        f"`missing_session_4h`: {audit['missing4hCount']}" + (f" ({missing_4h_list})" if missing_4h_list else ""),
        f"`data_problem`: {audit['dataProblemCount']}" + (f" ({data_prob_list})" if data_prob_list else ""),
    ]
    if audit["errorCount"]:
        audit_parts.append(f"Fehler: {audit['errorCount']}")
    if audit["corruptManifests"]:
        audit_parts.append(f"Defekte Manifeste: {len(audit['corruptManifests'])}")

    lines.extend([
        "---",
        "**Technik- & Daten-Audit:**  ",
        " | ".join(audit_parts) + "  ",
        "*Hinweis zur Ausführung: Alle Stop-Kurse enthalten bereits den 0,3-%-Puffer (abgerundet auf volle Cent). Stop-Nachführung erst ab Erreichen des `+2R Ziel`-Schlusskurses (`r2_fan`) oder auf 3-Kontakt-Safety (`qualified_fan`) verengen.*",
    ])
    return "\n".join(lines) + "\n"


def write_csv(report, path):
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    rows = report["candidates"] + report["fastAPlus"]
    with dest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for item in rows:
            writer.writerow(item)
    return dest


def write_outputs(report, *, md_out=None, csv_out=None, json_out=None, store_latest=True):
    written = {}
    if md_out:
        p = Path(md_out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(render_markdown(report), encoding="utf-8")
        written["markdown"] = str(p)
    if csv_out:
        written["csv"] = str(write_csv(report, csv_out))
    if json_out:
        p = Path(json_out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
        written["json"] = str(p)
    if store_latest:
        state_dir = data_dir() / "paper-watch"
        state_dir.mkdir(parents=True, exist_ok=True)
        latest_path = state_dir / "latest-scan.json"
        tmp = latest_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(report, ensure_ascii=False, allow_nan=False), encoding="utf-8")
        tmp.replace(latest_path)
        written["latest"] = str(latest_path)
    return written
