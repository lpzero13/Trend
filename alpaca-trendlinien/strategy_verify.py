"""Independent price, event chronology, eligibility and cash-ledger checks.

Does not invoke strategy_path, SafetyState, entry_contract or portfolio.simulate.
The oracle reads immutable source candles, checks first executable exits and
recomputes monetary results with Decimal arithmetic. No provider operations.
"""
from bisect import bisect_right
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_FLOOR
import hashlib
import json
from pathlib import Path
import math
import statistics

from datasets import digest, read_dataset, source_bars
from market_calendar import calendar
from models import Bar, NY
from settings import ROOT


def close(a, b):
    assert math.isclose(float(a), float(b), abs_tol=1e-7, rel_tol=1e-10), (a, b)


def grid(start, end):
    first, last = (datetime.fromtimestamp(t, NY).date() for t in (start, end))
    for year in range(first.year, last.year+1):
        cal = calendar(year)
        for day in cal.sessions_in_range(max(str(first), f"{year}-01-01"), min(str(last), f"{year}-12-31")):
            opened, closed = int(cal.session_open(day).timestamp()), int(cal.session_close(day).timestamp())
            for at in range(opened, closed, 300):
                if start <= at and at+300 <= end:
                    yield at


def volatility(rows):
    if len(rows) < 15:
        return None
    return float(sum(Decimal(str(max(b.high-b.low, abs(b.high-a.close), abs(b.low-a.close))))
                     for a, b in zip(rows[-15:-1], rows[-14:]))/Decimal(14))


def pivots(rows, upper, side):
    result = []
    for i in range(side, len(rows)-side):
        center = rows[i].high if upper else rows[i].low
        around = [(b.high if upper else b.low) for b in rows[i-side:i+side+1]]
        if (center == max(around) if upper else center == min(around)) and around.count(center) == 1:
            result.append(i)
    return result


def trend(rows):
    hi, lo = pivots(rows, True, 2), pivots(rows, False, 2)
    if len(hi) < 2 or len(lo) < 2:
        return "unknown"
    return "up" if rows[hi[-1]].high > rows[hi[-2]].high and rows[lo[-1]].low > rows[lo[-2]].low else "down" if rows[hi[-1]].high < rows[hi[-2]].high and rows[lo[-1]].low < rows[lo[-2]].low else "mixed"


def weekly(rows):
    groups = defaultdict(list)
    for b in rows:
        date = datetime.fromtimestamp(b.time, NY).date()
        groups[date-timedelta(days=date.weekday())].append(b)
    result = []
    for week, bars in sorted(groups.items()):
        cal = calendar(week.year)
        sessions = list(cal.sessions_in_range(str(week), str(week+timedelta(days=6))))
        actual = {str(datetime.fromtimestamp(b.time, NY).date()) for b in bars}
        if not sessions or actual != {str(s.date()) for s in sessions}:
            continue
        end = int(cal.session_close(sessions[-1]).timestamp())
        result.append(Bar(bars[0].time, end, bars[0].open, max(b.high for b in bars), min(b.low for b in bars), bars[-1].close, sum(b.volume for b in bars)))
    return result


def known_market(daily, rules):
    weeks = weekly(daily)
    daily_atr = volatility(daily)
    width = max(rules["tick"], (daily_atr or 0)*rules["zone_width_atr"])
    levels = []
    side = rules["pivot_side"]
    for tf, rows in (("1D", daily), ("1W", weeks)):
        for i in pivots(rows, True, side):
            prominence = rows[i].high-max(min(b.low for b in rows[i-side:i]), min(b.low for b in rows[i+1:i+side+1]))
            vol = volatility(rows[:i+side+1])
            if tf == "1D" and (vol is None or prominence < rules["daily_prominence_atr"]*vol):
                continue
            known = rows[i+side].end
            if any(b.end > known and b.close > rows[i].high+width for b in daily):
                continue
            levels.append((rows[i].high-width, rows[i].high+width, tf, rows[i].time, known))
    zones = []
    for lo, hi, tf, at, known in sorted(levels):
        if zones and lo <= zones[-1][1]:
            zones[-1] = (zones[-1][0], max(zones[-1][1], hi))
        else:
            zones.append((lo, hi))
    return {"daily": trend(daily), "weekly": trend(weeks), "lastDailyClose": daily[-1].end if daily else None,
            "lastWeeklyClose": weeks[-1].end if weeks else None, "zones": zones, "dailyATR": daily_atr}


