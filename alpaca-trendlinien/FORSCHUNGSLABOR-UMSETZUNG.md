# Forschungslabor: Auftrag und Abnahme

Auftrag vom 18.10.2026: Den zuvor besprochenen vollständigen Forschungsablauf technisch umsetzen. Zunächst Code und automatisierte Prüfungen; Browserprüfung erst nach vollständiger technischer Umsetzung. Das Labor ist separat wählbar. Bestehende Chart-/Legacy-/Tori-Aufträge bleiben archiviert und unverändert. Keine Orders, keine automatische Veröffentlichung oder Containerinstallation.

## Verbindlicher Umfang

| Nr. | Anforderung | Geplanter Nachweis | Stand |
|---|---|---|---|
| 1 | Verblindete zufällige historische Fallpakete, manuelle Linien-/Entry-Beurteilung, gespeicherte Labels, späterer Vergleich mit Engine; nach Offenlegung als beeinflusst markieren | Review-API/CLI/UI; Tests gegen Zukunftsdaten in Blindantworten | lokal geprüft |
| 2 | Versionierte Regelprofile: technische Voraussetzungen, Einstiegsdefinition, Qualität, Risiko und unbekannte Werte getrennt; unveränderte strenge Referenz | Profilmanifest und Vergleich mit bisherigem Scanner | lokal geprüft |
| 3 | Diagnosefälle einschließlich abgelehnter Kandidaten, alle Kriterienwerte, Ausschlusskombinationen und einzelne verhindernde Kriterien; hypothetische Verläufe deutlich getrennt | Persistente Berichte und synthetische Ablehnungsfälle | lokal geprüft |
| 4 | Ein vollständiger kausaler Ereignisscan je Profil/Aktie; stabile Ereignisse, Deduplizierung und Überlappungs-/Episodenhinweise; Zufallsstartmodus bleibt separat | Ereignis-/Replay-/Schocktests | lokal geprüft |
| 5 | Ausbruch, Horizontalbestätigung und Retest getrennt; optionale alternative Retestbestätigung als vorregistriertes Profil | Familienberichte und unterschiedliche Kerzenanforderungen | lokal geprüft |
| 6 | Reproduzierbare festgelegte Universen, größere Listen, zeitabhängige Mitgliedschaft und Datenabdeckung; kein behaupteter historischer Bestand ohne Quelle | Universumsmanifest/Tests mit IPO/Delisting-Zeitgrenzen | lokal geprüft |
| 7 | Explizite Datenkonventionen: reguläre Sitzungen, 4h-Aufteilung, feinere Ausführungsdaten, Kursbereinigung und fehlende Daten; bestehende Bestände nicht überschreiben | Kalender-/Resampling-/Adapter-/Cachetests | lokal geprüft |
| 8 | Einfache Ausbruchsreferenz, kausal zugeordnete Zufallseinstiege derselben Aktie und optionaler gepinnter Marktvergleich; eigene Stichprobenzahlen | Reproduzierbare Kontrollgruppen, Unterschiedsberichte | lokal geprüft |
| 9 | 5/10/20-Handelstage, Schlusskursänderung, MFE/MAE nach tatsächlichem Entry, Zeitpunkte, initiale Safety-Berührung, R-Bezug und unvollständige Horizonte | Pfadtests einschließlich Entry innerhalb eines Tages | lokal geprüft |
| 10 | Hypothesen/primäre Kennzahl/Varianten vorregistrieren, Versuchsjournal und begrenztes Variantenbudget, gescheiterte Versuche erhalten, Unsicherheit mit Abhängigkeitsgruppen | Unveränderliche Registrierung, Budget-/Bootstraptests | lokal geprüft |
| 11 | Gemeinsame chronologische Entwicklungs-/Validierungs-/Holdout-Grenzen, Sperre von Zukunftslabels, eingefrorener Kandidat, finaler Zugriff protokolliert; Walk-forward mit ausschließlich früheren Auswahlwerten | Split-/Purge-/Seal-/Walk-forward-Leakagetests | lokal geprüft |
| 12 | Kleine versionierte Ausstiegs-/Kosten-/Gap-Simulation; Cash, Stückzahlen, konkurrierende Signale, Positionsgrenzen und Depotverlauf; Hermes kann vorgegebene Untersuchungen steuern/lesen, LLM nicht Signalquelle | Ausführungs-/Portfolio-/CLI-/HTTP-/Wiederaufnahmetests | lokal geprüft |

