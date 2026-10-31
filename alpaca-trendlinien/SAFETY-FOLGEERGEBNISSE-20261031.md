# Safety-Folgeexperiment – 31.10.2026

69 Aktien, 4 bekannte Entryfenster, **6668 unveränderte Originalfälle**. Datenende: 2026-10-29T15:25:00+00:00.

## Was umgesetzt und vorab festgelegt wurde

- `original_safety`: ursprüngliche steigende Entry-Safety weiterprojizieren.
- `fan_safety`: bisherige aktuelle gültige steigende Safety, auch mit nur zwei Kontakten.
- `qualified_fan`: ursprüngliche Safety weiterführen; eine aktuelle Safety zusätzlich nur zulassen, wenn sie am betreffenden 4h-Schluss bereits qualifiziert ist. Höheren gültigen Kandidaten wählen.
- `r2_fan`: ursprüngliche Safety bis mindestens +2 initiale R am bestätigten 4h-Schluss, einschließlich modellierter Verkaufskosten. Danach dauerhaft aktuelle Safety zulassen; kein Zurücksetzen bei Kursrückgang.
- `fixed`: fester Anfangsstop als Kontrolle. Kein Gewinnexit; offene Gewinner sind bei diesem Modell konstruktionsbedingt.

Keine neue Entryauswahl, keine Änderung des Anfangsstops, kein Take Profit, keine Tagesexits und keine Depot-/Kapital-/Slotsperren. Je Fall 1.000 USD nominal mit fraktionalen Stückzahlen. Bestehende Kosten, 300 Sekunden Verzögerung, nächstes erwartetes 5m-Open, Gap-Fills und ausschließlich aufwärts nachgezogene Hard-Stops bleiben erhalten. Die zusätzlichen Varianten ändern keine laufenden Web-/Worker-Defaults.

## Bewertungsmethode

**Geschlossen** bedeutet realisiertes modelliertes Nettoergebnis. **Offen** erhält einen separaten hypothetischen Netto-Liquidationswert am vorhandenen Datenende; das ist kein Exit. **Zensiert** bedeutet unbekannter weiterer Pfad wegen Datenlücke und bleibt außerhalb der Bewertungsmittel. Der Mittelwert geschlossen + offen ist eine Bewertung gleicher nominaler Einzelfälle mit unterschiedlichen Haltedauern, keine finanzierbare Depotperformance. Ausgeschlossene Lücken können das Ergebnis systematisch verzerren. Auch eine gemeinsame auswertbare Teilmenge löst dieses Problem nicht.

## Alle Kontaktklassen und Entryfamilien

