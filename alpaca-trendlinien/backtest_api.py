"""Read-only HTTP API for /backtest (Backtest-Explorer & Replay-Training).

Reads completed local scanner-backtest study artifacts (outside Git) and serves
filtered, tier-classified trades with direct causal chart-replay deep links.
Strictly offline; never writes databases or places broker orders.
"""
from collections import Counter
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import statistics
from urllib.parse import urlencode

from hermes_scanner import TIER_ORDER, classify_tier, stop_price
from lab_data import session_bounds
from models import DataError

ROOT = Path(__file__).resolve().parent
ARTIFACTS_DIR = ROOT / "artifacts"

# Simple in-memory caches
_CACHE = {}
_TRAIL_CACHE = {}


def _compute_stop_trail(symbol, dataset_id, entry_at, exit_at, entry_price, initial_stop, policy):
    """Reconstruct the causal 4H ratchet stop trail for one backtest case (~0.1s).

    Uses the exact same PilotObserver (fan_master, lag=0) and 0.3% hard-stop rule
    as scanner_backtest.py. Returns (trail_points, r2_activated_at).
    """
    if not dataset_id or not entry_at or initial_stop is None or entry_price is None:
        return [], None
    cache_key = (dataset_id, int(entry_at), int(exit_at or 0), policy)
    if cache_key in _TRAIL_CACHE:
        return _TRAIL_CACHE[cache_key]
    try:
        from fan_geometry import profile
        from fan_observer import WatchRules, price_at
        from fan_study import source_gaps
        from fast_chart_store import _read_chart_frames
        from pilot_backtest import PilotObserver
        from settings import data_dir

        packed, _ = _read_chart_frames(data_dir(), dataset_id)
        if not packed or "4h" not in packed:
            return [], None
        all_4h = packed["4h"][0]
        end_bound = int(exit_at or entry_at) + 86400
        start_bound = int(entry_at) - 550 * 86400
        window = [b for b in all_4h if start_bound <= b.end <= end_bound]
        if len(window) < 20:
            return [], None

        rules = profile("master")
        watch_rules = WatchRules(arm_bars=2, retest_bars=16, stop_buffer_pct=0.3)
        gaps = source_gaps(window, window[-1].end, "4h")
        obs = PilotObserver(symbol, rules=rules, watch=watch_rules)
        orig_green = None
        cur_stop = float(initial_stop)
        entry_f = float(entry_price)
        # Match CaseExecution(spread_bps=5, slippage_bps=5) -> cost = 0.001 exactly
        cost = 0.001
        entry_fill = entry_f * (1.0 + cost)
        planned_risk = max(0.0, entry_fill - cur_stop * (1.0 - cost))
        r2_active = False
        r2_at = None
        started = False
        trail = []

        def _eligible(ln, ref_i, bar_end, bar_close):
            if not ln or (ln.get("slope") or 0.0) <= 0:
                return None
            if (ln.get("knownAt") or 0) > bar_end:
                return None
            val = price_at(ln, ref_i)
            if not (0 < val < bar_close):
                return None
            sp = stop_price(val, buffer_pct=0.3, tick=0.01)
            return sp if (sp is not None and sp < bar_close) else None

        for idx, bar in enumerate(window):
            if idx in gaps:
                obs.gap(bar)
            _ev, _sigs, snap = obs.push(bar)
            if bar.end < int(entry_at):
                continue
            if not started:
                started = True
                if snap and snap.get("green") and (snap["green"].get("slope") or 0.0) > 0:
                    orig_green = dict(snap["green"])
                trail.append({"time": bar.time, "value": round(cur_stop, 2)})
                continue

            if exit_at and bar.end > int(exit_at):
                break

            ref_idx = snap.get("referenceIndex", idx) if snap else idx
            cur_g = snap.get("green") if snap else None
            cand_vals = []

            if policy == "original_safety":
                sp_orig = _eligible(orig_green, ref_idx, bar.end, bar.close)
                if sp_orig is not None:
                    cand_vals.append(sp_orig)
            elif policy == "r2_fan":
                if not r2_active and planned_risk > 0:
                    net_r = (bar.close * (1.0 - cost) - entry_fill) / planned_risk
                    if net_r >= 2.0:
                        r2_active = True
                        r2_at = bar.time
                chosen = cur_g if r2_active else orig_green
                sp_chosen = _eligible(chosen, ref_idx, bar.end, bar.close)
                if sp_chosen is not None:
                    cand_vals.append(sp_chosen)
            elif policy == "qualified_fan":
                sp_orig = _eligible(orig_green, ref_idx, bar.end, bar.close)
                if sp_orig is not None:
                    cand_vals.append(sp_orig)
                if cur_g and cur_g.get("qualified"):
                    sp_cur = _eligible(cur_g, ref_idx, bar.end, bar.close)
                    if sp_cur is not None:
                        cand_vals.append(sp_cur)

            if cand_vals:
                cur_stop = max(cur_stop, max(cand_vals))
            trail.append({"time": bar.time, "value": round(cur_stop, 2)})

        if len(_TRAIL_CACHE) > 64:
            _TRAIL_CACHE.clear()
        _TRAIL_CACHE[cache_key] = (trail, r2_at)
        return trail, r2_at
    except Exception:
        return [], None


