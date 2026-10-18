# Prüfung – 17.10.2026

## Aktueller Stand: Handelskerzen, Stichtag und Fixierung

Dieser Abschnitt ersetzt ältere Aussagen unten zur Kalenderzeit-Auswahl, zu geknickten Linien und zu noch nicht vorhandenen Stichtagen/Fixierungen. Die folgenden älteren Abschnitte bleiben als Verlauf der vorherigen Prüfungen erhalten.

- **35 Python-Tests und 13 Node-Tests bestanden**, einschließlich unabhängiger Hüllensuche mit Handelspausen, linearer Projektion pro Kerze, exakt zwei Renderer-Endpunkten, historischer Abschneidegrenze, Archivspeicherung und Sicherheitsprüfungen der lokalen Speicherroute. JavaScript-Syntaxprüfung aller drei eigenen Skripte bestanden.
- Explizit vom Nutzer gewählte neue Basis: `tori-candle-axis-0.2`, Steigung pro Quellkerze. Keine Behauptung unveränderter Anker/Signale gegenüber der früheren zeitbasierten Pine-Referenz. MTF-Chartprojektion und Quellereignisse sind gekennzeichnet und dokumentiert.
- Reale AMZN-Daten zum 14.10.2026, 13:00 ET per API und UI geprüft: 2271 Stundenkerzen, 721 Vierstundenkerzen und 307 Tageskerzen. Sämtliche Kerzen enden bis zum Stichtag. Späterer Stand: 2291 / 727 / 310 Kerzen. Alle Achsen enthalten ausschließlich tatsächliche Balken. Historisch neu berechnete Quell-Lanes entsprechen dem bereits archivierten Stand. Nachweis: `artifacts/history-live-verification.json`.
- Im Browser Stand fixiert, bis zum aktuellen Bestand weitergegangen und alle zwölf sichtbaren Originalanker unverändert verglichen. Server neu gestartet, Seite neu geladen und Archiv erneut geöffnet: Anker wieder identisch. Der Archivstand bleibt unter „Datum“ auswählbar. Ein Sprung auf den 13.10. bei aktiver Fixierung vom 14.10. wird ausdrücklich abgefangen, die bisherige Ansicht bleibt sichtbar. Ohne Fixierung funktioniert der Sprung zum 09.10., 13:00 ET; letzte Stundenkerze beginnt 12:00 ET.
- Fixierte Rohkerzen werden bei Ergänzung beibehalten, spätere Kerzen nur nach dem archivierten Präfix hinzugefügt. Regressionstest mit rückwirkend geänderten Anbieterpreisen und zukünftigen Zeilen. Ein weiterer Test hält auch projizierte MTF-Ankerpositionen fest, die beim Speichern noch außerhalb der abgeschlossenen Chartachse liegen.
- 1h-/4h-/1D-Wechsel, Ein-/Ausklappen samt Reload-Persistenz, Zeichnen einer eigenen Ray, unveränderte Originalwerte beim Intervallwechsel und Rückgängig geprüft. Temporäre Testzeichnung entfernt. Zoom verengt den logischen Bereich, Rücksetzen funktioniert. Linien im Chart visuell gerade.
- Finale Browserkonsole: keine beobachteten Fehler der lokalen Anwendung; vorhandene Warnungen stammen aus einer fremden Chrome-Erweiterung. Credential-Prüfung in 24 Quellen/Prüfdateien ohne Treffer. Aktive Seite: AMZN / 1h, Automatik, Infobox eingeklappt, keine eigenen Testzeichnungen. Bildnachweise: `artifacts/straight-lines-collapsed.png` und `artifacts/frozen-analysis-verified.png`.
- 390 × 844: Dokumentbreite 390 ohne horizontalen Überlauf; eingeklappte Infobox und Datumsdialog sichtbar und bedienbar. Viewport anschließend zurückgesetzt. Keine vollständige Touchgeräteprüfung.
- Ein historischer Stand ist eine Rekonstruktion aus heute verfügbaren Kursen und Symbolzuordnungen. Keine Garantie einer historischen Datenversion, kein vollständiger Strategie-Backtest. Bei Fixierung bleiben Ereignisse und Kontakte auf dem archivierten Analysestand; spätere Brüche gegen fixierte Linien werden noch nicht als Ereignisfolge berechnet.

## Ergebnis

