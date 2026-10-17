# Long-Kriterien – Diskussionsentwurf 0.1

Stand: 17.10.2026. Dies ist ein Vorschlag für reproduzierbare technische Tests. Die Regeln werden durch diese Datei nicht in der Anwendung aktiviert. Keine Orders. Ausbruch und Retest werden entsprechend deiner Auswahl getrennt ausgewertet.

## Gemeinsame Grundlage

- Signalintervall zunächst 4h, Tageschart als Kontext. 1h dient der Ansicht und erzeugt für diese beiden Tests keine zusätzlichen Einstiegsentscheidungen. Eine 4h-Erholung bei noch fallenden Tageshochs/-tiefs als frühe Trendwende kennzeichnen und von einer Fortsetzung einer bereits steigenden Tagesstruktur unterscheiden. Die rote Linienfarbe allein bestimmt den Tagestrend nicht. Ein Einstieg direkt unter einem bekannten Tageswiderstand braucht ausreichend Raum.
- Nur bis zum jeweiligen Entscheidungszeitpunkt abgeschlossene Kerzen verwenden. Keine Berechnung aus späteren Hochs/Tiefs. Keine Datenwarnung, genügend Rückblick und eindeutige Kurs-/Sessionbasis.
- Die Linien müssen vor dem Ausbruch die bisherigen Dochte respektieren, bestätigt sein und die Kettenregel B → A erfüllen. Mindestens zwei Anker definieren die Linie; die Anwendung nennt sie erst ab drei Kontakten über sieben Kalendertage „qualifiziert“. Nach deiner Auswahl laufen Zwei-Kontakt-Linien als getrennte Testgruppe mit. Ergebnisse dieser Qualitätsgruppen nicht zusammenwerfen. Daraus entstehen A-vorläufig, A-qualifiziert, B-vorläufig und B-qualifiziert. Bei gemischter Qualität von Rot und Grün zählt die schwächere Linie für die Gruppe.
- Am Signal die tatsächlich gebrochene rote Linie und die damalige grüne Schutzlinie samt ihren IDs/Ankern sichern. Eine danach neu gewählte rote Linie ist kein rückwirkender Auslöser. Die gegenwärtige manuelle Fixierung ersetzt noch kein automatisches Signaljournal.
- Für Signale und Abstand zur Schutzlinie die Werte des eigenen Quellintervalls verwenden. Gerade MTF-Überlagerungen sind Chartprojektionen und können andere Schnittpunkte zeigen.

## Variante A: Ausbruch

1. Der vorherige 4h-Schluss liegt auf/unter der zuvor bekannten roten Linie; der neue abgeschlossene 4h-Schluss liegt über ihr.
2. Einen festen Ausbruchspuffer vor dem Test festlegen. Diskussionswert: 0,2 % des roten Linienpreises. Keine nachträgliche Anpassung pro erfolgreichem Beispiel. Testweise zunächst auch ohne zusätzlichen Puffer auswertbar; Varianten klar trennen.
3. Die grüne Schutzlinie liegt unter dem Kurs und wurde von der Signalkerze nicht durchstochen.
4. Signal nach Kerzenschluss; eine simulierte Ausführung erfolgt frühestens zur Eröffnung der nächsten verfügbaren Kerze. Der gerade bekannte Schlusskurs ist kein garantiert erreichbarer Kaufkurs. Bei einer ungünstigen Eröffnung Risiko und verfügbaren Raum neu prüfen; gegebenenfalls auslassen.

## Variante B: Ausbruch mit Retest

1. Derselbe zunächst bestätigte Ausbruch wie bei A; die gebrochene rote Linie festhalten.
2. Erst in einer späteren 4h-Kerze kehrt der Kurs in die Umgebung dieser Linie zurück. Die Ausbruchskerze selbst zählt nicht als ihr eigener Retest.
3. Als eindeutig prüfbarer Diskussionswert: innerhalb der nächsten fünf vorhandenen 4h-Kerzen liegt das Tief innerhalb einer Zone von ±0,2 % um die ursprüngliche rote Projektion und die Kerze schließt wieder über dem oberen Zonenrand. Dies sind Testparameter, keine nachgewiesen optimalen Werte.
4. Ein zwischenzeitlicher Schluss unter dem unteren Zonenrand oder eine Verletzung der grünen Schutzlinie verwirft diesen Retest-Kandidaten. Ohne Rücklauf im festgelegten Fenster gibt es keinen B-Einstieg.
5. Einstieg frühestens zur Eröffnung nach der bestätigten Retest-Kerze; mit derselben Prüfung auf ungünstige Eröffnung wie bei A.