def freshness(at):
    date = datetime.fromtimestamp(at, NY).date()
    closed, weeks = [], defaultdict(list)
    for year in range((date-timedelta(days=40)).year, (date+timedelta(days=7)).year+1):
        cal = calendar(year)
        for d in cal.sessions_in_range(max(str(date-timedelta(days=40)), f"{year}-01-01"), min(str(date+timedelta(days=7)), f"{year}-12-31")):
            stamp = int(cal.session_close(d).timestamp())
            if stamp <= at:
                closed.append(stamp)
            day = d.date()
            weeks[day-timedelta(days=day.weekday())].append(stamp)
    return max(closed, default=None), max((max(v) for v in weeks.values() if max(v) <= at), default=None)


def audit_contract(entry, contract, sources, rules, market_cache):
    at = entry["entryAt"]
    four = [b for b in sources["4h"] if b.end <= at]
    daily = [b for b in sources["1D"] if b.end <= at]
    key = (entry["datasetId"], len(daily))
    if key not in market_cache:
        market_cache[key] = known_market(daily, rules)
    known = market_cache[key]
    assert contract["id"] == digest({k: v for k, v in contract.items() if k != "id"})
    assert contract["entryId"] == entry["id"] and contract["green"] == entry["green"] and contract["red"] == entry["red"]
    assert contract["entryIndex"] == len(four)-1 and contract["knownAt"] == at
    vol = volatility(four)
    if vol is None:
        assert contract["atr"] is None and contract["initialStop"] is None and not contract["eligible"]
        return
    close(vol, contract["atr"])
    buffer = max(rules["tick"], vol*rules["initial_buffer_atr"])
    close(contract["buffer"], buffer)
    close(contract["initialStop"], entry["initialStop"]-buffer)
    close(contract["initialRisk"], contract["entryFill"]-contract["initialStop"])
    for field in ("daily", "weekly", "lastDailyClose", "lastWeeklyClose"):
        assert contract["context"][field] == known[field], field
    actual_zones = contract["context"]["zones"]
    assert len(actual_zones) == len(known["zones"])
    for zone, (lo, hi) in zip(actual_zones, known["zones"]):
        close(zone["lower"], lo)
        close(zone["upper"], hi)
        for source in zone["sources"]:
            assert source["knownAt"] <= at
    zone = next((z for z in known["zones"] if z[1] > entry["entryPrice"]), None) if known["dailyATR"] is not None else None
    if zone is None:
        assert contract["zone"] is None and contract["netRoomR"] is None and contract["targetPrice"] is None
    else:
        close(contract["zone"]["lower"], zone[0])
        close(contract["zone"]["upper"], zone[1])
        target = zone[0] if zone[0] > entry["entryPrice"] else None
        if target is None:
            assert contract["targetPrice"] is None
        else:
            close(contract["targetPrice"], target)
        room = (zone[0]*(1-contract["costs"]["side_cost"])-contract["entryFill"])/contract["initialRisk"]
        close(contract["netRoomR"], room)
    daily_end, week_end = freshness(at)
    checks = {"known_atr": True, "positive_stop": 0 < contract["initialStop"] < entry["entryPrice"],
        "risk_atr": contract["initialRisk"]/vol <= rules["max_risk_atr"],
        "line_age": (at-entry["red"]["a_time"])/86400 >= rules["min_age_days"],
        "fresh_daily": known["lastDailyClose"] == daily_end,
        "fresh_weekly": known["lastWeeklyClose"] == week_end,
        "daily_context": None if known["daily"] == "unknown" else known["daily"] != "down",
        "weekly_context": None if known["weekly"] == "unknown" else known["weekly"] != "down",
        "net_room": None if zone is None else contract["netRoomR"] >= rules["min_room_r"]}
    assert checks == contract["checks"]
    assert contract["eligible"] == all(v is True for v in checks.values())
    assert contract["blockedBy"] == [k for k, v in checks.items() if v is not True]


