# Strukturfilter für Signalkandidaten – 31.10.2026

**Ergebnis: Die Vorschläge sind überprüfbare Hypothesen, kein bewiesener Filter für gute Trades. Die strenge Kombination liefert 206 Fälle, aber negative historische Mittel unter allen vier Stopführungen. Sie wird nicht als erfolgreiche Strategie übernommen.**

69 Aktien, 6668 unveränderte Rohfälle, vier bekannte Entryfenster. Keine neuen Providerabrufe, Entries, Exits, Zeitlimits oder Depotlimits. Die vorhandenen eingefrorenen Exitpfade werden nach der Auswahl neu ausgewertet. Alle Profile und Schwellen wurden vor dem Lesen ihrer Ergebnisse gespeichert.

**Grenze dieses Versuchs:** Er filtert die ersten bereits archivierten Ereignisse pro Episode/Familie. Er sucht keine späteren Ersatzentries, wenn das erste Rohsignal den neuen Filter verfehlt. Ein später erstmals qualifiziertes oder erst nach einem Kontextwechsel geeignetes Signal derselben Episode kann im Original bereits als Wiederholung unterdrückt worden sein. Dafür braucht es einen eigenen kausalen Scannerlauf mit Beobachtungszustand und erstmaliger Profilfreigabe, keine nachträgliche Auswahl eines späteren Gewinners.

## Definitionen und wichtige Abweichungen von der Rückmeldung

Die Auswahl verwendet ausschließlich Geometrie und Kurse am Signalschluss. Stopabstände beziehen sich auf den rohen Signalschluss und den bereits feststehenden Anfangsstop. Der tatsächliche Kaufkurs der nächsten Kerze darf einen historischen Signalmarker nicht rückwirkend zulassen oder entfernen. Die alten Tabellen verwenden dagegen Abstände vom späteren modellierten Fill; dadurch sind die neuen Gruppen nicht exakt dieselben.

SMA200 bedeutet: Durchschnitt der letzten 200 vollständig geschlossenen regulären Tageskerzen. Für den Trendvergleich gilt der letzte abgeschlossene Tages-Schluss, nicht der spätere Schluss des noch laufenden Signaltages. Eine Lücke innerhalb dieser 200 Sitzungen oder ein fehlender letzter erwarteter Tag macht den Kontext unbekannt. Erforderliche unbekannte Merkmale führen zum Ausschluss, nicht zu einem stillen Bestehen.

Linienreife ist die bereits bestätigte Kontaktspanne, keine nur durch Warten verlängerte Ankerhistorie. Verengung misst die positive geometrische Breite zwischen der fallenden roten und steigenden grünen Linie am Signal relativ zum gemeinsamen Ankerbeginn. Diese Geometrie ist am Signal bekannt; sie behauptet nicht, dass dieselben später bestätigten Linien bereits am historischen Ankerbeginn handelbar waren. Ein bereits gekreuztes oder nicht positiv messbares Dreieck wird nicht zugelassen.

Die Ausgangsgruppe `qualified` verlangt einen qualifizierten Ausbruch/Retest und bekannte Signal-/Safety-Geometrie. Von den zuvor genannten 1.886 roten qualifizierten Rohfällen fehlt 96 die notwendige Safety-Geometrie; diese waren auch vorher nicht gefüllt. Damit verbleiben 1.790 zeichnungsfähige Fälle, darunter 1.778 tatsächliche Fills und zwölf später abgesagte Entries.

## Vorab festgelegte Profile

