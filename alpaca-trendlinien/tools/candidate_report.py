"""Write the candidate study conclusions from validated local evidence."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def run(root,output):
    root=Path(root);s=json.loads((root/'summary.json').read_text('utf-8'))
    v=json.loads((root/'candidate-verification.json').read_text('utf-8'))
    cash=json.loads((root/'cash-summary.json').read_text('utf-8'))
    assert v['passed'] and v['contractHash']==s['contractHash']==cash['contractHash']
    rs=[r for p in (root/'stocks').glob('*.json') for r in json.loads(p.read_text('utf-8'))['records']]
    def f(x):return 'unbekannt' if x is None else f'{x:.3f}'
    lines=['# Kandidatenversuch – Ergebnis und Grenzen (22.10.2026)','',
      '## Was umgesetzt wurde','',
      '- Vor der Auswertung gespeicherter Versuchsplan und feste Daten-/Engine-Bindung.',
      '- 20 zufällige SIP-Präfixe für die blinde Linienprüfung in der vorhandenen Sichtprüfung. Keine menschlichen Bewertungen erfunden.',
      '- Merkmale und fünf vor Ergebnisbetrachtung gespeicherte Zufallskontrollen je geeignetem Retest; 5/10/20 Handelstage sowie fixierte und nachgezogene Safety.',
      '- Separate Kandidatenansicht mit Originalankern, zusammengefassten ähnlichen Geometrien, Zuständen und Warnungen. Eine ähnliche Variante darf das Signal der ursprünglichen Linie nicht umbenennen.',
      '- 28 Kapitalledger mit denselben Kosten und Risikobudgets; fünf separate Kontrolldepots statt fünffachem Kapitaleinsatz.',
      '- Getrennter prospektiver SIP-Beobachter mit Registrierung, Revisionserkennung, Wiederaufnahme, paginiertem Journal, Importbudget und CLI/API. Der alte IEX-Beobachter bleibt unverändert.','',
      '## Grundgesamtheit und Methode','',
      f'{len(rs)} 4h-Retests in 60 Aktien; {len({(r["symbol"],r["entryAt"]) for r in rs})} eindeutige Aktie/Einstiegszeit-Kombinationen. Die gemeinsame Vergleichsmenge mit dem früheren IEX-Versuch umfasst {v["matchedOldUniverseEntries"]} Retests in 57 Aktien. CRM, KO und LOW werden nur aus diesem zusätzlichen Feedvergleich herausgehalten, nicht aus der vorab festgelegten SIP-Hauptgruppe.',
      '', 'Daten: SIP, splitbereinigt, reguläre XNYS-Sitzungen, 5m-Ausführungspfad; Rohhistorie ab 27.07.2020, ein Jahr Vorlauf, Untersuchung bis 21.10.2026. Es handelt sich um bereits untersuchte Zeiträume und ein heutiges Aktienuniversum. Delistete Titel und ein historisch vollständiges Universum fehlen.',
      '', 'Das age7-Profil verlangt mindestens drei unabhängige Reaktionen an der Aktionslinie, zwei an der Safety und sieben Tage Alter. Momentum, Safety-Abstand, Kontext, Raum und Unternehmensereignisse werden zusätzlich als Merkmale/Warnungen erfasst. Dies ist ausdrücklich keine Behauptung, dass alle Tori-Filter bei jedem der 349 Einstiege erfüllt waren.',
      '', 'Kontrollen: gleiche Aktie, New-York-Uhrzeit, Kalenderquartal und Seite des damals bekannten MA20; mindestens 20 Handelstage vom Original entfernt. Aus den 20 nächsten bekannten ATR/Kurs-Nachbarn werden bis zu fünf mit festem Zufallsseed ausgewählt. Der anfängliche prozentuale Stoppabstand wird übertragen. Die horizontale grüne Kontrollreferenz ist kein nachträglich entdeckter Trend.',
      '', 'Kontrollen sind rückblickende Vergleichsfälle und können innerhalb des Quartals vor oder nach dem Signal liegen. Ihre späteren Ergebnisse oder Datenlücken beeinflussen die Auswahl nicht. Die Methode isoliert keinen kausalen Effekt. Fehlende ganze Panels werden ausgewiesen; sie können trotzdem verbleibenden Auswahlbias verursachen.',
      '', 'Kosten je Seite: 0,075 % (halber 5-bp-Spread und 5 bp Slippage), keine Ordergebühr. 5/10/20 bedeutet folgende reguläre Handelssitzungen nach dem Einstiegstag. Kursentwicklung ignoriert einen vorherigen Stopp; Stoppmodelle schließen beim simulierten Stopp oder bewerten eine noch offene Position am Horizont. Diese Horizonte sind keine neu eingeführten Tori-Take-Profits.','',
      '## Vorab festgelegter Hauptvergleich','',
      '| Horizont | Bewertung | Bekannte Originale / 349 | Vollständige 5er-Panels | Vorteil gegenüber Kontrollen | Beschreibendes Unsicherheitsband |',
      '|---|---|---:|---:|---:|---|']
    for h in ('5','10','20'):
        for kind,label,unit in [('market','Kursentwicklung','pp'),('fixed','Fixierte Safety','R'),('higher_low','Bestätigte höhere Tiefs','R')]:
            m=s['groups']['all']['horizons'][h][kind];i=m['interval']
            lines.append(f'| {h} | {label} | {m["knownEntries"]} / 349 | {m["pairedPanels"]} | {f(m["meanExcess"])} {unit} | {f(i["low"])} bis {f(i["high"])} {unit} |')
    lines+=['','Der primäre 20-Tage-Kursvergleich liegt positiv. Der entsprechende Vorteil unter fixierter Safety beträgt rund 0,307 R; bei nachgezogenen höheren Tiefs umfasst das Band null. Das bedeutet einen interessanten historischen Befund, keinen validierten handelbaren Vorteil. Die Bänder sind die Hülle separater Aktien- und Quartals-Cluster-Bootstraps mit 500 festen Ziehungen, ohne Korrektur für viele Vergleiche und ohne garantierte Abdeckung. Überlappende Fälle sind keine unabhängigen Trades.','',
      '## Stabilität zwischen den Zeitphasen','',
      '| Phase | Fälle | 20-Tage-Bewertung | Panels | Vorteil | Band |','|---|---:|---|---:|---:|---|']
    for phase in ('2021-2023','2024-2026'):
        g=s['groups'][phase]
        for kind,unit in [('market','pp'),('fixed','R'),('higher_low','R')]:
            m=g['horizons']['20'][kind];i=m['interval']
            lines.append(f'| {phase} | {g["entries"]} | {kind} | {m["pairedPanels"]} | {f(m["meanExcess"])} {unit} | {f(i["low"])} bis {f(i["high"])} |')
    lines+=['','Der Vorteil ist in der frühen Phase deutlich stärker. In 2024–2026 umfassen alle drei 20-Tage-Vergleichsbänder null. Deshalb wird daraus kein automatisch optimierter Gewinn-Score und kein neuer harter Filter abgeleitet.','',
      '## Merkmale: Hinweise statt nachträglicher Optimierung','',
      '| Vorbekanntes Merkmal | Fälle | Panels, fixierte Safety 20 Tage | Mittlere Originalbewertung (R) | Vorteil (R) |','|---|---:|---:|---:|---:|']
    for key,g in s['groups'].items():
        if key.startswith('all/'):
            m=g['horizons']['20']['fixed'];lines.append(f'| {key[4:]} | {g["entries"]} | {m["pairedPanels"]} | {f(m["meanActual"])} | {f(m["meanExcess"])} |')
    lines+=['','Mehr Kontakte, engerer Safety-Abstand, Momentum oder der vorhandene Raumfilter verbessern die Ergebnisse hier nicht durchgehend. Die kleinen Untergruppen und die wechselnden Phasen verbieten eine belastbare Rangfolge. Insbesondere wird ein großer Safety-Abstand nicht deshalb als gut erklärt, weil seine rückblickende Untergruppe besser abschneidet. Die Merkmale bleiben sichtbar und Warnungen bleiben bestehen. Unternehmensereignisse haben keine verifizierte Point-in-time-Abdeckung und sind unbekannt.','',
      '## Kapital und Exits','',
      'Annahmen: 2.000 USD, 1 % geplantes Risiko je Position, höchstens 25 % Kapitaleinsatz je Position, fünf gleichzeitige Positionen, Bruchteile, eine Position je Aktie. Abgelehnte Einstiege und gleichzeitig belegtes Kapital bleiben Teil der Simulation. Ein fehlender Kurs in einer gehaltenen Position stoppt weitere Depotentscheidungen. Offene Schlussbewertungen sind keine realisierten Gewinne.','',
      '| Phase / Gruppe | Exit | Status | Angenommen / offen | Gesamte Depotbewertung (%) | Realisierter P/L (USD) |','|---|---|---|---:|---:|---:|']
    for x in cash['items']:
        lines.append(f'| {x["phase"]} / {x["cohort"]} | {x["model"]} | {x["status"]} | {x["accepted"]} / {x["open"]} | {f(x["markedReturnPct"])} | {f(x["realizedNetPnl"])} |')
    lines+=['',f'{sum(x["status"]=="incomplete" for x in cash["items"])} von 28 Depots sind unvollständig. Diese werden nicht aus der Bewertung gelöscht und bekommen keinen Gesamtertrag. Das volle Retest-Depot 2024–2026 mit fixierter Safety zeigt +20,49 % Schlussbewertung bei fünf offenen Positionen, aber −105,83 USD realisierten P/L. Das ist kein Beweis für abgeschlossene profitable Trades.',
      '', 'Einzelne vollständige Teilkohorten sind interessant, dürfen aber nicht den unvollständigen Gesamtvergleich ersetzen. Der nächste belastbare Exit-Vergleich benötigt vollständige gemeinsame Pfade und neue prospektive Beobachtungen. Die bekannten SIP-Lücken, unter anderem CVX 25.10.2021 und COST 23.08.2024/12.09.2025, werden nicht mit erfundenen Kerzen gefüllt; bereits untersuchte 1m-Abrufe lösten die alten Lücken nicht verlässlich.','',
      '## Prüfung und weiteres Vorgehen','',
      f'Geprüft: Daten-/Engine-/Planhash, {v["entries"]} Originale gegen eingefrorene Signale, {v["controlObservations"]} Kontrollzuordnungen, {v["independentFineHorizonPaths"]} vollständige 5m-Horizontpfade direkt nachgerechnet und neun paarweise Hauptmittelwerte unabhängig berechnet. Alle 28 Kapitalledger wurden separat auf Cash sowie Risiko-/Allokationsbudgets abgeglichen.',
      '', 'Jetzt nutzbar: manuelle Strukturprüfung, Merkmalsvergleich, nachvollziehbare Beobachtung und prospektive Papierfälle. Noch offen: deine unbeeinflussten Bewertungen der 20 SIP-Fälle, ausreichend neue Vorwärtsfälle, verlässlichere Lückenklärung und eine unabhängige Strategieprüfung. Ein LLM kann anschließend die gespeicherten Fakten erklären; es berechnet keine OHLC-Werte oder rückwirkenden Signale.',
      '', 'Keine Orders, keine externen Nachrichten, kein Container-Deployment, kein automatisch gewählter neuer Parametersatz. Der alte IEX-Lauf und die manuelle Chartfunktion bleiben bestehen.','',
      'Reproduzierbare Quellen: Studienvertrag, Auswahldateien, 60 Aktienblöcke, summary.json, matched57-summary.json, candidate-verification.json und 28 Cashledger im lokalen Laufverzeichnis. Laufzeitdaten und private Bewertungen werden nicht nach Git übernommen.']
    Path(output).write_text('\n'.join(lines)+'\n','utf-8')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True);p.add_argument('--output',required=True);a=p.parse_args();run(a.root,a.output)
