# Interner Versuch: Linienkandidaten und frühe Beobachtung

Vorab festgelegter Forschungsvertrag vom 21.10.2026. Keine Änderung der Weboberfläche, bisherigen Profile oder Zeitpläne, keine Orders, Meldungen, Deployment oder Veröffentlichung. Parameter sind eigene Operationalisierungen; Tori-Nähe ist kein Profitabilitätsnachweis.

## Hypothesen und feste Modelle

1. `hull_exact`: bestehende Hüllengeometrie/ausgewählte rote Referenz und nächstgelegene gültige grüne Hüllenlinie. Kontaktmessung wie bisher. Gemeinsamer neuer Lebenszyklus/Trigger, deshalb kein behauptet identischer Ersatz alter Laborfälle.
2. `hull_episodes`: gleiche Geometrie, aber unabhängige Kontaktreaktionen in fester ATR-Zone. Isoliert die Kontaktdefinition.
3. `swing_envelope`: zusätzliche Geraden durch bestätigte Wendepunkte, striktes Nichtdurchschneiden aller Dochte. Eigene Kontaktreaktionen und mehrere begrenzte Zeithorizonte.
4. `swing_zone`: ausdrücklich andere experimentelle Strukturzonen. Dochte dürfen innerhalb der festen Zone über die Mittellinie ragen, Kerzenkörper dürfen die Mittellinie nicht schneiden. Kein stiller Wechsel der Tori-Regeln.

Alle Modelle: 4h-Struktur, XNYS-Sitzungen; Wendepunkte mit zwei linken und zwei rechten tatsächlich abgeschlossenen Nachbarn. Fenster 30/90/365 Kalendertage, höchstens zehn jüngste bestätigte Wendepunkte je Seite/Fenster für neue Kandidaten. Geraden durch alle zulässigen Punktpaare; Koordinaten pro vorhandener Quellkerze. Eine aufgezeichnete Gerade ändert ihre Anker nicht. Neue Kandidaten ersetzen keine alten Ereignisse rückwirkend.

Kontaktzone bei erster Aufnahme eingefroren: max(0,01 USD, 0,10 bekannte 4h-ATR14). Unabhängige Kontaktreaktion erst nach Entfernung um weitere 0,50 Aufnahme-ATR per späterem Kerzenschluss und mindestens zwei Kerzen Abstand. Ein Liniencluster hält die zuerst akzeptierte Geometrie; ähnliche Vorschläge werden als Alternativen gezählt. Gruppierung: höchstens 0,15 aktuelle ATR Niveauunterschied und 0,25 ATR Projektionsunterschied nach zwanzig Kerzenschritten. Keine nachträgliche Gewinnerwahl.

## Beobachtung und Einstiege

- Status bilden/struktur/annäherung/ausbruch/rücklauf/retest/ungültig/abgelaufen. Mindestens zwei Kontakte für aktive Beobachtung. Annäherung innerhalb 0,75 aktueller ATR unter der roten Oberkante. Pro Aktie/Modell/4h-Schluss höchstens drei erste Annäherungsmeldungen; nachvollziehbare Priorität aus Abstand, getrennten Reaktionen und Projektionssensitivität, keine Gewinnwahrscheinlichkeit.
- Ursprüngliche Linie zuerst gegen neue Kerze prüfen, erst danach neue Linien aufnehmen. Lebensdauer höchstens 60 Quellkerzen ab Aufnahme; Verletzung/Fehlausbruch schließen Kandidaten. Geometrisch unveränderte Kandidaten werden nicht beliebig neu erfunden. Jede Statusänderung hat bekannte Zeit und feste Setup-/Ereignisschlüssel ohne Dataset-ID.
- Direkter Ausbruch: 4h-Schluss über der oberen Zone, vorheriger Schluss noch nicht darüber, positiver Körper und Schluss oberhalb des vorherigen Schlusses. Bloß fallende Linie ohne Aufwärtsbewegung gilt als Drift, kein Entry.
- Horizontale Variante: zusätzlich Schluss über das bei Ausbruch bereits bekannte Hoch der vorangegangenen sechs Quellkerzen. Retest separat: spätere Kerze überlappt ursprüngliche rote Zone und schließt positiv über deren Oberkante; kein vorangegangener Schluss unter ihrer Unterkante. Bounce separat explorativ: Reaktion an schon bekannter grüner Zone, positiver Körper und Schluss über vorherigem Hoch. Kein primärer Vergleich mit Ausbruch/Retest vermischt.
- Ausführung am ersten **erwarteten** regulären 5m-Open frühestens fünf Minuten nach Bestätigung. Fehlende Ausführungskerze wird nicht übersprungen. Nicht mehr oberhalb der Signalgrenze liegender Open wird zurückgewiesen. Absicherung zwischen Signal und Open darf nicht verletzt sein.
- Ursprüngliche grüne Aufnahmegerade und nächstgelegene bei Bestätigung bekannte gültige grüne Gerade getrennt dokumentieren. Puffer 0,25 Signal-ATR, nicht willkürlich zum Filterbestehen verschieben. Keine Absicherung: Beobachtung behalten, kein ausführbarer Long-Entry. Risiko/ATR, Kontakte, Reife, Tages-/Wochenkontext und bekannter Raum zunächst Merkmale; die früheren strengen Zusatzprüfungen zusätzlich kennzeichnen, nicht alle Annäherungen verwerfen.

