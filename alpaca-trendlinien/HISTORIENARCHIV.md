# Historienarchiv V1: erster Sammelimport

**Aktueller Standard ist V2:** [Bedienung und Betrieb](SAMMLER-V2.md), [Vergleich und Hochrechnung](SAMMLER-V2-ERGEBNISSE.md). Dieses Dokument beschreibt den ersten Implementierungsstand. `archive-create` legt inzwischen V2-Aufträge an; für aktuelle CLI-Beispiele den V2-Leitfaden verwenden. Vorhandene v1-Kursdateien bleiben erhalten und können geprüft übernommen werden.


Stand: 29.10.2026. Der neue Sammler ergänzt die bestehenden Imports. Er ändert weder Signalregeln noch laufende Forschungsaufträge oder automatische Handelsentscheidungen.

## Datenvertrag

- Explizite Datumsgrenzen ab **1. Januar 2016**, ohne die 3.650-Tage-Grenze des bisherigen Chartimports. Das Ende wird beim Anlegen festgehalten; alle Aktien erhalten denselben Stichtag.
- Standard **Alpaca SIP**, `split`, 5-Minuten-Basis. Das Ende muss mindestens 15 Minuten alt sein. Zugang und tatsächliche Verfügbarkeit werden beim Abruf geprüft; keine kostenpflichtige Bestellung und keine Orders.
- Reguläre XNYS-Sitzungen. Aus denselben 5m-Kerzen werden **1h, 4h, 1D** und der bestehende Cache vollständiger **1W**-Kerzen abgeleitet. Letzter 4h-Block kann kürzer sein. Feiertage, Sommerzeit und verkürzte Sitzungen verwenden den gemeinsamen Kalender.
- Fehlende 5m-Kerzen werden nicht aufgefüllt. Unvollständige größere Kerzen werden ausgelassen. Zusätzlich zur bisherigen Bucketprüfung zählt das Archiv vollständig fehlende Sitzungen und unterscheidet interne, führende und nachlaufende leere Sitzungen. Ein leerer Anfang beweist kein Börsengangsdatum.
- Splitbereinigung ist der Providerstand beim Abruf, **kein historisch garantierter Corporate-Action-Vintage**. SIP/IEX, Bereinigung und Normalisierung bleiben getrennt. Dividenden werden bei `split` nicht zu einem Total-Return-Verlauf umgerechnet.
- Heutige Universumsmitglieder werden rückwirkend untersucht. Das ist keine historische Indexzusammensetzung und beseitigt keinen Survivorship Bias.

