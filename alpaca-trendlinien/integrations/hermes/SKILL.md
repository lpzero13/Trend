---
name: tori-research
description: Starte und prüfe technische Tori-Ereignisstudien über definierte JSON-Werkzeuge.
---

# Tori-Forschung

Diese Vorlage ist für die spätere Einrichtung im Hermes-Zielsystem gedacht. Sie wurde nicht automatisch in eine vorhandene Hermes-Installation installiert. Projektpfad und ausführbaren Python-Pfad an den Zielcontainer anpassen. Auf demselben Container und als berechtigter Dienstbenutzer `tori`: `TORI_DATA_DIR=/var/lib/tori /opt/tori/.venv/bin/python /opt/tori/tori.py`. Alternativ nach Installation den Wrapper `tori-tool` verwenden. Der Datenordner muss mit dem Webdienst übereinstimmen; sonst sieht der Agent eine andere Queue.

## Aufgabe

Tori untersucht Long-Ereignisse anhand zufälliger historischer Startpunkte. Ein Hintergrunddienst erledigt bereits die geplanten Untersuchungen. Nutze die vorhandenen Aufträge zuerst, statt bei jeder Nachfrage denselben Versuch erneut zu starten.

## Tages-Radar, Top 10 & 1.000-€-Papertrading

Alle Tagesbefehle laufen immer mit demselben `TORI_DATA_DIR=/var/lib/tori` wie der Webdienst (`User=tori`). Keine Brokerorders, keine erfundenen Kurse, strikt kausal nach US-Börsenschluss.

1. **Täglicher Komplettlauf (SIP-Update + Top-10-Scan + Watchlist/Papertrade-Auswertung):**
   ```bash
   TORI_DATA_DIR=/var/lib/tori /opt/tori/.venv/bin/python /opt/tori/tools/tori_candidate_preview.py \
     --update --session auto --top 10 --evaluate-watchlist \
     --md-out /var/lib/tori/operations/preview/full/latest-report.md \
     --csv-out /var/lib/tori/operations/preview/full/latest-candidates.csv \
     --json-out /var/lib/tori/operations/preview/full/ranked-candidates.json
   ```
   - `--update` aktualisiert alle lokal vorhandenen SIP-Historien (Dow 30, Nasdaq-100, S&P 500 sowie vorhandene `SPY`/`QQQ`-Benchmarks) inkrementell nach US-Börsenschluss.
   - Der Scanner sortiert die Tages-Top-10 strikt nach den empirisch über alle drei PIT-Splits (`train`/`validation`/`holdout`) bestätigten Qualitäts-Stufen:
     - **Stufe `C` (Premium):** Direkt-Einstieg (`1A`/`4A`) + Aktive Annäherung + Hohe Reife (`≥ 21 T` / `≥ 4 K`) + Ruhige Tagesvola (`ATR_1D < 1,5 %`). Immer ganz oben.
     - **Stufe `B` (Stark):** Ruhige Vola + 2 der 3 Kernmerkmale.
     - **Stufe `4` (Ruhige Vola):** `ATR_1D < 1,5 %` mit weniger als 2 weiteren Kernmerkmalen.
     - **Stufe `A` (3/3-Kern):** Direkt + Aktiv + Hohe Reife (höhere Tagesvola).
     - **BASIS:** Übrige valide Setups.
   - `marketRegime` (`SPY`/`QQQ` vs. SMA200/SMA50) ist rein informativ und filtert keine Setups automatisch weg.
   - `--evaluate-watchlist` aktualisiert automatisch alle aktiven Watchlist- und 1.000-€-Papertrade-Einträge in `TORI_DATA_DIR/paper-watch/watchlist.sqlite3` (getrennt von `research/jobs.sqlite3`).
   - Systemd-Vorlagen für Mo–Fr 23:00 Uhr `Europe/Berlin`: `deploy/tori-daily-radar.service` und `deploy/tori-daily-radar.timer`.