| Profil | Kriterien | Fälle | Gefüllt | Abgesagt / nicht gefüllt |
|---|---|---:|---:|---:|
| all |  | 6668 | 6232 | 436 |
| qualified | Qualifizierter Ausbruch oder roter Retest | 1790 | 1778 | 12 |
| risk | Qualifizierter Ausbruch oder roter Retest; Signalabstand zum Anfangsstop mindestens 1 ATR4h und 2 % | 1332 | 1327 | 5 |
| trend | Qualifizierter Ausbruch oder roter Retest; Letzter vollständig geschlossener Tageskurs über sauberem Tages-SMA200 | 981 | 974 | 7 |
| mature | Qualifizierter Ausbruch oder roter Retest; Kontaktspanne Rot mindestens 14 und Safety mindestens 20 Kalendertage | 1104 | 1098 | 6 |
| convergent | Qualifizierter Ausbruch oder roter Retest; Rot fällt, Safety steigt; positive Dreiecksbreite seit gemeinsamem Ankerbeginn mindestens halbiert | 1616 | 1607 | 9 |
| both_qualified | Qualifizierter Ausbruch oder roter Retest; Auch die beim Signal gewählte Safety bereits qualifiziert | 722 | 721 | 1 |
| balanced | Qualifizierter Ausbruch oder roter Retest; Signalabstand zum Anfangsstop mindestens 1 ATR4h und 2 %; Letzter vollständig geschlossener Tageskurs über sauberem Tages-SMA200 | 749 | 745 | 4 |
| strict | Qualifizierter Ausbruch oder roter Retest; Signalabstand zum Anfangsstop mindestens 1 ATR4h und 2 %; Letzter vollständig geschlossener Tageskurs über sauberem Tages-SMA200; Kontaktspanne Rot mindestens 14 und Safety mindestens 20 Kalendertage; Rot fällt, Safety steigt; positive Dreiecksbreite seit gemeinsamem Ankerbeginn mindestens halbiert; Auch die beim Signal gewählte Safety bereits qualifiziert; Direkter Ausbruch höchstens 3,5 ATR4h und 6 % über Anfangsstop; Retest separat | 206 | 206 | 0 |

`all` ist ausschließlich die Vergleichsgruppe. `balanced` wurde vor den Ergebnissen als Standard für eine reduzierte Sichtprüfungs-Playlist festgelegt; es ist kein nachträglich ausgewählter historischer Gewinner. Die Kriterien bleiben im Chart ausdrücklich experimentell.

## Fairer Modellvergleich innerhalb der ausgewählten Gruppe

Für jede Zeile werden nur Fälle verwendet, die unter allen vier Safety-Modellen geschlossen oder am Datenende offen bewertbar sind. Geschlossene Nettoergebnisse und offene hypothetische Netto-Liquidationswerte sind für diesen Bewertungsvergleich zusammengeführt. Datenbedingt unbekannte weitere Verläufe bleiben ausgeschlossen. Das ist keine Depotperformance und kein Nachweis gleicher Kapitalbindung. Die Auswahl verschiedener Profile erzeugt unterschiedliche Fallmengen; deren Mittelwerte beweisen keine kausale Verbesserung.

