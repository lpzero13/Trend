# Tori-Fächer: kausale Linien und Backtestfälle

**Ergänzung:** Das neue gelieferte Pine-Update steht separat als `fan_master` zur Verfügung. Regeln, Unterschiede, Bedienung und aktueller Prüfnachweis: [TORI-MASTER-UPDATE-20261029.md](TORI-MASTER-UPDATE-20261029.md). Die nachfolgend beschriebenen bisherigen Profile bleiben erhalten.

Stand 29.10.2026. Optionaler lokaler Modus neben den bisherigen Linien und Forschungsengines. Bedienung unter `/faecher`, im Chart über **Analysemodell → Tori-Fächer** oder **Fächer: mehrere Startanker**. Die Chartanalyse startet weiterhin ausgeschaltet. Keine Brokerorders, kein Container-Rollout und keine automatische Änderung eines Zeitplans.

## Was umgesetzt ist

Der korrigierte, vom Nutzer gelieferte Pine Master ist als Python-Geometrie übertragen. Das ist keine vollständige Implementierung des ursprünglichen Jilly-Indikators und keine Behauptung, dessen gesamte Filter oder subjektive Tori-Linienwahl exakt nachzubilden. Die bestehenden gebündelten Bibliothekslizenzen bleiben erhalten; kein zusätzliches fremdes Repository eingebunden.

| Modul | Aufgabe |
|---|---|
| `fan_geometry.py` | Wilder-ATR, bestätigte Pivots, Körper-/Docht-Hülle, Kontakte und Fächer |
| `fan_observer.py` | Bekannte Linien verfolgen, Annäherung, Ausbruch, roter Retest, feste Signalepisoden |
| `fan_execution.py` | Bedingter Einstieg, Stückzahl, Kosten, Stop-/Zeit-/optionale Zielausführung |
| `fan_study.py` | Zufallsstarts, kerzenweises Fortschalten, Kohorten und Ergebniszusammenfassung |
| `fan_jobs.py` | Bestehende SQLite-Queue, Checkpoints, Ereignisjournal und Ergebnis-Paginierung |
| `fan_chart.py`, `fan_api.py` | Gleiche Quellberechnung für Chart, Forschungsfall und Headless |
| `static/fan.*`, `static/fan-view.js` | Formular, Aufträge, getrennte Gruppen, Originalfall-Chartlinks |

Keine zusätzlichen Runtime-Abhängigkeiten. SQLite bleibt Betriebsdatenbank; vorhandene unveränderliche Parquet-Datasets bleiben die Kursgrundlage. Persönliche Rays und Messungen bleiben im Browser und werden nicht zur automatischen Signalerzeugung verwendet.

## Linien und Zeitpunkt X

Standard: ATR 14 nach Wilder, Pivots mit zwei Kerzen links und rechts, mindestens fünf Quellkerzen zwischen Kontakten, Kontakttoleranz 0,45 des **damaligen** ATR, Dochtverletzung höchstens 0,15 ATR. Kerzenkörper dürfen die ungebrochene Linie nicht überschreiten. Fallende Widerstände und steigende Safety-Linien, bis vier Fächerstufen je Seite. Suchhorizont 320 Kalendertage, begrenzt auf 1.800 Quellkerzen und 80 Pivots je Seite. Begrenzungen werden im Analyseobjekt ausgewiesen.

Die Standardvariante `extreme` beginnt am Extrempivot. `local` ergänzt zwei jüngere Startanker als getrenntes Experiment. Reaktionskontakte erfassen zusätzlich eine ausreichende Bewegung weg von der Linie zwischen Kontakten; dieses Merkmal ist vorerst kein zusätzlicher harter Ausschluss.

Ein Pivot ist erst nach seinen rechten Bestätigungskerzen verfügbar. Linien mit zwei Kontakten, mit mindestens drei noch zu jungen Kontakten und mit mindestens drei Kontakten plus sieben Kalendertagen werden getrennt geführt. „Qualifiziert“ bedeutet hier ausschließlich diese Kontakt-/Altersklasse, nicht das gesamte Tori-Regelwerk und keine geprüfte Handelsqualität.

Chart und Beobachter rechnen auf abgeschlossenen **Quellkerzen** in 1h, 4h, 1D oder 1W. Wochen werden aus vollständigen erwarteten XNYS-Sitzungen abgeleitet. Auf ein anderes Chartintervall projizierte Linien sind Zeichnungen, keine dort neu entstandenen Einstiegssignale.

