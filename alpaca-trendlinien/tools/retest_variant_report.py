"""Rebuild all preregistered exit-variant tables without changing the cohort."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from datasets import digest
from tools.retest_exit_study import read,checked


def f(value):
    return "–" if value is None else f"{value:.3f}"


def run(root,output):
    root=Path(root).resolve()
    contract=read(root/"contract.json")
    lines=["# Drei Retest-Exitvarianten: vollständige Tabellen","",
        "Vertrag `"+digest(contract)+"`. [Vorabregeln](RETEST-EXIT-VARIANTEN-PLAN.md), [Fazit](RETEST-EXIT-VARIANTEN-ERGEBNISSE.md).",
        "Bekannte Entwicklungs-/Prüfzeiträume, überlappende Fälle; keine unabhängige Marktvalidierung. Alle Ergebnisse nach Modellkosten. Fehlende Daten bleiben unbekannt. Die feste Referenz wird wiederholt gezeigt, nicht als weitere unabhängige Stichprobe gezählt.",""]
    for variant in contract["variants"]:
        for stage in contract["phases"]:
            result=checked(root/variant/(stage+"-results.json"))
            if result["contractHash"] != digest(contract):raise ValueError("Contract mismatch")
            lines.extend(["## "+variant+" / "+stage,"",
                "| Gruppe | Modell | Fälle | geschlossen | unbekannt | Ø R | Gewinnanteil % | Ø Gewinn R | Ø Verlust R | Profitfaktor R | Ø Netto % | längste Verlustserie | ohne besten Fall Ø R |",
                "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"])
            for key,group in result["groups"].items():
                for model,v in group["models"].items():
                    lines.append(f"| {key} | {model} | {v['cases']} | {v['closed']} | {v['unknown']} | {f(v['meanR'])} | {f(v['winPct'])} | {f(v['meanWinR'])} | {f(v['meanLossR'])} | {f(v['profitFactorR'])} | {f(v['meanReturnPct'])} | {v['longestLossStreak']} | {f(v['withoutBestMeanR'])} |")
            lines.extend(["","### Gepaarter Unterschied: Variante minus Referenz","",
                "| Gruppe | beide geschlossen | Ø Differenz R | Blockintervall unten | oben | gleiche volle Zehn-Tage-Strecke: Referenz Ø R | Variante Ø R |",
                "|---|---:|---:|---:|---:|---:|---:|"])
            for key,v in result["groups"].items():
                lines.append(f"| {key} | {v['pairedClosed']} | {f(v['meanDeltaR'])} | {f(v['deltaInterval']['low'])} | {f(v['deltaInterval']['high'])} | {f(v['fullHorizonPaired']['fixed']['meanR'])} | {f(v['fullHorizonPaired'][variant]['meanR'])} |")
            lines.extend(["","### Je Phase unabhängig 2.000 USD, vollständige bekannte Vorgeschichte","",
                "| Geometrie / Exit | Status | akzeptiert | geschlossen | offen | Endwert USD | Rendite % | max. 5m-Drawdown % |",
                "|---|---|---:|---:|---:|---:|---:|---:|"])
            for key,v in result["portfolios"].items():
                lines.append(f"| {key} | {v['status']} | {v['accepted']} | {v['closed']} | {v['open']} | {f(v['markedEquity'])} | {f(v['markedReturnPct'])} | {f(v['max5mSampledDrawdownPct'])} |")
            lines.append("")
    Path(output).write_text("\n".join(lines),"utf-8")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    run(args.root,args.output)
