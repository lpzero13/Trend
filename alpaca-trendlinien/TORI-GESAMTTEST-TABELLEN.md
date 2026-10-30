# Gesamttest der Tori-Kriterien – 60 Aktien und längere Historie

Stand 22.10.2026. Isolierte lokale Forschung; Chart, bestehende Profile und laufender Beobachter unverändert. Keine Orders und kein Container-Rollout.

**Ergebnisstatus: mit wesentlichen Einschränkungen interpretierbar; keine validierte Handelsstrategie.** Die kursbasierten Regeln sind ausführbar und der erweiterte Durchlauf ist abgeschlossen. Vollständige Kriterienkonformität bleibt wegen fehlender historischer Ereignisabdeckung ungeklärt. Menschliche Linienbewertungen stehen ebenfalls aus.

## Datenbasis und tatsächliche Abdeckung

Vorab festgelegte Aktien: 60; importiert: 57; vollständig zurückgewiesene Imports: 3. Verfügbare Anfangsdaten: 2020-07-27 bis 2020-07-27; Ende 21.10.2026. Zehn Jahre angefordert, IEX liefert in diesen Imports erst ab 2020. Nach einem Jahr Vorlauf jede Quellkerze verarbeitet, ohne kurze Suchfenster- oder Linienlebensdauergrenze.

Gespeicherte reguläre 5m-Kerzen: 6,731,311. 4h-Kerzen: 129,220; Tageskerzen: 57,975. Median der tatsächlichen Abdeckung: 5m 98.48 %, 4h 78.94 %, 1D 72.45 %. Eine einzige fehlende 5m-Kerze kann ein Aggregat entwerten. Fehlende Kurse wurden weder ergänzt noch als Seitwärtskerzen erfunden.

Fehlende IEX-Kerzen sind nicht automatisch defekte Downloads: Ohne geeignete Trades wird laut [Alpacas Market Data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq) keine Bar erzeugt. Unser vollständiges 5m-Raster ist eine konservative Forschungsannahme; es kann deshalb viele Aggregate und lange Haltedauern ausschließen. Die vorhandenen OHLC-Daten unterscheiden fehlende Handelsaktivität auf IEX, Datenlieferlücken und die Ausführbarkeit am Gesamtmarkt nicht zuverlässig. Nicht durch erfundene konstante Kerzen beheben.

Die heutigen 60 überwiegend liquiden US-Unternehmen sind kein historisch vollständiges Aktienuniversum. Delistings, Europa und Dividendenrenditen fehlen. Splitbereinigung nach heutigem Anpassungsstand und IEX als einzelner Handelsplatz bleiben Modellgrenzen; die normalisierten historischen Preise sind keine damaligen unbereinigten Brokerpreise. Frühere bekannte Zeiträume sind kein neuer unberührter Holdout.

| Aktie | 5m vollständig % | 4h vollständig % | 1D vollständig % |
|---|---:|---:|---:|
| AAPL | 99.88 | 99.81 | 99.74 |
| ABBV | 98.10 | 71.86 | 60.46 |
| ABT | 98.48 | 76.15 | 64.03 |
| ADBE | 95.59 | 51.76 | 39.09 |
| AMAT | 99.08 | 84.22 | 75.64 |
| AMD | 99.85 | 99.26 | 98.72 |
| AMZN | 97.80 | 78.91 | 75.70 |
| AVGO | 93.55 | 50.42 | 43.56 |
| AXP | 95.26 | 48.40 | 34.44 |
| BA | 98.00 | 72.92 | 61.80 |
| BAC | 99.59 | 99.39 | 99.30 |
| C | 99.49 | 96.70 | 94.64 |
| CAT | 94.03 | 40.52 | 27.04 |
| COST | 85.63 | 22.02 | 13.39 |
| CRM | Import zurückgewiesen | — | — |
| CSCO | 99.86 | 99.30 | 98.79 |
| CVX | 99.11 | 87.80 | 80.68 |
| DE | 89.06 | 24.71 | 13.71 |
| DIS | 99.34 | 92.22 | 87.50 |
| GE | 98.38 | 78.94 | 70.92 |
| GOOGL | 95.18 | 71.67 | 69.20 |
| GS | 89.79 | 28.49 | 16.96 |
| HD | 96.64 | 57.59 | 44.90 |
| HON | 94.34 | 40.52 | 25.19 |
| IBM | 96.95 | 60.76 | 46.81 |
| INTC | 99.87 | 99.71 | 99.55 |
| INTU | 88.95 | 28.49 | 20.34 |
| JNJ | 98.93 | 82.04 | 72.45 |
| JPM | 99.04 | 85.12 | 77.30 |
| KO | Import zurückgewiesen | — | — |
| LLY | 94.63 | 46.99 | 34.89 |
| LMT | 82.16 | 14.21 | 7.78 |
| LOW | Import zurückgewiesen | — | — |
| MA | 95.63 | 53.78 | 41.26 |
| MCD | 95.03 | 46.64 | 34.44 |
| META | 99.67 | 94.65 | 91.90 |
| MRK | 99.30 | 91.17 | 85.46 |
| MS | 99.03 | 84.92 | 76.40 |
| MSFT | 99.82 | 98.05 | 96.43 |
| MU | 99.82 | 98.05 | 96.56 |
| NFLX | 95.36 | 57.62 | 47.58 |
| NKE | 99.31 | 91.04 | 85.08 |
| NOW | 85.35 | 28.14 | 21.11 |
| NVDA | 99.71 | 95.87 | 93.49 |
| ORCL | 99.25 | 91.04 | 86.61 |
| PEP | 97.85 | 67.89 | 55.55 |
| PFE | 99.61 | 99.04 | 98.60 |
| PG | 98.68 | 81.59 | 73.34 |
| QCOM | 99.40 | 88.22 | 81.31 |
| RTX | 98.04 | 71.41 | 58.16 |
| SBUX | 99.32 | 86.11 | 78.44 |
| SCHW | 99.38 | 91.77 | 86.16 |
| TGT | 97.72 | 67.45 | 53.83 |
| TXN | 98.37 | 70.39 | 56.38 |
| UNH | 96.99 | 61.65 | 48.28 |
| UPS | 96.78 | 58.23 | 42.41 |
| V | 99.02 | 84.60 | 75.77 |
| WFC | 99.60 | 98.75 | 98.02 |
| WMT | 99.14 | 89.40 | 83.48 |
| XOM | 99.57 | 97.98 | 96.81 |

## Schritt 1: Drei Kontakte und Geometrie

Außenlinie und Kontaktbereich sind getrennt: in der strengen Geometrie keine Dochtverletzung, dennoch nahe Kontakte auf der erlaubten Seite. Zwei benachbarte Kerzen ergeben keinen zusätzlichen Abpraller. Mehrere bestätigte Pivotpaare bleiben bis zur Signalauswahl erhalten; Ranking ohne spätere Renditen. Kontaktband bei Entstehung fixiert.

