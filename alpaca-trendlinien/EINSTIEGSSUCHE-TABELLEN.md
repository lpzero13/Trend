# Interne Einstiegssuche: vollständige Vergleichstabellen

Erzeugt aus dem festgehaltenen Vertrag `6ec9ebe213280727c73af473189ac114ff69a1a8deaac1021244b4793241767c`. Regeln: [EINSTIEGSSUCHE-INTERN.md](EINSTIEGSSUCHE-INTERN.md).
Alle Renditen sind Schlusskursbeobachtungen nach Kostenannahme, keine ausgeführten Strategie-/Depotgewinne. `Mehr` ist die mittlere Differenz in Prozentpunkten zu passenden Kontrollzeitpunkten. Vollständige 5m-Pfade nötig; keine unabhängigen Trades. Gruppen überlappen.

## development

Wissenschaftlicher Zusammenfassungshash `35aa4145b16779bbbc20abbbd711ce2c5958843c2efc3b2b5dffe2865d6f4baa`.

| Modell/Familie/Gruppe | H | Einstiege | volle Pfade | Aktien | Netto % | Median % | positiv % | Mehr pp | mit Kontrollen | +1R vor Safety | +2R vor Safety |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hull_exact/breakout/all | 5 | 232 | 166 | 20 | 0.33 | 0.49 | 58.43 | -0.24 | 164 | 45/166 | 10/166 |
| hull_exact/breakout/all | 10 | 232 | 151 | 20 | 0.51 | 0.88 | 54.30 | -0.71 | 148 | 67/151 | 28/151 |
| hull_exact/breakout/all | 20 | 232 | 130 | 18 | 2.22 | 1.61 | 56.92 | -0.58 | 126 | 72/130 | 46/130 |
| hull_exact/breakout/three_reactions | 5 | 68 | 51 | 16 | 0.06 | 0.77 | 56.86 | -0.04 | 50 | 16/51 | 2/51 |
| hull_exact/breakout/three_reactions | 10 | 68 | 47 | 15 | 0.68 | 0.82 | 53.19 | 0.05 | 46 | 23/47 | 9/47 |
| hull_exact/breakout/three_reactions | 20 | 68 | 42 | 14 | 3.15 | 1.51 | 59.52 | 1.50 | 39 | 25/42 | 15/42 |
| hull_exact/breakout/strict_diagnostic | 5 | 4 | 3 | 3 | 0.57 | 1.14 | 66.67 | -0.62 | 3 | 2/3 | 1/3 |
| hull_exact/breakout/strict_diagnostic | 10 | 4 | 3 | 3 | -0.10 | -0.54 | 33.33 | -1.86 | 3 | 2/3 | 1/3 |
| hull_exact/breakout/strict_diagnostic | 20 | 4 | 3 | 3 | -1.60 | -0.01 | 33.33 | -4.45 | 2 | 2/3 | 1/3 |
| hull_exact/horizontal/all | 5 | 193 | 140 | 21 | 0.11 | 0.67 | 56.43 | -0.49 | 137 | 37/140 | 6/140 |
| hull_exact/horizontal/all | 10 | 193 | 123 | 18 | 0.53 | 0.87 | 52.85 | -1.02 | 119 | 54/123 | 21/123 |
| hull_exact/horizontal/all | 20 | 193 | 109 | 16 | 2.12 | 1.02 | 54.13 | -0.83 | 106 | 59/109 | 34/109 |
| hull_exact/horizontal/three_reactions | 5 | 60 | 43 | 17 | 0.32 | 0.87 | 60.47 | 0.60 | 41 | 14/43 | 0/43 |
| hull_exact/horizontal/three_reactions | 10 | 60 | 38 | 15 | 0.47 | 0.29 | 50.00 | -0.06 | 36 | 17/38 | 7/38 |
| hull_exact/horizontal/three_reactions | 20 | 60 | 33 | 13 | 3.66 | 2.97 | 57.58 | 1.33 | 31 | 19/33 | 12/33 |
| hull_exact/horizontal/strict_diagnostic | 5 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| hull_exact/horizontal/strict_diagnostic | 10 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| hull_exact/horizontal/strict_diagnostic | 20 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| hull_exact/retest/all | 5 | 54 | 39 | 19 | 0.00 | -0.08 | 46.15 | -1.14 | 38 | 11/39 | 6/39 |
| hull_exact/retest/all | 10 | 54 | 38 | 18 | 0.83 | -0.52 | 44.74 | -0.99 | 38 | 15/38 | 8/38 |
| hull_exact/retest/all | 20 | 54 | 31 | 15 | 2.38 | 1.53 | 61.29 | -2.54 | 31 | 13/31 | 9/31 |
| hull_exact/retest/three_reactions | 5 | 14 | 10 | 8 | -1.10 | -0.76 | 40.00 | -2.66 | 9 | 5/10 | 1/10 |
| hull_exact/retest/three_reactions | 10 | 14 | 9 | 7 | 1.30 | 1.74 | 55.56 | -0.72 | 9 | 5/9 | 3/9 |
| hull_exact/retest/three_reactions | 20 | 14 | 8 | 6 | 4.76 | 3.43 | 75.00 | 0.49 | 8 | 5/8 | 3/8 |
| hull_exact/retest/strict_diagnostic | 5 | 1 | 1 | 1 | -3.78 | -3.78 | 0.00 | -3.63 | 1 | 0/1 | 0/1 |
| hull_exact/retest/strict_diagnostic | 10 | 1 | 1 | 1 | 1.74 | 1.74 | 100.00 | 2.02 | 1 | 0/1 | 0/1 |
| hull_exact/retest/strict_diagnostic | 20 | 1 | 1 | 1 | 4.57 | 4.57 | 100.00 | 2.35 | 1 | 0/1 | 0/1 |
| hull_exact/bounce/all | 5 | 21 | 18 | 12 | -0.94 | -1.64 | 27.78 | -1.42 | 17 | 6/18 | 5/18 |
| hull_exact/bounce/all | 10 | 21 | 16 | 10 | -0.82 | -1.69 | 37.50 | -3.13 | 16 | 6/16 | 5/16 |
| hull_exact/bounce/all | 20 | 21 | 15 | 9 | 3.55 | 3.27 | 80.00 | -0.42 | 15 | 6/15 | 5/15 |
| hull_exact/bounce/three_reactions | 5 | 18 | 16 | 11 | -1.00 | -1.64 | 25.00 | -1.50 | 15 | 4/16 | 3/16 |
| hull_exact/bounce/three_reactions | 10 | 18 | 14 | 9 | -0.67 | -1.69 | 35.71 | -3.30 | 14 | 4/14 | 3/14 |
| hull_exact/bounce/three_reactions | 20 | 18 | 13 | 8 | 3.46 | 2.56 | 76.92 | -0.80 | 13 | 4/13 | 3/13 |
| hull_exact/bounce/strict_diagnostic | 5 | 3 | 3 | 3 | -4.36 | -5.12 | 0.00 | -7.12 | 2 | 0/3 | 0/3 |
| hull_exact/bounce/strict_diagnostic | 10 | 3 | 2 | 2 | -1.08 | -1.08 | 0.00 | -5.62 | 2 | 0/2 | 0/2 |
| hull_exact/bounce/strict_diagnostic | 20 | 3 | 2 | 2 | 3.33 | 3.33 | 100.00 | -1.36 | 2 | 0/2 | 0/2 |
| hull_episodes/breakout/all | 5 | 228 | 164 | 20 | 0.27 | 0.49 | 57.93 | -0.34 | 162 | 45/164 | 12/164 |
| hull_episodes/breakout/all | 10 | 228 | 150 | 20 | 0.46 | 0.85 | 54.00 | -0.83 | 147 | 67/150 | 30/150 |
| hull_episodes/breakout/all | 20 | 228 | 130 | 18 | 2.23 | 1.61 | 56.92 | -0.67 | 125 | 73/130 | 48/130 |
| hull_episodes/breakout/three_reactions | 5 | 68 | 51 | 16 | 0.06 | 0.77 | 56.86 | -0.04 | 50 | 16/51 | 2/51 |
| hull_episodes/breakout/three_reactions | 10 | 68 | 47 | 15 | 0.68 | 0.82 | 53.19 | 0.05 | 46 | 23/47 | 9/47 |
| hull_episodes/breakout/three_reactions | 20 | 68 | 42 | 14 | 3.15 | 1.51 | 59.52 | 1.50 | 39 | 25/42 | 15/42 |
| hull_episodes/breakout/strict_diagnostic | 5 | 4 | 3 | 3 | 0.57 | 1.14 | 66.67 | -0.62 | 3 | 2/3 | 1/3 |
| hull_episodes/breakout/strict_diagnostic | 10 | 4 | 3 | 3 | -0.10 | -0.54 | 33.33 | -1.86 | 3 | 2/3 | 1/3 |
| hull_episodes/breakout/strict_diagnostic | 20 | 4 | 3 | 3 | -1.60 | -0.01 | 33.33 | -4.45 | 2 | 2/3 | 1/3 |
| hull_episodes/horizontal/all | 5 | 188 | 137 | 21 | 0.01 | 0.67 | 56.93 | -0.65 | 134 | 35/137 | 6/137 |
| hull_episodes/horizontal/all | 10 | 188 | 121 | 18 | 0.41 | 0.63 | 52.07 | -1.28 | 117 | 50/121 | 21/121 |
| hull_episodes/horizontal/all | 20 | 188 | 108 | 16 | 2.01 | 0.97 | 53.70 | -1.04 | 105 | 57/108 | 33/108 |
| hull_episodes/horizontal/three_reactions | 5 | 60 | 43 | 17 | 0.32 | 0.87 | 60.47 | 0.60 | 41 | 14/43 | 0/43 |
| hull_episodes/horizontal/three_reactions | 10 | 60 | 38 | 15 | 0.47 | 0.29 | 50.00 | -0.06 | 36 | 17/38 | 7/38 |
| hull_episodes/horizontal/three_reactions | 20 | 60 | 33 | 13 | 3.66 | 2.97 | 57.58 | 1.33 | 31 | 19/33 | 12/33 |
| hull_episodes/horizontal/strict_diagnostic | 5 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| hull_episodes/horizontal/strict_diagnostic | 10 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| hull_episodes/horizontal/strict_diagnostic | 20 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| hull_episodes/retest/all | 5 | 51 | 37 | 19 | -0.18 | -0.21 | 45.95 | -1.21 | 36 | 10/37 | 5/37 |
| hull_episodes/retest/all | 10 | 51 | 36 | 18 | 0.58 | -0.68 | 41.67 | -1.06 | 36 | 13/36 | 7/36 |
| hull_episodes/retest/all | 20 | 51 | 29 | 14 | 1.89 | 1.05 | 58.62 | -2.81 | 29 | 11/29 | 7/29 |
| hull_episodes/retest/three_reactions | 5 | 14 | 10 | 8 | -1.10 | -0.76 | 40.00 | -2.66 | 9 | 5/10 | 1/10 |
| hull_episodes/retest/three_reactions | 10 | 14 | 9 | 7 | 1.30 | 1.74 | 55.56 | -0.72 | 9 | 5/9 | 3/9 |
| hull_episodes/retest/three_reactions | 20 | 14 | 8 | 6 | 4.76 | 3.43 | 75.00 | 0.49 | 8 | 5/8 | 3/8 |
| hull_episodes/retest/strict_diagnostic | 5 | 1 | 1 | 1 | -3.78 | -3.78 | 0.00 | -3.63 | 1 | 0/1 | 0/1 |
| hull_episodes/retest/strict_diagnostic | 10 | 1 | 1 | 1 | 1.74 | 1.74 | 100.00 | 2.02 | 1 | 0/1 | 0/1 |
| hull_episodes/retest/strict_diagnostic | 20 | 1 | 1 | 1 | 4.57 | 4.57 | 100.00 | 2.35 | 1 | 0/1 | 0/1 |
| hull_episodes/bounce/all | 5 | 25 | 22 | 13 | -0.86 | -1.64 | 31.82 | -1.60 | 21 | 8/22 | 7/22 |
| hull_episodes/bounce/all | 10 | 25 | 20 | 11 | 0.31 | -1.08 | 45.00 | -2.14 | 20 | 8/20 | 7/20 |
| hull_episodes/bounce/all | 20 | 25 | 19 | 10 | 3.75 | 3.16 | 73.68 | 0.07 | 18 | 8/19 | 7/19 |
| hull_episodes/bounce/three_reactions | 5 | 18 | 16 | 11 | -1.00 | -1.64 | 25.00 | -1.50 | 15 | 4/16 | 3/16 |
| hull_episodes/bounce/three_reactions | 10 | 18 | 14 | 9 | -0.67 | -1.69 | 35.71 | -3.30 | 14 | 4/14 | 3/14 |
| hull_episodes/bounce/three_reactions | 20 | 18 | 13 | 8 | 3.46 | 2.56 | 76.92 | -0.80 | 13 | 4/13 | 3/13 |
| hull_episodes/bounce/strict_diagnostic | 5 | 3 | 3 | 3 | -4.36 | -5.12 | 0.00 | -7.12 | 2 | 0/3 | 0/3 |
| hull_episodes/bounce/strict_diagnostic | 10 | 3 | 2 | 2 | -1.08 | -1.08 | 0.00 | -5.62 | 2 | 0/2 | 0/2 |
| hull_episodes/bounce/strict_diagnostic | 20 | 3 | 2 | 2 | 3.33 | 3.33 | 100.00 | -1.36 | 2 | 0/2 | 0/2 |
| swing_envelope/breakout/all | 5 | 154 | 116 | 22 | 0.09 | 0.45 | 55.17 | -0.30 | 111 | 32/116 | 10/116 |
| swing_envelope/breakout/all | 10 | 154 | 105 | 20 | 0.50 | 0.88 | 57.14 | -0.72 | 102 | 46/105 | 16/105 |
| swing_envelope/breakout/all | 20 | 154 | 93 | 17 | 2.34 | 2.30 | 58.06 | 0.51 | 89 | 50/93 | 30/93 |
| swing_envelope/breakout/three_reactions | 5 | 38 | 27 | 12 | 2.04 | 1.75 | 77.78 | 1.31 | 27 | 11/27 | 6/27 |
| swing_envelope/breakout/three_reactions | 10 | 38 | 27 | 12 | 2.79 | 3.17 | 66.67 | 0.63 | 27 | 14/27 | 7/27 |
| swing_envelope/breakout/three_reactions | 20 | 38 | 23 | 10 | 5.67 | 3.97 | 82.61 | 3.46 | 23 | 18/23 | 11/23 |
| swing_envelope/breakout/strict_diagnostic | 5 | 2 | 2 | 2 | 0.77 | 0.77 | 100.00 | 0.89 | 2 | 1/2 | 1/2 |
| swing_envelope/breakout/strict_diagnostic | 10 | 2 | 2 | 2 | 3.69 | 3.69 | 100.00 | 3.04 | 2 | 1/2 | 1/2 |
| swing_envelope/breakout/strict_diagnostic | 20 | 2 | 2 | 2 | 0.23 | 0.23 | 50.00 | -0.42 | 2 | 1/2 | 1/2 |
| swing_envelope/horizontal/all | 5 | 136 | 102 | 22 | -0.29 | -0.00 | 50.00 | -0.71 | 97 | 21/102 | 6/102 |
| swing_envelope/horizontal/all | 10 | 136 | 91 | 20 | -0.27 | -0.06 | 49.45 | -1.60 | 89 | 30/91 | 11/91 |
| swing_envelope/horizontal/all | 20 | 136 | 81 | 17 | 0.89 | -0.42 | 48.15 | -0.59 | 79 | 36/81 | 22/81 |
| swing_envelope/horizontal/three_reactions | 5 | 38 | 25 | 12 | 1.29 | 1.33 | 72.00 | 0.84 | 25 | 9/25 | 4/25 |
| swing_envelope/horizontal/three_reactions | 10 | 38 | 25 | 12 | 1.37 | 1.51 | 56.00 | -0.28 | 25 | 11/25 | 5/25 |
| swing_envelope/horizontal/three_reactions | 20 | 38 | 22 | 11 | 4.42 | 3.47 | 68.18 | 3.12 | 22 | 15/22 | 9/22 |
| swing_envelope/horizontal/strict_diagnostic | 5 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| swing_envelope/horizontal/strict_diagnostic | 10 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| swing_envelope/horizontal/strict_diagnostic | 20 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| swing_envelope/retest/all | 5 | 33 | 25 | 15 | 0.02 | -0.21 | 44.00 | 0.61 | 24 | 5/25 | 1/25 |
| swing_envelope/retest/all | 10 | 33 | 22 | 12 | 0.18 | -0.22 | 45.45 | -0.25 | 22 | 7/22 | 2/22 |
| swing_envelope/retest/all | 20 | 33 | 19 | 11 | 0.52 | 0.27 | 52.63 | -1.56 | 19 | 7/19 | 4/19 |
| swing_envelope/retest/three_reactions | 5 | 9 | 7 | 5 | -0.14 | -0.21 | 42.86 | 0.08 | 6 | 1/7 | 0/7 |
| swing_envelope/retest/three_reactions | 10 | 9 | 6 | 4 | 1.75 | 2.05 | 66.67 | -0.09 | 6 | 2/6 | 1/6 |
| swing_envelope/retest/three_reactions | 20 | 9 | 6 | 4 | 3.90 | 2.59 | 83.33 | 1.06 | 6 | 3/6 | 3/6 |
| swing_envelope/retest/strict_diagnostic | 5 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| swing_envelope/retest/strict_diagnostic | 10 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| swing_envelope/retest/strict_diagnostic | 20 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| swing_envelope/bounce/all | 5 | 15 | 15 | 10 | -0.05 | -0.46 | 40.00 | -1.60 | 14 | 8/15 | 5/15 |
| swing_envelope/bounce/all | 10 | 15 | 11 | 6 | -1.03 | -2.01 | 36.36 | -2.60 | 10 | 6/11 | 4/11 |
| swing_envelope/bounce/all | 20 | 15 | 10 | 6 | 1.44 | 1.04 | 60.00 | -1.21 | 9 | 5/10 | 3/10 |
| swing_envelope/bounce/three_reactions | 5 | 15 | 15 | 10 | -0.05 | -0.46 | 40.00 | -1.60 | 14 | 8/15 | 5/15 |
| swing_envelope/bounce/three_reactions | 10 | 15 | 11 | 6 | -1.03 | -2.01 | 36.36 | -2.60 | 10 | 6/11 | 4/11 |
| swing_envelope/bounce/three_reactions | 20 | 15 | 10 | 6 | 1.44 | 1.04 | 60.00 | -1.21 | 9 | 5/10 | 3/10 |
| swing_envelope/bounce/strict_diagnostic | 5 | 2 | 2 | 2 | -3.76 | -3.76 | 0.00 | -7.63 | 1 | 0/2 | 0/2 |
| swing_envelope/bounce/strict_diagnostic | 10 | 2 | 1 | 1 | -1.04 | -1.04 | 0.00 | -6.12 | 1 | 0/1 | 0/1 |
| swing_envelope/bounce/strict_diagnostic | 20 | 2 | 1 | 1 | 1.92 | 1.92 | 100.00 | -2.29 | 1 | 0/1 | 0/1 |
| swing_zone/breakout/all | 5 | 221 | 164 | 23 | 0.53 | 0.35 | 54.27 | 0.07 | 157 | 49/164 | 16/164 |
| swing_zone/breakout/all | 10 | 221 | 150 | 21 | 1.06 | 0.73 | 56.00 | -0.37 | 147 | 65/150 | 22/150 |
| swing_zone/breakout/all | 20 | 221 | 131 | 18 | 3.17 | 2.30 | 60.31 | 0.80 | 125 | 69/131 | 35/131 |
| swing_zone/breakout/three_reactions | 5 | 77 | 55 | 18 | 2.01 | 0.77 | 58.18 | 1.06 | 54 | 23/55 | 10/55 |
| swing_zone/breakout/three_reactions | 10 | 77 | 52 | 16 | 2.90 | 1.15 | 57.69 | 0.69 | 52 | 26/52 | 11/52 |
| swing_zone/breakout/three_reactions | 20 | 77 | 46 | 14 | 6.31 | 3.74 | 71.74 | 2.47 | 44 | 29/46 | 16/46 |
| swing_zone/breakout/strict_diagnostic | 5 | 2 | 2 | 2 | 0.77 | 0.77 | 100.00 | 0.89 | 2 | 1/2 | 1/2 |
| swing_zone/breakout/strict_diagnostic | 10 | 2 | 2 | 2 | 3.69 | 3.69 | 100.00 | 3.04 | 2 | 1/2 | 1/2 |
| swing_zone/breakout/strict_diagnostic | 20 | 2 | 2 | 2 | 0.23 | 0.23 | 50.00 | -0.42 | 2 | 1/2 | 1/2 |
| swing_zone/horizontal/all | 5 | 183 | 137 | 23 | 0.40 | 0.17 | 51.82 | -0.16 | 129 | 37/137 | 10/137 |
| swing_zone/horizontal/all | 10 | 183 | 122 | 21 | 0.69 | 0.05 | 50.82 | -0.95 | 120 | 45/122 | 15/122 |
| swing_zone/horizontal/all | 20 | 183 | 110 | 18 | 1.76 | 0.82 | 51.82 | -0.24 | 107 | 52/110 | 27/110 |
| swing_zone/horizontal/three_reactions | 5 | 66 | 46 | 17 | 1.89 | 0.99 | 60.87 | 1.04 | 44 | 21/46 | 7/46 |
| swing_zone/horizontal/three_reactions | 10 | 66 | 42 | 14 | 2.11 | 0.89 | 52.38 | -0.11 | 42 | 20/42 | 8/42 |
| swing_zone/horizontal/three_reactions | 20 | 66 | 38 | 13 | 4.03 | 3.47 | 60.53 | 2.08 | 37 | 23/38 | 13/38 |
| swing_zone/horizontal/strict_diagnostic | 5 | 1 | 1 | 1 | -2.30 | -2.30 | 0.00 | -2.40 | 1 | 0/1 | 0/1 |
| swing_zone/horizontal/strict_diagnostic | 10 | 1 | 1 | 1 | 3.04 | 3.04 | 100.00 | 2.02 | 1 | 0/1 | 0/1 |
| swing_zone/horizontal/strict_diagnostic | 20 | 1 | 1 | 1 | 8.97 | 8.97 | 100.00 | 1.05 | 1 | 0/1 | 0/1 |
| swing_zone/retest/all | 5 | 55 | 43 | 18 | 1.39 | 0.00 | 51.16 | 1.53 | 41 | 14/43 | 5/43 |
| swing_zone/retest/all | 10 | 55 | 39 | 14 | 2.79 | 0.30 | 51.28 | 2.28 | 39 | 16/39 | 8/39 |
| swing_zone/retest/all | 20 | 55 | 33 | 12 | 3.22 | 1.53 | 63.64 | 0.99 | 30 | 16/33 | 8/33 |
| swing_zone/retest/three_reactions | 5 | 19 | 15 | 11 | 1.99 | 0.77 | 53.33 | 2.51 | 14 | 5/15 | 2/15 |
| swing_zone/retest/three_reactions | 10 | 19 | 14 | 10 | 5.83 | 1.72 | 57.14 | 5.47 | 14 | 7/14 | 4/14 |
| swing_zone/retest/three_reactions | 20 | 19 | 14 | 10 | 6.16 | 2.59 | 78.57 | 4.26 | 12 | 8/14 | 5/14 |
| swing_zone/retest/strict_diagnostic | 5 | 1 | 1 | 1 | 12.52 | 12.52 | 100.00 | 17.21 | 1 | 1/1 | 1/1 |
| swing_zone/retest/strict_diagnostic | 10 | 1 | 1 | 1 | 21.98 | 21.98 | 100.00 | 27.47 | 1 | 1/1 | 1/1 |
| swing_zone/retest/strict_diagnostic | 20 | 1 | 1 | 1 | 4.80 | 4.80 | 100.00 | – | 0 | 1/1 | 1/1 |
| swing_zone/bounce/all | 5 | 37 | 30 | 17 | 0.27 | -0.27 | 46.67 | -1.91 | 29 | 15/30 | 10/30 |
| swing_zone/bounce/all | 10 | 37 | 24 | 13 | -0.49 | -2.42 | 37.50 | -1.46 | 23 | 13/24 | 9/24 |
| swing_zone/bounce/all | 20 | 37 | 19 | 11 | 1.16 | 1.68 | 63.16 | -1.06 | 18 | 9/19 | 6/19 |
| swing_zone/bounce/three_reactions | 5 | 34 | 28 | 17 | 0.60 | 0.70 | 50.00 | -0.80 | 27 | 15/28 | 10/28 |
| swing_zone/bounce/three_reactions | 10 | 34 | 23 | 13 | -0.35 | -2.25 | 39.13 | -1.33 | 22 | 13/23 | 9/23 |
| swing_zone/bounce/three_reactions | 20 | 34 | 18 | 11 | 1.34 | 1.80 | 66.67 | -1.01 | 17 | 9/18 | 6/18 |
| swing_zone/bounce/strict_diagnostic | 5 | 2 | 2 | 2 | -3.76 | -3.76 | 0.00 | -7.63 | 1 | 0/2 | 0/2 |
| swing_zone/bounce/strict_diagnostic | 10 | 2 | 1 | 1 | -1.04 | -1.04 | 0.00 | -6.12 | 1 | 0/1 | 0/1 |
| swing_zone/bounce/strict_diagnostic | 20 | 2 | 1 | 1 | 1.92 | 1.92 | 100.00 | -2.29 | 1 | 0/1 | 0/1 |

