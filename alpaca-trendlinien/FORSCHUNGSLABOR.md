# Tori-Forschungslabor

Lokaler Entwicklungsstand vom 18.10.2026 auf `codex/research-lab`. **Lokal technisch abgenommen; kein Proxmox-Rollout.** Die konkreten Nachweise stehen in [FORSCHUNGSLABOR-UMSETZUNG.md](FORSCHUNGSLABOR-UMSETZUNG.md). Die Dokumentation beschreibt die vorhandenen Codepfade; sie ist kein Nachweis bereits erhobener manueller Labels, einer ausreichend großen Untersuchung oder einer profitablen Strategie.

## Zweck und Trennung

`entry_mode: "lab"` ist ein zusätzlicher Modus. Legacy und der bisherige Tori-Modus bleiben erhalten. Die Navigation **Labor** öffnet `/lab`; Chart und Forschung bleiben eigenständig. Der Laborauftrag wird von der bestehenden dauerhaften Queue verarbeitet, ohne Browser und ohne LLM. Ein unveränderlicher Experimentvertrag hält Hypothese, Profile, primäre Einstiegsfamilie, Kennzahl, Horizonte, Universum, Datenkonventionen und Ausführungsannahmen fest. Neue Regeln benötigen ein neues Experiment. Bestehende Zeitpläne werden nicht automatisch umgestellt.

Die primäre Frage wird vor dem Lauf ausgewählt. Ausbruch, horizontale Bestätigung und Retest sowie vorläufige/qualifizierte Fälle bleiben getrennte Gruppen. `baseline` ist ein Grundsignal **auf derselben Trendlinien-/Safety-Geometrie**, ohne die zusätzlichen Qualitätsfilter. Es ist keine von der Linienerkennung unabhängige Marktstrategie. Die Referenz bleibt in ihrer bisherigen Kriterienauslegung unverändert. `retest_hold` lässt ausschließlich bei einer Retestbestätigung die vier Ausbruchskörper-/Momentumprüfungen weg. Ein Retest muss weiterhin selbst bestätigt werden.

## Daten

Künstliche Offline-Fixtures werden als `dataKind: "synthetic"` gespeichert und im Chart sowie in der Fallprüfung ausdrücklich als Testdaten gekennzeichnet. SYNTHA/SYNTHB sind keine Aktien. Vorhandene explizit markierte Fixtures werden auch ohne Änderung ihrer gespeicherten Dateien erkannt.

Neue Laborimporte laden explizite 5-Minuten-Daten des gewählten Feeds und bauen daraus reguläre XNYS-Sitzungen. Stunden- und 4h-Kerzen starten um 09:30 New York; die letzte Kerze endet beim tatsächlichen Börsenschluss. Feiertage, Sommerzeit und verkürzte Sitzungen kommen aus dem versionierten Kalender. Eine unvollständige fein aufgelöste Gruppe ergibt keine aggregierte Kerze. Fehlende Handelsaktivität eines Einzelplatzes kann deshalb ebenfalls als unvollständiger Pfad erscheinen; dies ist keine automatisch nachgewiesene Anbieterstörung.

Feed und Bereinigung gehören zu Cache- und Dataset-Identität. Bereinigte Abrufe werden bei Aktualisierung vollständig neu geladen, damit unterschiedliche Bereinigungsskalen nicht zusammengemischt werden. Alte unveränderliche Datasets bleiben erhalten. `raw`, `split` und `all` sind ausdrücklich verschiedene Untersuchungen. Der heutige bereinigte Datenstand ist kein historisches Veröffentlichungsvintage; Gesamtrendite, Dividendengutschriften und Kapitalmaßnahmen im Depot sind nicht automatisch rekonstruiert. Die Ausführung bleibt ein Modell in der jeweiligen gespeicherten Preiseinheit; ganzzahlige bereinigte Einheiten sind nicht zwingend damalige Originalstückzahlen.

Mit `allow_native: true` können gepinnte native Altbestände ausdrücklich für eingeschränkte Techniktests verwendet werden. Tatsächlicher Feed/Bereinigung und fehlende zeitliche Präzision werden im Manifest genannt. Die strenge 5m-Konvention wird dadurch nicht als erfüllt ausgegeben. Ohne 5m-Daten erzeugt die Depotsimulation keine erfundenen Fills.

