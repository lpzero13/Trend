# Technische Strategiesuche: positive Kandidaten, Kontrolltor noch offen

Abschlussstand **30.10.2026**, lokal und vollständig offline. Keine Webentwicklung. Grundlagen: [Pilot](BACKTEST-PILOT.md), [vorab festgelegte Runde 1](STRATEGIE-SUCHE-PLAN-20261030.md), [dokumentierter Folgeplan](STRATEGIE-SUCHE-FOLGEPLAN-20261030.md).

## Ergebnis in einem Satz

Ein qualifizierter 4h-Ausbruch mit gültiger Safety, festem Initialstop und höchstens 40 Handelstagen Haltedauer ist ein positiver weiterzuprüfender Kandidat: im späteren ursprünglichen Achterkorb **+14,59 %**, im vorab benannten gemeinsamen 16er-Korb **+16,90 %** nach modellierten Kosten. Das vorab festgelegte Vergleichstor zu Zufallsportfolios wurde jedoch nicht bestanden. Daher keine Freigabe als belegte Signalüberlegenheit und keine Garantie zukünftiger Erträge.

## Daten, Scope und Prüflogik

- Runde 1 auf AAPL/JPM/JNJ/XOM/KO/CAT/HD/NEE. Entwicklung: Entry-Jahre 2019, 2020, 2022; zeitlich späterer Test: 2024. Jeder Fold startet mit eigenem Kapital und umfasst zusätzlich seinen deklarierten Nachlauf. Keine zusammengesetzte Mehrjahresrendite aus diesen Fold-Zahlen ableiten.
- 30 vorab begrenzte Varianten: drei Entry-Familien, rote Kontaktklassen alle/qualifiziert, Bounce nur qualifiziert, drei Stopführungen, Tages-SMA200 aus/an, zunächst 20 Handelstage maximale Haltedauer. Quelle ist die gemeinsame kausale Master-Geometrie. Keine nachträglich gezeichnete Linie als früheres Signal.
- Runde 2: weitere 30 Varianten mit ausschließlich längerer maximaler Haltedauer von 40 Tagen. Auswahl erneut in denselben Entwicklungsfolds; der erste Prüfblock 2024 gilt danach als bekannte Entwicklungsinformation. Späterer Test: Entries 01.04.2025–31.03.2026, Nachbeobachtung bis 30.06.2026. Das ist kein Nachweis, dass historische Kurse in älteren Projektarbeiten nie betrachtet wurden.
- Anschließend feste Übertragbarkeitsprüfung auf IBM/GS/MRK/CVX/PG/HON/MCD/VZ im nun bekannten späteren Zeitraum. Keine weitere Parameterwahl. Zusätzlich derselbe feste Kandidat auf allen 16 Aktien gemeinsam.
- Insgesamt 48 unterschiedliche Aktien-/Entry-Zeitfenster und 2.575 unterschiedliche gespeicherte Signalfälle in diesen Fenstern. Wiederverwendung der Entwicklungssignale für andere Exits macht daraus keine neuen unabhängigen Stichproben. Zusätzlich zur Auswahl gab es ausdrücklich nachträgliche Sensitivitätsdiagnosen; sie wurden nicht als neue unabhängige Bestätigungen oder zur Umbenennung des Siegers verwendet.
- Alle Daten bereits lokal vorhanden, SIP/split, reguläre Sitzungen. Die heutige Auswahl großer überlebender Aktien ist kein historisch vollständiges Universum. Keine neuen Providerimporte; der frühere 100er-Auftrag bleibt bei 69 fertigen Aktien pausiert.

## Gemeinsame Kapital- und Ausführungsregeln

**2.000 USD Gesamtmodellkapital**, ganze Aktien, höchstens drei offene Positionen und höchstens eine pro Symbol, maximal 25 % Allokation und 1 % geplantes Risiko je Entry. Gleichzeitige Signale konkurrieren deterministisch nach Symbol/ID um Cash und Plätze; keine spätere Gewinnsortierung. Die Auswahlreihenfolge ist nicht optimiert.

Signal am abgeschlossenen 4h-Intervall, Modellkauf am nächsten erwarteten regulären 5m-Open nach 300 Sekunden. Safety am tatsächlichen Signal gültig und unter dem Kurs; bei roten Episoden bleibt der ursprüngliche Widerstand gebunden, alte Bruch-Safety/Stop bleiben zusätzlich archiviert. Initialstop 0,3 % unter der Signal-Safety, Tickabrundung. Hard-Stop auf 5m-OHLC, Gap-Fill am verfügbaren Open mit Kosten. Künftige Datenlücken dürfen einen später nicht auswertbaren Fall nicht vorab aus der Auswahl entfernen; ein betroffenes gehaltenes Depot stoppt an der Lücke.

