# Prospektive Beobachtung mit unveränderten Regeln

Stand 22.10.2026. Beobachtung und manuelle Sichtprüfung sind lokale Funktionen;
keine Brokerorders und keine automatisch als profitabel bewertete Strategie.

## Vor Beginn festgelegt

- Zwei getrennte Geometrien: `hull_exact` und `swing_zone`, bestehende unveränderte
  Entry-Engine, Kontakt-/Reaktionsregeln, normalisierte geschlossene 4h-Quellen.
- Für jeden neuen Retest zwei bestehende Exits: feste anfängliche Safety und
  Gewinnschutz ab netto +1R mit 2ATR Abstand. Maximal zehn XNYS-Sitzungen bleibt
  die Forschungsgrenze. Keine Gewinnziele oder Grenzwerte nachjustieren.
- Die bisherige feste Liste von 25 US-Aktien, IEX und splitbereinigte Kurse.
  Änderungen an Aktienauswahl oder Regeln erfordern eine neue Registrierung.
- Beginn wird vor neuen Beobachtungen mit Uhrzeit/Codehash gespeichert. Neue
  Registrierung lässt sich nicht rückdatieren. Alte Signale mit späterem Open
  werden nicht als neue prospektive Entries gezählt. Erstimporte dienen dem
  Vorlauf; dieser wird nicht als neue Erfolgsstichprobe ausgegeben.
- Frühe Phasen Annäherung/Ausbruch/Rücklauf/Retest/Grün-Reaktion sind Hinweise zur
  Sichtprüfung. Nur die separate Retest-Ausführung erzeugt einen Modellpfad;
  ein Kandidat ist kein ausgeführter Entry. Fehlende Ausführungen bleiben im
  Watch-Zustand dokumentiert. Zwei Kontakte bleiben Beobachtung, kein Gütesiegel.
- Manuelle Urteile beeinflussen keine Berechnung. Auf den bisherigen Juli–Oktober-
  Ergebnissen werden keine neuen Parameter ausgewählt. Dieser alte Test ist
  verbraucht; neue Ergebnisse bleiben als eigener Lauf getrennt.

## Einrichtung und laufender Datenabruf

Aus dem Anwendungsordner. `TORI_DATA_DIR` bleibt der vorhandene Datenpfad,
im Container `/var/lib/tori`. Keys werden wie bisher serverseitig gelesen;
keine Zugangsdaten in CLI-Argumente oder Repository schreiben.

```text
python tools/forward_watch.py init
python tools/forward_watch.py run --id RUN_ID
python tools/forward_watch.py status
python tools/forward_watch.py stop --id RUN_ID
```

`init` registriert die feste Standardliste und den aktuellen Start, ruft noch
keine Kurse ab. Nur ein aktivierter Lauf ist erlaubt. `run` hält eine exklusive
OS-Sperre und wiederholt alle 15 Minuten; `run --once` macht einen Durchlauf.
`stop` beendet nach dem laufenden Import/Rechenschritt. Ein abgestürzter Prozess
kann mit derselben ID und unveränderter Engine fortgesetzt werden. Ein anderer
Lauf oder veränderter Code darf keine alten Zustände übernehmen.

Der erste Import lädt pro Aktie eine konsistente normalisierte 910-Tage-Historie
als neue Generation. Dadurch werden alte Forschungsarchive nicht umgeschrieben
und Splitbereinigungen nicht aus unterschiedlichen Datenständen gemischt. Dieser
einmalige Vorlauf kann länger dauern. Anschließend nur ein überlappendes, regulär
30 Tage langes 5m-Fenster aktualisieren, bei längerer Pause entsprechend mehr.
Cache, bestehende Providerpagination, Timeout, Retry und ein konservatives
40-Requests/Minute-Budget des Beobachterprozesses bleiben wirksam.