2. **Watchlist & 1.000-€-Papertrading steuern (`tools/tori_paper_watch.py`):**
   - `... tools/tori_paper_watch.py list` — aktive Watchlist- & Papertrade-Positionen + Gesamtbilanz.
   - `... tools/tori_paper_watch.py add --symbol <TICKER> --stop-policy r2_fan --capital 1000` — Kandidat aus dem letzten Scan auf die Watchlist bzw. als isolierten 1.000-€-Papertrade setzen.
   - `... tools/tori_paper_watch.py evaluate` — alle aktiven Positionen kausal auf 5m-Kerzen aktualisieren.
   - `... tools/tori_paper_watch.py updates --limit 30` — letzte Stop-/Entry-/Exit-Ereignisse.
   - `... tools/tori_paper_watch.py summary` / `archive --id <ID>`.

3. **Web-Oberflächen (gleicher `TORI_DATA_DIR`):**
   - `/radar`: Tages-Radar (Top 10 nach Stufe farblich markiert, US-Marktlage, 1-Klick-Übernahme auf Watchlist/Papertrade).
   - `/backtest`: Point-in-Time-Backtest-Explorer & Blind-Training mit 1-Klick-Replay-Sprung (liest Studien aus `<app>/artifacts/` oder `TORI_DATA_DIR/artifacts/`).

## Werkzeuge

**Lokaler Vorwarnversuch vom 01.11.2026:** `tools/early_warning.py` ist ein eigener Offline-CLI-Weg; Vertrag in `EARLY-WARNING.md`, Ergebnisvergleich in `EARLY-WARNING-ERGEBNISSE-20261101.md`. `all/prepare/build/evaluate` verwenden einen ausdrücklich ausgewählten lokalen Quellplan und denselben `TORI_DATA_DIR`; `tools/verify_early_warning.py` und `tools/verify_warning_prefix.py` prüfen Ergebnisse und Zukunftsgrenzen. Code-/Planänderung verlangt einen neuen Studienordner. `briefing --asof` gibt nur damals bekannte offene Warnungen aus geeigneten historischen Fenstern aus, ohne zukünftige Entries/Ausgänge; `show` ist dagegen eine ausdrücklich ergebnisoffene Forschungsansicht. `review` speichert mute/unmute/snooze je Familie oder Episode, ohne Forschungsfälle zu entfernen. Stufen und Warnungen sind noch keine Brokerfreigaben, tatsächlichen Fills oder Profiterwartungen. Die konkrete Originalgeometrie stammt aus dem Warnsnapshot; der normale Chartlink allein garantiert nicht, dass derselbe ältere Kandidat als aktuelle Linie ausgewählt wird. Keine Warnsnapshot-Webebene, kein Liveimport, Versand, Dauerauftrag oder automatischer Rollout eingerichtet. Historische Treffer niemals als neue aktuelle Meldungen verschicken. Ein bis zwei Tage vor einem rohen Bruch und ein bis zwei Tage vor einer späteren Entrybestätigung unterscheiden; die Studie misst beides getrennt. Diese Vorlage wurde nicht in Hermes installiert.

**Optionaler neuer Safety-Weg (20.10.2026, lokal):** `strategy-rules`, `strategy-export`, `strategy-study`, `strategy-report`, `strategy-verify`, `strategy-scan`; Vertrag und genaue Befehle in `SAFETY-STRATEGIEN.md`. Nicht mit bestehender Queue oder den Laborphasen verwechseln. Neue Strategie-Studien benötigen einen frischen Ausgabeordner und gepinnte echte IEX-Datasets; nach Import offline. `--resume` nur unter unveränderter Engine und Quelle, abgeschlossene Phasen nicht überschreiben. Kandidatenscan rekonstruiert chronologisch bis zum Stichtag, gibt historische Open-Ereignisse und noch nicht ausführbare Pending-Signale getrennt aus. Aktualität sichtbar prüfen, stabile IDs deduplizieren, keine rückwirkenden Orders/Meldungen aus historischen Treffern erzeugen. Die Varianten sind Forschungsmodelle, keine freigegebene Gewinnstrategie. Finaler Holdout bleibt geschlossen. Diese Vorlage wurde nicht in Hermes installiert.

