# Trendlinien im Chart und Replay

## Beschleunigung vom 31.10.2026

Normale Dataset-Charts und der Zufalls-Replay verwenden jetzt `chart_sources.py`. Beim ersten Zugriff wird der vollständige unveränderliche Bestand mit dem vorhandenen Datasetleser geprüft, einschließlich der 5m-Parquetblöcke. Im Speicher verbleiben nur 1h-/4h-/1D-Chartquellen und Metadaten für höchstens zwei Bestände. Die Chartansicht und der zugehörige Schrittabruf verwenden diese gemeinsam. Bei weiteren Kerzenschritten wird nicht erneut die komplette Ausführungshistorie geladen.

Manifest- und Blockdateien werden vor jedem Zugriff auf Größe, Änderungs-/Erstellungsstand und Dateiidentität geprüft. Änderungen oder fehlende Dateien erzwingen erneute vollständige Prüfung beziehungsweise einen Fehler. Spätestens nach zehn Minuten wird auch ein unveränderter Bestand vollständig nachgeprüft. Dieser Webcache ersetzt weder Prüfsummen noch den strikten Datasetleser der Forschung. Es werden keine ungeprüften neuen Kerzen angehängt. Die Rückgaben sind vom Cache getrennte Listen/Metadaten; Kursobjekte sind unveränderlich.

`chart_lane_cache.py` speichert zusätzlich höchstens 32 reine Quellintervall-Analyseergebnisse bis zusammen 8 MiB **serialisierter** Größe; der tatsächliche Python-RAM-Bedarf enthält zusätzlichen Objektaufwand. Schlüssel enthalten sämtliche verwendeten OHLCV-Kerzen sowie Intervall, Aktie, Modell, Regeln/Gapzustand und relevante Optionen. Eine frühere Kurskorrektur erzeugt auch bei gleicher letzter Kerze einen neuen Schlüssel. Unveränderte Tages-/Wochenintervalle und bereits besuchte historische Zustände werden wiederverwendet. Ausgaben werden vor Verwendung kopiert, damit fixierte Forschungsgeometrien oder spätere Ansichten keinen gespeicherten Zustand verändern.

Die ursprünglichen Berechnungsfunktionen bleiben maßgeblich: keine verkürzte Historie, geänderte Kontaktregel, vorgeschätzte Linie oder Zukunftskerze. Neue bisher nicht besuchte Quellpräfixe werden regulär berechnet. Der erste Aktienaufruf einschließlich Prüfsummen und Kalenderinitialisierung bleibt deshalb teurer. Bereits fixierte Forschungsfälle verwenden weiterhin ihren bisherigen Overlaypfad. Kein neuer Import, Dauerscanner, Hintergrund-Backtest, Datenbankwechsel oder zusätzliche Abhängigkeit.

Lokaler AAPL-Vergleich mit identischen gespeicherten Kursdaten, 4h-Ansicht am 22.10.2024: Rückwärtsschritt bisher 1,90 Sekunden (Legacy) beziehungsweise 1,98 Sekunden (Pine Master), danach 0,45 beziehungsweise 0,35 Sekunden. Bereits besuchter Vorwärtsschritt 1,82 auf 0,30 beziehungsweise 0,24 Sekunden. Der erste kalte Gesamtaufruf blieb rund 4,6 Sekunden. Dies sind Backendmessungen auf dem lokalen Rechner, keine garantierten Container-/Browserzeiten. Sämtliche sechs Vergleichsausgaben stimmen nach Ausklammerung der Erstellungszeit und temporären Analyse-ID vollständig mit den zuvor gespeicherten Referenzen überein. Keine Browserkorrekturen nötig.

Neue Tests prüfen vollständige Inputschlüssel, frühere Kurskorrekturen, getrennte Modelle, Kopierschutz, Speichergrenzen, Ausnahmen, Cacheablauf, geänderte/fehlende Parquetblöcke, Dataset-/Intervallwechsel, exakt abgeschnittene Präfixe und alle drei Fan-Modi gegen die ungespeicherte Berechnung. Der Zukunftsschocktest im Zufallsmodus prüft ausdrücklich den neuen Loader, damit er trotz Cache nicht wirkungslos wird.

Abnahme: 563 Python-Tests ohne Fehler (ein bestehender Skip), 84 JS-Prüfungen bestanden. Lokaler Dienst 8877 ohne allgemeinen Worker neu gestartet. Echte HTTP-Gegenprobe: warmer Dataset-Schritt rund 0,005 Sekunden, folgende analysierte Chartantwort 0,72–0,83 Sekunden einschließlich JSON-Übertragung/-Einlesen im Testclient; Referenzkerzen und -linien identisch. Auf GitHub übergeben; noch nicht im Container installiert.

Stand: 30.10.2026. Dieselbe Bedienung gilt im normalen Chart, bei einem lokal gespeicherten Dataset und unter **Zufall**.

## Bedienung