Alle Aktien eines Experiments bekommen dieselben zeitlichen Phasengrenzen im gemeinsamen Datenbereich nach einem Jahr Vorlauf. Ein zu kurzer gemeinsamer Bereich ergibt einen nachvollziehbaren Fehler; IPOs oder kurze Einzelbestände verlängern die gemeinsame Historie nicht künstlich. Eine explizite Mitgliedschaftsliste kann je Symbol inklusive Start/Ende und Quelle angegeben werden. Ohne solche Angaben ist das Universum eine heutige Liste mit möglichem Survivorship Bias, kein belegter historischer Indexbestand. Datenbanken, Datasetdateien und Backups gehören in denselben externen `TORI_DATA_DIR`; sie werden nicht nach Git hochgeladen.

## Ablauf und Zustände

1. Entwicklung registriert den Vertrag und bindet den unveränderlichen Datenbestand plus gemeinsamen Phasenplan.
2. Ein vollständiger chronologischer Scan pro Profil/Aktie hält ursprüngliche Linienpaare fest. Neue Linien verdrängen alte Setups nicht rückwirkend.
3. Spätere Phasen spielen den Signalzustand ab dem gemeinsamen Entwicklungsstart erneut durch. Dazu gehören Identitäten abgelaufener Setups. Ein kurzer Vorlauf würde sonst alte Linien eventuell erneut aktivieren. Frühere Einstiege werden nicht als neue Phaseneinstiege ausgewertet.
4. Die Ergebnisbewertung erfolgt nach der Signalberechnung in einem getrennten Modul. Ergebnisse fließen nicht in historische Signale zurück.
5. Die Validierung setzt einen abgeschlossenen Entwicklungslauf voraus. Nach abgeschlossener Validierung kann ein vorregistriertes Profil mit Begründung eingefroren werden.
6. Der Abschlusslauf benötigt zusätzlich `confirm_final_test: true`. Er untersucht nur das eingefrorene Profil. Der Zugriff wird bereits beim Start reserviert, auch wenn der Lauf später abbricht. Überlappende bereits geöffnete Abschlusszeitbereiche derselben Aktie bleiben auch unter neuen Datenrevisionen oder verändertem Universum gesperrt. Das ist eine interne Versuchssperre; externe Kurskenntnis kann sie nicht erkennen.
7. Walk-forward verwendet ausschließlich Entwicklungs- und Validierungsdaten. Jedes Trainingsfenster wählt das Profil anhand vollständiger Trainingsbeobachtungen der vorregistrierten primären Familie/Kennzahl. Unvollständige Horizonte werden nicht zur Auswahl benutzt. Bei zu wenig Fällen gibt es ausdrücklich keinen ausgewählten Kandidaten. Die Wahl wird vor der anschließenden Auswertung im Ereignisjournal gespeichert. Reservierte Abschlussdaten bleiben unberührt.

Unterbrechungen werden über stabile IDs und atomare Upserts fortgesetzt. Fertige Abschnitte werden übersprungen; ein unvollständiger Abschnitt wird deterministisch wiederholt. Abgebrochene und bereits bei Vorbereitung/Import gescheiterte Versuche bleiben im Journal. Ein anderer Engine-Hash wird nicht akzeptiert. Der vorregistrierte Profilumfang ist begrenzt; ein automatischer unbeschränkter Parameteroptimierer existiert nicht.

## Ergebnisse und Grenzen

