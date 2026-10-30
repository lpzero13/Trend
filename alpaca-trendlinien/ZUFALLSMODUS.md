# Zufallsmodus für manuelle Chartübungen

Stand: 28.10.2026. Im Menü **Zufall** unter `/zufall` wird beim Öffnen eine Aktie mit einem historischen Zeitpunkt gezogen. **Neu würfeln** erzeugt einen neuen Fall. Verwendet werden vorhandene unveränderliche lokale Marktdatasets; die Auswahl und Wiedergabe rufen keinen Provider ab.

## Bedienung

1. **Zufall** öffnen. Der Chart beginnt mit ausgeschalteter Tori-Analyse. Der Startzeitpunkt steht über dem Chart; alle angezeigten Intervalle enthalten ausschließlich damals abgeschlossene Kerzen.
2. Zwischen **1D, 4h und 1h** wechseln. Der bekannte Zeitpunkt bleibt gleich; eine laufende Tageskerze wird nicht mit später bekannten Werten eingeblendet.
3. Mit **◀ / ▶** oder den Pfeiltasten eine Kerze des ausgewählten Intervalls zurück oder weiter gehen. **Zum Startpunkt** kehrt zum ursprünglichen Zufallszeitpunkt zurück. Über **Datum** lässt sich innerhalb des gespeicherten Verlaufs springen.
4. **Linienart** wählen, dann das Ray-Werkzeug aktivieren und zwei Punkte setzen. Verfügbar sind Ray nach rechts, Ray nach links, Gerade in beide Richtungen, begrenzte Strecke und horizontale Widerstands-/Unterstützungslinie. Zwei horizontale Linien können eine Zone begrenzen.
5. Eine bestehende Linie anklicken und ihre Linienart ändern. Anker und ganze Linie sind verschiebbar. Löschen und Rückgängig bleiben verfügbar. Früher gespeicherte Rays ohne neue Richtungsangabe behalten ihr Verhalten nach rechts.
6. Mit dem Messwerkzeug zwei Preise vergleichen: aufwärts blau, abwärts rot. Messungen speichern, löschen und wiederherstellen funktioniert auch hier.
7. Neu laden oder den aktuellen Link später öffnen: Fall und Wiedergabezeitpunkt bleiben über die URL erhalten. Eigene Linien und Messungen werden je Fall im Browserspeicher aufbewahrt; sie überschreiben keine Zeichnungen der normalen Aktienchart.

Der Chart verwendet dieselben Chart-, Mess- und Zeichnungswerkzeuge wie die Hauptansicht. Eigene Linien werden bei neuen Kerzen nicht automatisch neu gewählt. Neu erstellte oder bearbeitete Linien tragen den damaligen Betrachtungszeitpunkt und werden beim Zurückgehen davor ausgeblendet. Die optische Darstellung eines schrägen Rays richtet sich weiterhin nach Handelskerzenpositionen des gewählten Intervalls. Eigene automatische Tori-Linien sind optional zuschaltbar und werden nur aus dem bekannten Präfix berechnet; eine automatische Snapshot-Fixierung ist im Zufallsmodus ausgeblendet.

## Auswahl und Grenzen

Die Auswahl erfolgt zuerst gleichverteilt über geeignete lokal vorhandene Aktien, anschließend gleichverteilt über geeignete gespeicherte 4h-Schlusszeitpunkte dieser Aktie. Je Aktie wird SIP mit Splitbereinigung bevorzugt, ansonsten ein vorhandener anderer Marktbestand. Es gibt keine Filter nach Einstiegssignal, nachfolgendem Gewinn, Trendrichtung oder Tori-Qualität. Doppelte Ziehungen sind bei echter Zufallsauswahl möglich.

