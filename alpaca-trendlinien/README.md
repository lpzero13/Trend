**Neu: [Strukturfilter für historische Signalkandidaten](SIGNALFILTER-BEWERTUNG-20261031.md).** Neun gemeinsame Offline-/Chartprofile unter „Historische Einstiege → Signalauswahl“. Qualifizierte Ausbrüche/Retests als Ausgangsansicht, zusätzliche Abstands-, SMA200-, Reife- und Verengungsfilter experimentell. [Ergebnisse aus 69 Aktien](SIGNALFILTER-ERGEBNISSE-20261031.md): 749 kombinierte oder 206 strenge Kandidaten; strenge Auswahl ist historisch schwächer, kein bestätigter Gewinnerfilter. Erste archivierte Signale filtern ist umgesetzt; ein neuer Scanner für den ersten erst später geeigneten Trigger bleibt geplant.

**Neu: [Safety-Folgeexperiment mit unveränderten Entries](SAFETY-FOLGEPLAN-20261031.md).** Zwei neue interne Stopvarianten: aktuelle Safety nur bei bestätigter Qualifikation oder erst ab +2R. [69-Aktien-Ergebnisse](SAFETY-FOLGEERGEBNISSE-20261031.md) · [Bewertung](SAFETY-FOLGEBEWERTUNG-20261031.md). Offene Buchwerte und Datenlücken getrennt, identische Fälle vergleichen. Höhere historische Mittel bei Ausbruch/Retest, schlechtere Mediane; keine Strategiefreigabe oder automatische Umstellung bestehender Defaults.

**Neu: [Historische Einstiege im normalen Chart](HISTORISCHE-EINSTIEGE.md).** Feste Signalpunkte und ursprüngliche Linien aus gespeicherten Untersuchungen, Familien-/Qualitätsfilter, Replay-Sprung und eigene Bewertungen. Optionale Offline-Suche für andere Zeiträume; keine automatische Neuberechnung beim Anzeigen. Datenbank Schema 5, gleicher Datenpfad; bei Updates vorhandene Dienste kontrolliert neu starten.

**Neu 31.10.2026: [Signalepisoden ohne Kapital-/Slotlimit und ohne Zeitexits](SIGNALFALLSTUDIE.md).** Eigenständiger Offline-Modus, gemeinsamer kausaler Linien-/Entrykern, strukturelle Wiederholungserkennung und drei Hard-Stop-Varianten. [69-Aktien-Ergebnisse](SIGNALFALL-ERGEBNISSE-20261031.md) · [Bewertung](SIGNALFALL-BEWERTUNG-20261031.md). 6.668 Fälle aus 4.614 Episoden, 10.218 Wiederholungen unterdrückt; leichte positive historische Mittel bei aktueller Safety, negative Mediane und keine Strategiefreigabe. Alte Depotstudien und Chart bleiben erhalten.

**Weitere Exitforschung (30.10.2026):** [Hard gegen 4h-Close, 40 gegen 80 Handelstage und Daten-Nachprüfung](EXIT-FORSCHUNGSERGEBNISSE-20261030.md). Roter Retest mit ursprünglicher Safety und längerer Haltedauer bleibt eine interessante Hypothese, mit erhöhtem Drawdown und Gewinnerkonzentration. Reiner Close-Stop zeigt große Verlustspitzen. 192 Depotvergleiche plus zwölf Konzentrationsdiagnosen geprüft; keine Strategiefreigabe oder automatische Umstellung.

**Einstiege / Exits getrennt (30.10.2026):** [Drei Entry-Familien, Kontaktklassen und identische Fälle für drei Exitmethoden](ENTRY-EXIT-ERGEBNISSE-20261030.md). 168 getrennte Depotbücher und sortierbare private CSVs. Ausbruch mit festem Stop und Retest mit geometrischem Nachziehen bleiben unterschiedliche Forschungshypothesen; keine neue Strategiefreigabe.

