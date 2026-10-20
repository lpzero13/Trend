# Safety-Strategien: vollständige Ergebnistabellen

Automatisch aus unveränderten lokalen Ergebnisdateien erstellt. USD, Kosten enthalten. Profil-/Familienfälle können abhängig sein und sind keine unabhängigen Trades. Vergleichswerte nutzen dieselben vollständig beobachteten Fälle je Horizont; unvollständige Pfade bleiben in der Fallübersicht sichtbar. Kein Holdout geöffnet.

## development

2083 Profil-/Familienfälle, 1299 eindeutige Aktie/Zeit/Familie-Ereignisse, 21 zulässige Fälle, 24996 Modellpfade.

### Gepaarter Einzelpositionsvergleich

| Profil | Familie | Gruppe | Tage | Modell | Alle / geschlossen | Gemeinsam N | Gewinnanteil % | Mittel netto % | Mittel netto R | ΔR zu fixed |
|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| baseline | breakout | all | 5 | fixed | 700 / 494 | 494 | 48.2 | 0.162 | 0.015 | 0.000 |
| baseline | breakout | all | 5 | original | 700 / 509 | 494 | 46.4 | 0.193 | 0.023 | 0.008 |
| baseline | breakout | all | 5 | structure | 700 / 511 | 494 | 46.0 | 0.195 | 0.022 | 0.007 |
| baseline | breakout | all | 5 | structure_target | 700 / 541 | 494 | 53.2 | -0.078 | -0.034 | -0.050 |
| baseline | breakout | all | 10 | fixed | 700 / 463 | 463 | 43.2 | 0.094 | 0.007 | 0.000 |
| baseline | breakout | all | 10 | original | 700 / 484 | 463 | 40.0 | 0.039 | -0.003 | -0.010 |
| baseline | breakout | all | 10 | structure | 700 / 488 | 463 | 39.5 | -0.021 | -0.017 | -0.024 |
| baseline | breakout | all | 10 | structure_target | 700 / 528 | 463 | 49.7 | -0.422 | -0.086 | -0.093 |
| baseline | breakout | all | 20 | fixed | 700 / 434 | 434 | 40.1 | 0.693 | 0.089 | 0.000 |
| baseline | breakout | all | 20 | original | 700 / 466 | 434 | 37.1 | 0.274 | 0.018 | -0.071 |
| baseline | breakout | all | 20 | structure | 700 / 474 | 434 | 35.0 | 0.112 | -0.021 | -0.111 |
| baseline | breakout | all | 20 | structure_target | 700 / 524 | 434 | 47.9 | -0.328 | -0.086 | -0.176 |
| baseline | breakout | eligible | 5 | fixed | 8 / 8 | 8 | 25.0 | -0.462 | -0.081 | 0.000 |
| baseline | breakout | eligible | 5 | original | 8 / 8 | 8 | 25.0 | 0.033 | 0.101 | 0.182 |
| baseline | breakout | eligible | 5 | structure | 8 / 8 | 8 | 12.5 | -0.209 | 0.004 | 0.084 |
| baseline | breakout | eligible | 5 | structure_target | 8 / 8 | 8 | 12.5 | -0.209 | 0.004 | 0.084 |
| baseline | breakout | eligible | 10 | fixed | 8 / 8 | 8 | 12.5 | -0.291 | 0.124 | 0.000 |
| baseline | breakout | eligible | 10 | original | 8 / 8 | 8 | 12.5 | 0.204 | 0.306 | 0.182 |
| baseline | breakout | eligible | 10 | structure | 8 / 8 | 8 | 12.5 | 0.330 | 0.357 | 0.232 |
| baseline | breakout | eligible | 10 | structure_target | 8 / 8 | 8 | 12.5 | 0.330 | 0.357 | 0.232 |
| baseline | breakout | eligible | 20 | fixed | 8 / 8 | 8 | 12.5 | -0.601 | -0.079 | 0.000 |
| baseline | breakout | eligible | 20 | original | 8 / 8 | 8 | 12.5 | -0.106 | 0.103 | 0.182 |
| baseline | breakout | eligible | 20 | structure | 8 / 8 | 8 | 12.5 | 0.020 | 0.154 | 0.232 |
| baseline | breakout | eligible | 20 | structure_target | 8 / 8 | 8 | 12.5 | 0.020 | 0.154 | 0.232 |
| baseline | horizontal | all | 5 | fixed | 331 / 242 | 242 | 48.3 | -0.053 | 0.016 | 0.000 |
| baseline | horizontal | all | 5 | original | 331 / 246 | 242 | 45.5 | -0.143 | -0.016 | -0.032 |
| baseline | horizontal | all | 5 | structure | 331 / 248 | 242 | 45.5 | -0.141 | -0.017 | -0.032 |
| baseline | horizontal | all | 5 | structure_target | 331 / 257 | 242 | 52.1 | -0.148 | -0.041 | -0.057 |
| baseline | horizontal | all | 10 | fixed | 331 / 221 | 221 | 45.7 | -0.175 | -0.005 | 0.000 |
| baseline | horizontal | all | 10 | original | 331 / 228 | 221 | 40.7 | -0.418 | -0.053 | -0.048 |
| baseline | horizontal | all | 10 | structure | 331 / 232 | 221 | 42.5 | -0.380 | -0.055 | -0.051 |
| baseline | horizontal | all | 10 | structure_target | 331 / 246 | 221 | 50.2 | -0.459 | -0.088 | -0.084 |
| baseline | horizontal | all | 20 | fixed | 331 / 214 | 214 | 43.9 | 0.775 | 0.106 | 0.000 |
| baseline | horizontal | all | 20 | original | 331 / 224 | 214 | 39.3 | 0.185 | 0.009 | -0.097 |
| baseline | horizontal | all | 20 | structure | 331 / 228 | 214 | 40.7 | 0.125 | -0.009 | -0.115 |
| baseline | horizontal | all | 20 | structure_target | 331 / 243 | 214 | 49.5 | -0.225 | -0.066 | -0.172 |
| baseline | horizontal | eligible | 5 | fixed | 1 / 1 | 1 | 0.0 | -0.869 | -1.094 | 0.000 |
| baseline | horizontal | eligible | 5 | original | 1 / 1 | 1 | 0.0 | -0.869 | -1.094 | 0.000 |
| baseline | horizontal | eligible | 5 | structure | 1 / 1 | 1 | 0.0 | -0.869 | -1.094 | 0.000 |
| baseline | horizontal | eligible | 5 | structure_target | 1 / 1 | 1 | 0.0 | -0.869 | -1.094 | 0.000 |
| baseline | horizontal | eligible | 10 | fixed | 1 / 1 | 1 | 0.0 | -0.869 | -1.094 | 0.000 |
| baseline | horizontal | eligible | 10 | original | 1 / 1 | 1 | 0.0 | -0.869 | -1.094 | 0.000 |
| baseline | horizontal | eligible | 10 | structure | 1 / 1 | 1 | 0.0 | -0.869 | -1.094 | 0.000 |
| baseline | horizontal | eligible | 10 | structure_target | 1 / 1 | 1 | 0.0 | -0.869 | -1.094 | 0.000 |
| baseline | horizontal | eligible | 20 | fixed | 1 / 1 | 1 | 0.0 | -0.869 | -1.094 | 0.000 |
| baseline | horizontal | eligible | 20 | original | 1 / 1 | 1 | 0.0 | -0.869 | -1.094 | 0.000 |
| baseline | horizontal | eligible | 20 | structure | 1 / 1 | 1 | 0.0 | -0.869 | -1.094 | 0.000 |
| baseline | horizontal | eligible | 20 | structure_target | 1 / 1 | 1 | 0.0 | -0.869 | -1.094 | 0.000 |
| baseline | retest | all | 5 | fixed | 201 / 144 | 144 | 51.4 | 0.523 | 0.161 | 0.000 |
| baseline | retest | all | 5 | original | 201 / 145 | 144 | 49.3 | 0.549 | 0.157 | -0.004 |
| baseline | retest | all | 5 | structure | 201 / 145 | 144 | 50.0 | 0.559 | 0.159 | -0.002 |
| baseline | retest | all | 5 | structure_target | 201 / 155 | 144 | 57.6 | 0.036 | 0.013 | -0.148 |
| baseline | retest | all | 10 | fixed | 201 / 139 | 139 | 50.4 | 0.870 | 0.180 | 0.000 |
| baseline | retest | all | 10 | original | 201 / 140 | 139 | 46.8 | 0.773 | 0.177 | -0.003 |
| baseline | retest | all | 10 | structure | 201 / 140 | 139 | 46.8 | 0.678 | 0.158 | -0.023 |
| baseline | retest | all | 10 | structure_target | 201 / 153 | 139 | 55.4 | 0.060 | 0.018 | -0.162 |
| baseline | retest | all | 20 | fixed | 201 / 131 | 131 | 41.2 | 0.905 | 0.187 | 0.000 |
| baseline | retest | all | 20 | original | 201 / 136 | 131 | 35.9 | 0.495 | 0.125 | -0.062 |
| baseline | retest | all | 20 | structure | 201 / 137 | 131 | 37.4 | 0.358 | 0.104 | -0.083 |
| baseline | retest | all | 20 | structure_target | 201 / 152 | 131 | 54.2 | -0.105 | -0.006 | -0.193 |
| baseline | retest | eligible | 5 | fixed | 7 / 5 | 5 | 0.0 | -1.790 | -1.049 | 0.000 |
| baseline | retest | eligible | 5 | original | 7 / 5 | 5 | 0.0 | -0.831 | -0.550 | 0.499 |
| baseline | retest | eligible | 5 | structure | 7 / 5 | 5 | 0.0 | -0.831 | -0.550 | 0.499 |
| baseline | retest | eligible | 5 | structure_target | 7 / 5 | 5 | 0.0 | -0.831 | -0.550 | 0.499 |
| baseline | retest | eligible | 10 | fixed | 7 / 5 | 5 | 0.0 | -1.790 | -1.049 | 0.000 |
| baseline | retest | eligible | 10 | original | 7 / 5 | 5 | 0.0 | -0.831 | -0.550 | 0.499 |
| baseline | retest | eligible | 10 | structure | 7 / 5 | 5 | 0.0 | -0.831 | -0.550 | 0.499 |
| baseline | retest | eligible | 10 | structure_target | 7 / 5 | 5 | 0.0 | -0.831 | -0.550 | 0.499 |
| baseline | retest | eligible | 20 | fixed | 7 / 5 | 5 | 0.0 | -1.790 | -1.049 | 0.000 |
| baseline | retest | eligible | 20 | original | 7 / 5 | 5 | 0.0 | -0.831 | -0.550 | 0.499 |
| baseline | retest | eligible | 20 | structure | 7 / 5 | 5 | 0.0 | -0.831 | -0.550 | 0.499 |
| baseline | retest | eligible | 20 | structure_target | 7 / 5 | 5 | 0.0 | -0.831 | -0.550 | 0.499 |
| momentum_two | breakout | all | 5 | fixed | 474 / 346 | 346 | 50.3 | 0.229 | 0.037 | 0.000 |
| momentum_two | breakout | all | 5 | original | 474 / 357 | 346 | 48.3 | 0.297 | 0.048 | 0.011 |
| momentum_two | breakout | all | 5 | structure | 474 / 359 | 346 | 47.7 | 0.297 | 0.046 | 0.009 |
| momentum_two | breakout | all | 5 | structure_target | 474 / 376 | 346 | 55.2 | 0.033 | -0.020 | -0.057 |
| momentum_two | breakout | all | 10 | fixed | 474 / 320 | 320 | 45.6 | 0.348 | 0.033 | 0.000 |
| momentum_two | breakout | all | 10 | original | 474 / 337 | 320 | 43.1 | 0.368 | 0.048 | 0.015 |
| momentum_two | breakout | all | 10 | structure | 474 / 341 | 320 | 42.5 | 0.327 | 0.039 | 0.006 |
| momentum_two | breakout | all | 10 | structure_target | 474 / 363 | 320 | 51.9 | -0.206 | -0.069 | -0.102 |
| momentum_two | breakout | all | 20 | fixed | 474 / 299 | 299 | 40.5 | 0.902 | 0.122 | 0.000 |
| momentum_two | breakout | all | 20 | original | 474 / 322 | 299 | 39.1 | 0.693 | 0.088 | -0.033 |
| momentum_two | breakout | all | 20 | structure | 474 / 329 | 299 | 36.5 | 0.519 | 0.048 | -0.073 |
| momentum_two | breakout | all | 20 | structure_target | 474 / 360 | 299 | 49.8 | -0.135 | -0.062 | -0.184 |
| momentum_two | breakout | eligible | 5 | fixed | 1 / 1 | 1 | 100.0 | 0.388 | 0.156 | 0.000 |
| momentum_two | breakout | eligible | 5 | original | 1 / 1 | 1 | 100.0 | 0.388 | 0.156 | 0.000 |
| momentum_two | breakout | eligible | 5 | structure | 1 / 1 | 1 | 0.0 | -1.555 | -0.626 | -0.782 |
| momentum_two | breakout | eligible | 5 | structure_target | 1 / 1 | 1 | 0.0 | -1.555 | -0.626 | -0.782 |
| momentum_two | breakout | eligible | 10 | fixed | 1 / 1 | 1 | 0.0 | -2.559 | -1.029 | 0.000 |
| momentum_two | breakout | eligible | 10 | original | 1 / 1 | 1 | 0.0 | -2.559 | -1.029 | 0.000 |
| momentum_two | breakout | eligible | 10 | structure | 1 / 1 | 1 | 0.0 | -1.555 | -0.626 | 0.404 |
| momentum_two | breakout | eligible | 10 | structure_target | 1 / 1 | 1 | 0.0 | -1.555 | -0.626 | 0.404 |
| momentum_two | breakout | eligible | 20 | fixed | 1 / 1 | 1 | 0.0 | -2.559 | -1.029 | 0.000 |
| momentum_two | breakout | eligible | 20 | original | 1 / 1 | 1 | 0.0 | -2.559 | -1.029 | 0.000 |
| momentum_two | breakout | eligible | 20 | structure | 1 / 1 | 1 | 0.0 | -1.555 | -0.626 | 0.404 |
| momentum_two | breakout | eligible | 20 | structure_target | 1 / 1 | 1 | 0.0 | -1.555 | -0.626 | 0.404 |
| momentum_two | horizontal | all | 5 | fixed | 297 / 216 | 216 | 47.2 | -0.236 | -0.034 | 0.000 |
| momentum_two | horizontal | all | 5 | original | 297 / 220 | 216 | 44.4 | -0.274 | -0.042 | -0.008 |
| momentum_two | horizontal | all | 5 | structure | 297 / 222 | 216 | 44.4 | -0.282 | -0.045 | -0.011 |
| momentum_two | horizontal | all | 5 | structure_target | 297 / 231 | 216 | 51.4 | -0.275 | -0.066 | -0.031 |
| momentum_two | horizontal | all | 10 | fixed | 297 / 198 | 198 | 45.5 | -0.374 | -0.049 | 0.000 |
| momentum_two | horizontal | all | 10 | original | 297 / 205 | 198 | 40.9 | -0.610 | -0.071 | -0.022 |
| momentum_two | horizontal | all | 10 | structure | 297 / 209 | 198 | 41.4 | -0.639 | -0.087 | -0.038 |
| momentum_two | horizontal | all | 10 | structure_target | 297 / 221 | 198 | 48.5 | -0.627 | -0.113 | -0.063 |
| momentum_two | horizontal | all | 20 | fixed | 297 / 192 | 192 | 41.7 | 0.551 | 0.075 | 0.000 |
| momentum_two | horizontal | all | 20 | original | 297 / 201 | 192 | 37.5 | 0.150 | 0.020 | -0.055 |
| momentum_two | horizontal | all | 20 | structure | 297 / 205 | 192 | 37.5 | -0.046 | -0.022 | -0.097 |
| momentum_two | horizontal | all | 20 | structure_target | 297 / 218 | 192 | 47.4 | -0.289 | -0.069 | -0.145 |
| momentum_two | horizontal | eligible | 5 | fixed | 2 / 1 | 1 | 0.0 | -2.707 | -1.028 | 0.000 |
| momentum_two | horizontal | eligible | 5 | original | 2 / 1 | 1 | 0.0 | -0.582 | -0.221 | 0.807 |
| momentum_two | horizontal | eligible | 5 | structure | 2 / 1 | 1 | 0.0 | -0.582 | -0.221 | 0.807 |
| momentum_two | horizontal | eligible | 5 | structure_target | 2 / 1 | 1 | 0.0 | -0.582 | -0.221 | 0.807 |
| momentum_two | horizontal | eligible | 10 | fixed | 2 / 1 | 1 | 0.0 | -2.707 | -1.028 | 0.000 |
| momentum_two | horizontal | eligible | 10 | original | 2 / 1 | 1 | 0.0 | -0.582 | -0.221 | 0.807 |
| momentum_two | horizontal | eligible | 10 | structure | 2 / 1 | 1 | 0.0 | -0.582 | -0.221 | 0.807 |
| momentum_two | horizontal | eligible | 10 | structure_target | 2 / 1 | 1 | 0.0 | -0.582 | -0.221 | 0.807 |
| momentum_two | horizontal | eligible | 20 | fixed | 2 / 1 | 1 | 0.0 | -2.707 | -1.028 | 0.000 |
| momentum_two | horizontal | eligible | 20 | original | 2 / 1 | 1 | 0.0 | -0.582 | -0.221 | 0.807 |
| momentum_two | horizontal | eligible | 20 | structure | 2 / 1 | 1 | 0.0 | -0.582 | -0.221 | 0.807 |
| momentum_two | horizontal | eligible | 20 | structure_target | 2 / 1 | 1 | 0.0 | -0.582 | -0.221 | 0.807 |
| momentum_two | retest | all | 5 | fixed | 80 / 55 | 55 | 47.3 | 0.087 | 0.016 | 0.000 |
| momentum_two | retest | all | 5 | original | 80 / 55 | 55 | 47.3 | 0.070 | 0.033 | 0.017 |
| momentum_two | retest | all | 5 | structure | 80 / 55 | 55 | 47.3 | 0.081 | 0.035 | 0.019 |
| momentum_two | retest | all | 5 | structure_target | 80 / 59 | 55 | 56.4 | -0.136 | -0.012 | -0.027 |
| momentum_two | retest | all | 10 | fixed | 80 / 52 | 52 | 51.9 | 0.631 | 0.122 | 0.000 |
| momentum_two | retest | all | 10 | original | 80 / 52 | 52 | 50.0 | 0.505 | 0.126 | 0.004 |
| momentum_two | retest | all | 10 | structure | 80 / 52 | 52 | 51.9 | 0.581 | 0.135 | 0.013 |
| momentum_two | retest | all | 10 | structure_target | 80 / 58 | 52 | 63.5 | 0.127 | 0.012 | -0.110 |
| momentum_two | retest | all | 20 | fixed | 80 / 50 | 50 | 48.0 | 0.936 | 0.152 | 0.000 |
| momentum_two | retest | all | 20 | original | 80 / 51 | 50 | 40.0 | 0.038 | 0.001 | -0.152 |
| momentum_two | retest | all | 20 | structure | 80 / 51 | 50 | 44.0 | 0.144 | 0.023 | -0.130 |
| momentum_two | retest | all | 20 | structure_target | 80 / 58 | 50 | 60.0 | 0.325 | 0.006 | -0.147 |
| momentum_two | retest | eligible | 5 | fixed | 2 / 1 | 1 | 0.0 | -0.869 | -1.094 | 0.000 |
| momentum_two | retest | eligible | 5 | original | 2 / 1 | 1 | 0.0 | -0.869 | -1.094 | 0.000 |
| momentum_two | retest | eligible | 5 | structure | 2 / 1 | 1 | 0.0 | -0.869 | -1.094 | 0.000 |
| momentum_two | retest | eligible | 5 | structure_target | 2 / 1 | 1 | 0.0 | -0.869 | -1.094 | 0.000 |
| momentum_two | retest | eligible | 10 | fixed | 2 / 1 | 1 | 0.0 | -0.869 | -1.094 | 0.000 |
| momentum_two | retest | eligible | 10 | original | 2 / 1 | 1 | 0.0 | -0.869 | -1.094 | 0.000 |
| momentum_two | retest | eligible | 10 | structure | 2 / 1 | 1 | 0.0 | -0.869 | -1.094 | 0.000 |
| momentum_two | retest | eligible | 10 | structure_target | 2 / 1 | 1 | 0.0 | -0.869 | -1.094 | 0.000 |
| momentum_two | retest | eligible | 20 | fixed | 2 / 1 | 1 | 0.0 | -0.869 | -1.094 | 0.000 |
| momentum_two | retest | eligible | 20 | original | 2 / 1 | 1 | 0.0 | -0.869 | -1.094 | 0.000 |
| momentum_two | retest | eligible | 20 | structure | 2 / 1 | 1 | 0.0 | -0.869 | -1.094 | 0.000 |
| momentum_two | retest | eligible | 20 | structure_target | 2 / 1 | 1 | 0.0 | -0.869 | -1.094 | 0.000 |