| Profil | Entry | Gemeinsam bewertbar | Safety | Mittel netto % | Median netto % | Mittel R | Positive Bewertungen % |
|---|---|---:|---|---:|---:|---:|---:|
| all | breakout | 3082 | original_safety | 3.17 | -1.38 | 0.36 | 26.05 |
| all | breakout | 3082 | fan_safety | 0.22 | -0.88 | 0.05 | 35.69 |
| all | breakout | 3082 | qualified_fan | 0.25 | -1.13 | 0.06 | 31.73 |
| all | breakout | 3082 | r2_fan | 0.47 | -1.31 | 0.05 | 29.07 |
| all | red_retest | 1878 | original_safety | 2.26 | -1.20 | 0.45 | 25.67 |
| all | red_retest | 1878 | fan_safety | 0.33 | -0.77 | 0.12 | 34.77 |
| all | red_retest | 1878 | qualified_fan | 0.39 | -0.97 | 0.13 | 31.84 |
| all | red_retest | 1878 | r2_fan | 0.42 | -1.15 | 0.11 | 28.38 |
| qualified | breakout | 1003 | original_safety | 4.62 | -1.46 | 0.62 | 27.62 |
| qualified | breakout | 1003 | fan_safety | 0.50 | -0.80 | 0.11 | 38.68 |
| qualified | breakout | 1003 | qualified_fan | 0.59 | -1.17 | 0.12 | 33.90 |
| qualified | breakout | 1003 | r2_fan | 0.77 | -1.39 | 0.12 | 30.61 |
| qualified | red_retest | 672 | original_safety | 2.04 | -1.30 | 0.56 | 26.64 |
| qualified | red_retest | 672 | fan_safety | 0.42 | -0.73 | 0.23 | 36.61 |
| qualified | red_retest | 672 | qualified_fan | 0.57 | -1.03 | 0.21 | 32.44 |
| qualified | red_retest | 672 | r2_fan | 0.59 | -1.25 | 0.21 | 28.72 |
| risk | breakout | 782 | original_safety | 5.78 | -2.01 | 0.71 | 28.90 |
| risk | breakout | 782 | fan_safety | 0.58 | -0.72 | 0.12 | 42.20 |
| risk | breakout | 782 | qualified_fan | 0.71 | -1.49 | 0.14 | 36.96 |
| risk | breakout | 782 | r2_fan | 0.93 | -1.89 | 0.14 | 32.35 |
| risk | red_retest | 457 | original_safety | 2.80 | -1.97 | 0.58 | 26.91 |
| risk | red_retest | 457 | fan_safety | 0.41 | -0.62 | 0.09 | 40.48 |
| risk | red_retest | 457 | qualified_fan | 0.64 | -1.42 | 0.08 | 35.23 |
| risk | red_retest | 457 | r2_fan | 0.65 | -1.90 | 0.06 | 29.54 |
| trend | breakout | 551 | original_safety | 1.10 | -1.49 | 0.16 | 27.59 |
| trend | breakout | 551 | fan_safety | 0.07 | -0.91 | 0.01 | 36.84 |
| trend | breakout | 551 | qualified_fan | 0.20 | -1.24 | 0.04 | 33.03 |
| trend | breakout | 551 | r2_fan | 0.34 | -1.46 | 0.02 | 29.22 |
| trend | red_retest | 385 | original_safety | 2.32 | -1.33 | 0.72 | 27.27 |
| trend | red_retest | 385 | fan_safety | 0.55 | -0.75 | 0.18 | 36.10 |
| trend | red_retest | 385 | qualified_fan | 0.54 | -1.05 | 0.14 | 31.43 |
| trend | red_retest | 385 | r2_fan | 0.41 | -1.33 | 0.11 | 28.05 |
| mature | breakout | 597 | original_safety | 4.90 | -1.90 | 0.69 | 25.80 |
| mature | breakout | 597 | fan_safety | 0.42 | -0.86 | 0.05 | 40.20 |
| mature | breakout | 597 | qualified_fan | 0.59 | -1.38 | 0.08 | 34.67 |
| mature | breakout | 597 | r2_fan | 0.47 | -1.78 | 0.03 | 29.15 |
| mature | red_retest | 420 | original_safety | 2.73 | -1.68 | 0.56 | 24.52 |
| mature | red_retest | 420 | fan_safety | 0.28 | -0.77 | 0.03 | 37.38 |
| mature | red_retest | 420 | qualified_fan | 0.49 | -1.25 | 0.04 | 32.14 |
| mature | red_retest | 420 | r2_fan | 0.50 | -1.64 | 0.01 | 27.14 |
| convergent | breakout | 943 | original_safety | 4.79 | -1.48 | 0.66 | 27.47 |
| convergent | breakout | 943 | fan_safety | 0.46 | -0.85 | 0.11 | 38.49 |
| convergent | breakout | 943 | qualified_fan | 0.49 | -1.22 | 0.12 | 33.30 |
| convergent | breakout | 943 | r2_fan | 0.57 | -1.41 | 0.12 | 30.65 |
| convergent | red_retest | 579 | original_safety | 2.25 | -1.38 | 0.51 | 25.91 |
| convergent | red_retest | 579 | fan_safety | 0.36 | -0.77 | 0.11 | 36.96 |
| convergent | red_retest | 579 | qualified_fan | 0.43 | -1.11 | 0.08 | 31.26 |
| convergent | red_retest | 579 | r2_fan | 0.51 | -1.33 | 0.08 | 28.50 |
| both_qualified | breakout | 385 | original_safety | -0.69 | -1.68 | -0.16 | 23.38 |
| both_qualified | breakout | 385 | fan_safety | -0.09 | -0.97 | -0.00 | 38.96 |
| both_qualified | breakout | 385 | qualified_fan | -0.16 | -1.42 | -0.01 | 32.47 |
| both_qualified | breakout | 385 | r2_fan | -0.10 | -1.61 | -0.03 | 27.53 |
| both_qualified | red_retest | 287 | original_safety | 0.69 | -1.59 | -0.10 | 21.60 |
| both_qualified | red_retest | 287 | fan_safety | -0.37 | -0.91 | -0.15 | 34.84 |
| both_qualified | red_retest | 287 | qualified_fan | -0.32 | -1.22 | -0.16 | 29.62 |
| both_qualified | red_retest | 287 | r2_fan | -0.19 | -1.54 | -0.17 | 24.74 |
| balanced | breakout | 438 | original_safety | 1.34 | -2.05 | 0.17 | 28.31 |
| balanced | breakout | 438 | fan_safety | 0.07 | -0.95 | 0.01 | 39.04 |
| balanced | breakout | 438 | qualified_fan | 0.23 | -1.55 | 0.04 | 35.16 |
| balanced | breakout | 438 | r2_fan | 0.40 | -2.04 | 0.02 | 30.14 |
| balanced | red_retest | 274 | original_safety | 3.02 | -1.96 | 0.85 | 27.37 |
| balanced | red_retest | 274 | fan_safety | 0.59 | -0.64 | 0.16 | 39.78 |
| balanced | red_retest | 274 | qualified_fan | 0.61 | -1.59 | 0.12 | 33.21 |
| balanced | red_retest | 274 | r2_fan | 0.41 | -1.96 | 0.07 | 28.10 |
| strict | breakout | 94 | original_safety | -1.05 | -1.70 | -0.26 | 28.72 |
| strict | breakout | 94 | fan_safety | -0.25 | -1.03 | -0.05 | 40.43 |
| strict | breakout | 94 | qualified_fan | -0.44 | -1.58 | -0.08 | 32.98 |
| strict | breakout | 94 | r2_fan | -0.63 | -1.65 | -0.13 | 31.91 |
| strict | red_retest | 97 | original_safety | -2.02 | -2.32 | -0.40 | 19.59 |
| strict | red_retest | 97 | fan_safety | -0.33 | -0.76 | -0.09 | 38.14 |
| strict | red_retest | 97 | qualified_fan | -1.62 | -1.88 | -0.31 | 25.77 |
| strict | red_retest | 97 | r2_fan | -1.67 | -2.32 | -0.31 | 20.62 |

