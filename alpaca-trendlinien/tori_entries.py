"""Optional, causal entry study. Frozen setups coexist with newly selected lines.

This module never selects exits, sends orders, or evaluates forward returns.
All thresholds are versioned experiment assumptions, not validated trade advice.
"""
from bisect import bisect_left, bisect_right
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timedelta
import math

from datasets import digest, source_bars
from models import Bar, DataError, NY
from trendlines import DAY, pair, rules_for, touch, window_start

VERSION = "tori-entries-1"
VARIANTS = ("breakout", "horizontal", "retest")
DEFAULTS = {
    "line_policy": "tracked", "safety_selection": "nearest_confirmed", "start_date": "", "end_date": "",
    "setup_bars": 60, "min_contacts": 2, "contact_gap_bars": 2,
    "min_age_days": 7, "breakout_bps": 10,
    "min_body_atr": .25, "min_body_fraction": .5, "min_close_location": .65,
    "max_safety_pct": 3, "max_safety_atr": 2,
    "horizontal_bars": 20, "context": "daily", "min_room_r": 2,
    "sampling": "full", "observe_forward": False,
}


def validate(value):
    if not isinstance(value, dict) or set(value)-set(DEFAULTS):
        raise DataError("Unbekannte Tori-Einstiegsparameter.", 400)
    result = {**DEFAULTS, **value}
    if result["sampling"] not in ("full", "random") or type(result["observe_forward"]) is not bool:
        raise DataError("Ungültige Tori-Zeitraum-/Beobachtungsauswahl.", 400)
    if result["line_policy"] not in ("tracked", "snapshot") or result["context"] not in ("daily", "topdown", "off"):
        raise DataError("Ungültige Tori-Linien-/Kontextauswahl.", 400)
    if result["safety_selection"] not in ("nearest_confirmed", "chart"):
        raise DataError("Ungültige Tori-Safety-Auswahl.", 400)
    for name, low, high in (("setup_bars", 1, 500), ("min_contacts", 2, 10),
                           ("contact_gap_bars", 1, 20), ("horizontal_bars", 3, 250)):
        if type(result[name]) is not int or not low <= result[name] <= high:
            raise DataError(f"{name}: ganze Zahl zwischen {low} und {high} erforderlich.", 400)
    for name, low, high in (("min_age_days", 0, 365), ("breakout_bps", 0, 500),
                           ("min_body_atr", 0, 5), ("min_body_fraction", 0, 1),
                           ("min_close_location", 0, 1), ("max_safety_pct", .01, 50),
                           ("max_safety_atr", .01, 20), ("min_room_r", 0, 10)):
        if type(result[name]) not in (int, float) or not math.isfinite(result[name]) or not low <= result[name] <= high:
            raise DataError(f"{name}: ungültiger Tori-Wertebereich.", 400)
    for name in ("start_date", "end_date"):
        try:
            if not isinstance(result[name], str) or (result[name] and datetime.strptime(result[name], "%Y-%m-%d").strftime("%Y-%m-%d") != result[name]):
                raise ValueError()
        except (ValueError, TypeError):
            raise DataError("Tori-Datum als JJJJ-MM-TT in New Yorker Börsenzeit angeben.", 400) from None
    if result["start_date"] and result["end_date"] and result["start_date"] > result["end_date"]:
        raise DataError("Tori-Startdatum liegt nach dem Enddatum.", 400)
    return result