| Geometrie / Intervall | Kandidaten | Kandidaten mit ≥3 Reaktionen | 2-Kontakt-Fälle | davon ≥3 nahe Aktionskontakte | davon ≥3 exakt kollineare Kontakte |
|---|---:|---:|---:|---:|---:|
| strict / 4h | 13132 | 2813 | 1225 | 359 | 1 |
| strict / 1D | 5650 | 1285 | 462 | 150 | 0 |
| zone / 4h | 16367 | 5581 | 1728 | 712 | 3 |
| zone / 1D | 7108 | 2570 | 695 | 319 | 1 |

Kandidaten und Profil-/Familienfälle sind keine unabhängigen Trades. Die lockere Zone erlaubt Dochtüberschreitungen und erfüllt damit nicht die strenge Zeichenregel. Exakte Kontaktzahlen sind hier eine Geometriediagnose, keine neue Handelsregel.

## Schritte 2–4: Kontakte, Alter, Momentum, Safety, Kontext

Alle Gruppen wurden vorab festgelegt. Hauptfolge ist verschachtelt; 14 Tage, drei grüne Kontakte, ganzer Körper und exakte Kontakte sind zusätzliche Sensitivitäten auf Basis der kursbasierten Kontextgruppe. Kein nachträglicher Wechsel zur günstigsten Einstellung.

| Intervall / Prüfstand | Profil-/Familienfälle | eindeutige Aktie/Entryzeiten | Aktien | Signale je Kalender-Aktienjahr |
|---|---:|---:|---:|---:|
| 4h / 2 Kontakte | 1225 | 1200 | 47 | 4.023 |
| 4h / 3 Aktionskontakte | 359 | 356 | 42 | 1.194 |
| 4h / + Alter 7 Tage | 310 | 308 | 41 | 1.033 |
| 4h / + Schwung / Zwischenhoch | 206 | 204 | 35 | 0.684 |
| 4h / + nahe Safety | 20 | 20 | 16 | 0.067 |
| 4h / + Kontext und Raum | 1 | 1 | 1 | 0.003 |
| 4h / + Ereigniskalender | 0 | 0 | 0 | 0.000 |
| 4h / Sensitivität: 14 Tage | 1 | 1 | 1 | 0.003 |
| 4h / Sensitivität: auch Grün 3 | 0 | 0 | 0 | 0.000 |
| 4h / Sensitivität: ganzer Körper | 0 | 0 | 0 | 0.000 |
| 4h / Sensitivität: exakt 3 | 0 | 0 | 0 | 0.000 |
| 1D / 2 Kontakte | 462 | 450 | 35 | 1.511 |
| 1D / 3 Aktionskontakte | 151 | 150 | 34 | 0.504 |
| 1D / + Alter 7 Tage | 151 | 150 | 34 | 0.504 |
| 1D / + Schwung / Zwischenhoch | 106 | 106 | 32 | 0.356 |
| 1D / + nahe Safety | 17 | 17 | 15 | 0.057 |
| 1D / + Kontext und Raum | 0 | 0 | 0 | 0.000 |
| 1D / + Ereigniskalender | 0 | 0 | 0 | 0.000 |
| 1D / Sensitivität: 14 Tage | 0 | 0 | 0 | 0.000 |
| 1D / Sensitivität: auch Grün 3 | 0 | 0 | 0 | 0.000 |
| 1D / Sensitivität: ganzer Körper | 0 | 0 | 0 | 0.000 |
| 1D / Sensitivität: exakt 3 | 0 | 0 | 0 | 0.000 |

Der Nenner umfasst die Kalenderzeit nach Vorlauf auch bei späteren Datenlücken. Niedrige Raten können deshalb von der Datenqualität mitverursacht sein. Ausbleibende Signale sind kein Beweis gegen eine selten handelnde Strategie. Unbekannte Ereignisse sind ausdrücklich kein bestandener Filter.

### Welche einzelne Prüfung bremst?

Die folgende Diagnose benutzt ausschließlich die 2-Kontakt-Referenzfälle. Prüfungen einzeln betrachtet, nicht als unabhängige Ursachen addieren. Kontext und Raum sind unsere vorab definierte numerische Auslegung der weichen Textregel, keine unveränderlichen Tori-Grenzen.

| Intervall | Prüfung | bestanden | nicht bestanden | unbekannt |
|---|---|---:|---:|---:|
| 4h | three | 359 | 866 | 0 |
| 4h | age7 | 1036 | 189 | 0 |
| 4h | momentum | 753 | 472 | 0 |
| 4h | safety | 235 | 990 | 0 |
| 4h | context | 260 | 370 | 595 |
| 4h | room | 89 | 1136 | 0 |
| 4h | events | 0 | 0 | 1225 |
| 4h | age14 | 572 | 653 | 0 |
| 4h | green3 | 160 | 1065 | 0 |
| 4h | whole_body | 432 | 793 | 0 |
| 4h | exact3 | 1 | 1224 | 0 |
| 1D | three | 150 | 312 | 0 |
| 1D | age7 | 462 | 0 | 0 |
| 1D | momentum | 285 | 177 | 0 |
| 1D | safety | 102 | 360 | 0 |
| 1D | context | 112 | 148 | 202 |
| 1D | room | 32 | 430 | 0 |
| 1D | events | 0 | 0 | 462 |
| 1D | age14 | 386 | 76 | 0 |
| 1D | green3 | 67 | 395 | 0 |
| 1D | whole_body | 163 | 299 | 0 |
| 1D | exact3 | 0 | 462 | 0 |

## Schritt 5: Warten statt kurzer Suchfenster

| Geometrie / Intervall / Profil | zufällige Starts | späterer Entry gefunden | bis Datenende keiner | Median Wartezeit unter gefundenen (Kalendertage) |
|---|---:|---:|---:|---:|
| strict / 4h / two | 5700 | 4267 | 1433 | 126.2 |
| strict / 4h / three | 5700 | 3774 | 1926 | 242.6 |
| strict / 4h / age7 | 5700 | 3508 | 2192 | 257.2 |
| strict / 4h / safety | 5700 | 991 | 4709 | 582.2 |
| strict / 4h / context_room | 5700 | 97 | 5603 | 1045.0 |
| strict / 1D / two | 5700 | 3308 | 2392 | 212.5 |
| strict / 1D / three | 5700 | 2971 | 2729 | 384.0 |
| strict / 1D / age7 | 5700 | 2971 | 2729 | 384.0 |
| strict / 1D / safety | 5700 | 917 | 4783 | 631.0 |
| strict / 1D / context_room | 5700 | 0 | 5700 | — |

100 feste Zufallsstarts je Aktie/Intervall/Geometrie, ohne Outcomes ausgewählt. Mehrere Starts dürfen denselben späteren Entry erreichen; sie sind keine zusätzlichen Einstiege. Der Median gilt nur für gefundene Fälle, am Datenende abgeschnittene Wartezeiten sind nicht enthalten.

## Schritte 6–7: Kursverlauf und natürliche Exits

