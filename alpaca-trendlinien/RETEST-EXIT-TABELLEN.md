# Retest-Exitvergleich: vollständige Tabellen

Vertrag `44b6b5f2a5c701a78a930c097c94a99d7787e9634402147dca0f02fd71873298`. Regeln: [RETEST-EXIT-TEST.md](RETEST-EXIT-TEST.md). Bilanz: [RETEST-EXIT-ERGEBNISSE.md](RETEST-EXIT-ERGEBNISSE.md).

Einzeltrade-R ist nach Kosten und anfänglichem Vertragsrisiko normiert. Historiengruppen und Geometrien getrennt; Fälle können überlappen. Nicht abgeschlossene Pfade zählen nicht als Nullgewinne. Kapitalrechnungen sind eigene modellierte USD-Depots, keine echten Konten. Es wird keine spätere Pfadvollständigkeit zur Depot-Entryauswahl verwendet.

## development

Archivierte Entries: 109; kausal vollständige Vorgeschichte: 56; reine Kalenderzensierung: 0.

| Geometrie / Vorgeschichte | Exit | Fälle | geschlossen | unbekannt | Gewinnanteil % | Ø R | Ø Gewinn R | Ø Verlust R | Profitfaktor R | Ø Netto % | längste Verlustserie | Stopanhebungen |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hull_exact/complete_history | fixed | 20 | 20 | 0 | 35.000 | -0.329 | 0.931 | -1.007 | 0.498 | -0.729 | 3 | 0 |
| hull_exact/complete_history | higher_low_stop | 20 | 20 | 0 | 35.000 | -0.324 | 0.931 | -1.000 | 0.501 | -0.715 | 3 | 5 |
| hull_exact/gapped_history | fixed | 34 | 21 | 13 | 28.571 | 0.019 | 2.133 | -0.827 | 1.032 | 0.743 | 9 | 0 |
| hull_exact/gapped_history | higher_low_stop | 34 | 21 | 13 | 23.810 | -0.156 | 1.857 | -0.786 | 0.739 | 0.027 | 12 | 8 |
| swing_zone/complete_history | fixed | 36 | 36 | 0 | 47.222 | 0.263 | 1.693 | -1.017 | 1.489 | 2.419 | 6 | 0 |
| swing_zone/complete_history | higher_low_stop | 36 | 36 | 0 | 47.222 | 0.269 | 1.693 | -1.006 | 1.506 | 2.424 | 6 | 10 |
| swing_zone/gapped_history | fixed | 19 | 5 | 14 | 20.000 | -0.064 | 3.957 | -1.069 | 0.925 | 3.120 | 4 | 0 |
| swing_zone/gapped_history | higher_low_stop | 19 | 5 | 14 | 20.000 | -0.064 | 3.957 | -1.069 | 0.925 | 3.120 | 4 | 1 |

### Gepaarte R-Differenz: Nachziehen minus fester Stop

| Gruppe | beide geschlossen | Ø Differenz R | Blockintervall unten | oben | volle Zehn-Tage-Strecke: feste Ø R | nachgezogene Ø R |
|---|---:|---:|---:|---:|---:|---:|
| hull_exact/complete_history | 20 | 0.005 | 0.000 | 0.014 | -0.291 | -0.286 |
| hull_exact/gapped_history | 21 | -0.175 | -0.628 | 0.085 | 0.131 | -0.063 |
| swing_zone/complete_history | 36 | 0.006 | -0.006 | 0.032 | 0.339 | 0.346 |
| swing_zone/gapped_history | 5 | 0.000 | 0.000 | 0.000 | -0.064 | -0.064 |

### Kapital: 2.000 USD je unabhängig gestarteter Phase