### Kapitalbegrenzte Portfolios

Bei `incomplete` ist das angegebene Vermögen nur der beobachtete Präfix; keine volle Phasenrendite. `marked_to_phase_end` kann offene Positionen enthalten. Leere Portfolios sind kein Strategieerfolg.

| Profil | Familie | Gruppe | Tage | Modell | Status | Käufe / geschlossen / offen | Vermögen USD | Phasenrendite % | Realisiert USD | 5m-Drawdown % |
|---|---|---|---:|---|---|---:|---:|---:|---:|---:|
| baseline | breakout | all | 5 | fixed | incomplete | 5 / 0 / 5 | 2001.31 | — | 0.00 | -0.555 |
| baseline | breakout | all | 5 | original | incomplete | 5 / 0 / 5 | 2001.31 | — | 0.00 | -0.555 |
| baseline | breakout | all | 5 | structure | incomplete | 5 / 0 / 5 | 2001.31 | — | 0.00 | -0.555 |
| baseline | breakout | all | 5 | structure_target | incomplete | 5 / 1 / 4 | 2002.04 | — | 2.58 | -0.555 |
| baseline | breakout | all | 10 | fixed | incomplete | 5 / 0 / 5 | 2001.31 | — | 0.00 | -0.555 |
| baseline | breakout | all | 10 | original | incomplete | 5 / 0 / 5 | 2001.31 | — | 0.00 | -0.555 |
| baseline | breakout | all | 10 | structure | incomplete | 5 / 0 / 5 | 2001.31 | — | 0.00 | -0.555 |
| baseline | breakout | all | 10 | structure_target | incomplete | 5 / 1 / 4 | 2002.04 | — | 2.58 | -0.555 |
| baseline | breakout | all | 20 | fixed | incomplete | 5 / 0 / 5 | 2001.31 | — | 0.00 | -0.555 |
| baseline | breakout | all | 20 | original | incomplete | 5 / 0 / 5 | 2001.31 | — | 0.00 | -0.555 |
| baseline | breakout | all | 20 | structure | incomplete | 5 / 0 / 5 | 2001.31 | — | 0.00 | -0.555 |
| baseline | breakout | all | 20 | structure_target | incomplete | 5 / 1 / 4 | 2002.04 | — | 2.58 | -0.555 |
| baseline | breakout | eligible | 5 | fixed | marked_to_phase_end | 7 / 7 / 0 | 1997.36 | -0.132 | -2.64 | -2.741 |
| baseline | breakout | eligible | 5 | original | marked_to_phase_end | 7 / 7 / 0 | 2017.42 | 0.871 | 17.42 | -1.765 |
| baseline | breakout | eligible | 5 | structure | marked_to_phase_end | 7 / 7 / 0 | 2007.62 | 0.381 | 7.62 | -2.005 |
| baseline | breakout | eligible | 5 | structure_target | marked_to_phase_end | 7 / 7 / 0 | 2007.62 | 0.381 | 7.62 | -2.005 |
| baseline | breakout | eligible | 10 | fixed | marked_to_phase_end | 7 / 7 / 0 | 2003.51 | 0.176 | 3.51 | -3.224 |
| baseline | breakout | eligible | 10 | original | marked_to_phase_end | 7 / 7 / 0 | 2023.62 | 1.181 | 23.62 | -2.252 |
| baseline | breakout | eligible | 10 | structure | marked_to_phase_end | 7 / 7 / 0 | 2028.74 | 1.437 | 28.74 | -2.005 |
| baseline | breakout | eligible | 10 | structure_target | marked_to_phase_end | 7 / 7 / 0 | 2028.74 | 1.437 | 28.74 | -2.005 |
| baseline | breakout | eligible | 20 | fixed | marked_to_phase_end | 7 / 7 / 0 | 1991.55 | -0.423 | -8.45 | -3.224 |
| baseline | breakout | eligible | 20 | original | marked_to_phase_end | 7 / 7 / 0 | 2011.54 | 0.577 | 11.54 | -2.252 |
| baseline | breakout | eligible | 20 | structure | marked_to_phase_end | 7 / 7 / 0 | 2016.62 | 0.831 | 16.62 | -2.005 |
| baseline | breakout | eligible | 20 | structure_target | marked_to_phase_end | 7 / 7 / 0 | 2016.62 | 0.831 | 16.62 | -2.005 |
| baseline | horizontal | all | 5 | fixed | incomplete | 3 / 0 / 3 | 2002.01 | — | 0.00 | -0.533 |
| baseline | horizontal | all | 5 | original | incomplete | 3 / 0 / 3 | 2002.01 | — | 0.00 | -0.533 |
| baseline | horizontal | all | 5 | structure | incomplete | 3 / 0 / 3 | 2002.01 | — | 0.00 | -0.533 |
| baseline | horizontal | all | 5 | structure_target | incomplete | 5 / 1 / 4 | 2000.08 | — | 2.58 | -0.533 |
| baseline | horizontal | all | 10 | fixed | incomplete | 3 / 0 / 3 | 2002.01 | — | 0.00 | -0.533 |
| baseline | horizontal | all | 10 | original | incomplete | 3 / 0 / 3 | 2002.01 | — | 0.00 | -0.533 |
| baseline | horizontal | all | 10 | structure | incomplete | 3 / 0 / 3 | 2002.01 | — | 0.00 | -0.533 |
| baseline | horizontal | all | 10 | structure_target | incomplete | 5 / 1 / 4 | 2000.08 | — | 2.58 | -0.533 |
| baseline | horizontal | all | 20 | fixed | incomplete | 3 / 0 / 3 | 2002.01 | — | 0.00 | -0.533 |
| baseline | horizontal | all | 20 | original | incomplete | 3 / 0 / 3 | 2002.01 | — | 0.00 | -0.533 |
| baseline | horizontal | all | 20 | structure | incomplete | 3 / 0 / 3 | 2002.01 | — | 0.00 | -0.533 |
| baseline | horizontal | all | 20 | structure_target | incomplete | 5 / 1 / 4 | 2000.08 | — | 2.58 | -0.533 |
| baseline | horizontal | eligible | 5 | fixed | marked_to_phase_end | 1 / 1 / 0 | 1995.65 | -0.217 | -4.35 | -0.217 |
| baseline | horizontal | eligible | 5 | original | marked_to_phase_end | 1 / 1 / 0 | 1995.65 | -0.217 | -4.35 | -0.217 |
| baseline | horizontal | eligible | 5 | structure | marked_to_phase_end | 1 / 1 / 0 | 1995.65 | -0.217 | -4.35 | -0.217 |
| baseline | horizontal | eligible | 5 | structure_target | marked_to_phase_end | 1 / 1 / 0 | 1995.65 | -0.217 | -4.35 | -0.217 |
| baseline | horizontal | eligible | 10 | fixed | marked_to_phase_end | 1 / 1 / 0 | 1995.65 | -0.217 | -4.35 | -0.217 |
| baseline | horizontal | eligible | 10 | original | marked_to_phase_end | 1 / 1 / 0 | 1995.65 | -0.217 | -4.35 | -0.217 |
| baseline | horizontal | eligible | 10 | structure | marked_to_phase_end | 1 / 1 / 0 | 1995.65 | -0.217 | -4.35 | -0.217 |
| baseline | horizontal | eligible | 10 | structure_target | marked_to_phase_end | 1 / 1 / 0 | 1995.65 | -0.217 | -4.35 | -0.217 |
| baseline | horizontal | eligible | 20 | fixed | marked_to_phase_end | 1 / 1 / 0 | 1995.65 | -0.217 | -4.35 | -0.217 |
| baseline | horizontal | eligible | 20 | original | marked_to_phase_end | 1 / 1 / 0 | 1995.65 | -0.217 | -4.35 | -0.217 |
| baseline | horizontal | eligible | 20 | structure | marked_to_phase_end | 1 / 1 / 0 | 1995.65 | -0.217 | -4.35 | -0.217 |
| baseline | horizontal | eligible | 20 | structure_target | marked_to_phase_end | 1 / 1 / 0 | 1995.65 | -0.217 | -4.35 | -0.217 |
| baseline | retest | all | 5 | fixed | incomplete | 3 / 1 / 2 | 1985.36 | — | -18.82 | -1.480 |
| baseline | retest | all | 5 | original | incomplete | 3 / 1 / 2 | 1985.36 | — | -18.82 | -1.480 |
| baseline | retest | all | 5 | structure | incomplete | 3 / 1 / 2 | 1985.36 | — | -18.82 | -1.480 |
| baseline | retest | all | 5 | structure_target | incomplete | 3 / 1 / 2 | 1985.36 | — | -18.82 | -1.480 |
| baseline | retest | all | 10 | fixed | incomplete | 3 / 1 / 2 | 1985.36 | — | -18.82 | -1.480 |
| baseline | retest | all | 10 | original | incomplete | 3 / 1 / 2 | 1985.36 | — | -18.82 | -1.480 |
| baseline | retest | all | 10 | structure | incomplete | 3 / 1 / 2 | 1985.36 | — | -18.82 | -1.480 |
| baseline | retest | all | 10 | structure_target | incomplete | 3 / 1 / 2 | 1985.36 | — | -18.82 | -1.480 |
| baseline | retest | all | 20 | fixed | incomplete | 3 / 1 / 2 | 1985.36 | — | -18.82 | -1.480 |
| baseline | retest | all | 20 | original | incomplete | 3 / 1 / 2 | 1985.36 | — | -18.82 | -1.480 |
| baseline | retest | all | 20 | structure | incomplete | 3 / 1 / 2 | 1985.36 | — | -18.82 | -1.480 |
| baseline | retest | all | 20 | structure_target | incomplete | 3 / 1 / 2 | 1985.36 | — | -18.82 | -1.480 |
| baseline | retest | eligible | 5 | fixed | incomplete | 1 / 0 / 1 | 2007.63 | — | 0.00 | -0.185 |
| baseline | retest | eligible | 5 | original | incomplete | 1 / 0 / 1 | 2007.63 | — | 0.00 | -0.185 |
| baseline | retest | eligible | 5 | structure | incomplete | 1 / 0 / 1 | 2007.63 | — | 0.00 | -0.185 |
| baseline | retest | eligible | 5 | structure_target | incomplete | 1 / 0 / 1 | 2007.63 | — | 0.00 | -0.185 |
| baseline | retest | eligible | 10 | fixed | incomplete | 1 / 0 / 1 | 2007.63 | — | 0.00 | -0.185 |
| baseline | retest | eligible | 10 | original | incomplete | 1 / 0 / 1 | 2007.63 | — | 0.00 | -0.185 |
| baseline | retest | eligible | 10 | structure | incomplete | 1 / 0 / 1 | 2007.63 | — | 0.00 | -0.185 |
| baseline | retest | eligible | 10 | structure_target | incomplete | 1 / 0 / 1 | 2007.63 | — | 0.00 | -0.185 |
| baseline | retest | eligible | 20 | fixed | incomplete | 1 / 0 / 1 | 2007.63 | — | 0.00 | -0.185 |
| baseline | retest | eligible | 20 | original | incomplete | 1 / 0 / 1 | 2007.63 | — | 0.00 | -0.185 |
| baseline | retest | eligible | 20 | structure | incomplete | 1 / 0 / 1 | 2007.63 | — | 0.00 | -0.185 |
| baseline | retest | eligible | 20 | structure_target | incomplete | 1 / 0 / 1 | 2007.63 | — | 0.00 | -0.185 |
| momentum_two | breakout | all | 5 | fixed | incomplete | 4 / 0 / 4 | 1997.50 | — | 0.00 | -0.527 |
| momentum_two | breakout | all | 5 | original | incomplete | 4 / 0 / 4 | 1997.50 | — | 0.00 | -0.527 |
| momentum_two | breakout | all | 5 | structure | incomplete | 4 / 0 / 4 | 1997.50 | — | 0.00 | -0.527 |
| momentum_two | breakout | all | 5 | structure_target | incomplete | 4 / 0 / 4 | 1997.50 | — | 0.00 | -0.527 |
| momentum_two | breakout | all | 10 | fixed | incomplete | 4 / 0 / 4 | 1997.50 | — | 0.00 | -0.527 |
| momentum_two | breakout | all | 10 | original | incomplete | 4 / 0 / 4 | 1997.50 | — | 0.00 | -0.527 |
| momentum_two | breakout | all | 10 | structure | incomplete | 4 / 0 / 4 | 1997.50 | — | 0.00 | -0.527 |
| momentum_two | breakout | all | 10 | structure_target | incomplete | 4 / 0 / 4 | 1997.50 | — | 0.00 | -0.527 |
| momentum_two | breakout | all | 20 | fixed | incomplete | 4 / 0 / 4 | 1997.50 | — | 0.00 | -0.527 |
| momentum_two | breakout | all | 20 | original | incomplete | 4 / 0 / 4 | 1997.50 | — | 0.00 | -0.527 |
| momentum_two | breakout | all | 20 | structure | incomplete | 4 / 0 / 4 | 1997.50 | — | 0.00 | -0.527 |
| momentum_two | breakout | all | 20 | structure_target | incomplete | 4 / 0 / 4 | 1997.50 | — | 0.00 | -0.527 |
| momentum_two | breakout | eligible | 5 | fixed | marked_to_phase_end | 1 / 1 / 0 | 2001.94 | 0.097 | 1.94 | -0.762 |
| momentum_two | breakout | eligible | 5 | original | marked_to_phase_end | 1 / 1 / 0 | 2001.94 | 0.097 | 1.94 | -0.762 |
| momentum_two | breakout | eligible | 5 | structure | marked_to_phase_end | 1 / 1 / 0 | 1992.22 | -0.389 | -7.78 | -0.775 |
| momentum_two | breakout | eligible | 5 | structure_target | marked_to_phase_end | 1 / 1 / 0 | 1992.22 | -0.389 | -7.78 | -0.775 |
| momentum_two | breakout | eligible | 10 | fixed | marked_to_phase_end | 1 / 1 / 0 | 1987.20 | -0.640 | -12.80 | -1.025 |
| momentum_two | breakout | eligible | 10 | original | marked_to_phase_end | 1 / 1 / 0 | 1987.20 | -0.640 | -12.80 | -1.025 |
| momentum_two | breakout | eligible | 10 | structure | marked_to_phase_end | 1 / 1 / 0 | 1992.22 | -0.389 | -7.78 | -0.775 |
| momentum_two | breakout | eligible | 10 | structure_target | marked_to_phase_end | 1 / 1 / 0 | 1992.22 | -0.389 | -7.78 | -0.775 |
| momentum_two | breakout | eligible | 20 | fixed | marked_to_phase_end | 1 / 1 / 0 | 1987.20 | -0.640 | -12.80 | -1.025 |
| momentum_two | breakout | eligible | 20 | original | marked_to_phase_end | 1 / 1 / 0 | 1987.20 | -0.640 | -12.80 | -1.025 |
| momentum_two | breakout | eligible | 20 | structure | marked_to_phase_end | 1 / 1 / 0 | 1992.22 | -0.389 | -7.78 | -0.775 |
| momentum_two | breakout | eligible | 20 | structure_target | marked_to_phase_end | 1 / 1 / 0 | 1992.22 | -0.389 | -7.78 | -0.775 |
| momentum_two | horizontal | all | 5 | fixed | incomplete | 5 / 0 / 5 | 1997.14 | — | 0.00 | -0.527 |
| momentum_two | horizontal | all | 5 | original | incomplete | 5 / 0 / 5 | 1997.14 | — | 0.00 | -0.527 |
| momentum_two | horizontal | all | 5 | structure | incomplete | 5 / 0 / 5 | 1997.14 | — | 0.00 | -0.527 |
| momentum_two | horizontal | all | 5 | structure_target | incomplete | 5 / 0 / 5 | 1997.14 | — | 0.00 | -0.527 |
| momentum_two | horizontal | all | 10 | fixed | incomplete | 5 / 0 / 5 | 1997.14 | — | 0.00 | -0.527 |
| momentum_two | horizontal | all | 10 | original | incomplete | 5 / 0 / 5 | 1997.14 | — | 0.00 | -0.527 |
| momentum_two | horizontal | all | 10 | structure | incomplete | 5 / 0 / 5 | 1997.14 | — | 0.00 | -0.527 |
| momentum_two | horizontal | all | 10 | structure_target | incomplete | 5 / 0 / 5 | 1997.14 | — | 0.00 | -0.527 |
| momentum_two | horizontal | all | 20 | fixed | incomplete | 5 / 0 / 5 | 1997.14 | — | 0.00 | -0.527 |
| momentum_two | horizontal | all | 20 | original | incomplete | 5 / 0 / 5 | 1997.14 | — | 0.00 | -0.527 |
| momentum_two | horizontal | all | 20 | structure | incomplete | 5 / 0 / 5 | 1997.14 | — | 0.00 | -0.527 |
| momentum_two | horizontal | all | 20 | structure_target | incomplete | 5 / 0 / 5 | 1997.14 | — | 0.00 | -0.527 |
| momentum_two | horizontal | eligible | 5 | fixed | incomplete | 1 / 0 / 1 | 1999.75 | — | 0.00 | -0.384 |
| momentum_two | horizontal | eligible | 5 | original | incomplete | 1 / 0 / 1 | 1999.75 | — | 0.00 | -0.384 |
| momentum_two | horizontal | eligible | 5 | structure | incomplete | 1 / 0 / 1 | 1999.75 | — | 0.00 | -0.384 |
| momentum_two | horizontal | eligible | 5 | structure_target | incomplete | 1 / 0 / 1 | 1999.75 | — | 0.00 | -0.384 |
| momentum_two | horizontal | eligible | 10 | fixed | incomplete | 1 / 0 / 1 | 1999.75 | — | 0.00 | -0.384 |
| momentum_two | horizontal | eligible | 10 | original | incomplete | 1 / 0 / 1 | 1999.75 | — | 0.00 | -0.384 |
| momentum_two | horizontal | eligible | 10 | structure | incomplete | 1 / 0 / 1 | 1999.75 | — | 0.00 | -0.384 |
| momentum_two | horizontal | eligible | 10 | structure_target | incomplete | 1 / 0 / 1 | 1999.75 | — | 0.00 | -0.384 |
| momentum_two | horizontal | eligible | 20 | fixed | incomplete | 1 / 0 / 1 | 1999.75 | — | 0.00 | -0.384 |
| momentum_two | horizontal | eligible | 20 | original | incomplete | 1 / 0 / 1 | 1999.75 | — | 0.00 | -0.384 |
| momentum_two | horizontal | eligible | 20 | structure | incomplete | 1 / 0 / 1 | 1999.75 | — | 0.00 | -0.384 |
| momentum_two | horizontal | eligible | 20 | structure_target | incomplete | 1 / 0 / 1 | 1999.75 | — | 0.00 | -0.384 |
| momentum_two | retest | all | 5 | fixed | incomplete | 2 / 0 / 2 | 2003.33 | — | 0.00 | -0.176 |
| momentum_two | retest | all | 5 | original | incomplete | 2 / 0 / 2 | 2003.33 | — | 0.00 | -0.176 |
| momentum_two | retest | all | 5 | structure | incomplete | 2 / 0 / 2 | 2003.33 | — | 0.00 | -0.176 |
| momentum_two | retest | all | 5 | structure_target | incomplete | 2 / 1 / 1 | 2004.03 | — | 3.12 | -0.071 |
| momentum_two | retest | all | 10 | fixed | incomplete | 2 / 0 / 2 | 2003.33 | — | 0.00 | -0.176 |
| momentum_two | retest | all | 10 | original | incomplete | 2 / 0 / 2 | 2003.33 | — | 0.00 | -0.176 |
| momentum_two | retest | all | 10 | structure | incomplete | 2 / 0 / 2 | 2003.33 | — | 0.00 | -0.176 |
| momentum_two | retest | all | 10 | structure_target | incomplete | 2 / 1 / 1 | 2004.03 | — | 3.12 | -0.071 |
| momentum_two | retest | all | 20 | fixed | incomplete | 2 / 0 / 2 | 2003.33 | — | 0.00 | -0.176 |
| momentum_two | retest | all | 20 | original | incomplete | 2 / 0 / 2 | 2003.33 | — | 0.00 | -0.176 |
| momentum_two | retest | all | 20 | structure | incomplete | 2 / 0 / 2 | 2003.33 | — | 0.00 | -0.176 |
| momentum_two | retest | all | 20 | structure_target | incomplete | 2 / 1 / 1 | 2004.03 | — | 3.12 | -0.071 |
| momentum_two | retest | eligible | 5 | fixed | incomplete | 2 / 1 / 1 | 1997.84 | — | -4.35 | -0.236 |
| momentum_two | retest | eligible | 5 | original | incomplete | 2 / 1 / 1 | 1997.84 | — | -4.35 | -0.236 |
| momentum_two | retest | eligible | 5 | structure | incomplete | 2 / 1 / 1 | 1997.84 | — | -4.35 | -0.236 |
| momentum_two | retest | eligible | 5 | structure_target | incomplete | 2 / 1 / 1 | 1997.84 | — | -4.35 | -0.236 |
| momentum_two | retest | eligible | 10 | fixed | incomplete | 2 / 1 / 1 | 1997.84 | — | -4.35 | -0.236 |
| momentum_two | retest | eligible | 10 | original | incomplete | 2 / 1 / 1 | 1997.84 | — | -4.35 | -0.236 |
| momentum_two | retest | eligible | 10 | structure | incomplete | 2 / 1 / 1 | 1997.84 | — | -4.35 | -0.236 |
| momentum_two | retest | eligible | 10 | structure_target | incomplete | 2 / 1 / 1 | 1997.84 | — | -4.35 | -0.236 |
| momentum_two | retest | eligible | 20 | fixed | incomplete | 2 / 1 / 1 | 1997.84 | — | -4.35 | -0.236 |
| momentum_two | retest | eligible | 20 | original | incomplete | 2 / 1 / 1 | 1997.84 | — | -4.35 | -0.236 |
| momentum_two | retest | eligible | 20 | structure | incomplete | 2 / 1 / 1 | 1997.84 | — | -4.35 | -0.236 |
| momentum_two | retest | eligible | 20 | structure_target | incomplete | 2 / 1 / 1 | 1997.84 | — | -4.35 | -0.236 |

