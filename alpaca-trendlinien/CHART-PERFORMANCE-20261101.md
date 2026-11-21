# Kursfenster und bedarfsgerechte Tori-Analyse

Stand: 01.11.2026. Lokale Entwicklung auf `codex/instant-replay-and-ray-anchors`;
noch nicht veröffentlicht oder im Container installiert. Die Prüfung erfolgt
auf Benutzerwunsch intern, ohne Browserbedienung.

## Verhalten

Die normale Chartansicht und der Zufalls-Replay laden für die ausgewählte Aktie
ein getrenntes Kursfenster. Andere Aktien werden dabei nicht importiert. Ein
Datumssprung oder Kerzenschritt innerhalb dieses Fensters überträgt anschließend
nur einen kompakten Analysezustand, statt sämtliche Kursreihen erneut zu senden.

- Native Alpaca-Charts behalten IEX/raw und den bisherigen Provideradapter.
  Angefordert werden 1.098 Kalendertage: bei aktuellem Start etwa zwei Jahre
  Untersuchung plus ein Jahr Vorlauf; bei historischem Start bis zu ein Jahr
  nach dem ausgewählten Zeitpunkt und etwa zwei Jahre davor. Grenzen der
  tatsächlichen Providerdaten gelten weiterhin. Es werden keine Kerzen erfunden.
- Archivcharts und Zufallsfälle verwenden ihr bereits ausgewähltes, unveränderliches
  Dataset. Die vorhandene Chart-Historie wird einmal übertragen; bei langen Archiven
  können das mehr als zwei Jahre sein. 5m-Ausführungskurse werden nicht übertragen.
- Die Oberfläche startet weiterhin ohne automatische Analyse. Das Einschalten
  berechnet nur den gewünschten Zeitpunkt, nicht alle vergangenen Jahre. Das
  vorbereitende Nachbarfenster umfasst weiterhin höchstens acht Schritte pro Richtung.
- Kerzenschritte werden aus den vorgeladenen tatsächlichen Schlusszeitpunkten
  bestimmt, ohne zusätzliche `/api/step`-Anfrage oder Providerimport pro Schritt.
  Am Fensterrand ist ein neuer Datumssprung oder eine Aktualisierung erforderlich.
- Bereits berechnete Ansichten werden wiederverwendet. Bei fixierten Linien
  fordern neue Schritte ausschließlich manuelle Kursansichten an; das Lösen
  berechnet die aktuelle Analyse und verwirft die nur für die Fixierung erzeugten
  Ansichten. Eigene Rays/Messungen und gespeicherte Stände bleiben getrennt.
- Forschungsfall-, Entryindex- und explizite Forschungs-Overlays behalten ihre
  bisherigen speziellen Routen. Diese Optimierung stellt keine Forschungsregeln um.

## Berechnungs- und Zukunftsgrenze

`chart_replay.py` hält höchstens zwei Sitzungen mit jeweils maximal 100.000
Quellkerzen. Pro Sitzung maximal 128 kompakte Antworten und 24 MiB serialisierte
Antwortdaten; Python-Objekt-, Kurs-, Checkpoint- und sonstiger Serviceaufwand kommt
hinzu. Keine neue Datenbank, Migration oder Abhängigkeit.

Das separate Transportobjekt `window` darf spätere Kurse enthalten. Jede sichtbare
Ansicht wird dagegen in **jedem Quellintervall nach `bar.end <= analysisCutoff`**
beschnitten. JavaScript prüft die übermittelten Präfixlängen erneut. Spätere Kurse
gelangen weder in die sichtbaren anderen Intervalle noch in eine gespeicherte Fixierung.
Gleitende Durchschnitte werden einmal als Transportreihe bereitgestellt, ihre
angezeigten Präfixe bleiben ebenfalls auf den gewählten Zeitpunkt begrenzt.
Zeichenachsen bestehen aus bekannten Kerzenpositionen und den bisherigen reinen
Kalenderpositionen; künftige beobachtete Kerzen bestimmen ihre historischen Formen nicht.

`replay_fan.py` verwendet die gemeinsamen `FanEngine`/`MasterEngine`, ATR-, Pivot-,
Kontakt- und Linienberechnungen. Er behält nur den bereits aufgebauten Eingabezustand
und höchstens zwölf nahe Checkpoints; vor jeder Geometrieausgabe werden die internen
Liniencaches geleert. Damit entspricht der Snapshot einer frischen Berechnung auf
dem gleichen Präfix, einschließlich Lückenresets. Keine zukünftigen Linien werden
als früher bekannt behandelt.