**Feste Robustheitsprüfung (30.10.2026):** [69 Aktien, vier Zeitfenster, Kostenstress und Ergebnisse](ROBUSTHEITSERGEBNISSE-20261030.md) · [Vorabplan](ROBUSTHEITSPLAN-20261030.md). Zwei vollständig auswertbare Gesamtdepots positiv, zwei wegen Datenlücken unvollständig; Kontrollvergleiche unvollständig, keine Strategiefreigabe. 30 konkrete Symbol-/Tagespaare zur Datenprüfung vorgemerkt. [Neues Signaljournal für Einzelschritte, eingefrorene Signale und Hermes](SIGNALJOURNAL.md), einschließlich Wiederaufnahme und Backup/Restore. Kein neuer Dauerdienst gestartet.

**Datensammler V2 (30.10.2026):** Neues Menü **Datensammler** (`/sammler`) mit vollständigen Emittenten-Abbildern, gemeinsamer Auswahl ohne doppelte Symbole, Start/Pause, geprüftem Cache und Übernahme alter Bestände. [Bedienung und Hermes-CLI](SAMMLER-V2.md) · [Messwerte, Datenprüfung und Zeit-/Speicherplanung je Universum](SAMMLER-V2-ERGEBNISSE.md). Echter Fünf-Aktien-Vergleich: rund 34 % weniger Zeit bei exakt gleichen Kursbeständen. Große Universen wurden dafür nicht gestartet; der frühere 100er-Lauf bleibt bei 69 fertigen Aktien pausiert.

**Chart / Replay:** [Trendlinien zuschalten, kerzenweise entwickeln und am Datum fixieren](CHART-REPLAY-FIXIERUNG.md). Funktioniert auch im Zufallsmodus und bei lokalen Datasets; Analyse startet weiterhin aus.

**Historienarchiv:** [Fortsetzbarer SIP-Sammelimport ab 2016, Parquet/Zstd, Qualitätsprotokoll und Hermes-CLI](HISTORIENARCHIV.md). Das erste benutzergewählte Universum umfasst Dow-30 plus 70 weitere S&P-100-Titel. Der tatsächliche Importstatus wird pro Job gespeichert.

# Tori Market Lab – Alpaca-Prototyp

**Technische Strategiesuche:** [Zwei festgelegte Runden, 16 Aktien und gemeinsames Kapitalbuch](STRATEGIE-SUCHE-ERGEBNISSE-20261030.md). Positive Modellkandidaten, aber das zusätzliche Zufallskontrolltor ist noch nicht bestanden. Alle Ergebnisse und Kosten-/Konzentrationsgrenzen sind dokumentiert; Webausbau bleibt zurückgestellt.

**Begrenzter Technikpilot:** [Eine Aktie / zwölf Monate, drei Entry-Familien und kausale Exitvergleiche](BACKTEST-PILOT.md). Explizit per `python tori.py pilot-backtest` aus vorhandenen lokalen Daten; keine automatische Großstudie. MSFT/2023 technisch reproduzierbar durchgelaufen, keine Strategiefreigabe.

**Roadmap:** [Backtest-Meilensteine: Datenbasis → Signalsuche → Verlauf → Exits → Robustheit → Depot → Hermes](BACKTEST-MEILENSTEINE.md). Technikpilot, Mehraktien-Kapitalbuch und feste Robustheitsrunde sind umgesetzt. Datenbereinigung, unabhängige Strategiebestätigung und Hermes-Dauerbetrieb bleiben offen.

**Pine Master · 29.10.: [Update und Bedienung](TORI-MASTER-UPDATE-20261029.md)** – zusätzlicher `fan_master`-Modus mit Hüllkurvenanpassung, getrennten Suchhorizonten, Haupt-Safety und SMA-Kontext.

**Neu: [Tori-Fächer-Test](TORI-FAECHER.md)** – optionaler Python-Linienfinder, kausale Ausbruch-/Retestfälle und Einzelfallpfade mit Stop/Kosten. Web `/faecher`; bisherige Analyse bleibt verfügbar und startet weiterhin aus. Beispielauftrag: `deploy/fan-study.example.json` (vorhandene lokale Dataset-ID einsetzen).