Die letzten 15 Minuten werden wie bisher ausgeschlossen. Gibt es seit dem letzten
Check keine neue erwartete reguläre 5m-Kerze, findet kein erneuter Providerabruf
statt, etwa über Nacht oder am Wochenende. Neue Entries brauchen weiterhin einen
bestätigten 4h-Schluss; der abschließende Tagesbucket kann kürzer als vier Stunden
sein. Stops werden anhand der verfügbaren 5m-Pfade modelliert. Das ist eine
verzögerte Beobachtung und kein live ausführender Handelsdienst.

Live-Abnahme der Einrichtung: Vor dem ersten prospektiven Fall wurde ein
Datenübergang nachgeschärft. Eine vom Provider entfernte, **bislang unbeobachtete**
Kerze darf nicht aus einer älteren Bootstrapdatei erhalten bleiben und damit ein
Loch verdecken. Die noch fallfreie Einrichtung wurde beendet und mit neuer
Enginekennung/Startzeit neu registriert. 23 bereits konsistent importierte
unveränderliche Datasets wurden ausdrücklich wiederverwendet, sämtliche
Modellzustände neu gerechnet. Keine alten Zustände unter verändertem Code
fortgesetzt, keine Entry-/Exitparameter geändert und keine Erfolgsfälle ausgewählt.

Ein fehlender letzter erwarteter IEX-Bar, API-Ausfall oder Fehler wird angezeigt
und später erneut geprüft. Änderungen oder Löschungen im bekannten Kurspräfix
sperren die betroffene Aktie; keine stillen Korrekturen alter Signale, kein
automatisches Rebasieren. Neue konsistente Generation erst ausdrücklich anlegen.
Historische IEX-Lücken können weiter bestehen; keine erfundenen Kerzen. Bekannte
Vorgeschichtsqualität und unbekannte Modellpfade bleiben getrennt ausgewiesen.

## Oberfläche und manuelle Prüfung

Menü **Beobachtung**, Route `/watch`. Zeigt Betriebsphase, Lebenszeichen, Fortschritt,
Fehler und gespeicherte Datenstände. Statusabfragen lösen keine Providerimporte aus.
Kandidaten nach Geometrie/Phase filtern. Seiten nutzen eine feste obere Sequenz,
damit neue Fälle während des Blätterns keine Zeilen überspringen lassen.

Ein Fall öffnet zunächst nur bis zur damaligen Meldung abgeschlossene 4h-Kerzen.
Rot/Orange ist die ursprüngliche Aktionslinie, Grün die **damals** verfügbare
Safety; Auswahl und Anker werden unmittelbar beim Ereignis gespeichert. Die
Linien bleiben auf Handelskerzenbasis gerade. Kein Rekonstruieren anhand später
bekannt gewordener grüner Linien. Der vorhandene manuelle Chart mit Ray-/Messtool
bleibt über einen Link erreichbar und startet weiterhin ohne Tori-Analyse.

„Späteren Verlauf … einblenden“ öffnet erst ausdrücklich den späteren Datenstand
und zugehörige Retest-Modellabschlüsse. Diese Öffnung wird gespeichert. Ein danach
abgegebenes Urteil bleibt als bereits mit Verlauf betrachtet gekennzeichnet,
auch nach Zurückschalten oder Neuladen. Das ist keine vollständige Verblindung:
andere Ansichten, bereits bekannte Aktienverläufe oder externe Charts können
Vorwissen vermitteln. Keine menschlichen Urteile simulieren oder als vorhanden
ausgeben, solange der Nutzer keine eingetragen hat.

Urteile: interessant, unklar, ablehnen und Notiz. Jede Änderung wird historisiert.
Fälle sind zeitgestempelte Meldungen, keine stets aktuellen Kaufempfehlungen;
ein älterer Kandidat kann inzwischen ungültig oder beendet sein. Die spätere
Sicht zeigt den Modellverlauf, nicht eine neue Empfehlung.

## Speicherung, Hermes und Betrieb

