# Interne Einstiegssuche: Umsetzung und Bilanz vom 21.10.2026

**Technisch funktioniert die zusätzliche Suche. Mehr Kandidaten sind möglich; bessere direkte Einstiege sind bisher nicht belegt.** Als Ergänzung für Hermes ist die frühe Beobachtung brauchbar. Einen automatischen Kaufstandard würde ich daraus noch nicht machen. Retests bleiben die interessanteste weiter zu prüfende Familie.

Der Versuch ist vom laufenden Programm getrennt. Chart, bisherige Profile, Forschungsqueue und Zeitpläne werden nicht umgestellt. Die Webansicht startet weiter mit ausgeschalteter Tori-Analyse. Kein Upload, Containerupdate, neuer Datenabruf, tatsächlicher Nachrichtenversand oder Brokerauftrag wurde durch diesen Versuch ausgelöst.

## Was umgesetzt wurde

| Vorschlag | Interne Umsetzung |
|---|---|
| Mehr als die jeweils ausgewählte rote/grüne Hüllenlinie | Bestätigte Wendepunkte mit 2+2 Nachbarn, Punktpaare in 30/90/365 Kalendertagen, höchstens zehn jüngste Wendepunkte je Seite/Fenster |
| Subjektive Nähe zum dritten Kontakt messbar machen | Bei Aufnahme eingefrorene 0,10-ATR-Zone; neue Reaktion erst nach späterem Schluss 0,50 Aufnahme-ATR außerhalb und mindestens zwei Quellkerzen Abstand; angrenzende Berührungen sind eine Episode |
| Tori-Regel nicht still ändern | Strenge Docht-Hülle und ausdrücklich abweichende Docht-Zonenvariante getrennt; Körper dürfen in der Zonenvariante die Mittellinie nicht schneiden |
| Nicht nur einen perfekten Einstieg suchen | Zustände Struktur, Annäherung, Ausbruch, Rücklauf, Retest, ungültig und abgelaufen; frühe Hinweise ohne vollständige strenge Eligibility |
| Varianten statt vermischter Treffer | Direkter Ausbruch, zusätzliche horizontale Bestätigung, späterer Retest und explorativer Bounce separat |
| Kein Entry allein durch fallende Linie | Positiver Körper und Schluss oberhalb des vorherigen Schlusses beim Ausbruch |
| Fixierte Beobachtung | Ursprüngliche Anker/Bandbreite bleiben erhalten; alte rote Linie zuerst gegen neuen Schluss prüfen, dann neue rote Linien aufnehmen; maximal 60 Quellkerzen |
| Geeignete Absicherung | Ursprüngliches Grün bei Aufnahme und nächstes gültiges Grün am Signal separat protokolliert; 0,25 Signal-ATR-Puffer; ohne bekannte Safety nur Beobachtung |
| Vernünftige Priorisierung | Abstand, Reaktionszahl und geometrische Empfindlichkeit transparent sortiert; höchstens drei neue Annäherungshinweise je Aktie/Modell/Schluss; keine Gewinnwahrscheinlichkeit |
| Hermes-Anbindung vorbereiten | JSON-Scanner mit gespeichertem Zustand, stabilen Ereignisschlüsseln, Wiederaufnahme und Fakten-Erklärungen; keine echte Zustellung und kein neu eingerichteter Scheduler |
| Historisch prüfen | Jede geschlossene 4h-Kerze, modellierte spätere 5m-Ausführung, fehlenden erwarteten Open zurückweisen; getrennte 5/10/20-Sitzungsbeobachtung nach Kosten und Kontrollzeitpunkten |
| Robustheit / manuelle Subjektivität | Kleine deterministische Dochtstörungen, Präfixtests, Wiederaufnahmevergleich sowie 24 verblindete bekannte Kerzenpräfixe mit Bewertungsvorlage und geometrischem Linienabgleich |