### Gleiche Aktien-/Quartalsabdeckung, Ausbruch, zehn Sitzungen

| Modell | Fälle | Mehr pp |
|---|---:|---:|
| hull_exact | 128 | -0.58 |
| hull_episodes | 127 | -0.67 |
| swing_envelope | 98 | -0.51 |
| swing_zone | 132 | -0.06 |

### Meldungen und ausführbare Zeitpunkte

| Modell | Annäherungen | Ausbruchsmeldungen | eindeutige Entryzeiten, alle Familien | zusätzliche Ausbruchszeiten | fehlende Referenz-Ausbruchszeiten |
|---|---:|---:|---:|---:|---:|
| hull_exact | 379 | 315 | 346 | 0 | 0 |
| hull_episodes | 376 | 309 | 342 | 3 | 7 |
| swing_envelope | 377 | 307 | 223 | 56 | 134 |
| swing_zone | 505 | 416 | 340 | 104 | 115 |

Union aller Modelle: **338** Ausbruchszeitpunkte gegenüber **232** in der Hüllenreferenz. Rein beschreibende Abdeckung, keine zusätzliche bestätigte Strategie.

## validation

Wissenschaftlicher Zusammenfassungshash `d47606f28a3ab1389987e27d1fd65c8d7d5e2235f334e11652dbae6f117279b9`.

