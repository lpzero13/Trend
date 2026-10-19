# Ausstiegsvergleich auf eingefrorenen Einstiegen

Stand 19.10.2026. Echte gespeicherte MSFT/AMZN/JPM/XOM/KO-Alpaca-IEX-Daten; splitbereinigt, reguläre XNYS-Sitzungen. **Explorative Ausführungssimulation, keine validierte Strategie.**

## Testvertrag

Zwei unveränderte Einstiegsprofile (Grundsignal und Momentum 2 aus 3), je Ausbruch, horizontale Bestätigung und Retest. Pro Profil/Familie/Aktie/Entryzeit ein vorab kanonisch bestimmtes Linienpaar. Alle sieben Ausstiege erhalten genau dessen Entry, ursprünglichen Stop und Originalanker. Keine Auswahl anhand späterer Gewinne. Mehrere Linienpaare werden nicht als mehrere unabhängige Trades gezählt.

Die strenge vollständige Einstiegsreferenz hatte in den vorangegangenen Läufen keine akzeptierten Einstiege. Die hier getesteten beiden Gruppen sind ausdrücklich Forschungsprofile: Kontaktqualität, Raum und Safety-Abstand werden nicht sämtlich als Pflichtfilter verlangt. „Tori-Kombination“ bezeichnet die Ausstiegs-Auslegung, keine nachträgliche Behauptung, alle Einstiege hätten die vollständige Tori-Checkliste erfüllt.

Entwicklung 02.05.2025–18.03.2026; bereits vorher untersuchte Validierung 19.03.–02.07.2026. Diese spätere Phase ist für die neue Exit-Forschung **kein unberührter finaler Test**. Holdout 06.07.–16.10.2026 bleibt ungeöffnet. Keine neue Schwellenwertoptimierung oder Auswahl des besten Horizonts.

5/10/20 Handelstage zählen strikt nach dem Entrytag. Frühere Verkäufe bleiben bis zum jeweiligen Endtag als unverzinster Geldbetrag liegen; kein Wiedereinstieg innerhalb desselben Falls. Die folgenden Tabellen verwenden pro Profil/Familie/Phase dieselben Fälle über **alle Modelle und alle drei Horizonte**. Dadurch sind die drei Spalten vergleichbar. Fehlende 5m-Strecken und Phasengrenzen sind ausgeschlossen, nie als Nullgewinn eingesetzt.

**Geldbeträge:** jeweils 1.000 USD pro unabhängig betrachteter Position, rechnerische Bruchstücke; Spread 5 Basispunkte (davon je Seite die Hälfte), Slippage 5 Basispunkte je Seite, Ordergebühr 0. Ohne Steuern, Dividenden, Finanzierung oder EUR-Umrechnung. Ein- und Ausstieg enthalten zusammen rund 0,15 % modellierte Kosten. Keine Summe dieser überlappenden Fälle als Depotgewinn ausgeben.

## Auslegungen der Regeln

| Modell | Getestete Regel |
|---|---|
| Zeitablauf | Kein Schutzstop; Verkauf am Schluss von Tag 5/10/20 als Referenz. |
| Fester Stop | Archivierter initialStop als fester Preis; Berührung während einer 5m-Kerze löst aus. |
| Stop + 2R | Derselbe Stop; Ziel = kostenbehafteter Kaufpreis + zweimal anfänglicher Preisabstand zum Stop. |
| Stop + Fakeout | Fester Stop; zusätzlich erster bestätigter 4h-Schluss unter der **ursprünglich** gebrochenen roten Linie; Verkauf am ersten regulären 5m-Open frühestens fünf Minuten später. |
| Grün nachziehen | Fester Stop; nach einem bestätigten späteren grünen B-Anker wird die aktuelle gültige grüne 4h-Linie am damaligen 4h-Schluss projiziert, minus 0,01 USD. Neuer fester Stoppreis wirkt frühestens fünf Minuten später und wird nur angehoben. Auch vorläufige Zwei-Kontakt-Linien sind zugelassen. |
| Stop + bekannter Widerstand | Fester Stop und zum Signal gespeichertes nächstes bekanntes Widerstandsniveau oberhalb des Kaufpreises als festes Ziel; sonst kein Gewinnziel. |
| Tori-Kombination | Nachziehen + bekanntes Widerstandsziel + Fakeout-Ausstieg; weiterhin ursprünglicher Schutzstop. |

