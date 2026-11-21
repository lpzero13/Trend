"""Multi-year, strictly causal feature-comparison backtest for hermes_scanner (Weg B).

Runs ONE chronological pass per symbol (fast, low-RAM, parallelizable across
workers with atomic per-symbol blocks and immutable plan/code/dataset binding).
Separates train, validation, and locked holdout splits to prevent overfitting.
"""
from bisect import bisect_right
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics
import time

from duckdb import Error as ParquetError

from daily_archive import inventory as archive_inventory, trading_day
from datasets import path_for
from exit_followup import policy_timeline
from fan_geometry import create_engine, profile, stable_id
from fan_observer import WatchRules, price_at
from fan_study import source_gaps
import hermes_scanner as hs
from lab_data import session_bounds
from models import Bar, DataError
from parquet_store import block_path, checksum, connect as duck_connect
from pilot_backtest import PilotObserver
import pit_membership as pm
from settings import data_dir
from setup_episodes import Episodes
from signal_path_index import CaseExecution, PathIndex, execute_unbounded, isolated_entry
from strategy_run_lock import study_lock

VERSION = "tori-scanner-backtest-1"
DEFAULT_SPLITS = {
    "train": ("2017-07-01", "2023-12-31"),
    "validation": ("2024-01-01", "2024-12-31"),
    "holdout": ("2025-01-01", "2026-06-30"),
}
DEFAULT_OUTCOME_CUTOFF = "2026-10-29"
STOP_POLICIES = ("r2_fan", "qualified_fan", "original_safety")
BINDING_FILES = (
    "scanner_backtest.py",
    "hermes_scanner.py",
    "pit_membership.py",
    "fan_master.py",
    "fan_geometry.py",
    "fan_observer.py",
    "pilot_backtest.py",
    "setup_episodes.py",
    "signal_path_index.py",
    "exit_followup.py",
    "entry_screen.py",
)


def code_binding():
    root = Path(__file__).resolve().parent
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in BINDING_FILES}


def _atomic_write_json(path, payload):
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    tmp.replace(dest)


def _load_plan(output_dir, *, verify_engine=True):
    path = Path(output_dir) / "plan.json"
    if not path.is_file():
        return None
    plan = json.loads(path.read_text("utf-8"))
    expected_id = stable_id({k: v for k, v in plan.items() if k != "id"})
    if plan.get("id") != expected_id:
        raise DataError("Studienplan-Prüfsumme weicht ab (plan.json beschädigt oder verändert).", 409)
    if verify_engine and plan.get("engine") != code_binding():
        raise DataError(
            "Studienplan oder Engine-Code weicht ab: bestehenden Ordner nicht mit neuem Code fortsetzen, sondern neuen Ausgabeordner verwenden.",
            409,
        )
    return plan


def prepare_plan(
    output_dir,
    *,
    universe="all",
    symbols=None,
    splits=None,
    outcome_cutoff=DEFAULT_OUTCOME_CUTOFF,
    capital_eur=1000.0,
    max_watch_sessions=20,
    pit_membership_path=None,
    root=None,
):
    """Create or validate an immutable study plan bound to exact code and datasets."""
    out = Path(output_dir)
    existing = _load_plan(out)
    if existing is not None:
        if symbols and sorted(s.upper() for s in symbols) != existing["symbols"]:
            raise DataError("Symbolauswahl kann beim Wiederaufnehmen nicht geändert werden.", 409)
        return existing

    data_root = Path(root) if root else data_dir()
    pit_obj = None
    pit_path_str = None
    if pit_membership_path:
        pit_p = Path(pit_membership_path) if pit_membership_path != "auto" else (data_root / pm.PIT_DIR_REL / pm.PIT_FILE_NAME)
        pit_obj = pm.PitMembership.load(pit_p)
        pit_path_str = str(pit_p.resolve())
        loaded_universes = pit_obj.payload["counts"]
        allowed_u = ("dow30", "nasdaq100", "sp500") if universe == "all" else (universe,)
        symbol_universes = {
            sym: set(meta["universes"]).intersection(allowed_u)
            for sym, meta in pit_obj.symbols.items()
            if set(meta["universes"]).intersection(allowed_u)
        }
    else:
        _, loaded_universes, symbol_universes = hs._universe_members(universe)

    selected = sorted({s.upper().strip() for s in symbols}) if symbols else sorted(symbol_universes)
    bases = archive_inventory(set(selected), data_root)
    active_splits = {k: list(v) for k, v in (splits or DEFAULT_SPLITS).items()}
    _, outcome_ts = session_bounds(outcome_cutoff)

    datasets = {}
    missing = []
    for sym in selected:
        base = bases.get(sym)
        if base is None:
            missing.append(sym)
        else:
            datasets[sym] = {
                "datasetId": base["datasetId"],
                "firstSession": base["firstSession"],
                "lastSession": base["lastSession"],
                "universes": sorted(symbol_universes.get(sym, {universe})),
                "pitIntervals": pit_obj.symbols[sym]["universes"] if (pit_obj and sym in pit_obj.symbols) else None,
            }

    plan = {
        "version": VERSION,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "universe": universe,
        "universes": loaded_universes,
        "pointInTime": bool(pit_obj is not None),
        "pitMembershipPath": pit_path_str,
        "splits": active_splits,
        "outcomeCutoffSession": outcome_cutoff,
        "outcomeCutoff": outcome_ts,
        "capitalEur": float(capital_eur),
        "maxWatchSessions": int(max_watch_sessions),
        "stopPolicies": list(STOP_POLICIES),
        "symbols": sorted(datasets),
        "missingSymbols": missing,
        "datasets": datasets,
        "engine": code_binding(),
    }
    plan["id"] = stable_id(plan)
    out.mkdir(parents=True, exist_ok=True)
    (out / "blocks").mkdir(parents=True, exist_ok=True)
    _atomic_write_json(out / "plan.json", plan)
    return plan