| Modell/Familie/Gruppe | H | Einstiege | volle Pfade | Aktien | Netto % | Median % | positiv % | Mehr pp | mit Kontrollen | +1R vor Safety | +2R vor Safety |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hull_exact/breakout/all | 5 | 76 | 57 | 20 | 0.92 | 0.82 | 54.39 | -0.10 | 56 | 12/57 | 6/57 |
| hull_exact/breakout/all | 10 | 76 | 51 | 20 | 2.29 | 1.72 | 64.71 | 0.41 | 48 | 17/51 | 10/51 |
| hull_exact/breakout/all | 20 | 76 | 37 | 16 | 4.81 | 2.18 | 54.05 | -1.16 | 35 | 15/37 | 11/37 |
| hull_exact/breakout/three_reactions | 5 | 24 | 19 | 13 | 2.13 | 3.70 | 57.89 | 1.58 | 19 | 5/19 | 1/19 |
| hull_exact/breakout/three_reactions | 10 | 24 | 18 | 12 | 3.69 | 2.33 | 66.67 | 0.96 | 17 | 8/18 | 3/18 |
| hull_exact/breakout/three_reactions | 20 | 24 | 13 | 8 | 6.13 | 0.50 | 53.85 | -1.32 | 12 | 5/13 | 3/13 |
| hull_exact/breakout/strict_diagnostic | 5 | 2 | 2 | 2 | -8.24 | -8.24 | 0.00 | -7.68 | 2 | 0/2 | 0/2 |
| hull_exact/breakout/strict_diagnostic | 10 | 2 | 2 | 2 | -8.74 | -8.74 | 0.00 | -5.30 | 2 | 0/2 | 0/2 |
| hull_exact/breakout/strict_diagnostic | 20 | 2 | 1 | 1 | -5.83 | -5.83 | 0.00 | -0.94 | 1 | 0/1 | 0/1 |
| hull_exact/horizontal/all | 5 | 69 | 53 | 21 | 1.10 | 0.56 | 50.94 | 0.10 | 52 | 13/53 | 6/53 |
| hull_exact/horizontal/all | 10 | 69 | 50 | 21 | 2.24 | 1.73 | 64.00 | 0.05 | 47 | 18/50 | 10/50 |
| hull_exact/horizontal/all | 20 | 69 | 37 | 17 | 4.89 | 2.22 | 64.86 | 0.28 | 36 | 18/37 | 12/37 |
| hull_exact/horizontal/three_reactions | 5 | 22 | 17 | 12 | 3.72 | 3.70 | 64.71 | 2.61 | 17 | 5/17 | 2/17 |
| hull_exact/horizontal/three_reactions | 10 | 22 | 17 | 12 | 4.62 | 3.91 | 76.47 | 0.55 | 16 | 8/17 | 4/17 |
| hull_exact/horizontal/three_reactions | 20 | 22 | 13 | 9 | 6.66 | 2.18 | 61.54 | 0.36 | 13 | 6/13 | 4/13 |
| hull_exact/horizontal/strict_diagnostic | 5 | 1 | 1 | 1 | -12.74 | -12.74 | 0.00 | -11.17 | 1 | 0/1 | 0/1 |
| hull_exact/horizontal/strict_diagnostic | 10 | 1 | 1 | 1 | 3.34 | 3.34 | 100.00 | 0.81 | 1 | 0/1 | 0/1 |
| hull_exact/horizontal/strict_diagnostic | 20 | 1 | 1 | 1 | 0.15 | 0.15 | 100.00 | 17.24 | 1 | 0/1 | 0/1 |
| hull_exact/retest/all | 5 | 24 | 19 | 14 | 1.47 | -0.40 | 42.11 | 0.33 | 19 | 4/19 | 1/19 |
| hull_exact/retest/all | 10 | 24 | 17 | 13 | 4.72 | 1.48 | 58.82 | 5.36 | 16 | 8/17 | 2/17 |
| hull_exact/retest/all | 20 | 24 | 15 | 13 | 4.52 | 1.92 | 66.67 | 2.33 | 12 | 9/15 | 6/15 |
| hull_exact/retest/three_reactions | 5 | 5 | 3 | 3 | 4.59 | 6.18 | 66.67 | 4.57 | 3 | 1/3 | 0/3 |
| hull_exact/retest/three_reactions | 10 | 5 | 3 | 3 | 3.48 | 1.48 | 66.67 | 6.04 | 3 | 2/3 | 0/3 |
| hull_exact/retest/three_reactions | 20 | 5 | 3 | 3 | 6.65 | 0.24 | 66.67 | 10.97 | 3 | 2/3 | 1/3 |
| hull_exact/retest/strict_diagnostic | 5 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| hull_exact/retest/strict_diagnostic | 10 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| hull_exact/retest/strict_diagnostic | 20 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| hull_exact/bounce/all | 5 | 10 | 8 | 7 | 3.57 | -0.54 | 50.00 | 1.72 | 8 | 3/8 | 2/8 |
| hull_exact/bounce/all | 10 | 10 | 8 | 7 | 6.56 | 2.79 | 75.00 | -1.46 | 8 | 4/8 | 2/8 |
| hull_exact/bounce/all | 20 | 10 | 8 | 7 | 16.85 | 3.27 | 62.50 | 3.08 | 8 | 4/8 | 3/8 |
| hull_exact/bounce/three_reactions | 5 | 10 | 8 | 7 | 3.57 | -0.54 | 50.00 | 1.72 | 8 | 3/8 | 2/8 |
| hull_exact/bounce/three_reactions | 10 | 10 | 8 | 7 | 6.56 | 2.79 | 75.00 | -1.46 | 8 | 4/8 | 2/8 |
| hull_exact/bounce/three_reactions | 20 | 10 | 8 | 7 | 16.85 | 3.27 | 62.50 | 3.08 | 8 | 4/8 | 3/8 |
| hull_exact/bounce/strict_diagnostic | 5 | 1 | 1 | 1 | -6.12 | -6.12 | 0.00 | -1.72 | 1 | 0/1 | 0/1 |
| hull_exact/bounce/strict_diagnostic | 10 | 1 | 1 | 1 | -9.23 | -9.23 | 0.00 | -9.09 | 1 | 0/1 | 0/1 |
| hull_exact/bounce/strict_diagnostic | 20 | 1 | 1 | 1 | -5.46 | -5.46 | 0.00 | -2.66 | 1 | 0/1 | 0/1 |
| hull_episodes/breakout/all | 5 | 75 | 57 | 20 | 0.92 | 0.82 | 54.39 | -0.10 | 56 | 12/57 | 6/57 |
| hull_episodes/breakout/all | 10 | 75 | 51 | 20 | 2.29 | 1.72 | 64.71 | 0.41 | 48 | 16/51 | 10/51 |
| hull_episodes/breakout/all | 20 | 75 | 37 | 16 | 4.81 | 2.18 | 54.05 | -1.16 | 35 | 14/37 | 11/37 |
| hull_episodes/breakout/three_reactions | 5 | 24 | 19 | 13 | 2.13 | 3.70 | 57.89 | 1.58 | 19 | 5/19 | 1/19 |
| hull_episodes/breakout/three_reactions | 10 | 24 | 18 | 12 | 3.69 | 2.33 | 66.67 | 0.96 | 17 | 7/18 | 3/18 |
| hull_episodes/breakout/three_reactions | 20 | 24 | 13 | 8 | 6.13 | 0.50 | 53.85 | -1.32 | 12 | 4/13 | 3/13 |
| hull_episodes/breakout/strict_diagnostic | 5 | 2 | 2 | 2 | -8.24 | -8.24 | 0.00 | -7.68 | 2 | 0/2 | 0/2 |
| hull_episodes/breakout/strict_diagnostic | 10 | 2 | 2 | 2 | -8.74 | -8.74 | 0.00 | -5.30 | 2 | 0/2 | 0/2 |
| hull_episodes/breakout/strict_diagnostic | 20 | 2 | 1 | 1 | -5.83 | -5.83 | 0.00 | -0.94 | 1 | 0/1 | 0/1 |
| hull_episodes/horizontal/all | 5 | 68 | 53 | 21 | 1.10 | 0.56 | 50.94 | 0.10 | 52 | 13/53 | 6/53 |
| hull_episodes/horizontal/all | 10 | 68 | 50 | 21 | 2.24 | 1.73 | 64.00 | 0.05 | 47 | 17/50 | 10/50 |
| hull_episodes/horizontal/all | 20 | 68 | 37 | 17 | 4.89 | 2.22 | 64.86 | 0.28 | 36 | 17/37 | 12/37 |
| hull_episodes/horizontal/three_reactions | 5 | 22 | 17 | 12 | 3.72 | 3.70 | 64.71 | 2.61 | 17 | 5/17 | 2/17 |
| hull_episodes/horizontal/three_reactions | 10 | 22 | 17 | 12 | 4.62 | 3.91 | 76.47 | 0.55 | 16 | 7/17 | 4/17 |
| hull_episodes/horizontal/three_reactions | 20 | 22 | 13 | 9 | 6.66 | 2.18 | 61.54 | 0.36 | 13 | 5/13 | 4/13 |
| hull_episodes/horizontal/strict_diagnostic | 5 | 1 | 1 | 1 | -12.74 | -12.74 | 0.00 | -11.17 | 1 | 0/1 | 0/1 |
| hull_episodes/horizontal/strict_diagnostic | 10 | 1 | 1 | 1 | 3.34 | 3.34 | 100.00 | 0.81 | 1 | 0/1 | 0/1 |
| hull_episodes/horizontal/strict_diagnostic | 20 | 1 | 1 | 1 | 0.15 | 0.15 | 100.00 | 17.24 | 1 | 0/1 | 0/1 |
| hull_episodes/retest/all | 5 | 24 | 19 | 14 | 1.47 | -0.40 | 42.11 | 0.33 | 19 | 4/19 | 1/19 |
| hull_episodes/retest/all | 10 | 24 | 17 | 13 | 4.72 | 1.48 | 58.82 | 5.36 | 16 | 8/17 | 2/17 |
| hull_episodes/retest/all | 20 | 24 | 15 | 13 | 4.52 | 1.92 | 66.67 | 2.33 | 12 | 9/15 | 6/15 |
| hull_episodes/retest/three_reactions | 5 | 5 | 3 | 3 | 4.59 | 6.18 | 66.67 | 4.57 | 3 | 1/3 | 0/3 |
| hull_episodes/retest/three_reactions | 10 | 5 | 3 | 3 | 3.48 | 1.48 | 66.67 | 6.04 | 3 | 2/3 | 0/3 |
| hull_episodes/retest/three_reactions | 20 | 5 | 3 | 3 | 6.65 | 0.24 | 66.67 | 10.97 | 3 | 2/3 | 1/3 |
| hull_episodes/retest/strict_diagnostic | 5 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| hull_episodes/retest/strict_diagnostic | 10 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| hull_episodes/retest/strict_diagnostic | 20 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| hull_episodes/bounce/all | 5 | 11 | 9 | 8 | 3.36 | 0.40 | 55.56 | 1.71 | 9 | 3/9 | 2/9 |
| hull_episodes/bounce/all | 10 | 11 | 9 | 8 | 6.28 | 3.81 | 77.78 | -1.03 | 9 | 4/9 | 2/9 |
| hull_episodes/bounce/all | 20 | 11 | 8 | 7 | 16.85 | 3.27 | 62.50 | 3.08 | 8 | 4/8 | 3/8 |
| hull_episodes/bounce/three_reactions | 5 | 10 | 8 | 7 | 3.57 | -0.54 | 50.00 | 1.72 | 8 | 3/8 | 2/8 |
| hull_episodes/bounce/three_reactions | 10 | 10 | 8 | 7 | 6.56 | 2.79 | 75.00 | -1.46 | 8 | 4/8 | 2/8 |
| hull_episodes/bounce/three_reactions | 20 | 10 | 8 | 7 | 16.85 | 3.27 | 62.50 | 3.08 | 8 | 4/8 | 3/8 |
| hull_episodes/bounce/strict_diagnostic | 5 | 1 | 1 | 1 | -6.12 | -6.12 | 0.00 | -1.72 | 1 | 0/1 | 0/1 |
| hull_episodes/bounce/strict_diagnostic | 10 | 1 | 1 | 1 | -9.23 | -9.23 | 0.00 | -9.09 | 1 | 0/1 | 0/1 |
| hull_episodes/bounce/strict_diagnostic | 20 | 1 | 1 | 1 | -5.46 | -5.46 | 0.00 | -2.66 | 1 | 0/1 | 0/1 |
| swing_envelope/breakout/all | 5 | 58 | 49 | 20 | -0.23 | -1.07 | 40.82 | -1.01 | 48 | 15/49 | 5/49 |
| swing_envelope/breakout/all | 10 | 58 | 48 | 20 | -0.18 | 0.50 | 52.08 | -1.44 | 46 | 19/48 | 8/48 |
| swing_envelope/breakout/all | 20 | 58 | 33 | 15 | 0.63 | -1.33 | 48.48 | -2.10 | 32 | 18/33 | 13/33 |
| swing_envelope/breakout/three_reactions | 5 | 16 | 14 | 11 | 3.06 | 2.63 | 78.57 | 0.92 | 14 | 8/14 | 2/14 |
| swing_envelope/breakout/three_reactions | 10 | 16 | 14 | 11 | 2.61 | 3.41 | 78.57 | -3.02 | 14 | 10/14 | 4/14 |
| swing_envelope/breakout/three_reactions | 20 | 16 | 9 | 7 | 7.25 | 5.03 | 77.78 | -0.57 | 9 | 8/9 | 6/9 |
| swing_envelope/breakout/strict_diagnostic | 5 | 1 | 1 | 1 | 2.26 | 2.26 | 100.00 | 2.87 | 1 | 1/1 | 0/1 |
| swing_envelope/breakout/strict_diagnostic | 10 | 1 | 1 | 1 | -5.13 | -5.13 | 0.00 | -0.78 | 1 | 1/1 | 0/1 |
| swing_envelope/breakout/strict_diagnostic | 20 | 1 | 1 | 1 | -8.09 | -8.09 | 0.00 | -5.97 | 1 | 1/1 | 0/1 |
| swing_envelope/horizontal/all | 5 | 47 | 41 | 20 | 0.12 | -0.96 | 41.46 | -0.62 | 40 | 12/41 | 4/41 |
| swing_envelope/horizontal/all | 10 | 47 | 41 | 20 | -0.24 | 0.27 | 51.22 | -1.31 | 39 | 16/41 | 7/41 |
| swing_envelope/horizontal/all | 20 | 47 | 28 | 15 | 0.30 | -0.60 | 50.00 | -2.35 | 27 | 15/28 | 11/28 |
| swing_envelope/horizontal/three_reactions | 5 | 14 | 13 | 10 | 3.86 | 2.94 | 76.92 | 1.96 | 13 | 6/13 | 2/13 |
| swing_envelope/horizontal/three_reactions | 10 | 14 | 13 | 10 | 4.34 | 3.88 | 84.62 | -0.01 | 13 | 8/13 | 4/13 |
| swing_envelope/horizontal/three_reactions | 20 | 14 | 9 | 7 | 7.09 | 5.03 | 77.78 | -0.06 | 9 | 7/9 | 6/9 |
| swing_envelope/horizontal/strict_diagnostic | 5 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| swing_envelope/horizontal/strict_diagnostic | 10 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| swing_envelope/horizontal/strict_diagnostic | 20 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| swing_envelope/retest/all | 5 | 14 | 12 | 8 | 0.56 | -0.20 | 50.00 | 0.04 | 12 | 5/12 | 2/12 |
| swing_envelope/retest/all | 10 | 14 | 11 | 7 | 2.88 | 1.62 | 72.73 | 2.80 | 11 | 6/11 | 2/11 |
| swing_envelope/retest/all | 20 | 14 | 10 | 7 | 0.45 | 1.05 | 60.00 | 0.32 | 10 | 6/10 | 3/10 |
| swing_envelope/retest/three_reactions | 5 | 2 | 1 | 1 | 3.06 | 3.06 | 100.00 | -1.80 | 1 | 1/1 | 0/1 |
| swing_envelope/retest/three_reactions | 10 | 2 | 1 | 1 | 4.69 | 4.69 | 100.00 | 1.26 | 1 | 1/1 | 0/1 |
| swing_envelope/retest/three_reactions | 20 | 2 | 1 | 1 | 2.29 | 2.29 | 100.00 | -5.56 | 1 | 1/1 | 0/1 |
| swing_envelope/retest/strict_diagnostic | 5 | 1 | 1 | 1 | 2.88 | 2.88 | 100.00 | -1.88 | 1 | 1/1 | 0/1 |
| swing_envelope/retest/strict_diagnostic | 10 | 1 | 1 | 1 | 1.49 | 1.49 | 100.00 | 2.25 | 1 | 1/1 | 0/1 |
| swing_envelope/retest/strict_diagnostic | 20 | 1 | 1 | 1 | -7.42 | -7.42 | 0.00 | -10.13 | 1 | 1/1 | 0/1 |
| swing_envelope/bounce/all | 5 | 8 | 7 | 6 | -0.44 | -1.45 | 42.86 | -2.36 | 7 | 3/7 | 1/7 |
| swing_envelope/bounce/all | 10 | 8 | 5 | 5 | 7.00 | 6.53 | 100.00 | 3.56 | 5 | 3/5 | 2/5 |
| swing_envelope/bounce/all | 20 | 8 | 5 | 5 | 6.45 | 8.64 | 80.00 | 0.04 | 5 | 3/5 | 2/5 |
| swing_envelope/bounce/three_reactions | 5 | 8 | 7 | 6 | -0.44 | -1.45 | 42.86 | -2.36 | 7 | 3/7 | 1/7 |
| swing_envelope/bounce/three_reactions | 10 | 8 | 5 | 5 | 7.00 | 6.53 | 100.00 | 3.56 | 5 | 3/5 | 2/5 |
| swing_envelope/bounce/three_reactions | 20 | 8 | 5 | 5 | 6.45 | 8.64 | 80.00 | 0.04 | 5 | 3/5 | 2/5 |
| swing_envelope/bounce/strict_diagnostic | 5 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| swing_envelope/bounce/strict_diagnostic | 10 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| swing_envelope/bounce/strict_diagnostic | 20 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| swing_zone/breakout/all | 5 | 86 | 70 | 21 | 0.05 | -0.67 | 44.29 | -1.34 | 69 | 22/70 | 8/70 |
| swing_zone/breakout/all | 10 | 86 | 69 | 21 | 1.03 | 1.72 | 60.87 | -1.64 | 66 | 30/69 | 13/69 |
| swing_zone/breakout/all | 20 | 86 | 52 | 18 | 2.81 | 1.78 | 55.77 | -1.04 | 51 | 30/52 | 21/52 |
| swing_zone/breakout/three_reactions | 5 | 36 | 30 | 16 | 2.24 | 2.20 | 66.67 | -0.02 | 30 | 13/30 | 4/30 |
| swing_zone/breakout/three_reactions | 10 | 36 | 30 | 16 | 3.20 | 3.28 | 80.00 | -1.27 | 29 | 19/30 | 8/30 |
| swing_zone/breakout/three_reactions | 20 | 36 | 24 | 15 | 5.63 | 4.90 | 70.83 | 1.13 | 24 | 18/24 | 13/24 |
| swing_zone/breakout/strict_diagnostic | 5 | 2 | 2 | 2 | -3.25 | -3.25 | 50.00 | -5.23 | 2 | 1/2 | 0/2 |
| swing_zone/breakout/strict_diagnostic | 10 | 2 | 2 | 2 | -0.61 | -0.61 | 50.00 | -7.55 | 2 | 1/2 | 0/2 |
| swing_zone/breakout/strict_diagnostic | 20 | 2 | 2 | 2 | 8.52 | 8.52 | 50.00 | -6.65 | 2 | 1/2 | 0/2 |
| swing_zone/horizontal/all | 5 | 71 | 59 | 21 | 0.39 | -0.82 | 44.07 | -0.86 | 58 | 17/59 | 6/59 |
| swing_zone/horizontal/all | 10 | 71 | 59 | 21 | 1.17 | 1.60 | 59.32 | -1.33 | 57 | 23/59 | 11/59 |
| swing_zone/horizontal/all | 20 | 71 | 45 | 18 | 2.04 | 1.37 | 57.78 | -0.77 | 44 | 24/45 | 17/45 |
| swing_zone/horizontal/three_reactions | 5 | 34 | 28 | 15 | 2.80 | 2.63 | 64.29 | 0.69 | 28 | 10/28 | 4/28 |
| swing_zone/horizontal/three_reactions | 10 | 34 | 28 | 15 | 4.16 | 3.41 | 82.14 | 0.34 | 28 | 15/28 | 7/28 |
| swing_zone/horizontal/three_reactions | 20 | 34 | 24 | 15 | 5.40 | 4.90 | 70.83 | 1.31 | 24 | 16/24 | 12/24 |
| swing_zone/horizontal/strict_diagnostic | 5 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| swing_zone/horizontal/strict_diagnostic | 10 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| swing_zone/horizontal/strict_diagnostic | 20 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| swing_zone/retest/all | 5 | 22 | 19 | 10 | 0.96 | 0.12 | 52.63 | 0.63 | 19 | 7/19 | 2/19 |
| swing_zone/retest/all | 10 | 22 | 17 | 9 | 2.59 | 1.62 | 70.59 | 2.32 | 17 | 8/17 | 2/17 |
| swing_zone/retest/all | 20 | 22 | 15 | 9 | 1.19 | 2.07 | 66.67 | 2.03 | 15 | 8/15 | 3/15 |
| swing_zone/retest/three_reactions | 5 | 7 | 5 | 4 | 3.50 | 4.45 | 80.00 | 1.46 | 5 | 3/5 | 0/5 |
| swing_zone/retest/three_reactions | 10 | 7 | 5 | 4 | 3.96 | 4.69 | 100.00 | 2.48 | 5 | 3/5 | 0/5 |
| swing_zone/retest/three_reactions | 20 | 7 | 5 | 4 | 4.06 | 3.11 | 100.00 | 4.97 | 5 | 3/5 | 0/5 |
| swing_zone/retest/strict_diagnostic | 5 | 2 | 2 | 2 | 0.46 | 0.46 | 50.00 | 0.69 | 2 | 1/2 | 0/2 |
| swing_zone/retest/strict_diagnostic | 10 | 2 | 1 | 1 | 1.49 | 1.49 | 100.00 | 2.25 | 1 | 1/1 | 0/1 |
| swing_zone/retest/strict_diagnostic | 20 | 2 | 1 | 1 | -7.42 | -7.42 | 0.00 | -10.13 | 1 | 1/1 | 0/1 |
| swing_zone/bounce/all | 5 | 15 | 11 | 9 | 0.61 | -1.45 | 45.45 | -1.18 | 11 | 6/11 | 3/11 |
| swing_zone/bounce/all | 10 | 15 | 9 | 8 | 5.29 | 4.08 | 88.89 | 2.29 | 9 | 6/9 | 5/9 |
| swing_zone/bounce/all | 20 | 15 | 9 | 8 | 4.61 | 8.63 | 77.78 | -0.66 | 8 | 6/9 | 5/9 |
| swing_zone/bounce/three_reactions | 5 | 14 | 11 | 9 | 0.61 | -1.45 | 45.45 | -1.18 | 11 | 6/11 | 3/11 |
| swing_zone/bounce/three_reactions | 10 | 14 | 9 | 8 | 5.29 | 4.08 | 88.89 | 2.29 | 9 | 6/9 | 5/9 |
| swing_zone/bounce/three_reactions | 20 | 14 | 9 | 8 | 4.61 | 8.63 | 77.78 | -0.66 | 8 | 6/9 | 5/9 |
| swing_zone/bounce/strict_diagnostic | 5 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| swing_zone/bounce/strict_diagnostic | 10 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |
| swing_zone/bounce/strict_diagnostic | 20 | 0 | 0 | 0 | – | – | – | – | 0 | 0/0 | 0/0 |

### Gleiche Aktien-/Quartalsabdeckung, Ausbruch, zehn Sitzungen

| Modell | Fälle | Mehr pp |
|---|---:|---:|
| hull_exact | 44 | 0.13 |
| hull_episodes | 44 | 0.13 |
| swing_envelope | 39 | -1.69 |
| swing_zone | 51 | -1.79 |

### Meldungen und ausführbare Zeitpunkte

| Modell | Annäherungen | Ausbruchsmeldungen | eindeutige Entryzeiten, alle Familien | zusätzliche Ausbruchszeiten | fehlende Referenz-Ausbruchszeiten |
|---|---:|---:|---:|---:|---:|
| hull_exact | 138 | 116 | 121 | 0 | 0 |
| hull_episodes | 139 | 114 | 121 | 1 | 2 |
| swing_envelope | 162 | 136 | 84 | 31 | 49 |
| swing_zone | 211 | 186 | 133 | 52 | 42 |

Union aller Modelle: **128** Ausbruchszeitpunkte gegenüber **76** in der Hüllenreferenz. Rein beschreibende Abdeckung, keine zusätzliche bestätigte Strategie.
