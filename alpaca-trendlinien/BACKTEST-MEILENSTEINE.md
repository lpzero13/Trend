# Backtest-Roadmap: Signale, Ausstiege und automatisierte Beobachtung

**Fortsetzung 31.10.2026 umgesetzt:** [Signalepisoden ohne gemeinsames Kapital-/Slotlimit und ohne Zeitexit](SIGNALFALLSTUDIE.md), [Ergebnisse](SIGNALFALL-ERGEBNISSE-20261031.md), [Einordnung](SIGNALFALL-BEWERTUNG-20261031.md). 69 Aktien, vier bekannte Entryfenster, 6.668 Fälle mit struktureller Deduplizierung. Neues isoliertes Forschungsinterface; ältere Depotverträge nicht umgestellt. M4 um regelbasierte unbegrenzte Einzelfallpfade erweitert; M5-Daten-/unabhängige Validierungsfragen bleiben offen. Die folgenden Meilensteine beschreiben auch frühere Studien, die dieser neuen Priorität nachgeordnet sind.

Planungsstand: **30.10.2026**. Grundlage ist das gemeinsam besprochene Backtest-Konzept nach der Chart-/Replay-Fixierung.

**Status: Technischer Pilot und Mehraktien-Simulation umgesetzt; breite Daten-/Strategiefreigabe offen.** Der [MSFT-Pilot](BACKTEST-PILOT.md) wurde um Mehraktien-Studien und eine [feste Robustheitsprüfung auf 69 archivierten Aktien](ROBUSTHEITSPLAN-20261030.md) erweitert. Ein positives Modellresultat ist keine bestätigte profitable Strategie. Diese Roadmap startet selbst keine weiteren Läufe.

**Technischer Ausbau am selben Tag:** [Vorab festgelegte Mehraktien-Studien und Ergebnisse](STRATEGIE-SUCHE-ERGEBNISSE-20261030.md). 48 Aktien-/Zeitfenster, drei Entry-Familien, getrennte Entwicklung/Prüfung, 60 begrenzte Auswahlvarianten und gemeinsames endliches Kapitalbuch technisch erprobt. Positive Kandidaten, aber kein bestandenes vollständiges Kontrolltor. Auf Nutzerwunsch weiterhin technische Forschung vor Web-/Optikausbau; keine neue UI vorgesehen.

**Weitere feste Robustheitsrunde:** [69 Aktien, vier Zeitfenster und offene Daten-/Ausführungsgrenzen](ROBUSTHEITSERGEBNISSE-20261030.md). 204 Kapitalbücher separat geprüft. [Signaljournal](SIGNALJOURNAL.md) als technische M7-Vorbereitung, kein neuer Daemon.

**Ergänzender Strategie-Abgleich, 30.10.2026:** [Zusammenfassung, Einstiegsfamilien, Fächer-Trailing und offene Definitionen](BACKTEST-STRATEGIE-ABGLEICH-20261030.md). Die neue Vorlage ergänzt diesen Plan; festgestellte Unterschiede zum aktuellen Code sind dort dokumentiert und noch nicht umgesetzt.

**Entry-/Exit-Diagnose:** [Alle sieben Entry-/Kontaktgruppen und drei gespeicherte Exits](ENTRY-EXIT-ERGEBNISSE-20261030.md), 168 Depotvarianten, gemeinsamer Fallvergleich und vollständige Status-/CSV-Ausgaben. Bekannte Daten, keine neue Auswahl oder M5-Freigabe.

**Isolierte Exit-Folgeprüfung:** [Hard/4h-Close und 40/80 Tage](EXIT-FORSCHUNGSERGEBNISSE-20261030.md) auf 4.076 unveränderten qualifizierten Entries, 192 Depotbücher und zwölf Konzentrationsdiagnosen. 34 gezielte historische Datenabfragen liefern keine Reparatur der gewählten Lücken. M4 erweitert, M0/M5-Daten- und Validierungsfragen weiterhin offen.

## Ziel und Erfolgskriterium

Möglichst viele brauchbare Long-Gelegenheiten nachvollziehbar erkennen, ihre anschließende Entwicklung untersuchen und daraus eine nach Kosten tragfähige Handelsweise prüfen. Die Signalzahl wird gemeinsam mit Qualität, Risiko, Kapitalbindung und Robustheit bewertet. Eine hohe Trefferquote oder ein positives Ergebnis auf bekannten Daten allein ist kein Abschlusskriterium.

