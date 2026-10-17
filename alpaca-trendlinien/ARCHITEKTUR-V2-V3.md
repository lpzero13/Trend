# Tori: Umbau für Hermes, Proxmox und selbstständige Backtests

Stand: 17.10.2026. Architekturprüfung des vorhandenen Codes, keine bereits implementierte V2/V3. Die laufende Anwendung wurde für diese Prüfung nicht verändert. Die konkrete Installation, Hardware und Werkzeugschnittstelle von Hermes/Proxmox wurden nicht untersucht.

Nachtrag: Die anschließende Umsetzung des gemeinsamen Kerns, der explorativen Ereignisstudie, dauerhafter Jobs, Webansicht und Linux-Dienstvorbereitung wird in [FORSCHUNG.md](FORSCHUNG.md) beschrieben. Der folgende ursprüngliche Plan umfasst darüber hinaus spätere Portfolio-/Scanner-Funktionen und ist keine Liste bereits vollständig implementierter Funktionen.

## Ergebnis

Die vorhandene Python-Geometrie ist eine brauchbare Basis. Empfohlen ist eine gemeinsame Python-Engine für Chart, historische Wiedergabe, Scanner und Backtest. Hermes startet definierte Aufträge und liest deren Ergebnisse. Kursberechnung, Ausführungssimulation und Ergebniszahlen bleiben reproduzierbarer Programmcode.

V2: eine Aktie ohne Browser vollständig durchspielen; vier vereinbarte Long-Testgruppen separat auswerten. V3: mehrere Aktien, wiederaufnehmbare Aufträge, zeitgesteuerter Scanner und Hermes als Auftraggeber/Auswerter. Ein Container allein ergänzt noch keine Backtest-Engine.

## Konkrete Befunde im aktuellen Code

| Stelle | Bereits vorhanden | Nötiger Umbau |
|---|---|---|
| `trendlines.py`: `build`, `choose`, `pair` | Deterministische Geometrie auf normalisierten Kerzen | Beibehalten; `Bar`, Börsenzeitzone und Fehlerklassen aus dem Alpaca-Modul in gemeinsame Modelle/Konfiguration lösen. Regeln explizit übergeben. |
| `trendlines.py`: `analyze` | Vorherige Linien werden gegen nachfolgende Schlusskurse geprüft | Geometriezustand und Ereigniserkennung trennen. Der kurze Rückblick und ein einzelnes überschriebenes `event` ersetzen kein Journal. `retest` enthält eine gebrochene rote Linie, keinen bestätigten Rücklauf. |
| `server.py`: `chart_payload` | Abruf, Stichtagsfilter, drei Quellanalysen und Chart-JSON | In einen browserunabhängigen Analysedienst aufteilen. HTTP und CLI rufen denselben Dienst auf. Simulation lädt Daten einmal, nicht pro Kerze einen vollständigen Chart-Payload. |
| `alpaca.py`: `load_bars` | Validierung, Seitennavigation, Cache und lesender Abruf | Explizite Zeiträume, Datenordner und Providervertrag; Abruf vom Replay trennen. Veränderlichen Cache nicht als unveränderlichen Testbestand verwenden. |
| `alpaca.py`: `bar_end` | Intraday-Start plus Intervall, Tagesende pauschal 16 Uhr New York | Sessionmodell und tatsächliche Verfügbarkeit definieren. Feiertage, verkürzte Sitzungen, Anbieteraggregation und verzögerte Daten getrennt behandeln. |
| `assets.py`: `normalize_assets` | Aktuell aktive US-Instrumente | Gewähltes Testuniversum mit Datum/Quelle archivieren. Aktive Titel von heute sind kein historisches Universum einschließlich später verschwundener Titel. |
| `snapshots.py`: `remember`, `save_snapshot` | Manuelle, unveränderliche Analysestände | Direkte Speicherung von Auftrags-/Signalzuständen ermöglichen. Aktuell muss der Stand zuvor in einem auf 32 Einträge begrenzten Prozessspeicher liegen. |
| `static/analysis.js`: `snapshotChart`, `fixedChartPositions` | Archivierte Kerzen und Fixierung werden im Browser angewandt | Fachliche Fixierung in Python abbilden; JS behält Darstellung. Sonst gelten für den Headless-Lauf nicht automatisch dieselben Zustände. |
| `static/measurements.js`, eigene Rays | Persönliche Browserwerkzeuge | Für automatische Tests nicht erforderlich. Später serverseitig synchronisieren, falls Windows- und Containeransicht denselben Bestand zeigen sollen; bestehende Browserdaten ausdrücklich migrieren. |
| `server.py`: `Handler`, `main` | Lokaler Server mit Host-/Origin-Prüfung | Loopback weiter als Standard. Fernzugriff bewusst über getrennte, authentifizierte Schnittstelle oder SSH; keine pauschale Freigabe aller Hosts/Origins. |

