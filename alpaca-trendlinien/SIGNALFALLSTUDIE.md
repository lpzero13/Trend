# Signalepisoden ohne Depot- und Zeitgrenzen

Umgesetzt am **31.10.2026** als eigene Offline-Untersuchung. Grundlage: [Forschungsentscheidung vom 30.10.](FORSCHUNGSAUSRICHTUNG-20261030.md). Die bisherigen Chart-, Forschungs-, Signaljournal- und Depotfunktionen bleiben erhalten; ihre bisherigen Verträge werden nicht still geändert.

## Was dieser Modus untersucht

Eine echte neue Einstiegsgelegenheit wird ein eigener Fall. Alle Fälle können gleichzeitig laufen, auch bei derselben Aktie. Es gibt kein gemeinsames begrenztes Kapital, keine Depotplätze, keine Allokationsgrenze und keine Sperre wegen einer offenen anderen Position. Einheitlicher Einsatz **1.000 USD je Fall, fraktionale Stückzahl**. Dies ist eine Vergleichsnormierung, keine Behauptung eines ausführbaren Portfolios.

Die unveränderte kausale Master-Geometrie und der bestehende `PilotObserver` liefern drei getrennte Entryfamilien: Ausbruch, roter Retest und Safety-Bounce. Zwei Kontakte, drei noch zu junge Kontakte und qualifizierte Linien bleiben getrennte Gruppen. Der Bounce benötigt weiterhin eine bereits zuvor qualifizierte steigende Safety. Es gibt keinen neuen SMA-Filter oder nach späterem Gewinn ausgewählten Entry.

## Wie Wiederholungen vermieden werden

`setup_episodes.py` ergänzt strukturelle Herkunft oberhalb der bestehenden Signalerkennung:

- Linien desselben roten beziehungsweise grünen Fächers teilen eine Herkunft. Eine Kindlinie, die zur Hauptlinie wird, erbt die Herkunft, soweit bekannte Anker sie verbinden.
- Eine neue technische ID, Endpunktkorrektur, bloße Qualitätsaufwertung oder weitere erfüllte Tageskerze allein eröffnet keine neue Episode.
- Eine bisher unverbundene Ankerstruktur ist ein neuer Ursprung. Innerhalb derselben Herkunft erlauben **mindestens zwei Kontakte, die nach Beginn der letzten Episode entstanden und vor dem neuen Signal bestätigt waren**, einen erneuten Strukturaufbau. Keine feste Wartefrist in Tagen.
- Pro Episode höchstens ein Signal je Entryfamilie. Gleichzeitige Alternativen werden anhand bereits bekannter Kontaktqualität, Kontaktzahl und stabiler ID ausgewählt.
- Ausbruch und späterer roter Retest bleiben über die ursprüngliche Szenario-ID verbunden, selbst wenn inzwischen eine neue Episode entstand. Exitvarianten sind ebenfalls keine neuen unabhängigen Fälle.
- Vorlauf und Zwischenjahre werden mitverarbeitet, damit ein Fensterbeginn kein künstliches neues Setup erzeugt.

Diese formale Abgrenzung ist eine **experimentelle Stichprobendefinition**. Sie muss später anhand gespeicherter Zeichnungen/Verläufe auf zu starke oder zu schwache Zusammenfassung geprüft werden. Sie ist keine bewiesene Gleichsetzung mit subjektiver Linienzeichnung und kein aus späteren Gewinnern optimierter Filter.

## Ausführung und Exits

Kauf am nächsten erwarteten regulären 5m-Open nach Signalzeit plus 300 Sekunden. Fehlt dieser Open, wird nicht einfach zur nächsten vorhandenen Kerze gesprungen. Liegt der Open unter dem Anfangsstop, wird der Entry abgesagt. Der Anfangsstop stammt aus der beim Signal aktuell gültigen engen Safety, mit 0,3 % Puffer und auf Cent abgerundet. Die ursprüngliche Safety beim roten Bruch bleibt zusätzlich archiviert.

Kosten je Seite: halber modellierter Spread von insgesamt 5 Basispunkten plus 5 Basispunkte Slippage; derzeit keine feste Ordergebühr. Normierte Fälle haben keine Mindeststückzahl. Geplantes R enthält die modellierten Kosten beider Seiten; prozentuales Nettoergebnis und nominales USD-Ergebnis bleiben zusätzlich sichtbar.

Drei vorab gewählte Hard-Stop-Varianten auf denselben Entries:

1. `fixed`: Anfangsstop unverändert als Kontrolle.
2. `original_safety`: ursprüngliche beim Entry gültige steigende Safety weiterprojizieren.
3. `fan_safety`: die jeweils aktuelle gültige steigende Safety nachziehen.

Stops dürfen nur steigen. Eine neue Safety muss zum Quellschluss gültig sein und unter dem aktuellen Schluss liegen. Bestätigung am 4h-Quellschluss; Aktivierung nach 300 Sekunden am nächsten erwarteten 5m-Open. Zwischen Bestätigung und Aktivierung gilt der alte Stop. Gap unter dem Stop: tatsächlicher Open statt erfundenem Stopfill. Das Hoch der Exitkerze wird nicht als Gewinn vor dem Stop angerechnet, weil die Intrabar-Reihenfolge unbekannt ist.

**Kein Tageslimit, kein Take Profit, kein Ersatzlimit von beispielsweise 250 Tagen.** Positionen folgen der Regel bis zum Exit oder tatsächlichen importierten Datenende. Das Entryfenster begrenzt nur neue Einstiege. Die Nachbeobachtung endet nicht am Fensterende.