| Entry / Klasse | Safety | Geschlossen | Offen | Lücke | Kein Fill | Mittel geschlossen % | Mittel geschlossen + offen % | Median Bewertung % | Mittel ohne beste 3 % |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| breakout:qualified | fixed | 824 | 120 | 130 | 67 | -4.20 | 15.64 | -3.06 | 10.71 |
| breakout:qualified | original_safety | 990 | 14 | 70 | 67 | -0.31 | 4.61 | -1.46 | 0.65 |
| breakout:qualified | fan_safety | 1045 | 0 | 29 | 67 | 0.60 | 0.60 | -0.74 | 0.41 |
| breakout:qualified | qualified_fan | 1037 | 0 | 37 | 67 | 0.86 | 0.86 | -1.09 | 0.66 |
| breakout:qualified | r2_fan | 1030 | 0 | 44 | 67 | 1.07 | 1.07 | -1.34 | 0.82 |
| breakout:two | fixed | 1778 | 202 | 174 | 192 | -3.78 | 12.07 | -2.78 | 9.94 |
| breakout:two | original_safety | 2048 | 31 | 75 | 192 | -0.56 | 2.48 | -1.35 | 0.90 |
| breakout:two | fan_safety | 2138 | 0 | 16 | 192 | 0.14 | 0.14 | -0.88 | 0.06 |
| breakout:two | qualified_fan | 2115 | 0 | 39 | 192 | 0.18 | 0.18 | -1.08 | 0.08 |
| breakout:two | r2_fan | 2111 | 0 | 43 | 192 | 0.51 | 0.51 | -1.25 | 0.35 |
| red_retest:qualified | fixed | 569 | 66 | 69 | 41 | -3.94 | 15.31 | -2.71 | 9.13 |
| red_retest:qualified | original_safety | 667 | 5 | 32 | 41 | 0.42 | 2.04 | -1.30 | 0.27 |
| red_retest:qualified | fan_safety | 695 | 0 | 9 | 41 | 0.47 | 0.47 | -0.71 | 0.22 |
| red_retest:qualified | qualified_fan | 687 | 0 | 17 | 41 | 0.73 | 0.73 | -0.98 | 0.44 |
| red_retest:qualified | r2_fan | 682 | 0 | 22 | 41 | 0.78 | 0.78 | -1.23 | 0.53 |
| red_retest:two | fixed | 1015 | 120 | 129 | 104 | -3.68 | 13.08 | -2.45 | 9.72 |
| red_retest:two | original_safety | 1188 | 18 | 58 | 104 | -0.32 | 2.38 | -1.16 | 0.74 |
| red_retest:two | fan_safety | 1247 | 0 | 17 | 104 | 0.36 | 0.36 | -0.75 | 0.25 |
| red_retest:two | qualified_fan | 1231 | 0 | 33 | 104 | 0.38 | 0.38 | -0.90 | 0.23 |
| red_retest:two | r2_fan | 1222 | 0 | 42 | 104 | 0.45 | 0.45 | -1.09 | 0.28 |
| safety_bounce:qualified | fixed | 927 | 53 | 56 | 32 | -2.08 | 7.32 | -1.68 | 3.82 |
| safety_bounce:qualified | original_safety | 1017 | 2 | 17 | 32 | -0.21 | -0.08 | -0.97 | -0.25 |
| safety_bounce:qualified | fan_safety | 1026 | 0 | 10 | 32 | 0.09 | 0.09 | -0.86 | 0.02 |
| safety_bounce:qualified | qualified_fan | 1022 | 0 | 14 | 32 | 0.03 | 0.03 | -0.91 | -0.04 |
| safety_bounce:qualified | r2_fan | 1024 | 0 | 12 | 32 | 0.10 | 0.10 | -0.90 | 0.02 |

## Identische bewertbare Fälle aller vier Safety-Varianten

Hier müssen alle vier Safety-Varianten geschlossen oder offen sein. Derselbe Fall zählt je Variante genau einmal. Die Auswahl berücksichtigt Auswertbarkeit, nicht die Richtung des Ergebnisses. Abhängige Episoden bleiben abhängig.

