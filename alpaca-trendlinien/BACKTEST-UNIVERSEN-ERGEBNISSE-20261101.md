# Entry-/Exit-Backtest auf drei Universen – 01.11.2026

**512 Aktien, 39,440 eingefrorene Signalfälle, 59,847 Wiederholungssignale unterdrückt.**
Dow Jones, Nasdaq-100 und S&P 500 als gespeicherte ETF-Bestände vom 28.10.2026. Ihre Vereinigung enthält 520 Aktienklassen; acht junge Bestände haben in keinem Fenster genügend Vorlauf. Alle Zeitfenster und Regeln wie zuvor.

Entries: 2018, 2021, 2023 und April 2025 bis März 2026. Nachbeobachtung bis 2026-10-29T15:25:00+00:00.
Je Fall 1.000 USD nominal/fraktional; unveränderte Kosten und 5m-Ausführung. Keine Depot-/Slotsperren, Tagesexits oder Take Profits. [Vorabregeln](BACKTEST-UNIVERSEN-PLAN-20261101.md).

**Alle Prozentwerte sind Nettoergebnisse einzelner Signalfälle, keine Depot- oder Indexrenditen.** Gewinner/Verlierer zählen nur geschlossene Pfade. Offene Buchwerte und unbekannte Datenlücken bleiben getrennt. Universen und Familien überlappen; ihre Zahlen nicht addieren.

## Qualifizierte Signale: fünf Exitvarianten

| Einstieg | Exit | Signale | Gefüllt | Geschlossen | Gewinner | Verlierer | Offen | Lücke | Treffer % geschlossen | Ø geschlossen % | Median geschlossen % | Ø geschlossen + offen % |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ausbruch | Fest | 6883 | 6226 | 4871 | 0 | 4871 | 414 | 941 | 0.00 | -4.15 | -3.38 | 7.61 |
| Ausbruch | Ursprüngliche Safety | 6883 | 6226 | 5685 | 1337 | 4348 | 60 | 481 | 23.52 | -0.68 | -1.63 | 2.45 |
| Ausbruch | Aktuelle Safety | 6883 | 6226 | 6028 | 2171 | 3857 | 0 | 198 | 36.02 | 0.14 | -0.94 | 0.14 |
| Ausbruch | Nur qualifizierte neue Safety | 6883 | 6226 | 5933 | 1871 | 4062 | 0 | 293 | 31.54 | 0.30 | -1.28 | 0.30 |
| Ausbruch | Neue Safety erst ab +2R | 6883 | 6226 | 5889 | 1686 | 4203 | 3 | 334 | 28.63 | 0.40 | -1.48 | 0.43 |
| Roter Retest | Fest | 4362 | 4022 | 3186 | 0 | 3186 | 262 | 574 | 0.00 | -3.84 | -3.00 | 7.28 |
| Roter Retest | Ursprüngliche Safety | 4362 | 4022 | 3701 | 883 | 2818 | 35 | 286 | 23.86 | -0.47 | -1.43 | 1.50 |
| Roter Retest | Aktuelle Safety | 4362 | 4022 | 3918 | 1323 | 2595 | 0 | 104 | 33.77 | 0.06 | -0.85 | 0.06 |
| Roter Retest | Nur qualifizierte neue Safety | 4362 | 4022 | 3850 | 1204 | 2646 | 0 | 172 | 31.27 | 0.33 | -1.15 | 0.33 |
| Roter Retest | Neue Safety erst ab +2R | 4362 | 4022 | 3818 | 1078 | 2740 | 1 | 203 | 28.23 | 0.44 | -1.33 | 0.43 |
| Safety-Bounce | Fest | 6099 | 5971 | 5276 | 0 | 5276 | 171 | 524 | 0.00 | -2.22 | -1.84 | 2.04 |
| Safety-Bounce | Ursprüngliche Safety | 6099 | 5971 | 5725 | 1165 | 4560 | 17 | 229 | 20.35 | -0.45 | -1.06 | -0.02 |
| Safety-Bounce | Aktuelle Safety | 6099 | 5971 | 5832 | 1507 | 4325 | 0 | 139 | 25.84 | -0.08 | -0.98 | -0.08 |
| Safety-Bounce | Nur qualifizierte neue Safety | 6099 | 5971 | 5799 | 1334 | 4465 | 0 | 172 | 23.00 | -0.10 | -1.02 | -0.10 |
| Safety-Bounce | Neue Safety erst ab +2R | 6099 | 5971 | 5809 | 1364 | 4445 | 0 | 162 | 23.48 | -0.08 | -1.03 | -0.08 |