**Neuer lokaler Laborzweig, Gesamtabnahme noch offen:** `entry_mode: "lab"` und die `lab-*`-CLI-Kommandos ergänzen registrierte Experimente, zeitlich getrennte Entwicklung/Validierung/Abschlusstests und Walk-forward. Vollständiger Werkzeugvertrag und Daten-/Ausführungsgrenzen: `FORSCHUNGSLABOR.md`. Einstieg `lab-profiles`, `lab-experiments`, `lab-experiment --id …`; Folgeläufe mit `lab-run`. Regeln/Daten eines Experiments nicht überschreiben. Nach Validierung `lab-seal` mit begründeter Kandidatenauswahl; finalen Holdout nur als bewusst beauftragte einmalige Prüfung öffnen. Unterschiedliche Profile/Familien und Trainings-/Prüfabschnitte niemals zu einer scheinbar unabhängigen Stichprobe addieren. Optionale modellierte Depotwerte sind von Legacy-Ereignisstudien und realen Brokerergebnissen zu unterscheiden. Vor einem tatsächlichen Rollout Schema 4 und den offenen Abnahmeplan beachten. Diese Skillvorlage wurde dadurch nicht in Hermes installiert.

- `list`: verfügbare Aufträge und Status als JSON lesen.
- `health`: lokale Betriebsbereitschaft, getrennte Lebenszeichen/Fortschrittszeiten, Datenalter und letzte Fehler lesen; kein Providerabruf. Warnung bei länger fehlendem Fortschritt ist kein sicherer Deadlock-Nachweis.
- `submit --spec <datei.json>`: einen validierten Forschungsauftrag einreichen. Parameterbeispiel: `/opt/tori/deploy/experiment.example.json`. Die Antwort enthält die Job-ID.
- `status --id <id>`: Fortschritt, ausgelassene Aktien und Fehler prüfen. Längere Abrufe sind normal; Status in sinnvollen Abständen statt in enger Schleife lesen.
- `report --id <id> --offset 0 --limit 250`: Gesamtauswertung plus paginierte Einzelfälle lesen. Für weitere Fälle Offset erhöhen. Die Gruppentabelle bezieht sich auf alle Fälle, nicht nur diese Seite.
- Optionaler Tori-Einstiegsmodus: `submit` mit `entry_mode: "tori"` und versionierten `tori`-Parametern. `sampling: "origins"` für zufällige Starttage mit Suche bis zum ersten Entry je Variante oder Entwicklungsende; `samples` und `seed` steuern die Tage, `search_bars` begrenzt diese Suche nicht. `full` prüft den gesamten Zeitraum, `random` behält die alte begrenzte Fensterstudie. Der spätere Holdout bleibt reserviert. Starts mit Entry und eindeutige spätere Entryzeitpunkte unterscheiden; mehrere Starts können denselben Entry erreichen, ein Entry ist nicht garantiert. `line_policy: "snapshot"` fixiert zu X, `tracked` verfolgt neue bestätigte Paare. `observe_forward: true` aktiviert rohe Schlusskursänderungen nach `horizons` XNYS-Handelstagen nach dem Einstiegstag, ohne Ausstiege/Kosten/Depot-P/L; in Zufallsfenstern nur erster Entry je Variante. API-Defaults bleiben vollständiger Zeitraum und nur Einstiege. Anleitungen: `TORI-EINSTIEGSMODUS.md`, `TORI-KURSBEOBACHTUNG.md`, Beispiel `deploy/tori-forward.example.json`. `report --entry-filter entries --limit 50` filtert Fälle, nicht die Gesamtsumme. Gleiche Zeitpunkte/Varianten nicht als unabhängige Trades zählen; unvollständige Horizonte und Fenster ohne Entry nennen. Bestehenden Zeitplan nur auf Nutzerauftrag umstellen.
- `events --id <id> --limit 250`: erste Ereignisseite als `{items, page}` lesen. Mit `--cursor <page.nextCursor>` fortsetzen, bis `hasMore` falsch ist. Standard 250, maximal 1.000; der Lesestand bleibt fest. Ein neuer Abruf ohne Cursor sieht inzwischen ergänzte Ereignisse. Frühere CLI-Parser für eine vollständige Liste müssen angepasst werden.
- `cancel --id <id>`: einen ausdrücklich unerwünschten Auftrag abbrechen, Archiv erhalten.
- `schedule`: bestehenden Zeitplan lesen; Änderungen nur entsprechend dem Auftrag des Nutzers vornehmen.
- `storage`: Größen nach Datenkategorie und freien Plattenplatz lesen. Vor Imports wird zusätzlich konservativ Platz geprüft; ein Fehler 507 ist kein Providerfehler.
- `backup --output <neuer-ordner>` / `verify-backup --path <backup>`: konsistente SQLite-/Dataset-/Snapshot-Sicherung außerhalb des aktiven Datenpfads erstellen und prüfen. Secrets, Cache und Browserzeichnungen sind nicht enthalten.
- `restore --backup <backup> --target <neuer-ordner>`: ausschließlich in einen neuen Ordner außerhalb des aktiven Datenpfads wiederherstellen; kein automatischer Dienstwechsel. Zeitplan vor einem separaten Teststart prüfen. Vorgehen und Rolloutgrenzen in `BETRIEB-P2.md`.
- `cleanup-preview`: ausschließlich Vorschau nicht referenzierter Datasets, keine Löschfunktion. Kandidaten nicht automatisch entfernen.

