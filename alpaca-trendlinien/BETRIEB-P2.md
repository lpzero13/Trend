# P2: Datenqualität, Sicherung und belastbare Forschung

Stand: 18.10.2026. Ergänzt [BETRIEB-P1.md](BETRIEB-P1.md). Lokal implementiert und unter Windows geprüft; kein Proxmox-Rollout und kein automatischer GitHub-Upload durch diese Arbeit.

## Datenqualität und Kalender

Neue Alpaca-Tageskerzen verwenden den tatsächlichen regulären XNYS-Sitzungsschluss aus `exchange-calendars==4.13.2`. Feiertage, Sommerzeit und verkürzte Sitzungen werden berücksichtigt. Beispiel: 27.11.2026 endet um 13 Uhr New York. Eine noch laufende Tageskerze wird weiterhin ausgeschlossen. Native Intraday-Aggregate bleiben unverändert; Vor-/Nachbörse und vom Provider vorgegebene Kerzengrenzen sind möglich.

Die Normalisierungsversion steht je Intervall im Dataset und gehört zu dessen Inhaltsprüfsumme. **Bestehende unveränderliche Datasets werden nicht umgeschrieben.** Alte Tageskerzen können weiterhin den früheren konservativen 16-Uhr-Schluss enthalten. Derselbe neu normalisierte Anbieterbestand kann deshalb eine neue Dataset-ID und andere Verfügbarkeitszeitpunkte ergeben. Das ist keine nachträgliche Veränderung einer alten Fixierung. Der Kalender rekonstruiert keine damals tatsächlich publizierten Datenstände oder Veröffentlichungslatenzen.

Neue Datasets erhalten ein beschreibendes Qualitätsaudit. Die vollständigen Hinweise liegen in der Datasetdatei, eine kleine Zusammenfassung in SQLite. Der Forschungsbericht zeigt die Hinweise pro Auftrag; ältere Bestände ohne Audit werden ausdrücklich als ungeprüft ausgewiesen. Geprüft werden:

- Explizite Feed-/Bereinigungsmetadaten; gemischte Angaben zwischen Intervallen werden abgelehnt.
- Fehlende Tages-Sitzungen innerhalb des beobachteten Zeitraums, unerwartete Sitzungstage und Unterschiede zwischen gespeichertem und kalendarischem Schluss.
- Große Tages-Eröffnungslücken ab 25 % gegenüber dem vorherigen Schluss als **Prüfhinweis**, nicht als bestätigter Split.
- Grenzen von Rohkursen, IEX als Einzelplatz und heutigem Aktienuniversum ohne gesicherte historische Delisting-Abdeckung.

Splits und Dividenden werden **nicht automatisch verifiziert oder korrigiert**. Kleine Dividendenlücken sind kein automatisch erkanntes Dividendenereignis; Ausschüttungen gehen nicht als Ertrag in die Ereignisstudie ein. Fehlende Daten werden nicht durch künstliche Kerzen ersetzt. Das Audit beschreibt den gesamten Datenbestand und darf nicht nachträglich als damaliger Einstiegsfilter dienen.

Der neue Providervertrag in `providers.py` trennt Abruf/Normalisierung von der Signalberechnung. Alpaca implementiert ihn; **EODHD bleibt geplant**. Dessen Adapter braucht eigene Instrument-, Währungs-, Zeitzonen-, Sitzungs- und Bereinigungsverträge. Ein anderer Provider darf nicht ungeprüft mit den US-Annahmen betrieben werden.