Fester Stop kann Gewinne nicht regulär schließen. Daher ist seine geschlossene Trefferquote kein fairer alleiniger Vergleich mit nachgezogenen Stops. Nullfälle sind in den CSVs separat enthalten.

## Universen: aktuelle Safety, qualifizierte Entries

| Universum | Lokale Titel | Geeignet | Einstieg | Signale | Geschlossen | Gewinner | Verlierer | Offen | Lücke | Ø geschlossen % | Ø inkl. offener Buchwerte % |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Dow Jones · DIA-Bestand | 30 | 30 | Ausbruch | 511 | 458 | 168 | 290 | 0 | 16 | 0.35 | 0.35 |
| Dow Jones · DIA-Bestand | 30 | 30 | Roter Retest | 344 | 314 | 109 | 205 | 0 | 5 | 0.28 | 0.28 |
| Dow Jones · DIA-Bestand | 30 | 30 | Safety-Bounce | 478 | 463 | 136 | 327 | 0 | 4 | 0.19 | 0.19 |
| Nasdaq-100 · CNDX-Bestand | 101 | 97 | Ausbruch | 1334 | 1240 | 469 | 771 | 0 | 11 | 0.49 | 0.49 |
| Nasdaq-100 · CNDX-Bestand | 101 | 97 | Roter Retest | 871 | 827 | 283 | 544 | 0 | 2 | 0.26 | 0.26 |
| Nasdaq-100 · CNDX-Bestand | 101 | 97 | Safety-Bounce | 1245 | 1201 | 337 | 864 | 0 | 14 | 0.13 | 0.13 |
| S&P 500 · IVV-Bestand | 505 | 499 | Ausbruch | 6789 | 5945 | 2144 | 3801 | 0 | 197 | 0.13 | 0.13 |
| S&P 500 · IVV-Bestand | 505 | 499 | Roter Retest | 4301 | 3862 | 1304 | 2558 | 0 | 104 | 0.07 | 0.07 |
| S&P 500 · IVV-Bestand | 505 | 499 | Safety-Bounce | 6020 | 5758 | 1486 | 4272 | 0 | 137 | -0.09 | -0.09 |

## Identische bewertbare Fälle aller vier nachgezogenen Safetys

Hier müssen alle vier Varianten geschlossen oder offen sein. Keine Auswahl nach Vorzeichen; Datenlückenzensierung kann diese gemeinsame Teilmenge dennoch verzerren.

| Einstieg / Klasse | Exit | Gemeinsam bewertbar | Ø Bewertung % | Median Bewertung % | Ø ohne beste drei % |
|---|---|---:|---:|---:|---:|
| Ausbruch / qualified | Aktuelle Safety | 5743 | -0.02 | -1.02 | -0.08 |
| Ausbruch / qualified | Ursprüngliche Safety | 5743 | 2.45 | -1.60 | 1.31 |
| Ausbruch / qualified | Nur qualifizierte neue Safety | 5743 | 0.07 | -1.34 | -0.03 |
| Ausbruch / qualified | Neue Safety erst ab +2R | 5743 | 0.12 | -1.54 | 0.03 |
| Ausbruch / three_young | Aktuelle Safety | 7 | -1.75 | -2.05 | -3.48 |
| Ausbruch / three_young | Ursprüngliche Safety | 7 | -3.15 | -2.25 | -5.11 |
| Ausbruch / three_young | Nur qualifizierte neue Safety | 7 | -1.82 | -2.05 | -3.48 |
| Ausbruch / three_young | Neue Safety erst ab +2R | 7 | -3.15 | -2.25 | -5.11 |
| Ausbruch / two | Aktuelle Safety | 10957 | -0.03 | -1.04 | -0.10 |
| Ausbruch / two | Ursprüngliche Safety | 10957 | 1.72 | -1.49 | 1.20 |
| Ausbruch / two | Nur qualifizierte neue Safety | 10957 | -0.03 | -1.27 | -0.09 |
| Ausbruch / two | Neue Safety erst ab +2R | 10957 | 0.10 | -1.43 | 0.05 |
| Roter Retest / qualified | Aktuelle Safety | 3733 | -0.06 | -0.92 | -0.13 |
| Roter Retest / qualified | Ursprüngliche Safety | 3733 | 1.50 | -1.42 | 0.74 |
| Roter Retest / qualified | Nur qualifizierte neue Safety | 3733 | 0.13 | -1.19 | -0.00 |
| Roter Retest / qualified | Neue Safety erst ab +2R | 3733 | 0.15 | -1.38 | 0.02 |
| Roter Retest / three_young | Aktuelle Safety | 1 | -1.87 | -1.87 | — |
| Roter Retest / three_young | Ursprüngliche Safety | 1 | -1.87 | -1.87 | — |
| Roter Retest / three_young | Nur qualifizierte neue Safety | 1 | -1.87 | -1.87 | — |
| Roter Retest / three_young | Neue Safety erst ab +2R | 1 | -1.87 | -1.87 | — |
| Roter Retest / two | Aktuelle Safety | 6775 | 0.03 | -0.91 | -0.09 |
| Roter Retest / two | Ursprüngliche Safety | 6775 | 2.16 | -1.31 | 1.13 |
| Roter Retest / two | Nur qualifizierte neue Safety | 6775 | 0.13 | -1.10 | -0.04 |
| Roter Retest / two | Neue Safety erst ab +2R | 6775 | 0.19 | -1.26 | 0.08 |
| Safety-Bounce / qualified | Aktuelle Safety | 5737 | -0.17 | -1.00 | -0.20 |
| Safety-Bounce / qualified | Ursprüngliche Safety | 5737 | -0.02 | -1.06 | -0.26 |
| Safety-Bounce / qualified | Nur qualifizierte neue Safety | 5737 | -0.19 | -1.03 | -0.22 |
| Safety-Bounce / qualified | Neue Safety erst ab +2R | 5737 | -0.17 | -1.04 | -0.21 |

