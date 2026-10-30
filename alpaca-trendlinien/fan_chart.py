"""Fan overlays for existing chart payloads; no provider or database writes."""
from copy import deepcopy
from dataclasses import asdict
import math

from fan_geometry import VERSION, analyze, profile, stable_id
from fan_observer import price_at
from fan_study import source_gaps
from lab_data import NORMALIZATION
from models import Bar, DataError

ENGINES = ("legacy", "fan_extreme", "fan_local", "fan_master")


def selected_engine(query):
    values = query.get("engine", ["legacy"])
    if len(values) != 1 or values[0] not in ENGINES:
        raise DataError("Analysemodell: legacy, fan_extreme, fan_local oder fan_master.", 400)
    return values[0]


def apply(payload, engine="fan_extreme", *, config=None, case=None):
    if engine not in ENGINES[1:]:
        raise DataError("Ungültiger Fächermodus.", 400)
    roots = engine.removeprefix("fan_")
    rules = profile(roots, (config or {}).get("geometry", {}))
    lanes = {}
    for tf, view in payload["charts"].items():
        rows = [Bar(**b) for b in view["bars"]]
        meta = payload["sources"][tf]
        regular = meta.get("normalization") == NORMALIZATION or tf == "1W" and payload["sources"]["1D"].get("normalization") == NORMALIZATION
        gaps = source_gaps(rows, rows[-1].end, tf) if regular else {}
        try:
            lane = analyze(rows, tf, symbol=payload["symbol"], rules=rules, gaps=gaps,
                           context_clean_atr=(config or {}).get("watch", {}).get("clean_atr", .15))
        except DataError as exc:
            if exc.status != 404:
                raise
            lane = {"timeframe": tf, "basis": "bars", "sourceTimes": [b.time for b in rows],
                    "red": None, "green": None, "outerRed": [], "outerGreen": [], "retest": None,
                    "event": None, "status": "Zu wenig Fächer-Vorlauf", "partial": True,
                    "distance": None, "sourceClose": rows[-1].end, "rules": asdict(rules)}
        lane["sourceGapCount"] = len(gaps)
        if roots == "master":
            from fan_master import context
            from fan_execution import ExecutionRules
            from fan_observer import WatchRules
            lane["context"] = context(rows, gaps)
            lane["tightSafety"] = lane.get("green")
            lane["safetyChoice"] = (config or {}).get("watch", {}).get("safety_choice", "tight")
            # Original immutable case Safety below remains authoritative.
            if lane["safetyChoice"] == "main":
                main = lane.get("mainSafety")
                lane["green"] = main if main and 0 < main["value"] < rows[-1].close else None
            watch = WatchRules(**(config or {}).get("watch", {}))
            execution = ExecutionRules(**(config or {}).get("execution", {}))
            reference = rows[-1].close
            green = lane.get("green")
            stop = math.floor(green["value"]*(1-watch.stop_buffer_pct/100)/rules.tick)*rules.tick if green else None
            risk = reference-stop if stop and 0 < stop < reference else None
            qty = max(0, math.floor(min(execution.capital/reference, execution.capital*execution.risk_fraction/risk))) if risk else None
            lane["closeModel"] = {"reference":reference, "stop":stop, "quantity":qty,
                                  "cash":qty*reference if qty is not None else None,
                                  "plannedRisk":qty*risk if qty is not None else None,
                                  "capital":execution.capital, "riskFraction":execution.risk_fraction,
                                  "meaning":"Hypothetisch am Quellschluss, ohne Kosten/Gaps; kein Forschungsfill"}
            lane["cleanCloseThreshold"] = lane["red"]["value"]+watch.clean_atr*lane["atr"] if lane.get("red") else None
        lane["sourceConvention"] = "regular; reset on gaps" if regular else "native chart only; not research execution"
        lanes[tf] = lane
    payload.update(lanes=lanes, analysisEnabled=True, analysisEngine=engine,
                   rulesVersion=("tori-pine-master-20261029-1" if roots == "master" else VERSION)+":"+stable_id(asdict(rules))[:12],
                   rulesSource="Corrected Pine Master fan; Python causal candidates, no retrospective signal creation")
    if case is not None:
        if case["datasetId"] != payload.get("datasetId") or case["geometry"] != roots:
            raise DataError("Fächerfall passt nicht zu Datenbestand oder Geometrie.", 400)
        signal, cutoff = case["signal"], payload["analysisCutoff"]
        payload["fanCase"] = {"id": case["id"], "status": "before_signal"}
        if signal["signalAt"] <= cutoff:
            tf = case["timeframe"]
            lane = payload["lanes"][tf]
            index = len(payload["charts"][tf]["bars"])-1
            red = deepcopy(signal["line"])
            red["value"] = price_at(red, index)
            lane["retest"] = {"ray": red, "time": signal["time"], "closedAt": signal["breakAt"]}
            lane["event"] = {"kind": "fan_break", "closedAt": signal["breakAt"]}
            if signal.get("safety"):
                green = deepcopy(signal["safety"])
                green["value"] = price_at(green, index)
                lane["outerGreen"] = ([lane["green"]] if lane["green"] else [])+lane["outerGreen"]
                lane["green"] = green
            lane["status"] = "Signal/Safety fixiert"
            entry = case["entry"]
            entered = entry["status"] == "filled" and entry["entryAt"] <= cutoff
            payload["researchSetup"] = {"eventId": signal["id"], "entryMode": "fan", "sourceTimeframe": tf, "signalAt": signal["signalAt"],
                                        "variant": case["variant"], "entryAt": entry["entryAt"] if entered else None,
                                        "entryPrice": entry["entryPrice"] if entered else None,
                                        "initialStop": signal["initialStop"], "validRisk": signal["validRisk"]}
            payload["fanCase"].update(status="entered" if entered else "signal_available", cohort=case["cohort"],
                                      geometry=roots, signalAt=signal["signalAt"])
            # No future path, result, target hit or entry-open quote before it exists.
    return payload
