# Historische Einstiege im normalen Chart

Umgesetzt am **31.10.2026**. Eigene zuschaltbare Chart-Ebene über den gespeicherten Ergebnissen der [Signalepisodenstudie](SIGNALFALLSTUDIE.md). Ohne ausdrücklichen Aufruf bleibt die Ebene aus. Die bestehende automatische Tori-Analyse, persönliche Zeichnungen und alte Forschungsinterfaces bleiben verfügbar. Der separate Zufallsmodus behält seinen isolierten Übungsfall; die neue Ebene wird dort nicht eingeblendet.

## Bedienung

1. Aktie wählen und **Historische Einstiege** einschalten.
2. Eine gespeicherte Untersuchung wählen. Das Panel nennt ausdrücklich die untersuchten Zeitfenster; außerhalb dieser Fenster bedeutet kein Marker nicht automatisch „es gab kein Signal“.
3. Nach Ausbruch, rotem Retest, Safety-Bounce und Kontaktklasse filtern. Standardmäßig ausführbare Entries anzeigen; im Replay vor dem tatsächlichen Open bleiben zunächst noch unbestätigte Kandidaten sichtbar. Ohne Ausführungsfilter sind auch nicht ausführbare Signale prüfbar.
4. Einen Marker oder einen Fall in der Liste anklicken. Nur dessen ursprüngliche Signallinie, Safety, bestätigte Kontaktpunkte und Anfangsstop werden eingeblendet. Die Liste beginnt bei den neuesten Ereignissen.
5. **Replay ab Signal · 4h** öffnet den damals bekannten Schluss. Mit ◀/▶ oder den Pfeiltasten einzelne Kerzen weiter/zurück gehen. Chartintervalle 1h/4h/1D/1W bleiben nutzbar; die Quellsignale dieser Untersuchung sind immer 4h.
6. Eigene Bewertung und Notiz speichern: plausibel, falsche Linie/Kontakte, zu spät, Wiederholung oder unklar. **Bewertung löschen** entfernt nur die eigene Bewertung, nicht den gespeicherten Signalfall. Gespeicherte Bewertungen überstehen Neuladen und Wiederaufnahme; ungespeicherte Eingaben bleiben beim Kerzenschritt im geöffneten Browser erhalten.

Das Panel ist angedockt, damit es die letzten Kerzen nicht überdeckt. Über die Überschrift lässt es sich einklappen; Markierungen und ausgewählte Linien bleiben sichtbar. Auf kleinen Bildschirmen teilt es sich die Höhe mit dem Chart. Die Preisskala berücksichtigt die ausgewählten Linien, wenn der Signalzeitpunkt sichtbar ist.

## Was fixiert ist

- Jeder Fall behält seine ID, Episodenherkunft, Entryfamilie, Signalzeit und ursprüngliche Geometrie. Eine Fortschreibung derselben Struktur erzeugt beim Anzeigen oder Kerzenschritt keine neuen Entries.
- Datenbankseitig höchstens ein Fall je Episode und Entryfamilie pro Untersuchung. Ausbruch und späterer roter Retest dürfen beide erscheinen, behalten aber ihre gemeinsame Herkunft. Verschiedene Untersuchungen werden nicht übereinander vermischt.
- Der Marker liegt an der Kerze des **Signalschlusses**. Das ist nicht zwangsläufig die Kaufkerze. Der tatsächliche Modell-Entry folgt am nächsten zulässigen Open nach 300 Sekunden und wird mit Zeit, rohem Open und Kostenfill im Detail angezeigt.
- Bei Intervallwechsel werden dieselben Ereignisse auf die enthaltende abgeschlossene Chartkerze abgebildet. Es findet keine neue 1h-/Tages-/Wochensignalsuche statt. Fehlt eine enthaltende abgeschlossene Kerze, wird kein Marker auf eine Nachbarkerze verschoben und keine künftige Kerze erfunden.
- Zeit-/Preisanker bleiben unverändert. Zusätzlich werden die Zeichenpositionen der ausgewählten Linien pro Fall/Datasetversion/Chartintervall im Browser fixiert, damit spätere unregelmäßige Kerzenabstände ihre Projektion nicht verschieben. Diese MTF-Projektionen sind ausschließlich Darstellung und keine neuen Entries.
- Die Linien der automatischen Ebene sind nicht als persönliche Rays editierbar. Eigene Rays, Messungen und deren Farben/Undo bleiben getrennt.

