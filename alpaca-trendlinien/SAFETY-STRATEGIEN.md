# Safety-Strategien: Umsetzung und Prüfvertrag

Stand 20.10.2026. Vor dem ersten Ergebnis festgelegter lokaler Forschungsauftrag. Long, keine Brokerorders. Bestehende Webansicht und Standardforschung bleiben erhalten. Ziel sind reproduzierbare, headless ausführbare Regeln mit ehrlicher Ergebnisbilanz; positive Ergebnisse sind keine Abnahmevoraussetzung, die durch nachträgliche Regeländerungen erzwungen wird.

## Vorab festgelegte Regeln

- Gemeinsame ursprüngliche Einstiege: archivierte Grundsignal-/Momentum-2-aus-3-Fälle, Ausbruch/horizontale Bestätigung/Retest getrennt. Auswahl der ursprünglichen Anker wie im vorherigen Exitvertrag, keine Gewinnerauswahl. Später zusätzlich kausaler Scan derselben Profile über die CLI, ohne Zukunfts-Auswertung im Signalpfad.
- Originalrot bleibt Diagnose. Rückfall darunter löst in A/B/C keinen Verkauf aus. Originalgrün bleibt dokumentiert. Die aktive Safety-Line-Identität kann nur durch ein bekanntes Strukturereignis wechseln.
- Gemeinsamer anfänglicher harter Stop: archivierte grüne Signalprojektion minus `max(0,01 USD, 0,25 × damals bekannte 4h-ATR(14))`. ATR ist nur eine von uns festgelegte Skalierung, keine behauptete Tori-Vorgabe. Fehlende ATR blockiert die ausführbare Strategie, nicht stillschweigend durch Null ersetzen. Der ursprüngliche Cent-Stop bleibt im alten Versuch archiviert.
- Kontrolle `fixed`: derselbe gepufferte harte Stop, sonst Zeitablauf. A `original`: ursprüngliche grüne Anker fortschreiben; erster bestätigter 4h-Schluss darunter löst einen Verkauf frühestens fünf Minuten später am verfügbaren regulären 5m-Open aus. Harter Stop hat Vorrang und bleibt bis zu einer bestätigten Strukturänderung unverändert.
- B `structure`: A plus neue verbundene Safety-Linie. Ein höheres Tief muss nach dem Einstieg und nach dem zuletzt akzeptierten B-Anker entstehen, zwei linke und zwei rechte abgeschlossene 4h-Nachbarn strikt überragen (als Tief unterschreiten), über dem bisherigen B-Tief liegen und auf ein nach Einstieg bekanntes neues Hoch folgen. Neuer A-Punkt ist der bisherige B-Punkt. Kein Docht darf die neue grüne Linie vom neuen A bis zur Bestätigung schneiden. Erst die bestätigte neue Struktur darf die aktive Linie ersetzen; sie muss am Bestätigungszeitpunkt enger als die bisherige sein. Neuer harter Stop höchstens nach oben zum neuen B-Tief minus damaligem ATR-Puffer. Bruchprüfung verwendet zuerst die zuvor aktive Linie; eine erst mit derselben Kerze gebildete Linie erzeugt keinen rückwirkenden Ausstieg.
- C `structure_target`: B plus vorher bekannte relevante Widerstandszone. Tages-/Wochenhochs mit 2+2 Bestätigung, Tageshoch zusätzlich mit mindestens einer damaligen Tages-ATR Prominenz zu den Nachbartiefs. Zonenbreite ±0,10 der bei Aufnahme bekannten Tages-ATR; nahe Pivotniveaus werden zusammengefasst. Ein nach Bestätigung oberhalb der Zone geschlossener Kurs entwertet das alte Widerstandslevel. Ziel ist die Unterkante der nächsten noch gültigen Zone; keine beliebige Auslassung eines nahen Hindernisses. Zonen und Ziele werden beim Einstieg festgehalten. Eine unbekannte Zone bleibt unbekannt; im ungefilterten Exitvergleich kein künstliches Ziel, im umsetzbaren Einstiegsfilter kein bestandener Raumtest.
- Einstiegsgruppen `all`: reine Vergleichsgruppe; `eligible`: positive Absicherung, höchstens 2 bekannte 4h-ATR bis zum gepufferten Stop, Linienalter mindestens sieben Kalendertage, bekannter Tages-/Wochenkontext jeweils nicht abwärts und mindestens 2R Netto-Raum bis zur nächsten gültigen Zone. Zwei-Kontakt-Linien bleiben zugelassen und werden separat gekennzeichnet; keine neue pauschale Drei-Kontakt-Pflicht. Monatskontext zunächst Diagnose, unbekannt bleibt unbekannt. Kein Filter wird nach Kenntnis der Ergebnisse aufgeweicht.
- 5/10/20 XNYS-Handelstage strikt nach dem Entrytag getrennt; früh verkaufte Position bleibt als Cash liegen. Nach der Phase keine Zukunftskurse verwenden. Stop-/Zielkontakt in derselben 5m-Kerze konservativ Stop zuerst; Gap-Stop zum verfügbaren Open. Kein Wiedereinstieg ohne neues eigenständiges Signal.
- Kosten wie im vorherigen Versuch: Spread 5 Basispunkte insgesamt, Slippage 5 Basispunkte je Seite, Ordergebühr null; USD, splitbereinigte IEX-Kurse, rechnerische Bruchstücke. Ergebnisse pro 1.000 USD und in initialen Risikoeinheiten; zusätzlicher chronologischer Portfoliotest mit 2.000 USD, 1 % geplantem Risiko pro Position, höchstens fünf Positionen, höchstens 25 % Kapital je Position, eine Position je Aktie. Kein Leverage. Nicht ausführbare/unvollständige Verläufe werden offen ausgewiesen.

