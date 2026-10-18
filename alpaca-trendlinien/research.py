"""Exploratory event study. Causal signals, random origins, no fitted entry filters.

Forward OHLC is available only to the outcome evaluator. Fixed-horizon returns
are observations, not a portfolio backtest or a claim of executable profit.
"""
from bisect import bisect_left, bisect_right
from dataclasses import asdict
from datetime import datetime, timezone
import random
import re
import statistics

from datasets import digest, source_bars
from models import DataError
from trendlines import DAY, RULES_VERSION, cut, detect_break, pair, rules_for, window_start

STUDY_VERSION = "tori-event-study-1"
DEFAULTS = {"symbols": ["MSFT", "AMZN"], "samples": 10, "seed": 20261017,
    "history_days": 900, "search_bars": 60, "horizons": [5, 10, 20],
    "holdout_fraction": 0.2, "retest_bars": 12, "retest_bps": 20,
    "latency_seconds": 900, "cost_bps": 5, "stop_buffer_bps": 0}


def validate_spec(value):
    if not isinstance(value, dict) or set(value) - (set(DEFAULTS) | {"dataset_ids", "universe"}):
        raise DataError("Unbekannte oder ungültige Forschungsparameter.", 400)
    result = {**DEFAULTS, **value}
    symbols = result["symbols"]
    if isinstance(symbols, str):
        symbols = symbols.upper().replace(",", " ").split()
    if not isinstance(symbols, list) or len(symbols) > 10000 or any(not isinstance(s, str) or not re.fullmatch(r"[A-Z][A-Z0-9./-]{0,29}", s) for s in symbols):
        raise DataError("Ungültige Aktienliste (US-Symbole in Großbuchstaben).", 400)
    result["symbols"] = sorted(set(symbols))
    if result.get("universe", "list") not in ("list", "all") or (not symbols and result.get("universe") != "all"):
        raise DataError("Bitte eine Aktienliste oder das gesamte Universum wählen.", 400)
    for name, low, high in [("samples", 1, 200), ("seed", 0, 2147483647), ("history_days", 450, 3650),
        ("search_bars", 1, 500), ("retest_bars", 1, 100), ("latency_seconds", 0, 86400)]:
        if type(result[name]) is not int or not low <= result[name] <= high:
            raise DataError(f"{name}: erlaubt sind ganze Zahlen von {low} bis {high}.", 400)
    for name, low, high in [("holdout_fraction", .1, .5), ("retest_bps", 0, 1000), ("cost_bps", 0, 500), ("stop_buffer_bps", 0, 1000)]:
        if type(result[name]) not in (int, float) or not low <= result[name] <= high:
            raise DataError(f"{name}: ungültiger Wertebereich.", 400)
    if not isinstance(result["horizons"], list) or not result["horizons"] or len(result["horizons"]) > 8 or any(type(x) is not int or not 1 <= x <= 250 for x in result["horizons"]):
        raise DataError("Beobachtungsfenster: 1–8 Kerzenabstände von 1 bis 250.", 400)
    result["horizons"] = sorted(set(result["horizons"]))
    ids = result.get("dataset_ids", {})
    if not isinstance(ids, dict) or any(k not in result["symbols"] or not isinstance(v, str) or not re.fullmatch(r"[a-f0-9]{64}", v) for k,v in ids.items()):
        raise DataError("Ungültige Dataset-Zuordnung.", 400)
    return result


def trial_plan(dataset, spec):
    """Draw origins by time/coverage alone, never by a later signal or return."""
    bars = source_bars(dataset)["4h"]
    rules = rules_for("4h")
    eligible = [i for i in range(1, len(bars)-1)
        if bars[0].time <= window_start(bars[i].end, rules.lookback_days)]
    if len(eligible) < 5:
        raise DataError("Zu wenig vollständige Vorlaufhistorie für zufällige Forschungsstarts.", 422)
    boundary = eligible[max(1, int(len(eligible)*(1-spec["holdout_fraction"])))]
    discovery = [i for i in eligible if i < boundary]
    # Sampling must not depend on future OHLC, including reserved holdout prices.
    rng = random.Random(f"{spec['seed']}|{dataset['material']['symbol']}|{bars[0].time}|{bars[boundary].time}|{STUDY_VERSION}")
    sampled = sorted(rng.sample(discovery, min(spec["samples"], len(discovery))))
    return {"starts": sampled, "discovery_end": boundary-1, "holdout_start": bars[boundary].end,
        "available_starts": len(discovery), "requested_samples": spec["samples"], "actual_samples": len(sampled)}