### Gleichbleibende Fallmenge über alle Modelle und Horizonte

Nur Fälle mit vollständigem Pfad in allen vier Modellen und allen drei Horizonten. Hier zur Übersicht 20 Tage, Referenzprofil, ungefiltert. Diese verfügbare Teilmenge kann Selektionsverzerrung enthalten.

| Familie | Modell | N | Mittel netto % | Mittel netto R |
|---|---|---:|---:|---:|
| breakout | fixed | 434 | 0.693 | 0.089 |
| breakout | original | 434 | 0.274 | 0.018 |
| breakout | structure | 434 | 0.112 | -0.021 |
| breakout | structure_target | 434 | -0.328 | -0.086 |
| horizontal | fixed | 214 | 0.775 | 0.106 |
| horizontal | original | 214 | 0.185 | 0.009 |
| horizontal | structure | 214 | 0.125 | -0.009 |
| horizontal | structure_target | 214 | -0.225 | -0.066 |
| retest | fixed | 131 | 0.905 | 0.187 |
| retest | original | 131 | 0.495 | 0.125 |
| retest | structure | 131 | 0.358 | 0.104 |
| retest | structure_target | 131 | -0.105 | -0.006 |

Blockierte Eintrittsprüfungen (Mehrfachnennungen): `daily_context`: 531, `fresh_daily`: 253, `fresh_weekly`: 582, `line_age`: 193, `net_room`: 1948, `risk_atr`: 1833, `weekly_context`: 907

