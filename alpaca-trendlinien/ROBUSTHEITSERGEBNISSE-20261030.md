# Breite Robustheitsprüfung des festen Ausbruch-Kandidaten

Stand: 30.10.2026. [Vorab festgelegter Versuchsplan](ROBUSTHEITSPLAN-20261030.md).

Unveränderte Strategie auf **69 Aktien und 4 Zeitfenstern** geprüft: 276 Aktien-/Zeitfenster, davon 10 wegen fehlender Vorgeschichte oder Entry-Abdeckung nicht verfügbar. Keine Ersetzung nach Ergebnis, keine erneute Parametersuche, keine Providerabrufe.

## Gesamtes Universum – je Zeitraum dasselbe Anfangskapital von 2.000 USD

| Entry-Zeitraum | Verfügbare Aktien | Trades / geschlossen | Netto Basis | Drawdown 5m | Doppelte variable Kosten | +1 USD je Order | +2 USD je Order |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2018 | 65/69 | 17 / 14 | nicht auswertbar | -7,45 % | nicht auswertbar | nicht auswertbar | nicht auswertbar |
| 2021 | 66/69 | 12 / 9 | nicht auswertbar | -5,33 % | nicht auswertbar | nicht auswertbar | nicht auswertbar |
| 2023 | 67/69 | 32 / 32 | +19,19 % | -5,71 % | +18,44 % | +8,12 % | +13,06 % |
| 2025-2026 | 68/69 | 40 / 40 | +11,80 % | -7,20 % | +10,80 % | +9,33 % | +8,17 % |

**Getrennte Kapitalstarts:** Die Tabellenwerte sind keine aufeinanderfolgenden Jahresrenditen und dürfen nicht addiert oder zu einer durchgehenden Depotkurve verkettet werden. Bei unvollständigen Büchern betrifft der Drawdown nur den beobachteten Teilpfad. Kosten können durch andere Stückzahlen auch spätere Belegungen verändern. Beispiel 2023: 32 Trades ohne Festgebühr, 34 bei 1 USD und 31 bei 2 USD je Order; die höhere Gesamtrendite bei 2 gegenüber 1 USD ist kein positiver isolierter Gebühreneffekt, sondern ein anderes belegtes Portfolio.

## Vorab definierte Prüfgrenzen und Kontrollen

| Zeitraum | Basis-/Kosten-/Streuungsgrenzen | Vollständige Kontrollbücher | Kontrollmedian | Kontroll-P90 | Gesamtes statistisches Prüftor |
|---|---|---:|---:|---:|---|
| 2018 | nicht bestanden | 31/39 | nicht auswertbar | nicht auswertbar | nicht bestanden |
| 2021 | nicht bestanden | 1/39 | nicht auswertbar | nicht auswertbar | nicht bestanden |
| 2023 | bestanden | 31/39 | nicht auswertbar | nicht auswertbar | nicht bestanden |
| 2025-2026 | bestanden | 33/39 | nicht auswertbar | nicht auswertbar | nicht bestanden |

Das Prüftor verlangt alle Basisgrenzen sowie einen Nettoertrag oberhalb des 90. Perzentils von 39 vollständigen Zufallskontrollen. Die Kontrollen haben dieselbe Aktie, denselben Monat und kausal gültige Safety; sie sind explorativ und kein korrigierter Signifikanztest. Unvollständige Kontrollen bestehen das Tor nicht.

## Vorherige 16 gegenüber zusätzlichen Aktien

| Zeitraum | Bisherige 16: Basis | Zusätzliche Aktien: Basis | Zusätzliche Aktien: doppelte Kosten |
|---|---:|---:|---:|
| 2018 | -3,78 % | +3,47 % | +2,83 % |
| 2021 | nicht auswertbar | nicht auswertbar | nicht auswertbar |
| 2023 | -4,17 % | +17,59 % | +16,58 % |
| 2025-2026 | +16,90 % | +11,66 % | +11,10 % |

Auch diese Gruppen haben jeweils ein eigenes vollständiges 2.000-USD-Buch. Kein Ergebnis wird nachträglich als Gewinnerkorb ausgewählt.

## Datenqualität, Signaldichte und Ablehnungen

### 2018

