# Einstiegskriterien und Exitmethoden auf denselben Fällen vergleichen

Stand 30.10.2026, angelegt vor dieser zusätzlichen Aufschlüsselung. **Nachträgliche diagnostische Auswertung bekannter Backtests**, kein neuer Holdout, keine neue Auswahl eines Strategiegewinners.

## Unveränderte Eingaben

Quelle ist die abgeschlossene feste Robustheitsstudie: 69 Aktien, vier Zeitfenster, 276 gespeicherte Blöcke, davon zehn ohne ausreichende Vorgeschichte/Entry-Abdeckung. Alle drei Entry-Familien und alle drei Hard-Stop-Pfade bis maximal 40 Handelstage sind bereits gespeichert. Keine neue Linienberechnung, Providerabfrage, Änderung der Einstiege oder Wiederaufnahme des Sammlers.

Die bestehende eingefrorene Ausbruch-Hypothese und ihre bisherigen Prüfgrenzen bleiben unverändert. Dieser Vergleich kann weitere Hypothesen für spätere, getrennte Tests liefern.

## Einstiegssortierung

1. Ausbruch über eine vorher bekannte rote Linie. Sofortiger und verzögert sauberer Schluss zusätzlich getrennt.
2. Rücklauf an die **ursprüngliche gebrochene rote Linie**, nicht an eine nachträglich passendere rote Linie.
3. Eigenständiger bestätigter Bounce an der steigenden grünen Safety, ohne zwingend vorherigen roten Ausbruch.

Für die beiden roten Familien drei getrennte Kontaktklassen: qualifiziert (mindestens drei Kontakte und sieben Tage), genau zwei Kontakte, sowie mindestens drei Kontakte mit noch zu geringem Alter. Die bisher vorhandene Klasse `three_young` darf nicht aus der Auswertung verschwinden. Safety-Bounces liegen im aktuellen Modell ausschließlich qualifiziert vor. Insgesamt sieben Entry-Gruppen, keine Vermischung von zwei und drei Kontakten.

Keine rückwirkende Aufwertung eines Kontakts. Die Tages-SMA200-Lage wird nur zusätzlich als bekanntes Merkmal aufgeschlüsselt; kein Filter wird in den Depotbüchern heimlich eingeschaltet.

## Drei bereits berechnete Exits

- **Fester Anfangsstop:** ursprüngliche Safety minus 0,3 %, Stop bleibt unverändert.
- **Ursprüngliche Safety nachziehen:** dieselbe beim Einstieg gebundene Gerade fortschreiben, Stop nur aufwärts nachziehen.
- **Aktuelle Safety nachziehen:** neu bekannte gültige Safety-Geraden berücksichtigen, Stop ebenfalls niemals senken.

Alle drei sind Hard-Stops, Quellentscheidungen an 4h-Schlüssen und nachgelagerte Wirksamkeit gemäß vorhandener Engine; spätester zeitlicher Exit nach 40 Handelstagen. Keine neu hinzugefügten Take-Profits, Teilverkäufe, Break-even-Umschaltungen oder Close-Stop-Pfade. Insbesondere ist der dritte Modus die aktuelle enge Safety der Engine, keine Garantie, dass stets eine bestimmte steilere Fächerstufe gewählt wird. Diese Abgrenzung gehört zur späteren Regelabnahme.

## Zwei Vergleiche mit unterschiedlicher Aussage

**Gleiche Einzelfälle:** pro Entry-Gruppe alle verfügbaren Einstiege und Pfadstatus zählen. Für den direkten Vergleich dieselben Case-IDs verwenden, deren drei Exitpfade vollständig abgeschlossen vorliegen. Ausweisen: Anzahl, Trefferquote, mittleres/medianes Netto-R, durchschnittliche Kursrendite, Gewinnfaktor auf R-Basis, Haltedauer, Exitgründe und Fälle mit zwischenzeitlich mindestens +1R, die nicht positiv enden. Unterschiede gegen den festen Stop paarweise berechnen. Gleiche Aktien-/Zeitfenster zusätzlich gleich gewichten und Weglassen je einer Aktie als Stabilitätsdiagnose prüfen.

Diese gemeinsame vollständige Teilmenge ist **nach Beobachtbarkeit ausgewählt** und kann verzerrt sein. Sie wird nicht als unabhängiger Erfolgsnachweis und niemals als zukünftiger Handelsfilter verwendet. Unvollständige Einstiege bleiben mit Anzahl und Grund sichtbar. Familien können dieselbe Kursbewegung überlappend erfassen; Stichproben sind nicht unabhängig.

**Endliches Depot:** alle zeitlich passenden Einstiege einer vorab bekannten Familie/Kontaktklasse verwenden, einschließlich später zensierter Pfade. Je Exitmodell und Zeitfenster separates 2.000-USD-Kapitalbuch mit bisherigen Risiko-/Belegungsregeln; Basiskosten und doppelter Spread/Slippage. Früheres Schließen kann andere spätere Entries ermöglichen. Damit erklärt diese Tabelle tatsächliche Varianten eines Modells, aber nicht den reinen Exit-Effekt bei identischen Trades. Keine Addition verschiedener Depotvarianten oder Fenster.

## Grenzen und technische Prüfung

Die vorhandenen Datenlücken und Split-/Ganzaktien-/Dividenden-Grenzen bleiben bestehen. Ein unvollständiges Depot erhält keine vollständige Rendite. Kein neuer Sieger wird auf denselben bekannten Daten als validierte Strategie freigegeben.

Vor Verwendung sämtliche Quellprüfsummen und gespeicherten R-Rechnungen prüfen; Depotbewegungen und vollständige 5m-Bewertung/Drawdowns unabhängig nachrechnen. Private JSON-/CSV-Ausgaben enthalten stabile Case-IDs und alle Pfadstatus für spätere Hermes-Auswertung. Manuelle Chartzeichnungen, Webansicht, Broker und Benachrichtigungen werden nicht geändert.