| Entry / Klasse | Gemeinsam / gefüllt | Safety | Mittel netto % | Median netto % | Mittel R | Median R | Positive Bewertungen % | Median beobachtete Tage |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| breakout:qualified | 1003 / 1074 | original_safety | 4.62 | -1.46 | 0.62 | -0.56 | 27.62 | 8.94 |
| breakout:qualified | 1003 / 1074 | fan_safety | 0.50 | -0.80 | 0.11 | -0.26 | 38.68 | 6.84 |
| breakout:qualified | 1003 / 1074 | qualified_fan | 0.59 | -1.17 | 0.12 | -0.47 | 33.90 | 8.83 |
| breakout:qualified | 1003 / 1074 | r2_fan | 0.77 | -1.39 | 0.12 | -0.54 | 30.61 | 8.84 |
| breakout:two | 2079 / 2154 | original_safety | 2.48 | -1.35 | 0.24 | -0.60 | 25.30 | 7.86 |
| breakout:two | 2079 / 2154 | fan_safety | 0.09 | -0.92 | 0.02 | -0.33 | 34.25 | 6.15 |
| breakout:two | 2079 / 2154 | qualified_fan | 0.09 | -1.11 | 0.02 | -0.51 | 30.69 | 7.83 |
| breakout:two | 2079 / 2154 | r2_fan | 0.33 | -1.26 | 0.02 | -0.58 | 28.33 | 7.85 |
| red_retest:qualified | 672 / 704 | original_safety | 2.04 | -1.30 | 0.56 | -0.54 | 26.64 | 7.99 |
| red_retest:qualified | 672 / 704 | fan_safety | 0.42 | -0.73 | 0.23 | -0.27 | 36.61 | 5.89 |
| red_retest:qualified | 672 / 704 | qualified_fan | 0.57 | -1.03 | 0.21 | -0.46 | 32.44 | 7.85 |
| red_retest:qualified | 672 / 704 | r2_fan | 0.59 | -1.25 | 0.21 | -0.54 | 28.72 | 7.99 |
| red_retest:two | 1206 / 1264 | original_safety | 2.38 | -1.16 | 0.38 | -0.57 | 25.12 | 7.09 |
| red_retest:two | 1206 / 1264 | fan_safety | 0.29 | -0.79 | 0.06 | -0.33 | 33.75 | 5.85 |
| red_retest:two | 1206 / 1264 | qualified_fan | 0.29 | -0.94 | 0.08 | -0.51 | 31.51 | 7.00 |
| red_retest:two | 1206 / 1264 | r2_fan | 0.34 | -1.11 | 0.06 | -0.56 | 28.19 | 7.06 |
| safety_bounce:qualified | 1019 / 1036 | original_safety | -0.08 | -0.97 | -0.04 | -0.72 | 23.85 | 3.83 |
| safety_bounce:qualified | 1019 / 1036 | fan_safety | 0.07 | -0.87 | 0.03 | -0.71 | 28.26 | 3.83 |
| safety_bounce:qualified | 1019 / 1036 | qualified_fan | 0.01 | -0.92 | -0.02 | -0.71 | 25.61 | 3.83 |
| safety_bounce:qualified | 1019 / 1036 | r2_fan | 0.07 | -0.91 | 0.03 | -0.71 | 26.79 | 3.83 |

## Qualifizierte Fälle nach Entryfenster

