# Signalepisoden bis zum regelbasierten Exit – 31.10.2026

69 Aktien, 4 bekannte Entryfenster; Nachbeobachtung bis **2026-10-29T15:25:00+00:00**.

**6668 Einstiegfälle aus 4614 Episoden. 10218 Fortsetzungs-/Alternativsignale derselben Struktur und Entryfamilie unterdrückt.** 10 Aktien-/Fensterkombinationen ohne ausreichenden Vorlauf gesondert ausgewiesen.

Dies ist eine Untersuchung einzelner Signalverläufe. Kein gemeinsames Depot, keine Kapital-/Slotsperren und keine Ein-Position-pro-Aktie-Sperre. Je Fall 1.000 USD nominal, fraktionale Stückzahl, 5 Basispunkte Spread insgesamt plus 5 Basispunkte Slippage je Seite, keine Ordergebühr. Kauf am nächsten erwarteten 5m-Open nach 300 Sekunden. Kein Kauf, wenn dieser Kurs fehlt oder der Open bereits unter dem Anfangsstop liegt.

## Vorab festgelegte Fallbildung

Alle Linien desselben Fächers teilen eine Herkunft. Wird eine Kindlinie zur Hauptlinie, bleibt diese Herkunft erhalten. Eine andere Linien-ID, ein nachjustierter Endpunkt oder eine weitere erfüllte Kerze allein erzeugt keinen neuen Fall. Eine bisher unverbundene Ankerstruktur oder mindestens zwei nach dem letzten Episodenstart entstandene und bereits bestätigte Kontakte erlauben eine neue Episode. Je Episode höchstens ein Ausbruch, ein roter Retest beziehungsweise ein Safety-Bounce. Roter Retest und ursprünglicher Ausbruch behalten ihre gemeinsame Szenarioherkunft, auch wenn inzwischen eine neue Episode entstand. Die Abgrenzung ist experimentell und noch kein Beleg für Gleichwertigkeit mit subjektivem Zeichnen.

Alle Zwischenjahre und der Vorlauf werden durch den Episodenfilter geführt; ausgewertet werden nur Entries in den vorab benannten Fenstern. Kontaktklassen werden bei der Entscheidung eingefroren; es gibt keine spätere Hochstufung anhand erfolgreicher Verläufe.

## Exits und Aussagegrenzen

Drei Hard-Stop-Varianten: fester Anfangsstop als Kontrolle, Projektion der ursprünglichen steigenden Safety und aktuelle gültige steigende Safety. Puffer 0,3 %, auf Cent abrunden, nur nach oben nachziehen. Neue Stops wirken erst nach Quellkerzenschluss und 300 Sekunden Verzögerung am nächsten erwarteten 5m-Open. Ein Gap unter den Stop wird zum tatsächlichen Open ausgeführt. Das Hoch der Exitkerze wird wegen unbekannter Intrabarreihenfolge nicht als MFE gutgeschrieben.

**Kein Zeitexit und kein Take Profit.** Der feste Kontrollstop kann einen Gewinn daher überhaupt nicht regulär realisieren: Gewinner bleiben bis Datenende offen oder werden bei fehlendem Pfad zensiert. Eine Trefferquote von null unter seinen geschlossenen Fällen ist konstruktionsbedingt und kein Beweis schlechter Entries. Auch zwischen den Safety-Modellen sind ausschließlich abgeschlossene Fälle keine identische Stichprobe. Offene Buchergebnisse und datenbedingt zensierte Fälle bleiben getrennt; sie werden nicht in abgeschlossene Renditen umbenannt.

## Alle Kontaktklassen

Prozentwerte sind Nettoergebnisse bei gleichem nominalen Einzeleinsatz, keine Depotperformance. Trefferquoten beziehen sich ausschließlich auf abgeschlossene Fälle.

