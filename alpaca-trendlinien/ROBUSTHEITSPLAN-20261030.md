# Feste Strategie breiter prüfen – vorab festgelegter Versuch

Stand: 30.10.2026. Dieser Plan entsteht vor Berechnung der neuen Ergebnisse. Die bisherige Strategie wird nicht neu optimiert.

## Fragestellung und Auswahl

Der unveränderte Kandidat ist `breakout:qualified:fixed:sma0:h40`: bestätigter 4h-Ausbruch einer vorher qualifizierten roten Linie (mindestens drei getrennte Kontakte und sieben Tage), gültige aktuelle Safety am Signal, fester anfänglicher Stop mit 0,3 % Puffer, maximal 40 Handelstage, kein SMA200-Filter. Signalberechnung und Ausführung bleiben dieselben wie in der vorherigen Untersuchung.

Alle **69 beim Planungszeitpunkt fertig lokal archivierten Aktien** werden aufgenommen, unabhängig von späteren Ergebnissen. Das private JSON-Manifest enthält sämtliche Symbol-/Dataset-IDs; der Auswertungscode benötigt keinen bestimmten Sammlerauftrag. Kein neuer Providerabruf und keine Wiederaufnahme des pausierten Sammlers.

Entry-Zeiträume: **2018, 2021, 2023** jeweils ganzjährig und **01.04.2025 bis 31.03.2026**. Jeweils 400 Kalendertage Vorlauf und bis 31.03. des Folgejahres Nachbeobachtung, im letzten Block bis 30.06.2026. Der letzte Zeitraum wurde für 16 Aktien bereits ausgewertet; er ist ausdrücklich kein neuer zeitlicher Holdout. Auch die übrige Historie kann in älteren Projektarbeiten bekannt gewesen sein. Diese Runde ist eine vorab definierte Robustheitsprüfung, keine garantierte unabhängige Bestätigung.

Fehlende Vorgeschichte beziehungsweise nicht abgedeckte Entry-Fenster werden als **nicht verfügbar** protokolliert, nicht als Null-Signal und nicht durch andere Aktien ersetzt. Fehlerhafte Strukturen stoppen den Lauf. Innere Datenlücken werden sichtbar gehalten; gehaltene Positionen werden bei fehlendem Ausführungspfad nicht anhand des späteren Ergebnisses entfernt.

## Vergleiche und Kosten

Pro Zeitraum ein gemeinsames Depot mit 2.000 USD, 1 % Risiko, maximal 25 % Positionsanteil, maximal drei Positionen, ganzen rechnerischen Aktien und deterministischer Konfliktreihenfolge. Jeder Zeitraum startet separat; Renditen werden weder addiert noch zu einer durchgehenden Depotkurve zusammengesetzt.

Primär zählt das gesamte verfügbare Universum. Die bisherigen 16 und die übrigen 53 Aktien werden zusätzlich getrennt ausgewiesen; daraus wird kein neuer Sieger ausgewählt. Je Gruppe vier Szenarien: bisheriger Spread/Slippage, doppelte Spread/Slippage, zusätzlich 1 USD pro Order, zusätzlich 2 USD pro Order. Alle Signale bleiben gleich, die tatsächliche Stückzahl und Belegung dürfen sich durch Kosten ändern.

Die bisherigen Prüfgrenzen bleiben erhalten: vollständiges Kapitalbuch, mindestens zehn Trades, positiver Nettoertrag und Kostenstress, Drawdown höchstens 10 %, mindestens vier positive Aktienbeiträge und maximal 50 % Anteil einer Aktie an positiven Beiträgen. Zusätzlich muss das Gesamtdepot in **jedem** Fenster das 90. Perzentil von 39 nach Aktie, Monat und kausal gültiger Safety gebildeten Zufallskontrollen übertreffen. Nicht bestandene Grenzen werden nicht nachträglich gelockert. Die Kontrollen bleiben explorativ, kein korrigierter Signifikanztest.

## Datenprüfung und Ausführungsgrenzen

Prüfung aller verwendeten OHLCV-Strukturen, eindeutiger Zeitpunkte, regulärer Sessiongrenzen, erwarteter 5m-Kerzen sowie Nachrechnung sämtlicher gespeicherter 1h-/4h-/1D-Aggregate gegen 5m. Feiertage, Sommerzeit und verkürzte Tage folgen dem versionierten Börsenkalender. Große Tageslücken sind Warnungen, keine bestätigten Kapitalmaßnahmen.

**SIP/split enthält splitbereinigte Preise.** Ohne die damaligen Splitfaktoren entsprechen rechnerisch ganze heutige Aktien nicht zwingend historisch handelbaren ganzen Aktien. Historische Bezahlbarkeit und Ordergebühren sind deshalb noch nicht vollständig validiert. Dividenden, EUR/USD, Steuern und Cashverzinsung fehlen ebenfalls. Auch ein bestandener statistischer Bildschirm gibt keine operative Strategiefreigabe. Kapitalmaßnahmen dürfen nicht erfunden oder durch pauschale Kurskorrekturen ersetzt werden.

## Weitere technische Arbeit

Ein gesondertes, versionsgebundenes Signaljournal soll Kerzen einzeln verarbeiten, ursprüngliche Signallinien unveränderlich speichern und nach Neustart ohne Doppelsignale fortsetzen. Ein historischer Replaytest dieses Journals zählt nicht als prospektiver Gewinnnachweis. Neue Live-Daten, Containerbetrieb, Benachrichtigungen und Brokerorders werden durch diesen Versuch nicht gestartet.