def audit_path(entry, contract, path, sources, rules, phase_end, grids):
    if path["status"] in ("unavailable", "invalid"):
        if not contract["checks"]["known_atr"] or not contract["checks"]["positive_stop"]:
            assert path["reason"] == "invalid_or_unknown_initial_safety"
            return
        raise AssertionError("Unexpected unavailable historical entry")
    fine = sources["5m_map"]
    four = sources["4h"]
    at = entry["entryAt"]
    date = datetime.fromtimestamp(at, NY).date()
    days = []
    for year in range(date.year, (date+timedelta(days=110)).year+1):
        cal = calendar(year)
        days.extend(cal.sessions_in_range(max(str(date+timedelta(days=1)), f"{year}-01-01"), min(str(date+timedelta(days=110)), f"{year}-12-31")))
    target_day = days[path["days"]-1]
    planned = int(calendar(target_day.year).session_close(target_day).timestamp())
    assert planned == path["plannedTimeExit"]
    target = contract["targetPrice"] if path["model"] == "structure_target" else None
    assert path["targetPrice"] == target
    close(path["initialStop"], contract["initialStop"])
    close(path["initialRisk"], contract["initialRisk"])
    gkey = (at, min(planned, phase_end))
    if gkey not in grids:
        grids[gkey] = list(grid(*gkey))
    ray, stop, peak = dict(entry["green"]), contract["initialStop"], contract["referenceHigh"]
    j = contract["entryIndex"]+1
    seen_events = []
    pending = False
    missing, expected = None, None
    for stamp in grids[gkey]:
        if stamp not in fine:
            missing = stamp
            break
        b = fine[stamp]
        if stamp == at:
            assert b.open == entry["entryPrice"]
        while j < len(four) and four[j].end <= phase_end and four[j].end+rules["latency_seconds"] <= stamp and not pending:
            current = four[j]
            old = ray["a_price"]+ray["slope"]*(j-ray["a_index"])
            if path["model"] != "fixed" and current.close < old:
                seen_events.append({"kind": "safety_close", "knownAt": current.end, "effectiveAt": stamp,
                                    "price": current.close, "level": old, "ray": dict(ray)})
                pending = True
            elif path["model"] in ("structure", "structure_target"):
                side, z = rules["pivot_side"], j-rules["pivot_side"]
                if z >= side and four[z].time > at and four[z].time > ray["b_time"]:
                    lows = [four[k].low for k in range(z-side, z+side+1)]
                    low = four[z].low
                    a = ray["b_index"]
                    highs = [four[k].high for k in range(a+1, z) if four[k].time >= at]
                    if low == min(lows) and lows.count(low) == 1 and low > four[a].low and highs and max(highs) > peak:
                        slope = (low-four[a].low)/(z-a)
                        wick_ok = all(four[k].low+1e-7 >= four[a].low+slope*(k-a) for k in range(a, j+1))
                        level = four[a].low+slope*(j-a)
                        vol = volatility(four[:j+1])
                        if wick_ok and old+rules["tick"] < level < current.close and vol is not None:
                            new = {"basis": "bars", "a_index": a, "b_index": z, "a_time": four[a].time,
                                   "b_time": four[z].time, "a_price": four[a].low, "b_price": low,
                                   "slope": slope, "valid": True, "confirmedAt": current.end}
                            new_stop = max(stop, low-max(rules["tick"], vol*rules["initial_buffer_atr"]))
                            seen_events.append({"kind": "safety_replace", "knownAt": current.end, "effectiveAt": stamp,
                                                "previousRay": dict(ray), "ray": new, "previousHardStop": stop,
                                                "hardStop": new_stop, "higherHigh": max(highs), "atr": vol})
                            ray, stop, peak = new, new_stop, max(highs)
            j += 1
        if b.open <= stop:
            expected = (stamp, b.open, "hard_stop_gap", True, False)
        elif pending:
            expected = (stamp, b.open, "safety_close", True, False)
        elif target is not None and b.open >= target:
            expected = (stamp, target, "resistance_at_open", True, False)
        elif b.low <= stop:
            expected = (stamp, stop, "hard_stop", False, target is not None and b.high >= target)
        elif target is not None and b.high >= target:
            expected = (stamp, target, "resistance", False, False)
        elif b.end == planned:
            expected = (stamp, b.close, "time", False, False)
        if expected:
            break
    assert len(seen_events) == len(path["events"])
    for actual, oracle in zip(path["events"], seen_events):
        assert set(actual) == set(oracle)
        for k, value in oracle.items():
            if type(value) in (int, float):
                close(actual[k], value)
            else:
                assert actual[k] == value, k
    if expected is None:
        assert path["status"] == "censored" and path["exitFill"] is None
        if missing is not None:
            assert path["reason"] == "missing_fine_path" and path["missingAt"] == missing
        else:
            assert path["reason"] == "phase_boundary" and planned > phase_end
        return
    stamp, price, reason, at_open, ambiguous = expected
    assert path["status"] == "closed" and path["fillBarAt"] == stamp and path["exitAt"] == fine[stamp].end
    assert path["exitReason"] == reason and path["atOpen"] == at_open and path["intrabarAmbiguous"] == ambiguous
    close(path["exitPrice"], price)
    c = contract["costs"]
    side = Decimal(str(c["spread_bps"]))/20000+Decimal(str(c["slippage_bps"]))/10000
    buy = Decimal(str(entry["entryPrice"]))*(1+side)
    sell = Decimal(str(price))*(1-side)
    qty = (Decimal(str(c["notional"]))-Decimal(str(c["fee_per_order"])))/buy
    pnl = qty*(sell-buy)-2*Decimal(str(c["fee_per_order"]))
    close(path["entryFill"], buy)
    close(path["exitFill"], sell)
    close(path["quantity"], qty)
    close(path["netPnl"], pnl)
    close(path["netReturnPct"], pnl/Decimal(str(c["notional"]))*100)
    close(path["netR"], pnl/(qty*(buy-Decimal(str(contract["initialStop"])))))