Der lokale Python-Server wurde auf `127.0.0.1:8765` gestartet und die Seite in Chrome geöffnet. Die Marktdaten stammen aus tatsächlichen authentifizierten, lesenden Alpaca-Abfragen (`feed=iex`, `adjustment=raw`), nicht aus Demo-/Zufallsdaten. Die Zugangsdaten wurden ausschließlich aus der bereits vorhandenen lokalen Datei gelesen; im Projekt liegt nur ein ignorierter Verweis auf deren Pfad.

## Automatische Prüfungen

`python -m unittest discover -s tests -v`: **16 Tests bestanden**.

- Wick-Hülle gegen eine unabhängig implementierte O(N²)-Hüllensuche auf 120 reproduzierbaren Zufallsdatensätzen, jeweils Rot und Grün.
- Jede Gerade berührt ihre Anker und schneidet auch bei Verlängerung keine späteren Wicks des geprüften Bestands.
- Bestätigungs-Folgekerze, kollineare Kontakte, Mindestzeitraum und Auswahl zwischen Qualität/innerster Linie.
- Preisprojektion mit echten Zeitabständen und unveränderte Eingabedaten.
- Ungültige OHLC-Datensätze, Duplikate und unvollständige Kerzen.
- Tagesabschluss in Sommer-/Winterzeit.
- Private Dateien nicht über HTTP erreichbar, Host-/Origin-Prüfung, ausschließlich lesende Routen und Symbolvalidierung vor Netzwerkzugriff.
- Zusätzliche Suche nach den realen Credential-Werten in den Projektquellen: **keine Treffer**. Die Werte selbst wurden dabei nicht ausgegeben.

## Echte Kursdaten

450 Kalendertage wurden je Quelle angefragt, einschließlich Pagination. Die Antwortseiten können trotz `limit=10000` kürzer sein; alle `next_page_token` wurden verfolgt.

| Symbol | 1h | 4h | 1D |
|---|---:|---:|---:|
| AAPL | 2425 Kerzen | 772 Kerzen | 310 Kerzen |
| MSFT | 2455 Kerzen | 783 Kerzen | 310 Kerzen |

In diesen sechs Beständen wurden keine formal ungültigen oder doppelten Kerzen gefunden. Fehlende Prints/Handelspausen werden dadurch nicht pauschal als geprüft oder als vollständig bezeichnet. Alle erzeugten Hüllensegmente wurden zusätzlich auf den echten Daten auf Ankerzuordnung und wickfreie Verlängerung geprüft. Details: `artifacts/live-data-verification.json`.

## Browserprüfung

- AAPL in 1h, 4h und 1D geöffnet; korrekte Kerzenzahlen, Kurswerte und Zusatzebenen angezeigt.
- 1D-/4h-Anker im 1h-Chart und nach Wechsel auf 1D identisch. Unterschiedliche projizierte Preiswerte entstehen durch den ausdrücklich angegebenen Referenzzeitpunkt der Chartkerze.
- Auf 4h und 1D keine doppelte lokale Ebene; im 1h-Chart zusätzlich eigenständige 1h-Linien.
- Aktienwechsel auf MSFT mit echtem Datenabruf; sowohl aktive rote als auch grüne Linien vorhanden.
- Preisachse bezieht aktuelle aktive Kontextlinien ein, damit entfernte Unterstützung nicht unsichtbar bleibt.
- Ebenen aus-/eingeblendet, äußere Linien und Jahresansicht aktiviert. Keine dabei beobachteten JavaScript-Fehler.
- Kalenderzeitachse erhält die zeitstempelbasierte Steigung. Wochenenden/Handelspausen erscheinen als leerer Raum, ohne erfundene OHLC-Werte.
- Ankerdetails geöffnet und mit den Datenwerten verglichen.
- Ungültiges Symbol `???`: HTTP 400, sichtbare Fehlermeldung, alte Kurse und Linien entfernt. Anschließend erfolgreich wieder MSFT geladen.
- Schmale Browseransicht 390 × 844 geprüft: Dokumentbreite 375 px bei 375 px nutzbarer Breite, kein horizontaler Überlauf. Temporäre Viewport-Vorgabe anschließend zurückgesetzt.
- Aktien-/Intervallauswahl wird im lokalen Seitenlink erhalten.
- Aktualisieren-Knopf mit tatsächlichem erneutem Alpaca-Abruf getestet; anschließend „Frisch geladen“ bei unveränderten Wochenendkursen angezeigt.
- Finale Browser-Konsole ohne aufgezeichnete Fehler. Startskript bei bereits laufendem Server erneut ausgeführt: erkennt die eigene Instanz und startet keinen zweiten Prozess.