Eine separate Installation kann alternativ dieselben Operationen über die in `FORSCHUNG.md` beschriebenen HTTP-Routen verwenden. Den bereitgestellten Bearer-Token als Header verwenden, niemals in URLs oder Berichte schreiben. Kein direkter Datenbankzugriff über Netzwerkfreigaben.

## Auswertung

Beim neuen Safety-Scan `eventKey` für importübergreifende Deduplizierung verwenden; Entry-/Vertrags-IDs sind dagegen an eine exakte Datenversion gebunden. Pending und beobachteter Open derselben Bestätigung teilen den `eventKey`. Regel-/Profilwechsel bewusst getrennt halten. `strategy-report` unterscheidet Einzelpfad-R/1.000-USD-Werte von Cash-Portfolios. `incomplete` ist nur ein beobachteter Präfix, `marked_to_phase_end` kann offene Positionen enthalten. Ergebnisbilanz vom 20.10.2026: `SAFETY-ERGEBNISSE.md`; kein Kandidat für den produktiven Betrieb ausgewählt.

1. Zwischen erfolgreich, teilweise erfolgreich, Fehler und unvollständigen Beobachtungen unterscheiden. Keine fehlenden Fälle als Erfolg zählen.
2. Ausbruch und Retest sowie vorläufige/qualifizierte Linien getrennt betrachten. Exakte Kontakte, Abstand zu Grün und Tageskontext stehen in den Fallmerkmalen.
3. Mehrere Ursprünge können denselben Entry finden; die Zusammenfassung dedupliziert ihn. Auch verschiedene überlappende Ereignisse und wiederholte Aufträge sind keine unabhängigen Stichproben.
4. Positive Nettokursänderung, MFE, MAE und Schutzmarkenberührung sind unterschiedliche Beobachtungen. Die Studie liefert keine Portfoliorendite und keinen exakten Stop-Verkauf.
5. Originalsignale und Dataset-IDs in Begründungen angeben. Auffällige Fälle über den Chart prüfen lassen, statt spätere automatische Linien als den damaligen Auslöser zu behandeln.
6. Regeln zunächst als Hypothesen vorschlagen und Parameteränderungen als neue Experimente kennzeichnen. Reservierten Holdout nicht zur fortlaufenden Auswahl besserer Parameter benutzen.
7. Keine heutigen Nachrichten, Kurskenntnisse oder LLM-Erinnerungen rückwirkend in historische Einstiegsentscheidungen einbringen. Der Rechenkern erzeugt Signale und Zahlen; der Agent beschreibt die gespeicherten Ergebnisse.
8. Keine Brokerorders. Es existiert keine Orderfunktion in Tori.
9. Datenqualitätshinweise im Bericht mitlesen. Ein Audit des gesamten Datasets ist kein zeitgerechter Einstiegsfilter und bestätigt keine Kapitalmaßnahmen. Ältere Datasets ohne Audit sind nicht automatisch geprüft. Neue US-Tageskerzen nutzen den versionierten XNYS-Kalender; alte Datasets behalten ihre gespeicherten Abschlüsse.
10. Vollständige/unvollständige Horizonte und zeitliche Überlappungen getrennt nennen. `overlapping_entries` ist keine statistische Korrektur der Stichprobe. Vor Updates sichern; Schema 3 hat Vorwärtsmigrationen, keine automatische Rückwärtsmigration. Engine-Hash-Abweichungen nicht umgehen.