Der fortlaufende Beobachter entdeckt eine Linie nur im damaligen Präfix. Er prüft zuvor bekannte Linien beim nächsten Schluss, bevor neue Kontakte ihre Qualität verbessern können. Eine neue aktuelle Fächerlinie löscht eine noch gültige beobachtete Episode nicht. Erst ungültige, abgelaufene oder durch eine Datenlücke unterbrochene Episoden werden beendet.

Der Geometriekern besitzt außerdem einen Pine-Vergleichsschnappschuss mit ausgespartem roten Ausbruchsfenster. Dieser Vergleichsmodus wird **nicht** zur rückwirkenden Erzeugung von Backtestsignalen verwendet. Unterschiedliche Feeds, Sessions und Bereinigungen können auch bei gleichem Algorithmus andere Linien liefern als TradingView.

## Ausbruch, Retest und Fixierung

Ausbruch: voriger Schluss auf/unter der alten roten Linie, neuer Schluss darüber; der saubere Schluss muss zusätzlich den Puffer von standardmäßig 0,15 ATR überwinden. Ein zunächst schwacher Bruch darf bis zum konfigurierten Bestätigungsfenster auf einen sauberen Schluss warten.

Beim Bruch werden die ursprüngliche rote Geometrie, die bis dahin bekannte Kontaktklasse und die zu diesem Schluss verfügbare grüne Safety gespeichert. Initialer Stop: Safety-Wert beim Bruch abzüglich standardmäßig 0,3 %, abgerundet auf den konfigurierten Tick. Dieser Stop bleibt auch beim späteren Retest derselben Episode erhalten. Ohne positive Safety unter dem Signalpreis entsteht kein ausführbarer Forschungsfall; das Ereignis bleibt im Journal.

Retest: erst **nach** dem bestätigten Bruch zurück in die ATR-Zone der ursprünglichen roten Linie, danach bullish geschlossene Bestätigung oberhalb der gepufferten Linie. Ein Kontakt mit Grün allein ist kein roter Retest. Ausbruch und Retest sind alternative Testgruppen und werden nicht zu zwei unabhängigen Trades desselben Depots erklärt.

Mehrere Linienmeldungen desselben Schlusses werden innerhalb von Geometrie, Einstiegsvariante und Kontaktgruppe zusammengefasst. Die Auswahl erfolgt **vor** der Auswertung: mehr Kontakte, mehr Reaktionskontakte, früher bekannt, schließlich stabile ID. Alternative Linien-IDs bleiben am Fall, alle Rohereignisse im Journal. Verschiedene Geometrien/Kohorten können weiterhin denselben Marktmoment enthalten.

Der Forschungsfall verlinkt auf seine Dataset-ID, Geometrie, Parameter und ursprüngliche Signallinie. Vor dem Signal sind dessen Marker und Einstieg nicht sichtbar; der tatsächliche Modell-Open erscheint erst ab seiner Verfügbarkeit. Orange zeigt die ursprüngliche gebrochene rote Linie, Grün die ursprüngliche Safety; die horizontale Schutzmarke ist der feste Stop. Aktuelle Linien können daneben weiter entstehen. Die Infobox nennt Signalstop und Modell-Einstieg separat. Vor-/Zurückschalten und Intervallwechsel behalten die Fallbindung, auch nach Neuladen. Normale Chart-Schnappschüsse und verschiedene Geometrien haben getrennte Fixierungs-Schlüssel.

## Zufallsstarts und Auswertung

Zufallsstarts werden nur anhand von Zeit und Abdeckung mit reproduzierbarem Seed ausgewählt, ohne zukünftige Gewinne oder Signale zu filtern. Pro Aktie werden dieselben Starts für beide Geometrien verwendet. `origin_start` und `origin_end` begrenzen die **Startauswahl**, nicht die anschließende Suche. Ab X wird bis zum ersten gültigen Signal je Variante/Kontaktgruppe, bis zu einer unbekannten Quellenlücke oder bis zur Auswertungsgrenze weitergegangen.

