# Einordnung der Vorschläge und Stand der Signalauswahl

## Das wichtigste Ergebnis

Der Ansatz „erst interessante Strukturen eingrenzen, dann deren Entwicklung prüfen“ ist richtig. Die konkrete strenge Kombination aus der Rückmeldung funktioniert in unseren bekannten Daten jedoch nicht als Erfolgsfilter. 206 passende Fälle zu finden ist kein Erfolg, wenn die Ergebnisse anschließend schwächer sind.

Die neun vorab festgelegten Profile wurden auf allen 6.668 Originalfällen aus 69 Aktien untersucht. Entries, Stops, Exitregeln und Episodenherkunft bleiben unverändert. Es gibt keine neue Tagesbegrenzung oder gemeinsame Depot-/Kapitalsperre. [Definitionen und vollständige Ergebnisse](SIGNALFILTER-ERGEBNISSE-20261031.md).

| Auswahl | Signale | Tatsächlich gefüllte Entries |
|---|---:|---:|
| Alle Originalfälle | 6.668 | 6.232 |
| Qualifizierter Ausbruch/Retest mit bekannter Safety-Geometrie | 1.790 | 1.778 |
| Zusätzlich Mindestabstand 1 ATR4h und 2 % am Signal | 1.332 | 1.327 |
| Zusätzlich Tages-SMA200 statt Mindestabstand | 981 | 974 |
| Qualifiziert + Mindestabstand + Tagestrend | 749 | 745 |
| Alle strengen Strukturregeln gemeinsam | 206 | 206 |

Die früher genannten 1.886 qualifizierten roten Rohfälle enthalten 96 Fälle ohne notwendige Safety-Geometrie und ohne Fill. Der neue Ausgangsfilter entfernt diese schon strukturell. Die Signale in der Tabelle zählen Fälle, nicht unabhängige Aktienideen: Ausbruch und Retest derselben Episode bleiben miteinander verbunden.

## Was an den Ideen brauchbar ist

Qualifizierte Ausbrüche und Retests von Bounces und Zweikontakt-Fällen zu trennen bleibt eine sinnvolle fachliche Grundlage. Die übrigen Gruppen werden für Vergleiche aufgehoben, statt ihre Ergebnisse zu löschen.

Stopabstand in Prozent und ATR gleichzeitig sichtbar zu machen hilft bei der Sichtprüfung. Ein Abstand von 1 ATR ist nicht gleichbedeutend mit 2 %. Die vorherigen Tabellen enthielten getrennte Verteilungen, aus denen man keinen bereits bewiesenen gemeinsamen „Sweet Spot“ ableiten kann. Ein Mindestabstand ist eine Hypothese und keine Garantie für einen strukturell besseren Stop.

Linienreife und geometrische Verengung lassen sich reproduzierbar messen. Der Algorithmus verwendet dafür bestätigte Kontaktspannen und die beim Signal bekannte Liniengeometrie. Damit lassen sich subjektive Aussagen am Chart prüfen. Dass eine Formation messbar reifer oder enger ist, beweist aber keine bessere Entwicklung.

## Was die Ergebnisse nicht bestätigen

Die strengen 206 Fälle enthalten 191 Verläufe, die unter allen vier Safety-Modellen geschlossen oder am Datenende offen bewertbar sind. Ihr mittleres Nettoergebnis liegt bei:

| Stopführung | Mittel netto inklusive offener Bewertungen |
|---|---:|
| Ursprüngliche Safety | −1,54 % |
| Bisherige aktuelle Safety | −0,29 % |
| Nur qualifizierte neue Safety | −1,04 % |
| Neue Safety erst ab +2R | −1,16 % |

Das sind Bewertungen gleich großer nominaler Einzelfälle, keine Depotperformance. Fehlende weitere Kursverläufe bleiben unbekannt. Die strenge Kombination wird ausdrücklich nicht als gewinnbringende Strategie übernommen.

Auch „beide Linien müssen schon qualifiziert sein“ und „ältere Linien sind grundsätzlich besser“ werden nicht bestätigt. Die gemeinsame Mindestabstands-/Trend-Auswahl ist mit 749 Fällen übersichtlicher, liefert aber keine eindeutige Verbesserung der Gesamtqualität; Mediane bleiben negativ und wenige größere Gewinner tragen erheblich bei.

Der Tages-SMA200 ist besonders kritisch. Unter den 1.790 zeichnungsfähigen qualifizierten Fällen liegen 981 darüber, 571 nicht darüber und 238 haben keinen sauberen aktuellen SMA-Kontext. Fehlende Daten und ein tatsächlich negativer Trendkontext wurden deshalb getrennt betrachtet. Bei gemeinsam auswertbaren qualifizierten Ausbrüchen erreicht die aktuelle Safety **+0,07 % oberhalb** gegenüber **+1,17 % nicht oberhalb** des SMA200. Bei Retests ist derselbe Vergleich nahezu gleich: +0,55 % gegenüber +0,54 %. Der SMA wirkt in dieser Untersuchung nicht als allgemeiner Qualitätsfilter. Eine mögliche Erklärung ist, dass ein Teil unseres Ansatzes frühe Trendwenden sucht; das bleibt eine Hypothese und rechtfertigt keinen umgekehrten „unter SMA kaufen“-Filter.

## Was im Chart umgesetzt ist

