"""Reproducible period sampling and isolated post-entry close observations.

No outcome is used by EntryScanner, sampling, or entry/line selection. No exits,
cost model, stop execution or portfolio returns are calculated here.
"""
from datetime import datetime, timedelta
import random
import statistics

from datasets import digest, source_bars
from market_calendar import CALENDAR_VERSION, calendar, session_close
from models import DataError, NY

VERSION = "tori-forward-closes-1"


def sample_windows(bars, first, end, spec, symbol):
    """Choose nonoverlapping, complete search windows using time/index only."""
    width = spec["search_bars"]
    candidates = list(range(first, end-width+2))
    if not candidates:
        raise DataError("Tori-Zeitraum ist kürzer als das Suchfenster. Suchkerzen oder Datumsgrenzen anpassen.", 422)
    rng = random.Random(f"{VERSION}|{spec['seed']}|{symbol}|{bars[first].time}|{bars[end].end}|{width}")
    rng.shuffle(candidates)
    chosen = []
    for start in candidates:
        if all(abs(start-other) >= width for other in chosen):
            chosen.append(start)
            if len(chosen) == spec["samples"]:
                break
    windows = [{"id": digest({"symbol": symbol, "start": bars[s].time, "width": width, "seed": spec["seed"]}),
                "scan_start": s, "discovery_end": s+width-1, "candles": width,
                "scanStartAt": bars[s-1].end, "scanEndAt": bars[s+width-1].end} for s in sorted(chosen)]
    return {"windows": windows, "starts": [w["scan_start"]-1 for w in windows],
            "requested_samples": spec["samples"], "actual_samples": len(windows), "candles": len(windows)*width,
            "samplingVersion": VERSION, "samplingNote": "nonoverlapping search windows; forward observations may overlap"}


def forward_closes(daily, entry_at, price, horizons, cutoff):
    """H = H-th XNYS session strictly AFTER the New York entry date.

    Calendar targets never slide when a provider day is missing. Only closing
    prices are inspected, avoiding pre-entry daily highs/lows and intrabar fills.
    """
    day = datetime.fromtimestamp(entry_at, NY).date()
    last = day+timedelta(days=max(horizons)*3+30)
    sessions = []
    for year in range(day.year, last.year+1):
        start = max(day+timedelta(days=1), day.replace(year=year, month=1, day=1))
        end = min(last, day.replace(year=year, month=12, day=31))
        if start <= end:
            sessions += [str(s.date()) for s in calendar(year).sessions_in_range(str(start), str(end))]
    rows = {str(datetime.fromtimestamp(b.time, NY).date()): b for b in daily}
    result = {}
    for horizon in horizons:
        target = sessions[horizon-1]
        expected = session_close(target)
        base = {"targetDate": target, "targetCloseAt": expected, "unit": "XNYS_sessions_after_entry_date"}
        if expected > cutoff:
            result[str(horizon)] = {**base, "complete": False, "reason": "observation_censored"}
            continue
        missing = [s for s in sessions[:horizon] if s not in rows or rows[s].end > cutoff]
        if missing:
            result[str(horizon)] = {**base, "complete": False, "reason": "missing_daily_sessions", "missingDates": missing}
            continue
        bar = rows[target]
        result[str(horizon)] = {**base, "complete": True, "closedAt": bar.end,
                               "close": bar.close, "return_pct": (bar.close/price-1)*100}
    return result


def observe_cases(cases, dataset, spec, plan, *, random_window=False):
    """Mark first entry PER VARIANT/window, then evaluate in a separate pass."""
    first = {}
    for case in cases:
        for variant in case["variants"]:
            if variant["status"] == "observed":
                name = variant["variant"]
                first[name] = min(first.get(name, variant["entryAt"]), variant["entryAt"])
    daily = source_bars(dataset)["1D"]
    # The holdout boundary is independent of any narrower entry-search date range.
    cutoff = plan["observation_end"]
    for case in cases:
        for variant in case["variants"]:
            if variant["status"] != "observed":
                continue
            selected = not random_window or variant["entryAt"] == first[variant["variant"]]
            variant["observationSelected"] = selected
            if selected:
                variant["forward"] = forward_closes(daily, variant["entryAt"], variant["entryPrice"], spec["horizons"], cutoff)


def summarize_observations(trials, horizons):
    groups = {}
    unique_all = set()
    selected_count = 0
    for trial in trials:
        for variant in trial["variants"]:
            if not variant.get("observationSelected"):
                continue
            selected_count += 1
            identity = (trial["datasetId"], variant["entryAt"])
            unique_all.add(identity)
            group = groups.setdefault(variant["group"], {})
            # Deduplicate within group BEFORE aggregating returns or counts.
            group.setdefault(identity, (variant, trial["symbol"]))
    result = {}
    for name, unique in groups.items():
        evaluated = {}
        for h in horizons:
            observations = [(identity, v.get("forward", {}).get(str(h), {}), symbol) for identity, (v, symbol) in unique.items()]
            complete = [(identity, o, symbol) for identity, o, symbol in observations if o.get("complete")]
            values = [o["return_pct"] for _, o, _ in complete]
            overlapping = set()
            by_dataset = {}
            for identity, o, _ in complete:
                by_dataset.setdefault(identity[0], []).append((identity, o["closedAt"]))
            for entries in by_dataset.values():
                entries.sort()
                for i, (identity, end) in enumerate(entries):
                    for next_id, _ in entries[i+1:]:
                        if next_id[1] > end:
                            break
                        overlapping.update((identity, next_id))
            evaluated[str(h)] = {"n": len(values), "incomplete": len(observations)-len(values),
                "positive": sum(v > 0 for v in values), "negative": sum(v < 0 for v in values),
                "flat": sum(v == 0 for v in values), "mean_pct": statistics.mean(values) if values else None,
                "median_pct": statistics.median(values) if values else None,
                "overlapping_entries": len(overlapping)}
        result[name] = {"uniqueEntries": len(unique), "horizons": evaluated}
    return {"version": VERSION, "calendar": CALENDAR_VERSION, "selectedRecords": selected_count,
            "uniqueEntriesAcrossVariants": len(unique_all), "groups": result,
            "interpretation": "Unadjusted close changes after trading sessions; no exits, costs or portfolio P/L. Groups and overlapping paths are dependent."}
