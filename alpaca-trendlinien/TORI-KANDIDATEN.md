# SIP-Kandidatenversuch: Bedienung und Betrieb

Stand 22.10.2026. Ergänzt `HERMES.md`; dessen Sicherheits- und Betriebsvorgaben gelten weiter.

## Implementierter Umfang

`/kandidaten` ergänzt Chart, Forschung, Labor, Beobachtung und Sichtprüfung. Die manuelle Chart startet weiterhin ohne automatische Analyse. Der Versuch verwendet 4h-SIP-Quellkerzen und damals bekannte Tages-/Wochenkontexte. Alte IEX-Profile und der bestehende IEX-Beobachter bleiben unverändert. MTF-Projektionen sind keine Einstiegssignale.

Umgesetzt: 20 zufällige SIP-Präfixe zur blinden Geometrieprüfung, Merkmalsstudie mit passenden Zufallskontrollen, kapitalbegrenzter Vergleich und separater prospektiver Papierbeobachter. Siehe `TORI-KANDIDATEN-PLAN.md` und `TORI-KANDIDATEN-ERGEBNISSE.md`.

Keine Orders, Nachrichten, Containerinstallation oder validierte Handelsstrategie. EODHD, historische Point-in-time-Unternehmensereignisse, automatische Meldepriorisierung und ein historisch vollständiges Universum sind hier nicht implementiert. Ein LLM soll später gespeicherte Fakten erläutern, keine OHLC-Werte erfinden oder rückwirkend passende Linien aussuchen.

## Linien, Gruppierung und Kandidaten

Ähnliche rote/grüne Paare werden bei höchstens 0,25 damaliger ATR Unterschied am bekannten Quellindex und dessen Projektion +20 zusammengefasst. +20 verwendet keine zukünftigen Kurse. Die ersten Anker bleiben unverändert; spätere Alternativen werden aufbewahrt. Ein Retest einer ähnlichen anderen Linie darf nicht als Retest der ersten Linie erscheinen.

Zustände: Annäherung, Ausbruch, Retest, Safety-Reaktion, ungültige Geometrie und unklar/ausgesetzt. Ein fehlendes Aktions-/Safety-Paar bleibt unklar. Verletzung der ursprünglichen Safety oder Schluss zurück unter die gebrochene Aktionslinie können die Geometrie ungültig machen. Das ist kein behaupteter Fill des gepufferten Papierstopps. Fehlende Quellkerzen setzen die Interpretation aus; ältere Annäherungen außerhalb der Nähezone werden unklar.

Sortiert wird erklärbar nach Phase und Zeitpunkt, nicht nach einem trainierten Gewinn-Score. Kontaktzahl, Alter, Safety-Abstand in ATR/Prozent sowie Momentum-, Safety-, Kontext-, Raum- und Ereigniswarnungen bleiben sichtbar. Historisch besser aussehende Untergruppen beseitigen keine Warnung.

Papier-Einstiege stammen unverändert aus `ExplainedReplay`/`CompleteReplay`: strict / age7 / retest. Gruppierung und Projektion verändern diese Einstiege nicht. Exits verwenden `fixed` und `higher_low` aus `complete_outcomes.py`.

## Start und Betrieb für Hermes

Befehle aus `alpaca-trendlinien/`. CLI, Web, Import und Worker müssen denselben Datenpfad verwenden; im LXC `/var/lib/tori`. Vorhandene Secrets nicht überschreiben, niemals Schlüssel in Git, Argumenten oder Berichten ablegen.

```bash
export TORI_DATA_DIR=/var/lib/tori
# Nur falls noch kein passender SIP-Import existiert; neue Generation wählen:
python tools/workbench_import.py --root /var/lib/tori/experiments/sip-import-generation-1
python tools/candidate_watch.py init --source /var/lib/tori/experiments/sip-import-generation-1
# Ausgegebene ID übernehmen:
python tools/candidate_watch.py run --id RUN_ID
python tools/candidate_watch.py status --id RUN_ID
python tools/candidate_watch.py events --id RUN_ID
python tools/candidate_watch.py stop --id RUN_ID
```