## Gleiche Bewertung in den einzelnen Entryfenstern

Gezeigt werden Referenz, reduzierte Playlist und strenge Kombination. Hier sind Auswertbarkeit und Status je Modell separat; verschiedene Fenster haben unterschiedliche mögliche Nachbeobachtungsdauer und sind bereits bekannte Daten.

| Profil | Fenster | Entry | Safety | Signale | Geschlossen | Offen | Lücke | Mittel Bewertung % | Median Bewertung % |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| qualified | 2018 | breakout | original_safety | 269 | 256 | 0 | 11 | -1.03 | -1.53 |
| qualified | 2018 | breakout | fan_safety | 269 | 266 | 0 | 1 | 0.39 | -0.74 |
| qualified | 2018 | breakout | qualified_fan | 269 | 266 | 0 | 1 | 0.11 | -1.13 |
| qualified | 2018 | breakout | r2_fan | 269 | 266 | 0 | 1 | 0.78 | -1.34 |
| qualified | 2021 | breakout | original_safety | 245 | 196 | 0 | 49 | -0.68 | -1.60 |
| qualified | 2021 | breakout | fan_safety | 245 | 222 | 0 | 23 | 0.35 | -0.84 |
| qualified | 2021 | breakout | qualified_fan | 245 | 215 | 0 | 30 | 0.69 | -1.06 |
| qualified | 2021 | breakout | r2_fan | 245 | 209 | 0 | 36 | 0.24 | -1.37 |
| qualified | 2023 | breakout | original_safety | 301 | 285 | 7 | 7 | 11.63 | -1.31 |
| qualified | 2023 | breakout | fan_safety | 301 | 295 | 0 | 4 | 1.05 | -0.47 |
| qualified | 2023 | breakout | qualified_fan | 301 | 295 | 0 | 4 | 1.64 | -0.96 |
| qualified | 2023 | breakout | r2_fan | 301 | 295 | 0 | 4 | 2.12 | -1.16 |
| qualified | 2025-2026 | breakout | original_safety | 263 | 253 | 7 | 3 | 6.26 | -1.53 |
| qualified | 2025-2026 | breakout | fan_safety | 263 | 262 | 0 | 1 | 0.53 | -0.91 |
| qualified | 2025-2026 | breakout | qualified_fan | 263 | 261 | 0 | 2 | 0.87 | -1.19 |
| qualified | 2025-2026 | breakout | r2_fan | 263 | 260 | 0 | 3 | 0.87 | -1.46 |
| qualified | 2018 | red_retest | original_safety | 175 | 171 | 0 | 3 | -0.97 | -1.53 |
| qualified | 2018 | red_retest | fan_safety | 175 | 174 | 0 | 0 | -0.08 | -0.74 |
| qualified | 2018 | red_retest | qualified_fan | 175 | 174 | 0 | 0 | -0.07 | -1.10 |
| qualified | 2018 | red_retest | r2_fan | 175 | 173 | 0 | 1 | -0.07 | -1.42 |
| qualified | 2021 | red_retest | original_safety | 158 | 130 | 0 | 26 | -0.60 | -1.27 |
| qualified | 2021 | red_retest | fan_safety | 158 | 148 | 0 | 8 | 0.44 | -0.81 |
| qualified | 2021 | red_retest | qualified_fan | 158 | 140 | 0 | 16 | 0.17 | -1.10 |
| qualified | 2021 | red_retest | r2_fan | 158 | 136 | 0 | 20 | -0.05 | -1.22 |
| qualified | 2023 | red_retest | original_safety | 190 | 182 | 2 | 3 | 3.05 | -1.30 |
| qualified | 2023 | red_retest | fan_safety | 190 | 186 | 0 | 1 | 0.38 | -0.65 |
| qualified | 2023 | red_retest | qualified_fan | 190 | 186 | 0 | 1 | 0.97 | -0.81 |
| qualified | 2023 | red_retest | r2_fan | 190 | 186 | 0 | 1 | 1.20 | -1.25 |
| qualified | 2025-2026 | red_retest | original_safety | 189 | 184 | 3 | 0 | 5.63 | -1.05 |
| qualified | 2025-2026 | red_retest | fan_safety | 189 | 187 | 0 | 0 | 1.10 | -0.67 |
| qualified | 2025-2026 | red_retest | qualified_fan | 189 | 187 | 0 | 0 | 1.67 | -0.79 |
| qualified | 2025-2026 | red_retest | r2_fan | 189 | 187 | 0 | 0 | 1.78 | -0.94 |
| balanced | 2018 | breakout | original_safety | 122 | 119 | 0 | 1 | -0.78 | -2.05 |
| balanced | 2018 | breakout | fan_safety | 122 | 120 | 0 | 0 | 0.14 | -0.85 |
| balanced | 2018 | breakout | qualified_fan | 122 | 120 | 0 | 0 | -0.37 | -1.66 |
| balanced | 2018 | breakout | r2_fan | 122 | 120 | 0 | 0 | 1.03 | -1.88 |
| balanced | 2021 | breakout | original_safety | 97 | 79 | 0 | 18 | -1.43 | -2.57 |
| balanced | 2021 | breakout | fan_safety | 97 | 89 | 0 | 8 | 0.11 | -0.98 |
| balanced | 2021 | breakout | qualified_fan | 97 | 88 | 0 | 9 | 0.51 | -1.89 |
| balanced | 2021 | breakout | r2_fan | 97 | 86 | 0 | 11 | -0.52 | -2.33 |
| balanced | 2023 | breakout | original_safety | 116 | 109 | 3 | 4 | 5.73 | -1.61 |
| balanced | 2023 | breakout | fan_safety | 116 | 114 | 0 | 2 | 0.63 | -0.43 |
| balanced | 2023 | breakout | qualified_fan | 116 | 114 | 0 | 2 | 1.94 | -1.32 |
| balanced | 2023 | breakout | r2_fan | 116 | 114 | 0 | 2 | 2.35 | -1.58 |
| balanced | 2025-2026 | breakout | original_safety | 128 | 125 | 3 | 0 | 1.19 | -1.92 |
| balanced | 2025-2026 | breakout | fan_safety | 128 | 128 | 0 | 0 | -0.10 | -0.98 |
| balanced | 2025-2026 | breakout | qualified_fan | 128 | 128 | 0 | 0 | 0.18 | -1.28 |
| balanced | 2025-2026 | breakout | r2_fan | 128 | 128 | 0 | 0 | -0.19 | -1.92 |
| balanced | 2018 | red_retest | original_safety | 72 | 72 | 0 | 0 | -0.41 | -2.01 |
| balanced | 2018 | red_retest | fan_safety | 72 | 72 | 0 | 0 | 0.68 | 0.01 |
| balanced | 2018 | red_retest | qualified_fan | 72 | 72 | 0 | 0 | 0.63 | -0.56 |
| balanced | 2018 | red_retest | r2_fan | 72 | 72 | 0 | 0 | 0.82 | -2.01 |
| balanced | 2021 | red_retest | original_safety | 58 | 49 | 0 | 8 | -1.48 | -2.18 |
| balanced | 2021 | red_retest | fan_safety | 58 | 56 | 0 | 1 | 0.64 | -0.52 |
| balanced | 2021 | red_retest | qualified_fan | 58 | 54 | 0 | 3 | -0.39 | -1.81 |
| balanced | 2021 | red_retest | r2_fan | 58 | 53 | 0 | 4 | -0.43 | -2.10 |
| balanced | 2023 | red_retest | original_safety | 77 | 75 | 0 | 2 | 0.71 | -2.04 |
| balanced | 2023 | red_retest | fan_safety | 77 | 77 | 0 | 0 | 0.47 | -0.77 |
| balanced | 2023 | red_retest | qualified_fan | 77 | 77 | 0 | 0 | 1.41 | -1.64 |
| balanced | 2023 | red_retest | r2_fan | 77 | 77 | 0 | 0 | 1.22 | -1.98 |
| balanced | 2025-2026 | red_retest | original_safety | 79 | 75 | 3 | 0 | 11.24 | -1.81 |
| balanced | 2025-2026 | red_retest | fan_safety | 79 | 78 | 0 | 0 | 1.02 | -0.76 |
| balanced | 2025-2026 | red_retest | qualified_fan | 79 | 78 | 0 | 0 | 1.68 | -1.47 |
| balanced | 2025-2026 | red_retest | r2_fan | 79 | 78 | 0 | 0 | 1.13 | -1.81 |
| strict | 2018 | breakout | original_safety | 29 | 29 | 0 | 0 | -1.63 | -2.23 |
| strict | 2018 | breakout | fan_safety | 29 | 29 | 0 | 0 | -0.62 | -1.24 |
| strict | 2018 | breakout | qualified_fan | 29 | 29 | 0 | 0 | -1.31 | -2.07 |
| strict | 2018 | breakout | r2_fan | 29 | 29 | 0 | 0 | -0.97 | -2.07 |
| strict | 2021 | breakout | original_safety | 26 | 19 | 0 | 7 | -0.89 | -2.71 |
| strict | 2021 | breakout | fan_safety | 26 | 22 | 0 | 4 | 0.52 | -1.11 |
| strict | 2021 | breakout | qualified_fan | 26 | 21 | 0 | 5 | 2.63 | -2.67 |
| strict | 2021 | breakout | r2_fan | 26 | 21 | 0 | 5 | 1.17 | -2.69 |
| strict | 2023 | breakout | original_safety | 22 | 21 | 0 | 1 | 0.20 | -1.52 |
| strict | 2023 | breakout | fan_safety | 22 | 21 | 0 | 1 | 0.74 | -0.32 |
| strict | 2023 | breakout | qualified_fan | 22 | 21 | 0 | 1 | 0.50 | -1.52 |
| strict | 2023 | breakout | r2_fan | 22 | 21 | 0 | 1 | 0.65 | -1.52 |
| strict | 2025-2026 | breakout | original_safety | 25 | 25 | 0 | 0 | -1.56 | -1.67 |
| strict | 2025-2026 | breakout | fan_safety | 25 | 25 | 0 | 0 | -0.45 | -0.58 |
| strict | 2025-2026 | breakout | qualified_fan | 25 | 25 | 0 | 0 | -1.05 | -1.17 |
| strict | 2025-2026 | breakout | r2_fan | 25 | 25 | 0 | 0 | -1.56 | -1.67 |
| strict | 2018 | red_retest | original_safety | 22 | 22 | 0 | 0 | -1.73 | -2.44 |
| strict | 2018 | red_retest | fan_safety | 22 | 22 | 0 | 0 | -1.14 | -0.86 |
| strict | 2018 | red_retest | qualified_fan | 22 | 22 | 0 | 0 | -1.59 | -2.37 |
| strict | 2018 | red_retest | r2_fan | 22 | 22 | 0 | 0 | -1.42 | -2.44 |
| strict | 2021 | red_retest | original_safety | 24 | 18 | 0 | 6 | -2.14 | -1.81 |
| strict | 2021 | red_retest | fan_safety | 24 | 23 | 0 | 1 | 1.06 | 1.12 |
| strict | 2021 | red_retest | qualified_fan | 24 | 22 | 0 | 2 | 0.31 | -1.31 |
| strict | 2021 | red_retest | r2_fan | 24 | 21 | 0 | 3 | -0.66 | -1.47 |
| strict | 2023 | red_retest | original_safety | 30 | 29 | 0 | 1 | -2.22 | -2.71 |
| strict | 2023 | red_retest | fan_safety | 30 | 30 | 0 | 0 | 0.17 | -1.46 |
| strict | 2023 | red_retest | qualified_fan | 30 | 30 | 0 | 0 | -0.73 | -1.81 |
| strict | 2023 | red_retest | r2_fan | 30 | 30 | 0 | 0 | -0.38 | -2.56 |
| strict | 2025-2026 | red_retest | original_safety | 28 | 28 | 0 | 0 | -1.97 | -2.26 |
| strict | 2025-2026 | red_retest | fan_safety | 28 | 28 | 0 | 0 | -0.72 | -0.66 |
| strict | 2025-2026 | red_retest | qualified_fan | 28 | 28 | 0 | 0 | -1.18 | -1.93 |
| strict | 2025-2026 | red_retest | r2_fan | 28 | 28 | 0 | 0 | -2.02 | -2.26 |

