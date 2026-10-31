"""Explicit, bounded, offline pilot command for humans and Hermes."""
from datetime import datetime, timezone
import json
from pathlib import Path

from datasets import read_dataset
from models import DataError, NY
from pilot_backtest import PilotSpec, run, FAMILIES, MODELS


def add_commands(commands):
    command = commands.add_parser("pilot-backtest",help="Offline-Technikpilot: eine Dataset-ID, maximal zwölf Monate")
    command.add_argument("--dataset",required=True)
    command.add_argument("--start",default="2023-01-01")
    command.add_argument("--end",default="2023-12-31")
    command.add_argument("--outcome-end",default="2024-03-31")
    command.add_argument("--output",required=True,help="Neuer Ergebnisordner außerhalb des veröffentlichten Quellbestands")


def text_report(result):
    m,s=result["manifest"],result["summary"]
    lines=["# Begrenzter Backtest-Technikpilot", "",f"Aktie: **{m['symbol']}** · 4h · SIP/split · {m['spec']['start']} bis {m['spec']['end']}",
        "", "Entwicklungstest auf bekanntem Bestand. Einzelfälle können sich überlappen. Kein gemeinsames Depot und kein Profitabilitätsnachweis.",
        "",f"Run-ID: `{result['runId']}`",f"Dataset-ID: `{m['datasetId']}`",
        f"Laufzeit: {result['elapsedSeconds']:.3f} s · technische Integritätsprüfung: {'OK' if result['audit']['passed'] else 'FEHLER'}",
        "", "## Drei Entry-Familien", "", "| Familie | Signale | Modell-Entries | Nicht ausgeführt |", "|---|---:|---:|---:|"]
    for family in FAMILIES:
        row=s[family];filled=row["entryStatuses"].get("filled",0)
        lines.append(f"| {family} | {row['signals']} | {filled} | {row['signals']-filled} |")
    lines += ["", "Signale sind je Familie/Schluss/Kontaktklasse zusammengefasst. Unterschiedliche Familien oder Kontaktklassen desselben Marktmoments sind weiterhin abhängig.",
        "", "## Exitvergleiche", "", "Mittelwerte beziehen sich nur auf geschlossene Einzelfälle. Offene und unklare Pfade stehen daneben; niemals als summierte Depotrendite lesen.",
        "", "| Familie | Modell | Auslösung | Handelstage | Geschlossen | Positiv | Mittel netto R | Offen/unklar |", "|---|---|---|---:|---:|---:|---:|---:|"]
    for family in FAMILIES:
        for key,v in s[family]["comparisons"].items():
            model,mode,h=key.split(":")
            uncertain=sum(v["statuses"].get(k,0) for k in ("open","censored","invalid","unavailable","pending"))
            mean="—" if v["meanNetR"] is None else f"{v['meanNetR']:.3f}"
            lines.append(f"| {family} | {model} | {mode} | {h} | {v['closed']} | {v['positive']} | {mean} | {uncertain} |")
    lines += ["", "## Definitionen und Grenzen", "",
        "- Bei roten Entries gilt die aktuelle gültige enge Safety am Signal; Safety/Stop des ersten Bruchs bleiben separat archiviert. Bounce benötigt vorher bekannte A+-Safety, begrenzte Docht-/Körperverletzung, Reaktion und erneute Aktivierung.",
        "- Sofort sauberer und verzögert sauberer Ausbruch sind Untertypen derselben Familie. Wartefristen: eine Folgekerze für clean, fünf Quellkerzen für roten Retest.",
        "- Hard-Stop nutzt 5m-OHLC; Close-Stop entscheidet erst am 4h-Schluss unter demselben prozentual gepufferten Stop. Dies ist ausdrücklich nicht Safety minus ATR.",
        "- Neue Stops gelten erst nach Quellschluss und Verzögerung. Gaps, Gebühren, Spread, Slippage und ganze Stückzahlen sind modelliert, nicht exakt vorhersagbar.",
        "- Alle Exitpfade haben einen deklarierten Zeitabschluss. Die 5/10/20/40-Tage-Beobachtungen im JSON sind zusätzlich reine Kursverläufe, auch nach hypothetischem Stop.",
        "- Kein SMA-Filter. Tages-SMA200 nur Kontext; vollständige Tages-/Wochen-Fächerfilter und universumsweite Validierung bleiben geplant.",
        "- Ein Safety-Rücksetzer nach Ausbruch wird nicht zusätzlich als vierte Hauptfamilie gewertet; diese gesonderte Untergruppe bleibt späterer Ausbau.",
        "- Kurslücken führen zu explizit unvollständigen Pfaden. Fehlende erwartete Entry-Opens werden nicht durch spätere günstige Opens ersetzt.",
        "", "## Prüffälle", "", "Die vollständigen Originalanker, Signal-Safetys, Ereignisse und Stopänderungen stehen in result.json; manifest.json enthält Regeln und Quellcode-Prüfsummen.",
        "", "| Familie | Signal (ET) | Entry-Status | Ursprünglicher Stop | Chart-Rekonstruktion |", "|---|---|---|---:|---|"]
    from urllib.parse import urlencode
    for case in result["cases"]:
        e=case["signal"]
        at=datetime.fromtimestamp(e["signalAt"],NY).isoformat()
        query=urlencode({"symbol":m["symbol"],"dataset":m["datasetId"],"tf":"4h","engine":"fan_master","asof":at})
        # A normal chart recalculates the state; it is not the old episode archive.
        lines.append(f"| {e['family']} | {at} | {case['entry']['status']} | {e['initialStop']} | [Zeitpunkt öffnen](http://127.0.0.1:8876/?{query}) |")
    lines += ["", "Chartlinks verwenden den lokalen Prüfport 8876; Host/Port gegebenenfalls anpassen. Sie rekonstruieren den Zeitpunkt und starten mit Analyse aus. Ursprüngliche, gegebenenfalls inzwischen abgelöste Episodenlinien sind verbindlich im JSON archiviert; diese Links sind keine neue gebundene Pilot-Fallansicht.", ""]
    return "\n".join(lines)


def save_result(destination,result):
    folder=Path(destination).resolve()
    if folder.exists():
        raise DataError("Pilot-Ausgabeordner existiert bereits. Neuen Ordner wählen; alte Ergebnisse bleiben erhalten.",409)
    folder.mkdir(parents=True)
    documents={"manifest.json":json.dumps(result["manifest"],ensure_ascii=False,allow_nan=False,indent=2),
               "result.json":json.dumps(result,ensure_ascii=False,allow_nan=False,indent=2),
               "report.md":text_report(result)}
    for name,text in documents.items():
        path=folder/name;temporary=path.with_suffix(path.suffix+".tmp")
        temporary.write_text(text,encoding="utf-8");temporary.replace(path)
    return str(folder)


def execute(args):
    if Path(args.output).exists():
        raise DataError("Ausgabe existiert bereits; für Wiederholung neuen Ordner wählen.",409)
    spec=PilotSpec(start=args.start,end=args.end,outcome_end=args.outcome_end)
    spec.bounds()
    result=run(read_dataset(args.dataset),spec)
    output=save_result(args.output,result)
    if not result["audit"]["passed"]:
        raise DataError("Technische Pilot-Prüfung fehlgeschlagen; Diagnose unter "+output,422)
    return {"runId":result["runId"],"output":output,"audit":result["audit"],
            "elapsedSeconds":result["elapsedSeconds"],"families":{k:{n:v[n] for n in ("signals","entryStatuses","cohorts","subtypes")} for k,v in result["summary"].items()}}