Vergleich unten: alle aufeinander aufbauenden kursbasierten Prüfstände der strengen Geometrie, damit auch die Wirkung vor dem besonders engen Safety- und Kontextfilter sichtbar bleibt. Kein fixes Take-Profit und kein Zehn-Tage-Zwangsverkauf. Nur die Freitagsvariante enthält den vorab definierten diskretionären Widerstandsausstieg. Tages-Freitagsverkauf nach dem Schluss ist nicht ausführbar und wird als nicht unterstützt ausgewiesen.

| Intervall / Profil / Familie / Phase | Entries | Exitmodell | geschlossen | offen | unbekannt | Ø R geschlossen | Treffer % geschlossen |
|---|---:|---|---:|---:|---:|---:|---:|
| 4h / two / breakout / 2021-2023 | 324 | fixed | 165 | 36 | 123 | -1.05 | 0.0 |
| 4h / two / breakout / 2021-2023 | 324 | higher_low | 272 | 6 | 46 | 0.12 | 40.8 |
| 4h / two / breakout / 2021-2023 | 324 | higher_low_green | 275 | 6 | 43 | 0.05 | 38.2 |
| 4h / two / breakout / 2021-2023 | 324 | friday | 281 | 4 | 39 | 0.02 | 44.1 |
| 4h / two / breakout / 2024-2026 | 533 | fixed | 271 | 87 | 175 | -1.12 | 0.0 |
| 4h / two / breakout / 2024-2026 | 533 | higher_low | 453 | 13 | 67 | -0.02 | 38.4 |
| 4h / two / breakout / 2024-2026 | 533 | higher_low_green | 459 | 13 | 61 | -0.02 | 38.1 |
| 4h / two / breakout / 2024-2026 | 533 | friday | 468 | 10 | 55 | -0.01 | 42.1 |
| 4h / two / retest / 2021-2023 | 118 | fixed | 62 | 18 | 38 | -1.07 | 0.0 |
| 4h / two / retest / 2021-2023 | 118 | higher_low | 110 | 0 | 8 | 0.05 | 40.9 |
| 4h / two / retest / 2021-2023 | 118 | higher_low_green | 110 | 0 | 8 | 0.08 | 40.9 |
| 4h / two / retest / 2021-2023 | 118 | friday | 111 | 0 | 7 | 0.03 | 44.1 |
| 4h / two / retest / 2024-2026 | 164 | fixed | 87 | 32 | 45 | -1.15 | 0.0 |
| 4h / two / retest / 2024-2026 | 164 | higher_low | 140 | 8 | 16 | -0.07 | 35.7 |
| 4h / two / retest / 2024-2026 | 164 | higher_low_green | 140 | 8 | 16 | 0.01 | 37.1 |
| 4h / two / retest / 2024-2026 | 164 | friday | 148 | 6 | 10 | 0.09 | 44.6 |
| 4h / two / bounce / 2021-2023 | 37 | fixed | 27 | 1 | 9 | -1.21 | 0.0 |
| 4h / two / bounce / 2021-2023 | 37 | higher_low | 31 | 0 | 6 | -0.03 | 35.5 |
| 4h / two / bounce / 2021-2023 | 37 | higher_low_green | 34 | 0 | 3 | -0.09 | 32.4 |
| 4h / two / bounce / 2021-2023 | 37 | friday | 34 | 0 | 3 | -0.08 | 35.3 |
| 4h / two / bounce / 2024-2026 | 49 | fixed | 38 | 4 | 7 | -1.23 | 0.0 |
| 4h / two / bounce / 2024-2026 | 49 | higher_low | 46 | 0 | 3 | -0.12 | 21.7 |
| 4h / two / bounce / 2024-2026 | 49 | higher_low_green | 46 | 0 | 3 | 0.07 | 26.1 |
| 4h / two / bounce / 2024-2026 | 49 | friday | 46 | 0 | 3 | -0.10 | 26.1 |
| 4h / three / breakout / 2021-2023 | 103 | fixed | 52 | 12 | 39 | -1.05 | 0.0 |
| 4h / three / breakout / 2021-2023 | 103 | higher_low | 91 | 2 | 10 | 0.22 | 45.1 |
| 4h / three / breakout / 2021-2023 | 103 | higher_low_green | 92 | 2 | 9 | 0.09 | 40.2 |
| 4h / three / breakout / 2021-2023 | 103 | friday | 94 | 2 | 7 | 0.06 | 46.8 |
| 4h / three / breakout / 2024-2026 | 163 | fixed | 73 | 32 | 58 | -1.11 | 0.0 |
| 4h / three / breakout / 2024-2026 | 163 | higher_low | 139 | 4 | 20 | 0.12 | 46.8 |
| 4h / three / breakout / 2024-2026 | 163 | higher_low_green | 140 | 4 | 19 | 0.09 | 47.9 |
| 4h / three / breakout / 2024-2026 | 163 | friday | 142 | 3 | 18 | 0.09 | 49.3 |
| 4h / three / retest / 2021-2023 | 30 | fixed | 18 | 3 | 9 | -1.12 | 0.0 |
| 4h / three / retest / 2021-2023 | 30 | higher_low | 29 | 0 | 1 | 0.34 | 48.3 |
| 4h / three / retest / 2021-2023 | 30 | higher_low_green | 29 | 0 | 1 | 0.37 | 44.8 |
| 4h / three / retest / 2021-2023 | 30 | friday | 30 | 0 | 0 | 0.17 | 50.0 |
| 4h / three / retest / 2024-2026 | 40 | fixed | 21 | 8 | 11 | -1.10 | 0.0 |
| 4h / three / retest / 2024-2026 | 40 | higher_low | 36 | 1 | 3 | 0.17 | 50.0 |
| 4h / three / retest / 2024-2026 | 40 | higher_low_green | 36 | 1 | 3 | 0.24 | 52.8 |
| 4h / three / retest / 2024-2026 | 40 | friday | 37 | 0 | 3 | 0.27 | 56.8 |
| 4h / three / bounce / 2021-2023 | 11 | fixed | 7 | 0 | 4 | -1.29 | 0.0 |
| 4h / three / bounce / 2021-2023 | 11 | higher_low | 8 | 0 | 3 | 0.32 | 50.0 |
| 4h / three / bounce / 2021-2023 | 11 | higher_low_green | 10 | 0 | 1 | 0.04 | 40.0 |
| 4h / three / bounce / 2021-2023 | 11 | friday | 10 | 0 | 1 | 0.12 | 50.0 |
| 4h / three / bounce / 2024-2026 | 12 | fixed | 8 | 1 | 3 | -1.42 | 0.0 |
| 4h / three / bounce / 2024-2026 | 12 | higher_low | 10 | 0 | 2 | -0.60 | 20.0 |
| 4h / three / bounce / 2024-2026 | 12 | higher_low_green | 10 | 0 | 2 | -0.20 | 30.0 |
| 4h / three / bounce / 2024-2026 | 12 | friday | 10 | 0 | 2 | -0.20 | 30.0 |
| 4h / age7 / breakout / 2021-2023 | 93 | fixed | 50 | 9 | 34 | -1.04 | 0.0 |
| 4h / age7 / breakout / 2021-2023 | 93 | higher_low | 82 | 1 | 10 | 0.11 | 42.7 |
| 4h / age7 / breakout / 2021-2023 | 93 | higher_low_green | 83 | 1 | 9 | 0.02 | 38.6 |
| 4h / age7 / breakout / 2021-2023 | 93 | friday | 85 | 1 | 7 | 0.01 | 45.9 |
| 4h / age7 / breakout / 2024-2026 | 132 | fixed | 58 | 27 | 47 | -1.11 | 0.0 |
| 4h / age7 / breakout / 2024-2026 | 132 | higher_low | 116 | 3 | 13 | 0.08 | 47.4 |
| 4h / age7 / breakout / 2024-2026 | 132 | higher_low_green | 116 | 3 | 13 | 0.02 | 45.7 |
| 4h / age7 / breakout / 2024-2026 | 132 | friday | 118 | 2 | 12 | 0.03 | 47.5 |
| 4h / age7 / retest / 2021-2023 | 28 | fixed | 18 | 3 | 7 | -1.12 | 0.0 |
| 4h / age7 / retest / 2021-2023 | 28 | higher_low | 27 | 0 | 1 | 0.20 | 44.4 |
| 4h / age7 / retest / 2021-2023 | 28 | higher_low_green | 27 | 0 | 1 | 0.24 | 40.7 |
| 4h / age7 / retest / 2021-2023 | 28 | friday | 28 | 0 | 0 | 0.07 | 46.4 |
| 4h / age7 / retest / 2024-2026 | 36 | fixed | 18 | 7 | 11 | -1.09 | 0.0 |
| 4h / age7 / retest / 2024-2026 | 36 | higher_low | 32 | 1 | 3 | 0.19 | 50.0 |
| 4h / age7 / retest / 2024-2026 | 36 | higher_low_green | 32 | 1 | 3 | 0.23 | 50.0 |
| 4h / age7 / retest / 2024-2026 | 36 | friday | 33 | 0 | 3 | 0.27 | 54.5 |
| 4h / age7 / bounce / 2021-2023 | 10 | fixed | 7 | 0 | 3 | -1.29 | 0.0 |
| 4h / age7 / bounce / 2021-2023 | 10 | higher_low | 8 | 0 | 2 | 0.32 | 50.0 |
| 4h / age7 / bounce / 2021-2023 | 10 | higher_low_green | 9 | 0 | 1 | -0.03 | 33.3 |
| 4h / age7 / bounce / 2021-2023 | 10 | friday | 9 | 0 | 1 | 0.06 | 44.4 |
| 4h / age7 / bounce / 2024-2026 | 11 | fixed | 7 | 1 | 3 | -1.48 | 0.0 |
| 4h / age7 / bounce / 2024-2026 | 11 | higher_low | 9 | 0 | 2 | -0.55 | 22.2 |
| 4h / age7 / bounce / 2024-2026 | 11 | higher_low_green | 9 | 0 | 2 | -0.22 | 33.3 |
| 4h / age7 / bounce / 2024-2026 | 11 | friday | 9 | 0 | 2 | -0.22 | 33.3 |
| 4h / momentum / breakout / 2021-2023 | 68 | fixed | 36 | 7 | 25 | -1.04 | 0.0 |
| 4h / momentum / breakout / 2021-2023 | 68 | higher_low | 60 | 1 | 7 | 0.08 | 40.0 |
| 4h / momentum / breakout / 2021-2023 | 68 | higher_low_green | 61 | 1 | 6 | -0.05 | 34.4 |
| 4h / momentum / breakout / 2021-2023 | 68 | friday | 63 | 1 | 4 | -0.02 | 42.9 |
| 4h / momentum / breakout / 2024-2026 | 101 | fixed | 39 | 22 | 40 | -1.07 | 0.0 |
| 4h / momentum / breakout / 2024-2026 | 101 | higher_low | 89 | 3 | 9 | 0.12 | 50.6 |
| 4h / momentum / breakout / 2024-2026 | 101 | higher_low_green | 89 | 3 | 9 | 0.07 | 49.4 |
| 4h / momentum / breakout / 2024-2026 | 101 | friday | 91 | 2 | 8 | 0.05 | 50.5 |
| 4h / momentum / retest / 2021-2023 | 6 | fixed | 3 | 1 | 2 | -1.01 | 0.0 |
| 4h / momentum / retest / 2021-2023 | 6 | higher_low | 5 | 0 | 1 | -0.01 | 40.0 |
| 4h / momentum / retest / 2021-2023 | 6 | higher_low_green | 5 | 0 | 1 | -0.03 | 40.0 |
| 4h / momentum / retest / 2021-2023 | 6 | friday | 6 | 0 | 0 | -0.04 | 50.0 |
| 4h / momentum / retest / 2024-2026 | 12 | fixed | 7 | 2 | 3 | -1.02 | 0.0 |
| 4h / momentum / retest / 2024-2026 | 12 | higher_low | 12 | 0 | 0 | 0.16 | 41.7 |
| 4h / momentum / retest / 2024-2026 | 12 | higher_low_green | 12 | 0 | 0 | 0.20 | 41.7 |
| 4h / momentum / retest / 2024-2026 | 12 | friday | 12 | 0 | 0 | 0.20 | 41.7 |
| 4h / momentum / bounce / 2021-2023 | 9 | fixed | 6 | 0 | 3 | -1.32 | 0.0 |
| 4h / momentum / bounce / 2021-2023 | 9 | higher_low | 7 | 0 | 2 | 0.52 | 57.1 |
| 4h / momentum / bounce / 2021-2023 | 9 | higher_low_green | 8 | 0 | 1 | 0.10 | 37.5 |
| 4h / momentum / bounce / 2021-2023 | 9 | friday | 8 | 0 | 1 | 0.19 | 50.0 |
| 4h / momentum / bounce / 2024-2026 | 10 | fixed | 6 | 1 | 3 | -1.54 | 0.0 |
| 4h / momentum / bounce / 2024-2026 | 10 | higher_low | 8 | 0 | 2 | -0.48 | 25.0 |
| 4h / momentum / bounce / 2024-2026 | 10 | higher_low_green | 8 | 0 | 2 | -0.12 | 37.5 |
| 4h / momentum / bounce / 2024-2026 | 10 | friday | 8 | 0 | 2 | -0.12 | 37.5 |
| 4h / safety / breakout / 2021-2023 | 2 | fixed | 1 | 1 | 0 | -1.02 | 0.0 |
| 4h / safety / breakout / 2021-2023 | 2 | higher_low | 2 | 0 | 0 | 0.18 | 50.0 |
| 4h / safety / breakout / 2021-2023 | 2 | higher_low_green | 2 | 0 | 0 | 0.22 | 50.0 |
| 4h / safety / breakout / 2021-2023 | 2 | friday | 2 | 0 | 0 | 0.22 | 50.0 |
| 4h / safety / breakout / 2024-2026 | 2 | fixed | 1 | 1 | 0 | -1.04 | 0.0 |
| 4h / safety / breakout / 2024-2026 | 2 | higher_low | 2 | 0 | 0 | 0.70 | 50.0 |
| 4h / safety / breakout / 2024-2026 | 2 | higher_low_green | 2 | 0 | 0 | -0.16 | 50.0 |
| 4h / safety / breakout / 2024-2026 | 2 | friday | 2 | 0 | 0 | -0.16 | 50.0 |
| 4h / safety / retest / 2021-2023 | 0 | fixed | 0 | 0 | 0 | — | — |
| 4h / safety / retest / 2021-2023 | 0 | higher_low | 0 | 0 | 0 | — | — |
| 4h / safety / retest / 2021-2023 | 0 | higher_low_green | 0 | 0 | 0 | — | — |
| 4h / safety / retest / 2021-2023 | 0 | friday | 0 | 0 | 0 | — | — |
| 4h / safety / retest / 2024-2026 | 2 | fixed | 1 | 1 | 0 | -1.02 | 0.0 |
| 4h / safety / retest / 2024-2026 | 2 | higher_low | 2 | 0 | 0 | -0.73 | 0.0 |
| 4h / safety / retest / 2024-2026 | 2 | higher_low_green | 2 | 0 | 0 | -0.73 | 0.0 |
| 4h / safety / retest / 2024-2026 | 2 | friday | 2 | 0 | 0 | -0.73 | 0.0 |
| 4h / safety / bounce / 2021-2023 | 5 | fixed | 3 | 0 | 2 | -1.17 | 0.0 |
| 4h / safety / bounce / 2021-2023 | 5 | higher_low | 4 | 0 | 1 | 1.18 | 75.0 |
| 4h / safety / bounce / 2021-2023 | 5 | higher_low_green | 4 | 0 | 1 | 0.85 | 75.0 |
| 4h / safety / bounce / 2021-2023 | 5 | friday | 4 | 0 | 1 | 0.85 | 75.0 |
| 4h / safety / bounce / 2024-2026 | 9 | fixed | 6 | 1 | 2 | -1.54 | 0.0 |
| 4h / safety / bounce / 2024-2026 | 9 | higher_low | 7 | 0 | 2 | -0.77 | 14.3 |
| 4h / safety / bounce / 2024-2026 | 9 | higher_low_green | 7 | 0 | 2 | -0.35 | 28.6 |
| 4h / safety / bounce / 2024-2026 | 9 | friday | 7 | 0 | 2 | -0.35 | 28.6 |
| 4h / context_room / breakout / 2021-2023 | 0 | fixed | 0 | 0 | 0 | — | — |
| 4h / context_room / breakout / 2021-2023 | 0 | higher_low | 0 | 0 | 0 | — | — |
| 4h / context_room / breakout / 2021-2023 | 0 | higher_low_green | 0 | 0 | 0 | — | — |
| 4h / context_room / breakout / 2021-2023 | 0 | friday | 0 | 0 | 0 | — | — |
| 4h / context_room / breakout / 2024-2026 | 0 | fixed | 0 | 0 | 0 | — | — |
| 4h / context_room / breakout / 2024-2026 | 0 | higher_low | 0 | 0 | 0 | — | — |
| 4h / context_room / breakout / 2024-2026 | 0 | higher_low_green | 0 | 0 | 0 | — | — |
| 4h / context_room / breakout / 2024-2026 | 0 | friday | 0 | 0 | 0 | — | — |
| 4h / context_room / retest / 2021-2023 | 0 | fixed | 0 | 0 | 0 | — | — |
| 4h / context_room / retest / 2021-2023 | 0 | higher_low | 0 | 0 | 0 | — | — |
| 4h / context_room / retest / 2021-2023 | 0 | higher_low_green | 0 | 0 | 0 | — | — |
| 4h / context_room / retest / 2021-2023 | 0 | friday | 0 | 0 | 0 | — | — |
| 4h / context_room / retest / 2024-2026 | 1 | fixed | 0 | 1 | 0 | — | — |
| 4h / context_room / retest / 2024-2026 | 1 | higher_low | 1 | 0 | 0 | -0.44 | 0.0 |
| 4h / context_room / retest / 2024-2026 | 1 | higher_low_green | 1 | 0 | 0 | -0.44 | 0.0 |
| 4h / context_room / retest / 2024-2026 | 1 | friday | 1 | 0 | 0 | -0.44 | 0.0 |
| 4h / context_room / bounce / 2021-2023 | 0 | fixed | 0 | 0 | 0 | — | — |
| 4h / context_room / bounce / 2021-2023 | 0 | higher_low | 0 | 0 | 0 | — | — |
| 4h / context_room / bounce / 2021-2023 | 0 | higher_low_green | 0 | 0 | 0 | — | — |
| 4h / context_room / bounce / 2021-2023 | 0 | friday | 0 | 0 | 0 | — | — |
| 4h / context_room / bounce / 2024-2026 | 0 | fixed | 0 | 0 | 0 | — | — |
| 4h / context_room / bounce / 2024-2026 | 0 | higher_low | 0 | 0 | 0 | — | — |
| 4h / context_room / bounce / 2024-2026 | 0 | higher_low_green | 0 | 0 | 0 | — | — |
| 4h / context_room / bounce / 2024-2026 | 0 | friday | 0 | 0 | 0 | — | — |
| 1D / two / breakout / 2021-2023 | 125 | fixed | 72 | 18 | 35 | -1.05 | 0.0 |
| 1D / two / breakout / 2021-2023 | 125 | higher_low | 99 | 6 | 20 | -0.22 | 24.2 |
| 1D / two / breakout / 2021-2023 | 125 | higher_low_green | 100 | 6 | 19 | -0.12 | 27.0 |
| 1D / two / breakout / 2024-2026 | 180 | fixed | 75 | 49 | 56 | -1.08 | 0.0 |
| 1D / two / breakout / 2024-2026 | 180 | higher_low | 145 | 8 | 27 | 0.01 | 36.6 |
| 1D / two / breakout / 2024-2026 | 180 | higher_low_green | 152 | 7 | 21 | -0.04 | 34.9 |
| 1D / two / retest / 2021-2023 | 63 | fixed | 37 | 15 | 11 | -1.03 | 0.0 |
| 1D / two / retest / 2021-2023 | 63 | higher_low | 49 | 5 | 9 | -0.33 | 32.7 |
| 1D / two / retest / 2021-2023 | 63 | higher_low_green | 50 | 5 | 8 | -0.27 | 34.0 |
| 1D / two / retest / 2024-2026 | 58 | fixed | 25 | 14 | 19 | -1.13 | 0.0 |
| 1D / two / retest / 2024-2026 | 58 | higher_low | 43 | 4 | 11 | -0.25 | 25.6 |
| 1D / two / retest / 2024-2026 | 58 | higher_low_green | 43 | 4 | 11 | -0.10 | 25.6 |
| 1D / two / bounce / 2021-2023 | 15 | fixed | 12 | 0 | 3 | -1.09 | 0.0 |
| 1D / two / bounce / 2021-2023 | 15 | higher_low | 14 | 0 | 1 | -1.02 | 0.0 |
| 1D / two / bounce / 2021-2023 | 15 | higher_low_green | 14 | 0 | 1 | -0.70 | 0.0 |
| 1D / two / bounce / 2024-2026 | 21 | fixed | 16 | 3 | 2 | -1.16 | 0.0 |
| 1D / two / bounce / 2024-2026 | 21 | higher_low | 19 | 0 | 2 | -0.62 | 21.1 |
| 1D / two / bounce / 2024-2026 | 21 | higher_low_green | 19 | 0 | 2 | -0.28 | 31.6 |
| 1D / three / breakout / 2021-2023 | 48 | fixed | 27 | 7 | 14 | -1.06 | 0.0 |
| 1D / three / breakout / 2021-2023 | 48 | higher_low | 34 | 3 | 11 | -0.37 | 17.6 |
| 1D / three / breakout / 2021-2023 | 48 | higher_low_green | 35 | 3 | 10 | -0.29 | 20.0 |
| 1D / three / breakout / 2024-2026 | 66 | fixed | 26 | 18 | 22 | -1.10 | 0.0 |
| 1D / three / breakout / 2024-2026 | 66 | higher_low | 51 | 3 | 12 | 0.26 | 41.2 |
| 1D / three / breakout / 2024-2026 | 66 | higher_low_green | 57 | 2 | 7 | 0.13 | 40.4 |
| 1D / three / retest / 2021-2023 | 15 | fixed | 10 | 2 | 3 | -1.01 | 0.0 |
| 1D / three / retest / 2021-2023 | 15 | higher_low | 12 | 0 | 3 | -0.04 | 50.0 |
| 1D / three / retest / 2021-2023 | 15 | higher_low_green | 12 | 0 | 3 | -0.01 | 50.0 |
| 1D / three / retest / 2024-2026 | 13 | fixed | 7 | 2 | 4 | -1.06 | 0.0 |
| 1D / three / retest / 2024-2026 | 13 | higher_low | 9 | 1 | 3 | -0.68 | 22.2 |
| 1D / three / retest / 2024-2026 | 13 | higher_low_green | 9 | 1 | 3 | -0.39 | 33.3 |
| 1D / three / bounce / 2021-2023 | 5 | fixed | 3 | 0 | 2 | -1.17 | 0.0 |
| 1D / three / bounce / 2021-2023 | 5 | higher_low | 4 | 0 | 1 | -1.00 | 0.0 |
| 1D / three / bounce / 2021-2023 | 5 | higher_low_green | 4 | 0 | 1 | -0.52 | 0.0 |
| 1D / three / bounce / 2024-2026 | 4 | fixed | 3 | 1 | 0 | -1.10 | 0.0 |
| 1D / three / bounce / 2024-2026 | 4 | higher_low | 4 | 0 | 0 | -0.15 | 50.0 |
| 1D / three / bounce / 2024-2026 | 4 | higher_low_green | 4 | 0 | 0 | 0.63 | 75.0 |
| 1D / age7 / breakout / 2021-2023 | 48 | fixed | 27 | 7 | 14 | -1.06 | 0.0 |
| 1D / age7 / breakout / 2021-2023 | 48 | higher_low | 34 | 3 | 11 | -0.37 | 17.6 |
| 1D / age7 / breakout / 2021-2023 | 48 | higher_low_green | 35 | 3 | 10 | -0.29 | 20.0 |
| 1D / age7 / breakout / 2024-2026 | 66 | fixed | 26 | 18 | 22 | -1.10 | 0.0 |
| 1D / age7 / breakout / 2024-2026 | 66 | higher_low | 51 | 3 | 12 | 0.26 | 41.2 |
| 1D / age7 / breakout / 2024-2026 | 66 | higher_low_green | 57 | 2 | 7 | 0.13 | 40.4 |
| 1D / age7 / retest / 2021-2023 | 15 | fixed | 10 | 2 | 3 | -1.01 | 0.0 |
| 1D / age7 / retest / 2021-2023 | 15 | higher_low | 12 | 0 | 3 | -0.04 | 50.0 |
| 1D / age7 / retest / 2021-2023 | 15 | higher_low_green | 12 | 0 | 3 | -0.01 | 50.0 |
| 1D / age7 / retest / 2024-2026 | 13 | fixed | 7 | 2 | 4 | -1.06 | 0.0 |
| 1D / age7 / retest / 2024-2026 | 13 | higher_low | 9 | 1 | 3 | -0.68 | 22.2 |
| 1D / age7 / retest / 2024-2026 | 13 | higher_low_green | 9 | 1 | 3 | -0.39 | 33.3 |
| 1D / age7 / bounce / 2021-2023 | 5 | fixed | 3 | 0 | 2 | -1.17 | 0.0 |
| 1D / age7 / bounce / 2021-2023 | 5 | higher_low | 4 | 0 | 1 | -1.00 | 0.0 |
| 1D / age7 / bounce / 2021-2023 | 5 | higher_low_green | 4 | 0 | 1 | -0.52 | 0.0 |
| 1D / age7 / bounce / 2024-2026 | 4 | fixed | 3 | 1 | 0 | -1.10 | 0.0 |
| 1D / age7 / bounce / 2024-2026 | 4 | higher_low | 4 | 0 | 0 | -0.15 | 50.0 |
| 1D / age7 / bounce / 2024-2026 | 4 | higher_low_green | 4 | 0 | 0 | 0.63 | 75.0 |
| 1D / momentum / breakout / 2021-2023 | 39 | fixed | 22 | 6 | 11 | -1.04 | 0.0 |
| 1D / momentum / breakout / 2021-2023 | 39 | higher_low | 29 | 2 | 8 | -0.29 | 20.7 |
| 1D / momentum / breakout / 2021-2023 | 39 | higher_low_green | 30 | 2 | 7 | -0.23 | 23.3 |
| 1D / momentum / breakout / 2024-2026 | 51 | fixed | 17 | 13 | 21 | -1.15 | 0.0 |
| 1D / momentum / breakout / 2024-2026 | 51 | higher_low | 37 | 2 | 12 | 0.30 | 43.2 |
| 1D / momentum / breakout / 2024-2026 | 51 | higher_low_green | 42 | 2 | 7 | 0.11 | 42.9 |
| 1D / momentum / retest / 2021-2023 | 4 | fixed | 4 | 0 | 0 | -1.02 | 0.0 |
| 1D / momentum / retest / 2021-2023 | 4 | higher_low | 4 | 0 | 0 | 0.04 | 50.0 |
| 1D / momentum / retest / 2021-2023 | 4 | higher_low_green | 4 | 0 | 0 | 0.10 | 50.0 |
| 1D / momentum / retest / 2024-2026 | 3 | fixed | 2 | 0 | 1 | -1.01 | 0.0 |
| 1D / momentum / retest / 2024-2026 | 3 | higher_low | 3 | 0 | 0 | -0.60 | 33.3 |
| 1D / momentum / retest / 2024-2026 | 3 | higher_low_green | 3 | 0 | 0 | -0.29 | 33.3 |
| 1D / momentum / bounce / 2021-2023 | 5 | fixed | 3 | 0 | 2 | -1.17 | 0.0 |
| 1D / momentum / bounce / 2021-2023 | 5 | higher_low | 4 | 0 | 1 | -1.00 | 0.0 |
| 1D / momentum / bounce / 2021-2023 | 5 | higher_low_green | 4 | 0 | 1 | -0.56 | 0.0 |
| 1D / momentum / bounce / 2024-2026 | 4 | fixed | 3 | 1 | 0 | -1.10 | 0.0 |
| 1D / momentum / bounce / 2024-2026 | 4 | higher_low | 4 | 0 | 0 | -0.15 | 50.0 |
| 1D / momentum / bounce / 2024-2026 | 4 | higher_low_green | 4 | 0 | 0 | 0.63 | 75.0 |
| 1D / safety / breakout / 2021-2023 | 2 | fixed | 1 | 0 | 1 | -1.01 | 0.0 |
| 1D / safety / breakout / 2021-2023 | 2 | higher_low | 1 | 0 | 1 | -0.65 | 0.0 |
| 1D / safety / breakout / 2021-2023 | 2 | higher_low_green | 1 | 0 | 1 | -0.50 | 0.0 |
| 1D / safety / breakout / 2024-2026 | 4 | fixed | 2 | 0 | 2 | -1.02 | 0.0 |
| 1D / safety / breakout / 2024-2026 | 4 | higher_low | 2 | 0 | 2 | -1.02 | 0.0 |
| 1D / safety / breakout / 2024-2026 | 4 | higher_low_green | 3 | 0 | 1 | -0.94 | 0.0 |
| 1D / safety / retest / 2021-2023 | 1 | fixed | 1 | 0 | 0 | -1.01 | 0.0 |
| 1D / safety / retest / 2021-2023 | 1 | higher_low | 1 | 0 | 0 | 0.89 | 100.0 |
| 1D / safety / retest / 2021-2023 | 1 | higher_low_green | 1 | 0 | 0 | 0.89 | 100.0 |
| 1D / safety / retest / 2024-2026 | 1 | fixed | 1 | 0 | 0 | -1.02 | 0.0 |
| 1D / safety / retest / 2024-2026 | 1 | higher_low | 1 | 0 | 0 | -1.02 | 0.0 |
| 1D / safety / retest / 2024-2026 | 1 | higher_low_green | 1 | 0 | 0 | -0.72 | 0.0 |
| 1D / safety / bounce / 2021-2023 | 5 | fixed | 3 | 0 | 2 | -1.17 | 0.0 |
| 1D / safety / bounce / 2021-2023 | 5 | higher_low | 4 | 0 | 1 | -1.00 | 0.0 |
| 1D / safety / bounce / 2021-2023 | 5 | higher_low_green | 4 | 0 | 1 | -0.56 | 0.0 |
| 1D / safety / bounce / 2024-2026 | 4 | fixed | 3 | 1 | 0 | -1.10 | 0.0 |
| 1D / safety / bounce / 2024-2026 | 4 | higher_low | 4 | 0 | 0 | -0.15 | 50.0 |
| 1D / safety / bounce / 2024-2026 | 4 | higher_low_green | 4 | 0 | 0 | 0.63 | 75.0 |
| 1D / context_room / breakout / 2021-2023 | 0 | fixed | 0 | 0 | 0 | — | — |
| 1D / context_room / breakout / 2021-2023 | 0 | higher_low | 0 | 0 | 0 | — | — |
| 1D / context_room / breakout / 2021-2023 | 0 | higher_low_green | 0 | 0 | 0 | — | — |
| 1D / context_room / breakout / 2024-2026 | 0 | fixed | 0 | 0 | 0 | — | — |
| 1D / context_room / breakout / 2024-2026 | 0 | higher_low | 0 | 0 | 0 | — | — |
| 1D / context_room / breakout / 2024-2026 | 0 | higher_low_green | 0 | 0 | 0 | — | — |
| 1D / context_room / retest / 2021-2023 | 0 | fixed | 0 | 0 | 0 | — | — |
| 1D / context_room / retest / 2021-2023 | 0 | higher_low | 0 | 0 | 0 | — | — |
| 1D / context_room / retest / 2021-2023 | 0 | higher_low_green | 0 | 0 | 0 | — | — |
| 1D / context_room / retest / 2024-2026 | 0 | fixed | 0 | 0 | 0 | — | — |
| 1D / context_room / retest / 2024-2026 | 0 | higher_low | 0 | 0 | 0 | — | — |
| 1D / context_room / retest / 2024-2026 | 0 | higher_low_green | 0 | 0 | 0 | — | — |
| 1D / context_room / bounce / 2021-2023 | 0 | fixed | 0 | 0 | 0 | — | — |
| 1D / context_room / bounce / 2021-2023 | 0 | higher_low | 0 | 0 | 0 | — | — |
| 1D / context_room / bounce / 2021-2023 | 0 | higher_low_green | 0 | 0 | 0 | — | — |
| 1D / context_room / bounce / 2024-2026 | 0 | fixed | 0 | 0 | 0 | — | — |
| 1D / context_room / bounce / 2024-2026 | 0 | higher_low | 0 | 0 | 0 | — | — |
| 1D / context_room / bounce / 2024-2026 | 0 | higher_low_green | 0 | 0 | 0 | — | — |

