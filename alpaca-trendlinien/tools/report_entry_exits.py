"""Readable entry-first/exit-second tables and sortable private portfolio export."""
import argparse
from collections import defaultdict
import csv
from pathlib import Path
import statistics
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from entry_exit_comparison import FAMILIES, COHORTS, MODELS
from strategy_screen import read

FAMILY={'breakout':'Ausbruch','red_retest':'Roter Retest','safety_bounce':'Safety-Bounce'}
COHORT={'qualified':'qualifiziert','two':'zwei Kontakte','three_young':'drei Kontakte, zu jung'}
MODEL={'fixed':'Fester Stop','original_safety':'Ursprüngliche Safety','fan_safety':'Aktuelle Safety'}


def fmt(value,unit='',signed=False):
    if value is None:return '—'
    s=(f'{value:+.3f}' if signed else f'{value:.3f}') if unit=='R' else (f'{value:+.2f}' if signed else f'{value:.2f}')
    return s.replace('.',',')+(' '+unit if unit else '')


def tail_diagnostics(root):
    values=defaultdict(list)
    with (Path(root)/'entry-exit-cases.csv').open(encoding='utf-8-sig',newline='') as stream:
        for row in csv.DictReader(stream):
            if row['cohort']=='qualified' and row['commonComplete']=='True':
                values[row['family'],row['exitModel']].append(float(row['netR']))
    out={}
    for (f,m),rs in values.items():
        rs.sort(reverse=True);positive=sum(r for r in rs if r>0)
        out[f,m]={'bestR':rs[0],'top5PositiveSharePct':100*sum(r for r in rs[:5] if r>0)/positive if positive else None,
                  'meanWithoutBest5':statistics.mean(rs[5:]) if len(rs)>5 else None}
    return out