`TORI_DATA_DIR/forward/watch.sqlite3`, eigene Schema-Version 1. Enthält registrierte
Läufe, Importstände, beide Modellzustände, unveränderliche Fälle, Ereignisjournal,
Verlaufssichten und manuelle Urteile. Checkpoint, Fälle und Ereignisse werden je
Aktie/Modell in einer SQLite-Transaktion gespeichert. Wiederholungen sind per
stabilen IDs dedupliziert. Providerdaten bleiben unveränderliche Dateien unter
`datasets/`. Browserzeichnungen bleiben getrennt im bisherigen Browserspeicher.

Hermes kann lesen:

```text
python tools/forward_watch.py events --id RUN_ID --after 0 --limit 100
```

Antwort enthält feste obere Sequenz `through`, `after` und Ereignis-IDs. Der
HTTP-Weg `/api/watch/events?after=...&through=...&limit=...` ermöglicht ebenfalls
stabile Seiten. Ein späterer Sender muss einen eigenen Bestätigungsstand führen;
das gespeicherte Journal ist dauerhaft lesbar. **Kein Nachrichtensender** vorhanden.
HTTP verwendet weiterhin bestehende Authentifizierung, Host-/Originprüfung und
Payloadgrenzen. Nur explizite Fallurteile sind im neuen Bereich schreibbar;
Registrierung/Start/Stop erfolgen am lokalen CLI, keine öffentlichen Importknöpfe.

Der bestehende Backup-/Restore-Weg sichert die Beobachtungs-SQLite konsistent mit
und prüft ihre referenzierten Datasets. Bereinigung bleibt Vorschau und schützt
Beobachtungsreferenzen. Rücksicherung nur in neues Verzeichnis; startet keinen
Beobachter. Für Updates laufenden Dienst stoppen/sichern, gleichen Datenpfad und
Secrets erhalten. Die spätere Containerinstallation benötigt einen eigenen
Prozess/Service für `tools/forward_watch.py run`; der Webserver startet ihn nicht
heimlich. Neu registrieren, wenn die eingefrorene Engine geändert wurde.

Speichergrenze des jetzigen Prototyps: Jede geänderte immutable Dataset-Version
enthält die vollständige Historie. Bei fortlaufenden 15-Minuten-Updates kann der
Bestand deutlich wachsen. Vor längerem oder größerem Containerbetrieb daher
Speicherbudget/Retention messen und gegebenenfalls eine gemeinsame inkrementelle
Kursablage ergänzen. Referenzierte Fall-/Beobachtungsdaten nicht automatisch
entfernen. Die vorhandene Speicheranzeige weist `forward` separat aus; dieses
Update ist keine Langlaufabnahme des Speicherbedarfs eines großen Universums.

`deploy/tori-watch.service` liegt als **uninstallierte Vorlage** bei. Für einen
späteren Containerlauf dort eine eigene Registrierung vornehmen und deren ID als
`TORI_WATCH_RUN_ID` in die bestehende geschützte Environment-Datei aufnehmen.
Lokale Lauf-ID/DB nicht unbemerkt mit einem Containerlauf vermischen. Systemd-
Vorlage ist hier nicht unter Linux getestet oder auf Proxmox installiert.

## Prüfung und Grenzen

Gezielte Gegenbeispiele für beide Geometrien, unveränderte Entryberechnung trotz
Ereignissnapshot, Zukunftsimmunität, Wiederaufnahme, späteren Open alter Signale,
bekannte Kursrevisionen/-löschungen, veraltete Providerantworten, atomaren Speicher,
stabile Seiten und Ereignisse, manuelle Verlaufssicht, unveränderliche Urteile,
Backup/Restore und API-Schutz. Künstliche Testdaten sind ausschließlich Technik-
Fixtures. Echte prospektive Fallzahlen entstehen erst nach Registrierung und
neuen Marktdaten. Eine aktuell leere Kandidatenliste ist ein gültiges Ergebnis.

Diese Stufe beweist technische Beobachtung. Sie ersetzt keine Strategievalidierung,
passenden Zufallsentry-Vergleich, europäische Datenversorgung oder echten Broker-
Ausführungstest. Überlappende Modellpositionen sind kein frei verfügbares Depot.
Kein automatischer Handel, keine Parameteranpassung und kein Proxmox-Rollout.
