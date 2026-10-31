"""Descriptive reporting only; never changes episode selection or stop rules."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from event_case_study import checked, load_block
from strategy_screen import read, write


def fmt(value, places=2):
    return "—" if value is None else f"{value:.{places}f}"


def report(root, destination):
    root = Path(root)
    p = checked(read(root/"plan.json"))
    result = read(root/"results.json")
    verify = read(root/"verification.json")
    assert result["planId"] == verify["planId"] == p["id"] and verify["passed"]
    cases, suppressed, entries = [], 0, []
    for symbol in p["symbols"]:
        b = load_block(root, p, symbol)
        cases.extend(b["cases"])
        suppressed += len(b["suppressed"])
        entries.append({"symbol": symbol, "cases": len(b["cases"]), "suppressed": len(b["suppressed"]),
                        "seconds": b["elapsedSeconds"]})
    bounds = datetime.fromtimestamp(p["outcomeCutoff"], timezone.utc).isoformat()
    lines = ["# Signalepisoden bis zum regelbasierten Exit – 31.10.2026", "",
        f"{result['stocks']} Aktien, {len(p['windows'])} bekannte Entryfenster; Nachbeobachtung bis **{bounds}**.", "",
        f"**{result['cases']} Einstiegfälle aus {result['episodes']} Episoden. {suppressed} Fortsetzungs-/Alternativsignale derselben Struktur und Entryfamilie unterdrückt.** "
        f"{len(result['unavailableWindows'])} Aktien-/Fensterkombinationen ohne ausreichenden Vorlauf gesondert ausgewiesen.", "",
        "Dies ist eine Untersuchung einzelner Signalverläufe. Kein gemeinsames Depot, keine Kapital-/Slotsperren und keine Ein-Position-pro-Aktie-Sperre. "
        "Je Fall 1.000 USD nominal, fraktionale Stückzahl, 5 Basispunkte Spread insgesamt plus 5 Basispunkte Slippage je Seite, keine Ordergebühr. "
        "Kauf am nächsten erwarteten 5m-Open nach 300 Sekunden. Kein Kauf, wenn dieser Kurs fehlt oder der Open bereits unter dem Anfangsstop liegt.", "",
        "## Vorab festgelegte Fallbildung", "",
        "Alle Linien desselben Fächers teilen eine Herkunft. Wird eine Kindlinie zur Hauptlinie, bleibt diese Herkunft erhalten. "
        "Eine andere Linien-ID, ein nachjustierter Endpunkt oder eine weitere erfüllte Kerze allein erzeugt keinen neuen Fall. "
        "Eine bisher unverbundene Ankerstruktur oder mindestens zwei nach dem letzten Episodenstart entstandene und bereits bestätigte Kontakte erlauben eine neue Episode. "
        "Je Episode höchstens ein Ausbruch, ein roter Retest beziehungsweise ein Safety-Bounce. Roter Retest und ursprünglicher Ausbruch behalten ihre gemeinsame Szenarioherkunft, "
        "auch wenn inzwischen eine neue Episode entstand. Die Abgrenzung ist experimentell und noch kein Beleg für Gleichwertigkeit mit subjektivem Zeichnen.", "",
        "Alle Zwischenjahre und der Vorlauf werden durch den Episodenfilter geführt; ausgewertet werden nur Entries in den vorab benannten Fenstern. "
        "Kontaktklassen werden bei der Entscheidung eingefroren; es gibt keine spätere Hochstufung anhand erfolgreicher Verläufe.", "",
        "## Exits und Aussagegrenzen", "",
        "Drei Hard-Stop-Varianten: fester Anfangsstop als Kontrolle, Projektion der ursprünglichen steigenden Safety und aktuelle gültige steigende Safety. "
        "Puffer 0,3 %, auf Cent abrunden, nur nach oben nachziehen. Neue Stops wirken erst nach Quellkerzenschluss und 300 Sekunden Verzögerung am nächsten erwarteten 5m-Open. "
        "Ein Gap unter den Stop wird zum tatsächlichen Open ausgeführt. Das Hoch der Exitkerze wird wegen unbekannter Intrabarreihenfolge nicht als MFE gutgeschrieben.", "",
        "**Kein Zeitexit und kein Take Profit.** Der feste Kontrollstop kann einen Gewinn daher überhaupt nicht regulär realisieren: "
        "Gewinner bleiben bis Datenende offen oder werden bei fehlendem Pfad zensiert. Eine Trefferquote von null unter seinen geschlossenen Fällen ist konstruktionsbedingt und kein Beweis schlechter Entries. "
        "Auch zwischen den Safety-Modellen sind ausschließlich abgeschlossene Fälle keine identische Stichprobe. "
        "Offene Buchergebnisse und datenbedingt zensierte Fälle bleiben getrennt; sie werden nicht in abgeschlossene Renditen umbenannt.", "",
        "## Alle Kontaktklassen", "",
        "Prozentwerte sind Nettoergebnisse bei gleichem nominalen Einzeleinsatz, keine Depotperformance. Trefferquoten beziehen sich ausschließlich auf abgeschlossene Fälle.", "",
        "| Entry / Kontaktklasse | Stopführung | Signale | Geschlossen | Offen | Datenlücke | Sonstige | Treffer % | Mittel R | Median R | Mittel netto % | Median netto % |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for group, methods in result["groups"].items():
        for model, v in methods.items():
            st = v["statuses"]
            others = sum(n for k, n in st.items() if k not in ("closed", "open", "censored"))
            lines.append(f"| {group} | {model} | {v['signals']} | {v['closed']} | {st.get('open',0)} | {st.get('censored',0)} | {others} | "
                f"{fmt(v['winPctClosed'])} | {fmt(v['meanNetR'])} | {fmt(v['medianNetR'])} | {fmt(v['meanNetReturnPct'])} | {fmt(v['medianNetReturnPct'])} |")
    lines += ["", "## Zeitfenster: qualifizierte Entries", "",
        "| Fenster | Entry | Safety | Geschlossen | Offen | Lücke | Treffer % | Mittel R | Median R | Mittel netto % |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for window, groups in result["windows"].items():
        for family in ("breakout", "red_retest", "safety_bounce"):
            for model in ("original_safety", "fan_safety"):
                v = groups.get(family+":qualified", {}).get(model)
                if v:
                    lines.append(f"| {window} | {family} | {model} | {v['closed']} | {v['statuses'].get('open',0)} | {v['statuses'].get('censored',0)} | "
                        f"{fmt(v['winPctClosed'])} | {fmt(v['meanNetR'])} | {fmt(v['medianNetR'])} | {fmt(v['meanNetReturnPct'])} |")
    lines += ["", "## Gemeinsame geschlossene Fälle: ursprüngliche gegen aktuelle Safety", "",
        "Die paarweise Teilmenge macht den Methodenvergleich vergleichbarer, löst aber die Auswahl durch Zensierung nicht. Keine Optimierung oder unabhängige Erfolgsbestätigung.", "",
        "| Entry / Klasse | Beide geschlossen | Nicht beide geschlossen | Mittel R original | Mittel R aktuell | Median ΔR aktuell−original |",
        "|---|---:|---:|---:|---:|---:|"]
    grouped = defaultdict(list)
    for c in cases:
        grouped[(c["signal"]["family"], c["signal"]["cohort"])].append(c)
    comparisons = {}
    for key, cs in sorted(grouped.items()):
        paired = [c for c in cs if all(c["paths"][m]["status"] == "closed" for m in ("original_safety", "fan_safety"))]
        original = [c["paths"]["original_safety"]["netR"] for c in paired]
        current = [c["paths"]["fan_safety"]["netR"] for c in paired]
        delta = [b-a for a, b in zip(original, current)]
        name = ":".join(key)
        comparisons[name] = {"bothClosed": len(paired), "notBothClosed": len(cs)-len(paired),
            "originalMeanR": statistics.mean(original) if original else None,
            "currentMeanR": statistics.mean(current) if current else None,
            "medianDeltaR": statistics.median(delta) if delta else None}
        v = comparisons[name]
        lines.append(f"| {name} | {len(paired)} | {len(cs)-len(paired)} | {fmt(v['originalMeanR'])} | {fmt(v['currentMeanR'])} | {fmt(v['medianDeltaR'])} |")
    concentration = {}
    lines += ["", "## Konzentration und offene Verläufe", "",
        "Anteile beziehen sich auf positive nominale Beiträge abgeschlossener Fälle; keine finanzierbare Depotaddition. "
        "Das Weglassen der besten Fälle ist eine nachträgliche Sensitivitätsbeschreibung, kein neuer Handelsfilter.", "",
        "| Qualifizierter Entry | Safety | Größte Aktie: positive Beiträge % | Top-3 Trades: positive Beiträge % | Median Haltedauer Tage | Mittel netto % ohne beste 3 Trades |",
        "|---|---|---:|---:|---:|---:|"]
    for family in ("breakout", "red_retest", "safety_bounce"):
        cs = grouped.get((family, "qualified"), [])
        for model in ("original_safety", "fan_safety"):
            closed = [c for c in cs if c["paths"][model]["status"] == "closed"]
            positive = defaultdict(float)
            for c in closed:
                positive[c["symbol"]] += max(0, c["paths"][model]["netPnl"])
            total = sum(positive.values())
            ordered = sorted(closed, key=lambda c: c["paths"][model]["netPnl"], reverse=True)
            trimmed = [c["paths"][model]["netReturnPct"] for c in ordered[3:]]
            v = result["groups"].get(family+":qualified", {}).get(model)
            if not v:
                continue
            share = 100*max(positive.values())/total if total else None
            trim = statistics.mean(trimmed) if trimmed else None
            concentration[family+":"+model] = {"largestPositiveSymbolSharePct": share,
                "closedMeanNetPctWithoutBest3": trim, "positiveContributionsBySymbol": dict(positive)}
            lines.append(f"| {family} | {model} | {fmt(share)} | {fmt(v['top3SharePositiveNominalPnlPct'])} | {fmt(v['medianHoldingCalendarDays'])} | {fmt(trim)} |")
    lines += ["", "## Offene qualifizierte Fälle am Datenende", "",
        "Hypothetischer Liquidationswert zum letzten vorhandenen Schluss einschließlich modellierter Verkaufskosten; kein tatsächlicher Exit. "
        "Nicht mit realisierten Gewinnen addieren. Durch Datenlücken zensierte Fälle sind hier nicht enthalten.", "",
        "| Entry | Stopführung | Offen | Davon Buchwert positiv | Mittel Buchergebnis netto % | Median Buchergebnis netto % |",
        "|---|---|---:|---:|---:|---:|"]
    open_marks = {}
    cost_checks = {}
    for family in ("breakout", "red_retest", "safety_bounce"):
        cs = grouped.get((family, "qualified"), [])
        for model in p["models"]:
            marks = [c["paths"][model]["markNetReturnPct"] for c in cs if c["paths"][model]["status"] == "open"]
            if marks:
                name = family+":"+model
                open_marks[name] = {"open": len(marks), "positiveMarks": sum(v > 0 for v in marks),
                                   "meanMarkNetPct": statistics.mean(marks), "medianMarkNetPct": statistics.median(marks)}
                v = open_marks[name]
                lines.append(f"| {family} | {model} | {len(marks)} | {v['positiveMarks']} | {fmt(v['meanMarkNetPct'])} | {fmt(v['medianMarkNetPct'])} |")
        for model in ("original_safety", "fan_safety"):
            repriced = []
            for c in cs:
                path, entry = c["paths"][model], c["entry"]
                if path["status"] != "closed":
                    continue
                r = entry["rules"]
                assert r["fee_per_order"] == 0, "Repricing formula assumes zero fixed fee"
                side = 2*(r["spread_bps"]/20000+r["slippage_bps"]/10000)
                repriced.append(100*(path["exitPrice"]*(1-side)/(entry["entryPrice"]*(1+side))-1))
            cost_checks[family+":"+model] = {"closed": len(repriced),
                "meanNetPctDoubleVariableCosts": statistics.mean(repriced) if repriced else None,
                "medianNetPctDoubleVariableCosts": statistics.median(repriced) if repriced else None}
    lines += ["", "## Kosten-Nachrechnung auf identischen geschlossenen Fällen", "",
        "Doppelter variabler Spread-/Slippageansatz bei denselben rohen Entry-/Exitkursen und Regeln. "
        "Der nominale Einsatz bleibt pro Fall gleich. Keine Aussage zur tatsächlichen Marktliquidität und kein Ausgleich zensierter Fälle.", "",
        "| Qualifizierter Entry | Safety | Geschlossen | Mittel netto % bei doppelten Kosten | Median netto % bei doppelten Kosten |",
        "|---|---|---:|---:|---:|"]
    for name, v in cost_checks.items():
        family, model = name.split(":")
        lines.append(f"| {family} | {model} | {v['closed']} | {fmt(v['meanNetPctDoubleVariableCosts'])} | {fmt(v['medianNetPctDoubleVariableCosts'])} |")
    lines += ["", "## Technische Prüfung und Dateien", "",
        f"{verify['cases']} Fälle, {verify['fills']} feststellbare Entries und {verify['accountedPaths']} ausgeführte Modellpfade auf IDs, "
        f"kausale Verfügbarkeit, Stopratchets und Kostenrechnung geprüft. {verify['independent5mReplays']} Pfade zusätzlich unabhängig Kerze für Kerze nachgerechnet. "
        "Ein separater AAPL-Pilot prüft alle 60 Pfade und die Unveränderlichkeit bei Weglassen zukünftiger Kerzen.", "",
        f"Plan-ID: `{p['id']}`. Private Quelldateien unter `{root.resolve()}`: `plan.json`, eingefrorener Enginecode, "
        "prüfsummengeschützte `stocks/*.json.gz`, `results.json`, `verification.json`, `cases.csv` und `report-details.json`.", "",
        "Pro Fall: ursprüngliche Signal-/Safety-Geometrie und Kontakte, Entrykurs/-zeit und Kosten, Stopabstand USD/%/ATR4h, "
        "zuletzt abgeschlossene Tageskerze, Stopänderungen mit Bestätigungs-/Aktivierungszeit, Exitgrund/-kurs, MFE/MAE und Status. "
        "Die CSV erleichtert spätere Abstandsauswertungen; verschachtelte Originaldetails bleiben in den Einzelblöcken.", "",
        "## Noch offen", "",
        "Keine prospektive oder unberührte Holdout-Bestätigung; diese bekannten Daten dienen der technischen und deskriptiven Forschung. "
        "Aktuelles Überlebendenuniversum, abhängige Episoden/Marktphasen, fehlende Dividenden/FX und Datenlücken bleiben Grenzen. "
        "Die drei Stopmodelle sind keine vollständige Umsetzung aller subjektiven Exitentscheidungen. Close-Stop mit explizitem Notstop, "
        "neue Abstandsfilter und ein späterer echter Depotbacktest bleiben getrennte nächste Experimente. Sammler bleibt pausiert; keine Providerabrufe, Orders oder Containeränderung.", ""]
    destination = Path(destination)
    destination.write_text("\n".join(lines), encoding="utf-8")
    write(root/"report-details.json", {"planId": p["id"], "paired": comparisons, "concentration": concentration,
        "openMarks": open_marks, "doubleCostsSameCases": cost_checks,
        "stocks": entries, "reportSha256": hashlib.sha256(destination.read_bytes()).hexdigest()})
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root")
    parser.add_argument("destination")
    args = parser.parse_args()
    print(report(args.root, args.destination))