## SMA200: bekannte Gegenprobe und unbekannte Daten trennen

Unter den 1.790 zeichnungsfähigen qualifizierten Fällen: 981 über SMA200, 571 nicht darüber und 238 mit unbekanntem SMA-Kontext. Ein Ausschluss unbekannter Daten ist keine bestätigte Trendregel. Folgende Werte nutzen wiederum gemeinsame bewertbare Fälle aller vier Modelle.

| Tageskontext | Entry | Gemeinsam | Original % | Aktuell % | Qualifizierter Fan % | Ab +2R % |
|---|---|---:|---:|---:|---:|---:|
| nicht über SMA200 | breakout | 338 | 5.18 | 1.17 | 1.31 | 1.54 |
| nicht über SMA200 | red_retest | 205 | 2.33 | 0.54 | 1.07 | 1.50 |
| unbekannt | breakout | 114 | 19.95 | 0.57 | 0.33 | 0.55 |
| unbekannt | red_retest | 82 | 0.01 | -0.48 | -0.51 | -0.89 |
| über SMA200 | breakout | 551 | 1.10 | 0.07 | 0.20 | 0.34 |
| über SMA200 | red_retest | 385 | 2.32 | 0.55 | 0.54 | 0.41 |

## Welche Aussagen der Rückmeldung tragen nicht?

