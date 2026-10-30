# Kandidatenversuch – Ergebnis und Grenzen (22.10.2026)

## Was umgesetzt wurde

- Vor der Auswertung gespeicherter Versuchsplan und feste Daten-/Engine-Bindung.
- 20 zufällige SIP-Präfixe für die blinde Linienprüfung in der vorhandenen Sichtprüfung. Keine menschlichen Bewertungen erfunden.
- Merkmale und fünf vor Ergebnisbetrachtung gespeicherte Zufallskontrollen je geeignetem Retest; 5/10/20 Handelstage sowie fixierte und nachgezogene Safety.
- Separate Kandidatenansicht mit Originalankern, zusammengefassten ähnlichen Geometrien, Zuständen und Warnungen. Eine ähnliche Variante darf das Signal der ursprünglichen Linie nicht umbenennen.
- 28 Kapitalledger mit denselben Kosten und Risikobudgets; fünf separate Kontrolldepots statt fünffachem Kapitaleinsatz.
- Getrennter prospektiver SIP-Beobachter mit Registrierung, Revisionserkennung, Wiederaufnahme, paginiertem Journal, Importbudget und CLI/API. Der alte IEX-Beobachter bleibt unverändert.

## Grundgesamtheit und Methode

349 4h-Retests in 60 Aktien; 349 eindeutige Aktie/Einstiegszeit-Kombinationen. Die gemeinsame Vergleichsmenge mit dem früheren IEX-Versuch umfasst 335 Retests in 57 Aktien. CRM, KO und LOW werden nur aus diesem zusätzlichen Feedvergleich herausgehalten, nicht aus der vorab festgelegten SIP-Hauptgruppe.

Daten: SIP, splitbereinigt, reguläre XNYS-Sitzungen, 5m-Ausführungspfad; Rohhistorie ab 27.07.2020, ein Jahr Vorlauf, Untersuchung bis 21.10.2026. Es handelt sich um bereits untersuchte Zeiträume und ein heutiges Aktienuniversum. Delistete Titel und ein historisch vollständiges Universum fehlen.

Das age7-Profil verlangt mindestens drei unabhängige Reaktionen an der Aktionslinie, zwei an der Safety und sieben Tage Alter. Momentum, Safety-Abstand, Kontext, Raum und Unternehmensereignisse werden zusätzlich als Merkmale/Warnungen erfasst. Dies ist ausdrücklich keine Behauptung, dass alle Tori-Filter bei jedem der 349 Einstiege erfüllt waren.

Kontrollen: gleiche Aktie, New-York-Uhrzeit, Kalenderquartal und Seite des damals bekannten MA20; mindestens 20 Handelstage vom Original entfernt. Aus den 20 nächsten bekannten ATR/Kurs-Nachbarn werden bis zu fünf mit festem Zufallsseed ausgewählt. Der anfängliche prozentuale Stoppabstand wird übertragen. Die horizontale grüne Kontrollreferenz ist kein nachträglich entdeckter Trend.

Kontrollen sind rückblickende Vergleichsfälle und können innerhalb des Quartals vor oder nach dem Signal liegen. Ihre späteren Ergebnisse oder Datenlücken beeinflussen die Auswahl nicht. Die Methode isoliert keinen kausalen Effekt. Fehlende ganze Panels werden ausgewiesen; sie können trotzdem verbleibenden Auswahlbias verursachen.

Kosten je Seite: 0,075 % (halber 5-bp-Spread und 5 bp Slippage), keine Ordergebühr. 5/10/20 bedeutet folgende reguläre Handelssitzungen nach dem Einstiegstag. Kursentwicklung ignoriert einen vorherigen Stopp; Stoppmodelle schließen beim simulierten Stopp oder bewerten eine noch offene Position am Horizont. Diese Horizonte sind keine neu eingeführten Tori-Take-Profits.

## Vorab festgelegter Hauptvergleich