Die Tori-Zusammenfassung nennt Safety Line, spätere Pullbacks und größere/horizontale Widerstände. Auslösung, Puffer, Teilverkäufe und Fakeout-Verkauf sind dort nicht vollständig festgelegt. Die letzten Varianten sind deshalb **unsere expliziten experimentellen Auslegungen**, kein verifiziertes Originalregelwerk. Der bekannte Widerstand stammt aus dem vorhandenen kausalen Raum-Merkmal (historische Hochs und bekannte Tageslinie); Wochen-/Monatsziele werden nicht ergänzt. Eine spätere neue rote Linie wird nie rückwirkend zum Ziel. Fehlender Widerstand wird im Rohbericht separat gezählt.

Bei Kurslücken unter einem Stop zählt das tatsächliche nächste Open. Bei gleichzeitigem Stop-/Zielkontakt in einer 5m-Kerze gilt der Stop zuerst. Ein bereits aktiver Gap-Stop geht einem gleichzeitig fälligen Fakeout-Verkauf vor. Gewinnziele erhalten bei Gaps keine bessere Ausführung als ihr Limit. Fehlende 5m-Daten beenden die Beweisbarkeit; ein bereits davor belegter Verkauf bleibt gültig.

## Ergebnisse: dieselben Fälle über 5/10/20 Tage

### development / baseline / breakout: 109 vollständig von 166 Einstiegen

Mittleres Nettoergebnis je 1.000 USD Einsatz; in Klammern mittlere Prozentänderung. Unterschiedliche Gruppen können dieselben physischen Einstiege enthalten.

| Ausstieg | 5 Tage | 10 Tage | 20 Tage |
|---|---:|---:|---:|
| Zeitablauf | -1.55 USD (-0.16 %) | -4.98 USD (-0.50 %) | +6.85 USD (+0.68 %) |
| Fester Stop | +0.19 USD (+0.02 %) | -5.68 USD (-0.57 %) | +2.54 USD (+0.25 %) |
| Stop + 2R | +0.13 USD (+0.01 %) | -3.36 USD (-0.34 %) | +2.84 USD (+0.28 %) |
| Stop + Fakeout | +0.49 USD (+0.05 %) | -6.70 USD (-0.67 %) | -1.15 USD (-0.12 %) |
| Grün nachziehen | +0.19 USD (+0.02 %) | -2.64 USD (-0.26 %) | -0.92 USD (-0.09 %) |
| Stop + bekannter Widerstand | -1.01 USD (-0.10 %) | -1.39 USD (-0.14 %) | +1.18 USD (+0.12 %) |
| Tori-Kombination | -0.90 USD (-0.09 %) | -0.27 USD (-0.03 %) | +0.29 USD (+0.03 %) |

### development / baseline / horizontal: 60 vollständig von 86 Einstiegen

Mittleres Nettoergebnis je 1.000 USD Einsatz; in Klammern mittlere Prozentänderung. Unterschiedliche Gruppen können dieselben physischen Einstiege enthalten.

| Ausstieg | 5 Tage | 10 Tage | 20 Tage |
|---|---:|---:|---:|
| Zeitablauf | -5.52 USD (-0.55 %) | -9.99 USD (-1.00 %) | +7.29 USD (+0.73 %) |
| Fester Stop | -4.93 USD (-0.49 %) | -11.25 USD (-1.12 %) | -0.33 USD (-0.03 %) |
| Stop + 2R | -4.96 USD (-0.50 %) | -10.87 USD (-1.09 %) | -4.70 USD (-0.47 %) |
| Stop + Fakeout | -3.15 USD (-0.32 %) | -8.97 USD (-0.90 %) | -6.65 USD (-0.66 %) |
| Grün nachziehen | -4.24 USD (-0.42 %) | -4.13 USD (-0.41 %) | -1.37 USD (-0.14 %) |
| Stop + bekannter Widerstand | -2.59 USD (-0.26 %) | -6.76 USD (-0.68 %) | -3.17 USD (-0.32 %) |
| Tori-Kombination | -3.17 USD (-0.32 %) | -2.56 USD (-0.26 %) | -1.74 USD (-0.17 %) |

### development / baseline / retest: 38 vollständig von 54 Einstiegen