Browsernachweise und Screenshots liegen in `artifacts/`. Der endgültige Stand zeigt MSFT im 4h-Chart. Die Startseite ohne Parameter verwendet AAPL.

## Umfang

Dies prüft Datenanbindung, aktuelle automatische Geometrie und Oberfläche. Ein Backtest, historische Wiedergabe, manuelle Punkte, eingefrorene Trade-Snapshots sowie Brokerorders sind nicht Teil dieses Prototyps. Es gibt keine behauptete numerische Gleichheit zu TradingView bei abweichenden Datenfeeds, Handelszeiten und Kerzengrenzen.


## Chart-Ausbau und Ladeoptimierung · 17.10.2026

- **25 automatisierte Tests bestanden.** Neue Prüfungen für Seitennavigation, Netzfreiheit frischer Caches, inkrementelle Kurskorrekturen, parallele unabhängige Downloads, gemeinsame Downloads derselben Datei, markierte alte Daten bei Fehlern, sichere Slash-Symbole sowie Wertpapierfilter, Namenssuche und Seitennavigation.
- JavaScript-Syntaxprüfungen für `app.js` und `drawings.js` bestanden. Keine JavaScript-Laufzeitfehler in der Anwendung beobachtet; der absichtliche unbekannte-Symbol-Test liefert erwartungsgemäß HTTP 404.
- Reale Alpaca-Daten für MSFT, AAPL und NVDA geladen, alle drei Ansichten im Antwortpaket geprüft. MSFT: Cache 0,122 s, erzwungene inkrementelle Aktualisierung 0,467 s; AAPL Aktualisierung 0,492 s; NVDA erstmalig 7,908 s. Gemessene Serverantwortzeiten auf diesem Rechner, keine garantierten Ladezeiten für jeden Titel. Vorheriger MSFT-Neuabruf: 13,680 s.
- Aktienkatalog: **13.246 aktive US-Börsentitel ohne OTC**, aus Alpacas Assets API. Die Kurshistorie wird nicht für alle Titel vorab geladen oder als vorhanden behauptet. Die Auswahl enthält auch ETFs und weitere gelistete Instrumente.
- Browser: Suche nach Microsoft/NVIDIA und Kürzeln, Börsenausschluss, leere Ergebnisse, Favoriten hinzufügen/entfernen, 100 → 200 Ergebnisse, Wechsel MSFT ↔ NVDA, 1h/4h/1D, Kontextlinien, äußere Linien, Zeiträume, Hell-/Dunkelmodus und Infobox getestet.
- Drei direkte Intervallwechsel erzeugten **keinen zusätzlichen `/api/chart`-Abruf** (Serverlog vorher/nachher je 3).
- Ray: zwei Punkte und umgekehrte Klickreihenfolge, Anker verschieben, gesamte Linie verschieben, Escape, Löschen und Rückgängig geprüft. Nach Rückgängig, Intervallwechsel und Neuladen wurden identische gespeicherte Zeit-/Preiswerte verglichen. Beim Aktienwechsel bleiben Zeichnungen getrennt. Nach Korrektur bleibt der sichtbare logische Chartausschnitt beim Ray-Ziehen identisch.
- Gefundene und behobene Fehler: gespeicherte Rays wurden beim ersten Rendern nach Reload nicht geladen; beim Ziehen einer Ray konnte der Chart gleichzeitig verschoben werden; bei unbekannten Symbolen blieb ein Ladehinweis als Instrumentname stehen. Anschließend jeweils erneut erfolgreich getestet.
- Responsive Prüfung: 390 × 844 CSS-Pixel, Dokumentbreite 390 ohne horizontalen Überlauf; Suchdialog 366 Pixel breit. Viewport danach zurückgesetzt. Dies ist keine umfassende Prüfung realer Touchgeräte.
- Testzeichnungen vor Übergabe entfernt und leeren gespeicherten Stand nach Reload bestätigt. Oberfläche bleibt auf MSFT / 4h geöffnet. Screenshots in `artifacts/chart-upgrade-light.png`, `chart-upgrade-dark.png`, `stock-picker-upgrade.png`.
- Zugangsdatenprüfung ohne Treffer in Projektquellen und Prüfarbelegen. Private Dateien sind weiterhin nicht über Webrouten erreichbar. Es werden keine Orders oder Kontoänderungen ausgeführt.

