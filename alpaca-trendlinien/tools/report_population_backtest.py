"""Describe a verified population replication, never select or optimize trades."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from event_case_study import checked as source_plan, load_block
from exit_followup import checked, load_followup, POLICIES
from strategy_screen import read,write

FAMILIES={'breakout':'Ausbruch','red_retest':'Roter Retest','safety_bounce':'Safety-Bounce'}
MODELS={'fixed':'Fest','original_safety':'Ursprüngliche Safety','fan_safety':'Aktuelle Safety',
        'qualified_fan':'Nur qualifizierte neue Safety','r2_fan':'Neue Safety erst ab +2R'}


class Bucket:
    def __init__(self):
        self.signals=0;self.status=Counter();self.entries=Counter()
        self.closed=[];self.open=[];self.rs=[];self.symbols=set()
    def add(self,c,p):
        self.signals+=1;self.status[p['status']]+=1;self.entries[c['entry']['status']]+=1
        self.symbols.add(c['symbol'])
        if p['status']=='closed':self.closed.append(p['netReturnPct']);self.rs.append(p['netR'])
        if p['status']=='open':self.open.append(p['markNetReturnPct'])
    def summary(self):
        closed=self.closed;vals=closed+self.open
        return {'signals':self.signals,'stocks':len(self.symbols),'filled':self.entries['filled'],
            'closed':len(closed),'wins':sum(x>0 for x in closed),'losses':sum(x<0 for x in closed),
            'flat':sum(x==0 for x in closed),'open':len(self.open),'censored':self.status['censored'],
            'noFill':self.signals-self.entries['filled'],'openPositive':sum(x>0 for x in self.open),
            'winPctClosed':100*sum(x>0 for x in closed)/len(closed) if closed else None,
            'meanClosedPct':statistics.mean(closed) if closed else None,
            'medianClosedPct':statistics.median(closed) if closed else None,
            'meanWinnerPct':statistics.mean(x for x in closed if x>0) if any(x>0 for x in closed) else None,
            'meanLoserPct':statistics.mean(x for x in closed if x<0) if any(x<0 for x in closed) else None,
            'meanOpenPct':statistics.mean(self.open) if self.open else None,
            'meanValuedPct':statistics.mean(vals) if vals else None,
            'medianValuedPct':statistics.median(vals) if vals else None,
            'meanClosedR':statistics.mean(self.rs) if self.rs else None,
            'medianClosedR':statistics.median(self.rs) if self.rs else None,
            'worstClosedPct':min(closed) if closed else None,'bestClosedPct':max(closed) if closed else None,
            'meanValuedWithoutBest3':statistics.mean(sorted(vals,reverse=True)[3:]) if len(vals)>3 else None}


def csv_write(path,rows,fields=None):
    with Path(path).open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields or list(rows[0]));writer.writeheader();writer.writerows(rows)


def fmt(v):return '—' if v is None else f'{v:.2f}'
def iso(at):return datetime.fromtimestamp(at,timezone.utc).isoformat() if at is not None else ''


def report(root,destination):
    root=Path(root);p=checked(read(root/'plan.json'));sr=Path(p['sourceRoot']);sp=source_plan(read(sr/'plan.json'))
    assert p['sourcePlanId']==sp['id']
    for folder,identity in ((root,p['id']),(sr,sp['id'])):
        proof=read(folder/'verification.json');assert proof['passed'] and proof['planId']==identity
    pop=read(sr/'population.json');assert pop['planId']==sp['id']
    members={k:{m['symbol'] for m in u['members']} for k,u in pop['universes'].items()}
    membership={s:[k for k,ss in members.items() if s in ss] for s in p['symbols']}
    universe=defaultdict(Bucket);stocks=defaultdict(Bucket);windows=defaultdict(Bucket);common=defaultdict(Bucket)
    best=[];worst=[];all_ids=set();pairs=set();suppressed=0;eligible={};controls=0;coverage={}
    columns=['caseId','episodeId','symbol','universes','window','family','cohort','policy','signalAtUTC','entryAtUTC',
        'entryStatus','entryPrice','initialStop','stopDistancePct','stopDistanceATR4h','status','exitAtUTC','exitPrice',
        'exitReason','netReturnPct','netR','openMarkPct','valuationAtUTC','mfeR','maeR','holdingCalendarDays']
    with (root/'trades-by-universe.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader()
        for s in p['symbols']:
            b=load_block(sr,sp,s);f=load_followup(root,p,s)
            assert f['sourceChecksum']==b['checksum'] and f['caseIds']==[c['id'] for c in b['cases']]
            eligible[s]=b['eligibility'];suppressed+=len(b['suppressed'])
            coverage[s]={'signals':len(b['cases']),'filled':sum(c['entry']['status']=='filled' for c in b['cases']),
                         'sourceGaps4h':b.get('diagnostics',{}).get('sourceGaps')}
            if 'reusedFrom' in b:controls+=1
            for c in b['cases']:
                assert c['id'] not in all_ids;all_ids.add(c['id'])
                pair=(c['signal']['episodeId'],c['signal']['family']);assert pair not in pairs;pairs.add(pair)
                paths={**c['paths'],**f['newPaths'][c['id']]};sig=c['signal'];e=c['entry']
                if e['status']!='filled':assert all(path['status']==e['status'] for path in paths.values())
                jointly=all(paths[m]['status'] in ('closed','open') for m in POLICIES if m!='fixed')
                for model in POLICIES:
                    path=paths[model];group=(sig['family'],sig['cohort'],model)
                    for u in ['ALL',*membership[s]]:universe[(u,*group)].add(c,path)
                    stocks[(s,*group)].add(c,path);windows[(c['window'],*group)].add(c,path)
                    if jointly and model!='fixed':common[group].add(c,path)
                    row={'caseId':c['id'],'episodeId':sig['episodeId'],'symbol':s,'universes':'|'.join(membership[s]),
                        'window':c['window'],'family':sig['family'],'cohort':sig['cohort'],'policy':model,
                        'signalAtUTC':iso(sig['signalAt']),'entryAtUTC':iso(e.get('entryAt')),'entryStatus':e['status'],
                        'entryPrice':e.get('entryPrice'),'initialStop':e.get('initialStop'),
                        'stopDistancePct':c['features'].get('stopDistancePct'),'stopDistanceATR4h':c['features'].get('stopDistanceATR4h'),
                        'status':path['status'],'exitAtUTC':iso(path.get('exitAt')),'exitPrice':path.get('exitPrice'),
                        'exitReason':path.get('reason'),'netReturnPct':path.get('netReturnPct'),'netR':path.get('netR'),
                        'openMarkPct':path.get('markNetReturnPct') if path['status']=='open' else None,
                        'valuationAtUTC':iso(path.get('exitAt') or path.get('lastObservedAt')),
                        'mfeR':path.get('mfeR'),'maeR':path.get('maeR'),'holdingCalendarDays':path.get('holdingCalendarDays')}
                    writer.writerow(row)
                    if sig['cohort']=='qualified' and model=='fan_safety' and path['status']=='closed':
                        best=sorted([*best,row],key=lambda x:x['netReturnPct'],reverse=True)[:10]
                        worst=sorted([*worst,row],key=lambda x:x['netReturnPct'])[:10]
    groups={k:v.summary() for k,v in universe.items()};stockgroups={k:v.summary() for k,v in stocks.items()}
    windowgroups={k:v.summary() for k,v in windows.items()};pairedgroups={k:v.summary() for k,v in common.items()}
    # Independent flat-export accounting: separate parser, denominators and sums.
    audit=defaultdict(Counter);csv_count=0;csv_ids=set()
    with (root/'trades-by-universe.csv').open(encoding='utf-8-sig',newline='') as stream:
        for row in csv.DictReader(stream):
            csv_count+=1;key=(row['caseId'],row['policy']);assert key not in csv_ids;csv_ids.add(key)
            for u in ['ALL',*row['universes'].split('|')]:
                a=audit[(u,row['family'],row['cohort'],row['policy'])];a['signals']+=1;a[row['status']]+=1
                a['filled']+=row['entryStatus']=='filled'
                if row['status']=='closed':
                    x=float(row['netReturnPct']);a['closedSum']+=x;a['wins']+=x>0;a['losses']+=x<0;a['flat']+=x==0
                if row['status']=='open':a['openSum']+=float(row['openMarkPct'])
    assert csv_count==len(all_ids)*len(POLICIES)
    for key,target in groups.items():
        a=audit[key]
        for n in ('signals','filled','closed','wins','losses','flat','open','censored'):assert target[n]==a[n],(key,n)
        if target['closed']:assert math.isclose(target['meanClosedPct'],a['closedSum']/a['closed'],abs_tol=1e-10)
        if target['closed']+target['open']:
            assert math.isclose(target['meanValuedPct'],(a['closedSum']+a['openSum'])/(a['closed']+a['open']),abs_tol=1e-10)
    def table_rows(source,labels):return [{**dict(zip(labels,key)),**value} for key,value in sorted(source.items())]
    csv_write(root/'universe-summary.csv',table_rows(groups,('universe','family','cohort','policy')))
    csv_write(root/'stock-summary.csv',table_rows(stockgroups,('symbol','family','cohort','policy')))
    csv_write(root/'window-summary.csv',table_rows(windowgroups,('window','family','cohort','policy')))
    csv_write(root/'largest-winners.csv',best,columns);csv_write(root/'largest-losers.csv',worst,columns)
    excluded={v['symbol']:v['reason'] for v in pop['excluded']}
    roster=[]
    for s in sorted(set.union(*members.values())):
        row={'symbol':s,'universes':'|'.join(u for u,ss in members.items() if s in ss),
            'eligibleAny':s in coverage,**{w['name']:eligible.get(s,{}).get(w['name'],False) for w in p['windows']},
            **coverage.get(s,{'signals':0,'filled':0,'sourceGaps4h':None}),
            'reason':excluded[s] if s in excluded else ('no_deduplicated_signal_in_selected_windows' if not coverage[s]['signals'] else '')}
        roster.append(row)
    csv_write(root/'coverage.csv',roster)
    existing=read(root/'results.json');assert existing['planId']==p['id'] and existing['cases']==len(all_ids)
    for (_,family,cohort,model),v in [(k,v) for k,v in groups.items() if k[0]=='ALL']:
        old=existing['groups'][family+':'+cohort][model]
        assert old['signals']==v['signals'] and old['wins']==v['wins'] and old['losses']==v['losses']
        for a,b in (('meanNetReturnPct','meanClosedPct'),('meanTerminalPct','meanValuedPct')):
            assert old[a] is v[b] is None or old[a] is not None and v[b] is not None and math.isclose(old[a],v[b],abs_tol=1e-10)
    lines=['# Entry-/Exit-Backtest auf drei Universen – 01.11.2026','',
        f"**{len(p['symbols'])} Aktien, {len(all_ids):,} eingefrorene Signalfälle, {suppressed:,} Wiederholungssignale unterdrückt.**",
        'Dow Jones, Nasdaq-100 und S&P 500 als gespeicherte ETF-Bestände vom 28.10.2026. Ihre Vereinigung enthält 520 Aktienklassen; acht junge Bestände haben in keinem Fenster genügend Vorlauf. Alle Zeitfenster und Regeln wie zuvor.',
        '', 'Entries: 2018, 2021, 2023 und April 2025 bis März 2026. Nachbeobachtung bis '+iso(p['cutoff'])+'.',
        'Je Fall 1.000 USD nominal/fraktional; unveränderte Kosten und 5m-Ausführung. Keine Depot-/Slotsperren, Tagesexits oder Take Profits. [Vorabregeln](BACKTEST-UNIVERSEN-PLAN-20261101.md).',
        '', '**Alle Prozentwerte sind Nettoergebnisse einzelner Signalfälle, keine Depot- oder Indexrenditen.** Gewinner/Verlierer zählen nur geschlossene Pfade. Offene Buchwerte und unbekannte Datenlücken bleiben getrennt. Universen und Familien überlappen; ihre Zahlen nicht addieren.',
        '', '## Qualifizierte Signale: fünf Exitvarianten','',
        '| Einstieg | Exit | Signale | Gefüllt | Geschlossen | Gewinner | Verlierer | Offen | Lücke | Treffer % geschlossen | Ø geschlossen % | Median geschlossen % | Ø geschlossen + offen % |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for family in FAMILIES:
        for model in POLICIES:
            v=groups.get(('ALL',family,'qualified',model))
            if v:lines.append(f"| {FAMILIES[family]} | {MODELS[model]} | {v['signals']} | {v['filled']} | {v['closed']} | {v['wins']} | {v['losses']} | {v['open']} | {v['censored']} | {fmt(v['winPctClosed'])} | {fmt(v['meanClosedPct'])} | {fmt(v['medianClosedPct'])} | {fmt(v['meanValuedPct'])} |")
    lines+=['','Fester Stop kann Gewinne nicht regulär schließen. Daher ist seine geschlossene Trefferquote kein fairer alleiniger Vergleich mit nachgezogenen Stops. Nullfälle sind in den CSVs separat enthalten.',
        '', '## Universen: aktuelle Safety, qualifizierte Entries','',
        '| Universum | Lokale Titel | Geeignet | Einstieg | Signale | Geschlossen | Gewinner | Verlierer | Offen | Lücke | Ø geschlossen % | Ø inkl. offener Buchwerte % |',
        '|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for u,ss in members.items():
        for family in FAMILIES:
            v=groups.get((u,family,'qualified','fan_safety'))
            if v:lines.append(f"| {pop['universes'][u]['name']} | {len(ss)} | {len(ss&set(p['symbols']))} | {FAMILIES[family]} | {v['signals']} | {v['closed']} | {v['wins']} | {v['losses']} | {v['open']} | {v['censored']} | {fmt(v['meanClosedPct'])} | {fmt(v['meanValuedPct'])} |")
    lines+=['','## Identische bewertbare Fälle aller vier nachgezogenen Safetys','',
        'Hier müssen alle vier Varianten geschlossen oder offen sein. Keine Auswahl nach Vorzeichen; Datenlückenzensierung kann diese gemeinsame Teilmenge dennoch verzerren.', '',
        '| Einstieg / Klasse | Exit | Gemeinsam bewertbar | Ø Bewertung % | Median Bewertung % | Ø ohne beste drei % |',
        '|---|---|---:|---:|---:|---:|']
    for (family,cohort,model),v in sorted(pairedgroups.items()):
        lines.append(f"| {FAMILIES[family]} / {cohort} | {MODELS[model]} | {v['closed']+v['open']} | {fmt(v['meanValuedPct'])} | {fmt(v['medianValuedPct'])} | {fmt(v['meanValuedWithoutBest3'])} |")
    lines+=['','## Aktien: aktuelle Safety, qualifizierte Entries','',
        'Alle drei Familien je Aktie zusammen, einschließlich ihrer Abhängigkeiten. Sortiert nach mittlerem geschlossenem Nettoergebnis; Stichprobengröße ausdrücklich gezeigt. Nachträgliche Beschreibung, keine Gewinnerauswahl als Handelsregel.', '',
        '| Aktie | Universen | Geschlossen | Gewinner | Verlierer | Offen | Lücke | Ø geschlossen % | Median geschlossen % |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    perstock=defaultdict(Bucket)
    # Merge original observations, not already averaged stock/family percentages.
    for (s,family,cohort,model),bucket in stocks.items():
        if cohort=='qualified' and model=='fan_safety':
            b=perstock[s];b.closed.extend(bucket.closed);b.open.extend(bucket.open);b.status.update(bucket.status)
            b.signals+=bucket.signals;b.entries.update(bucket.entries);b.symbols.update(bucket.symbols);b.rs.extend(bucket.rs)
    overview=[{'symbol':s,'universes':'|'.join(u for u,ss in members.items() if s in ss),
               'eligibleAny':s in coverage,'families':'all_three','cohort':'qualified','policy':'fan_safety',
               **perstock[s].summary()} for s in sorted(set.union(*members.values()))]
    csv_write(root/'stock-overview.csv',overview)
    ranking=sorted([(s,b.summary()) for s,b in perstock.items() if b.closed],key=lambda item:item[1]['meanClosedPct'],reverse=True)
    for s,v in (ranking if len(ranking)<=20 else ranking[:10]+ranking[-10:]):
        lines.append(f"| {s} | {', '.join(membership[s])} | {v['closed']} | {v['wins']} | {v['losses']} | {v['open']} | {v['censored']} | {fmt(v['meanClosedPct'])} | {fmt(v['medianClosedPct'])} |")
    for title,rows in [('Größte geschlossene Gewinner',best),('Größte geschlossene Verlierer',worst)]:
        lines+=['', '## '+title,'','Referenz wie oben: qualifizierte Entries und aktuelle Safety, keine Auswahl des besten Exitmodells je Trade.','',
            '| Aktie | Entrytyp | Entry UTC | Exit UTC | Netto % | Netto R |', '|---|---|---|---|---:|---:|']
        for row in rows:lines.append(f"| {row['symbol']} | {FAMILIES[row['family']]} | {row['entryAtUTC']} | {row['exitAtUTC']} | {fmt(row['netReturnPct'])} | {fmt(row['netR'])} |")
    lines+=['','## Dateien, Kontrolle und Grenzen','',
        f"Privater Studienordner: `{root.as_posix()}`. Plan-ID `{p['id']}`. {controls} unveränderte Kontrollaktien, {len(p['symbols'])-controls} neu berechnete Aktien. CSV-Abgleich aller {csv_count:,} Modellzeilen und Universumszähler bestanden.",
        'Sortierbare Dateien: `trades-by-universe.csv` (jede Fall-/Modellkombination einmal, mit Entry/Exit/Stop/Prozenten/R), `universe-summary.csv`, `stock-summary.csv`, `window-summary.csv`, `largest-winners.csv`, `largest-losers.csv`. `stock-overview.csv` bietet eine Zeile je Titel für qualifizierte Entries mit aktueller Safety; `stock-summary.csv` trennt zusätzlich Familien/Kontaktklassen/Modelle. `coverage.csv` enthält alle 520 Titel einschließlich Ausschlüssen und geeigneten Aktien ohne Signal. Alle Kontaktklassen und Modelle bleiben in den Detaildateien enthalten, auch ohne Gewinn oder Fill.',
        'Bekannte heutige Überlebendenbestände, bereits untersuchte Zeiträume und abhängige Episoden: keine unabhängige Strategiebestätigung. Dividenden, Steuern, FX und historische Kapitalmaßnahmen sind nicht vollständig als handelbares Ganzaktienportfolio abgebildet. Unbekannte Datenlücken können selektiv sein; offene Buchwerte sind keine realisierten Gewinne. Keine neue Providerabfrage, Order, Meldung, Webänderung oder Containerinstallation.', '']
    Path(destination).write_text('\n'.join(lines),encoding='utf-8')
    result={'planId':p['id'],'stocks':len(p['symbols']),'cases':len(all_ids),'csvRows':csv_count,'csvAuditPassed':True,
        'groups':table_rows(groups,('universe','family','cohort','policy')),
        'common':table_rows(pairedgroups,('family','cohort','policy')),
        'eligibleStocksWithoutSignals':[s for s,v in coverage.items() if not v['signals']],
        'eligibleByWindow':{w['name']:sum(e[w['name']] for e in eligible.values()) for w in p['windows']},
        'reportSha256':hashlib.sha256(Path(destination).read_bytes()).hexdigest()}
    write(root/'population-report.json',result)
    return {k:result[k] for k in ('planId','stocks','cases','csvRows','csvAuditPassed')}


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('root');ap.add_argument('--output',required=True);a=ap.parse_args()
    print(json.dumps(report(a.root,a.output)),flush=True)