| Fenster | Entry | Safety | Geschlossen | Offen | Lücke | Mittel Bewertung % | Median Bewertung % |
|---|---|---|---:|---:|---:|---:|---:|
| 2018 | breakout | original_safety | 256 | 0 | 11 | -1.03 | -1.53 |
| 2018 | breakout | fan_safety | 266 | 0 | 1 | 0.39 | -0.74 |
| 2018 | breakout | qualified_fan | 266 | 0 | 1 | 0.11 | -1.13 |
| 2018 | breakout | r2_fan | 266 | 0 | 1 | 0.78 | -1.34 |
| 2018 | red_retest | original_safety | 171 | 0 | 3 | -0.97 | -1.53 |
| 2018 | red_retest | fan_safety | 174 | 0 | 0 | -0.08 | -0.74 |
| 2018 | red_retest | qualified_fan | 174 | 0 | 0 | -0.07 | -1.10 |
| 2018 | red_retest | r2_fan | 173 | 0 | 1 | -0.07 | -1.42 |
| 2018 | safety_bounce | original_safety | 249 | 0 | 0 | -0.49 | -1.09 |
| 2018 | safety_bounce | fan_safety | 249 | 0 | 0 | -0.24 | -1.03 |
| 2018 | safety_bounce | qualified_fan | 249 | 0 | 0 | -0.35 | -1.06 |
| 2018 | safety_bounce | r2_fan | 249 | 0 | 0 | -0.30 | -1.06 |
| 2021 | breakout | original_safety | 196 | 0 | 49 | -0.68 | -1.60 |
| 2021 | breakout | fan_safety | 222 | 0 | 23 | 0.35 | -0.84 |
| 2021 | breakout | qualified_fan | 215 | 0 | 30 | 0.69 | -1.06 |
| 2021 | breakout | r2_fan | 209 | 0 | 36 | 0.24 | -1.37 |
| 2021 | red_retest | original_safety | 130 | 0 | 26 | -0.60 | -1.27 |
| 2021 | red_retest | fan_safety | 148 | 0 | 8 | 0.44 | -0.81 |
| 2021 | red_retest | qualified_fan | 140 | 0 | 16 | 0.17 | -1.10 |
| 2021 | red_retest | r2_fan | 136 | 0 | 20 | -0.05 | -1.22 |
| 2021 | safety_bounce | original_safety | 220 | 0 | 14 | -0.40 | -0.99 |
| 2021 | safety_bounce | fan_safety | 226 | 0 | 8 | -0.09 | -0.86 |
| 2021 | safety_bounce | qualified_fan | 223 | 0 | 11 | -0.09 | -0.95 |
| 2021 | safety_bounce | r2_fan | 224 | 0 | 10 | -0.04 | -0.94 |
| 2023 | breakout | original_safety | 285 | 7 | 7 | 11.63 | -1.31 |
| 2023 | breakout | fan_safety | 295 | 0 | 4 | 1.05 | -0.47 |
| 2023 | breakout | qualified_fan | 295 | 0 | 4 | 1.64 | -0.96 |
| 2023 | breakout | r2_fan | 295 | 0 | 4 | 2.12 | -1.16 |
| 2023 | red_retest | original_safety | 182 | 2 | 3 | 3.05 | -1.30 |
| 2023 | red_retest | fan_safety | 186 | 0 | 1 | 0.38 | -0.65 |
| 2023 | red_retest | qualified_fan | 186 | 0 | 1 | 0.97 | -0.81 |
| 2023 | red_retest | r2_fan | 186 | 0 | 1 | 1.20 | -1.25 |
| 2023 | safety_bounce | original_safety | 270 | 1 | 2 | 0.68 | -0.85 |
| 2023 | safety_bounce | fan_safety | 272 | 0 | 1 | 0.61 | -0.78 |
| 2023 | safety_bounce | qualified_fan | 271 | 0 | 2 | 0.56 | -0.82 |
| 2023 | safety_bounce | r2_fan | 272 | 0 | 1 | 0.59 | -0.81 |
| 2025-2026 | breakout | original_safety | 253 | 7 | 3 | 6.26 | -1.53 |
| 2025-2026 | breakout | fan_safety | 262 | 0 | 1 | 0.53 | -0.91 |
| 2025-2026 | breakout | qualified_fan | 261 | 0 | 2 | 0.87 | -1.19 |
| 2025-2026 | breakout | r2_fan | 260 | 0 | 3 | 0.87 | -1.46 |
| 2025-2026 | red_retest | original_safety | 184 | 3 | 0 | 5.63 | -1.05 |
| 2025-2026 | red_retest | fan_safety | 187 | 0 | 0 | 1.10 | -0.67 |
| 2025-2026 | red_retest | qualified_fan | 187 | 0 | 0 | 1.67 | -0.79 |
| 2025-2026 | red_retest | r2_fan | 187 | 0 | 0 | 1.78 | -0.94 |
| 2025-2026 | safety_bounce | original_safety | 278 | 1 | 1 | -0.21 | -0.91 |
| 2025-2026 | safety_bounce | fan_safety | 279 | 0 | 1 | 0.03 | -0.82 |
| 2025-2026 | safety_bounce | qualified_fan | 279 | 0 | 1 | -0.04 | -0.86 |
| 2025-2026 | safety_bounce | r2_fan | 279 | 0 | 1 | 0.08 | -0.83 |

## Tatsächlicher Wechsel auf eine engere aktuelle Safety

Ein anderer Linienname allein ist kein Nachweis für engeres Absichern. Gezählt wird die erste Stopänderung auf eine andere Linie, deren Stop oberhalb des gleichzeitig zulässigen Kandidaten der ursprünglichen Safety liegt. Fortschreiben derselben Ursprungslinie zählt nicht als Wechsel. R bezieht sich auf den damaligen bestätigten Schluss und enthält modellierte Kosten, nicht auf zukünftige MFE.