Ein gebrochener Widerstand kann als Unterstützung wirken; das ist die technische Grundidee des Retests, keine Garantie für einen erfolgreichen Verlauf. [Fidelity: Support and resistance](https://www.fidelity.com/learning-center/trading-investing/technical-analysis/support-and-resistance?print=true-0).

## Schutz, Raum und Verwaltung

- Initialen Stop unter der für das Setup maßgeblichen grünen 4h-Schutzlinie festlegen, mit einem vorab definierten Puffer. Den Stop nicht künstlich enger wählen, nur um einen Filter zu bestehen.
- Risikobudget vorab in Geld festlegen. Ganze Aktien = Minimum aus abrundbarem Kapitalbudget/Kaufpreis und Risikobudget/Verlustabstand pro Aktie; Kosten einrechnen. Reicht das Budget nicht für eine Aktie, wird ausgelassen.
- Bekannte Widerstände und Swing-Hochs aus dem damaligen Bestand begrenzen den verfügbaren Raum. Als diskutierbarer Auswahlfilter mindestens etwa 2R bis zur nächsten relevanten Zone verlangen, nach Kosten. Beispiel: Einstieg 100, Stop 97, bekannte Zone 106 ergibt vor Kosten 6/3 = 2R. Dies ist kein automatischer Take-Profit.
- Gemäß deinem ursprünglichen Konzept kein festes Gewinnziel voraussetzen: zunächst im Signalintervall bleiben und ein separates, vorab definiertes Nachziehen anhand bestätigter höherer Zwischentiefs testen. Stop nur nach oben versetzen. Die konkreten Trailing-Regeln gehören noch gemeinsam festgelegt.
- Tatsächliche Stopausführungen können bei Kurslücken schlechter als der Stopkurs sein. [SEC / Investor.gov: Stop orders](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-15). Der Backtest muss diese Ausführung berücksichtigen; unklare Reihenfolgen innerhalb einer OHLC-Kerze markieren oder konservativ behandeln.
- Vor einem späteren echten Einstieg Spread, Handelssitzung, Quartalszahlen und Dividenden-/Kapitalmaßnahmen prüfen. Diese Ereignis- und Ausführungskontrollen sind im jetzigen Chart nicht vollständig automatisiert. Starre Uhrzeitangaben aus dem ursprünglichen Text müssen Feiertage und unterschiedliche Sommerzeitwechsel berücksichtigen.
- Ein simulierter Ausführungskurs muss zur festgelegten Handelssitzung passen. Die nativen 1h-/4h-Aggregate können vor-/nachbörsliche Zeiten enthalten und beginnen nicht zwingend am regulären Sitzungsbeginn. Fehlt ein passender Kurs zur vorgesehenen Ausführung, den Fall als nicht präzise auswertbar kennzeichnen oder ein feineres Ausführungsraster abrufen. Eine reine Zeitstempelverschiebung genügt nicht.
- Den kostenlosen IEX-Datensatz zunächst als technische Testbasis behandeln. Ein Volumenfilter darf IEX-Volumen nicht ungeprüft als Gesamtmarktvolumen interpretieren.

## Auswertung

A und B auf denselben Aktien und Entscheidungszeitpunkten vergleichen. Jede Variante als eigene Simulation führen; nicht beide Einstiege als unabhängige Trades im selben Portfolio aufsummieren. Vorläufige und qualifizierte Linien getrennt kennzeichnen. Neben Treffern auch Fehlversuche, ausgelassene Kandidaten, Kosten, Haltedauer und maximalen Rückgang erfassen. Kein nachträgliches Auswählen nur der gelungenen Ausbrüche.

Noch festzulegen: endgültige Puffer/Zeitfenster, Risikobudget, Definition des nächsten relevanten Widerstands und die vollständige Trailing-/Ausstiegsregel. Zwei-Kontakt-Linien und die getrennte Prüfung beider Einstiegsvarianten sind als Testumfang bestätigt.