Maschinenlesbare Nachweise: `artifacts/upgrade-live-verification.json` und `artifacts/upgrade-browser-verification.json`.


## Zeitachse, Projektion und Zoom · 17.10.2026

- 25 Python-Tests und 9 Node-Tests bestanden. Neue Tests vergleichen Zeit-/Index-Rundläufe, Tages-/Wochenendpausen, Quellanker zwischen Chartkerzen, DST-Abstände, sichtbare Projektionen bei außerhalb des Ausschnitts liegenden Ankern sowie Zoom und Rückkehr zur letzten Kerze.
- Die zeitbasierte Python-Berechnung bleibt unverändert. Linien werden am Zeitpunkt jeder sichtbaren Kerze ausgewertet. Eine Verlängerung nur anhand zweier Bildschirmpunkte wird nicht mehr als Projektion verwendet. Auf komprimierter Zeitachse sind deshalb Knicke an Handelspausen möglich und ausdrücklich beschrieben; die Anzeige behauptet keine Umstellung auf Handelskerzen-Steigungen.
- Im Browser mit AMZN / 1h geprüft: Mausrad zoomt, + verengt den Ausschnitt bei erhaltener letzter Kerze, − stellt die Breite wieder her; Verschieben und „Letzte Kerze“ erhalten den Zoom; „Ansicht ↺“ und Taste 0 setzen die Ansicht zurück. Rechte Preisskala gezogen → Auto aus; Doppelklick → Auto wieder an. „Linien einpassen“ ein/aus geprüft.
- Eine manuelle Test-Ray wurde in der komprimierten Ansicht angelegt. Ihre Originalanker blieben beim Wechsel zur Kalenderzeit und zurück sowie beim Zoomen unverändert. Die Tabellenpreise blieben beim Achsenwechsel identisch. Test-Ray anschließend entfernt und nach Neuladen leere Zeichnungsliste bestätigt.
- Die getesteten Achsen-/Zoom-/Ray-Aktionen erzeugten keinen zusätzlichen Markt-API-Abruf (lokales Serverlog vor/nach diesem Abschnitt je 13 `/api/chart`-Aufrufe).
- Responsive Ansicht bei 390 × 844 geprüft: kein horizontaler Überlauf, Navigationsleiste innerhalb des Viewports; danach normale Größe wiederhergestellt. Aktive Oberfläche bleibt AMZN / 1h.

- Zusätzlicher Darstellungsfehler behoben und mit Regressionstest abgesichert: außerhalb des sichtbaren Ausschnitts liegende Anker dürfen sichtbare Liniensegmente nicht unterdrücken.
- „Alle“ auf Kalenderzeit geprüft: logischer Bereich 0 bis 10792. Kleine minimale Balkenbreite erlaubt die vollständige Historie; anschließend Ansicht zurückgesetzt.
- Keine JavaScript-Laufzeitfehler der Anwendung beobachtet. Vergleichsaufnahmen: `artifacts/navigation-calendar.png`, `artifacts/navigation-compact.png`. Prüfbericht: `artifacts/navigation-verification.json`.

## Intervallbeschriftungen · 17.10.2026

- Aktive rote/grüne Linien tragen ihr Quellintervall und ihre Farbe als Text. Äußere Hilfslinien bleiben unbeschriftet. Keine Änderung der Berechnung, Anker, Signale oder Speicherformate.
- Beschriftungen werden nach den Linien gezeichnet, mit 12px kräftiger Schrift und dunklerem farbigem Hintergrund. Kollisionsprüfung gegen andere Beschriftungen, Infobox, Instrumentkopf und Ansichtsleiste. Versetzte Beschriftungen haben eine Verbindung zur eigenen Linie; die Zuordnung wird nicht vor den Beginn eines Rays projiziert.
- 14 Node-Tests bestanden, einschließlich Regression für fast deckungsgleiche Intervalllinien und ein überdeckendes Infobox-Rechteck. Syntaxprüfung bestanden. Backend unverändert; dessen vorherige 35 bestandene Tests bleiben im vorherigen Abschnitt dokumentiert.
- AMZN im Browser in 1h, 4h und 1D, Hell-/Dunkelmodus sowie mit offener und eingeklappter Infobox visuell geprüft. Finale Browserkonsole ohne Fehler. Nachweise: `artifacts/interval-labels-light.png`, `artifacts/interval-labels-dark.png`.

