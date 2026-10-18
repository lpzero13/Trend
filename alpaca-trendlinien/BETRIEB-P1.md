# P1: Ereignisjournal, Betriebszustand und Lastmessung

Stand: **18.10.2026**. Betriebsverbesserung ohne neue Handelsregeln oder Container-Rollout.

## Ereignisjournal

```text
GET /api/research/jobs/<id>/events?limit=250
GET /api/research/jobs/<id>/events?limit=250&cursor=<URL-kodierter-nextCursor>
tori-tool events --id <id> --limit 250
tori-tool events --id <id> --limit 250 --cursor '<nextCursor>'
```

HTTP und CLI liefern `{items, page}`. `page` enthält `limit`, `total`, `hasMore`, `nextCursor`, `snapshot` und `order: "append"`.

- Standard 250 Ereignisse, gültig 1–1.000, auch ohne Parameter begrenzt.
- `total` zählt den gesamten festen Lesestand, nicht die Seitengröße. Den Cursor unverändert übernehmen, bis `hasMore` falsch ist. HTTP-Querywerte URL-kodieren.
- Die erste Seite hält die obere Grenze bereits bestätigter SQLite-Zeilen fest. Später ergänzte Ereignisse verändern diesen Export nicht. Ein neuer Abruf ohne Cursor eröffnet einen neuen Lesestand.
- Reihenfolge: Einfügung, nicht Ereigniszeit oder alphabetisch nach Dataset/ID. Fachliche IDs und Zeitangaben bleiben erhalten.
- Ungültige/fremde Cursor und Limits ergeben HTTP 400; ein nicht mehr verfügbarer Lesestand HTTP 409.
- Keine Bereinigung, Wiederherstellung oder `VACUUM` zwischen zusammengehörigen Seiten durchführen. Nach Wartung einen neuen Export beginnen.
- Ein Index unterstützt den begrenzten Abruf; die API deserialisiert nicht mehr das gesamte Journal.

**Kompatibilität:** HTTP behält `items` und ergänzt `page`. Die CLI lieferte bisher eine vollständige Liste und liefert jetzt ebenfalls `{items, page}`. Hermes muss seinen bisherigen CLI-Parser und gegebenenfalls HTTP-Vollabrufe anpassen. „Journal JSON“ öffnet die erste Seite, keinen vollständigen Download. Ein kompletter Export erfolgt durch die Seitenfolge; Streaming wurde nicht ergänzt.

Die Auftragsliste lässt außerdem große Zufallspläne je Symbol aus. Der einzelne `status`-Abruf behält sie bei.

## Betriebszustand ohne Providerabruf

Die Forschungsansicht zeigt „Betriebszustand“. Dieselben lokalen Angaben stehen unter `operations` in `/api/health` und `/api/research/jobs`; die CLI liefert sie mit `tori-tool health`.

| Angabe | Bedeutung |
|---|---|
| `worker.lockHeld` | Betriebssystemseitige Worker-Sperre belegt. |
| `worker.heartbeatAt` / `heartbeatAgeSeconds` | Letztes gespeichertes Lebenszeichen und dessen Alter. |
| `worker.loopAgeSeconds` | Alter der Meldung der Hauptschleife, auch im Leerlauf. |
| `worker.progress` | Phase, Phasenbeginn, letzter Arbeitsfortschritt und Details. |
| `lastSuccessfulImport` | Letzter erfolgreicher Forschungs-/CLI-Import, einschließlich geprüftem Cachebestand. |
| `lastDataset` | Zuletzt von Forschung/CLI-Import geprüfter Bestand, eventuell ein älteres Offline-Dataset. |
| `dataAge` | Je Intervall: Alter des ursprünglichen Abrufs und letzten Kerzenschlusses im Dataset. |
| `lastError` | Letzter Auftrags-/Symbolfehler mit Zeitpunkt; bleibt als historischer Hinweis sichtbar. |
| `readiness` | Lokale Bereitschaft von Web, Worker und einem erfassten historischen Bestand. |

Der Monitor meldet alle fünf Sekunden ein Lebenszeichen. Arbeitsfortschritt wird unabhängig gespeichert. Importphasen zeigen Intervall, geladene Seiten und Kerzen, aber keine unbekannte Gesamtzahl oder erfundene Prozentanzeige. Ereignisberechnung meldet verarbeitete Kerzen, Versuchsauswertung bearbeitete Starts der aktuellen Aktie. Keine geschätzte Restlaufzeit.

Worker-Zustände: `absent` = keine Sperre; `unverified` = Sperre ohne gültiges aktives Monitor-Lebenszeichen; `unresponsive` = Lebenszeichen überfällig; `stalled` = frisches Lebenszeichen, aber länger kein Fortschritt/keine Leerlaufmeldung; `working` = aktiver Auftrag ohne bisheriges Warnsignal; `idle` = wartet auf Arbeit.

`stalled` ist ein Prüfhinweis, kein sicherer Deadlock-Nachweis. Langsame Anbieter oder einzelne lange Berechnungen können ihn ebenfalls auslösen. Aufträge werden nicht automatisch beendet und Sperren nicht umgangen.

Optionale Umgebungsvariablen, Sekunden jeweils 1–86.400:

```text
TORI_HEARTBEAT_TIMEOUT_SECONDS=30
TORI_PROGRESS_WARNING_SECONDS=300
```