Der feste Stop kann ohne weitere Exitregel keine Gewinne realisieren. Positive Verläufe bleiben dort offen oder später datenbedingt zensiert. Deshalb sind die Trefferquoten seiner ausschließlich geschlossenen Fälle kein sinnvoller Erfolgsvergleich mit nachziehenden Stops. Auch bei Safety-Modellen müssen unterschiedliche offene/zensierte Teilmengen berücksichtigt werden.

## Daten und Status

Nur explizit gewählte vorhandene immutable SIP/split-Datasets, keine Providerimporte. `TORI_DATA_DIR` muss auf denselben Datenbestand zeigen wie der Dienst; im Container gewöhnlich `/var/lib/tori`. Nicht still den Datenpfad wechseln.

`closed` bedeutet regelbasierter Exit. `open` bedeutet noch offen am echten Datenende, mit getrenntem Buchergebnis. `censored` bedeutet fehlender ausführbarer Pfad: weder Gewinn noch Verlust erfunden. Ein solcher Fall stoppt keine anderen Fälle. Fehlende Vorgeschichte sowie ungültige, abgesagte oder nicht ausführbare Entries werden getrennt ausgewiesen. Feiertage, reguläre Sitzungen und Sommerzeit kommen aus dem vorhandenen XNYS-Kalender.

Der deklarierte Importzeitpunkt begrenzt die Beobachtung. Er wird nicht je Aktie auf die letzte zufällig vorhandene Kerze verkürzt; auch fehlende Schlussintervalle bleiben dadurch erkennbar. Angebrochene 4h-Kerzen liefern keine neuen Stopentscheidungen, vollständig vorhandene 5m-Kerzen können aber laufende Hard-Stops auslösen.

## Aufruf und Wiederaufnahme

Aus `alpaca-trendlinien/`, mit aktiviertem Python-Environment. Die Quelle ist ein explizites lokales Universumsmanifest mit Dataset-IDs; das Beispiel ist der vorhandene private Forschungsplan, kein mit Git ausgeliefertes Marktdataset:

```powershell
python tools/run_event_cases.py artifacts/event-cases-pilot --source artifacts/robustness-v2-20261030/plan.json --symbols AAPL --windows 2023 --workers 1
python tools/verify_event_cases.py artifacts/event-cases-pilot --samples-per-stock 20 --prefix

python tools/run_event_cases.py artifacts/event-cases-wide --source artifacts/robustness-v2-20261030/plan.json --workers 3
python tools/verify_event_cases.py artifacts/event-cases-wide --samples-per-stock 2
python tools/report_event_cases.py artifacts/event-cases-wide SIGNALFALL-ERGEBNISSE.md
```

Ohne `--symbols` alle im Quellmanifest enthaltenen Aktien; ohne `--windows` alle dort genannten Fenster. Kein automatisches Nachladen fehlender Aktien. Ein bis vier technische Worker, unabhängig von der Zahl gleichzeitiger Fälle.

Wiederaufnahme mit identischem Code und identischem Plan:

```powershell
python tools/run_event_cases.py artifacts/event-cases-wide --phase build --workers 3
python tools/run_event_cases.py artifacts/event-cases-wide --phase evaluate
```

Ein OS-Lock verhindert zwei Schreiber pro Studienordner. Plan, Enginecode und Dataset-IDs werden gebunden; Code-/Auswahländerung benötigt einen **neuen** Studienordner. Vollständige Aktienblöcke sind atomar geschrieben und prüfsummengeschützt. Ein abgebrochener unvollständiger Aktienblock wird erneut berechnet, vollständige unveränderte Blöcke werden wiederverwendet. Keine laufende automatische Optimierung, kein Daemon und keine Brokerorders.

## Ergebnisse und Prüfungen

Private Dateien im Studienordner:

- `plan.json`, `engine/`: vor der Berechnung eingefrorene Annahmen und Produzercode.
- `stocks/*.json.gz`: Episodenherkunft, unterdrückte Kandidaten, Ereignisjournal, unveränderliche Signal-/Safety-Geometrie, Entrymerkmale, Quellenzeitlinie und alle Exitpfade.
- `results.json`: Zähler, getrennte Gruppen und Zeitfenster, Trefferquote/Mittelwert/Median nur mit ausdrücklichem Nenner.
- `cases.csv`: pro Fall und Exitvariante Entryzeit, Stopabstand in %/ATR, Status, Exit, Netto-R, Netto-%, normiertes USD-Ergebnis, MFE/MAE und offene Markierung.
- `verification.json`: IDs/Kosten/Stopverfügbarkeit für alle Fälle; zusätzliche separate 5m-Replays ohne den beschleunigten Intervallindex.
- `report-details.json`: paarweise gemeinsame Fälle, Gewinnerkonzentration und rechnerische Sensitivität ohne beste drei Trades; kein neuer Handelsfilter.

Der Pilot prüft zusätzlich, dass Weglassen zukünftiger Kerzen die zuvor gefundenen Episoden/Signale nicht verändert. Neue Unit-Tests decken unter anderem unveränderte Strukturen, frische Kontakte, Ausbruch-/Retestherkunft, Datenlücken einschließlich Importende, Stoplatenz, fehlende Entrykurse, Kosten, mehr als 80 Tage offene Fälle sowie unveränderte Wiederaufnahme und Manipulationsschutz ab.

## Weiterhin geplant

Sichtprüfung repräsentativer Episoden, breitere unabhängige Daten/prospektive Prüfung, Abstandsmerkmale auswerten und neue Schwellen getrennt validieren. Ein Close-Stop mit explizitem Notstop, subjektive Exitbestandteile und ein echtes gemeinsames Depot sind eigene weitere Experimente. Eine positive historische Tabelle ist noch keine Strategie- oder Hermes-Handelsfreigabe. Bekannte Daten, Überlebendenauswahl, fehlende Dividenden/FX und abhängige Fälle bleiben Einschränkungen.