## Kerzenschritte, Messwerkzeug und Infobox · 17.10.2026

- 40 Python- und 15 Node-Tests bestanden. Neue Prüfungen: Kerzenschritte über Wochenenden für alle drei Intervalle, keine noch offenen Schritte, begrenzte paginierte Vorwärtssuche mit wiederverwendbarem Navigationscache, exakte Rekonstruktion eines Vor-/Rückschritts samt identischen Quell-Lanes, ungültige Anfragen ohne Netzwerk sowie Messung mit erstem Preis als Prozentbasis.
- Im Browser mit echtem AMZN-Bestand: 1h-Schritt von 30.09.2026 15:00 (2199 Kerzen) auf 01.10.08:00 (2200), zurück wieder 2199. 4h 702 → 703 → 702; 1D 298 → 299 → 298. Leere Handelszeiten werden übersprungen. Jede Darstellung enthält ausschließlich bis zum gewählten Schluss abgeschlossene Quellkerzen.
- Stand vom 30.09.16:00 ET fixiert, weitergegangen und alle zwölf Originalanker unverändert verglichen. Zurück bis zum fixierten Ausgangsstand, weitere Rückwärtsnavigation dort deaktiviert. Anschließend Fixierung gelöst, Archiv erhalten.
- Zwei-Punkt-Messung im Browser aufwärts blau und abwärts rot geprüft: +3,36 USD (+1,37 %) bzw. −3,36 USD (−1,35 %) bei umgekehrten Start-/Endpreisen. Die unterschiedliche Prozentzahl folgt korrekt aus dem anderen Startpreis. Ausgabe pro Aktie, mit 20 Kerzenschritten; kein simuliertes Geschäft. Messungen entfernt. Bildnachweise in `artifacts/replay-measure-positive.png` und `artifacts/replay-measure-negative.png`.
- Infobox eingeklappt und Seite neu geladen: automatisch sichtbar und ausgeklappt. 390×844: Dokumentbreite 390, kein seitlicher Überlauf; Datum, Kerzenschritte, Fixierung und Messwerkzeug sichtbar. Danach normale Größe wiederhergestellt.
- Original-Screenshot rechnerisch nachvollzogen: Chartschluss 249,17 USD; grüne Projektionen 245,94 / 245,92 / 247,03 ergeben gerundet 1,30 % / 1,30 % / 0,86 %. Die roten Linien gehen nicht in diesen Abstand ein.
- Kein vollständiger Strategie-Backtest oder neues Ereignisprotokoll gegen fixierte Linien. Der fixierte Analysezustand bleibt unverändert; spätere Kurse können visuell und mit dem Messwerkzeug geprüft werden.

- Abschließende Browserprüfung: Tastatur ←/→ funktioniert; Zoomweite vor/nach Schritt über Nacht exakt 126,75 Kerzen. Manuelle Messwerte blieben beim Schritt unverändert. Temporäre Messung entfernt und ursprünglicher Analysezeitpunkt 01.10.2026, 05:34 ET wiederhergestellt. Finale Browserkonsole ohne Fehler, Infobox offen. 19 Quell-/Dokumentationsdateien auf Credentialwerte geprüft, keine Treffer.

## Dauerhafte Messungen und Verbindungsfehler · 17.10.2026

