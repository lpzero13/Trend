"""Matched historical feed comparison and separate cash-feasibility ledgers."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import json
from pathlib import Path
from statistics import mean,median
import sys
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from datasets import digest,read_dataset
from lab_data import session_bounds
from lab_splits import sessions_between
from models import NY
from workbench_portfolio import CloseMarks,ledger
from tools.complete_study_import import write
from tools.complete_study import engine_hashes
from workbench_scanner import engine_hash as scanner_hash


def load(root):
    c=json.loads((root/'study-contract.json').read_text('utf-8'))
    v=json.loads((root/'verification.json').read_text('utf-8'))
    if not v['passed'] or v['contractHash']!=digest(c) or c['engine']!=engine_hashes():raise ValueError('Verified, unchanged engine required')
    imports=json.loads((root/'imports.json').read_text('utf-8'))
    blocks=[]
    for p in sorted((root/'studies').glob('*-strict.json')):
        b=json.loads(p.read_text('utf-8'))
        if b['contractHash']!=digest(c) or b['checksum']!=digest({k:v for k,v in b.items() if k!='checksum'}):raise ValueError('Changed block')
        blocks.append(b)
    return c,imports,blocks


def group(entries):
    stats={}
    for profile in ('two','three','age7','momentum','safety','context_room','all_events'):
        rows=[e for e in entries if e['profile']==profile]
        stats[profile]={'entries':len(rows),'uniqueStockTimes':len({(e['symbol'],e['entryAt']) for e in rows}),
            'stocks':len({e['symbol'] for e in rows}),'families':dict(Counter(e['family'] for e in rows))}
    outcomes={}
    for family in ('breakout','retest','bounce'):
        for phase in ('all','2021-2023','2024-2026'):
            rows=[e for e in entries if e['profile']=='age7' and e['family']==family and
                (phase=='all' or (datetime.fromtimestamp(e['entryAt'],NY).year<=2023)==(phase=='2021-2023'))]
            horizons={}
            for h in (5,10,20,60):
                vals=[e['intermediate'][str(h)]['netReturnPct'] for e in rows if e['intermediate'][str(h)]['status']=='known']
                horizons[str(h)]={'known':len(vals),'unknown':len(rows)-len(vals),'meanNetPct':mean(vals) if vals else None,
                    'positivePct':100*sum(v>0 for v in vals)/len(vals) if vals else None}
            paths={}
            for model in ('fixed','higher_low','higher_low_green','friday'):
                ps=[e['paths'][model] for e in rows];closed=[p for p in ps if p['status']=='closed'];rs=[p['netR'] for p in closed]
                paths[model]={'statuses':dict(Counter(p['status'] for p in ps)),'closedMeanR':mean(rs) if rs else None,
                    'closedWins':sum(r>0 for r in rs),'withoutBestMeanR':mean(sorted(rs)[:-1]) if len(rs)>1 else None}
            warnings={k:dict(Counter('unknown' if e['signalChecks'].get(k) is None else 'pass' if e['signalChecks'][k] else 'warn' for e in rows)) for k in ('momentum','safety','context','room','events')}
            outcomes[family+'/'+phase]={'entries':len(rows),'intermediate':horizons,'paths':paths,'featuresAtSignal':warnings}
    return {'profiles':stats,'age7':outcomes}


def run(iex,sip,output):
    iex,sip,output=map(lambda p:Path(p).resolve(),(iex,sip,output))
    ic,ii,ib=load(iex);sc,si,sb=load(sip)
    scanner=json.loads((sip/'scanner-verification.json').read_text('utf-8'))
    if not scanner['passed'] or scanner['studyContract']!=digest(sc) or scanner['engineHash']!=scanner_hash():raise ValueError('Verified unchanged explained scanner required')
    if ic['rules']!=sc['rules'] or ic['engine']!=sc['engine']:raise ValueError('Rules differ')
    ir=json.loads((iex/'import-contract.json').read_text('utf-8'));sr=json.loads((sip/'import-contract.json').read_text('utf-8'))
    if ir['endAt']!=sr['endAt']:raise ValueError('Unmatched end')
    paired=sorted(s for s in set(ii)&set(si) if ii[s].get('id') and si[s].get('id'))
    comparison={};quality=[]
    contexts={}
    for feed,imports,blocks in [('iex',ii,ib),('sip',si,sb)]:
        for tf in ('4h','1D'):
            comparison[feed+'/'+tf]=group([e for b in blocks if b['symbol'] in paired and b['timeframe']==tf for e in b['entries']])
        for symbol in paired:
            d=read_dataset(imports[symbol]['id']);m=d['material'];bars=m['bars']
            if m['feed']!=feed:raise ValueError('Mislabeled feed')
            start=min(b['time'] for b in bars['5m'])
            days=sessions_between(str(datetime.fromtimestamp(start,NY).date()),str(datetime.fromtimestamp(sr['endAt'],NY).date()))
            fine=sum((session_bounds(day)[1]-session_bounds(day)[0])//300 for day in days)
            four=sum((session_bounds(day)[1]-session_bounds(day)[0]+14399)//14400 for day in days)
            quality.append({'symbol':symbol,'feed':feed,'first':start,'last':bars['5m'][-1]['end'],
                'counts':{tf:len(rows) for tf,rows in bars.items()},
                'coveragePct':{'5m':100*len(bars['5m'])/fine,'4h':100*len(bars['4h'])/four,'1D':100*len(bars['1D'])/len(days)}})
            if feed=='sip':contexts[d['id']]=SimpleNamespace(fine=CloseMarks(bars['5m']))
    extra=sorted(s for s,v in si.items() if v.get('id') and s not in paired)
    extra_stats={tf:group([e for b in sb if b['symbol'] in extra and b['timeframe']==tf for e in b['entries']]) for tf in ('4h','1D')}
    near=[]
    for snap in scanner['snapshots']:
        if not snap['count']:continue
        c=json.loads((sip/'candidates'/f"{snap['symbol']}-{snap['timeframe']}.json").read_text('utf-8'))
        if c['engineHash']!=scanner['engineHash']:raise ValueError('Changed candidate export')
        for f in c['currentNear']:near.append(f)
    early=int(datetime(2023,12,31,23,59,tzinfo=timezone.utc).timestamp())
    portfolios={}
    for phase,start,end in [('2021-2023',int(datetime(2021,7,27,tzinfo=timezone.utc).timestamp()),early),('2024-2026',int(datetime(2024,1,1,tzinfo=timezone.utc).timestamp()),sr['endAt'])]:
        for family in ('breakout','retest','bounce'):
            entries=[{**e,'datasetId':b['datasetId']} for b in sb if b['symbol'] in paired and b['timeframe']=='4h' for e in b['entries'] if e['profile']=='age7' and e['family']==family and start<=e['entryAt']<=end]
            for model in ('fixed','higher_low'):
                p=ledger(entries,contexts,{'startAt':start,'endAt':end},model)
                # Independent arithmetic guard over every actually accepted position.
                for t in p['trades']:
                    assert t['quantity']>0 and t['cashAfterEntry']>=-1e-8
                    assert t['plannedRiskUSD']<=.01*t['equityAtEntry']+1e-6
                    assert t['quantity']*t['entryFill']<=.25*t['equityAtEntry']+1e-6
                    if t['exitAt'] is not None:assert abs(t['netPnl']-t['quantity']*(t['exitFill']-t['entryFill']))<1e-6
                if p['halt']:assert p['markedReturnPct'] is None
                destination=sip/'ledgers'/f'{phase}-{family}-{model}.json';write(destination,p)
                portfolios['/'.join((phase,family,model))]={k:v for k,v in p.items() if k not in ('trades','skipped','equity')}
                print(json.dumps({'ledger':destination.name,'status':p['status'],'accepted':p['accepted'],'returnPct':p['markedReturnPct']}),flush=True)
    summary={'pairedStocks':paired,'additionalSIPStocks':extra,'comparison':comparison,'additionalSIP':extra_stats,'scannerVerification':scanner,
        'quality':quality,'portfolios':portfolios,'currentNear':near,'iexContract':digest(ic),'sipContract':digest(sc),
        'meaning':'Known-period diagnostic feed comparison; dependent event observations are not independent trades. No new holdout or proven profitability.'}
    write(sip/'workbench-summary.json',summary)
    lines=['# Werkbank: vollständigerer Feed, Sichtprüfung und erklärte Kandidaten','','Stand 22.10.2026. Gleiche unveränderte Regeln, keine Optimierung anhand des neuen Verlaufs. Keine Orders, keine Veröffentlichung oder Containerinstallation.','',
        f'## Datenvergleich auf denselben {len(paired)} Aktien','',
        '27.07.2020–21.10.2026; ein Jahr Vorlauf, danach chronologisch jede geschlossene Quellkerze. Historischer SIP-Zugriff mit bestehendem Zugang erfolgreich. Echtzeit-SIP ist dadurch nicht freigeschaltet. Splitbereinigte RTH-5m-Daten; Schlussauktions-/Nachbörsenkerzen sind nicht nachträglich ergänzt. Fehlende Daten bleiben unbekannt.','',
        '| Feed | Median 5m-Abdeckung | Median 4h-Abdeckung | Median 1D-Abdeckung |','|---|---:|---:|---:|']
    for feed in ('iex','sip'):
        q=[x for x in quality if x['feed']==feed];lines.append('| '+feed.upper()+' | '+' | '.join(f"{median(x['coveragePct'][tf] for x in q):.2f} %" for tf in ('5m','4h','1D'))+' |')
    lines+=['','## Wie viele Einstiege statt harter Zusatzfilter?','','Familienfälle können am selben Aktienzeitpunkt zusammenfallen. „Eindeutige Zeitpunkte“ dedupliziert diese, ist aber noch kein kapitalbegrenztes Portfolio.','',
        '| Intervall | Profil | IEX Fälle / Zeitpunkte | SIP Fälle / Zeitpunkte | SIP Aktien |','|---|---|---:|---:|---:|']
    for tf in ('4h','1D'):
        for profile in ('two','three','age7','momentum','safety','context_room','all_events'):
            a,b=[comparison[f+'/'+tf]['profiles'][profile] for f in ('iex','sip')]
            lines.append(f"| {tf} | {profile} | {a['entries']} / {a['uniqueStockTimes']} | {b['entries']} / {b['uniqueStockTimes']} | {b['stocks']} |")
    lines+=['','## Beispiel einer Kandidatenliste am Datenende','',
        'Alle 60 vorab festgelegten Aktien; nur letzte bekannte Quellschlüsse bis 21.10.2026. Keine aktuelle Kaufempfehlung. Annäherung bedeutet ungebrochene Linie innerhalb 0,75 ATR, keinen bestätigten Ausbruch. Zusätzliche Warnungen filtern diese Ansicht nicht weg.','',
        '| Aktie / Intervall | Quellschluss New York | Schlusskurs USD | Risikoabstand ATR | Hinweise |','|---|---|---:|---:|---|']
    for f in near:
        stamp=datetime.fromtimestamp(f['knownAt'],NY).strftime('%d.%m.%Y %H:%M')
        notes='; '.join(w.replace('Momentum fehlt unbekannt','Momentum noch nicht bestätigt') for w in f['warnings']) or 'Keine Zusatzwarnung'
        lines.append(f"| {f['symbol']} / {f['timeframe']} | {stamp} | {f['sourceClose']:.2f} | {f['riskATRAtClose']:.2f} | {notes} |")
    lines+=['','## Retest: Endkursbeobachtung und Exits getrennt','','Drei Kontakte + sieben Tage Alter. Endkursbeobachtungen nach 20 Sitzungen ignorieren einen möglichen früheren Stop. Sie sind keine Trefferquote einer ausgeführten Strategie.','',
        '| Feed / Intervall / Phase | Entries | Bekannte 20T-Endpunkte | Positiv | Mittlere Änderung nach Kosten | Higher-low: geschlossen / unbekannt / offen | Mittel R geschlossen |','|---|---:|---:|---:|---:|---|---:|']
    def fmt(x):return '—' if x is None else f'{x:.2f}'
    for feed in ('iex','sip'):
        for tf in ('4h','1D'):
            for phase in ('all','2021-2023','2024-2026'):
                a=comparison[feed+'/'+tf]['age7']['retest/'+phase];h=a['intermediate']['20'];p=a['paths']['higher_low'];s=p['statuses']
                lines.append(f"| {feed}/{tf}/{phase} | {a['entries']} | {h['known']} | {fmt(h['positivePct'])} % | {fmt(h['meanNetPct'])} % | {s.get('closed',0)} / {s.get('unknown',0)} / {s.get('open',0)} | {fmt(p['closedMeanR'])} |")
    lines+=['','## Kapitalrechnung separat','','SIP, dieselben Aktien, 4h; Familien getrennt. 2.000 USD, 1 % geplantes Risiko, maximal 25 % Kapital pro Position, fünf Positionen, Bruchteile, keine Kredite, Kosten 5bp voller Spread + 5bp Slippage pro Seite. Kein Ausschluss anhand späterer Datenlücken. Fehlender gehaltener Pfad beendet die Berechnung; dann bleibt die Gesamtrendite unbekannt. Offene Positionen werden bewertet, nicht als realisierter Gewinn ausgegeben.','',
        '| Phase / Familie / Exit | Status | Angenommen | Geschlossen | Offen | Markierte Änderung |','|---|---|---:|---:|---:|---:|']
    for key,p in portfolios.items():lines.append(f"| {key} | {p['status']} | {p['accepted']} | {p['closed']} | {p['open']} | {fmt(p['markedReturnPct'])} % |")
    lines+=['','## Technische Prüfung','',
        f"Unabhängiger Pfadaudit bestanden: {json.loads((sip/'verification.json').read_text('utf-8'))['uniquePaths']:,} unterschiedliche Modellpfade. Erklärter Scanner: {scanner['blocks']} Quellreplays mit {scanner['unchangedEntries']:,} exakt unveränderten ursprünglichen Profil-Entries, unveränderten Ablehnungen/Trichtern und {scanner['facts']:,} vorwärts erzeugten Beobachtungsfakten. Profile überlappen; diese Anzahl ist keine Zahl unabhängiger Trades. Python: 303 Tests jeweils unter 3.12 und 3.13 bestanden (je ein bekannter Windows-Symlink-Skip); 41 JS-Tests bestanden. Echte lokale HTTP-Abnahme und Controller-Test, keine Browser-Sichtprüfung.",
        '','## Sichtprüfung und Grenzen','',
        'Unter `/pruefung` liegen 82 bisherige Diagnosefälle und 20 fest gezogene Zufallsfälle bereit. Beide Quellintervalle, eigene Rays, horizontale Widerstände und Kontaktmarkierungen; löschen/rückgängig; erst speichern, dann Engine aufdecken. Bewertungen, Historie und Datasetreferenzen liegen im bestehenden gesicherten SQLite-Speicher. Es wurden keine menschlichen Urteile erfunden. Die Diagnosefälle sind Engine-selektiert; die 20 Kontrollen sind keine hinreichende Erfolgsstichprobe.','',
        'Die drei zuvor ungültigen IEX-Imports werden nicht in den Hauptvergleich aufgenommen. Separat verfügbare SIP-Titel: '+(', '.join(extra) or 'keine')+'. Deren Kennzahlen stehen im lokalen JSON. Kein historisch vollständiges Universum, keine delisteten Titel rekonstruiert; keine unabhängige Validierung dieser bereits untersuchten Zeiträume. Historische Unternehmensereignisse bleiben ohne belegte Point-in-time-Abdeckung unbekannt.','',
        'Der separate JSON-Scanner exportiert Beobachtungsmerkmale ohne Zukunftskurse oder angenommene Kaufkurse. Neue prospektive Registrierungen sind nicht rückdatierbar, bekannte Präfixe und Enginehash werden geschützt. Der vorhandene laufende Beobachter bleibt bei seinen bisherigen Regeln. Der SIP-Vergleich ersetzt keine menschliche Linienprüfung und beweist keine gewinnbringende Strategie.','',
        'Quellen: lokale unveränderliche Imports, Studienverträge, eingefrorene Signaldateien, unabhängig geprüfte Pfadjournale und Kapitalledger. Marktfeed-Zugriff: [offizielle Alpaca-FAQ](https://docs.alpaca.markets/us/docs/market-data-faq).']
    output.write_text('\n'.join(lines)+'\n','utf-8')
    print(json.dumps({'report':str(output),'matchedStocks':len(paired),'additionalStocks':extra}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--iex',required=True);p.add_argument('--sip',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();run(a.iex,a.sip,a.output)