Weitere Beobachtungen: `analyze` wählt Regeln momentan anhand des Intervalls intern aus. `load_bars` hat einen festen Rückblick von 450 Kalendertagen und Dateicaches pro historischem Enddatum. Dateisperren schützen Threads desselben Prozesses, nicht mehrere Worker-Prozesse. `quality.rejected` fließt in die Analyse ein, eine veraltete Cache-Warnung ist noch keine verbindliche Sperre für automatische Entscheidungen.

Lokale Stichprobe ohne Netzwerk: MSFT mit 2.455/783/310 Kerzen für 1h/4h/1D; je ein `analyze`-Aufruf ungefähr 24/22/13 ms. Dabei wurden nur die letzten 11/6/12 Quellkerzen auf Ereignisse durchsucht. Diese Einzelmessung sagt nichts über vollständige mehrjährige Portfolioläufe oder die Containerhardware aus.

## Gemeinsamer Kern

Vorgeschlagene Verantwortlichkeiten, keine Forderung nach einer sofortigen Komplettmigration aller Dateien:

```text
tori/
  domain/        Bar, Instrument, Line, Signal, Position, Rules
  providers/     Alpaca; später EODHD
  datasets/      Import, Qualität, Versionen, Sessiongrenzen
  engine/        Analyse, Ereignisse, Setup-Zustände, Fixierung
  backtest/      Zeitsteuerung, simulierte Ausführung, Portfolio, Kennzahlen
  storage/       Aufträge, Checkpoints, Ereignisjournal, Ergebnisdateien
  interfaces/    CLI/JSON und HTTP
static/          bestehende Chartoberfläche
```

Der Provider liefert Kerzen und Metadaten. Die Engine benötigt weder HTTP noch Zugangsdaten. Ein Analyseauftrag enthält Instrument-ID, Provider, Feed, Kursanpassung, Sessionschema, Intervalle, expliziten Stichtag und Regelkonfiguration. Zeitzonen gehören zum Instrument bzw. Markt, nicht global zum Alpaca-Adapter.

Die bestehende Chartdarstellung bleibt erhalten. Linien im anderen Chartintervall sind weiterhin Projektionen. Einstieg, Abstand und Stopprüfung verwenden ausschließlich die jeweilige Quellachse. Kalender, Kerzengrenzen und fehlende Feed-Kerzen können Anker und Signale beeinflussen; ein Wechsel zu EODHD braucht deshalb einen eigenen Datenvertrag und Vergleichstests.

## V2: reproduzierbarer Einzelaktien-Backtest