- „Ohne Overfitting“ ist unbelegt. Plausible Strukturregeln und verbreitete Indikatoren können ebenfalls auf bekannte Ergebnisse angepasst werden. Diese Fenster waren bereits mehrfach ausgewertet.
- ATR- und Prozentklassen sind nicht austauschbar. 1 ATR entspricht je Aktie, Zeitpunkt und Volatilität einem anderen Prozentabstand. Die gemeinsame Bedingung wurde deshalb ausdrücklich separat getestet.
- Die „ATR-Todeszone“ ist keine bestätigte Marktursache. Im alten Retest-Tableau stehen in 0,5–1 ATR 67 gefüllte Fälle (65 geschlossen, zwei zensiert); 1–2 ATR enthält 222 und über 2 ATR 394. Die dort genannten 65/218/391 sind keine konsistenten Gesamtfallzahlen.
- ATR ist ein Durchschnitt wahrer Handelsspannen, keine garantierte Mindestschwankung einer einzelnen nächsten Kerze. Ein breiterer Stop macht aus einem ungeeigneten Einstieg nicht automatisch einen guten.
- Beide Linien mit hoher Kontaktqualität zu verlangen ist eine testbare Zusatzregel. Die Gruppe `both_qualified` ist hier schwächer als die einfache Ausgangsgruppe, nicht automatisch besser.
- 206 strenge Fälle erfüllen ungefähr die erhoffte Größenordnung, liefern aber negative Mittel unter sämtlichen vier Stops. Eine kleine „Lehrbuch“-Liste ist kein Erfolgsnachweis.

