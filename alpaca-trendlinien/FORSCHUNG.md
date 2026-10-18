# Automatische Forschung, Webansicht und Hermes

Die manuelle Chartoberfläche bleibt unter `/` erhalten. Unter `/research` gibt es eine Forschungsansicht. `server.py` startet zusätzlich einen dauerhaften Worker; Aufträge laufen auch bei geschlossenem Browser. Der erste Start richtet einmalig einen täglichen Forschungsauftrag für MSFT und AMZN mit jeweils zehn Zufallsstarts ein. Ein gespeicherter Zeitplan wird durch Neustarts nicht überschrieben. Über die Webansicht lässt er sich ändern oder pausieren. `TORI_AUTO_ENABLED=0` unterdrückt nur die erstmalige Einrichtung, nicht einen bereits gespeicherten Zeitplan.

Das ist eine explorative Ereignisstudie mit einer Hintergrund-Engine. Noch kein Portfolio-Backtest mit einer festgelegten Ausstiegsstrategie und kein laufender Echtzeit-Kandidatenscanner. Es gibt keine Orderfunktionen. Eine bestehende Proxmox-/Hermes-Installation wird durch die lokalen Dateien nicht automatisch verändert.

## Was ein Auftrag macht

Die folgenden Zufallsstarts beschreiben den bisherigen Standardmodus. Zusätzlich gibt es im Formular den separat wählbaren **Tori-Einstiegsmodus**: vollständiger 4h-Durchlauf oder Zufallsfenster, Linienpaare weiterverfolgen oder zu X fixieren, drei Einstiegsvarianten, Prüfprotokolle und beobachtete 1h-Eröffnungen. Optional Schlusskursänderungen nach 5/10/20 Handelstagen, ohne Ausstiegs-/Depotsimulation. Siehe [TORI-EINSTIEGSMODUS.md](TORI-EINSTIEGSMODUS.md) und [TORI-KURSBEOBACHTUNG.md](TORI-KURSBEOBACHTUNG.md) für Parameter, Auswahl, Grenzen und CLI. Der bestehende Zeitplan wird durch bloßes Umschalten im Formular nicht geändert.

1. Die explizite Aktienliste bzw. den aktuellen angebotenen US-Börsenkatalog für diesen Auftrag festhalten. Der Gesamtkatalog kann viele Titel ohne ausreichende IEX-Historie enthalten; diese erscheinen mit Auslassungsgrund.
2. Je Aktie standardmäßig 900 Kalendertage für 1h, 4h und 1D abrufen. Alle Antwortseiten beachten. Veralteten Ersatzcache oder formal zurückgewiesene Kerzen für einen Forschungsimport ablehnen.
3. Den normalisierten Bestand samt Provider, Feed, Anpassung, Sessionbeschreibung und Inhaltsprüfsumme als unveränderliches Dataset sichern. Ein neuer Anbieterbestand wird zu einer neuen Version. Die damaligen Rohkerzen werden durch spätere Abrufe nicht überschrieben.
4. Nach mindestens 365 Tagen Linienvorlauf zufällige vorhandene 4h-Schlusszeitpunkte ohne Zurücklegen ziehen. X und Seed sind einstellbar. Nicht anhand späterer Gewinne oder Signale auswählen. Bei zu wenigen Startpunkten die tatsächlich erreichte Zahl melden.
5. Den späteren Anteil der grundsätzlich möglichen Starts als Holdout reservieren, standardmäßig 20 %. Kein Such- oder Auswertungsfenster darf in diesen Abschnitt reichen. Der Holdout wird in dieser Version nicht für die Strategieauswahl ausgewertet. Er ist ein zeitlich späterer Abschnitt desselben heutigen Datasets, kein damals archivierter Datenstand.
6. Nach jedem Zufallsstart den ersten Schlussbruch einer zuvor bekannten roten 4h-Linie suchen, maximal 60 weitere 4h-Kerzen. Ohne Ereignis ebenfalls ein Ergebnis speichern: kein Entry, Suchfenster abgelaufen oder Datenabschnitt zu Ende.
7. Ausbruch und späteren Retest getrennt beobachten. Der Retest braucht eine spätere Kerze mit Tief in der konfigurierten Zone um die ursprüngliche rote Linie und Schluss über der Zone. Ein Schluss unter der Zone verwirft den Retest. Standardannahme: ±20 Basispunkte (0,20 %), höchstens zwölf weitere 4h-Kerzen. Das sind überprüfbare Ereignisdefinitionen, keine als optimal bewiesenen Parameter.
8. Kontakte, Zeitspanne, Abstand zu Grün, Verletzung von Grün, Anordnung des Linienpaars und den bereits abgeschlossenen 1D-Kontext speichern. Darauf werden derzeit keine zusätzlichen harten Einstiegsfilter angewandt. Qualifiziert/vorläufig wird getrennt ausgewiesen; bei gemischten Paaren zählt die schwächere Qualität. „Vorläufig“ enthält neben Zwei-Kontakt-Linien auch andere Paare, die nicht beide Qualitätsbedingungen erfüllen. Exakte Kontaktzahlen bleiben im JSON erhalten.
9. Die erste danach beginnende Anbieter-4h-Kerze als beobachteten Einstieg verwenden. Das Signal wird standardmäßig erst 900 Sekunden nach Kerzenschluss verfügbar. Eine bereits vorher eröffnete Kerze ist deshalb kein zulässiger Eröffnungskurs. Diese konservative grobe Ausführungsannahme kann einen Einstieg erheblich verzögern; für genauere Ausführung brauchen wir später feinere Daten und eine definierte reguläre Sitzung.
10. Nach 5, 10 und 20 weiteren 4h-Kerzen Kursänderung, Nettokursänderung nach Kostenannahme, maximalen positiven/negativen Ausschlag und R-Beobachtungen speichern. Das sind Kerzenzahlen, keine Handelstage. Erweiterte Handelszeiten können enthalten sein.

