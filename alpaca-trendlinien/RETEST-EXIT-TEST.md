# Retest-Exitversuch vom 22.10.2026: vorab festgelegter Vertrag

Interner lokaler Vergleich auf unveränderten archivierten Einstiegen. Keine Web-/Workerumstellung, Orders, Nachrichten, Imports, Uploads oder Containeränderungen. Die bisherigen Zeiträume und Schlusskursbeobachtungen sind bereits bekannt; keine behauptet unberührte Validierung und keine Parameteroptimierung. Der finale Holdout bleibt ohne Ergebnisauswertung.

## Unveränderliche Auswahl

- Quelle: Vertrag und geprüfte Fallblöcke aus `artifacts/entry-discovery-20261021-b`, 25 gepinnte reale splitbereinigte Alpaca-IEX-Aktien.
- Nur Familie `retest`, Geometrien `hull_exact` und `swing_zone`, getrennt. Alle aufgezeichneten Einstiege bleiben erhalten; kein neuer Entry-Scan, keine Auswahl nach späteren Gewinnen, Kontakten, Risiko oder Raum. Deduplizierung innerhalb einer Geometrie nach Aktie/Entryzeit; mehrere Geometrien nicht als unabhängige Stichprobe behandeln.
- Entwicklung 02.05.2025–18.03.2026 und bereits bekannte spätere Phase 19.03.–02.07.2026 getrennt; Regeln bleiben danach gleich.
- Hauptgruppe: vollständige erwartete 4h-Kerzen zwischen frühestem roten/grünen Linienanker (oder Beginn der 15 für Signal-ATR benötigten Quellkerzen, falls früher) und Signal. Prüfung ausschließlich aus damals bekannten Daten. Fälle mit Lücken als eigene Diagnosegruppe erhalten.
- Zehn XNYS-Sitzungen strikt nach dem Entrytag. Für den Hauptvergleich und die Kapitalrechnung muss das geplante Ende innerhalb der jeweiligen Phase liegen; reine Kalendergrenze, keine Kursauswahl. Spätere Einstiege werden separat als kalenderzensiert gezählt. Kein stiller Wechsel auf verfügbare spätere Kurse.

## Genau zwei Exitmodelle

1. `fixed`: archivierter anfänglicher gepufferter Stop unverändert; sonst Verkauf zum Schluss der zehnten Sitzung.
2. `higher_low_stop`: exakt derselbe anfängliche Stop; nur nach bestätigter Tori-Struktur anheben, sonst ebenfalls Schluss der zehnten Sitzung. Bestehende `SafetyState`-Kriterien: tiefer Wendepunkt mit zwei linken und zwei geschlossenen rechten Nachbarn nach Entry, höher als aktives B, neues höheres Zwischenhoch, verbundene steigende grüne Gerade ohne Dochtschnitt, streng höher und unter aktuellem Schluss. Neuer horizontaler Stop unter bestätigtem Tief mit max(0,01 USD, 0,25 aktueller bekannter 4h-ATR14); nie lockern. Kein zusätzlicher Exit nur aufgrund eines Schlusses unter der projizierten grünen Geraden. Keine Gewinnschwelle, Breakeven-Automatik, festes Take Profit oder Zieloptimierung.

Ein Ersatz wird frühestens fünf Minuten nach Bestätigung wirksam. In dieser Zeit gilt der alte Stop. Kurslücke unter wirksamem Stop: Ausführung am vorhandenen nächsten regulären 5m-Open; Intrabar-Berührung: Stoppreis. Zeitexit: tatsächlicher Schluss der letzten erwarteten 5m-Kerze. Spread/Slippage zusätzlich auf Ausführungsbasis, keine Garantie echter Stopausführung.

Archivierter Stop wird **nicht ein zweites Mal gepuffert**. Der rohe Safetywert dient nur dazu, den bestehenden Entryvertrag nachzurechnen; gespeicherter Stop und rekonstruierter Stop müssen übereinstimmen. Die alten strengen Eligibility-Grenzen bleiben Diagnose, werden nicht nachträglich auf diese Einstiege angewendet.

## Datenlücken, Vergleich und Kennzahlen