Der Importbefehl reproduziert einen historischen Versuchszeitraum bis 21.10.2026; er ist kein beliebiger Live-Universumsimport. Registrierung prüft 1–200 vorhandene echte SIP-Splitdatasets und schreibt den Beginn jetzt fest. Bei fehlendem SIP-Zugang wird nicht still auf IEX gewechselt. Einmaliger Zyklus: `run --id RUN_ID --once`. Als dauernder Prozess später einen eigenen systemd-Dienst mit gleicher Datenbasis einrichten; der Webserver startet diesen Beobachter nicht automatisch. Eine Linux-Serviceabnahme ist noch ausstehend.

Loop: Prüfung alle 15 Minuten. Ohne offene Papierpositionen erst bei neuem erwarteten 4h-Abschluss importieren; bei offenen Papierpositionen neue reguläre 5m-Abschlüsse berücksichtigen. Mindestens 15 Minuten Datenverzögerung, keine Orderausführung. Feiertage, kurze Sitzungen und Sommerzeit folgen dem gemeinsamen Kalender. Keine Providerabrufe durch GET/Healthcheck und kein Abruf bei unverändertem erwarteten Abschluss.

Startbestand ist sichtbar, zählt aber nicht als neuer Vorwärtsfall. Für Papier-Einstiege müssen Signal und Einstieg nach Registrierung liegen. Datenrevisionen oder verschwundene bekannte Kerzen sperren die Spur; neue Generation erforderlich. Geänderte Engine-/Bibliotheksbindung verlangt ebenfalls neue Registrierung. Niemals alte Checkpoints unter neuem Code fortsetzen oder deren Hash passend überschreiben.

## Speichergrenzen

Datasets sind noch vollständige unveränderliche Dateien. Gemessener historischer 60er-SIP-Bestand: rund 977 MiB; eine neue volle Generation kann ähnlich groß sein. Zusätzlich zur freien Speicherreserve gilt konservativ ein 4-GiB-Importbudget je Registrierung. Status: `addedDatasetBytes`, `importBudgetBytes`. Budget-/Speichermangel sperrt die Spur sichtbar. Es wird nichts automatisch gelöscht.

Das begrenzt den lokalen Versuch, garantiert keinen unbegrenzten Dauerbetrieb. Vor großen Universen: Wachstum messen, Sicherung/Restore betreiben und inkrementelle, gemeinsam referenzierbare Dataset-Chunks entwerfen. Neue Run-IDs beseitigen keinen Speicherverbrauch. Aufräumen zunächst nur als Vorschau; referenzierte Daten niemals löschen.

## Persistenz, Wiederaufnahme und Schnittstellen

Bestehende Haupt-SQLite-Datenbank, `settings` unter `cw:*`: Runregistrierung/Herzschlag, Spurcheckpoints/Gruppen, append-festes Journal, unveränderliche Papier-Einstiege, Studien/Einzelfälle und Cashzusammenfassung. Keine neue Runtime-Abhängigkeit oder separate ungesicherte Datenbank. Backup/Restore und rekursiver Dataset-Referenzschutz greifen auch hier; getestet mit externem Datenpfad und Wiederherstellung.

Je Aktie atomare Speicherung von Checkpoint, Papierständen und Journal. Ein OS-Lock verhindert zwei Writer desselben Laufs und wird bei Prozessabbruch freigegeben. Bekannte Stopperhöhungen und abgeschlossene wirtschaftliche Ergebnisse bleiben unveränderlich. Neue stichtagsabhängige Outcome-IDs allein dürfen keinen falschen Revisionskonflikt auslösen. Nutzerdrawings und blinde Bewertungen bleiben getrennt.

