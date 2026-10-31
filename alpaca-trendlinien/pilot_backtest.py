"""Bounded offline engineering pilot; no provider, queue, orders or portfolio claims."""
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.metadata
import math
from pathlib import Path
import platform
import statistics
import time

from datasets import data_kind, source_bars
from fan_execution import ExecutionRules, entry_contract, holding_close, next_open_time
from fan_geometry import profile, stable_id
from fan_observer import FanObserver, WatchRules, price_at
from fan_study import source_gaps, timestamp
from lab_data import require_convention
from lab_metrics import expected_grid
from models import DataError, NY

VERSION = "tori-bounded-pilot-1"
FAMILIES = ("breakout", "red_retest", "safety_bounce")
MODELS = ("fixed", "original_safety", "fan_safety")


@dataclass(frozen=True)
class PilotSpec:
    start: str = "2023-01-01"
    end: str = "2023-12-31"
    outcome_end: str = "2024-03-31"
    warmup_days: int = 400
    horizons: tuple = (5, 10, 20, 40)
    stop_modes: tuple = ("hard_stop", "close_stop")
    arm_bars: int = 1
    retest_bars: int = 5

    def bounds(self):
        start, end, outcome = timestamp(self.start), timestamp(self.end, upper=True), timestamp(self.outcome_end, upper=True)
        if not start or not end or not outcome or not start < end <= outcome:
            raise DataError("Pilot benötigt geordneten Start, Entry-Ende und Beobachtungsende.", 400)
        if end-start > 367*86400 or outcome-end > 180*86400:
            raise DataError("Technischer Pilot: höchstens zwölf Monate Entries und 180 Tage Nachbeobachtung.", 400)
        if type(self.warmup_days) is not int or not 365 <= self.warmup_days <= 730:
            raise DataError("Pilot-Vorlauf: 365–730 Kalendertage.", 400)
        if not self.horizons or any(type(h) is not int or not 1 <= h <= 40 for h in self.horizons) or len(set(self.horizons)) != len(self.horizons):
            raise DataError("Pilot-Horizonte: eindeutige ganze Handelstage von 1 bis 40.", 400)
        if not self.stop_modes or set(self.stop_modes)-{"hard_stop", "close_stop"} or len(set(self.stop_modes)) != len(self.stop_modes):
            raise DataError("Pilot-Stopmodus: hard_stop / close_stop.", 400)
        WatchRules(arm_bars=self.arm_bars, retest_bars=self.retest_bars)
        warmup = int((datetime.fromtimestamp(start, NY)-timedelta(days=self.warmup_days)).timestamp())
        return warmup, start, end, outcome