`/api/health` bleibt ein erreichbarer Dienstcheck mit HTTP 200; Betriebsbereitschaft aus den JSON-Feldern lesen. Ein separat betriebener Worker wird über denselben Datenpfad erkannt. `credentialsConfigured` bedeutet nur lesbare lokale Konfiguration, `providerAuthentication` ist ausdrücklich `not_checked_by_health`. Auch ein erfolgreicher Cache-Import bestätigt keine aktuelle Provider-Anmeldung. Normale Chartabrufe erzeugen keinen Forschungsimport-Nachweis. Frühere, nicht protokollierte Importzeiten werden beim Update nicht erfunden.

Ein Offline-Lauf aktualisiert den verwendeten Dataset-Bestand, nicht den letzten Import. Neue Importmetadaten werden separat erfasst; unveränderliche Datasetdateien bleiben erhalten. Historische Daten und Handelspausen können große Alterswerte erklären.

## Updatehinweise für Hermes

Die Datenbank erhält `job_progress`, einen Ereignisindex und Metadaten in der bestehenden `settings`-Tabelle. Aufträge, Datasets, Journale und Zeitpläne werden nicht gelöscht. Ein formales versioniertes Migrationssystem bleibt P2.

Vor einem Container-Update: konsistentes Backup, laufende Arbeit kontrolliert beenden, Code aktualisieren und den Dienst vollständig neu starten. Der Engine-Hash umfasst geänderte Auftrags-/Forschungsdateien. Alte unterbrochene Aufträge dürfen deshalb nicht stillschweigend unter neuer Logik fortgesetzt werden. Neuen Auftrag auf denselben Dataset-IDs anlegen oder gezielt die alte Codeversion verwenden. Abgeschlossene Archive bleiben lesbar.

Host-/Originprüfung und Backend-Authentifizierung bleiben unverändert. Ein bestehender loginfreier interner Zugang über einen vertrauenswürdig konfigurierten Proxy wird nicht auf einen neuen Login umgestellt. Token nur serverseitig beziehungsweise als vorgesehenen Authorization-Header verwenden, nicht im Frontend oder in URLs. Der installierte Proxmox-Container wurde für diese Entwicklung nicht verändert.

## Lastmessung und Nachweise

```text
python tools/benchmark_research.py
```

Jeder Fall läuft in einem eigenen Prozess mit temporärem Datenverzeichnis. Journale sind synthetisch vergrößerte Fixture-Ereignisse. Keine Marktabrufe oder Änderungen vorhandener Aufträge. Gemessen werden vollständiger HTTP-Seitenabruf, Antwortgröße, Python-Spitzenallokation der ersten Seite, Prozess-Spitzen-RAM und Health-Laufzeit. Windows verwendet Peak Working Set, Linux/macOS `ru_maxrss`. HTTP-Client und Server laufen im selben Messprozess; RAM enthält beide Anteile. Die erste Seite ist durch `tracemalloc` instrumentiert und zeitlich nicht unmittelbar mit uninstrumentierten Abrufen vergleichbar.

Lokaler Lauf am 18.10.2026, Windows 11, Python 3.12.10, 250 Ereignisse je Seite; MB/KB dezimal:

| Ereignisse | Seiten | Gesamtabruf | Größte Antwort | Python-Spitzenallokation erste Seite | Prozess-Spitzen-RAM | Health |
|---:|---:|---:|---:|---:|---:|---:|
| 10.000 | 40 | 0,87 s | 380,98 KB | 2,19 MB | 47,80 MB | 8,04 ms |
| 50.000 | 200 | 4,87 s | 381,23 KB | 2,19 MB | 48,00 MB | 8,20 ms |
| 100.000 | 400 | 11,72 s | 381,23 KB | 2,19 MB | 48,33 MB | 8,11 ms |

Ein tatsächlicher Offline-Worker-Lauf auf einem synthetischen 800-Tage-Dataset mit einer Aktie und drei Starts benötigte 1,36 Sekunden und 38,40 MB Prozess-Spitzen-RAM; zwölf Ereignisse und drei Versuche wurden gespeichert.

Das zeigt begrenzte Seiten und nahezu konstanten Abrufspeicher für diese Journale, **keine Volluniversum-Kapazität**. Der Worker hält Ereignisse weiterhin pro Aktie im RAM. Komplexere Kursverläufe, größere Datasets, mehr Aktien und gleichzeitige Webzugriffe brauchen Messungen im Zielcontainer. Die erste Indexanlage auf einem großen bestehenden Journal kann zusätzliche Zeit benötigen.

Tests prüfen feste Lesestände bei späteren Inserts, fehlerhafte/fremde Cursor, HTTP-/CLI-Gleichheit, bestehende Datenbanken, getrennte Lebenszeichen-/Fortschrittszeiten, Import-/Offline-Metadaten und providerfreie Healthchecks. Ein tatsächlich beendeter Worker-Prozess wird erkannt und sein Auftrag anschließend offline wiederaufgenommen. Bestehende fachliche und Zugriffsschutztests bleiben erhalten.

Abschließend bestanden 75 Python- und 24 JavaScript-Tests. Im Chrome-Browser wurden die neue Karte, Hell/Dunkel und ein kurzzeitig nicht erreichbarer lokaler Server geprüft: Die Anzeige meldet den veralteten Stand, statt weiter einen gesunden Worker vorzutäuschen, und erholt sich nach dem Neustart. Ein neuer Auftrag mit drei Starts auf dem bereits vorhandenen echten AMZN-Dataset wurde ohne erneuten Import erfolgreich abgeschlossen. Derselbe Bestand und der gespeicherte Auftrag waren nach dem lokalen Dienstneustart weiter verfügbar. Eine vollständige Backup-/Restore-Abnahme im Container bleibt ausstehend.