| Horizont | Bewertung | Bekannte Originale / 349 | Vollständige 5er-Panels | Vorteil gegenüber Kontrollen | Beschreibendes Unsicherheitsband |
|---|---|---:|---:|---:|---|
| 5 | Kursentwicklung | 342 / 349 | 268 | 0.474 pp | -0.285 bis 1.189 pp |
| 5 | Fixierte Safety | 343 / 349 | 269 | 0.059 R | -0.078 bis 0.186 R |
| 5 | Bestätigte höhere Tiefs | 343 / 349 | 269 | 0.053 R | -0.083 bis 0.177 R |
| 10 | Kursentwicklung | 337 / 349 | 262 | 1.594 pp | 0.430 bis 2.734 pp |
| 10 | Fixierte Safety | 338 / 349 | 264 | 0.198 R | 0.001 bis 0.388 R |
| 10 | Bestätigte höhere Tiefs | 339 / 349 | 265 | 0.172 R | -0.028 bis 0.352 R |
| 20 | Kursentwicklung | 322 / 349 | 249 | 2.556 pp | 0.621 bis 4.400 pp |
| 20 | Fixierte Safety | 329 / 349 | 254 | 0.307 R | 0.020 bis 0.580 R |
| 20 | Bestätigte höhere Tiefs | 330 / 349 | 255 | 0.227 R | -0.029 bis 0.457 R |

Der primäre 20-Tage-Kursvergleich liegt positiv. Der entsprechende Vorteil unter fixierter Safety beträgt rund 0,307 R; bei nachgezogenen höheren Tiefs umfasst das Band null. Das bedeutet einen interessanten historischen Befund, keinen validierten handelbaren Vorteil. Die Bänder sind die Hülle separater Aktien- und Quartals-Cluster-Bootstraps mit 500 festen Ziehungen, ohne Korrektur für viele Vergleiche und ohne garantierte Abdeckung. Überlappende Fälle sind keine unabhängigen Trades.

## Stabilität zwischen den Zeitphasen

| Phase | Fälle | 20-Tage-Bewertung | Panels | Vorteil | Band |
|---|---:|---|---:|---:|---|
| 2021-2023 | 172 | market | 107 | 4.180 pp | 1.453 bis 6.386 |
| 2021-2023 | 172 | fixed | 111 | 0.542 R | 0.091 bis 1.015 |
| 2021-2023 | 172 | higher_low | 112 | 0.412 R | 0.035 bis 0.853 |
| 2024-2026 | 177 | market | 142 | 1.332 pp | -1.282 bis 4.221 |
| 2024-2026 | 177 | fixed | 143 | 0.125 R | -0.193 bis 0.454 |
| 2024-2026 | 177 | higher_low | 143 | 0.082 R | -0.179 bis 0.360 |

Der Vorteil ist in der frühen Phase deutlich stärker. In 2024–2026 umfassen alle drei 20-Tage-Vergleichsbänder null. Deshalb wird daraus kein automatisch optimierter Gewinn-Score und kein neuer harter Filter abgeleitet.

## Merkmale: Hinweise statt nachträglicher Optimierung

| Vorbekanntes Merkmal | Fälle | Panels, fixierte Safety 20 Tage | Mittlere Originalbewertung (R) | Vorteil (R) |
|---|---:|---:|---:|---:|
| contacts/3 | 301 | 218 | 0.130 | 0.334 |
| contacts/4+ | 48 | 36 | -0.205 | 0.143 |
| age/14–30 | 127 | 99 | 0.054 | 0.029 |
| age/30+ | 160 | 111 | 0.021 | 0.601 |
| age/7–14 | 62 | 44 | 0.335 | 0.191 |
| riskATR/<=2 | 79 | 50 | -0.139 | -0.112 |
| riskATR/>2 | 270 | 204 | 0.152 | 0.410 |
| momentum/pass | 64 | 44 | -0.167 | 0.076 |
| momentum/warn | 285 | 210 | 0.143 | 0.355 |
| context/pass | 101 | 86 | 0.005 | 0.156 |
| context/unknown | 57 | 38 | 0.238 | 0.627 |
| context/warn | 191 | 130 | 0.087 | 0.313 |
| room/pass | 29 | 21 | -0.369 | -0.467 |
| room/warn | 320 | 233 | 0.131 | 0.377 |
| greenContacts/2 | 309 | 223 | 0.097 | 0.290 |
| greenContacts/3+ | 40 | 31 | 0.005 | 0.428 |