def _read_all_frames(dataset_id, cutoff, *, root=None):
    """Read immutable 4h, 1D and 5m bars <= cutoff for one symbol in a single DuckDB query."""
    path = path_for(dataset_id) if root is None else Path(root) / "datasets" / f"{dataset_id}.json"
    if not path.is_file():
        raise DataError(f"Dataset {dataset_id} fehlt.", 404)
    manifest = json.loads(path.read_text("utf-8"))
    storage = manifest.get("storage")
    if storage is None:
        material = manifest["material"]
        return {
            tf: [Bar(**b) for b in material["bars"][tf] if b["end"] <= cutoff]
            for tf in ("4h", "1D", "5m")
        }
    if manifest["id"] != dataset_id:
        raise DataError("Kursmanifest passt nicht zur Dataset-ID.", 409)
    month_limit = datetime.fromtimestamp(cutoff, timezone.utc).strftime("%Y-%m")
    ds_root = path.parent.parent
    paths = []
    for entry in storage.get("blocks", []):
        if entry["month"] > month_limit:
            continue
        bp = block_path(ds_root, entry["path"])
        if bp.stat().st_size != entry["bytes"] or checksum(bp) != entry["sha256"]:
            raise DataError("Parquet-Prüfsumme ungültig.", 409)
        paths.append(str(bp))
    frames = {"4h": [], "1D": [], "5m": []}
    if paths:
        with duck_connect() as db:
            rows = db.execute(
                'SELECT timeframe,"time","end",open,high,low,close,volume FROM read_parquet(?) '
                'WHERE timeframe IN (?,?,?) AND "end"<=? ORDER BY timeframe,"time"',
                [paths, "4h", "1D", "5m", cutoff],
            ).fetchall()
        for tf, *bar in rows:
            frames[tf].append(Bar(*bar))
    return frames


class CausalDailyStream:
    """Precomputed O(1) causal daily metrics + 1D Master red resistance (only closed days <= bar.end)."""

    def __init__(self, symbol, daily_bars):
        self.bars = daily_bars
        self.ends = [b.end for b in daily_bars]
        self.metrics = []
        if not daily_bars:
            return
        gaps = source_gaps(daily_bars, daily_bars[-1].end, "1D")
        gap_prefix = [0]
        for i in range(len(daily_bars)):
            gap_prefix.append(gap_prefix[-1] + int(i in gaps))
        close_sums = [0.0]
        vol_sums = [0.0]
        dvol_sums = [0.0]
        for b in daily_bars:
            close_sums.append(close_sums[-1] + b.close)
            vol_sums.append(vol_sums[-1] + b.volume)
            dvol_sums.append(dvol_sums[-1] + b.volume * b.close)

        # Single streaming pass for Wilder 14-day ATR + 1D MasterEngine red resistance
        eng_1d = create_engine(symbol, "1D", profile("master"))
        atr_1d = None
        tr_seed = []
        prev = None
        for i, bar in enumerate(daily_bars):
            if i in gaps:
                atr_1d = None
                tr_seed.clear()
                prev = None
                eng_1d.reset_history()
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

            eng_1d.push(bar)
            snap_1d = eng_1d.snapshot()
            daily_red = None
            if snap_1d.get("ready"):
                vals = [
                    ln["value"]
                    for ln in snap_1d.get("reds", [])
                    if ln.get("valid") and hs._finite(ln.get("value")) and ln["value"] > bar.close
                ]
                daily_red = min(vals) if vals else None

            count = i + 1
            sma200 = None
            if count >= 200 and gap_prefix[count] - gap_prefix[count - 200 + 1] == 0:
                sma200 = (close_sums[count] - close_sums[count - 200]) / 200.0
            sma50 = None
            if count >= 50 and gap_prefix[count] - gap_prefix[count - 50 + 1] == 0:
                sma50 = (close_sums[count] - close_sums[count - 50]) / 50.0
            w20 = min(20, count)
            avg_vol_20 = (vol_sums[count] - vol_sums[count - w20]) / w20
            avg_dvol_20 = (dvol_sums[count] - dvol_sums[count - w20]) / w20
            above_sma200 = None if sma200 is None else bool(bar.close >= sma200)
            atr_1d_pct = (100.0 * atr_1d / bar.close) if (atr_1d is not None and bar.close > 0) else None
            self.metrics.append({
                "daily_close": bar.close,
                "daily_sma50": sma50,
                "daily_sma200": sma200,
                "above_sma200": above_sma200,
                "avg_vol_20": avg_vol_20,
                "avg_dollar_vol_20": avg_dvol_20,
                "atr_1d_pct": atr_1d_pct,
                "daily_red": daily_red,
            })

    def at(self, cutoff):
        pos = bisect_right(self.ends, cutoff) - 1
        if pos < 0:
            return {
                "daily_close": None, "daily_sma50": None, "daily_sma200": None,
                "above_sma200": None, "avg_vol_20": 0.0, "avg_dollar_vol_20": 0.0,
                "atr_1d_pct": None, "daily_red": None,
            }
        return self.metrics[pos]


def _split_for_day(day_str, splits):
    for name, (start, end) in splits.items():
        if start <= day_str <= end:
            return name
    return None


def _session_closing_indices(bars_4h):
    """Return set of bar indices that are the final closed 4h bar of their NY trading day."""
    last_by_day = {}
    for i, bar in enumerate(bars_4h):
        last_by_day[trading_day(bar.end)] = i
    return set(last_by_day.values())


def _active_universes_on(day_str, default_universes, pit_intervals):
    if pit_intervals is None:
        return default_universes
    return {
        u_name
        for u_name, ivs in pit_intervals.items()
        if any(s <= day_str <= e for s, e in ivs)
    }


