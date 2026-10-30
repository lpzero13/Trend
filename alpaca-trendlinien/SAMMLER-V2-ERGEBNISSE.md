# Sammler V2: gemessene Ergebnisse und Universumsplanung

Abschlussstand **30.10.2026**. [Bedienung und Hermes-Betrieb](SAMMLER-V2.md).

## Gemessener Vergleich

Vorab gewählte Aktien: **AAPL, GS, KO, BNY, SNDK**. Apple deckt hohe Handelsaktivität ab, Goldman Sachs und Coca-Cola weitere große US-Aktien, BNY einen umbenannten Titel und SanDisk eine kürzere verfügbare Historie. Die Auswahl erfolgte nicht nach Handelssignalen oder späteren Kursgewinnen.

Beide Verfahren fragten denselben Zeitraum **01.01.2016 bis 29.10.2026, 15:25:47 UTC**, denselben historischen SIP-Feed und dieselbe Splitbereinigung ab. Getrennte frische Laufverzeichnisse verhinderten Cachetreffer beim Kaltvergleich. Die Methoden liefen nacheinander; sie teilten das kanonische Kontobudget, statt durch mehrere Laufverzeichnisse zusätzliche API-Kapazität vorzutäuschen.

| Verfahren | Gemessene Laufzeit | HTTP-Versuche/Antwortseiten |
|---|---:|---:|
| Bisheriger Sammler, Monatsabrufe | 356.71 s (5:57 min) | 821 |
| Erster V2-Versuch, ein langer Strom je Aktie | 285.10 s (4:45 min) | 567 |
| V2 mit parallel bearbeiteten Jahresfenstern | 237.24 s (3:57 min) | 598 |

Das entspricht **1.50-facher Geschwindigkeit**, **33.5 % weniger Zeit** und **27.2 % weniger Abfragen** gegenüber dem Monatsverfahren. Der finale V2-Lauf benötigte keine HTTP-Wiederholung. Die erste V2-Variante hatte zwar noch weniger Seiten, aber einen langsameren Gesamtabschluss: Unabhängig bearbeitbare Jahresfenster vermeiden einen langen seriellen Nachlauf einer einzelnen Aktie.

| Aktie | Erste verfügbare 5m-Kerze, Datum NY | Reguläre 5m-Kerzen | Seiten bisher | Seiten V2 | Materialprüfung |
|---|---|---:|---:|---:|---|
| AAPL | 2016-01-04 | 211 488 | 260 | 201 | identisch |
| GS | 2016-01-04 | 211 258 | 133 | 121 | identisch |
| KO | 2016-01-04 | 211 262 | 153 | 128 | identisch |
| BNY | 2016-01-04 | 211 199 | 130 | 110 | identisch |
| SNDK | 2025-02-13 | 33 285 | 145 | 38 | identisch |

**Alle fünf unveränderlichen Dataset-IDs beider Verfahren stimmen exakt überein.** Die Identität umfasst sämtliche gespeicherten 5m-/1h-/4h-/Tageswerte und ihren Materialvertrag, nicht nur eine gezeichnete Ansicht.

Zusätzlich hat der unabhängige Offline-Prüfer alle fünf finalen Bestände einschließlich **878,492 regulärer 5m-Kerzen** mit Prüfsummen gelesen, jedes veröffentlichte Stunden-, Vierstunden- und Tagesaggregat aus seinem genauen 5m-Intervall nachgerechnet und den Wochen-Cache verglichen. **Keine Abweichung.** Fehlende Anbieterkerzen bleiben als Lücken erkennbar; es wurden keine Ersatzkurse erfunden.

## Wiederverwendung und Übernahme

- Ein weiterer Auftrag mit denselben fünf vorhandenen Beständen benötigte **33.19 Sekunden** und **0 HTTP-Versuche**, bei 650 wiederverwendeten Monatscheckpoints. Der Provideraufruf war in diesem Test absichtlich gesperrt; ein versehentlicher Neuabruf hätte den Test abgebrochen.
- Eine getrennte, rein lokale Übernahme des bisherigen Fünfer-Auftrags in die neue Metadatenstruktur benötigte **18.06 Sekunden** für 650 Monate und fünf fertige Datasets. Die alte Auftragsstruktur blieb unverändert; es wurden keine Providerzugangsdaten benötigt.
- Diese Tests sind vom normalen lokalen Bestand getrennt. Der ursprüngliche 100er-Auftrag bleibt **pausiert mit 69 fertigen Aktien und 9.074 Monatscheckpoints**. Er wurde nicht zur Fertigstellung dieses Vergleichs fortgesetzt.

## Zeit- und Speicherhochrechnung

**Die folgenden Werte sind Planungswerte für einen vollständigen Erstimport, keine gemessenen großen Universumsläufe.** Sie beziehen sich auf einen Zeitraum wie den Benchmark und das Profil mit acht Downloadarbeitern und 190 Versuchen pro Minute. Ein niedrigeres ausdrücklich konfiguriertes Kontobudget erhöht die Schätzung entsprechend.

Die kürzere SanDisk-Historie wird für den Aufwand einer langen Historie nicht in das Aktienmittel eingerechnet. Grundlage sind die vier langen Bestände AAPL/GS/KO/BNY:

- Mittlere V2-Seitenzahl pro langer Historie: **140**.
- Effektive gemessene Wandzeit pro Antwortseite des vollständigen Fünferlaufs: **237,24 / 598 Sekunden**; darin stecken Download, Warten, Verarbeitung und Veröffentlichung.
- Daraus: **55,54 Sekunden pro langer Aktienhistorie** als lineares Planungsmodell.
- Mittlere veröffentlichte Kursbestände einschließlich Wochen-Cache und Manifest: **4 897 436,5 Bytes pro langer Aktie**.
- Zusätzliche Monatsdateien für Wiederaufnahme: **3 881 993,75 Bytes pro langer Aktie**.