Offizielle Quellen: [Alpaca Datenpläne](https://docs.alpaca.markets/us/docs/about-market-data-api), [historisches SIP und Verzögerung](https://docs.alpaca.markets/us/docs/market-data-faq), [Bars/Paginierung](https://docs.alpaca.markets/us/reference/stockbars).

## Speicherung und Wiederaufnahme

Monatsabrufe gehen direkt in unveränderliche **Parquet/Zstd**-Checkpoints unter `TORI_DATA_DIR/imports/chunks/`. Es entsteht kein zusätzlicher großer JSON-Kurscache. Kleine Job-/Universums-/Qualitätsmetadaten liegen in der vorhandenen SQLite-Tabelle `settings`; keine neue Datenbankschema-Migration.

Nach jedem vollständigen Monatsabruf: OHLCV-/Zeitprüfung, Prüfung widersprüchlicher Duplikate und Paginierung, reguläre Sitzungsauswahl, Parquet-Rundlauf, Dateiprüfsumme, anschließend SQLite-Commit. Leere, erfolgreich abgefragte Monate erhalten ebenfalls einen Checkpoint. Unvollständige Monatsabrufe werden bei Wiederaufnahme erneut geladen. Vor Wiederverwendung werden Dateien/Prüfsummen geprüft. Beschädigte Dateien werden nicht still übergangen.

Maximal vier Monatsabfragen laufen gleichzeitig. Das **gemeinsame rollierende Abruflimit** in `provider_budget.py` gilt über Prozesse mit demselben `TORI_DATA_DIR`, standardmäßig 150 Versuche pro Minute, maximal 200 konfigurierbar über `TORI_API_REQUESTS_PER_MINUTE`. Wiederholungen verbrauchen ebenfalls Slots; HTTP 429 setzt eine geteilte Wartefrist. Andere Anwendungen oder getrennte Datenverzeichnisse sind nicht erfasst. Bereits laufende Python-Prozesse verwenden bis zum regulären Neustart ihren alten Code.

Pro Aktie wird danach genau ein bestehendes, unveränderliches reguläres Dataset veröffentlicht. Die Daten sind in den bestehenden lokalen Dataset-/Fächer-/Zufalls- und Forschungswegen nutzbar. Der Sammler hält nur eine Aktie zur Veröffentlichung im Speicher, nicht das ganze Universum. Die monatlichen Downloadcheckpoint-Dateien bleiben zusätzlich zum fertigen Dataset erhalten; ihre Größe wird separat ausgewiesen. Kein automatisches Löschen alter Bestände.

Speicherprüfung vor dem Job und vor jedem neuen Monat; Schätzung ist konservativ, kein Größenversprechen. Betriebssicherung und Restore umfassen auch die in der SQLite-Sicherung referenzierten Monatscheckpoints. Fertige Dataset-Referenzen sind durch den vorhandenen Aufräumvorschau-Schutz erfasst.

Archivjobs binden den relevanten Collector-/Provider-/Normalisierungs-Codehash. Nach einer entsprechenden Codeänderung keinen alten Job unter neuer Engine weiterlaufen lassen. Unveränderte Jobs nach SIGINT/SIGTERM oder einem Prozessabbruch mit derselben ID fortsetzen. Eine betriebssystemseitige Sperre lässt nur einen Archivsammler je Datenverzeichnis zu. Ein harter Prozessabbruch kann `status=running` zurücklassen: `updatedAt` beachten und Prozess prüfen; ein unveränderter Job kann erneut gestartet werden. Das ist kein eigener dauerhaft überwachter Dienst.

## Hermes-CLI

Im Anwendungsverzeichnis arbeiten. Im Container **immer denselben** `TORI_DATA_DIR=/var/lib/tori` wie der Webdienst verwenden. Lokale Zugangsdaten/Environment erhalten; sie gehören weder in die Spezifikation noch ins Repository.

```sh
python tori.py archive-create --spec /pfad/universe.json
python tori.py archive-run --id <ID>
python tori.py archive-status --id <ID>
python tools/verify_archive.py --id <ID> --output /pfad/lokaler-pruefbericht.json
```

Der zusätzliche Offline-Prüfer liest alle veröffentlichten Kurse und Monatsdateien mit Prüfsummen zurück, berechnet jede gespeicherte 1h-/4h-/Tageskerze direkt aus ihrem exakten 5m-Intervall nach und vergleicht den Wochen-Cache. `--watch` prüft neu fertiggestellte Aktien bereits während eines laufenden Imports; ohne diese Option wird einmalig der aktuelle Stand geprüft. Ein vorhandener Prüfbericht wird fortgeschrieben; für eine erneute vollständige Prüfung einen neuen Ausgabepfad wählen. Auch Prüfberichte bleiben lokale Artefakte.

`archive-run` gibt je abgeschlossener Aktie eine JSON-Fortschrittszeile und zum Schluss die Zusammenfassung aus. Die bestehende Forschungsqueue wird nicht automatisch gestartet oder geändert. `requests` zählt erfolgreich zurückgegebene Providerseiten des Jobs, nicht sämtliche HTTP-Wiederholungsversuche. Ein fehlgeschlagener Titel führt zu `partial`, nicht zu einer falschen Vollständigkeitsmeldung. Derselbe Aufruf wiederholt die noch fehlenden Monate. SIGINT/SIGTERM pausiert nach Sicherung vollständig empfangener Monate. Statusabfragen benötigen keine Provideraufrufe.

Beispielspezifikation (Datumsende optional, beim Anlegen eingefroren):

```json
{
  "symbols": ["AAPL", "MSFT"],
  "start": "2016-01-01T00:00:00Z",
  "feed": "sip",
  "adjustment": "split",
  "universe": {
    "name": "Mein eingefrorenes Universum",
    "asOf": "2026-10-28",
    "sources": [{"url": "https://quelle.example/bestand", "asOf": "2026-10-28", "sha256": "Originaldatei-Pruefsumme"}]
  }
}
```

## Erstes Universum

Vom Nutzer ausgewählt: **alle Dow-30 plus 70 weitere Titel aus dem S&P 100**, insgesamt 100 verschiedene Aktien. Dies ist ein eigenes Testuniversum, kein „Dow-100“-Index.

Zusammensetzung mit Stand 28.10.2026 aus den offiziellen vollständigen Bestandsdateien von [State Street DIA](https://www.ssga.com/us/en/individual/etfs/state-street-spdr-dow-jones-industrial-average-etf-trust-dia) und [iShares OEF](https://www.ishares.com/us/products/239723/ishares-sp-100-etf). Zuerst sämtliche 30 DIA-Aktien; dann die 70 noch nicht enthaltenen OEF-Aktien nach absteigendem aktuellem Fondsgewicht (Symbol als Tie-Breaker). GOOG wird als zweite Alphabet-Aktienklasse ausgelassen, da GOOGL bereits im Dow enthalten ist. Berkshire wird auf das Providerformat `BRK.B` abgebildet. Keine Auswahl nach anschließendem Backtesterfolg.

Originaldatei-Prüfsummen, Quellen-URLs, Name, Mitglieder und Auswahlregel werden im Job eingefroren. Originaldownloads, Spezifikation, Logs und Kursdateien bleiben lokale Runtime-/Prüfartefakte. Der lokale Sammelauftrag ist kein GitHub-Upload oder Proxmox-Rollout.

## Abnahme und Grenzen

Credentialfreie Tests prüfen frühe 2016-Historie, explizite Grenzen, gemeinsame Abrufslots unter Konkurrenz, Paginierung mit kurzen Seiten, falsche Kerzen, widersprüchliche Duplikate, wiederholte Tokens, externe Pfade, beschädigte Parquets, ganze fehlende Sitzungen, echten Backup/Restore eines pausierten Jobs, Wiederaufnahme ohne erneuten Monatsdownload, Enginebindung und Veröffentlichung der regulären Intervalle.

Echter Vorabtest: AAPL Januar 2016, SIP/split: 1.482 reguläre 5m-, 133 Stunden-, 38 Vierstunden- und 19 Tageskerzen; keine fehlende erwartete 5m-Kerze. Das prüft die technische Verarbeitung, nicht die Erfolgsquote von Signalen. Der separate Abschlussbericht des 100er-Laufs enthält die tatsächlich erreichten Datenbereiche und Qualitätslücken. Keine erfundenen Daten vor Börsenbeginn eines Titels und keine pauschale Garantie vollständiger Historie für jeden Titel.