1. Aktie und Intervall (1h, 4h, 1D oder 1W) wählen. Über **Datum** einen historischen Zeitpunkt auswählen oder einen Zufallsfall öffnen. Datumseingaben und Anzeigen verwenden New Yorker Börsenzeit (ET).
2. **Tori-Analyse: Aus** anklicken. Das ausgewählte Analysemodell berechnet seine Linien ausschließlich aus den bis zum gewählten Zeitpunkt abgeschlossenen Kerzen. Beim Öffnen oder Neuladen bleibt die Analyse zunächst ausgeschaltet.
3. Mit **▶ / ◀** jeweils eine abgeschlossene Kerze im gewählten Intervall vor- oder zurückgehen. Ohne Fixierung gilt **Mitlaufend**: Jede neue Ansicht erhält die zu diesem Zeitpunkt berechneten Linien. Eine neue Kerze muss nicht zwangsläufig neue Anker ergeben; die Regeln des gewählten Modells entscheiden darüber.
4. Bei einem interessanten Stand **Linien jetzt fixieren** anklicken. Der Server speichert den angezeigten Analysezustand und seine Kurspräfixe atomar unter `TORI_DATA_DIR/snapshots/`. Die Anzeige nennt das Fixierungsdatum.
5. Weitere Kerzen zeigen: Die ursprünglichen Anker, Kontakte und historischen Bruchinformationen bleiben erhalten. Die Geraden verlängern sich mit ihrer ursprünglichen Steigung; ihr projizierter Preis an einer späteren Kerze ist deshalb nicht konstant. Es werden keine neuen Linien an die Stelle der fixierten Linien gesetzt.
6. **Fixierung lösen · Mitlaufen** schaltet an der inzwischen erreichten Position wieder auf deren aktuelle Analyse um. Der gespeicherte Stand bleibt im Datumsdialog verfügbar.

Die Pfeile funktionieren auch im normalen Chart ohne eigens geöffneten Replay-Modus. Am Ende der verfügbaren abgeschlossenen Historie erscheint ein Hinweis; es werden keine Kerzen erfunden. Ein Schritt folgt dem gewählten Intervall einschließlich verkürzter Handelstage und Handelspausen.

## Grenzen und Erhaltung eigener Arbeit

- Mit aktiver Fixierung kann die Ansicht nicht vor deren Analysezeitpunkt springen. Sonst würden später bekannte Linien in die Vergangenheit gelangen. Fixierung zuerst lösen, dann zurückgehen.
- Beim bloßen Ausschalten der Analyse bleibt eine aktive Fixierung in der geöffneten Seite erhalten. Sie lässt sich auch ausgeschaltet lösen. Im manuellen Modus werden ihre späteren Daten nicht in eine frühere Ansicht eingeblendet.
- Eigene Linien, Farben und Messungen bleiben separat bearbeitbar. Ein Intervallwechsel ändert das Fixierungsdatum nicht.
- Fixierungen werden nach Aktie, Dataset, Zufallsfall und Analysemodell getrennt. Der Datumsdialog bietet passende Stände an. Einen gespeicherten Zufallsstand im zugehörigen Fall öffnen; neue Zufallsfälle übernehmen keine fremden Linien.
- Bereits archivierte Forschungsfälle behalten ihren Originalsignalstand. Sie werden nicht über diesen Schalter nachträglich umgeschrieben.
- Während des Speicherns sind Schrittwechsel und Modellwechsel gesperrt. Bei einem Speicherfehler bleibt der bisherige Modus nutzbar und eine Fehlermeldung sichtbar.
- MTF-Projektionen sind Zeichnungen. Signale werden weiterhin im jeweiligen Quellintervall berechnet. Manuelles Replay ist kein Nachweis einer profitablen Strategie.

## Technischer Vertrag

Die vorhandenen `/api/chart`, `/api/dataset-chart` und `/api/random/cases/<id>/chart` verarbeiten `analysis=0/1`, `engine` und `asof`. Der Zufallsweg registriert nun auch für den bisherigen Linienfinder eine speicherbare Analyse-ID, nachdem Dataset- und Fallkontext feststehen. Snapshot-Identitäten enthalten diesen Kontext; alte gespeicherte Dateien bleiben lesbar. Die Snapshot-Liste ergänzt `datasetId`, `randomCaseId` und `analysisEngine`. Keine Datenbankmigration und keine Umstellung von Forschungsdefaults oder Zeitplänen.

Automatisierte Abnahme: echte Frontend-Controller-Interaktionen für dynamische Schritte, Fixieren, spätere Kerzen, Intervallwechsel, Aus-/Einschalten und Lösen in allen drei Ansichten; Speicherfehler und konkurrierende Aktionen. Offline-HTTP-Tests prüfen alle vier Linienfinder, alle Intervalle, geschlossene Präfixe, passende Snapshot-Kontexte und unveränderte gespeicherte Stände nach weiteren Schritten. Bestehende Zukunftsschock- und Geometrietests bleiben erhalten.

SMA-Kontextkurven werden auf das vollständige sichtbare Kerzenraster gelegt, mit leeren Punkten außerhalb ihrer bekannten Werte. Das verhindert ein abweichendes Zeitraster bei Lücken oder einem früher endenden fixierten Kontext; zukünftige SMA-Werte werden nicht ergänzt.
