# Begrenzter Backtest-Pilot: MSFT, zwölf Monate

Stand: **30.10.2026**. Erster technischer Teil der [Meilenstein-Roadmap](BACKTEST-MEILENSTEINE.md), mit den drei Hauptfamilien aus dem [Strategie-Abgleich](BACKTEST-STRATEGIE-ABGLEICH-20261030.md).

## Zweck und Umfang

Ein expliziter Offline-Lauf über genau eine unveränderliche Dataset-ID. Entry-Suche im Kalenderjahr **2023**, 4h-Quellkerzen; **400 Kalendertage Vorgeschichte** für Geometrie/ATR und Beobachtung bis **31.03.2024** für spätere Verläufe. Die gesamte Aktienhistorie und andere Aktien werden nicht durchgescannt. Der Zeitraum wurde vor dem Pilot-Ergebnis als technische Entwicklungsprobe gewählt; 2023 ist kein als unberührt ausgewiesener Holdout.

Vorhandener lokaler MSFT-Bestand: SIP, splitbereinigt, reguläre XNYS-Sitzungen. Keine neuen Providerdaten nötig. Die Kursdaten bleiben unter dem bestehenden `TORI_DATA_DIR`; Ergebnisse werden in einen ausdrücklich gewählten neuen Ordner geschrieben. Keine Queue, kein Zeitplan, keine Orders, keine Änderung der Webanalyse und keine Wiederaufnahme des pausierten Sammlers.

## Ausdrücklich festgelegter Pilot-Vertrag

| Bereich | Annahme |
|---|---|
| Geometrie | Unverändertes vorhandenes Master-Profil, derselbe Quellkern wie im Chart |
| Kontaktqualität | Zwei, drei junge und qualifizierte Kontakte separat ausweisen; Bounce benötigt vorher bekannte qualifizierte Safety |
| Ausbruch | Sofort sauber oder spätestens auf der einen Folgekerze sauber; Untertypen derselben Entry-Familie |
| Roter Retest | Frühestens nach sauberem Ausbruch, maximal fünf 4h-Quellkerzen später; ursprüngliche rote Geometrie bleibt erhalten |
| Safety am roten Entry | Aktuelle gültige enge Safety am tatsächlichen Signalzeitpunkt. Safety und Stop des ersten Bruchs werden zusätzlich archiviert |
| Safety-Bounce | Safety war vor der Signalkerze qualifiziert bekannt; vorheriger Schluss oberhalb; vorangegangene Entfernung mindestens 0,5 damaliger ATR; Kontakt bis 0,45 ATR, Docht höchstens 0,15 ATR darunter, Körper höchstens 0,05 ATR darunter; bullischer Schluss oberhalb |
| Bounce-Episoden | Nach Signal erst nach erneuter Entfernung aktivierbar; mindestens fünf Quellkerzen Abstand zwischen Bounce-Signalen |
| Entry-Ausführung | Nächster erwarteter regulärer 5m-Open nach 300 Sekunden Modellverzögerung, kein rückwirkender Einstieg zum Signalclose |
| Kapital | Je separatem Einzelfall 2.000 **USD**, ein Prozent geplantes Risiko, ganze Stückzahlen; keine EUR-Umrechnung und kein gemeinsames Depot |
| Kosten | Fünf Basispunkte Gesamtspread und fünf Basispunkte zusätzliche Slippage pro Seite; modellierte halbe Spreadkosten pro Ausführungsseite, null fixe Ordergebühr |
| Initialstop | Safety-Wert am Signal minus 0,3 Prozent, auf Tick abgerundet |
| Stopführung | Fest; Fortschreibung derselben Entry-Safety; alternativ Wechsel auf aktuell bekannte enge Fächer-Safety. Ratchet: niemals absenken |
| Stopaktualisierung | Nur nach abgeschlossenem 4h-Quellintervall und Verzögerung am nächsten erwarteten 5m-Open wirksam |
| Auslösung | Hard-Stop bei 5m-Berührung/Gaps; separater Close-Stop bei 4h-Schluss unter **demselben prozentual gepufferten Ratchet-Stop**, Fill erst danach |
| Close-Stop-Abgrenzung | Bewusst nicht die andere Formel `Safety − 0,15 ATR`. Kein zusätzlicher versteckter Intraday-Notstop |
| Zeitgrenzen | Vier separate Vergleichspfade mit 5, 10, 20 und 40 Handelstagen maximaler Haltedauer; kein festes Gewinnziel |
| Kontext | Tages-SMA200 aus abgeschlossenen lückenlosen Tageskerzen, ausschließlich Merkmal; kein SMA-Filter |