- 700 qualifizierte Ausbruch-Signale vor Budget-/Belegungsprüfung; 17 angenommene Trades.
- Ablehnungsgründe: `{'max_positions': 311, 'already_holding_symbol': 15, 'invalid_signal_stop': 13, 'opening_gap_through_stop': 3, 'no_affordable_units': 1}`.
- Wegen Datenhalt noch nicht entschiedene spätere Signale: 340. Das sind keine geprüften Ablehnungen.
- Nicht verfügbare Aktien: GEV, LIN, PLTR, SNDK.
- Verfügbare Aktien einschließlich Vorlauf/Nachbeobachtung: 162 fehlende von 2,964,390 erwarteten 5m-Kerzen. Keine Auffüllung.
- Nicht bestandene Basisgrenzen: complete, netPositive, costStressPositive.
- Datenbedingter Kapitalbuchhalt: `{'reason': 'held_position_missing_market_path', 'at': 1529602500, 'symbols': ['ANET']}`.
- Positive Aktienbeiträge: 5; größter Anteil an positiven Beiträgen: 35.8 %.

### 2021

- 692 qualifizierte Ausbruch-Signale vor Budget-/Belegungsprüfung; 12 angenommene Trades.
- Ablehnungsgründe: `{'invalid_signal_stop': 5, 'max_positions': 199, 'already_holding_symbol': 7, 'no_affordable_units': 1, 'opening_gap_through_stop': 1}`.
- Wegen Datenhalt noch nicht entschiedene spätere Signale: 467. Das sind keine geprüften Ablehnungen.
- Nicht verfügbare Aktien: GEV, PLTR, SNDK.
- Verfügbare Aktien einschließlich Vorlauf/Nachbeobachtung: 13,104 fehlende von 3,020,292 erwarteten 5m-Kerzen. Keine Auffüllung.
- Nicht bestandene Basisgrenzen: complete, netPositive, broadContributions, costStressPositive.
- Datenbedingter Kapitalbuchhalt: `{'reason': 'held_position_missing_market_path', 'at': 1618839300, 'symbols': ['LIN', 'MMM']}`.
- Positive Aktienbeiträge: 3; größter Anteil an positiven Beiträgen: 47.3 %.

### 2023

- 762 qualifizierte Ausbruch-Signale vor Budget-/Belegungsprüfung; 32 angenommene Trades.
- Ablehnungsgründe: `{'invalid_signal_stop': 30, 'max_positions': 654, 'already_holding_symbol': 42, 'opening_gap_through_stop': 3, 'no_affordable_units': 1}`.
- Wegen Datenhalt noch nicht entschiedene spätere Signale: 0. Das sind keine geprüften Ablehnungen.
- Nicht verfügbare Aktien: GEV, SNDK.
- Verfügbare Aktien einschließlich Vorlauf/Nachbeobachtung: 5,942 fehlende von 3,055,200 erwarteten 5m-Kerzen. Keine Auffüllung.
- Nicht bestandene Basisgrenzen: keine.
- Datenbedingter Kapitalbuchhalt: `None`.
- Positive Aktienbeiträge: 12; größter Anteil an positiven Beiträgen: 30.3 %.

### 2025-2026

- 728 qualifizierte Ausbruch-Signale vor Budget-/Belegungsprüfung; 40 angenommene Trades.
- Ablehnungsgründe: `{'invalid_signal_stop': 30, 'no_affordable_units': 16, 'already_holding_symbol': 34, 'max_positions': 605, 'opening_gap_through_stop': 3}`.
- Wegen Datenhalt noch nicht entschiedene spätere Signale: 0. Das sind keine geprüften Ablehnungen.
- Nicht verfügbare Aktien: SNDK.
- Verfügbare Aktien einschließlich Vorlauf/Nachbeobachtung: 1,999 fehlende von 3,104,064 erwarteten 5m-Kerzen. Keine Auffüllung.
- Nicht bestandene Basisgrenzen: keine.
- Datenbedingter Kapitalbuchhalt: `None`.
- Positive Aktienbeiträge: 11; größter Anteil an positiven Beiträgen: 23.6 %.

Sämtliche gespeicherten 1h-/4h-/1D-Aggregate der untersuchten Fenster wurden gegen ihre 5m-Basis nachgerechnet. Feiertage, Sommerzeit und verkürzte Sitzungen folgen dem versionierten Börsenkalender. Große Kurslücken allein bestätigen keine Kapitalmaßnahme.

## Gezielte Datenprüfung als nächster Schritt

Die reine Offline-Vorschau nennt **30 Symbol-/Tagespaare an 10 Handelstagen**, an denen gehaltene Pfade die Basis-, Kosten- oder Kontrollbücher unterbrechen. Das ist keine vollständige Liste aller Archivlücken und kein nachträglicher Handelsfilter.