Für eine verwendbare Übung muss der Bestand mindestens 81 gespeicherte Tageskerzen und die Intervalle 1h/4h/1D enthalten. Der Start hat mindestens 60 vergangene Tageskerzen und mindestens 20 weitere Tageskerzen zum Durchspielen. Die Randbereiche sind damit bewusst ausgeschlossen. Die Auswahl ist kein gleichverteiltes Los aus allen weltweiten Aktien und historischen Kalendertagen. Nur bereits importierte lokale Aktien nehmen teil. Fehlende Kurse bleiben fehlend und werden nicht erfunden. Synthetische Technikdaten werden ausgeschlossen.

Fall und Dataset werden fest gebunden. Ein später neuer Import ersetzt den vorhandenen Fall nicht. Die Seite zeigt keinen späteren Gesamtverlauf beim Start und sendet keine zukünftigen OHLC-Werte über versteckte Intervallansichten. Manuelles Weiterspringen ist die ausdrücklich gewünschte Offenlegung. Diese Übungen sind keine unabhängigen wissenschaftlichen Blindbewertungen und beeinflussen die automatischen Forschungsläufe nicht.

## Technische Schnittstellen

Unter den bisherigen Host-, Origin- und optionalen Tokenregeln:

```text
POST /api/random/cases                 JSON: {}
GET  /api/random/cases/CASE_ID
GET  /api/random/cases/CASE_ID/chart?timeframe=4h&analysis=0[&asof=ISO_TIME]
GET  /api/random/cases/CASE_ID/step?timeframe=4h&asof=ISO_TIME&direction=next
```

POST speichert nur die lokale Fallregistrierung; kein Kursimport oder Brokerzugriff. Bekannte Datasets werden vor Verwendung per Prüfsumme geprüft. Die schnellen Metadaten-Hinweise für den Auswahlkatalog ersetzen diese Prüfung nicht. Datumseingaben ohne Zeitzone werden wie in der Hauptansicht als New York behandelt; mehrdeutige/nicht existente Sommerzeit-Zeitpunkte werden abgewiesen.

Registrierungen liegen in der bestehenden Haupt-SQLite unter `random:case:<id>` und referenzieren `datasetId`. Damit gelten der bestehende Dataset-Referenzschutz sowie Backup/Restore. Persönliche Linien und Messungen bleiben im Browser, unter `tori-rays:random:<case>` beziehungsweise `tori-measurements:random:<case>`. Sie werden nicht an automatische Forschung oder Beobachter übergeben. Keine neuen Python-/Node-Laufzeitabhängigkeiten, kein Schemawechsel, keine Änderung bestehender Worker-Enginebindungen oder Zeitpläne.

## Lokale Abnahme

334 Python-Tests unter 3.12 und 3.13 bestanden (je ein vorhandener Skip), 47 JavaScript-Tests bestanden. Neue Tests prüfen Auswahl ohne Signal-/Gewinnfilter, alle drei bekannten Intervallpräfixe, Schrittgrenzen, Sommerzeit, gesperrte ungeeignete/synthetische Bestände, feste Datasetbindung, Zugriffsschutz und getrennte Fallzeichnungen. Die vollständigen vorhandenen Tests bleiben grün.

Zusätzlich mit einem echten lokalen SIP-Dataset über HTTP geprüft: neue Fallregistrierung, Navigation aller Seiten, 1h/4h/1D ausschließlich bis zum Startzeitpunkt sowie jeweils der nächste Kerzenschluss. Im Browser geprüft: Zufallsstart, Tagesintervall ohne noch laufende Tageskerze, ein weiterer Tag und Rückkehr zum ursprünglichen Zeitpunkt, beidseitige Gerade, Erhalt der Linie nach Neuladen, Preisänderungsmessung, Löschen und Rückgängig. Ein dabei aufgefallener Klickblocker am nicht interaktiven Zeichenhinweis wurde durch `pointer-events:none` behoben und erneut praktisch geprüft. Die verwendete Testmessung ist eine Werkzeugdemonstration und kein Studienergebnis.

Für diese lokale Abnahme wurde nur die Webansicht gestartet (`server.py --port 8765 --no-worker`); Forschungsjobs, Beobachter und bestehende Zeitpläne wurden nicht neu gestartet oder umgeschrieben. Kein GitHub-Push oder Container-Rollout.