`replay_legacy.py` verwendet die gemeinsamen Hull-/Auswahl-/Bruchfunktionen und hält
höchstens 96 exakte Linienpaare je Sitzung. Das ursprüngliche rollende Ereignisbudget
wird je Abfrage erneut angewandt; ältere Ereignisse werden nicht unbegrenzt mitgeführt.
Die vollständigen Ausgaben beider Wege werden gegen die bisherigen kanonischen
Berechnungen geprüft. MTF-Projektionen bleiben Darstellungen und erzeugen keine Entries.

Der native Vorlauf wird gegenüber dem früheren 450-Tage-Einzelabruf größer. Dadurch
können insbesondere ATR-Startwerte und einzelne Master-Ergebnisse anders ausfallen.
Vergleichsgleichheit gilt für **denselben Datenbestand und denselben Stichtag**;
ein länger geladener Datenbestand ist nicht derselbe Eingang. Bestehende automatische
Forschungsengines und deren Datensatzbindungen werden nicht umgestellt.

## Betrieb und Schnittstellen

- `GET /api/replay/open`: ausgewähltes natives Symbol, Dataset oder bestehender
  Zufallsfall, Intervall, Datum, Modell und optional Analyse. Antwort enthält ein
  Kursfenster und die separate kompakte Ansicht.
- `GET /api/replay/view`: Sitzung, Datum, Intervall, Modell und Analyse ein/aus.
  Überträgt keine OHLC-Kopien; Quellachsen und SMA-Präfixe werden aus dem geladenen
  Fenster rekonstruiert. Auch der bereits bekannte Teil der Zeichenachse wird
  nicht nochmals übertragen.
- `POST /api/snapshots` mit `replay`: speichert ausdrücklich den angezeigten
  Zeitpunkt über den bestehenden Snapshotvertrag. Erst dabei wird der vollständige
  analysierte Stand registriert und gespeichert, statt bei jedem Hintergrundschritt.
- Host-, Origin-, Authentifizierungs-, Größen- und Gzip-Grenzen bleiben erhalten.
- Sitzungen sind flüchtig. Nach Serverneustart/Verdrängung antwortet die View mit
  410; der Client fordert ein vollständiges neues Kursfenster an und mischt keine
  Kursrevisionen. Ein fehlgeschlagener Refresh erhält die alte sichtbare Ansicht.
- Datasetdateistände werden weiterhin vor jedem Zugriff geprüft; die bestehende
  volle Prüfsummenprüfung wird spätestens nach zehn Minuten wiederholt. Änderungen
  oder beschädigte Dateien dürfen keinen alten Sitzungszustand weiterverwenden.
- Native Bestände mit verworfenen Providerzeilen sowie übergroße Fenster bleiben
  auf dem strengeren bisherigen Einzelabrufpfad. Keine stillschweigende Umstellung
  zwischen IEX/raw und SIP/split.
- Denselben `TORI_DATA_DIR` verwenden. Sammler bleibt pausiert, kein allgemeiner
  Worker, keine Brokerorders, Benachrichtigungen oder Containerinstallation gestartet.

## Reproduzierbare interne Prüfung

Aus dem Anwendungsordner mit seinem bestehenden `TORI_DATA_DIR`:

```powershell
.venv/Scripts/python.exe tools/benchmark_chart_replay.py
```

Das Werkzeug verwendet AAPL, MSFT, AMZN, JPM und XOM aus bereits vorhandenen,
verifizierten Archiven; kein Providerabruf ist erlaubt. Es startet einen temporären
Loopback-HTTP-Server ohne Worker. Gemessen werden echte HTTP-Anfragen einschließlich
Gzip, Übertragung und JSON-Einlesen, keine Browserdarstellung oder GPU-Zeiten.

Je Aktie und Modell (Legacy/Master) werden drei Startbereiche in 2024, 2025 und 2026
geöffnet, jeweils acht neue 4h-Schritte vorwärts und acht besuchte Schritte zurück
ausgeführt und anschließend 1h, 1D und 1W untersucht. 780 kompakte Viewanfragen und
150 vollständige kanonische Vergleichsberechnungen. Verglichen werden Kerzen,
Quellmetadaten, sämtliche Linien/Ereignisse, SMA-Reihen, Fingerprints und Zeichenachsen.
Die Ergebnisdatei unter `artifacts/` enthält nur private Messwerte und wird nicht
mitveröffentlicht. Der Benchmark ist eine technische Prüfung, keine Handelsstudie.

