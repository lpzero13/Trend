"""Publishable aggregate Markdown from a private, verified offline radar study."""
import argparse
from pathlib import Path
import sys
import statistics

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from early_warning_study import checked, load_block
from fan_study import timestamp, schedule
from datetime import datetime
from models import NY
from strategy_screen import read


def number(value, places=1):
    return '–' if value is None else f'{value:.{places}f}'


def report(root):
    root = Path(root); plan = checked(read(root/'plan.json')); result = read(root/'results.json')
    receipt = read(root/'verification.json')
    assert receipt['planId'] == plan['id'] and result['planId'] == plan['id']
    names = {'breakout': 'Ausbruch', 'red_retest': 'Roter Retest', 'safety_bounce': 'Safety-Bounce'}
    out = ['# Historische Vorwarnstudie – 01.11.2026', '',
        f"{result['symbols']} vorhandene echte SIP/split-Aktien, {result['sessions']} XNYS-Handelstage in vier bereits bekannten Forschungsfenstern.",
        'Fenster: '+', '.join(w['name'] for w in plan['windows'])+'.',
        'Keine Providerabrufe, Orders, P/L-Studie, neue Holdout-Auswahl oder laufenden Nachrichten.', '',
        'Die gemeinsame kausale Master-/Pilot-Entrylogik läuft erneut über die Quellen. Vorwarn-Episoden entstehen bereits bei Kandidatenerkennung; diese neue Gruppierung ist nicht die alte 1.790er-Fallauswahl. Die Entryzahlen sind je Familie/Policy episodenweise deduplizierte Bestätigungen mit gültiger Anfangsabsicherung, keine behaupteten Fills.',
        'Je Policy dieselbe Referenzmenge. Verschiedene Policies teilen Fälle und dürfen nicht als unabhängige Stichprobe addiert werden. Ohne ausreichenden Vorlauf wird das jeweilige Aktienfenster ausgeschlossen.', '',
        '## Abstandswarnungen', '',
        '| Familie | ATR-Schwelle | Entries | Vorwarnungen | Entries vorher erfasst % | Davon 1–2 Sitzungstage vor Entry: Anteil aller Entries % | Median Vorlauf / Kerzen | Verpufft unter aufgelösten Warnungen % | Unentschieden | Meldungen/Tag | Spitze/Tag |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for g in result['groups']:
        if not g['policy'].startswith('distance:'): continue
        out.append(f"| {names[g['family']]} | {g['policy'].split(':')[1]} | {g['entries']} | {g['warnings']} | {number(g['recallPct'])} | {number(g['early1to2SessionRecallPct'])} | {number(g['medianLeadBars'])} | {number(g['fizzlePctAmongResolved'])} | {g['censored']} | {number(g['messagesPerSession'],2)} | {g['peakMessagesPerSession']} |")
    out += ['', 'Vorlaufmedian nur unter tatsächlich vorher gewarnten Entries. 1–2 Sitzungstage bezeichnet den Abstand der Börsen-Sitzungsdaten, keine vollen 24–48 Stunden; Kerzen werden separat gemessen. Eine Warnung auf der Entrykerze zählt nicht als rechtzeitig.',
        'Verpufft bedeutet: Beobachtung wurde vor einem passenden gültigen Signal aufgelöst. Ein Kursverlust oder tatsächlicher Stop-Fill ist damit nicht nachgewiesen. Spätere Signale nach bereits geschlossener Beobachtung werden nicht als erfolgreiche Vorwarnung gutgeschrieben.', '',
        '## Zusätzliche Merkmale als Pflichtbedingungen, jeweils 1 ATR', '',
        '| Familie | Variante | Vorwarnungen | Erfasste Entries % | Bestätigung unter allen Warnungen % | Meldungen/Tag |',
        '|---|---|---:|---:|---:|---:|']
    for g in result['groups']:
        if not g['policy'].endswith(':1'): continue
        out.append(f"| {names[g['family']]} | {g['policy'].split(':')[0]} | {g['warnings']} | {number(g['recallPct'])} | {number(g['confirmedWarningPct'])} | {number(g['messagesPerSession'],2)} |")
    out += ['', '`distance`: nur Abstand; `active`: zusätzlich aktive Annäherung; `compression`: zusätzlich Verengung; `combined`: beides. Die Gruppenmitgliedschaften unterscheiden sich; bessere Anteile sind kein kausaler Wirkungsnachweis.', '',
        '## Kontaktklassen getrennt, Abstand 1 ATR', '',
        '| Familie | Qualität BEI Vorwarnung | Warnungen | Später bestätigt | Verpufft | Unentschieden |',
        '|---|---|---:|---:|---:|---:|']
    for g in result['groups']:
        if g['policy'] != 'distance:1': continue
        for cohort, v in sorted(g['warningResultsByCohort'].items()):
            out.append(f"| {names[g['family']]} | {cohort} | {v['warnings']} | {v['confirmed']} | {v['fizzled']} | {v['censored']} |")
    out += ['', '| Familie | Später qualifizierte Entries | Davon vorher gewarnt | Davon bei Warnung erst zwei Kontakte |', '|---|---:|---:|---:|']
    for g in result['groups']:
        if g['policy'] != 'distance:1': continue
        q = g['entryCoverageByCohort'].get('qualified', {})
        out.append(f"| {names[g['family']]} | {q.get('entries',0)} | {q.get('covered',0)} | {q.get('warningWasTwo',0)} |")
    out += ['', 'Die Qualifikation am späteren Signal darf eine frühere Zweikontakt-Warnung nicht rückwirkend aufwerten.', '',
        '## Originalwarnlinie und spätere Signallinie', '',
        '| Familie, 1 ATR | Auf Episodenebene erfasst | Davon identische technische Linie | Andere Linie derselben Herkunft |',
        '|---|---:|---:|---:|']
    for g in result['groups']:
        if g['policy'] == 'distance:1':
            out.append(f"| {names[g['family']]} | {g['coveredEntries']} | {g['sameLineConfirmations']} | {g['coveredEntries']-g['sameLineConfirmations']} |")
    out += ['', 'Die Haupterfassungsquote bezieht sich auf Episode/Familie. Ein verwandter späterer Kandidat desselben Fächers ist nicht automatisch genau die im ersten Warnsnapshot gespeicherte Linie. Diese Fälle sind sichtbar getrennt.', '',
        '## Berührung, roher Bruch und Bestätigung unterscheiden', '',
        '| Familie, 1 ATR | Median bis rohe Rot-Kreuzung / Kerzen | Median bis erste Berührung / Kerzen | Vor erster Berührung gewarnte bestätigte Fälle |',
        '|---|---:|---:|---:|']
    for g in result['groups']:
        if g['policy'] == 'distance:1':
            out.append(f"| {names[g['family']]} | {number(g['medianRawBreakLeadBars'])} | {number(g['medianFirstTouchLeadBars'])} | {g['coveredBeforeFirstTouch']} |")
    out += ['', 'Negative Berührungs-Vorlaufwerte bedeuten: Die erste Berührung war schon vor der Warnung bekannt. Eine Warnung vor der späteren Bestätigung ist dann keine Warnung vor dem ersten Kontakt. Ein roter Retest beobachtet die Originalbruchlinie; die grüne Safety bleibt eine eigene Familie.', '',
        '## Ein bis zwei Sitzungstage vor dem rohen Rot-Bruch', '',
        '| Policy | Ausbruchs-Entryreferenz | Bei aktivem Watch 1–2 Sitzungstage vor rohem Bruch gewarnt | Anteil aller Ausbruchs-Entries % | Median reale Stunden vor rohem Bruch |',
        '|---|---:|---:|---:|---:|']
    raw_days = {g['policy']: 0 for g in result['groups']}
    raw_hours = {g['policy']: [] for g in result['groups']}
    window_clocks = []
    for window in plan['windows']:
        a, z = timestamp(window['start']), timestamp(window['end'], upper=True)
        dates = sorted({datetime.fromtimestamp(t, NY).date() for t, _ in schedule(a, z, '4h')})
        window_clocks.append((window['name'], a, z, {d: i for i, d in enumerate(dates)}))
    for symbol in plan['symbols']:
        block = load_block(root, plan, symbol)
        for r in block['records']:
            if r['family'] != 'breakout' or not r['entry'] or not r['entry']['validRisk'] or not r['entry']['activeAtSignal']: continue
            warning = next((w for w in r['warnings'] if w['stage'] == 2), None)
            if warning is None or r['rawBreakAt'] is None or warning['at'] >= r['rawBreakAt']: continue
            for name, a, z, dates in window_clocks:
                if not block['eligibility'][name]: continue
                if not a <= warning['at'] < r['rawBreakAt'] <= r['entry']['at'] <= z: continue
                raw_hours[r['policy']].append((r['rawBreakAt']-warning['at'])/3600)
                first_day = dates[datetime.fromtimestamp(warning['at'], NY).date()]
                raw_day = dates[datetime.fromtimestamp(r['rawBreakAt'], NY).date()]
                if 1 <= raw_day-first_day <= 2: raw_days[r['policy']] += 1
    for g in result['groups']:
        if g['family'] != 'breakout': continue
        count = raw_days[g['policy']]
        hours = raw_hours[g['policy']]
        out.append(f"| {g['policy']} | {g['entries']} | {count} | {number(100*count/g['entries'] if g['entries'] else None)} | {number(statistics.median(hours) if hours else None)} |")
    out += ['', 'Dieser strengere Vorlauf endet bereits bei der ersten beobachteten Rot-Kreuzung der Episode. Die Clean-Close-Entrybestätigung kann später liegen; ihre längere Vorlaufzeit darf nicht als dieselbe Frühwarnzeit ausgegeben werden.', '',
        '## Spätere Einstiege nach bereits geschlossener Beobachtung', '',
        '| Familie, Abstand 1 ATR | Entryreferenz | Vorwarnung vorhanden, aber Watch vor Entry schon beendet |', '|---|---:|---:|']
    for g in result['groups']:
        if g['policy'] == 'distance:1':
            out.append(f"| {names[g['family']]} | {g['entries']} | {g['afterClosedWatchEntries']} |")
    out += ['', 'Hier besteht ein wichtiger Forschungsansatz für begrenzte erneute Freigaben nach einem tatsächlich neuen Aufbau. Ein späterer Entry beweist nicht rückwirkend, dass die ursprüngliche Warngeometrie intakt geblieben war. Diese Fälle sind daher weiterhin nicht als erfolgreiche aktive Vorwarnungen gezählt.', '',
        '## Gesamte hypothetische Nachrichtenlast', '',
        '| Policy | Meldungen/Tag, alle Familien | Spitzentag |', '|---|---:|---:|']
    policies = sorted({g['policy'] for g in result['groups']})
    for policy in policies:
        groups = [g for g in result['groups'] if g['policy'] == policy]
        days = {d for g in groups for d in g['daily']}
        peak = max((sum(g['daily'].get(d, 0) for g in groups) for d in days), default=0)
        out.append(f"| {policy} | {sum(g['messagesPerSession'] for g in groups):.2f} | {peak} |")
    out += ['', 'Zeitgleiche Stufe 2 und 3 derselben Episode/Familie sind ein Briefing. Wiederholte Tagesansichten erzeugen keine weiteren Warnungen. Die genannten Häufigkeiten sind historische Lasten des jeweiligen Universums, kein erzwungenes Tageskontingent.', '',
        '## Technische Prüfung und Grenzen', '',
        f"Unabhängiger Nachrechner: {receipt['warningSnapshotsChecked']:,} gespeicherte Warnzustände, {receipt['symbols']} Aktien und alle {receipt['allGroupCountsChecked']} aggregierten Gruppen geprüft. ATR wird separat Kerze für Kerze rekonstruiert; Abstände, Zeitgrenzen, Kontaktbekanntheit, SMA-Kontext, Projektionen und Zählungen werden aus den gespeicherten Quellen nachgerechnet.",
        'Quellfenster mit ausreichendem Vorlauf: '+', '.join(f'{w}: {n} Aktien' for w, n in result['eligibility'].items())+'.',
        'Zusätzlich synthetische Zukunftsschocks, Episodenwechsel, Datenlücken, Snapshotgrenzen, manuelle Stummschaltung und Wiederaufnahme geprüft.',
        'Die Originalgeometrie wird je Warnstufe gespeichert. Eine Rückprojektion derselben aktuell bekannten Linie über vergangene Kurse ist eine aktuelle Merkmalsmessung, kein damals bereits bekanntes Signal; `lineKnownAtComparison` kennzeichnet die Unterscheidung.',
        'Die ATR-Projektion ist ein Szenario mit unveränderter Linie und heutigem ATR. Der tatsächliche Entry kommt ausschließlich aus dem gemeinsamen Entry-Modul; insbesondere erzeugt der projizierte Offset keinen Safety-Bounce-Trigger.', '',
        'Dieses bekannte Überlebendenuniversum und diese bereits ausgewerteten Zeitfenster sind keine unabhängige Strategiebestätigung. Es wird weder Rentabilität noch eine verlässliche Vorhersage eines Ausbruchs in ein bis zwei Tagen behauptet.', '',
        'Werkzeugvertrag und nächste Schritte: [EARLY-WARNING.md](EARLY-WARNING.md). Private Pläne, Kursdaten, Snapshots, Blöcke, Reviews und Rohmessungen unter dem Studienordner bleiben außerhalb von Git.', '']
    return '\n'.join(out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True); parser.add_argument('--output', required=True)
    args = parser.parse_args(); Path(args.output).write_text(report(args.root), encoding='utf-8')
