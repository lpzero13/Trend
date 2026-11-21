"""Compare immutable radar universes; distinguish the unchanged control from added stocks."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from early_warning_study import checked, load_block
from fan_geometry import stable_id
from strategy_screen import read, write


def difference(total, baseline, sessions):
    """Exact additive counts for a disjoint added universe; never average rates."""
    result = {k: total[k]-baseline[k] for k in ('entries', 'coveredEntries', 'covered1to2Sessions',
        'warnings', 'confirmed', 'fizzled', 'censored')}
    assert all(v >= 0 for v in result.values())
    days = set(total['daily']) | set(baseline['daily'])
    assert all(total['daily'].get(d, 0) >= baseline['daily'].get(d, 0) for d in days)
    result['daily'] = {d: total['daily'].get(d, 0)-baseline['daily'].get(d, 0) for d in sorted(days)
                       if total['daily'].get(d, 0) > baseline['daily'].get(d, 0)}
    result['recallPct'] = 100*result['coveredEntries']/result['entries'] if result['entries'] else None
    result['early1to2SessionRecallPct'] = 100*result['covered1to2Sessions']/result['entries'] if result['entries'] else None
    result['confirmedWarningPct'] = 100*result['confirmed']/result['warnings'] if result['warnings'] else None
    result['messagesPerSession'] = sum(result['daily'].values())/sessions
    return result


def compare(baseline, expanded, output):
    baseline, expanded = Path(baseline), Path(expanded)
    old, new = checked(read(baseline/'plan.json')), checked(read(expanded/'plan.json'))
    for field in ('engine', 'rules', 'windows', 'warmupDays', 'dataRoot'):
        assert stable_id(old[field]) == stable_id(new[field]), ('different experiment', field)
    for root, plan in ((baseline, old), (expanded, new)):
        assert read(root/'verification.json')['planId'] == plan['id']
    common = set(old['symbols']) & set(new['symbols'])
    excluded = set(old['symbols'])-set(new['symbols'])
    for symbol in common:
        assert old['datasets'][symbol] == new['datasets'][symbol], ('changed control data', symbol)
    # Every control block must retain precisely the same hypotheses and geometry.
    for symbol in sorted(common):
        a, b = load_block(baseline, old, symbol), load_block(expanded, new, symbol)
        for field in ('records', 'episodes', 'eligibility', 'rawSignals', 'sourceGaps'):
            assert a[field] == b[field], ('control changed', symbol, field)
    for symbol in excluded:
        assert not any(load_block(baseline, old, symbol)['eligibility'].values()), ('eligible control missing', symbol)
    added = set(new['symbols'])-set(old['symbols'])
    previous, total = read(baseline/'results.json'), read(expanded/'results.json')
    assert previous['sessions'] == total['sessions']
    previous_groups = {(g['policy'], g['family']): g for g in previous['groups']}
    rows = []
    for g in total['groups']:
        key = g['policy'], g['family']; a = previous_groups[key]
        b = difference(g, a, total['sessions'])
        for metric in ('entries', 'coveredEntries', 'covered1to2Sessions', 'warnings', 'confirmed', 'fizzled', 'censored'):
            assert a[metric]+b[metric] == g[metric], (key, metric)
        rows.append({'policy': key[0], 'family': key[1], 'baseline': a, 'added': b, 'expanded': g})
    result = {'baselinePlanId': old['id'], 'expandedPlanId': new['id'], 'unchangedControlSymbols': len(common),
              'ineligibleOldSymbolsNotNeeded': sorted(excluded), 'addedSymbols': len(added),
              'expandedSymbols': len(new['symbols']), 'groups': rows, 'controlRecordsIdentical': True}
    write(expanded/'universe-comparison.json', result)
    names = {'breakout': 'Ausbruch', 'red_retest': 'Roter Retest', 'safety_bounce': 'Safety-Bounce'}
    text = ['# Vorwarnversuch auf erweitertem Bestand – 01.11.2026', '',
        f"{len(new['symbols'])} für mindestens ein Fenster geeignete Symbole; {len(common)} unveränderte Kontrollaktien und {len(added)} zusätzliche Aktien.",
        'Die nicht mehr im neuen Quellplan enthaltenen alten Symbole waren in keinem alten Testfenster geeignet: '+', '.join(sorted(excluded))+'.',
        'Identische Regeln, Quellintervalle und Fenster: 2018, 2021, 2023 sowie April 2025–März 2026. Keine neue Parameteroptimierung, neue Providerabfrage oder unabhängige Zeitvalidierung.', '',
        '## Einfache Abstandswarnung, 1 ATR', '',
        '| Familie | Auswertung | Entries | Vorher erfasst % | 1–2 Sitzungstage vor Entry: Anteil aller Entries % | Warnungen | Meldungen/Tag |',
        '|---|---|---:|---:|---:|---:|---:|']
    def fmt(value): return '–' if value is None else f'{value:.1f}'
    for row in rows:
        if row['policy'] != 'distance:1': continue
        for label, tag in (('Bisheriger Bestand', 'baseline'), ('Zusätzliche Aktien', 'added'), ('Gesamter neuer Bestand', 'expanded')):
            g = row[tag]
            text.append(f"| {names[row['family']]} | {label} | {g['entries']} | {fmt(g['recallPct'])} | {fmt(g['early1to2SessionRecallPct'])} | {g['warnings']} | {g['messagesPerSession']:.2f} |")
    text += ['', 'Erfassungsquoten gelten auf Episode/Familie und nur für Warnungen vor dem Entry bei noch aktiver Beobachtung. Für den rohen Rot-Bruch und die erste Berührung gelten die gesonderten Tabellen des vollständigen Ergebnisberichts. Die Quoten sind keine Gewinnerquoten.', '',
        '## Zusatzbedingungen bei Ausbrüchen, jeweils 1 ATR', '',
        '| Variante | Alter Bestand: erfasst % | Neue Aktien: erfasst % | Gesamt: erfasst % | Gesamt: später bestätigte Warnungen % | Gesamt: Meldungen/Tag |',
        '|---|---:|---:|---:|---:|---:|']
    for row in rows:
        if row['family'] != 'breakout' or not row['policy'].endswith(':1'): continue
        a, b, g = row['baseline'], row['added'], row['expanded']
        text.append(f"| {row['policy'].split(':')[0]} | {fmt(a['recallPct'])} | {fmt(b['recallPct'])} | {fmt(g['recallPct'])} | {fmt(g['confirmedWarningPct'])} | {g['messagesPerSession']:.2f} |")
    text += ['', '## Prüfergebnis', '',
        'Alle Kontrollaktien behalten dieselben Dataset-IDs, Originalwarnungen, Episoden, Entryreferenzen und Quellenlücken. Die zusätzlichen Aktien bilden eine disjunkte Ergänzung. Ihre Zähler werden deshalb exakt als Gesamt minus unveränderte Kontrolle ermittelt und ihre Quoten daraus neu berechnet. Gesamt- und Kontrollzähler wurden unabhängig geprüft. Mediane werden nicht aus Gruppenmedianen gemittelt.',
        'Das Universum entspricht vorhandenen heutigen Aktienbeständen, nicht historischen Indexmitgliedschaften. Aktienklassen, Branchen und gemeinsame Markttage erzeugen Abhängigkeiten. Die zwölf Policies teilen Fälle; ihre Stichproben dürfen nicht addiert werden.',
        'Dies wiederholt die letzte Vorwarn-/Signalstudie. Es ist keine neue Exit-, Fill- oder Depot-P/L-Simulation.', '',
        'Vollständige Schwellen-, Qualitäts-, Vorlauf- und Lasttabellen: [EARLY-WARNING-512-ERGEBNISSE-20261101.md](EARLY-WARNING-512-ERGEBNISSE-20261101.md).', '']
    Path(output).write_text('\n'.join(text), encoding='utf-8')
    return {'controlIdentical': True, 'added': len(added), 'expanded': len(new['symbols'])}


if __name__ == '__main__':
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True); parser.add_argument('--expanded', required=True); parser.add_argument('--output', required=True)
    args = parser.parse_args(); print(json.dumps(compare(args.baseline, args.expanded, args.output)), flush=True)
