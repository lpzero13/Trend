# Drei Retest-Exitvarianten: vollständige Tabellen

Vertrag `faf62307eb52ac09691b9d9de38698e21a66ca130d6ed3efcd2b936b4024eb21`. [Vorabregeln](RETEST-EXIT-VARIANTEN-PLAN.md), [Fazit](RETEST-EXIT-VARIANTEN-ERGEBNISSE.md).
Bekannte Entwicklungs-/Prüfzeiträume, überlappende Fälle; keine unabhängige Marktvalidierung. Alle Ergebnisse nach Modellkosten. Fehlende Daten bleiben unbekannt. Die feste Referenz wird wiederholt gezeigt, nicht als weitere unabhängige Stichprobe gezählt.

## failed_retest / development

| Gruppe | Modell | Fälle | geschlossen | unbekannt | Ø R | Gewinnanteil % | Ø Gewinn R | Ø Verlust R | Profitfaktor R | Ø Netto % | längste Verlustserie | ohne besten Fall Ø R |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hull_exact/complete_history | fixed | 20 | 20 | 0 | -0.329 | 35.000 | 0.931 | -1.007 | 0.498 | -0.729 | 3 | -0.459 |
| hull_exact/complete_history | failed_retest | 20 | 20 | 0 | -0.265 | 25.000 | 1.203 | -0.754 | 0.532 | -0.511 | 5 | -0.391 |
| hull_exact/gapped_history | fixed | 34 | 21 | 13 | 0.019 | 28.571 | 2.133 | -0.827 | 1.032 | 0.743 | 9 | -0.155 |
| hull_exact/gapped_history | failed_retest | 34 | 23 | 11 | -0.110 | 17.391 | 2.638 | -0.688 | 0.807 | -0.005 | 9 | -0.273 |
| swing_zone/complete_history | fixed | 36 | 36 | 0 | 0.263 | 47.222 | 1.693 | -1.017 | 1.489 | 2.419 | 6 | 0.076 |
| swing_zone/complete_history | failed_retest | 36 | 36 | 0 | 0.148 | 33.333 | 2.027 | -0.791 | 1.282 | 1.597 | 6 | -0.041 |
| swing_zone/gapped_history | fixed | 19 | 5 | 14 | -0.064 | 20.000 | 3.957 | -1.069 | 0.925 | 3.120 | 4 | -1.069 |
| swing_zone/gapped_history | failed_retest | 19 | 7 | 12 | 0.006 | 14.286 | 3.957 | -0.653 | 1.010 | 2.769 | 5 | -0.653 |

### Gepaarter Unterschied: Variante minus Referenz

| Gruppe | beide geschlossen | Ø Differenz R | Blockintervall unten | oben | gleiche volle Zehn-Tage-Strecke: Referenz Ø R | Variante Ø R |
|---|---:|---:|---:|---:|---:|---:|
| hull_exact/complete_history | 20 | 0.064 | -0.036 | 0.211 | -0.291 | -0.226 |
| hull_exact/gapped_history | 21 | -0.095 | -0.271 | 0.061 | 0.131 | 0.026 |
| swing_zone/complete_history | 36 | -0.114 | -0.380 | 0.054 | 0.339 | 0.219 |
| swing_zone/gapped_history | 5 | 0.198 | 0.000 | 0.338 | -0.064 | 0.134 |

### Je Phase unabhängig 2.000 USD, vollständige bekannte Vorgeschichte

| Geometrie / Exit | Status | akzeptiert | geschlossen | offen | Endwert USD | Rendite % | max. 5m-Drawdown % |
|---|---|---:|---:|---:|---:|---:|---:|
| hull_exact/fixed | marked_to_phase_end | 19 | 19 | 0 | 1904.266 | -4.787 | -6.102 |
| hull_exact/failed_retest | marked_to_phase_end | 19 | 19 | 0 | 1925.872 | -3.706 | -5.275 |
| swing_zone/fixed | marked_to_phase_end | 32 | 32 | 0 | 2244.635 | 12.232 | -5.408 |
| swing_zone/failed_retest | marked_to_phase_end | 33 | 33 | 0 | 2149.027 | 7.451 | -5.408 |

## failed_retest / validation

