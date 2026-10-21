"""Rebuild inspectable tables from pinned internal-study outputs; no market fetch."""
import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
from statistics import mean, median
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datasets import digest
from entry_geometry import MODELS
from models import NY
from strategy_research import write_json


def read(path):
    return json.loads(path.read_text("utf-8"))


def fmt(v):
    return "–" if v is None else f"{v:.2f}"


def run(args):
    root, target = Path(args.root).resolve(), Path(args.output).resolve()
    contract = read(root/"contract.json")
    lines = ["# Interne Einstiegssuche: vollständige Vergleichstabellen", "",
        "Erzeugt aus dem festgehaltenen Vertrag `"+digest(contract)+"`. Regeln: [EINSTIEGSSUCHE-INTERN.md](EINSTIEGSSUCHE-INTERN.md).",
        "Alle Renditen sind Schlusskursbeobachtungen nach Kostenannahme, keine ausgeführten Strategie-/Depotgewinne. `Mehr` ist die mittlere Differenz in Prozentpunkten zu passenden Kontrollzeitpunkten. Vollständige 5m-Pfade nötig; keine unabhängigen Trades. Gruppen überlappen.", ""]
    extra = {}
    for stage in ("development", "validation"):
        summary = read(root/(stage+"-summary.json"))
        entries, states = [], []
        for symbol in contract["symbols"]:
            for model in MODELS:
                block = read(root/stage/(symbol+"-"+model+".json"))
                assert block["checksum"] == digest({k: v for k, v in block.items() if k != "checksum"})
                entries.extend(block["observations"])
                states.append(block["state"])
        phase = {}
        for model in MODELS:
            rows = [e for e in entries if e["model"] == model]
            ref_times = {(e["symbol"], e["entryAt"]) for e in entries if e["model"] == "hull_exact" and e["family"] == "breakout"}
            times = {(e["symbol"], e["entryAt"]) for e in rows if e["family"] == "breakout"}
            stop = [e for e in rows if e["armSafetyValid"]]
            paired = [e for e in rows if e["family"] == "breakout" and e["forward"]["10"].get("excessPct") is not None and e["forward"]["10"]["controlCount"] == 3]
            near = [m for s in states if s["model"] == model for m in s["messages"] if m["state"] == "near" and
                    contract["phases"][stage]["startAt"] <= m["knownAt"] <= contract["phases"][stage]["endAt"]]
            # Collapse duplicate family observations for lead-time statistics.
            lead = {(e["symbol"], e["entryAt"]): (e["signalAt"]-e["nearAt"])/3600 for e in rows if e.get("nearAt") and e["nearAt"] < e["signalAt"]}
            phase[model] = {"entries": len(rows), "uniqueTimes": len({(e["symbol"], e["entryAt"]) for e in rows}),
                "additionalBreakoutTimes": len(times-ref_times), "missingReferenceBreakoutTimes": len(ref_times-times),
                "strictEntries": sum(e["strictEligible"] for e in rows),
                "blockedBy": dict(Counter(k for e in rows for k in e["blockedBy"])),
                "armSafetyPairs": len(stop), "nearerSafetyPairs": sum(e["initialStop"] > e["armStop"]+1e-7 for e in stop),
                "meanSignalRiskATR": mean(e["signalRiskATR"] for e in rows) if rows else None,
                "meanArmRiskATR": mean(e["armRiskATR"] for e in stop) if stop else None,
                "withAllThreeControls": len(paired), "meanExcessThreeControls": mean(e["forward"]["10"]["excessPct"] for e in paired) if paired else None,
                "nearMessagesPerSession": len(near)/contract["phases"][stage]["sessions"],
                "physicalEntriesWithPriorNear": len(lead), "medianLeadCalendarHours": median(lead.values()) if lead else None}
        all_times = {(e["symbol"], e["entryAt"]) for e in entries if e["family"] == "breakout"}
        ref = {(e["symbol"], e["entryAt"]) for e in entries if e["model"] == "hull_exact" and e["family"] == "breakout"}
        extra[stage] = {"models": phase, "unionBreakoutTimes": len(all_times), "referenceBreakoutTimes": len(ref),
            "meaning": "Union is descriptive coverage only; no post-hoc winning-model selection or return claim."}
        lines.extend(["## "+stage, "", "Wissenschaftlicher Zusammenfassungshash `"+summary["scientificHash"]+"`.", "",
            "| Modell/Familie/Gruppe | H | Einstiege | volle Pfade | Aktien | Netto % | Median % | positiv % | Mehr pp | mit Kontrollen | +1R vor Safety | +2R vor Safety |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"])
        for key, group in summary["groups"].items():
            for h, v in group["horizons"].items():
                one, two = v["oneR"], v["twoR"]
                lines.append(f"| {key} | {h} | {group['entries']} | {v['completePaths']} | {v['stocks']} | {fmt(v['meanNetPct'])} | {fmt(v['medianNetPct'])} | {fmt(v['positivePct'])} | {fmt(v['meanExcessPct'])} | {v['matchedCases']} | {one['yes']}/{one['known']} | {two['yes']}/{two['known']} |")
        lines.extend(["", "### Gleiche Aktien-/Quartalsabdeckung, Ausbruch, zehn Sitzungen", "",
            "| Modell | Fälle | Mehr pp |", "|---|---:|---:|"])
        for model, v in summary["commonCoverage10d"].items():
            lines.append(f"| {model} | {v['count']} | {fmt(v['meanExcessPct'])} |")
        lines.extend(["", "### Meldungen und ausführbare Zeitpunkte", "",
            "| Modell | Annäherungen | Ausbruchsmeldungen | eindeutige Entryzeiten, alle Familien | zusätzliche Ausbruchszeiten | fehlende Referenz-Ausbruchszeiten |", "|---|---:|---:|---:|---:|---:|"])
        for model, v in summary["watches"].items():
            p = phase[model]
            lines.append(f"| {model} | {v['messages'].get('near',0)} | {v['messages'].get('breakout',0)} | {p['uniqueTimes']} | {p['additionalBreakoutTimes']} | {p['missingReferenceBreakoutTimes']} |")
        lines.extend(["", f"Union aller Modelle: **{len(all_times)}** Ausbruchszeitpunkte gegenüber **{len(ref)}** in der Hüllenreferenz. Rein beschreibende Abdeckung, keine zusätzliche bestätigte Strategie.", ""])
    target.write_text("\n".join(lines), "utf-8")
    write_json(root/"diagnostics.json", extra)
    print(json.dumps(extra, ensure_ascii=False))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True)
    p.add_argument("--output", required=True)
    run(p.parse_args())