def plan(dataset, spec):
    bars = source_bars(dataset)["4h"]
    eligible = [i for i in range(1, len(bars)) if bars[0].time <= window_start(bars[i-1].end, 365)]
    if len(eligible) < 5:
        raise DataError("Zu wenig Vorlauf für die vollständige Tori-Untersuchung.", 422)
    boundary = eligible[max(1, int(len(eligible)*(1-spec["holdout_fraction"])))]
    first, end = eligible[0], boundary-1
    options = spec["tori"]
    if options["start_date"]:
        at = datetime.strptime(options["start_date"], "%Y-%m-%d").replace(tzinfo=NY).timestamp()
        first = max(first, bisect_left([b.time for b in bars], at))
    if options["end_date"]:
        until = (datetime.strptime(options["end_date"], "%Y-%m-%d")+timedelta(days=1)).replace(tzinfo=NY).timestamp()
        end = min(end, bisect_left([b.end for b in bars], until)-1)
    if first > end:
        raise DataError("Kein Tori-Zeitraum nach Vorlauf und vor reserviertem Holdout. Datum/Historie prüfen.", 422)
    result = {"mode": VERSION, "scan_start": first, "discovery_end": end,
            "scanStartAt": bars[first-1].end, "scanEndAt": bars[end].end,
            "observation_end": bars[boundary-1].end,
            "holdout_start": bars[boundary].end, "starts": [first-1],
            "actual_samples": 0, "requested_samples": 0, "candles": end-first+1}
    if options.get("sampling") == "random":
        from tori_observations import sample_windows
        result.update(sample_windows(bars, first, end, spec, dataset["material"]["symbol"]))
    return result


def value(ray, index):
    return ray["a_price"]+ray["slope"]*(index-ray["a_index"])


def atr(bars, period=14):
    if len(bars) < period+1:
        return None
    return sum(max(b.high-b.low, abs(b.high-a.close), abs(b.low-a.close))
               for a, b in zip(bars[-period-1:-1], bars[-period:]))/period


def pivots(bars, upper):
    """2+2 confirmed swings: right-hand confirmation must already be closed."""
    prices = [b.high if upper else b.low for b in bars]
    return [prices[i] for i in range(2, len(prices)-2)
            if all(prices[i] > prices[j] if upper else prices[i] < prices[j]
                   for j in (i-2, i-1, i+1, i+2))]


def structure(bars):
    highs, lows = pivots(bars, True), pivots(bars, False)
    if len(highs) < 2 or len(lows) < 2:
        return "unknown"
    if highs[-1] > highs[-2] and lows[-1] > lows[-2]:
        return "up"
    if highs[-1] < highs[-2] and lows[-1] < lows[-2]:
        return "down"
    return "mixed"


def aggregate(daily, monthly=False):
    """Only complete XNYS weeks/months, including holiday/early-close calendars."""
    from market_calendar import calendar, session_close
    groups = {}
    for bar in daily:
        day = datetime.fromtimestamp(bar.time, NY).date()
        key = day.replace(day=1) if monthly else day-timedelta(days=day.weekday())
        groups.setdefault(key, []).append(bar)
    result = []
    cutoff = daily[-1].end if daily else 0
    for start, rows in groups.items():
        end = ((start.replace(day=28)+timedelta(days=4)).replace(day=1) if monthly else start+timedelta(days=7))-timedelta(days=1)
        sessions = calendar(start.year).sessions_in_range(str(start), str(end))
        expected = {str(d.date()) for d in sessions}
        actual = {str(datetime.fromtimestamp(b.time, NY).date()) for b in rows}
        if not expected or actual != expected:
            continue
        close = session_close(max(expected))
        if close > cutoff:
            continue
        result.append(Bar(rows[0].time, close, rows[0].open, max(b.high for b in rows),
                          min(b.low for b in rows), rows[-1].close, sum(b.volume for b in rows)))
    return result


def contact_count(ray, bars, upper, gap):
    last_touch, count = -gap, 0
    rules = rules_for("4h")
    for i in range(ray["a_index"], len(bars)):
        if touch(bars[i].high if upper else bars[i].low, value(ray, i), rules):
            if i-last_touch >= gap:
                count += 1
            # A continuous run of touching candles is one contact episode.
            last_touch = i
    return count


def check(name, passed, measured=None, required=True):
    return {"name": name, "state": "unknown" if passed is None else "pass" if passed else "fail",
            "value": measured, "required": required}