- Ursprünglicher Fehler nachvollzogen: lokaler Port 8765 verweigerte die Verbindung; der eingetragene Serverprozess lief nicht mehr. Kein Absturzgrund im Fehlerprotokoll. Zugangsdaten waren nach Wiederherstellung gültig; authentifizierter erneuter Kursabruf erfolgreich.
- Start-Tori.ps1 startet standardmäßig einen unsichtbaren Windows-Worker via lokalem Win32_Process.Create; der Server liegt dadurch außerhalb des Prozessjobs der aufrufenden Shell. Kein geplanter Task und kein Windows-Autostart eingerichtet. Worker führt dieselbe PID-/Log-Verwaltung aus. Stoppen/Starten sowie wiederholter Start ohne zweite Serverinstanz geprüft. Gesundheit über getrennte spätere Toolaufrufe bestätigt.
- apiFetch liefert bei unterbrochener lokaler Verbindung eine deutsche Meldung mit Start-/Wiederholungsanweisung. HTTP-Fehler des Datenanbieters bleiben davon getrennt. Im Browser den Server bewusst gestoppt, einen Kerzenschritt versucht, verständlichen Hinweis und unveränderte Messung bestätigt; nach Neustart erfolgreich aktualisiert. Ein erwarteter erster vollständiger historischer Neuabruf dauerte 6,95 Sekunden.
- Jede abgeschlossene Messung wird im Browser je Aktie als eigener Eintrag gespeichert, einschließlich beider Zeit-/Preisanker, Quellintervall, Erstellungszeitpunkt, Analysestichtag und Anbieter-/Feed-/Anpassungsangaben. Speicherung ist an Browser/Origin gebunden, keine geräteübergreifende Ablage. Neue Einträge ersetzen alte nicht. Datumswechsel zeigt Messungen mit späteren Endpunkten nicht im Chart; die Liste unterdrückt dort Preis-/Prozentwerte.
- ▤ öffnet den Messungsbestand. Eintrag wählen zeigt ihn an; × am Eintrag oder an der aktiven Messung löscht diese. Gelöschte Einträge bleiben im Browser wiederherstellbar. Bei Schreibfehlern bleibt der bisherige Bestand erhalten; eine neue nicht gespeicherte Messung wird als nur für diese Sitzung markiert.
- Browserprüfung: zwei AMZN-Messungen erstellt; erste Messung nach Reload mit identischen Werten, beide Einträge nach weiterem Reload vorhanden. Zweiten Eintrag gelöscht und wiederhergestellt, erneut Reload mit beiden Einträgen. Erste Messung geöffnet. MSFT zeigt null eigene Messungen; Rückkehr zu AMZN zeigt dessen unveränderte aktive Messung. Beide Einträge über Serverneustart erhalten. Eigene Testeinträge anschließend in den wiederherstellbaren Löschverlauf verschoben; nach Reload keine aktiven Testmessungen. Ursprüngliche Aktie/Intervall/Datum erhalten (AMZN / 1h / 29.09.2026, 11:00 ET). Finale Browserkonsole ohne Fehler.
- 40 Python- und 21 Node-Tests bestanden. Neue Tests: mehrere gespeicherte Messungen und aktive Auswahl im JSON-Rundlauf, verlustfreies Löschen/Wiederherstellen, Löschen inaktiver Einträge, defekte/duplizierte gespeicherte Punkte, Schreibfehler ohne Verlust bestehender Daten und Unterscheidung Netzwerkfehler/HTTP-Anbieterfehler. Eigene JavaScript-Dateien auf Syntax geprüft.
- Screenshot des geprüften Messungsdialogs: `artifacts/saved-measurements.png`. Regelentwurf separat in `LONG-KRITERIEN-ENTWURF.md`: Long, beide Einstiegsvarianten und beide Qualitätsgruppen entsprechend deiner Auswahl. Noch nicht in der Signallogik aktiviert.

## P2: Betrieb und Datenqualität – 18.10.2026

## Optionaler Tori-Einstiegsmodus – 18.10.2026

113 Python-Tests unter Windows jeweils mit Python 3.12 und 3.13 erfolgreich, je ein Symlinktest wegen fehlender Berechtigung übersprungen; 24 JavaScript-Tests erfolgreich. 15 neue Tori-Tests decken insbesondere Einzelschritte gegen großen Sprung, unveränderte frühere Entscheidungen bei zukünftigen Kursänderungen, spätere Entry-Stundentiefs, parallele alte/neue Linienpaare, Fixierung zu X, Kontakt-Episoden, Kontext-/Momentum-/Safety-Prüfung, 1h-Eröffnung und Offline-Wiederaufnahme ohne Duplikate ab. Neue Implementierung separat auswählbar; bisherige Forschung bleibt Standard.

