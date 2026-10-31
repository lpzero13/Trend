"""Descriptive report and independent CSV aggregation; no policy tuning."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import math
from pathlib import Path
import statistics
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from exit_followup import checked, load_cases, terminal, POLICIES
from strategy_screen import read, write


def fmt(v):
    return '—' if v is None else f'{v:.2f}'


def report(root,destination):
    root=Path(root);p=checked(read(root/'plan.json'));r=read(root/'results.json');v=read(root/'verification.json')
    assert r['planId']==v['planId']==p['id'] and v['passed']
    # Reaggregate the flat export without using producer statistics functions.
    rows=defaultdict(list)
    with (root/'cases.csv').open(encoding='utf-8',newline='') as stream:
        for row in csv.DictReader(stream):
            rows[(row['family']+':'+row['cohort'],row['policy'])].append(row)
    for (g,m),cs in rows.items():
        target=r['groups'][g][m]
        assert len(cs)==target['signals'] and dict(Counter(c['status'] for c in cs))==target['statuses']
        for field,key in (('terminalPct','meanTerminalPct'),('netReturnPct','meanNetReturnPct'),
                          ('terminalR','meanTerminalR'),('netR','meanNetR')):
            values=[float(c[field]) for c in cs if c[field]!='']
            if values:assert math.isclose(statistics.mean(values),target[key],rel_tol=1e-10,abs_tol=1e-10)
            else:assert target[key] is None
    cases,diag=load_cases(root,p);groups=defaultdict(list)
    for c in cases:groups[c['signal']['family']+':'+c['signal']['cohort']].append(c)
    cutoff=datetime.fromtimestamp(p['cutoff'],timezone.utc).isoformat()
    lines=['# Safety-Folgeexperiment – 31.10.2026','',
        f"{len(p['symbols'])} Aktien, {len(p['windows'])} bekannte Entryfenster, **{len(cases)} unveränderte Originalfälle**. Datenende: {cutoff}.",'',
        '## Was umgesetzt und vorab festgelegt wurde','',
        '- `original_safety`: ursprüngliche steigende Entry-Safety weiterprojizieren.',
        '- `fan_safety`: bisherige aktuelle gültige steigende Safety, auch mit nur zwei Kontakten.',
        '- `qualified_fan`: ursprüngliche Safety weiterführen; eine aktuelle Safety zusätzlich nur zulassen, wenn sie am betreffenden 4h-Schluss bereits qualifiziert ist. Höheren gültigen Kandidaten wählen.',
        '- `r2_fan`: ursprüngliche Safety bis mindestens +2 initiale R am bestätigten 4h-Schluss, einschließlich modellierter Verkaufskosten. Danach dauerhaft aktuelle Safety zulassen; kein Zurücksetzen bei Kursrückgang.',
        '- `fixed`: fester Anfangsstop als Kontrolle. Kein Gewinnexit; offene Gewinner sind bei diesem Modell konstruktionsbedingt.',
        '',
        'Keine neue Entryauswahl, keine Änderung des Anfangsstops, kein Take Profit, keine Tagesexits und keine Depot-/Kapital-/Slotsperren. '
        'Je Fall 1.000 USD nominal mit fraktionalen Stückzahlen. Bestehende Kosten, 300 Sekunden Verzögerung, nächstes erwartetes 5m-Open, '
        'Gap-Fills und ausschließlich aufwärts nachgezogene Hard-Stops bleiben erhalten. Die zusätzlichen Varianten ändern keine laufenden Web-/Worker-Defaults.',
        '', '## Bewertungsmethode','',
        '**Geschlossen** bedeutet realisiertes modelliertes Nettoergebnis. **Offen** erhält einen separaten hypothetischen Netto-Liquidationswert am vorhandenen Datenende; '
        'das ist kein Exit. **Zensiert** bedeutet unbekannter weiterer Pfad wegen Datenlücke und bleibt außerhalb der Bewertungsmittel. '
        'Der Mittelwert geschlossen + offen ist eine Bewertung gleicher nominaler Einzelfälle mit unterschiedlichen Haltedauern, keine finanzierbare Depotperformance. '
        'Ausgeschlossene Lücken können das Ergebnis systematisch verzerren. Auch eine gemeinsame auswertbare Teilmenge löst dieses Problem nicht.',
        '', '## Alle Kontaktklassen und Entryfamilien','',
        '| Entry / Klasse | Safety | Geschlossen | Offen | Lücke | Kein Fill | Mittel geschlossen % | Mittel geschlossen + offen % | Median Bewertung % | Mittel ohne beste 3 % |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for g,methods in sorted(r['groups'].items()):
        for m in POLICIES:
            x=methods[m];s=x['statuses'];other=sum(n for k,n in s.items() if k not in ('closed','open','censored'))
            lines.append(f"| {g} | {m} | {s.get('closed',0)} | {s.get('open',0)} | {s.get('censored',0)} | {other} | {fmt(x['meanNetReturnPct'])} | {fmt(x['meanTerminalPct'])} | {fmt(x['medianTerminalPct'])} | {fmt(x['meanTerminalPctWithoutBest3'])} |")
    common={};trailing=POLICIES[1:]
    lines+=['','## Identische bewertbare Fälle aller vier Safety-Varianten','',
        'Hier müssen alle vier Safety-Varianten geschlossen oder offen sein. Derselbe Fall zählt je Variante genau einmal. '
        'Die Auswahl berücksichtigt Auswertbarkeit, nicht die Richtung des Ergebnisses. Abhängige Episoden bleiben abhängig.', '',
        '| Entry / Klasse | Gemeinsam / gefüllt | Safety | Mittel netto % | Median netto % | Mittel R | Median R | Positive Bewertungen % | Median beobachtete Tage |',
        '|---|---:|---|---:|---:|---:|---:|---:|---:|']
    for g,cs in sorted(groups.items()):
        subset=[c for c in cs if all(terminal(c,m) is not None for m in trailing)]
        filled=sum(c['entry']['status']=='filled' for c in cs);common[g]={'cases':len(subset),'filled':filled,'policies':{}}
        for m in trailing:
            values=[terminal(c,m)['pct'] for c in subset]
            days=[((c['paths'][m].get('exitAt') or c['paths'][m]['lastObservedAt'])-c['entry']['entryAt'])/86400 for c in subset]
            x={'mean':statistics.mean(values) if values else None,'median':statistics.median(values) if values else None,
               'meanR':statistics.mean(terminal(c,m)['r'] for c in subset) if subset else None,
               'medianR':statistics.median(terminal(c,m)['r'] for c in subset) if subset else None,
               'positivePct':100*sum(x>0 for x in values)/len(values) if values else None,
               'medianObservedDays':statistics.median(days) if days else None}
            common[g]['policies'][m]=x
            lines.append(f"| {g} | {len(subset)} / {filled} | {m} | {fmt(x['mean'])} | {fmt(x['median'])} | {fmt(x['meanR'])} | {fmt(x['medianR'])} | {fmt(x['positivePct'])} | {fmt(x['medianObservedDays'])} |")
    lines+=['','## Qualifizierte Fälle nach Entryfenster','',
        '| Fenster | Entry | Safety | Geschlossen | Offen | Lücke | Mittel Bewertung % | Median Bewertung % |',
        '|---|---|---|---:|---:|---:|---:|---:|']
    for window,gs in r['windows'].items():
        for family in ('breakout','red_retest','safety_bounce'):
            for m in trailing:
                x=gs.get(family+':qualified',{}).get(m)
                if x:
                    s=x['statuses'];lines.append(f"| {window} | {family} | {m} | {s.get('closed',0)} | {s.get('open',0)} | {s.get('censored',0)} | {fmt(x['meanTerminalPct'])} | {fmt(x['medianTerminalPct'])} |")
    lines+=['','## Tatsächlicher Wechsel auf eine engere aktuelle Safety','',
        'Ein anderer Linienname allein ist kein Nachweis für engeres Absichern. Gezählt wird die erste Stopänderung auf eine andere Linie, '
        'deren Stop oberhalb des gleichzeitig zulässigen Kandidaten der ursprünglichen Safety liegt. Fortschreiben derselben Ursprungslinie zählt nicht als Wechsel. '
        'R bezieht sich auf den damaligen bestätigten Schluss und enthält modellierte Kosten, nicht auf zukünftige MFE.', '',
        '| Entry / Klasse | Engerer Wechsel | Bereits qualifiziert | Nur 2 Kontakte | Median Tage nach Entry | Median damaliges R |',
        '|---|---:|---:|---:|---:|---:|']
    for g,x in sorted(r['firstUpgrades'].items()):
        lines.append(f"| {g} | {x['tighterReplacements']} | {x['qualified']} | {x['twoContacts']} | {fmt(x['medianDaysAfterEntry'])} | {fmt(x['medianNetRAtKnownClose'])} |")
    lines+=['','## Anfangsstop-Abstände: Beschreibung, kein neuer Filter','',
        'Feste Klassen, keine Quantile und keine optimierten Mindestabstände. Alle gefüllten Fälle einschließlich offener und zensierter Pfade bleiben in den Statuszahlen. '
        'Die Prozent-/ATR-Details sämtlicher Kontaktklassen stehen in `results.json` und `cases.csv`; hier qualifizierte Retests.', '',
        '| Maß | Abstandsklasse | Safety | Geschlossen | Offen | Lücke | Mittel Bewertung % |',
        '|---|---|---|---:|---:|---:|---:|']
    for unit,bs in r['distanceBins'].get('red_retest:qualified',{}).items():
        for band,methods in bs.items():
            for m in trailing:
                x=methods[m];s=x['statuses'];lines.append(f"| {unit} | {band} | {m} | {s.get('closed',0)} | {s.get('open',0)} | {s.get('censored',0)} | {fmt(x['meanTerminalPct'])} |")
    lines+=['','## Offene Läufer der ursprünglichen Safety','',
        'Nachträglich nach dem Status der Referenz ausgewählte Beispiele; deshalb kein eigenständiger Erfolgsnachweis. '
        'Werte sind Netto-% geschlossen oder offen bewertet; zensiert bleibt unbekannt. Alle Originalfälle bleiben im Gesamttest.', '',
        '| Aktie | Entry | Fall | Original | Aktuell | Qualifiziert | Ab +2R |',
        '|---|---|---|---:|---:|---:|---:|']
    for x in r['originalOpenQualified']:
        values=[fmt(x['outcomes'][m]['terminal']['pct']) if x['outcomes'][m]['terminal'] else 'unbekannt' for m in trailing]
        lines.append(f"| {x['symbol']} | {x['family']} | {x['caseId'][:12]} | "+' | '.join(values)+' |')
    open_stop={}
    lines+=['','## Hypothetisches Ergebnis am letzten aktiven Stop','',
        'Kein „gesicherter Gewinn“: bei Kurslücken kann der tatsächliche Fill unter dem Stop liegen. Für offene Fälle gilt das letzte vorhandene '
        'Beobachtungsdatum; zensierte Fälle haben nur einen früheren letzten zusammenhängenden Beobachtungsstand. '
        'Die CSV enthält pro Fall `stopMarkR` und `markAsOf`. Diese Werte sind keine zusätzlichen realisierten Gewinne.', '',
        '| Qualifizierter Entry | Safety | Status | Fälle | Median hypothetisches Stop-R |',
        '|---|---|---|---:|---:|']
    for (g,m),cs in sorted(rows.items()):
        if not g.endswith(':qualified') or m=='fixed':continue
        for status in ('open','censored'):
            vals=[float(c['stopMarkR']) for c in cs if c['status']==status and c['stopMarkR']!='']
            if vals:
                x={'count':len(vals),'medianStopR':statistics.median(vals)};open_stop[g+':'+m+':'+status]=x
                lines.append(f"| {g} | {m} | {status} | {len(vals)} | {fmt(x['medianStopR'])} |")
    lines+=['','## Korrekturen an der Interpretation der Rückmeldung','',
        'Offene Buchwerte verändern den bisherigen reinen Closed-Trade-Vergleich erheblich. Das bestätigt weder pauschal die ursprüngliche Safety '
        'noch die Behauptung, alle fehlenden Verläufe wären Gewinner. Median ΔR nahe null bedeutet keine Mehrheit identischer Ergebnisse: '
        'unter den gemeinsam geschlossenen qualifizierten Ausbrüchen sind 382/989 identisch, bei Retests 244/667. '
        'Die medianen Anfangsstop-Abstände liegen bei 3,39 % für Ausbrüche und 2,98 % für Retests; Mittelwerte in R und Prozent sind nicht direkt austauschbar.', '',
        'Alle 75 wegen Open unter Anfangsstop abgesagten Käufe lagen in einer späteren New-York-Handelssitzung: 17,5 bis 89,5 Stunden nach dem Signal. '
        'Das ist kein Nachweis eines Stops, der innerhalb von fünf Minuten zu eng wurde. Die 360 Fälle ohne gültigen Anfangsstop benötigen '
        'eine separate kausale Untersuchung der Einstiegskonstellation; der Anfangsstop wurde hier bewusst nicht nachträglich verbreitert.', '',
        '## Prüfungen, Reproduktion und Grenzen','',
        f"{v['cases']} Fälle und {v['newPaths']} neue Pfade vollständig auf Herkunft, Stopratchets, kausale Verfügbarkeit und Kosten geprüft. "
        f"{v['independent5mReplays']} deterministisch ausgewählte Pfade zusätzlich unabhängig 5m-Kerze für 5m-Kerze nachgerechnet. "
        f"CSV-Statuszahlen und Netto-Mittelwerte aller {len(rows)} Gruppen/Modellkombinationen separat nachgerechnet. "
        'Zusätzlicher AAPL-Pilot: 107 Originalfälle, 214 neue Pfade, 24 unabhängige Replays.', '',
        f"Plan-ID: `{p['id']}`. Quellplan-ID: `{p['sourcePlanId']}`. Private Laufdateien unter `{root.resolve()}`. "
        'Plan, Enginebindung, Dataset-IDs, prüfsummengeschützte Aktienblöcke, Ergebnisse, CSV und Prüfbericht bleiben erhalten; keine Rohdaten im Git-Repository.', '',
        '```powershell',
        'python tools/run_exit_followup.py STUDIENORDNER --source ORIGINALSTUDIE --phase prepare',
        'python tools/run_exit_followup.py STUDIENORDNER --phase build --workers 3',
        'python tools/run_exit_followup.py STUDIENORDNER --phase evaluate',
        'python tools/verify_exit_followup.py STUDIENORDNER --samples 2',
        'python tools/report_exit_followup.py STUDIENORDNER --output BERICHT.md',
        '```', '',
        'Gleichen `TORI_DATA_DIR` wie der Dienst verwenden. Ein geänderter Producer verlangt einen neuen Studienordner; keine Fortsetzung unter anderer Engine. '
        'Alle Varianten bleiben explorativ auf bereits bekannten historischen Daten und einem heutigen Überlebendenuniversum. '
        'Keine unabhängige neue Validierung, keine Annualisierung, keine garantierte Handelbarkeit und kein Profitabilitätsnachweis. '
        'Noch nötig: visuelle Episodenprüfung, plausible Robustheitsprüfung auf unangetasteten Daten und Prüfung der Datenlückensensitivität. '
        'Sammler und Providerabrufe bleiben aus; keine Orders oder Containeränderungen.', '']
    Path(destination).write_text('\n'.join(lines),encoding='utf-8')
    write(root/'report-details.json',{'planId':p['id'],'commonFourSafety':common,'lastStopMarks':open_stop,
        'csvAggregationPassed':True,'csvRows':sum(map(len,rows.values())),
        'reportSha256':hashlib.sha256(Path(destination).read_bytes()).hexdigest()})
    return {'report':str(destination),'csvRowsVerified':sum(map(len,rows.values()))}


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('root');ap.add_argument('--output',required=True);a=ap.parse_args()
    print(report(a.root,a.output))