| Gruppe | Modell | Fälle | geschlossen | unbekannt | Ø R | Gewinnanteil % | Ø Gewinn R | Ø Verlust R | Profitfaktor R | Ø Netto % | längste Verlustserie | ohne besten Fall Ø R |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hull_exact/complete_history | fixed | 9 | 9 | 0 | 0.420 | 66.667 | 0.861 | -0.462 | 3.726 | 3.293 | 2 | 0.230 |
| hull_exact/complete_history | failed_retest | 9 | 9 | 0 | 0.437 | 66.667 | 0.861 | -0.411 | 4.186 | 3.192 | 2 | 0.249 |
| hull_exact/gapped_history | fixed | 11 | 8 | 3 | 0.354 | 37.500 | 1.745 | -0.480 | 2.181 | 3.145 | 4 | -0.168 |
| hull_exact/gapped_history | failed_retest | 11 | 8 | 3 | 0.137 | 12.500 | 4.009 | -0.416 | 1.376 | 1.826 | 6 | -0.416 |
| swing_zone/complete_history | fixed | 16 | 16 | 0 | 0.581 | 68.750 | 1.086 | -0.531 | 4.501 | 2.845 | 3 | 0.368 |
| swing_zone/complete_history | failed_retest | 16 | 16 | 0 | 0.306 | 43.750 | 1.258 | -0.435 | 2.248 | 1.803 | 3 | 0.074 |
| swing_zone/gapped_history | fixed | 5 | 1 | 4 | -1.109 | 0.000 | – | -1.109 | 0.000 | -0.895 | 1 | – |
| swing_zone/gapped_history | failed_retest | 5 | 2 | 3 | -0.617 | 0.000 | – | -0.617 | 0.000 | -0.678 | 2 | -1.109 |

### Gepaarter Unterschied: Variante minus Referenz

| Gruppe | beide geschlossen | Ø Differenz R | Blockintervall unten | oben | gleiche volle Zehn-Tage-Strecke: Referenz Ø R | Variante Ø R |
|---|---:|---:|---:|---:|---:|---:|
| hull_exact/complete_history | 9 | 0.017 | -0.141 | 0.111 | 0.420 | 0.437 |
| hull_exact/gapped_history | 8 | -0.217 | -0.553 | 0.000 | 0.354 | 0.137 |
| swing_zone/complete_history | 16 | -0.275 | -0.613 | 0.065 | 0.581 | 0.306 |
| swing_zone/gapped_history | 1 | 0.000 | – | – | -1.109 | -1.109 |

### Je Phase unabhängig 2.000 USD, vollständige bekannte Vorgeschichte

| Geometrie / Exit | Status | akzeptiert | geschlossen | offen | Endwert USD | Rendite % | max. 5m-Drawdown % |
|---|---|---:|---:|---:|---:|---:|---:|
| hull_exact/fixed | marked_to_phase_end | 9 | 9 | 0 | 2086.913 | 4.346 | -1.984 |
| hull_exact/failed_retest | marked_to_phase_end | 9 | 9 | 0 | 2084.074 | 4.204 | -1.931 |
| swing_zone/fixed | marked_to_phase_end | 10 | 10 | 0 | 2144.277 | 7.214 | -1.851 |
| swing_zone/failed_retest | marked_to_phase_end | 13 | 13 | 0 | 2111.762 | 5.588 | -2.798 |

## time_no_progress / development

| Gruppe | Modell | Fälle | geschlossen | unbekannt | Ø R | Gewinnanteil % | Ø Gewinn R | Ø Verlust R | Profitfaktor R | Ø Netto % | längste Verlustserie | ohne besten Fall Ø R |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hull_exact/complete_history | fixed | 20 | 20 | 0 | -0.329 | 35.000 | 0.931 | -1.007 | 0.498 | -0.729 | 3 | -0.459 |
| hull_exact/complete_history | time_no_progress | 20 | 20 | 0 | -0.411 | 20.000 | 0.956 | -0.753 | 0.317 | -0.965 | 5 | -0.545 |
| hull_exact/gapped_history | fixed | 34 | 21 | 13 | 0.019 | 28.571 | 2.133 | -0.827 | 1.032 | 0.743 | 9 | -0.155 |
| hull_exact/gapped_history | time_no_progress | 34 | 21 | 13 | -0.027 | 23.810 | 2.293 | -0.752 | 0.953 | 0.492 | 9 | -0.203 |
| swing_zone/complete_history | fixed | 36 | 36 | 0 | 0.263 | 47.222 | 1.693 | -1.017 | 1.489 | 2.419 | 6 | 0.076 |
| swing_zone/complete_history | time_no_progress | 36 | 36 | 0 | 0.226 | 36.111 | 1.998 | -0.776 | 1.456 | 2.302 | 6 | 0.038 |
| swing_zone/gapped_history | fixed | 19 | 5 | 14 | -0.064 | 20.000 | 3.957 | -1.069 | 0.925 | 3.120 | 4 | -1.069 |
| swing_zone/gapped_history | time_no_progress | 19 | 6 | 13 | -0.093 | 16.667 | 3.957 | -0.904 | 0.876 | 2.418 | 4 | -0.904 |

