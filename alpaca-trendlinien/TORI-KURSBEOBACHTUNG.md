# Tori: Zufallszeiträume und Kursentwicklung nach dem Einstieg

Stand: 18.10.2026. Lokale Erweiterung auf Basis des optionalen Tori-Einstiegsmodus. Das ist eine historische Ereignisstudie mit Einstiegskriterien, keine vollständige Handels-/Depotsimulation. Die bestehenden Kriterien werden durch spätere Kurse nicht verändert. Es werden keine Orders erzeugt.

## Bedienung

Unter **Forschung → Untersuchungsmodus → Tori-Kriterien · Einstiege und Kursverläufe**:

1. Aktienliste eintragen, beispielsweise die fünf technischen Testtitel aus `deploy/tori-forward.example.json`.
2. Bei **Zeiträume** „Zufällige Zeiträume je Aktie“ wählen. Anzahl, Suchfenster in 4h-Kerzen und Seed einstellen.
3. **Nach dem Einstieg** auf Kursauswertung stellen. Unter Beobachtungsannahmen Horizonte `5, 10, 20` verwenden; diese zählen im Tori-Modus Handelstage. Kostenannahmen sind hier deaktiviert.
4. Linienmodus und Einstiegskriterien wählen. Der Standard verfolgt neue Linien und hält ursprüngliche Setups befristet weiter. Die alternative Fixierung nimmt je Suchfenster nur das am Fensterbeginn bekannte Linienpaar auf.
5. „Einmal untersuchen“ starten. Aufträge, Daten, Parameter und Ergebnisse bleiben lokal gespeichert. Bestehende Zeitpläne werden durch die Formauswahl nicht verändert.

Alternativ ist der gesamte gewählte Zeitraum weiterhin untersuchbar. „Nur Einstiege erfassen“ schaltet die Kursbeobachtung aus. Die bisherige Forschung bleibt ein separater Modus mit unveränderter Auswertung nach 4h-Kerzen. Alte Berichte erhalten keine nachträglich erfundenen Kursbeobachtungen.

## Zufallsverfahren und Auswahl

- Ein Jahr Vorlauf und der reservierte spätere Holdout bleiben bestehen. Optionale Datumsfelder begrenzen die **Einstiegssuche**, nicht den späteren Kursverlauf; dieser darf bis zum Ende des Entwicklungsbestands reichen.
- Fenster werden aus vollständig verfügbaren Suchzeiträumen allein anhand der Zeitachse gewählt. Ein lokaler Zufallsgenerator verwendet Seed, Symbol, Zeitgrenzen, Fensterbreite und Verfahrensversion. Weder spätere Signale noch Kursgewinne beeinflussen die Auswahl. Verschiedene Aktien können verschiedene Kalenderfenster erhalten.
- Kandidaten werden gemischt und nicht überlappende Suchfenster bis zur gewünschten Anzahl aufgenommen. Es handelt sich um ein reproduzierbares Zufallsverfahren, keine gleichgewichtete unabhängige Stichprobe aller möglichen Fensterkombinationen. Platz oder zufällige Anordnung können weniger Fenster ergeben als angefordert; der Bericht nennt die tatsächliche Anzahl. Zu kurze Zeiträume ergeben einen verständlichen Fehler.
- Innerhalb jedes Fensters läuft die bestehende kausale 4h-Engine Kerze für Kerze. Neue Linienpaare ersetzen alte Setups nicht rückwirkend. Jedes Fenster startet mit frischem Setup-Zustand, aber vollständiger vorheriger Linienhistorie; Setups aus früheren Fenstern werden nicht übernommen.
- Für die Kursbeobachtung wird je **Fenster und Einstiegsvariante** der früheste tatsächlich bestätigte Einstieg ausgewählt. Zeitgleiche Ankerpaare bleiben im Prüfprotokoll, werden je Dataset, Variante und Qualitätsgruppe in der Kennzahl nur einmal gezählt. Spätere Einstiege desselben Fensters bleiben als Erkennungen sichtbar, tragen aber keine Kursbeobachtung bei. Dadurch sind Erkennungszahlen und Stichprobengröße ausdrücklich verschieden.
- Ausbruch, horizontale Bestätigung und Retest werden separat untersucht. Ein früher Ausbruch verhindert nicht die Untersuchung des späteren ersten Retests. Die Fixierung ist eine eigene Variante der Linienbehandlung und wird im Auftrag dokumentiert.
- Fenster ohne Linienpaar oder ohne Einstieg bleiben in der Fensterübersicht sichtbar. Pending-/Randfälle zählen nicht als erfolgreiche Einstiege. Datensatz-/Importfehler bleiben pro Aktie erhalten, auch bei teilweise erfolgreichen Aufträgen.

## Was „nach 5 / 10 / 20 Tagen“ bedeutet

Es werden XNYS-Börsensitzungen nach dem **New Yorker Einstiegstag** gezählt: Tag 1 ist die erste Sitzung nach diesem Datum. Wochenenden, Feiertage, Sommerzeit und verkürzte Börsentage folgen dem versionierten Börsenkalender. Die erste verfügbare 1h-Eröffnung nach 4h-Bestätigung und Latenz bleibt die bestehende Einstiegsannahme; auch Vor-/Nachbörsenzeiten können enthalten sein. Die Kursbeobachtung benutzt dagegen Tagesschlusskurse.

