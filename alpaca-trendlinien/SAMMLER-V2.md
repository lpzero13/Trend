# Datensammler V2: Bedienung und Betrieb

Stand: **30.10.2026**. [Messwerte und Hochrechnung](SAMMLER-V2-ERGEBNISSE.md).

V2 ist lokal implementiert und mit fünf echten US-Aktien geprüft. Der frühere 100er-Auftrag bleibt separat pausiert: 69 Aktien und 9.074 Monatscheckpoints sind erhalten. Ein GitHub-Update transportiert Quellcode und Dokumentation; Kursdaten und Zugangsdaten werden separat verwaltet.

## Webansicht

Menü **Datensammler**, Route `/sammler`:

1. **Bestandslisten aktualisieren** lädt nur Universumslisten von den Emittenten, keine Aktienkurse.
2. Ein oder mehrere Universen auswählen. Die Vorschau zählt verschiedene Symbole; Überschneidungen werden entfernt. Beispielsweise enthalten die geladenen S&P-500- und Dow-Abbilder zusammen 505 verschiedene Symbole.
3. Zeitraum wählen. Das Ende wird beim Anlegen eingefroren und muss mindestens 15 Minuten alt sein. Ohne Eingabe gilt der aktuelle Zeitpunkt abzüglich 16 Minuten.
4. Optional einen geprüften **Altbestand übernehmen**. Dann gelten dessen ursprünglicher Zeitraum und Datenstand. Die Datumsfelder werden entsprechend festgesetzt.
5. **Auswahl sammeln** legt einen Auftrag an und startet ihn ausdrücklich. Das Öffnen der Seite, die Vorschau und Statusabfragen starten keinen Kursimport.
6. **Pause · Fortschritt behalten** fordert einen geordneten Stopp an. Vollständige Monate bleiben gesichert. Die aktuell laufende HTTP-Anfrage kann noch bis zu ihrem Timeout benötigen. Später **Starten / fortsetzen** verwenden.

Die Oberfläche zeigt fertige Aktien, abgeschlossene Monate, Dateigröße, aktuelle Phase und Fehler. Bestandszahlen sind zunächst Hinweise: Ein vorhandener kürzerer oder anders bereinigter SIP-Bestand ist noch kein vollständig wiederverwendbarer Datenbereich. Die Zeitschätzung bezieht sich deshalb ausdrücklich auf einen vollständigen Erstimport.

Die Auftragsliste überträgt keine vollständigen Aktiendetails. Die Detail-API liefert standardmäßig 50, höchstens 200 Aktien pro Seite (`offset`/`limit`). Host-, Origin- und vorhandene Tokenprüfungen des Servers bleiben aktiv; interner loginfreier Zugang folgt weiterhin der bestehenden Serverkonfiguration.

## Universen und Quellen

Die Auswahl basiert auf **aktuellen ETF-Aktienbeständen als Index-Abbild**. Sie ist keine lizenzierte historische Indexmitglieder-Datenbank. Aktienklassen, Residualpositionen und Indexänderungen erklären Abweichungen von nominalen Größen. Für historische Forschung wird die beim Anlegen gewählte Zusammensetzung mit Namen, Quelle, Quellenstand und Datei-Prüfsumme eingefroren.

| CLI-ID | Quelle | Geladene Symbole, Stand 28.10.2026 |
|---|---|---:|
| `dow30` | State Street DIA | 30 |
| `sp100` | iShares OEF | 101 |
| `nasdaq100` | iShares CNDX | 101 |
| `sp500` | iShares IVV | 505 |
| `russell1000` | iShares IWB | 1.024 |
| `russell2000` | iShares IWM | 1.963 |
| `dow_plus70` | Dow-30 plus 70 weitere OEF-Titel | 100 |

Beim IWM-Abbild sind zwölf Sonderpositionen ausdrücklich in `excludedHoldings` dokumentiert, beispielsweise CVRs, private/restringierte Positionen oder Einträge ohne abfragbares Symbol. Sie werden nicht als gewöhnliche Aktienkurse behandelt. Cash und Derivate gehören ebenfalls nicht zur Aktienauswahl. Unbekannte doppelte gewöhnliche Symbole, unlesbare Dateien und unerwartete Listengrößen führen zu einem Fehler; ein zuvor gespeicherter Katalog bleibt erhalten.

Alle sieben Auswahlen zusammen enthalten im geladenen Quellenstand **3.002 verschiedene Symbole**, nicht die Summe aller einzelnen Listen. Eigene Symbollisten sind über eine CLI-Spezifikation möglich. Europäische Originalnotierungen und EODHD sind weiterhin ein späterer Ausbau.

## Hermes-CLI

Im Anwendungsverzeichnis `alpaca-trendlinien/` arbeiten. Im Container denselben Datenpfad wie der Dienst verwenden:

```sh
export TORI_DATA_DIR=/var/lib/tori
python tori.py archive-universes --refresh all
python tori.py archive-universes
python tori.py archive-estimate --universes sp500
python tori.py archive-create --universes sp500 --workers 8
python tori.py archive-run --id AUFTRAGS_ID
python tori.py archive-status --id AUFTRAGS_ID
python tori.py archive-pause --id AUFTRAGS_ID
python tori.py archive-list
```

`archive-create` gibt die neue ID und eingefrorene Spezifikation aus. Ein Anlegen per CLI startet noch keinen Download. `archive-run` ist ein eigenständiger Prozess und endet nach Abschluss. Es richtet keinen Zeitplan ein. Hermes kann diesen Prozess später im eigenen überwachten Betriebsablauf starten.

Mehrere Universen in **einem** Auftrag zusammenführen:

```sh
python tori.py archive-estimate --universes sp500,russell1000
python tori.py archive-create --universes sp500,russell1000
```

Eigene Liste oder zusätzliche Einstellungen:

```json
{
  "symbols": ["AAPL", "GS", "KO", "BNY", "SNDK"],
  "start": "2016-01-01T00:00:00Z",
  "feed": "sip",
  "adjustment": "split",
  "workers": 8,
  "requests_per_minute": 190,
  "universe": {
    "name": "Meine Watchlist",
    "sources": [{"url": "https://meine-dokumentierte-quelle.example", "asOf": "2026-10-28"}]
  }
}
```

```sh
python tori.py archive-create --spec /pfad/watchlist.json
```

Spezifikationen und Laufdaten gehören nicht ins öffentliche Repository, soweit sie persönliche Laufstände enthalten. Schlüssel werden ausschließlich über den vorhandenen serverseitigen Zugang gelesen.

## Geprüfte Übernahme des alten Sammlers

```sh
python tori.py archive-list
python tori.py archive-create --universes dow_plus70 --adopt-from ALTE_V1_ID
python tori.py archive-run --id NEUE_V2_ID
```

Der neue Auftrag erhält Zeitraum, Feed, Bereinigung, Datenvintage und den ursprünglichen Symbolstand des Altauftrags. Beim Start werden Dateien und fertige Datasets geprüft und übernommen. Erst anschließend werden fehlende Monate geladen. Der Altauftrag wird nicht geändert und sein Enginehash wird nicht umgeschrieben.

Alternativ einen bereits passend angelegten neuen Auftrag ausdrücklich prüfen/übernehmen:

```sh
python tori.py archive-adopt --id NEUE_V2_ID --source ALTE_V1_ID
```

Dieses Kommando setzt identische Datenverträge einschließlich `asof` voraus. `--adopt-from` beim Anlegen setzt diese Felder automatisch. Die aktuelle v1-Übernahme akzeptiert nur zur gewählten Tagesvintage passende Abrufdaten; mehrtägige v1-Altaufträge benötigen eine gesondert geprüfte Übernahmeregel. Der tatsächlich vorhandene 69er-Bestand wurde am 29.10.2026 gesammelt und erfüllt diese Voraussetzung. Seine Übernahme wurde in dieser Entwicklungsrunde nicht gestartet.

Für den Container müssen die Kursdateien und die zugehörigen Metadaten separat übertragen werden. Der vorhandene Backup-/Restore-Weg sichert auch die referenzierten Monatscheckpoints. Ein Restore überschreibt kein vorhandenes Zielverzeichnis. Bestehende Containerdaten deshalb vor einem Austausch/Abgleich gesondert berücksichtigen; `/var/lib/tori` und lokale Secrets nicht stillschweigend ersetzen.

## Geschwindigkeit und Datenvertrag

- Bis zu acht Downloadarbeiter standardmäßig, konfigurierbar zwischen eins und zwölf.
- Parallel bearbeitete Jahresfenster; API-Seitengrenzen sind unabhängig von den monatlichen Dateigrenzen.
- Threadlokale wiederverwendete HTTPS-Verbindungen zum festen read-only Alpaca-Endpunkt.
- Standardbudget 190 Versuche/Minute, weiterhin unter dem dokumentierten Basic-Kontolimit von 200. Ein ausdrücklich gesetztes `TORI_API_REQUESTS_PER_MINUTE` ist auch für V2 eine zusätzliche Obergrenze. Wiederholungsversuche zählen mit; HTTP 429 setzt eine gemeinsame Wartefrist.
- Das Budget wird über Prozesse mit demselben Datenpfad geteilt. Andere Hosts oder getrennte Datenpfade koordinieren sich damit nicht automatisch. Pro Alpaca-Konto entsprechend nur einen unabhängigen Bulk-Collector betreiben beziehungsweise Budgets aufteilen.
- Kleine transaktionale Einträge je Auftrag, Aktie und Monat in der vorhandenen SQLite-`settings`-Tabelle; keine neue Schema-Migration.
- Typisierte Parquet/Zstd-Monatsdateien ohne CSV-Zwischenschritt im Downloadpfad. Der bestehende unveränderliche Dataset-Publisher bleibt der gemeinsame Veröffentlichungsweg.
- Eine Aktie gleichzeitig zur Veröffentlichung, damit der Speicherbedarf nicht mit der Zahl gleichzeitiger Downloads vervielfacht wird.