def backtest_symbol(
    symbol,
    bars_4h,
    bars_1d,
    bars_5m,
    *,
    dataset_id,
    universes,
    splits,
    outcome_cutoff,
    capital_eur=1000.0,
    max_watch_sessions=20,
    pit_intervals=None,
):
    """Single-pass strictly causal streaming backtest for one symbol."""
    if not bars_4h or not bars_1d or not bars_5m:
        return {"symbol": symbol, "datasetId": dataset_id, "status": "no_bars", "trades": [], "watches": 0}

    rows_4h = [b for b in bars_4h if b.end <= outcome_cutoff]
    rows_1d = [b for b in bars_1d if b.end <= outcome_cutoff]
    rows_5m = [b for b in bars_5m if b.end <= outcome_cutoff]
    if len(rows_4h) < 40 or len(rows_5m) < 40:
        return {"symbol": symbol, "datasetId": dataset_id, "status": "insufficient_bars", "trades": [], "watches": 0}

    daily_stream = CausalDailyStream(symbol, rows_1d)
    rules = profile("master")
    watch_rules = WatchRules(arm_bars=2, retest_bars=16, stop_buffer_pct=0.3)
    gaps_4h = source_gaps(rows_4h, rows_4h[-1].end, "4h")
    observer = PilotObserver(symbol, rules=rules, watch=watch_rules)
    lineage = Episodes(symbol)
    session_closes = _session_closing_indices(rows_4h)

    history = []          # (idx, bar, atr)
    broken_reds = {}      # scenarioId -> break info
    timeline = []         # canonical timeline for exit_followup / signal_path_index
    seen_episodes = set() # (lineage_key, entry_source_family) deduplication
    active_watches = {}   # lineage_key -> watched pre-breakout setup
    raw_cases = []        # list of causal entry cases before 5m execution
    watch_count = 0
    prev_bar = None
    first_4h_time = rows_4h[0].time

    for i, bar in enumerate(rows_4h):
        gap_here = i in gaps_4h
        if gap_here:
            observer.gap(bar)
            history.clear()
            broken_reds.clear()
            active_watches.clear()
            lineage = Episodes(symbol)
            prev_bar = None

        events, signals, snap = observer.push(bar)
        if not snap or not snap.get("ready") or not hs._finite(snap.get("atr")) or snap["atr"] <= 0:
            prev_bar = bar
            continue

        idx = snap["referenceIndex"]
        atr = snap["atr"]
        history.append((idx, bar, atr))
        if len(history) > rules.max_bars:
            history.pop(0)
        lineage.observe(snap)

        timeline.append({
            "closedAt": bar.end,
            "index": idx,
            "close": bar.close,
            "green": deepcopy(snap.get("green")),
            "gapAt": bar.time if gap_here else None,
        })

        for ev in events:
            if ev["kind"] == "break":
                ln = deepcopy(ev["line"])
                broken_reds[ev["scenarioId"]] = {
                    "scenarioId": ev["scenarioId"],
                    "line": ln,
                    "breakIndex": idx,
                    "breakAt": bar.end,
                    "breakAgeDays": hs._line_age_days(ln, bar.end),
                    "breakContactSpanDays": hs._contact_span_days(ln),
                }
        for sid in [k for k, v in broken_reds.items() if idx - v["breakIndex"] > 16]:
            del broken_reds[sid]

        bar_day = trading_day(bar.end)
        # 1) Check active pre-breakout watches on EVERY closed 4h bar for causal entry trigger
        cur_green = snap.get("green")
        for wkey in list(active_watches):
            w = active_watches[wkey]
            if bar_day > w["lastDay"]:
                w["sessionsElapsed"] += 1
                w["lastDay"] = bar_day
            w_red = w["red"]
            w_green = w["green"]
            g_proj = price_at(w_green, idx)
            if bar.close <= g_proj * 0.997:
                del active_watches[wkey]
                continue
            r_proj = price_at(w_red, idx)
            use_green = (
                cur_green
                if (cur_green and cur_green["slope"] > 0 and 0 < price_at(cur_green, idx) < bar.close)
                else (w_green if 0 < g_proj < bar.close else None)
            )
            g_val = price_at(use_green, idx) if use_green else None
            stop_val = hs.stop_price(g_val, buffer_pct=0.3, tick=rules.tick) if g_val else None
            triggered = False
            if stop_val and 0 < stop_val < bar.close:
                rpct = 100.0 * (bar.close - stop_val) / bar.close
                ratr = (bar.close - stop_val) / atr
                if 1.8 <= rpct <= 9.5 and ratr >= 1.0:
                    if w["scenario"] == "4B_RETEST_APPROACH":
                        prev_low = prev_bar.low if prev_bar else bar.low
                        if min(bar.low, prev_low) <= r_proj + 0.30 * atr and bar.close >= r_proj and bar.close > bar.open:
                            triggered = True
                    elif bar.close >= r_proj + 0.15 * atr:
                        triggered = True
            if triggered:
                sig_id = stable_id([VERSION, symbol, "watch_entry", w["watchId"], bar.end])
                raw_cases.append({
                    "id": sig_id,
                    "symbol": symbol,
                    "split": w["split"],
                    "year": w["day"][:4],
                    "entryDay": bar_day,
                    "watchDay": w["day"],
                    "entrySource": "watch_to_entry",
                    "scenario": w["scenario"],
                    "features": w["features"],
                    "signal": {
                        "id": sig_id,
                        "symbol": symbol,
                        "family": "red_retest" if w["scenario"] == "4B_RETEST_APPROACH" else "breakout",
                        "signalAt": bar.end,
                        "signalClose": bar.close,
                        "line": deepcopy(w_red),
                        "safety": deepcopy(use_green),
                        "initialStop": stop_val,
                    },
                })
                del active_watches[wkey]
            elif w["sessionsElapsed"] >= max_watch_sessions:
                del active_watches[wkey]

        # 2) At the final closed 4h bar of each trading session, run exact Hermes Scanner gates
        split = _split_for_day(bar_day, splits)
        if i not in session_closes or split is None:
            prev_bar = bar
            continue
        day_universes = _active_universes_on(bar_day, universes, pit_intervals)
        if not day_universes:
            prev_bar = bar
            continue
        if (bar.end - first_4h_time) < 320 * 86400:
            prev_bar = bar
            continue

        dstats = daily_stream.at(bar.end)
        close_4h = bar.close
        if close_4h < 20.0 or (dstats["avg_vol_20"] < 1_000_000 and dstats["avg_dollar_vol_20"] < 40_000_000):
            prev_bar = bar
            continue
        if not hs._check_green_gate(cur_green, close_4h, bar.end, history, idx, rules):
            prev_bar = bar
            continue

        green_now = price_at(cur_green, idx)
        stop0 = hs.stop_price(green_now, buffer_pct=0.3, tick=rules.tick)
        if not stop0 or stop0 >= close_4h:
            prev_bar = bar
            continue

        reds = snap.get("reds", [])
        greens = snap.get("greens", [])
        above_sma200 = dstats["above_sma200"]
        strategy_tag = "TREND_FOLLOW" if above_sma200 is True else "REVERSAL" if above_sma200 is False else "UNKNOWN"
        atr_1d_pct = dstats["atr_1d_pct"]
        daily_red_val = dstats["daily_red"]
        bars_tail = [(h_idx, h_bar) for h_idx, h_bar, _ in history[-6:]]

        def _make_features(scenario, red, *, comp_ratio, width_now, active_appr):
            red_now = price_at(red, idx)
            trig1 = (red_now + red["slope"]) + 0.15 * atr
            entry_ref = close_4h if scenario in ("1A_CLEAN_BREAKOUT", "4A_RETEST_TRIGGER") else max(trig1, close_4h)
            unit_risk = entry_ref - stop0
            if unit_risk <= 0:
                return None
            risk_pct = 100.0 * unit_risk / entry_ref
            risk_atr = unit_risk / atr
            width_atr = (width_now / atr) if hs._finite(width_now) else None
            red_age = hs._line_age_days(red, bar.end)
            red_cspan = hs._contact_span_days(red)
            roof_r, roof_near, clear_sky = hs._overhead_roof(red, reds, daily_red_val, idx, entry_ref, unit_risk)
            score, comp_flag, low_vol = hs._compute_score(
                active_approach=active_appr,
                compression_ratio=comp_ratio,
                width_atr=width_atr,
                red_age_days=red_age,
                red_contacts=red["contacts"],
                red_origin=red.get("origin", "pivot"),
                risk_pct=risk_pct,
                risk_atr=risk_atr,
                universes=day_universes,
                atr_1d_pct=atr_1d_pct,
                clear_sky=clear_sky,
            )
            return {
                "score": score,
                "strategy_tag": strategy_tag,
                "above_sma200": above_sma200,
                "active_approach": bool(active_appr),
                "compression": bool(comp_flag),
                "high_maturity": bool(red_age >= 21.0 or red["contacts"] >= 4),
                "red_origin": red.get("origin", "pivot"),
                "stop_sweet_spot": bool(2.2 <= risk_pct <= 5.5 and 1.2 <= risk_atr <= 2.5),
                "high_beta": bool(("nasdaq100" in day_universes) or (hs._finite(atr_1d_pct) and atr_1d_pct >= 2.8)),
                "clear_sky": bool(clear_sky),
                "overhead_roof_near": bool(roof_near),
                "low_daily_volatility": bool(low_vol),
                "risk_pct": round(risk_pct, 2),
                "risk_atr": round(risk_atr, 2),
                "red_contacts": int(red["contacts"]),
                "red_age_days": round(red_age, 1),
                "red_contact_span_days": round(red_cspan, 1),
                "green_contacts": int(cur_green["contacts"]),
                "atr_1d_pct": round(atr_1d_pct, 2) if hs._finite(atr_1d_pct) else None,
                "universes": "|".join(sorted(day_universes)),
                "close_4h": round(close_4h, 4),
                "stop_0_3_pct": stop0,
            }

        day_hits = []
        # Broken qualified reds: 1A, 1B, 4A, 4B
        for b_info in broken_reds.values():
            red = b_info["line"]
            bars_since = idx - b_info["breakIndex"]
            if red["contacts"] < 3 or red["slope"] >= 0:
                continue
            if b_info["breakAgeDays"] < 10.0 or b_info["breakContactSpanDays"] < 7.0:
                continue
            if hs._has_body_violation(red, history, b_info["breakIndex"] - 1, rules, upper_exclude_tail=0):
                continue
            conv_ok, comp_ratio, width_brk = hs._check_convergence(red, cur_green, b_info["breakIndex"])
            if not conv_ok:
                continue
            red_now = price_at(red, idx)
            if bars_since <= 1 and close_4h > red_now:
                rpct = 100.0 * (close_4h - stop0) / close_4h
                ratr = (close_4h - stop0) / atr
                apex = ratr < 0.6 and rpct >= 1.0
                if (apex or (ratr >= 1.0 and rpct >= 2.0)) and rpct <= 8.5 and ratr <= 3.8:
                    if close_4h >= red_now + 0.15 * atr and close_4h <= red_now + 1.2 * atr:
                        f = _make_features("1A_CLEAN_BREAKOUT", red, comp_ratio=comp_ratio, width_now=width_brk, active_appr=True)
                        if f:
                            day_hits.append(("1A_CLEAN_BREAKOUT", red, f))
                    elif close_4h < red_now + 0.15 * atr:
                        f = _make_features("1B_ARMED_WAIT_CLEAN", red, comp_ratio=comp_ratio, width_now=width_brk, active_appr=True)
                        if f:
                            day_hits.append(("1B_ARMED_WAIT_CLEAN", red, f))
            if 2 <= bars_since <= 16:
                dist = (close_4h - red_now) / atr
                if -0.15 <= dist <= 0.75:
                    rpct = 100.0 * (close_4h - stop0) / close_4h
                    ratr = (close_4h - stop0) / atr
                    apex = ratr < 0.6 and rpct >= 1.0
                    if (apex or (ratr >= 1.0 and rpct >= 1.8)) and rpct <= 10.0:
                        prev_low = prev_bar.low if prev_bar else bar.low
                        if min(bar.low, prev_low) <= red_now + 0.30 * atr and close_4h >= red_now and bar.close > bar.open:
                            f = _make_features("4A_RETEST_TRIGGER", red, comp_ratio=comp_ratio, width_now=width_brk, active_appr=True)
                            if f:
                                day_hits.append(("4A_RETEST_TRIGGER", red, f))
                        elif len(history) >= 3 and close_4h < history[-3][1].close and 0.20 <= dist <= 0.75:
                            f = _make_features("4B_RETEST_APPROACH", red, comp_ratio=comp_ratio, width_now=width_brk, active_appr=False)
                            if f:
                                day_hits.append(("4B_RETEST_APPROACH", red, f))

        # Active reds above close: 2_IMMEDIATE_TEST, 3_APPROACH_WATCH
        for red in reds:
            if not red.get("valid") or red["slope"] >= 0 or red["contacts"] < 3:
                continue
            red_now = price_at(red, idx)
            if not (green_now < close_4h <= red_now):
                continue
            if hs._line_age_days(red, bar.end) < 10.0 or hs._contact_span_days(red) < 7.0:
                continue
            if hs._has_body_violation(red, history, idx, rules, upper_exclude_tail=2):
                continue
            conv_ok, comp_ratio, width_now = hs._check_convergence(red, cur_green, idx)
            if not conv_ok:
                continue
            dist_atr = (red_now - close_4h) / atr
            rc_pct = 100.0 * (close_4h - stop0) / close_4h
            rc_atr = (close_4h - stop0) / atr
            trig_b = (red_now + red["slope"]) + 0.15 * atr
            rb_pct = 100.0 * (trig_b - stop0) / trig_b if trig_b > 0 else 999.0
            rb_atr = (trig_b - stop0) / atr
            apex = rc_atr < 0.6 and rb_pct >= 1.0
            if not ((apex or (rc_atr >= 1.0 and rc_pct >= 1.8 and rb_pct >= 2.0)) and rb_pct <= 8.5 and rb_atr <= 3.8):
                continue
            active_appr = hs._active_approach(red, bars_tail, idx, atr)
            comp_watch = (hs._finite(comp_ratio) and comp_ratio <= 0.50) or (hs._finite(width_now) and width_now / atr <= 2.5)
            if dist_atr <= 0.40 or bar.high >= red_now - 0.15 * atr:
                f = _make_features("2_IMMEDIATE_TEST", red, comp_ratio=comp_ratio, width_now=width_now, active_appr=active_appr)
                if f:
                    day_hits.append(("2_IMMEDIATE_TEST", red, f))
            elif 0.40 < dist_atr <= 0.85 and (active_appr or comp_watch):
                f = _make_features("3_APPROACH_WATCH", red, comp_ratio=comp_ratio, width_now=width_now, active_appr=active_appr)
                if f:
                    day_hits.append(("3_APPROACH_WATCH", red, f))

        if day_hits:
            day_hits.sort(key=lambda item: (hs.SCENARIO_ORDER.get(item[0], 99), -item[2]["score"]))
            scenario, red, feats = day_hits[0]
            anc = lineage.lines.get(red["id"]) or stable_id(["red", red["a_time"], red["a_price"]])
            if scenario in ("1A_CLEAN_BREAKOUT", "4A_RETEST_TRIGGER"):
                dedup_key = (anc, scenario)
                if dedup_key not in seen_episodes:
                    seen_episodes.add(dedup_key)
                    sig_id = stable_id([VERSION, symbol, scenario, bar.end, red["id"]])
                    raw_cases.append({
                        "id": sig_id,
                        "symbol": symbol,
                        "split": split,
                        "year": bar_day[:4],
                        "entryDay": bar_day,
                        "watchDay": bar_day,
                        "entrySource": "direct_1A" if scenario == "1A_CLEAN_BREAKOUT" else "direct_4A",
                        "scenario": scenario,
                        "features": feats,
                        "signal": {
                            "id": sig_id,
                            "symbol": symbol,
                            "family": "breakout" if scenario == "1A_CLEAN_BREAKOUT" else "red_retest",
                            "signalAt": bar.end,
                            "signalClose": close_4h,
                            "line": deepcopy(red),
                            "safety": deepcopy(cur_green),
                            "initialStop": stop0,
                        },
                    })
            else:
                dedup_key = (anc, "watch")
                if dedup_key not in seen_episodes and anc not in active_watches:
                    seen_episodes.add(dedup_key)
                    watch_count += 1
                    active_watches[anc] = {
                        "watchId": stable_id([VERSION, symbol, "watch", bar.end, red["id"]]),
                        "split": split,
                        "day": bar_day,
                        "lastDay": bar_day,
                        "sessionsElapsed": 0,
                        "scenario": scenario,
                        "red": deepcopy(red),
                        "green": deepcopy(cur_green),
                        "features": feats,
                    }
        prev_bar = bar

    # --- Execute all collected causal cases on the single 5m PathIndex ---
    if not raw_cases:
        return {"symbol": symbol, "datasetId": dataset_id, "status": "ok", "trades": [], "watches": watch_count}

    exec_rules = CaseExecution(
        notional=capital_eur,
        latency_seconds=300,
        spread_bps=5.0,
        slippage_bps=5.0,
        fee_per_order=0.0,
        buffer_pct=0.3,
        tick=0.01,
    )
    first_sig_at = min(c["signal"]["signalAt"] for c in raw_cases)
    fine_relevant = [b for b in rows_5m if b.time >= first_sig_at - 86400]
    path_idx = PathIndex(fine_relevant, outcome_cutoff, start=first_sig_at)

    trades = []
    for case in raw_cases:
        sig = case["signal"]
        entry = isolated_entry(sig, path_idx, exec_rules)
        outcomes = {}
        if entry["status"] == "filled":
            for pol in STOP_POLICIES:
                if pol in ("r2_fan", "qualified_fan"):
                    proj_tl, r2_at = policy_timeline({"signal": sig, "entry": entry}, timeline, pol)
                    res = execute_unbounded(sig, entry, path_idx, proj_tl, "fan_safety")
                else:
                    r2_at = None
                    res = execute_unbounded(sig, entry, path_idx, timeline, "original_safety")
                if res["status"] == "closed":
                    pnl = round(res["netPnl"], 2)
                    ret = round(res["netReturnPct"], 2)
                    r_val = round(res["netR"], 3)
                    days_held = round(res["holdingCalendarDays"], 1)
                else:
                    pnl = round(res["markNetPnl"], 2) if res.get("markNetPnl") is not None else None
                    ret = round(res["markNetReturnPct"], 2) if res.get("markNetReturnPct") is not None else None
                    r_val = (
                        round(res["markNetPnl"] / entry["plannedRisk"], 3)
                        if (res.get("markNetPnl") is not None and entry.get("plannedRisk"))
                        else None
                    )
                    days_held = round(((res.get("lastObservedAt") or outcome_cutoff) - entry["entryAt"]) / 86400.0, 1)
                r2_during_trade = bool(
                    r2_at is not None and (res.get("exitAt") is None or r2_at < res["exitAt"])
                )
                outcomes[pol] = {
                    "status": res["status"],
                    "reason": res.get("reason"),
                    "pnlEur": pnl,
                    "returnPct": ret,
                    "netR": r_val,
                    "mfeR": round(res["mfeR"], 2) if res.get("mfeR") is not None else None,
                    "maeR": round(res["maeR"], 2) if res.get("maeR") is not None else None,
                    "r2Activated": r2_during_trade,
                    "holdingDays": days_held,
                }
        trades.append({
            "id": case["id"],
            "symbol": symbol,
            "split": case["split"],
            "year": case["year"],
            "watchDay": case["watchDay"],
            "entryDay": case["entryDay"],
            "entrySource": case["entrySource"],
            "scenario": case["scenario"],
            "entryStatus": entry["status"],
            "entryReason": entry.get("reason"),
            "entryPrice": round(entry["entryPrice"], 4) if entry.get("entryPrice") is not None else None,
            "initialStop": entry.get("initialStop"),
            "features": case["features"],
            "outcomes": outcomes,
        })

    return {
        "symbol": symbol,
        "datasetId": dataset_id,
        "status": "ok",
        "watches": watch_count,
        "trades": trades,
    }


