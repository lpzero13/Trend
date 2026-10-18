---
name: tori-research
description: Starte und prüfe technische Tori-Ereignisstudien über definierte JSON-Werkzeuge.
---

# Tori-Forschung

Diese Vorlage ist für die spätere Einrichtung im Hermes-Zielsystem gedacht. Sie wurde nicht automatisch in eine vorhandene Hermes-Installation installiert. Projektpfad und ausführbaren Python-Pfad an den Zielcontainer anpassen. Auf demselben Container und als berechtigter Dienstbenutzer `tori`: `TORI_DATA_DIR=/var/lib/tori /opt/tori/.venv/bin/python /opt/tori/tori.py`. Alternativ nach Installation den Wrapper `tori-tool` verwenden. Der Datenordner muss mit dem Webdienst übereinstimmen; sonst sieht der Agent eine andere Queue.

## Aufgabe

Tori untersucht Long-Ereignisse anhand zufälliger historischer Startpunkte. Ein Hintergrunddienst erledigt bereits die geplanten Untersuchungen. Nutze die vorhandenen Aufträge zuerst, statt bei jeder Nachfrage denselben Versuch erneut zu starten.

## Werkzeuge

- `list`: verfügbare Aufträge und Status als JSON lesen.
- `health`: lokale Betriebsbereitschaft, getrennte Lebenszeichen/Fortschrittszeiten, Datenalter und letzte Fehler lesen; kein Providerabruf. Warnung bei länger fehlendem Fortschritt ist kein sicherer Deadlock-Nachweis.
- `submit --spec <datei.json>`: einen validierten Forschungsauftrag einreichen. Parameterbeispiel: `/opt/tori/deploy/experiment.example.json`. Die Antwort enthält die Job-ID.
- `status --id <id>`: Fortschritt, ausgelassene Aktien und Fehler prüfen. Längere Abrufe sind normal; Status in sinnvollen Abständen statt in enger Schleife lesen.
- `report --id <id> --offset 0 --limit 250`: Gesamtauswertung plus paginierte Einzelfälle lesen. Für weitere Fälle Offset erhöhen. Die Gruppentabelle bezieht sich auf alle Fälle, nicht nur diese Seite.
- Optionaler Tori-Einstiegsmodus: `submit` mit `entry_mode: "tori"` und versionierten `tori`-Parametern. `sampling: "full"` für vollständigen Zeitraum oder `"random"` für reproduzierbare nicht überlappende Suchfenster; `samples`, `search_bars`, `seed` steuern die Fenster. `line_policy: "snapshot"` fixiert zu X, `tracked` verfolgt neue bestätigte Paare. `observe_forward: true` aktiviert rohe Schlusskursänderungen nach `horizons` XNYS-Handelstagen nach dem Einstiegstag, ohne Ausstiege/Kosten/Depot-P/L; in Zufallsfenstern nur erster Entry je Variante. API-Defaults bleiben vollständiger Zeitraum und nur Einstiege. Anleitungen: `TORI-EINSTIEGSMODUS.md`, `TORI-KURSBEOBACHTUNG.md`, Beispiel `deploy/tori-forward.example.json`. `report --entry-filter entries --limit 50` filtert Fälle, nicht die Gesamtsumme. Gleiche Zeitpunkte/Varianten nicht als unabhängige Trades zählen; unvollständige Horizonte und Fenster ohne Entry nennen. Bestehenden Zeitplan nur auf Nutzerauftrag umstellen.
- `events --id <id> --limit 250`: erste Ereignisseite als `{items, page}` lesen. Mit `--cursor <page.nextCursor>` fortsetzen, bis `hasMore` falsch ist. Standard 250, maximal 1.000; der Lesestand bleibt fest. Ein neuer Abruf ohne Cursor sieht inzwischen ergänzte Ereignisse. Frühere CLI-Parser für eine vollständige Liste müssen angepasst werden.
- `cancel --id <id>`: einen ausdrücklich unerwünschten Auftrag abbrechen, Archiv erhalten.
- `schedule`: bestehenden Zeitplan lesen; Änderungen nur entsprechend dem Auftrag des Nutzers vornehmen.
- `storage`: Größen nach Datenkategorie und freien Plattenplatz lesen. Vor Imports wird zusätzlich konservativ Platz geprüft; ein Fehler 507 ist kein Providerfehler.
- `backup --output <neuer-ordner>` / `verify-backup --path <backup>`: konsistente SQLite-/Dataset-/Snapshot-Sicherung außerhalb des aktiven Datenpfads erstellen und prüfen. Secrets, Cache und Browserzeichnungen sind nicht enthalten.
- `restore --backup <backup> --target <neuer-ordner>`: ausschließlich in einen neuen Ordner außerhalb des aktiven Datenpfads wiederherstellen; kein automatischer Dienstwechsel. Zeitplan vor einem separaten Teststart prüfen. Vorgehen und Rolloutgrenzen in `BETRIEB-P2.md`.
- `cleanup-preview`: ausschließlich Vorschau nicht referenzierter Datasets, keine Löschfunktion. Kandidaten nicht automatisch entfernen.

