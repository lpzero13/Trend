
# Inkrementelles Kursupdate für Hermes

## Ausgangspunkt und Umfang

Der Branch `codex/incremental-daily-archive` integriert die Abend-Watchlist aus `fe5265001f2a13f075b8ce42c33a2f1598c96933` und das manuelle Papertrading aus `753aef1aea9a93dad80af7bc2ab68fcd7d2da38c`. Beide basieren auf `1ed3aab6173499fabd919239a90fdb3fd41656db`. Der lokale CT118-Integrationscommit war im GitHub-Checkout nicht verfügbar. Der nachvollziehbare Integrationscommit `f5c2dff2ca2820b6264992622aff96027f5ddcb6` ist zugleich die gemessene Referenz.

Der bisherige Tagespfad hydratisierte die vollständige 5m-Historie, aggregierte alle Sitzungen neu und serialisierte und prüfte den Gesamtbestand mehrfach. Er verwendete identische physische Monatsdateien bereits wieder. Der CPU- und Speicheraufwand entstand vor allem vor und nach diesem Wiederverwendungsschritt. Die Tests laufen mit eigenen Datenverzeichnissen und protokolliertem Offline-Provider. Die Abnahme im Container steht aus.

## Datenvertrag und Dateien

- `daily_archive.py` plant je Symbol über Rohdatencursor und gespeicherten Prüfstand. Die drei lokal gespeicherten Universen werden dedupliziert. Der Normalmodus verarbeitet einen kleinen Rückstand und meldet größere Rückstände. Reparaturen bekommen einen eigenen Aufruf. Der gemeinsame Collector-Lock schützt vor parallelem Bulk-Abruf. Der gemeinsame Provider-Limiter zählt Versuche und Retries und übernimmt 429-Cooldowns. Vollständige Sitzungsantworten landen mit SHA-256 in SQLite. Die Cache-Schlüssel binden Modus, Stichtag, Symbol und Sitzung.
- `daily_delta.py` prüft die referenzierten komprimierten Bytes, liest relevante 5m-Sitzungen und prüft die Vergleichssitzung auf übereinstimmende OHLC-Werte. Volumenrevisionen bleiben nachvollziehbar. Der XNYS-Kern berechnet die betroffenen 1h-, 4h- und Tagesbuckets. Betroffene Wochen werden mit der vollständigen erwarteten Kalenderwoche berechnet. Eine Woche kann aus Bars zweier Monatsblöcke bestehen. Die tägliche Qualitätsprüfung verwendet die Tagesreihe. Die RTH-Metadaten der neuen Version benennen die betroffenen Sitzungen. Der frühere vollständige RTH-Bericht bleibt im referenzierten Quelldataset erhalten.
- `parquet_store.py`, `datasets.py` und `maintenance.py` unterstützen das Manifestformat `tori-parquet-2`. Es verwendet die vorhandenen typisierten Parquet-Dateien. Für neue Monatsblöcke wird der exakte Inhalt einschließlich Zahlentypen rückgelesen. Die V2-ID bindet per SHA-256 den Formatnamen, den Datenkontext und den geordneten Blockindex inklusive Datei-Prüfsummen und Frame-Zählungen. Parquet-V1- und Legacy-JSON-Datasets behalten die bisherige Identität über das vollständige Kursmaterial. Beim Ableiten eines V2-Stands prüft der Lauf die gespeicherten SHA-256-Prüfsummen der bereits bei Veröffentlichung vollständig geprüften Altblöcke. Die Material-ID des Altdatasets wird weiterhin beim vollständigen Lesen dieses Datasets geprüft.
- Der Publisher synchronisiert neue Blockdateien und das neue Manifest vor dem SQLite-Checkpoint. Neue 5m-Kerzen bleiben auch bei fehlender vollständiger Tageskerze erhalten. Ein Abbruch vor Manifestveröffentlichung lässt das alte Manifest als gültigen Stand zurück. Ein Abbruch nach Veröffentlichung kann aus dem neuen Manifest wiederanlaufen. Jeder frühere Stand bleibt unter seiner bisherigen ID verfügbar. Der inkrementelle Lauf aktualisiert bestehende Parquet-Archive. Legacy-JSON bleibt für Chart und Forschung lesbar. Die SQLite-Schemaversion bleibt gleich.
- `daily_review.py` wertet dieselben 4h- und Tageskurse bis zum abgeschlossenen Stichtag aus. Der Ergebniscache bindet lokale Dataset-Dateistände, Regelprofil, Analysecode, Auswertungszeitpunkt und Vergleichsbericht. Eine Dateiänderung invalidiert das Ergebnis. Nach einer Stunde wird erneut geprüft. Sortierung, Linienregeln und Chartlinks behalten ihren Datenvertrag.
- `archive_cli.py`, `SAMMLER-V2.md` und `HERMES.md` dokumentieren die Betriebsmodi. `tests/test_daily_delta.py` deckt formatübergreifende Leser, Referenzdaten, Wiederanlauf, Sperren, Korruption und Backup/Restore ab. `tools/benchmark_daily_archive.py` und `reference/daily-archive-benchmark.json` liefern den reproduzierbaren Vergleich.