Mittleres Nettoergebnis je 1.000 USD Einsatz; in Klammern mittlere Prozentänderung. Unterschiedliche Gruppen können dieselben physischen Einstiege enthalten.

| Ausstieg | 5 Tage | 10 Tage | 20 Tage |
|---|---:|---:|---:|
| Zeitablauf | +6.33 USD (+0.63 %) | +5.82 USD (+0.58 %) | +14.43 USD (+1.44 %) |
| Fester Stop | +2.78 USD (+0.28 %) | -0.99 USD (-0.10 %) | +5.95 USD (+0.59 %) |
| Stop + 2R | +3.56 USD (+0.36 %) | +0.79 USD (+0.08 %) | +5.67 USD (+0.57 %) |
| Stop + Fakeout | +3.49 USD (+0.35 %) | -0.15 USD (-0.02 %) | +0.24 USD (+0.02 %) |
| Grün nachziehen | +2.28 USD (+0.23 %) | +3.85 USD (+0.39 %) | +6.76 USD (+0.68 %) |
| Stop + bekannter Widerstand | -0.70 USD (-0.07 %) | -1.82 USD (-0.18 %) | -1.39 USD (-0.14 %) |
| Tori-Kombination | +0.60 USD (+0.06 %) | +0.74 USD (+0.07 %) | +1.22 USD (+0.12 %) |

### development / momentum_two / breakout: 84 vollständig von 112 Einstiegen

Mittleres Nettoergebnis je 1.000 USD Einsatz; in Klammern mittlere Prozentänderung. Unterschiedliche Gruppen können dieselben physischen Einstiege enthalten.

| Ausstieg | 5 Tage | 10 Tage | 20 Tage |
|---|---:|---:|---:|
| Zeitablauf | -0.33 USD (-0.03 %) | -2.79 USD (-0.28 %) | +8.88 USD (+0.89 %) |
| Fester Stop | +2.37 USD (+0.24 %) | -3.20 USD (-0.32 %) | +3.78 USD (+0.38 %) |
| Stop + 2R | +2.80 USD (+0.28 %) | -0.01 USD (-0.00 %) | +4.14 USD (+0.41 %) |
| Stop + Fakeout | +2.41 USD (+0.24 %) | -4.65 USD (-0.47 %) | +2.21 USD (+0.22 %) |
| Grün nachziehen | +0.92 USD (+0.09 %) | -2.18 USD (-0.22 %) | +0.68 USD (+0.07 %) |
| Stop + bekannter Widerstand | +0.73 USD (+0.07 %) | +1.15 USD (+0.11 %) | +4.28 USD (+0.43 %) |
| Tori-Kombination | -0.29 USD (-0.03 %) | +0.51 USD (+0.05 %) | +1.31 USD (+0.13 %) |

### development / momentum_two / horizontal: 56 vollständig von 78 Einstiegen

Mittleres Nettoergebnis je 1.000 USD Einsatz; in Klammern mittlere Prozentänderung. Unterschiedliche Gruppen können dieselben physischen Einstiege enthalten.

| Ausstieg | 5 Tage | 10 Tage | 20 Tage |
|---|---:|---:|---:|
| Zeitablauf | -7.26 USD (-0.73 %) | -9.65 USD (-0.96 %) | +6.81 USD (+0.68 %) |
| Fester Stop | -6.44 USD (-0.64 %) | -11.07 USD (-1.11 %) | -3.45 USD (-0.35 %) |
| Stop + 2R | -6.48 USD (-0.65 %) | -10.67 USD (-1.07 %) | -8.13 USD (-0.81 %) |
| Stop + Fakeout | -4.06 USD (-0.41 %) | -8.72 USD (-0.87 %) | -6.76 USD (-0.68 %) |
| Grün nachziehen | -3.55 USD (-0.36 %) | -2.81 USD (-0.28 %) | +0.15 USD (+0.01 %) |
| Stop + bekannter Widerstand | -4.09 USD (-0.41 %) | -7.99 USD (-0.80 %) | -3.64 USD (-0.36 %) |
| Tori-Kombination | -3.25 USD (-0.33 %) | -2.70 USD (-0.27 %) | -1.81 USD (-0.18 %) |

### development / momentum_two / retest: 20 vollständig von 27 Einstiegen

Mittleres Nettoergebnis je 1.000 USD Einsatz; in Klammern mittlere Prozentänderung. Unterschiedliche Gruppen können dieselben physischen Einstiege enthalten.

