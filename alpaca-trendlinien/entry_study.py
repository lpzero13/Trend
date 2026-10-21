"""Post-decision evaluation for the isolated entry experiment, never a scanner input."""
from collections import Counter
from datetime import datetime
from statistics import mean, median

from lab_metrics import OutcomeEvaluator, blocked_interval
from models import NY

HORIZONS = (5, 10, 20)
SEED = 20261021
SIDE_COST = .00075  # half of 5bp spread plus 5bp slippage per side


def net_return(gross_pct):
    return ((1+gross_pct/100)*(1-SIDE_COST)/(1+SIDE_COST)-1)*100


def evaluate_entries(dataset, entries, phase):
    evaluator = OutcomeEvaluator(dataset)
    spec = {"seed": SEED, "horizons": list(HORIZONS), "lab": {"random_controls": 3}}
    result = []
    for e in entries:
        if not phase["startAt"] <= e["entryAt"] <= phase["endAt"]:
            continue
        forward = evaluator.evaluate(e, HORIZONS, phase["endAt"])
        controls = evaluator.controls(e, phase, spec)
        for h, f in forward.items():
            f["netPct"] = net_return(f["return_pct"]) if f["complete"] else None
            matched = [c["forward"][h] for c in controls
                       if c["forward"][h]["complete"] and c["forward"][h].get("pathComplete") is True]
            f["controlCount"] = len(matched)
            f["controlNetPct"] = mean(net_return(c["return_pct"]) for c in matched) if matched else None
            f["excessPct"] = f["netPct"]-f["controlNetPct"] if f["netPct"] is not None and matched and f.get("pathComplete") is True else None
        result.append({**e, "forward": forward, "controls": controls})
    return result


def quarter(e):
    d = datetime.fromtimestamp(e["entryAt"], NY)
    return e["symbol"], d.year, (d.month-1)//3


def summarize(entries, models):
    output = {}
    for model in models:
        for family in ("breakout", "horizontal", "retest", "bounce"):
            all_rows = [e for e in entries if e["model"] == model and e["family"] == family]
            for group in ("all", "three_reactions", "strict_diagnostic"):
                rows = [e for e in all_rows if group == "all" or
                        (e["features"]["reactionEpisodes"] >= 3 if group == "three_reactions" else e["strictEligible"])]
                horizons = {}
                for h in HORIZONS:
                    complete = [e for e in rows if e["forward"][str(h)]["complete"] and e["forward"][str(h)].get("pathComplete") is True]
                    same_set = [e for e in complete if all(e["forward"][str(k)]["complete"] and e["forward"][str(k)].get("pathComplete") is True for k in HORIZONS)]
                    values = [e["forward"][str(h)] for e in complete]
                    one = [v["oneRBeforeSafety"] for v in values if v.get("oneRBeforeSafety") is not None]
                    two = [v["twoRBeforeSafety"] for v in values if v.get("twoRBeforeSafety") is not None]
                    excess = [{"symbol": e["symbol"], "entryAt": e["entryAt"], "excess": e["forward"][str(h)]["excessPct"]}
                              for e in complete if e["forward"][str(h)]["excessPct"] is not None]
                    horizons[str(h)] = {"completePaths": len(complete), "incomplete": len(rows)-len(complete),
                        "stocks": len({e["symbol"] for e in complete}),
                        "meanNetPct": mean(v["netPct"] for v in values) if values else None,
                        "medianNetPct": median(v["netPct"] for v in values) if values else None,
                        "positivePct": 100*sum(v["netPct"] > 0 for v in values)/len(values) if values else None,
                        "meanMfePct": mean(v["mfe_pct"] for v in values) if values else None,
                        "meanMaePct": mean(v["mae_pct"] for v in values) if values else None,
                        "oneR": {"yes": sum(one), "known": len(one)}, "twoR": {"yes": sum(two), "known": len(two)},
                        "ambiguous": sum(v.get("intrabarAmbiguous", False) for v in values),
                        "matchedCases": len(excess), "meanExcessPct": mean(e["excess"] for e in excess) if excess else None,
                        "excessInterval": blocked_interval(excess, "excess", seed=SEED),
                        "constantHorizonSet": {"count": len(same_set), "meanNetPct": mean(e["forward"][str(h)]["netPct"] for e in same_set) if same_set else None}}
                output[model+"/"+family+"/"+group] = {"entries": len(rows), "horizons": horizons}
    common = set.intersection(*({quarter(e) for e in entries if e["model"] == m and e["family"] == "breakout" and e["forward"]["10"].get("excessPct") is not None} for m in models))
    return {"groups": output, "commonStockQuarters": len(common),
        "commonCoverage10d": {m: {"count": len(values), "meanExcessPct": mean(values) if values else None}
            for m in models for values in [[e["forward"]["10"]["excessPct"] for e in entries if e["model"] == m and e["family"] == "breakout" and quarter(e) in common and e["forward"]["10"].get("excessPct") is not None]]},
        "uniquePhysicalTimes": len({(e["symbol"], e["entryAt"]) for e in entries}),
        "meaning": "Fixed-horizon event observations with overlapping cases; not a portfolio or executed exit strategy."}


def development_decision(summary):
    groups = summary["groups"]
    ref = groups["hull_exact/breakout/all"]["horizons"]["10"]
    new = groups["swing_envelope/breakout/all"]["horizons"]["10"]
    enough = all(v["matchedCases"] >= 20 and v["stocks"] >= 3 for v in (ref, new))
    delta = new["meanExcessPct"]-ref["meanExcessPct"] if enough else None
    return {"comparison": "swing_envelope vs hull_exact / breakout / 10 sessions", "enough": enough,
            "developmentDeltaExcessPct": delta, "advanceAsHypothesis": bool(enough and delta > 0),
            "meaning": "Frozen before later-phase labels; no parameter adjustment. Validation dates are already known, not untouched holdout."}


def watch_summary(results, phase):
    out = {}
    for r in results:
        d = out.setdefault(r["model"], {"messages": Counter(), "executionsRejected": Counter(), "candidates": 0,
            "threeReactionCandidates": 0, "alternatives": 0, "bars": 0, "uniqueEntryTimes": set(), "nearLeadHours": []})
        d["messages"].update(m["state"] for m in r["messages"] if phase["startAt"] <= m["knownAt"] <= phase["endAt"])
        d["executionsRejected"].update(e["status"] for e in r["executions"] if phase["startAt"] <= e["signalAt"] <= phase["endAt"])
        d["candidates"] += sum(phase["startAt"] <= c["knownAt"] <= phase["endAt"] for c in r["candidates"])
        d["threeReactionCandidates"] += sum(phase["startAt"] <= c["knownAt"] <= phase["endAt"] and c["lastFeatures"]["reactionEpisodes"] >= 3 for c in r["candidates"])
        d["alternatives"] += r["coverage"]["alternativeLines"]
        d["bars"] += r["coverage"]["bars"]
        for e in r["entries"]:
            if phase["startAt"] <= e["entryAt"] <= phase["endAt"]:
                d["uniqueEntryTimes"].add((e["symbol"], e["entryAt"]))
                if e.get("nearAt") and e["nearAt"] < e["signalAt"]:
                    d["nearLeadHours"].append((e["signalAt"]-e["nearAt"])/3600)
    for d in out.values():
        d["uniqueEntryTimes"] = len(d["uniqueEntryTimes"])
        d["medianNearLeadHours"] = median(d["nearLeadHours"]) if d["nearLeadHours"] else None
        d["entriesWithEarlierNear"] = len(d.pop("nearLeadHours"))
    return out
