# Gewinner-/Verlierer-Backtest: Bilanz des erweiterten Bestands

Abgeschlossen am 01.11.2026. [Vollständige Tabellen und Beispiele](BACKTEST-UNIVERSEN-ERGEBNISSE-20261101.md), [vorab festgelegte Regeln](BACKTEST-UNIVERSEN-PLAN-20261101.md).

## Umfang

Dow Jones, Nasdaq-100 und S&P 500 sind als lokal gespeicherte ETF-Bestandslisten vom 28.10.2026 enthalten: 30 / 101 / 505 Aktienklassen, vereinigt 520 unterschiedliche Titel. 512 haben genug Historie für mindestens eines der unveränderten Entryfenster 2018, 2021, 2023 und April 2025 bis März 2026. Nachbeobachtung bis 29.10.2026, 15:25 UTC. 71 einzelne Aktien-/Fensterkombinationen fehlen wegen zu wenig Vorlauf; acht ansonsten geeignete Aktien haben in den gewählten Fenstern überhaupt kein dedupliziertes Signal.

Ergebnis: **39.440 Fälle aus 27.072 Episoden**, 59.847 Fortsetzungs-/Alternativsignale unterdrückt, **35.424 modellierte Fills**. Alle fünf bisherigen Exitvarianten wurden angewandt. Keine Zeitexits, Take Profits oder gemeinsamen Kapital-/Slotlimits. Je Fall gleicher nominaler Einsatz von 1.000 USD mit fraktionalen Stückzahlen und den bisherigen Kosten. Zweikontaktlinien bleiben eine eigene Testklasse; die folgenden Hauptzahlen betreffen qualifizierte Entries.

## Die bisherige Referenz: aktuelle Safety

| Einstieg | Signale | Gefüllt | Geschlossen | Gewinner | Verlierer | Trefferquote geschlossen | Ø netto geschlossen | Median netto geschlossen |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Ausbruch | 6.883 | 6.226 | 6.028 | 2.171 | 3.857 | 36,02 % | +0,14 % | −0,94 % |
| Roter Retest | 4.362 | 4.022 | 3.918 | 1.323 | 2.595 | 33,77 % | +0,06 % | −0,85 % |
| Safety-Bounce | 6.099 | 5.971 | 5.832 | 1.507 | 4.325 | 25,84 % | −0,08 % | −0,98 % |

198 / 104 / 139 gefüllte Fälle sind bei dieser Variante wegen Datenlücken unbekannt, keiner bleibt offen. Nicht gefüllte Signale sind weder Gewinne noch Verluste. Diese Mittelwerte sind Einzelfallrenditen, **keine Depot- oder Indexrenditen**. Die typischen Fälle verlieren; größere Gewinner tragen die kleinen positiven Mittelwerte. Gegenüber dem bisherigen 69er-Bestand sinken die qualifizierten Ausbruchs-/Retestmittel von ungefähr +0,60/+0,47 % auf +0,14/+0,06 %. Der breitere Bestand bestätigt daher keinen starken allgemeinen Vorteil.

## Unterschiede zwischen den Universen

Qualifizierte, geschlossene Fälle mit aktueller Safety, gleiche Regeln:

| Universum | Ausbruch: Ø netto | Roter Retest: Ø netto | Safety-Bounce: Ø netto |
|---|---:|---:|---:|
| Dow Jones | +0,35 % | +0,28 % | +0,19 % |
| Nasdaq-100 | +0,49 % | +0,26 % | +0,13 % |
| S&P 500 | +0,13 % | +0,07 % | −0,09 % |

Nasdaq-Ausbrüche und die Dow-Gruppe schneiden in dieser Referenz besser ab als der breite S&P-Bestand. Die Mitgliedschaften überlappen; Ergebnisse nicht addieren. Dies sind heutige Bestände, keine historisch vollständigen Indexuniversen. Ein nachträglicher Wechsel zum besten Universum wäre eine neue Auswahlhypothese und keine unabhängige Erfolgsbestätigung.

## Die Exitfrage bleibt offen

Auf allen jeweils verfügbaren geschlossenen Fällen steigen die Ausbruchs-/Retestmittel mit ausschließlich qualifizierter neuer Safety auf +0,30/+0,33 %, mit neuer Safety erst ab +2R auf +0,40/+0,44 %. Dabei sinken die Trefferquoten und die Verlustmediane verschlechtern sich. Unterschiedliche Datenlückenzensierung macht diese Mittelwerte allein nicht zu einem fairen Modellvergleich.

Auf **identischen gemeinsam bewertbaren Fällen** aller vier nachgezogenen Safetys ergibt sich:

| Modell | Ausbruch: Ø Bewertung | Roter Retest: Ø Bewertung |
|---|---:|---:|
| Aktuelle Safety | −0,02 % | −0,06 % |
| Nur qualifizierte neue Safety | +0,07 % | +0,13 % |
| Neue Safety erst ab +2R | +0,12 % | +0,15 % |
| Ursprüngliche Safety | +2,45 % | +1,50 % |