Langfristig soll Hermes interessante Aktien frühzeitig zur manuellen Prüfung hervorheben können. Signalerkennung, Einzelfall-Ausführung und gemeinsame Depotbewertung bleiben unterscheidbar. Keine Brokerorders vorgesehen.

## Vorhandene Grundlagen

- Manueller Chart und Zufalls-Replay mit zuschaltbarer Analyse, Kerzenschritten und archivierten Fixierungen.
- Gemeinsame kausale Quellberechnung für Chart und Headless; Pine-Master-Profil `fan_master` ist vorhanden.
- Beobachter für Linienepisoden, Ausbruch und roten Retest; ursprüngliche Geometrie und Safety können am Signal gebunden werden.
- Ausführungsbausteine für reguläre 5-Minuten-Kerzen, Kosten, Stückzahl, Stop und Beobachtungshorizonte.
- Parquet-Kursbestände, unveränderliche Dataset-IDs, Forschungsqueue, Checkpoints und Ereignisjournal.
- Zuletzt bestätigter Langzeitimport: 69 fertige Aktien im pausierten 100er-Auftrag, angefragter Zeitraum ab 2016 bis 29.10.2026. Tatsächlicher Beginn, Lücken und Eignung unterscheiden sich je Aktie. Weitere lokale Bestände und Versionen sind nicht automatisch zusätzliche unabhängige Aktien.

Siehe [Fächer-Vertrag](TORI-FAECHER.md), [Master-Profil](TORI-MASTER-UPDATE-20261029.md), [Chart-Fixierung](CHART-REPLAY-FIXIERUNG.md) und [Sammler-Ergebnisse](SAMMLER-V2-ERGEBNISSE.md).

## Reihenfolge und abnehmbare Ergebnisse

### M0 – Datenbasis und Versuch vorab festlegen

**Status: Expliziter Versuchsvertrag mit 69 Dataset-IDs und vier Zeitfenstern umgesetzt. Historische Datenlücken, Split-/Ganzaktien-Abgleich und unabhängige/prospektive Bestätigung bleiben offen.**

- Die vorhandenen Langzeitbestände inventarisieren: Dataset-ID, Symbol, Feed, Bereinigung, Zeitspanne, Lücken und verfügbare Intervalle. Zunächst keine neuen Großimporte.
- Für den Hauptversuch einen einheitlichen SIP-/Split-Bestand verwenden; alternative Feeds, synthetische Technikdaten und doppelte Versionen getrennt halten.
- Warm-up und tatsächlich auswertbaren Zeitraum je Aktie ausweisen. Kurze Historien nicht künstlich verlängern und nicht alle Titel auf die kürzeste gemeinsame Historie beschränken.
- Bereits untersuchte Daten mit bisherigen Forschungsberichten abgleichen. Entwicklungs-, Prüf- und gegebenenfalls noch unberührte Zeit-/Aktienblöcke vorab bestimmen. Bekannte Daten werden durch eine neue Bezeichnung nicht zum unberührten Holdout.
- Codeversion, Parameter, Dataset-Manifest, Kalender und Ausführungsannahmen festhalten; den reservierten Bereich auch bei Ergebniswegen zeitlich abschirmen.
- Vor dem Test die offenen Definitionen im Strategie-Abgleich entscheiden: Körper-/Kontaktabstände, Wartefenster, Safety am späteren Entry, Bounce-Grenzen, Close-Stop und zeitliche Wirksamkeit neuer Stops. Keine pauschale Eins-zu-eins-Übereinstimmung von Vorlage und aktuellem Master-Code behaupten.

**Abnahme:** prüfbares Daten-/Versuchsmanifest und dokumentierte Grenzen. Heutige Indexmitglieder bilden kein historisch vollständiges Universum einschließlich ausgeschiedener Unternehmen.

### M1 – Vollständiger kausaler 4h-Signalscan

**Status: Kausaler Scan für den Pilot und Mehraktien-Studien umgesetzt; zusätzlicher Lauf über 276 angefragte Aktien-/Zeitfenster, davon 266 mit ausreichender Vorgeschichte/Entry-Abdeckung. Keine vollständige Live-Scanner-Abnahme.**