Basis sind reguläre 5-Minuten-Kerzen. Der vorhandene gemeinsame Kalender/Rechenkern leitet daraus 1h, 4h, 1D und vollständige 1W-Kerzen ab. Feiertage, Sommerzeit und verkürzte Sitzungen bleiben berücksichtigt. Fehlende Kerzen werden nicht erfunden; unvollständige höhere Aggregate werden ausgelassen und protokolliert. Die Signallogik und persönliche Browserzeichnungen werden nicht geändert.

`asof` bezeichnet die Identität des angefragten Symbols, **nicht** den Preiskerzen-Stichtag. Standard ist der Symbolstand der Abrufvintage. So kann ein heutiger umbenannter Titel auch bei einem älteren Preis-Enddatum seine zugehörige frühere Historie finden. Der Preis-Endzeitpunkt begrenzt weiterhin strikt die zugelassenen abgeschlossenen Kerzen.

Die Platzprüfung für neue V2-Aufträge rechnet vorsichtig mit **4.000 Bytes je Aktie und Kalendertag plus freier Reserve**. Sie kann deshalb mehr freien Platz verlangen als die reine Dateigrößen-Hochrechnung im Ergebnisbericht. Das schützt die Veröffentlichung und temporäre Arbeit; die tatsächlichen Dateigrößen werden im Fortschritt getrennt ausgewiesen.

## Wiederaufnahme, Cache und Sicherung

Jeder vollständig empfangene Monat wird validiert, als Parquet geschrieben, synchronisiert, mit Prüfsumme exakt zurückgelesen und erst dann in SQLite referenziert. Zeitstempel, OHLCV, Sortierung, widersprüchliche Duplikate und Paginierung werden geprüft. Als leer bestätigte Monate werden ebenfalls gespeichert. Ein abgebrochener unvollständiger Monat wird erneut geladen; abgelaufene Seitentokens verhindern keine Wiederaufnahme.

Bereits vollständig rückgelesene unveränderliche Dateien können nach erneuter Größen-/Dateihashprüfung wiederverwendet werden. Die abschließende Dataset-Veröffentlichung validiert die tatsächlichen Kurswerte erneut. Beschädigte Checkpoints werden nicht still übersprungen.

Cacheverträge trennen Symbol, Feed, Bereinigung, Normalisierung, Symbolstand und Datenvintage. Wiederverwendung über verschiedene Universen funktioniert für passende gemeinsame Datenstände. Abweichende Monatsgrenzen, insbesondere ein späteres Ende im laufenden Monat, können einen erneuten Abruf dieses Monats erfordern.

**Noch geplant:** automatische tägliche Fortschreibung splitbereinigter Historien über neue Vintages hinweg. Dafür müssen Kurskorrekturen und Corporate Actions versionsbewusst behandelt werden. V2 mischt nicht blind alte bereinigte Preise mit einem neuen Datenstand. Die derzeitige Vintage ist ein eingefrorener Abrufbatch, keine vom Anbieter garantierte historische Corporate-Action-Version.

Ein Auftrag bindet den relevanten Codehash. Nach einer Kernänderung einen neuen Auftrag anlegen; alte Forschungs-/Importaufträge nicht durch manipulierte Hashes fortsetzen. Fertige Kursbestände bleiben lesbar. Der Cache darf nur bei weiterhin passendem, versioniertem Datenvertrag übernommen werden.

Nach einem harten Prozessabbruch kann der letzte Status noch `running` lauten. Prozess und Dateisperre prüfen; `updatedAt`/`stale` liefern Hinweise. Die Webansicht kann einen ausdrücklich gestarteten Auftrag nach einem Dienstneustart weiterführen. Sie ist kein eigener garantierter Import-Scheduler.

## Unabhängige Offline-Prüfung

```sh
python tools/verify_archive.py --id AUFTRAGS_ID --output /pfad/pruefbericht.json
```

Der Prüfer unterstützt v1 und v2, benötigt keine Providerzugangsdaten und liest alle referenzierten Kursdateien mit Prüfsummen. Er rechnet jedes gespeicherte Stunden-, Vierstunden- und Tagesaggregat aus seinem exakten 5m-Intervall nach und vergleicht den vollständigen Wochen-Cache. `--watch` prüft neue fertige Aktien während eines ausdrücklich laufenden Imports. Für eine erneute vollständige Prüfung einen neuen Berichtspfad verwenden.

Sicherungen umfassen SQLite, referenzierte Datasets und referenzierte v1/v2-Monatsdateien; Zugangsdaten und große Roh-JSON-Caches bleiben ausgeschlossen. Es wurde kein automatisches Löschen alter Bestände ergänzt.