class PilotObserver:
    """Reuse the chart's causal Master geometry and existing red-episode observer.

    Safety bounce uses only the preceding snapshot, with a reaction/rearm and
    global contact-gap cooldown. It never awards a third touch on its own bar.
    """
    def __init__(self, symbol, rules=None, watch=None):
        self.rules = rules or profile("master")
        self.watch = watch or WatchRules(arm_bars=1, retest_bars=5)
        self.red = FanObserver(symbol, "4h", self.rules, self.watch)
        self.previous = None
        self.snapshot = None
        self.armed = set()
        self.last_bounce = -10000

    def gap(self, bar):
        self.previous = self.snapshot = None
        self.armed.clear()
        return self.red.gap(bar)

    def push(self, bar):
        old, previous = self.snapshot, self.previous
        events = self.red.push(bar)
        snap = self.red.last_snapshot
        self.snapshot, self.previous = snap, bar
        signals = []
        for event in events:
            if event["kind"] == "entry_signal":
                signal = deepcopy(event)
                signal["family"] = "breakout" if signal["variant"] == "breakout" else "red_retest"
                signal["subtype"] = ("immediate" if signal["cleanAt"] == signal["breakAt"] else "delayed") if signal["family"] == "breakout" else "original_red"
                # Keep original break context, but do not enter using a stale
                # Safety which the current shared geometry no longer validates.
                signal["breakSafety"] = deepcopy(signal["safety"])
                signal["breakInitialStop"] = signal["initialStop"]
                signal["safety"] = deepcopy(snap["green"])
                green = signal["safety"]
                signal["initialStop"] = (math.floor(green["value"]*(1-self.watch.stop_buffer_pct/100)/self.rules.tick)*self.rules.tick
                                         if green and 0 < green["value"] < bar.close else None)
                signal["validRisk"] = signal["initialStop"] is not None and 0 < signal["initialStop"] < bar.close
                signal["features"]["safetyContacts"] = green["contacts"] if green else None
                signals.append(signal)
        if old and old.get("ready") and previous:
            index, vol = snap["referenceIndex"], snap["atr"]
            options = []
            for line in old["greens"]:
                if not line["qualified"] or line["slope"] <= 0:
                    continue
                before, level = price_at(line, index-1), price_at(line, index)
                if previous.close >= before+self.rules.reaction_atr*old["atr"]:
                    self.armed.add(line["id"])
                touched = bar.low <= level+self.rules.contact_atr*vol
                valid = (level > 0 and bar.low >= level-self.rules.wick_atr*vol and
                         min(bar.open, bar.close) >= level-self.rules.body_atr*vol)
                if (line["id"] in self.armed and index-self.last_bounce >= self.rules.contact_gap and
                    previous.close > before and touched and valid and bar.close > max(level, bar.open)):
                    options.append(line)
                if not valid:
                    self.armed.discard(line["id"])
            if options:
                line = max(options, key=lambda x:(price_at(x, index), x["contacts"], x["id"]))
                safety = deepcopy(line)
                safety["value"] = price_at(line, index)
                stop = math.floor(safety["value"]*(1-self.watch.stop_buffer_pct/100)/self.rules.tick)*self.rules.tick
                signals.append({"id": stable_id([VERSION,"bounce",line["id"],bar.end]),
                    "kind":"entry_signal", "family":"safety_bounce", "variant":"safety_bounce", "subtype":"qualified_safety",
                    "signalAt":bar.end, "knownAt":bar.end, "signalClose":bar.close, "candidateAt":old["sourceClose"],
                    "cohort":"qualified", "line":deepcopy(line), "safety":safety,
                    "initialStop":stop, "validRisk":0 < stop < bar.close,
                    "features":{"atr":vol,"contacts":line["contacts"],"safetyContacts":line["contacts"]}})
                self.last_bounce = index
                self.armed.clear()
            # Do not grow per-line state forever or resurrect absent invalid lines.
            self.armed.intersection_update(line["id"] for line in snap.get("greens", []))
        return events, signals, snap


def scan(symbol, rows, start, end, *, rules=None, watch=None, progress=lambda **kw:None):
    observer = PilotObserver(symbol, rules, watch)
    gaps = source_gaps(rows, rows[-1].end, "4h")
    signals, timeline, journal = [], [], []
    raw_counts, duplicate_counts = Counter(), Counter()
    for i, bar in enumerate(rows):
        if i in gaps:
            journal.extend(observer.gap(bar))
        events, found, snap = observer.push(bar)
        if snap and snap.get("ready"):
            timeline.append({"closedAt":bar.end,"time":bar.time,"index":snap["referenceIndex"],
                "close":bar.close,"atr":snap["atr"],"green":deepcopy(snap["green"]),
                "gap":i in gaps,"gapAt":gaps.get(i)})
        if start <= bar.end <= end:
            journal.extend(events)
            groups = defaultdict(list)
            for signal in found:
                raw_counts[signal["family"]] += 1
                groups[signal["family"],signal["cohort"]].append(signal)
            for (family, cohort), alternatives in groups.items():
                chosen = min(alternatives,key=lambda s:(-s["line"]["contacts"],-s["line"].get("reactionContacts",0),s["candidateAt"],s["id"]))
                chosen["alternativeSignalIds"] = sorted(s["id"] for s in alternatives if s["id"] != chosen["id"])
                duplicate_counts[family] += len(alternatives)-1
                signals.append(chosen)
        if i % 100 == 0:
            progress(completed=i,total=len(rows),phase="scan")
    return signals, timeline, journal, {"rawSignals":dict(raw_counts),"same_close_duplicates":dict(duplicate_counts),"sourceGaps":len(gaps)}


def _level(safety, index, tick=.01):
    return math.floor(price_at(safety,index)*.997/tick)*tick