| Entry / Klasse | Engerer Wechsel | Bereits qualifiziert | Nur 2 Kontakte | Median Tage nach Entry | Median damaliges R |
|---|---:|---:|---:|---:|---:|
| breakout:qualified | 543 | 2 | 540 | 6.00 | 0.25 |
| breakout:two | 971 | 5 | 960 | 5.17 | 0.22 |
| red_retest:qualified | 348 | 4 | 343 | 4.00 | 0.18 |
| red_retest:two | 582 | 2 | 575 | 4.05 | 0.19 |
| safety_bounce:qualified | 246 | 3 | 243 | 7.10 | 1.41 |

## Anfangsstop-Abstände: Beschreibung, kein neuer Filter

Feste Klassen, keine Quantile und keine optimierten Mindestabstände. Alle gefüllten Fälle einschließlich offener und zensierter Pfade bleiben in den Statuszahlen. Die Prozent-/ATR-Details sämtlicher Kontaktklassen stehen in `results.json` und `cases.csv`; hier qualifizierte Retests.

| Maß | Abstandsklasse | Safety | Geschlossen | Offen | Lücke | Mittel Bewertung % |
|---|---|---|---:|---:|---:|---:|
| percent | 0–1 | original_safety | 48 | 0 | 1 | 0.84 |
| percent | 0–1 | fan_safety | 48 | 0 | 1 | 1.00 |
| percent | 0–1 | qualified_fan | 48 | 0 | 1 | 0.87 |
| percent | 0–1 | r2_fan | 48 | 0 | 1 | 0.95 |
| percent | 1–2 | original_safety | 149 | 1 | 4 | 0.33 |
| percent | 1–2 | fan_safety | 150 | 0 | 4 | 0.24 |
| percent | 1–2 | qualified_fan | 150 | 0 | 4 | 0.15 |
| percent | 1–2 | r2_fan | 150 | 0 | 4 | 0.25 |
| percent | 2–4 | original_safety | 236 | 1 | 10 | 2.66 |
| percent | 2–4 | fan_safety | 246 | 0 | 1 | 0.44 |
| percent | 2–4 | qualified_fan | 243 | 0 | 4 | 0.56 |
| percent | 2–4 | r2_fan | 243 | 0 | 4 | 0.43 |
| percent | 4–inf | original_safety | 234 | 3 | 17 | 2.74 |
| percent | 4–inf | fan_safety | 251 | 0 | 3 | 0.54 |
| percent | 4–inf | qualified_fan | 246 | 0 | 8 | 1.23 |
| percent | 4–inf | r2_fan | 241 | 0 | 13 | 1.44 |
| atr4h | 0–0.5 | original_safety | 21 | 0 | 0 | 1.98 |
| atr4h | 0–0.5 | fan_safety | 21 | 0 | 0 | 2.04 |
| atr4h | 0–0.5 | qualified_fan | 21 | 0 | 0 | 2.06 |
| atr4h | 0–0.5 | r2_fan | 21 | 0 | 0 | 2.02 |
| atr4h | 0.5–1 | original_safety | 65 | 0 | 2 | -0.20 |
| atr4h | 0.5–1 | fan_safety | 65 | 0 | 2 | 0.11 |
| atr4h | 0.5–1 | qualified_fan | 65 | 0 | 2 | -0.20 |
| atr4h | 0.5–1 | r2_fan | 65 | 0 | 2 | -0.07 |
| atr4h | 1–2 | original_safety | 214 | 2 | 6 | 3.56 |
| atr4h | 1–2 | fan_safety | 218 | 0 | 4 | 0.80 |
| atr4h | 1–2 | qualified_fan | 218 | 0 | 4 | 0.95 |
| atr4h | 1–2 | r2_fan | 218 | 0 | 4 | 0.76 |
| atr4h | 2–inf | original_safety | 367 | 3 | 24 | 1.55 |
| atr4h | 2–inf | fan_safety | 391 | 0 | 3 | 0.26 |
| atr4h | 2–inf | qualified_fan | 383 | 0 | 11 | 0.70 |
| atr4h | 2–inf | r2_fan | 378 | 0 | 16 | 0.88 |