Der Bounce verwendet die Kontaktklasse der vorher bekannten Safety, nicht einen erst durch die Signalkerze bestätigten dritten Pivot. Bei roten Episoden war der Widerstand schon vor dem Bruch bekannt; neue Linien ersetzen den ursprünglichen Widerstand nicht rückwirkend. Verschiedene ältere noch aktive Episoden dürfen Signale liefern; es wird nicht nur die heute sichtbare innerste Linie betrachtet.

Sofortiger Ausbruch, verzögerter Ausbruch und Retest einer Episode werden als abhängige Alternativen behandelt. Innerhalb Familie/Quellschluss/Kontaktklasse wird vor Kenntnis des späteren Ergebnisses eine Linie ausgewählt. Der Pilot ist eine Ereignisstudie mit Ausführungspfaden; er verhindert noch keine überlappenden Positionen in einem gemeinsamen Depot.

Die Safety-Auswahl am Entry wurde während der technischen Abnahme ausdrücklich vom alten Beobachterverhalten abgegrenzt: Dieser bindet die Safety bereits beim ersten Bruch. Der neue Pilot übernimmt dessen rote Ereignisse, archiviert die alten Werte, verwendet für den tatsächlichen Entry aber die dann gültige Master-Safety. Der bestehende Forschungsweg wird dadurch nicht verändert. Frühere private Pilotdateien vor dieser Vertragsprüfung sind keine finalen Ergebnisse und werden nicht überschrieben.

## CLI für lokale Anwendung und Hermes

Aus dem Anwendungsordner, mit dem gleichen Datenpfad wie der Dienst; im Container ist das normalerweise `/var/lib/tori`:

```text
python tori.py pilot-backtest --dataset DATASET_ID --start 2023-01-01 --end 2023-12-31 --outcome-end 2024-03-31 --output NEUER_ERGEBNISORDNER
python tools/verify_pilot.py --result NEUER_ERGEBNISORDNER/result.json
```

`DATASET_ID` muss lokal existieren. Die CLI importiert fehlende Daten nicht selbst. Entry-Fenster sind auf ungefähr zwölf Monate begrenzt, Nachbeobachtung auf 180 Kalendertage. Für sechs Monate Datumsgrenzen entsprechend ändern; die erforderliche Vorgeschichte bleibt erhalten.

Der Ausgabeordner muss neu sein. `manifest.json` enthält Parameter, Dataset-Identität, Datenfenster, Python-/Paketversionen und Quellcode-Prüfsummen. `result.json` enthält alle drei Signalgruppen, Originalgeometrien, tatsächliche Entry-Verträge, Kursbeobachtungen, Ereignisse und Exitpfade. `report.md` ist die lesbare Zusammenfassung. Wiederholung mit geändertem Kerncode ist ein neuer Lauf, keine Wiederaufnahme eines alten Zustands.

Chartlinks im Bericht rekonstruieren einen historischen Zeitpunkt über den vorhandenen lokalen Chart. Sie starten mit Analyse aus. Die ursprüngliche Episode kann von einer mittlerweile neu gezeichneten Chartlinie abweichen; die verbindlichen Originalanker sind im Pilot-JSON archiviert. Eine neue gebundene Pilot-Fall-Webansicht ist noch nicht implementiert.

## Gemessener finaler Pilot

| Entry-Familie | Signal-Fälle | Modell-Entries | Wegen Budget nicht ausgeführt |
|---|---:|---:|---:|
| Ausbruch | 36 | 30 | 6 |
| Roter Retest | 12 | 11 | 1 |
| Safety-Bounce | 4 | 4 | 0 |
| Summe der Forschungsfälle | 52 | 45 | 7 |

Die 52 Fälle liegen an **50 unterschiedlichen Quellschlüssen**. Es gibt 38 unterschiedliche rote Episoden; ein Ausbruch und sein Retest sind keine unabhängigen Belege. Ausbrüche: 28 sofort sauber, acht verzögert. Kontaktklassen der Signale: Ausbruch 33 mit zwei Kontakten und drei qualifiziert; Retest elf mit zwei Kontakten und einer qualifiziert; alle vier Bounces mit qualifizierter Safety.