Quellcode: `entry_geometry.py`, `entry_watch.py`, `entry_study.py`, `entry_blind.py`; Werkzeuge unter `tools/entry_discovery_*.py` und `tools/entry_watch_scan.py`. Bestehende Chart-/Signalberechnungen wurden nicht ersetzt. Die neuen Varianten verwenden dieselben normalisierten Quellintervalle und Kerzenkoordinaten, sind aber eigene Forschungsmodelle. Eine spätere Webintegration müsste ausdrücklich dieselbe neue Engine verwenden.

Die Hüllenreferenz `hull_exact` übernimmt die vorhandene Liniengeometrie, verwendet aber den gemeinsamen neuen Lebenszyklus und Trigger. Die folgenden Zahlen sind deshalb **kein direkter Vorher-/Nachhervergleich mit allen alten Laboraufträgen**. `hull_episodes` isoliert die Kontaktzählung, `swing_envelope` die zusätzliche strenge Wendepunktsuche und `swing_zone` die getrennte Zonenhypothese. RANSAC/Regression ist kein zusätzlicher fünfter Motor dieses Versuchs: Die besprochenen zulässigen Wendepunktpaare werden hier deterministisch geprüft, statt Geraden beliebig durch Kerzen zu fitten.

## Prüfgrundlage und Grenzen

- Gepinnte echte Alpaca-IEX-Kurse für 25 festgelegte US-Aktien; splitbereinigt, reguläre XNYS-Sitzungen, gespeicherte 5m/1h/4h/1D-Daten. Kein nachträglicher Wechsel auf günstigere Aktien oder Datenstände.
- Entwicklung: **02.05.2025–18.03.2026**, 220 Sitzungen. Spätere Prüfung: **19.03.–02.07.2026**, 73 Sitzungen. COST mit dokumentiert späterer Datenbereitschaft. Diese Zeiträume wurden schon in früheren Untersuchungen verwendet; die spätere Phase ist kein unberührter Holdout. Der reservierte finale Zeitraum wird nicht als Ergebnis ausgewertet.
- Regeln vor diesem Vergleich in [EINSTIEGSSUCHE-INTERN.md](EINSTIEGSSUCHE-INTERN.md) festgehalten. Hauptvergleich: strenge Wendepunktvariante gegen Hüllenreferenz, Ausbruch, zehn Sitzungen, mittlere Differenz zu passenden Kontrollen.
- Vor der späteren Phase gespeicherte Entwicklungsentscheidung: **keine Verbesserung**, Differenz der mittleren Kontrollabweichung **−0,0134 Prozentpunkte**. Keine anschließende Parametersuche nach besseren Renditen.
- Kontrollzeitpunkte: gleiche Aktie, NY-Uhrzeit, Kalenderquartal, vorherige Tagesrichtung; ähnliche damals bekannte Volatilität. Auswahl ohne zukünftige Rendite oder Datenvollständigkeit. Ein bis drei auswertbare Kontrollen je Fall; zusätzlich Diagnose nur mit allen drei vollständigen Kontrollen.
- Modellkosten: 5 Basispunkte Spread insgesamt und 5 Basispunkte Slippage je Seite. Nettobeobachtung = `(Endkurs × 0,99925 / (Entry × 1,00075) − 1) × 100`. Keine bestätigten Brokerfüllungen, kein Kapital-/Positionsledger dieses Versuchs und keine behauptete Portfoliorendite. +1R/+2R-vor-Safety sind Wegdiagnosen, kein vollständiges Exitmodell.
- Fehlende Kursdaten werden nicht aufgefüllt. Für Wegkennzahlen/Tabellen nur vollständige erwartete 5m-Pfade. Unvollständige Vorläufe können bereits die Linienbildung und Signalabdeckung beeinflussen; fehlende historische Kandidaten lassen sich aus dieser Studie nicht rekonstruieren. IEX ist keine vollständige marktweite Handelsmenge. Volumen wird deshalb nicht als harter Hauptfilter genutzt.
- Die Phasen-/Aktienbestände reichen bei vollständigen 5m-Kerzen von **76,84 bis 100 %** Abdeckung; die daraus konservativ normalisierten 4h-/Tagesbestände teilweise nur von **22,88 % bzw. 14,55 %** bis 100 %. Nur **1.351 von 2.504** Modell-/Familienfällen haben zwischen frühestem Linienanker und Signal eine vollständig erwartete 4h-Historie. Die Haupttabellen sind keine ausschließlich auf lückenloser Vorgeschichte beruhende Signalstudie. Gerade positive Retest-Ergebnisse benötigen deshalb bessere Datenreplikation.
- Modell- und Familienfälle überschneiden sich. Dieselbe Aktie/Zeit wird zusätzlich eindeutig gezählt; Blockintervalle nach Aktie/Quartal sind nur beschreibend und nicht für die Auswahl aus vielen Varianten korrigiert.