- Alle freigegebenen abgeschlossenen 4h-Kerzen chronologisch durchlaufen. Zufallsstarts ergänzen die visuelle Kontrolle, ersetzen aber nicht die vollständige Signalsuche.
- 1D und 1W zunächst als jeweils schon verfügbaren Kontext erfassen; 5m für die spätere Ausführung verwenden. Keine zukünftigen Tages-/Wochenabschlüsse oder noch unbestätigten Pivots vorziehen.
- Bekannte Linien als versionierte Episoden weiterverfolgen. Neue aktuelle Linien dürfen ältere noch gültige Situationen nicht stillschweigend löschen.
- Ursprünglichen roten Widerstand und damals verfügbare Safety beim Ausbruch binden; Retests gegen diese ursprüngliche rote Linie untersuchen.
- Rohereignisse, ungültige Situationen, Datenlücken und tatsächlich ausführbare Signale unterscheidbar protokollieren. Überlappende Linien desselben Marktgeschehens zusammenführen; Herkunft erhalten.

**Abnahme:** wiederholbarer Signalkatalog mit Replay-Links zum Originalstand. Präfixtests und Veränderungen ausschließlich zukünftiger Daten dürfen frühere Entscheidungen nicht ändern.

### M2 – Einstiegsgruppen und Merkmale vergleichen

**Status: Drei Hauptfamilien und 60 begrenzte Varianten verglichen. Für die neue Robustheitsrunde nur die vorher festgelegte Ausbruch-Hypothese, keine Neuauswahl auf Prüfdaten. Weitere Merkmalsforschung bleibt möglich.**

Zunächst das Master-Modell als gemeinsame Grundlage verwenden:

| Gruppe | Einstieg | Kontaktklasse |
|---|---|---|
| A | Bestätigter Ausbruch | Zwei Kontakte |
| B | Bestätigter Ausbruch | Mindestens drei Kontakte |
| C | Bestätigter Ausbruch, danach roter Retest mit Bestätigung | Zwei Kontakte |
| D | Bestätigter Ausbruch, danach roter Retest mit Bestätigung | Mindestens drei Kontakte |

Alter, Abstand und Reaktionsqualität der Kontakte zusätzlich ausweisen; drei junge Kontakte nicht pauschal als vollständig qualifiziert bezeichnen. Ausbruch und Retest derselben Episode sind alternative Forschungsgruppen, keine unabhängigen Depotpositionen.

Ergänzung aus der neuen Vorlage: innerhalb der Ausbruchsfamilie sofort sauberen und erst verzögert sauberen Schluss separat kennzeichnen. Den Retest der gebrochenen roten Linie von einem Safety-Rücksetzer nach Ausbruch unterscheiden. Ein eigenständiger A+-Safety-Bounce ohne vorausgesetzten roten Bruch ist eine zusätzliche Einstiegsfamilie. Die A–D-Tabelle beschreibt die ursprüngliche erste Ausbaustufe, nicht bereits alle neu vorgeschlagenen Gruppen. Definitionen und stufenweise Einordnung stehen im verlinkten Strategie-Abgleich.

Merkmale zunächst speichern statt sofort hart filtern: Safety-Distanz, Ausbruchsstärke relativ zum ATR, Linienalter, getrennte Reaktionen, Tages-/Wochenkontext sowie Retestdauer und -tiefe. Vorab bestehende Modellparameter dokumentieren. Ergebnisbasierte neue Filter nur im Entwicklungsbereich erarbeiten.

**Abnahme:** nachvollziehbare Gruppen- und Merkmalsübersicht einschließlich Signalhäufigkeit, Verwerfungen und gemeinsamem Ursprung. Kein Erzwingen einer Mindestzahl durch nachträgliches Aufweichen.

### M3 – Entwicklung nach dem Einstieg messen

**Status: 5/10/20/40-Tage-Messungen im Pilot und 20-/40-Tage-Vergleiche auf mehreren Aktien vorhanden. Breiter 40-Tage-Lauf technisch umgesetzt; unvollständige Pfade bleiben unvollständig.**

- Nach 5, 10, 20 und ergänzend 40 Handelstagen Schlussentwicklung messen; diese Horizonte sind Versuchsannahmen.
- Höchsten zwischenzeitlichen Gewinn und größten Rückgang, Stopberührung, Reihenfolge und Wartezeiten erfassen.
- Prozentwerte und R ausweisen: ein R bezeichnet das dokumentierte anfängliche Preisrisiko zwischen tatsächlichem Einstieg und Stop. Nettobeträge berücksichtigen zusätzlich die Ausführungskosten.
- Eine spätere Kurserholung nach bereits ausgelöstem Stop nicht als gewonnenen Handel ausgeben. Preisbeobachtung und ausgeführter Handel bleiben getrennte Ergebnisse.
- Am Daten-/Phasenende unvollständige Fälle offen ausweisen. Unterschiedliche Horizonte desselben Einstiegs nicht als unabhängige zusätzliche Trades zählen.

