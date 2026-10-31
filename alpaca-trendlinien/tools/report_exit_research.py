"""Tables for isolated trigger/horizon pairs and all finite portfolio variants."""
import argparse,csv
from collections import defaultdict
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from trigger_horizon_research import checked,FAMILIES,MODELS,MODES,HORIZONS
from strategy_screen import read,load_task,task_path

FAMILY={'breakout':'Ausbruch','red_retest':'Roter Retest'}
MODEL={'fixed':'Fester Stop','original_safety':'Ursprüngliche Safety','fan_safety':'Aktuelle Safety'}
MODE={'hard_stop':'Hard','close_stop':'4h-Close'}


def fmt(x,unit='',signed=False):
    if x is None:return '—'
    return (f'{x:+.3f}' if signed and unit=='R' else f'{x:.3f}' if unit=='R' else f'{x:+.2f}' if signed else f'{x:.2f}').replace('.',',')+(' '+unit if unit else '')


def export(root):
    root=Path(root);p=checked(read(root/'plan.json'));r=read(root/'results.json');rows=[];risk=defaultdict(list)
    for fold in p['folds']['validation']:
        for symbol in p['symbols']:
            block=load_task(task_path(root,'validation',symbol,fold),p)
            for c in block['pilot']['cases']:
                e=c['entry']
                for key,path in c['paths'].items():
                    model,mode,h=key.split(':');factor=e['initialRisk']*e['quantity']/e['plannedRisk'] if e['status']=='filled' else None
                    mae=path.get('maeR',0)*factor if factor is not None and 'maeR' in path else None
                    if path['status']=='closed':risk[c['signal']['family'],key].append(mae)
                    rows.append({'caseId':c['id'],'symbol':symbol,'window':fold['name'],'family':c['signal']['family'],
                        'model':model,'mode':mode,'horizon':h,'entryStatus':e['status'],'entryAt':e['entryAt'],
                        'pathStatus':path['status'],'exitAt':path.get('exitAt'),'exitReason':path.get('reason'),
                        'netR':path.get('netR'),'observedMaePlannedR':mae,'closeDecisionAt':path.get('closeDecision',{}).get('knownAt')})
    rows.sort(key=lambda v:(FAMILIES.index(v['family']),v['window'],v['symbol'],v['entryAt'],v['caseId'],v['model'],v['mode'],int(v['horizon'])))
    with (root/'exit-cases.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    books=[]
    for w in r['windows']:
        for identity,scenarios in w['books'].items():
            f,quality,m,mode,h=identity.split(':')
            for cost,v in scenarios.items():
                books.append({'window':w['fold']['name'],'family':f,'model':m,'mode':mode,'horizon':h,'costs':cost,
                    'netReturnPct':v['markedReturnPct'],'drawdown5mPct':v['max5mSampledDrawdownPct'],'accepted':v['accepted'],
                    'closed':v['closed'],'open':v['open'],'status':v['status'],'halt':str(v['halt'])})
    with (root/'exit-portfolios.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(books[0]));writer.writeheader();writer.writerows(books)
    return risk


def render(root,risk,assessment=None):
    root=Path(root);p=checked(read(root/'plan.json'));r=read(root/'results.json');v=read(root/'verification.json');a=p['dataAudit']
    lines=['# Folgeforschung: Hard-Stop, 4h-Schlusskurs-Exit und längere Haltedauer','',
           'Stand: 30.10.2026. [Vorabplan](EXIT-FORSCHUNGSPLAN-20261030.md). Alle Zeiträume sind bereits bekannte Forschungsdaten; keine neue unabhängige Bestätigung.', '',
           f"{len(p['symbols'])} Aktien, {len(p['folds']['validation'])} Zeitfenster, **{r['cases']:,} unveränderte qualifizierte Entry-Kandidaten**, zwölf Exitvarianten je Familie. Intrabar-/Close-Auslösung und 40-/80-Tage-Grenze sind getrennte Faktoren. Die ursprünglichen Signale, Linien, Safety und nominalen Entries stimmen exakt mit der vorherigen Studie überein.", '',
           '## Konkrete Datenprüfung','',
           f"{a['pairs']} Symbol-/Tagespaare erneut beim identischen Alpaca-SIP/split-Feed abgefragt: **{a['recoveredBars']} zurückgewonnene Kerzen**, {a['stillAbsent']:,} weiterhin fehlende aktienspezifische 5m-Intervalle, {a['conflictingPairs']} widersprüchliche Überlappungen. Die Antworten entsprechen den bestehenden Daten. Keine neuen Datasets veröffentlicht, keine Kerzen ergänzt, Sammler weiterhin pausiert.", '',
           'Vier ergänzende 1m-Abfragen: LIN und MMM am 19.04.2021, ANET am 21.06.2018, AXP am 25.10.2021. In keinem der vier betroffenen 5m-Abschnitte lagen Minutenkerzen vor. Das beweist keine Handelsaussetzung; Daten fehlen auch im erneuten Providerabruf. Die Aussage betrifft diese ausgewählten Tage, nicht die gesamte Datenbank. Protokolle und Providerantworten bleiben privat gespeichert.', '',
           'API-Vertrag: [Alpaca Historical Bars](https://docs.alpaca.markets/us/reference/stockbars). Keine anderen Feeds oder unvereinbar bereinigten Kurse in das Archiv gemischt. Für eine spätere zweite Quelle einen vollständigen separaten Referenzversuch vorsehen.', '',
           '## Exakter Exitvertrag','',
           '- Hard-Stop: vorhandener Stop intrabar, Gaps am verfügbaren Open; keine Garantie eines Fills genau am Stop.',
           '- 4h-Close: Schluss unter dem vorher aktiven gepufferten Ratchet-Stop; Ausführung erst am nächsten erwarteten 5m-Open nach 300 Sekunden. Kein zusätzlicher Hard-Notstop in diesem Versuch.',
           '- Beide verwenden dieselbe 0,3-Prozent-Pufferung und dieselbe Stopführung. Dies ist kein Test der abweichenden Schwelle „Safety minus 0,15 ATR“.',
           '- Stopführung fest, ursprüngliche gebundene Safety oder später bekannte aktuelle enge Safety. Geometrische Stops nur aufwärts und nach bestätigtem Quellschluss/Verzögerung wirksam.',
           '- Zeitexit nach 40 oder 80 Handelssitzungen nach dem Einstiegstag; Nachlauf jeweils bis 160 Kalendertage nach Entry-Ende. Kein Profitziel und kein Teilverkauf.', '',
           '**Risikobezug:** Geplante Stoprisiken sind keine Obergrenze realer Verluste. Insbesondere der Close-Stop kann zwischenzeitlich und beim späteren Verkauf deutlich mehr verlieren. Die Stückzahl bleibt aus dem anfänglichen geplanten Stop berechnet. Das ist ein bewusst isolierter Regelvergleich, keine Empfehlung eines ungesicherten Live-Betriebs.', '',
           '## Gleiche Einstiege: Hard gegen Close','',
           'Jede Zeile verwendet dieselben gemeinsam vollständig beobachteten Case-IDs für beide Auslösearten. R = Nettoergebnis / ursprünglich geplantes Risiko. Positive Differenz bevorzugt Close. Fehlende Beobachtungen werden gezählt, nicht als Verlust oder Gewinn ersetzt. Unterschiedliche Zeilen können unterschiedliche vollständige Teilmengen haben.', '',
           '| Einstieg | Stopführung | Max. Tage | Gemeinsame Fälle / nominale Entries | Hard Ø R | Close Ø R | Close minus Hard |',
           '|---|---|---:|---:|---:|---:|---:|']
    for f in FAMILIES:
        for key,x in r['paired'][f]['trigger'].items():
            model,h=key.split(':')
            lines.append(f"| {FAMILY[f]} | {MODEL[model]} | {h} | {x['commonComplete']} / {x['filled']} | {fmt(x['firstMeanR'],'R',True)} | {fmt(x['secondMeanR'],'R',True)} | {fmt(x['meanDeltaR'],'R',True)} |")
    lines+=['','## Gleiche Einstiege: 40 gegen 80 Handelstage','',
            '| Einstieg | Stopführung | Auslösung | Gemeinsame Fälle / nominale Entries | 40 Tage Ø R | 80 Tage Ø R | 80 minus 40 |',
            '|---|---|---|---:|---:|---:|---:|']
    for f in FAMILIES:
        for key,x in r['paired'][f]['horizon'].items():
            model,mode=key.split(':')
            lines.append(f"| {FAMILY[f]} | {MODEL[model]} | {MODE[mode]} | {x['commonComplete']} / {x['filled']} | {fmt(x['firstMeanR'],'R',True)} | {fmt(x['secondMeanR'],'R',True)} | {fmt(x['meanDeltaR'],'R',True)} |")
    lines+=['','**Beobachtbarkeitsverzerrung bleibt möglich:** Gemeinsame vollständige Pfade sind eine nach Beobachtbarkeit ausgewählte Teilmenge. Überlappende Episoden und gemeinsame Marktphasen sind nicht unabhängig. Keine p-Werte, keine neue Kontrolltor-Freigabe und kein Optimieren auf diesen Tabellen.', '',
            '## Verlustverteilung der vollständig beobachteten Einzelpfade','',
            'Diese Tabelle verwendet je Variante deren eigene vollständige Pfade, deshalb keine direkten ungepaarten Mittelwertvergleiche daraus ableiten. Die ungünstigste beobachtete Bewegung vor dem Exit nutzt 5m-OHLC und ist kein tickgenauer Depotdrawdown.', '',
            '| Einstieg | Führung / Auslösung / Tage | Vollständig | Trefferquote | Schlechtestes realisiertes R | Verlust größer als 1R | Schlechteste beobachtete Bewegung R |',
            '|---|---|---:|---:|---:|---:|---:|']
    for f in FAMILIES:
        for key,x in r['summaries'][f].items():
            model,mode,h=key.split(':');maes=[z for z in risk[f,key] if z is not None]
            lines.append(f"| {FAMILY[f]} | {MODEL[model]} / {MODE[mode]} / {h} | {x['closed']} | {fmt(x['winPct'],'%')} | {fmt(x['worstNetR'],'R',True)} | {fmt(x['lossBeyondOneRPct'],'%')} | {fmt(min(maes) if maes else None,'R',True)} |")
    lines+=['','## Endliche Depots – keine nachträgliche Entry-Auswahl','',
            'Je Variante/Zeitfenster separat 2.000 USD, 1 % geplantes Risiko, maximal 25 % pro Position und drei Positionen. Alle passenden Entries einschließlich später zensierter Pfade. Andere Exitzeitpunkte ändern spätere Belegung und Stückzahl. Die Tabellenrenditen sind weder additiv noch annualisiert; spätere Ausstiege liegen im zusätzlichen Nachlauf.', '',
            '| Entry-Zeitraum | Einstieg | Führung / Auslösung | 40 Tage netto | 80 Tage netto | 40 Tage DD 5m | 80 Tage DD 5m | Trades 40 / 80 |',
            '|---|---|---|---:|---:|---:|---:|---|']
    for w in r['windows']:
        for f in FAMILIES:
            for model in MODELS:
                for mode in MODES:
                    a=w['books'][f'{f}:qualified:{model}:{mode}:40']['base'];b=w['books'][f'{f}:qualified:{model}:{mode}:80']['base']
                    net=lambda x:'unvollständig' if x['markedReturnPct'] is None else fmt(x['markedReturnPct'],'%',True)
                    lines.append(f"| {w['fold']['name']} | {FAMILY[f]} | {MODEL[model]} / {MODE[mode]} | {net(a)} | {net(b)} | {fmt(a['max5mSampledDrawdownPct'],'%',True)} | {fmt(b['max5mSampledDrawdownPct'],'%',True)} | {a['accepted']} / {b['accepted']} |")
    lines+=['','Bei unvollständigen Büchern ist der Drawdown nur der beobachtete Teilpfad. Die vollständigen Depotzahlen unter doppeltem Spread/Slippage stehen zusätzlich in `exit-portfolios.csv`.', '',
            '## Technische Nachweise und verbleibende Grenzen','',
            f"{v['blocks']} Quellblöcke, {v['entries']:,} unveränderte Entries, {v['paths']:,} Exitpfade und {v['cashAnd5mValuationBooks']} Kapitalbücher geprüft. {v['originalHard40ComparisonsReproduced']} ursprüngliche 40-Tage-Hard-Referenzvergleiche mit früherem Beobachtungsende reproduziert. Close-Entscheidungen, Ausführungsverzögerung, R-Arithmetik und Quellzuordnung geprüft. Bewertungs- und Drawdownkontrolle im vorhandenen 5m-/Entscheidungsraster.", '',
            'Regression: 509 Python-Tests ohne Fehler (ein bestehender Skip), 70 Web-/Chart-JavaScript-Tests bestanden. Beim ersten Anlegen kollidierte der neue Modulname mit einem bestehenden Forschungsmodul und dessen Testdatei. Beide Bestandsdateien wurden byteidentisch aus dem vorher unveränderten Repository-Stand wiederhergestellt. Die neue Untersuchung liegt separat in `trigger_horizon_research.py`; alte Funktionen und neue Tests sind getrennt. Ursprünglicher neuer Produzercode und erster Lauf bleiben archiviert. Ein neuer Plan übernahm die unveränderten Pfade nach Prüfung identischer wissenschaftlicher Funktions-ASTs, Eingaben und Abhängigkeiten. Alle Tabellen und wissenschaftlichen Resultate wurden danach exakt reproduziert.', '',
            'Bekannte historische Zeiträume, überlebendes heutiges Universum, verbleibende Datenlücken und unvollständiger Split-/Ganzaktien-/Dividenden-/FX-Abgleich verhindern weiterhin eine operative Freigabe. Für diese zusätzlichen Varianten wurde keine neue unabhängige Kontrollstudie oder prospektive Gewinnbilanz eröffnet. Bestehender Chart, gespeicherte Zeichnungen, Journal und bisherige Forschungsengine bleiben erhalten.', '',
            'Private Dateien: `plan.json`, Quellblöcke, `results.json`, `verification.json`, `exit-cases.csv`, `exit-portfolios.csv` und einzelne Kapitalbücher. Alles verwendet den vorhandenen `TORI_DATA_DIR`. Keine Zugangsdaten, Runtime-Daten oder Ledger nach GitHub übernehmen.', '',
            '```text',
            'python tools/run_exit_research.py --root NEUER_PRIVATER_VERSUCH --source PRIVATER_ROBUSTHEITSVERSUCH --data-audit PRIVATER_DATENPRUEFORDNER --phase prepare',
            'python tools/run_exit_research.py --root PRIVATER_VERSUCH --phase build --workers 2',
            'python tools/run_exit_research.py --root PRIVATER_VERSUCH --phase evaluate',
            'python tools/verify_exit_research.py --root PRIVATER_VERSUCH',
            '```']
    if assessment:
        note=Path(assessment).read_text(encoding='utf-8').strip();index=lines.index('## Konkrete Datenprüfung');lines[index:index]=[note,'']
    return '\n'.join(lines)+'\n'


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--root',required=True);a.add_argument('--output',required=True);a.add_argument('--assessment');args=a.parse_args()
    risk=export(args.root);Path(args.output).write_text(render(args.root,risk,args.assessment),encoding='utf-8')