| Entry / Kontaktklasse | Stopführung | Signale | Geschlossen | Offen | Datenlücke | Sonstige | Treffer % | Mittel R | Median R | Mittel netto % | Median netto % |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| breakout:qualified | fixed | 1141 | 824 | 120 | 130 | 67 | 0.00 | -1.08 | -1.00 | -4.20 | -3.41 |
| breakout:qualified | original_safety | 1141 | 990 | 14 | 70 | 67 | 26.57 | -0.06 | -0.57 | -0.31 | -1.52 |
| breakout:qualified | fan_safety | 1141 | 1045 | 0 | 29 | 67 | 40.00 | 0.13 | -0.22 | 0.60 | -0.74 |
| breakout:two | fixed | 2346 | 1778 | 202 | 174 | 192 | 0.00 | -1.08 | -1.00 | -3.78 | -3.03 |
| breakout:two | original_safety | 2346 | 2048 | 31 | 75 | 192 | 24.17 | -0.12 | -0.61 | -0.56 | -1.37 |
| breakout:two | fan_safety | 2346 | 2138 | 0 | 16 | 192 | 34.99 | 0.04 | -0.31 | 0.14 | -0.88 |
| red_retest:qualified | fixed | 745 | 569 | 66 | 69 | 41 | 0.00 | -1.08 | -1.00 | -3.94 | -2.99 |
| red_retest:qualified | original_safety | 745 | 667 | 5 | 32 | 41 | 26.09 | 0.11 | -0.55 | 0.42 | -1.31 |
| red_retest:qualified | fan_safety | 745 | 695 | 0 | 9 | 41 | 37.41 | 0.24 | -0.26 | 0.47 | -0.71 |
| red_retest:two | fixed | 1368 | 1015 | 120 | 129 | 104 | 0.00 | -1.09 | -1.00 | -3.68 | -2.68 |
| red_retest:two | original_safety | 1368 | 1188 | 18 | 58 | 104 | 23.99 | -0.03 | -0.59 | -0.32 | -1.19 |
| red_retest:two | fan_safety | 1368 | 1247 | 0 | 17 | 104 | 35.04 | 0.09 | -0.30 | 0.36 | -0.75 |
| safety_bounce:qualified | fixed | 1068 | 927 | 53 | 56 | 32 | 0.00 | -1.11 | -1.00 | -2.08 | -1.76 |
| safety_bounce:qualified | original_safety | 1068 | 1017 | 2 | 17 | 32 | 23.70 | -0.09 | -0.72 | -0.21 | -0.97 |
| safety_bounce:qualified | fan_safety | 1068 | 1026 | 0 | 10 | 32 | 28.65 | 0.04 | -0.70 | 0.09 | -0.86 |

## Zeitfenster: qualifizierte Entries

