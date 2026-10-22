# Unabhängiger Retest-Zeitvergleich und Entwicklungsdiagnose

Vorabvertrag `e7f4112bb6e6fc14ccd6976d83202e2179874a08ab0255acbb4d9b0305e9be14`. Zeitraum 2026-07-06 bis 2026-10-16, 74 XNYS-Sitzungen, 25 unverändert gewählte Aktien.

Alle Modellzahlen nach angenommenen Kosten, USD. Überlappende Einzelpositionen sind kein Depot.

## Datenabdeckung vor Ergebnisauswertung

| Aktie | vorhandene 5m / erwartet | Abdeckung |
|---|---:|---:|
| AAPL | 5772 / 5772 | 100.00 % |
| ADBE | 5770 / 5772 | 99.97 % |
| AMD | 5765 / 5772 | 99.88 % |
| AMZN | 5772 / 5772 | 100.00 % |
| AVGO | 5772 / 5772 | 100.00 % |
| BAC | 5772 / 5772 | 100.00 % |
| CAT | 5733 / 5772 | 99.32 % |
| COST | 5614 / 5772 | 97.26 % |
| CVX | 5743 / 5772 | 99.50 % |
| GOOGL | 5772 / 5772 | 100.00 % |
| GS | 5610 / 5772 | 97.19 % |
| HD | 5768 / 5772 | 99.93 % |
| JNJ | 5730 / 5772 | 99.27 % |
| JPM | 5769 / 5772 | 99.95 % |
| KO | 5772 / 5772 | 100.00 % |
| MA | 5755 / 5772 | 99.71 % |
| META | 5772 / 5772 | 100.00 % |
| MSFT | 5772 / 5772 | 100.00 % |
| NVDA | 5772 / 5772 | 100.00 % |
| ORCL | 5772 / 5772 | 100.00 % |
| PG | 5759 / 5772 | 99.77 % |
| UNH | 5771 / 5772 | 99.98 % |
| V | 5772 / 5772 | 100.00 % |
| WMT | 5772 / 5772 | 100.00 % |
| XOM | 5766 / 5772 | 99.90 % |

## Abgeschlossene Hauptgruppen

Vollständige relevante Vorgeschichte und kalendarisch genug Nachlauf; zukünftige Datenabdeckung ist kein Auswahlfilter.

| Geometrie / Exit | Fälle | geschlossen | unbekannt | mittlere R | Gewinnanteil |
|---|---:|---:|---:|---:|---:|
| swing_zone / fixed | 16 | 16 | 0 | -0.3972 | 31.2500 % |
| swing_zone / atr_gain_stop | 16 | 16 | 0 | -0.3848 | 31.2500 % |

swing_zone: gepaarte Fälle 16, mittlere ATR−Fest-Differenz 0.0124R; beschreibendes Aktie-/Quartal-Intervall: `{"low": 0.0, "high": 0.042397699818187536, "blocks": 8, "method": "symbol-quarter block bootstrap; descriptive, not adjusted for profile selection"}`.

Unvollständige Vorgeschichte (separat): 6 Fälle; zu wenig kalendarischer Nachlauf: 5 weitere Entries.

| hull_exact / fixed | 9 | 9 | 0 | 1.3842 | 66.6667 % |
| hull_exact / atr_gain_stop | 9 | 9 | 0 | 1.3823 | 66.6667 % |

hull_exact: gepaarte Fälle 9, mittlere ATR−Fest-Differenz -0.0019R; beschreibendes Aktie-/Quartal-Intervall: `{"low": -0.005083678925872448, "high": 0.0, "blocks": 7, "method": "symbol-quarter block bootstrap; descriptive, not adjusted for profile selection"}`.

Unvollständige Vorgeschichte (separat): 5 Fälle; zu wenig kalendarischer Nachlauf: 2 weitere Entries.

## Modellierte Portfolios