Vor dem Signal werden weder sein Marker noch seine Linien angezeigt. Vor dem tatsächlichen Entry werden dessen Fillkurs, Ausführungsentscheidung und daraus abgeleitete Abstände nicht vorweggenommen. Zukünftige Exitpfade, Gewinne/Verluste und MFE/MAE werden für diese Sichtprüfung überhaupt nicht an den Browser geliefert. Der Anfangsstop ist eine unveränderte Referenzlinie; ein nachgezogener aktiver Exitstop wird hier noch nicht animiert.

## Andere Aktien oder Zeiträume

Unter **Andere Zeiträume lokal berechnen** Start und Ende der Entries wählen. Leer bedeutet die gesamte geeignete verfügbare Historie, mit 400 Tagen Vorlauf als Standard und mindestens 320 Tagen vorhandener Vorgeschichte. Nur eine Aktie pro Auftrag.

Die Berechnung verwendet exakt `event_case_study.scan_episodes`, damit es keinen zweiten abweichenden visuellen Linienfinder gibt. Entryausführung verwendet denselben isolierten nächsten-Open-Vertrag. Die neue gespeicherte Version heißt **Lokale Signalsuche**: Sie untersucht Entries, führt aber nicht automatisch eine neue Exit-/Performance-Studie aus.

Es werden ausschließlich lokale reguläre SIP/split-Datasets verwendet, keine Alpaca- oder sonstigen Providerimporte ausgelöst. Fehlende Historie oder unpassende Daten werden verständlich gemeldet. Der Chart bleibt während der Berechnung bedienbar. Eine Phase/Fortschrittsanzeige und Abbruch sind vorhanden; die reine Geometriephase hat nur groben Fortschritt. Abbruch wird nach dem laufenden Rechenschritt wirksam, bevor neue Fälle veröffentlicht werden.

Nach erfolgreicher Berechnung bleibt die alte Version erhalten und die Ansicht springt zum Ende des neu untersuchten Zeitraums. Der Browser merkt sich einen laufenden Auftrag zur Statusabfrage nach Neuladen. Ein Webserver-Abbruch startet die Suche nicht still unter anderem Code erneut; ohne Heartbeat wird sie nach 90 Sekunden als unterbrochen erkannt. Danach ausdrücklich neu starten. Es läuft höchstens ein solcher Suchauftrag gleichzeitig, ohne wirtschaftliche Depot-/Slotsperren.

## Speicherung, Betrieb und API

Die neuen Tabellen liegen in der bestehenden Datenbank **`TORI_DATA_DIR/research/jobs.sqlite3`**, Schema **5**: `entry_runs`, `entry_cases`, `entry_reviews`, `entry_searches`. Alte Daten werden transaktional ergänzt. Bei einem Update vorhandene Web-/Workerprozesse kontrolliert neu starten, damit keine ältere Anwendung gegen das neuere Schema arbeitet. Der Datenpfad und Zugangsdaten werden nicht verändert.

Die bestehenden konsistenten Backup-/Restorewerkzeuge sichern Fälle und Bewertungen mit. Datasetreferenzen aus Untersuchungen und Suchaufträgen schützen die verwendeten Kursbestände vor einer Einstufung als unreferenziert. Persönliche Browserzeichnungen und die kleinen Projektionsanker bleiben weiterhin Browserspeicher; sie werden dadurch nicht zu serverseitigen Rays.

Vorhandene abgeschlossene Signalstudie explizit registrieren, aus `alpaca-trendlinien/` mit demselben `TORI_DATA_DIR` wie der Dienst:

```powershell
python tools/register_entry_history.py artifacts/event-cases-wide-v2-20261031
```

Die Registrierung prüft Plan-, Fallblock- und Datasetidentität. Die API übernimmt keine beliebigen Dateipfade. Ein erneut registrierter identischer Lauf bleibt derselbe; vorhandene Bewertungen werden erhalten. Die ursprüngliche Engineversion bleibt im Manifest, statt historische Fälle mit dem heutigen Code neu zu zeichnen. Der private Artefaktordner ist nicht Bestandteil von Git; für einen Container die Studie dort berechnen/registrieren oder ein konsistentes Datenbackup verwenden.

Routen:

- `GET /api/entries/runs?symbol=AAPL`: gespeicherte Versionen dieser Aktie.
- `GET /api/entries/cases?run=…&asof=…&offset=0&limit=100`: stabile Seiten, maximal 250 Fälle pro Seite; Familien-/Kontakt-/Ausführungsfilter.
- `GET /api/entries/case?run=…&case=…&asof=…`: ursprüngliche, zeitlich begrenzte Details ohne spätere Ergebnisse.
- `GET /api/entries/chart?run=…&timeframe=4h&asof=…`: manuelle Kerzen aus exakt dem gebundenen Dataset, ohne Neuzeichnung des Linienfinders.
- `POST /api/entries/review`: Bewertung speichern oder mit `delete: true` entfernen.
- `POST /api/entries/search`, `GET /api/entries/search?id=…`, `POST /api/entries/cancel`: eigener ausdrücklicher Offline-Auftrag.

