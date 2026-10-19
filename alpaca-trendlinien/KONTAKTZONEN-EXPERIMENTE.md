# Kontaktzonen: drei Entwicklungsrunden

Auftrag vom 19.10.2026: Kontaktmessung entkoppeln, anschließend insgesamt drei Runden aus Erkenntnis, Umsetzung, Code-Backtest und Auswertung. Keine Browserprüfung. Long; Schlusskursentwicklung nach **5, 10 und 20 Handelstagen separat**, keine nachträgliche Wahl des günstigsten Horizonts.

## Festgelegtes Vorgehen

- Echte Alpaca/IEX-Daten für MSFT, AMZN, JPM, XOM und KO. Einmaliger Import, 900 Kalendertage, Split-Bereinigung, reguläre XNYS-Sitzungen aus 5m-Daten. Alle Vergleiche danach offline auf denselben unveränderlichen Dataset-IDs. Keine synthetischen Marktergebnisse.
- Gemeinsamer zeitlicher Plan: Entwicklung 02.05.2025–18.03.2026 (220 Sitzungen); anschließende Validierung 19.03.2026–02.07.2026 (73); Holdout 06.07.2026–16.10.2026 (74) bleibt geschlossen. Signalzustand wird für spätere Phasen ab Entwicklungsbeginn nachgespielt; Labels enden an der jeweiligen Phasengrenze.
- Primärer Vergleich: direkter Ausbruch, mittlere Mehrentwicklung gegenüber kausal anhand bekannter Merkmale zugeordneten Zufallskontrollen nach zehn Handelstagen. Fünf und zwanzig Tage sowie Horizontalbestätigung/Retest bleiben separate sekundäre Auswertungen. Die Kontrollen werden nicht anhand ihres späteren Gewinns gewählt.
- Höchstens 20 verschiedene Profildefinitionen im gesamten Entwicklungsablauf, keine Schwellenwertsuche und kein nachträglicher Austausch schlechter Runden. Kandidaten mit weniger als 20 vollständigen Zehn-Tage-Beobachtungen oder weniger als drei beteiligten Aktien werden nicht als belastbare Auswahl behandelt. Auswahlentscheidung vor Validierung dokumentieren. Die Validierung darf zu einer Ablehnung führen, nicht zu einer vierten Optimierungsrunde.
- Bestehende Profile, Cent-Kontakte, Geometrie, Gültigkeit und Qualitätsklassen bleiben erhalten. Neue Profile sind ausdrücklich wählbare Experimente; keine automatische Zeitplanumstellung.
- Einstieg erst am verfügbaren 5m-Open nach abgeschlossener Bestätigung und fünf Minuten Latenz. Ein Docht genügt nicht. Absicherung darf nicht bereits verletzt sein. Neue Raumprofile interpretieren unbekannten Raum nicht als bestanden. Safety und Positionsgröße werden nicht zum Bestehen eines Filters verschoben.
- Zählung je Profil/Familie eindeutig nach Aktie und Einstiegszeitpunkt. Familien/Profile können denselben Zeitpunkt enthalten. Überlappende Verläufe sind abhängig. Erfolgsanteile verwenden ausschließlich vollständige Horizonte; fehlende Sitzungen und Phasengrenzen zählen nicht als Verlust oder Erfolg.
- Gemessen wird die rohe Kursänderung bis zum Schluss des jeweiligen zukünftigen Handelstags, keine realisierte Rendite einer Stop-/Ausstiegsstrategie. Die gesamte Zwischenstrecke muss Tagesdaten enthalten. Eine später positive Schlusskursänderung kann trotzdem vorher einen Stop verletzt haben. Keine Brokerorders.

## Runde 1 – Kontaktmessung isolieren

Implementiert: `contact_zones.py`, zusätzliche Profile in `lab_profiles.py`, getrennte Merkmalsgruppen in `lab_metrics.py`. Zone = `max(0,01 USD, 0,05 × damals bekannte 4h-ATR)`; bei Setupaufnahme gespeichert. Unveränderte Anker und Liniengültigkeit. Kontaktepisoden werden mit demselben Kerzenabstand zusammengefasst; eine breite Zone kann Berührungen auch zu einer Episode zusammenführen. Sie garantiert keine höhere Zahl.