def execute_path(signal, entry, fine, timeline, cutoff, horizon, model, mode):
    """Source-close stop updates activate at a later expected 5m open.

    Close-stop deliberately uses the SAME buffered ratcheted stop as hard-stop;
    it is not the different Safety-minus-ATR rule in the supplied prose.
    """
    if model not in MODELS or mode not in ("hard_stop","close_stop"):
        raise DataError("Unbekanntes Pilot-Exitmodell.",400)
    result = {"model":model,"stopMode":mode,"horizon":horizon,"status":entry["status"],
        "reason":entry.get("reason"),"netPnl":None,"netR":None,"stopEvents":[],"exitAt":None}
    if entry["status"] != "filled":
        return result
    r = ExecutionRules(**entry["rules"])
    at, buy, stop = entry["entryAt"], entry["entryFill"], entry["initialStop"]
    target = holding_close(at,horizon)
    limit = min(cutoff,target)
    result.update(status="open",reason="observation_boundary",plannedTimeExit=target,
                  mfeR=0.,maeR=0.,finalStop=stop)
    t_ends = [s["closedAt"] for s in timeline]
    # Censor at the first missing source close, not a later recovery candle.
    missing_source = next((s.get("gapAt",s["closedAt"]) for s in timeline
                           if s["gap"] and s.get("gapAt",s["closedAt"]) > at), None)
    ti = bisect_right(t_ends, signal["signalAt"])
    fi = bisect_left([b.time for b in fine],at)
    pending, close_order = [], None
    last = None
    side_cost = r.spread_bps/20000+r.slippage_bps/10000

    def finish(bar, raw, reason, at_open=False):
        sell = raw*(1-side_cost)
        pnl = entry["quantity"]*(sell-buy)-2*r.fee_per_order
        return {**result,"status":"closed","reason":reason,"exitAt":bar.time if at_open else bar.end,
            "mfeR":max(result["mfeR"],(raw-buy)/entry["initialRisk"]),
            "maeR":min(result["maeR"],(raw-buy)/entry["initialRisk"]),
            "fillBarAt":bar.time,"atOpen":at_open,"exitPrice":raw,"exitFill":sell,
            "netPnl":pnl,"netR":pnl/entry["plannedRisk"],"finalStop":stop}

    for stamp in expected_grid(at,limit):
        if missing_source is not None and missing_source <= stamp:
            return {**result,"status":"censored","reason":"source_gap","missingAt":missing_source,"finalStop":stop}
        if fi >= len(fine) or fine[fi].time != stamp or fine[fi].end != stamp+300:
            return {**result,"status":"censored","reason":"missing_fine_path","missingAt":stamp,"finalStop":stop}
        bar = fine[fi]
        fi += 1
        while ti < len(timeline) and timeline[ti]["closedAt"] <= stamp:
            state = timeline[ti]
            ti += 1
            # A source close reached before entry cannot retroactively manage it.
            if state["closedAt"] <= at:
                continue
            effective = next_open_time(state["closedAt"]+r.latency_seconds)
            if state["gap"]:
                return {**result,"status":"censored","reason":"source_gap","missingAt":state["closedAt"],"finalStop":stop}
            if mode == "close_stop" and state["close"] < stop and close_order is None:
                close_order = {"effectiveAt":effective,"knownAt":state["closedAt"]}
            if model != "fixed":
                safety = signal["safety"] if model == "original_safety" else state["green"]
                if safety and safety["slope"] > 0 and 0 < price_at(safety,state["index"]) < state["close"]:
                    candidate = _level(safety,state["index"],r.tick)
                    if candidate > stop:
                        pending.append({"newStop":candidate,"knownAt":state["closedAt"],"effectiveAt":effective,
                                        "lineId":safety["id"]})
        if close_order and close_order["effectiveAt"] <= stamp:
            result["closeDecision"] = close_order
            return finish(bar,bar.open,"close_stop",True)
        while pending and pending[0]["effectiveAt"] <= stamp:
            change = pending.pop(0)
            if change["newStop"] > stop:
                stop = change["newStop"]
                result["stopEvents"].append(change)
        if mode == "hard_stop":
            if bar.open <= stop:
                return finish(bar,bar.open,"stop_gap",True)
            if bar.low <= stop:
                # Do not credit the unknown high-before-low order of the exit bar.
                result["maeR"] = min(result["maeR"],(stop-buy)/entry["initialRisk"])
                return finish(bar,stop,"stop")
        result["mfeR"] = max(result["mfeR"],(bar.high-buy)/entry["initialRisk"])
        result["maeR"] = min(result["maeR"],(bar.low-buy)/entry["initialRisk"])
        if bar.end == target:
            return finish(bar,bar.close,"time")
        last = bar
    return {**result,"status":"open" if cutoff < target else "censored",
            "reason":"observation_boundary" if cutoff < target else "missing_time_exit_bar",
            "markPrice":last.close if last else None,"lastObservedAt":last.end if last else at,"finalStop":stop}


