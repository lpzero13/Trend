# Feste Safety, ATR-Risikohypothese und unabhängige Beobachtung

Vorabplan vom 22.10.2026, vor der ersten Signalauswertung des reservierten
Zeitabschnitts. Die bisherigen Entwicklungs-/Validierungszeiträume sind bekannt.
Dieser Versuch löst ausschließlich für den folgenden einmaligen, eingefrorenen
Vergleich die frühere Reservierung auf. Danach ist dieser Abschnitt verbraucht;
keine erneute Abstimmung von Parametern auf seinen Ergebnissen.

## Unverändert prüfen

- Primär `swing_zone`, Retest der ursprünglichen roten/orangenen Linie; anfängliche
  Absicherung unter der damals bekannten grünen Linie. `hull_exact` ist eine
  separat berichtete Referenz, kein weiterer auswählbarer Gewinner.
- Alle 25 bereits festgelegten US-Aktien, unveränderte Entry-Engine und Kosten.
  Fortsetzung aus dem gespeicherten Watch-Zustand am 02.07.2026: keine nachträglich
  passenden Starttermine oder Neuzeichnung alter Setups.
- Prüfung 06.07.–16.10.2026, reguläre XNYS-Sitzungen, 4h-Quelle und 5m-Ausführung.
  Beide Exits auf genau denselben Entries: feste anfängliche Safety oder bestehender
  ATR-Schutz ab netto +1R, Abstand 2 ATR, monoton, erst nach bestätigtem Schluss
  und Latenz wirksam. Zehn Sitzungen bleiben die gemeinsame Forschungsgrenze.
- Keine anderen Exitvarianten/Entryfamilien oder Parameter suchen. Alle Signale
  werden vor der Ergebnisberechnung gespeichert. Anbieterzugriff ist gesperrt.

## Vorab festgelegter Ertrag-/Rückgangstausch

Für eine erste **beschreibende Bestätigung der Risikohypothese** verlangen wir:

1. Mindestens 30 vollständig abgeschlossene, gepaarte Zonen-Retests aus mindestens
   acht Aktien mit zum Signalzeitpunkt vollständiger relevanter 4h-Vorgeschichte.
2. Im Mittel höchstens 0,05R Ertragsverzicht des ATR-Schutzes pro gepaartem Entry.
3. Mindestens 20 % relativ kleinerer maximaler 5m-Depotdrawdown als bei fester Safety.
4. Keine unbekannten Pfade in der Hauptgruppe, kein abgebrochenes Modellportfolio
   und keine offenen Positionen in diesen Portfolios.

Diese Grenzen sind neue, transparente Forschungsannahmen zur Entscheidung über
weitere Beobachtung, keine statistisch abgesicherten Handelsregeln. Sie wurden
nicht aus diesem Zeitabschnitt ermittelt. Zu wenig Fälle bedeutet „nicht belegt“.
Auch ein bestandenes Tor ersetzt weder Zufallsentry-Kontrolle noch Live-Erfahrung.
Es gibt keine automatische Umstellung der Anwendung oder Betriebsfreigabe.

Jedes Depot startet separat mit 2.000 USD, 1 % geplantem Risiko, höchstens 25 %
Kapital pro Position, fünf gleichzeitigen Positionen, Bruchteilen und genau einer
Position je Aktie. Keine Hebelwirkung; Gebühren/Spread/Slippage wie bisher.
Frühere Exits können Kapital für andere Entries freigeben. Deshalb zusätzlich
gepaarte Einzeltrade-R berichten, nicht nur Depotendstände vergleichen.

## Daten und Unsicherheit

Bestandsaufnahme vorab nur anhand Zeitstempeln und Zählungen, ohne Kurs-/Ertrags-
Auswertung. Kein Wechsel von Aktien wegen schlechter Ergebnisse oder Abdeckung.
Unvollständige Vorgeschichte wird separat ausgewiesen. Zu späte Entries ohne
zehn Sitzungen Nachlauf bleiben sichtbar, außerhalb der Hauptgruppe. Zukünftige
Pfadabdeckung darf niemals die Entry-/Portfolioauswahl filtern. Datenlöcher
bleiben unbekannt; ein Loch in einer gehaltenen Position stoppt die Portfolio-
Fortsetzung. IEX, heutige Aktienauswahl, splitbereinigte Kurse und nur ein kurzer
Zeitabschnitt begrenzen die Aussage. Kein Dividenden-/Gesamtmarktertragsbeweis.

## Einstiegsdiagnose getrennt halten

Nur die alte Entwicklung auswerten, keine neuen Grenzen lernen: Kontakte,
Reaktionszahl, Kontaktspanne, Linienalter, Projektionssensitivität, Signalrisiko
in ATR, Raum in R, Abstand zum ursprünglichen Stop sowie bekannte Tages- und
Wochenstruktur. Verfügbarkeit, Median und Anzahl positiver/nichtpositiver
fester Abschlüsse zeigen. Kleine, überlappende Gruppen und Aktien-/Markteffekte
erlauben keine kausale Trennung. Diese Diagnose beeinflusst den neuen Test nicht.

## Hermes als Beobachter

Separates Offline-CLI: Watch-Zustand, ursprüngliche Entrylinien, Stop, Modellstatus,
beide Exitpfade und deduplizierbares Ereignisjournal atomar speichern. Gleicher
Aufruf liefert keine neuen Ereignisse; spätere unveränderte Datenpräfixe dürfen
fortgesetzt werden. Geänderter Code, alte Kurse oder rückwärts gesetzte Zeit
erfordern eine neue Generation. Fehlende Pfade nicht als Gewinn/Verlust ausgeben.
Die gespeicherten unabhängigen Positionen sind kein Echtgeld-/Kapitalportfolio.

Historische Wiederaufnahme ist ein technischer Nachweis, keine prospektive
Bestätigung. Nach dem letzten Datenstand beginnt erst eine echte neue Beobachtung.
Kein Scheduler, Providerimport, Benachrichtigungsdienst, Order oder Deployment.

## Nachvollziehbarkeit

Vor Signalberechnung Regeln, Code, Datensatz-IDs, Bestandsaufnahme und Startzustände
hashen. Ein separater Prüfer rekonstruiert Stop-/ATR-Entscheidungen und Geldflüsse.
Tests: Zukunftsimmunität, Prefixänderung, Wiederaufnahme, Deduplizierung,
unbekannte Pfade, Entscheidungstore und Entwicklungsdiagnose. Änderungen an Web,
vorherigen Engines und Produktionsdatenbank gehören nicht zu diesem Versuch.