Profile: alte Referenz, Grundsignal, altes `contacts3`, reine Zonenmessung, Rot ≥3/Grün ≥2, Grün ≥3/Rot ≥2, beide ≥3 sowie Referenz mit ausschließlich ersetzter Kontaktmessung. Die alte Qualität „vorläufig/qualifiziert“ wird nicht umbenannt.

Ergebnis: 888 identische Quell-Linienpaare zwischen Grundsignal und reiner Zonenmessung, identische Anker und identische Einstiegszeitpunkte aller drei Familien. Beide liefern 235 eindeutige Aktie-/Einstiegszeitpunkte. Unter 309 auswertbaren Ausbruchspaaren hatten 265 mit Cent-Messung an beiden Linien genau zwei Kontakte. Die feste Zone erkennt 65 Fälle mit Rot ≥3, 12 mit Grün ≥3 und zwei mit beiden ≥3. Das ist keine unabhängige Stichprobe von 309 Trades.

Mit den jeweiligen Kontaktfiltern verbleiben 56 eindeutige Zeitpunkte für Rot ≥3, 13 für Grün ≥3 und zwei für beide ≥3. Strenge Referenz und alte Drei-Kontakt-Bedingung bleiben ohne Entry. Zusätzliche Kontakte zeigen keinen durchgängigen Vorteil über alle Horizonte; einzelne kleine Gruppen dürfen nicht als robuste Verbesserung gelten.

Grundsignal nach Familien: 166 Ausbruch-, 86 Horizontal- und 54 Retestzeitpunkte, teilweise identisch. Beim direkten Ausbruch sind nach 5/10/20 Tagen 129/122/110 Beobachtungen vollständig; positive Anteile 51,2/43,4/51,8 %, mittlere Rohänderung +0,02/−0,38/+0,81 %, mittlere Mehrentwicklung zu Kontrollen −0,70/−1,01/−0,86 Prozentpunkte. Retests sind in dieser Entwicklung günstiger, aber nach zehn/zwanzig Tagen ebenfalls ohne positiven mittleren Kontrollvorsprung.

Konsequenz: Kontakte als Merkmale erhalten; drei an beiden Linien nicht pauschal verpflichtend machen. Nächste Runde untersucht Momentum und bekannten Raum einzeln, da Referenzablehnungen häufig Safety-/Raum- und Formprüfungen enthalten. Häufige Blocker sind keine nachgewiesenen Ursachen schlechter Renditen.

## Runde 2 – Momentum und Raum getrennt

Vor dem Lauf ergänzt: `momentum_two` verlangt positiven Körper und zwei nachweislich bestandene Merkmale aus Körper/ATR, Körperanteil und Schlussposition. Das alte Momentumprofil verlangt weiterhin alle. `room_15` ändert ausschließlich die bekannte Raumgrenze von 2R auf 1,5R, auch bei der tatsächlichen Einstiegsprüfung. Unbekannter Raum blockiert beide Raumprofile. Gemeinsame Scanneroptionen werden nicht verändert. Referenz und Grundsignal laufen als Kontrollen mit.

Ergebnis: Mit allen Momentum-Bedingungen 131 eindeutige Aktie-/Einstiegszeitpunkte, mit zwei von drei 159. Direkte Ausbrüche steigen von 94 auf 112 (vollständige Zehn-Tage-Pfade 77 auf 90); mittlere Rohänderung nach zehn Tagen +0,12 % gegenüber −0,04 %, Kontrollvorsprung −0,54 gegenüber −0,51 Prozentpunkten. Die zusätzliche Abdeckung ist keine durchgängige Qualitätsverbesserung. Retestfälle steigen von 17 auf 27; vollständige 5/10/20-Tage-Pfade 21/20/20 mit 66,7/60,0/70,0 % positiven Verläufen, Rohänderung +0,79/+0,68/+2,28 %, Kontrollvorsprung +0,40/+0,15/−0,24 Prozentpunkten. Das bleibt eine explorative, teilweise überlappende Stichprobe.

Bekannter Raum ≥2R liefert drei eindeutige Zeitpunkte, ≥1,5R fünf. Diese Gruppen sind zu klein für eine belastbare Auswahl. Aus der Lockerung folgt kein Beleg, dass die Raumdefinition gut genug als harter Filter ist. Raum bleibt im nächsten kombinierten Profil eine offen ausgewiesene Diagnose; unbekannter Raum wird nicht als ausreichend ausgegeben.