## Aktien: aktuelle Safety, qualifizierte Entries

Alle drei Familien je Aktie zusammen, einschließlich ihrer Abhängigkeiten. Sortiert nach mittlerem geschlossenem Nettoergebnis; Stichprobengröße ausdrücklich gezeigt. Nachträgliche Beschreibung, keine Gewinnerauswahl als Handelsregel.

| Aktie | Universen | Geschlossen | Gewinner | Verlierer | Offen | Lücke | Ø geschlossen % | Median geschlossen % |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| ASML | nasdaq100 | 9 | 5 | 4 | 0 | 0 | 19.27 | 1.37 |
| CVNA | sp500 | 17 | 9 | 8 | 0 | 0 | 15.91 | 1.45 |
| PLTR | nasdaq100, sp500 | 17 | 10 | 7 | 0 | 0 | 6.88 | 0.93 |
| JBHT | sp500 | 7 | 3 | 4 | 0 | 2 | 4.83 | -2.23 |
| DDOG | nasdaq100, sp500 | 42 | 24 | 18 | 0 | 0 | 4.55 | 1.09 |
| TKO | sp500 | 8 | 6 | 2 | 0 | 0 | 4.42 | 5.92 |
| COIN | sp500 | 28 | 9 | 19 | 0 | 0 | 4.09 | -2.70 |
| XYZ | sp500 | 26 | 12 | 14 | 0 | 0 | 3.97 | -0.15 |
| BE | sp500 | 28 | 11 | 17 | 0 | 2 | 3.95 | -1.35 |
| BR | sp500 | 4 | 3 | 1 | 0 | 0 | 3.89 | 5.21 |
| VLTO | sp500 | 1 | 0 | 1 | 0 | 0 | -3.27 | -3.27 |
| PKG | sp500 | 1 | 0 | 1 | 0 | 1 | -3.36 | -3.36 |
| SMCI | sp500 | 21 | 3 | 18 | 0 | 0 | -3.40 | -4.36 |
| ALAB | nasdaq100 | 13 | 3 | 10 | 0 | 0 | -3.44 | -2.84 |
| PODD | sp500 | 3 | 0 | 3 | 0 | 0 | -3.49 | -2.16 |
| COO | sp500 | 14 | 1 | 13 | 0 | 0 | -3.57 | -1.31 |
| CRL | sp500 | 1 | 0 | 1 | 0 | 0 | -3.59 | -3.59 |
| SOLV | sp500 | 1 | 0 | 1 | 0 | 0 | -3.67 | -3.67 |
| MPWR | nasdaq100, sp500 | 4 | 0 | 4 | 0 | 0 | -3.73 | -3.42 |
| ECHO | sp500 | 5 | 0 | 5 | 0 | 0 | -4.71 | -3.71 |

## Größte geschlossene Gewinner

Referenz wie oben: qualifizierte Entries und aktuelle Safety, keine Auswahl des besten Exitmodells je Trade.