Ein Auftrag erstellt einen vollständigen kausalen Ereignisstrom für den untersuchten Abschnitt ab dem frühesten gezogenen Start, statt nur das letzte Ereignis eines kurzen Chart-Rückblicks zu übernehmen. Die Linienwahl für einen Bruch erfolgt vor Kenntnis der neuen Kerze. Tagesmerkmale kommen ausschließlich aus bereits abgeschlossenen Tageskerzen. Originalanker und ursprüngliche grüne Schutzmarke werden pro Ereignis archiviert.

## Ergebnis lesen

- **Kursänderung:** Schluss des Beobachtungsfensters gegenüber beobachtetem Einstiegskurs.
- **Netto:** derselbe Verlauf mit angenommenen Kosten je Kauf- und Verkaufsseite, standardmäßig jeweils fünf Basispunkte. Keine vollständige Brokerabrechnung oder genaue Spread-/Slippage-Simulation.
- **MFE/MAE:** höchste bzw. niedrigste Kursabweichung im Fenster einschließlich der Einstiegskerze. Sie sind keine automatisch realisierten Gewinne/Verluste.
- **R:** Einstieg minus damalige grüne Schutzmarke (ggf. konfigurierter Puffer). Nur bei positiver Risikodistanz definiert. Die Marke ist ein fester ursprünglicher Preis, keine später nachgezogene Linie.
- **+1R/+2R vor Schutzmarke:** erste Berührungen im Verlauf vergleichen. Wenn beide Schwellen in derselben OHLC-Kerze möglich sind, wird kein Erfolg gutgeschrieben und die Mehrdeutigkeit markiert. Ein Gap-Stop wird in dieser Studie nicht als exakter Verkauf simuliert.
- **Unvollständig:** Such-/Retest-/Auswertungsfenster endet am Dataset- bzw. Holdout-Rand. Fehlende Zukunft wird nicht als Nullrendite oder Erfolg gewertet.
- **Überlappung:** verschiedene Starts können denselben Einstieg finden. Die Gruppentabelle dedupliziert nach Signal und Einstieg; Einzelfälle bleiben sichtbar. Verschiedene Signale mit überlappenden Verläufen bleiben statistisch abhängig. Wiederholte Aufträge werden nicht als unabhängige Beweise aufsummiert.

Vier Gruppen werden angezeigt: Ausbruch/Retest jeweils vorläufig/qualifiziert. Die Gruppen entstehen aus beobachteten Linienqualitäten, nicht durch Ausschluss der vorläufigen Fälle. „Positiv“ bedeutet ausschließlich positive Nettokursänderung im jeweiligen vollständigen Beobachtungsfenster. Für eine Handelsstrategie müssen wir später Ein-/Ausstieg, Stopnachziehen, Gaps, Kapital und zeitgleiche Positionen definieren.

