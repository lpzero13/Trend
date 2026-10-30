# Vorabplan: Retestmerkmale, Kontrollen und neue Vorwärtsbeobachtung

22.10.2026, vor der neuen Merkmals-/Kontrollauswertung. Bereits bekannte Marktzeiträume bleiben bekannt. Kein neuer historischer Holdout, keine Optimierung bis eine Rendite gefällt. Bestehende Studien, Observer, persönliche Zeichnungen und Chartdefaults bleiben erhalten.

## Population und primäre Frage

- Unveränderte strenge 4h-Entries `age7`/`retest` aus dem geprüften SIP-Versuch, alle 60 zuvor bestimmten Aktien; die bisherigen 57 zusätzlich getrennt ausweisen. Originalsignale/Stops bleiben unverändert. Daten bis 21.10.2026, ein Jahr Vorlauf.
- Primär: Differenz der netto 20-Sitzungs-Kursänderung gegenüber gematchten Kontrollen derselben Aktie. Endkursänderung ist keine ausgeführte Handelsrendite. 5/10 Sitzungen sekundär. Beide bekannten Zeitabschnitte 2021–2023 und 2024–2026 getrennt, keine Unabhängigkeit behaupten.
- Zusätzlich feste Safety und bestätigte höhere Tiefs auf denselben Entries und Kontrollopens. Gleiche Kosten, ursprüngliches Risiko; nach 5/10/20 Sitzungen offene Positionen liquidationsnah bewerten, kein behaupteter Tori-Zeitexit. Tatsächlich geschlossene Ergebnisse und offene Bewertungen getrennt. Referenz 2.000 USD, 1 % geplantes Risiko, 25 % Allokation, fünf Positionen; Bruchteile, keine Kredite, keine Dividenden. Unbekannte gehaltene Pfade stoppen das bestehende Kapitalledger.

## Kontrollauswahl vor Ergebnissen

- Fünf Kontrollen je tatsächlichem Entry. Gleiche Aktie, NY-Uhrzeit und Kalenderquartal, gleiche damals bekannte MA20-Seite, nächster vorbekannter ATR/Preis als Matchingmerkmal. Nur bis zum jeweiligen Kontrollopen bekannte Historie. Keine Wahl nach späterer Rendite, Stoppberührung oder Pfadvollständigkeit.
- Mindestens 20 Börsensitzungen Abstand zum Signalentry; zunächst Pool der 20 nächsten Volatilitätsnachbarn. Feste Hash-Zufallsziehung mit Seed `20261022`. Weniger Kandidaten offen ausweisen; keinen Entry erzwingen. Kontrollen können zwischen Signalentries wiederverwendet werden, bleiben abhängige Vergleichsfälle.
- Kontrollstop mit derselben anfänglichen Risikofraktion wie beim zugeordneten Signalentry, aus dem Kontrollopen berechnet. Dies testet das Timing gegenüber Zufall bei vergleichbarem Risiko, keine tatsächlich vorhandene Kontroll-Safety-Linie. Kontrollfälle nie als echte Trendlinien-Signale ausgeben.
- Primäre Paardifferenz nur bei bekanntem vollständigem Signalpfad und vollständig bekanntem ursprünglich gewähltem Kontrollpanel. Fehlende Beobachtungen bleiben im Datensatz, in Nennern und Gründen enthalten. Niemals zukünftige Vollständigkeit als Auswahlfilter.
- Unsicherheit anhand Aktien-/Quartalsblöcken, 500 feste Bootstrap-Ziehungen; deskriptiv, keine Korrektur für alle früheren Versuche, keine unabhängige Trefferwahrscheinlichkeit. Überlappende Fälle nicht als unabhängige Stichprobe bezeichnen.

## Merkmale und begrenzte Hypothesen

Nur zum Signal/Entry bekannte Merkmale: Aktions-/Safety-Kontakte, Alter, Momentum, Abstand zur ursprünglichen Safety in ATR/Prozent, Kontext, Raum zum Widerstand. Vorab vorhandene Grenzen als Diagnose: drei/vier+ Kontakte; 7–14/14–30/30+ Tage; Risiko bis/über zwei ATR; Momentum/Kontext/Raum erfüllt/nicht erfüllt/unbekannt; Safety zwei/drei+ Kontakte. Keine nachträglich auf Gewinn gesuchten Schwellen, kein automatisch trainierter Gewinnscore. Phasenunterschiede und kleine Gruppen offen zeigen.

MFE/MAE, ursprüngliche Safetyberührung und OHLC-Reihenfolge nicht vermischen: wenn innerhalb derselben 5m-Kerze Schutz und Gegenbewegung vorkommen, keine Reihenfolge erfinden. Für Marktpfadmetriken vollständiges erwartetes 5m-Raster bis zum gewählten Horizont; ein früher vollständig bekannter Stop kann trotzdem einen bekannten Trade-P/L liefern, wenn erst danach eine Datenlücke liegt.

## Sichtprüfung

20 feste zufällige SIP-Quellpräfixe, beide Quellintervalle. Auswahl ohne spätere Entries/Gewinne; bekannte bestätigte Vorschläge und Widerstände nur bis zum Stichtag. Bestehender Speichern-/Offenlegen-/Historienmechanismus, keine automatischen menschlichen Bewertungen. Alte IEX-Pakete erhalten.

## Kandidaten und Vorwärtslauf

- Neue eigene Version für Kandidatenzustände: Annäherung, bestätigter Ausbruch, bestätigter Retest, ungültig/ungeklärt. Ähnliche Originalrays derselben Aktie/Quelle zusammenfassen; Originalfakten behalten. Qualitätsmerkmale und Warnungen zeigen, kein behaupteter validierter Performance-Rang.
- Neue Registrierung mit tatsächlichem Beginn und Engine-/Datenbindung. Separates Journal und neue Kennung, keine Umstellung des bisherigen `forward_watch`-Laufs. Erste Bestandsansicht nicht als nachträgliches prospektives Signal ausgeben.
- Eigenständige lokale CLI/Loop mit historischen SIP-Daten und mindestens 15 Minuten Verzögerung. Nur bei neuem erwarteten RTH-Abschluss abrufen, überlappend ergänzen, Präfixrevisionen sperren. Herkunft, Alter, Fehler, Fortschritt und letzte erfolgreiche Runde zeigen. Kein Nachrichtenversand, Brokerauftrag oder Containerdeployment.
- Neue nach Registrierung bestätigte 4h-Entries unverändert mit beiden Stopmodellen fortschreiben. Regelfassung bis zu einer später ausdrücklich neuen Generation beibehalten. Eine zukünftige Erfolgsbilanz lässt sich heute nicht vorwegnehmen.

## Abnahme und Grenzen

Zukunftsschocks, Kontrollselektion ohne Zukunftsqualität, originale Signal-/Stoppidentität, fehlende Pfade, Kosten, Kalender/DST, Bootstrap-Abhängigkeit, Quellzustände, stabile Cluster, Deduplizierung, Wiederaufnahme, Auth/Origin, Backup-/Datasetreferenzen und tatsächliche lokale HTTP-Antworten prüfen. Keine echten Credentials in Unit-Tests. Markt-/Runtimeartefakte bleiben privat. Fehlende tatsächliche Ereignisdaten und menschliche Bewertungen offen lassen; keine Bewertung erfinden und keine unbekannten Kurse auffüllen.