Basiskosten: fünf Basispunkte Gesamtspread und fünf Basispunkte zusätzliche Slippage je Ausführungsseite; jede Seite trägt einen halben Spread. Null fixe Ordergebühr in der Basisauswertung. Doppelte Kosten verdoppeln Spread und Slippage; Positionsgrößen können sich dadurch ebenfalls ändern. Zusätzlich feste Ordergebühren geprüft. Keine Dividenden, Cashzinsen, Steuern oder EUR-/USD-Umrechnung. Ergebnisse sind Modell-Preis-P/L, keine echten Brokerabrechnungen.

## Runde 1: 20 Handelstage

Sechs der 30 Varianten erfüllen die Entwicklungstore. Der globale Entwicklungsgewinner ist **qualifizierter Ausbruch, fester Stop, kein SMA200-Filter**. Die Entwicklungsfolds liefern +7,28 %, +3,94 % und +0,46 %; 92 tatsächlich akzeptierte Trades, schlechtester gemessener 5m-Drawdown −7,61 %. Beim Weglassen jeweils einer Aktie bleibt der mittlere Entwicklungsfold-Ertrag positiv.

Nur die vorher festgelegten Familiensieger wurden anschließend auf 2024 geprüft:

| Familiensieger | Netto | Doppelte Kosten | Urteil |
|---|---:|---:|---|
| Qualifizierter Ausbruch, fester Stop | +3,00 % | +2,00 % | Cash-/Risiko-/Streuungstore bestanden, Kontrollvergleich nicht bestanden |
| Qualifizierter roter Retest, fester Stop | +7,25 % | +6,70 % | Positive Beiträge knapp über der vorab gesetzten Konzentrationsgrenze auf eine Aktie konzentriert |
| Qualifizierter Safety-Bounce, ursprüngliche Safety fortschreiben | −2,75 % | −4,07 % | Negativer späterer Befund |

Für den primären Ausbruch: 34 Trades, 2.059,92 USD Endkapital, −3,64 % 5m-Drawdown. Unter 39 zeitlich/aktienweise bedingten Zufallsportfolios liegt der Median bei +6,23 %, das 90-Prozent-Quantil bei +11,45 %. Damit wurde das **gesamte vorab festgelegte Tor nicht bestanden**. Der ursprünglich reservierte nächste Block wurde in diesem ersten Protokoll nicht als automatische Bestätigung geöffnet.

## Runde 2: 40 Handelstage

Der Folgeplan wurde vor Auswertung des späteren Blocks registriert. Wieder werden sechs Varianten in der Entwicklung zugelassen. Primär bleibt **qualifizierter Ausbruch, fester Stop, kein SMA200-Filter**, jetzt maximal 40 Handelstage. Entwicklungsfolds: +13,95 %, +10,81 %, −1,30 %; 73 tatsächlich akzeptierte Trades.

Späteres Entry-Fenster April 2025 bis März 2026 mit Nachlauf bis Juni 2026:

| Vorher festgelegter Familiensieger | Netto | Doppelte Kosten | 5m-Drawdown | Trades |
|---|---:|---:|---:|---:|
| Qualifizierter Ausbruch, fester Stop | **+14,59 %** | **+13,86 %** | **−3,22 %** | 25 |
| Qualifizierter Safety-Bounce, fester Stop | +10,60 % | +9,69 % | −4,48 % | 31 |
| Qualifizierter roter Retest, fester Stop | +7,50 % | +8,06 % | −7,05 % | 19 |

Die höhere Retest-Rendite unter doppelten Kosten ist durch die ganze Stückzahl und dadurch andere Positionsgrößen/Belegungen möglich; sie bedeutet nicht, dass höhere Gebühren einzelne identische Trades verbessern.

Primärer Ausbruch: 2.291,86 USD Endkapital, fünf Aktien mit positiven realisierten Beiträgen und größter Anteil an den positiven Aktienbeiträgen 35,23 %. Alle vorab gesetzten Cash-/Streuungs-/Drawdown-/Kostentore bestanden. Aber: Kontrollmedian +11,75 %, 90-Prozent-Quantil +18,52 %; der Kandidat schlägt 25 von 39 Kontrollen, nicht deren oberstes Zehntel. **Das vollständige ursprüngliche Kontrolltor bleibt nicht bestanden.**