class EntryScanner:
    """Advance in one step or batches: every source candle follows the same path."""
    def __init__(self, dataset, spec, scan_plan, emit=lambda item: None):
        self.dataset, self.spec, self.plan = dataset, spec, scan_plan
        self.options = spec["tori"]
        sources = source_bars(dataset)
        self.bars, self.daily, self.hourly = (sources[k] for k in ("4h", "1D", "1h"))
        self.daily_ends = [b.end for b in self.daily]
        self.hour_times = [b.time for b in self.hourly]
        self.last = scan_plan["scan_start"]-1
        self.cases, self.known, self.active = {}, set(), set()
        self.last_saved = {}
        self.emit = emit
        self.context_cache = {}
        self.coverage = {"candles": 0, "withoutPair": 0}

    def journal(self, case, kind, at, **detail):
        event = {"id": digest({"case": case["id"], "kind": kind, "at": at, "detail": detail}),
                 "setupId": case["id"], "kind": kind, "time": at, "closedAt": at,
                 "redBreak": kind == "tori_break", **detail}
        self.emit({"event": event})

    def save(self, case):
        case["status"] = "observed" if any(v["status"] == "observed" for v in case["variants"]) else "pending" if any(v["status"] == "pending" for v in case["variants"]) else "no_entry"
        fingerprint = digest(case)
        if self.last_saved.get(case["id"]) == fingerprint:
            return
        self.last_saved[case["id"]] = fingerprint
        self.emit({"trial": deepcopy(case)})

    def context(self, at):
        count = bisect_right(self.daily_ends, at)
        if count not in self.context_cache:
            daily = self.daily[:count]
            lines = pair(daily, rules_for("1D")) if count >= 2 else {"red": None, "green": None}
            last = daily[-1] if daily else None
            lane = {"closedAt": last.end if last else None, "close": last.close if last else None,
                    "red": lines["red"].output(last.time) if lines["red"] else None,
                    "green": lines["green"].output(last.time) if lines["green"] else None}
            states = {"1D": structure(daily), "1W": structure(aggregate(daily)), "1M": structure(aggregate(daily, True))}
            self.context_cache[count] = {"daily": lane, "structure": states}
        return self.context_cache[count]

    def arm(self, i):
        prefix = self.bars[:i]
        lines = pair(prefix, rules_for("4h"))
        red, green = lines["red"], lines["green"]
        if self.options["safety_selection"] == "nearest_confirmed":
            alternatives = lines.get("greens", [])
            candidates = [r for r in alternatives if r.valid and 0 < r.value(prefix[-1].time) < prefix[-1].close]
            if candidates:
                green = max(candidates, key=lambda ray: ray.value(prefix[-1].time))
        if red is None or green is None:
            self.coverage["withoutPair"] += 1
            return
        red, green = red.output(prefix[-1].time), green.output(prefix[-1].time)
        anchors = [{k: ray[k] for k in ("a_time", "a_price", "b_time", "b_price")} for ray in (red, green)]
        identity = digest({"dataset": self.dataset["id"], "anchors": anchors, "mode": VERSION,
                           "options": self.options, "latency": self.spec["latency_seconds"],
                           "retest": [self.spec["retest_bars"], self.spec["retest_bps"]],
                           **({"window": self.plan["windowId"]} if "windowId" in self.plan else {})})
        if identity in self.known:
            return
        self.known.add(identity)
        context = self.context(prefix[-1].end)
        signal = {"id": identity, "kind": "tori_setup", "index": i-1, "time": prefix[-1].time, "closedAt": prefix[-1].end,
                  "red": red, "green": green, "close": prefix[-1].close, "features": deepcopy(context)}
        initial_qualified = (contact_count(red,prefix,True,self.options["contact_gap_bars"]) >= 3 and
                             contact_count(green,prefix,False,self.options["contact_gap_bars"]) >= 3 and
                             (prefix[-1].end-red["a_time"])/DAY >= 7)
        quality = "qualified" if initial_qualified else "provisional"
        case = {"id": identity, "datasetId": self.dataset["id"], "symbol": self.dataset["material"]["symbol"],
                "mode": VERSION, "startAt": prefix[-1].end, "startIndex": i-1, "partition": "discovery",
                "holdoutStart": self.plan["holdout_start"], "armedIndex": i-1,
                "frozen": {"red": red, "green": green}, "signal": signal,
                "variants": [{"variant": v, "status": "pending", "phase": "breakout", "signal": deepcopy(signal),
                              "armedSignal": deepcopy(signal), "entryMode": "tori",
                              "eventId": identity, "signalAt": prefix[-1].end, "checks": [], "quality": quality,
                              "group": v+"_"+quality} for v in VARIANTS]}
        if "windowId" in self.plan:
            case["windowId"] = self.plan["windowId"]
        self.cases[identity] = case
        self.active.add(identity)
        self.journal(case, "tori_armed", prefix[-1].end, anchors=anchors)
        self.save(case)

    def base_checks(self, case, i, prefix):
        bar = self.bars[i]
        red, green = case["frozen"]["red"], case["frozen"]["green"]
        volatility = atr(prefix)
        rc = contact_count(red, prefix, True, self.options["contact_gap_bars"])
        gc = contact_count(green, prefix, False, self.options["contact_gap_bars"])
        age = (bar.end-red["a_time"])/DAY
        level, safety = value(red, i), value(green, i)
        body = bar.close-bar.open
        span = bar.high-bar.low
        context = self.context(bar.end)
        required_frames = () if self.options["context"] == "off" else ("1D", "1W", "1M") if self.options["context"] == "topdown" else ("1D",)
        states = [context["structure"][tf] for tf in required_frames]
        context_ok = None if not states or "unknown" in states else all(s != "down" for s in states)
        checks = [check("confirmed_anchors", red["valid"] and green["valid"]),
                  check("red_contacts", rc >= self.options["min_contacts"], rc),
                  check("green_contacts", gc >= 2, gc),
                  check("line_age", age >= self.options["min_age_days"], age),
                  check("ordered_safety", 0 < safety < level and bar.low >= safety),
                  check("close_above_red", bar.close > level*(1+self.options["breakout_bps"]/10000), bar.close-level),
                  check("positive_body", body > 0, body),
                  check("body_atr", None if not volatility else body/volatility >= self.options["min_body_atr"], body/volatility if volatility else None),
                  check("body_fraction", span > 0 and body/span >= self.options["min_body_fraction"], body/span if span else None),
                  check("close_location", span > 0 and (bar.close-bar.low)/span >= self.options["min_close_location"], (bar.close-bar.low)/span if span else None),
                  check("context", context_ok, context["structure"], bool(required_frames))]
        risk = bar.close-safety
        checks += self.risk_checks(bar.close, safety, volatility)
        highs = pivots(prefix[-250:], True)
        daily_red = context["daily"]["red"]
        resistances = [p for p in highs if p > bar.close]
        if daily_red and daily_red["value"] > bar.close:
            resistances.append(daily_red["value"])
        room = (min(resistances)-bar.close)/risk if resistances and risk > 0 else None
        checks.append(check("room", room >= self.options["min_room_r"] if room is not None else None,
                            {"r": room, "resistance": min(resistances) if resistances else None}, bool(resistances)))
        quality = "qualified" if rc >= 3 and gc >= 3 and age >= 7 else "provisional"
        return checks, quality, volatility, context

    def risk_checks(self, price, safety, volatility):
        distance = price-safety
        return [check("safety_distance_pct", 0 < distance/price*100 <= self.options["max_safety_pct"], distance/price*100),
                check("safety_distance_atr", None if not volatility else 0 < distance/volatility <= self.options["max_safety_atr"], distance/volatility if volatility else None)]

    @staticmethod
    def blocked(checks):
        return [c["name"] for c in checks if c["required"] and c["state"] != "pass"]

    def close_variant(self, case, variant, reason, at, status="rejected"):
        variant.update(status=status, reason=reason, decidedAt=at)
        self.journal(case, "tori_"+status, at, variant=variant["variant"], reason=reason)

    def confirm(self, case, variant, i, checks, volatility):
        variant.update(checks=checks, signalAt=self.bars[i].end)
        if self.blocked(checks):
            reason = ",".join(self.blocked(checks))
            if variant["variant"] == "breakout":
                self.close_variant(case, variant, reason, self.bars[i].end)
            elif variant.get("waitingFor") != reason:
                variant["waitingFor"] = reason
                self.journal(case, "tori_wait", self.bars[i].end, variant=variant["variant"], reason=reason)
            return
        available = self.bars[i].end+self.spec["latency_seconds"]
        room = next(c["value"] for c in checks if c["name"] == "room")
        variant.pop("waitingFor", None)
        variant.update(phase="execution", availableAt=available, safetyAtSignal=value(case["frozen"]["green"], i),
                       triggerAtSignal=value(case["frozen"]["red"], i), atrAtSignal=volatility, resistanceAtSignal=room["resistance"])
        self.journal(case, "tori_confirmed", self.bars[i].end, variant=variant["variant"], availableAt=available)

    def executions(self, case, until):
        for variant in case["variants"]:
            if variant["status"] != "pending" or variant["phase"] != "execution":
                continue
            index = bisect_left(self.hour_times, variant["availableAt"])
            if index >= len(self.hourly) or self.hourly[index].time > until:
                continue
            bar = self.hourly[index]
            # Only the opening price is known here. Never inspect this hour's later high/low.
            checks = self.risk_checks(bar.open, variant["safetyAtSignal"], variant["atrAtSignal"])
            red = variant["triggerAtSignal"]
            checks.append(check("execution_above_trigger", bar.open > max(red, case["ceiling"] if variant["variant"] == "horizontal" else 0)))
            known_hours = [b for b in self.hourly if b.time >= variant["signalAt"] and b.end+self.spec["latency_seconds"] <= bar.time]
            known_source = [(i,b) for i,b in enumerate(self.bars[:self.last+1]) if b.end >= variant["signalAt"] and b.end+self.spec["latency_seconds"] <= bar.time]
            safe = not any(b.low < variant["safetyAtSignal"] for b in known_hours) and not any(b.low < value(case["frozen"]["green"],i) for i,b in known_source)
            checks.append(check("interim_safety", safe))
            resistance = variant["resistanceAtSignal"]
            if resistance:
                risk = bar.open-variant["safetyAtSignal"]
                checks.append(check("execution_room", risk > 0 and (resistance-bar.open)/risk >= self.options["min_room_r"]))
            variant["executionChecks"] = checks
            if self.blocked(checks):
                self.close_variant(case, variant, "execution:"+",".join(self.blocked(checks)), bar.time)
            else:
                variant.update(status="observed", entryAt=bar.time, entryPrice=bar.open,
                               initialStop=variant["safetyAtSignal"], validRisk=True, executionTimeframe="1h")
                self.journal(case, "tori_entry", bar.time, variant=variant["variant"], price=bar.open)
            self.save(case)

    def process(self, case, i):
        bar, before = self.bars[i], self.bars[i-1]
        red, green = case["frozen"]["red"], case["frozen"]["green"]
        # Execute previously confirmed signals before using this candle's later low/close.
        self.executions(case, bar.end)
        pending = [v for v in case["variants"] if v["status"] == "pending" and v["phase"] != "execution"]
        if not pending:
            return
        if i-case["armedIndex"] > self.options["setup_bars"]:
            for v in pending: self.close_variant(case, v, "setup_expired", bar.end, "expired")
            self.save(case)
            return
        if bar.low < value(green, i):
            for v in pending: self.close_variant(case, v, "green_violated", bar.end)
            self.save(case)
            return
        if "breakIndex" not in case:
            if not (before.close <= value(red, i-1) and bar.close > value(red, i)):
                return
            prefix = self.bars[:i]
            checks, quality, volatility, context = self.base_checks(case, i, prefix)
            features = deepcopy(context)
            if self.options["line_policy"] == "snapshot":
                features["daily"] = deepcopy(case["signal"]["features"]["daily"])
                features["dailyAtBreak"] = deepcopy(context["daily"])
            signal = {"id": case["id"], "kind": "red_break", "index": i, "time": bar.time, "closedAt": bar.end, "close": bar.close,
                      "red": {**red, "value": value(red, i)}, "green": {**green, "value": value(green, i)},
                      "features": features}
            case.update(breakIndex=i, signal=signal, ceiling=max(b.high for b in prefix[-self.options["horizontal_bars"]:]))
            self.journal(case, "tori_break", bar.end, ceiling=case["ceiling"])
            # Structural requirements are shared; momentum/risk can improve at a later confirmation.
            structural = [c for c in checks if c["name"] in ("confirmed_anchors", "red_contacts", "green_contacts", "line_age", "ordered_safety")]
            for v in pending:
                v.update(signal=deepcopy(signal), quality=quality, group=v["variant"]+"_"+quality, checks=checks)
                if self.blocked(structural):
                    self.close_variant(case, v, ",".join(self.blocked(structural)), bar.end)
                elif v["variant"] == "breakout":
                    self.confirm(case, v, i, checks, volatility)
                else:
                    v["phase"] = v["variant"]
            # Horizontal confirmation may occur on the breakout candle itself; retest may not.
        for v in case["variants"]:
            if v["status"] != "pending" or v["phase"] not in ("horizontal", "retest"):
                continue
            if i-case["breakIndex"] > self.spec["retest_bars"]:
                self.close_variant(case, v, "confirmation_expired", bar.end, "expired")
                continue
            level = value(red, i)
            zone = level*self.spec["retest_bps"]/10000
            if bar.close < level-zone:
                self.close_variant(case, v, "red_lost", bar.end)
                continue
            ready = bar.close > case["ceiling"]*(1+self.options["breakout_bps"]/10000) if v["phase"] == "horizontal" else (
                i > case["breakIndex"] and level-zone <= bar.low <= level+zone and bar.close > level+zone)
            if ready:
                checks, _, volatility, _ = self.base_checks(case, i, self.bars[:i])
                checks.append(check("horizontal_confirmed" if v["phase"] == "horizontal" else "retest_held", True,
                                    case["ceiling"] if v["phase"] == "horizontal" else level))
                self.confirm(case, v, i, checks, volatility)
        self.save(case)

    def advance(self, end_index, cancelled=lambda: False, progress=None):
        end_index = min(end_index, self.plan["discovery_end"])
        for i in range(self.last+1, end_index+1):
            if cancelled():
                return False
            if self.options["line_policy"] == "tracked" or i == self.plan["scan_start"]:
                self.arm(i)
            for identity in sorted(self.active):
                self.process(self.cases[identity], i)
                if not any(v["status"] == "pending" for v in self.cases[identity]["variants"]):
                    self.active.discard(identity)
            self.last = i
            self.coverage["candles"] += 1
            if progress: progress(i-self.plan["scan_start"]+1, self.plan["candles"])
        return True

    def finish(self):
        at = self.bars[self.last].end
        for identity in sorted(self.active):
            case = self.cases[identity]
            for variant in case["variants"]:
                if variant["status"] == "pending":
                    self.close_variant(case, variant, "window_end", at, "censored")
            self.save(case)
        self.active.clear()


def summarize(trials):
    groups = {}
    total = 0
    for trial in trials:
        total += 1
        for variant in trial["variants"]:
            key = variant.get("group", variant["variant"]+"_provisional")
            group = groups.setdefault(key, {"setups": 0, "entries": 0, "rejected": 0, "expired": 0, "censored": 0, "pending": 0, "reasons": {}, "_entries": set()})
            group["setups"] += 1
            status = variant["status"]
            group["entries" if status == "observed" else status] += 1
            if status == "observed":
                group["_entries"].add((trial["datasetId"], variant["entryAt"]))
            if variant.get("reason"):
                group["reasons"][variant["reason"]] = group["reasons"].get(variant["reason"], 0)+1
    for group in groups.values():
        group["uniqueEntries"] = len(group.pop("_entries"))
    return {"mode": VERSION, "setups": total, "groups": groups,
            "interpretation": "Nur Einstiege. Varianten und überlappende Linienpaare sind abhängig; keine Ausstiege, Trefferquote oder Depot-P/L."}
