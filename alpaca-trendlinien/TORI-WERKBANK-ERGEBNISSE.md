# Werkbank: vollständigerer Feed, Sichtprüfung und erklärte Kandidaten

Stand 22.10.2026. Gleiche unveränderte Regeln, keine Optimierung anhand des neuen Verlaufs. Keine Orders, keine Veröffentlichung oder Containerinstallation.

## Datenvergleich auf denselben 57 Aktien

27.07.2020–21.10.2026; ein Jahr Vorlauf, danach chronologisch jede geschlossene Quellkerze. Historischer SIP-Zugriff mit bestehendem Zugang erfolgreich. Echtzeit-SIP ist dadurch nicht freigeschaltet. Splitbereinigte RTH-5m-Daten; Schlussauktions-/Nachbörsenkerzen sind nicht nachträglich ergänzt. Fehlende Daten bleiben unbekannt.

| Feed | Median 5m-Abdeckung | Median 4h-Abdeckung | Median 1D-Abdeckung |
|---|---:|---:|---:|
| IEX | 98.48 % | 78.94 % | 72.45 % |
| SIP | 99.81 % | 99.78 % | 99.74 % |

## Wie viele Einstiege statt harter Zusatzfilter?

Familienfälle können am selben Aktienzeitpunkt zusammenfallen. „Eindeutige Zeitpunkte“ dedupliziert diese, ist aber noch kein kapitalbegrenztes Portfolio.

| Intervall | Profil | IEX Fälle / Zeitpunkte | SIP Fälle / Zeitpunkte | SIP Aktien |
|---|---|---:|---:|---:|
| 4h | two | 1225 / 1200 | 4701 / 4626 | 57 |
| 4h | three | 359 / 356 | 1482 / 1469 | 57 |
| 4h | age7 | 310 / 308 | 1351 / 1339 | 57 |
| 4h | momentum | 206 / 204 | 837 / 830 | 57 |
| 4h | safety | 20 / 20 | 100 / 100 | 44 |
| 4h | context_room | 1 / 1 | 3 / 3 | 3 |
| 4h | all_events | 0 / 0 | 0 / 0 | 0 |
| 1D | two | 462 / 450 | 2155 / 2123 | 57 |
| 1D | three | 151 / 150 | 684 / 681 | 57 |
| 1D | age7 | 151 / 150 | 684 / 681 | 57 |
| 1D | momentum | 106 / 106 | 451 / 450 | 57 |
| 1D | safety | 17 / 17 | 73 / 73 | 36 |
| 1D | context_room | 0 / 0 | 1 / 1 | 1 |
| 1D | all_events | 0 / 0 | 0 / 0 | 0 |

## Beispiel einer Kandidatenliste am Datenende

Alle 60 vorab festgelegten Aktien; nur letzte bekannte Quellschlüsse bis 21.10.2026. Keine aktuelle Kaufempfehlung. Annäherung bedeutet ungebrochene Linie innerhalb 0,75 ATR, keinen bestätigten Ausbruch. Zusätzliche Warnungen filtern diese Ansicht nicht weg.

| Aktie / Intervall | Quellschluss New York | Schlusskurs USD | Risikoabstand ATR | Hinweise |
|---|---|---:|---:|---|
| AXP / 4h | 21.10.2026 16:00 | 323.70 | 1.82 | Momentum noch nicht bestätigt; Wenig Raum zum Widerstand; Unternehmensereignisse unbekannt |
| AXP / 1D | 21.10.2026 16:00 | 323.70 | 2.58 | Momentum noch nicht bestätigt; Safety-Abstand groß oder ungeeignet; Wenig Raum zum Widerstand; Unternehmensereignisse unbekannt |
| INTU / 4h | 21.10.2026 16:00 | 335.50 | 2.41 | Momentum noch nicht bestätigt; Safety-Abstand groß oder ungeeignet; Wenig Raum zum Widerstand; Unternehmensereignisse unbekannt |
| JNJ / 4h | 21.10.2026 16:00 | 257.70 | 7.47 | Momentum noch nicht bestätigt; Safety-Abstand groß oder ungeeignet; Wenig Raum zum Widerstand; Unternehmensereignisse unbekannt |

## Retest: Endkursbeobachtung und Exits getrennt

Drei Kontakte + sieben Tage Alter. Endkursbeobachtungen nach 20 Sitzungen ignorieren einen möglichen früheren Stop. Sie sind keine Trefferquote einer ausgeführten Strategie.

| Feed / Intervall / Phase | Entries | Bekannte 20T-Endpunkte | Positiv | Mittlere Änderung nach Kosten | Higher-low: geschlossen / unbekannt / offen | Mittel R geschlossen |
|---|---:|---:|---:|---:|---|---:|
| iex/4h/all | 64 | 59 | 74.58 % | 5.20 % | 59 / 4 / 1 | 0.20 |
| iex/4h/2021-2023 | 28 | 26 | 73.08 % | 5.31 % | 27 / 1 / 0 | 0.20 |
| iex/4h/2024-2026 | 36 | 33 | 75.76 % | 5.10 % | 32 / 3 / 1 | 0.19 |
| iex/1D/all | 28 | 27 | 55.56 % | 1.48 % | 21 / 6 / 1 | -0.32 |
| iex/1D/2021-2023 | 15 | 15 | 53.33 % | -0.04 % | 12 / 3 / 0 | -0.04 |
| iex/1D/2024-2026 | 13 | 12 | 58.33 % | 3.39 % | 9 / 3 / 1 | -0.68 |
| sip/4h/all | 335 | 317 | 59.94 % | 2.23 % | 321 / 7 / 7 | 0.12 |
| sip/4h/2021-2023 | 166 | 153 | 60.13 % | 2.24 % | 155 / 6 / 5 | 0.06 |
| sip/4h/2024-2026 | 169 | 164 | 59.76 % | 2.23 % | 166 / 1 / 2 | 0.18 |
| sip/1D/all | 163 | 156 | 48.72 % | -0.21 % | 150 / 4 / 9 | -0.08 |
| sip/1D/2021-2023 | 86 | 81 | 46.91 % | -0.71 % | 76 / 3 / 7 | -0.30 |
| sip/1D/2024-2026 | 77 | 75 | 50.67 % | 0.33 % | 74 / 1 / 2 | 0.15 |