| Geometrie / Exit | Status | akzeptiert | geschlossen | offen | Endwert USD | Rendite % | max. 5m-Drawdown % |
|---|---|---:|---:|---:|---:|---:|---:|
| hull_exact/fixed | marked_to_phase_end | 19 | 19 | 0 | 1904.266 | -4.787 | -6.102 |
| hull_exact/higher_low_stop | marked_to_phase_end | 19 | 19 | 0 | 1905.654 | -4.717 | -6.034 |
| swing_zone/fixed | marked_to_phase_end | 32 | 32 | 0 | 2244.635 | 12.232 | -5.408 |
| swing_zone/higher_low_stop | marked_to_phase_end | 32 | 32 | 0 | 2245.626 | 12.281 | -5.408 |

## validation

Archivierte Entries: 46; kausal vollständige Vorgeschichte: 28; reine Kalenderzensierung: 5.

| Geometrie / Vorgeschichte | Exit | Fälle | geschlossen | unbekannt | Gewinnanteil % | Ø R | Ø Gewinn R | Ø Verlust R | Profitfaktor R | Ø Netto % | längste Verlustserie | Stopanhebungen |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hull_exact/complete_history | fixed | 9 | 9 | 0 | 66.667 | 0.420 | 0.861 | -0.462 | 3.726 | 3.293 | 2 | 0 |
| hull_exact/complete_history | higher_low_stop | 9 | 9 | 0 | 66.667 | 0.420 | 0.861 | -0.462 | 3.726 | 3.293 | 2 | 5 |
| hull_exact/gapped_history | fixed | 11 | 8 | 3 | 37.500 | 0.354 | 1.745 | -0.480 | 2.181 | 3.145 | 4 | 0 |
| hull_exact/gapped_history | higher_low_stop | 11 | 8 | 3 | 37.500 | 0.390 | 1.745 | -0.423 | 2.475 | 3.375 | 4 | 3 |
| swing_zone/complete_history | fixed | 16 | 16 | 0 | 68.750 | 0.581 | 1.086 | -0.531 | 4.501 | 2.845 | 3 | 0 |
| swing_zone/complete_history | higher_low_stop | 16 | 16 | 0 | 68.750 | 0.539 | 1.086 | -0.666 | 3.589 | 2.577 | 3 | 3 |
| swing_zone/gapped_history | fixed | 5 | 1 | 4 | 0.000 | -1.109 | – | -1.109 | 0.000 | -0.895 | 1 | 0 |
| swing_zone/gapped_history | higher_low_stop | 5 | 1 | 4 | 0.000 | -1.109 | – | -1.109 | 0.000 | -0.895 | 1 | 0 |

### Gepaarte R-Differenz: Nachziehen minus fester Stop

| Gruppe | beide geschlossen | Ø Differenz R | Blockintervall unten | oben | volle Zehn-Tage-Strecke: feste Ø R | nachgezogene Ø R |
|---|---:|---:|---:|---:|---:|---:|
| hull_exact/complete_history | 9 | 0.000 | 0.000 | 0.000 | 0.420 | 0.420 |
| hull_exact/gapped_history | 8 | 0.036 | 0.000 | 0.086 | 0.354 | 0.390 |
| swing_zone/complete_history | 16 | -0.042 | -0.127 | 0.000 | 0.581 | 0.539 |
| swing_zone/gapped_history | 1 | 0.000 | – | – | -1.109 | -1.109 |

### Kapital: 2.000 USD je unabhängig gestarteter Phase

| Geometrie / Exit | Status | akzeptiert | geschlossen | offen | Endwert USD | Rendite % | max. 5m-Drawdown % |
|---|---|---:|---:|---:|---:|---:|---:|
| hull_exact/fixed | marked_to_phase_end | 9 | 9 | 0 | 2086.913 | 4.346 | -1.984 |
| hull_exact/higher_low_stop | marked_to_phase_end | 9 | 9 | 0 | 2086.913 | 4.346 | -1.984 |
| swing_zone/fixed | marked_to_phase_end | 10 | 10 | 0 | 2144.277 | 7.214 | -1.851 |
| swing_zone/higher_low_stop | marked_to_phase_end | 10 | 10 | 0 | 2129.785 | 6.489 | -2.514 |