def _worker_task(args):
    sym, ds_meta, splits, outcome_cutoff, capital_eur, max_watch, data_root_str, block_path_str = args
    t0 = time.monotonic()
    try:
        frames = _read_all_frames(ds_meta["datasetId"], outcome_cutoff, root=data_root_str)
        res = backtest_symbol(
            sym,
            frames["4h"],
            frames["1D"],
            frames["5m"],
            dataset_id=ds_meta["datasetId"],
            universes=set(ds_meta["universes"]),
            splits={k: tuple(v) for k, v in splits.items()},
            outcome_cutoff=outcome_cutoff,
            capital_eur=capital_eur,
            max_watch_sessions=max_watch,
            pit_intervals=ds_meta.get("pitIntervals"),
        )
        res["elapsedSeconds"] = round(time.monotonic() - t0, 2)
    except (DataError, ParquetError, OSError, ValueError, KeyError) as exc:
        res = {"symbol": sym, "datasetId": ds_meta["datasetId"], "status": "error", "error": str(exc), "trades": [], "watches": 0}
    _atomic_write_json(block_path_str, res)
    return sym, res["status"], len(res.get("trades", [])), res.get("elapsedSeconds", 0.0)


def run_study(
    output_dir,
    *,
    universe="all",
    symbols=None,
    splits=None,
    outcome_cutoff=DEFAULT_OUTCOME_CUTOFF,
    capital_eur=1000.0,
    max_watch_sessions=20,
    pit_membership_path=None,
    workers=4,
    resume=True,
    root=None,
    progress=None,
):
    """Execute or resume a multi-year scanner backtest into a dedicated artifacts folder."""
    out = Path(output_dir)
    data_root = Path(root) if root else data_dir()
    with study_lock(out / ".run"):
        plan = prepare_plan(
            out,
            universe=universe,
            symbols=symbols,
            splits=splits,
            outcome_cutoff=outcome_cutoff,
            capital_eur=capital_eur,
            max_watch_sessions=max_watch_sessions,
            pit_membership_path=pit_membership_path,
            root=data_root,
        )
        tasks = []
        skipped = 0
        for sym in plan["symbols"]:
            bpath = out / "blocks" / f"{sym}.json"
            if resume and bpath.is_file():
                skipped += 1
                continue
            tasks.append((
                sym,
                plan["datasets"][sym],
                plan["splits"],
                plan["outcomeCutoff"],
                plan["capitalEur"],
                plan["maxWatchSessions"],
                str(data_root),
                str(bpath),
            ))

        t0 = time.monotonic()
        done = 0
        errors = 0
        if workers <= 1 or len(tasks) <= 1:
            for item in tasks:
                sym, st, cnt, sec = _worker_task(item)
                done += 1
                if st == "error":
                    errors += 1
                if progress:
                    progress(done + skipped, len(plan["symbols"]), sym, st, cnt, sec)
        else:
            with ProcessPoolExecutor(max_workers=workers) as pool:
                futs = [pool.submit(_worker_task, item) for item in tasks]
                for fut in as_completed(futs):
                    sym, st, cnt, sec = fut.result()
                    done += 1
                    if st == "error":
                        errors += 1
                    if progress:
                        progress(done + skipped, len(plan["symbols"]), sym, st, cnt, sec)

        return {
            "planId": plan["id"],
            "outputDir": str(out),
            "totalSymbols": len(plan["symbols"]),
            "skippedResume": skipped,
            "processedNow": done,
            "errors": errors,
            "elapsedSeconds": round(time.monotonic() - t0, 2),
        }