## Kapitalrechnung separat

SIP, dieselben Aktien, 4h; Familien getrennt. 2.000 USD, 1 % geplantes Risiko, maximal 25 % Kapital pro Position, fünf Positionen, Bruchteile, keine Kredite, Kosten 5bp voller Spread + 5bp Slippage pro Seite. Kein Ausschluss anhand späterer Datenlücken. Fehlender gehaltener Pfad beendet die Berechnung; dann bleibt die Gesamtrendite unbekannt. Offene Positionen werden bewertet, nicht als realisierter Gewinn ausgegeben.

| Phase / Familie / Exit | Status | Angenommen | Geschlossen | Offen | Markierte Änderung |
|---|---|---:|---:|---:|---:|
| 2021-2023/breakout/fixed | incomplete | 12 | 7 | 5 | — % |
| 2021-2023/breakout/higher_low | incomplete | 22 | 17 | 5 | — % |
| 2021-2023/retest/fixed | incomplete | 12 | 7 | 5 | — % |
| 2021-2023/retest/higher_low | incomplete | 15 | 10 | 5 | — % |
| 2021-2023/bounce/fixed | marked_to_phase_end | 41 | 37 | 4 | -7.89 % |
| 2021-2023/bounce/higher_low | marked_to_phase_end | 43 | 40 | 3 | -2.41 % |
| 2024-2026/breakout/fixed | incomplete | 12 | 7 | 5 | — % |
| 2024-2026/breakout/higher_low | incomplete | 49 | 45 | 4 | — % |
| 2024-2026/retest/fixed | marked_to_phase_end | 12 | 7 | 5 | 20.49 % |
| 2024-2026/retest/higher_low | incomplete | 88 | 83 | 5 | — % |
| 2024-2026/bounce/fixed | incomplete | 11 | 8 | 3 | — % |
| 2024-2026/bounce/higher_low | marked_to_phase_end | 44 | 42 | 2 | 13.08 % |

## Technische Prüfung

Unabhängiger Pfadaudit bestanden: 69,420 unterschiedliche Modellpfade. Erklärter Scanner: 120 Quellreplays mit 13,096 exakt unveränderten ursprünglichen Profil-Entries, unveränderten Ablehnungen/Trichtern und 4,540 vorwärts erzeugten Beobachtungsfakten. Profile überlappen; diese Anzahl ist keine Zahl unabhängiger Trades. Python: 303 Tests jeweils unter 3.12 und 3.13 bestanden (je ein bekannter Windows-Symlink-Skip); 41 JS-Tests bestanden. Echte lokale HTTP-Abnahme und Controller-Test, keine Browser-Sichtprüfung.

## Sichtprüfung und Grenzen

Unter `/pruefung` liegen 82 bisherige Diagnosefälle und 20 fest gezogene Zufallsfälle bereit. Beide Quellintervalle, eigene Rays, horizontale Widerstände und Kontaktmarkierungen; löschen/rückgängig; erst speichern, dann Engine aufdecken. Bewertungen, Historie und Datasetreferenzen liegen im bestehenden gesicherten SQLite-Speicher. Es wurden keine menschlichen Urteile erfunden. Die Diagnosefälle sind Engine-selektiert; die 20 Kontrollen sind keine hinreichende Erfolgsstichprobe.

Die drei zuvor ungültigen IEX-Imports werden nicht in den Hauptvergleich aufgenommen. Separat verfügbare SIP-Titel: CRM, KO, LOW. Deren Kennzahlen stehen im lokalen JSON. Kein historisch vollständiges Universum, keine delisteten Titel rekonstruiert; keine unabhängige Validierung dieser bereits untersuchten Zeiträume. Historische Unternehmensereignisse bleiben ohne belegte Point-in-time-Abdeckung unbekannt.

Der separate JSON-Scanner exportiert Beobachtungsmerkmale ohne Zukunftskurse oder angenommene Kaufkurse. Neue prospektive Registrierungen sind nicht rückdatierbar, bekannte Präfixe und Enginehash werden geschützt. Der vorhandene laufende Beobachter bleibt bei seinen bisherigen Regeln. Der SIP-Vergleich ersetzt keine menschliche Linienprüfung und beweist keine gewinnbringende Strategie.

Quellen: lokale unveränderliche Imports, Studienverträge, eingefrorene Signaldateien, unabhängig geprüfte Pfadjournale und Kapitalledger. Marktfeed-Zugriff: [offizielle Alpaca-FAQ](https://docs.alpaca.markets/us/docs/market-data-faq).