Der erste technische Durchlauf `...-a` wurde nach zwei Zustandskorrekturen verworfen: Grün vor Rot bei der Initialisierung aufnehmen und bereits gemeldete Annäherungen nicht erneut in das Kontingent neuer Hinweise nehmen. Auch die Ergebnis-Hashbildung wurde für identische Wiederholungen stabilisiert. Der ausgewertete vollständige Lauf `...-b` wurde neu gerechnet. Keine numerischen Handelsparameter wurden deswegen angepasst.

## Mehr Einstiege?

| Modell, direkter Ausbruch | Entwicklung | spätere Phase |
|---|---:|---:|
| Hüllenreferenz | 232 | 76 |
| Hülle mit unabhängigen Reaktionen | 228 | 75 |
| Strenge Wendepunktlinien | 154 | 58 |
| Experimentelle Strukturzonen | 221 | 86 |
| Vereinigung aller Modelle, gleiche Aktie/Zeit nur einmal | **338** | **128** |

Die Vereinigung ist eine **nachträglich beschreibende Abdeckungsrechnung**, keine nach Ergebnissen ausgewählte Handelsstrategie. Gegenüber der Referenz sind es **45,7 %** zusätzliche Zeitpunkte in der Entwicklung und **68,4 %** in der späteren Phase. Der einzelne strenge Wendepunktmotor liefert insgesamt weniger ausführbare Einstiege. Er findet allerdings auch neue Situationen: 56 bzw. 31 Ausbruchszeitpunkte fehlen in der Referenz. Er sollte diese deshalb ergänzen, nicht pauschal ersetzen.

Warum bleibt die Anzahl begrenzt? In der späteren Phase scheitern bei der strengen Wendepunktvariante 131 Signal-/Familienversuche an fehlender bekannter Safety. Die Zonenvariante hat 139 solcher Fälle. Das ist ein wesentlicher Engpass zusätzlich zur roten Linie. Die früheren strengen Prüfungen blockieren weiterhin sehr häufig Risikoabstand und verfügbaren Raum. Diese Gründe werden protokolliert; ein enger Stop wird nicht künstlich erzeugt.

## Werden die Einstiege besser?

Ausbrüche, zehn Sitzungen; durchschnittliche Schlusskursänderung nach modellierten Kosten. `Mehr` ist die durchschnittliche Abweichung von den jeweils passenden Kontrollzeitpunkten in Prozentpunkten.

Die Nettobeobachtung nutzt alle vollständigen Pfade. `Mehr` nutzt daraus nur Fälle mit mindestens einem ebenfalls vollständig beobachteten Kontrollzeitpunkt; diese Nenner sind in den vollständigen Tabellen getrennt ausgewiesen. Fehlende Kontrollen gelten nicht als Nullrendite.

| Modell | volle Entwicklungspfade | Netto % | Mehr pp | volle spätere Pfade | Netto % | Mehr pp |
|---|---:|---:|---:|---:|---:|---:|
| Hüllenreferenz | 151 | +0,51 | −0,71 | 51 | +2,29 | +0,41 |
| Hülle mit Reaktionen | 150 | +0,46 | −0,83 | 51 | +2,29 | +0,41 |
| Strenge Wendepunktlinien | 105 | +0,50 | −0,72 | 48 | −0,18 | −1,44 |
| Strukturzonen | 150 | +1,06 | −0,37 | 69 | +1,03 | −1,64 |