1. **Datenimport:** Gewählten Testzeitraum plus genügend Aufwärmhistorie laden, normalisieren und prüfen. Der heutige 450-Tage-Rückblick ist eine Abrufentscheidung des Prototyps, keine Aussage über die gesamte Providerhistorie. Für die 365-Tage-Regeln vor dem ersten ausgewerteten Signal ausreichend Vorlauf vorsehen; unvollständigen Vorlauf kennzeichnen.
2. **Unveränderlicher Bestand:** Dataset mit allen verwendeten Intervallen, Instrumentzuordnung, Feed, Anpassung, Sessiondefinition, Abrufzeit und Inhaltsprüfsummen sichern. Ein laufender Test liest nur diese Version und braucht keinen Providerzugriff. Anbieterrevisionen erzeugen neue Dataset-Versionen.
3. **Simulierte Zeit:** Eine gemeinsame Uhr vorwärts bewegen. Die Strategie bekommt nur bis dahin abgeschlossene und nach der festgelegten Latenz verfügbare Kerzen. 1D und 4h werden über ihre Verfügbarkeit zusammengeführt; eine noch offene Tageskerze darf keine Intraday-Entscheidung beeinflussen. Bei verspäteter Signalfreigabe muss auch der Ausführungszeitpunkt später liegen.
4. **Einzelner Engine-Schritt:** Den vor der neuen Kerze bekannten Linienzustand gegen diese Kerze prüfen. Erst danach neue Geometrie für die nächste Entscheidung auswählen. Für jeden Zustand muss feststehen, wann seine Anker und deren Bestätigung bekannt waren. Die heutige Präfixberechnung dient zunächst als einfache Referenz; Optimierung erst nach Vergleichstests.
5. **Vier getrennte Strategiezweige:** Ausbruch und Retest jeweils mit Zwei-Kontakt- bzw. qualifizierten Linien. Qualitätsgruppe beim Signal festhalten; bei gemischter Qualität die vereinbarte schwächere Linie verwenden. Puffer, Fristen, Stop und vollständige Ausstiegsregel sind noch festzulegen; siehe `LONG-KRITERIEN-ENTWURF.md`.
6. **Setup-Zustandsmaschine:** Beispielsweise `beobachtet -> Ausbruch bestätigt -> wartet auf Retest -> Einstieg geplant -> Position offen -> beendet/verworfen`. Ein Red-Bruch allein ist kein Retest. Jede Transition bekommt Zeit, Grund und stabile ID.
7. **Fixierung:** Die tatsächlich gebrochene rote Linie und die damalige grüne Schutzlinie am Signal archivieren. Neue automatische Analyselinien laufen parallel weiter. Alte Signale und bereits laufende Positionen werden dadurch nicht rückwirkend umgeschrieben. Eine Kerzenlinie behält ihre Anker und Steigung pro vorhandener Quellkerze; sie wird fortgeschrieben, nicht zu einem horizontalen Preis gemacht. Indizes müssen auf einer stabilen Dataset-Achse liegen, nicht auf einem später verschobenen Ladefenster.
8. **Ausführungssimulation:** Erst nach dem Signal verfügbare Ausführungskurse verwenden. Die nächste Eröffnung ist nur dann geeignet, wenn sie zeitlich nach Signalverfügbarkeit liegt und zur Handelssitzung passt. Kosten, Slippage, ganze Aktien, Cash, reserviertes Risiko und Gaps abbilden. Feinere Ausführungsdaten bei Bedarf getrennt importieren; die Strategie sieht deren Zukunft nicht. Unklare Abläufe innerhalb einer OHLC-Kerze markieren oder konservativ behandeln.
9. **Ergebnis:** Signale, Auslassungen mit Gründen, simulierte Ausführungen, Positionen, Equity-Verlauf und Kosten speichern. Offene Positionen am Testende ausdrücklich behandeln. Rendite, Drawdown, Tradezahl und Verlustserien aus demselben Journal ableiten. Einzelfälle im bestehenden Chart wieder öffnen können.

Die vier Varianten werden als eigenständige Experimente geführt. Für spätere Portfolios müssen auch zeitgleiche Signale verschiedener Aktien durch ein gemeinsames Cash-/Risikolimit laufen; Einzeltitel-Ergebnisse dürfen nicht ungeprüft addiert werden.

Wichtige Grenze: Heute heruntergeladene historische Kurse rekonstruieren nicht automatisch die damals publizierte Datenversion. Auch Alpacas `asof`-Parameter für Symbolzuordnung ist keine historische Datenversionierung. Im Bericht deshalb zwischen kausalem Replay auf einem heutigen Dataset und einer echten Rekonstruktion damaliger Veröffentlichungen unterscheiden. Bei mehrjährigen Tests Kapitalmaßnahmen und ausgeschiedene Titel berücksichtigen; ungeklärte Splits zunächst ausschließen/kennzeichnen, statt sie als Signale zu behandeln.

## Dauerhafte Aufträge und Hermes-Schnittstelle

Für den ersten Container: lokale SQLite-Datenbank für `jobs`, `experiments`, `events`, `checkpoints` und Ergebnisverweise; unveränderliche Datasets separat auf lokalem persistentem Speicher. Ein Worker übernimmt Schreibzugriffe, die Oberfläche liest über den Dienst. Keine SQLite-Datei als gemeinsame Netzwerkfreigabe zwischen Hermes und Tori verwenden.

Ein Auftrag hat eine ID, eine feste Konfiguration und Zustände `queued/running/succeeded/failed/cancelled`. Fortschritt, letzter abgeschlossener Schritt, Fehler und Heartbeat werden gespeichert. Nach einem Neustart wird ab einem transaktional gesicherten Checkpoint weitergemacht. Checkpoint umfasst Zeitposition, bekannte Linien, wartende Retests, Positionen, Cash und Journalposition. Doppelte Zustellung desselben Auftrags/Schritts erzeugt keine doppelten Signale oder Trades. Wiederholung mit veränderten Regeln bekommt eine neue Experiment-ID.