Read-only API unter bestehenden Host-/Origin-/Tokenregeln:

```text
GET /api/candidates/runs
GET /api/candidates/status?run=RUN_ID
GET /api/candidates/cases?run=RUN_ID&state=active&offset=0&limit=30
GET /api/candidates/case?run=RUN_ID&id=CASE_ID
GET /api/candidates/events?run=RUN_ID&limit=100[&cursor=CURSOR]
GET /api/candidates/papers?run=RUN_ID&offset=0&limit=50
GET /api/candidates/research
GET /api/candidates/records?research=RESEARCH_ID&offset=0&limit=20
GET /api/candidates/record?research=RESEARCH_ID&id=ENTRY_ID
GET /api/candidates/cash?research=RESEARCH_ID
```

Fallcharts zeigen zunächst nur das damals bekannte Präfix. `future=1` zeigt ausdrücklich spätere gespeicherte Kerzen und Outcomes. Journalcursor sind an Lauf und festen High-Watermark gebunden. Hermes kann Fakten lesen; das autorisiert keinen Nachrichtenversand. Konfiguration und Stoppen erfolgen vorerst über CLI.

## Studien reproduzieren

Benötigt vollständig geprüfte unveränderliche SIP-Gesamtstudie mit passender Enginebindung. Alte Generationen nie unter geändertem Code fortsetzen.

```bash
python tools/candidate_review_pack.py --source /var/lib/tori/experiments/sip-generation
python tools/candidate_study.py --source /var/lib/tori/experiments/sip-generation --root /var/lib/tori/experiments/candidate-generation
python tools/verify_candidate_study.py --source /var/lib/tori/experiments/sip-generation --root /var/lib/tori/experiments/candidate-generation
python tools/candidate_cash.py --root /var/lib/tori/experiments/candidate-generation
python tools/candidate_report.py --root /var/lib/tori/experiments/candidate-generation --output /var/lib/tori/experiments/candidate-generation/ergebnis.md
```

Auswahl wird vor Outcomes gespeichert. Fehlende Kontrollen werden nicht durch zukünftige bessere Fälle ersetzt. Nur vollständige Fünferpanels zählen in den primären Paarvergleich, Ausfälle bleiben im Nenner. Historische Untergruppen sind Hypothesen; kein neuer unabhängiger Holdout wurde beansprucht oder reservierter Holdout zur Optimierung geöffnet.

Kapitalvergleich: volle Originalkohorte, vor Outcome bekannte matchbare Originalkohorte und fünf separate Kontrollreplikate. Fehlende Pfade bleiben enthalten. Ein unbekannter gehaltener Pfad stoppt das Depot. Kursendpunkt, MFE/MAE, realisierter P/L und offene Bewertung bleiben getrennt.

## Tests und ausstehende Arbeit

Abschlussprüfung: 326 Python-Unittests unter 3.12 und 3.13 (je ein vorhandener Skip), 43 JS-Tests und 21 echte HTTP-Prüfungen bestanden. HTTP-/Controllerprüfungen decken Präfixansicht, ausdrückliches Zukunftstoggle, Theme, Papierpositions-Paging, Journalgrenzen, Schutzregeln und Backup/Restore ab. Keine behauptete visuelle Browserabnahme aus diesen Tests ableiten. Unit-Tests benötigen keine echten Providercredentials. Der lokale SIP-Worker hat alle 60 Spuren ohne Fehler initialisiert; tatsächliche neue Vorwärtsfälle stehen noch aus.

Noch offen: deine blinden Bewertungen der 20 SIP-Fälle, ausreichend neue Vorwärtsfälle, gemeinsame vollständige Datenpfade für den Depotvergleich und unabhängige Strategieprüfung. Für großen Dauerbetrieb zusätzlich Chunkablage, externe Neustartüberwachung und vereinbarte Alarmierung. Geplant bedeutet nicht bereits umgesetzt oder profitabel.