### Gepaarter Unterschied: Variante minus Referenz

| Gruppe | beide geschlossen | Ø Differenz R | Blockintervall unten | oben | gleiche volle Zehn-Tage-Strecke: Referenz Ø R | Variante Ø R |
|---|---:|---:|---:|---:|---:|---:|
| hull_exact/complete_history | 20 | -0.082 | -0.312 | 0.155 | -0.291 | -0.377 |
| hull_exact/gapped_history | 21 | -0.046 | -0.181 | 0.058 | 0.131 | 0.080 |
| swing_zone/complete_history | 36 | -0.037 | -0.194 | 0.086 | 0.339 | 0.301 |
| swing_zone/gapped_history | 5 | 0.040 | 0.000 | 0.151 | -0.064 | -0.024 |

### Je Phase unabhängig 2.000 USD, vollständige bekannte Vorgeschichte

| Geometrie / Exit | Status | akzeptiert | geschlossen | offen | Endwert USD | Rendite % | max. 5m-Drawdown % |
|---|---|---:|---:|---:|---:|---:|---:|
| hull_exact/fixed | marked_to_phase_end | 19 | 19 | 0 | 1904.266 | -4.787 | -6.102 |
| hull_exact/time_no_progress | marked_to_phase_end | 20 | 20 | 0 | 1889.572 | -5.521 | -6.827 |
| swing_zone/fixed | marked_to_phase_end | 32 | 32 | 0 | 2244.635 | 12.232 | -5.408 |
| swing_zone/time_no_progress | marked_to_phase_end | 33 | 33 | 0 | 2234.093 | 11.705 | -5.408 |

## time_no_progress / validation

| Gruppe | Modell | Fälle | geschlossen | unbekannt | Ø R | Gewinnanteil % | Ø Gewinn R | Ø Verlust R | Profitfaktor R | Ø Netto % | längste Verlustserie | ohne besten Fall Ø R |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hull_exact/complete_history | fixed | 9 | 9 | 0 | 0.420 | 66.667 | 0.861 | -0.462 | 3.726 | 3.293 | 2 | 0.230 |
| hull_exact/complete_history | time_no_progress | 9 | 9 | 0 | 0.278 | 55.556 | 0.899 | -0.498 | 2.257 | 2.635 | 2 | 0.071 |
| hull_exact/gapped_history | fixed | 11 | 8 | 3 | 0.354 | 37.500 | 1.745 | -0.480 | 2.181 | 3.145 | 4 | -0.168 |
| hull_exact/gapped_history | time_no_progress | 11 | 8 | 3 | 0.177 | 12.500 | 4.009 | -0.371 | 1.544 | 1.704 | 6 | -0.371 |
| swing_zone/complete_history | fixed | 16 | 16 | 0 | 0.581 | 68.750 | 1.086 | -0.531 | 4.501 | 2.845 | 3 | 0.368 |
| swing_zone/complete_history | time_no_progress | 16 | 16 | 0 | 0.367 | 50.000 | 1.175 | -0.441 | 2.665 | 1.823 | 3 | 0.140 |
| swing_zone/gapped_history | fixed | 5 | 1 | 4 | -1.109 | 0.000 | – | -1.109 | 0.000 | -0.895 | 1 | – |
| swing_zone/gapped_history | time_no_progress | 5 | 1 | 4 | -1.109 | 0.000 | – | -1.109 | 0.000 | -0.895 | 1 | – |