Die Schnittstelle kann zunächst eine CLI mit JSON-Ausgabe sein. Beispielnamen als Entwurf, diese Befehle existieren noch nicht:

```text
python -m tori dataset import --spec dataset.json
python -m tori analyze --spec analysis.json
python -m tori backtest submit --spec experiment.json
python -m tori job status --id <job-id>
python -m tori report --id <job-id> --format json
```

Hermes kann diese eng umrissenen Werkzeuge im selben Container oder über eingeschränkten SSH-Zugang nutzen. Falls Hermes ausschließlich HTTP-Werkzeuge unterstützt, dieselben Operationen über eine interne, authentifizierte Job-API anbieten. Lange Tests nicht innerhalb eines offenen HTTP-Requests abarbeiten: sofort eine Job-ID zurückgeben, Fortschritt/Ergebnis getrennt abrufen. Welche Anbindung passt, hängt von der noch zu prüfenden Hermes-Installation ab.

Hermes darf vorgegebene Konfigurationen auswählen, Aufträge einreichen und Zahlen/Einzelfälle zusammenfassen. Ein technischer Scan und ein Backtest laufen auch ohne LLM weiter. Für Tests mit Nachrichten oder LLM-Einstiegsfiltern müssen Eingaben und Ausgaben zeitlich versioniert werden; heutiges Wissen über spätere Kursverläufe darf nicht in historische Entscheidungen gelangen. Für V2 wertet Hermes deshalb nur die fertigen technischen Ergebnisse aus.

## V3: Batch, Scanner und kontrollierte Experimente

- Mehrere Instrumente und Zeiträume aus einem versionierten Universum; zunächst kleine, feste technische Testliste statt des gesamten aktuellen Katalogs.
- Abruflimit zentral je Provider verwalten; Wartezeiten, Wiederholungen und begrenzte Parallelität. Datenfehler eines Symbols ergeben einen dokumentierten Auslassungsgrund, keinen scheinbar erfolgreichen vollständigen Lauf.
- Zeitgesteuerte Scans an tatsächlichen Quell-Kerzenschlüssen mit definierter Verzögerung. Nicht schlicht alle vier Kalenderstunden ab Mitternacht; Sessiongrenzen, Sommerzeit und Tagesfreigabe beachten. Verpasste Abschlüsse nach einem Ausfall nachholen, Ereignisse über IDs deduplizieren.
- Benachrichtigungen über eine spätere Ausgangsqueue entkoppeln. Nur neue relevante Ereignisse senden; wiederholte Scans erzeugen keine Nachrichtenflut.
- Große Backtests in kontrollierbare Aufträge aufteilen. Gemeinsame Portfolioauswertung bleibt zeitlich synchron. CPU-Worker erst nach Messung erhöhen; Schreibzugriffe zentralisieren. Bei mehreren schreibenden Diensten/Hosts gegebenenfalls auf eine Serverdatenbank wechseln.
- Hermes kann vorab begrenzte Varianten vergleichen und auffällige Fehlschläge zur Prüfung vorschlagen. Jede Variante und jeder Versuch bleibt nachvollziehbar. Test- und Auswertungszeiträume vorher trennen; ein zurückgehaltener Zeitraum wird nicht fortlaufend zur Optimierung verwendet. Bei einem neuen Prüfzyklus neue, unberührte Daten vorsehen.

## Betrieb unter Proxmox

Für den Start passt ein Linux-LXC mit Python-Umgebung und systemd-Dienst/Timer. Die vorhandenen Windows-Start-/Stopskripte bleiben für die lokale Entwicklung; im Container übernimmt der Dienst Neustart und Bootstart. Keine zusätzliche Docker-Ebene ist dafür nötig. Falls stattdessen Docker gewünscht ist, die VM-/Containerentscheidung mit dem bestehenden Proxmox-Aufbau abgleichen; die Proxmox-Dokumentation beschreibt die Isolationseigenschaften und VM-Optionen.