**Kein belastbarer Qualitätsgewinn beim direkten Ausbruch.** Ein positives Endergebnis ist hier oft auch an passenden Vergleichszeitpunkten entstanden. Die zusätzlichen Varianten unterschreiten diese in der späteren Phase im Mittel. Auf gemeinsamer Aktien-/Quartalsabdeckung bleibt dieselbe Richtung erhalten: Referenz +0,13 pp, strenge Wendepunkte −1,69 pp, Zonen −1,79 pp. Nur Fälle mit drei vollständigen Kontrollen ergeben +1,10 / −0,13 / −0,16 pp; auch diese Diagnose beweist keinen Vorteil der neuen Ausbrüche.

Eine mechanische Forderung nach drei unabhängigen Reaktionen ist ebenfalls noch keine Lösung. Die gesonderten Dreiergruppen sind klein. Ein schönes Ergebnis wie fünf spätere Zonen-Retests mit fünf positiven Enden darf nicht als bewiesene 100-%-Trefferquote interpretiert werden.

## Retests und Frühwarnungen

**Zonen-Retest** als getrennte, weiter zu prüfende Hypothese:

| Zehn Sitzungen | Entwicklung | spätere Phase |
|---|---:|---:|
| vollständige Fälle | 39 | 17 |
| mittlere Nettobeobachtung | +2,79 % | +2,59 % |
| Median | +0,30 % | +1,62 % |
| Mittel über Kontrollen | +2,28 pp | +2,32 pp |
| beschreibendes 95-%-Blockintervall dieser Mehrentwicklung | −0,94 bis +5,22 pp | −1,53 bis +7,57 pp |

Die Intervalle umfassen auch negative Werte. In der späteren Phase wurden bei 17 Fällen nur **8-mal +1R und 2-mal +2R vor Safety** erreicht. Gute Schlusskursbeobachtungen bedeuten folglich nicht automatisch, dass ein konkreter Stop-/Take-Profit-Handel genauso gewonnen hätte. Das bereits vorhandene Exitlabor wäre der spätere Ort für eine gesonderte, vorab festgelegte Überprüfung.

Einzelne große Bewegungen beeinflussen die Mittelwerte deutlich: Der größte Entwicklungsfall liegt bei +45,16 %, der größte spätere Fall bei +22,94 %. Lässt man rein diagnostisch jeweils den besten Fall weg, sinken die mittleren Nettobeobachtungen auf +1,67 % bzw. +1,32 %. Das ist keine nachträglich geänderte Auswahlregel; die Hauptzahlen enthalten alle Fälle. Zusammen mit dem deutlich niedrigeren Entwicklungsmedian spricht es gegen eine voreilige Erfolgsbehauptung.

Die frühen Hinweise funktionieren technisch: Zonenvariante mit **505 Annäherungen** in der Entwicklung und **211** in der späteren Phase, also rund **2,3 bzw. 2,9 neue Hinweise pro Börsensitzung für das gesamte 25er-Universum**, falls nur dieses Modell verwendet wird. Einzelne Situationen und Modelle können dieselbe Aktie betreffen. Keine Hochrechnung auf tausende Titel ohne Last-/Meldungsbudgetprüfung.

Bei 68 eindeutigen späteren Entryzeiten der Zonenvariante gab es bereits vorher einen Annäherungshinweis; der mediane Vorlauf dieser Teilmenge betrug **26,5 Kalenderstunden**, einschließlich Nächten/Wochenenden. Die übrigen Einstiege hatten keinen früheren protokollierten Hinweis. Das ist ein praktikabler Ansatz für „Schau dir Aktie A genauer an“, kein Prognosebeweis.

## Technische Prüfung und offene manuelle Bewertung