| Fenster | Entry | Safety | Geschlossen | Offen | Lücke | Treffer % | Mittel R | Median R | Mittel netto % |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2018 | breakout | original_safety | 256 | 0 | 11 | 25.39 | -0.19 | -0.56 | -1.03 |
| 2018 | breakout | fan_safety | 266 | 0 | 1 | 40.60 | 0.01 | -0.17 | 0.39 |
| 2018 | red_retest | original_safety | 171 | 0 | 3 | 26.32 | -0.27 | -0.64 | -0.97 |
| 2018 | red_retest | fan_safety | 174 | 0 | 0 | 39.08 | -0.11 | -0.24 | -0.08 |
| 2018 | safety_bounce | original_safety | 249 | 0 | 0 | 20.88 | -0.02 | -0.78 | -0.49 |
| 2018 | safety_bounce | fan_safety | 249 | 0 | 0 | 26.91 | -0.09 | -0.76 | -0.24 |
| 2021 | breakout | original_safety | 196 | 0 | 49 | 25.00 | -0.01 | -0.66 | -0.68 |
| 2021 | breakout | fan_safety | 222 | 0 | 23 | 37.39 | 0.18 | -0.28 | 0.35 |
| 2021 | red_retest | original_safety | 130 | 0 | 26 | 15.38 | 0.28 | -0.69 | -0.60 |
| 2021 | red_retest | fan_safety | 148 | 0 | 8 | 33.11 | 0.53 | -0.32 | 0.44 |
| 2021 | safety_bounce | original_safety | 220 | 0 | 14 | 20.45 | -0.34 | -0.71 | -0.40 |
| 2021 | safety_bounce | fan_safety | 226 | 0 | 8 | 25.22 | -0.16 | -0.74 | -0.09 |
| 2023 | breakout | original_safety | 285 | 7 | 7 | 29.12 | 0.10 | -0.53 | 0.47 |
| 2023 | breakout | fan_safety | 295 | 0 | 4 | 44.07 | 0.25 | -0.16 | 1.05 |
| 2023 | red_retest | original_safety | 182 | 2 | 3 | 29.12 | 0.33 | -0.46 | 2.25 |
| 2023 | red_retest | fan_safety | 186 | 0 | 1 | 40.32 | 0.19 | -0.22 | 0.38 |
| 2023 | safety_bounce | original_safety | 270 | 1 | 2 | 29.63 | 0.17 | -0.69 | 0.25 |
| 2023 | safety_bounce | fan_safety | 272 | 0 | 1 | 31.99 | 0.41 | -0.64 | 0.61 |
| 2025-2026 | breakout | original_safety | 253 | 7 | 3 | 26.09 | -0.14 | -0.55 | -0.18 |
| 2025-2026 | breakout | fan_safety | 262 | 0 | 1 | 37.02 | 0.10 | -0.29 | 0.53 |
| 2025-2026 | red_retest | original_safety | 184 | 3 | 0 | 30.43 | 0.15 | -0.50 | 0.64 |
| 2025-2026 | red_retest | fan_safety | 187 | 0 | 0 | 36.36 | 0.38 | -0.24 | 1.10 |
| 2025-2026 | safety_bounce | original_safety | 278 | 1 | 1 | 23.02 | -0.23 | -0.71 | -0.24 |
| 2025-2026 | safety_bounce | fan_safety | 279 | 0 | 1 | 29.75 | -0.05 | -0.67 | 0.03 |

## Gemeinsame geschlossene Fälle: ursprüngliche gegen aktuelle Safety

Die paarweise Teilmenge macht den Methodenvergleich vergleichbarer, löst aber die Auswahl durch Zensierung nicht. Keine Optimierung oder unabhängige Erfolgsbestätigung.

| Entry / Klasse | Beide geschlossen | Nicht beide geschlossen | Mittel R original | Mittel R aktuell | Median ΔR aktuell−original |
|---|---:|---:|---:|---:|---:|
| breakout:qualified | 989 | 152 | -0.06 | 0.08 | 0.00 |
| breakout:two | 2048 | 298 | -0.12 | -0.00 | 0.00 |
| red_retest:qualified | 667 | 78 | 0.11 | 0.19 | 0.00 |
| red_retest:two | 1188 | 180 | -0.03 | 0.05 | 0.00 |
| safety_bounce:qualified | 1017 | 51 | -0.09 | 0.02 | 0.00 |

## Konzentration und offene Verläufe

Anteile beziehen sich auf positive nominale Beiträge abgeschlossener Fälle; keine finanzierbare Depotaddition. Das Weglassen der besten Fälle ist eine nachträgliche Sensitivitätsbeschreibung, kein neuer Handelsfilter.

| Qualifizierter Entry | Safety | Größte Aktie: positive Beiträge % | Top-3 Trades: positive Beiträge % | Median Haltedauer Tage | Mittel netto % ohne beste 3 Trades |
|---|---|---:|---:|---:|---:|
| breakout | original_safety | 6.33 | 8.74 | 8.83 | -0.47 |
| breakout | fan_safety | 5.97 | 10.10 | 6.85 | 0.41 |
| red_retest | original_safety | 25.42 | 28.43 | 7.90 | -0.25 |
| red_retest | fan_safety | 8.58 | 14.71 | 6.00 | 0.22 |
| safety_bounce | original_safety | 4.41 | 8.35 | 3.83 | -0.28 |
| safety_bounce | fan_safety | 5.61 | 6.67 | 3.83 | 0.02 |

## Offene qualifizierte Fälle am Datenende