### Gepaarter Unterschied: Variante minus Referenz

| Gruppe | beide geschlossen | Ø Differenz R | Blockintervall unten | oben | gleiche volle Zehn-Tage-Strecke: Referenz Ø R | Variante Ø R |
|---|---:|---:|---:|---:|---:|---:|
| hull_exact/complete_history | 9 | -0.142 | -0.506 | 0.048 | 0.420 | 0.278 |
| hull_exact/gapped_history | 8 | -0.178 | -0.617 | 0.152 | 0.354 | 0.177 |
| swing_zone/complete_history | 16 | -0.214 | -0.496 | 0.058 | 0.581 | 0.367 |
| swing_zone/gapped_history | 1 | 0.000 | – | – | -1.109 | -1.109 |

### Je Phase unabhängig 2.000 USD, vollständige bekannte Vorgeschichte

| Geometrie / Exit | Status | akzeptiert | geschlossen | offen | Endwert USD | Rendite % | max. 5m-Drawdown % |
|---|---|---:|---:|---:|---:|---:|---:|
| hull_exact/fixed | marked_to_phase_end | 9 | 9 | 0 | 2086.913 | 4.346 | -1.984 |
| hull_exact/time_no_progress | marked_to_phase_end | 9 | 9 | 0 | 2059.760 | 2.988 | -2.101 |
| swing_zone/fixed | marked_to_phase_end | 10 | 10 | 0 | 2144.277 | 7.214 | -1.851 |
| swing_zone/time_no_progress | marked_to_phase_end | 11 | 11 | 0 | 2122.272 | 6.114 | -2.704 |

## atr_gain_stop / development

| Gruppe | Modell | Fälle | geschlossen | unbekannt | Ø R | Gewinnanteil % | Ø Gewinn R | Ø Verlust R | Profitfaktor R | Ø Netto % | längste Verlustserie | ohne besten Fall Ø R |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hull_exact/complete_history | fixed | 20 | 20 | 0 | -0.329 | 35.000 | 0.931 | -1.007 | 0.498 | -0.729 | 3 | -0.459 |
| hull_exact/complete_history | atr_gain_stop | 20 | 20 | 0 | -0.399 | 30.000 | 0.884 | -0.948 | 0.400 | -0.805 | 5 | -0.559 |
| hull_exact/gapped_history | fixed | 34 | 21 | 13 | 0.019 | 28.571 | 2.133 | -0.827 | 1.032 | 0.743 | 9 | -0.155 |
| hull_exact/gapped_history | atr_gain_stop | 34 | 21 | 13 | -0.044 | 38.095 | 1.169 | -0.791 | 0.910 | 0.047 | 5 | -0.212 |
| swing_zone/complete_history | fixed | 36 | 36 | 0 | 0.263 | 47.222 | 1.693 | -1.017 | 1.489 | 2.419 | 6 | 0.076 |
| swing_zone/complete_history | atr_gain_stop | 36 | 36 | 0 | 0.252 | 52.778 | 1.297 | -0.916 | 1.582 | 2.356 | 6 | 0.072 |
| swing_zone/gapped_history | fixed | 19 | 5 | 14 | -0.064 | 20.000 | 3.957 | -1.069 | 0.925 | 3.120 | 4 | -1.069 |
| swing_zone/gapped_history | atr_gain_stop | 19 | 6 | 13 | 0.064 | 33.333 | 2.332 | -1.069 | 1.090 | 3.399 | 4 | -0.695 |

### Gepaarter Unterschied: Variante minus Referenz

| Gruppe | beide geschlossen | Ø Differenz R | Blockintervall unten | oben | gleiche volle Zehn-Tage-Strecke: Referenz Ø R | Variante Ø R |
|---|---:|---:|---:|---:|---:|---:|
| hull_exact/complete_history | 20 | -0.070 | -0.239 | 0.073 | -0.291 | -0.364 |
| hull_exact/gapped_history | 21 | -0.063 | -0.404 | 0.281 | 0.131 | 0.061 |
| swing_zone/complete_history | 36 | -0.011 | -0.287 | 0.252 | 0.339 | 0.328 |
| swing_zone/gapped_history | 5 | -0.019 | -0.071 | 0.000 | -0.064 | -0.083 |