## Umsetzung im Chart und Replay

Unter **Historische Einstiege → Signalauswahl** stehen dieselben neun Profile zur Verfügung. Chartstandard ist die einfache qualifizierte Ausgangsgruppe. Die vorab festgelegte reduzierte Struktur-/Abstands-/Trend-Playlist bleibt als experimentelles Profil und als private Sichtprüfungsliste verfügbar; sie wurde durch ihr Ergebnis nicht zur empfohlenen Strategie erklärt. Es werden nur die zum Chartzeitpunkt bereits bekannten passenden Signalpunkte gezeigt. Die Statuszeile nennt die durch das Profil ausgeschlossene Anzahl. Die ausgewählte Originalgeometrie bleibt fixiert; Replay, einzelne Kerzenschritte und persönliche Bewertungen bleiben erhalten. Ein Profilwechsel entfernt ausgeschlossene Marker und ausgewählte Linien. „Alle Rohsignale · Vergleich“ macht Ausschlüsse kontrollierbar. Im Detail werden Signalabstand, Tageskontext und Profil erläutert; keine späteren Gewinne oder zukünftigen Fills werden vorweggenommen. Tori-Analyse und historische Signalebene starten weiterhin optional, persönliche Zeichnungen bleiben separat.

Keine neue Datenbank, Migration oder Duplizierung der ursprünglichen Fälle. Ein begrenzter Speicher-Cache je unveränderlicher Entryversion spart wiederholtes Lesen. Die Filter verwenden denselben Code wie das Offline-Experiment. Die erste Öffnung einer noch nicht geprüften Aktie kann einmalig Datasetprüfung und Featureaufbau benötigen; keine erneute Linienfindung oder Providerabfrage bei einem Profilwechsel.

