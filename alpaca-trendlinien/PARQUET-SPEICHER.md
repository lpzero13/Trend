# Parquet-Kursablage und feste persönliche Zeichnungen

Stand: 28.10.2026. Lokale Implementierung; kein Container-Rollout oder zusätzlicher Universumsimport.

**Lokales Ergebnis:** 487 bestehende Datasets derselben 60 Aktien erfolgreich umgestellt. Aktive Ablage einschließlich Wochen-Cache und Prüfmetadaten: **339.524.821 Bytes** (339,5 MB), gegenüber **4.642.963.441 Bytes** vorherigem JSON, rund **92,7 % weniger**. Das ist der kombinierte Effekt aus Parquet-Kompression und Wiederverwendung unveränderter Monate. 9.501 eindeutige Blöcke, 21.926 Referenzen. Die Original-JSON-Dateien bleiben vollständig als Rückfallkopien erhalten und belegen weiterhin ihren bisherigen Platz; der separate Anbieter-Rohcache bleibt ebenfalls unverändert.

## Umgesetzte Ablage

Die SQLite-Betriebsdatenbank bleibt für Forschungsaufträge, Fortschritt, Fälle, Universums-/Datasetreferenzen und Bewertungen zuständig. Der Datenpfad bleibt unverändert: im Dienst `/var/lib/tori`, lokal der konfigurierte `TORI_DATA_DIR`, sonst `data/` im Anwendungsordner.

Neue unveränderliche Kursdatensätze werden als **Parquet mit Zstd, Stufe 3** abgelegt. `datasets/<Dataset-ID>.json` ist jetzt ein kleines Manifest mit bisherigen Prüfprotokollen und Metadaten. Die Kerzen stehen in gemeinsam genutzten Dateien `datasets/chunks/<Inhaltsschlüssel>.parquet`. Eine physische Partition enthält die vorhandenen Intervalle derselben Aktie und desselben UTC-Monats; UTC-Monate sind Dateigrenzen, keine neue Definition von Handelskerzen. Mehrere Datasetgenerationen und Universen verwenden unveränderte Blöcke gemeinsam.

Gespeichert werden **1h, 4h, 1D**, die originale **5m-Basis, soweit vorhanden**, und zusätzlich ein **1W-Cache** aus vollständig abgeschlossenen erwarteten XNYS-Handelswochen. Fehlerhafte/unvollständige Wochen werden nicht aufgefüllt. Der vollständige Wochen-Cache ist kein historisch früher verfügbares Signal: Chart und Forschung begrenzen weiterhin anhand der tatsächlichen Kerzenschlusszeit. Die Chartwochen werden weiterhin kausal aus bekannten Tageskerzen aufgebaut; der gespeicherte Cache steht als Ableitung zur Verfügung und ist keine neue Forschungsserie.

Native historische Anbieterkerzen bleiben native Kerzen. Die Speicherumstellung führt keine Neuberechnung ihrer 1h-/4h-/Tageskurse aus. Neue reguläre Forschungsimporte nutzen wie bisher `lab_data.resample_regular`: 5m-Basis, Sitzungsbeginn als Anker, verkürzter letzter Zeitblock möglich, unvollständige Blöcke ausgeschlossen. Feed, Kursbereinigung, Kalender-/Normalisierungskonvention, Anbieter und synthetische Herkunft sind Bestandteile der Datensatzidentität; unterschiedliche Bestände werden nicht vermischt.

## Identität und Veröffentlichung