## Abnahmefolge

1. Rechenkern, Datenverträge, Versionierung und Tests bauen.
2. Queue, Speicherung, Migrationen, Backup/Restore, sichere CLI-/HTTP-Werkzeuge integrieren.
3. Forschungs-/Fallprüfungsoberfläche und Dokumentation vervollständigen.
4. Vollständige Python-/JS-Prüfungen, isolierte Offline-Ende-zu-Ende-Läufe, Abbruch/Wiederaufnahme, Sicherheitsgrenzen und relevante Betriebsszenarien ausführen.
5. Erst danach die fertigen Abläufe im Browser prüfen und reparieren.
6. Anforderungen einzeln gegen tatsächliche Nachweise auditieren. Technisch vorhandene Funktionen sind keine bereits erhobene menschliche Beurteilung oder validierte Strategie. Fehlende Daten/Quellen, leere Gruppen und unvollständige Tests bleiben ausdrücklich sichtbar.

Der Gesamtauftrag wird nicht durch einen kleineren Diagnosemodus ersetzt. Die nachstehende technische Abnahme dokumentiert die Nachweise; die lokale Prüfung ist abgeschlossen. Eine belastbare Marktstudie ist davon getrennt.

## Technischer Zwischenstand vor Browserprüfung · 18.10.2026

Der folgende Zwischenstand wurde vor dem ersten Browseraufruf festgehalten. Die abgeschlossene lokale Abnahme folgt unten; sie ersetzt die damaligen offenen Prüfschritte.

- 1: `lab_reviews.py`, Review-HTTP/CLI und `/lab` mit gespeicherten Zwei-Anker-Linien, Begründung, Blindantwort, expliziter Offenlegung und Beeinflussungsmarkierung. `test_lab_execution_reviews.py` und `test_lab_api.py` prüfen Zukunftsdaten, Speicherung und Zugriffsschutz. Es wurden keine echten menschlichen Beurteilungen erhoben.
- 2/5: `lab_profiles.py`; Tests vergleichen Referenzeinstiege mit `EntryScanner`, alternative Retestbestätigung ohne Lockerung des direkten Ausbruchs und unveränderte gemeinsame Prüfwerte. Unbekannter Raum bleibt unbekannt und blockiert das ausdrücklich dafür gewählte Raumprofil.
- 3/4: `lab_engine.py`, `lab_metrics.py` und Queue-Upserts; reine Diagnose bei fehlender grüner Linie, getrennte hypothetische Ablehnungen, vollständiger kausaler Durchlauf, Profilidentitäten, Episoden und Schock-/Wiederholtests. Phasen spielen auch bereits abgelaufene Setups wieder ab, statt sie durch begrenzten Vorlauf neu zu aktivieren.
- 6/7: Fixierte Listen bzw. Katalogsnapshot, Mitgliedschaftsgrenzen und Herkunft, gemeinsame Phasengrenzen, expliziter Datenabdeckungsfehler bei zu kurzem gemeinsamen Bestand. Kalender-/5m-/4h-/Sommerzeit-/Halbtag-/Lücken-/Feed-/Bereinigungstests. Synthetischer splitähnlicher Rohkurssprung wird markiert; eine neue bereinigte Revision überschreibt den Rohbestand nicht. Kein behaupteter vollständiger historischer Aktienbestand und keine verifizierte Kapitalmaßnahmenrekonstruktion.
- 8/9: Kontrollwahl ohne Verwendung späterer Renditen, fehlende Marktvergleichsuhrzeit bleibt fehlend, getrennte Vergleichszahlen, post-Entry-Pfade, anfängliches Risiko und unvollständige Sitzungen. Die einfache Grundreferenz verwendet dieselbe Tori-Liniengeometrie; keine davon unabhängige Marktstrategie wird behauptet.
- 10/11: Vertrag, Variantenbudget, paginiertes Hashjournal, Fehlversuche, gemeinsame Zeitgrenzen, versiegelter Kandidat, Sperre auch überlappender Holdouts unter anderen Datenrevisionen, vorgelagerte Trainingsauswahl. Beschreibende Unsicherheitsintervalle sind keine vollständige Korrektur aller Marktquerabhängigkeiten oder Mehrfachtests.
- 12: `lab_execution.py`, profil-/familienspezifische Depotsimulationen, Kosten, konservative Intrabarreihenfolge, Gap-Fills, Cash/Stückzahlen/Positionsgrenzen, ungeklärte Datenlücken, HTTP/CLI/Hermes-Vertrag. Speicherung, Wiederaufnahme und Backup/Restore sind geprüft. Bereinigte Preiseinheiten, fehlende historische Originalstückzahlen und fehlende Dividendengutschriften bleiben explizite Modellgrenzen.