| Geometrie / Exit | angenommen / geschlossen / offen | Endwert USD | Rendite | max. 5m-Drawdown | Status |
|---|---:|---:|---:|---:|---|
| swing_zone/fixed | 12 / 12 / 0 | 1941.86 | -2.9068 % | -6.2160 % | marked_to_phase_end |
| swing_zone/atr_gain_stop | 12 / 12 / 0 | 1941.86 | -2.9068 % | -6.2160 % | marked_to_phase_end |
| hull_exact/fixed | 8 / 8 / 0 | 2205.71 | 10.2854 % | -1.8919 % | marked_to_phase_end |
| hull_exact/atr_gain_stop | 8 / 8 / 0 | 2205.49 | 10.2746 % | -1.8919 % | marked_to_phase_end |

Drawdown auf 5m-Schlussbewertungen; größere intrabar Verluste möglich. Endwerte sind modelliert, nicht erzielte Brokerergebnisse.

## Vorabtor

```json
{
  "pairs": 16,
  "symbols": 8,
  "meanDeltaR": 0.012354556376252608,
  "relativeDrawdownReduction": 0.0,
  "checks": {
    "sample": false,
    "complete_paths": true,
    "mean_r_budget": true,
    "drawdown": false,
    "uninterrupted_portfolios": true
  },
  "decision": "not_established_keep_fixed_reference",
  "meaning": "A predeclared research gate, not a significance test, strategy validation or deployment approval."
}
```

## Einstiegsmerkmale ausschließlich aus der alten Entwicklung

Median, keine optimierten Grenzwerte. Gewinner/Verlierer beziehen sich auf den festen Stop nach Kosten; Gruppen können zeitlich/je Aktie abhängig sein.

| Merkmal | positiv: verfügbar / Median | nichtpositiv: verfügbar / Median | fehlend gesamt |
|---|---:|---:|---:|
| contacts | 17 / 2.0000 | 19 / 2.0000 | 0 |
| reactionEpisodes | 17 / 2.0000 | 19 / 2.0000 | 0 |
| contactSpanDays | 17 / 7.0000 | 19 / 18.0000 | 0 |
| lineAgeDays | 17 / 19.2708 | 19 / 29.0000 | 0 |
| projectionSensitivityATR | 17 / 0.1500 | 19 / 0.0962 | 0 |
| signalRiskATR | 17 / 3.4838 | 19 / 1.9743 | 0 |
| netRoomR | 16 / 0.3018 | 19 / 0.5488 | 1 |
| safetyDistancePct | 17 / 5.8299 | 19 / 2.3224 | 0 |

all: 36 Fälle aus 15 Aktien; Tages-/Wochenkontext `{"daily": {"down": 7, "mixed": 16, "up": 13}, "weekly": {"down": 3, "mixed": 10, "unknown": 3, "up": 20}}`.

positive: 17 Fälle aus 7 Aktien; Tages-/Wochenkontext `{"daily": {"down": 4, "mixed": 7, "up": 6}, "weekly": {"down": 1, "mixed": 6, "up": 10}}`.

nonpositive: 19 Fälle aus 13 Aktien; Tages-/Wochenkontext `{"daily": {"down": 3, "mixed": 9, "up": 7}, "weekly": {"down": 2, "mixed": 4, "unknown": 3, "up": 10}}`.

Merkmale waren vor oder beim Entry bekannt: Linienmerkmale aus dem eingefrorenen Signal, Kontext aus damals geschlossenen Kerzen; Risiko/Raum/Safety-Abstand verwenden den beobachteten Entry-Open. Keine späteren Verlaufskerzen.

Der reservierte Zeitraum ist nach diesem Vergleich verbraucht. Kein Parameterlernen daraus; für neue Kriterien braucht es neue Evidenz. Heutiges US-Universum, IEX-Lücken, wenige abhängige Fälle und kein Zufallsentry-Exitvergleich begrenzen die Aussage.