- Dataset-IDs beruhen weiterhin auf dem **exakt gleichen logischen Material**. `read_dataset()` liefert weiter den bisherigen Vertrag mit allen Originalkerzen; alte JSON-Datasets bleiben lesbar.
- Parquet speichert Preise als float64, Zeitstempel als ganze Zahlen. Eine Typmaske bewahrt vorhandene JSON-Unterschiede zwischen Integer und Float; seltene Integer jenseits 2^53 werden zusätzlich exakt erhalten. Keine Preisrundung zur Kompression.
- Jeder Block erhält eine Inhaltsadresse und eine Datei-SHA256. Vor Veröffentlichung des Manifests wird der gesamte Datensatz zurückgelesen und die kanonische Darstellung mit dem Original verglichen.
- Erst vollständige Blöcke, dann atomare Veröffentlichung des Manifests. Parallele Schreiber ersetzen keine vorhandenen Blöcke. Abgebrochene Vorbereitungen können unreferenzierte temporäre Dateien/Blöcke hinterlassen; diese werden nicht als Datensätze benutzt oder automatisch gelöscht.
- Neue Kerzen oder Revisionen erzeugen eine neue Dataset-ID. Unveränderte Monate werden wiederverwendet. Ein geänderter aktueller Monat wird neu geschrieben; eine vollständige neue Mehrjahreshistorie ist dafür nicht mehr nötig.
- Importzeitpunkt, Prüfmetadaten und bestehende Reihenfolge im lokalen Katalog bleiben bei der Migration erhalten. Die verfügbare Historie und die bisherige bevorzugte Datasetgeneration ändern sich dadurch nicht.

## Bestehende Installation umstellen

Runtime-Abhängigkeiten aus `requirements.txt` aktualisieren, einschließlich `duckdb==2.0.0`. Kein zusätzlicher Datenbankserver, kein Node-Build. Code kann weiterhin schreibgeschützt sein; temporäre Kursdateien liegen im Datenordner.

Vor einem Containerupdate vorhandene Dienste/Worker stoppen und einen konsistenten Bestand außerhalb des aktiven Datenordners sichern. Lokale Secrets und denselben Datenpfad erhalten. **Alte unterbrochene Forschungsaufträge/Beobachter nicht unter einem geänderten Enginehash fortsetzen.** Ergebnisse und Datasetreferenzen bleiben lesbar; neue Berechnungen benötigen ihre passende neue Registrierung. Die Migration startet keine Worker und verändert keinen Zeitplan.

Im Anwendungsordner, mit demselben Datenpfad wie der Dienst:

```bash
TORI_DATA_DIR=/var/lib/tori .venv/bin/python tools/migrate_parquet.py
TORI_DATA_DIR=/var/lib/tori .venv/bin/python tools/migrate_parquet.py --apply --workers 2
```

Ohne `--apply` werden vorhandene Datensätze geprüft, aber nicht umgeschrieben. Mit `--dataset <ID>` lässt sich zunächst ein bestimmter Bestand umstellen. Ein bis vier lokale Prozesse sind wählbar. Keine Providerabrufe, keine neuen Aktien und kein automatischer Backtest.

Vor dem Austausch eines alten JSON-Datasets wird dessen unveränderte Originaldatei unter `datasets/legacy-json/<ID>.json` gesichert. Die Umstellung ist wiederholbar, bereits umgestellte IDs werden geprüft und übersprungen. Deshalb wird der Platz der alten JSON-Kopien **nicht sofort freigegeben**. Die Rückfallkopien werden nicht automatisch gelöscht und gehören vor einer späteren Entfernung in eine separat geprüfte Sicherung. Sie sind nicht Teil des neuen aktiven Parquet-Backups.

`maintenance.backup/verify/restore` verwendet für neue Sicherungen **`tori-backup-2`** und erfasst die aktiven Manifeste und alle referenzierten Parquet-Blöcke, gemeinsame Blöcke genau einmal. Es prüft Dateiprüfsummen, logische Dataset-IDs und SQLite-Referenzen. Eine Wiederherstellung geht weiterhin ausschließlich in einen neuen Ordner. Alte reine JSON-Sicherungen mit **`tori-backup-1`** bleiben lesbar; neue Parquet-Sicherungen brauchen einen passenden Leser aus dieser Version. Rohdownloadcache, Secrets, Rückfallarchiv und lokale Browserzeichnungen bleiben außerhalb dieser Sicherung.

Die Bereinigung bleibt eine Vorschau. Die Größe eines unreferenzierten Manifests ist **keine** Zusage, dass seine gemeinsam genutzten Blöcke gelöscht werden dürften. Importbudgets berücksichtigen die referenzierten Blockgrößen konservativ; sie zählen geteilte Blöcke lieber mehrfach als sie zu übersehen.

## Persönliche Linien und Farben