### Bisher tatsächlich ausgeführte Prüfungen

- Vollständige Python-Suite: **152 Tests** unter 3.12 und 3.13 erfolgreich, jeweils ein bestehender Windows-Symlinktest übersprungen. Danach vier zusätzliche gezielte Kriterien-/Mitgliedschafts-/Kontroll-/Kapitalmaßnahmenprüfungen: insgesamt **29 Labor-Tests** unter 3.12 erfolgreich. Der nächste Gesamtlauf umfasst diese zusätzlich.
- JavaScript: **27 Tests** erfolgreich; neue Laborprojektionen, Phasentrennung und Markup-Escaping eingeschlossen. JavaScript-Syntaxprüfung erfolgreich. Browser-Rendering noch nicht daraus abgeleitet.
- `tools/verify_lab.py --output artifacts/lab-offline-20261018-a`: kompletter isolierter Offlineablauf mit zwei synthetischen Aktien, jeweils 39.132 5m-, 3.513 Stunden-, 1.003 4h- und 504 Tageskerzen. Entwicklung/Validierung/Abschluss/Walk-forward erfolgreich; erneuter Abschluss erwartungsgemäß verweigert; Beeinflussungsmarkierung und Backup/Restore erhalten. Kein Providerabruf.
- Dieser synthetische Lauf dauerte 68,36 s, Prozessspitze 177.668.096 Bytes (ca. 169,4 MiB), erster Bericht ca. 261,6 ms, Ergebnisseite mit Gesamtkennzahlen 411.539 Bytes. Das ist kein Beleg für Volluniversumskapazität oder Marktrenditen. Ergebnisse liegen ausschließlich im ignorierten lokalen Artefaktordner.
- Vollständige Kursbestände werden in der Queue aktienweise gelesen; die Geometrie wird nur für die aktuelle Kerze zwischen Profilen geteilt. Die Ausführung hält einen begrenzten Quellen-Cache. Es wird nicht das gesamte Universum gleichzeitig als Kerzenobjekte im RAM gehalten.

Die damals offenen Schritte sind in der folgenden Abnahme nachgewiesen. Keine automatische Veröffentlichung, kein Containerupdate.


## Abgeschlossene lokale Abnahme · 18.10.2026

Alle zwölf Tabellenzeilen sind lokal technisch geprüft. Als Beleg dienen die oben je Anforderung benannten Module und gezielten Tests sowie die folgenden vollständigen Läufe. Das bedeutet weder eine erhobene menschliche Vergleichsstichprobe noch eine nachgewiesene Handelsrendite.