## Kurzbefehle für den Betrieb nach Freigabe

Arbeitsverzeichnis ist `alpaca-trendlinien/`. Verwende den Dienstbenutzer, seine bestehende Python-Umgebung und den Datenpfad des Dienstes. Hermes legt die Startzeit fest. Die Zielsitzung ist der letzte reguläre XNYS-Schluss mit 16 Minuten Datenpuffer.

~~~sh
export TORI_DATA_DIR=/var/lib/tori

# Vorschau ohne Providerzugriff
python tori.py archive-update --plan

# Normaler Tageslauf und Abend-Watchlist
python tori.py archive-review --workers 1 --progress

# Begrenzter Nachhollauf, je Titel fünf alte Sitzungen plus Überlapp
python tori.py archive-update --mode catchup --max-sessions 5 --workers 1 --progress

# Bekannte Lücken oder eine explizit gewählte Sitzung prüfen
python tori.py archive-update --mode repair --max-sessions 3 --workers 1 --progress
python tori.py archive-update --mode repair --session 2026-11-13 --workers 1 --progress

# Vorfilter aus lokalem Stand
python tori.py archive-review --scan-only --base-url https://tori.example.internal --progress
~~~

Bei einer Reparatur zeigt `--plan` zuerst, welche Titel und Sitzungen betroffen sind. `checkedThrough`, `lastBarSession` und `lastSession` bezeichnen Prüfstand, letzte 5m-Sitzung und letzte vollständige Tageskerze. `backlogSessions`, `missingBarsBySession`, `gapStatus`, `errorKind` und `interrupted` geben die Betriebsfälle an. Eine geprüfte Sitzung kann Lücken haben. Bei einer OHLC-Revision oder einem Split braucht der Titel eine separat freigegebene neu bereinigte Historie. Die anderen Titel können durchlaufen.

## Reproduzierbarer Offline-Benchmark

Linux unter WSL2, eine CPU per Prozessaffinität, ein Worker und identische synthetische 5‑Minuten-Kurse von Anfang 2016 bis November 2026. Die Eingabe deckt 2.739 abgeschlossene XNYS-Sitzungen mit 212.886 5m-Kerzen je Aktie ab. Der erste Aufruf läuft in einem frischen Prozess. Die Wiederholung verwendet denselben Prozess. Der Betriebssystem-Dateicache wurde nicht geleert. Beide Pfade laufen unter einem Limit von 1.024 MiB ohne Swap. Der neue Pfad läuft zusätzlich mit einem harten Limit von 512 MiB ohne Swap. Der Vergleich prüft die Hashes sämtlicher 5m-, 1h-, 4h-, 1D- und vollständiger 1W-Kerzen sowie der Tagesprüfung. Der Vorfiltervergleich prüft Kandidaten und Linienmerkmale. Die Dataset-IDs in den Chartlinks folgen dem jeweiligen Formatvertrag.

~~~sh
git worktree add --detach /tmp/tori-baseline f5c2dff2ca2820b6264992622aff96027f5ddcb6
cd alpaca-trendlinien
python tools/benchmark_daily_archive.py \
  --baseline /tmp/tori-baseline/alpaca-trendlinien \
  --comparison-cap-mib 1024 --cap-mib 512 \
  --output /tmp/tori-daily-benchmark.json
~~~

Der Benchmark benötigt die Anwendungsabhängigkeiten und für die Speichergrenzen einen Linux-Systemd-User-Scope. `VmHWM` misst den Prozess-RSS-Spitzenwert. Der Cgroup-Spitzenwert verwendet eine eigene Speicherzuordnung inklusive Dateicache. Die `/proc`-I/O-Zähler beinhalten logische Lese- und Schreibbytes sowie physische I/O-Zähler. Die JSON-Datei weist außerdem wiederverwendete und neu geschriebene Blöcke, zur Prüfsumme gelesene Bytes und Offline-Anfragen aus. [Maschinenlesbare Messung](reference/daily-archive-benchmark.json)