## Offene Läufer der ursprünglichen Safety

Nachträglich nach dem Status der Referenz ausgewählte Beispiele; deshalb kein eigenständiger Erfolgsnachweis. Werte sind Netto-% geschlossen oder offen bewertet; zensiert bleibt unbekannt. Alle Originalfälle bleiben im Gesamttest.

| Aktie | Entry | Fall | Original | Aktuell | Qualifiziert | Ab +2R |
|---|---|---|---:|---:|---:|---:|
| AAPL | breakout | a2a67e64dd7d | 38.57 | -0.02 | 22.76 | 18.14 |
| ABBV | breakout | 6e173723a020 | 110.97 | -3.45 | 6.69 | 6.69 |
| AMGN | breakout | 33cf282d7ac0 | 54.95 | -1.30 | 7.76 | 21.44 |
| AMGN | red_retest | 9dbd4885e0f2 | 55.34 | -0.39 | 8.04 | 21.75 |
| CVX | breakout | c34023000d5b | 52.54 | 19.16 | 19.16 | 19.16 |
| GEV | breakout | 2bbf4b472dc2 | 189.41 | 3.35 | 48.68 | 48.68 |
| GEV | red_retest | abfa8ce8f27a | 170.93 | -3.25 | 39.18 | 44.88 |
| IBM | breakout | ca3408d0a8b3 | 107.15 | 11.45 | 20.57 | 11.45 |
| JNJ | breakout | 25ce2081e91a | 81.91 | 3.22 | 1.01 | 16.64 |
| META | breakout | 6c18526a8a28 | 106.46 | 4.14 | 4.14 | 92.79 |
| META | breakout | 907501436952 | 97.73 | 3.69 | 55.52 | 11.77 |
| MRK | breakout | 7264146cc4bc | 63.72 | 12.08 | 12.08 | 20.07 |
| MU | breakout | ee62796c4710 | 1190.76 | 24.91 | 24.91 | 24.91 |
| MU | red_retest | 9f60270898f5 | 709.37 | 69.80 | 98.22 | 69.80 |
| NFLX | red_retest | b56e244830b0 | 46.07 | 15.03 | 14.89 | 15.03 |
| NVDA | breakout | 72e80317fafd | 413.44 | 15.09 | 18.12 | 15.09 |
| PLTR | breakout | dd44399a6131 | 2371.03 | 93.78 | 100.78 | 93.78 |
| UNP | breakout | b95ffc057426 | 56.91 | 4.59 | 3.76 | 19.59 |
| WFC | red_retest | 26051a095606 | 106.22 | -1.70 | 7.78 | 18.50 |

## Hypothetisches Ergebnis am letzten aktiven Stop

Kein „gesicherter Gewinn“: bei Kurslücken kann der tatsächliche Fill unter dem Stop liegen. Für offene Fälle gilt das letzte vorhandene Beobachtungsdatum; zensierte Fälle haben nur einen früheren letzten zusammenhängenden Beobachtungsstand. Die CSV enthält pro Fall `stopMarkR` und `markAsOf`. Diese Werte sind keine zusätzlichen realisierten Gewinne.

| Qualifizierter Entry | Safety | Status | Fälle | Median hypothetisches Stop-R |
|---|---|---|---:|---:|
| breakout:qualified | fan_safety | censored | 29 | -0.73 |
| breakout:qualified | original_safety | open | 14 | 1.74 |
| breakout:qualified | original_safety | censored | 70 | -0.54 |
| breakout:qualified | qualified_fan | censored | 37 | -0.74 |
| breakout:qualified | r2_fan | censored | 44 | -0.77 |
| red_retest:qualified | fan_safety | censored | 9 | -0.95 |
| red_retest:qualified | original_safety | open | 5 | 2.01 |
| red_retest:qualified | original_safety | censored | 32 | -0.48 |
| red_retest:qualified | qualified_fan | censored | 17 | -0.61 |
| red_retest:qualified | r2_fan | censored | 22 | -0.86 |
| safety_bounce:qualified | fan_safety | censored | 10 | -0.60 |
| safety_bounce:qualified | original_safety | open | 2 | 8.84 |
| safety_bounce:qualified | original_safety | censored | 17 | -0.45 |
| safety_bounce:qualified | qualified_fan | censored | 14 | -0.49 |
| safety_bounce:qualified | r2_fan | censored | 12 | -0.53 |