Manuelle Zeichnungen speichern Zeit-/Preisanker, Farbe und Verlängerungsart. Beim Wechsel zwischen 1h/4h/1D/1W werden die **zwei unveränderten Anker** in die aktuelle Chartachse projiziert und mit einer einzigen geraden Linie verbunden. Die bisher gespeicherte Zeichenachse (`drawing-axis-2`) bleibt aus Kompatibilitätsgründen lesbar, definiert aber keine abgetastete Ursprungskurve mehr. Bestehende Zeichnungen brauchen nicht neu angelegt zu werden.

Erst absichtliches Ziehen eines Ankers oder Verschieben der ganzen Linie ändert die gespeicherten Zeit-/Preisanker. Diese Bearbeitung ist rückgängig zu machen. Eine bloße Auswahl, ein Intervallwechsel oder eine Farbänderung verändert sie nicht. Auswahl-/Trefferprüfung und Beschriftung folgen derselben gezeichneten Geraden.

Zusätzlich korrigiert: Die gebündelte Chartbibliothek unterstützt bei `logicalToCoordinate` nur ganze Kerzenindizes. Ein Anker aus einem anderen Intervall kann aber zwischen diesen Kerzen liegen. Solche Positionen werden jetzt zwischen den benachbarten unterstützten Koordinaten interpoliert; die inverse Pixelabbildung ebenfalls. Damit springen Linienpunkte beim Intervallwechsel nicht mehr fälschlich an den linken Chartrand.

**Farbe** oben neben der Linienart ändert die ausgewählte Linie und die Vorgabe für neue Linien. Ohne ausgewählte Linie ändert sie nur die Vorgabe. Auswahl, Löschen und Rückgängig bleiben erhalten. Farben haben keine automatische Bedeutung für Forschung oder Signale; man kann beispielsweise fallende Widerstände rot und steigende Unterstützungen grün markieren.

Für die Verlängerung werden drei Jahre **geplanter Kalenderpositionen** ergänzt, ohne spätere OHLCV-Kerzen zu laden oder zu übertragen. Reguläre Achsen beachten XNYS-Sitzungen, Sommerzeit, Feiertage und verkürzte Tage; native Achsen behalten ihre beobachtete Uhrzeitkonvention. Diese Positionen werden nur von persönlichen Zeichnungen verwendet, nicht von Signalen oder Ausführungssimulationen. Jenseits dieses Planungshorizonts wird mit dem festen normalen Achsenschritt extrapoliert.

Bei unterschiedlich komprimierten Handelsachsen lässt sich eine Linie nicht gleichzeitig in jedem Intervall geometrisch gerade zeichnen **und** ihren Preis an jedem Zwischenzeitstempel identisch halten. Maßgeblich sind jetzt die **unveränderten beiden Anker und eine gerade Darstellung in jedem Intervall**. Die frühere Übertragung einzelner Ursprungskerzenpreise erzeugte sichtbare Zickzackkurven und wurde entfernt. Zwischen den Ankern und in der Verlängerung können die abgelesenen Preise bei verschiedenen Intervallen deshalb abweichen; die Anker selbst bleiben bei identischen Zeitstempeln und Preisen. Automatische Signalberechnungen werden dadurch nicht geändert.

Zeichnungen bleiben privat im Browserspeicher, getrennt nach Origin und Aktie bzw. Zufallsfall. Sie werden nicht in automatische Forschungsaufträge übernommen. Die Parquet-Ablage speichert Kursdaten, nicht diese persönlichen Zeichnungen.

## Abnahme

Tests decken numerisch exaktes Rücklesen, große Integer, gemeinsame unveränderte Monate, unabhängige Revisionen, Wochenfinalität, beschädigte/fehlende Blöcke, Pfadbegrenzung, idempotente Migration, Abbruch vor Manifestveröffentlichung und Backup/Restore ab. Zeichentests prüfen unveränderte Anker in allen Intervallen, Kollinearität der Darstellung, einen einzigen geraden Rendererabschnitt auch für alte 1D-Zeichnungen in 4h/1W, konsistente Trefferprüfung, absichtliche Bearbeitung samt Undo sowie Farbänderung ohne Geometrieänderung. Kalenderpositionen werden separat auf Wochenenden, Feiertage, DST und verkürzte Sitzungen geprüft. Die konkrete lokale Gesamtprüfung und Migration ist im aktuellen Eintrag in `HERMES.md` festgehalten.