Hypothetischer Liquidationswert zum letzten vorhandenen Schluss einschließlich modellierter Verkaufskosten; kein tatsächlicher Exit. Nicht mit realisierten Gewinnen addieren. Durch Datenlücken zensierte Fälle sind hier nicht enthalten.

| Entry | Stopführung | Offen | Davon Buchwert positiv | Mittel Buchergebnis netto % | Median Buchergebnis netto % |
|---|---|---:|---:|---:|---:|
| breakout | fixed | 120 | 120 | 151.86 | 78.31 |
| breakout | original_safety | 14 | 14 | 352.54 | 102.09 |
| red_retest | fixed | 66 | 66 | 181.26 | 87.25 |
| red_retest | original_safety | 5 | 5 | 217.59 | 106.22 |
| safety_bounce | fixed | 53 | 53 | 171.71 | 67.70 |
| safety_bounce | original_safety | 2 | 2 | 62.29 | 62.29 |

## Kosten-Nachrechnung auf identischen geschlossenen Fällen

Doppelter variabler Spread-/Slippageansatz bei denselben rohen Entry-/Exitkursen und Regeln. Der nominale Einsatz bleibt pro Fall gleich. Keine Aussage zur tatsächlichen Marktliquidität und kein Ausgleich zensierter Fälle.

| Qualifizierter Entry | Safety | Geschlossen | Mittel netto % bei doppelten Kosten | Median netto % bei doppelten Kosten |
|---|---|---:|---:|---:|
| breakout | original_safety | 990 | -0.46 | -1.67 |
| breakout | fan_safety | 1045 | 0.45 | -0.89 |
| red_retest | original_safety | 667 | 0.27 | -1.46 |
| red_retest | fan_safety | 695 | 0.32 | -0.85 |
| safety_bounce | original_safety | 1017 | -0.36 | -1.12 |
| safety_bounce | fan_safety | 1026 | -0.06 | -1.00 |

## Technische Prüfung und Dateien

6668 Fälle, 6232 feststellbare Entries und 18696 ausgeführte Modellpfade auf IDs, kausale Verfügbarkeit, Stopratchets und Kostenrechnung geprüft. 408 Pfade zusätzlich unabhängig Kerze für Kerze nachgerechnet. Ein separater AAPL-Pilot prüft alle 60 Pfade und die Unveränderlichkeit bei Weglassen zukünftiger Kerzen.

Plan-ID: `581ff6f6cc9ae149b9ebb79ad2cb612d5392e360641bd7a12bbc68d6952060c6`. Private Quelldateien unter `C:\Users\chris\Documents\ChatGPT\Trendlinien\alpaca-trendlinien\artifacts\event-cases-wide-v2-20261031`: `plan.json`, eingefrorener Enginecode, prüfsummengeschützte `stocks/*.json.gz`, `results.json`, `verification.json`, `cases.csv` und `report-details.json`.

Pro Fall: ursprüngliche Signal-/Safety-Geometrie und Kontakte, Entrykurs/-zeit und Kosten, Stopabstand USD/%/ATR4h, zuletzt abgeschlossene Tageskerze, Stopänderungen mit Bestätigungs-/Aktivierungszeit, Exitgrund/-kurs, MFE/MAE und Status. Die CSV erleichtert spätere Abstandsauswertungen; verschachtelte Originaldetails bleiben in den Einzelblöcken.

## Noch offen

Keine prospektive oder unberührte Holdout-Bestätigung; diese bekannten Daten dienen der technischen und deskriptiven Forschung. Aktuelles Überlebendenuniversum, abhängige Episoden/Marktphasen, fehlende Dividenden/FX und Datenlücken bleiben Grenzen. Die drei Stopmodelle sind keine vollständige Umsetzung aller subjektiven Exitentscheidungen. Close-Stop mit explizitem Notstop, neue Abstandsfilter und ein späterer echter Depotbacktest bleiben getrennte nächste Experimente. Sammler bleibt pausiert; keine Providerabrufe, Orders oder Containeränderung.
