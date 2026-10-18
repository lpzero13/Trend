"""Causal full scans and isolated post-decision enrichment for the research lab.

Signal computation has no access to evaluators. Enrichment runs after a scan;
its outputs never modify the source scanner or another profile's decisions.
"""
from bisect import bisect_left, bisect_right
from copy import deepcopy

from datasets import digest, source_bars
from lab_metrics import OutcomeEvaluator
from lab_profiles import LabScanner, VERSION, profile_manifest
from lab_splits import member
from models import DataError


def scan_plan(dataset,phase,*,sources=None):
    bars=(sources or source_bars(dataset))["4h"]
    first=max(1,bisect_left([b.time for b in bars],phase["startAt"]))
    visible_first=first
    if "historyStartAt" in phase:
        # Replay all prior state, including the identities of already expired
        # setups. A bounded warmup could incorrectly re-arm an old line pair.
        history=max(1,bisect_left([b.time for b in bars],phase["historyStartAt"]))
        first=min(first,history)
    end=bisect_right([b.end for b in bars],phase["endAt"])-1
    if visible_first>end:raise DataError("Keine abgeschlossenen 4h-Kerzen in dieser Forschungsphase.",422)
    return {"scan_start":first,"discovery_end":end,"holdout_start":phase["endAt"]+1,
            "candles":end-first+1,"warmupCandles":visible_first-first,"scanStartAt":bars[first-1].end,"scanEndAt":bars[end].end}


def identity_for(source_id,profile,phase):
    return digest({"sourceSetupId":source_id,"profile":profile,"phase":phase,"version":VERSION})


def decorate(item,profile,phase,manifest):
    result=deepcopy(item)
    if "trial" in result:
        case=result["trial"];original=case["id"]
        case.update(id=identity_for(original,manifest,phase),sourceSetupId=original,profile=profile,labPhase=phase,
                    labVersion=VERSION,profileFingerprint=digest(manifest))
        for entry in case["variants"]:
            entry.update(eventId=case["id"],labProfile=profile)
    else:
        event=result["event"]
        event.update(id=identity_for(event["id"],manifest,phase),
                     setupId=identity_for(event["setupId"],manifest,phase),profile=profile,labPhase=phase)
    return result


def hypothetical_point(scanner,case,entry,phase):
    """Only a rejected, actually triggered family gets a hypothetical fill.

    Expiry, absent confirmations and a broken safety before any breakout are
    not retroactively converted to entries. No alternative fill is called a
    successful criterion match or included in portfolio execution.
    """
    if entry["status"]!="rejected" or "breakIndex" not in case:return None
    family=entry["variant"]
    if family!="breakout" and not any(c["name"]==("retest_held" if family=="retest" else "horizontal_confirmed") and c["state"]=="pass" for c in entry.get("checks",[])):
        return None
    confirmed=max(case["signal"]["closedAt"],entry.get("signalAt",0))
    available=confirmed+scanner.spec["latency_seconds"]
    if entry.get("reason","").startswith("execution:"):available=max(available,entry["decidedAt"])
    i=bisect_left(scanner.hour_times,available)
    if i>=len(scanner.hourly) or scanner.hourly[i].time>phase["endAt"]:return None
    bar=scanner.hourly[i]
    from tori_entries import value
    green=case["frozen"].get("green")
    stop=entry.get("safetyAtSignal",value(green,case["breakIndex"]) if green else None)
    return {"entryAt":bar.time,"entryPrice":bar.open,"initialStop":stop,
            "executionTimeframe":scanner.execution_timeframe,"assumption":"first available open after rejected family confirmation + latency; not an accepted entry"}


