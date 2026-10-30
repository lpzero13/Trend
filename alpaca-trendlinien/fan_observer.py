"""Closed-bar long scenarios. Frozen episodes never inherit replacement lines."""
from copy import deepcopy
from dataclasses import asdict, dataclass
import math

from fan_geometry import FanRules, create_engine, stable_id
from models import DataError

VERSION = "tori-fan-observer-1"


@dataclass(frozen=True)
class WatchRules:
    clean_atr: float = .15
    approach_atr: float = 1.
    retest_atr: float = .15
    stop_buffer_pct: float = .3
    arm_bars: int = 20
    retest_bars: int = 60
    max_active: int = 256
    safety_choice: str = "tight"

    def __post_init__(self):
        if self.safety_choice not in ("tight", "main"):
            raise DataError("Safety-Auswahl: tight oder main.", 400)
        for k, lo, hi in (("clean_atr", 0, 2), ("approach_atr", 0, 10),
                          ("retest_atr", 0, 2), ("stop_buffer_pct", 0, 10)):
            v = getattr(self, k)
            if type(v) not in (int, float) or not math.isfinite(v) or not lo <= v <= hi:
                raise DataError(f"Ungültiger Beobachtungsparameter {k}.", 400)
        for k, lo, hi in (("arm_bars", 1, 500), ("retest_bars", 1, 1000), ("max_active", 10, 1000)):
            if type(getattr(self, k)) is not int or not lo <= getattr(self, k) <= hi:
                raise DataError(f"Ungültiger Beobachtungsparameter {k}.", 400)


def price_at(line, index):
    return line["a_price"] + line["slope"]*(index-line["a_index"])


def cohort(line, at_time, rules):
    if line["contacts"] == 2:
        return "two"
    return "qualified" if at_time-line["a_time"] >= rules.min_age_days*86400 else "three_young"