| Ausstieg | 5 Tage | 10 Tage | 20 Tage |
|---|---:|---:|---:|
| Zeitablauf | +6.55 USD (+0.65 %) | +5.25 USD (+0.52 %) | +21.27 USD (+2.13 %) |
| Fester Stop | +2.92 USD (+0.29 %) | +0.92 USD (+0.09 %) | +6.32 USD (+0.63 %) |
| Stop + 2R | +3.81 USD (+0.38 %) | +2.09 USD (+0.21 %) | +8.06 USD (+0.81 %) |
| Stop + Fakeout | +3.49 USD (+0.35 %) | +0.93 USD (+0.09 %) | +0.86 USD (+0.09 %) |
| Grün nachziehen | +0.73 USD (+0.07 %) | +2.00 USD (+0.20 %) | +1.89 USD (+0.19 %) |
| Stop + bekannter Widerstand | +0.30 USD (+0.03 %) | -1.32 USD (-0.13 %) | -0.69 USD (-0.07 %) |
| Tori-Kombination | +0.12 USD (+0.01 %) | -0.29 USD (-0.03 %) | -0.29 USD (-0.03 %) |

### validation / baseline / breakout: 44 vollständig von 63 Einstiegen

Mittleres Nettoergebnis je 1.000 USD Einsatz; in Klammern mittlere Prozentänderung. Unterschiedliche Gruppen können dieselben physischen Einstiege enthalten.

| Ausstieg | 5 Tage | 10 Tage | 20 Tage |
|---|---:|---:|---:|
| Zeitablauf | +2.36 USD (+0.24 %) | +10.39 USD (+1.04 %) | +12.99 USD (+1.30 %) |
| Fester Stop | +0.24 USD (+0.02 %) | -2.25 USD (-0.22 %) | +0.94 USD (+0.09 %) |
| Stop + 2R | +0.24 USD (+0.02 %) | -2.50 USD (-0.25 %) | -1.44 USD (-0.14 %) |
| Stop + Fakeout | -0.56 USD (-0.06 %) | +1.53 USD (+0.15 %) | +8.24 USD (+0.82 %) |
| Grün nachziehen | -3.87 USD (-0.39 %) | -4.30 USD (-0.43 %) | -6.59 USD (-0.66 %) |
| Stop + bekannter Widerstand | -2.49 USD (-0.25 %) | -2.20 USD (-0.22 %) | -3.62 USD (-0.36 %) |
| Tori-Kombination | -9.25 USD (-0.92 %) | -9.28 USD (-0.93 %) | -9.28 USD (-0.93 %) |

### validation / baseline / horizontal: 23 vollständig von 28 Einstiegen

Mittleres Nettoergebnis je 1.000 USD Einsatz; in Klammern mittlere Prozentänderung. Unterschiedliche Gruppen können dieselben physischen Einstiege enthalten.

| Ausstieg | 5 Tage | 10 Tage | 20 Tage |
|---|---:|---:|---:|
| Zeitablauf | +12.65 USD (+1.26 %) | +11.75 USD (+1.17 %) | +13.73 USD (+1.37 %) |
| Fester Stop | +10.93 USD (+1.09 %) | +6.81 USD (+0.68 %) | +11.87 USD (+1.19 %) |
| Stop + 2R | +10.93 USD (+1.09 %) | +7.71 USD (+0.77 %) | +7.28 USD (+0.73 %) |
| Stop + Fakeout | +9.13 USD (+0.91 %) | +10.05 USD (+1.01 %) | +17.27 USD (+1.73 %) |
| Grün nachziehen | +5.65 USD (+0.57 %) | +0.31 USD (+0.03 %) | +0.31 USD (+0.03 %) |
| Stop + bekannter Widerstand | +7.92 USD (+0.79 %) | +2.91 USD (+0.29 %) | +4.59 USD (+0.46 %) |
| Tori-Kombination | +0.41 USD (+0.04 %) | -1.71 USD (-0.17 %) | -1.71 USD (-0.17 %) |

### validation / baseline / retest: 17 vollständig von 23 Einstiegen

Mittleres Nettoergebnis je 1.000 USD Einsatz; in Klammern mittlere Prozentänderung. Unterschiedliche Gruppen können dieselben physischen Einstiege enthalten.