Eine separate Installation kann alternativ dieselben Operationen über die in `FORSCHUNG.md` beschriebenen HTTP-Routen verwenden. Den bereitgestellten Bearer-Token als Header verwenden, niemals in URLs oder Berichte schreiben. Kein direkter Datenbankzugriff über Netzwerkfreigaben.

## Auswertung

1. Zwischen erfolgreich, teilweise erfolgreich, Fehler und unvollständigen Beobachtungen unterscheiden. Keine fehlenden Fälle als Erfolg zählen.
2. Ausbruch und Retest sowie vorläufige/qualifizierte Linien getrennt betrachten. Exakte Kontakte, Abstand zu Grün und Tageskontext stehen in den Fallmerkmalen.
3. Mehrere Ursprünge können denselben Entry finden; die Zusammenfassung dedupliziert ihn. Auch verschiedene überlappende Ereignisse und wiederholte Aufträge sind keine unabhängigen Stichproben.
4. Positive Nettokursänderung, MFE, MAE und Schutzmarkenberührung sind unterschiedliche Beobachtungen. Die Studie liefert keine Portfoliorendite und keinen exakten Stop-Verkauf.
5. Originalsignale und Dataset-IDs in Begründungen angeben. Auffällige Fälle über den Chart prüfen lassen, statt spätere automatische Linien als den damaligen Auslöser zu behandeln.
6. Regeln zunächst als Hypothesen vorschlagen und Parameteränderungen als neue Experimente kennzeichnen. Reservierten Holdout nicht zur fortlaufenden Auswahl besserer Parameter benutzen.
7. Keine heutigen Nachrichten, Kurskenntnisse oder LLM-Erinnerungen rückwirkend in historische Einstiegsentscheidungen einbringen. Der Rechenkern erzeugt Signale und Zahlen; der Agent beschreibt die gespeicherten Ergebnisse.
8. Keine Brokerorders. Es existiert keine Orderfunktion in Tori.
9. Datenqualitätshinweise im Bericht mitlesen. Ein Audit des gesamten Datasets ist kein zeitgerechter Einstiegsfilter und bestätigt keine Kapitalmaßnahmen. Ältere Datasets ohne Audit sind nicht automatisch geprüft. Neue US-Tageskerzen nutzen den versionierten XNYS-Kalender; alte Datasets behalten ihre gespeicherten Abschlüsse.
10. Vollständige/unvollständige Horizonte und zeitliche Überlappungen getrennt nennen. `overlapping_entries` ist keine statistische Korrektur der Stichprobe. Vor Updates sichern; Schema 3 hat Vorwärtsmigrationen, keine automatische Rückwärtsmigration. Engine-Hash-Abweichungen nicht umgehen.