def observations(entry, fine, cutoff, horizons):
    result = {}
    if entry["status"] != "filled":
        return result
    times = [b.time for b in fine]
    start = bisect_left(times,entry["entryAt"])
    for h in horizons:
        wanted = holding_close(entry["entryAt"],h)
        limit = min(wanted,cutoff)
        rows = fine[start:bisect_left(times,limit)]
        available = {b.time for b in rows}
        complete = wanted <= cutoff and rows and rows[-1].end == wanted and all(t in available for t in expected_grid(entry["entryAt"],wanted))
        result[str(h)] = {"complete":bool(complete),"closedAt":wanted,"close":rows[-1].close if complete else None,
            "returnPct":(rows[-1].close/entry["entryFill"]-1)*100 if complete else None,
            "mfeR":max((b.high-entry["entryFill"])/entry["initialRisk"] for b in rows) if rows else None,
            "maeR":min((b.low-entry["entryFill"])/entry["initialRisk"] for b in rows) if rows else None,
            "meaning":"Price path observation, including movement after hypothetical stop; not executed P/L"}
    return result


def code_digest():
    root = Path(__file__).parent
    names = ("pilot_backtest.py","fan_geometry.py","fan_master.py","fan_observer.py","fan_execution.py",
             "fan_study.py","lab_metrics.py","lab_data.py","lab_splits.py","market_calendar.py","models.py")
    hashes = {name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in names}
    return {"files":hashes,"digest":stable_id(hashes)}


def run(dataset, spec=None, execution=None, *, progress=lambda **kw:None):
    spec, execution = spec or PilotSpec(), execution or ExecutionRules()
    warmup,start,end,cutoff = spec.bounds()
    if execution.target_r:
        raise DataError("Pilot führt keine festen Gewinnziele aus.",400)
    require_convention(dataset)
    if data_kind(dataset) != "market":
        raise DataError("Der Markt-Pilot akzeptiert keine synthetischen Datasets.",422)
    if dataset["material"]["feed"] != "sip" or dataset["material"]["adjustment"] != "split":
        raise DataError("Pilot-Referenz benötigt einheitlich SIP/split.",422)
    started = time.perf_counter()
    frames = {tf:[b for b in rows if b.time >= warmup and b.end <= cutoff] for tf,rows in source_bars(dataset).items()}
    if not all(frames.get(tf) for tf in ("5m","4h","1D")):
        raise DataError("5m/4h/1D fehlen für den Pilot.",422)
    from fan_study import schedule
    expected_source=list(schedule(start,end,"4h"))
    if frames["4h"][0].end > start-320*86400 or not expected_source or frames["4h"][-1].end < expected_source[-1][1] or frames["5m"][-1].end < expected_source[-1][1]:
        raise DataError("Zu wenig Vorgeschichte oder Entry-Fenster nicht abgedeckt.",422)
    watch = WatchRules(arm_bars=spec.arm_bars,retest_bars=spec.retest_bars)
    rules = profile("master")
    signals,timeline,journal,diagnostics = scan(dataset["material"]["symbol"],frames["4h"],start,end,watch=watch,progress=progress)
    cases = []
    daily_ends = [b.end for b in frames["1D"]]
    for i,signal in enumerate(signals):
        entry = entry_contract(signal,frames["5m"],cutoff,execution)
        known_daily = frames["1D"][:bisect_right(daily_ends,signal["signalAt"])]
        last200=known_daily[-200:]
        daily_clean=len(last200)==200 and not source_gaps(last200,last200[-1].end,"1D")
        context = {"dailyClose":known_daily[-1].close if known_daily else None,
                   "dailySma200":sum(b.close for b in last200)/200 if daily_clean else None,
                   "filterApplied":False}
        paths = {}
        for model in MODELS:
            for mode in spec.stop_modes:
                for h in spec.horizons:
                    paths[f"{model}:{mode}:{h}"] = execute_path(signal,entry,frames["5m"],timeline,cutoff,h,model,mode)
        cases.append({"id":stable_id([VERSION,dataset["id"],signal["id"]]),"signal":signal,"entry":entry,
                      "context":context,"observations":observations(entry,frames["5m"],cutoff,spec.horizons),"paths":paths})
        progress(completed=i+1,total=len(signals),phase="outcomes")
    summary = summarize(cases,spec)
    manifest = {"version":VERSION,"datasetId":dataset["id"],"symbol":dataset["material"]["symbol"],
        "feed":"sip","adjustment":"split","timeframe":"4h","spec":asdict(spec),"geometry":asdict(rules),
        "watch":asdict(watch),"execution":asdict(execution),"code":code_digest(),
        "runtime":{"python":platform.python_version(),"packages":{name:importlib.metadata.version(name)
                   for name in ("duckdb","exchange_calendars","tzdata","pandas")}},
        "dataBounds":{tf:{"count":len(b),"first":b[0].time,"lastClose":b[-1].end} for tf,b in frames.items() if b},
        "warmupFrom":warmup,"entryStart":start,"entryEnd":end,"outcomeCutoff":cutoff,
        "purpose":"Technical development pilot on previously available data; no independent validation or portfolio P/L",
        "decisions":{"safety":"current valid tight Safety at entry signal; original red-break Safety archived separately; bounce from preceding qualified snapshot",
            "closeStop":"source close below same percentage-buffered ratchet as hard stop, next expected 5m open after latency",
            "updates":"at source closes, effective only after latency; no retroactive stop changes",
            "bounce":"prior A+ Safety, reaction rearm, body/wick bounds and five-source-bar cooldown",
            "signals":"all previously known red episodes; same close/cohort deduplicated; families may overlap"}}
    checks = audit(cases,start,end)
    return {"manifest":manifest,"runId":stable_id(manifest),"summary":summary,"diagnostics":diagnostics,
        "audit":checks,"cases":cases,"journal":journal,"timeline":timeline,
        "elapsedSeconds":time.perf_counter()-started}