## Runde 3 – Safety isolieren und eine Kombination prüfen

Vor dem dritten Lauf ergänzt: `risk_5` verändert gegenüber `risk` nur die Prozentgrenze von 3 auf 5; die ATR-Grenze bleibt bei 2 und dieselbe grüne Safety unverändert. `momentum_two_risk5` kombiniert genau diesen Filter mit positivem Körper und zwei bestätigten Momentum-Merkmalen. Kontaktzonen werden eingefroren gemessen, zusätzliche Kontakte und Raum bleiben Diagnosen. Keine verpflichtenden drei Kontakte an beiden Linien. Verglichen werden außerdem Referenz, Grundsignal, reine Zonenmessung und Momentum 2 aus 3. Keine weiteren Profiländerungen nach dieser Runde.

Die drei Runden prüfen insgesamt 15 verschiedene Profile, innerhalb des vorab begrenzten Budgets von 20. Die isolierten Profile bleiben für weitere Forschung wählbar; ein kombiniertes Profil wird nicht allein wegen einiger positiver Beispiele zum neuen Standard erklärt.

Ergebnis: Safety 3 % liefert 91 eindeutige Zeitpunkte, Safety 5 % 95. Die zusätzliche Abdeckung bleibt klein; die ATR-Grenze blockiert weiter. Die Kombination liefert 48 Zeitpunkte. Bei direkten Ausbrüchen liegt die mittlere Zehn-Tage-Mehrentwicklung aller untersuchten Profile weiterhin unter null. Vor Öffnen der Validierung wird deshalb **kein auswählbarer Kandidat** festgehalten. Die sieben vorregistrierten Profile werden anschließend unverändert beschreibend geprüft; daraus wird keine vierte Entwicklungsrunde gemacht.

Die Kombination zeigt im Entwicklungs-Retest sieben vollständige Zehn-/Zwanzig-Tage-Beobachtungen mit jeweils sechs positiven Verläufen und im Mittel +3,36/+4,68 %. Das ist eine kleine Teilgruppe. Im späteren Zeitraum bleiben nur zwei Retest-Einstiege und ein vollständiger Pfad: −1,00/−2,18/+1,30 % nach 5/10/20 Tagen. Die attraktive Entwicklungsquote ist somit keine belastbare allgemeine Erfolgsquote.

## Getrennter späterer Prüfzeitraum

Validierung 19.03.–02.07.2026, ohne neue Regelauswahl. Grundsignal 94 eindeutige Aktie-/Zeitpunkte, Momentum 2 aus 3 60, Safety 3 % 25, Safety 5 % 28, Kombination zwölf. Der Holdout bleibt laut Datenbankreservierungen und Versuchsjournal ungeöffnet.

Die folgende Tabelle fasst innerhalb des Grundsignals die drei Familien nur für **rohe Kursänderungen** nach eindeutigem Aktie-/Einstiegszeitpunkt zusammen. Ein Zeitpunkt zählt einmal; verschiedene anfängliche Stops desselben Zeitpunkts begründen hier keine Depotbewertung. Die familiengetrennten vollständigen Tabellen stehen in [KONTAKTZONEN-ERGEBNISSE.md](KONTAKTZONEN-ERGEBNISSE.md).

| Phase | Horizont | positiv / vollständig | positiver Anteil | mittlere Rohänderung | mittlerer Kontrollvorsprung |
|---|---:|---:|---:|---:|---:|
| Entwicklung, 235 Zeitpunkte | 5 | 96/185 | 51,9 % | +0,06 % | −0,54 PP |
| Entwicklung | 10 | 79/176 | 44,9 % | −0,32 % | −0,92 PP |
| Entwicklung | 20 | 84/158 | 53,2 % | +0,84 % | −0,61 PP |
| Validierung, 94 Zeitpunkte | 5 | 46/89 | 51,7 % | +0,48 % | −0,10 PP |
| Validierung | 10 | 45/83 | 54,2 % | +0,70 % | −0,35 PP |
| Validierung | 20 | 37/69 | 53,6 % | +1,38 % | +0,48 PP |

Der Nenner für einen Kontrollvergleich kann kleiner als der für die Rohänderung sein, wenn passende Kontrollen fehlen. Erfolgsanteile und Renditemittelwerte verschiedener Horizonte beruhen wegen Lücken/Zensierung auf unterschiedlichen Fallzahlen. Die Zeilen bilden keine Kurskurve und keine Depotperformance.

