"""Internal replayable watchlist. No outcomes, provider calls or notifications.

Confirmed old action lines are tested before newly created action lines enter
the book. A newly confirmed green line may be used after that same close.
"""
from bisect import bisect_left
from copy import deepcopy
from datetime import datetime, timedelta
import hashlib
from pathlib import Path

from datasets import digest, source_bars
from entry_geometry import VERSION, RULES, Geometry, at, measure, equivalent, violation
from lab_data import session_bounds, require_convention
from lab_metrics import expected_grid
from lab_splits import sessions_between
from models import NY
from safety_strategy import StrategyContext
from tori_entries import atr


def engine_signature():
    root = Path(__file__).parent
    return {name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in
            ("entry_geometry.py", "entry_watch.py", "tori_entries.py", "trendlines.py", "safety_strategy.py")}


def execution_time(closed_at):
    earliest = closed_at+RULES["latency_seconds"]
    day = datetime.fromtimestamp(closed_at, NY).date()
    for date in sessions_between(str(day), str(day+timedelta(days=12))):
        opened, closed = session_bounds(date)
        target = max(opened, earliest)
        target = opened+max(0, (target-opened+299)//300)*300
        if target < closed:
            return target
    raise ValueError("No scheduled execution session")


class WatchReplay:
    def __init__(self, dataset, model, start_at, cutoff):
        require_convention(dataset)
        self.symbol, self.dataset_id = dataset["material"]["symbol"], dataset["id"]
        self.sources = {tf: [b for b in rows if b.end <= cutoff] for tf, rows in source_bars(dataset).items()}
        self.bars = self.sources["4h"]
        self.fine = {b.time: b for b in self.sources["5m"]}
        self.context = StrategyContext(self.sources, cutoff)
        self.geometry = Geometry(self.bars, self.symbol, model)
        self.model, self.start_at, self.cutoff = model, start_at, cutoff
        self.candidates, self.events, self.messages, self.entries, self.executions = [], [], [], [], []
        self.pending, self.seen_entries = [], set()
        self.i = next((i for i, b in enumerate(self.bars) if b.end >= start_at), len(self.bars))-1
        self.known_until = self.bars[self.i].end if self.i >= 0 else 0
        self.coverage = {"bars": 0, "alternativeLines": 0}
        if self.i >= 0:
            initial = self.geometry.proposals(self.i)
            self.add_candidates(initial, self.i, upper=False)
            self.add_candidates(initial, self.i, upper=True)

    def transition(self, c, state, i, reason=None):
        if c["state"] == state:
            return
        c["state"] = state
        event = {"eventKey": digest([VERSION, self.symbol, self.model, c["id"], state, self.bars[i].end]),
                 "candidateId": c["id"], "state": state, "knownAt": self.bars[i].end,
                 "sourceIndex": i, "reason": reason, "upper": c["upper"]}
        self.events.append(event)

    def greens(self, i):
        return [c for c in self.candidates if not c["upper"] and c["active"] and
                c["lastFeatures"]["contacts"] >= 2 and 0 < at(c["ray"], i) < self.bars[i].close]

    def add_candidates(self, proposals, i, upper=None):
        vol = atr(self.bars[max(0, i-14):i+1]) or 1
        for c in proposals:
            if upper is not None and c["upper"] != upper:
                continue
            old = next((p for p in self.candidates if p["active"] and p["breakIndex"] is None and equivalent(p, c, i, vol)), None)
            if old:
                old["alternatives"] += 1
                self.coverage["alternativeLines"] += 1
                continue
            if c["upper"]:
                green = max(self.greens(i), key=lambda g: at(g["ray"], i), default=None)
                if green:
                    c["armGreen"] = deepcopy(green["ray"])
                    c["armGreenCandidate"] = green["id"]
            self.candidates.append(c)
            if c["lastFeatures"]["contacts"] >= 2:
                self.transition(c, "structure", i)

    def features(self, c, i):
        f = deepcopy(c["lastFeatures"])
        f["projectionSensitivityATR"] = .05*(1+2*max(0, i-c["ray"]["b_index"])/(c["ray"]["b_index"]-c["ray"]["a_index"]))
        vol = atr(self.bars[max(0, i-14):i+1])
        f.update(distanceATR=(at(c["ray"], i)+c["width"]-self.bars[i].close)/vol,
                 lineAgeDays=(self.bars[i].end-c["ray"]["a_time"])/86400)
        return f

    def explain(self, c, state, i):
        context = self.context.known_context(self.bars[i].end)
        f = self.features(c, i)
        text = {"near": "Kurs nähert sich einer beobachteten 4h-Struktur; noch kein bestätigter Einstieg.",
                "breakout": "4h-Ausbruch bestätigt; Ausführung und Absicherung werden getrennt geprüft.",
                "pullback": "Rücklauf an die ursprünglich gebrochene 4h-Zone wird beobachtet.",
                "retest": "Spätere 4h-Kerze hält die ursprüngliche Zone und schließt positiv darüber.",
                "bounce": "Separater experimenteller Bounce an einer bereits bekannten grünen Struktur."}[state]
        return {"eventKey": digest([VERSION, self.symbol, self.model, c["id"], state]),
                "candidateId": c["id"], "symbol": self.symbol, "model": self.model,
                "state": state, "knownAt": self.bars[i].end, "features": f,
                "dailyContext": context["daily"], "weeklyContext": context["weekly"],
                "lastDailyClose": context["lastDailyClose"], "lastWeeklyClose": context["lastWeeklyClose"],
                "explanation": text, "action": "review_only", "brokerAction": None}

    def notify(self, c, state, i):
        if state not in c["notified"]:
            self.messages.append(self.explain(c, state, i))
            c["notified"].append(state)
            if state == "near":
                c["nearAt"] = self.bars[i].end

    def signal(self, c, family, i, trigger):
        if family in c.setdefault("families", []):
            return
        c["families"].append(family)
        green = c if family == "bounce" else max(self.greens(i), key=lambda g: at(g["ray"], i), default=None)
        vol = atr(self.bars[max(0, i-14):i+1])
        if green is None:
            self.executions.append({"candidateId": c["id"], "signalAt": self.bars[i].end,
                                    "family": family, "status": "no_known_safety"})
            return
        red = deepcopy(c["ray"])
        safety = {**deepcopy(green["ray"]), "contacts": green["lastFeatures"]["contacts"]}
        red["contacts"] = c["lastFeatures"]["contacts"]
        point = {"symbol": self.symbol, "datasetId": self.dataset_id, "model": self.model,
                 "profile": self.model, "family": family, "sourceSetupId": c["id"],
                 "signalAt": self.bars[i].end, "signalIndex": i,
                 "availableAt": self.bars[i].end+RULES["latency_seconds"],
                 "entryAt": execution_time(self.bars[i].end), "trigger": trigger,
                 "red": red, "green": safety, "initialStop": at(safety, i),
                 "signalATR": vol, "features": self.features(c, i),
                 "armGreen": deepcopy(c["armGreen"]), "armedAt": c["knownAt"],
                 "nearAt": c.get("nearAt"), "signalWidth": c["width"],
                 "eventKey": digest([VERSION, self.symbol, self.model, family, self.bars[i].end])}
        self.pending.append(point)

    def resolve(self, known_until):
        self.known_until = max(self.known_until, known_until)
        for e in list(self.pending):
            when = e["entryAt"]
            if when+300 > known_until:
                continue
            self.pending.remove(e)
            b = self.fine.get(when)
            reason = None
            if b is None:
                reason = "missing_expected_execution"
            else:
                stop = e["initialStop"]-max(.01, e["signalATR"]*RULES["stop_buffer_atr"])
                intervening = list(expected_grid(e["signalAt"], when))
                if any(t not in self.fine for t in intervening):
                    reason = "unknown_interim_safety"
                elif any(self.fine[t].low <= stop for t in intervening) or b.open <= stop:
                    reason = "interim_or_open_safety_broken"
                elif b.open <= e["trigger"]:
                    reason = "open_not_above_signal_trigger"
                elif stop <= 0:
                    reason = "invalid_risk"
            if reason:
                self.executions.append({"candidateId": e["sourceSetupId"], "family": e["family"],
                                        "signalAt": e["signalAt"], "status": reason})
                continue
            identity = (e["family"], when)
            if identity in self.seen_entries:
                continue
            self.seen_entries.add(identity)
            e["entryPrice"] = b.open
            e["id"] = digest([VERSION, self.symbol, self.model, e["family"], when])
            contract = self.context.entry_contract(e)
            e["rawSafety"] = e["initialStop"]
            e["initialStop"] = contract["initialStop"]
            e["strictEligible"] = contract["eligible"]
            e["blockedBy"] = contract["blockedBy"]
            e["context"] = {k: contract["context"][k] for k in ("daily", "weekly", "monthly", "lastDailyClose", "lastWeeklyClose")}
            e["netRoomR"] = contract["netRoomR"]
            arm = e["armGreen"]
            e["armSafetyValid"] = bool(arm and not any(violation(arm, self.bars[j], j, False, 0)
                for j in range(arm["b_index"], e["signalIndex"]+1)))
            e["armStop"] = at(arm, e["signalIndex"])-max(.01, e["signalATR"]*.25) if e["armSafetyValid"] else None
            e["signalRiskATR"] = (b.open-e["initialStop"])/e["signalATR"]
            e["armRiskATR"] = (b.open-e["armStop"])/e["signalATR"] if e["armStop"] else None
            self.entries.append(e)

    def step(self, i):
        if i != self.i+1:
            raise ValueError("Replay must process each source bar once")
        self.i = i
        bar = self.bars[i]
        self.resolve(bar.end)
        self.coverage["bars"] += 1
        old = [c for c in self.candidates if c["active"]]
        for c in old:
            if i-c["createdIndex"] > RULES["lifetime_bars"]:
                c["active"] = False
                self.transition(c, "expired", i, "fixed_lifetime")
                continue
            if abs((bar.high if c["upper"] else bar.low)-at(c["ray"], i)) <= c["width"]+1e-7:
                c["lastFeatures"] = measure(c, self.bars, i)
            if not c["upper"] and violation(c["ray"], bar, i, False, c["width"], self.model == "swing_zone"):
                c["active"] = False
                self.transition(c, "invalid", i, "green_violated")
        proposals = self.geometry.proposals(i)
        self.add_candidates(proposals, i, upper=False)
        for c in old:
            if not c["active"]:
                continue
            if not c["upper"]:
                if (c["lastFeatures"]["contacts"] >= 2 and bar.low <= at(c["ray"], i)+c["width"] and
                    bar.close > at(c["ray"], i)+c["width"] and bar.close > bar.open and bar.close > self.bars[i-1].high):
                    self.notify(c, "bounce", i)
                    self.signal(c, "bounce", i, at(c["ray"], i)+c["width"])
                continue
            top, bottom = at(c["ray"], i)+c["width"], at(c["ray"], i)-c["width"]
            if c["breakIndex"] is None:
                crossed = bar.close > top and self.bars[i-1].close <= at(c["ray"], i-1)+c["width"]
                if crossed and c["lastFeatures"]["contacts"] >= 2 and bar.close > bar.open and bar.close > self.bars[i-1].close:
                    c["breakIndex"] = i
                    c["horizontal"] = max(b.high for b in self.bars[max(0, i-6):i])
                    self.transition(c, "breakout", i)
                    self.notify(c, "breakout", i)
                    self.signal(c, "breakout", i, top)
                elif violation(c["ray"], bar, i, True, c["width"], self.model == "swing_zone"):
                    c["active"] = False
                    self.transition(c, "invalid", i, "drift_or_unconfirmed_violation")
            if c["breakIndex"] is not None and c["active"]:
                if bar.close < bottom:
                    c["active"] = False
                    self.transition(c, "invalid", i, "closed_back_below_action_zone")
                    continue
                if bar.close > max(top, c["horizontal"]) and bar.close > bar.open:
                    self.signal(c, "horizontal", i, max(top, c["horizontal"]))
                if i > c["breakIndex"] and bar.low <= top and bar.high >= bottom:
                    self.transition(c, "pullback", i)
                    self.notify(c, "pullback", i)
                    if bar.close > top and bar.close > bar.open:
                        self.transition(c, "retest", i)
                        self.notify(c, "retest", i)
                        self.signal(c, "retest", i, top)
        self.add_candidates(proposals, i, upper=True)
        vol = atr(self.bars[max(0, i-14):i+1])
        near = [c for c in self.candidates if c["active"] and c["upper"] and c["breakIndex"] is None and "near" not in c["notified"] and
                c["lastFeatures"]["contacts"] >= 2 and 0 <= at(c["ray"], i)+c["width"]-bar.close <= RULES["near_atr"]*vol]
        near.sort(key=lambda c: (self.features(c, i)["distanceATR"], -min(4, c["lastFeatures"]["contacts"]), self.features(c, i)["projectionSensitivityATR"], c["id"]))
        for c in near[:RULES["notifications_per_bar"]]:
            self.transition(c, "near", i)
            self.notify(c, "near", i)

    def run(self):
        for i in range(self.i+1, len(self.bars)):
            self.step(i)
        self.resolve(self.cutoff)
        return self.result()

    def result(self):
        return {"version": VERSION, "symbol": self.symbol, "datasetId": self.dataset_id, "model": self.model,
                "asOf": self.cutoff, "startAt": self.start_at, "entries": self.entries,
                "events": self.events, "messages": self.messages, "pending": self.pending,
                "executions": self.executions, "coverage": self.coverage, "candidates": self.candidates}

    def state(self):
        end = self.known_until
        prefix = {tf: [b.__dict__ for b in rows if b.end <= end] for tf, rows in self.sources.items()}
        return deepcopy({**self.result(), "i": self.i, "knownUntil": end, "prefixHash": digest(prefix),
                         "rules": RULES, "engine": engine_signature(), "checked": sorted(self.geometry.checked), "seenEntries": sorted(self.seen_entries)})

    def restore(self, saved):
        end = saved["knownUntil"]
        prefix = {tf: [b.__dict__ for b in rows if b.end <= end] for tf, rows in self.sources.items()}
        if saved["version"] != VERSION or saved["rules"] != RULES or saved["engine"] != engine_signature() or saved["prefixHash"] != digest(prefix) or saved["symbol"] != self.symbol or saved["model"] != self.model or saved["startAt"] != self.start_at:
            raise ValueError("Changed rules/source prefix; a new replay generation is required")
        for name in ("entries", "events", "messages", "pending", "executions", "coverage", "candidates", "i"):
            setattr(self, name, deepcopy(saved[name]))
        self.geometry.checked = {tuple(x) for x in saved["checked"]}
        self.seen_entries = {tuple(x) for x in saved["seenEntries"]}
        self.known_until = end