**Geschlossene Fälle allein sind keine unverzerrte Gesamtperformance.** Länger gehaltene Positionen können häufiger in eine Datenlücke laufen; sie wurden als unbekannt zensiert. Die Ausstiegsmodelle dürfen deshalb nicht anhand der Mittelwerte unterschiedlich vollständiger Gruppen zum Gewinner erklärt werden. Offene Buchwerte sind kein realisierter Gewinn. R ist das anfängliche geplante Positionsrisiko einschließlich Einstiegskosten, keine Depotprozentzahl.

Insbesondere realisiert ein ausschließlich fester Stop unter dem Einstieg ohne sonstigen Ausstieg definitionsgemäß nur Verluste; erfolgreiche Positionen bleiben offen. Seine null Prozent Gewinntrades unter den geschlossenen Fällen sind deshalb keine faire Verlustquote der Gesamtstrategie.

Kostenannahme pro Seite: halber Spread 2,5 Basispunkte plus 5 Basispunkte Slippage, keine zusätzliche fixe Gebühr. Stop-Gaps zum verfügbaren Open. Bei fehlendem erwarteten 5m-Pfad keine erfundene Stopreihenfolge. Nachgezogene Stops werden erst nach 2+2-Bestätigung und fünf Minuten Latenz wirksam; niemals rückwirkend.