**1W und Offline-Speicherplanung, 28.10.2026:** Wochenansicht in Chart und Zufallsmodus mit vollständigen abgeschlossenen XNYS-Wochen aus vorhandenen Tagesquellen, Wochen-Schritten sowie Zeichnungen/Messungen. Keine Monatskerzen oder Änderung alter Forschungsdatasets. [Aktienbestand, gemessener SQLite-Platzbedarf und Universumsplanung](WOCHEN-UND-DATENSPEICHER.md).

**Zufall, 28.10.2026:** Neuer Menüpunkt `/zufall` für manuelle Übungen mit zufälliger Aktie/historischem Zeitpunkt aus lokalen Marktdaten, bekannten 1h-/4h-/1D-Präfixen und Kerzenschritten vor/zurück. Zeichnungen/Messungen bleiben je Fall getrennt gespeichert. Neue Linienarten: Ray links/rechts, Gerade beidseitig, Strecke und horizontaler Widerstand/Unterstützung. [Bedienung und Auswahlgrenzen](ZUFALLSMODUS.md).

**SIP-Kandidatenversuch, 22.10.2026:** Menü **Kandidaten** unter `/kandidaten`, 20 zusätzliche blinde SIP-Fälle, Merkmals-/Zufallskontrollvergleich von 349 historischen 4h-Retests, zwei Stoppmodelle und 28 Cashledger. Getrennter prospektiver SIP-Papierbeobachter, alte IEX-Beobachtung unverändert. [Bedienung, Speichergrenzen und Hermes-API](TORI-KANDIDATEN.md) · [Plan](TORI-KANDIDATEN-PLAN.md) · [Ergebnisse und Grenzen](TORI-KANDIDATEN-ERGEBNISSE.md). Keine validierte Handelsfreigabe; fehlende Pfade und offene Bewertungen bleiben sichtbar.

**Lokale Werkbank, 22.10.2026:** [Bedienung, Sichtprüfung und Hermes-Scanner](TORI-WERKBANK.md). Neuer Menüpunkt **Sichtprüfung**: eigene Linien/Widerstände/Kontakte zuerst speichern, Engine erst ausdrücklich aufdecken; 102 vorbereitete Präfixe, keine erfundenen menschlichen Urteile. Separater erklärter Scanner mit stabilen Fakten, Präfix-/Codeprüfung und paginiertem dauerhaftem Journal. [Unveränderter SIP/IEX-Datenvergleich und getrennte Kapitalrechnung](TORI-WERKBANK-ERGEBNISSE.md), [Bilanz und Folgerungen](TORI-WERKBANK-FAZIT.md), [Vorabplan](TORI-WERKBANK-PLAN.md). Historische SIP-Abfrage mit bestehendem Zugang erfolgreich; vorhandener Beobachter und manuelle Chartdefaults bleiben unverändert. Kein neuer Dauerdienst, keine Orders oder Profitabilitätsfreigabe.