## Daten und Auswertung

Gepinnte reale 25 Aktien aus `safety-universe-20261020-b` wiederverwenden; kein neuer Providerabruf. Entwicklung 02.05.2025–18.03.2026, bereits bekannte spätere Phase 19.03.–02.07.2026. Replay für spätere Phase wieder ab ursprünglichem Entwicklungsbeginn; COST mit dokumentiert späterem Vorlaufbeginn. Finalen Holdout nicht öffnen. Es ist eine neue Untersuchung auf bereits bekannten Zeiträumen, keine unberührte zeitliche Validierung.

Einmal jede abgeschlossene Quellkerze prüfen. Ein Fall darf kein Signal erzwingen. Deduplizierung je Aktie/Modell/Familie/Einstiegszeit, zusätzlich Aktie/Zeit über Familien. Beobachtungen, ausführbare Einstiege und strenge Zusatzgruppe getrennt. Annäherungsmeldungen pro einzigartiger Situation, Vorlauf bis Entry und Meldungsaufwand erfassen. Unbestätigte oder gescheiterte Kandidaten bleiben im Nenner. Keine Benachrichtigungen tatsächlich senden.

Horizonte 5/10/20 XNYS-Sitzungen nach Entrytag. Brutto-Schlussänderung, Kostenmodell (5bp Spread insgesamt +5bp Slippage je Seite), MFE/MAE und +1R/+2R vor ursprünglicher Absicherung getrennt. Vollständige 5m-Strecke nötig für Wegkennzahlen; fehlende Daten weder Verlust noch Gewinn. Rohes positives Ende ist kein ausgeführter Strategiegewinn. Kontrollzeitpunkte wie vorhandener Laborvergleich: gleiche Aktie/Uhrzeit/Quartal/vorherige Tagesrichtung, nahe bekannte Volatilität, Auswahl ohne spätere Rendite/Abdeckung. Vergleich zusätzlich auf gemeinsamer Aktien-/Quartalsabdeckung und konstant vollständiger Horizontmenge; Abhängigkeiten und Verlustgruppen erhalten.

Primär: `swing_envelope` gegen `hull_exact`, direkter Ausbruch, zehn Handelstage, vollständige Pfade, mittlere Mehrentwicklung gegenüber Kontrollen. Vor Betrachtung der späteren Phase Entscheidung festhalten. Mindestens zwanzig vollständige Fälle und drei Aktien ist nur ein Mindestumfang, keine Signifikanz. Mehr Abdeckung ohne positive unabhängige wirtschaftliche Evidenz ist keine freigegebene Gewinnstrategie. Keine Parametersuche nach Kenntnis der Ergebnisse.

## Technische und manuelle Prüfung

Getrennte Unit-Gegenbeispiele, Präfix-/Zukunftsimmunität, Bestätigungslatenz, unveränderliche Anker/Bandbreite, Meldungsdeduplizierung, Zustands-Serialisierung/Wiederaufnahme und gestoppter Datenzugriff. Kleiner deterministischer Jittervergleich der Kandidaten auf historischen Präfixen; zusätzlich analytische Projektionsempfindlichkeit als Diagnose.

Verblindete Fallpakete aus Entwicklungspräfixen und zufälligen Gegenbeispielen erstellen: bekannte Kerzen ohne Zukunft/Ergebnisse, Vorschläge getrennt von manueller Bewertung. Vorlagen für manuelle Linien/Urteile und Abgleich bereitstellen. **Nutzerurteile werden nicht erfunden**; bis echte Bewertungen vorliegen bleibt dieser Teil offen. Kein Training eines LLM auf scheinbaren Gewinnern. Hermes-Erklärungen werden ausschließlich aus protokollierten Merkmalen erzeugt.