def _aggregate_group(rows, policy="r2_fan"):
    """Compute honest performance & robustness metrics (incl. ex-Top-3-winners!)."""
    filled = [r for r in rows if r["entryStatus"] == "filled" and policy in r["outcomes"]]
    closed = [r for r in filled if r["outcomes"][policy]["status"] == "closed"]
    opened = [r for r in filled if r["outcomes"][policy]["status"] == "open"]
    censored = [r for r in filled if r["outcomes"][policy]["status"] == "censored"]

    eval_rows = closed + opened  # closed + open mark-to-market; censored excluded honestly
    pnls = [r["outcomes"][policy]["pnlEur"] for r in eval_rows if r["outcomes"][policy]["pnlEur"] is not None]
    r_vals = [r["outcomes"][policy]["netR"] for r in eval_rows if r["outcomes"][policy]["netR"] is not None]
    closed_r = [r["outcomes"][policy]["netR"] for r in closed if r["outcomes"][policy]["netR"] is not None]
    wins = sum(1 for r in closed if (r["outcomes"][policy]["pnlEur"] or 0) > 0)
    r2_hits = sum(1 for r in eval_rows if r["outcomes"][policy].get("r2Activated"))

    ex_top3_r = None
    if len(r_vals) > 3:
        trimmed = sorted(r_vals)[:-3]
        ex_top3_r = round(sum(trimmed) / len(trimmed), 3)

    return {
        "signals": len(rows),
        "filled": len(filled),
        "closed": len(closed),
        "open": len(opened),
        "censored": len(censored),
        "winRatePct": round(100.0 * wins / len(closed), 1) if closed else None,
        "totalPnlEur": round(sum(pnls), 2),
        "avgPnlEur": round(sum(pnls) / len(pnls), 2) if pnls else None,
        "avgR": round(sum(r_vals) / len(r_vals), 3) if r_vals else None,
        "medianR": round(statistics.median(r_vals), 3) if r_vals else None,
        "avgRExTop3": ex_top3_r,
        "closedAvgR": round(sum(closed_r) / len(closed_r), 3) if closed_r else None,
        "r2RatePct": round(100.0 * r2_hits / len(eval_rows), 1) if eval_rows else None,
    }