Mehr Kontakte, engerer Safety-Abstand, Momentum oder der vorhandene Raumfilter verbessern die Ergebnisse hier nicht durchgehend. Die kleinen Untergruppen und die wechselnden Phasen verbieten eine belastbare Rangfolge. Insbesondere wird ein großer Safety-Abstand nicht deshalb als gut erklärt, weil seine rückblickende Untergruppe besser abschneidet. Die Merkmale bleiben sichtbar und Warnungen bleiben bestehen. Unternehmensereignisse haben keine verifizierte Point-in-time-Abdeckung und sind unbekannt.

## Kapital und Exits

Annahmen: 2.000 USD, 1 % geplantes Risiko je Position, höchstens 25 % Kapitaleinsatz je Position, fünf gleichzeitige Positionen, Bruchteile, eine Position je Aktie. Abgelehnte Einstiege und gleichzeitig belegtes Kapital bleiben Teil der Simulation. Ein fehlender Kurs in einer gehaltenen Position stoppt weitere Depotentscheidungen. Offene Schlussbewertungen sind keine realisierten Gewinne.

| Phase / Gruppe | Exit | Status | Angenommen / offen | Gesamte Depotbewertung (%) | Realisierter P/L (USD) |
|---|---|---|---:|---:|---:|
| 2021-2023 / all_actual | fixed | incomplete | 12 / 5 | unbekannt | -85.715 |
| 2021-2023 / all_actual | higher_low | incomplete | 15 / 5 | unbekannt | -21.856 |
| 2021-2023 / matched_actual | fixed | incomplete | 10 / 5 | unbekannt | -88.867 |
| 2021-2023 / matched_actual | higher_low | incomplete | 11 / 5 | unbekannt | -55.242 |
| 2021-2023 / control_0 | fixed | incomplete | 8 / 4 | unbekannt | -86.294 |
| 2021-2023 / control_0 | higher_low | incomplete | 12 / 2 | unbekannt | -58.310 |
| 2021-2023 / control_1 | fixed | incomplete | 10 / 4 | unbekannt | -101.972 |
| 2021-2023 / control_1 | higher_low | incomplete | 11 / 3 | unbekannt | -53.404 |
| 2021-2023 / control_2 | fixed | incomplete | 10 / 4 | unbekannt | -120.529 |
| 2021-2023 / control_2 | higher_low | incomplete | 11 / 3 | unbekannt | -102.938 |
| 2021-2023 / control_3 | fixed | incomplete | 9 / 4 | unbekannt | -94.534 |
| 2021-2023 / control_3 | higher_low | incomplete | 10 / 2 | unbekannt | -74.771 |
| 2021-2023 / control_4 | fixed | incomplete | 10 / 4 | unbekannt | -114.648 |
| 2021-2023 / control_4 | higher_low | incomplete | 10 / 2 | unbekannt | -107.655 |
| 2024-2026 / all_actual | fixed | marked_to_phase_end | 12 / 5 | 20.491 | -105.832 |
| 2024-2026 / all_actual | higher_low | incomplete | 91 / 5 | unbekannt | 423.129 |
| 2024-2026 / matched_actual | fixed | marked_to_phase_end | 11 / 5 | 19.344 | -89.783 |
| 2024-2026 / matched_actual | higher_low | marked_to_phase_end | 128 / 0 | 23.548 | 470.953 |
| 2024-2026 / control_0 | fixed | incomplete | 13 / 5 | unbekannt | -133.119 |
| 2024-2026 / control_0 | higher_low | marked_to_phase_end | 125 / 0 | 6.077 | 121.539 |
| 2024-2026 / control_1 | fixed | incomplete | 19 / 5 | unbekannt | -220.601 |
| 2024-2026 / control_1 | higher_low | marked_to_phase_end | 127 / 0 | -9.791 | -195.825 |
| 2024-2026 / control_2 | fixed | incomplete | 21 / 5 | unbekannt | -228.071 |
| 2024-2026 / control_2 | higher_low | marked_to_phase_end | 129 / 1 | -13.360 | -290.892 |
| 2024-2026 / control_3 | fixed | marked_to_phase_end | 15 / 5 | 36.035 | -144.098 |
| 2024-2026 / control_3 | higher_low | marked_to_phase_end | 125 / 1 | -12.404 | -262.677 |
| 2024-2026 / control_4 | fixed | incomplete | 9 / 5 | unbekannt | -43.152 |
| 2024-2026 / control_4 | higher_low | marked_to_phase_end | 121 / 1 | -12.963 | -270.714 |

