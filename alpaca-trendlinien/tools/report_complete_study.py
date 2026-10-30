"""Inspectably aggregate the frozen study; no threshold search/model selection."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import random
from statistics import mean, median
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from complete_strategy import PROFILES
from complete_outcomes import EXITS
from datasets import read_dataset, source_bars, digest
from lab_data import session_bounds
from lab_splits import sessions_between
from models import NY
from tools.complete_study_import import write

LABELS = {'two':'2 Kontakte', 'three':'3 Aktionskontakte', 'age7':'+ Alter 7 Tage',
    'momentum':'+ Schwung / Zwischenhoch', 'safety':'+ nahe Safety',
    'context_room':'+ Kontext und Raum', 'all_events':'+ Ereigniskalender',
    'age14':'Sensitivität: 14 Tage', 'green3':'Sensitivität: auch Grün 3',
    'whole_body':'Sensitivität: ganzer Körper', 'exact3':'Sensitivität: exakt 3'}


def fmt(v, digits=2):
    return '—' if v is None else f'{v:.{digits}f}'


def stock_interval(entries, value):
    blocks = defaultdict(list)
    for e,v in entries:
        if v is not None: blocks[e['symbol']].append(v)
    names = sorted(blocks)
    if len(names) < 3: return None
    rng = random.Random('complete-study-stock-bootstrap-20261022|'+value)
    samples = []
    for _ in range(1000):
        drawn = [x for name in rng.choices(names,k=len(names)) for x in blocks[name]]
        samples.append(mean(drawn))
    samples.sort()
    return [samples[24],samples[974]]


def run(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    summary = json.loads((root/'summary.json').read_text('utf-8'))
    contract = json.loads((root/'study-contract.json').read_text('utf-8'))
    verified = json.loads((root/'verification.json').read_text('utf-8'))
    if not verified['passed'] or verified['contractHash'] != digest(contract): raise ValueError('Verified run required')
    imports = json.loads((root/'imports.json').read_text('utf-8'))
    all_entries, quality = [], []
    for p in sorted((root/'studies').glob('*.json')):
        b = json.loads(p.read_text('utf-8'))
        all_entries.extend(b['entries'])
    for symbol, imp in sorted(imports.items()):
        if not imp.get('id'):
            quality.append({'symbol':symbol,'error':imp.get('error')});continue
        data = read_dataset(imp['id']); sources = source_bars(data); fine = sources['5m']
        first, last = [str(datetime.fromtimestamp(t,NY).date()) for t in (fine[0].time,contract_time(contract, root))]
        expected_days = sessions_between(first,last)
        expected_fine = sum((session_bounds(d)[1]-session_bounds(d)[0])//300 for d in expected_days)
        expected_four = sum((session_bounds(d)[1]-session_bounds(d)[0]+14399)//14400 for d in expected_days)
        quality.append({'symbol':symbol,'firstDate':first,'lastDate':str(datetime.fromtimestamp(fine[-1].end,NY).date()),
            'fine':len(fine),'expectedFine':expected_fine,'finePct':len(fine)/expected_fine*100,
            'four':len(sources['4h']),'expectedFour':expected_four,'fourPct':len(sources['4h'])/expected_four*100,
            'daily':len(sources['1D']),'expectedDaily':len(expected_days),'dailyPct':len(sources['1D'])/len(expected_days)*100})
    available = [q for q in quality if 'fine' in q]
    by_profile = {}
    for tf in ('4h','1D'):
        exposure = sum(sum(b['barCounts'].values()) for b in summary['coverage'] if b['timeframe']==tf and b['geometry']=='strict')
        calendar_years = sum((b['endAt']-b['startAt'])/86400/365.25 for b in summary['coverage'] if b['timeframe']==tf and b['geometry']=='strict')
        for profile in PROFILES:
            rows = [e for e in all_entries if e['geometry']=='strict' and e['timeframe']==tf and e['profile']==profile]
            by_profile[tf+'/'+profile] = {'entries':len(rows),'physicalTimes':len({(e['symbol'],e['entryAt']) for e in rows}),
                'stocks':len({e['symbol'] for e in rows}), 'calendarStockYears':calendar_years,
                'signalsPerCalendarStockYear':len({(e['symbol'],e['entryAt']) for e in rows})/calendar_years if calendar_years else None,
                'completeSourceBarsAfterWarmup':exposure}
    lines = ['# Gesamttest der Tori-Kriterien – 60 Aktien und längere Historie', '',
        'Stand 22.10.2026. Isolierte lokale Forschung; Chart, bestehende Profile und laufender Beobachter unverändert. Keine Orders und kein Container-Rollout.', '',
        '**Ergebnisstatus: mit wesentlichen Einschränkungen interpretierbar; keine validierte Handelsstrategie.** Die kursbasierten Regeln sind ausführbar und der erweiterte Durchlauf ist abgeschlossen. Vollständige Kriterienkonformität bleibt wegen fehlender historischer Ereignisabdeckung ungeklärt. Menschliche Linienbewertungen stehen ebenfalls aus.', '',
        '## Datenbasis und tatsächliche Abdeckung', '',
        f"Vorab festgelegte Aktien: {len(imports)}; importiert: {len(available)}; vollständig zurückgewiesene Imports: {len(imports)-len(available)}. Verfügbare Anfangsdaten: {min(q['firstDate'] for q in available)} bis {max(q['firstDate'] for q in available)}; Ende 21.10.2026. Zehn Jahre angefordert, IEX liefert in diesen Imports erst ab 2020. Nach einem Jahr Vorlauf jede Quellkerze verarbeitet, ohne kurze Suchfenster- oder Linienlebensdauergrenze.", '',
        f"Gespeicherte reguläre 5m-Kerzen: {sum(q['fine'] for q in available):,}. 4h-Kerzen: {sum(q['four'] for q in available):,}; Tageskerzen: {sum(q['daily'] for q in available):,}. Median der tatsächlichen Abdeckung: 5m {median(q['finePct'] for q in available):.2f} %, 4h {median(q['fourPct'] for q in available):.2f} %, 1D {median(q['dailyPct'] for q in available):.2f} %. Eine einzige fehlende 5m-Kerze kann ein Aggregat entwerten. Fehlende Kurse wurden weder ergänzt noch als Seitwärtskerzen erfunden.", '',
        'Fehlende IEX-Kerzen sind nicht automatisch defekte Downloads: Ohne geeignete Trades wird laut [Alpacas Market Data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq) keine Bar erzeugt. Unser vollständiges 5m-Raster ist eine konservative Forschungsannahme; es kann deshalb viele Aggregate und lange Haltedauern ausschließen. Die vorhandenen OHLC-Daten unterscheiden fehlende Handelsaktivität auf IEX, Datenlieferlücken und die Ausführbarkeit am Gesamtmarkt nicht zuverlässig. Nicht durch erfundene konstante Kerzen beheben.', '',
        'Die heutigen 60 überwiegend liquiden US-Unternehmen sind kein historisch vollständiges Aktienuniversum. Delistings, Europa und Dividendenrenditen fehlen. Splitbereinigung nach heutigem Anpassungsstand und IEX als einzelner Handelsplatz bleiben Modellgrenzen; die normalisierten historischen Preise sind keine damaligen unbereinigten Brokerpreise. Frühere bekannte Zeiträume sind kein neuer unberührter Holdout.', '',
        '| Aktie | 5m vollständig % | 4h vollständig % | 1D vollständig % |', '|---|---:|---:|---:|']
    for q in quality:
        lines.append(f"| {q['symbol']} | {fmt(q.get('finePct'))} | {fmt(q.get('fourPct'))} | {fmt(q.get('dailyPct'))} |" if 'fine' in q else f"| {q['symbol']} | Import zurückgewiesen | — | — |")
    lines += ['', '## Schritt 1: Drei Kontakte und Geometrie', '',
        'Außenlinie und Kontaktbereich sind getrennt: in der strengen Geometrie keine Dochtverletzung, dennoch nahe Kontakte auf der erlaubten Seite. Zwei benachbarte Kerzen ergeben keinen zusätzlichen Abpraller. Mehrere bestätigte Pivotpaare bleiben bis zur Signalauswahl erhalten; Ranking ohne spätere Renditen. Kontaktband bei Entstehung fixiert.', '',
        '| Geometrie / Intervall | Kandidaten | Kandidaten mit ≥3 Reaktionen | 2-Kontakt-Fälle | davon ≥3 nahe Aktionskontakte | davon ≥3 exakt kollineare Kontakte |', '|---|---:|---:|---:|---:|---:|']
    for geo in ('strict','zone'):
        for tf in ('4h','1D'):
            cov = [b for b in summary['coverage'] if b['geometry']==geo and b['timeframe']==tf]
            rows = [e for e in all_entries if e['geometry']==geo and e['timeframe']==tf and e['profile']=='two']
            lines.append(f"| {geo} / {tf} | {sum(b['candidates'] for b in cov)} | {sum(b['threeContactCandidates'] for b in cov)} | {len(rows)} | {sum(e['info']['contacts']>=3 for e in rows)} | {sum(e['info']['exactContacts']>=3 for e in rows)} |")
    lines += ['', 'Kandidaten und Profil-/Familienfälle sind keine unabhängigen Trades. Die lockere Zone erlaubt Dochtüberschreitungen und erfüllt damit nicht die strenge Zeichenregel. Exakte Kontaktzahlen sind hier eine Geometriediagnose, keine neue Handelsregel.', '',
        '## Schritte 2–4: Kontakte, Alter, Momentum, Safety, Kontext', '',
        'Alle Gruppen wurden vorab festgelegt. Hauptfolge ist verschachtelt; 14 Tage, drei grüne Kontakte, ganzer Körper und exakte Kontakte sind zusätzliche Sensitivitäten auf Basis der kursbasierten Kontextgruppe. Kein nachträglicher Wechsel zur günstigsten Einstellung.', '',
        '| Intervall / Prüfstand | Profil-/Familienfälle | eindeutige Aktie/Entryzeiten | Aktien | Signale je Kalender-Aktienjahr |', '|---|---:|---:|---:|---:|']
    for tf in ('4h','1D'):
        for p in PROFILES:
            v=by_profile[tf+'/'+p]
            lines.append(f"| {tf} / {LABELS[p]} | {v['entries']} | {v['physicalTimes']} | {v['stocks']} | {fmt(v['signalsPerCalendarStockYear'],3)} |")
    lines += ['', 'Der Nenner umfasst die Kalenderzeit nach Vorlauf auch bei späteren Datenlücken. Niedrige Raten können deshalb von der Datenqualität mitverursacht sein. Ausbleibende Signale sind kein Beweis gegen eine selten handelnde Strategie. Unbekannte Ereignisse sind ausdrücklich kein bestandener Filter.', '',
        '### Welche einzelne Prüfung bremst?', '',
        'Die folgende Diagnose benutzt ausschließlich die 2-Kontakt-Referenzfälle. Prüfungen einzeln betrachtet, nicht als unabhängige Ursachen addieren. Kontext und Raum sind unsere vorab definierte numerische Auslegung der weichen Textregel, keine unveränderlichen Tori-Grenzen.', '',
        '| Intervall | Prüfung | bestanden | nicht bestanden | unbekannt |', '|---|---|---:|---:|---:|']
    marginal = {}
    for tf in ('4h','1D'):
        rows = [e for e in all_entries if e['geometry']=='strict' and e['timeframe']==tf and e['profile']=='two']
        marginal[tf] = {}
        for check in ('three','age7','momentum','safety','context','room','events','age14','green3','whole_body','exact3'):
            v = {'pass':sum(e['checks'][check] is True for e in rows),
                 'fail':sum(e['checks'][check] is False for e in rows),
                 'unknown':sum(e['checks'][check] is None for e in rows)}
            marginal[tf][check] = v
            lines.append(f"| {tf} | {check} | {v['pass']} | {v['fail']} | {v['unknown']} |")
    lines += ['',
        '## Schritt 5: Warten statt kurzer Suchfenster', '',
        '| Geometrie / Intervall / Profil | zufällige Starts | späterer Entry gefunden | bis Datenende keiner | Median Wartezeit unter gefundenen (Kalendertage) |', '|---|---:|---:|---:|---:|']
    for tf in ('4h','1D'):
        for p in ('two','three','age7','safety','context_room'):
            v=summary['waiting']['strict/'+tf+'/'+p]
            lines.append(f"| strict / {tf} / {p} | {v['starts']} | {v['found']} | {v['notFoundBeforeEnd']} | {fmt(v['medianCalendarDaysAmongFound'],1)} |")
    lines += ['', '100 feste Zufallsstarts je Aktie/Intervall/Geometrie, ohne Outcomes ausgewählt. Mehrere Starts dürfen denselben späteren Entry erreichen; sie sind keine zusätzlichen Einstiege. Der Median gilt nur für gefundene Fälle, am Datenende abgeschnittene Wartezeiten sind nicht enthalten.', '',
        '## Schritte 6–7: Kursverlauf und natürliche Exits', '',
        'Vergleich unten: alle aufeinander aufbauenden kursbasierten Prüfstände der strengen Geometrie, damit auch die Wirkung vor dem besonders engen Safety- und Kontextfilter sichtbar bleibt. Kein fixes Take-Profit und kein Zehn-Tage-Zwangsverkauf. Nur die Freitagsvariante enthält den vorab definierten diskretionären Widerstandsausstieg. Tages-Freitagsverkauf nach dem Schluss ist nicht ausführbar und wird als nicht unterstützt ausgewiesen.', '',
        '| Intervall / Profil / Familie / Phase | Entries | Exitmodell | geschlossen | offen | unbekannt | Ø R geschlossen | Treffer % geschlossen |', '|---|---:|---|---:|---:|---:|---:|---:|']
    ci={}
    for tf in ('4h','1D'):
        for profile in ('two','three','age7','momentum','safety','context_room'):
            for family in ('breakout','retest','bounce'):
                for phase in ('2021-2023','2024-2026'):
                    key='/'.join(('strict',tf,profile,family,phase)); group=summary['groups'][key]
                    for model in EXITS:
                        if tf=='1D' and model=='friday': continue
                        s=group['exits'][model]
                        lines.append(f"| {tf} / {profile} / {family} / {phase} | {group['entries']} | {model} | {s['closed']} | {s['statuses'].get('open',0)} | {s['statuses'].get('unknown',0)} | {fmt(s['meanR'])} | {fmt(s['winPct'],1)} |")
                    selected=[e for e in all_entries if e['geometry']=='strict' and e['timeframe']==tf and e['profile']==profile and e['family']==family and ('2021-2023' if datetime.fromtimestamp(e['entryAt'],NY).year<=2023 else '2024-2026')==phase]
                    ci[key]={m:stock_interval([(e,e['paths'][m].get('netR')) for e in selected if e['paths'][m]['status']=='closed'], key+'/'+m) for m in EXITS}
    lines += ['', '**Geschlossene Fälle allein sind keine unverzerrte Gesamtperformance.** Länger gehaltene Positionen können häufiger in eine Datenlücke laufen; sie wurden als unbekannt zensiert. Die Ausstiegsmodelle dürfen deshalb nicht anhand der Mittelwerte unterschiedlich vollständiger Gruppen zum Gewinner erklärt werden. Offene Buchwerte sind kein realisierter Gewinn. R ist das anfängliche geplante Positionsrisiko einschließlich Einstiegskosten, keine Depotprozentzahl.', '',
        'Insbesondere realisiert ein ausschließlich fester Stop unter dem Einstieg ohne sonstigen Ausstieg definitionsgemäß nur Verluste; erfolgreiche Positionen bleiben offen. Seine null Prozent Gewinntrades unter den geschlossenen Fällen sind deshalb keine faire Verlustquote der Gesamtstrategie.', '',
        'Kostenannahme pro Seite: halber Spread 2,5 Basispunkte plus 5 Basispunkte Slippage, keine zusätzliche fixe Gebühr. Stop-Gaps zum verfügbaren Open. Bei fehlendem erwarteten 5m-Pfad keine erfundene Stopreihenfolge. Nachgezogene Stops werden erst nach 2+2-Bestätigung und fünf Minuten Latenz wirksam; niemals rückwirkend.', '',
        'Vollständige Gruppen einschließlich ungefilterter Referenz, Sensitivitäten, 5/10/20/60-Sitzungs-Schlusskursbeobachtungen, gepaarter geschlossener Fälle und Aktien-Blockintervalle liegen in den privaten JSON-Dateien. Diese Schlusskursbeobachtungen sind Ereignisstudien, keine simulierten Strategieexits oder Depot-P/L.', '',
        '### Vergleich einschließlich offener Positionen', '',
        'Auf derselben Fallmenge werden geschlossene Positionspfade zum realisierten Wert, offene zum beobachteten Liquidationsbuchwert am gemeinsamen Phasenende bewertet. Kein Verkauf wird dadurch ausgelöst. Nur Fälle mit für alle drei Modelle bekanntem Pfad; diese Auswahl nach Pfadvollständigkeit dient ausschließlich der Diagnose und ist kein handelbarer Entryfilter. Unbekannte Fälle fehlen weiterhin und begrenzen die Aussage.', '',
        '| Intervall / Profil / Familie | alle Fälle | drei Modelle gemeinsam bekannt | fixed Ø bewertetes R | higher_low Ø bewertetes R | higher_low_green Ø bewertetes R |', '|---|---:|---:|---:|---:|---:|']
    terminal = {}
    for tf in ('4h','1D'):
        for profile in ('two','three','age7','momentum','safety','context_room'):
            for family in ('breakout','retest','bounce'):
                rows = [e for e in all_entries if e['geometry']=='strict' and e['timeframe']==tf and e['profile']==profile and e['family']==family]
                models = ('fixed','higher_low','higher_low_green')
                known = [e for e in rows if all(e['paths'][m]['status'] in ('closed','open') for m in models)]
                values = {m: [e['paths'][m]['netR'] if e['paths'][m]['status']=='closed' else e['paths'][m]['markNetR'] for e in known] for m in models}
                averages = {m:mean(v) if v else None for m,v in values.items()}
                key='/'.join((tf,profile,family))
                terminal[key]={'all':len(rows),'jointKnown':len(known),'means':averages,
                    'meanHigherLowDeltaR':mean(v-u for u,v in zip(values['fixed'],values['higher_low'])) if known else None}
                lines.append(f"| {tf} / {profile} / {family} | {len(rows)} | {len(known)} | {fmt(averages['fixed'])} | {fmt(averages['higher_low'])} | {fmt(averages['higher_low_green'])} |")
    lines += ['',
        '## Was weiterhin offen ist', '',
        f"- {len(list((root/'blind').glob('*.json')))} verblindete Quellintervall-Fälle vorbereitet; noch keine echten manuellen Ray-Bewertungen. Eine verbesserte Nachbildung subjektiver Linienwahl ist damit technisch messbar, aber nicht durch menschliche Urteile bestätigt.",
        '- Historische, zum jeweiligen Zeitpunkt bekannte Ereignisabdeckung fehlt. Daher keine vollständig nach allen sechs Prüfständen freigegebenen Trades und kein Nachweis für das komplette Textpaket.',
        '- Kein neues Depot-/Cashledger für diese neue Strategie. Die Fallzahlen sind nicht gleich unabhängig gleichzeitig handelbaren Positionen. Keine Aussage über erzielbare Kontorendite.',
        '- Für belastbare Aussage über seltene Signale braucht es ausreichende zusammenhängende Marktdaten, weitere Zukunftsbeobachtung und echte manuelle Geometrieprüfung. Mehr Jahre ersetzen fehlende Datenqualität nicht.', '',
        '## Reproduzieren', '', '```powershell',
        'python tools/complete_study_import.py --root artifacts/tori-complete-neu',
        'python tools/complete_study.py --root artifacts/tori-complete-neu',
        'python tools/verify_complete_study.py --root artifacts/tori-complete-neu',
        'python tools/report_complete_study.py --root artifacts/tori-complete-neu --output TORI-GESAMTTEST-TABELLEN.md',
        '```', '',
        'Immer denselben TORI_DATA_DIR benutzen. Die Werkzeuge importieren keine Zugangsdaten in Artefakte und führen keine Orders aus. Ein bereits eingefrorener Lauf verweigert geänderte Engine-/Datasetverträge. Technischer AAPL-Pilot im Importverzeichnis `-a`; finaler Lauf in `-b` verwendet explizit dieselben gepinnten Imports, ergänzt um unveränderte Datenerfassung für den Auditor. Keine Parameter anhand des Pilotergebnisses geändert.', '',
        f"Prüfsumme Forschungsauftrag: `{digest(contract)}`. Unabhängige Abnahme: {verified['entries']} Entrydatensätze, {verified['uniquePaths']} unterschiedliche Modellpfade, {verified['auditedFineBars']} geprüfte Pfadkerzen. Keine Browserprüfung nötig, da keine Weboberfläche geändert wurde.", '']
    diagnostics={'profileCounts':by_profile,'quality':quality,'stockBootstrapIntervals':ci,'marginalChecks':marginal,'terminalKnownComparison':terminal,
                 'meaning':'Intervals conditional on known closed outcomes; no correction for unavailable paths or universe selection.'}
    write(root/'diagnostics.json',diagnostics)
    output.write_text('\n'.join(lines),'utf-8')
    print(json.dumps({'output':str(output),'imports':len(imports),'available':len(available),'entries':len(all_entries)}))


def contract_time(contract,root):
    return json.loads((root/'import-contract.json').read_text('utf-8'))['endAt']


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();run(a.root,a.output)