### Je Phase unabhängig 2.000 USD, vollständige bekannte Vorgeschichte

| Geometrie / Exit | Status | akzeptiert | geschlossen | offen | Endwert USD | Rendite % | max. 5m-Drawdown % |
|---|---|---:|---:|---:|---:|---:|---:|
| hull_exact/fixed | marked_to_phase_end | 19 | 19 | 0 | 1904.266 | -4.787 | -6.102 |
| hull_exact/atr_gain_stop | marked_to_phase_end | 20 | 20 | 0 | 1898.426 | -5.079 | -6.390 |
| swing_zone/fixed | marked_to_phase_end | 32 | 32 | 0 | 2244.635 | 12.232 | -5.408 |
| swing_zone/atr_gain_stop | marked_to_phase_end | 34 | 34 | 0 | 2243.390 | 12.169 | -3.489 |

## atr_gain_stop / validation

| Gruppe | Modell | Fälle | geschlossen | unbekannt | Ø R | Gewinnanteil % | Ø Gewinn R | Ø Verlust R | Profitfaktor R | Ø Netto % | längste Verlustserie | ohne besten Fall Ø R |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hull_exact/complete_history | fixed | 9 | 9 | 0 | 0.420 | 66.667 | 0.861 | -0.462 | 3.726 | 3.293 | 2 | 0.230 |
| hull_exact/complete_history | atr_gain_stop | 9 | 9 | 0 | 0.458 | 66.667 | 0.917 | -0.462 | 3.970 | 3.527 | 2 | 0.272 |
| hull_exact/gapped_history | fixed | 11 | 8 | 3 | 0.354 | 37.500 | 1.745 | -0.480 | 2.181 | 3.145 | 4 | -0.168 |
| hull_exact/gapped_history | atr_gain_stop | 11 | 8 | 3 | 0.395 | 37.500 | 1.854 | -0.480 | 2.317 | 3.408 | 4 | -0.121 |
| swing_zone/complete_history | fixed | 16 | 16 | 0 | 0.581 | 68.750 | 1.086 | -0.531 | 4.501 | 2.845 | 3 | 0.368 |
| swing_zone/complete_history | atr_gain_stop | 16 | 16 | 0 | 0.544 | 68.750 | 1.032 | -0.531 | 4.278 | 2.712 | 3 | 0.328 |
| swing_zone/gapped_history | fixed | 5 | 1 | 4 | -1.109 | 0.000 | – | -1.109 | 0.000 | -0.895 | 1 | – |
| swing_zone/gapped_history | atr_gain_stop | 5 | 2 | 3 | -0.570 | 0.000 | – | -0.570 | 0.000 | -0.474 | 2 | -1.109 |

### Gepaarter Unterschied: Variante minus Referenz

| Gruppe | beide geschlossen | Ø Differenz R | Blockintervall unten | oben | gleiche volle Zehn-Tage-Strecke: Referenz Ø R | Variante Ø R |
|---|---:|---:|---:|---:|---:|---:|
| hull_exact/complete_history | 9 | 0.038 | 0.000 | 0.125 | 0.420 | 0.458 |
| hull_exact/gapped_history | 8 | 0.041 | 0.000 | 0.105 | 0.354 | 0.395 |
| swing_zone/complete_history | 16 | -0.037 | -0.095 | 0.000 | 0.581 | 0.544 |
| swing_zone/gapped_history | 1 | 0.000 | – | – | -1.109 | -1.109 |

### Je Phase unabhängig 2.000 USD, vollständige bekannte Vorgeschichte

| Geometrie / Exit | Status | akzeptiert | geschlossen | offen | Endwert USD | Rendite % | max. 5m-Drawdown % |
|---|---|---:|---:|---:|---:|---:|---:|
| hull_exact/fixed | marked_to_phase_end | 9 | 9 | 0 | 2086.913 | 4.346 | -1.984 |
| hull_exact/atr_gain_stop | marked_to_phase_end | 9 | 9 | 0 | 2094.009 | 4.700 | -1.590 |
| swing_zone/fixed | marked_to_phase_end | 10 | 10 | 0 | 2144.277 | 7.214 | -1.851 |
| swing_zone/atr_gain_stop | marked_to_phase_end | 10 | 10 | 0 | 2137.865 | 6.893 | -1.851 |