def _artifact_roots():
    roots = []
    if ARTIFACTS_DIR.is_dir():
        roots.append(ARTIFACTS_DIR)
    try:
        from settings import data_dir
        dd_art = data_dir() / "artifacts"
        if dd_art.is_dir() and dd_art.resolve() not in {r.resolve() for r in roots}:
            roots.append(dd_art)
    except Exception:
        pass
    return roots


def _list_study_dirs():
    roots = _artifact_roots()
    if not roots:
        return []
    found = []
    seen_ids = set()
    for base in roots:
        for child in sorted(base.iterdir(), reverse=True):
            if not child.is_dir() or child.name in seen_ids:
                continue
            plan_path = child / "plan.json"
            blocks_dir = child / "blocks"
            if plan_path.is_file() and blocks_dir.is_dir():
                try:
                    plan = json.loads(plan_path.read_text("utf-8"))
                except (OSError, ValueError):
                    continue
                seen_ids.add(child.name)
                found.append({
                    "id": child.name,
                    "path": child,
                    "planId": plan.get("id", ""),
                    "createdAt": plan.get("createdAt"),
                    "pointInTime": bool(plan.get("pointInTime")),
                    "symbolCount": len(plan.get("symbols") or []),
                    "splits": plan.get("splits") or {},
                })
    # Prefer PIT studies first, then newest directory name
    found.sort(key=lambda item: (0 if item["pointInTime"] else 1, item["id"]), reverse=False)
    # Within same PIT flag, newest directory name first
    pit_yes = sorted([x for x in found if x["pointInTime"]], key=lambda x: x["id"], reverse=True)
    pit_no = sorted([x for x in found if not x["pointInTime"]], key=lambda x: x["id"], reverse=True)
    return pit_yes + pit_no


def _session_end_ts(day_str):
    if not day_str:
        return None
    bounds = session_bounds(day_str)
    if bounds:
        return int(bounds[1])
    try:
        d = date.fromisoformat(day_str)
        return int(datetime(d.year, d.month, d.day, 20, 0, tzinfo=timezone.utc).timestamp())
    except ValueError:
        return None


def _session_end_iso(day_str):
    ts = _session_end_ts(day_str)
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, timezone.utc).isoformat()


def _next_session_end(approx_ts):
    """Snap an approximate UTC timestamp to the nearest valid US session close >= date."""
    d = datetime.fromtimestamp(approx_ts, timezone.utc).date()
    for offset in range(7):
        cand = (d + timedelta(days=offset)).isoformat()
        b = session_bounds(cand)
        if b:
            return cand, int(b[1]), datetime.fromtimestamp(int(b[1]), timezone.utc).isoformat()
    iso = datetime.fromtimestamp(approx_ts, timezone.utc).isoformat()
    return d.isoformat(), int(approx_ts), iso