`Signal` und `Verlauf` öffnen den vorhandenen Chart auf dem exakt verwendeten Dataset. Die ursprünglichen roten/grünen 4h- und 1D-Signallinien bleiben dort fixiert, während spätere Kerzen hinzukommen. Vor dem Signalzeitpunkt werden diese späteren Ereignisinformationen nicht eingeblendet. Der Entry wird nach Erreichen als Pfeil angezeigt. Ein Aktienwechsel verlässt diesen Dataset-Kontext. Persönliche Messungen/Rays bleiben browserlokal und werden nicht in die Forschung einbezogen.

## Dauerhafte Daten und Wiederaufnahme

- `data/datasets/<sha256>.json`: unveränderliche normalisierte Bestände mit Prüfsumme.
- `data/research/jobs.sqlite3`: Aufträge, versionierte Parameter, archiviertes Universum, Ereignisse und einzelne Versuche.
- `data/research/worker.lock`: Betriebssystem-Dateisperre verhindert zwei gleichzeitige Worker auf demselben lokalen Bestand.
- `TORI_DATA_DIR`: alternativer persistenter Datenordner für Marktcache, Datensätze, manuelle Snapshots und Forschung. SQLite nicht auf eine gemeinsame Netzwerkfreigabe legen.

Jeder vollständig ausgewertete Versuch ist ein transaktionaler Checkpoint. Nach einem Prozessabbruch werden laufende Aufträge wieder aufgenommen. Dataset und gezogene Starts bleiben erhalten. Eine unterbrochene Ereignisberechnung kann erneut laufen; abgeschlossene Versuche werden über stabile IDs nicht dupliziert. Ein abgebrochener Auftrag bleibt als Archiv erhalten. Fehlgeschlagene Titel werden ausdrücklich aufgeführt; bei gemischten Ergebnissen erhält der Auftrag den Status „teilweise abgeschlossen“.

Ändert sich die Engine-Version während der Unterbrechung, wird die alte Untersuchung nicht stillschweigend mit neuer Logik fortgesetzt. Ein neuer Auftrag ist erforderlich. Manifest enthält Codeprüfsumme, Linien-/Studienversion und Ausführungsannahmen. Es gibt derzeit keine automatische Regeloptimierung oder automatische Freigabe neuer Strategien.

Der tägliche Zeitplan startet wiederkehrende Forschungsaufträge, keine börsengetakteten Live-Einstiegsmeldungen. Eine verpasste Zeitplanperiode führt nach Wiederanlauf zu einem Auftrag, nicht zu einer Flut nachzuholender identischer Läufe. Bereits laufende automatische Aufträge überlappen sich nicht. Der gemeinsame Marktdatenabruf im Dienst hat ein konfigurierbares Prozessbudget (`TORI_API_REQUESTS_PER_MINUTE`, standardmäßig 150) und begrenzte Wiederholungen. Unabhängige zusätzliche CLI-Importer teilen dieses Prozessbudget nicht; sie sollten nicht parallel unkontrolliert laufen.

## Hermes-Werkzeuge ohne Browser

Vom Projektordner aus (Linux `python`, Windows `.venv\Scripts\python.exe`):

```text
python tori.py submit --spec deploy/experiment.example.json
python tori.py status --id <job-id>
python tori.py report --id <job-id>
python tori.py events --id <job-id>
python tori.py cancel --id <job-id>
python tori.py list
python tori.py worker --once
python tori.py worker
python tori.py import --symbol MSFT --history-days 900
python tori.py analyze --dataset <dataset-id> --asof 2025-10-01T20:00:00Z
```

Alle Werkzeuge geben JSON aus. Ein Standalone-Worker ist optional; der Webdienst startet bereits einen. Die Dateisperre verhindert Doppelarbeit. Mit `server.py --no-worker` lässt sich die Webansicht bei einem getrennten Worker betreiben.