| Ausstieg | 5 Tage | 10 Tage | 20 Tage |
|---|---:|---:|---:|
| Zeitablauf | +1.50 USD (+0.15 %) | -2.25 USD (-0.23 %) | +9.43 USD (+0.94 %) |
| Fester Stop | +1.56 USD (+0.16 %) | -1.00 USD (-0.10 %) | +6.39 USD (+0.64 %) |
| Stop + 2R | +2.08 USD (+0.21 %) | -3.24 USD (-0.32 %) | -1.80 USD (-0.18 %) |
| Stop + Fakeout | +8.72 USD (+0.87 %) | +16.17 USD (+1.62 %) | +24.95 USD (+2.50 %) |
| Grün nachziehen | +0.05 USD (+0.00 %) | -1.09 USD (-0.11 %) | -1.09 USD (-0.11 %) |
| Stop + bekannter Widerstand | -4.05 USD (-0.41 %) | -1.68 USD (-0.17 %) | -1.70 USD (-0.17 %) |
| Tori-Kombination | -3.75 USD (-0.38 %) | -3.75 USD (-0.38 %) | -3.75 USD (-0.38 %) |

### validation / momentum_two / breakout: 33 vollständig von 48 Einstiegen

Mittleres Nettoergebnis je 1.000 USD Einsatz; in Klammern mittlere Prozentänderung. Unterschiedliche Gruppen können dieselben physischen Einstiege enthalten.

| Ausstieg | 5 Tage | 10 Tage | 20 Tage |
|---|---:|---:|---:|
| Zeitablauf | +2.52 USD (+0.25 %) | +15.63 USD (+1.56 %) | +16.56 USD (+1.66 %) |
| Fester Stop | +0.96 USD (+0.10 %) | +5.13 USD (+0.51 %) | +7.27 USD (+0.73 %) |
| Stop + 2R | +0.96 USD (+0.10 %) | +4.18 USD (+0.42 %) | +1.39 USD (+0.14 %) |
| Stop + Fakeout | +0.94 USD (+0.09 %) | +9.91 USD (+0.99 %) | +16.51 USD (+1.65 %) |
| Grün nachziehen | -2.75 USD (-0.27 %) | -1.15 USD (-0.11 %) | -4.20 USD (-0.42 %) |
| Stop + bekannter Widerstand | -2.95 USD (-0.30 %) | -1.65 USD (-0.16 %) | -4.08 USD (-0.41 %) |
| Tori-Kombination | -10.90 USD (-1.09 %) | -10.90 USD (-1.09 %) | -10.90 USD (-1.09 %) |

### validation / momentum_two / horizontal: 19 vollständig von 24 Einstiegen

Mittleres Nettoergebnis je 1.000 USD Einsatz; in Klammern mittlere Prozentänderung. Unterschiedliche Gruppen können dieselben physischen Einstiege enthalten.

| Ausstieg | 5 Tage | 10 Tage | 20 Tage |
|---|---:|---:|---:|
| Zeitablauf | +8.73 USD (+0.87 %) | +2.10 USD (+0.21 %) | -3.74 USD (-0.37 %) |
| Fester Stop | +8.87 USD (+0.89 %) | +0.40 USD (+0.04 %) | -0.72 USD (-0.07 %) |
| Stop + 2R | +8.87 USD (+0.89 %) | +0.40 USD (+0.04 %) | -3.25 USD (-0.32 %) |
| Stop + Fakeout | +9.11 USD (+0.91 %) | +7.41 USD (+0.74 %) | +8.23 USD (+0.82 %) |
| Grün nachziehen | +3.95 USD (+0.40 %) | -3.15 USD (-0.31 %) | -3.15 USD (-0.31 %) |
| Stop + bekannter Widerstand | +12.20 USD (+1.22 %) | +7.72 USD (+0.77 %) | +8.82 USD (+0.88 %) |
| Tori-Kombination | +5.02 USD (+0.50 %) | +2.54 USD (+0.25 %) | +2.54 USD (+0.25 %) |

### validation / momentum_two / retest: 4 vollständig von 5 Einstiegen

Mittleres Nettoergebnis je 1.000 USD Einsatz; in Klammern mittlere Prozentänderung. Unterschiedliche Gruppen können dieselben physischen Einstiege enthalten.