- **220 Python-Tests je unter 3.12/3.13**, jeweils ein bestehender Windows-Symlink-Skip; **35 JS-Tests**. Darin 16 neue Gegenbeispiele einschließlich Kontaktfolgen, verspäteter Pivotbestätigung, Drei-Reaktions-Linie, Zukunftsimmunität, Drift, späterem Retest, unveränderten Ankern, näherer bereits bekannter Safety, fehlendem erwarteten Ausführungskurs, JSON-Wiederaufnahme, idempotentem Offline-Scan und manueller Bewertungsvalidierung.
- Separater Prüfer: **alle 2.504 Modell-/Familienfälle**, 5.095 verfügbare Horizont-Endbeobachtungen, 2.417 nicht verfügbare Endbeobachtungen; unabhängige Decimal-Rendite-/Kostenrechnung, erwartete Ausführungszeit, Signal-ATR, Stop, 5m-Pfadabdeckung, MFE/MAE und Reihenfolge von +1R/+2R/Safety. Verfügbare Endbeobachtung heißt nicht automatisch vollständiger Intradaypfad.
- Acht echte Kombinationen aus Aktie/Modell (AAPL/XOM × vier Modelle): vollständiger Replay identisch zur Wiederaufnahme aus dem Entwicklungszustand; extreme Änderungen nach dem historischen Stichtag ändern dessen Ergebnisse nicht. Das ist eine Stichprobe für diese technischen Eigenschaften, kein Test aller möglichen Kursverläufe.
- 100 ohne Ergebnisfilter deterministisch zufällig gezogene Entwicklungspräfixe, je drei kleine Störungen bekannter Dochte: geometrisch ähnliche Linie innerhalb 0,25 ATR am rechten Rand und zwanzig rechnerischen Schritten weiter in **336/384** Hüllen-, **733/777** strengen Swing- und **910/954** Zonenvergleichen. Die letzte Projektion verwendet keine zukünftigen Kurse. Das misst lokale numerische Robustheit, nicht die Qualität späterer Entries.
- 24 verblindete Fallpakete mit SVG, bekannten normierten Kerzen, manueller Bewertungsvorlage und separater Maschinenauflösung sind lokal erstellt. **Noch keine menschlichen Bewertungen vorhanden.** Der Vergleich mit deiner manuellen subjektiven Linie kann erst danach abgeschlossen werden. Es werden weder Nutzerurteile erfunden noch Gewinnercharts als Trainingsmaterial ausgegeben.
- Keine Browserprüfung für diesen internen Versuch und keine neuen Webelemente. Die bestehenden Webtests bestehen; das ist keine neue visuelle Abnahme.

## Werkzeuge und Wiederholung

Aus dem Anwendungsordner; `TORI_DATA_DIR` ausdrücklich auf den Bestand mit den gepinnten Dataset-Dateien setzen. Beim Containerbetrieb weiterhin denselben `/var/lib/tori`-Pfad nutzen. Beispiele für diesen **lokalen isolierten** Bestand:

```powershell
.venv\Scripts\python.exe tools/entry_discovery_study.py --source artifacts/safety-universe-20261020-b --root artifacts/entry-discovery-20261021-b --stage development
.venv\Scripts\python.exe tools/entry_discovery_study.py --source artifacts/safety-universe-20261020-b --root artifacts/entry-discovery-20261021-b --stage validation
.venv\Scripts\python.exe tools/entry_discovery_check.py --source artifacts/safety-universe-20261020-b --root artifacts/entry-discovery-20261021-b
.venv\Scripts\python.exe tools/entry_discovery_report.py --root artifacts/entry-discovery-20261021-b --output EINSTIEGSSUCHE-TABELLEN.md
```

Kein Providerimport durch diese Werkzeuge. Entwicklung und Entscheidung müssen vor der späteren Phase vorliegen. Manifest, Regeln, Dataset-Identitäten und Enginehashes sind fest; geänderte Engines benötigen ein neues Ausgabeverzeichnis. Alte Aufträge niemals unter geänderten Regeln fortsetzen. Prüfer und Bericht prüfen gespeicherte Checksummen; Datenstände werden beim Lesen validiert. Fortschritt wird je Aktie/Modell gespeichert. Ein Abbruch innerhalb eines Blocks rechnet diesen Block erneut, statt halbe Ergebnisse zu übernehmen.