- Konfigurierbares Datenverzeichnis statt Schreibzugriff auf das Quellverzeichnis. Datasets, Datenbank und Berichte über Neustarts erhalten und sichern. Datenbank-Backups konsistent erstellen; Wiederherstellung testen.
- Zugangsdaten aus Umgebungsvariablen oder eingehängter Secret-Datei. Beides ist im Alpaca-Adapter bereits grundsätzlich vorgesehen; der Windows-Desktop-Pfad wird im Container nicht benutzt.
- Betriebsbereitschaft von bloßer Prozesserreichbarkeit trennen: letzter erfolgreicher Import/Scan, Aktualität, Datenwarnungen, laufender Job und Fehlergrund anzeigen. Logs mit Job-/Instrument-ID, ohne Schlüssel.
- UI und Steuerzugriff nur passend zum vorhandenen internen Netzwerk öffnen und authentifizieren. Die heutige Loopback-Bindung würde einen Zugriff aus einem anderen Container zunächst verhindern; sie wird nicht stillschweigend gelockert.
- Eine kleine JSON-Steuerung und Datenübertragung reichen zwischen Hermes und Tori; die lokale LLM-Inferenz muss nicht im Tori-Container laufen. Ressourcen erst nach Batch-Messungen festlegen.

## Abnahme vor selbstständigen Läufen

1. Ein kompletter Lauf funktioniert auf einem eingefrorenen Dataset ohne Browser, Netzwerk und Provider-Schlüssel.
2. Identische Dataset-, Code- und Konfigurationsversionen erzeugen identische fachliche Ereignisse und Ergebnisse; Lauf-ID und Erstellzeit dürfen abweichen. Ein Manifest erfasst zusätzlich Universe-, Kalender-, Ausführungsmodell- und gegebenenfalls Zufallsversion/Seed.
3. Extrem veränderte Zukunftskerzen ändern keine bereits früher getroffene Entscheidung. Das auch für 1D/4h-Zusammenführung, Bestätigung, Retest und Stopnachziehen testen.
4. Historische Engine-Präfixe und der Chartdienst liefern dieselben Quellanker und Quellsignale; eine MTF-Chartprojektion ist kein Referenzsignal.
5. Signalarchiv und ursprüngliche Linien bleiben beim Weiterlaufen unverändert. Auch nach Verschieben des Datenfensters bleibt die Projektion auf der Quellachse gleich.
6. Abbruch/Neustart und doppelte Auftragszustellung liefern dasselbe Ergebnis wie ein unterbrechungsfreier Lauf, ohne doppelte Ausführungen.
7. Sommerzeit, verkürzte Sitzungen, leere Feed-Abschnitte, Stale-Cache, Splits, verzögerte Freigabe, Gaps und mehrdeutige OHLC-Abläufe haben explizite Tests.
8. Cash/Risikolimits gelten auch bei mehreren zeitgleichen Kandidaten. Jede Ergebniszahl lässt sich auf konkrete simulierte Ausführungen zurückführen.

Vorhandene Tests zu Geometrie, Stichtagsgrenzen, Replay und Fixierung dienen als Ausgangspunkt; sie belegen noch keine vollständige Strategie- oder Containerabnahme.

## Empfohlene Reihenfolge

1. Gemeinsame Modelle, explizite Konfiguration und Analysedienst aus dem HTTP-Handler lösen; Chartverhalten beibehalten und vergleichen.
2. Unveränderliche Datasets sowie CLI-Analyse für genau eine Aktie hinzufügen.
3. Replay-Engine, Signaljournal, Setup-Fixierung und die vier Strategiezweige; zuvor fehlende Ausstiegs- und Ausführungsregeln festlegen.
4. Einzelaktien-Backtest mit Bericht und Sprung zu seinen Ereignissen im vorhandenen Chart.
5. Linux-Dienst, dauerhafte Jobs, Neustart-/Offlineprüfungen und Hermes-Werkzeug anbinden.
6. Batch-/Portfolioläufe und Scanner ausbauen; EODHD nach eigenständiger Prüfung des Datenvertrags ergänzen.

## Primärquellen für die Architekturannahmen

- [Alpaca Historical Bars](https://docs.alpaca.markets/us/reference/stockbars): Zeiträume, Seitennavigation, Feed, Kursanpassung und Bedeutung der Symbolzuordnung `asof`.
- [Alpaca Market Data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq): Aggregation, Bar-Zeitstempel und Symboländerungen.
- [SQLite: Appropriate Uses](https://sqlite.org/whentouse.html): eingebetteter Serverbetrieb, begrenzte Schreibparallelität und Grenzen gemeinsamer Netzwerkdateien.
- [Proxmox: Container Toolkit, offizielle Dokumentationsquellen](https://github.com/proxmox/pve-docs/blob/master/pct.adoc): LXC, gemeinsame Kernelbasis und Optionen für Anwendungen/VM-Isolation. Die konkret installierte Proxmox-Version wurde hier nicht geprüft.