## validation

840 Profil-/Familienfälle, 529 eindeutige Aktie/Zeit/Familie-Ereignisse, 7 zulässige Fälle, 10080 Modellpfade.

### Gepaarter Einzelpositionsvergleich

| Profil | Familie | Gruppe | Tage | Modell | Alle / geschlossen | Gemeinsam N | Gewinnanteil % | Mittel netto % | Mittel netto R | ΔR zu fixed |
|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| baseline | breakout | all | 5 | fixed | 287 / 216 | 216 | 52.3 | 0.887 | 0.093 | 0.000 |
| baseline | breakout | all | 5 | original | 287 / 218 | 216 | 49.5 | 0.818 | 0.046 | -0.047 |
| baseline | breakout | all | 5 | structure | 287 / 218 | 216 | 50.0 | 0.829 | 0.048 | -0.045 |
| baseline | breakout | all | 5 | structure_target | 287 / 238 | 216 | 56.5 | 0.388 | 0.007 | -0.085 |
| baseline | breakout | all | 10 | fixed | 287 / 201 | 201 | 53.7 | 1.780 | 0.233 | 0.000 |
| baseline | breakout | all | 10 | original | 287 / 206 | 201 | 45.3 | 1.203 | 0.075 | -0.158 |
| baseline | breakout | all | 10 | structure | 287 / 206 | 201 | 45.3 | 1.153 | 0.073 | -0.159 |
| baseline | breakout | all | 10 | structure_target | 287 / 234 | 201 | 53.7 | 0.618 | 0.004 | -0.229 |
| baseline | breakout | all | 20 | fixed | 287 / 167 | 167 | 44.9 | 3.860 | 0.520 | 0.000 |
| baseline | breakout | all | 20 | original | 287 / 182 | 167 | 39.5 | 2.680 | 0.252 | -0.269 |
| baseline | breakout | all | 20 | structure | 287 / 188 | 167 | 40.7 | 2.688 | 0.269 | -0.251 |
| baseline | breakout | all | 20 | structure_target | 287 / 226 | 167 | 50.9 | 1.397 | 0.104 | -0.416 |
| baseline | breakout | eligible | 5 | fixed | 4 / 4 | 4 | 25.0 | -2.971 | -0.862 | 0.000 |
| baseline | breakout | eligible | 5 | original | 4 / 4 | 4 | 25.0 | -2.317 | -0.588 | 0.275 |
| baseline | breakout | eligible | 5 | structure | 4 / 4 | 4 | 25.0 | -2.317 | -0.588 | 0.275 |
| baseline | breakout | eligible | 5 | structure_target | 4 / 4 | 4 | 25.0 | -2.317 | -0.588 | 0.275 |
| baseline | breakout | eligible | 10 | fixed | 4 / 3 | 3 | 0.0 | -5.224 | -1.634 | 0.000 |
| baseline | breakout | eligible | 10 | original | 4 / 3 | 3 | 0.0 | -4.352 | -1.267 | 0.366 |
| baseline | breakout | eligible | 10 | structure | 4 / 3 | 3 | 0.0 | -4.352 | -1.267 | 0.366 |
| baseline | breakout | eligible | 10 | structure_target | 4 / 4 | 3 | 0.0 | -4.352 | -1.267 | 0.366 |
| baseline | breakout | eligible | 20 | fixed | 4 / 3 | 3 | 0.0 | -5.224 | -1.634 | 0.000 |
| baseline | breakout | eligible | 20 | original | 4 / 3 | 3 | 0.0 | -4.352 | -1.267 | 0.366 |
| baseline | breakout | eligible | 20 | structure | 4 / 3 | 3 | 0.0 | -4.352 | -1.267 | 0.366 |
| baseline | breakout | eligible | 20 | structure_target | 4 / 4 | 3 | 0.0 | -4.352 | -1.267 | 0.366 |
| baseline | horizontal | all | 5 | fixed | 148 / 113 | 113 | 53.1 | 1.249 | 0.100 | 0.000 |
| baseline | horizontal | all | 5 | original | 148 / 115 | 113 | 49.6 | 1.119 | 0.050 | -0.050 |
| baseline | horizontal | all | 5 | structure | 148 / 115 | 113 | 49.6 | 1.126 | 0.051 | -0.049 |
| baseline | horizontal | all | 5 | structure_target | 148 / 121 | 113 | 53.1 | 0.360 | -0.000 | -0.100 |
| baseline | horizontal | all | 10 | fixed | 148 / 108 | 108 | 60.2 | 2.628 | 0.265 | 0.000 |
| baseline | horizontal | all | 10 | original | 148 / 110 | 108 | 50.0 | 1.965 | 0.117 | -0.149 |
| baseline | horizontal | all | 10 | structure | 148 / 110 | 108 | 50.0 | 1.892 | 0.119 | -0.146 |
| baseline | horizontal | all | 10 | structure_target | 148 / 117 | 108 | 53.7 | 0.745 | 0.042 | -0.223 |
| baseline | horizontal | all | 20 | fixed | 148 / 88 | 88 | 55.7 | 6.755 | 0.714 | 0.000 |
| baseline | horizontal | all | 20 | original | 148 / 98 | 88 | 46.6 | 5.086 | 0.435 | -0.279 |
| baseline | horizontal | all | 20 | structure | 148 / 100 | 88 | 45.5 | 4.836 | 0.443 | -0.271 |
| baseline | horizontal | all | 20 | structure_target | 148 / 111 | 88 | 52.3 | 1.598 | 0.201 | -0.513 |
| baseline | horizontal | eligible | 5 | fixed | 0 / 0 | 0 | — | — | — | — |
| baseline | horizontal | eligible | 5 | original | 0 / 0 | 0 | — | — | — | — |
| baseline | horizontal | eligible | 5 | structure | 0 / 0 | 0 | — | — | — | — |
| baseline | horizontal | eligible | 5 | structure_target | 0 / 0 | 0 | — | — | — | — |
| baseline | horizontal | eligible | 10 | fixed | 0 / 0 | 0 | — | — | — | — |
| baseline | horizontal | eligible | 10 | original | 0 / 0 | 0 | — | — | — | — |
| baseline | horizontal | eligible | 10 | structure | 0 / 0 | 0 | — | — | — | — |
| baseline | horizontal | eligible | 10 | structure_target | 0 / 0 | 0 | — | — | — | — |
| baseline | horizontal | eligible | 20 | fixed | 0 / 0 | 0 | — | — | — | — |
| baseline | horizontal | eligible | 20 | original | 0 / 0 | 0 | — | — | — | — |
| baseline | horizontal | eligible | 20 | structure | 0 / 0 | 0 | — | — | — | — |
| baseline | horizontal | eligible | 20 | structure_target | 0 / 0 | 0 | — | — | — | — |
| baseline | retest | all | 5 | fixed | 63 / 52 | 52 | 46.2 | 0.192 | 0.042 | 0.000 |
| baseline | retest | all | 5 | original | 63 / 52 | 52 | 44.2 | 0.270 | 0.041 | -0.002 |
| baseline | retest | all | 5 | structure | 63 / 52 | 52 | 44.2 | 0.293 | 0.040 | -0.003 |
| baseline | retest | all | 5 | structure_target | 63 / 55 | 52 | 50.0 | -0.357 | -0.048 | -0.090 |
| baseline | retest | all | 10 | fixed | 63 / 48 | 48 | 54.2 | 1.186 | 0.120 | 0.000 |
| baseline | retest | all | 10 | original | 63 / 48 | 48 | 47.9 | 1.056 | 0.061 | -0.060 |
| baseline | retest | all | 10 | structure | 63 / 49 | 48 | 47.9 | 1.120 | 0.070 | -0.051 |
| baseline | retest | all | 10 | structure_target | 63 / 53 | 48 | 56.2 | -0.090 | -0.021 | -0.142 |
| baseline | retest | all | 20 | fixed | 63 / 40 | 40 | 42.5 | 1.156 | 0.156 | 0.000 |
| baseline | retest | all | 20 | original | 63 / 41 | 40 | 37.5 | 1.300 | 0.086 | -0.070 |
| baseline | retest | all | 20 | structure | 63 / 42 | 40 | 37.5 | 0.928 | 0.065 | -0.091 |
| baseline | retest | all | 20 | structure_target | 63 / 51 | 40 | 50.0 | -0.688 | -0.121 | -0.277 |
| baseline | retest | eligible | 5 | fixed | 1 / 1 | 1 | 0.0 | -2.889 | -1.026 | 0.000 |
| baseline | retest | eligible | 5 | original | 1 / 1 | 1 | 0.0 | -2.861 | -1.016 | 0.010 |
| baseline | retest | eligible | 5 | structure | 1 / 1 | 1 | 0.0 | -2.861 | -1.016 | 0.010 |
| baseline | retest | eligible | 5 | structure_target | 1 / 1 | 1 | 0.0 | -2.861 | -1.016 | 0.010 |
| baseline | retest | eligible | 10 | fixed | 1 / 1 | 1 | 0.0 | -2.889 | -1.026 | 0.000 |
| baseline | retest | eligible | 10 | original | 1 / 1 | 1 | 0.0 | -2.861 | -1.016 | 0.010 |
| baseline | retest | eligible | 10 | structure | 1 / 1 | 1 | 0.0 | -2.861 | -1.016 | 0.010 |
| baseline | retest | eligible | 10 | structure_target | 1 / 1 | 1 | 0.0 | -2.861 | -1.016 | 0.010 |
| baseline | retest | eligible | 20 | fixed | 1 / 1 | 1 | 0.0 | -2.889 | -1.026 | 0.000 |
| baseline | retest | eligible | 20 | original | 1 / 1 | 1 | 0.0 | -2.861 | -1.016 | 0.010 |
| baseline | retest | eligible | 20 | structure | 1 / 1 | 1 | 0.0 | -2.861 | -1.016 | 0.010 |
| baseline | retest | eligible | 20 | structure_target | 1 / 1 | 1 | 0.0 | -2.861 | -1.016 | 0.010 |
| momentum_two | breakout | all | 5 | fixed | 195 / 147 | 147 | 52.4 | 0.896 | 0.078 | 0.000 |
| momentum_two | breakout | all | 5 | original | 195 / 149 | 147 | 49.0 | 0.873 | 0.064 | -0.014 |
| momentum_two | breakout | all | 5 | structure | 195 / 149 | 147 | 49.7 | 0.889 | 0.068 | -0.011 |
| momentum_two | breakout | all | 5 | structure_target | 195 / 163 | 147 | 56.5 | 0.364 | 0.008 | -0.070 |
| momentum_two | breakout | all | 10 | fixed | 195 / 137 | 137 | 55.5 | 2.129 | 0.245 | 0.000 |
| momentum_two | breakout | all | 10 | original | 195 / 139 | 137 | 45.3 | 1.516 | 0.114 | -0.131 |
| momentum_two | breakout | all | 10 | structure | 195 / 139 | 137 | 44.5 | 1.391 | 0.102 | -0.143 |
| momentum_two | breakout | all | 10 | structure_target | 195 / 159 | 137 | 54.7 | 0.801 | 0.029 | -0.216 |
| momentum_two | breakout | all | 20 | fixed | 195 / 113 | 113 | 46.0 | 4.238 | 0.587 | 0.000 |
| momentum_two | breakout | all | 20 | original | 195 / 122 | 113 | 39.8 | 3.142 | 0.337 | -0.249 |
| momentum_two | breakout | all | 20 | structure | 195 / 126 | 113 | 40.7 | 3.106 | 0.351 | -0.235 |
| momentum_two | breakout | all | 20 | structure_target | 195 / 152 | 113 | 52.2 | 2.090 | 0.196 | -0.390 |
| momentum_two | breakout | eligible | 5 | fixed | 2 / 2 | 2 | 50.0 | -1.531 | -0.276 | 0.000 |
| momentum_two | breakout | eligible | 5 | original | 2 / 2 | 2 | 50.0 | -1.531 | -0.276 | 0.000 |
| momentum_two | breakout | eligible | 5 | structure | 2 / 2 | 2 | 50.0 | -1.531 | -0.276 | 0.000 |
| momentum_two | breakout | eligible | 5 | structure_target | 2 / 2 | 2 | 50.0 | -1.531 | -0.276 | 0.000 |
| momentum_two | breakout | eligible | 10 | fixed | 2 / 1 | 1 | 0.0 | -6.850 | -2.005 | 0.000 |
| momentum_two | breakout | eligible | 10 | original | 2 / 1 | 1 | 0.0 | -6.850 | -2.005 | 0.000 |
| momentum_two | breakout | eligible | 10 | structure | 2 / 1 | 1 | 0.0 | -6.850 | -2.005 | 0.000 |
| momentum_two | breakout | eligible | 10 | structure_target | 2 / 2 | 1 | 0.0 | -6.850 | -2.005 | 0.000 |
| momentum_two | breakout | eligible | 20 | fixed | 2 / 1 | 1 | 0.0 | -6.850 | -2.005 | 0.000 |
| momentum_two | breakout | eligible | 20 | original | 2 / 1 | 1 | 0.0 | -6.850 | -2.005 | 0.000 |
| momentum_two | breakout | eligible | 20 | structure | 2 / 1 | 1 | 0.0 | -6.850 | -2.005 | 0.000 |
| momentum_two | breakout | eligible | 20 | structure_target | 2 / 2 | 1 | 0.0 | -6.850 | -2.005 | 0.000 |
| momentum_two | horizontal | all | 5 | fixed | 124 / 95 | 95 | 56.8 | 1.350 | 0.080 | 0.000 |
| momentum_two | horizontal | all | 5 | original | 124 / 96 | 95 | 53.7 | 1.303 | 0.063 | -0.017 |
| momentum_two | horizontal | all | 5 | structure | 124 / 96 | 95 | 53.7 | 1.312 | 0.064 | -0.016 |
| momentum_two | horizontal | all | 5 | structure_target | 124 / 101 | 95 | 56.8 | 0.543 | 0.018 | -0.062 |
| momentum_two | horizontal | all | 10 | fixed | 124 / 90 | 90 | 60.0 | 2.877 | 0.247 | 0.000 |
| momentum_two | horizontal | all | 10 | original | 124 / 91 | 90 | 50.0 | 2.300 | 0.146 | -0.101 |
| momentum_two | horizontal | all | 10 | structure | 124 / 91 | 90 | 50.0 | 2.175 | 0.146 | -0.101 |
| momentum_two | horizontal | all | 10 | structure_target | 124 / 97 | 90 | 53.3 | 0.693 | 0.052 | -0.195 |
| momentum_two | horizontal | all | 20 | fixed | 124 / 75 | 75 | 52.0 | 6.659 | 0.620 | 0.000 |
| momentum_two | horizontal | all | 20 | original | 124 / 81 | 75 | 45.3 | 5.658 | 0.470 | -0.150 |
| momentum_two | horizontal | all | 20 | structure | 124 / 83 | 75 | 42.7 | 5.350 | 0.475 | -0.145 |
| momentum_two | horizontal | all | 20 | structure_target | 124 / 92 | 75 | 54.7 | 2.068 | 0.258 | -0.363 |
| momentum_two | horizontal | eligible | 5 | fixed | 0 / 0 | 0 | — | — | — | — |
| momentum_two | horizontal | eligible | 5 | original | 0 / 0 | 0 | — | — | — | — |
| momentum_two | horizontal | eligible | 5 | structure | 0 / 0 | 0 | — | — | — | — |
| momentum_two | horizontal | eligible | 5 | structure_target | 0 / 0 | 0 | — | — | — | — |
| momentum_two | horizontal | eligible | 10 | fixed | 0 / 0 | 0 | — | — | — | — |
| momentum_two | horizontal | eligible | 10 | original | 0 / 0 | 0 | — | — | — | — |
| momentum_two | horizontal | eligible | 10 | structure | 0 / 0 | 0 | — | — | — | — |
| momentum_two | horizontal | eligible | 10 | structure_target | 0 / 0 | 0 | — | — | — | — |
| momentum_two | horizontal | eligible | 20 | fixed | 0 / 0 | 0 | — | — | — | — |
| momentum_two | horizontal | eligible | 20 | original | 0 / 0 | 0 | — | — | — | — |
| momentum_two | horizontal | eligible | 20 | structure | 0 / 0 | 0 | — | — | — | — |
| momentum_two | horizontal | eligible | 20 | structure_target | 0 / 0 | 0 | — | — | — | — |
| momentum_two | retest | all | 5 | fixed | 23 / 17 | 17 | 29.4 | -0.418 | -0.243 | 0.000 |
| momentum_two | retest | all | 5 | original | 23 / 17 | 17 | 29.4 | 0.005 | -0.161 | 0.082 |
| momentum_two | retest | all | 5 | structure | 23 / 17 | 17 | 29.4 | 0.005 | -0.161 | 0.082 |
| momentum_two | retest | all | 5 | structure_target | 23 / 19 | 17 | 41.2 | -0.829 | -0.212 | 0.031 |
| momentum_two | retest | all | 10 | fixed | 23 / 16 | 16 | 50.0 | 1.146 | -0.060 | 0.000 |
| momentum_two | retest | all | 10 | original | 23 / 16 | 16 | 43.8 | 1.307 | -0.031 | 0.029 |
| momentum_two | retest | all | 10 | structure | 23 / 16 | 16 | 43.8 | 1.455 | 0.007 | 0.067 |
| momentum_two | retest | all | 10 | structure_target | 23 / 18 | 16 | 50.0 | -0.482 | -0.148 | -0.088 |
| momentum_two | retest | all | 20 | fixed | 23 / 15 | 15 | 40.0 | 0.350 | -0.165 | 0.000 |
| momentum_two | retest | all | 20 | original | 23 / 16 | 15 | 46.7 | 1.677 | 0.051 | 0.216 |
| momentum_two | retest | all | 20 | structure | 23 / 16 | 15 | 46.7 | 1.865 | 0.094 | 0.258 |
| momentum_two | retest | all | 20 | structure_target | 23 / 18 | 15 | 53.3 | -0.434 | -0.139 | 0.025 |
| momentum_two | retest | eligible | 5 | fixed | 0 / 0 | 0 | — | — | — | — |
| momentum_two | retest | eligible | 5 | original | 0 / 0 | 0 | — | — | — | — |
| momentum_two | retest | eligible | 5 | structure | 0 / 0 | 0 | — | — | — | — |
| momentum_two | retest | eligible | 5 | structure_target | 0 / 0 | 0 | — | — | — | — |
| momentum_two | retest | eligible | 10 | fixed | 0 / 0 | 0 | — | — | — | — |
| momentum_two | retest | eligible | 10 | original | 0 / 0 | 0 | — | — | — | — |
| momentum_two | retest | eligible | 10 | structure | 0 / 0 | 0 | — | — | — | — |
| momentum_two | retest | eligible | 10 | structure_target | 0 / 0 | 0 | — | — | — | — |
| momentum_two | retest | eligible | 20 | fixed | 0 / 0 | 0 | — | — | — | — |
| momentum_two | retest | eligible | 20 | original | 0 / 0 | 0 | — | — | — | — |
| momentum_two | retest | eligible | 20 | structure | 0 / 0 | 0 | — | — | — | — |
| momentum_two | retest | eligible | 20 | structure_target | 0 / 0 | 0 | — | — | — | — |