Gespeicherter Einzelaktienscan, mit vorhandenem Dataset und Unix-Zeitgrenzen:

```text
python tools/entry_watch_scan.py --dataset DATASET_ID --model swing_envelope --start-at UNIX_START --asof UNIX_CUTOFF --state PRIVATE_STATE.json
```

Der erste Aufruf berechnet den bekannten Verlauf. Spätere Aufrufe mit identischem Beginn und höherem Stichtag verarbeiten neue abgeschlossene Kerzen. Gleicher Stichtag liefert keine neuen Meldungen/Entries. Für einen früheren Stichtag eine eigene Zustandsdatei verwenden. Neue Dataset-ID ist zulässig, wenn der bereits bekannte Präfix unverändert ist; rückwirkende Kursrevision, geänderte Regeln oder Code werden abgewiesen. Alle Meldungen bleiben als überprüfbare Liste im Zustand. Ein späterer Zusteller muss Ereignisschlüssel deduplizieren und Zustellbestätigungen verwalten; durch eine gespeicherte Liste allein entsteht keine garantierte Nachrichtenzustellung.

`tools/entry_discovery_check.py --reviews AUSGEFUELLTE_BEWERTUNGEN.json` übernimmt echte manuelle Urteile aus der Blindvorlage. Ray-Felder: `upper` (Rot=true/Grün=false), `aIndex`, `bIndex` innerhalb der gezeigten bekannten 100 Kerzen und normierte `aPrice`, `bPrice` aus `cases.json`; Endkurs am rechten Rand entspricht 100. `private-unblind.json` erst nach der Bewertung öffnen. Der Abgleich misst Linienabweichung am Stichtag und nach zwanzig rechnerischen Schritten in damaliger ATR. Die SVGs zeigen Form und Kerzenfolge ohne Preis-/Aktiennamen; sie sind keine neue Webansicht.

Lokale Belege: `artifacts/entry-discovery-20261021-b/contract.json`, Phasen-Unterordner, `signal-state/`, `development-decision.json`, Zusammenfassungen, `diagnostics.json`, `verification.json`, `blind/`. Manifesthash: `6ec9ebe213280727c73af473189ac114ff69a1a8deaac1021244b4793241767c`. Diese privaten Laufdaten und Kursbestände werden nicht eingecheckt; [aggregierte Tabellen](EINSTIEGSSUCHE-TABELLEN.md) bleiben nachvollziehbare Dokumentation.

## Meine Entscheidung für den nächsten Schritt

1. Gespeicherte Beobachtung, unabhängige Reaktionen und nachvollziehbare Statusmeldungen behalten. Sie beheben technische/subjektive Unklarheiten, ohne einen Renditevorteil zu behaupten.
2. Den bisherigen Motor erhalten und die zusätzlichen Linien nur als getrennt gekennzeichnete Kandidatenquelle ansehen. Der strenge Swing-Motor ist kein überzeugender Ersatz.
3. Vor einer Integration die verblindeten Fälle wirklich manuell bewerten. Prüfen, welche Linien wir als Mensch akzeptieren und welche das System verpasst oder überbewertet. Erst daraus eine überprüfbare weitere Geometriehypothese ableiten.
4. Zonen-Retests gezielt weiter replizieren, mit festem Regelstand, besserer historischer Datenabdeckung und unverwendeten späteren Daten. Nicht die fünf schönsten Dreierkontakte zur neuen Regel erklären.
5. Erst bei ausreichender Evidenz Web-/Hermes-Produktintegration und konkreten Exitvergleich angehen. Der aktuelle Versuch rechtfertigt eine Beobachtungsliste; eine behauptet gewinnbringende automatische Einstiegsstrategie rechtfertigt er noch nicht.