- Horizonte zählen 5/10/20 Börsensitzungen **nach dem New Yorker Einstiegstag**, nicht Kalender- oder 4h-Kerzen. Fehlende Sitzungen verschieben den Zieltermin nicht. Phasengrenzen schneiden Horizonte ab.
- Schlusskursänderung, MFE/MAE, deren Kerzenintervalle, anfängliches Risiko, terminales R sowie Safety-/1R-/2R-Berührungen werden getrennt erfasst. Der Pfad beginnt beim tatsächlichen Entry; frühere Tageshochs/-tiefs zählen nicht dazu.
- MFE/MAE aus lückenhaften oder nativen unbestätigten Pfaden bleiben Einzelfallbeobachtungen, werden aber nicht in die Mittelwerte vollständiger Feindatenpfade eingerechnet. Eine Berührung kann beobachtet sein; Nichtberührung ist bei Lücken unbekannt. Intrabarreihenfolgen bleiben teilweise mehrdeutig.
- Hypothetische abgelehnte Fälle werden nur für tatsächlich ausgelöste Familien erzeugt. Ein nie bestätigter Retest, eine bloße Ablaufmarkierung oder ein Safety-Bruch vor jedem Ausbruch wird nicht rückwirkend zu einem Einstieg. Hypothetische Fälle sind getrennt und gelangen nicht ins simulierte Depot.
- Kontrollen kommen aus derselben Aktie, demselben New Yorker Zeitraster und Kalenderquartal, mit gleicher vorher bekannter Tages-MA20-Seite und einer vorher definierten Auswahl nach vergangener ATR/Preis. Die Zufallswahl verwendet keine späteren Renditen. Das ist ein beschreibender Vergleich, kein Nachweis einer kausalen Wirkung des Einstiegs.
- Der optionale Marktvergleich benötigt eine tatsächlich vorhandene fein aufgelöste Eröffnung zur gleichen Zeit. Fehlt sie, bleibt er unbekannt; es wird nicht heimlich eine andere Uhrzeit eingesetzt.
- Wiederholte Ankerpaare werden je Gruppe auf Dataset/Einstiegszeit dedupliziert. Verschiedene Familien, Qualitätsgruppen und Profile können weiterhin dieselben Zeitpunkte enthalten. Überlappende Pfade einer Aktie werden zu Episoden zusammengefasst. Unterschiedliche Aktien können gemeinsam vom Markt abhängen.
- Beschreibende Bootstrapintervalle gruppieren Aktie/Kalenderquartal; sie korrigieren weder jede Marktquerabhängigkeit noch die Auswahl mehrerer Profile. Bei weniger als drei Blöcken wird kein Intervall ausgewiesen. Kleine oder leere Gruppen sind kein belastbarer Vorteil.
- Vorgegebene Merkmalsgruppen für Kontakte, Linienalter, Safety-Prozent und Tagesstruktur sind beschreibend. Es werden daraus keine optimalen Schwellen behauptet.

## Optionale Depotsimulation

`lab.execution.enabled` startet getrennte Modelle pro Profil **und** Einstiegsfamilie. Unterstützt sind `time`, `stop_time`, `stop_target_time`. Der ursprüngliche Stop bleibt fest; das optionale Ziel ist ein festes Vielfaches des anfänglichen modellierten Preisrisikos. Diese Modelle ersetzen keine später zu erforschenden Trailing-/Exitregeln.

Käufe erhalten halben Spread plus Slippage, Verkäufe dieselben Abschläge, hinzu kommen feste Gebühren pro Order. Bei einem Stop-Gap wird die schlechtere Eröffnung verwendet. Eine Zieleröffnung wird konservativ nur zum Ziel abgerechnet. Liegen Stop und Ziel innerhalb derselben Kerze und ist ihre Reihenfolge unbekannt, gilt Stop zuerst. Kapital wird konservativ erst am Kerzenende frei. Fehlende 5m-Pfade lassen Positionen ungeklärt; es gibt keine fiktive Stop-/Zielausführung über eine Lücke.

Stückzahlen werden aus dem dann bekannten markierten Depotwert, verfügbarem Cash, Risiko-/Kapitalanteil und Positionsgrenzen bestimmt. Keine Kreditaufnahme, höchstens eine Position pro Aktie. Gleichzeitige Kandidaten werden nach Symbol und stabiler Setup-ID geordnet, niemals nach späterem Gewinn. Gebühren gehen in Cash und Netto-Ergebnis ein. Offene Positionen werden zu dann bekannten Preisen bewertet. Die Depotkurve enthält Tagesabschlüsse und Einstiegszeitpunkte; ihr Rückgang ist kein vollständiger Intraday-Drawdown. Unsichere offene Pfade sind markiert. Ein Gap kann das geplante Risikobudget überschreiten.

## Verblindete Sichtprüfung

Fallpakete lassen sich nur aus abgeschlossenen Entwicklungsaufträgen erstellen. Sie mischen zufällige Kerzen und diagnostische Bestätigungs-/Ablehnungsfälle, ohne spätere Renditen für die Auswahl zu verwenden. Das ist keine repräsentative Erfolgsstichprobe.