### Kapitalbegrenzte Portfolios

Bei `incomplete` ist das angegebene Vermögen nur der beobachtete Präfix; keine volle Phasenrendite. `marked_to_phase_end` kann offene Positionen enthalten. Leere Portfolios sind kein Strategieerfolg.

| Profil | Familie | Gruppe | Tage | Modell | Status | Käufe / geschlossen / offen | Vermögen USD | Phasenrendite % | Realisiert USD | 5m-Drawdown % |
|---|---|---|---:|---|---|---:|---:|---:|---:|---:|
| baseline | breakout | all | 5 | fixed | incomplete | 3 / 0 / 3 | 2002.83 | — | 0.00 | -0.526 |
| baseline | breakout | all | 5 | original | incomplete | 3 / 0 / 3 | 2002.83 | — | 0.00 | -0.526 |
| baseline | breakout | all | 5 | structure | incomplete | 3 / 0 / 3 | 2002.83 | — | 0.00 | -0.526 |
| baseline | breakout | all | 5 | structure_target | incomplete | 3 / 1 / 2 | 2001.76 | — | 2.89 | -0.526 |
| baseline | breakout | all | 10 | fixed | incomplete | 3 / 0 / 3 | 2002.83 | — | 0.00 | -0.526 |
| baseline | breakout | all | 10 | original | incomplete | 3 / 0 / 3 | 2002.83 | — | 0.00 | -0.526 |
| baseline | breakout | all | 10 | structure | incomplete | 3 / 0 / 3 | 2002.83 | — | 0.00 | -0.526 |
| baseline | breakout | all | 10 | structure_target | incomplete | 3 / 1 / 2 | 2001.76 | — | 2.89 | -0.526 |
| baseline | breakout | all | 20 | fixed | incomplete | 3 / 0 / 3 | 2002.83 | — | 0.00 | -0.526 |
| baseline | breakout | all | 20 | original | incomplete | 3 / 0 / 3 | 2002.83 | — | 0.00 | -0.526 |
| baseline | breakout | all | 20 | structure | incomplete | 3 / 0 / 3 | 2002.83 | — | 0.00 | -0.526 |
| baseline | breakout | all | 20 | structure_target | incomplete | 3 / 1 / 2 | 2001.76 | — | 2.89 | -0.526 |
| baseline | breakout | eligible | 5 | fixed | marked_to_phase_end | 4 / 4 / 0 | 1941.87 | -2.906 | -58.13 | -3.980 |
| baseline | breakout | eligible | 5 | original | marked_to_phase_end | 4 / 4 / 0 | 1954.59 | -2.271 | -45.41 | -3.347 |
| baseline | breakout | eligible | 5 | structure | marked_to_phase_end | 4 / 4 / 0 | 1954.59 | -2.271 | -45.41 | -3.347 |
| baseline | breakout | eligible | 5 | structure_target | marked_to_phase_end | 4 / 4 / 0 | 1954.59 | -2.271 | -45.41 | -3.347 |
| baseline | breakout | eligible | 10 | fixed | marked_to_phase_end | 4 / 3 / 1 | 1950.44 | -2.478 | -76.54 | -3.980 |
| baseline | breakout | eligible | 10 | original | marked_to_phase_end | 4 / 3 / 1 | 1963.16 | -1.842 | -63.82 | -3.347 |
| baseline | breakout | eligible | 10 | structure | marked_to_phase_end | 4 / 3 / 1 | 1963.16 | -1.842 | -63.82 | -3.347 |
| baseline | breakout | eligible | 10 | structure_target | marked_to_phase_end | 4 / 4 / 0 | 1962.20 | -1.890 | -37.80 | -3.347 |
| baseline | breakout | eligible | 20 | fixed | marked_to_phase_end | 4 / 3 / 1 | 1950.44 | -2.478 | -76.54 | -3.980 |
| baseline | breakout | eligible | 20 | original | marked_to_phase_end | 4 / 3 / 1 | 1963.16 | -1.842 | -63.82 | -3.347 |
| baseline | breakout | eligible | 20 | structure | marked_to_phase_end | 4 / 3 / 1 | 1963.16 | -1.842 | -63.82 | -3.347 |
| baseline | breakout | eligible | 20 | structure_target | marked_to_phase_end | 4 / 4 / 0 | 1962.20 | -1.890 | -37.80 | -3.347 |
| baseline | horizontal | all | 5 | fixed | incomplete | 5 / 3 / 2 | 1979.48 | — | -22.42 | -2.104 |
| baseline | horizontal | all | 5 | original | incomplete | 5 / 3 / 2 | 1979.48 | — | -22.42 | -2.104 |
| baseline | horizontal | all | 5 | structure | incomplete | 5 / 3 / 2 | 1979.48 | — | -22.42 | -2.104 |
| baseline | horizontal | all | 5 | structure_target | incomplete | 5 / 3 / 2 | 1979.48 | — | -22.42 | -2.104 |
| baseline | horizontal | all | 10 | fixed | incomplete | 5 / 2 / 3 | 1960.93 | — | -40.07 | -2.859 |
| baseline | horizontal | all | 10 | original | incomplete | 5 / 2 / 3 | 1960.93 | — | -40.07 | -2.859 |
| baseline | horizontal | all | 10 | structure | incomplete | 5 / 2 / 3 | 1960.93 | — | -40.07 | -2.859 |
| baseline | horizontal | all | 10 | structure_target | incomplete | 5 / 2 / 3 | 1960.93 | — | -40.07 | -2.859 |
| baseline | horizontal | all | 20 | fixed | incomplete | 5 / 2 / 3 | 1960.93 | — | -40.07 | -2.859 |
| baseline | horizontal | all | 20 | original | incomplete | 5 / 2 / 3 | 1960.93 | — | -40.07 | -2.859 |
| baseline | horizontal | all | 20 | structure | incomplete | 5 / 2 / 3 | 1960.93 | — | -40.07 | -2.859 |
| baseline | horizontal | all | 20 | structure_target | incomplete | 5 / 2 / 3 | 1960.93 | — | -40.07 | -2.859 |
| baseline | horizontal | eligible | 5 | fixed | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| baseline | horizontal | eligible | 5 | original | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| baseline | horizontal | eligible | 5 | structure | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| baseline | horizontal | eligible | 5 | structure_target | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| baseline | horizontal | eligible | 10 | fixed | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| baseline | horizontal | eligible | 10 | original | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| baseline | horizontal | eligible | 10 | structure | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| baseline | horizontal | eligible | 10 | structure_target | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| baseline | horizontal | eligible | 20 | fixed | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| baseline | horizontal | eligible | 20 | original | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| baseline | horizontal | eligible | 20 | structure | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| baseline | horizontal | eligible | 20 | structure_target | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| baseline | retest | all | 5 | fixed | incomplete | 15 / 10 / 5 | 2055.93 | — | 42.28 | -3.536 |
| baseline | retest | all | 5 | original | incomplete | 15 / 10 / 5 | 2058.09 | — | 44.43 | -3.536 |
| baseline | retest | all | 5 | structure | incomplete | 15 / 10 / 5 | 2058.62 | — | 44.96 | -3.536 |
| baseline | retest | all | 5 | structure_target | incomplete | 19 / 16 / 3 | 2040.53 | — | 34.92 | -2.345 |
| baseline | retest | all | 10 | fixed | incomplete | 11 / 8 / 3 | 2063.33 | — | 47.74 | -3.372 |
| baseline | retest | all | 10 | original | incomplete | 11 / 9 / 2 | 2051.71 | — | 50.60 | -4.133 |
| baseline | retest | all | 10 | structure | incomplete | 11 / 9 / 2 | 2076.02 | — | 50.57 | -4.159 |
| baseline | retest | all | 10 | structure_target | incomplete | 19 / 15 / 4 | 2035.57 | — | 17.53 | -2.345 |
| baseline | retest | all | 20 | fixed | incomplete | 12 / 8 / 4 | 2069.06 | — | 81.08 | -3.195 |
| baseline | retest | all | 20 | original | incomplete | 12 / 9 / 3 | 2019.78 | — | 42.86 | -4.133 |
| baseline | retest | all | 20 | structure | incomplete | 14 / 11 / 3 | 2050.70 | — | 53.44 | -4.159 |
| baseline | retest | all | 20 | structure_target | incomplete | 19 / 15 / 4 | 2035.57 | — | 17.53 | -2.345 |
| baseline | retest | eligible | 5 | fixed | marked_to_phase_end | 1 / 1 / 0 | 1985.55 | -0.722 | -14.45 | -1.169 |
| baseline | retest | eligible | 5 | original | marked_to_phase_end | 1 / 1 / 0 | 1985.70 | -0.715 | -14.30 | -1.162 |
| baseline | retest | eligible | 5 | structure | marked_to_phase_end | 1 / 1 / 0 | 1985.70 | -0.715 | -14.30 | -1.162 |
| baseline | retest | eligible | 5 | structure_target | marked_to_phase_end | 1 / 1 / 0 | 1985.70 | -0.715 | -14.30 | -1.162 |
| baseline | retest | eligible | 10 | fixed | marked_to_phase_end | 1 / 1 / 0 | 1985.55 | -0.722 | -14.45 | -1.169 |
| baseline | retest | eligible | 10 | original | marked_to_phase_end | 1 / 1 / 0 | 1985.70 | -0.715 | -14.30 | -1.162 |
| baseline | retest | eligible | 10 | structure | marked_to_phase_end | 1 / 1 / 0 | 1985.70 | -0.715 | -14.30 | -1.162 |
| baseline | retest | eligible | 10 | structure_target | marked_to_phase_end | 1 / 1 / 0 | 1985.70 | -0.715 | -14.30 | -1.162 |
| baseline | retest | eligible | 20 | fixed | marked_to_phase_end | 1 / 1 / 0 | 1985.55 | -0.722 | -14.45 | -1.169 |
| baseline | retest | eligible | 20 | original | marked_to_phase_end | 1 / 1 / 0 | 1985.70 | -0.715 | -14.30 | -1.162 |
| baseline | retest | eligible | 20 | structure | marked_to_phase_end | 1 / 1 / 0 | 1985.70 | -0.715 | -14.30 | -1.162 |
| baseline | retest | eligible | 20 | structure_target | marked_to_phase_end | 1 / 1 / 0 | 1985.70 | -0.715 | -14.30 | -1.162 |
| momentum_two | breakout | all | 5 | fixed | incomplete | 3 / 0 / 3 | 2002.83 | — | 0.00 | -0.526 |
| momentum_two | breakout | all | 5 | original | incomplete | 3 / 0 / 3 | 2002.83 | — | 0.00 | -0.526 |
| momentum_two | breakout | all | 5 | structure | incomplete | 3 / 0 / 3 | 2002.83 | — | 0.00 | -0.526 |
| momentum_two | breakout | all | 5 | structure_target | incomplete | 3 / 1 / 2 | 2001.76 | — | 2.89 | -0.526 |
| momentum_two | breakout | all | 10 | fixed | incomplete | 3 / 0 / 3 | 2002.83 | — | 0.00 | -0.526 |
| momentum_two | breakout | all | 10 | original | incomplete | 3 / 0 / 3 | 2002.83 | — | 0.00 | -0.526 |
| momentum_two | breakout | all | 10 | structure | incomplete | 3 / 0 / 3 | 2002.83 | — | 0.00 | -0.526 |
| momentum_two | breakout | all | 10 | structure_target | incomplete | 3 / 1 / 2 | 2001.76 | — | 2.89 | -0.526 |
| momentum_two | breakout | all | 20 | fixed | incomplete | 3 / 0 / 3 | 2002.83 | — | 0.00 | -0.526 |
| momentum_two | breakout | all | 20 | original | incomplete | 3 / 0 / 3 | 2002.83 | — | 0.00 | -0.526 |
| momentum_two | breakout | all | 20 | structure | incomplete | 3 / 0 / 3 | 2002.83 | — | 0.00 | -0.526 |
| momentum_two | breakout | all | 20 | structure_target | incomplete | 3 / 1 / 2 | 2001.76 | — | 2.89 | -0.526 |
| momentum_two | breakout | eligible | 5 | fixed | marked_to_phase_end | 2 / 2 / 0 | 1984.37 | -0.782 | -15.63 | -2.022 |
| momentum_two | breakout | eligible | 5 | original | marked_to_phase_end | 2 / 2 / 0 | 1984.37 | -0.782 | -15.63 | -2.022 |
| momentum_two | breakout | eligible | 5 | structure | marked_to_phase_end | 2 / 2 / 0 | 1984.37 | -0.782 | -15.63 | -2.022 |
| momentum_two | breakout | eligible | 5 | structure_target | marked_to_phase_end | 2 / 2 / 0 | 1984.37 | -0.782 | -15.63 | -2.022 |
| momentum_two | breakout | eligible | 10 | fixed | marked_to_phase_end | 2 / 1 / 1 | 1993.03 | -0.349 | -34.25 | -2.022 |
| momentum_two | breakout | eligible | 10 | original | marked_to_phase_end | 2 / 1 / 1 | 1993.03 | -0.349 | -34.25 | -2.022 |
| momentum_two | breakout | eligible | 10 | structure | marked_to_phase_end | 2 / 1 / 1 | 1993.03 | -0.349 | -34.25 | -2.022 |
| momentum_two | breakout | eligible | 10 | structure_target | marked_to_phase_end | 2 / 2 / 0 | 1992.06 | -0.397 | -7.94 | -2.022 |
| momentum_two | breakout | eligible | 20 | fixed | marked_to_phase_end | 2 / 1 / 1 | 1993.03 | -0.349 | -34.25 | -2.022 |
| momentum_two | breakout | eligible | 20 | original | marked_to_phase_end | 2 / 1 / 1 | 1993.03 | -0.349 | -34.25 | -2.022 |
| momentum_two | breakout | eligible | 20 | structure | marked_to_phase_end | 2 / 1 / 1 | 1993.03 | -0.349 | -34.25 | -2.022 |
| momentum_two | breakout | eligible | 20 | structure_target | marked_to_phase_end | 2 / 2 / 0 | 1992.06 | -0.397 | -7.94 | -2.022 |
| momentum_two | horizontal | all | 5 | fixed | incomplete | 4 / 2 / 2 | 1997.87 | — | -2.38 | -0.871 |
| momentum_two | horizontal | all | 5 | original | incomplete | 4 / 2 / 2 | 1997.87 | — | -2.38 | -0.871 |
| momentum_two | horizontal | all | 5 | structure | incomplete | 4 / 2 / 2 | 1997.87 | — | -2.38 | -0.871 |
| momentum_two | horizontal | all | 5 | structure_target | incomplete | 4 / 2 / 2 | 1997.87 | — | -2.38 | -0.871 |
| momentum_two | horizontal | all | 10 | fixed | incomplete | 4 / 1 / 3 | 1979.33 | — | -20.03 | -2.157 |
| momentum_two | horizontal | all | 10 | original | incomplete | 4 / 1 / 3 | 1979.33 | — | -20.03 | -2.157 |
| momentum_two | horizontal | all | 10 | structure | incomplete | 4 / 1 / 3 | 1979.33 | — | -20.03 | -2.157 |
| momentum_two | horizontal | all | 10 | structure_target | incomplete | 4 / 1 / 3 | 1979.33 | — | -20.03 | -2.157 |
| momentum_two | horizontal | all | 20 | fixed | incomplete | 4 / 1 / 3 | 1979.33 | — | -20.03 | -2.157 |
| momentum_two | horizontal | all | 20 | original | incomplete | 4 / 1 / 3 | 1979.33 | — | -20.03 | -2.157 |
| momentum_two | horizontal | all | 20 | structure | incomplete | 4 / 1 / 3 | 1979.33 | — | -20.03 | -2.157 |
| momentum_two | horizontal | all | 20 | structure_target | incomplete | 4 / 1 / 3 | 1979.33 | — | -20.03 | -2.157 |
| momentum_two | horizontal | eligible | 5 | fixed | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| momentum_two | horizontal | eligible | 5 | original | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| momentum_two | horizontal | eligible | 5 | structure | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| momentum_two | horizontal | eligible | 5 | structure_target | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| momentum_two | horizontal | eligible | 10 | fixed | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| momentum_two | horizontal | eligible | 10 | original | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| momentum_two | horizontal | eligible | 10 | structure | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| momentum_two | horizontal | eligible | 10 | structure_target | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| momentum_two | horizontal | eligible | 20 | fixed | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| momentum_two | horizontal | eligible | 20 | original | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| momentum_two | horizontal | eligible | 20 | structure | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| momentum_two | horizontal | eligible | 20 | structure_target | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| momentum_two | retest | all | 5 | fixed | incomplete | 10 / 7 / 3 | 2015.49 | — | 9.76 | -2.648 |
| momentum_two | retest | all | 5 | original | incomplete | 10 / 7 / 3 | 2017.62 | — | 11.89 | -2.545 |
| momentum_two | retest | all | 5 | structure | incomplete | 10 / 7 / 3 | 2017.62 | — | 11.89 | -2.545 |
| momentum_two | retest | all | 5 | structure_target | incomplete | 10 / 8 / 2 | 2006.49 | — | 6.54 | -1.970 |
| momentum_two | retest | all | 10 | fixed | incomplete | 8 / 4 / 4 | 2020.15 | — | -28.03 | -2.648 |
| momentum_two | retest | all | 10 | original | incomplete | 8 / 4 / 4 | 2022.29 | — | -25.94 | -2.545 |
| momentum_two | retest | all | 10 | structure | incomplete | 8 / 4 / 4 | 2028.52 | — | -19.71 | -2.545 |
| momentum_two | retest | all | 10 | structure_target | incomplete | 10 / 8 / 2 | 2006.49 | — | 6.54 | -1.970 |
| momentum_two | retest | all | 20 | fixed | incomplete | 8 / 3 / 5 | 2030.42 | — | -43.78 | -2.648 |
| momentum_two | retest | all | 20 | original | incomplete | 8 / 3 / 5 | 2032.57 | — | -41.71 | -2.545 |
| momentum_two | retest | all | 20 | structure | incomplete | 8 / 3 / 5 | 2038.80 | — | -35.48 | -2.545 |
| momentum_two | retest | all | 20 | structure_target | incomplete | 10 / 8 / 2 | 2006.49 | — | 6.54 | -1.970 |
| momentum_two | retest | eligible | 5 | fixed | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| momentum_two | retest | eligible | 5 | original | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| momentum_two | retest | eligible | 5 | structure | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| momentum_two | retest | eligible | 5 | structure_target | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| momentum_two | retest | eligible | 10 | fixed | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| momentum_two | retest | eligible | 10 | original | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| momentum_two | retest | eligible | 10 | structure | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| momentum_two | retest | eligible | 10 | structure_target | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| momentum_two | retest | eligible | 20 | fixed | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| momentum_two | retest | eligible | 20 | original | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| momentum_two | retest | eligible | 20 | structure | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |
| momentum_two | retest | eligible | 20 | structure_target | marked_to_phase_end | 0 / 0 / 0 | 2000.00 | 0.000 | 0.00 | 0.000 |