**Abnahme:** Verlaufstabelle und visuell prüfbare Fälle, einschließlich Fehlsignalen und unklarer Pfade. Noch keine gemeinsame Depotperformance behaupten.

### M4 – Wenige Exitmodelle auf identischen Einstiegen testen

**Status: Feste und geometrische Stops mit Hard-/4h-Close-Auslösung sowie 40-/80-Tage-Grenze auf 69 Aktien und zwei qualifizierten Entry-Familien geprüft. 0,3-Prozent-Ratchet-Vertrag; keine Gleichsetzung mit Safety-minus-ATR. Weitere Modelle/Originalregelabnahme und unabhängige Validierung offen.**

| Variante | Vorab festgelegte Auslegung |
|---|---|
| Referenz | Ursprünglicher Stop; ansonsten Ausstieg nach festem Zeitraum |
| Gewinnziel | Ursprünglicher Stop plus festes Ziel, beispielsweise 2R |
| Trendfolge | Ursprünglicher Stop, später nur unter bestätigten höheren Tiefs nachziehen |

Exakte Zeiträume, Zielwerte, Puffer und Wirksamkeitszeitpunkte vor dem Vergleich festlegen. Das Beispiel 2R ist keine validierte Regel. Keine umfangreiche nachträgliche Suche nach dem schönsten Zielwert.

Die neue Vorlage priorisiert Trendfolge ohne festes Gewinnziel. Dafür zusätzlich die Fortschreibung derselben ursprünglichen Safety und den Wechsel auf neue bestätigte Fächer-Safetys als eigene Varianten planen; beides ist nicht gleich dem vorhandenen Higher-Low-Pivot-Stop. Hard-Stop und Quellkerzen-Close-Stop benötigen getrennte eindeutige Verträge. Erst Referenz und geometrisches Nachziehen prüfen, dann gezielt Varianten ergänzen; nicht sofort sämtliche Kombinationen optimieren. Teilverkäufe, SMA200-Filter und Zeitstopp bleiben optionale spätere Experimente.

Ausführung: Signal erst nach Kerzenschluss, Einstieg am nächsten erwarteten regulären 5m-Open nach der dokumentierten Reaktionszeit; Gebühren, Spread und Slippage modellieren. Stop-Gaps am ungünstigeren verfügbaren Kurs behandeln. Bei Stop und Ziel innerhalb derselben 5m-Kerze bleibt die Reihenfolge unbekannt: konservative Annahme und Umfang der Mehrdeutigkeit ausweisen. Fehlende erwartete Kerzen nicht durch bequemere spätere Kurse ersetzen.

**Abnahme:** Vergleich auf denselben zugrunde liegenden Signalen, mit ausgeführten, abgelehnten, offenen und nicht auswertbaren Fällen sowie Kostenempfindlichkeit. Einzelfall-Simulation bleibt vom Depot getrennt.

### M5 – Robustheit und unabhängige Prüfung

**Status: Zeit-, Kosten- und Korbprüfungen auf 69 Aktien technisch durchgeführt. Zwei Gesamtfenster positiv vollständig, zwei datenbedingt unvollständig; alle Kontrollvergleiche unvollständig. Gesamtes Prüftor nicht bestanden. Konkrete Datenprüfung und unabhängige/prospektive Bestätigung offen.**

- Entwicklung von zeitlich späterer Prüfung trennen; soweit der Datenstand es erlaubt, mehrere rollierende Trainings-/Prüfblöcke und zusätzlich andere Aktien untersuchen.
- Verwendete Varianten und Parameteränderungen protokollieren. Den abschließenden reservierten Bereich erst nach Festlegung einer Variante öffnen und nicht zur laufenden Optimierung verwenden.
- Ergebnisse nach Aktie, Jahr, Marktphase und Sektor aufschlüsseln; Konzentration auf wenige Gewinner sichtbar machen.
- Zufällige Long-Einstiege als Kontrollgruppe in vergleichbaren Aktien/Zeiträumen mit denselben Ausführungs- und Exitregeln vergleichen. Zufallsauswahl und Wiederholungen vorab festlegen.
- Moderate Änderungen von Kosten und Parametern prüfen. Abhängige/überlappende Fälle nicht wie unabhängige Stichproben behandeln; Unsicherheit beispielsweise nach Zeit- und Aktiengruppen auswerten.

