"""Development-only feature descriptions and reserved-window result tables."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datasets import digest
from retest_observation import diagnose
from tools.retest_exit_study import checked, read, save


def render(root, development, output):
    contract = read(root/"contract.json")
    result = checked(root/"results.json")
    if result["contractHash"] != digest(contract):
        raise ValueError("Results contract mismatch")
    dev_contract = read(development/"contract.json")
    records = []
    for file in sorted((development/"development").glob("*.json")):
        block = checked(file)
        if block["contractHash"] != digest(dev_contract):
            raise ValueError("Development archive mismatch")
        records.extend(block["records"])
    diagnosis = {"sourceContractHash": digest(dev_contract), "stage": "development_only", **diagnose(records)}
    save(root/"development-features.json", diagnosis)
    lines = ["# Unabhängiger Retest-Zeitvergleich und Entwicklungsdiagnose", "",
        f"Vorabvertrag `{digest(contract)}`. Zeitraum {contract['phase']['startDate']} bis {contract['phase']['endDate']}, "
        f"{contract['phase']['sessions']} XNYS-Sitzungen, {len(contract['symbols'])} unverändert gewählte Aktien.", "",
        "Alle Modellzahlen nach angenommenen Kosten, USD. Überlappende Einzelpositionen sind kein Depot.", "",
        "## Datenabdeckung vor Ergebnisauswertung", "",
        "| Aktie | vorhandene 5m / erwartet | Abdeckung |", "|---|---:|---:|"]
    for symbol, row in contract["inventory"].items():
        lines.append(f"| {symbol} | {row['available5m']} / {row['expected5m']} | {100*row['available5m']/row['expected5m']:.2f} % |")
    lines += ["", "## Abgeschlossene Hauptgruppen", "",
        "Vollständige relevante Vorgeschichte und kalendarisch genug Nachlauf; zukünftige Datenabdeckung ist kein Auswahlfilter.", "",
        "| Geometrie / Exit | Fälle | geschlossen | unbekannt | mittlere R | Gewinnanteil |", "|---|---:|---:|---:|---:|---:|"]
    def number(v):
        return "—" if v is None else f"{v:.4f}"
    for model in contract["models"]:
        group = result["groups"][model+"/complete_history"]
        for variant, row in group["models"].items():
            lines.append(f"| {model} / {variant} | {row['cases']} | {row['closed']} | {row['unknown']} | {number(row['meanR'])} | {number(row['winPct'])} % |")
        lines += ["", f"{model}: gepaarte Fälle {group['pairedClosed']}, mittlere ATR−Fest-Differenz {number(group['meanDeltaR'])}R; "
            f"beschreibendes Aktie-/Quartal-Intervall: `{json.dumps(group['deltaInterval'], ensure_ascii=False)}`.", "",
            f"Unvollständige Vorgeschichte (separat): {result['groups'][model+'/gapped_history']['cases']} Fälle; "
            f"zu wenig kalendarischer Nachlauf: {result['lateEntries'][model]} weitere Entries.", ""]
    lines += ["## Modellierte Portfolios", "", "| Geometrie / Exit | angenommen / geschlossen / offen | Endwert USD | Rendite | max. 5m-Drawdown | Status |",
              "|---|---:|---:|---:|---:|---|"]
    for key, p in result["portfolios"].items():
        lines.append(f"| {key} | {p['accepted']} / {p['closed']} / {p['open']} | {p['markedEquity']:.2f} | {p['markedReturnPct']:.4f} % | {p['max5mSampledDrawdownPct']:.4f} % | {p['status']} |")
    lines += ["", "Drawdown auf 5m-Schlussbewertungen; größere intrabar Verluste möglich. Endwerte sind modelliert, nicht erzielte Brokerergebnisse.", "",
              "## Vorabtor", "", "```json", json.dumps(result["assessment"], ensure_ascii=False, indent=2), "```", "",
              "## Einstiegsmerkmale ausschließlich aus der alten Entwicklung", "",
              "Median, keine optimierten Grenzwerte. Gewinner/Verlierer beziehen sich auf den festen Stop nach Kosten; Gruppen können zeitlich/je Aktie abhängig sein.", "",
              "| Merkmal | positiv: verfügbar / Median | nichtpositiv: verfügbar / Median | fehlend gesamt |", "|---|---:|---:|---:|"]
    for feature in diagnosis["features"]:
        rows = {k: diagnosis["groups"][k]["numeric"][feature] for k in ("all", "positive", "nonpositive")}
        lines.append(f"| {feature} | {rows['positive']['available']} / {number(rows['positive']['median'])} | "
                     f"{rows['nonpositive']['available']} / {number(rows['nonpositive']['median'])} | {rows['all']['missing']} |")
    for label, group in diagnosis["groups"].items():
        lines += ["", f"{label}: {group['cases']} Fälle aus {group['symbols']} Aktien; Tages-/Wochenkontext `{json.dumps(group['context'], ensure_ascii=False)}`."]
    lines += ["", "Merkmale waren vor oder beim Entry bekannt: Linienmerkmale aus dem eingefrorenen Signal, Kontext aus damals geschlossenen Kerzen; Risiko/Raum/Safety-Abstand verwenden den beobachteten Entry-Open. Keine späteren Verlaufskerzen.", "",
              "Der reservierte Zeitraum ist nach diesem Vergleich verbraucht. Kein Parameterlernen daraus; für neue Kriterien braucht es neue Evidenz. Heutiges US-Universum, IEX-Lücken, wenige abhängige Fälle und kein Zufallsentry-Exitvergleich begrenzen die Aussage.", ""]
    output.write_text("\n".join(lines), "utf-8")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True)
    p.add_argument("--development", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    render(Path(a.root), Path(a.development), Path(a.output))
