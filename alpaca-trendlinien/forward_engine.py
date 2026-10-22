"""Prospective two-geometry observer. Entry/exit mathematics stays unchanged."""
from copy import deepcopy
import hashlib
from pathlib import Path

from datasets import digest
from entry_watch import WatchReplay
from entry_geometry import at
from retest_observation import context_for, record, signature as reference_signature, EXITS
from retest_variants import RULES
from strategy_research import RAW_COSTS

VERSION = "forward-watch-1"
MODELS = ("hull_exact", "swing_zone")


def signature():
    root = Path(__file__).parent
    return {**reference_signature(), **{n: hashlib.sha256((root/n).read_bytes()).hexdigest()
            for n in ("forward_engine.py", "forward_data.py", "forward_watch.py", "alpaca.py")}}


class CaptureReplay(WatchReplay):
    """Capture geometry at notification time, never reconstruct from final greens."""
    def notify(self, candidate, state, i):
        before = len(self.messages)
        super().notify(candidate, state, i)
        if len(self.messages) == before or self.bars[i].end < self.capture_from:
            return
        green = candidate if not candidate["upper"] else max(self.greens(i), key=lambda g: at(g["ray"], i), default=None)
        message = self.messages[-1]
        self.captured.append({"id": message["eventKey"], "symbol": self.symbol, "model": self.model,
            "phase": state, "knownAt": message["knownAt"], "sourceIndex": i, "candidateId": candidate["id"],
            "red": deepcopy(candidate["ray"]) if candidate["upper"] else None,
            "green": deepcopy(green["ray"]) if green else None, "width": candidate["width"],
            "features": deepcopy(message["features"]), "explanation": message["explanation"],
            "daily": message["dailyContext"], "weekly": message["weeklyContext"], "action": "review_only"})


def advance(dataset, model, start_at, from_at, asof, previous=None):
    if model not in MODELS or start_at > asof or start_at > from_at:
        raise ValueError("Ungültige Beobachtungsgeometrie oder Zeitspanne.")
    config = {"version": VERSION, "engine": signature(), "model": model, "startAt": start_at,
              "fromAt": from_at, "costs": deepcopy(RAW_COSTS), "exitRules": deepcopy(RULES)}
    context = context_for(dataset, asof)
    def prefix(cutoff):
        return digest({tf: [b.__dict__ for b in bars if b.end <= cutoff] for tf, bars in context.sources.items()})
    replay = CaptureReplay(dataset, model, start_at, asof)
    replay.captured, replay.capture_from = [], from_at
    if previous:
        if previous["config"] != config or asof < previous["asOf"] or prefix(previous["asOf"]) != previous["prefixHash"]:
            raise ValueError("Alte Kurse, Regeln oder Zeit geändert; neue Beobachtungsgeneration erforderlich.")
        replay.restore(previous["watch"])
    replay.run()
    # Signal and fill must both occur after registration. Old overnight signals
    # remain in WatchReplay, but are not retroactively prospective entries.
    records = [record(context, e) for e in replay.entries if e["family"] == "retest" and
               e["signalAt"] >= from_at and e["entryAt"] >= from_at]
    old_records = {r["entry"]["id"]: r for r in previous["records"]} if previous else {}
    current = {r["entry"]["id"]: r for r in records}
    for key, prior in old_records.items():
        if key not in current or prior["entry"] != current[key]["entry"]:
            raise ValueError("Ursprünglicher Entry verändert.")
        for variant in EXITS:
            old, new = prior["paths"][variant], current[key]["paths"][variant]
            if old["status"] == "closed" and old != new:
                raise ValueError("Abgeschlossener Modellpfad verändert.")
            if new["events"][:len(old["events"])] != old["events"]:
                raise ValueError("Bereits bekannte Stopentscheidung verändert.")
    cases = replay.captured
    events = []
    for case in cases:
        events.append({"id": case["id"], "kind": "candidate", "knownAt": case["knownAt"], "caseId": case["id"]})
    for r in records:
        e = r["entry"]
        items = [("entry", "both", e["entryAt"]+300, {"price": e["entryPrice"], "stop": e["initialStop"],
                  "completeHistory": r["history"]["complete"]})]
        for v, p in r["paths"].items():
            items.extend((ev["kind"], v, ev["knownAt"], ev) for ev in p["events"])
            if p["status"] == "closed":
                items.append(("closed", v, p["exitAt"], {k: p[k] for k in ("exitFill", "exitReason", "netR", "netReturnPct")}))
            elif p.get("reason") != "phase_boundary":
                items.append(("unresolved", v, p.get("missingAt", e["entryAt"])+300, {"reason": p.get("reason")}))
        for kind, variant, known, detail in items:
            events.append({"id": digest([VERSION, model, e["id"], kind, variant, known, detail]),
                           "kind": kind, "variant": variant, "knownAt": known, "entryId": e["id"], "detail": detail})
    state = {"config": config, "asOf": asof, "prefixHash": prefix(asof), "datasetId": dataset["id"],
             "watch": replay.state(), "records": records}
    return state, cases, events