def audit_portfolio(portfolio, entries, paths, sources, phase, costs):
    """Reconstruct accepted/skipped decisions and every reported cash mark."""
    entry_by_id = {e["id"]: e for e in entries}
    paths = sorted(paths, key=lambda p: (p["entryAt"], entry_by_id[p["entryId"]]["symbol"], p["entryId"]))
    trades = {p["entryId"]: p for p in portfolio["trades"]}
    skipped = {p["entryId"]: p for p in portfolio["skipped"]}
    cash = portfolio["initialCapital"]
    options = portfolio["options"]
    active = {}
    by_time = defaultdict(list)
    for p in paths:
        by_time[p["entryAt"]].append(p)
    stamps = ({t+300 for t in grid(phase["startAt"], phase["endAt"])} if paths else set()) | set(by_time) | {phase["endAt"]}
    fee = costs["fee_per_order"]
    side = costs["spread_bps"]/20000+costs["slippage_bps"]/10000
    ends = {key: [b.end for b in value["5m"]] for key, value in sources.items()}
    seen, released = set(), set()
    peak, drawdown = cash, 0.
    actual_halt = None

    def mark(at):
        value = cash
        for identity, (p, quantity) in active.items():
            e = entry_by_id[identity]
            i = bisect_right(ends[e["datasetId"]], at)-1
            b = sources[e["datasetId"]]["5m"][i] if i >= 0 else None
            price = b.close if b and b.end > p["entryAt"] else e["entryPrice"]
            value += quantity*price
        return value

    reported_marks = {m["at"]: m for m in portfolio["equity"]}
    observed = phase["startAt"]
    for at in sorted(stamps):
        for identity, (path, quantity) in list(active.items()):
            if path["status"] == "closed" and path["exitAt"] <= at:
                cash += quantity*path["exitFill"]-fee
                actual = trades[identity]
                close(actual["netPnl"], quantity*(path["exitFill"]-path["entryFill"])-2*fee)
                assert actual["exitAt"] == path["exitAt"]
                del active[identity]
                released.add(identity)
        gaps = [p[0]["missingAt"] for p in active.values() if p[0].get("missingAt", math.inf) <= at]
        if gaps:
            actual_halt = min(gaps)
            observed = actual_halt
            value = mark(observed)
            peak = max(peak, value)
            drawdown = min(drawdown, (value/peak-1)*100)
            break
        for p in by_time.get(at, []):
            identity = p["entryId"]
            e = entry_by_id[identity]
            reason = p.get("reason") if p["status"] in ("invalid", "unavailable") else "already_holding_symbol" if any(entry_by_id[k]["symbol"] == e["symbol"] for k in active) else "max_positions" if len(active) >= options["max_positions"] else None
            if reason is not None:
                assert skipped[identity]["reason"] == reason and identity not in trades
                seen.add(identity)
                continue
            equity = mark(at)
            unit_risk = p["entryFill"]-p["initialStop"]*(1-side)
            quantity = min(max(0, cash-fee)/p["entryFill"], equity*options["allocation_fraction"]/p["entryFill"], max(0, equity*options["risk_fraction"]-2*fee)/unit_risk)
            quantity = math.floor(quantity*1e6)/1e6 if options["fractional"] else math.floor(quantity)
            if quantity <= 0:
                assert skipped[identity]["reason"] == "no_affordable_units"
                seen.add(identity)
                continue
            trade = trades[identity]
            close(trade["quantity"], quantity)
            close(trade["equityAtEntry"], equity)
            planned_risk = quantity*unit_risk+2*fee
            close(trade["plannedRiskUSD"], planned_risk)
            assert planned_risk <= equity*options["risk_fraction"]+1e-7
            cash -= quantity*p["entryFill"]+fee
            assert cash >= -1e-7
            close(trade["cashAfterEntry"], cash)
            active[identity] = (p, quantity)
            seen.add(identity)
        equity = mark(at)
        peak = max(peak, equity)
        drawdown = min(drawdown, (equity/peak-1)*100)
        if at in reported_marks:
            close(reported_marks[at]["value"], equity)
            close(reported_marks[at]["cash"], cash)
            assert reported_marks[at]["positions"] == len(active)
        observed = at
    assert seen == set(trades) | set(skipped)
    assert portfolio["accepted"] == len(trades) and portfolio["closed"] == len(released)
    assert portfolio["open"] == len(active) and portfolio["observedThrough"] == observed
    close(portfolio["cash"], cash)
    close(portfolio["markedEquity"], mark(observed))
    close(portfolio["realizedNetPnl"], sum(trades[k]["netPnl"] for k in released))
    close(portfolio["max5mSampledDrawdownPct"], drawdown)
    if actual_halt is None:
        assert portfolio["halt"] is None and portfolio["status"] == "marked_to_phase_end"
        close(portfolio["markedReturnPct"], (mark(observed)/options["capital"]-1)*100)
    else:
        assert portfolio["halt"]["at"] == actual_halt and portfolio["markedReturnPct"] is None


