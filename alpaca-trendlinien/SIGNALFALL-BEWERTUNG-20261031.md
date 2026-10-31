# Einordnung der neuen Signalstudie

**31.10.2026 – Lauf abgeschlossen und technisch geprüft.** [Vollständige Tabellen](SIGNALFALL-ERGEBNISSE-20261031.md), [Definition und Aufruf](SIGNALFALLSTUDIE.md).

## Was jetzt erreicht ist

69 vorhandene Aktien, Entryfenster 2018, 2021, 2023 und April 2025 bis März 2026; alle entstandenen Positionen bis zum Stop oder tatsächlichen Importende am 29.10.2026, 15:25 UTC, beobachtet. Keine Zeitexits und keine gemeinsamen Geld-/Slotsperren. 6.668 Entryfälle aus 4.614 strukturellen Episoden; 10.218 Wiederholungs-/Alternativsignale derselben Struktur und Entryfamilie unterdrückt. Zehn Aktien-/Fensterkombinationen haben nicht genug Vorgeschichte.

6.232 tatsächliche simulierte Entries; 360 Signale ohne gültigen Anfangsstop, 75 wegen Open unter Stop abgesagt, ein erwarteter Entry-Open fehlt. Diese 436 Fälle werden nicht als Trades mit erfundenem Kurs verbucht. Ausbruch und Retest derselben Episode sowie drei Exitvarianten zählen nicht als unabhängige neue Dreiecke.

Die Fallbildung ist bewusst strenger als bloßes Deduplizieren technischer Linien-IDs. Ihre Übereinstimmung mit menschlich als neu empfundenen Setups muss trotzdem noch anhand gespeicherter Beispiele geprüft werden. Die Studie untersucht nur die bereits implementierten Entrydefinitionen und drei klar definierte Hard-Stop-Regeln; sie bestätigt nicht automatisch jede subjektive Tori-Regel.

## Was die Ergebnisse sagen

Mit **jeweils aktueller gültiger Safety** ergeben sich bei qualifizierten Linien:

| Entry | Abgeschlossene Fälle | Trefferquote geschlossen | Mittel netto je Fall | Median netto je Fall |
|---|---:|---:|---:|---:|
| Ausbruch | 1.045 | 40,0 % | +0,60 % | −0,74 % |
| Roter Retest | 695 | 37,4 % | +0,47 % | −0,71 % |
| Safety-Bounce | 1.026 | 28,7 % | +0,09 % | −0,86 % |

Das sind Einzelpositionsergebnisse bei gleichem nominalen Einsatz, keine Depotprozente. Weitere 29/9/10 gefüllte qualifizierte Fälle sind bei diesen drei Gruppen durch fehlende Pfade zensiert. Es gab dort keine am Datenende noch offenen aktuellen-Safety-Fälle. Unausführbare Signale sind nicht im Nenner der Trefferquote.

**Es gibt einen positiven historischen Forschungsbefund, aber noch keine belastbare fertige Handelsstrategie.** Die Mehrzahl der Trades verliert. Gewinne sind im Durchschnitt groß genug, um diese Verluste in zwei interessanteren Gruppen leicht zu überkompensieren. Deshalb wären Aussagen wie „die meisten Signale sind gut“ oder „wir haben jetzt eine hohe Trefferquote“ falsch.

Ausbrüche mit aktueller Safety haben in allen vier bekannten Fenstern einen positiven mittleren Prozentwert; 2018 ist der mittlere R-Wert allerdings nahezu null. Qualifizierte Retests sind 2018 im Prozentmittel leicht negativ. Bekannte Daten, Zensierung und abhängige Aktien/Marktphasen verhindern eine unabhängige Robustheitsbestätigung.

Bei doppelten variablen Kosten bleiben Ausbruch und Retest mit aktueller Safety im Mittel bei etwa +0,45 % und +0,32 %. Der Bounce fällt auf −0,06 %. Das spricht gegen eine Gleichbehandlung aller drei Familien. Kontaktklasse „zwei“ bleibt mitgeführt und getrennt; es wird aus diesem Lauf kein neuer harter Qualitätsfilter abgeleitet.