„Erstes Signal“ garantiert noch keinen Modell-Einstieg: Ein Open unter dem Stop, unzureichendes Kapital/Risikobudget oder fehlende Feindaten werden separat ausgewiesen. Es wird nicht nachträglich das erste gewinnbringende oder ausführbare Signal ausgewählt. Auch ohne Entry bleibt ein Startversuch nachvollziehbar. Ein späteres Signal ist nicht garantiert.

Der Bericht unterscheidet Startversuche, von diesen erreichte verschiedene Signale und sämtliche Signalfälle im Verlauf. Mehrere Starts können denselben Fall erreichen. Herkunft `market`/`synthetic`, Feed und Kursbereinigung werden nicht in gemeinsamen Ergebnisgruppen vermischt. Synthetische Technikfälle werden ausdrücklich markiert. Berichte lesen eine konsistente SQLite-Sicht und halten beim Zusammenfassen keine vollständigen Origin-Snapshots oder Pfade im RAM; ID-Mengen und Zähler wachsen weiterhin mit dem Bestand.

Die letzten standardmäßig 20 % der Quellhistorie bleiben außerhalb von Signal- **und** Ergebnisberechnung. Ein zusätzlicher früherer `cutoff` kann die Freigabe nur verkürzen. Der gebundene Fallchart lehnt spätere Zeitpunkte auch bei ausgeschalteter Analyse ab. Das ist eine Grenze dieses Forschungsauftrags, kein Zugriffsschutz gegen das bewusste Öffnen derselben Aktie in einem unabhängigen normalen Chart. Bereits aus älteren Experimenten bekannte Daten werden dadurch nicht nachträglich zu einem unberührten Holdout.

## Ausführungsannahmen

- Nur vorhandene normalisierte reguläre 5m-Datasets. Provider-native/Extended-Hours-Daten werden nicht stillschweigend für diesen Backtest umgedeutet. Signale und Ausführung nutzen denselben Feed und Bereinigungsstand.
- Einstieg am **nächsten erwarteten regulären 5m-Open** nach Signalschluss plus standardmäßig 300 Sekunden Verzögerung. Fehlendes erwartetes Open heißt „unavailable“, nicht auf ein bequemeres späteres Open ausweichen. Open durch den Stop: verwerfen.
- Bedingtes Paper-Modell: Erst am Open werden ganze Kurseinheiten anhand von Kapital und geplantem Stoprisiko inklusive Kosten bestimmt. Standard 2.000 Einheiten Kurswährung und 1 % Risikobudget. Das ist keine garantierte vorab ausführbare Brokerorder. Splitbereinigte historische Kurseinheiten sind nicht ohne Weiteres damalige reale Stückzahlen.
- Standardkosten: 5 Basispunkte gesamter Spread, 5 Basispunkte Slippage **je Seite**, feste Gebühr je Order standardmäßig null. Netto-P/L und prozentuale Fallrendite enthalten beide Seiten und beide festen Gebühren. Keine EUR/USD-Umrechnung.
- Fester Stop oder separat ein Stop unter bestätigten höheren Tiefs. Ein höheres Tief muss nach dem Entry entstanden und rechts bestätigt sein; eine Anhebung gilt erst nach Bestätigung plus Verzögerung am nächsten erwarteten Open. Kein rückwirkendes Nachziehen in die Bestätigungskerze.
- Stop-Gap zum tatsächlichen Open, sonst Stoppreis mit modellierten Kosten. Stop und optionales Ziel innerhalb derselben OHLC-Kerze: konservativ Stop zuerst, Fall als mehrdeutig markieren. Ziel standardmäßig **aus**, kein 3R-Zwang. Positives Ziel-Gap wird konservativ zum Zielpreis bewertet.
- Zeitende nach 5/10/20 **folgenden Handelssitzungen**, Entrytag zählt nicht mit. Jeder Horizont/Stop ist ein eigener Modellpfad. Fehlender 5m-Pfad wird zensiert; offene/zensierte Fälle erhalten keine erfundene realisierte Rendite. Separat gibt es reine Schlusskursbeobachtungen ohne Stopausstieg.

Das ist ein kausaler **Einzelfall-Backtest mit Ausführungsmodell**, keine gemeinsame Depotstrategie. Positionen teilen kein Kapital, Fälle überlappen, Dividenden/Finanzierung/Steuern und reales Orderbuch werden nicht vollständig simuliert. Mittelwerte nur geschlossener Fälle können gerade bei offenen Verlustfällen verzerrt sein.