Unter den 69 über alle zwanzig Sitzungen vollständigen Validierungszeitpunkten liegen 20 nach allen drei Horizonten im Plus. Rückblickende Beispiele (je Aktie der früheste solche Zeitpunkt, New Yorker Zeit; keine nachträgliche Einstiegsregel):

| Aktie | Entry | Open USD | nach 5 Tagen | nach 10 Tagen | nach 20 Tagen |
|---|---|---:|---:|---:|---:|
| AMZN | 01.04.2026 13:35 | 212,37 | +9,96 % | +17,58 % | +24,80 % |
| JPM | 19.03.2026 13:35 | 286,11 | +1,97 % | +3,01 % | +8,43 % |
| KO | 23.04.2026 13:35 | 76,39 | +3,12 % | +2,70 % | +6,23 % |
| MSFT | 08.04.2026 09:30 | 384,77 | +6,90 % | +12,48 % | +7,55 % |
| XOM | 21.04.2026 13:35 | 148,625 | +1,30 % | +4,21 % | +9,41 % |

## Schlussfolgerungen aus den drei Runden

1. Das starre Kontaktmaß ist behoben, ohne die Linienauswahl zu verändern. Die neue Messung ist als Zusatzmerkmal brauchbar; sie rechtfertigt keine pauschale Drei-Kontakt-Pflicht für beide Linien.
2. Gelockertes Momentum erhöht die Abdeckung, verbessert aber nicht jeden Horizont oder jede Familie. Es bleibt ein separat wählbares Profil.
3. Die Prozentgrenze allein erklärt die geringe Abdeckung der strengen Kriterien nicht. Ein enger Safety-Filter ist außerdem kein nachgewiesener Renditefilter. Die bekannte Raumdefinition ist in diesem Test für einen pauschalen Pflichtfilter zu restriktiv bzw. die verbleibende Stichprobe zu klein.
4. Die Suche findet viele rückblickend steigende Verläufe. Ein vorab erkennbarer, über Aktien und Zeitabschnitte belastbarer Vorteil ist damit **nicht nachgewiesen**. Insbesondere gewinnt das Grundsignal nach zehn Tagen im Mittel nicht gegen seine Kontrollen. Keine neue Standardstrategie aus den kleinen attraktiven Retestgruppen ableiten.
5. Als nächster Forschungsbedarf bleiben Datenabdeckung, weitere unabhängige Zeitabschnitte/Aktien und ein verblindeter Vergleich manueller gegen algorithmische Linien. Diese drei Optimierungsrunden werden hier beendet; die Validierung wird nicht erneut zum Trainingsmaterial für diesen Versuch gemacht.

## Tatsächliche technische Prüfung

- **170 Python-Tests** jeweils unter 3.12 und 3.13 erfolgreich, jeweils ein vorhandener Windows-Symlinktest übersprungen; **27 JavaScript-Tests** erfolgreich. Neue Tests: unveränderte Geometrie/Entryzeiten/Qualität, feste Zone trotz späterer Volatilität, Kontaktepisoden, fehlende ATR, separate Pflichtkontakte, Momentum-Abstimmung mit unbekannten Werten, unveränderte gemeinsame Optionen, konstante ATR-Grenze und Safety sowie Statistiknenner und Schutz vor stiller Rundenwiederholung.
- Alle drei Entwicklungsaufträge und die separate Validierung erfolgreich. Laufzeiten etwa 116/98/106/131 Sekunden auf diesem Rechner, ohne Kapazitätsversprechen für Proxmox. Nach einmaligem Datenimport wurden Providerzugriffe während sämtlicher Scans explizit gesperrt.
- Unabhängige Verifikation aus den gepinnten Kursdateien: 7.328 vollständige Haupthorizonte mit Dezimalarithmetik neu berechnet, 2.302 unvollständige Horizonte geprüft, 28.854 Kontrollhorizonte geprüft und 69 zusammengefasste Horizontstatistiken nachgerechnet. Diese Prüfungen enthalten wiederverwendete Zeitpunkte und sind keine Zahl unabhängiger Trades.
- Grundsignal-Zeitpunkte und zugehörige Schlusskursbeobachtungen sind in allen drei Entwicklungsrunden identisch; die reine Zonenmessung verändert sie in keiner Runde. Die Auswertung früher abgelehnter Kontakte verwendet den tatsächlichen Bruchzeitpunkt statt des alten Aufnahmezeitpunkts einer noch nie bestätigten Variante.
- **Keine Browserprüfung durchgeführt**, wie beauftragt. Keine Brokerorders, kein Containerupdate, keine Änderung bestehender Zeitpläne oder bereits gespeicherter Marktdatasets.