### Gleichbleibende Fallmenge über alle Modelle und Horizonte

Nur Fälle mit vollständigem Pfad in allen vier Modellen und allen drei Horizonten. Hier zur Übersicht 20 Tage, Referenzprofil, ungefiltert. Diese verfügbare Teilmenge kann Selektionsverzerrung enthalten.

| Familie | Modell | N | Mittel netto % | Mittel netto R |
|---|---|---:|---:|---:|
| breakout | fixed | 167 | 3.860 | 0.520 |
| breakout | original | 167 | 2.680 | 0.252 |
| breakout | structure | 167 | 2.688 | 0.269 |
| breakout | structure_target | 167 | 1.397 | 0.104 |
| horizontal | fixed | 88 | 6.755 | 0.714 |
| horizontal | original | 88 | 5.086 | 0.435 |
| horizontal | structure | 88 | 4.836 | 0.443 |
| horizontal | structure_target | 88 | 1.598 | 0.201 |
| retest | fixed | 40 | 1.156 | 0.156 |
| retest | original | 40 | 1.300 | 0.086 |
| retest | structure | 40 | 0.928 | 0.065 |
| retest | structure_target | 40 | -0.688 | -0.121 |

Blockierte Eintrittsprüfungen (Mehrfachnennungen): `daily_context`: 235, `fresh_daily`: 70, `fresh_weekly`: 146, `line_age`: 67, `net_room`: 780, `risk_atr`: 746, `weekly_context`: 375