def _load_study(study_id=None):
    studies = _list_study_dirs()
    if not studies:
        raise DataError("Keine lokale Backtest-Studie unter artifacts/ gefunden.", 404)
    chosen = next((s for s in studies if s["id"] == study_id), None) if study_id else studies[0]
    if chosen is None:
        raise DataError(f"Backtest-Studie '{study_id}' nicht gefunden.", 404)

    study_dir = chosen["path"]
    plan_path = study_dir / "plan.json"
    blocks_dir = study_dir / "blocks"
    sig_mtime = plan_path.stat().st_mtime_ns
    block_files = sorted(blocks_dir.glob("*.json"))
    cache_key = (chosen["id"], sig_mtime, len(block_files))
    cached = _CACHE.get(chosen["id"])
    if cached and cached[0] == cache_key:
        return cached[1]

    plan = json.loads(plan_path.read_text("utf-8"))
    datasets = plan.get("datasets") or {}
    session_iso_cache = {}
    records = []

    for bp in block_files:
        try:
            data = json.loads(bp.read_text("utf-8"))
        except (OSError, ValueError):
            continue
        sym = data.get("symbol") or bp.stem
        ds_id = data.get("datasetId") or (datasets.get(sym) or {}).get("datasetId") or ""
        for t in data.get("trades") or []:
            f = t.get("features") or {}
            direct = t.get("entrySource") in ("direct_1A", "direct_4A")
            tier = classify_tier(
                direct_entry=direct,
                active_approach=bool(f.get("active_approach")),
                high_maturity=bool(f.get("high_maturity")),
                low_daily_volatility=bool(f.get("low_daily_volatility")),
            )
            entry_day = t.get("entryDay") or ""
            watch_day = t.get("watchDay") or entry_day
            if entry_day not in session_iso_cache:
                session_iso_cache[entry_day] = _session_end_iso(entry_day)
            if watch_day not in session_iso_cache:
                session_iso_cache[watch_day] = _session_end_iso(watch_day)

            entry_asof = session_iso_cache.get(entry_day)
            watch_asof = session_iso_cache.get(watch_day)
            replay_url = "/?" + urlencode({
                "symbol": sym,
                "dataset": ds_id,
                "asof": entry_asof or "",
                "tf": "4h",
                "engine": "fan_master",
                "analysis": "1",
            })
            watch_replay_url = "/?" + urlencode({
                "symbol": sym,
                "dataset": ds_id,
                "asof": watch_asof or "",
                "tf": "4h",
                "engine": "fan_master",
                "analysis": "1",
            }) if watch_day != entry_day else replay_url

            records.append({
                "id": t.get("id"),
                "symbol": sym,
                "datasetId": ds_id,
                "split": t.get("split"),
                "year": str(t.get("year") or ""),
                "watchDay": watch_day,
                "entryDay": entry_day,
                "entrySource": t.get("entrySource"),
                "scenario": t.get("scenario"),
                "entryStatus": t.get("entryStatus"),
                "entryPrice": t.get("entryPrice"),
                "initialStop": t.get("initialStop"),
                "tier": tier,
                "tierRank": TIER_ORDER[tier],
                "score": f.get("score"),
                "strategyTag": f.get("strategy_tag"),
                "activeApproach": bool(f.get("active_approach")),
                "highMaturity": bool(f.get("high_maturity")),
                "lowVol": bool(f.get("low_daily_volatility")),
                "redOrigin": f.get("red_origin"),
                "redContacts": f.get("red_contacts"),
                "redAgeDays": f.get("red_age_days"),
                "greenContacts": f.get("green_contacts"),
                "riskPct": f.get("risk_pct"),
                "riskAtr": f.get("risk_atr"),
                "atr1dPct": f.get("atr_1d_pct"),
                "universes": f.get("universes") or "",
                "outcomes": t.get("outcomes") or {},
                "replayUrl": replay_url,
                "watchReplayUrl": watch_replay_url,
            })

    years = sorted({r["year"] for r in records if r["year"]}, reverse=True)
    payload = {
        "study": {k: v for k, v in chosen.items() if k != "path"},
        "years": years,
        "records": records,
    }
    _CACHE[chosen["id"]] = (cache_key, payload)
    return payload


def _first(query, key, default=None):
    vals = query.get(key)
    return vals[0] if vals else default


def _summarize(records, policy):
    filled = [r for r in records if r["entryStatus"] == "filled" and policy in r["outcomes"]]
    closed = [r for r in filled if r["outcomes"][policy].get("status") == "closed"]
    opened = [r for r in filled if r["outcomes"][policy].get("status") == "open"]
    censored = [r for r in filled if r["outcomes"][policy].get("status") == "censored"]
    ev = [r for r in (closed + opened) if r["outcomes"][policy].get("pnlEur") is not None]
    pnls = [r["outcomes"][policy]["pnlEur"] for r in ev]
    rs = [r["outcomes"][policy]["netR"] for r in ev if r["outcomes"][policy].get("netR") is not None]
    wins = sum(1 for r in closed if (r["outcomes"][policy].get("pnlEur") or 0) > 0)
    r2_hits = sum(1 for r in ev if r["outcomes"][policy].get("r2Activated"))
    ex3 = None
    if len(rs) > 3:
        trimmed = sorted(rs)[:-3]
        ex3 = round(sum(trimmed) / len(trimmed), 3)
    return {
        "totalSignals": len(records),
        "filled": len(filled),
        "evaluated": len(ev),
        "closed": len(closed),
        "open": len(opened),
        "censored": len(censored),
        "winRatePct": round(100.0 * wins / len(closed), 1) if closed else None,
        "totalPnlEur": round(sum(pnls), 2),
        "avgPnlEur": round(sum(pnls) / len(pnls), 2) if pnls else None,
        "avgR": round(sum(rs) / len(rs), 3) if rs else None,
        "medianR": round(statistics.median(rs), 3) if rs else None,
        "avgRExTop3": ex3,
        "r2RatePct": round(100.0 * r2_hits / len(ev), 1) if ev else None,
        "tierCounts": dict(Counter(r["tier"] for r in records)),
    }


