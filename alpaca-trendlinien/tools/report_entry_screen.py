"""Report the predeclared screen, including negative results and missing context."""
import argparse
from collections import Counter,defaultdict
import hashlib
from pathlib import Path
import statistics
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from entry_screen import PROFILES,RULES,DEFAULT
from event_case_study import load_block
from exit_followup import load_followup,terminal
from strategy_screen import read,write
from tools.run_entry_screen import checked,POLICIES


def fmt(v):return '—' if v is None else f'{v:.2f}'


def report(root,destination):
    root=Path(root);p=checked(read(root/'plan.json'));r=read(root/'results.json');v=read(root/'verification.json')
    assert r['planId']==v['planId']==p['id'] and v['passed']
    lines=['# Strukturfilter für Signalkandidaten – 31.10.2026','',
        '**Ergebnis: Die Vorschläge sind überprüfbare Hypothesen, kein bewiesener Filter für gute Trades. Die strenge Kombination liefert 206 Fälle, '
        'aber negative historische Mittel unter allen vier Stopführungen. Sie wird nicht als erfolgreiche Strategie übernommen.**','',
        f"{len(p['symbols'])} Aktien, {r['cases']} unveränderte Rohfälle, vier bekannte Entryfenster. Keine neuen Providerabrufe, Entries, Exits, Zeitlimits oder Depotlimits. "
        'Die vorhandenen eingefrorenen Exitpfade werden nach der Auswahl neu ausgewertet. Alle Profile und Schwellen wurden vor dem Lesen ihrer Ergebnisse gespeichert.', '',
        '**Grenze dieses Versuchs:** Er filtert die ersten bereits archivierten Ereignisse pro Episode/Familie. Er sucht keine späteren Ersatzentries, '
        'wenn das erste Rohsignal den neuen Filter verfehlt. Ein später erstmals qualifiziertes oder erst nach einem Kontextwechsel geeignetes '
        'Signal derselben Episode kann im Original bereits als Wiederholung unterdrückt worden sein. Dafür braucht es einen eigenen kausalen '
        'Scannerlauf mit Beobachtungszustand und erstmaliger Profilfreigabe, keine nachträgliche Auswahl eines späteren Gewinners.', '',
        '## Definitionen und wichtige Abweichungen von der Rückmeldung','',
        'Die Auswahl verwendet ausschließlich Geometrie und Kurse am Signalschluss. Stopabstände beziehen sich auf den rohen Signalschluss und den bereits feststehenden Anfangsstop. '
        'Der tatsächliche Kaufkurs der nächsten Kerze darf einen historischen Signalmarker nicht rückwirkend zulassen oder entfernen. '
        'Die alten Tabellen verwenden dagegen Abstände vom späteren modellierten Fill; dadurch sind die neuen Gruppen nicht exakt dieselben.', '',
        'SMA200 bedeutet: Durchschnitt der letzten 200 vollständig geschlossenen regulären Tageskerzen. Für den Trendvergleich gilt der letzte abgeschlossene Tages-Schluss, '
        'nicht der spätere Schluss des noch laufenden Signaltages. Eine Lücke innerhalb dieser 200 Sitzungen oder ein fehlender letzter erwarteter Tag macht den Kontext unbekannt. '
        'Erforderliche unbekannte Merkmale führen zum Ausschluss, nicht zu einem stillen Bestehen.', '',
        'Linienreife ist die bereits bestätigte Kontaktspanne, keine nur durch Warten verlängerte Ankerhistorie. '
        'Verengung misst die positive geometrische Breite zwischen der fallenden roten und steigenden grünen Linie am Signal relativ zum gemeinsamen Ankerbeginn. '
        'Diese Geometrie ist am Signal bekannt; sie behauptet nicht, dass dieselben später bestätigten Linien bereits am historischen Ankerbeginn handelbar waren. '
        'Ein bereits gekreuztes oder nicht positiv messbares Dreieck wird nicht zugelassen.', '',
        'Die Ausgangsgruppe `qualified` verlangt einen qualifizierten Ausbruch/Retest und bekannte Signal-/Safety-Geometrie. '
        'Von den zuvor genannten 1.886 roten qualifizierten Rohfällen fehlt 96 die notwendige Safety-Geometrie; diese waren auch vorher nicht gefüllt. '
        'Damit verbleiben 1.790 zeichnungsfähige Fälle, darunter 1.778 tatsächliche Fills und zwölf später abgesagte Entries.', '',
        '## Vorab festgelegte Profile','',
        '| Profil | Kriterien | Fälle | Gefüllt | Abgesagt / nicht gefüllt |',
        '|---|---|---:|---:|---:|']
    for name,profile in PROFILES.items():
        g=r['profiles'][name]['groups']['all'];st=g['statuses']
        lines.append(f"| {name} | "+'; '.join(RULES[k] for k in profile['rules'])+f" | {g['signals']} | {st.get('filled',0)} | {g['signals']-st.get('filled',0)} |")
    lines+=['','`all` ist ausschließlich die Vergleichsgruppe. `balanced` wurde vor den Ergebnissen als Standard für eine reduzierte Sichtprüfungs-Playlist festgelegt; '
        'es ist kein nachträglich ausgewählter historischer Gewinner. Die Kriterien bleiben im Chart ausdrücklich experimentell.', '',
        '## Fairer Modellvergleich innerhalb der ausgewählten Gruppe','',
        'Für jede Zeile werden nur Fälle verwendet, die unter allen vier Safety-Modellen geschlossen oder am Datenende offen bewertbar sind. '
        'Geschlossene Nettoergebnisse und offene hypothetische Netto-Liquidationswerte sind für diesen Bewertungsvergleich zusammengeführt. '
        'Datenbedingt unbekannte weitere Verläufe bleiben ausgeschlossen. Das ist keine Depotperformance und kein Nachweis gleicher Kapitalbindung. '
        'Die Auswahl verschiedener Profile erzeugt unterschiedliche Fallmengen; deren Mittelwerte beweisen keine kausale Verbesserung.', '',
        '| Profil | Entry | Gemeinsam bewertbar | Safety | Mittel netto % | Median netto % | Mittel R | Positive Bewertungen % |',
        '|---|---|---:|---|---:|---:|---:|---:|']
    for name in PROFILES:
        for family in ('breakout','red_retest'):
            g=r['profiles'][name]['groups'][family]
            for m,x in g['common'].items():
                lines.append(f"| {name} | {family} | {g['commonCount']} | {m} | {fmt(x['meanTerminalPct'])} | {fmt(x['medianTerminalPct'])} | {fmt(x['meanTerminalR'])} | {fmt(x['positiveTerminalPct'])} |")
    lines+=['','## Gleiche Bewertung in den einzelnen Entryfenstern','',
        'Gezeigt werden Referenz, reduzierte Playlist und strenge Kombination. Hier sind Auswertbarkeit und Status je Modell separat; '
        'verschiedene Fenster haben unterschiedliche mögliche Nachbeobachtungsdauer und sind bereits bekannte Daten.', '',
        '| Profil | Fenster | Entry | Safety | Signale | Geschlossen | Offen | Lücke | Mittel Bewertung % | Median Bewertung % |',
        '|---|---|---|---|---:|---:|---:|---:|---:|---:|']
    for name in ('qualified','balanced','strict'):
        for family in ('breakout','red_retest'):
            for window,methods in r['profiles'][name]['groups'][family]['windows'].items():
                for m,x in methods.items():
                    st=x['statuses']
                    lines.append(f"| {name} | {window} | {family} | {m} | {x['signals']} | {st.get('closed',0)} | {st.get('open',0)} | {st.get('censored',0)} | {fmt(x['meanTerminalPct'])} | {fmt(x['medianTerminalPct'])} |")
    # A matched known-context control avoids blaming the SMA rule for missing data.
    base=read(Path(p['baseRoot'])/'plan.json');follow=read(Path(p['sourceRoot'])/'plan.json');contexts=defaultdict(list);counts=Counter()
    for symbol in p['symbols']:
        b=load_block(p['baseRoot'],base,symbol);f=load_followup(p['sourceRoot'],follow,symbol)
        screen=read(root/'stocks'/(symbol+'.json.gz'))
        for c,x in zip(b['cases'],screen['cases']):
            if not x['selection']['qualified']['accepted']:continue
            state=x['checks']['trend'];label='unbekannt' if state is None else 'über SMA200' if state else 'nicht über SMA200'
            counts[label]+=1
            paths={**c['paths'],**f['newPaths'][c['id']]};case={**c,'paths':paths}
            if all(terminal(case,m) is not None for m in POLICIES):contexts[(label,c['signal']['family'])].append(case)
    lines+=['','## SMA200: bekannte Gegenprobe und unbekannte Daten trennen','',
        f"Unter den 1.790 zeichnungsfähigen qualifizierten Fällen: {counts['über SMA200']} über SMA200, "
        f"{counts['nicht über SMA200']} nicht darüber und {counts['unbekannt']} mit unbekanntem SMA-Kontext. "
        'Ein Ausschluss unbekannter Daten ist keine bestätigte Trendregel. Folgende Werte nutzen wiederum gemeinsame bewertbare Fälle aller vier Modelle.', '',
        '| Tageskontext | Entry | Gemeinsam | Original % | Aktuell % | Qualifizierter Fan % | Ab +2R % |',
        '|---|---|---:|---:|---:|---:|---:|']
    controls={}
    for (label,family),cs in sorted(contexts.items()):
        means={m:statistics.mean(terminal(c,m)['pct'] for c in cs) for m in POLICIES}
        controls[label+':'+family]={'cases':len(cs),'means':means}
        lines.append(f"| {label} | {family} | {len(cs)} | "+' | '.join(fmt(means[m]) for m in POLICIES)+' |')
    lines+=['','## Welche Aussagen der Rückmeldung tragen nicht?','',
        '- „Ohne Overfitting“ ist unbelegt. Plausible Strukturregeln und verbreitete Indikatoren können ebenfalls auf bekannte Ergebnisse angepasst werden. Diese Fenster waren bereits mehrfach ausgewertet.',
        '- ATR- und Prozentklassen sind nicht austauschbar. 1 ATR entspricht je Aktie, Zeitpunkt und Volatilität einem anderen Prozentabstand. Die gemeinsame Bedingung wurde deshalb ausdrücklich separat getestet.',
        '- Die „ATR-Todeszone“ ist keine bestätigte Marktursache. Im alten Retest-Tableau stehen in 0,5–1 ATR 67 gefüllte Fälle (65 geschlossen, zwei zensiert); 1–2 ATR enthält 222 und über 2 ATR 394. Die dort genannten 65/218/391 sind keine konsistenten Gesamtfallzahlen.',
        '- ATR ist ein Durchschnitt wahrer Handelsspannen, keine garantierte Mindestschwankung einer einzelnen nächsten Kerze. Ein breiterer Stop macht aus einem ungeeigneten Einstieg nicht automatisch einen guten.',
        '- Beide Linien mit hoher Kontaktqualität zu verlangen ist eine testbare Zusatzregel. Die Gruppe `both_qualified` ist hier schwächer als die einfache Ausgangsgruppe, nicht automatisch besser.',
        '- 206 strenge Fälle erfüllen ungefähr die erhoffte Größenordnung, liefern aber negative Mittel unter sämtlichen vier Stops. Eine kleine „Lehrbuch“-Liste ist kein Erfolgsnachweis.', '',
        '## Umsetzung im Chart und Replay','',
        'Unter **Historische Einstiege → Signalauswahl** stehen dieselben neun Profile zur Verfügung. Chartstandard ist die einfache qualifizierte Ausgangsgruppe. '
        'Die vorab festgelegte reduzierte Struktur-/Abstands-/Trend-Playlist bleibt als experimentelles Profil und als private Sichtprüfungsliste verfügbar; '
        'sie wurde durch ihr Ergebnis nicht zur empfohlenen Strategie erklärt. '
        'Es werden nur die zum Chartzeitpunkt bereits bekannten passenden Signalpunkte gezeigt. Die Statuszeile nennt die durch das Profil ausgeschlossene Anzahl. '
        'Die ausgewählte Originalgeometrie bleibt fixiert; Replay, einzelne Kerzenschritte und persönliche Bewertungen bleiben erhalten. '
        'Ein Profilwechsel entfernt ausgeschlossene Marker und ausgewählte Linien. „Alle Rohsignale · Vergleich“ macht Ausschlüsse kontrollierbar. '
        'Im Detail werden Signalabstand, Tageskontext und Profil erläutert; keine späteren Gewinne oder zukünftigen Fills werden vorweggenommen. '
        'Tori-Analyse und historische Signalebene starten weiterhin optional, persönliche Zeichnungen bleiben separat.', '',
        'Keine neue Datenbank, Migration oder Duplizierung der ursprünglichen Fälle. Ein begrenzter Speicher-Cache je unveränderlicher Entryversion spart wiederholtes Lesen. '
        'Die Filter verwenden denselben Code wie das Offline-Experiment. Die erste Öffnung einer noch nicht geprüften Aktie kann einmalig Datasetprüfung und Featureaufbau benötigen; '
        'keine erneute Linienfindung oder Providerabfrage bei einem Profilwechsel.', '',
        '## Technische Nachweise und Reproduktion','',
        f"{v['cases']} Fälle, {v['profiles']} vorab definierte Profile; Mitgliedschaften und aggregierte Mittelwerte separat geprüft. "
        f"{v['independentSmaAndPrefixChecks']} Stichproben mit unabhängig berechnetem Tages-SMA und abgeschnittener Zukunft bestätigen den Signalzeitpunkt-Vertrag. "
        'Quellindizes aller Fälle stimmen mit der eingefrorenen ursprünglichen 4h-Timeline überein. Die Sichtprüfungs-Playlist enthält keine Exit-/Erfolgsdaten.', '',
        f"Plan-ID: `{p['id']}`. Private Laufdateien: `{root.resolve()}`. Plan/Code/Datasetbindung, atomare Aktienblöcke und Schreiblock. "
        'Neue Engine erfordert einen neuen Studienordner; gleichen `TORI_DATA_DIR` wie der Dienst verwenden. Laufdaten und Datasets nicht veröffentlichen.', '',
        '```powershell',
        'python tools/run_entry_screen.py STUDIE --source SAFETY-FOLGESTUDIE --phase prepare',
        'python tools/run_entry_screen.py STUDIE --phase build --workers 3',
        'python tools/run_entry_screen.py STUDIE --phase evaluate',
        'python tools/verify_entry_screen.py STUDIE --workers 3',
        'python tools/report_entry_screen.py STUDIE --output BERICHT.md',
        '```','',
        '## Empfehlung','',
        'Die einfache qualifizierte Ausgangsgruppe als Forschungsreferenz behalten. Stopabstand ist eine nützliche Beschreibung, aber hier kein eindeutiger pauschaler Mindestfilter. '
        'SMA200, Linienalter und Verengung nicht gemeinsam zum verpflichtenden Strategie-Gate erklären. '
        'Zuerst Ausbruch und Retest getrennt anhand eingefrorener Beispiele blind prüfen, einschließlich ausgeschlossener Fälle. '
        'Danach wenige fachlich begründete Regeln auf tatsächlich unangetasteten Daten prüfen, ohne Schwellen an diesen Ergebnissen weiter zu optimieren. '
        'Das Ziel ist eine kleinere brauchbare Beobachtungsliste mit vertretbaren Verlusten und ausreichenden positiven Beiträgen, keine rückwirkend gewinnreine Liste. '
        'Aktuelles Überlebendenuniversum, abhängige Episoden, informative Datenlücken, Kostenannahmen und ungleiche Haltedauer bleiben Grenzen. '
        'Keine automatisch als profitabel freigegebene Strategie, keine Orders und keine Containeränderung.', '']
    Path(destination).write_text('\n'.join(lines),encoding='utf-8')
    write(root/'report-details.json',{'planId':p['id'],'smaControl':controls,'smaSignalCounts':dict(counts),
        'reportSha256':hashlib.sha256(Path(destination).read_bytes()).hexdigest()})
    return {'report':str(destination),'cases':r['cases']}


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('root');ap.add_argument('--output',required=True);a=ap.parse_args()
    print(report(a.root,a.output))