def summarize(cases,spec):
    result = {}
    for family in FAMILIES:
        selected = [c for c in cases if c["signal"]["family"]==family]
        groups = {}
        for model in MODELS:
            for mode in spec.stop_modes:
                for h in spec.horizons:
                    key = f"{model}:{mode}:{h}"
                    paths = [c["paths"][key] for c in selected]
                    closed = [p for p in paths if p["status"]=="closed"]
                    groups[key] = {"statuses":dict(Counter(p["status"] for p in paths)),"closed":len(closed),
                        "positive":sum(p["netPnl"]>0 for p in closed),
                        "meanNetR":statistics.mean(p["netR"] for p in closed) if closed else None,
                        "exitReasons":dict(Counter(p["reason"] for p in closed))}
        result[family] = {"signals":len(selected),"entryStatuses":dict(Counter(c["entry"]["status"] for c in selected)),
            "cohorts":dict(Counter(c["signal"]["cohort"] for c in selected)),
            "subtypes":dict(Counter(c["signal"]["subtype"] for c in selected)),"comparisons":groups}
    return result


def audit(cases,start,end):
    errors = []
    for case in cases:
        s,e = case["signal"],case["entry"]
        if not start <= s["signalAt"] <= end or s["line"]["knownAt"] >= s["signalAt"]:
            errors.append([case["id"],"signal_time_or_line_availability"])
        for line in (s["line"],s.get("safety")):
            if line and (line["knownAt"] > s["signalAt"] or line["b_time"] > s["signalAt"] or
                         any(p.get("known_at",0) > s["signalAt"] for p in line.get("contactPoints",[]))):
                errors.append([case["id"],"future_pivot_or_safety"])
        if e["status"] != "filled":
            continue
        if not e["entryAt"] >= s["signalAt"]+e["rules"]["latency_seconds"] or e["entryPrice"] <= e["initialStop"]:
            errors.append([case["id"],"entry_contract"])
        if (e["plannedCash"] > e["rules"]["capital"]+1e-7 or
            e["plannedRisk"] > e["rules"]["capital"]*e["rules"]["risk_fraction"]+1e-7):
            errors.append([case["id"],"cash_or_risk_budget"])
        for key,p in case["paths"].items():
            previous = e["initialStop"]
            for change in p["stopEvents"]:
                if change["newStop"] <= previous or change["effectiveAt"] < change["knownAt"]+e["rules"]["latency_seconds"]:
                    errors.append([case["id"],key,"stop_causality"])
                previous = change["newStop"]
            if p["status"]=="closed":
                side=e["rules"]["spread_bps"]/20000+e["rules"]["slippage_bps"]/10000
                expected=e["quantity"]*(p["exitPrice"]*(1-side)-e["entryFill"])-2*e["rules"]["fee_per_order"]
                if p["exitAt"] < e["entryAt"] or abs(expected-p["netPnl"]) > 1e-7:
                    errors.append([case["id"],key,"cash_or_exit_time"])
    return {"passed":not errors,"errors":errors,"casesChecked":len(cases),
            "scope":"signal timing, line knowledge, ratchet, latency and independent cash recomputation"}