Echter vorhandener AMZN-Bestand offline im lokalen Worker: 674 Kerzen, 284 Linienpaare. Horizontale Bestätigung und Retest fanden je denselben einen eindeutigen Einstieg, zwei zugrunde liegende Linienpaare führten zu doppelten Rohfällen. Snapshot + Chart-Safety vom 05.–20.09.2025: genau ein Linienpaar über 22 Kerzen untersucht. Originaldataset unverändert; kein Providerimport für diese Prüfaufträge. Kein Take-Profit, Ausstieg oder realisierter Gewinn berechnet.

Chrome: Moduswechsel Tori/bisherig, gültige Standardwerte, Auswahl „zu X fixieren“, Entry-Filter/alle Ablehnungen und Seitenwechsel 51–100 von 284 geprüft. Historischen Entry über Chartlink geöffnet; 4h-/1D-Anker vor/nach einem 1h-Schritt identisch. Lokale Screenshots in `artifacts/tori-entry-chart.png` und `artifacts/tori-entry-research.png` (außerhalb Git). Parameter und Grenzen in [TORI-EINSTIEGSMODUS.md](TORI-EINSTIEGSMODUS.md). Bestehender Zeitplan unverändert, kein Containerrollout oder Push.

## P2-Nachweise (vorheriger Stand)

Nachtrag zur Scrollkorrektur: Die gemeinsame Chart-CSS sperrte das HTML-Dokument mit `overflow: hidden`; der automatische Höhenmodus des Forschungs-Bodys konnte dies nicht aufheben. Die Forschungsseite hat nun eine eigene HTML-Klasse mit vertikalem Dokumentscrollen, der Body bleibt ohne eigene Scrollfläche. In Chrome nach Neuladen echtes Mausrad-Scrollen bis zum Dokumentende und zurück sowie Bild-ab geprüft: Scrollposition bis 1116/1116, Fußnote vollständig sichtbar, Navigation weiterhin oben. 24 bestehende JavaScript-Tests erfolgreich; keine Änderung an Berechnung oder Chartlayout.

98 Python-Tests unter Windows jeweils mit Python 3.12 und 3.13.12 erfolgreich (je ein Symlinktest wegen fehlender Berechtigung übersprungen), 24 JavaScript-Tests erfolgreich. Kalender-/Rohkursgrenzen, transaktionale Migrationen, sichere Backup-/Restore-Ziele, Referenzschutz, knapper Speicher, Berichtszählung und ein echter Proxy-/Worker-Subprozess sind abgedeckt. Vorhandene Wiederaufnahmeprüfungen bleiben aktiv. CI auf Linux/Windows mit beiden Python-Versionen eingerichtet, noch kein Remote-Ergebnis für diesen lokalen Stand.

Ein echtes lokales Backup mit zwei Datasets und fünf Snapshots wurde in einen neuen Ordner wiederhergestellt; ein daraus gepinnter Auftrag mit drei AMZN-Starts lieferte ohne Providerimport dieselben Fälle und dieselbe Zusammenfassung. Neue Speicher-/Berichtsansicht in Chrome geprüft. Keine Änderung am installierten Zielcontainer. Vollständige Nachweise, Ressourcenmessung und bewusste Grenzen in [BETRIEB-P2.md](BETRIEB-P2.md); lokale Screenshots/Backupdaten bleiben außerhalb Git. Neu normalisierte Tageskerzen verwenden jetzt den XNYS-Kalender; alte Datasets und ältere Aussagen unten zum damaligen Stand bleiben unverändert archiviert.

## Automatische Ereignisstudien und gemeinsamer Kern – 17.10.2026