Ohne die jeweils besten drei abgeschlossenen Fälle bleiben Ausbruch und Retest mit aktueller Safety durchschnittlich bei +0,41 % und +0,22 %. Positive Beiträge verteilen sich über mehrere Aktien; die größte Aktie trägt etwa 6,0 % beziehungsweise 8,6 % der positiven nominalen Beiträge. Das ist ermutigender als ein Ergebnis, das ausschließlich von drei Gewinnen lebt, aber weiterhin eine nachträgliche Beschreibung derselben bekannten Stichprobe.

Die ursprüngliche Safety ist insgesamt schwächer und lässt einige sehr große Gewinner offen. Aktuelle Safety schließt schneller; Median der Haltedauer bei qualifizierten Ausbrüchen etwa 6,85 Kalendertage, Retests 6 Tage, Bounce 3,83 Tage. Diese Dauern sind **Resultate der Exitregel**, keine neu eingeführten Zeitlimits. Gemeinsame geschlossene Fälle werden im Bericht zusätzlich paarweise verglichen.

Der feste Kontrollstop hat ausschließlich Verlustabschlüsse und 561 noch offene Fälle über alle Kontaktklassen. Ohne Gewinnexit ist das konstruktionsbedingt. Offene positive Markierungen dürfen weder als realisierte Gewinne noch als Beleg schlechter Signale verschwinden. Auch bei nachziehenden Hard-Stops können Kursgaps Verluste jenseits von −1R verursachen.

## Technische Bilanz

- 18.696 Pfade gefüllter Entries auf Identitäten, Kosten und kausale Stopaktivierung geprüft; 408 zusätzliche Pfade unabhängig Kerze für Kerze nachgerechnet.
- AAPL-Pilot: 20 Fälle, alle 60 Varianten nachgerechnet und Signale/Episoden ohne zukünftige Kerzen unverändert reproduziert.
- 20.004 CSV-Zeilen einschließlich nicht ausführbarer Statusfälle separat aggregiert; Statuszähler, Mittelwerte und Mediane stimmen in allen 15 beobachteten Gruppen mit dem Ergebnis überein.
- Wiederaufnahme aller 69 vollständigen Aktienblöcke ohne Neuberechnung geprüft. Code-/Plan-/Blockänderungen werden abgewiesen; unvollständige Aktienblöcke sind erneut berechenbar.
- 526 Python-Tests ohne Fehler durchlaufen, davon ein bestehender Skip; 70 Chart-/Web-JS-Tests bestanden. 17 neue Tests für diesen Modus.
- Ein Fehler beim Journalisieren der Geometrie-Neuinitialisierung nach einer Lücke wurde gefunden, behoben und mit Regressionstest abgesichert. Der erste breite Versuch und der erste Pilot bleiben archiviert. Fertiger Lauf und Wiederholungspilot liegen getrennt unter `artifacts/event-cases-wide-v2-20261031` und `artifacts/event-cases-pilot-v2-20261031`.

## Sinnvolle nächste Schritte, noch nicht umgesetzt

1. Repräsentative Gewinner, Verlierer und unterdrückte Wiederholungen visuell prüfen: Fächertopologie und echte neue Episoden wirklich plausibel?
2. Gespeicherte Entrymerkmale auswerten: Stopabstand in % und 4h-ATR, Kontaktgeometrie, Kontext und Gapverluste. Zuerst erklären, wo Verluste und Gewinne entstehen; noch keine nachträglich perfekt zugeschnittenen Schwellen aktivieren.
3. Wenige daraus begründete Hypothesen vorab einfrieren und auf getrennten beziehungsweise prospektiven Daten testen. Kosten- und Zensierungsgrenzen beibehalten. Close-Stop mit Notstop oder verzögerte enge Safety jeweils als eigene klar definierte Folgevariante, falls fachlich sinnvoll.

Noch keine Orders, neue Datenimporte, Containerumstellung oder GitHub-Veröffentlichung. Der Sammler bleibt pausiert. Die Webansicht und ältere Depotstudien wurden für diese Untersuchung nicht umgebaut.