- Python 3.12: **158 Tests**, erfolgreich, ein Windows-Symlinktest übersprungen; Python 3.13: ebenfalls **158 Tests**, erfolgreich, derselbe Skip. Darunter 31 gezielte Labortests. Die Gesamtsuiten prüfen auch bestehende Chart-, Legacy-, Tori-, Sicherheits- und Betriebspfade.
- JavaScript: **27 Tests** erfolgreich; Syntaxprüfungen von `static/app.js` und `static/lab.js` erfolgreich.
- Abschließender Offline-Gesamtlauf: `tools/verify_lab.py --output artifacts/lab-offline-20261018-final`. Zwei ausdrücklich synthetische Aktien mit jeweils 39.132 5m-, 3.513 Stunden-, 1.003 4h- und 504 Tageskerzen. Entwicklung 576 Fälle/2.854 Ereignisse; Validierung 678/3.262; reservierter Abschlusstest 268/1.286; Walk-forward 959/4.768. Wiederholter Abschlusstest erwartungsgemäß verweigert. Providerabrufe: **0**. Backup und tatsächliche Wiederherstellung geprüft.
- Ressourcen dieses letzten synthetischen Laufs: 86,97 s insgesamt, Prozessspitze 176.168.960 Bytes (168 MiB), erste Ergebnisseite ca. 339 ms und 411.214 Bytes. Kein Nachweis der Kapazität eines Volluniversums oder eines Proxmox-Containers.
- Der Browser wurde erst nach Code, vollständigen automatisierten Prüfungen und dem ersten Offline-Gesamtlauf verwendet. Im Browser: Formularregistrierung mit gepinnten synthetischen Daten, Queue-Aktualisierung bis Abschluss (192 Fälle/982 Ereignisse), Ergebnisgruppen, Simulationstabelle/Depotkurve, Fallpaket, eigene Zwei-Anker-Linie, Speichern und Wiederladen, explizites Aufdecken und beeinflusste Labels geprüft. Keine echten Handelsentscheidungen als menschliche Labels ausgegeben.
- Browserbefunde korrigiert: Fallchart zunächst auf letzte 120 Kerzen statt winzigen Gesamtvorlauf; vollständiger Vorlauf bleibt wählbar. Auch Zufallsfälle erhalten nach Offenlegung eine ausdrücklich hypothetische Vorwärtsbeobachtung, ohne einen Engine-Trade zu erzeugen. Fallstatus und ausgewählter Auftrag/URL bleiben aktuell. Rohdaten sind eingeklappt. Erstklick mit logischer Chartkoordinate wird berücksichtigt.
- Synthetische Daten tragen jetzt eine unveränderliche Herkunftsmarkierung. Bereits vorhandene explizite Offline-Fixtures werden anhand ihrer Metadaten erkannt, ohne deren Dateien umzuschreiben. Chartkopf, Banner und Statusleiste sowie Fallprüfung nennen deutlich **synthetische Testdaten – keine Börsenkurse**. Tests sichern auch die unveränderte Identität normaler Marktdatasets.
- Manuelle Regression: Forschungsfall im normalen Chart öffnen, ursprüngliche Signallinien, einzelne Kerze vor, Intervallwechsel 4h/1h mit Tageskontext, Hell/Dunkel und Infobox geprüft. Normale Anwendung unter `127.0.0.1:8765` mit gespeichertem echtem AAPL-Dataset geöffnet, keine synthetische Kennzeichnung; Labor meldet Worker bereit. Isolierte Tests nutzen eigenes Datenverzeichnis und Port 8766; kein Testauftrag im normalen Benutzerbestand.
- Bestehender lokaler Datenbestand vor dem Start konsistent gesichert; Schema 4, keine aktiven Altjobs, vorhandener Tageszeitplan unverändert. Lokale Sicherungen und Screenshots liegen ausschließlich unter ignoriertem `artifacts/`; sie werden nicht ins Repository aufgenommen.

### Ausdrückliche Grenzen der Abnahme

Der Referenzscanner bleibt streng; zusätzliche Profile sind Experimente. Keine garantierte Entryzahl. Ereignisstudie, hypothetische Ablehnungsfälle und simulierte Depots bleiben getrennt. Keine Brokerorders. Keine echte Marktstudie aus SYNTHA/SYNTHB ableiten. Datenlücken und fehlende 5m-Pfade werden nicht gefüllt. Historische Universumszusammensetzung braucht eine belegte Quelle; der aktuelle Katalog löst Survivorship Bias nicht. Gemeinsame Prüfzeiträume benötigen genügend überlappende Daten. Bereinigte Preiseinheiten ersetzen keine historische Kapitalmaßnahmen-/Dividendendepotbuchführung. Unsicherheitsintervalle berücksichtigen Symbol-/Quartalsgruppen näherungsweise, nicht jede Marktquerabhängigkeit. EODHD, Benachrichtigungen und Proxmox-Rollout bleiben spätere Arbeit.