def get(path, query):
    if path == "/api/backtest/studies":
        return {
            "studies": [{k: v for k, v in s.items() if k != "path"} for s in _list_study_dirs()],
        }

    if path == "/api/backtest/case":
        trade_id = (_first(query, "id", "") or "").strip()
        if not trade_id:
            raise DataError("Trade-ID fehlt.", 400)
        study_id = _first(query, "study")
        policy = _first(query, "policy", "r2_fan")
        if policy not in ("r2_fan", "qualified_fan", "original_safety"):
            raise DataError("Ungültiges Stop-Modell.", 400)
        loaded = _load_study(study_id)
        rec = next((r for r in loaded["records"] if r["id"] == trade_id), None)
        if rec is None:
            raise DataError("Backtest-Fall nicht gefunden.", 404)
        out = rec["outcomes"].get(policy) or {}
        entry_ts = _session_end_ts(rec["entryDay"])
        entry_iso = _session_end_iso(rec["entryDay"])
        hold_days = out.get("holdingDays")
        exit_day, exit_ts, exit_iso = (None, None, None)
        if entry_ts is not None and hold_days is not None:
            approx_exit = entry_ts + int(round(float(hold_days) * 86400.0))
            exit_day, exit_ts, exit_iso = _next_session_end(approx_exit)
        exit_price = None
        if rec["entryPrice"] is not None and out.get("returnPct") is not None:
            exit_price = round(float(rec["entryPrice"]) * (1.0 + float(out["returnPct"]) / 100.0), 2)
        r2_target = None
        if rec["entryPrice"] is not None and rec["initialStop"] is not None:
            _cost = 0.001
            _buy = float(rec["entryPrice"]) * (1.0 + _cost)
            _risk = _buy - float(rec["initialStop"]) * (1.0 - _cost)
            if _risk > 0:
                r2_target = round((_buy + 2.0 * _risk) / (1.0 - _cost), 2)
        stop_trail, r2_at = _compute_stop_trail(
            rec["symbol"], rec["datasetId"], entry_ts, exit_ts, rec["entryPrice"], rec["initialStop"], policy
        )
        return {
            "studyId": loaded["study"]["id"],
            "policy": policy,
            "id": rec["id"],
            "symbol": rec["symbol"],
            "datasetId": rec["datasetId"],
            "tier": rec["tier"],
            "split": rec["split"],
            "scenario": rec["scenario"],
            "watchDay": rec["watchDay"],
            "entryDay": rec["entryDay"],
            "entryAt": entry_ts,
            "entryAsOfIso": entry_iso,
            "entryPrice": rec["entryPrice"],
            "initialStop": rec["initialStop"],
            "r2TargetPrice": r2_target,
            "exitDay": exit_day,
            "exitAt": exit_ts,
            "exitAsOfIso": exit_iso,
            "exitPrice": exit_price,
            "r2ActivatedAt": r2_at,
            "stopTrail": stop_trail,
            "outcome": out,
        }

    if path == "/api/backtest/trades":
        study_id = _first(query, "study")
        loaded = _load_study(study_id)
        policy = _first(query, "policy", "r2_fan")
        if policy not in ("r2_fan", "qualified_fan", "original_safety"):
            raise DataError("Ungültiges Stop-Modell.", 400)

        tier_q = _first(query, "tier", "all")
        split_q = _first(query, "split", "all")
        year_q = _first(query, "year", "all")
        scenario_q = _first(query, "scenario", "all")
        outcome_q = _first(query, "outcome", "all")
        symbol_q = (_first(query, "symbol", "") or "").strip().upper()
        sort_q = _first(query, "sort", "date_desc")
        page = max(1, int(_first(query, "page", "1") or "1"))
        limit = max(10, min(250, int(_first(query, "limit", "100") or "100")))

        tier_sets = {
            "all": None,
            "focus": {"C", "B", "4", "A"},
            "quiet": {"C", "B", "4"},
            "core": {"C", "A"},
            "C": {"C"},
            "B": {"B"},
            "4": {"4"},
            "A": {"A"},
            "BASIS": {"BASIS"},
        }
        allowed_tiers = tier_sets.get(tier_q)

        matched = []
        for r in loaded["records"]:
            if allowed_tiers is not None and r["tier"] not in allowed_tiers:
                continue
            if split_q != "all" and r["split"] != split_q:
                continue
            if year_q != "all" and r["year"] != year_q:
                continue
            if scenario_q != "all":
                if scenario_q == "direct":
                    if r["entrySource"] not in ("direct_1A", "direct_4A"):
                        continue
                elif scenario_q == "watch":
                    if r["entrySource"] != "watch_to_entry":
                        continue
                elif r["scenario"] != scenario_q:
                    continue
            if symbol_q and symbol_q not in r["symbol"]:
                continue

            out = r["outcomes"].get(policy) or {}
            if outcome_q != "all":
                st = out.get("status")
                pnl = out.get("pnlEur")
                if outcome_q == "win" and not (st in ("closed", "open") and pnl is not None and pnl > 0):
                    continue
                if outcome_q == "loss" and not (st in ("closed", "open") and pnl is not None and pnl <= 0):
                    continue
                if outcome_q == "r2" and not out.get("r2Activated"):
                    continue
                if outcome_q == "censored" and st != "censored":
                    continue
            matched.append(r)

        def _r_val(rec):
            v = (rec["outcomes"].get(policy) or {}).get("netR")
            return v if v is not None else -9999.0

        def _pnl_val(rec):
            v = (rec["outcomes"].get(policy) or {}).get("pnlEur")
            return v if v is not None else -999999.0

        if sort_q == "date_asc":
            matched.sort(key=lambda r: (r["entryDay"], r["tierRank"], r["symbol"]))
        elif sort_q == "tier":
            matched.sort(key=lambda r: (r["tierRank"], r["entryDay"], r["symbol"]))
            # Newest within each tier first:
            matched.sort(key=lambda r: r["entryDay"], reverse=True)
            matched.sort(key=lambda r: r["tierRank"])
        elif sort_q == "r_desc":
            matched.sort(key=lambda r: (-_r_val(r), r["entryDay"], r["symbol"]))
        elif sort_q == "r_asc":
            matched.sort(key=lambda r: (_r_val(r), r["entryDay"], r["symbol"]))
        elif sort_q == "pnl_desc":
            matched.sort(key=lambda r: (-_pnl_val(r), r["entryDay"], r["symbol"]))
        else:  # date_desc
            matched.sort(key=lambda r: (r["entryDay"], -r["tierRank"], r["symbol"]), reverse=True)

        summary = _summarize(matched, policy)
        total = len(matched)
        pages = max(1, (total + limit - 1) // limit)
        page = min(page, pages)
        start = (page - 1) * limit
        slice_rows = matched[start : start + limit]

        study_name = loaded["study"]["id"]
        items = []
        for r in slice_rows:
            out = r["outcomes"].get(policy) or {}
            bt_qs = "&" + urlencode({"bt": r["id"], "bt_policy": policy, "bt_study": study_name})
            items.append({
                "id": r["id"],
                "symbol": r["symbol"],
                "split": r["split"],
                "year": r["year"],
                "watchDay": r["watchDay"],
                "entryDay": r["entryDay"],
                "entrySource": r["entrySource"],
                "scenario": r["scenario"],
                "entryStatus": r["entryStatus"],
                "entryPrice": r["entryPrice"],
                "initialStop": r["initialStop"],
                "tier": r["tier"],
                "score": r["score"],
                "strategyTag": r["strategyTag"],
                "activeApproach": r["activeApproach"],
                "highMaturity": r["highMaturity"],
                "lowVol": r["lowVol"],
                "redOrigin": r["redOrigin"],
                "redContacts": r["redContacts"],
                "redAgeDays": r["redAgeDays"],
                "greenContacts": r["greenContacts"],
                "riskPct": r["riskPct"],
                "riskAtr": r["riskAtr"],
                "atr1dPct": r["atr1dPct"],
                "universes": r["universes"],
                "outcome": out,
                "replayUrl": r["replayUrl"] + bt_qs,
                "watchReplayUrl": r["watchReplayUrl"] + bt_qs,
            })

        return {
            "study": loaded["study"],
            "years": loaded["years"],
            "policy": policy,
            "summary": summary,
            "pagination": {"page": page, "pages": pages, "limit": limit, "total": total},
            "items": items,
        }

    raise DataError("Unbekannter Backtest-Endpunkt.", 404)