| Szenario | Dauer alt → neu | CPU-Zeit alt → neu | Peak-RSS alt → neu |
|---|---:|---:|---:|
| Ein Titel, eine neue Sitzung | 8,45 → 2,01 s | 8,38 → 1,97 s | 586 → 163 MiB |
| Drei Titel, je eine neue Sitzung | 20,08 → 2,36 s | 19,92 → 2,29 s | 586 → 165 MiB |
| Ein Titel, drei Sitzungen nachholen | 8,62 → 1,96 s | 8,56 → 1,91 s | 585 → 162 MiB |

Im Drei-Titel-Lauf wurden in beiden Pfaden drei Parquet-Blöcke veröffentlicht und 390 wiederverwendet. Der neue Pfad las für Prüfsummen 19,73 MB statt zuvor 58,47 MB. Die Wiederholung dauerte mit dem neuen Pfad ungefähr 3 ms. Dabei fielen null Provider-Aufrufe und null neue Dataset-Dateien an. Spitzenwerte bei späteren Phasen in der JSON-Datei gelten kumulativ ab Prozessstart.

Der Vorfilter lieferte jeweils dieselben drei Kandidaten mit identischen Linienmerkmalen. Der erste Scan dauerte im neuen Pfad 0,87 s gegenüber 0,41 s in der Referenz. Der wiederholte Scan mit Cache dauerte 0,012 s gegenüber 0,399 s. Alle drei Szenarien liefen auch unter dem harten 512-MiB-Limit mit einem Worker. Die Ressourcentabelle in der JSON-Datei weist die Spitzenwerte einschließlich Vorfilter aus. Der Swap-Peak betrug null. Diese Messung deckt den Einzel-Worker ab. Ein Vollbestandstest mit 520 Titeln und eine Messung des gesamten Containers bei parallelem Webdienst und Paper-Worker stehen aus.

Die Python-Suite lief mit 595 Tests und einem bestehenden Skip ohne Fehler. Darin enthalten sind Papertrading, Update- und Leserkompatibilität, Backup/Restore, Abbruchszenarien und ein an die Referenz gebundener Vergleich über Sommerzeit, verkürzte Sitzungen sowie Monats- und Jahreswechsel. 84 JavaScript-Tests des Hauptprojekts und 49 Tests des Positionsrechners sind ebenfalls bestanden.

## Installation und Rollback

1. Nach separater Freigabe den exakten Übergabecommit mit dem passenden Reader in einem separaten Checkout bereitstellen. Vor produktiver Nutzung SQLite, Datasets und Paper-Ledger sichern und den Restore in einem neuen Testverzeichnis prüfen. Die neue Version mit einer isolierten Datenkopie, dem Dienstbenutzer und den für CT118 vorgesehenen Limits abnehmen.
2. Vor dem ersten freigegebenen Containerlauf per `--plan` die Mitgliedslisten sowie normale Fälligkeiten, Rückstände und fehlende Lokalhistorien prüfen. Der gestoppte historische Sammelauftrag bleibt gestoppt. Alte Aufträge binden ihren Engine-Code. Im Pilotlauf Speicher- und Swap-Peak des Updateprozesses sowie den Gesamtverbrauch mit Webdienst und Paper-Worker messen.
3. Für einen Rollback Tagesupdate und Vorfilter stoppen. Solange V2-Bestände gelesen werden sollen, einen V2-fähigen Reader im laufenden Datenordner verwenden. Bei einem Rollback auf den früheren Code das vorab gesicherte Abbild in einem separaten Datenverzeichnis verwenden. Die neueren Kursstände und die seit dem Backup erfassten Paper-Bewegungen im bisherigen Verzeichnis aufbewahren. Eine V2-ID kann nicht als V1-ID umgedeutet werden.

Offen bleiben die Betriebsabnahme mit produktivem Datenumfang, Dateicache, Parallelbetrieb der Containerdienste und passender CPU-Quote. Der Überlapp prüft die aktuell bereitgestellte Providerbereinigung. Unbemerkte Kursrevisionen außerhalb dieses Fensters können separat untersucht werden. Die Laufzeit des Bestandskatalogs kann mit der Zahl vorhandener Versionen wachsen. Abgebrochene Cache-Teilbestände sind unter demselben Stichtag und Modus wiederverwendbar. Alte Kursbestände und unreferenzierte Blöcke bleiben bis zu einer gesonderten Wartung auf Datenträger.
