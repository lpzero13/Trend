# Tori Market Lab – Alpaca-Prototyp

Repository und zentrale Hermes-/Container-Dokumentation: [Trend](https://github.com/lpzero13/Trend) · [HERMES.md](../HERMES.md). Dieses Verzeichnis ist die Anwendung innerhalb des Repositories.

Lokale Seite mit echten historischen IEX-Kursen von Alpaca, Kerzen für **1h, 4h und 1D** sowie der automatischen Tori-Linienberechnung. Manuelle Suche unter `/`, automatische Ereignisstudien unter `/research`. Hintergrundaufträge mit Zufallsstarts, unveränderlichen Datenbeständen und JSON-Werkzeugen für Hermes. Noch kein vollständiger Portfolio-Backtest und keine Orderfunktionen.

**Neu:** [Automatische Forschung, Bedienung und Linux-/Hermes-Anbindung](FORSCHUNG.md). Der erste normale Serverstart richtet einen täglichen Forschungsauftrag für MSFT/AMZN ein, zehn Starts je Aktie; die Forschungsansicht kann diesen Zeitplan ändern oder pausieren. Aufträge laufen ohne offenen Browser.

**Tori-Kriterien historisch prüfen:** [Zufallsfenster und Kursentwicklung nach 5/10/20 Handelstagen](TORI-KURSBEOBACHTUNG.md). In der Forschung den Tori-Modus, zufällige Zeiträume und Kursbeobachtung wählen. Einstiegsvarianten werden getrennt erfasst; die Kursänderungen enthalten keine Ausstiegs- oder Depotbewertung.

Die feste Hauptnavigation oben bietet **Chart** für die manuelle Suche und **Forschung** für automatische Untersuchungen, Aufträge und Ergebnisse.

**Zusätzliches Forschungslabor:** Unter **Labor** (`/lab`) stehen vollständige chronologische Scans, vergleichbare Regelprofile, verblindete Fallprüfung, Entwicklungs-/Validierungs-/Abschlussphasen und optionale Ausführungssimulationen bereit. [Anleitung und Modellgrenzen](FORSCHUNGSLABOR.md), [lokale Prüfnachweise](FORSCHUNGSLABOR-UMSETZUNG.md).

**Neuer Offline-Ausstiegsvergleich:** [Sieben Ausstiegsmodelle auf denselben Einstiegen nach 5/10/20 Handelstagen](AUSSTIEGSVERGLEICH.md), einschließlich experimenteller Tori-Auslegung, Kosten, Fakeouts und nachvollziehbarer Geldbeträge pro Einzelposition. Wiederholbar über `tools/exit_study.py`, unabhängige Ausführungsprüfung über `tools/verify_exit_study.py`. Noch keine zusätzliche Webauswahl und keine neue Standardstrategie.

## Start unter Windows

Im Projektordner mit Python 3.12 oder 3.13 (lokal geprüfte Versionen):

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\Start-Tori.ps1
```

Anschließend **http://127.0.0.1:8765** im Browser öffnen. Der Starter lässt den Server im Hintergrund laufen und startet ihn über einen unsichtbaren Windows-Worker unabhängig vom aufrufenden Terminal. Dafür wird kein geplanter Task eingerichtet. Nach einem Rechnerneustart ist der Starter erneut auszuführen. Beenden mit `Stop-Tori.ps1`. Alternativ im Vordergrund:

```powershell
.\.venv\Scripts\python.exe server.py --port 8765
```

Python muss außerhalb Windows die IANA-Zeitzonendaten ebenfalls finden können; `tzdata` ist als einzige Python-Abhängigkeit festgeschrieben. Das Frontend benötigt keinen Build und kein Node.js.

## Zugangsdaten

Die bereits vorhandene Datei auf dem Desktop wird nur vom Server gelesen. `config.local.json` enthält **ausschließlich den Dateipfad**, keine kopierten Schlüssel:

```json
{"credentials_file": "C:/Users/<Benutzer>/Desktop/Alpaca API.txt"}
```

Alternativ `ALPACA_CREDENTIALS_FILE` setzen oder die beiden Variablen `APCA_API_KEY_ID` und `APCA_API_SECRET_KEY` verwenden. Die Datei wird als Datenquelle behandelt; enthaltene URLs oder Anweisungen werden nicht ausgeführt. Die Zugangsdaten werden nur als Authentifizierungsheader an Alpaca gesendet: Kurse von `https://data.alpaca.markets`, der Wertpapierkatalog über `GET /v2/assets` von `https://paper-api.alpaca.markets` beziehungsweise `https://api.alpaca.markets`. Es werden weder Konten noch Orders abgefragt oder verändert.

Die Infobox berechnet **Abstand = (letzter abgeschlossener Chartschluss − grüne Chartprojektion) / Chartschluss × 100**. Das ist der aktuelle Abstand zur grünen Linie, kein Einstiegsergebnis und kein vollständiges Positionsrisiko. Negative Werte bedeuten: Chartschluss unter Grün. Berechnet wird mit ungerundeten Kurswerten, angezeigt auf zwei Dezimalstellen.

Serverbindung standardmäßig ausschließlich `127.0.0.1`. Private Dateien und Marktcache sind keine Webrouten. Host/Origin werden geprüft. Schreibende Endpunkte speichern lokale Analysestände, Forschungsaufträge und deren Zeitplan; Providerzugriffe bleiben ausschließlich lesend. Netzwerkbetrieb für Linux ist explizit mit Token und erlaubtem Host konfigurierbar, siehe `FORSCHUNG.md`. Es gibt keine Ausgabe der Schlüssel im Frontend oder Serverlog. Konfiguration, Daten, Logs und virtuelle Umgebung sind von Git ausgeschlossen.

## Bedienung

- Oben das Symbol anklicken: Suche nach **Unternehmensname oder Symbol**, Börsenfilter, Favoritensterne und weitere Seiten mit jeweils 100 Werten. Das aktuelle Alpaca-Verzeichnis enthält aktive US-Börsentitel einschließlich ETFs, ADRs, Vorzugsaktien und weiterer gelisteter Instrumente. OTC wird ausgeschlossen, weil der kostenlose IEX-Feed dafür nicht geeignet ist. Das Verzeichnis ist keine Zusage einer ausreichenden IEX-Historie für jeden Titel; zu kurze Daten werden beim Laden gemeldet. Keine Xetra-Daten.
- **1h / 4h / 1D** wechselt das Chartintervall direkt im Browser. Alle drei Ansichten werden mit dem ersten Abruf gemeinsam geliefert. 4h und 1D bleiben als ein-/ausblendbarer Kontext vorhanden; 1h kommt im 1h-Chart hinzu.
- **1M / 3M / 6M / 1J / Alle** verändert den sichtbaren Ausschnitt, nicht den Berechnungsrückblick. Mausrad zoomt, Ziehen im Chart verschiebt die Ansicht. Unten im Chart stehen **− / +**, **Letzte Kerze**, **Ansicht ↺** und **Auto** bereit. „Letzte Kerze“ behält den Zoom bei; „Ansicht ↺“ setzt Zeitraum und Preisskala zurück (1h/4h: 30 Tage, 1D: 90 Tage). Die Preisskala rechts und die Zeitachse unten lassen sich ziehen und per Doppelklick zurücksetzen. Tastatur: **+ / −**, **Pos1** und **0**. „Alle“ zeigt die gesamte geladene Historie.
- **Mond/Sonne** schaltet zwischen Hell- und Dunkelmodus um. Die Themenauswahl wird lokal im Browser gespeichert. Die Infobox ist beim Öffnen oder Neuladen immer sichtbar und ausgeklappt; während der Sitzung lässt sie sich weiterhin ein-/ausklappen und ausblenden.
- Die automatische Preisskala passt sich standardmäßig nur an die sichtbaren Kerzen an. **Linien einpassen** berücksichtigt zusätzlich die aktiven eingeblendeten Tori-Linien im sichtbaren Ausschnitt; die eigene Zeichnung verändert die Skala nicht.
- Die kompakte **Infobox oben rechts** zeigt Linienwerte, Abstand vom letzten Chartschluss zur grünen Chartprojektion, Status, Kontakte und das letzte gefundene Bruchereignis. Über **⋯** sind genaue Originalanker und Datenstände einsehbar. **− / ＋** in der Kopfzeile klappt die Box ein/aus; **ⓘ** blendet sie vollständig aus/ein. „Äußere“ zeigt frühere Hüllensegmente. Aktive rote und grüne Linien tragen Intervallbeschriftungen, etwa „1D · Grün“ oder „4h · Rot“. Nahe Beschriftungen werden versetzt und mit der zugehörigen Linie verbunden; die Infobox wird bei der Platzierung ausgespart. Äußere Hilfssegmente bleiben unbeschriftet. Orange kennzeichnet eine gebrochene rote Linie, keinen bestätigten Retest.
- **Datum** wählt einen Analysezeitpunkt in **New Yorker Zeit (ET)**. Alle Quellen werden vor der Berechnung auf bis dahin abgeschlossene Kerzen begrenzt. Bloßes Scrollen bleibt eine Änderung des Ausschnitts der geladenen Analyse. „Zur aktuellen Analyse“ lädt wieder den aktuellen Datenstand. Das Datum wird im Seitenlink erhalten.
- **◀ / ▶ neben Datum** springen um eine tatsächlich vorhandene Kerze des gewählten Intervalls zurück oder weiter; Tastatur **← / →**. Handelspausen werden übersprungen. Jede Zielanalyse wird auf den neuen Schlusszeitpunkt begrenzt. Der Zoom bleibt erhalten und die Ansicht folgt der letzten Kerze. Mit aktiver Fixierung endet der Rückweg an deren Datenstand; zum Untersuchen früherer Zeitpunkte zuerst die Fixierung lösen. Ohne weitere abgeschlossene Kerze bleibt die bisherige Ansicht mit einem Hinweis stehen.
- **Messwerkzeug ↕ / M**: zuerst den Startpreis, dann den Endpreis anklicken. Aufwärts blau, abwärts rot. Anzeige: absolute Preisänderung **pro Aktie**, Prozentänderung relativ zum ersten Punkt und Kerzenschritte. Die Zeitpositionen rasten auf vorhandenen Chartkerzen ein; die Preise wählst du frei. Jede abgeschlossene Messung wird automatisch in diesem Browser je Aktie gespeichert. Die aktive Messung bleibt beim Weitergehen, Intervallwechsel und Neuladen erhalten; beim Aktienwechsel wird der jeweils eigene Bestand geladen. Vor ihrem Endpunkt wird sie ausgeblendet und erscheint beim erneuten Erreichen wieder. **▤** öffnet die gespeicherten Messungen, **×** löscht die aktive Messung bzw. einen ausgewählten Listeneintrag. „Zuletzt gelöschte Messung wiederherstellen“ holt gelöschte Einträge auch nach einem Reload zurück. Eine neue Messung ersetzt die alten Einträge nicht. Speicherung gilt für diesen Browser und Origin (Host/Port), nicht geräteübergreifend. Bei vollem oder nicht verfügbarem Browserspeicher bleibt der bisherige Bestand erhalten und eine neue Messung wird als nur für die Sitzung gekennzeichnet. Gebühren und Stückzahl sind nicht enthalten.
- **Fixieren** speichert die gerade angezeigte automatische Analyse samt Rohkerzen als unveränderliche lokale Datei. Die Anker und der Analysezustand bleiben fest, während beim Laden späterer Zeitpunkte neue Kerzen ergänzt werden. Die Geraden verlängern sich mit ihrer Steigung weiter. Der historische Kerzenbestand wird beim Ergänzen nicht durch Providerkorrekturen ersetzt. „Fixierung lösen“ aktiviert die automatische Neuauswahl, behält aber das Archiv. Unter **Datum → Gespeicherten Linienstand öffnen** lässt sich ein Stand wiederherstellen. Auch die Positionen der Chartprojektion werden aus dem archivierten Achsenbestand festgehalten. Bei einem Quellanker nach der letzten abgeschlossenen Chartkerze bleibt dabei die damalige grafische Extrapolationsannahme erhalten. Die aktive Fixierung wird je Aktie im Browser gemerkt; die vollständige Datei liegt unter `data/snapshots/`. Ein Stand mit später abgeschlossenen Kerzen wird an einem früheren Datum abgewiesen; große Lücken zwischen Archiv und neuem Ladefenster ebenfalls. Kontakte und Brüche der Infobox bleiben bei Fixierung auf dem gespeicherten Analysestand, es wird kein neuer Ereignisverlauf gegen diese Linien berechnet.
- **Ray-Tool links** oder **R**: ersten und zweiten Punkt setzen. Die Linie wird nach rechts verlängert. Danach im Auswahlmodus Anker oder Linie ziehen. **V** aktiviert Auswahl, **Escape** bricht eine Zeichnung ab/hebt Auswahl auf. **Entf** beziehungsweise der Löschen-Button entfernt die ausgewählte eigene Linie **oder Messung**. Eine neue Messung ist automatisch ausgewählt; später ihren Rahmen anklicken oder sie über **▤** öffnen. **Strg+Z** und **↶** machen die jüngste Linien- oder Messänderung in gemeinsamer Reihenfolge rückgängig, einschließlich Anlegen und Löschen. Bei einem angefangenen Entwurf wird zuerst dieser abgebrochen. Rückgängig umfasst maximal 40 Änderungen für die aktuelle Sitzung und Aktie, auch über Intervall- und Datumssprünge hinweg. Neuladen oder Aktienwechsel setzt den Verlauf zurück; gelöschte gespeicherte Messungen lassen sich weiterhin über **▤ → Wiederherstellen** zurückholen.
- Eigene Rays sind **blau**, nach Aktie getrennt und über alle drei Intervalle sichtbar. Sie speichern Zeitstempel und Preise sowie das Ursprungsintervall; die automatische Tori-Analyse verändert sie nicht. Speicherung im lokalen Browserspeicher dieses Origins: anderer Browser, anderer Port oder `localhost` statt `127.0.0.1` hat eigenen Speicher. Bei gesperrtem Speicher wird ein Hinweis angezeigt. Test-Rays werden vor der Übergabe entfernt.
- **↻** ergänzt neue Kerzen. Beim ersten Abruf eines neuen Symbols ist der vollständige Download erforderlich. Danach bleiben Rohdaten auf dem Server gespeichert; nach fünf Minuten werden nur neue Daten plus sieben Tage Überlappung für Korrekturen angefordert. Die drei Quellen laden parallel; gleichzeitige Anfragen derselben Datei teilen sich den Download. Bei einem Abruffehler werden vorhandene Daten mit sichtbarer Warnung angezeigt. Browseransichten bleiben bis zum Aktualisieren/Neuladen auf ihrem geladenen Stand; kein automatischer Live-Ticker.
- Das Aktienverzeichnis wird für 24 Stunden gespeichert; bei einem Ausfall wird ein vorhandener älterer Katalog ausdrücklich gekennzeichnet.

## Linienregeln und Grenzen

`reference/Tori_Trendline_Automator_v5.pine` ist eine unveränderte Referenzkopie des bisherigen Skripts. `trendlines.py` überträgt seine automatische Wick-Hülle, strikte Richtungsprüfung, Folgekerzenbestätigung, Kontakte, Kontaktzeitraum und Linienauswahl. Die neue Version `tori-candle-axis-0.2` berechnet die Steigung pro vorhandener Quellkerze. Das ist eine bewusst geänderte Regel gegenüber der zeitbasierten Pine-Referenz: automatische Anker und Signale können abweichen. Zeitstempel bleiben die gespeicherten Ankerkennungen. 4h/1D: 365 Kalendertage, Qualität zuerst. 1h: 60 Tage, innerste bestätigte Linie. Eine qualifizierte Linie benötigt mindestens drei Kontakte über mindestens sieben Kalendertage. Kontakt-Toleranz als Prototypannahme: 0,01 USD. Die Linien sind mathematische Verlängerungen, keine Kursziele.

Die Suche nach dem jüngsten Bruch übernimmt die begrenzte v5-Suche (maximal 12 Quellkerzen, bei großen Fenstern weniger). „Kein Bruch“ bedeutet nur „keiner in diesem Abschnitt“. Dies ist kein vollständiges Ereignisarchiv. Manuelle Anker der automatischen Berechnung, automatisches Abspielen, Alarme und Strategie-Backtests sind nicht implementiert. Kerzenweise Vor-/Rückschritte sind vorhanden. Historische Stichtagsanalysen und unveränderliche gespeicherte Stände sind vorhanden. Eigene manuelle Zeichnungen liegen als getrennte Ebene vor.

Das Frontend verwendet Anbieterkerzen **direkt von Alpaca**, `feed=iex`, `adjustment=raw`. IEX ist ein einzelner US-Handelsplatz. Intraday-Aggregate können erweiterte Handelszeiten einschließen; es erfolgt keine Filterung auf TradingViews reguläre Sitzung. Die genaue Abweichung zu TradingView ist keine Aussage über die Qualität der Linienberechnung. Die Achse zeigt nur vorhandene Handelskerzen ohne reservierte Leerstellen. Geraden werden zwischen ihren Originalankern auf den Kerzenpositionen des gewählten Charts verlängert, ohne Knicke an Wochenenden. Bei Überlagerung eines anderen Quellintervalls ist dies eine **Chartprojektion**: wegen unterschiedlicher Kerzenverteilung kann der gezeichnete Preis vom Wert im eigenen Quellintervall abweichen. Infobox und Details kennzeichnen das; Bruchereignisse werden ausschließlich auf abgeschlossenen Quellkerzen im jeweiligen Quellintervall bestimmt. Ein visuelles Kreuzen einer MTF-Projektion ist deshalb kein zusätzlich bestätigtes Quellsignal. Das aktuelle Chartintervall und die übergeordneten Ebenen bleiben getrennt wählbar. Außerhalb der geladenen Historie wird für die grafische Zeitzuordnung der häufigste Zeitabstand angenommen; zukünftige Kurse oder Handelssitzungen werden nicht erfunden. Tagesdaten und Intraday-Aggregate werden unabhängig angefordert. Der Server lädt 450 Kalendertage, folgt sämtlichen Antwortseiten und verwirft formal ungültige sowie noch nicht abgeschlossene Kerzen. Er meldet erkannte formale Fehler und zu kurze Analysehistorie. Lücken ohne IEX-Transaktion werden nicht künstlich aufgefüllt; Vollständigkeit jedes Börsenfeeds wird dadurch nicht garantiert.

Intraday-Kerzenschluss = Anbieter-Start plus Intervall. Neue Tageskerzen verwenden den regulären XNYS-Schluss aus dem versionierten Börsenkalender, einschließlich verkürzter Sitzungen und Sommerzeit. Alte unveränderliche Datasets behalten ihren gespeicherten Schluss. Eine zusätzliche Sicherheitsverzögerung von 15 Minuten wird auf den Abrufzeitpunkt angewandt. Inkrementelle Abrufe gleichen sieben Tage rückwirkend ab; ältere nachträgliche Providerkorrekturen und Änderungen der Symbolzuordnung werden dadurch nicht vollständig neu eingelesen. Splits/Dividenden können unbereinigte längere Zeiträume beeinflussen. Gleiche Daten und Einstellungen ergeben dieselben berechneten Anker; der aktuelle Live-Datensatz wird bei späterem Abruf selbstverständlich ergänzt beziehungsweise vom Provider korrigiert.

Neue Forschungsdatasets erhalten ein beschreibendes Qualitätsaudit. Es meldet unter anderem fehlende Sitzungen und große Tageslücken, verifiziert Kapitalmaßnahmen aber nicht automatisch. Speicherübersicht, Importprüfung, Datenbankmigrationen, Backup/Restore und reine Aufräumvorschau sind in [BETRIEB-P2.md](BETRIEB-P2.md) beschrieben.

Historische Stichtage schließen spätere und noch offene Kerzen vor jeder Berechnung aus. Sie verwenden aber den heute verfügbaren historischen Anbieterbestand und aktuelle Symbolzuordnungen. Das ist keine garantierte Rekonstruktion der damals veröffentlichten Datenversion und keine Bereinigung von Survivorship Bias. Rückwirkende Datenkorrekturen können eine neu gerechnete historische Analyse verändern; ein bereits gespeicherter Stand bleibt erhalten. Die tägliche Quellkerze wird erst nach ihrem Abschluss zugelassen, auch wenn das Intraday-Datum bereits fortgeschritten ist. Beim ersten weit zurückliegenden Datum kann erneut ein vollständiges 450-Tage-Fenster nötig sein.

## Prüfung

Optional unter Forschung: **Tori-Kriterien · alle Einstiege im Zeitraum**. Dieser separate Modus prüft jede geschlossene 4h-Kerze, archiviert die ursprünglichen Linienpaare und bietet eine Fixierung zu X. Ausbruch, horizontale Bestätigung und Retest werden mit expliziten Kriterien geprüft; die bisherige Zufallsstudie bleibt wählbar. Anleitung und Grenzen: [TORI-EINSTIEGSMODUS.md](TORI-EINSTIEGSMODUS.md).

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Zusätzliche Frontend-Geometrietests (mit Node.js, ohne npm-Abhängigkeiten):

```powershell
node --test tests/test_geometry.cjs tests/test_snapshot_view.cjs tests/test_measurements.cjs
```

Die Geometrie wird gegen eine unabhängige quadratische Hüllensuche und auf wickfreie Verlängerung geprüft. Weitere Tests decken Bestätigung, Kontakte, Auswahl, abgeschlossene Kerzen, Sommerzeit und private HTTP-Routen ab. Browser- und Live-Datentests werden in `VERIFICATION.md` dokumentiert. Es wird keine vollständige Gleichheit zur Pine-Laufzeit oder Handelsprofitabilität behauptet.

## Aufbau

- `alpaca.py`: lesender Marktdatenadapter, Validierung, paralleler und inkrementeller Marktcache.
- `assets.py`: lesender Wertpapierkatalog, Namenssuche, Börsenfilter und Seitennavigation.
- `trendlines.py`: anbieterunabhängige automatische Geometrie auf normalisierten Kerzen.
- `server.py`: Loopback-HTTP-Server, harte Stichtagsgrenze und Zusammenführung der drei Intervalle.
- `snapshots.py`: unveränderliche lokale Analysestände.
- `data/snapshots/`: ignorierte Archivdateien mit Linien, Quellen und Kerzenbestand; nur über die lokale API erreichbar.
- `static/`: Oberfläche, Ray-Zeichenebene und lokal gebündelte Chartbibliothek.
- `data/market/`: ignorierter Rohdaten-Cache mit Abrufmetadaten.

Zusätzlich: `models.py`/`settings.py` für gemeinsame Datenmodelle und portable Pfade, `analysis_service.py` für die gemeinsame Chartanalyse, `datasets.py` für unveränderliche Datenbestände, `research.py` für kausale Ereignisstudien, `jobs.py` für die dauerhafte Queue und `tori.py` für Hermes-JSON-Werkzeuge. `deploy/` enthält die vorbereitete Linux-Diensteinrichtung.

Später kann EODHD hinter einem weiteren Adapter eingebunden werden. Kerzengrenzen und Preisanpassungen müssen beim Wechsel erneut abgeglichen werden.

## Abhängigkeiten und Quellen

Lightweight Charts **5.2.1** von TradingView ist lokal unter `static/vendor` gebündelt, Apache-2.0, Lizenzdatei liegt bei. Attribution in der Seite und im Chart. https://tradingview.github.io/lightweight-charts/

Alpaca Historical Bars: https://docs.alpaca.markets/us/reference/stockbars

Alpaca Feed-Erklärung: https://docs.alpaca.markets/us/docs/market-data-faq



Alpaca-Wertpapierverzeichnis: https://docs.alpaca.markets/us/reference/get-v2-assets-1

Bei „Verbindung zum lokalen Tori-Server fehlgeschlagen“ zuerst `Start-Tori.ps1` ausführen und anschließend ↻ oder die Seite neu laden. Wenn der Server läuft, aber Alpaca eine Anfrage ablehnt, wird die separate Anbieterfehlermeldung angezeigt.

Diskussionsstand für spätere Long-Tests: `LONG-KRITERIEN-ENTWURF.md` (noch keine aktivierten Einstiegskriterien).


**Kontaktzonen und drei Forschungsrunden (19.10.2026):** [Regeln, Auswertung und Schlussfolgerungen](KONTAKTZONEN-EXPERIMENTE.md), [vollständige Tabellen](KONTAKTZONEN-ERGEBNISSE.md). Neue Profile sind im Labor ausdrücklich wählbar; die bisherigen Standardprofile bleiben erhalten.