Die gezielten Regressionen prüfen zusätzlich zukünftige Kursänderungen, Rücksprünge
über Checkpoints/Lücken, alle vier Linienmodelle, unveränderte Snapshotgrenzen,
Cachegrenzen, verzögerte Aktienantworten, Serverneustart, Refreshfehler und das
Umschalten zwischen manueller, dynamischer und fixierter Analyse. Tests benötigen
keine Providerzugangsdaten. CI führt auch `tests/test_replay_window.cjs` aus.

## Messwerte und Einordnung

Abschließender Lauf auf diesem Windows-Rechner, fünf echte SIP/split-Archive,
780 Viewanfragen und 150 exakte Vergleichsprüfungen ohne Abweichung:

| Vorgang | Legacy Mittel / P95 | Master Mittel / P95 |
|---|---:|---:|
| Neuer Datumssprung | 190 / 529 ms | 153 / 255 ms |
| Neue 4h-Kerze vorwärts | 103 / 171 ms | 83 / 148 ms |
| Besuchter 4h-Zustand zurück | 14 / 28 ms | 16 / 30 ms |
| Neue 1h-/1D-/1W-Ansichten | 79 / 193 ms | 87 / 140 ms |
| Bisherige vollständige Antwort, Vergleich | 622 / 802 ms | 1.046 / 1.265 ms |

Größter einzelner neuer 4h-Schritt: Legacy 316 ms, Master 182 ms.
Die kompletten Vergleichsantworten betreffen dieselben untersuchten Start-/Endstände,
aber keine paarweise identische Zeitmessung sämtlicher Zwischenschritte. Daraus folgt
keine garantierte Beschleunigungszahl für jeden Klick.

Erstladen einschließlich vollständiger Datasetprüfung und HTTP:

| Aktie | Erstladen | Komprimierter einmaliger Transport |
|---|---:|---:|
| AAPL, erster Aufruf im kalten Prozess | 7,276 s | 1,33 MiB |
| MSFT | 2,051 s | 1,37 MiB |
| AMZN | 2,124 s | 1,31 MiB |
| JPM | 2,052 s | 1,31 MiB |
| XOM | 1,992 s | 1,27 MiB |

Das sind im Mittel 3,10 Sekunden; nach dem ersten Aufruf im Mittel 2,05 Sekunden.
Die erste Aktie enthält auch die erstmalige Kalender-/Bibliotheksinitialisierung.
Die Bestände reichen überwiegend bis 2016 zurück und sind damit umfangreicher als
zwei Jahre. Kompakte Folgeantworten umfassen durchschnittlich 29 KiB (Legacy)
bzw. 32 KiB (Master) komprimiert. Rohmessungen:
`artifacts/replay-window-benchmark-final-20261101.json`; das Skript verweigert Providerabrufe.

Bewertung: Für den kerzenweisen Analyseablauf deutlich verbessert und als nächster
lokaler Stand sinnvoll. Die verbliebene Verzögerung liegt überwiegend im Erstladen
und in völlig neuen Analyse-/Kalenderständen. Erst danach wäre ein dauerhaft
versionierter Zustandsindex für sehr große Sprünge oder mehr als zwei gleichzeitig
aktive Aktien sinnvoll; nicht nötig, um diesen Schritt nutzbar zu machen.

Gesamtregression: 576 Python-Tests bestanden, ein bestehender Skip. Danach elf
Zufalls-Replaytests einschließlich der ergänzten Kursfenster-/Modell-/Intervallprobe
bestanden. Alle 104 JavaScript-Prüfungen bestanden; der echte Chartcontroller wird
dabei ohne Browser mit kontrollierten DOM-/Chart-Schnittstellen ausgeführt. Keine
visuelle Browserprüfung in diesem Auftrag. `git diff --check` ohne Inhaltsfehler.

Privater Prüfstand:
`artifacts/replay-window-full-python.log`, `artifacts/replay-window-random-tests.log`,
`artifacts/replay-window-full-js.log`.
Ein echtes erstmaliges Herunterladen fehlender Alpaca-Daten ist nicht Bestandteil
dieses Offline-Tests; dafür darf aus den lokalen Messwerten keine feste Dauer
versprochen werden. Auch tatsächlich sichtbare Browserzeiten bleiben separat zu messen.
