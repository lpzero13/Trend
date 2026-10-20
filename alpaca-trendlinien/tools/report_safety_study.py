"""Source-backed Markdown tables, no new simulations or provider calls."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def number(value, places=3):
    return "—" if value is None else f"{value:.{places}f}"


def report(root, output):
    root = Path(root).resolve()
    manifest = json.loads((root/"manifest.json").read_text("utf-8"))
    lines = ["# Safety-Strategien: vollständige Ergebnistabellen", "",
             "Automatisch aus unveränderten lokalen Ergebnisdateien erstellt. USD, Kosten enthalten. "
             "Profil-/Familienfälle können abhängig sein und sind keine unabhängigen Trades. "
             "Vergleichswerte nutzen dieselben vollständig beobachteten Fälle je Horizont; "
             "unvollständige Pfade bleiben in der Fallübersicht sichtbar. Kein Holdout geöffnet.", ""]
    receipts = {"manifest": hashlib.sha256((root/"manifest.json").read_bytes()).hexdigest(), "stages": {}}
    summary = {}
    for stage in ("development", "validation"):
        path = root/(stage+".json")
        if not path.exists():
            continue
        data = json.loads(path.read_text("utf-8"))
        receipts["stages"][stage] = hashlib.sha256(path.read_bytes()).hexdigest()
        unique = {(e["symbol"], e["entryAt"], e["family"]) for e in data["entries"]}
        summary[stage] = {"entries": len(data["entries"]), "physicalFamilyEvents": len(unique),
            "symbolsWithEntries": len({e["symbol"] for e in data["entries"]}),
            "eligible": data["eligible"], "paths": len(data["paths"]),
            "pathStates": dict(Counter(p["status"] for p in data["paths"])),
            "portfolioStates": dict(Counter(p["status"] for p in data["portfolios"])),
            "blockedBy": data["blockedBy"],
            "primary": [r for r in data["rows"] if r["profile"] == "momentum_two" and r["family"] == "breakout" and r["cohort"] == "eligible" and r["days"] == 10]}
        lines += [f"## {stage}", "", f"{len(data['entries'])} Profil-/Familienfälle, {len(unique)} eindeutige Aktie/Zeit/Familie-Ereignisse, "
                  f"{data['eligible']} zulässige Fälle, {len(data['paths'])} Modellpfade.", "",
                  "### Gepaarter Einzelpositionsvergleich", "",
                  "| Profil | Familie | Gruppe | Tage | Modell | Alle / geschlossen | Gemeinsam N | Gewinnanteil % | Mittel netto % | Mittel netto R | ΔR zu fixed |",
                  "|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|"]
        for row in data["rows"]:
            p, all_cases = row["paired"], row["all"]
            lines.append(f"| {row['profile']} | {row['family']} | {row['cohort']} | {row['days']} | {row['model']} | "
                         f"{all_cases['cases']} / {all_cases['closed']} | {p['closed']} | {number(p['winRatePct'], 1)} | "
                         f"{number(p['meanNetPct'])} | {number(p['meanNetR'])} | {number(row['meanPairedDeltaR'])} |")
        lines += ["", "### Kapitalbegrenzte Portfolios", "",
                  "Bei `incomplete` ist das angegebene Vermögen nur der beobachtete Präfix; keine volle Phasenrendite. "
                  "`marked_to_phase_end` kann offene Positionen enthalten. Leere Portfolios sind kein Strategieerfolg.", "",
                  "| Profil | Familie | Gruppe | Tage | Modell | Status | Käufe / geschlossen / offen | Vermögen USD | Phasenrendite % | Realisiert USD | 5m-Drawdown % |",
                  "|---|---|---|---:|---|---|---:|---:|---:|---:|---:|"]
        for p in data["portfolios"]:
            lines.append(f"| {p['profile']} | {p['family']} | {p['cohort']} | {p['days']} | {p['model']} | {p['status']} | "
                         f"{p['accepted']} / {p['closed']} / {p['open']} | {number(p['markedEquity'], 2)} | "
                         f"{number(p['markedReturnPct'])} | {number(p['realizedNetPnl'], 2)} | {number(p['max5mSampledDrawdownPct'])} |")
        lines += ["", "### Gleichbleibende Fallmenge über alle Modelle und Horizonte", "",
                  "Nur Fälle mit vollständigem Pfad in allen vier Modellen und allen drei Horizonten. "
                  "Hier zur Übersicht 20 Tage, Referenzprofil, ungefiltert. Diese verfügbare Teilmenge kann Selektionsverzerrung enthalten.", "",
                  "| Familie | Modell | N | Mittel netto % | Mittel netto R |", "|---|---|---:|---:|---:|"]
        for row in data["rows"]:
            if row["profile"] == "baseline" and row["cohort"] == "all" and row["days"] == 20:
                p = row["constant"]
                lines.append(f"| {row['family']} | {row['model']} | {p['closed']} | {number(p['meanNetPct'])} | {number(p['meanNetR'])} |")
        lines += ["", "Blockierte Eintrittsprüfungen (Mehrfachnennungen): " + ", ".join(f"`{k}`: {v}" for k, v in sorted(data["blockedBy"].items())), ""]
    decision = json.loads((root/"decision-before-validation.json").read_text("utf-8"))
    summary.update(decision=decision, sourceReceipts=receipts, rules=manifest["rules"], costs=manifest["costs"])
    output = Path(output).resolve()
    output.write_text("\n".join(lines).rstrip()+"\n", "utf-8")
    output.with_suffix(".json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), "utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = report(args.study, args.output)
    print(json.dumps({k: {n: v for n, v in data.items() if n not in ("primary", "blockedBy")} for k, data in result.items() if k in ("development", "validation")}))