**Betriebszustand und Ereignisseiten:** [BETRIEB-P1.md](BETRIEB-P1.md) beschreibt die lokale Health-/Fortschrittsanzeige, Tests und Lastmessungen. `python tori.py health` beziehungsweise `operations` in `/api/health` liefert Lebenszeichen, Phasen, Datenalter und Fehler ohne Providerabfrage. `events --id <id> --limit 250` liefert jetzt `{items, page}` statt einer vollständigen Liste. Mit `--cursor <page.nextCursor>` weiterblättern, bis `hasMore` falsch ist; HTTP entsprechend mit URL-kodiertem `cursor`. Die Seiten behalten ihren ersten Lesestand trotz neuer Ereignisse. Standard 250, maximal 1.000 pro Seite. Auch Auftragslisten enthalten keine großen Zufallspläne mehr; der einzelne Statusabruf behält sie.

**Datenbetrieb und Berichte (P2):** [BETRIEB-P2.md](BETRIEB-P2.md) beschreibt `storage`, `backup --output`, `verify-backup --path`, `restore --backup --target` und `cleanup-preview`. Backup/Restore benötigen neue Zielordner außerhalb des aktiven Datenpfads; die Vorschau löscht nichts. Die SQLite-Datenbank wird transaktional auf Schema 3 migriert; vor Updates konsistent sichern, keine automatische Rückwärtsmigration. Neue Datasets tragen ein beschreibendes Qualitätsaudit, ältere fehlende Audits werden ausgewiesen. Die Gruppentabelle trennt Versuche mit Entry, eindeutige Einstiege und Versuche ohne Entry. Je Horizont bleiben vollständige/unvollständige Fälle und zeitliche Überlappungen innerhalb desselben Datasets getrennt sichtbar. Das korrigiert keine statistische Abhängigkeit; der Holdout bleibt unbenutzt.

**Linux-Dienst und CLI müssen denselben Datenordner verwenden.** Bei der mitgelieferten Unit ist das `/var/lib/tori`. Für direkte Hermes-Aufrufe als berechtigter Dienstbenutzer `tori` deshalb `TORI_DATA_DIR=/var/lib/tori /opt/tori/.venv/bin/python /opt/tori/tori.py ...` benutzen. Optional `deploy/tori-tool` als ausführbares `/usr/local/bin/tori-tool` installieren; es setzt diesen Standardpfad und benötigt für `submit/status/report` keine Alpaca-Schlüssel. Für einen Agenten in einem anderen Container ist die authentifizierte HTTP-Schnittstelle der einfachere Weg.

Einzelfälle im Bericht sind auf 250 pro Seite begrenzt, damit ein großer Auftrag nicht die gesamte Webansicht blockiert. Gruppenergebnisse berücksichtigen den vollständigen Auftrag. Für weitere Fälle `report --offset 250 --limit 250` bzw. `?offset=250&limit=250` verwenden (maximal 1.000 pro Seite). JSON-Export enthält dieselbe paginierte Ansicht samt Seitenmetadaten; die UI bietet Weiter-/Zurückblättern.

Ein vollständig offline wiederholbarer Forschungsauftrag enthält zusätzlich `dataset_ids: {"MSFT": "<dataset-id>"}`. Das Manifest bindet ihn an die aktuelle Engine. Dann braucht die Berechnung weder Alpaca-Zugang noch Netzwerk. Die CLI `schedule --spec <file.json>` nimmt `{ "enabled": true, "interval_hours": 24, "spec": { ... } }` entgegen; ohne Datei wird der aktuelle Zeitplan ausgegeben.

Alternativ für einen Hermes-HTTP-Client:

```text
POST /api/research/jobs                 JSON: Forschungsparameter -> Job-ID, HTTP 202
GET  /api/research/jobs                 Aufträge, Zeitplan, aktiver Worker
GET  /api/research/jobs/<id>            Fortschritt und Metadaten
GET  /api/research/jobs/<id>/report     Ergebnis und Einzelfälle
GET  /api/research/jobs/<id>/events     Archivierte Linienereignisse
POST /api/research/jobs/<id>/cancel     JSON: {}
GET/POST /api/research/schedule         Zeitplan lesen/ändern
```

HTTP-Maschinenzugriff nutzt `Authorization: Bearer <TORI_API_TOKEN>`. Der Browser kann denselben Dienst über HTTP Basic (Benutzer `tori`, Passwort = Token) öffnen. Die Token-Eingabe nicht in URLs schreiben. Für Fernzugriff TLS über den vorhandenen internen Reverse Proxy verwenden; Host-/Origin-Prüfung passend zum tatsächlichen Host erhalten.