## Reproduzierbarkeit und Prüfung

`tools/contact_study.py` registriert jeden Lauf vor Start, speichert Hypothese, Daten-/Engine-IDs, vorgelagerte Erkenntnis und tatsächliche Queue-ID. Er verweigert stilles Wiederholen eines bereits registrierten Rundenvertrags und sperrt Providerzugriffe während des Scans. `tools/verify_contact_study.py` berechnet gespeicherte vollständige Kursänderungen unabhängig mit Dezimalarithmetik und Tageskalender neu; prüft auch fehlende Horizonte, eindeutige Zeitpunkte und tatsächliche 5m-Openpreise nach Latenz.

Lokale Laufartefakte: `artifacts/contact-loops-20261019-a/`. Rohkurse, Datenbanken und lokale Exporte gehören nicht ins Repository. Nachvollziehbare zusammengefasste Ergebnisse und Regeln stehen in diesem Dokument; Dateien sind lokal für vertiefte Prüfung verfügbar. Ein GitHub-Upload oder Containerupdate ist nicht Teil dieses Auftrags.


### Befehle

Im Anwendungsordner (Python aus der Projektumgebung verwenden):

```text
python tools/contact_study.py --root artifacts/contact-study-new --prepare
python tools/contact_study.py --root artifacts/contact-study-new --round 1
python tools/verify_contact_study.py --root artifacts/contact-study-new --label round-1
```

Jede weitere Runde verlangt dokumentierte `--hypothesis`, `--finding` und explizite `--profiles`. Historische Codefassungen sind am im Rundenvertrag gespeicherten Engine-Hash erkennbar. Der aktuelle Code kann die alten Einzelprofile zusätzlich im selben Lauf vergleichen; das ersetzt keine erneute unabhängige Validierung. `--round 3 --validation` startet die vorregistrierte Validierung des dritten Experiments ohne neue Auswahl anhand ihrer Ergebnisse. Derselbe Ordner darf für eine abgeschlossene Runde nicht still wiederverwendet werden.


### Abschlussaudit des endgültigen Codes

Ein zusätzlicher Reproduktionslauf (keine vierte Optimierungsrunde) prüfte alle 15 zuvor verwendeten Profile gemeinsam auf denselben Entwicklungsdaten. Auftrag `c2942acd138e49bd8f85eb4e0b16d66c` erfolgreich, 13.320 gespeicherte Linienpaare. Alle 22 Profil-/Rundenvergleiche reproduzieren die physischen Entryzeitpunkte, Entryopenpreise und vollständigen/unvollständigen 5-/10-/20-Tage-Ergebnisse der drei Originalrunden. Engine-Hash des tatsächlich abschließend geprüften Codes: `211ea26679c60719e93ae4ebad24ba526729448d3db8cf52fe9eb68ced2d8009`.

Der zusätzliche Prüffall stellt sicher, dass eine ausdrücklich höher konfigurierte rote Mindestkontaktzahl auch in `zone_reference` erhalten bleibt. Bei den echten Versuchen galt unverändert die Standardzahl zwei; deren Ergebnisse ändern sich dadurch nicht. Beim ersten Reproduktionsvergleich hatte ein Hilfsskript versehentlich eine ursprüngliche Profilliste im Speicher erweitert. Der Vergleich liest jetzt die unveränderten Originaldateien neu ein; die Korrektur verändert keine Backtestergebnisse.

Reproduktion prüfen: `python tools/verify_contact_study.py --root artifacts/contact-loops-20261019-a --release`. Die normale lokale Anwendung wurde im Leerlauf mit dem neuen Code neu gestartet; ein reiner HTTP-Test bestätigt alle neun zusätzlichen auswählbaren Profile. Dafür wurde kein Browser verwendet. Die drei Hauptrunden und die separate Validierung stehen in den vollständigen Ergebnistabellen; der zusätzliche Reproduktionslauf wird nicht als zusätzliche Stichprobe ausgewertet.
