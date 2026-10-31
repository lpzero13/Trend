# Signaljournal für Replay und spätere Hermes-Beobachtung

Stand: 30.10.2026. Implementierte technische Vorbereitung, **kein installierter Scanner oder laufender Gewinnnachweis**. Webchart, persönliche Zeichnungen und bisheriger Forward-Beobachter bleiben erhalten. Dieses Journal protokolliert gezielt die unveränderte neue Backtest-Hypothese, ohne den bisherigen Beobachtervertrag zu ersetzen.

## Was implementiert ist

- Dieselbe kausale 4h-Master-/Pilotberechnung wie im untersuchten Ausbruch-Kandidaten, qualifizierte rote Linie, aktuelle Safety und ursprüngliche Liniengeometrie im Ereignis.
- Wahlweise genau eine nächste abgeschlossene 4h-Kerze oder Fortschritt bis zu einem expliziten Zeitpunkt. Bei mehreren Aktien wird der nächste gemeinsame Zeitfortschritt verarbeitet; gleichzeitige Schlussereignisse gehören zum selben Schritt.
- Festes Universum, Startdatum, 400-Tage-Vorlauf, Strategie- und Codebindung. Replay und prospektive Beobachtung sind getrennt gekennzeichnet. Ein historischer Start darf nicht nachträglich als prospektiv ausgegeben werden.
- Transaktionale SQLite-Checkpoints und einmalige Ereignisse. Abbruch vor Commit hinterlässt weder Teilereignisse noch einen vorgerückten Cursor. Wiederholung desselben Schlusses erzeugt kein Duplikat.
- Automatische Linien dürfen sich künftig verändern; bereits protokollierte Signalgeometrien bleiben erhalten. Ein Signal mit ungültiger aktueller Safety wird als abgelehnt protokolliert, nicht als handelbarer Einstieg dargestellt.
- Dataset-Wechsel nur bei unverändertem bereits beobachtetem 4h-Präfix und derselben Provenienz. Neue Kurse dürfen angehängt werden. Rückwirkende Kursänderungen werden ausdrücklich abgelehnt; ein neues Journal ist nötig.
- Kein Vorrücken über veraltete Eingaben: Alle beobachteten Aktien müssen den angeforderten Zeitpunkt abdecken. Für Kursdatenaktualisierung bleibt der bestehende Import zuständig; das Journal selbst erzeugt keine Providerabrufe.
- Begrenzte Ereignisseiten mit stabiler Sequenzobergrenze sowie Status mit Cursor, letztem beobachtetem Quellschluss und Alter des letzten Aufrufs.
- Speicherung unter `TORI_DATA_DIR/signal-journals/`. Referenzen werden bei der Aufräumvorschau erhalten. Das bestehende Backup/Restore nimmt konsistente SQLite-Snapshots einschließlich Dataset-Referenzen auf; neues Backupformat 3 liest auch die bisherigen Formate 1 und 2. SQLite-WAL-Dateien müssen nicht separat kopiert werden.

## Was ausdrücklich noch fehlt

Das Journal meldet **Signal-Kandidaten**, keine ausgeführten Trades. Nächster ausführbarer Kurs, Budget, gleichzeitig belegte Positionen, Stops und späteres Ergebnis müssen wie im Backtest gesondert bewertet werden. Ein Live-Dienst mit Zeitplanung, Provideraktualisierung, Fehlerüberwachung und späterer Ergebniszuordnung ist noch nicht eingerichtet. Benachrichtigungen, Brokerorders und Installation auf Proxmox sind nicht Teil dieser Umsetzung.

Der Heartbeat beschreibt den letzten Journalaufruf, keinen nachgewiesen laufenden Daemon. Es gibt keinen Hintergrundprozess, der ohne separaten Auftrag gestartet wird. Ein Enginewechsel erfordert ein neues Journal; bestehende Aufträge werden nicht unter geändertem Code fortgesetzt. Alte Journale bleiben les- und sicherbar.

## Bedienung ohne Weboberfläche

Alle Befehle aus `alpaca-trendlinien/` und mit **demselben `TORI_DATA_DIR` wie der Dienst** starten. Auf Proxmox ist das üblicherweise `/var/lib/tori`. Die symbolische Beispieldatei `datasets.json` ist ein privates Objekt wie `{"AAPL":"<64-stellige lokale Dataset-ID>"}`; keine Zugangsdaten.

```text
python tori.py journal-init --name replay-aapl --datasets datasets.json --start 2025-04-01T00:00:00-04:00 --mode replay
python tori.py journal-advance --name replay-aapl --step
python tori.py journal-advance --name replay-aapl --asof 2025-04-03T16:00:00-04:00
python tori.py journal-status --name replay-aapl --limit 100
python tori.py journal-status --name replay-aapl --after 100 --upper-seq 230 --limit 100
```

`--upper-seq` aus der ersten Antwort übernehmen, `--after` jeweils aus `nextAfter`. Damit ändern neue Ereignisse während des Blätterns den Umfang dieser Lesesitzung nicht.

Für eine spätere prospektive Einrichtung `--mode prospective` und einen Start **jetzt** verwenden. Historische Starts werden abgelehnt. Erst nach einer separat gesteuerten lokalen Datenaktualisierung das Journal vorwärts bewegen:

```text
python tori.py journal-advance --name neuer-prospektiver-versuch --datasets aktualisierte-dataset-ids.json --step
```

Das funktioniert nur bei unverändertem Universum und unveränderter bereits beobachteter 4h-Historie. Ein rückwirkend neu bereinigtes Dataset muss in einem neuen Journal untersucht werden. Historische Ganzaktien-Ausführbarkeit und Dividenden sind durch reine Signalbeobachtung weiterhin nicht geklärt.

## Prüfung

Die Tests prüfen Schritt/Batchequivalenz, eingefrorene Ereignisse, Neustart/Deduplizierung, Abbruch/Rollback, neue Dataset-IDs mit gleichem Präfix, Ablehnung revidierter Historie und geänderten Codes, prospektive Startgrenzen, Seitengrenzen sowie echten Backup/Restore. Das zusätzliche Offline-Werkzeug vergleicht dieselben Eigenschaften an einer echten lokal gespeicherten Aktie:

```text
python tools/verify_signal_journal.py --root NEUER_PRIVATER_TESTORDNER --plan PRIVATER_ROBUSTHEITSPLAN --symbol AAPL
```

Die einmalige Hydrierung des echten Datasets im Integrationswerkzeug dient nur der Laufzeit; die geprüfte Journalberechnung bekommt weiterhin ausschließlich Kerzen bis zum jeweiligen Schluss. Ein solcher Replaytest ist kein prospektiver Erfolgsnachweis.