class FanObserver:
    def __init__(self, symbol, timeframe, rules=None, watch=None):
        self.rules, self.watch = rules or FanRules(), watch or WatchRules()
        self.engine = create_engine(symbol, timeframe, self.rules)
        self.symbol, self.timeframe = symbol, timeframe
        self.active = {}
        self.seen = set()
        self.previous = None
        self.last_snapshot = None

    def _event(self, kind, bar, scenario=None, **detail):
        identity = scenario["id"] if scenario else self.symbol+":"+self.timeframe
        return {"id": stable_id([VERSION, identity, kind, bar.end, detail.get("variant")]),
                "kind": kind, "knownAt": bar.end, "closedAt": bar.end,
                "time": bar.time, "symbol": self.symbol, "timeframe": self.timeframe,
                "scenarioId": scenario["id"] if scenario else None, **deepcopy(detail)}

    def gap(self, next_bar):
        """An unknown source interval cannot be crossed by geometry or a scenario."""
        result = [self._event("invalidated", next_bar, s, reason="source_gap") for s in self.active.values()]
        result.append(self._event("source_gap", next_bar))
        self.active.clear()
        self.engine.reset_history()  # retain global source-bar coordinates
        self.previous = None
        return result

    def _signal(self, scenario, bar, variant):
        line = scenario["brokenLine"]
        stop = scenario["initialStop"]
        return self._event("entry_signal", bar, scenario, variant=variant,
                           cohort=scenario["cohort"], signalAt=bar.end,
                           line=line, safety=scenario["safety"], initialStop=stop,
                           breakAt=scenario["breakAt"], cleanAt=scenario["cleanAt"],
                           candidateAt=scenario["candidateAt"], qualifiedAt=scenario["qualifiedAt"],
                           touchAt=scenario.get("touchAt"),
                           signalClose=bar.close, validRisk=stop is not None and 0 < stop < bar.close,
                           features={"atr": self.engine.atr, "contacts": line["contacts"],
                                     "reactionContacts": line["reactionContacts"],
                                     "ageDays": (scenario["breakAt"]-line["a_time"])/86400,
                                     "distanceATR": (bar.close-price_at(line, self.engine.index))/self.engine.atr,
                                     "safetyContacts": scenario["safety"]["contacts"] if scenario["safety"] else None})

    def push(self, bar):
        previous, index = self.previous, self.engine.index+1
        self.engine.push(bar)
        self.previous = bar
        snap = self.engine.snapshot()
        self.last_snapshot = snap
        if not snap["ready"]:
            return []
        vol = snap["atr"]
        events = []
        # Inspect lines that existed BEFORE this close; new pivots cannot improve
        # the grade of a breakout on this very candle.
        for key, scenario in list(self.active.items()):
            line = scenario["line"]
            level = price_at(line, index)
            if scenario["state"] == "active":
                horizon = self.rules.action_lookback_days if self.rules.algorithm == "master" else self.rules.lookback_days
                if self.rules.algorithm == "master" and bar.end-line["a_time"] > horizon*86400:
                    events.append(self._event("expired", bar, scenario, reason="line_horizon"))
                    del self.active[key]
                    continue
                crossed = previous and previous.close <= price_at(line, index-1) and bar.close > level
                if crossed:
                    frozen = deepcopy(line)
                    frozen["value"] = level
                    frozen["knownAt"] = scenario["lastKnownAt"]
                    green = deepcopy(snap.get("mainSafety", next(iter(snap["greens"]), None)) if self.watch.safety_choice == "main" else snap["green"])
                    if green and not 0 < green["value"] < bar.close:
                        green = None
                    stop = math.floor(green["value"]*(1-self.watch.stop_buffer_pct/100)/self.rules.tick)*self.rules.tick if green else None
                    scenario.update(state="broken", brokenLine=frozen, breakIndex=index,
                                    breakAt=bar.end, cleanAt=None, initialStop=stop, safety=green,
                                    cohort=cohort(frozen, scenario["lastKnownAt"], self.rules),
                                    retestSent=False, touchAt=None)
                    events.append(self._event("break", bar, scenario, line=frozen,
                                              cohort=scenario["cohort"], safety=green, initialStop=stop))
                elif max(bar.open, bar.close) > level+(self.rules.body_atr*vol if self.rules.algorithm == "master" else 0)+1e-9 or bar.high > level+self.rules.wick_atr*vol+1e-9:
                    events.append(self._event("invalidated", bar, scenario, reason="wick_or_body_violation"))
                    del self.active[key]
                    continue
                else:
                    # Contact upgrades become available only for NEXT close.
                    pts = line["contactPoints"]
                    for p in self.engine.pivots[True]:
                        if p.index-pts[-1]["index"] >= line.get("contactGap", self.rules.contact_gap) and abs(p.price-price_at(line, p.index)) <= self.rules.contact_atr*p.atr:
                            away = any(price_at(line, i)-b.close >= self.rules.reaction_atr*pts[-1]["atr"]
                                       for i, b, _ in self.engine.rows if pts[-1]["index"] < i < p.index)
                            pts.append(asdict(p))
                            line["reactionContacts"] += int(away)
                    line["contacts"] = len(pts)
                    line["value"] = level
                    line["qualified"] = cohort(line, bar.end, self.rules) == "qualified"
                    line["span_days"] = (bar.end-line["a_time"])/86400
                    if line["qualified"] and scenario["qualifiedAt"] is None:
                        scenario["qualifiedAt"] = bar.end
                        events.append(self._event("qualified", bar, scenario, line=line))
                    scenario["lastKnownAt"] = bar.end
                    if not scenario["nearSent"] and 0 <= level-bar.close <= self.watch.approach_atr*vol:
                        scenario["nearSent"] = True
                        events.append(self._event("approaching", bar, scenario, line=line))
                    if bar.end-line["a_time"] > self.rules.lookback_days*86400:
                        events.append(self._event("expired", bar, scenario, reason="line_horizon"))
                        del self.active[key]
                    continue
            if scenario["state"] == "broken":
                stop = scenario["initialStop"]
                if stop is not None and bar.close <= stop:
                    events.append(self._event("invalidated", bar, scenario, reason="safety_close_before_retest"))
                    del self.active[key]
                    continue
                if scenario["cleanAt"] is None:
                    if index-scenario["breakIndex"] > self.watch.arm_bars:
                        events.append(self._event("expired", bar, scenario, reason="clean_close_timeout"))
                        del self.active[key]
                        continue
                    if bar.close >= level+self.watch.clean_atr*vol:
                        scenario["cleanAt"], scenario["cleanIndex"] = bar.end, index
                        events.append(self._signal(scenario, bar, "breakout"))
                elif index > scenario["cleanIndex"]:
                    if index-scenario["cleanIndex"] > self.watch.retest_bars:
                        events.append(self._event("expired", bar, scenario, reason="retest_timeout"))
                        del self.active[key]
                        continue
                    if scenario["touchAt"] is None and bar.low <= level+self.watch.retest_atr*vol and bar.high >= level-self.watch.retest_atr*vol:
                        scenario["touchAt"] = bar.end
                        events.append(self._event("retest_touch", bar, scenario, line=scenario["brokenLine"]))
                    if not scenario["retestSent"] and scenario["touchAt"] and bar.close > bar.open and bar.close >= level+self.watch.clean_atr*vol:
                        events.append(self._signal(scenario, bar, "retest"))
                        scenario["retestSent"] = True
                        del self.active[key]
        for line in snap["reds"]:
            if line["id"] in self.seen or line["contacts"] < 2:
                continue
            self.seen.add(line["id"])
            identity = stable_id([VERSION, self.symbol, self.timeframe, line["id"], bar.end, asdict(self.watch)])
            scenario = {"id": identity, "line": deepcopy(line), "state": "active", "candidateAt": bar.end,
                        "qualifiedAt": bar.end if line["qualified"] else None,
                        "lastKnownAt": bar.end, "nearSent": 0 <= line["value"]-bar.close <= self.watch.approach_atr*vol}
            self.active[line["id"]] = scenario
            events.append(self._event("candidate", bar, scenario, line=line, approaching=scenario["nearSent"]))
        while len(self.active) > self.watch.max_active:
            key = next(iter(self.active))
            events.append(self._event("expired", bar, self.active.pop(key), reason="capacity"))
        return events