def render(root,assessment=None):
    root=Path(root);r=read(root/'comparison.json');v=read(root/'verification.json')
    lines=['# Einstiegskriterien und Exitmethoden – getrennte Auswertung', '',
        'Stand: 30.10.2026. [Vergleichsplan und Definitionen](ENTRY-EXIT-VERGLEICHSPLAN-20261030.md).', '',
        f"{r['cases']:,} gespeicherte Fälle aus {len({b['symbol'] for b in r['inputProofs']})} Aktien und {len(r['windows'])} Entry-Zeiträumen nach Einstiegsfamilie/Kontaktklasse getrennt. Drei Exitmethoden auf denselben Einstiegen verglichen; zusätzlich getrennte endliche Depotbücher. **Nachträgliche Diagnose auf bekannten Daten, keine neue Strategiefreigabe.**", '',
        '## Welche Einstiege und Exits sind gemeint?', '',
        '| Einstieg | Tatsächlich geprüft |','|---|---|',
        '| Ausbruch | Sauberer 4h-Schluss mindestens 0,15 ATR über einer vorher bekannten roten Linie; sofortiger oder innerhalb einer weiteren Quellkerze sauberer Ausbruch |',
        '| Roter Retest | Rücklauf/Bestätigung an der ursprünglich gebrochenen roten Linie im fünf-Quellkerzen-Fenster; gültige aktuelle Safety am tatsächlichen Signal |',
        '| Safety-Bounce | Rücklauf von oben an eine zuvor qualifizierte steigende Safety, begrenzte Docht-/Körperverletzung, bullischer Schluss und Wiederbewaffnung/Cooldown |', '',
        'Qualifiziert bedeutet mindestens drei bestätigte Kontakte und mindestens sieben Tage im damaligen Szenariostand. Zwei Kontakte und mindestens drei noch zu junge Kontakte werden separat ausgewiesen. Klassen werden nicht durch spätere Kerzen aufgewertet. Ein Safety-Bounce macht nicht automatisch auch einen roten Widerstand qualifiziert.', '',
        '| Exit | Tatsächlich geprüft |','|---|---|',
        '| Fester Stop | Safety am Einstieg minus 0,3 %, danach unverändert |',
        '| Ursprüngliche Safety | Dieselbe am Einstieg gebundene Gerade fortschreiben; Stop nur aufwärts nachziehen |',
        '| Aktuelle Safety | Später bekannte gültige enge Safety der Engine berücksichtigen; Stop niemals senken |', '',
        '**Gemeinsam:** Hard-Stop, Änderungen erst nach kausalem Quellschluss und Verzögerung wirksam, maximal 40 Handelstage. Die 40 Tage sind eine technische Versuchsannahme, kein bestätigtes Tori-Exitkriterium. Kein festes Gewinnziel. Close-Stop, Teilverkäufe, höhere Pivot-Tiefs und Break-even-Umschaltungen wurden hier nicht zusätzlich berechnet. Der aktuelle Safety-Modus garantiert keinen Wechsel auf eine bestimmte steilere Fächerstufe. Ein speziell an eine vorherige Ausbruchsepisode gebundener Safety-Retest ist weiterhin keine eigene ausgewiesene Entry-Familie.', '',
        '## Direkter Exitvergleich – identische qualifizierte Einstiege', '',
        '**R** ist das Nettoergebnis geteilt durch das ursprünglich geplante Risiko inklusive modellierter Ausführungskosten. +0,5R bedeutet im Mittel die Hälfte dieses Risikos als Gewinn. Es ist keine Depot-Prozentzahl. Alle drei Werte einer Zeile stammen aus exakt denselben Case-IDs.', '',
        '| Einstieg | Kandidaten | Modell-Entries | Gemeinsam vollständig | Fester Stop Ø | Ursprüngliche Safety Ø | Aktuelle Safety Ø |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for family in FAMILIES:
        g=r['groups'][family+':qualified'];m=g['models']
        lines.append(f"| {FAMILY[family]} | {g['signals']} | {g['filled']} | {g['commonComplete']} | {fmt(m['fixed']['sameEntries']['meanNetR'],'R',True)} | {fmt(m['original_safety']['sameEntries']['meanNetR'],'R',True)} | {fmt(m['fan_safety']['sameEntries']['meanNetR'],'R',True)} |")
    lines += ['', '**Beobachtbarkeitsgrenze:** Die gemeinsame Teilmenge verlangt drei vollständige Exitpfade. Sie kann durch fehlende Daten verzerrt sein. Alle Kandidaten und unvollständigen Fälle bleiben gezählt; für die Depotberechnung werden solche Fälle ausdrücklich nicht vorher entfernt. Überlappende Ausbruch-/Retest-/Bounce-Episoden sind keine unabhängigen Stichproben.', '',
              '| Einstieg | Exit | Gleiche Fälle | Trefferquote | Median | Ø Kursrendite nach variablen Kosten | Gewinnfaktor auf R-Basis | Median Haltedauer, Kalendertage | Mindestens +1R gesehen, dann nicht positiv |',
              '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for family in FAMILIES:
        for model in MODELS:
            s=r['groups'][family+':qualified']['models'][model]['sameEntries']
            lines.append(f"| {FAMILY[family]} | {MODEL[model]} | {s['n']} | {fmt(s['winPct'],'%')} | {fmt(s['medianNetR'],'R',True)} | {fmt(s['meanPriceReturnPct'],'%',True)} | {fmt(s['profitFactorR'])} | {fmt(s['medianCalendarDays'])} | {fmt(s['oneRThenNonpositivePct'],'%')} |")
    lines += ['', 'Gewinnfaktor auf R-Basis = Summe positiver R / Betrag der Summe negativer R. Bei fehlenden Verlusten ist der Quotient nicht definiert. Die letzte Spalte bezieht sich auf die bis zum jeweiligen Exit beobachtete Bewegung und den ursprünglichen Risiko-Nenner; sie sagt nichts über spätere Kurse nach diesem Exit.', '',
              '### Abhängigkeit von großen Gewinnern', '',
              '| Einstieg | Exit | Größter Fall | Fünf größte Gewinner / positive R-Summe | Ø R ohne diese fünf |',
              '|---|---|---:|---:|---:|']
    tails=tail_diagnostics(root)
    for f in FAMILIES:
        for m in MODELS:
            t=tails[f,m]
            lines.append(f"| {FAMILY[f]} | {MODEL[m]} | {fmt(t['bestR'],'R',True)} | {fmt(t['top5PositiveSharePct'],'%')} | {fmt(t['meanWithoutBest5'],'R',True)} |")
    lines += ['', 'Reine nachträgliche Abhängigkeitsdiagnose, keine Strategie, die große Gewinner vorab erkennen oder entfernen könnte. Sehr enge initiale Stops können große R-Werte erzeugen; sie entsprechen wegen Positions-/Kapitalgrenzen nicht denselben Depot-Prozenten. Kein zusätzlicher Beleg unabhängiger Stichproben.', '',
              '## Alle Kontaktklassen separat', '',
              '| Familie / Klasse | Kandidaten | Entries | Gemeinsam vollständig | Für direkten Vergleich unvollständig | Fester Stop Ø R | Ursprüngliche Safety Ø R | Aktuelle Safety Ø R |',
              '|---|---:|---:|---:|---:|---:|---:|---:|']
    for key,g in r['groups'].items():
        f,c=key.split(':');values=[fmt(g['models'][m]['sameEntries']['meanNetR'],'R',True) for m in MODELS]
        lines.append(f"| {FAMILY[f]} / {COHORT[c]} | {g['signals']} | {g['filled']} | {g['commonComplete']} | {g['incompleteForPaired']} | {' | '.join(values)} |")
    lines += ['', 'Modell-Entry bezeichnet den gespeicherten Einzelfall-Fill mit großem nominalem Prüfkapital. Er ist noch keine Annahme im realistisch begrenzten 2.000-USD-Depot. Ungültige Safety, Eröffnungsgap durch den Stop, fehlender Entrykurs oder andere nicht ausgeführte Entries zählen nicht als Verlusttrade.', '',
              '## Zeiträume für qualifizierte Einstiege', '',
              '| Zeitraum | Einstieg | Gemeinsam vollständig | Fester Stop Ø R | Ursprüngliche Safety Ø R | Aktuelle Safety Ø R |',
              '|---|---|---:|---:|---:|---:|']
    for w in r['windows']:
        for family in FAMILIES:
            g=w['groups'][family+':qualified'];values=[fmt(g['models'][m]['sameEntries']['meanNetR'],'R',True) for m in MODELS]
            lines.append(f"| {w['fold']['name']} | {FAMILY[family]} | {g['commonComplete']} | {' | '.join(values)} |")
    lines += ['', '## Sofortiger und verzögerter qualifizierter Ausbruch', '',
              '| Untertyp | Kandidaten | Gemeinsam vollständig | Fester Stop Ø R | Ursprüngliche Safety Ø R | Aktuelle Safety Ø R |',
              '|---|---:|---:|---:|---:|---:|']
    for sub,g in r['breakoutSubtypes'].items():
        values=[fmt(g['models'][m]['sameEntries']['meanNetR'],'R',True) for m in MODELS]
        lines.append(f"| {sub} | {g['signals']} | {g['commonComplete']} | {' | '.join(values)} |")
    lines += ['', '## Paarweise Unterschiede gegen den festen Stop', '',
              '| Einstieg | Alternative | Ø Unterschied R je Fall | Median Unterschied R | Alternative besser | Ø Unterschied, Aktien-/Zeitfenster gleich gewichtet | Bereich beim Weglassen je einer Aktie |',
              '|---|---|---:|---:|---:|---:|---|']
    for family in FAMILIES:
        for model,d in r['groups'][family+':qualified']['pairedAgainstFixed'].items():
            bounds=d['leaveOneSymbolOutDeltaRange'];interval='—' if bounds is None else fmt(bounds[0],'R',True)+' bis '+fmt(bounds[1],'R',True)
            lines.append(f"| {FAMILY[family]} | {MODEL[model]} | {fmt(d['meanDeltaR'],'R',True)} | {fmt(d['medianDeltaR'],'R',True)} | {fmt(d['betterPct'],'%')} | {fmt(d['equalStockWindowMeanDeltaR'],'R',True)} | {interval} |")
    lines += ['', 'Positive Unterschiede bevorzugen die Alternative, negative den festen Stop. Gleichgewichtung und Weglassen einzelner Aktien sind Abhängigkeitsdiagnosen, keine Konfidenzintervalle oder Signifikanztests. Marktbewegungen können viele Aktien gleichzeitig beeinflussen.', '',
              '## Endliches Depot – qualifizierte Einstiege', '',
              'Je Familie/Exit/Zeitfenster neues 2.000-USD-Depot, 1 % geplantes Risiko, 25 % Positionsgrenze, maximal drei Positionen, rechnerisch ganze Aktien. Alle passenden Einstiege einschließlich später unvollständiger Pfade. Bei gehaltenen Datenlücken stoppt das gesamte Buch. Verschiedene Exits ermöglichen andere Folgeentries; deshalb sind diese Bücher keine identischen Trade-Listen.', '',
              '| Zeitraum | Einstieg | Fester Stop netto | Ursprüngliche Safety netto | Aktuelle Safety netto | Angenommene Trades fest / ursprünglich / aktuell |',
              '|---|---|---:|---:|---:|---|']
    for w in r['windows']:
        for family in FAMILIES:
            books=w['portfolios'][family+':qualified'];vals=[books[m]['base'] for m in MODELS]
            returns=['unvollständig' if v['markedReturnPct'] is None else fmt(v['markedReturnPct'],'%',True) for v in vals]
            lines.append(f"| {w['fold']['name']} | {FAMILY[family]} | {' | '.join(returns)} | {' / '.join(str(v['accepted']) for v in vals)} |")
    lines += ['', '### Dasselbe mit doppeltem Spread/Slippage', '',
              '| Zeitraum | Einstieg | Fester Stop netto | Ursprüngliche Safety netto | Aktuelle Safety netto |',
              '|---|---|---:|---:|---:|']
    for w in r['windows']:
        for family in FAMILIES:
            books=w['portfolios'][family+':qualified'];vals=[books[m]['doubleCosts']['markedReturnPct'] for m in MODELS]
            returns=['unvollständig' if v is None else fmt(v,'%',True) for v in vals]
            lines.append(f"| {w['fold']['name']} | {FAMILY[family]} | {' | '.join(returns)} |")
    lines += ['', 'Keine Addition oder Verkettung der Tabellenrenditen. Das Entry-Jahr umfasst den deklarierten Nachbeobachtungszeitraum für spätere Exits; keine Annualisierung. Bestehende Grenzen der Splitbereinigung, historischen Ganzaktien-Bezahlbarkeit, fehlenden Dividenden/FX und des heutigen überlebenden Aktienuniversums bleiben bestehen.', '',
              '## Tages-SMA200 als bekannte Kontextinformation', '',
              '| Qualifizierter Einstieg | Bekannte Tageslage | Kandidaten | Gemeinsam vollständig | Fester Stop Ø R |',
              '|---|---|---:|---:|---:|']
    for family,buckets in r['smaContext'].items():
        for name,g in buckets.items():
            lines.append(f"| {FAMILY[family]} | {name} | {g['signals']} | {g['commonComplete']} | {fmt(g['models']['fixed']['sameEntries']['meanNetR'],'R',True)} |")
    lines += ['', 'above = Tageskurs mindestens SMA200; below = darunter; unknown = im damaligen Zeitpunkt nicht ausreichend bekannt. Dies ist keine nachträgliche Freigabe eines SMA-Filters; die Depotbücher oben bleiben ungefiltert.', '',
              '## Technische Nachweise und weitere Nutzung', '',
              f"{v['sourceCases']:,} Quellfälle, {v['csvPaths']:,} CSV-Pfade und sieben disjunkte Entry-Gruppen unabhängig auf Mitgliedschaft, identische Vergleichs-IDs, Mittelwert, Median und Trefferquote geprüft. {v['cashLedgers']} Kapitalbücher mit unabhängiger Kapitalrechnung; zusätzlich Bewertungen/Drawdowns im gespeicherten 5m-/Entscheidungsraster beim Erzeugen geprüft. Keine neuen Providerabrufe, keine Änderung der eingefrorenen Quellenauswahl.", '',
              'Die erste zusätzliche Auswertung deckte einen Randfall des unabhängigen Drawdown-Prüfers auf: zusätzliche Open-Exit-Zeitpunkte wurden bewertet, obwohl der Simulator zu abgeschlossenen 5m-Kerzen und Entry-Entscheidungszeiten abtastet. Der Prüfer rekonstruiert jetzt dasselbe Raster einschließlich abgelehnter Entryzeiten; ein Gap-Exit-Regressionstest sichert dies ab. Handelsengine, Einstiege und Exits wurden nicht geändert. Der unvollständige erste Vergleich bleibt erhalten; die fertige Auswertung hat einen neuen Plan.', '',
              'Private maschinenlesbare Ergebnisse: `comparison.json`, `entry-exit-cases.csv` (ein Fall je Exit und sämtliche Status), `entry-exit-portfolios.csv` (alle sieben Entry-Gruppen, Fenster, Exits und Kosten), einzelne Kapitalbücher und Prüfprotokolle. Der CSV-Pfad bezeichnet keinen empfohlenen Trade. Diese Runtime-Dateien gehören nicht nach GitHub.', '',
              '```text',
              'python tools/compare_entry_exits.py --source PRIVATER_ROBUSTHEITSVERSUCH --root NEUER_PRIVATER_VERGLEICH',
              'python tools/verify_entry_exit_comparison.py --root PRIVATER_VERGLEICH',
              'python tools/report_entry_exits.py --root PRIVATER_VERGLEICH --output ERGEBNISSE.md',
              '```', '',
              'Die Ergebnisse dürfen neue Prüfideen begründen. Für eine Regeländerung einen neuen Versuchsvertrag und eine zusätzliche unabhängige/prospektive Prüfung verwenden; keine Bestvariante auf diesen bekannten Daten als validierte Strategie ausgeben.']
    if assessment:
        note=Path(assessment).read_text(encoding='utf-8').strip()
        insertion=lines.index('## Welche Einstiege und Exits sind gemeint?')
        lines[insertion:insertion]=[note,'']
    return '\n'.join(lines)+'\n'


def export_portfolios(root):
    root=Path(root);r=read(root/'comparison.json');rows=[]
    for w in r['windows']:
        for group,models in w['portfolios'].items():
            for model,scenarios in models.items():
                for scenario,v in scenarios.items():
                    rows.append({'window':w['fold']['name'],'group':group,'model':model,'costs':scenario,
                        'netReturnPct':v['markedReturnPct'],'drawdownPct':v['max5mSampledDrawdownPct'],
                        'accepted':v['accepted'],'closed':v['closed'],'open':v['open'],'status':v['status'],
                        'eligible':v['eligibleSignals'],'positiveSymbols':v['positiveSymbols'],
                        'positiveConcentration':v['positiveProfitConcentration'],'halt':str(v['halt'])})
    with (root/'entry-exit-portfolios.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    with (root/'entry-exit-cases.csv').open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream);fields=reader.fieldnames;cases=list(reader)
    cases.sort(key=lambda c:(FAMILIES.index(c['family']),COHORTS.index(c['cohort']),c['signalET'],c['symbol'],c['caseId'],MODELS.index(c['exitModel'])))
    with (root/'entry-exit-cases-grouped.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(cases)


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--root',required=True);a.add_argument('--output',required=True);a.add_argument('--assessment',help='Separat verfasste Bewertung dieser konkreten Ergebnisse');args=a.parse_args()
    export_portfolios(args.root);Path(args.output).write_text(render(args.root,args.assessment),encoding='utf-8')