Hermes darf Aufträge starten, deren Zustand lesen und Ergebnisse erklären. Die Rechenengine arbeitet ohne LLM weiter. Historische Einstiegsauswahl durch ein heutiges LLM ist nicht Teil der Studie: dafür wären zeitlich passende Nachrichten, archivierte Eingaben/Ausgaben und zusätzliche Schutzmaßnahmen gegen Zukunftswissen nötig.

## Installation in einem Linux-LXC auf Proxmox

Hermes hat die Installation und erste Betriebsszenarien laut Nutzerbericht vom 18.10.2026 inzwischen im Container geprüft. Die neuen P1-/P2-Änderungen sind noch nicht dorthin ausgerollt. Die manuelle Webansicht und der Worker laufen gemeinsam als Python-Dienst; Docker und eine lokale LLM-Inferenz sind dafür nicht erforderlich. Python 3.12 und 3.13 wurden lokal geprüft; Abhängigkeiten stehen in `requirements.txt`.

1. Projekt nach `/opt/tori` kopieren, lokale Windows-`.venv`, Zugangsdaten, Logs und `.runtime` nicht übernehmen. Datasets/Forschung nur übernehmen, wenn der bisherige Bestand weitergeführt werden soll.
2. Dienstbenutzer `tori` und `/etc/tori` anlegen. In `/opt/tori/.venv` eine Linux-Python-Umgebung erzeugen und `requirements.txt` installieren.
3. `deploy/tori.env.example` nach `/etc/tori/tori.env` kopieren, echte Schlüssel und ein zufälliges langes Token lokal eintragen. `TORI_ALLOWED_HOST` auf den tatsächlich verwendeten Host einschließlich Port setzen. Datei nur für den Dienst bzw. root lesbar machen. Zugangsdaten nicht ins Repository übernehmen.
4. `deploy/tori.service` nach `/etc/systemd/system/tori.service` kopieren; danach `systemctl daemon-reload` und `systemctl enable --now tori`.
5. Browser unter dem konfigurierten Host öffnen; `/` ist Chart, `/research` ist Automatik. `journalctl -u tori` zeigt Dienstlogs. `systemctl status tori` und die Forschungsansicht zur Prüfung nutzen.

Die Unit schreibt unter `/var/lib/tori`; Quellcode bleibt schreibgeschützt. Der Netzwerkstart erfordert Token und expliziten erlaubten Host. Standardstart unter Windows bleibt ausschließlich `127.0.0.1:8765` ohne neue Netzwerkfreigabe. Bei Reverse Proxy oder anderer Portzuordnung die Host-Konfiguration entsprechend anpassen.

Die optionale Hermes-Anleitung steht unter `integrations/hermes/SKILL.md`. Sie ist eine Vorlage und wurde nicht in den bestehenden Agenten installiert.

Die Backup-CLI sichert Datasets, manuelle Snapshots und einen konsistenten SQLite-Stand einschließlich WAL über die Backup-API. Sie prüft Dateihashes und Referenzen. Wiederherstellung in einen neuen Ordner testen; Secrets/Browserzeichnungen sind nicht enthalten. Nicht bloß eine gerade beschriebene DB-Datei herauskopieren und WAL ignorieren. Details und geprüfte Befehle in BETRIEB-P2.md.

## Bewusste Grenzen

Alpaca-IEX ist die technische Testquelle; native Intraday-Kerzengrenzen und erweiterte Sitzungen bleiben erhalten. Neue Tageskerzen verwenden den versionierten XNYS-Sitzungsschluss einschließlich verkürzter Tage; alte Datasets behalten ihre gespeicherten Abschlüsse. Tatsächliche damalige Anbieter-Veröffentlichungszeiten werden nicht rekonstruiert. Rohkurse können Kapitalmaßnahmen enthalten. Das beschreibende Audit verifiziert Splits/Dividenden nicht automatisch und prüft kein historisches Instrumentenuniversum. Größere Aussagen über eine Strategie brauchen weitere Datenkontrollen und unabhängige Validierung. EODHD ist trotz des neuen Providervertrags noch kein implementierter Adapter.

Die neue Engine trennt Geometrie, Signalbeobachtung und zukünftige Auswertung. Sie ersetzt noch nicht eine ausdefinierte Portfolio-/Broker-Simulation. Die bestehende manuelle Fixierung und Browserwerkzeuge bleiben erhalten; die Forschungsfixierung wird serverseitig aus dem archivierten Signal berechnet.