def causal_events(dataset, end_index, *, first_index=1, cancelled=lambda: False, progress=None):
    """Complete stream for the requested prefix, unlike the chart's short event scan."""
    all_bars = source_bars(dataset)
    bars, daily = all_bars["4h"], all_bars["1D"]
    rules = rules_for("4h")
    previous = pair(bars[:first_index], rules)
    daily_ends = [b.end for b in daily]
    daily_cache = {}
    for i in range(first_index, min(end_index+1, len(bars))):
        if cancelled():
            return
        before, current = bars[i-1], bars[i]
        partial = bars[0].time > window_start(before.end, rules.lookback_days)
        event, red_break = detect_break(previous, before, current, i, rules, partial=partial)
        if event or red_break:
            red, green = previous["red"], previous["green"]
            # Features use only daily bars already closed at this signal's close.
            d = bisect_right(daily_ends, current.end)
            if d not in daily_cache:
                lane = pair(daily[:d], rules_for("1D")) if d >= 2 else {"red": None, "green": None}
                last = daily[d-1] if d else None
                daily_cache[d] = {"closedAt": last.end if last else None,
                    "close": last.close if last else None,
                    "red": lane["red"].output(last.time) if lane["red"] else None,
                    "green": lane["green"].output(last.time) if lane["green"] else None}
            green_value = green.value(current.time, i) if green else None
            record = {"index": i, "time": current.time, "closedAt": current.end,
                "kind": event["kind"] if event else "red_break", "redBreak": red_break,
                "close": current.close,
                "red": {**red.output(current.time),"value":red.value(current.time,i)} if red else None,
                "green": {**green.output(current.time),"value":green.value(current.time,i)} if green else None,
                "quality": "qualified" if red and green and red.qualified and green.qualified else "provisional",
                "features": {"distance_green_pct": (current.close-green_value)/current.close*100 if green_value else None,
                    "green_violated": green is None or cut(current.low, green_value, False, rules),
                    "ordered_pair": bool(red and green and 0 < green_value < red.value(current.time, i)),
                    "partial_history": partial, "daily": daily_cache[d]}}
            record["id"] = digest({"dataset": dataset["id"], "index": i, "kind": record["kind"], "rules": RULES_VERSION, "study": STUDY_VERSION})
            yield record
        previous = pair(bars[:i+1], rules)
        if progress:
            progress(i-first_index+1, min(end_index+1,len(bars))-first_index)


def line_value(ray, index):
    return ray["a_price"] + ray["slope"] * (index-ray["a_index"])


def find_retest(bars, event, spec, end_index):
    ray = event["red"]
    limit = min(end_index, event["index"]+spec["retest_bars"])
    for i in range(event["index"]+1, limit+1):
        level = line_value(ray, i)
        zone = level*spec["retest_bps"]/10000
        if bars[i].close < level-zone:
            return None, "retest_invalidated"
        if level-zone <= bars[i].low <= level+zone and bars[i].close > level+zone:
            return i, None
    return None, "retest_censored" if limit < event["index"]+spec["retest_bars"] else "no_retest"


def outcomes(bars, entry_index, stop, horizons, cost_bps, end_index):
    """Future data lives here only. Do not feed this result back into signal choice."""
    price = bars[entry_index].open
    cost = cost_bps/10000
    buy = price*(1+cost)
    risk = price-stop if stop is not None and 0 < stop < price else None
    result = {}
    for horizon in horizons:
        last = entry_index+horizon-1
        if last > end_index or last >= len(bars):
            result[str(horizon)] = {"complete": False, "reason": "observation_censored"}
            continue
        path = bars[entry_index:last+1]
        terminal = path[-1].close
        first_stop, first_r1, first_r2, ambiguity = None, None, None, False
        if risk:
            for offset, bar in enumerate(path):
                stopped = bar.low <= stop
                hit1, hit2 = bar.high >= price+risk, bar.high >= price+2*risk
                if first_stop is None and stopped:
                    first_stop = offset
                if first_r1 is None and hit1:
                    first_r1 = offset
                if first_r2 is None and hit2:
                    first_r2 = offset
                if stopped and ((first_r1 == offset) or (first_r2 == offset)):
                    ambiguity = True
        # Strictly earlier: simultaneous high/low crossings are never credited as wins.
        result[str(horizon)] = {"complete": True, "closedAt": path[-1].end,
            "return_pct": (terminal/price-1)*100,
            "net_return_pct": (terminal*(1-cost)/buy-1)*100,
            "mfe_pct": (max(b.high for b in path)/price-1)*100,
            "mae_pct": (min(b.low for b in path)/price-1)*100,
            "terminal_r": (terminal-price)/risk if risk else None,
            "stop_touched": first_stop is not None if risk else None,
            "one_r_before_stop": (first_r1 is not None and (first_stop is None or first_r1 < first_stop)) if risk else None,
            "two_r_before_stop": (first_r2 is not None and (first_stop is None or first_r2 < first_stop)) if risk else None,
            "intrabar_ambiguous": ambiguity}
    return result