## Hermes / Container / CLI

Web: `/faecher` → lokale Bestände auswählen → Intervall und Geometrie → Vergleich einreichen. Ein vorhandener Forschungsworker bearbeitet die Queue. Ohne Worker bleibt der Auftrag wartend; das Formular startet keinen Providerimport und keinen zusätzlichen Worker. Lokale Bestände zeigt `GET /api/fan/datasets` ohne Kursabruf oder Hydrierung aller OHLC-Dateien.

CLI aus dem Anwendungsordner, mit demselben `TORI_DATA_DIR` wie der Dienst, im Container `/var/lib/tori`:

```bash
python tori.py submit --spec deploy/fan-study.example.json
python tori.py worker --once
python tori.py status --id JOB_ID
python tori.py report --id JOB_ID --entry-filter entries --offset 0 --limit 20
python tori.py report --id JOB_ID --entry-filter origins --offset 0 --limit 20
python tori.py events --id JOB_ID --limit 100
python tori.py analyze --dataset DATASET_ID --timeframe 4h --asof 2024-06-28T20:00:00Z --engine fan_extreme
```

Die Beispiel-Dataset-ID **muss** durch eine vorhandene lokale ID ersetzt werden. Alte Analyseaufrufe ohne `--engine` behalten ihre bisherigen Regeln. Die vorhandene geschützte Job-API bleibt zuständig; Host-/Origin-/Token-Schutz bleibt erhalten. `GET /api/fan/chart` ergänzt die gebundene Fallansicht mit `dataset`, `fan_job`, `fan_case`, `engine`, `asof`, `timeframe`, `analysis=0|1`.

Ein abgebrochener Symbolteil wird deterministisch wieder durchlaufen, gespeicherte Ereignis-/Fall-IDs werden nicht doppelt angelegt; fertig geprüfte Symbole werden übersprungen. Ein geänderter Enginehash verhindert die Fortsetzung alter Aufträge. **Nach diesem Update neue Jobs anlegen**, keine vorhandenen Produktionsaufträge durch geänderten Code fortsetzen. Keine Änderung des Datenpfads, keine Migration und kein Überschreiben lokaler Secrets durch diesen Modus. Referenzschutz sowie bestehendes Backup/Restore greifen auch für die neuen Fälle. Vorhandene Proxmox-Installation wurde hier nicht verändert.

## Technische Abnahme und Befund

Die sieben Ziele aus [TORI-FAECHER-PLAN.md](TORI-FAECHER-PLAN.md) sind durch Gegenbeispiele, Queue-/HTTP-Tests und einen isolierten Browserlauf abgedeckt: unabhängiger langsamer Geometrieprüfer, gecachte/ungecachte Präfixe, geänderte Zukunft, bestätigte Pivots, unveränderliche Episoden, Retest/Safety, erwarteter Open, Gaps/OHLC-Reihenfolge/Kosten, Deduplizierung, fehlende Daten, alle vier Quellintervalle, Holdout, Abbruch/Wiederholung und Chartgleichheit. Die Tests benötigen keine Providerzugangsdaten.

Endgültiger lokaler Stand: **390 Python-Testfälle unter 3.12.10, davon ein bestehender Skip, keine Fehler; 58 JavaScript-Tests bestanden**. Darin 40 gezielte Python-Fächerfälle. Der neue JS-Renderer ist zusätzlich in der bestehenden CI-Testliste; Python 3.13/Linux werden hierdurch nicht als bereits lokal abgenommen behauptet. Der zusätzliche Testserver mit isoliertem Datenordner wurde nach der Abnahme beendet; bestehende Dienste und Zeitpläne wurden nicht umgestellt. Der normale lokale Dienst muss zum Laden der neuen Python-Routen regulär neu gestartet werden.

Im Browser wurden Formularübermittlung, echter Workerauftrag, Ergebnisse, offene Falldetails über mehrere Aktualisierungen, Hell/Dunkel, vertikales Scrollen, Originalfall-Link, Analyse zunächst aus, Aktivierung, Vor-/Zurückschritt, Intervallwechsel bis 1W und erneutes Laden mit erhaltener Fallbindung geprüft. Zwei dabei gefundene Fehler behoben: falsche Formularschrittweiten und verlorene Fall-/Engineparameter in der aktualisierten URL. Einstieg und Stop werden jetzt auch dann angezeigt, wenn der Open innerhalb der letzten abgeschlossenen Quellkerze liegt. Ein isolierter synthetischer Auftrag wurde gesichert, in einen neuen Datenordner wiederhergestellt und mit identischen Fällen/Zusammenfassungen gelesen; zusätzlicher CLI-Analyseaufruf auf 1W erfolgreich.