## Ablauf und Schutz vor Ergebnisoptimierung

1. Kausalen Kern, Strukturzustand, Zonen und Gegenbeispiele testen.
2. Neuen unveränderlichen Vertrag und sämtliche neuen Code-/Datenversionen vor dem ersten Lauf speichern. Alte Aufträge nur lesend öffnen, nicht fortsetzen.
3. Gepinnte echte MSFT/AMZN/JPM/XOM/KO-Daten offline verwenden. Entwicklung 02.05.2025–18.03.2026 und bereits bekannte spätere Phase 19.03.–02.07.2026 getrennt. Der finale Holdout bleibt zunächst geschlossen.
4. Technische Fehler mit nachvollziehbarer Ursache korrigieren und betroffene Prüfungen wiederholen; Ergebnisdateien vorheriger Anläufe erhalten. Keine Schwellenwertsuche bis ein Gewinn herauskommt.
5. Gegenüber Kontrolle gepaart auf denselben verfügbaren Fällen prüfen; Horizonte zusätzlich auf konstanter Fallmenge vergleichen. Einzelaktien, Kontaktgruppen, Abdeckung, Kosten und negative Ergebnisse erhalten. Portfolio-Cash/Positionsgrößen/Gaps zusätzlich unabhängig prüfen.
6. Nur einen ausreichend belegten Kandidaten vor einer späteren unabhängigen Prüfung festhalten. Bei zu wenigen oder widersprüchlichen Fällen bleibt das Ergebnis „noch nicht für einen produktiven Strategieentscheid ausreichend“.

## Quellen und Abgrenzung