Schreibzugriffe verwenden die vorhandene Host-/Origin-/Tokenprüfung. Kein pauschales Abschalten des Backendschutzes. Ein laufender Suchauftrag ist an den Shared-Enginecode und den Suchadapter gebunden; bei Codeänderung keine stille Veröffentlichung unter derselben Version.

## Durchgeführte Prüfungen und Grenzen

- 69 Versionen der breiten Studie mit 6.668 unveränderten Fällen lokal registriert. Apple 2024 über den Web-Knopf zusätzlich mit 23 Fällen berechnet; keine neue Performancebehauptung daraus.
- Originalfall im Browser ausgewählt, Replay am Signal, späteren Fill zunächst verborgen; Kerzenschritte und Intervallwechsel geprüft. Eigene Testbewertung gespeichert, nach Neuladen wiedergefunden und wieder gelöscht.
- Abbruch einer Microsoft-Suche geprüft: Status `cancelled`, keine neue Version veröffentlicht.
- Reine gespeicherte Fallabfrage lokal etwa 0,01–0,05 Sekunden; warme historische Chartantworten etwa 0,38–0,50 Sekunden in der Stichprobe. Netzwerk/Rendering und erster Dataset-Ladevorgang kommen hinzu. Kein Geschwindigkeitsversprechen für andere Container.
- Vollständige Python-Regression ohne Fehler; zwölf neue Backendtests einschließlich Zukunftsschutz, unveränderlicher Registrierung, Manipulationsprüfung, Originprüfung und echtem Backup/Restore. 81 Chart-/Web-JS-Tests einschließlich elf neuer Prüfungen für diese Ebene bestanden.

Die bisher untersuchten Zeitfenster und das heutige Aktienuniversum sind keine unabhängige Strategiebestätigung. Die Ansicht dient der fachlichen Kontrolle, nicht als neue Orderfunktion. Neue frei gewählte Zeiträume haben ihre eigene Vorlauf-/Episodenhistorie; sie ersetzen nicht rückwirkend die Fallauswahl älterer Studien. Keine GitHub-Publikation oder Containerinstallation durch diese Umsetzung.
# Ergänzung 31.10.2026: Strukturprofile

Unter **Signalauswahl** startet die Ansicht mit qualifizierten Ausbrüchen und roten Retests mit bekannter Safety. Neun Profile erlauben getrennte Vergleiche nach Stopabstand, Tages-SMA200, Kontaktspanne und Verengung. Erweiterte Profile sind experimentell, kein Filter nach späteren Gewinnern; „Alle Rohsignale · Vergleich“ hebt die Strukturfilter auf. Der bestehende Ausführbarkeitsfilter wirkt zusätzlich.

Die API-Routen `GET /api/entries/cases` und `/api/entries/case` akzeptieren optional `quality=all|qualified|risk|trend|mature|convergent|both_qualified|balanced|strict`; ohne Parameter bleibt API-kompatibel `all`. Der Chart setzt den Parameter ausdrücklich. Merkmale stehen am Signalschluss fest, spätere Openkurse oder Gewinne entscheiden keine historische Zulassung. Bei einem Profilwechsel verschwinden ausgeschlossene Marker und Detailzeichnungen. Quelle und ursprüngliche Fall-IDs bleiben unverändert.

Die Liste liefert zusätzlich `screen.profile`, `label`, `beforeProfile`, `excluded` und `experimental`; im gefilterten verfügbaren Detail stehen die bekannten Kriterien unter `screen.features`. Vor dem Signal wird keine Filtergeometrie geliefert; vor dem Fill keine zukünftigen Entrywerte. Ein direkt abgefragter ausgeschlossener Fall hat `state=filtered_out`. Erforderlicher unbekannter Kontext besteht den Filter nicht. Es wird keine Datenbankmigration benötigt. Die erste Datasetprüfung kann einmalig dauern; danach maximal vier Featureversionen im Speicher, kein Providerabruf oder erneuter Signalscan pro Profilwechsel.

[Ergebnisse und Grenzen](SIGNALFILTER-BEWERTUNG-20261031.md). Ein eigener Scanner, der zunächst beobachtet und erst den ersten geeigneten Trigger derselben Episode zulässt, ist noch nicht umgesetzt; die Profile filtern derzeit die ursprüngliche archivierte Fallauswahl.