**Historische Einstiege → Signalauswahl** enthält neun auswählbare Profile. Der Chart startet mit der einfachen qualifizierten Ausgangsgruppe. Die 749er-Auswahl und die strenge Kombination bleiben ausdrücklich experimentelle Alternativen. Es gibt keine nachträglich erzeugte „nur Gewinner“-Ansicht.

Ein Profilwechsel aktualisiert Marker und Liste und entfernt ausgeschlossene ausgewählte Linien. Originalgeometrie, Kontakte, Anfangsstop und Replay-Sprung bleiben erhalten; neue Kerzen verändern die gespeicherten Signale nicht. Im Detail stehen Profil, Abstand am Signalschluss und gegebenenfalls Tages-Schluss/SMA200. Vor dem tatsächlichen Fill wird kein zukünftiger Kaufkurs gezeigt. „Alle Rohsignale · Vergleich“ und der bestehende Ausführbarkeitsfilter erlauben die Gegenprobe.

Die Filter funktionieren auf vorhandenen gespeicherten Untersuchungen und neuen lokalen Entriesuchen ohne erneuten Exitbacktest. Die erste Datasetprüfung je Aktie kann kurz dauern; Profilwechsel verwenden einen begrenzten Cache. Es gibt keine neue Datenbank oder automatische Kursabfrage. Persönliche Zeichnungen und automatische Forschung bleiben getrennt.

## Meine zusätzliche wichtigste Beobachtung

Wir filtern hier bereits archivierte **erste** Signale. Wenn ein Rohsignal früh mit zwei Kontakten entsteht und erst später ein wirklich gutes Dreikontakt-Setup derselben Episode vorliegt, kann das spätere Ereignis im bisherigen Episodenfilter schon unterdrückt worden sein. Ein nachträglicher Filter auf die archivierte Liste kann diese Situation nicht zurückholen.

Für die nächste echte Signalsuche ist deshalb ein eigener kausaler Versuch sinnvoll:

1. Eine neue Struktur zunächst nur als Beobachtungskandidat führen; noch keinen Entryplatz der Episode verbrauchen.
2. Pro bestätigtem 4h-Schluss prüfen, ob die vorher festgelegten qualitativen Kriterien **und** ein tatsächlicher Einstiegstrigger erfüllt sind.
3. Den ersten passenden Einstieg einfrieren und diese Familie in dieser Episode anschließend sperren. Kein täglicher neuer Entry, keine nachträgliche Wahl der besten Kerze.
4. Nach einem zu weit gelaufenen Ausbruch den späteren roten Retest derselben Herkunft weiterhin separat zulassen. Ein beliebiger späterer Kursrückgang ist noch kein Retesttrigger.
5. Bestehende Rohsignalvariante als unveränderte Kontrolle behalten. Pro Fall protokollieren, wann er nur beobachtet wurde, warum die Freigabe ausblieb und wann ein echter Trigger erstmals zugelassen wurde.

**Dieser neue Beobachtungs-/Freigabe-Scanner ist noch nicht umgesetzt oder getestet.** Aktuell umgesetzt ist die gemeinsame kausale Filterung vorhandener Ereignisse in Offline-Auswertung und Chart. Das ist für die Sichtprüfung nützlich, ersetzt diesen nächsten Versuch aber nicht.

## Wie ich weiterforschen würde

Zuerst wenige eingefrorene Beispiele blind bewerten: passende und ausgeschlossene Signale, beide roten Entryfamilien und verschiedene Marktphasen. Die Entscheidung festhalten, bevor nachfolgende Kerzen eingeblendet werden. Das vorhandene Bewertungsfeld ist dafür geeignet. Ein menschlich abgelehnter Fall ist nicht automatisch ein finanzieller Verlierer, ein gut aussehendes Dreieck nicht automatisch ein Gewinner.

Danach den oben beschriebenen erstmaligen Freigabeversuch auf einer festgelegten fachlichen Grundlage laufen lassen. Nicht immer weitere Bedingungen stapeln, nur weil eine historische Teilgruppe positiv aussieht. Die vorhandenen Fenster sind bereits bekannt; eine Strategiebestätigung benötigt tatsächlich unangetastete Daten. Costs, Verlustspitzen, Gewinnerkonzentration und unbekannte Pfade müssen erhalten bleiben. Erst danach würden wir einen verbindlichen automatischen Kandidatenscanner aus einer Regelvariante ableiten.

## Prüfung und Betrieb

555 Python-Tests ohne Fehler, ein bestehender Skip; 72 relevante JS-Prüfungen bestanden. Mitgliedschaften, Aggregationen und Quellindizes sämtlicher 6.668 Fälle geprüft; 136 Stichproben zusätzlich mit abgeschnittener Zukunft und unabhängig nachgerechnetem Tages-SMA. Die private 749er-Playlist enthält keine Erfolgs-/Exitdaten.

Lokaler Webdienst auf Port 8877 ausdrücklich ohne allgemeinen Worker neu gestartet, gleicher Datenpfad. Echte API-Prüfung mit AAPL: 26 ausgewählte gegenüber 105 ausführbaren Originalfällen, strenges Profil neun; warmer Profilwechsel rund 0,01 Sekunden, erste kalte Prüfung rund vier Sekunden. Signaldetail am damaligen Schluss zeigt ausstehenden Fill und keine Ergebnisse. DOM-/Controllerinteraktionen sind automatisiert geprüft; keine erneute Browser-Sichtprüfung durchgeführt. Kein GitHub-Upload, Container-Rollout, Providerimport oder Brokerauftrag.
