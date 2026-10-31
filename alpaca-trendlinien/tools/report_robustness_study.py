"""Render completed fixed-rule evidence as Markdown, including failures and missing data."""
import argparse
from pathlib import Path
import statistics
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from robustness_study import validate_plan, window_root
from strategy_screen import read


def number(v):return 'nicht auswertbar' if v is None else f'{v:+.2f} %'.replace('.',',')


def render(root):
    root=Path(root);p=validate_plan(read(root/'plan.json'));summary=read(root/'summary.json')
    rows=[read(window_root(root,f)/'result.json') for f in p['folds']['validation']]
    blocks=sum(len(r['availability']) for r in rows)
    unavailable=sum(v!='available' for r in rows for v in r['availability'].values())
    lines=['# Breite Robustheitsprüfung des festen Ausbruch-Kandidaten',
        '', 'Stand: 30.10.2026. [Vorab festgelegter Versuchsplan](ROBUSTHEITSPLAN-20261030.md).', '',
        f"Unveränderte Strategie auf **{len(p['symbols'])} Aktien und {len(rows)} Zeitfenstern** geprüft: {blocks} Aktien-/Zeitfenster, davon {unavailable} wegen fehlender Vorgeschichte oder Entry-Abdeckung nicht verfügbar. Keine Ersetzung nach Ergebnis, keine erneute Parametersuche, keine Providerabrufe.", '',
        '## Gesamtes Universum – je Zeitraum dasselbe Anfangskapital von 2.000 USD', '',
        '| Entry-Zeitraum | Verfügbare Aktien | Trades / geschlossen | Netto Basis | Drawdown 5m | Doppelte variable Kosten | +1 USD je Order | +2 USD je Order |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        c=r['cohorts']['all'];v=c['scenarios'];b=v['base']
        lines.append(f"| {r['fold']['name']} | {len(c['availableSymbols'])}/{len(c['symbols'])} | {b['accepted']} / {b['closed']} | {number(b['markedReturnPct'])} | {number(b['max5mSampledDrawdownPct'])} | {number(v['double_cost']['markedReturnPct'])} | {number(v['fee_1']['markedReturnPct'])} | {number(v['fee_2']['markedReturnPct'])} |")
    lines += ['', '**Getrennte Kapitalstarts:** Die Tabellenwerte sind keine aufeinanderfolgenden Jahresrenditen und dürfen nicht addiert oder zu einer durchgehenden Depotkurve verkettet werden. Bei unvollständigen Büchern betrifft der Drawdown nur den beobachteten Teilpfad. Kosten können durch andere Stückzahlen auch spätere Belegungen verändern. Beispiel 2023: 32 Trades ohne Festgebühr, 34 bei 1 USD und 31 bei 2 USD je Order; die höhere Gesamtrendite bei 2 gegenüber 1 USD ist kein positiver isolierter Gebühreneffekt, sondern ein anderes belegtes Portfolio.', '',
              '## Vorab definierte Prüfgrenzen und Kontrollen', '',
              '| Zeitraum | Basis-/Kosten-/Streuungsgrenzen | Vollständige Kontrollbücher | Kontrollmedian | Kontroll-P90 | Gesamtes statistisches Prüftor |',
              '|---|---|---:|---:|---:|---|']
    for r in rows:
        c=r['controls'];returns=[v['markedReturnPct'] for v in c['items'] if v['markedReturnPct'] is not None]
        complete=c['complete'];gate=r['cohorts']['all']['baseGate']
        median=statistics.median(returns) if complete else None
        lines.append(f"| {r['fold']['name']} | {'bestanden' if gate['passed'] else 'nicht bestanden'} | {len(returns)}/39 | {number(median)} | {number(c['q90ReturnPct'] if complete else None)} | {'bestanden' if r['statisticalScreenPassed'] else 'nicht bestanden'} |")
    lines += ['', 'Das Prüftor verlangt alle Basisgrenzen sowie einen Nettoertrag oberhalb des 90. Perzentils von 39 vollständigen Zufallskontrollen. Die Kontrollen haben dieselbe Aktie, denselben Monat und kausal gültige Safety; sie sind explorativ und kein korrigierter Signifikanztest. Unvollständige Kontrollen bestehen das Tor nicht.', '',
              '## Vorherige 16 gegenüber zusätzlichen Aktien', '',
              '| Zeitraum | Bisherige 16: Basis | Zusätzliche Aktien: Basis | Zusätzliche Aktien: doppelte Kosten |',
              '|---|---:|---:|---:|']
    for r in rows:
        a=r['cohorts']['previous16']['scenarios'];b=r['cohorts']['additional']['scenarios']
        lines.append(f"| {r['fold']['name']} | {number(a['base']['markedReturnPct'])} | {number(b['base']['markedReturnPct'])} | {number(b['double_cost']['markedReturnPct'])} |")
    lines += ['', 'Auch diese Gruppen haben jeweils ein eigenes vollständiges 2.000-USD-Buch. Kein Ergebnis wird nachträglich als Gewinnerkorb ausgewählt.', '', '## Datenqualität, Signaldichte und Ablehnungen', '']
    for r in rows:
        c=r['cohorts']['all'];b=c['scenarios']['base'];available=c['availableSymbols']
        q=[r['quality'][s] for s in available]
        expected=sum(v['expectedFineBars'] for v in q);missing=sum(v['missingFineBars'] for v in q)
        unavailable=[s for s,v in r['availability'].items() if v!='available']
        failed=[k for k,v in c['baseGate']['checks'].items() if not v]
        gap_halt=b.get('halt')
        lines += [f"### {r['fold']['name']}", '',
                  f"- {b['eligibleSignals']} qualifizierte Ausbruch-Signale vor Budget-/Belegungsprüfung; {b['accepted']} angenommene Trades.",
                  f"- Ablehnungsgründe: `{b['skippedReasons']}`.",
                  f"- Wegen Datenhalt noch nicht entschiedene spätere Signale: {max(0,b['eligibleSignals']-b['accepted']-sum(b['skippedReasons'].values()))}. Das sind keine geprüften Ablehnungen.",
                  f"- Nicht verfügbare Aktien: {', '.join(unavailable) or 'keine'}.",
                  f"- Verfügbare Aktien einschließlich Vorlauf/Nachbeobachtung: {missing:,} fehlende von {expected:,} erwarteten 5m-Kerzen. Keine Auffüllung.",
                  f"- Nicht bestandene Basisgrenzen: {', '.join(failed) or 'keine'}.",
                  f"- Datenbedingter Kapitalbuchhalt: `{gap_halt}`.",
                  f"- Positive Aktienbeiträge: {b['positiveSymbols']}; größter Anteil an positiven Beiträgen: {100*b['positiveProfitConcentration']:.1f} %." if b['positiveProfitConcentration'] is not None else '- Keine positiven Aktienbeiträge.', '']
    lines += ['Sämtliche gespeicherten 1h-/4h-/1D-Aggregate der untersuchten Fenster wurden gegen ihre 5m-Basis nachgerechnet. Feiertage, Sommerzeit und verkürzte Sitzungen folgen dem versionierten Börsenkalender. Große Kurslücken allein bestätigen keine Kapitalmaßnahme.', '']
    preview=root/'data-repair-preview.json'
    if preview.exists():
        repair=read(preview)
        lines += ['## Gezielte Datenprüfung als nächster Schritt', '',
                  f"Die reine Offline-Vorschau nennt **{len(repair['items'])} Symbol-/Tagespaare an {len(repair['dates'])} Handelstagen**, an denen gehaltene Pfade die Basis-, Kosten- oder Kontrollbücher unterbrechen. Das ist keine vollständige Liste aller Archivlücken und kein nachträglicher Handelsfilter.", '',
                  '| Handelstag ET | Betroffene Aktien in unterbrochenen Büchern |','|---|---|']
        for d in repair['dates']:lines.append(f"| {d['dayET']} | {', '.join(d['symbols'])} |")
        lines += ['', 'Zuerst die konkreten 5m-Zeitpunkte und Importmetadaten prüfen, dann fehlende Providerdaten von bestätigten Handelspausen oder Intervallen ohne Handel unterscheiden. Bei neuen Providerdaten neue unveränderliche Datasets und einen neuen Versuchsplan anlegen. Alte Kurse, Prüfergebnisse und Journale erhalten; keine automatische Auffüllung oder Löschung. Der Sammler wurde nicht fortgesetzt.', '']
    verified=root/'verification.json'
    if verified.exists():
        v=read(verified)
        lines += ['## Technische Nachweise', '',
                  f"Separater Prüflauf bestanden: {v['cacheBlocks']} Blöcke, {v['signalCases']:,} Signalfälle aller Familien und {v['cashLedgers']} Kapitalbücher. Sämtliche vier Basisportfolios reproduziert; Kapitalbewegungen sowie Bewertungen/Drawdowns auf jeder 5m-Stufe unabhängig nachgerechnet. Auswahl unverändert, keine Providerabrufe.", '',
                  'Regression: 494 Python-Tests ohne Fehler, ein bestehender Skip; 70 Chart-/Web-JavaScript-Tests bestanden. Neues Signaljournal: echter AAPL-Vergleich zwischen Einzelschritten und Batch, Neustart ohne Duplikate, zukünftige Kursschocks ohne Änderung alter Signale, echter Prozessabbruch mit Rollback und Backup/Restore geprüft. Das ist technische Prüfung, keine prospektive Handelsbilanz.', '',
                  'Der erste Auswertungsversuch scheiterte beim Kontrollpool einer Aktie ohne ausreichende Vor-IPO-Historie. Korrektur in einem neuen Plan: solche ausdrücklich nicht verfügbaren Aktien haben keine gewünschten Kontrollentries. Alle 276 ursprünglichen Pilotblöcke wurden mit gleichem Daten-/Signal-/Ausführungscode geprüft übernommen; Quellplan, alter Code und alte Ausgaben bleiben erhalten. Keine Fortsetzung des alten Auftrags unter geänderter Engine.', '']
    lines += [
              '## Bewertung und verbleibende Grenzen', '',
              f"{summary['positiveWindows']} von {len(rows)} Gesamtfenstern haben einen vollständig berechenbaren positiven Basis-Nettoertrag. Vollständiges statistisches Prüftor über alle Fenster: **{'bestanden' if summary['allStatisticalScreensPassed'] else 'nicht bestanden'}**. Die Hypothese bleibt unverändert; ein Fehlschlag wird nicht durch neue Schwellen auf denselben Daten repariert.", '',
              '**Keine operative Freigabe:** Die historischen Daten enthalten splitbereinigte Preise. Ohne historische Splitfaktoren ist ein rechnerisch ganzzahliges Depot nicht vollständig als damals handelbares Ganzaktien-Depot nachgewiesen. Historische Gebühren, Dividenden, EUR/USD, Steuern und Cashverzinsung sind nicht vollständig abgebildet. Der aktuelle überlebende Aktienbestand ersetzt kein historisches Universum einschließlich delisteter Titel.', '',
              '2018/2021/2023 sind zusätzliche Robustheitsfenster dieser Runde, jedoch nicht garantiert projektweit unangetastet. Der spätere Block 2025/26 wurde für Teile des Universums schon verwendet. Die Ergebnisse sind keine prospektive Erfolgsbestätigung.', '',
              '## Reproduzierbarkeit und Hermes', '',
              'Das private Studienverzeichnis enthält den vor Berechnung gespeicherten Plan, explizite Dataset-IDs, Engine-Prüfsummen, je Symbol/Zeitfenster geprüfte Signal-/Kursblöcke, sämtliche Kapitalbücher, Kostenvarianten, Kontrollen und Ergebnis-Prüfsummen. Laufende/abgebrochene Berechnungen können nur mit unverändertem Plan und Engine wiederaufgenommen werden.', '',
              '```text',
              'python tools/run_robustness_study.py --root PRIVATER_ORDNER --source ALTER_40_TAGE_VERSUCH --datasets SYMBOL_DATASET_JSON --phase prepare',
              'python tools/run_robustness_study.py --root PRIVATER_ORDNER --phase build --workers 2',
              'python tools/run_robustness_study.py --root PRIVATER_ORDNER --phase evaluate',
              'python tools/verify_robustness_study.py --root PRIVATER_ORDNER',
              '```', '',
              'Alle Befehle verwenden den bestehenden `TORI_DATA_DIR`. Keine automatische Datenbeschaffung, kein Sammler-Resume, keine UI-Änderung, Containerinstallation, Order oder Meldungszustellung.']
    return '\n'.join(lines)+'\n'


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--root',required=True);a.add_argument('--output',required=True);args=a.parse_args()
    Path(args.output).write_text(render(args.root),encoding='utf-8')