def _risk_bin(pct):
    if pct is None:
        return "unbekannt"
    if pct < 2.5:
        return "<2,5%"
    if pct < 4.0:
        return "2,5–4,0%"
    if pct < 6.0:
        return "4,0–6,0%"
    return "6,0–8,5%+"


def _risk_atr_bin(atr):
    if atr is None:
        return "unbekannt"
    if atr < 1.5:
        return "<1,5 ATR"
    if atr < 2.5:
        return "1,5–2,5 ATR"
    if atr < 3.5:
        return "2,5–3,5 ATR"
    return ">=3,5 ATR"


def _score_bin(score):
    if score <= 5:
        return "0–5 Punkte"
    if score <= 7:
        return "6–7 Punkte"
    if score == 8:
        return "8 Punkte"
    if score == 9:
        return "9 Punkte"
    return "10 Punkte"


def build_report(output_dir, *, policy="r2_fan", reveal_holdout=False):
    """Aggregate all completed symbol blocks into report.md, feature-comparison.csv & trades.csv."""
    out = Path(output_dir)
    plan = _load_plan(out, verify_engine=False)
    if plan is None:
        raise DataError(f"Kein Studienplan unter {out} gefunden.", 404)

    blocks_dir = out / "blocks"
    all_trades = []
    block_counts = Counter()
    total_watches = 0
    for sym in plan["symbols"]:
        bp = blocks_dir / f"{sym}.json"
        if not bp.is_file():
            block_counts["missing_block"] += 1
            continue
        data = json.loads(bp.read_text("utf-8"))
        block_counts[data.get("status", "unknown")] += 1
        total_watches += data.get("watches", 0)
        all_trades.extend(data.get("trades", []))

    allowed_splits = ("train", "validation", "holdout") if reveal_holdout else ("train", "validation")
    visible = [t for t in all_trades if t["split"] in allowed_splits]
    hidden_holdout = sum(1 for t in all_trades if t["split"] == "holdout") if not reveal_holdout else 0

    # Write trades.csv (only visible splits!)
    trades_csv = out / "trades.csv"
    trade_fields = [
        "id", "symbol", "split", "year", "watchDay", "entryDay", "entrySource", "scenario",
        "entryStatus", "entryPrice", "initialStop",
        "score", "strategy_tag", "active_approach", "compression", "high_maturity",
        "red_origin", "stop_sweet_spot", "high_beta", "clear_sky", "overhead_roof_near",
        "low_daily_volatility", "risk_pct", "risk_atr", "red_contacts", "red_age_days",
        "green_contacts", "universes",
        f"{policy}_status", f"{policy}_pnl_eur", f"{policy}_ret_pct", f"{policy}_net_r",
        f"{policy}_mfe_r", f"{policy}_mae_r", f"{policy}_r2", f"{policy}_days",
    ]
    with trades_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=trade_fields)
        writer.writeheader()
        for t in visible:
            f = t["features"]
            o = t["outcomes"].get(policy, {})
            writer.writerow({
                "id": t["id"], "symbol": t["symbol"], "split": t["split"], "year": t["year"],
                "watchDay": t["watchDay"], "entryDay": t["entryDay"], "entrySource": t["entrySource"],
                "scenario": t["scenario"], "entryStatus": t["entryStatus"],
                "entryPrice": t["entryPrice"], "initialStop": t["initialStop"],
                **{k: f.get(k) for k in (
                    "score", "strategy_tag", "active_approach", "compression", "high_maturity",
                    "red_origin", "stop_sweet_spot", "high_beta", "clear_sky", "overhead_roof_near",
                    "low_daily_volatility", "risk_pct", "risk_atr", "red_contacts", "red_age_days",
                    "green_contacts", "universes",
                )},
                f"{policy}_status": o.get("status"),
                f"{policy}_pnl_eur": o.get("pnlEur"),
                f"{policy}_ret_pct": o.get("returnPct"),
                f"{policy}_net_r": o.get("netR"),
                f"{policy}_mfe_r": o.get("mfeR"),
                f"{policy}_mae_r": o.get("maeR"),
                f"{policy}_r2": o.get("r2Activated"),
                f"{policy}_days": o.get("holdingDays"),
            })

    # Build feature comparison rows per split
    comp_rows = []

    def add_section(split_name, section, group_fn, order=None):
        subset = [t for t in visible if t["split"] == split_name]
        buckets = defaultdict(list)
        for t in subset:
            buckets[group_fn(t)].append(t)
        keys = order if order else sorted(buckets)
        for key in keys:
            if key not in buckets:
                continue
            stats = _aggregate_group(buckets[key], policy=policy)
            comp_rows.append({"split": split_name, "kategorie": section, "gruppe": key, **stats})

    for sp in allowed_splits:
        add_section(sp, "Gesamt", lambda t: "Alle qualifizierten Einstiege")
        add_section(sp, "Einstiegs-Quelle", lambda t: t["entrySource"], ["direct_1A", "direct_4A", "watch_to_entry"])
        add_section(sp, "Szenario", lambda t: t["scenario"])
        add_section(
            sp, "Punktzahl", lambda t: _score_bin(t["features"]["score"]),
            ["0–5 Punkte", "6–7 Punkte", "8 Punkte", "9 Punkte", "10 Punkte"],
        )
        add_section(sp, "Kriterium: Aktive Annäherung", lambda t: "Ja" if t["features"]["active_approach"] else "Nein", ["Ja", "Nein"])
        add_section(sp, "Kriterium: Starke Kompression", lambda t: "Ja" if t["features"]["compression"] else "Nein", ["Ja", "Nein"])
        add_section(sp, "Kriterium: Hohe Reife (>=21T/4K)", lambda t: "Ja" if t["features"]["high_maturity"] else "Nein", ["Ja", "Nein"])
        add_section(sp, "Kriterium: Linien-Typ", lambda t: t["features"]["red_origin"], ["pivot", "refit"])
        add_section(sp, "Kriterium: Stop-Sweet-Spot", lambda t: "Ja" if t["features"]["stop_sweet_spot"] else "Nein", ["Ja", "Nein"])
        add_section(sp, "Kriterium: Nasdaq-100 / High-Beta", lambda t: "Ja" if t["features"]["high_beta"] else "Nein", ["Ja", "Nein"])
        add_section(sp, "Kriterium: Freie Bahn (clear_sky)", lambda t: "Ja" if t["features"]["clear_sky"] else "Nein", ["Ja", "Nein"])
        add_section(sp, "Trend-Kontext (SMA200)", lambda t: t["features"]["strategy_tag"], ["TREND_FOLLOW", "REVERSAL", "UNKNOWN"])
        add_section(sp, "Nahes Widerstandsdach (<1,5R)", lambda t: "Ja" if t["features"]["overhead_roof_near"] else "Nein", ["Ja", "Nein"])
        add_section(sp, "Niedrige Tages-Vola (<1,5% ATR)", lambda t: "Ja" if t["features"].get("low_daily_volatility") else "Nein", ["Ja", "Nein"])
        add_section(sp, "Stop-Abstand (%)", lambda t: _risk_bin(t["features"]["risk_pct"]), ["<2,5%", "2,5–4,0%", "4,0–6,0%", "6,0–8,5%+"])
        add_section(sp, "Stop-Abstand (ATR)", lambda t: _risk_atr_bin(t["features"].get("risk_atr")), ["<1,5 ATR", "1,5–2,5 ATR", "2,5–3,5 ATR", ">=3,5 ATR"])
        add_section(sp, "Kalenderjahr", lambda t: t["year"])

    # Also compare all 3 stop policies on train & validation
    policy_rows = []
    for sp in allowed_splits:
        subset = [t for t in visible if t["split"] == sp]
        for pol in STOP_POLICIES:
            policy_rows.append({"split": sp, "stop_modell": pol, **_aggregate_group(subset, policy=pol)})

    comp_csv = out / "feature-comparison.csv"
    comp_fields = [
        "split", "kategorie", "gruppe", "signals", "filled", "closed", "open", "censored",
        "winRatePct", "totalPnlEur", "avgPnlEur", "avgR", "medianR", "avgRExTop3", "closedAvgR", "r2RatePct",
    ]
    with comp_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=comp_fields)
        writer.writeheader()
        writer.writerows(comp_rows)

    # Render clean German Markdown report
    def _fmt(v, suffix="", dec=2):
        if v is None:
            return "–"
        return f"{v:.{dec}f}".replace(".", ",") + suffix

    def _fmts(v, suffix="", dec=2):
        if v is None:
            return "–"
        return ("+" if v > 0 else "") + f"{v:.{dec}f}".replace(".", ",") + suffix

    pit_mode = (
        f"Point-in-Time (Dow 30 + Nasdaq-100 + S&P 500 2016–2026; `{len(plan['symbols'])}` mit Daten, `{len(plan.get('missingSymbols', []))}` fehlend)"
        if plan.get("pointInTime")
        else "Heutige Index-Bestände (Survivorship-Bias)"
    )
    md = [
        f"# 📊 Scanner-Backtest & Kriterien-Vergleich (Weg B)",
        "",
        f"- **Studien-ID:** `{plan['id'][:16]}` · **Universum-Modus:** {pit_mode}",
        f"- **Stop-Modell im Fokus:** `{policy}` · **Kapital je Trade:** `{plan['capitalEur']:.0f} €` (nominal)",
        f"- **Aktien-Blöcke:** `{block_counts.get('ok', 0)}` ok / `{len(plan['symbols'])}` gesamt (Fehler: `{block_counts.get('error', 0)}`, fehlend: `{block_counts.get('missing_block', 0)}`)",
        f"- **Zeiträume:** `train` = `{plan['splits']['train'][0]} .. {plan['splits']['train'][1]}` | `validation` = `{plan['splits']['validation'][0]} .. {plan['splits']['validation'][1]}` | `holdout` = `{plan['splits']['holdout'][0]} .. {plan['splits']['holdout'][1]}` (Nachbeobachtung bis `{plan['outcomeCutoffSession']}`)",
    ]
    if hidden_holdout:
        md.append(
            f"- **Holdout-Schutz aktiv:** `{hidden_holdout}` Holdout-Fälle sind im Bericht ausgeblendet (erst per `--reveal-holdout` für die einmalige Gegenprobe öffnen)."
        )
    pit_note = (
        "Point-in-Time-Mitgliedschaft (Dow 30, Nasdaq-100 & S&P 500 inkl. historischer/delisteter Ex-Mitglieder, ohne Survivorship-Bias)"
        if plan.get("pointInTime")
        else "heutige Index-Bestände (Survivorship-Bias)"
    )
    md.extend([
        "",
        f"> **Hinweis:** Alle Ergebnisse nutzen {pit_note} und unabhängige 1.000-€-Einzeltrades (keine gemeinsame Depot-Rendite). Beurteile Kriterien immer anhand von `Ø Netto-R`, `Median R`, `Ø R ohne Top-3` und Jahres-Stabilität.",
        "",
        "## 1. Vergleich der Stop-Modelle",
        "",
        "| Split | Stop-Modell | Gefüllt | Geschl. / Offen / Lücke | Treffer % | Gesamt-€ | Ø € | Ø Netto-R | Median R | Ø R ohne Top-3 | +2R % |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])
    for r in policy_rows:
        md.append(
            f"| `{r['split']}` | `{r['stop_modell']}` | {r['filled']} | {r['closed']} / {r['open']} / {r['censored']} | "
            f"{_fmt(r['winRatePct'], '%', 1)} | {_fmts(r['totalPnlEur'], ' €')} | {_fmts(r['avgPnlEur'], ' €')} | "
            f"{_fmts(r['avgR'], ' R', 3)} | {_fmts(r['medianR'], ' R', 3)} | {_fmts(r['avgRExTop3'], ' R', 3)} | {_fmt(r['r2RatePct'], '%', 1)} |"
        )

    for sp in allowed_splits:
        md.extend(["", f"## 2. Kriterien-Vergleich im Split `{sp}` (Stop-Modell `{policy}`)"])
        sections = []
        for r in comp_rows:
            if r["split"] == sp and r["kategorie"] not in sections:
                sections.append(r["kategorie"])
        for sec in sections:
            md.extend([
                "",
                f"### {sec}",
                "| Gruppe | Gefüllt | Geschl. / Offen / Lücke | Treffer % | Gesamt-€ | Ø € | Ø Netto-R | Median R | Ø R ohne Top-3 | +2R % |",
                "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
            ])
            for r in comp_rows:
                if r["split"] == sp and r["kategorie"] == sec:
                    md.append(
                        f"| {r['gruppe']} | {r['filled']} | {r['closed']} / {r['open']} / {r['censored']} | "
                        f"{_fmt(r['winRatePct'], '%', 1)} | {_fmts(r['totalPnlEur'], ' €')} | {_fmts(r['avgPnlEur'], ' €')} | "
                        f"{_fmts(r['avgR'], ' R', 3)} | {_fmts(r['medianR'], ' R', 3)} | {_fmts(r['avgRExTop3'], ' R', 3)} | {_fmt(r['r2RatePct'], '%', 1)} |"
                    )

    report_md = out / "report.md"
    report_md.write_text("\n".join(md) + "\n", encoding="utf-8")
    return {
        "planId": plan["id"],
        "policy": policy,
        "revealHoldout": reveal_holdout,
        "hiddenHoldoutTrades": hidden_holdout,
        "visibleTrades": len(visible),
        "blockCounts": dict(block_counts),
        "files": {
            "report": str(report_md),
            "featureComparisonCsv": str(comp_csv),
            "tradesCsv": str(trades_csv),
        },
    }
