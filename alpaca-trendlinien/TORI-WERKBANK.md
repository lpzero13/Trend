# Werkbank für Hermes: Sichtprüfung und erklärter Kandidatenscanner

Lokale Erweiterung vom 22.10.2026. [Vorabplan](TORI-WERKBANK-PLAN.md), [Daten-/Ergebnisvergleich](TORI-WERKBANK-ERGEBNISSE.md). Getrennt vom bestehenden Chartmodell und vom bereits registrierten `forward_watch`-Beobachter. Kein neuer automatischer Dienst, keine Orders oder Nachrichten.

## Was implementiert ist

- Menü **Sichtprüfung**, `/pruefung`: geschlossene Original-Quellkerzen in 4h oder 1D, Hell/Dunkel, eigene rote/grüne Rays, horizontale Widerstände, zusätzliche Kontaktmarkierungen, Linie löschen und Rückgängig. Speichern auf dem Server, keine Vermischung mit persönlichen Browserzeichnungen des Hauptcharts.
- Engine-Linien bleiben bis zur ausdrücklich angeforderten Offenlegung verborgen. Zuvor muss eine eigene Beurteilung mit Begründung gespeichert werden. Danach bleiben die ursprünglichen unbeeinflussten Linien erhalten; spätere Änderungen werden historisiert und als beeinflusst gekennzeichnet. Diese Seite liefert auch nach der Offenlegung keine zukünftigen Kurse oder Ergebnisse.
- Geometrischer Vergleich zum damaligen Schluss und als mathematische Projektion 20 Quellkerzen weiter, geteilt durch die damalige ATR. Die Projektion kennt keine zukünftigen Kurse. Kontaktmarkierungen sind menschliche Annotationen und keine automatisch bestätigten unabhängigen Reaktionen. Dochtüberschreitungen werden getrennt vor/am letzten Balken gezeigt. Bekanntes Vorwissen des Menschen lässt sich technisch nicht ausschließen.
- Separate `ExplainedReplay` erweitert den unveränderten `CompleteReplay` ausschließlich um erklärende Beobachtungsmerkmale. Drei Kontakte plus sieben Tage Alter der Aktions-/Safety-Linie; Ausbruch, Retest und Grün-Abpraller getrennt. Momentum, Safety-Distanz, Tages-/Wochen-/Monatskontext, Raum und Ereignisse sind Hinweise, keine weiteren harten Ausschlüsse dieser Gruppe.
- Zusätzlich `approaching` als Beobachtungsstadium: Schluss höchstens 0,75 damalige ATR unter einer aktiven roten Linie. Dies ist eine Versuchskonvention für Nähe, kein validierter Einstieg. Kontaktzahl hier konservativ vor der Aktualisierung der gerade geschlossenen Kerze. `currentNear` liefert die Merkmale am letzten bekannten Quellschluss; es kann mehrere geometrisch ähnliche Linien enthalten. Noch keine automatische universumsweite Priorisierung oder Nachrichtenauswahl.
- Unveränderliche ursprüngliche Anker und aktuelle Schlussmerkmale. Keine späteren Kauf-/Verkaufskurse oder Resultate in den Scannerfakten. Ein Signal am Schluss ist von späterer Ausführbarkeit zu unterscheiden.
- Dauerhaftes Journal mit stabiler Kennung aus Feed/Bereinigung/Aktie/Intervall/Geometrie/Ankerfamilie/Phase; dieselbe Phase derselben Linienkombination wird einmal registriert. Ein neues Ankerpaar ist eine andere Hypothese, kein automatisch unabhängiger Trade.
- Checkpoint schützt Engine, Provider/Feed/Bereinigung, Quellpräfix, Kalenderpräfix und registrierten Beginn. Historische Wiederholung muss ausdrücklich `historical` heißen. Prospektiver Beginn ist nicht rückdatierbar. Bei gleicher Datenlage keine neuen Journalfakten. Änderungen erfordern eine neue Scannerkennung, kein stilles Zurücksetzen.
- Historischer SIP-Import mit bestehendem Alpaca-Zugang; Feed bleibt separat gespeichert. Dieselbe strenge 5m-RTH-Normalisierung wie IEX, keine erfundenen Kerzen. [Alpaca erklärt historische SIP-Abfragen ohne Echtzeitabo bei mindestens 15 Minuten altem Ende](https://docs.alpaca.markets/us/docs/market-data-faq). Dies garantiert keine aktuelle/latest-SIP-Berechtigung.
- Wiederverwendung des vorhandenen Cash-/Risikoledgers für eingefrorene vollständige Studienpfade. Unbekannte gehaltene Pfade stoppen die Rechnung, statt nur vollständige Gewinner zu behalten. Kein neues Depotmodell im Chart. Kapitalversuch auf splitbereinigten Modellkursen, ohne Dividendenzahlungen oder historisches Corporate-Action-Depotjournal; keine Rekonstruktion realer Brokerabrechnungen.

## Bedienung der Sichtprüfung

Paket und Fall wählen. Chart verschieben/zoomen; „Ansicht zurücksetzen“ passt bekannte Kerzen ein. Ray oder Widerstand auswählen, zwei Anker von links nach rechts anklicken. Für Zusatzkontakte die eigene Linie im Auswahlfeld wählen und „Kontakt markieren“ aktivieren. Erneuter Klick auf dieselbe Kerze entfernt deren Markierung. „Zeichnen beenden“ verwirft nur den noch nicht abgeschlossenen Anker. „Linie löschen“ entfernt die gewählte Linie, „Rückgängig“ stellt letzte Zeichnungsänderungen wieder her.

Urteil und Begründung speichern. Erst dann „Engine ausdrücklich aufdecken“. Automatische Linien erscheinen gestrichelt, eigene durchgezogen. Linienrollen sind zusätzlich im Auswahlfeld bezeichnet. Ungespeicherte Änderungen verhindern einen stillen Fallwechsel. Der vorhandene Hauptchart startet weiterhin ohne Tori-Analyse.

Die ersten 102 vorbereiteten Fälle bestehen aus 82 bisherigen, nach Enginefällen ausgewählten Diagnosepräfixen und 20 festen Zufallspräfixen ohne Auswahl anhand späterer Rendite. Keine repräsentative Populationstrefferquote daraus ableiten. **Es wurden keine menschlichen Bewertungen erzeugt.** Ein sinnvolles nächstes Ergebnis ist die tatsächliche Übereinstimmung deiner eigenen Linien mit den automatischen Vorschlägen.

## Datenhaltung und Betrieb

Immer denselben `TORI_DATA_DIR` verwenden: im Container `/var/lib/tori`, lokal der bereits konfigurierte Datenordner. Fälle, Urteile, Revisionshistorie, Scannercheckpoints und Journalfakten sind namensräumlich getrennte JSON-Dokumente in der bestehenden `research/jobs.sqlite3`-Tabelle `settings` (`wb:*`). Keine zusätzliche Datenbank oder Runtime-Abhängigkeit. Datasetreferenzen bleiben für Aufräumvorschau geschützt. Konsistentes vorhandenes Backup/Restore enthält diese Dokumente und zugehörige immutable Datasets; das wurde mit einem echten isolierten Restore getestet.

Die CLI registriert Fälle aus lokalen Datensätzen. HTTP kann keine beliebigen Dateipfade einlesen, Downloads starten oder Scanner konfigurieren. Authentifizierung, Host- und Originprüfung gelten unverändert. Dataset-, Backup-, Log- und Secretdateien werden nicht als statische Dateien ausgeliefert.

Neue Module ändern nicht die Regeln alter Forschungsaufträge. Die zwei laufenden Welten bleiben ausdrücklich verschieden: `forward_watch` beobachtet die bisherigen beiden Modelle; `workbench_scan` ist ein neuer, separat registrierter expliziter Aufruf. Noch keine automatische Installation oder Kopplung an Hermes vorgenommen.

## Wiederholbare Befehle

Aus `alpaca-trendlinien/`, mit dem bestehenden Datenpfad und lokalen Providersecrets. Keine Secrets als Kommandozeilenargumente verwenden.

```sh
# Einmaliger historischer SIP-Vergleich, vorab festgelegte 60 Aktien.
python tools/workbench_import.py --root artifacts/tori-workbench-20261022-a
python tools/workbench_run.py --root artifacts/tori-workbench-20261022-a --iex artifacts/tori-complete-20261022-b --output TORI-WERKBANK-ERGEBNISSE.md

# Wiederholbare Fallvorbereitung aus eingefrorenen Studienpräfixen.
python tools/workbench_prepare.py --root artifacts/tori-complete-20261022-b

# Historischer Scan; DATASET_ID aus einem unveränderlichen gültigen Import.
python tools/workbench_scan.py --dataset DATASET_ID --stream eigene-historische-pruefung --timeframe 4h --cutoff 1792612800 --from-at 1627517400 --mode historical

# Dauerhaftes Journal nach verlorener CLI-Antwort, danach nextCursor verwenden.
python tools/workbench_scan.py --stream eigene-historische-pruefung --journal --limit 100
```

Wiederholte Imports nutzen vorhandenen Cache; Studien/Audits laufen nach dem Pinning offline. Kontrakt-/Codeänderungen sperren alte Verzeichnisse, statt deren Resultate umzuschreiben. `workbench_run --wait-import` wartet begrenzt auf einen separat laufenden vollständigen Import. Marktdaten und Artefakte sind privat und gehören nicht ins Git-Repository. Dieses datierte Werkzeug ist kein allgemeiner Provider-Downloader mit beliebigen historischen Parametern.

`workbench_run` führt auch `tools/workbench_verify_scanner.py` aus: für jede Aktie und beide Quellintervalle exakt dieselben ursprünglichen Entries, Ablehnungen, offenen Ausführungen und Trichterwerte gegen die eingefrorenen Studienblöcke prüfen. Kandidatenmerkmale werden vorher ohne Ergebniswissen berechnet und separat unter `candidates/` exportiert. Dieser Vergleich prüft die technische Trennung, keine Profitabilität. Der Kurs-/Stopp-Auditor rekonstruiert danach Kontakte, Fills und Ergebnisse unabhängig vom Exit-Evaluator.

Für **neue prospektive** Scannerkennung `--mode prospective` (Standard) verwenden und `--from-at` weglassen. Beginn wird auf die tatsächliche Registrierung gesetzt, nicht auf den historischen Datensatzanfang. Der erste alte Datenstand liefert damit keine angeblich neu beobachteten historischen Signale. Später dasselbe Symbol/Intervall/Feed mit erweitertem unverändertem Präfix und größerem `--cutoff` aufrufen. `sourceAgeSeconds` misst Abstand vom angeforderten Stichtag, `sourceAgeAtRunSeconds` zusätzlich das echte Alter beim Aufruf; `sourceAfterRegistration` zeigt, ob überhaupt ein Quellschluss seit Anmeldung vorliegt. Handelspausen bei der Interpretation berücksichtigen. `currentNear` ist eine Stichtagsansicht und keine automatische aktuelle Handelsaufforderung.

Ein gespeicherter Scanner ist nicht selbst ein Zeitplan. Zukünftig Hermes passende abgeschlossene Quellkerzen prüfen lassen, danach Journal abrufen und anhand Cursor/ID deduplizieren. Bei Regel-/Datenrevision neue Generation registrieren. Historische Varianten nie im laufenden unveränderten Beobachter unter derselben Kennung fortsetzen.

## Lesende API und Schreibgrenzen

- `GET /api/workbench/packs`
- `GET /api/workbench/packs/PACK?offset=0&limit=50` (maximal 100)
- `GET /api/workbench/packs/PACK/CASE` (nur bekannte Quellkerzen, Engine vor Offenlegung nicht enthalten)
- `GET /api/workbench/packs/PACK/compare` (geometrische Ergebnisse nur für ausdrücklich aufgedeckte Fälle)
- `POST /api/workbench/packs/PACK/CASE/label` mit `{revision, verdict, note, rays}`; Optimistic-Locking, Konflikt 409.
- `POST /api/workbench/packs/PACK/CASE/reveal` mit `{revision}`; ohne gespeichertes Urteil 409.
- `GET /api/workbench/scans` (maximal 200 Checkpoints)
- `GET /api/workbench/scans/STREAM/facts?limit=100&cursor=...` (maximal 500); append-fester Snapshot pro Seitenfolge, Cursor an Stream gebunden.

Journalseiten bleiben auch während weiterer Aufrufe stabil. Neue Fakten erscheinen in einer neu begonnenen Seitenfolge. Keine Broker-/Benachrichtigungsendpunkte.

## Ereigniskalender und noch offene Arbeit

Optional `workbench_scan --events datei.json`. `workbench_events.py` validiert ausschließlich explizite Daten: `{coverage: [{symbol, knownAt, fromAt, throughAt}], events: [{symbol, knownAt, at, kind}]}`. Zeiten als positive UTC-Unixsekunden; Ereignisse `earnings` oder `dividend_announcement`. `knownAt` muss ein belegter damaliger Bekanntheitszeitpunkt sein. Der Validator kann die Wahrheit einer gelieferten Veröffentlichung nicht beweisen. Abdeckung muss den Signalzeitpunkt und die nächsten drei Handelssitzungen einschließen, sonst `events: null`. Nachträglich bekannte Termine entlasten keinen früheren Einstieg.

**Noch nicht vorhanden:** echte historische Unternehmensereignisse mit nachgewiesener damaliger Veröffentlichung, EODHD-Umstellung, menschliche Linienbeurteilungen, deduplizierte Meldeauswahl, neuer Dauerdienst für diese Regeln, unabhängige neue Vorwärtsbeobachtung dieser Variante, bestätigte Profitabilität. Bekannte historische Zeiträume sind kein neuer unabhängiger Holdout. Weitere Verbesserungen zuerst aus Datenqualität und tatsächlicher menschlicher Übereinstimmung ableiten, nicht nachträglich aus den größten Gewinnern.