Die Blindantwort enthält ausschließlich abgeschlossene 4h-/Tageskerzen bis zum Fallzeitpunkt, Herkunft und eigene gespeicherte Beurteilung. Engineentscheidung und Zukunft sind zunächst verborgen. In der Laboransicht können rote und grüne Linien mit je zwei Klicks gezeichnet werden. Gespeichert werden Anker, Ja/Nein/Warten und Begründung. Erst danach lässt sich explizit aufdecken. Geänderte Labels nach Offenlegung werden als beeinflusst markiert und aus dem beschreibenden Übereinstimmungsvergleich ausgeschlossen. Labels vor Offenlegung bleiben im Audit erhalten. Exakte Ankerübereinstimmung ist enger als visuell ähnliche Linien; der Bericht behauptet dafür keine automatische Näherungsbewertung.

## Werkzeuge für Hermes

Wie bisher `tori-tool submit --spec <json>` und `report/status/events`. Neue Kommandos:

```text
tori-tool lab-profiles
tori-tool lab-experiments
tori-tool lab-experiment --id <experiment>
tori-tool lab-run --id <experiment> --stage validation
tori-tool lab-run --id <experiment> --stage walk_forward
tori-tool lab-seal --id <experiment> --profile reference --rationale "Vorher dokumentierte Auswahlbegründung"
tori-tool lab-run --id <experiment> --stage holdout --confirm-final-test
tori-tool lab-audit --id <experiment> --limit 50
tori-tool lab-audit --id <experiment> --after <nextAfter> --through <through> --limit 50
tori-tool lab-review-create --job <development-job> --count 30 --seed 7 --profile reference
tori-tool lab-review --id <pack> --limit 50
tori-tool lab-review-case --id <pack> --case <case>
tori-tool lab-review-label --id <pack> --case <case> --file <label.json>
tori-tool lab-review-reveal --id <pack> --case <case>
tori-tool lab-review-compare --id <pack>
tori-tool lab-portfolio --job <job> --section development --profile reference --family breakout --limit 100
```

CLI-JSON ist UTF-8, auch bei Windows-Pipes. HTTP verwendet die entsprechenden `/api/lab/profiles`, `/experiments`, `/experiments/<id>[/audit|/run|/seal]`, `/reviews`, `/reviews/<pack>[/<case>|/compare]`, `/reviews/<pack>/<case>/label|reveal` und `/portfolio?job=…&section=…&profile=…&family=…`. GET verändert keine Regeln und startet keinen Anbieterabruf. Schreibzugriffe behalten die vorhandene Host-/Origin-/Authentifizierungsprüfung. Keine Tokens in URLs.

Journal, Fälle und Simulationsdaten sind paginiert. Simulationsseiten enthalten getrennte Seiteninformationen für Trades, ausgelassene Kandidaten und Depotpunkte. Berichte halten zeitliche Abschnitte auseinander. Hermes darf die gespeicherten Ergebnisse erklären und vorgegebene Läufe ausführen; er darf keine heutigen Nachrichten oder eigenes Zukunftswissen in historische Signale einbauen.

## Betrieb und lokale Abnahme

Migration auf Schema 4 ergänzt Labortabellen, verändert keine historischen Jobs/Datasets und behält transaktionale Strukturprüfungen. Backup/Restore nimmt die zusätzlichen SQLite-Tabellen mit; gebundene Experimente und Reviewfälle halten Datasetreferenzen für die Bereinigungsvorschau fest. Vor einem tatsächlichen Update Dienst stoppen und konsistent sichern. Kein automatisches Downgrade. Der gleiche externe Datenordner gilt für Webdienst und Worker/CLI.

Gezielte technische Tests liegen in `test_lab_data.py`, `test_lab_engine.py`, `test_lab_registry_jobs.py`, `test_lab_execution_reviews.py`, `test_lab_api.py` und `test_lab_view.cjs`. Die vollständige lokale Prüfung umfasst 158 Python-Tests je unter 3.12/3.13, 27 JavaScript-Tests, Offline-Ende-zu-Ende mit Backup/Restore und anschließende Browserprüfung. Konkrete Nachweise und Grenzen stehen im Abnahmeplan. Die synthetischen Prüfungen belegen technische Abläufe, keine Marktprofitabilität.