| Aktie | Entrytyp | Entry UTC | Exit UTC | Netto % | Netto R |
|---|---|---|---|---:|---:|
| CVNA | Roter Retest | 2023-06-01T13:30:00+00:00 | 2023-08-18T13:30:00+00:00 | 166.19 | 9.49 |
| ASML | Ausbruch | 2025-08-06T17:35:00+00:00 | 2026-06-23T13:30:00+00:00 | 156.76 | 147.49 |
| PLTR | Ausbruch | 2023-05-08T17:35:00+00:00 | 2023-07-06T13:35:00+00:00 | 93.78 | 12.29 |
| RKLB | Safety-Bounce | 2025-06-18T13:30:00+00:00 | 2025-09-02T13:30:00+00:00 | 76.78 | 24.18 |
| MU | Roter Retest | 2025-09-02T17:35:00+00:00 | 2025-10-22T14:25:00+00:00 | 69.80 | 24.05 |
| BE | Roter Retest | 2025-12-29T18:35:00+00:00 | 2026-03-23T19:55:00+00:00 | 60.92 | 1.32 |
| APP | Safety-Bounce | 2023-06-22T17:35:00+00:00 | 2023-10-16T13:45:00+00:00 | 60.49 | 14.55 |
| AMZN | Ausbruch | 2018-01-02T18:35:00+00:00 | 2018-10-05T15:55:00+00:00 | 57.99 | 4.45 |
| CVNA | Safety-Bounce | 2023-06-27T17:35:00+00:00 | 2023-08-18T13:30:00+00:00 | 57.93 | 4.51 |
| AMZN | Roter Retest | 2018-01-03T14:30:00+00:00 | 2018-10-05T15:55:00+00:00 | 57.77 | 4.41 |

## Größte geschlossene Verlierer

Referenz wie oben: qualifizierte Entries und aktuelle Safety, keine Auswahl des besten Exitmodells je Trade.

| Aktie | Entrytyp | Entry UTC | Exit UTC | Netto % | Netto R |
|---|---|---|---|---:|---:|
| TSLA | Ausbruch | 2021-01-25T18:35:00+00:00 | 2021-03-05T16:15:00+00:00 | -35.60 | -0.84 |
| FTNT | Roter Retest | 2023-10-31T17:35:00+00:00 | 2023-11-03T13:30:00+00:00 | -22.13 | -7.37 |
| FTNT | Ausbruch | 2023-10-31T13:30:00+00:00 | 2023-11-03T13:30:00+00:00 | -21.34 | -10.41 |
| GNRC | Ausbruch | 2023-07-27T13:30:00+00:00 | 2023-08-02T13:30:00+00:00 | -19.56 | -3.13 |
| GNRC | Roter Retest | 2023-07-31T17:35:00+00:00 | 2023-08-02T13:30:00+00:00 | -18.95 | -4.51 |
| CAH | Safety-Bounce | 2018-05-02T17:35:00+00:00 | 2018-05-03T13:30:00+00:00 | -17.79 | -4.25 |
| TWLO | Roter Retest | 2023-05-09T17:35:00+00:00 | 2023-05-10T13:30:00+00:00 | -17.69 | -1.67 |
| MU | Roter Retest | 2026-03-16T13:30:00+00:00 | 2026-03-26T13:35:00+00:00 | -17.62 | -1.00 |
| LULU | Ausbruch | 2025-06-03T13:30:00+00:00 | 2025-06-06T13:30:00+00:00 | -17.59 | -3.89 |
| ALAB | Ausbruch | 2026-02-06T18:35:00+00:00 | 2026-02-12T15:40:00+00:00 | -17.57 | -0.95 |

## Dateien, Kontrolle und Grenzen

Privater Studienordner: `artifacts/exit-followup-population-20261101`. Plan-ID `314b4283b2c46aa59a4c96b78ce4c5fa2df2eadea188b07baf4d61b7134ce696`. 68 unveränderte Kontrollaktien, 444 neu berechnete Aktien. CSV-Abgleich aller 197,200 Modellzeilen und Universumszähler bestanden.
Sortierbare Dateien: `trades-by-universe.csv` (jede Fall-/Modellkombination einmal, mit Entry/Exit/Stop/Prozenten/R), `universe-summary.csv`, `stock-summary.csv`, `window-summary.csv`, `largest-winners.csv`, `largest-losers.csv`. `stock-overview.csv` bietet eine Zeile je Titel für qualifizierte Entries mit aktueller Safety; `stock-summary.csv` trennt zusätzlich Familien/Kontaktklassen/Modelle. `coverage.csv` enthält alle 520 Titel einschließlich Ausschlüssen und geeigneten Aktien ohne Signal. Alle Kontaktklassen und Modelle bleiben in den Detaildateien enthalten, auch ohne Gewinn oder Fill.
Bekannte heutige Überlebendenbestände, bereits untersuchte Zeiträume und abhängige Episoden: keine unabhängige Strategiebestätigung. Dividenden, Steuern, FX und historische Kapitalmaßnahmen sind nicht vollständig als handelbares Ganzaktienportfolio abgebildet. Unbekannte Datenlücken können selektiv sein; offene Buchwerte sind keine realisierten Gewinne. Keine neue Providerabfrage, Order, Meldung, Webänderung oder Containerinstallation.
