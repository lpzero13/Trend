# Wochenansicht und Speicherplanung für Offline-Universen

Stand: 28.10.2026. Speicherzahlen sind lokal gemessene Größen beziehungsweise ausdrücklich gekennzeichnete Hochrechnungen; keine Migration des laufenden Datenbestands.

## Wochenansicht umgesetzt

Chart und Zufallsmodus bieten **1h, 4h, 1D und 1W**. Monatskerzen wurden nicht ergänzt. 1W wird aus den bereits abgerufenen beziehungsweise lokal gespeicherten Tageskursen berechnet und benötigt keinen eigenen zusätzlichen Kursabruf. Alpaca unterstützt auch native Wochenabfragen; die Anwendung verwendet bewusst dieselben Tagesquellen und den vorhandenen Börsenkalender.

Eine Wochenkerze wird erst nach dem letzten tatsächlichen regulären XNYS-Handelsschluss ihrer Woche gezeigt. Karfreitag, verkürzte Handelstage, Sommerzeit und Jahreswechsel werden berücksichtigt. Alle erwarteten Tageskerzen müssen vorhanden und abgeschlossen sein; fehlende Tage werden nicht erfunden, unvollständige Wochen werden weggelassen. Für die Wochenansicht müssen mindestens drei vollständige Wochen verfügbar sein. Bei kürzerem Bestand bleiben die bisherigen Intervalle nutzbar.

Auch im Zufallsmodus kommen keine späteren Tageshochs oder Wochenschlusskurse in den bekannten Chart. Vor-/Zurückschritte unterstützen Wochen. Rückwärts verwendet die Bedienung den Schluss der aktuell sichtbaren Kerze, damit ein Klick tatsächlich diese Kerze zurücknimmt. Zeichnungen, Messungen und deren Speicherung sind auch für 1W freigegeben. Bei alten fixierten Ständen ohne Wochenansicht wird ein Wechsel verständlich abgefangen; alte Archive werden nicht verändert. Neue Wochenlinien sind Chartkontext, keine neue headless Forschungsstrategie oder automatischen Entryregeln. Bestehende gespeicherte Datasets, Kalender-/Engineversionen und Forschungszeitpläne bleiben unangetastet.

## Welche Wertpapiere sind vorhanden?

Der aktuelle Abruf unseres gefilterten Alpaca-Verzeichnisses ergibt **13.227 aktive gelistete US-Wertpapiere**, davon 13.189 als handelbar markiert. Der Katalog enthält Aktien, ETFs und weitere als `us_equity` eingeordnete Instrumente; die Zahl ist keine Zählung ausschließlich gewöhnlicher Unternehmensaktien. Ein Verzeichniseintrag garantiert keine lückenlose historische Datenabdeckung. Kein europäisches Xetra-Universum.

Verteilung im Auswahlverzeichnis: NASDAQ 5.617, NYSE 2.894, ARCA 2.747, BATS 1.677, AMEX 292. Die aktuelle alphabetisch durchsuchbare Auswahl findet sich weiterhin über das Symbolfeld der Hauptchart. Die vollständige Katalogantwort bleibt als Laufzeitdatei lokal, ohne Credentials.

**Lokal gespeicherte Aktien: 60.** Diese sind jetzt grundsätzlich für die offline Auswahl und für gespeicherte Zufallsfälle vorhanden; jeweilige Datenlücken und ausreichende Historie sind weiterhin zu prüfen:

```text
AAPL ABBV ABT ADBE AMAT AMD AMZN AVGO AXP BA
BAC C CAT COST CRM CSCO CVX DE DIS GE
GOOGL GS HD HON IBM INTC INTU JNJ JPM KO
LLY LMT LOW MA MCD META MRK MS MSFT MU
NFLX NKE NOW NVDA ORCL PEP PFE PG QCOM RTX
SBUX SCHW TGT TXN UNH UPS V WFC WMT XOM
```

## Gemessener Speichertest

Nicht destruktiver Versuch mit **AAPL, JPM, XOM**, Historie Juli 2020 bis Oktober 2026. Je Aktie rund 122.000 vorhandene reguläre 5m-Kerzen, dazu 1h/4h/1D-Aggregate. Kein Datenabruf für den Benchmark, keine Rundung von Preisen, keine Änderung an Forschungsdaten. Python-Standardbibliothek SQLite; `WITHOUT ROWID` mit `(series_id, at)` als Schlüssel, OHLCV als REAL, Zeitstempel als INTEGER. Zeilenzahlen und zehn verteilte Originalzeilen je Serie wurden nach dem Schreiben exakt abgeglichen.

| Ablage für die drei Testaktien | Größe, dezimale MB | Inhalt |
|---|---:|---|
| Bestehende unveränderliche JSON-Datasets | 51,74 | 5m, 1h, 4h, 1D und Metadaten |
| SQLite mit allen vier Intervallen | 23,16 | Gleiche vorhandene Kerzen aller vier Intervalle, Serienmetadaten |
| SQLite nur mit 5m-Basis | 20,43 | Nur originale 5m-Kerzen; höhere Intervalle können abgeleitet werden |