def scan_stock(dataset,spec,phase,*,profiles=None,phase_id=None,benchmark=None,
               emit=lambda item:None,cancelled=lambda:False,progress=lambda **detail:None):
    """One chronological traversal per preregistered profile, all cases persisted.

    Cached geometry is shared only for identical causal prefixes and rules.
    Replaying after interruption produces the same IDs for transactional upsert.
    """
    profiles=profiles or spec["lab"]["profiles"]
    if any(p not in spec["lab"]["profiles"] for p in profiles):raise DataError("Nicht vorregistriertes Profil.",400)
    sources=source_bars(dataset)
    plan=scan_plan(dataset,phase,sources=sources)
    evaluator=OutcomeEvaluator(dataset,sources)
    market=benchmark if isinstance(benchmark,OutcomeEvaluator) else OutcomeEvaluator(benchmark) if benchmark else None
    phase_id=phase_id or spec["lab"]["stage"]
    shared={"sources":sources};coverage={};scanners={};symbol=dataset["material"]["symbol"];cache_peak=0
    for profile in profiles:
        manifest=profile_manifest(profile,spec["lab"],spec["tori"])
        send=lambda item,p=profile,m=manifest:emit(decorate(item,p,phase_id,m))
        scanners[profile]=LabScanner(dataset,spec,plan,profile,send,shared)
    for i in range(plan["scan_start"],plan["discovery_end"]+1):
        for position,(profile,scanner) in enumerate(scanners.items()):
            if not scanner.advance(i,cancelled):
                partial={p:{**s.coverage,"setups":len(s.cases),"complete":False} for p,s in scanners.items()}
                return {"complete":False,"profiles":partial}
            progress(symbol=symbol,profile=profile,section=phase_id,completed=(i-plan["scan_start"])*len(profiles)+position+1,total=len(profiles)*plan["candles"],unit="candles")
        cache_peak=max(cache_peak,len(shared.get("lines",{})))
        # Profiles advance together, so retaining historic Ray.source_times
        # would only consume quadratic memory without useful cache hits.
        shared.get("lines",{}).clear()
    for position,(profile,scanner) in enumerate(scanners.items()):
        coverage[profile]={**scanner.coverage,"setups":len(scanner.cases),"complete":True,
                           "membershipExcluded":0,"uniqueEntries":0,"warmupCandles":plan["warmupCandles"],"outcomesComplete":False}
        scanner.finish()
        unique=set()
        for case_position,case in enumerate(scanner.cases.values(),1):
            if cancelled():return {"complete":False,"profiles":coverage}
            progress(symbol=symbol,profile=profile,section=phase_id,completed=case_position,total=len(scanner.cases),unit="outcomes")
            for entry in case["variants"]:
                decision=max(entry.get("entryAt",0),entry.get("signalAt",0),entry.get("decidedAt",0),case.get("signal",{}).get("closedAt",0))
                entry["inPhase"]=phase["startAt"]<=decision<=phase["endAt"]
                point=entry if entry["status"]=="observed" else hypothetical_point(scanner,case,entry,phase)
                if point is None:continue
                if not member(symbol,point["entryAt"],spec["lab"]):
                    if entry["status"]=="observed":
                        coverage[profile]["membershipExcluded"]+=1
                        entry.update(status="rejected",reason="outside_historical_membership")
                    continue
                if not phase["startAt"]<=point["entryAt"]<=phase["endAt"]:
                    if entry["status"]=="observed":entry.update(status="censored",reason="entry_outside_phase")
                    continue
                point["forward"]=evaluator.evaluate(point,spec["horizons"],phase["labelEndAt"])
                point["controls"]=evaluator.controls(point,phase,spec)
                point["benchmark"]=market.benchmark(point,spec["horizons"],phase["labelEndAt"]) if market else {}
                if entry["status"]=="observed":unique.add(point["entryAt"])
                else:entry["hypothetical"]=point
            scanner.save(case)
        coverage[profile]["uniqueEntries"]=len(unique)
        coverage[profile]["outcomesComplete"]=True
        progress(symbol=symbol,profile=profile,completed=(position+1)*plan["candles"],total=len(profiles)*plan["candles"],unit="candles")
    return {"complete":True,"profiles":coverage,"phase":phase,"phaseId":phase_id,"geometryCachePeak":cache_peak}


def training_choice(records,spec):
    """Select from already cut-off training outcomes; evaluation never enters here."""
    import statistics
    by_profile={p:{} for p in spec["lab"]["profiles"]}
    h=str(spec["lab"]["primary_horizon"]);metric=spec["lab"]["primary_metric"]
    for case in records:
        for entry in case["variants"]:
            if entry["status"]!="observed":continue
            if entry["variant"]!=spec["lab"]["primary_family"]:continue
            outcome=entry.get("forward",{}).get(h,{})
            if not outcome.get("complete"):continue
            controls=[c["forward"][h]["return_pct"] for c in entry.get("controls",[]) if c.get("forward",{}).get(h,{}).get("complete")]
            value=outcome["return_pct"]
            if metric=="mean_excess_pct":
                if not controls:continue
                value-=statistics.mean(controls)
            by_profile[case["profile"]].setdefault((case["datasetId"],entry["entryAt"]),value)
    scores={}
    for p,points in by_profile.items():
        values=list(points.values())
        scores[p]={"n":len(values),"score":(statistics.median(values) if metric=="median_return_pct" else statistics.mean(values)) if len(values)>=spec["lab"]["min_train_events"] else None}
    eligible=[p for p in scores if scores[p]["score"] is not None]
    chosen=min(eligible,key=lambda p:(-scores[p]["score"],p)) if eligible else None
    return {"profile":chosen,"scores":scores,"primaryMetric":metric,"primaryHorizon":int(h),"primaryFamily":spec["lab"]["primary_family"],
            "rule":"highest predeclared training score, ties by profile id; no selection when sample insufficient"}