Repository und zentrale Hermes-/Container-Dokumentation: [Trend](https://github.com/lpzero13/Trend) · [HERMES.md](../HERMES.md). Dieses Verzeichnis ist die Anwendung innerhalb des Repositories.

**Separater größerer Kriterienversuch, 22.10.2026:** [Bilanz auf 60 angefragten / 57 verwendbaren Aktien mit Historie ab 2020](TORI-GESAMTTEST-ERGEBNISSE.md), [vorab festgelegte Regeln](TORI-GESAMTTEST-PLAN.md), [vollständige Tabellen und CLI](TORI-GESAMTTEST-TABELLEN.md). Drei unabhängige Kontakte ohne Dochtverletzung, 4h und Tagesbasis, gestufte Einstiegskriterien und natürliche Ausstiege ohne Zehn-Tage-Zwang. Technisch geprüft; vollständiger Ereignisfilter und menschliche Linienabnahme fehlen, keine validierte Handelsstrategie. Chart, bestehende Forschungsprofile und laufende Beobachtung werden nicht umgestellt.

**Neue lokale Beobachtung, 22.10.2026:** Menü **Beobachtung** (`/watch`) zeigt neue Fälle beider unveränderter Geometrien mit damaligen Linien, bewusst zuschaltbarem Verlauf und manuellen Urteilen. Separater Hintergrunddienst mit gespeichertem Beginn, konsistentem Erstimport, späteren inkrementellen Updates, Journal und Wiederaufnahme. [Regeln, CLI, Start/Stop und Betriebsgrenzen](FORWARD-BEOBACHTUNG.md). Lokal gestartet; Erstimport aller 25 Aktien abgeschlossen, beide Geometrien werden im Hintergrund beobachtet. Noch keine prospektive Erfolgsbilanz. Kein automatischer Handel oder Proxmox-Rollout.

**Unabhängiger Vergleich und Beobachtung, 22.10.2026:** [Bilanz, Werkzeuge und Hermes-Vertrag](RETEST-BEOBACHTUNG-ERGEBNISSE.md). Bisher reservierter Abschnitt Juli–Oktober einmalig mit eingefrorenen Regeln ausgewertet: Zonen-Retests diesmal negativ, ATR-Risikohypothese nicht bestätigt. [Vorabplan](RETEST-BEOBACHTUNG-PLAN.md), [alle Tabellen](RETEST-BEOBACHTUNG-TABELLEN.md). Neuer persistierter Offline-Beobachter für ursprüngliche Entries und beide Exitpfade; Wiederaufnahme geprüft, noch kein prospektiver Dauerdienst. Webstandard bleibt unverändert.

**Weitere interne Exits, 22.10.2026:** [Orange-Zonen-Fehlschlag, Fünf-Tage-Zeitexit und ATR-Gewinnschutz](RETEST-EXIT-VARIANTEN-ERGEBNISSE.md), jeweils gegen die feste Safety. Regeln vorab fixiert, nacheinander getestet; kein neuer Webstandard. Keine klare Ertragsverbesserung bei den Zonen, ATR als weiter zu prüfende Risikovariante. Private Laufdaten/Marktdatasets werden nicht versioniert.

**Interner Versuch, 22.10.2026:** [Retest-Exit-/Kapitalvergleich](RETEST-EXIT-ERGEBNISSE.md) auf unveränderten archivierten Entries: fester Stop gegen bestätigtes Stopnachziehen, zehn Sitzungen, vollständige Vorgeschichte und Datenlücken getrennt. Eigene CLI, keine Umstellung der Oberfläche. Zonen-Retests im begrenzten bekannten Datensatz positiv; Nachziehen bisher kein überzeugender Vorteil, keine validierte Handelsfreigabe.

**Interner Versuch, 21.10.2026:** [Zusätzliche Einstiegssuche und persistierter Beobachtungsscanner](EINSTIEGSSUCHE-ERGEBNISSE.md). Separate CLI-Module; kein automatischer Wechsel der Webanalyse. Der Vergleich findet mehr zusätzliche Zeitpunkte, bisher keine nachweislich besseren direkten Einstiege. Regeln, Ergebnisgrenzen und Wiederholungsbefehle sind dort dokumentiert.

## Chart manuell oder mit Tori-Analyse

Die Weboberfläche startet **bei jedem Öffnen und Neuladen mit ausgeschalteter Tori-Analyse**. Die Kerzen werden angezeigt; Ray- und Messwerkzeug, gespeicherte eigene Zeichnungen, Zoom und historische Kerzenschritte bleiben nutzbar. Es erscheinen zunächst keine automatischen Trendlinien, Bruch-/Einstiegsmarker oder Tori-Infoboxen.

Mit **„Tori-Analyse: Aus“** einschalten: Der Knopf wechselt auf **„Tori-Analyse: An“**, die bestehende automatische Chartanalyse wird geladen und Linien/Marker/Infobox erscheinen. Erneuter Klick blendet diese wieder aus, ohne eigene Zeichnungen oder Messungen zu löschen. Die Infobox ist nach dem Einschalten zunächst ausgeklappt. Die Wahl gilt für die laufende Seite, auch bei Intervall-/Aktienwechseln; beim Neuladen ist Tori wieder aus. URL-Parameter und alte Browsereinstellungen aktivieren die Analyse nicht automatisch.

Auch Forschungslinks und über „Datum“ geöffnete Fixierungen starten ohne Tori-Einblendungen. Ein gespeicherter Stand wird ausdrücklich über Datum gewählt; alte Fixierungen werden beim manuellen Seitenstart nicht automatisch geladen. Beim Einschalten einer ausdrücklich geöffneten Fixierung werden deren ursprüngliche Linien verwendet. Ohne aktivierte Analyse ist „Fixieren“ ausgeblendet. Datum/Replay bleiben bedienbar; die Fixierungsgrenze für Linien greift wieder bei aktiver Analyse.

Im Hintergrund fordert die Oberfläche zunächst `/api/chart?…&analysis=0` beziehungsweise `/api/dataset-chart?…&analysis=0` an. Die Antwort enthält Kerzen und Quellenmetadaten, `analysisEnabled: false`, leere `lanes` und keine neue `analysisId`. Linienberechnung und Signaloverlays werden übersprungen. Einschalten verwendet `analysis=1`; Ausschalten benötigt keinen neuen Abruf. Neue manuelle Kursabrufe entwerten ältere Analyse-Caches derselben Ansicht. Fehlt `analysis`, bleibt das frühere API-Verhalten aktiv; bestehende CLI-/Forschungsaufrufe werden nicht still umgestellt.

Der Schalter betrifft die vorhandene automatische **Chartanalyse** mit Intervalllinien, Kontakten, Qualität und Bruchmarkierungen. Er startet keine Forschungsaufträge oder Safety-Portfolios und ändert keine laufenden Zeitpläne. Der neue Safety-Kandidatenscan bleibt der separat dokumentierte CLI-Forschungsweg.

Lokale Seite mit echten historischen IEX-Kursen von Alpaca, Kerzen für **1h, 4h und 1D** sowie der automatischen Tori-Linienberechnung. Manuelle Suche unter `/`, automatische Ereignisstudien unter `/research`. Hintergrundaufträge mit Zufallsstarts, unveränderlichen Datenbeständen und JSON-Werkzeugen für Hermes. Keine Orderfunktionen.

**Neu lokal, 20.10.2026:** Separater [Safety-Strategie- und Kandidatenweg für Hermes](SAFETY-STRATEGIEN.md) über die CLI, mit Kosten, kausalen Ausstiegen, Kapital-/Risikoportfolio und unabhängiger Nachrechnung. [Bilanz auf 25 Aktien](SAFETY-ERGEBNISSE.md): noch keine als profitabel bestätigte Strategie. Webprofile und Zeitpläne werden nicht automatisch umgestellt; die bisherigen Ereignisstudien bleiben Kursbeobachtungen ohne Depot-P/L.

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
- Eigene Linien sind nach Aktie getrennt und über 1h/4h/1D/1W sichtbar. Die zwei Zeit-/Preisanker bleiben beim Intervallwechsel erhalten und werden in jedem Intervall durch eine Gerade verbunden; nur absichtliches Verschieben ändert die Anker. Oben neben der Linienart lässt sich die Farbe der ausgewählten Linie bzw. die Vorgabe für neue Linien ändern. Automatische Tori-Signale verwenden diese Zeichnungen nicht. Speicherung im lokalen Browserspeicher dieses Origins: anderer Browser, anderer Port oder `localhost` statt `127.0.0.1` hat eigenen Speicher. Bei gesperrtem Speicher wird ein Hinweis angezeigt. Details und Projektionsgrenzen: [Parquet und persönliche Linien](PARQUET-SPEICHER.md).
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