def verify_study(root):
    root = Path(root)
    manifest = json.loads((root/"manifest.json").read_text("utf-8"))
    for name, expected in manifest["engineFiles"].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected, name
    identities = {e["datasetId"] for entries in manifest["cohorts"].values() for e in entries}
    sources = {key: source_bars(read_dataset(key)) for key in identities}
    for frames in sources.values():
        frames["5m_map"] = {b.time: b for b in frames["5m"]}
    output = {"manifestHash": digest(manifest), "stages": {}, "providerCalls": 0,
              "meaning": "Independent causal event/fill replay, known-context/zone/eligibility checks, Decimal P/L/R and cash ledger/selection/5m-mark audit; not provider or broker truth."}
    market_cache, grids = {}, {}
    for stage in ("development", "validation"):
        path = root/(stage+".json")
        if not path.exists():
            continue
        result = json.loads(path.read_text("utf-8"))
        assert result["manifestHash"] == digest(manifest)
        entries = {e["id"]: e for e in result["entries"]}
        assert list(entries) == [e["id"] for e in manifest["cohorts"][stage]]
        contracts = {c["entryId"]: c for c in result["contracts"]}
        assert entries.keys() == contracts.keys()
        for identity, entry in entries.items():
            audit_contract(entry, contracts[identity], sources[entry["datasetId"]], manifest["rules"], market_cache)
        seen = set()
        for p in result["paths"]:
            identity = (p["entryId"], p["model"], p["days"])
            assert identity not in seen
            seen.add(identity)
            assert p["model"] in manifest["models"] and p["days"] in manifest["horizons"]
            entry = entries[p["entryId"]]
            assert (p["profile"], p["family"], p["symbol"], p["datasetId"]) == (entry["profile"], entry["family"], entry["symbol"], entry["datasetId"])
            audit_path(entry, contracts[entry["id"]], p, sources[entry["datasetId"]], manifest["rules"], manifest["phases"][stage]["endAt"], grids)
        assert len(seen) == len(entries)*len(manifest["models"])*len(manifest["horizons"])
        for row in result["rows"]:
            pool = [p for p in result["paths"] if (p["profile"], p["family"], p["days"]) == (row["profile"], row["family"], row["days"])
                    and (row["cohort"] == "all" or contracts[p["entryId"]]["eligible"])]
            counts = Counter(p["entryId"] for p in pool if p["status"] == "closed")
            paired = [p for p in pool if p["model"] == row["model"] and counts[p["entryId"]] == len(manifest["models"])]
            assert row["paired"]["closed"] == len(paired)
            if paired:
                close(row["paired"]["meanNetR"], statistics.mean(p["netR"] for p in paired))
                close(row["paired"]["meanPnlPer1000USD"], statistics.mean(p["netPnl"] for p in paired))
            fixed = [p for p in pool if p["model"] == row["model"] and p["entryId"] in row["constantIds"]]
            assert row["constant"]["closed"] == len(fixed)
            if fixed:
                close(row["constant"]["meanNetR"], statistics.mean(p["netR"] for p in fixed))
        for portfolio in result["portfolios"]:
            members = [e for e in entries.values() if (e["profile"], e["family"]) == (portfolio["profile"], portfolio["family"])]
            paths = [p for p in result["paths"] if (p["profile"], p["family"], p["days"], p["model"]) ==
                     (portfolio["profile"], portfolio["family"], portfolio["days"], portfolio["model"])
                     and (portfolio["cohort"] == "all" or contracts[p["entryId"]]["eligible"])]
            audit_portfolio(portfolio, members, paths, sources, manifest["phases"][stage], manifest["costs"])
        output["stages"][stage] = {"entries": len(entries), "paths": len(seen), "rows": len(result["rows"]),
                                  "portfolios": len(result["portfolios"]), "eligible": sum(c["eligible"] for c in contracts.values())}
    if "validation" in output["stages"]:
        assert (root/"decision-before-validation.json").exists() and "development" in output["stages"]
    output["verifierHash"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    from strategy_research import write_json
    write_json(root/"verification.json", output)
    return output