Vollständige Gruppen einschließlich ungefilterter Referenz, Sensitivitäten, 5/10/20/60-Sitzungs-Schlusskursbeobachtungen, gepaarter geschlossener Fälle und Aktien-Blockintervalle liegen in den privaten JSON-Dateien. Diese Schlusskursbeobachtungen sind Ereignisstudien, keine simulierten Strategieexits oder Depot-P/L.

### Vergleich einschließlich offener Positionen

Auf derselben Fallmenge werden geschlossene Positionspfade zum realisierten Wert, offene zum beobachteten Liquidationsbuchwert am gemeinsamen Phasenende bewertet. Kein Verkauf wird dadurch ausgelöst. Nur Fälle mit für alle drei Modelle bekanntem Pfad; diese Auswahl nach Pfadvollständigkeit dient ausschließlich der Diagnose und ist kein handelbarer Entryfilter. Unbekannte Fälle fehlen weiterhin und begrenzen die Aussage.

| Intervall / Profil / Familie | alle Fälle | drei Modelle gemeinsam bekannt | fixed Ø bewertetes R | higher_low Ø bewertetes R | higher_low_green Ø bewertetes R |
|---|---:|---:|---:|---:|---:|
| 4h / two / breakout | 857 | 559 | 0.12 | -0.22 | -0.19 |
| 4h / two / retest | 282 | 199 | 0.34 | -0.27 | -0.16 |
| 4h / two / bounce | 86 | 70 | -0.16 | -0.40 | -0.25 |
| 4h / three / breakout | 266 | 169 | 0.48 | -0.04 | -0.07 |
| 4h / three / retest | 70 | 50 | 0.77 | -0.18 | -0.11 |
| 4h / three / bounce | 23 | 16 | -0.89 | -0.39 | -0.27 |
| 4h / age7 / breakout | 225 | 144 | 0.11 | -0.08 | -0.14 |
| 4h / age7 / retest | 64 | 46 | 0.12 | -0.19 | -0.14 |
| 4h / age7 / bounce | 21 | 15 | -0.88 | -0.35 | -0.29 |
| 4h / momentum / breakout | 169 | 104 | 0.22 | -0.00 | -0.07 |
| 4h / momentum / retest | 18 | 13 | -0.40 | -0.18 | -0.16 |
| 4h / momentum / bounce | 19 | 13 | -0.86 | -0.24 | -0.17 |
| 4h / safety / breakout | 4 | 4 | 1.99 | 0.44 | 0.03 |
| 4h / safety / retest | 2 | 2 | -0.81 | -0.73 | -0.73 |
| 4h / safety / bounce | 14 | 10 | -0.67 | -0.20 | -0.04 |
| 4h / context_room / breakout | 0 | 0 | — | — | — |
| 4h / context_room / retest | 1 | 1 | -0.61 | -0.44 | -0.44 |
| 4h / context_room / bounce | 0 | 0 | — | — | — |
| 1D / two / breakout | 305 | 214 | 0.17 | -0.23 | -0.19 |
| 1D / two / retest | 121 | 91 | 0.33 | -0.33 | -0.21 |
| 1D / two / bounce | 36 | 31 | -0.43 | -0.80 | -0.46 |
| 1D / three / breakout | 114 | 78 | 0.61 | -0.05 | -0.05 |
| 1D / three / retest | 28 | 21 | -0.37 | -0.27 | -0.14 |
| 1D / three / bounce | 9 | 7 | -0.42 | -0.58 | 0.10 |
| 1D / age7 / breakout | 114 | 78 | 0.61 | -0.05 | -0.05 |
| 1D / age7 / retest | 28 | 21 | -0.37 | -0.27 | -0.14 |
| 1D / age7 / bounce | 9 | 7 | -0.42 | -0.58 | 0.10 |
| 1D / momentum / breakout | 90 | 58 | 0.45 | -0.03 | -0.05 |
| 1D / momentum / retest | 7 | 6 | -1.02 | -0.31 | -0.17 |
| 1D / momentum / bounce | 9 | 7 | -0.42 | -0.58 | 0.08 |
| 1D / safety / breakout | 6 | 3 | -1.02 | -0.90 | -0.85 |
| 1D / safety / retest | 2 | 2 | -1.02 | -0.07 | 0.08 |
| 1D / safety / bounce | 9 | 7 | -0.42 | -0.58 | 0.08 |
| 1D / context_room / breakout | 0 | 0 | — | — | — |
| 1D / context_room / retest | 0 | 0 | — | — | — |
| 1D / context_room / bounce | 0 | 0 | — | — | — |

