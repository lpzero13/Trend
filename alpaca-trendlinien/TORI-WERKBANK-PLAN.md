# Vorabplan: Sichtprüfung, Datenvergleich und erklärte Kandidaten

22.10.2026, vor dem SIP-Universumsimport und dessen Signal-/Verlaufsauswertung. Fortsetzung des Kriterien-Gesamttests, eigenständiger Versuch. Keine Änderungen an den festgehaltenen Ergebnissen oder an den Regeln des bestehenden Beobachters.

## Datenvergleich statt Ersatzkerzen

Eine kleine Berechtigungsprobe AAPL / 29.09.2023 / 5m / SIP war mit dem bestehenden Zugang erfolgreich. Die [offizielle FAQ](https://docs.alpaca.markets/us/docs/market-data-faq) erlaubt historische SIP-Abfragen ohne Echtzeitabonnement mit mindestens 15 Minuten altem Ende. Keine Abonnementänderung, keine aktuellen SIP-Endpunkte.

- Dieselben vorab festgelegten 60 Aktien, 27.07.2020–21.10.2026. Primärer Feedvergleich auf denselben 57 gültigen IEX-Aktien; drei zuvor ungültige Imports gegebenenfalls separat ausweisen. Keine Aktien nach Rendite auswählen.
- SIP ausdrücklich als eigener Feed speichern, splitbereinigt, unveränderte reguläre 5m-Normalisierung mit am Börsenstart verankerten 4h-/Tageskerzen. Fehlende Kerzen bleiben unbekannt. Keine Konstantkurse, keine stillen Änderungen des IEX-Datenmodells.
- Das Raster verwendet reguläre 5m-Intervalle vor dem Sitzungsschluss, keine nachbörslichen 16:00–16:05-Kerzen. Es ist keine Rekonstruktion eines amtlichen Tages-/Auktionsschlusskurses aus Einzeltrades.
- Gemeinsamer Kalenderzeitraum, ein Jahr Vorlauf. Gleiche unveränderte `CompleteReplay`- und Outcome-Mathematik, beide Quellintervalle. Strenge Außenlinien als Hauptvergleich. Unveränderte gestufte Profile nur zur Diagnose.
- Primäre Kandidatengruppe: drei unabhängige Aktionskontakte plus sieben Tage Linien-/Safety-Alter, separat Ausbruch/Retest/Grün-Abpraller. Momentum, Safety-Abstand, Kontext, Raum und Unternehmensereignisse als explizite Merkmale/Unbekanntheiten; keine neue Auswahl nach zukünftiger Rendite.
- 5/10/20/60-Sitzungs-Kursbeobachtung und natürliche Exits getrennt. Nicht bekannte Intrabarpfade bleiben unbekannt. Bereits untersuchte Zeiträume bleiben bekannt; kein neuer unabhängiger Holdout behauptet.

## Sichtprüfung

- Die 82 vorbereiteten Fälle in eine eigene zugängliche Webansicht übernehmen. Quellintervall respektieren, nur bis zum Bewertungszeitpunkt abgeschlossene Kerzen liefern; eigene rote/grüne Rays und horizontale Widerstände, manuelle zusätzliche Kontaktmarkierungen, Löschen/Rückgängig und serverseitige Speicherung.
- Urteil zuerst speichern, Engine-Linien erst ausdrücklich aufdecken. Spätere Änderungen historisieren und als beeinflusst markieren; ursprüngliche unbeeinflusste Bewertung erhalten. Keine zukünftigen Kurse auf dieser Seite, auch nicht beim Enginevergleich.
- Ergänzende feste Zufallsfälle ohne Auswahl anhand späterer Entries oder Gewinne. Das bisherige Paket ist eine diagnostische Auswahl von Enginefällen, keine repräsentative Schätzung menschlicher Trefferquote.
- Vergleich anhand Quellkerzenpositionen und damaliger ATR, Anker-/Projektionsabweichung, eigene Kontaktmarkierungen und Dochtüberschreitungen. Keine erfundenen menschlichen Bewertungen. Reale Urteile bleiben dem Nutzer vorbehalten.

## Headless und Kapital

- Eigener JSON-Scanner für gespeicherte Datasets/Stichtage: Kandidaten mit Originalankern, Quellintervall, Kontaktqualität, Abstand, ursprünglicher Safety, Kontext, Raum und erklärten Warnungen. Kein Brokerauftrag, kein automatischer Nachrichtenversand, kein neuer laufender Zeitplan.
- Ersten Zustand und Engine-/Datenpräfix festhalten; weitere Stichtage nur kausal vorwärts, Signalidentitäten stabil, bei Datenrevision/Engineänderung neue Generation verlangen. Dieser technische Modus liefert vorerst Beobachtungskandidaten.
- Vorhandenes Cash-/Risikoledger für eine separate Machbarkeitsrechnung verwenden: 2.000 USD, ein Prozent geplantes Risiko, maximal 25 Prozent Allokation, fünf Positionen, Bruchteile als Modellannahme, keine Kredite. Keine Vorauswahl nach späterer Pfadvollständigkeit. Bei unbekanntem gehaltenem Pfad stoppen und Gesamtrendite unbekannt lassen.
- Historischer Ereigniskalender nur bei nachgewiesenem damaligem Bekanntheitszeitpunkt und expliziter Abdeckung. Schnittstelle validieren; fehlende echte Daten offen lassen. Keine LLM-generierten Termine einsetzen.

## Abnahme

Quellpräfix-/Zukunftsschocktests, getrennte Feeds/Datensatzidentität, keine Aufweichung der Docht-/Lückenregeln, unabhängige Kennzahlen-/Pfadprüfung, Cash-/Allokationskontrolle, Sichtprüfung ohne Zukunftsleck, Origin-/Auth-Schutz und Lösch-/Rückgängigverhalten prüfen. Bestehende Python-/JS-Suiten erhalten. Private Datasets, SQLite, Urteile und Laufartefakte nicht versionieren; Referenzschutz und konsistente Sicherung für neue gespeicherte Fälle berücksichtigen.