Für jeden Horizont:

`Kursänderung in % = (Tagesschlusskurs / beobachteter Einstiegskurs − 1) × 100`

Gespeichert werden Ziel-Handelstag, erwarteter Börsenschluss, tatsächlicher gespeicherter Kerzenschluss, Kurs und Prozentänderung. Die tägliche Hoch-/Tiefspanne wird nicht verwendet, weil der Einstieg innerhalb des Tages liegen kann. Die Kursbeobachtung wählt keinen Exit und berechnet weder Kosten, Stop-Ausführung, Take-Profit, MFE/MAE noch Depot-P/L. Das bestehende `initialStop` ist weiterhin die Safety-Referenz des Einstiegssystems und keine hier ausgeführte Stoporder.

**Datenlücken verschieben den Horizont nicht.** Fehlt eine erwartete Sitzung zwischen Einstieg und Ziel, bleibt die Beobachtung unvollständig und enthält die fehlenden Datumswerte. Reicht der Zieltag in den reservierten Holdout oder über den Entwicklungsbestand hinaus, wird `observation_censored` gespeichert. Es werden keine Holdout-Kurse ergänzt und keine unvollständigen Ergebnisse als null Prozent verbucht.

Alpaca/IEX-Rohkurse sind keine um Dividenden/Splits bereinigte Gesamtrendite. Kapitalmaßnahmen, ein einzelner Handelsplatz, mögliche erweiterte Handelszeiten und das heutige Aktienuniversum bleiben Grenzen. Die aktuelle Dataset-Normalisierung wird nicht stillschweigend umgeschrieben.

## Ergebnisansicht

- Bisherige Tabelle: alle erkannten Linienpaare, Einstiege und Ablehnungen nach Variante/Qualität.
- Neue Tabelle: Median und arithmetischer Mittelwert der Kursänderung je Horizont, Anzahl vollständiger eindeutiger Beobachtungen (`n`), höhere/tiefere/gleiche Schlusskurse sowie unvollständige und zeitlich überlappende Fälle.
- Einzelfälle: Einstiegspreis und -zeit, Zieltag, Schlusskurs und Kursänderung. Die Einzelfalltabelle folgt der aktuellen Ergebnisseite; die Zusammenfassung umfasst den gesamten Auftrag.
- Gesamtzahl eindeutiger Einstiegszeitpunkte über Varianten hinweg. Gruppenzahlen dürfen nicht als unabhängige Trades addiert werden.

Nicht überlappende Suchfenster verhindern keine überlappenden 20-Tage-Beobachtungen. Innerhalb jeder Gruppe werden Überschneidungen derselben Dataset-Zeitachse markiert. Abhängigkeiten zwischen Varianten, verschiedenen Aktien, Dataset-Revisionen oder Qualitätsgruppen bleiben darüber hinaus möglich. Ein positiver späterer Schlusskurs ist keine Strategie-Trefferquote. Ohne Vergleichsbasis und breitere, getrennte Validierung ergibt sich daraus noch kein Vorteil gegenüber dem Markt.

## CLI, Speicherung und Betrieb

```text
tori-tool submit --spec /opt/tori/deploy/tori-forward.example.json
tori-tool report --id <id> --entry-filter entries --limit 50
```

Die Beispielwerte sind Testannahmen, keine optimierten Regeln. Zusätzliche Parameter in `tori`: `sampling: "random" | "full"` (API-Standard `full`) und `observe_forward: true | false` (API-Standard `false`). Die Weboberfläche bietet für neue Tori-Aufträge zunächst Zufallsfenster und Kursbeobachtung an. `samples`, `search_bars` und `seed` steuern die Zufallsfenster; `horizons` steuert bei aktivierter Tori-Kursbeobachtung die Handelstage. Der Legacy-Modus behält seine bisherigen Bedeutungen.

Für eine garantierte Offline-Wiederholung `dataset_ids` je Symbol aus dem ursprünglichen Auftrag übernehmen. Dann sind keine Providerabrufe nötig. Der erste Auftrag ohne gepinnte Daten nutzt die vorhandene Provider-/Cache-Anbindung und archiviert den normalisierten Bestand; ein alter Dataset-Bestand wird nicht überschrieben.

`tori_observations.py` trennt Auswahl und spätere Schlusskursbewertung vom Einstiegsscanner. Aufträge halten Version `tori-forward-closes-1`, Horizonte und Auswahlverfahren im Manifest fest. Fensterplan/Abdeckung und Fälle liegen in der bestehenden SQLite-Datenbank; Schema bleibt 3. Wiederaufnahme berechnet den deterministischen Abschnitt erneut und schreibt stabile Fenster-/Fall-IDs fort, ohne doppelte finale Ergebnisse. Der Engine-Hash enthält das neue Modul; alte unterbrochene Aufträge werden nicht unter neuer Logik fortgesetzt.

Vor lokalem Update wurde ein konsistentes Anwendungsbackup erstellt. Dies ist kein Proxmox-Rollout. Testnachweise stehen in `VERIFICATION.md`.