| Ausstieg | 5 Tage | 10 Tage | 20 Tage |
|---|---:|---:|---:|
| Zeitablauf | +16.87 USD (+1.69 %) | +49.88 USD (+4.99 %) | +64.46 USD (+6.45 %) |
| Fester Stop | +16.87 USD (+1.69 %) | +48.22 USD (+4.82 %) | +54.09 USD (+5.41 %) |
| Stop + 2R | +16.87 USD (+1.69 %) | +48.22 USD (+4.82 %) | +54.54 USD (+5.45 %) |
| Stop + Fakeout | +15.59 USD (+1.56 %) | +51.55 USD (+5.16 %) | +57.42 USD (+5.74 %) |
| Grün nachziehen | -12.57 USD (-1.26 %) | -12.57 USD (-1.26 %) | -12.57 USD (-1.26 %) |
| Stop + bekannter Widerstand | +27.04 USD (+2.70 %) | +51.14 USD (+5.11 %) | +45.16 USD (+4.52 %) |
| Tori-Kombination | -7.39 USD (-0.74 %) | -7.39 USD (-0.74 %) | -7.39 USD (-0.74 %) |

## Prüfungen und Grenzen

Unabhängiger Preis-/Zeit-/Dezimalaudit: 14,994 Pfade, davon {'closed': 12724, 'censored': 2270}, 884 verschiedene nachgezogene grüne Linien und 252 Vergleichszeilen. Ausführliche Fallprotokolle, Einzelaktien, je Horizont verfügbare Fälle und Verlust-vor-späterem-Gewinn-Zählungen stehen in den lokalen JSON-Dateien.

Die Tabelle bevorzugt vollständig beobachtbare Strecken; deren Datenabdeckung kann systematisch von den ausgeschlossenen Fällen abweichen. Deshalb enthält results.json daneben alle bereits sicher beendeten Fälle und die Gründe unvollständiger Pfade. Solche Gruppen mit unterschiedlicher Abdeckung sind kein fairer direkter Modellvergleich. Fälle überlappen, fünf heutige Aktien bilden kein historisches Gesamtuniversum; keine statistische Unabhängigkeit, kein Beweis für zukünftige Gewinne. IEX ist ein Teilmarkt; Ausführung und Spreads sind Annahmen. Bruchstücke und splitbereinigte Kurse sind eine normierte Forschungseinheit, keine damalige Brokerabrechnung.

## Wiederholen

Im Anwendungsordner:

```text
python tools/exit_study.py --source artifacts/contact-loops-20261019-a --output artifacts/exit-study-neu
python tools/verify_exit_study.py --source artifacts/contact-loops-20261019-a --output artifacts/exit-study-neu
```

Ein vorhandener Ausgabeordner wird vom Lauf verweigert. Der Vertrag wird vor der Auswertung geschrieben und enthält Kohorte, Engine-Dateihashes, Ausgangsaufträge, Kosten und Phasengrenzen. Rohdaten/Verträge/Fallprotokolle bleiben lokal unter artifacts/ und werden nicht committed. Vorliegende Archivaufträge werden nur lesend geöffnet, nicht unter neuem Engine-Code fortgesetzt. Der neue CLI-Vergleich verändert keine Web- oder Worker-Standards. Kein Browser, keine neuen Providerabrufe, keine Brokerorders.

## Einordnung und konkrete Fälle

Im späteren Zeitraum bleiben beim Grundsignal-Ausbruch 44 von 63 Einstiegen über alle Modelle und Horizonte vollständig vergleichbar. Nach zwanzig Tagen beträgt das mittlere Nettoergebnis pro 1.000 USD ohne Stop +12,99 USD, mit festem Stop +0,94 USD, mit zusätzlichem Fakeout-Ausstieg +8,24 USD, mit Grün-Nachziehen −6,59 USD und mit der Tori-Kombination −9,28 USD. Der Verzicht auf einen Stop ist hier eine Vergleichsrechnung, keine Empfehlung. Vier der 44 Fälle enden mit dem festen Stop im Minus, obwohl der reine Zwanzig-Tage-Verlauf positiv ist. In der Fakeout-Variante treten 19 direkte Fakeout-Verkäufe auf, alle im Minus; sechs dieser Fälle wären beim reinen Zeitablauf nach zwanzig Tagen positiv gewesen. Zusätzlich sind sieben Fälle über anfänglichen Stop/Gap beendet worden; diese werden nicht nachträglich als bestätigte Fakeouts etikettiert.