19 von 28 Depots sind unvollständig. Diese werden nicht aus der Bewertung gelöscht und bekommen keinen Gesamtertrag. Das volle Retest-Depot 2024–2026 mit fixierter Safety zeigt +20,49 % Schlussbewertung bei fünf offenen Positionen, aber −105,83 USD realisierten P/L. Das ist kein Beweis für abgeschlossene profitable Trades.

Einzelne vollständige Teilkohorten sind interessant, dürfen aber nicht den unvollständigen Gesamtvergleich ersetzen. Der nächste belastbare Exit-Vergleich benötigt vollständige gemeinsame Pfade und neue prospektive Beobachtungen. Die bekannten SIP-Lücken, unter anderem CVX 25.10.2021 und COST 23.08.2024/12.09.2025, werden nicht mit erfundenen Kerzen gefüllt; bereits untersuchte 1m-Abrufe lösten die alten Lücken nicht verlässlich.

## Prüfung und weiteres Vorgehen

Geprüft: Daten-/Engine-/Planhash, 349 Originale gegen eingefrorene Signale, 1569 Kontrollzuordnungen, 5537 vollständige 5m-Horizontpfade direkt nachgerechnet und neun paarweise Hauptmittelwerte unabhängig berechnet. Alle 28 Kapitalledger wurden separat auf Cash sowie Risiko-/Allokationsbudgets abgeglichen.

Jetzt nutzbar: manuelle Strukturprüfung, Merkmalsvergleich, nachvollziehbare Beobachtung und prospektive Papierfälle. Noch offen: deine unbeeinflussten Bewertungen der 20 SIP-Fälle, ausreichend neue Vorwärtsfälle, verlässlichere Lückenklärung und eine unabhängige Strategieprüfung. Ein LLM kann anschließend die gespeicherten Fakten erklären; es berechnet keine OHLC-Werte oder rückwirkenden Signale.

Keine Orders, keine externen Nachrichten, kein Container-Deployment, kein automatisch gewählter neuer Parametersatz. Der alte IEX-Lauf und die manuelle Chartfunktion bleiben bestehen.

Reproduzierbare Quellen: Studienvertrag, Auswahldateien, 60 Aktienblöcke, summary.json, matched57-summary.json, candidate-verification.json und 28 Cashledger im lokalen Laufverzeichnis. Laufzeitdaten und private Bewertungen werden nicht nach Git übernommen.

## Lokale technische Abnahme nach Fortsetzung

326 Python-Tests unter Python 3.12 und 3.13 bestanden (je ein bestehender Skip), 43 JavaScript-Tests bestanden. 21 echte lokale HTTP-Prüfungen bestätigen Navigation, API, ausdrückliche Zukunftsansicht und Schutzgrenzen. Controllerprüfungen sind keine visuelle Browserabnahme.

Der getrennte SIP-Beobachter hat alle 60 Aktien ohne Spurfehler aus der vorhandenen Historie eingelesen und wartet mit aktiver Prozesssperre auf neue reguläre Abschlüsse. Keine neuen prospektiven Papier-Einstiege; die 78 aktiven Geometriegruppen sind vorhandener Startbestand, keine 78 neuen Einstiegssignale. Ein separater echter AAPL-SIP-Probeimport war erfolgreich. Die lokale Bootstrap-Prüfung wird korrekt nicht als neuer Providerimport gezählt. Der IEX-Beobachter und bestehende Forschungszeitplan sind erhalten.

Die Vollsnapshotablage bleibt eine Betriebsgrenze: 4 GiB Importbudget je Registrierung, keine automatische Datenlöschung. Unbeaufsichtigter Großbetrieb benötigt eine sparsamere inkrementelle Datenablage.