Die Kontrollen entsprechen monatlicher Signalanzahl, Aktie, gültiger damaliger Safety und gegebenenfalls Tagesfilter. Rote Kontaktqualität wird nicht gematcht. Ziehen mit Zurücklegen kann identische Kontrollzeitpunkte erzeugen; das gemeinsame Kapitalbuch behandelt auch diese mit Symbol-/Positionsgrenzen. Der Vergleich ist explorativ, kein über alle 60 untersuchten Auswahlvarianten korrigierter p-Wert. Eine nachträglich interessante Rendite-/Drawdown-Kennzahl ändert das vorab festgelegte Tor nicht.

## Übertragung auf weitere Aktien und gemeinsames Depot

Die Regel bleibt unverändert. Der Zeitraum ist bereits bekannt; dieser Abschnitt prüft die Übertragbarkeit auf andere Aktien, keine neue zeitliche Unabhängigkeit.

| Korb | Netto | Endkapital aus 2.000 USD | Doppelte Kosten | 5m-Drawdown | Trades |
|---|---:|---:|---:|---:|---:|
| Ursprüngliche acht Aktien | +14,59 % | 2.291,86 USD | +13,86 % | −3,22 % | 25 |
| Zusätzliche acht Aktien | +4,41 % | 2.088,14 USD | +3,53 % | −6,03 % | 31 |
| **Alle 16 gemeinsam** | **+16,90 %** | **2.337,97 USD** | **+16,06 %** | **−4,52 %** | **30** |

Im zusätzlichen Achterkorb tragen nur zwei Aktien positiv bei, CVX liefert 78,26 % der positiven Aktienbeiträge. Sein eigenes breites Streuungstor ist nicht bestanden; auch die Kontrolle ist stärker. Im gemeinsamen 16er-Korb sind zehn Aktienbeiträge positiv und der größte Anteil an positiven Beiträgen beträgt 30,38 %. Es gibt **160 passende Ausbruchssignale**, aber nur 30 ausführbare Depot-Trades: 88 Kandidaten entfallen wegen voller Positionsplätze, weitere wegen bereits gehaltener Aktie, Stückzahl oder ungültigem Stop/Gap.

Die 16er-Zahl ist keine Summe der Achterdepots und wurde nicht nachträglich aus dem besseren Korb ausgewählt. Alle Signale konkurrieren um dasselbe Gesamtmodellkapital. Kein annualisierter Ertrag: zwölf Monate Entry-Zulassung plus deklariertem Nachlauf.

## Nachträgliche Belastungsdiagnosen

Nur auf dem bereits ausgewerteten ursprünglichen Achterkorb, ohne neue Siegerwahl oder Änderung der festgelegten 40-Tage-Regel:

- Weglassen jeder einzelnen Aktie: spätere Nettoergebnisse zwischen **+8,77 % und +18,51 %**, alle positiv.
- Gleiche Signale/Preise, andere maximale Haltedauer: 20 Tage +7,36 %, 30 Tage +20,14 %, 40 Tage +14,59 %, 50 Tage +17,40 %. Das Kapitalbuch kann wegen anderer Haltedauer unterschiedliche spätere Trades zulassen. Die 30-Tage-Zahl wird nicht nachträglich als ausgewählte neue Strategie ausgegeben.
- Ausführungsverzögerung 0/300/600/900 Sekunden: etwa +14,57 / +14,59 / +14,65 / +14,68 %. Null Sekunden ist eine idealisierte Vergleichsannahme.
- Zusätzlich 1 USD fixe Gebühr je Kauf und Verkauf: **+12,38 %**; 2 USD je Order: **+9,61 %**.
- Getrennt zurückgesetzte Kapitalbücher für die erste/zweite Hälfte des Entry-Fensters: +10,40 % / +10,20 %. Nachläufe überlappen; weder unabhängig noch zu addieren.

Diese Diagnosen sprechen gegen einen einzigen punktgenauen Parameter-/Aktienausreißer, sind aber keine neue unabhängige Bestätigung.

## Technische Umsetzung und Nachweise