Der scheinbar günstigere Fakeout-Ausstieg im späteren Zeitraum ist nicht stabil über beide Phasen: Im Entwicklungs-Ausbruch (109 vollständige Fälle) nach zwanzig Tagen −0,12 % mit Fakeout gegenüber +0,25 % mit festem Stop. Im späteren Grundsignal-Retest bleiben nur 17 vollständige Fälle, dort +2,50 % mit Fakeout gegenüber +0,64 % mit festem Stop. Momentum-Retests haben später nur vier vollständige Fälle; die dort hohen Mittelwerte sind kein belastbarer Strategiegewinn.

In der späteren Ausbruchgruppe (alle sicher beendeten Widerstandsmodell-Fälle des Grundsignals, nicht die auf 44 beschränkte Vergleichsgruppe) haben zehn von 42 Zielverkäufen nach Kosten ein negatives Nettoergebnis: Der vorher bekannte Widerstand liegt zu nahe am Kaufpreis. Der Eintrag bleibt im Vergleich enthalten, weil nachträglich geänderte Einstiege den gepaarten Ausstiegsvergleich verfälschen würden. Das spricht für eine gezielte spätere Prüfung des Raum-Merkmals und des Zielabstands nach Kosten, nicht für ein nachträgliches Entfernen dieser Verluste.

Die Beispiele sind rückblickend zur Erklärung gewählt. Zeiten in New York, jeweils normierte 1.000 USD, Kosten enthalten:

| Fall / Modell | Nach 5 Tagen | Nach 10 Tagen | Nach 20 Tagen |
|---|---:|---:|---:|
| JPM 23.03.2026 13:35, Entry 291,74 USD: reiner Zeitablauf | −28,81 USD | +18,04 USD | +71,27 USD |
| Derselbe Einstieg: ursprünglicher Stop 282,06235 USD | −34,62 USD | −34,62 USD | −34,62 USD |
| Derselbe Einstieg: zusätzlich Fakeout-Verkauf | −27,96 USD | −27,96 USD | −27,96 USD |
| JPM 20.03.2026 13:35, Entry 288,96 USD: ursprünglicher Stop bleibt unberührt | −22,94 USD | +21,31 USD | +95,74 USD |
| Derselbe Einstieg: Stop + 2R-Ziel | −22,94 USD | +21,31 USD | +51,31 USD |
| Derselbe Einstieg: Grün nachziehen | −10,62 USD | −10,62 USD | −10,62 USD |

Der Stop des ersten Falls wird am 27.03.2026 in der 5m-Kerze 15:45–15:50 getroffen. Beim Fakeout-Verkauf bestätigt der 4h-Schluss um 13:30 den Rückfall; gehandelt wird erst zum 13:35-Open, im Protokoll mit Kerzenende 13:40. Der zweite Fall zeigt das Gegenstück: Ein zwischenzeitlicher Verlust wird später zum Gewinn, wenn der ursprüngliche Stop hält. Das frühe Grün-Nachziehen hätte die Erholung abgeschnitten. Eine höhere Gewinnquote allein genügt deshalb nicht zur Wahl eines Exits.

**Nächster sinnvoller Forschungsentscheid:** Keine neue Standardstrategie aus diesen Ergebnissen wählen. Die Umsetzung des frühen Nachziehens (auch nur zwei Kontakte, 0,01-USD-Puffer) und die sehr nahen Widerstandsziele anhand verblindeter Fälle prüfen. Anschließend wenige fachlich begründete Regeln vorab festhalten und erst dann den reservierten finalen Zeitraum einmal verwenden. Für einen gesamten Depot-Endwert wären zusätzlich Kapital, Positionsgröße, konkurrierende/überlappende Signale, Stückelung und Wiederanlage verbindlich zu simulieren; die hier berichteten Mittelwerte beantworten das Ergebnis pro Einstieg.

Lokaler Vertrag: `artifacts/exit-study-20261019-a/contract.json`, SHA-256 des kanonischen JSON `01921faddd0ecfed4a5bd34bc52408d5826316cd87e45939efca1a0cf3d7fd49`. Audit in `verification.json`, Fälle in `results.json`. 714 Profil-/Familienfälle über beide Phasen, keine 714 unabhängigen Trades; jeder Fall wird in 21 Modell-/Horizontkombinationen wiederverwendet.