## Korrekturen an der Interpretation der Rückmeldung

Offene Buchwerte verändern den bisherigen reinen Closed-Trade-Vergleich erheblich. Das bestätigt weder pauschal die ursprüngliche Safety noch die Behauptung, alle fehlenden Verläufe wären Gewinner. Median ΔR nahe null bedeutet keine Mehrheit identischer Ergebnisse: unter den gemeinsam geschlossenen qualifizierten Ausbrüchen sind 382/989 identisch, bei Retests 244/667. Die medianen Anfangsstop-Abstände liegen bei 3,39 % für Ausbrüche und 2,98 % für Retests; Mittelwerte in R und Prozent sind nicht direkt austauschbar.

Alle 75 wegen Open unter Anfangsstop abgesagten Käufe lagen in einer späteren New-York-Handelssitzung: 17,5 bis 89,5 Stunden nach dem Signal. Das ist kein Nachweis eines Stops, der innerhalb von fünf Minuten zu eng wurde. Die 360 Fälle ohne gültigen Anfangsstop benötigen eine separate kausale Untersuchung der Einstiegskonstellation; der Anfangsstop wurde hier bewusst nicht nachträglich verbreitert.

## Prüfungen, Reproduktion und Grenzen

6668 Fälle und 13336 neue Pfade vollständig auf Herkunft, Stopratchets, kausale Verfügbarkeit und Kosten geprüft. 272 deterministisch ausgewählte Pfade zusätzlich unabhängig 5m-Kerze für 5m-Kerze nachgerechnet. CSV-Statuszahlen und Netto-Mittelwerte aller 25 Gruppen/Modellkombinationen separat nachgerechnet. Zusätzlicher AAPL-Pilot: 107 Originalfälle, 214 neue Pfade, 24 unabhängige Replays.

Plan-ID: `fcbee21ee6b7a13e970a647bebb5c60744e7e61591abf79e85e8da6f7fa4afc7`. Quellplan-ID: `581ff6f6cc9ae149b9ebb79ad2cb612d5392e360641bd7a12bbc68d6952060c6`. Private Laufdateien unter `C:\Users\chris\Documents\ChatGPT\Trendlinien\alpaca-trendlinien\artifacts\exit-followup-wide-20261031`. Plan, Enginebindung, Dataset-IDs, prüfsummengeschützte Aktienblöcke, Ergebnisse, CSV und Prüfbericht bleiben erhalten; keine Rohdaten im Git-Repository.

```powershell
python tools/run_exit_followup.py STUDIENORDNER --source ORIGINALSTUDIE --phase prepare
python tools/run_exit_followup.py STUDIENORDNER --phase build --workers 3
python tools/run_exit_followup.py STUDIENORDNER --phase evaluate
python tools/verify_exit_followup.py STUDIENORDNER --samples 2
python tools/report_exit_followup.py STUDIENORDNER --output BERICHT.md
```

Gleichen `TORI_DATA_DIR` wie der Dienst verwenden. Ein geänderter Producer verlangt einen neuen Studienordner; keine Fortsetzung unter anderer Engine. Alle Varianten bleiben explorativ auf bereits bekannten historischen Daten und einem heutigen Überlebendenuniversum. Keine unabhängige neue Validierung, keine Annualisierung, keine garantierte Handelbarkeit und kein Profitabilitätsnachweis. Noch nötig: visuelle Episodenprüfung, plausible Robustheitsprüfung auf unangetasteten Daten und Prüfung der Datenlückensensitivität. Sammler und Providerabrufe bleiben aus; keine Orders oder Containeränderungen.