Quellen für die Datenkonventionen: [Alpaca Stock Bars](https://docs.alpaca.markets/us/reference/stockbars), [versionierter Kalender](https://pypi.org/project/exchange_calendars/4.13.2/), [NYSE-Handelskalender](https://www.nyse.com/trade/hours-calendars).

## Speicher und Importprüfung

`tori-tool storage` zeigt Dateien und Bytes nach Marktcache, Datasets, Snapshots, Forschung, Katalog und sonstigen Dateien sowie freien Plattenplatz. Dieselben Angaben stehen in der Forschungsansicht unter „Betriebszustand / Speicher nach Kategorie & Wartung“. HTTP-Healthchecks verwenden höchstens 30 Sekunden alte Inventurdaten und lösen keine Providerabfragen aus. Externe Backups liegen außerhalb dieser Inventur.

Vor einem unfixierten Forschungsauftrag, nach Auflösung des Gesamtkatalogs und nochmals vor jedem Aktienimport wird freier Speicher geprüft. Die konservative Schätzung lautet:

```text
256 MiB Reserve + Historientage × noch zu importierende Aktien × 32.000 Bytes
```

Das ist eine Heuristik einschließlich Cache, normalisierten Daten und temporären Schreibvorgängen, kein garantiertes Größenmodell. Wiederverwendbarer Cache kann zur Überschätzung führen. `TORI_MIN_FREE_BYTES` ändert die Reserve. Bei unzureichendem Platz folgt ein verständlicher Fehler (HTTP 507); der jeweilige Import beginnt nicht. Ein laufender Auftrag kann dadurch teilweise oder ganz fehlschlagen, sein Archiv bleibt erhalten.

## Datenbankschema und Update

`database.py` verwaltet derzeit Schema **3** über `PRAGMA user_version` und `schema_migrations`. Version 1 bildet den bisherigen Grundbestand ab, Version 2 Ereignisindex/Fortschritt, Version 3 Qualitätszusammenfassungen. Bestehende unversionierte Tabellen werden übernommen und auf benötigte Spalten geprüft. Alle nötigen Migrationsschritte laufen in einer Transaktion; bei Fehlern wird zurückgerollt. Unbekannte Altschemata werden nicht überschrieben. Eine Datenbank aus einer neueren Version wird vor Schreibzugriffen abgewiesen.

Vor dem Rollout den Dienst geordnet stoppen und den Bestand mit der bisherigen Version konsistent sichern. Dann Code und `requirements.txt` aktualisieren, Tests ausführen und den neuen Dienst mit **demselben `TORI_DATA_DIR`** starten. Der erste Datenbankzugriff migriert auch bei CLI-/Health-Aufrufen. Keine alten Worker parallel gegen die Migration betreiben. Es gibt **keine automatische Rückwärtsmigration**: für einen Rollback passenden Code und zugehöriges Backup in einer separaten Umgebung verwenden. Alte P1-Versionen besitzen noch keinen Schutz gegen neuere Schemata.

Der Engine-Hash enthält jetzt auch Kalender, Qualitätsprüfung, Providervertrag und Anforderungen. Unterbrochene Aufträge einer anderen Kernversion werden weiterhin nicht übergangen oder still fortgesetzt. Alte abgeschlossene Berichte bleiben lesbar; neue Wiederholungen erhalten einen neuen Auftrag.

## Backup, Prüfung und Wiederherstellung

Auf dem Zielsystem als berechtigter Dienstbenutzer, mit installiertem Wrapper und bereits vorhandenem Backup-Elternordner:

```sh
tori-tool backup --output /srv/tori-backups/backup-2026-10-18
tori-tool verify-backup --path /srv/tori-backups/backup-2026-10-18
tori-tool restore --backup /srv/tori-backups/backup-2026-10-18 --target /srv/tori-restores/test-2026-10-18
```

Ohne Wrapper: `TORI_DATA_DIR=/var/lib/tori /opt/tori/.venv/bin/python /opt/tori/tori.py ...`. Windows entsprechend mit `.venv\Scripts\python.exe tori.py ...` und absolutem Zielpfad. Zielordner müssen **neu** sein; ihre Eltern müssen existieren. Backup und Restore schreiben außerhalb des aktiven Datenordners. Es wird kein bestehender Ordner überschrieben und keine laufende Installation umgeschaltet.

Die Sicherung verwendet die SQLite-Backup-API einschließlich des konsistenten WAL-Lesestands und kopiert alle unveränderlichen Datasets und manuellen Snapshotdateien. Fehlende referenzierte Datasets führen zum Abbruch. Ein Manifest enthält Dateigrößen und SHA-256-Prüfsummen. Dataset-Inhaltsprüfsummen, sichere relative Pfade, SQLite-Integrität und Referenzen werden geprüft, bevor der fertige Ordner unter seinem endgültigen Namen erscheint. Auch eine Sicherung während neuer Datenbankeinträge wird getestet; laufende Änderungen nach dem SQLite-Lesestand gehören nicht zu diesem Backup.

Nicht enthalten: Zugangsdaten, Markt-/Katalogcache, Logs, Worker-Sperre und browserlokale Rays/Messungen. Secrets getrennt geschützt sichern. Für reine Offline-Forschung reichen die archivierten Datasets; für neue Providerimporte müssen Zugang und Cache neu eingerichtet werden. Das Manifest prüft Integrität, ist aber keine kryptografische Signatur gegen einen Angreifer, der Backup und Manifest gemeinsam verändern kann.

Restore prüft das Backup vor dem Kopieren und die kopierten Dateien erneut. Danach erst einen **separaten** Testdienst/CLI-Prozess mit `TORI_DATA_DIR` auf das neue Verzeichnis richten, Berichte und Snapshots lesen sowie einen gepinnten Auftrag offline wiederholen. Einen wiederhergestellten Zeitplan vor dem normalen Serverstart prüfen: er kann noch aktiv sein. Die CLI `worker --once` führt die gewählten Queuearbeiten aus; ein gepinnter Test braucht keine Schlüssel.

## Aufräumen bleibt eine Vorschau

```sh
tori-tool cleanup-preview
```

Dieser Befehl löscht nichts. Er schützt Dataset-Verweise aus allen Aufträgen, Symbolen, Ereignissen, Einstellungen einschließlich gepinnter Zeitpläne und manuellen Snapshots. Nicht sicher lesbare Referenzdokumente verhindern eine Vorschau. Die Kandidatenliste ist eine Momentaufnahme, kein Löschauftrag; neue Verweise können danach entstehen. Es gibt bewusst keinen automatischen Löschbefehl und keinen entsprechenden HTTP-Schreibendpunkt.

## Forschungsberichte lesen

Die vier Gruppen Ausbruch/Retest × vorläufig/qualifiziert bleiben bestehen. Die Tabelle trennt jetzt Versuche mit Entry, eindeutige Einstiege und Versuche ohne Entry. Das JSON enthält zusätzlich eindeutige Signale und Gründe ohne Entry. Mehrere Ursprünge können dasselbe Signal/Entry treffen; sie zählen nicht mehrfach in den Horizontkennzahlen.

Je Horizont werden vollständige (`n`) und unvollständige Beobachtungen getrennt ausgewiesen. Unvollständige Zukunft ist weder Nullrendite noch Gewinn. `overlapping_entries` zählt Einstiege, deren Fenster mit einem früheren Fenster **desselben Datasets innerhalb der Gruppe** überlappt. `unknown_windows` zählt fehlende Endzeitpunkte. Das ist kein korrigierter statistischer Stichprobenumfang: andere Abhängigkeiten, Gruppenüberschneidungen und Korrelationen zwischen Aktien bleiben möglich. Der reservierte Holdout bleibt unbenutzt. Ereignisstudien bleiben von einer ausführbaren Strategie und Depot-P/L getrennt.

## Prüfnachweise vom 18.10.2026

- Unter Windows jeweils **98 Python-Tests** mit Python 3.12 und 3.13.12 erfolgreich, je ein übersprungener Symlinktest wegen fehlender Windows-Berechtigung; **24 JavaScript-Tests** erfolgreich.
- Automatisierter echter Subprozess mit externem Datenpfad, schreibgeschütztem Code und internem Testproxy: Webzugang ohne Browserlogin über Proxy, direkte Backendanfrage ohne Token 401, fremder Origin beim Schreiben 403, gepinnter Offline-Auftrag erfolgreich. Unter Windows werden Dateiattribute geprüft; die echte Unix-Schreibverweigerung wird in der Linux-CI geprüft.
- Transaktionale Migration mit absichtlichem Fehler/Zurückrollen, unbekannte Schema-/Zukunftsversion, Backup während neuer Einträge, Manipulation/Pfadtraversal, fehlender Speicher, Referenzschutz und Offline-Wiederholung getestet. Vorhandene Tests für Worker-Abbruch/Wiederaufnahme bleiben erhalten.
- Echter lokaler Bestand: **2 Datasets, 5 Snapshots, 8 gesicherte Dateien, 6.816.672 Bytes**. In einen neuen Ordner wiederhergestellt; alle Snapshots lesbar. Ein neuer gepinnter Auftrag mit drei AMZN-Starts lieferte identische Fälle und Zusammenfassung; ein Providerimport war im Test ausdrücklich verboten.
- Im Chrome-Browser Speicherübersicht, Schemaanzeige, Ergebniszählung und Datenqualitätshinweis für ältere Datasets geprüft. Der lokale Dienst wurde neu gestartet; der Zielcontainer blieb unverändert.

CI ist für Linux/Windows × Python 3.12/3.13 eingerichtet. Diese vier Remote-Läufe sind erst nach Veröffentlichung und ihrem tatsächlichen Abschluss bestätigt.

### Begrenzte Ressourcenmessung

Isolierte lokale Prozesse, Python 3.12, keine Providerzugriffe; synthetisches Journal und eine Offline-Testaktie. Dies ist keine Volluniversum-Abnahme.

| Messung | Ergebnis |
|---|---:|
| Journalereignisse / Seitenlimit | 100.000 / 250 |
| Seiten / vollständiger Export | 400 / 12,28 s |
| Erste HTTP-Seite | 139,24 ms |
| Größte Antwort | 381.234 Bytes |
| Python-Allokationsspitze erste Seite | 2.174.320 Bytes |
| Prozess-RAM-Spitze Journal | 97.648.640 Bytes |
| Health-Abfrage im Journaltest | 10,32 ms |
| SQLite-Größe synthetisches Journal | 215.142.400 Bytes |
| Offline-Worker, 800 Quelltage / 3 Starts | 1,36 s / 90.857.472 Bytes RAM-Spitze |

Die Kalenderabhängigkeit erhöht den Grundbedarf gegenüber P1. Vor größerem Universum auf dem Ziel-LXC mit begrenzten Aktienlisten messen. Eine Übertragung dieser Einzelfallzeiten auf Tausende Aktien wäre nicht belastbar.

## Was danach offen bleibt

Verifizierte Kapitalmaßnahmen und Total-Return-Konventionen, historisches Instrumentenuniversum, EODHD samt europäischen Kalendern, feinere Ausführungs-/Sessionmodelle, Volluniversum-Lastmessungen und eine eigene unabhängige Strategievalidierung. Eine externe Backupaufbewahrung, Wiederherstellungsübungen im Zielcontainer und ein späterer Rollout bleiben Betriebsaufgaben. PostgreSQL, Redis, Docker oder ein neues Frontend sind dafür momentan nicht erforderlich.