- `strategy_screen.py`: vorab gebundener Plan, zwei lokale Rechenprozesse, kleine komprimierte Prüfsummen-Caches, Entwicklungsauswahl und spätere Tests getrennt.
- `screening_portfolio.py`: Adapter zum vorhandenen Cashledger, bekannte Entryfilter, echte Budget-/Belegungsgrenzen, Kostenneuberechnung und separate Buchungsprüfung.
- `screening_extension.py`: Folgeversuch mit dokumentierter neuer Haltedauer; alte Resultate bleiben bestehen.
- Headless-Werkzeuge in `tools/`: explizite Phasen, lesbare Berichte, getrennte Sensitivitätsdiagnosen, feste weitere Aktien und Offline-Nachprüfung. Keine zusätzlichen Runtime-Abhängigkeiten.
- Die drei Hauptstudien umfassen **313 unabhängig nachgerechnete Kapitalbücher** einschließlich doppelter Kosten und Zufallskontrollen. Spätere primäre Ledger wurden aus den gespeicherten Quellfällen erneut simuliert, Entwicklungswahl beziehungsweise Übernahme reproduziert, Caches und Codebindung geprüft. Weitere Belastungsbücher ebenfalls separat auf Cash nachgerechnet.
- **479 Python-Testfälle ohne Fehler, ein bestehender Skip; alle 70 Web-/Chart-JavaScript-Tests bestanden.** 15 zusätzliche gezielte Tests prüfen endliches Kapital, Stückzahlen, Konflikte, Kosten, unbekannte Zukunftspfade, unveränderte Auswahl, Datenblock-Grenzen, Cacheintegrität und festen Korbtransfer.

Beispielkommandos aus dem Anwendungsordner, im Container mit demselben `TORI_DATA_DIR` wie der Dienst:

```text
python tools/run_strategy_screen.py --root PRIVATER_ORDNER_R1 --phase development
python tools/run_strategy_screen.py --root PRIVATER_ORDNER_R1 --phase validation
python tools/run_screening_extension.py --root PRIVATER_ORDNER_R2 --base PRIVATER_ORDNER_R1 --phase development
python tools/run_screening_extension.py --root PRIVATER_ORDNER_R2 --base PRIVATER_ORDNER_R1 --phase validation
python tools/test_fixed_basket.py --root PRIVATER_ORDNER_KORB --source PRIVATER_ORDNER_R2 --phase test
python tools/verify_strategy_screen.py --root PRIVATER_ORDNER_R2
python tools/report_strategy_screen.py --root PRIVATER_ORDNER_R2 --output PRIVATER_BERICHT.md
```

Die Vorbereitungswerkzeuge dieser konkreten Untersuchung lösen ihre Dataset-IDs aus dem vorhandenen lokalen Referenzarchiv auf. Fehlt dieser Auftrag in einem anderen Container, scheitern sie ausdrücklich; sie starten keinen Ersatzimport. Für ein anderes Universum oder geänderte Engine einen neuen Versuchsplan registrieren und die Auswahl vor Ergebnissen festlegen. Das allgemeine `tori.py pilot-backtest --dataset ...` bleibt unabhängig davon mit beliebigen geeigneten lokalen IDs nutzbar.

Aktuelle private Ergebnisse liegen unter `artifacts/strategy-screen-20261030/`, `artifacts/strategy-screen-followup-20261030/` und `artifacts/strategy-screen-external-20261030/`. Pläne, Auswahlzustände, vollständige Ledger, Kurs-/Signalspeicher und persönliche Daten werden nicht veröffentlicht. Alte Ausgaben werden bei neuen Diagnoserunden erhalten.

## Bewertung und weiterer technischer Fokus

Wir haben **positive, wiederholbar berechnete Kandidaten**, mehr als nur einen einzelnen glücklichen Entry und ein funktionsfähiges gemeinsames Kapitalbuch. Ein pauschales Versprechen „die Tori-Signale schlagen Zufall“ wäre dennoch nicht gedeckt. Die beste aktuell festgehaltene Hypothese bleibt der qualifizierte Ausbruch mit festem Stop und maximal 40 Handelstagen; engere Fächerstopps oder SMA200-Filter verbesserten die Auswahl nicht automatisch.

Weitere technische Arbeit sollte eine unveränderte prospektive Beobachtung, realistischere Kostendaten und eine breitere, vorher festgelegte Daten-/Regimeprüfung priorisieren. Der bereits betrachtete Zeitraum ist verbraucht. Keine weitere Parameterwahl auf denselben Testdaten als neue Bestätigung ausgeben. Webansicht, autonome Meldungszustellung, Containerinstallation und Brokerorders sind durch diese Untersuchung nicht umgesetzt.
