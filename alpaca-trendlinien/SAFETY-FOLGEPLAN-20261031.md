# Safety-Folgeexperiment: technische Umsetzung

## Fragestellung und feste Varianten

Die Entryepisoden aus `event-cases-wide-v2-20261031` bleiben unverändert. Der Versuch untersucht ausschließlich die Stopführung und die Bewertung offener Fälle. Die beiden neuen Regeln wurden im versionierten Plan vor dem Lesen der Pilotergebnisse festgelegt; anschließend wurde der breite Plan vor Ergebnisvergleich gespeichert. Kein Schwellenwertsuchlauf.

1. **Qualifizierte aktuelle Safety (`qualified_fan`):** Die ursprüngliche steigende Entry-Safety weiterprojizieren. Zusätzlich eine aktuelle steigende Safety nur zulassen, wenn sie am betreffenden bestätigten 4h-Schluss bereits qualifiziert ist. Der höhere gültige Kandidat gewinnt; ein Stop darf niemals sinken.
2. **Aktuelle Safety ab +2R (`r2_fan`):** Bis zu einem bestätigten 4h-Schluss mit mindestens +2 initialen geplanten R die ursprüngliche Entry-Safety verwenden. Die Berechnung enthält modellierte Verkaufskosten. Danach dauerhaft die aktuelle gültige steigende Safety zulassen, auch bei anschließendem Kursrückgang. Intrabar-Hoch und spätere MFE lösen die Freigabe nicht aus.

Referenzen bleiben ursprüngliche Safety, bisherige aktuelle Safety und fester Anfangsstop. „Ursprünglich“ bezeichnet die beim Entry gewählte Safety; dies ist nicht automatisch die tiefste Hauptlinie des Fächers.

Kein neuer Entryfilter, keine Änderung von Anfangsstop, Stückzahl oder Kosten, keine Zeitexits, keine Gewinnziele und keine Depot-/Slotsperren. Keine automatische Änderung bestehender Web-, Forschungs- oder Worker-Defaults. Varianten sind getrennt wählbare interne Offline-Experimente.

## Gemeinsame technische Ausführung

`exit_followup.py` transformiert die bereits kausal gespeicherte 4h-Kandidatentimeline. Die Ausführung nutzt unverändert `signal_path_index.execute_unbounded`: 300 Sekunden Verzögerung und nächstes erwartetes 5m-Open, tatsächlicher Gap-Open unter dem Stop, Cent-Rundung, Puffer und nur aufwärts wirksame Stopänderungen. Fehlende erwartete Kurse bleiben unbekannt. Der Versuch erzeugt keine zweiten Entryepisoden und keinen zweiten Linienfinder.

`tools/run_exit_followup.py` bietet `prepare`, `build`, `evaluate` und `all`. Maximal vier Prozesse, Betriebssystem-Schreiblock, atomare prüfsummengeschützte Aktienblöcke, an Enginecode/Dataset-IDs/Originalplan gebundene Wiederaufnahme. Geänderter Producer erfordert einen neuen Studienordner. Der Dienst und direkte CLI müssen denselben `TORI_DATA_DIR` verwenden.

Der Folgeversuch lädt nur vorhandene unveränderliche Datasets; der Providerzugriff wird beim Berechnen ausdrücklich blockiert. Sammler bleibt pausiert. Keine Orders, Nachrichten oder Containeränderung.

## Auswertung

- Geschlossene Nettoergebnisse und offene Netto-Liquidationsbewertungen separat ausweisen, zusätzlich gemeinsamer Bewertungsmittelwert. Das ist kein tatsächlich realisierter Gesamtgewinn und keine Depotperformance.
- Zensierte Pfade bleiben unbekannt. Niemals ihre letzte Bewertung als Ergebnis am globalen Datenende ausgeben.
- Modelle paarweise und zusätzlich auf identischen bewertbaren Fällen aller vier Safety-Varianten vergleichen. Verschiedene Haltedauern und Abhängigkeiten offenlegen.
- Ergebnisse nach Entryfamilie, ursprünglicher Kontaktklasse und Entryfenster aufteilen; alle gefüllten Fälle in Stopabstandsgruppen einschließlich offen/zensiert behalten.
- Feste Abstandsklassen: Prozent 0/1/2/4/unendlich; ATR4h 0/0,5/1/2/unendlich. Rein beschreibend, keine nachträglich optimierten Mindestabstände.
- Tatsächlichen ersten Wechsel auf eine engere aktuelle Linie von bloßer Fortschreibung der Ursprungslinie unterscheiden; damalige Qualität, Kontakte, Alter, Zeit seit Entry und damaliges Netto-R protokollieren.
- Hypothetisches Netto-R am letzten aktiven Stop mit Beobachtungsdatum speichern. Kein garantierter „Locked-in“-Gewinn: Gap-Fills können schlechter ausfallen.

## Prüfung und Dateien

`tools/verify_exit_followup.py` implementiert die Kandidatenzulassung separat und prüft sämtliche Fälle auf unveränderte Herkunft, kausale Verfügbarkeit, Ratchets, Aktivierungszeiten und Kosten. Eine deterministische Stichprobe wird unabhängig Kerze für Kerze anhand der 5m-Daten nachgerechnet. `tests/test_exit_followup.py` deckt unter anderem Zweikontakt-Sperre, zeitverzögerte Zulassung, Schlusskurs statt Intrabar-Hoch, dauerhafte +2R-Freigabe, keine Zukunftsfreigabe nach bereits erfolgtem Exit und unveränderte Entrydaten ab.

`tools/report_exit_followup.py` prüft die flache CSV-Aggregation separat und erzeugt den lesbaren Ergebnisbericht. Private Pläne, Aktienblöcke, Datasets und CSVs verbleiben unter `artifacts/`; Code und Ergebnisdokumentation dürfen später veröffentlicht werden, diese Laufdaten nicht.

Die konkrete Bilanz steht nach abgeschlossenem Lauf in `SAFETY-FOLGEERGEBNISSE-20261031.md` und `SAFETY-FOLGEBEWERTUNG-20261031.md`. Alle bekannten Daten sind explorativ; keine neue unabhängige Erfolgsbestätigung. Sichtprüfung unterdrückter Episoden, unangetastete Validierung und die kausale Wahl eines alternativen tieferen Anfangsstops bleiben separate Aufgaben.
