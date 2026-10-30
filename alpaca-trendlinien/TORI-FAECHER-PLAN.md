# Tori-Fächer und kausaler Backtest

Umsetzungsauftrag vom 29.10.2026, eigener optionaler Modus. Bestehende Chart- und Forschungsregeln bleiben wählbar. Kein Upload, Container-Rollout, neuer Providerimport, Zeitplanwechsel oder Brokerauftrag Bestandteil dieser Arbeit.

## Abnahmeziele

1. Korrigierten Pine-Master-Linienfinder nach Python übertragen: Wilder-ATR, bestätigte Pivots, historische Kontakttoleranzen, Abstand, Körper-/Docht-Hülle, Fächer, Kalenderalter, begrenzter Suchhorizont. Ein unabhängiger langsamer Prüfer vergleicht die Geometrie. Pine-Stichtagsmodus und fortlaufende Kandidatenentdeckung ausdrücklich unterscheiden.
2. Gleicher Rechenkern für Chart und Headless. Optionaler Fächer-Modus, Analyse beim normalen Chartstart weiterhin aus. 1h/4h/1D und abgeschlossene 1W-Ansicht, Quellenintervalle bleiben getrennt. MTF-Projektion ist kein Signal.
3. Kerze-für-Kerze-Beobachter: vorab bekannte Kandidaten, feste Linienidentitäten, Qualifikation vor Ausbruch, bestätigter Ausbruch und späterer Retest der ursprünglichen roten Linie getrennt. Safety beim Signal einfrieren, neue aktuelle Linien ersetzen keine alte Episode. Zwei Kontakte und qualifizierte Fälle getrennt; Reaktionsmerkmale erfassen.
4. Zufällige Startpunkte ohne Ergebnisfilter; ab X weiter bis zum ersten späteren Entry je Variante oder ehrlichem Datenende. Starts mit Entry, eindeutige Entries und ungelöste Fälle getrennt ausweisen. Keine erzwungenen Entries, keine künstliche Gleichsetzung von Versuchen und unabhängigen Trades.
5. Explizites Ausführungsmodell mit nächstem erwarteten regulären 5m-Open nach Signal/Verzögerung, Stop, Gaps, Kosten und konservativer OHLC-Reihenfolge; fehlende Daten zensieren statt überspringen. 5/10/20-Sitzungsbeobachtungen und unabhängige Stop-/Exit-Modellpfade. Keine Portfolio-Rendite aus Fallmittelwerten behaupten.
6. Bestehende Queue/Status/Abbruch/Paginierung und Datenspeicherung verwenden. Neue Enginebindung, Offline-Wiederholung/Wiederaufnahme und Datasetreferenzschutz; keine automatische Fortsetzung alter Jobs unter neuem Code. Webbedienung und JSON-CLI für Hermes.
7. Tests mit Gegenbeispielen: Zukunftsänderungen, Pivotverfügbarkeit, Kontaktgruppen, alte gebrochene Linie, Retest/Safety-Verwechslung, Ausführung am nächsten Open, Gap, Stop/Target in einer Kerze, Datenlücke, Kosten, Duplikate, Startauswahl, Abbruch/Wiederholung, Chart/Headless-Übereinstimmung. Gesamtsuites und lokaler HTTP-/Browserdurchlauf mit eindeutig markierten Technikdaten; zusätzlicher begrenzter Offline-Marktversuch ohne neue Imports.

## Leitplanken

Die Linie allein beweist keinen Handelsvorteil. Parameter sind Forschungsannahmen. Identische Eingabekerzen können algorithmisch verglichen werden; unterschiedliche TradingView-/Alpaca-Feeds, Sessions und Bereinigungen müssen nicht dieselben Linien ergeben. A+ des Master-Skripts ist nur drei Kontakte plus Mindestalter, nicht automatisch das gesamte Jilly-Regelwerk. Einzelne Kontaktpunkte sind noch kein Beweis unabhängiger Abprallreaktionen.

Der erste Fächer startet am Extrempivot wie im korrigierten Pine. Mehrere Startanker sind ein getrenntes Experiment. Die strenge kausale Entdeckung verwendet den aktuellen abgeschlossenen Präfix; der Pine-Schnappschuss mit ausgespartem Ausbruchsfenster dient als Vergleich, nicht zum nachträglichen Erzeugen alter Entries.

Die sieben Abnahmeziele sind lokal umgesetzt und geprüft. Konkreter Berechnungsvertrag, Gesamttests, Browser-/Queue-/Restore-Abnahme und begrenzter echter Marktversuch stehen in [TORI-FAECHER.md](TORI-FAECHER.md) und HERMES.md. Dieser Plan allein ist kein Abschlussnachweis und keine Profitabilitätsfreigabe.