## Technische Nachweise und Reproduktion

6668 Fälle, 9 vorab definierte Profile; Mitgliedschaften und aggregierte Mittelwerte separat geprüft. 136 Stichproben mit unabhängig berechnetem Tages-SMA und abgeschnittener Zukunft bestätigen den Signalzeitpunkt-Vertrag. Quellindizes aller Fälle stimmen mit der eingefrorenen ursprünglichen 4h-Timeline überein. Die Sichtprüfungs-Playlist enthält keine Exit-/Erfolgsdaten.

Plan-ID: `fb34d18af966975236b0165741a3cf246472239cff61630e2cec76329a769b94`. Private Laufdateien: `C:\Users\chris\Documents\ChatGPT\Trendlinien\alpaca-trendlinien\artifacts\entry-screen-20261031`. Plan/Code/Datasetbindung, atomare Aktienblöcke und Schreiblock. Neue Engine erfordert einen neuen Studienordner; gleichen `TORI_DATA_DIR` wie der Dienst verwenden. Laufdaten und Datasets nicht veröffentlichen.

```powershell
python tools/run_entry_screen.py STUDIE --source SAFETY-FOLGESTUDIE --phase prepare
python tools/run_entry_screen.py STUDIE --phase build --workers 3
python tools/run_entry_screen.py STUDIE --phase evaluate
python tools/verify_entry_screen.py STUDIE --workers 3
python tools/report_entry_screen.py STUDIE --output BERICHT.md
```

## Empfehlung

Die einfache qualifizierte Ausgangsgruppe als Forschungsreferenz behalten. Stopabstand ist eine nützliche Beschreibung, aber hier kein eindeutiger pauschaler Mindestfilter. SMA200, Linienalter und Verengung nicht gemeinsam zum verpflichtenden Strategie-Gate erklären. Zuerst Ausbruch und Retest getrennt anhand eingefrorener Beispiele blind prüfen, einschließlich ausgeschlossener Fälle. Danach wenige fachlich begründete Regeln auf tatsächlich unangetasteten Daten prüfen, ohne Schwellen an diesen Ergebnissen weiter zu optimieren. Das Ziel ist eine kleinere brauchbare Beobachtungsliste mit vertretbaren Verlusten und ausreichenden positiven Beiträgen, keine rückwirkend gewinnreine Liste. Aktuelles Überlebendenuniversum, abhängige Episoden, informative Datenlücken, Kostenannahmen und ungleiche Haltedauer bleiben Grenzen. Keine automatisch als profitabel freigegebene Strategie, keine Orders und keine Containeränderung.