def evaluate_trial(dataset, spec, plan, start_index, events):
    bars = source_bars(dataset)["4h"]
    end = plan["discovery_end"]
    search_end = min(end, start_index+spec["search_bars"])
    trial_id = digest({"dataset": dataset["id"], "spec": spec, "start": start_index, "study": STUDY_VERSION})
    base = {"id": trial_id, "datasetId": dataset["id"], "symbol": dataset["material"]["symbol"],
        "startIndex": start_index, "startAt": bars[start_index].end, "partition": "discovery",
        "searchEndAt": bars[search_end].end, "holdoutStart": plan["holdout_start"]}
    event = next((e for e in events if e["redBreak"] and start_index < e["index"] <= search_end), None)
    if event is None:
        return {**base, "status": "no_entry", "reason": "search_censored" if search_end < start_index+spec["search_bars"] else "search_timeout", "variants": []}
    entries = []
    bar_times = [b.time for b in bars]
    for variant in ("breakout", "retest"):
        signal_index, reason = (event["index"], None) if variant == "breakout" else find_retest(bars, event, spec, search_end)
        observation = {"variant": variant, "group": variant+"_"+event["quality"], "quality": event["quality"],
            "eventId": event["id"], "signal": event}
        if signal_index is None:
            entries.append({**observation, "status": "no_entry", "reason": reason})
            continue
        available = bars[signal_index].end+spec["latency_seconds"]
        entry = bisect_left(bar_times, available)
        if entry > end or entry >= len(bars):
            entries.append({**observation, "status": "no_entry", "reason": "execution_censored", "signalAt": bars[signal_index].end})
            continue
        green = event["green"]
        # Fixed initial protection at the setup's original signal, not a later selected line.
        stop = line_value(green, event["index"])*(1-spec["stop_buffer_bps"]/10000) if green else None
        if stop is not None and stop <= 0:
            stop = None
        entries.append({**observation, "status": "observed", "signalAt": bars[signal_index].end,
            "availableAt": available, "entryAt": bars[entry].time, "entryIndex": entry, "entryPrice": bars[entry].open,
            "initialStop": stop, "validRisk": stop is not None and 0 < stop < bars[entry].open,
            "outcomes": outcomes(bars, entry, stop, spec["horizons"], spec["cost_bps"], end)})
    return {**base, "status": "observed" if any(e["status"] == "observed" for e in entries) else "no_entry", "variants": entries}


def summarize(trials, horizons):
    groups = {}
    trial_count=no_entry=0
    for trial in trials:
        trial_count+=1
        no_entry+=trial["status"]=="no_entry"
        for entry in trial["variants"]:
            group = groups.setdefault(entry["group"], {"cases": 0, "observed": 0, "uniqueSignals": set(), "horizons": {}})
            group["cases"] += 1
            if entry["status"] != "observed":
                continue
            group["observed"] += 1
            group["uniqueSignals"].add(entry["eventId"])
            for horizon in horizons:
                measure = group["horizons"].setdefault(str(horizon), {})
                # Deduplicate repeated origins that landed on the same entry.
                outcome = entry["outcomes"][str(horizon)]
                if outcome["complete"]:
                    measure[(entry["eventId"], entry["entryAt"])] = outcome
    for group in groups.values():
        group["uniqueSignals"] = len(group["uniqueSignals"])
        for key, measures in list(group["horizons"].items()):
            values = list(measures.values())
            group["horizons"][key] = {"n": len(values),
                "positive": sum(x["net_return_pct"] > 0 for x in values),
                "median_net_pct": statistics.median(x["net_return_pct"] for x in values) if values else None,
                "median_mfe_pct": statistics.median(x["mfe_pct"] for x in values) if values else None,
                "median_mae_pct": statistics.median(x["mae_pct"] for x in values) if values else None,
                "ambiguous": sum(x["intrabar_ambiguous"] for x in values)}
    return {"trials": trial_count, "no_entry": no_entry, "groups": groups,
        "interpretation": "Explorative Beobachtungen, keine Portfoliorendite. Überlappende Fälle bleiben abhängig; Summen sind nach Signal/Einstieg dedupliziert. Der spätere Holdout bleibt unbenutzt."}
