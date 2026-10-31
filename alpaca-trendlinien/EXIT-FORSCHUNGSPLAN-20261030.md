# Gezielte Folgeforschung: Stopauslösung und Haltedauer

Vor der neuen Ergebnisberechnung am 30.10.2026 festgelegt. Explorative Folgeuntersuchung auf bekannten historischen Zeiträumen; keine unabhängige Validierung und keine Neuauswahl eines bestätigten Gewinners.

## Daten und begrenzte Nachprüfung

Die 30 konkreten Symbol-/Tagespaare aus der vorigen Studie werden beim selben Alpaca-SIP-Feed mit Splitbereinigung und gleicher Symbolzuordnung erneut geprüft. Nur tatsächlich zurückgegebene fehlende Kerzen dürfen bei exakt übereinstimmenden Überlappungen in neue unveränderliche Datasets übernommen werden. Weder das vorhandene Archiv noch alte Studien werden überschrieben; keine Handelsaussetzung wird ohne Beleg angenommen.

Die erneuten 5m-Antworten lieferten bei den zuerst geprüften Paaren dieselben Lücken. Ergänzende 1m-Stichproben bei LIN/MMM am 19.04.2021, ANET am 21.06.2018 und AXP am 25.10.2021 enthalten ebenfalls keine Kerzen im betreffenden 5m-Abschnitt. Endgültige Zahlen stehen im Ergebnisbericht. Verbleibende Lücken werden nicht gefüllt oder anhand des späteren Tradegewinns herausgefiltert. Der große Sammler bleibt pausiert.

API-Vertrag: [Alpaca Historical Bars](https://docs.alpaca.markets/us/reference/stockbars). Der lokale Adapter erhält die bestehende serverseitige Authentifizierung; in Protokollen stehen keine Zugangsdaten. Der Connector bietet die erforderliche explizite Bereinigungswahl nicht an.

## Unveränderte Einstiege

69 archivierte Aktien, dieselben Entry-Zeiträume 2018, 2021, 2023 und April 2025 bis März 2026. Nur qualifizierter Ausbruch und qualifizierter roter Retest als zwei getrennte Hauptgruppen. Zwei-Kontakt-Fälle und Safety-Bounce bleiben in den vorherigen Berichten sichtbar, werden in dieser begrenzten Runde nicht neu optimiert.

Linien, Szenario-ID, Signalzeit, Safety und nominaler nächster Entrykurs müssen bei unveränderten Datasets **exakt** mit der vorherigen Studie übereinstimmen. Der Quellscan wird nur für die längere Nachbeobachtung fortgeführt; zukünftige Kerzen dürfen frühere Entries nicht verändern. Bei zurückgegebenen Kursänderungen ist dieser feste Entryvergleich gesperrt, bis ein eigener neuer Daten-/Signalversuch registriert wurde.

## Zwölf vorab benannte Exits je Familie

- Stopführung: fest, ursprüngliche Safety, aktuelle enge Safety der bestehenden Engine.
- Auslösung: Hard-Stop oder 4h-Schluss unter dem vorher aktiven gepufferten Ratchet-Stop, danach nächster erwarteter 5m-Open nach 300 Sekunden Verzögerung.
- Spätester Zeitexit: nach 40 oder 80 Handelssitzungen nach dem Einstiegstag.

Der Close-Stop verwendet für den isolierten Vergleich dieselbe Stop-Schwelle mit 0,3-Prozent-Puffer wie der Hard-Stop. Er ist **nicht** die andere Vorlage „Safety minus 0,15 ATR“. Er hat in diesem Versuch keinen zusätzlichen Intrabar-Notstop; Verluste können das anfänglich geplante Risiko deutlich überschreiten. Bei geometrischen Modellen erfolgen nur erlaubte, nachgelagert wirksame Anhebungen; der Stop wird nie abgesenkt. Die vorhandene Engine wird nicht stillschweigend umdefiniert.

400 Kalendertage Vorlauf. Nachbeobachtung bis 160 Kalendertage nach Entry-Ende, damit auch späte 80-Tage-Entries beobachtbar sein können. Keine Profitziele, Teilverkäufe, SMA-Umschaltung, neuen Kontaktgrenzen oder monatlichen Gewinnerwechsel.

## Vergleich und Prüfung

Je Modell/Horizont Hard gegen Close auf denselben gemeinsam vollständig beobachteten Entries; je Modell/Auslöseart 40 gegen 80 ebenfalls paarweise. Vollständigkeitsquoten und fehlende Pfade sichtbar halten. Diese Teilmengen bleiben eine potenziell verzerrte deskriptive Auswahl, kein Handelsfilter.

Zusätzlich separate 2.000-USD-Depots pro Familie, Exit und Zeitraum mit bisherigen Risiko-/Belegungsregeln, Basis- und doppelten variablen Kosten. Später unvollständige Pfade bleiben im Depot und können es anhalten. Rendite, 5m-Drawdown, Tradezahl, große Verluste und Exitauslöser gemeinsam beurteilen. Keine Zusammensetzung der besten Variante pro Zeitraum. Unterschiedliche Haltedauern verändern Folgeentries und sind deshalb kein reiner Einzelfallvergleich.

Quellprüfsummen, Gleichheit der vorherigen Signale/Entries, Kausalität der Stopänderungen und sämtliche Kapitalbewegungen/5m-Bewertungen prüfen. Keine neue Freigabe durch diese Studie: historische Universumsselektion, Split-/Ganzaktien-Bezahlbarkeit, Dividenden/FX und unabhängige/prospektive Bestätigung bleiben offen. Kein neuer Daemon, keine Brokerorder, Benachrichtigung, UI- oder Containeränderung.