| Handelstag ET | Betroffene Aktien in unterbrochenen Büchern |
|---|---|
| 2018-02-15 | ABBV |
| 2018-06-21 | ANET |
| 2021-04-19 | ABT, BA, CAT, CRM, CVX, HD, IBM, JNJ, KO, LIN, MCD, MMM, NEE, ORCL, PG, PM, TMO, TRV, UNP, VZ |
| 2021-10-25 | AXP, MCD |
| 2023-03-15 | LLY |
| 2023-06-09 | TMO |
| 2023-09-01 | LRCX |
| 2025-04-29 | LIN |
| 2025-05-05 | SHW |
| 2025-09-22 | TRV |

Zuerst die konkreten 5m-Zeitpunkte und Importmetadaten prüfen, dann fehlende Providerdaten von bestätigten Handelspausen oder Intervallen ohne Handel unterscheiden. Bei neuen Providerdaten neue unveränderliche Datasets und einen neuen Versuchsplan anlegen. Alte Kurse, Prüfergebnisse und Journale erhalten; keine automatische Auffüllung oder Löschung. Der Sammler wurde nicht fortgesetzt.

## Technische Nachweise

Separater Prüflauf bestanden: 276 Blöcke, 14,849 Signalfälle aller Familien und 204 Kapitalbücher. Sämtliche vier Basisportfolios reproduziert; Kapitalbewegungen sowie Bewertungen/Drawdowns auf jeder 5m-Stufe unabhängig nachgerechnet. Auswahl unverändert, keine Providerabrufe.

Regression: 494 Python-Tests ohne Fehler, ein bestehender Skip; 70 Chart-/Web-JavaScript-Tests bestanden. Neues Signaljournal: echter AAPL-Vergleich zwischen Einzelschritten und Batch, Neustart ohne Duplikate, zukünftige Kursschocks ohne Änderung alter Signale, echter Prozessabbruch mit Rollback und Backup/Restore geprüft. Das ist technische Prüfung, keine prospektive Handelsbilanz.

Der erste Auswertungsversuch scheiterte beim Kontrollpool einer Aktie ohne ausreichende Vor-IPO-Historie. Korrektur in einem neuen Plan: solche ausdrücklich nicht verfügbaren Aktien haben keine gewünschten Kontrollentries. Alle 276 ursprünglichen Pilotblöcke wurden mit gleichem Daten-/Signal-/Ausführungscode geprüft übernommen; Quellplan, alter Code und alte Ausgaben bleiben erhalten. Keine Fortsetzung des alten Auftrags unter geänderter Engine.

## Bewertung und verbleibende Grenzen

2 von 4 Gesamtfenstern haben einen vollständig berechenbaren positiven Basis-Nettoertrag. Vollständiges statistisches Prüftor über alle Fenster: **nicht bestanden**. Die Hypothese bleibt unverändert; ein Fehlschlag wird nicht durch neue Schwellen auf denselben Daten repariert.

**Keine operative Freigabe:** Die historischen Daten enthalten splitbereinigte Preise. Ohne historische Splitfaktoren ist ein rechnerisch ganzzahliges Depot nicht vollständig als damals handelbares Ganzaktien-Depot nachgewiesen. Historische Gebühren, Dividenden, EUR/USD, Steuern und Cashverzinsung sind nicht vollständig abgebildet. Der aktuelle überlebende Aktienbestand ersetzt kein historisches Universum einschließlich delisteter Titel.

2018/2021/2023 sind zusätzliche Robustheitsfenster dieser Runde, jedoch nicht garantiert projektweit unangetastet. Der spätere Block 2025/26 wurde für Teile des Universums schon verwendet. Die Ergebnisse sind keine prospektive Erfolgsbestätigung.

## Reproduzierbarkeit und Hermes

Das private Studienverzeichnis enthält den vor Berechnung gespeicherten Plan, explizite Dataset-IDs, Engine-Prüfsummen, je Symbol/Zeitfenster geprüfte Signal-/Kursblöcke, sämtliche Kapitalbücher, Kostenvarianten, Kontrollen und Ergebnis-Prüfsummen. Laufende/abgebrochene Berechnungen können nur mit unverändertem Plan und Engine wiederaufgenommen werden.

```text
python tools/run_robustness_study.py --root PRIVATER_ORDNER --source ALTER_40_TAGE_VERSUCH --datasets SYMBOL_DATASET_JSON --phase prepare
python tools/run_robustness_study.py --root PRIVATER_ORDNER --phase build --workers 2
python tools/run_robustness_study.py --root PRIVATER_ORDNER --phase evaluate
python tools/verify_robustness_study.py --root PRIVATER_ORDNER
```

Alle Befehle verwenden den bestehenden `TORI_DATA_DIR`. Keine automatische Datenbeschaffung, kein Sammler-Resume, keine UI-Änderung, Containerinstallation, Order oder Meldungszustellung.