- Geometrie und Datenmodelle vom Provider gelöst; HTTP und Dataset-Chart verwenden `analysis_service.build_chart`. Der Forschungsstrom verwendet dieselbe kausale Brucherkennung wie der manuelle Chart. Snapshot-/Messungswerkzeuge bleiben erhalten.
- Finale Prüfung: **61 Python-Tests und 21 Node-Tests bestanden**. Neue Prüfungen umfassen unveränderliche Dataset-Versionen und Manipulationserkennung, Auswahl ohne Kenntnis späterer OHLC, Schocks in zukünftigen Quell-/Tageskerzen, Übereinstimmung von Chart und Ereignisstrom, Retest erst nach der Ausbruchskerze, Ausführung erst nach Signalverfügbarkeit, feste ursprüngliche Schutzmarke, OHLC-Mehrdeutigkeit, unvollständige Beobachtungen, Deduplizierung, Offline-Checkpoint/Wiederaufnahme, Ergebnisseiten, atomare Auftragsübernahme und stornierte Aufträge, Worker-Sperre, Zeitplan, HTTP-Authentifizierung/Origin und private Pfade.
- Echter Alpaca-Lauf: automatischer Auftrag `67d5dd79ebd947b9b1b6f40ccb318308` für AMZN/MSFT; 900 Kalendertage, zehn Zufallsstarts pro Aktie, 20 Starts ausgewertet, einer ohne Einstieg, 194 Linienereignisse archiviert. Beide Titel ohne Datenfehler. Keine qualifizierten Linienpaare in diesen gezogenen Fällen; keine Aussage, dass diese allgemein nicht vorkommen.
- Beim ersten Entwicklungslauf reichte das alte 20-Seiten-Limit für lange Intraday-Abfragen nicht. Alpaca lieferte hier etwa 190 Stundenkerzen bzw. 55 Vierstundenkerzen je Antwortseite. Grenze auf 512 Seiten mit Schleifenprüfung erhöht; Regressionstest mit 23 kleinen Seiten bestanden. Erfolgreicher AMZN-4h-Import hatte 24 Seiten. Der fehlgeschlagene frühe Auftrag bleibt als Fehler im Archiv sichtbar.
- Betriebssystemspezifische Sperre korrigiert: Unter Windows verhindert die Byte-Sperre auch einen Lesezugriff. Der Statuscheck liest das gesperrte Byte nicht mehr. Konkurrenzprüfung bestanden, Hintergrundworker nach letztem Serverneustart aktiv.
- Echter Headless-Vergleich: Server gestoppt, Auftrag `e53c53864b794c399a9501d61adfc953` per CLI auf genau denselben Dataset-IDs gestartet, API-Key/Secret aus der Prozessumgebung entfernt und Credential-Dateipfad auf eine nicht existierende Datei gesetzt. CLI-Worker abgeschlossen. Gruppenergebnisse und alle 20 Fälle identisch zum Live-Lauf, abgesehen von den Versuch-IDs (die vollständige Parameter einschließlich Dataset-Zuordnung enthalten). Nachweis: `artifacts/research-replay-verification.json`.
- Chrome: `/research` erfolgreich geladen, täglichen Zeitplan per Oberfläche übernommen, echten Fortschritt und Abschluss gesehen. Heller und dunkler Modus visuell kontrolliert; ursprünglichen hellen Modus wiederhergestellt. Forschungsfall über „Verlauf“ geöffnet, eine tatsächliche 4h-Kerze weitergeschaltet und sechs Originalanker-Zeilen unverändert verglichen. Wechsel auf 1h mit fixierten 4h-/1D-Linien erfolgreich. Ursprüngliche Signalereignisse statt späterer automatischer Brüche angezeigt; Schutzmarke als eigene horizontale Referenz gezeichnet.
- Bestehende manuelle AMZN-/1h-Ansicht am ursprünglichen Stichtag neu geladen: Kursdaten, Forschungslink und ausgeklappte Infobox vorhanden; keine sichtbare Fehlermeldung. Forschungs- und Fall-Chartkonsole zum Prüfzeitpunkt ohne Fehler. Screenshots: `artifacts/research-dashboard.png`, `artifacts/research-case.png`.
- Nach abschließendem Neustart: Worker aktiv, automatischer Zeitplan weiterhin aktiv (24 Stunden, AMZN/MSFT, zehn Starts je Aktie), beide abgeschlossenen Aufträge und alle gespeicherten Ergebnisse weiterhin vorhanden. Server-Fehlerlog leer. Kopierprüfung in 26 Quell-/Dokumentations-/Deploymentdateien: keine tatsächlichen Alpaca-Zugangsdaten gefunden.
- Grenzen: Kein Volluniversum-Lasttest, keine laufende Echtzeit-Kandidatenüberwachung, keine Broker-/Portfolio-Ausführung, keine tatsächliche Linux-/Proxmox-Installation und keine Installation der Hermes-Skillvorlage im Agenten. Linux-Dienst, Wrapper, Umgebungsbeispiel und JSON-Schnittstelle sind vorbereitet; Zielcontainer/Zugang sind noch offen. Historische Kursversionen, Kapitalmaßnahmen und vollständige Börsenkalender werden nicht als bereits gelöst dargestellt. Details in `FORSCHUNG.md`.