**Offline-Marktversuch, keine Optimierung:** vorhandene SIP-/splitbereinigte 5m-Datasets von AMZN, MSFT und NVDA, Beginn Juli 2020, 200 Quellkerzen Vorlauf, 4h, Freigabe bis 28.06.2024, unveränderte Standardparameter, je zehn zufällige Starts. Beide Geometrien erhalten dieselben insgesamt 30 Zeitpunkte, daher 60 gespeicherte Geometrie-Startversuche. Keine neuen API-Abrufe. 762 je Testgruppe deduplizierte Signalfälle, davon 662 im Kapital-/Risikomodell eingestiegen und 100 wegen Größe/Risikobudget abgewiesen. Keine fehlenden 4h-Quellenintervalle in diesem Bestand. Einzeltitel-Verarbeitung inklusive Laden/Modellpfaden ca. 6,6–8,6 Sekunden auf diesem Rechner, kein Nachweis für ein Volluniversum.

| Finder | Entry / Kontakte | Signalfälle / Modell-Entries | Fest 5 Sitzungen | Fest 20 Sitzungen | Höhere Tiefs 20 Sitzungen |
|---|---|---:|---:|---:|---:|
| Extrem | Ausbruch / 3+ mit Alter | 63 / 53 | +1,54 % | +2,45 % | +3,48 % |
| Extrem | Retest / 3+ mit Alter | 36 / 29 | +1,69 % | +1,93 % | +1,73 % |
| Extrem | Ausbruch / 2 | 137 / 119 | −0,55 % | +1,22 % | +0,99 % |
| Extrem | Retest / 2 | 80 / 69 | +0,07 % | +1,38 % | +0,94 % |
| Mehrere Anker | Ausbruch / 3+ mit Alter | 71 / 62 | +1,70 % | +2,74 % | +3,51 % |
| Mehrere Anker | Retest / 3+ mit Alter | 40 / 34 | +1,34 % | +2,53 % | +1,36 % |
| Mehrere Anker | Ausbruch / 2 | 210 / 186 | +0,25 % | +1,19 % | +1,33 % |
| Mehrere Anker | Retest / 2 | 125 / 110 | +0,23 % | −0,16 % | +0,37 % |

Prozentwerte: ungewichtete Mittel **nur geschlossener Einzelfallpfade**, nach Modellkosten; keine Depotrenditen. Bei 20 Sitzungen bleiben je nach Gruppe bis vier Fälle offen; sie sind aus diesen Mittelwerten ausgeschlossen. Keine Gruppe junger Drei-Kontakt-Linien in diesem Versuch. Mehrere Gruppen können dieselben Kurse/Signale enthalten. Die drei heutigen großen Gewinner sind kein repräsentatives historisches Universum; bekannte Marktdaten und Parameter aus vorangegangener Entwicklung sind keine unberührte externe Validierung. Private Laufparameter, Dataset-Hashes und Einzelfälle liegen nur unter dem ignorierten lokalen `artifacts/fan-acceptance-20261029/`.

**Bewertung:** Technisch ist die gewünschte Untersuchung von Zeitpunkt X über Entry und Stop bis zum späteren Verlauf möglich und getestet. Mehrere Anker erhöhen hauptsächlich die Zwei-Kontakt-Fallzahl; mehr Meldungen sind nicht automatisch besser. Qualifizierte Gruppen zeigen hier ein interessantes positives Signal, während nachgezogene Stops nicht jede Retestgruppe verbessern. Nächster Forschungsbedarf: vorher festgelegter Vergleich auf breiterem Universum mit mehr Marktphasen, weniger überlappende Episoden und passende Kontrollfälle, dann zeitlich getrennte Validierung. Noch offen sind eine produktive Live-Scanner-/Benachrichtigungsanbindung dieser Engine, vollständige Portfolioausführung, historische Delistings/Kapitalmaßnahmen und Volluniversum-Ressourcentests.
