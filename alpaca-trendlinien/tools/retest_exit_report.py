"""Rebuild all paired Retest result tables from immutable local study blocks."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from datasets import digest


def read(path):
    data = json.loads(path.read_text("utf-8"))
    if "checksum" in data and data["checksum"] != digest({k:v for k,v in data.items() if k != "checksum"}):
        raise ValueError("Corrupt result")
    return data


def f(value):
    return "–" if value is None else f"{value:.3f}"


def run(root, output):
    root=Path(root).resolve()
    contract=read(root/"contract.json")
    lines=["# Retest-Exitvergleich: vollständige Tabellen", "",
        "Vertrag `"+digest(contract)+"`. Regeln: [RETEST-EXIT-TEST.md](RETEST-EXIT-TEST.md). Bilanz: [RETEST-EXIT-ERGEBNISSE.md](RETEST-EXIT-ERGEBNISSE.md).", "",
        "Einzeltrade-R ist nach Kosten und anfänglichem Vertragsrisiko normiert. Historiengruppen und Geometrien getrennt; Fälle können überlappen. Nicht abgeschlossene Pfade zählen nicht als Nullgewinne. Kapitalrechnungen sind eigene modellierte USD-Depots, keine echten Konten. Es wird keine spätere Pfadvollständigkeit zur Depot-Entryauswahl verwendet.", ""]
    for stage in ("development","validation"):
        result=read(root/(stage+"-results.json"))
        if result["contractHash"] != digest(contract):
            raise ValueError("Contract mismatch")
        lines.extend(["## "+stage,"",f"Archivierte Entries: {result['rawEntries']}; kausal vollständige Vorgeschichte: {result['causalHistoryComplete']}; reine Kalenderzensierung: {result['calendarCensored']}.","",
            "| Geometrie / Vorgeschichte | Exit | Fälle | geschlossen | unbekannt | Gewinnanteil % | Ø R | Ø Gewinn R | Ø Verlust R | Profitfaktor R | Ø Netto % | längste Verlustserie | Stopanhebungen |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"])
        for key,group in result["groups"].items():
            for model,v in group["models"].items():
                lines.append(f"| {key} | {model} | {v['cases']} | {v['closed']} | {v['unknown']} | {f(v['winPct'])} | {f(v['meanR'])} | {f(v['meanWinR'])} | {f(v['meanLossR'])} | {f(v['profitFactorR'])} | {f(v['meanReturnPct'])} | {v['longestLossStreak']} | {v['stopRaises']} |")
        lines.extend(["","### Gepaarte R-Differenz: Nachziehen minus fester Stop","",
            "| Gruppe | beide geschlossen | Ø Differenz R | Blockintervall unten | oben | volle Zehn-Tage-Strecke: feste Ø R | nachgezogene Ø R |",
            "|---|---:|---:|---:|---:|---:|---:|"])
        for key,v in result["groups"].items():
            lines.append(f"| {key} | {v['pairedClosed']} | {f(v['meanDeltaR'])} | {f(v['deltaInterval']['low'])} | {f(v['deltaInterval']['high'])} | {f(v['fullHorizonPaired']['fixed']['meanR'])} | {f(v['fullHorizonPaired']['higher_low_stop']['meanR'])} |")
        lines.extend(["","### Kapital: 2.000 USD je unabhängig gestarteter Phase","",
            "| Geometrie / Exit | Status | akzeptiert | geschlossen | offen | Endwert USD | Rendite % | max. 5m-Drawdown % |",
            "|---|---|---:|---:|---:|---:|---:|---:|"])
        for key,v in result["portfolios"].items():
            lines.append(f"| {key} | {v['status']} | {v['accepted']} | {v['closed']} | {v['open']} | {f(v['markedEquity'])} | {f(v['markedReturnPct'])} | {f(v['max5mSampledDrawdownPct'])} |")
        lines.append("")
    Path(output).write_text("\n".join(lines),"utf-8")


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    run(args.root,args.output)