Jede erwartete 5m-Kerze vom Entry bis zum jeweiligen Exit muss vorliegen. Fehlt sie vorher, bleibt das Ergebnis unbekannt. Ein bereits vorher regelgerecht geschlossener Trade bleibt bekannt. Beide Modelle bekommen exakt dieselben Entryfälle. Gepaarte Vergleiche nur für Fälle mit zwei bekannten Abschlüssen; zusätzlich eine gleiche vollständig beobachtete Zehn-Tage-Strecke als diagnostische Auswertungsmenge, niemals als Vorauswahl einer Handelssimulation.

Kennzahlen: Netto-R pro Modell, durchschnittlicher Gewinn/Verlust in R, Gewinnanteil, Profitfaktor (Summe positiver zu absoluten negativen R), längste Verlustserie chronologisch nach Exitzeit, maximale zwischenzeitliche Verlustserie in summiertem Einzeltrade-R (kein Depotdrawdown), Gründe/Zeiten der Exits und Zahl bestätigter Stopanhebungen. Vergleich zum reinen Zehn-Tage-Schlusskurs hält ursprüngliche Stopverluste sichtbar. R entspricht bestehendem Vertrag `kostenbehafteter Kaufpreis − ursprünglicher Stop`; Stopverkaufskosten können einen Verlust größer als −1R machen. USD pro Fall beziehen sich auf 1.000 USD unabhängigen Einzelpositionseinsatz, niemals summierte Depotperformance. Große Gewinner und wegfallende beste Fälle rein diagnostisch, keine Falllöschung zur Modellwahl. Gepaarte R-Differenzen mit beschreibendem Aktie-/Quartal-Blockintervall, keine Signifikanzbehauptung nach Modell-/Familienauswahl.

Kosten unverändert: 5bp Gesamtspread, 5bp Slippage je Seite, keine feste Ordergebühr. Fraktionale Stücke als Modellannahme.

## Kapitalrechnung

Vorhandenes chronologisches Cash-/Risikoledger wiederverwenden: jede Phase startet unabhängig mit **2.000 USD**, höchstens **1 %** modelliertes Stoprisiko je Position, höchstens **25 %** Aktienallokation je Position, maximal **fünf** gleichzeitige Positionen, nur eine je Aktie, kein Hebel. Alphabetische/stabile Reihenfolge bei identischem Entryzeitpunkt, keine Gewinnerpriorisierung. Nicht 2.000 EUR: alle Kurse und die Simulation sind in USD. Keine Währungsumrechnung angenommen.

Primär nur vollständige bekannte Vorgeschichte und kalendarisch innerhalb der Phase beobachtbare Zehn-Tage-Entries. Für den Depotlauf **keine nachträgliche Auswahl anhand zukünftiger Pfadvollständigkeit oder Exitgewinn**. Wird während einer gehaltenen Position eine erwartete 5m-Kerze unbekannt, hält der Lauf an und darf keine vollständige Phasenrendite ausweisen. Unterschiedliche Modellabbrüche nicht als vollständigen Performancevergleich darstellen. Kein Ausweichen auf ein anderes Modell wegen Datenlücken. Cash, akzeptierte/übersprungene Entries, offene/geschlossene Positionen und maximaler 5m-Stichprobendrawdown ausweisen.

## Prüfung und Entscheidung

Gezielte Tests für identischen Anfangsstop, keinen doppelten Puffer, bestätigte Anhebung/Wirksamkeitslatenz, keine Lockerung/Originalankeränderung, Stopkurslücken, Schluss unter Diagonale ohne Stopkontakt, fehlende Pfade, Zukunftsimmunität und kausale Historienauswahl. Vollständige relevante Python-/JS-Suiten; keine Browserprüfung erforderlich, da kein Webcode geändert wird.

Separater Nachrechner rekonstruiert Exit/Stopereignisse und Decimal-P/L/R sowie Kapital-/Risikoledger. Ergebnisse mit kleinen Gruppen, überlappenden Positionen, Datenmängeln und bereits bekannten Prüfzeiträumen kennzeichnen. Primäre Frage: Verbessert `higher_low_stop` in der vollständigen Vorgeschichtsgruppe die gepaarte mittlere Netto-R gegenüber `fixed`, ohne einen Vorteil durch verschiedene Entries oder ungleiche unbekannte Fälle vorzutäuschen? Keine garantierte positive Antwort.