Das Modell skaliert mit Zeitraum und eindeutiger Aktienzahl. Das Band von **0,7 bis 1,4** ist eine ausdrücklich gewählte Planungsreserve, **kein statistisches Konfidenzintervall**. Auf einem anderen Container können CPU, SSD, Netzwerk, API-Latenz, Wiederholungen und andere parallele Arbeit abweichen. Bei Smallcaps können weniger Datenpunkte und mehr Datenlücken auftreten; ein Russell-Bestand wurde nicht vollständig durchgemessen.

Die Liste ist auf den **Quellenstand 28.10.2026** eingefroren. Es sind ETF-Aktienbestände als Index-Abbilder, einschließlich mehrfacher Aktienklassen und mit dokumentierten ausgeschlossenen Sonderpositionen.

| Universum/Abbild | Symbole | Zeitmodell | Planungsband | Kursbestand GiB | Monatsdateien GiB |
|---|---:|---:|---:|---:|---:|
| Dow Jones · DIA-Bestand | 30 | 28 min | 19 min–39 min | 0.14 | 0.11 |
| S&P 100 · OEF-Bestand | 101 | 1 h 33 min | 1 h 05 min–2 h 11 min | 0.46 | 0.37 |
| Nasdaq-100 · CNDX-Bestand | 101 | 1 h 33 min | 1 h 05 min–2 h 11 min | 0.46 | 0.37 |
| S&P 500 · IVV-Bestand | 505 | 7 h 47 min | 5 h 27 min–10 h 54 min | 2.30 | 1.83 |
| Russell 1000 · IWB-Bestand | 1024 | 15 h 48 min | 11 h 04 min–22 h 07 min | 4.67 | 3.70 |
| Russell 2000 · IWM-Bestand | 1963 | 30 h 17 min | 21 h 12 min–42 h 24 min | 8.95 | 7.10 |
| Dow-30 + 70 aus dem S&P 100 | 100 | 1 h 33 min | 1 h 05 min–2 h 10 min | 0.46 | 0.36 |

GiB = 1.073.741.824 Bytes. Hinzu kommen Betriebsdatenbank, Logs, Sicherungen, sonstige vorhandene Bestände und freie Reserve für temporäre Arbeit. Diese Größen sind keine exakten Kapazitätszusagen für beliebige Aktien.

Alle sieben Auswahlen zusammen ergeben **3002 verschiedene Symbole**. Das gleiche Kaltmodell ergäbe dafür ungefähr **46.3 Stunden** und **24.5 GiB** Kurs- und Monatsdateien. Mehrere Universen dürfen deshalb nicht einfach als getrennte Vollimporte addiert werden: Überschneidungen werden dedupliziert, passende vorhandene Monate wiederverwendet.

Ein vollständiger S&P-500-Erstbestand erscheint als erster Nachtlauf sinnvoll planbar. Für die größeren Russell-Abbilder ist eine geordnete Wiederaufnahme über mehrere Nächte vorgesehen. Vorhandene passende Bestände sparen zusätzliche Abrufe; die Tabelle zieht ungeprüfte Bestands-Hinweise ausdrücklich noch nicht ab.

## Abnahme und Betriebsgrenzen

- Vollständige Python-Prüfung: **441 Testfälle, ein bestehender Skip, keine Fehler**.
- Sämtliche **62 JavaScript-Tests**, einschließlich der neuen Sammler-Tests, bestanden.
- HTTP-Tests erhalten Host-/Origin-/Bearer-Grenzen, prüfen Erstellen ohne Preisabruf, Pause, private Dateisperren und begrenzte Detailantworten.
- Echte Browserprüfung: Quellenlisten, deduplizierte Auswahl, Zeit-/Speicherschätzung, sichtbarer pausierter Altbestand und gesperrte Datumsfelder bei dessen Auswahl. Es wurde kein Großuniversum gestartet.
- Betrieb auf Proxmox wurde hier nicht gemessen oder ausgerollt. Daten, Zugangsdaten und lokale Prüfartefakte sind keine GitHub-Artefakte.
- Automatische tägliche Fortschreibung bereits splitbereinigter Archive über neue Vintages hinweg bleibt ein gesonderter Ausbau. Wiederverwendung ist an passende, eingefrorene Datenverträge gebunden.

Die gemessenen Auftrags-/Prüfberichte und Logs liegen lokal unter `artifacts/fast-archive-benchmark-20261029/`; sie enthalten die vollständigen Nachweise. Die Dateien werden nicht mit Marktdaten ins Repository aufgenommen.

## Quellen

[Alpaca-Datenpläne und Kontolimit](https://docs.alpaca.markets/us/docs/about-market-data-api), [Bars/Paginierung und Symbolstand](https://docs.alpaca.markets/us/reference/stockbars), [DIA](https://www.ssga.com/us/en/individual/etfs/state-street-spdr-dow-jones-industrial-average-etf-trust-dia), [OEF](https://www.ishares.com/us/products/239723/ishares-sp-100-etf), [CNDX](https://www.ishares.com/uk/individual/en/products/253741/ishares-nasdaq-100-ucits-etf), [IVV](https://www.ishares.com/us/products/239726/ishares-core-sp-500-etf), [IWB](https://www.ishares.com/us/products/239707/ishares-russell-1000-etf), [IWM](https://www.ishares.com/us/products/239710/ishares-russell-2000-etf).