**Abnahme:** belegte Stärken, Schwächen und Unsicherheit auf getrennten Prüfdaten. Ein negatives oder unentschiedenes Ergebnis ist zulässig; kein Anspruch auf Profitabilität allein aus einem positiven Entwicklungsdurchlauf.

### M6 – Gemeinsames Depot simulieren

**Status: Gemeinsames Cash-/Risikobuch für acht/16 Aktien geprüft und auf den festen 69er-Versuch erweitert. Historisch exakte Ganzaktien-Ausführbarkeit ist bei splitbereinigten Kursen ohne Splitfaktoren nicht abschließend belegt. Keine Strategiefreigabe.**

- Endliches Anfangskapital, Positionsrisiko, maximale gleichzeitige Positionen und Gesamtrisiko festlegen.
- Bei gleichzeitig auftretenden Signalen ausschließlich damals bekannte Informationen zur Auswahl verwenden. Alternative Linien/Modelle derselben Episode nicht mehrfach kaufen.
- Kapitalbindung, Kosten, realisierte und offene Gewinne/Verluste, Drawdown, Verlustphasen und nicht finanzierbare Signale erfassen.
- Ganze Stückzahlen beziehungsweise eine ausdrücklich gewählte Bruchstückannahme beachten. Ein wegen Budget oder Mindeststückzahl nicht ausführbares Signal bleibt im Signalkatalog sichtbar.
- Das frühere Beispiel von 2.000 Euro erfordert eine klare Währungsentscheidung: entweder ein ausdrücklich benanntes USD-Modell oder eine nachvollziehbare EUR-/FX-Auslegung. Euro und Dollar nicht stillschweigend gleichsetzen.

**Abnahme:** überprüfbares gemeinsames Kapital-/Positionsbuch und Nettobewertung der festgelegten Strategie. Nicht die hypothetischen Erträge vieler jeweils separat voll finanzierter Einzelfälle addieren.

### M7 – Prospektiv beobachten und Hermes vorbereiten

**Status: [Versionsgebundenes Signaljournal](SIGNALJOURNAL.md) mit Einzelschritten, eingefrorenen Signalen, transaktionaler Wiederaufnahme, Dataset-Präfixprüfung und Backup/Restore umgesetzt. Prospektiver Dauerbetrieb, neue Datenversorgung und Ergebnisbilanz bleiben offen.**

- Unveränderte Regeln auf neu eintreffende Daten anwenden; Signale vor Bekanntwerden ihres Ergebnisses speichern.
- Zustände wie Beobachtung, Annäherung, bestätigter Ausbruch und bestätigter Retest ausgeben, mit Originalgeometrie, Risiko und Chartlink.
- Dauerbetrieb, Abschlusszeiten, Wiederaufnahme, Deduplizierung und technische Überwachung abnehmen.
- Hermes kann Kandidaten zur manuellen Prüfung aufbereiten. Zustellweg, Zeitplan und Containerbetrieb bei späterer Umsetzung ausdrücklich festlegen; diese Roadmap richtet nichts davon ein.

**Abnahme:** technisch belastbare, nachvollziehbare Kandidatenbeobachtung. Die Entscheidung über weitere Automatisierung folgt aus den Ergebnissen, nicht aus der Existenz einer funktionierenden Oberfläche.

## Nächster Schritt bei einer späteren Umsetzung

Aktuelle Nutzerpriorität ist die technische Forschung, nicht die Webansicht. Nach den dokumentierten Mehraktien-Runden die unveränderte Kandidatenhypothese, reale Kosten und neue unabhängige/prospektive Beobachtung weiter prüfen; bereits betrachtete Prüfblöcke nicht erneut als unberührt verwenden. Der erste 69er-Daten-/Versuchsvertrag von **M0** steht; Datenlücken und historische Ausführbarkeit benötigen weitere Klärung. Vorhandene Module gezielt erweitern und separat abnehmen; manuellen Chart, Replay und bestehende Forschungsinterfaces erhalten. Nach jedem Meilenstein festhalten: Was wurde umgesetzt, welche Daten wurden tatsächlich ausgewertet, was hat funktioniert, welche Grenzen bleiben und ist der nächste Schritt begründet?

Der pausierte Sammelauftrag bleibt erhalten und pausiert. Diese Planung ist weder eine Aufforderung zur Wiederaufnahme noch zum Veröffentlichen oder Deployen neuer Änderungen.
