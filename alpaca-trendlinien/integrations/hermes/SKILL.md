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
- `submit --spec <datei.json>`: einen validierten Forschungsauftrag einreichen. Parameterbeispiel: `/opt/tori/deploy/experiment.example.json`. Die Antwort enthält die Job-ID.
- `status --id <id>`: Fortschritt, ausgelassene Aktien und Fehler prüfen. Längere Abrufe sind normal; Status in sinnvollen Abständen statt in enger Schleife lesen.
- `report --id <id> --offset 0 --limit 250`: Gesamtauswertung plus paginierte Einzelfälle lesen. Für weitere Fälle Offset erhöhen. Die Gruppentabelle bezieht sich auf alle Fälle, nicht nur diese Seite.
- `events --id <id>`: archivierte Linienereignisse lesen.
- `cancel --id <id>`: einen ausdrücklich unerwünschten Auftrag abbrechen, Archiv erhalten.
- `schedule`: bestehenden Zeitplan lesen; Änderungen nur entsprechend dem Auftrag des Nutzers vornehmen.

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