Der inhaltlich gleiche Vier-Intervall-Vergleich spart damit rund **55 %** Platz. Die 5m-Basis benötigt im Test durchschnittlich **6,81 MB pro Aktie** für gut sechs Jahre. Ein SQLite-Seiten-/Indexlayout ist keine zugesagte Parquet-Kompressionsrate. Die drei langen, liquiden Titel sind eine Größenprobe, keine Messung des gesamten Katalogs. Neuere Listings haben weniger Historie, andere Titel/Feeds und längere Zeiträume ändern die Größe.

## Hochrechnung bei derselben Historiendauer und 5m-Dichte

Nur eine 5m-Serie je Aktie, abgeleitete Intervalle nicht zusätzlich dauerhaft gehalten. Dezimale GB, ohne Backups, Rohdownloadcache, Versionen, Ereignis-/Forschungsjournale oder zusätzliche Feeds:

| Eindeutige Aktien | Ungefähre reine Kursdaten |
|---:|---:|
| 60 | 0,41 GB |
| 100 | 0,68 GB |
| 500 | 3,41 GB |
| 1.000 | 6,81 GB |
| 5.000 | 34,05 GB |
| 13.227 | 90,08 GB |

Planungswert für den vollständigen heutigen Katalog einschließlich Arbeitsreserve und zwei bis drei Datenkopien eher **200–300 GB**. Das ist eine Kapazitätsplanung, kein Beleg, dass alle Titel sechs Jahre lückenlose Kurse liefern oder gleichzeitig importiert werden können. Zehn Jahre bei gleicher Kerzendichte wären entsprechend größer. Ein reiner Tageskursbestand ist sehr viel kleiner; für unsere Ausführungs-/Stoppprüfung bleibt die feinere Basis wichtig.

Aktuell liegen **487 Datasetdateien mit zusammen 4,64 GB** vor. Darin stecken unterschiedliche Feeds, Bereinigungen und Generationen derselben 60 Aktien. Diese Unterschiede dürfen nicht pauschal als entbehrliche Duplikate gelöscht werden. Hinzu kommen der separate Provider-Rohcache und sonstige Laufzeitdaten. Der Unterschied zur 0,41-GB-Hochrechnung bedeutet deshalb nicht, dass wir bestehende Forschung ohne Datenverlust auf diese Größe zusammenschrumpfen können.

## Empfohlener nächster Ausbauschritt – noch nicht migriert

1. Ein gemeinsamer versionierter Kursbestand statt einer vollständigen neuen Datei bei jeder Aktualisierung. Identität mindestens aus Provider, Feed, Aktie, Bereinigung, Normalisierung/Kalender und Intervall; Preise nicht auf Anzeige-Cents runden.
2. Originale reguläre 5m-Kerzen einmal speichern, 1h/4h/1D/1W konsistent daraus ableiten oder als wiederherstellbaren Cache halten. Keine Monatsdaten erforderlich. Native Altbestände nicht still als normalisierte Feindaten umetikettieren.
3. Universen als eigene Mitgliedslisten mit Datum speichern. Wenn eine Aktie in drei Universen vorkommt, referenzieren diese dieselben Kursserien. Es zählt die Vereinigungsmenge der Aktien, nicht die Summe aller Listenlängen.
4. Datenrevisionen und Kapitalmaßnahmen versionieren. Studien bleiben an ihren ursprünglichen Manifest-/Chunkprüfsummen gebunden. Neue Imports dürfen alte bekannte Kurse und Ergebnisse nicht überschreiben.
5. Importfortschritt, Datenabdeckung und Lücken je Aktie dokumentieren. Nach vollständigem Import arbeiten Backtests ausschließlich mit lokalen Daten. Historische Universumsmitgliedschaften und ausgeschiedene Titel berücksichtigen, damit heutige Gewinnerlisten keinen unbemerkten Survivorship-Bias erzeugen.
6. Erst ein überschaubares Universum technisch abnehmen, dann größere oder weitere Listen importieren. Bestehende Backups und Referenzschutz erhalten, Restore testen; kein automatisches Löschen referenzierter Originaldaten.

Die derzeitigen Vollsnapshots und das Importbudget bestehender Beobachter sind nicht durch den Benchmark ersetzt worden. Auch kein großes Aktienuniversum wurde ungefragt importiert.

## Technische Abnahme

340 Python-Tests unter 3.12 und 3.13 bestanden (je ein bestehender Skip), 48 JavaScript-Tests bestanden. Neue Gegenbeispiele prüfen OHLCV, fehlende Tage, Karfreitag, Thanksgiving, Sommerzeit, Jahreswechsel und spätere Kursschocks. Wochenansicht und Wochenschritte sind zusätzlich mit einem echten lokalen SIP-Dataset über HTTP und im Browser geprüft. Im Browser zeigte der Mittwoch-Zufallsstart nur die zuvor abgeschlossene Woche; ein Rückschritt entfernte genau eine sichtbare Wochenkerze, und die Rückkehr zum Start stellte den Originalzeitpunkt wieder her. Keine Änderung alter Forschungs-Enginebindungen oder Datenbankmigration.

Quellen: lokaler Alpaca-Verzeichnisabruf vom 28.10.2026, lokale Dataset-Inventur, reproduzierbarer Messlauf `tools/storage_benchmark.py`. Anbieterinformationen: [Market Data API / Basic](https://docs.alpaca.markets/us/docs/about-market-data-api), [Feed-/SIP-Grenzen](https://docs.alpaca.markets/us/docs/market-data-faq), [Historische Bar-Intervalle](https://docs.alpaca.markets/us/reference/stockbars).