Bewertung umfasst geschlossene Ergebnisse und separat bekannte offene Netto-Buchwerte. Die ursprüngliche Safety hält in diesen Gruppen noch 60 beziehungsweise 35 Fälle offen; ihre hohe Bewertung ist kein regulär realisierter Exitgewinn. Bei der +2R-Variante sind es drei beziehungsweise ein offener Fall. Die gemeinsame Teilmenge kann durch Datenlücken ebenfalls selektiv sein.

Ohne die drei besten Fälle bleiben beim +2R-Modell in diesen gemeinsamen Gruppen nur etwa +0,03/+0,02 % übrig. Auch das ist bloß eine nachträgliche Konzentrationsdiagnose. Beim Safety-Bounce sind auf den gemeinsamen bewertbaren Fällen alle vier Varianten im Mittel negativ. Es gibt damit weiterhin keinen belastbar freigegebenen automatischen Gewinnerfilter und keinen allgemeinen Gewinner beim Exitvergleich.

## Einzelne Aktien und Trades

Mit qualifizierten Entries und aktueller Safety zählen beispielsweise CVNA-Retest Juni–August 2023 **+166,19 %**, ASML-Ausbruch August 2025–Juni 2026 **+156,76 %** und PLTR-Ausbruch Mai–Juli 2023 **+93,78 %** zu den größten geschlossenen Gewinnern. Dem stehen unter anderem TSLA-Ausbruch Januar–März 2021 **−35,60 %** und FTNT-Retest Oktober–November 2023 **−22,13 %** gegenüber.

Die Ursachen unterscheiden sich: Beim genannten TSLA-Fall lag der anfängliche Stop rund 42,43 % unter dem modellierten Fill. Beim FTNT-Retest waren es nur etwa 2,93 %, der Stop wurde jedoch durch ein Openinggap weit unterschritten. Ein enger geplanter Stop begrenzt den tatsächlichen Gapverlust nicht auf diesen Abstand. Das ist in den vorhandenen Ausführungsregeln berücksichtigt, kein fehlender pauschaler Verkauf zum Wunschpreis.

Die Aktienübersicht enthält auch Fallzahlen: ASML erreicht beispielsweise +19,27 % geschlossenes Mittel aus neun Fällen, PLTR +6,88 % aus 17; SMCI liegt bei −3,40 % aus 21. Das sind beschreibende bekannte Ergebnisse, keine vorab verfügbaren Aktienempfehlungen. 22 geeignete Aktien haben in den gewählten Fenstern kein qualifiziertes Signal; die vollständige CSV zeigt sie trotzdem.

## Was bleiben und was als Nächstes geprüft werden sollte

Beibehalten: kausale Entryberechnung, feste Episodenherkunft, Deduplizierung, getrennte Entryfamilien, realistische Gap-Fills, Kosten und offene/unbekannte Status. Technisch funktioniert die breite automatische Signalsuche.

Die nächste Forschung sollte die Anfangsstop-Geometrie und die Qualität der Ausbruchs-/Retest-Aufbauten erklären, statt einfach weitere Exitparameter zu optimieren. Sehr weite anfängliche Abstände und sehr kleine Anfangsrisiken mit riesigen R-Ausreißern getrennt untersuchen. Einen eventuellen Abstandsfilter vorab festlegen und auf neuen Daten prüfen; keine optimale Grenze aus dieser Gewinnerliste übernehmen. Safety-Bounce als eigene, im breiten Bestand bisher schwache Hypothese weiterführen. Datenlücken und die Zensierung länger gehaltener Fälle bleiben wesentlich. Ein späteres ausführbares Depot mit Risikoallokation ist ein eigenes Experiment.

## Dateien und Prüfung

Privat unter `artifacts/exit-followup-population-20261101/`:

- `stock-overview.csv`: 520 Titel, je eine Zeile; qualifizierte Entries mit aktueller Safety, Gewinner/Verlierer, Mittel/Median und mittlere Gewinner-/Verliererrendite.
- `stock-summary.csv`: feinere Aufschlüsselung nach Aktie, Entryfamilie, Kontaktklasse und Exitmodell.
- `universe-summary.csv`, `window-summary.csv`: Gruppen- und Zeitvergleich.
- `trades-by-universe.csv`: 197.200 eindeutige Fall-/Modellzeilen mit ursprünglichem Entry, Anfangsstop, Exit, Netto-%/R und Universumszuordnung; offene Buchwerte getrennt.
- `coverage.csv`: alle 520 Titel, Eignung je Fenster, Fälle/Fills und bekannte 4h-Quellenlücken.
- `largest-winners.csv`, `largest-losers.csv`: größte geschlossene qualifizierte Referenzfälle.

Alle Fälle und Modellstatus wurden auf kausale Verfügbarkeit, Stopanpassungen und Rechnung geprüft; **4.965 Modellpfade** zusätzlich unabhängig auf tatsächlichen 5m-Kerzen nachgerechnet. 469 Signalfälle aus fünf zusätzlichen Aktien sind auf abgeschnittener Historie identisch. Alle CSV-Zähler und Gruppenmittel wurden aus dem Export erneut aggregiert. 68 unveränderte Kontrollaktien und alle alten Kennzahlen/CSV reproduziert. 26 gezielte Tests bestanden. Keine API-Abfrage, kein Browsertest, keine Veröffentlichung und keine neuen Handels-/Scannerdefaults.