Eingereichte Kriterien: [Arbeitsnotiz](TORI-KRITERIEN-ARBEITSNOTIZ.md). Öffentlich geprüfte Beschreibungen: [Tori: Safety und Struktur](https://toritradez.com/blog/all/low-risk-trend-line-trading-break-retest-bounce), [Tori: A+-Beispiel](https://toritradez.com/blog/all/perfect-trade-trend-line-setup), [Tori-Darstellung auf TradeZella](https://www.tradezella.com/strategies/trendline-strategy). Pufferwerte, Pivotbestätigung, quantitative Zonendefinition, kombinierte Eligibility und Portfolioannahmen sind explizite eigene Operationalisierungen, keine vollständig verifizierte Originalstrategie.

Ergebnisbilanz: [SAFETY-ERGEBNISSE.md](SAFETY-ERGEBNISSE.md); vollständige Tabellen: [SAFETY-ERGEBNISTABELLEN.md](SAFETY-ERGEBNISTABELLEN.md).

## Implementierung und Verwendung durch Hermes

Der neue Kern ist ein eigener, optionaler **CLI-Forschungsweg**. Er ersetzt weder bestehende Webprofile noch laufende Queue-Aufträge oder Zeitpläne. Die manuelle Chartansicht bleibt verfügbar. Es gibt keinen Orderadapter und keine neu eingerichteten Benachrichtigungen. Neue Codeversionen müssen im Zielcontainer zunächst installiert werden; lokale Änderungen aktualisieren Proxmox nicht.

| Datei | Aufgabe |
|---|---|
| `safety_strategy.py` | Unveränderlicher Einstiegsvertrag, bekannte Widerstandszonen, vier Exitmodelle und chronologischer Safety-Zustand |
| `strategy_research.py` | Offline-Vergleich, feste Auswahlentscheidung vor späterer Phase, kausaler Kandidatenscan |
| `strategy_portfolio.py` | Eigenes Cash-/Risiko-/Positionsledger, 5m-Bewertung und Abbruch bei fehlendem gehaltenem Marktpfad |
| `strategy_verify.py` | Separater Nachrechner für Kontext, Ereignisse, Ausführungen, Decimal-Geldbeträge und Portfolios |
| `strategy_run_lock.py` | Betriebssystem-Sperre pro Versuch, automatisch freigegeben nach Prozessende |
| `strategy_identity.py` | Importübergreifender Signal-Schlüssel für die spätere Deduplizierung |
| `tools/safety_universe.py` | Vorab definierte Erweiterung auf 25 Aktien, Dataset-Wiederverwendung und abdeckungsabhängiger Replaybeginn |
| `tools/safety_data_quality.py` | Kalenderbasierte Abdeckung ohne Signal-/Renditeauswahl |
| `tools/report_safety_study.py` | Vollständige Markdown-Tabellen und Quellenprüfsummen aus gespeicherten Ergebnissen |

Befehle aus dem Anwendungsordner, unter demselben Dienstbenutzer und mit **demselben `TORI_DATA_DIR` wie der Webdienst** ausführen. In Linux beispielsweise `export TORI_DATA_DIR=/var/lib/tori`; Pythonpfad an Installation anpassen. Die folgenden Pfade und IDs sind Platzhalter:

```sh
python tori.py strategy-rules
python tori.py strategy-export --job DEVELOPMENT_JOB --phase development --validation-job VALIDATION_JOB --output /var/lib/tori/research/safety-entries.json
python tori.py strategy-study --entries /var/lib/tori/research/safety-entries.json --output /var/lib/tori/research/safety-001 --stage development
python tori.py strategy-report --study /var/lib/tori/research/safety-001
# Erst nach gespeicherter Entwicklungsentscheidung:
python tori.py strategy-study --entries /var/lib/tori/research/safety-entries.json --output /var/lib/tori/research/safety-001 --stage validation
python tori.py strategy-verify --study /var/lib/tori/research/safety-001
python tools/report_safety_study.py --study /var/lib/tori/research/safety-001 --output /var/lib/tori/research/safety-001/tables.md
```

`strategy-export` benötigt abgeschlossene Laboraufträge mit passenden Entwicklungs-/Validierungsphasen. Der Export übernimmt deren ursprüngliche, deterministisch deduplizierte Einstiege und Originalanker. Er verändert keine Laborprofile. Ein Auftrag mit Legacy-/Tori-Modus ist nicht automatisch ein passender Laborexport.

Unterbrochenen, **unveränderten** Versuch mit demselben `strategy-study`-Befehl und zusätzlichem `--resume` fortsetzen. Geänderte Quellverträge oder Engine-Dateien verlangen einen neuen Ausgabeordner. Abgeschlossene Phasen werden nicht überschrieben. Checkpoints haben Inhaltsprüfsummen; ein zweiter Schreiber erhält Fehler 409. Die Wiederaufnahme erfolgt blockweise je Dataset/Phase, nicht innerhalb einer einzelnen Position. Lokaler tatsächlicher Prozessabbruch und Wiederaufnahme wurden mit exakter Ergebnisgleichheit getestet.

Ein aktueller oder historischer Kandidatenscan benötigt ein bereits importiertes Dataset:

```sh
python tori.py strategy-scan --dataset DATASET_ID --asof 2026-07-02T20:00:00Z --since 2026-06-25T20:00:00Z --profile momentum_two
```

`--history-start` ist optional. Standard ist der erste vollständige 4h-Quelltag plus 365 Kalendertage; ein abweichender Start muss ebenfalls diesen Vorlauf erfüllen. Der gesamte Zustand ab diesem Start wird chronologisch rekonstruiert, nicht nur die letzte Kerze geprüft. **Denselben History-Start beibehalten**, wenn aufeinanderfolgende Stichtage verglichen werden sollen. `--since` begrenzt die ausgegebenen Ereignisse, nicht den Zustandsvorlauf. Nur bis `--asof` abgeschlossene Kerzen erreichen den Scanner; er ruft keine Zukunftsauswertung auf.

Die JSON-Antwort enthält:

- `observations`: historische Signale mit bereits beobachtetem folgendem Open, Originalankern, Einstiegsprüfungen und importübergreifendem `eventKey`. Das sind keine heute ausführbaren Kaufempfehlungen.
- `pending`: bestätigte Signale, deren nächstes erlaubtes Open noch nicht beobachtet wurde. Deren endgültiger Raum-/Risikotest ist noch unbekannt; kein fiktiver Kaufkurs.
- `eligibleObservations`, `setupsReplayed`, `latestSourceClose`, `latestFineClose`, `historyStartAt`, `datasetId`, `dataKind` und `feed`: Prüfbarkeit und sichtbare Datenaktualität.

Für einen späteren regelmäßigen Scanner: nach abgeschlossenem Import aufrufen, `eventKey` persistent deduplizieren, Aktualität prüfen und zunächst nur Papierbeobachtungen führen. Dieser Schlüssel bleibt bei Dataset-Aktualisierungen und zwischen Pending-/Open-Ereignis gleich; exakte Entry-/Vertrags-IDs behalten die Datenversion. Die Ausgabe hat ausdrücklich `brokerAction: null`. Persistente universumsweite Scanplanung, inkrementeller Live-Positionszustand und automatische Meldungen für diesen neuen Weg sind **noch nicht verdrahtet**. Die vorhandene Forschungsqueue bleibt ein anderer, bestehender Ablauf.

## Grenzen des technischen Modells

- Die Signalquelle bleibt die bestehende kausale Laborlogik. Zwei Kontakte sind erlaubt; Momentum-/Grundprofil sowie drei Einstiegsfamilien werden getrennt gehalten. Die neue gemeinsame Eligibility ist eine ausdrücklich eigene quantitative Tori-Auslegung, kein Nachweis, alle diskretionären Tori-Situationen abzubilden.
- Studie und Scanner greifen nach dem Import nur auf unveränderliche lokale Datasets zu. In der Studie ist der Provideraufruf zusätzlich gesperrt. Rohdaten werden nicht in Git aufgenommen. Ein Clone enthält deshalb nicht die hier lokal getesteten Kursbestände.
- IEX bildet nur einen Teilmarkt ab. Nicht vorhandene 5m-Bars werden nicht erfunden. Eine 4h-/Tagesaggregation verlangt vollständige erwartete Unterkerzen. Weniger Quellkerzen können Signale und Kontext verhindern; positive Ergebnisse auf der verbleibenden Teilmenge beweisen keine unverzerrte Vollmarktstrategie.
- Nach der ersten fehlenden erwarteten 5m-Kerze ist ein noch laufender Einzelpfad unvollständig. Ein Portfolio mit einer dort gehaltenen Position stoppt alle späteren Entscheidungen. Es zeigt dann nur ein Präfixvermögen und ausdrücklich keine volle Phasenrendite. Bereits vorher bekannte Verkäufe bleiben gültig.
- Ziel und Stop in derselben 5m-Kerze: Stop zuerst. Stopgap: verfügbarer Open. Safety-Schlussverkauf: nächster erlaubter Open nach mindestens fünf Minuten. Kapital wird konservativ erst am Ende der ausführenden 5m-Kerze freigegeben. Es gibt keine behauptete Tickgenauigkeit oder garantierte Brokerfüllung.
- `marked_to_phase_end` kann offene Positionen enthalten; Marktwert ist kein realisierter Gewinn. Drawdown ist aus abgeschlossenen 5m-Bewertungen, nicht aus jeder intrabar Preisbewegung. Ausgewiesene 1.000-USD-Einzelfälle sind von den 2.000-USD-Portfolios zu unterscheiden.
- Unterschiedliche Profile und Familien können dieselbe Marktbewegung mehrfach abbilden. Gepaarte Vergleiche reduzieren Vergleichsfehler, erzeugen aber keine unabhängige Stichprobe. Die Mindestzahl für Kandidatenauswahl ist ein Vorfilter, kein statistischer Profitabilitätsnachweis.

## Laufprotokoll

1. **Erste technische und wirtschaftliche Prüfung:** Implementierung unter Commit `af03c1f`, isolierter Bestand `artifacts/safety-strategies-20261020-a`. 523 Entwicklungs- und 191 spätere Profil-/Familienfälle, vier Modelle und drei Horizonte; 8.568 Modellpfade und 288 getrennte Portfolios unabhängig geprüft. Keine Providerabrufe in der Forschung. Sechs beziehungsweise fünf Fälle bestehen die neuen gemeinsamen Eintrittsprüfungen; für die vorab bestimmte primäre Gruppe nur ein vollständiger Entwicklungsfall. Deshalb vor Öffnen der späteren Phase ausdrücklich kein Kandidat ausgewählt. Endlicher technischer Erfolg ist nicht mit bewiesener Profitabilität gleichgesetzt.
2. **Vorab registrierte Erweiterung:** Unveränderte Regeln auf zusätzlich 20 festen US-Aktien (Liste im Werkzeug `tools/safety_universe.py`), zusammen 25. Einmaliger Import und gepinnte IDs; danach Offline-Discovery ohne Zukunfts-Evaluator. Kein Austausch schlechter Aktien oder erneute Optimierung. Dies ist eine Erweiterung über Aktien im bereits bekannten Zeitraum, keine unberührte zeitliche Validierung.
3. **Datenbefund während des Imports:** Unterschiedlich viele unbesetzte IEX-5m-Zeitfenster führen bei der strikten Aggregation zu stark unterschiedlicher Zahl vollständiger Quellkerzen. Das belegt keine verlorenen Provider-Nachrichten; fehlende IEX-Prints sind eine mögliche Ursache. Bei COST beginnt die erste vollständige 4h-Quellkerze erst am 11.07.2024. Die gewünschte gemeinsame Replay-Historie ab Mai 2025 reicht damit unter der bestehenden Ein-Jahr-Vorlaufregel dort noch nicht. Diese Grenze wird offen als Datenabdeckung behandelt, nicht durch erfundene Bars oder einen Ausschluss anhand der späteren Rendite behoben.
4. **Betriebshärtung:** Eigene OS-Dateisperre pro Strategieauftrag, ohne die bestehende Queue-Sperre zu verwenden. Zweiter Schreiber wird abgewiesen; Betriebssystem gibt die Sperre nach Prozessabbruch frei. Neue Engine-Version erfordert einen neuen Versuch; alte Ergebnisse und Checkpoints bleiben erhalten. Unterbrochene unveränderte Versuche können pro abgeschlossenem Aktien-/Phasenblock wiederaufgenommen werden.
5. **Erweiterung abgeschlossen:** Alle 25 festen Aktien offline rekonstruiert; 2.083 Entwicklungsfälle und 840 spätere Fälle. 21 beziehungsweise sieben bestehen sämtliche Eintrittsprüfungen. Der vorab festgelegte primäre Test hat weiterhin nur einen vollständigen Entwicklungsfall; keine Kandidatenauswahl. 35.076 Modellpfade und 288 Portfolios separat nachgerechnet. Keine neue Hypothese anhand der späteren Rendite eingeführt.
6. **Importübergreifende Signalidentität:** Dataset-/Entry-IDs allein eignen sich nicht zur Benachrichtigungsdeduplizierung, weil ein Import neue Datenversionen erzeugt. Neuer `eventKey` verwendet den physischen Bestätigungszeitpunkt und Marktkontext ohne Dataset-ID. Versionswechsel in frischem Versuch `safety-strategies-20261020-final`; exakter Vergleich bestätigt unveränderte Einstiege, Verträge, Ausstiege, Portfolioergebnisse und Blocker beider Phasen. Ein echter MSFT-Scan an zwei aufeinanderfolgenden Stichtagen bestätigt die Wiedererkennung und identische archivierte Originalentries. Keine Providerabrufe dabei.