## Was weiterhin offen ist

- 82 verblindete Quellintervall-Fälle vorbereitet; noch keine echten manuellen Ray-Bewertungen. Eine verbesserte Nachbildung subjektiver Linienwahl ist damit technisch messbar, aber nicht durch menschliche Urteile bestätigt.
- Historische, zum jeweiligen Zeitpunkt bekannte Ereignisabdeckung fehlt. Daher keine vollständig nach allen sechs Prüfständen freigegebenen Trades und kein Nachweis für das komplette Textpaket.
- Kein neues Depot-/Cashledger für diese neue Strategie. Die Fallzahlen sind nicht gleich unabhängig gleichzeitig handelbaren Positionen. Keine Aussage über erzielbare Kontorendite.
- Für belastbare Aussage über seltene Signale braucht es ausreichende zusammenhängende Marktdaten, weitere Zukunftsbeobachtung und echte manuelle Geometrieprüfung. Mehr Jahre ersetzen fehlende Datenqualität nicht.

## Reproduzieren

```powershell
python tools/complete_study_import.py --root artifacts/tori-complete-neu
python tools/complete_study.py --root artifacts/tori-complete-neu
python tools/verify_complete_study.py --root artifacts/tori-complete-neu
python tools/report_complete_study.py --root artifacts/tori-complete-neu --output TORI-GESAMTTEST-TABELLEN.md
```

Immer denselben TORI_DATA_DIR benutzen. Die Werkzeuge importieren keine Zugangsdaten in Artefakte und führen keine Orders aus. Ein bereits eingefrorener Lauf verweigert geänderte Engine-/Datasetverträge. Technischer AAPL-Pilot im Importverzeichnis `-a`; finaler Lauf in `-b` verwendet explizit dieselben gepinnten Imports, ergänzt um unveränderte Datenerfassung für den Auditor. Keine Parameter anhand des Pilotergebnisses geändert.

Prüfsumme Forschungsauftrag: `145ce1e6e106ded43c33baa1180a6c9f933c743280ebf41492cf0ca9060ceb68`. Unabhängige Abnahme: 8084 Entrydatensätze, 16096 unterschiedliche Modellpfade, 20365238 geprüfte Pfadkerzen. Keine Browserprüfung nötig, da keine Weboberfläche geändert wurde.