Rechenzeit ohne vorheriges Einlesen des unveränderlichen Datasets: **6,43 Sekunden**. Offline-Wiederholung: **5,72 Sekunden**. Das ist eine lokale Windows-Messung, keine universumsweite oder Container-Prognose.

52 Fälle × drei Stopführungen × zwei Auslösearten × vier Horizonte ergeben **1.248 Vergleichspfade**, keine 1.248 unabhängigen Trades. Davon **1.080 geschlossen**; 168 Pfade gehören zu den sieben abgelehnten Entries. In diesem Pilot keine offenen oder wegen Pfadlücken unklaren Exitpfade; das begrenzte Auswertefenster enthält keine fehlenden erwarteten 4h-Quellkerzen. Dies ersetzt keine allgemeine Datenqualitätsfreigabe.

Beispielhafte feste 20-Handelstage-Auswertung mit Hard-Stop, **Durchschnitt netto R je geschlossenem Einzelfall**:

| Familie | Anzahl | Fester Stop | Ursprüngliche Safety fortschreiben | Neue Fächer-Safety zulassen |
|---|---:|---:|---:|---:|
| Ausbruch | 30 | +0,37 R | +0,54 R | +0,36 R |
| Roter Retest | 11 | +0,78 R | +0,97 R | +0,65 R |
| Safety-Bounce | 4 | −1,08 R | −0,69 R | −0,72 R |

Alle vier Horizonte und beide Stoparten stehen im vollständigen lokalen Bericht; diese Tabelle bestimmt keinen nachträglich ausgewählten Gewinner. Die vollständigen Kursverläufe werden zusätzlich auch nach hypothetischen Stops beobachtet und ausdrücklich von den ausgeführten P/L-Pfaden getrennt.

**Bewertung:** Der technische Durchlauf findet alle drei Entry-Familien und führt sie einschließlich Ablehnungen, Kosten, Gaps und Stopänderungen reproduzierbar durch. Ausbrüche und rote Retests sind in dieser begrenzten Probe positiv im Mittel; die vier Bounces verlieren. Die kleine, abhängige Auswahl einer einzigen Aktie in einem bekannten Jahr genügt weder zur Strategiefreigabe noch zur Verwerfung einer ganzen Entry-Familie. Ein engerer Fächerstop verbessert die Ergebnisse hier nicht durchgehend. Keine Depot-Rendite aus den Mittelwerten ableiten.

## Nachweise und verbleibende Arbeit

- 21 gezielte synthetische Unit-Tests für drei Entry-Familien, verspäteten Ausbruch, aktuelle/ursprüngliche Safety, Kontaktgrenzen, vorherige Qualifikation, gemeinsamen Master-Kern, spätere Stopwirksamkeit, Gaps, Close-Stop, Ratchet, fehlende Daten, Budget und Fenstergrenzen.
- Gespeicherter Marktversuch vollständig offline wiederholt: alle fachlichen Ergebnisse einschließlich Timeline, Journal und Manifest identisch; Providerzugriff im Prüfer gesperrt.
- Nur zukünftige 4h-Kerzen des Bestands stark verändert: die 20 Signale der ersten Fensterhälfte bleiben vollständig identisch.
- Alle 52 Fälle und 1.248 Exitpfade auf Verfügbarkeit, Budget, Stopmonotonie und Aktivierungszeitpunkte kontrolliert; Cash-Ergebnisse separat aus Fills, Stückzahlen und Kosten nachgerechnet.
- Gesamtregression: 464 Python-Testfälle ohne Fehler, ein bestehender Skip; alle 70 Web-/Chart-JavaScript-Tests bestanden. Ein erster parallel belasteter Lauf verfehlte das bestehende Worker-Startzeitlimit; isolierte Operations-Prüfung und der anschließende Gesamtlauf bestanden. Dafür wurden weder Worker-Code noch Testzeitlimit verändert.

Als Nächstes sind ausgewählte Originalfälle visuell zu prüfen und offene Definitionen aus dem Strategie-Abgleich zu bestätigen. Vollständige Tages-/Wochen-Fächerfilter, separate Safety-Rücksetzer nach Ausbruch, Teilverkäufe, echte Depotbelegung, breite unabhängige Validierung und Hermes-Dauerbetrieb bleiben spätere Meilensteine. Der frühere 100er-Sammelauftrag bleibt pausiert.
