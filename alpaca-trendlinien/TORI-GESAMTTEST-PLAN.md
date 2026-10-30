# Gesamttest des Kriterienpakets vom 22.10.2026

Vorabplan, vor dem erweiterten Import und vor neuen Ergebnissen festgehalten. Isolierte Forschung; keine Umstellung von Chart, Queue oder laufendem Beobachter. Keine Brokerorders. Die Zahlen unten sind operationalisierte Hypothesen, keine behaupteten Originalparameter oder validierten Handelsregeln.

## Population, Zeit und Daten

- Feste 60 heutige US-Aktien (Liste im Importwerkzeug), keine ergebnisabhängige Auswahl. Damit bleibt Survivorship-/Liquiditätsauswahl bestehen; keine Repräsentativität für alle Aktien oder Europa behaupten.
- Zehn Kalenderjahre anfordern, tatsächlich verfügbare Historie je Aktie berichten. IEX-Probe AAPL: erste Tageskerze 27.07.2020. Keine alten Kurse ergänzen oder erfinden.
- Ende 21.10.2026, 20:00 UTC. Ausschließlich kostenloser IEX-Feed, splitbereinigt, reguläre XNYS-Sitzungen aus echten 5m-Kerzen, gleiche Normalisierung wie bisher. Unvollständige Aggregate entfallen, erwartete Lücken bleiben nachweisbar.
- Ein Jahr Vorgeschichte, dann jede vorhandene abgeschlossene 4h-/Tageskerze der Reihe nach. Keine kurze Suchfenstergrenze, keine 60-Kerzen-Lebensdauer für gültige Linien. Fehlende erwartete Quellkerzen entwerten die davon betroffene strenge Linie; keine Interpolation.
- Zeitgruppen 2021–2023 und 2024–21.10.2026 getrennt. Bereits betrachtete spätere Daten bleiben bekannte Daten. Auch neue frühere/zusätzliche Bestände sind durch die Auswahl kein garantiert unberührter Out-of-sample-Test.
- Vollständiger Durchlauf statt nur zufälliger Starttage. Ergänzend feste zufällige Starttage und Wartezeit bis zum ersten späteren Signal; mehrere Starts mit gleichem Entry sind keine zusätzlichen Trades.

## Geometrie und drei Kontakte

- Gemeinsame Quellintervall-Geometrie: bestätigte 2+2-Wendepunkte, Paare innerhalb 30/90/365 Tagen, letzte zehn Wendepunkte je Fenster. Geraden auf Handelskerzenbasis, keine MTF-Zeichnungsprojektion als Signal.
- Strenge Außenlinien: vor dem Ausbruch keine Dochtüberschreitung. Kontakte innerhalb max(0,01 USD; 0,10 der bei Linienentstehung bekannten ATR), nur auf der erlaubten Seite. Band bleibt fest.
- Eigenständige Kontakte erfordern dazwischen einen späteren Schlusskurs mindestens 0,50 Entstehungs-ATR außerhalb des Bandes und zwei Kerzen Abstand. Benachbarte Kerzen sind eine Kontaktphase. Qualifikation für Ausbruch/Retest wird vor der Ausbruchskerze eingefroren; der spätere Retest erzeugt keinen rückwirkenden dritten Kontakt.
- Mehrere Kandidaten behalten, nahezu identische Linien anhand aktueller und 20-Kerzen-Projektion gruppieren. Bessere vorab bekannte Kontaktqualität muss bei der Signalauswahl Vorrang haben; kein Ranking nach späterem Gewinn.
- Separate lockere Dochtzonen als Sensitivitätskontrolle, nicht als Erfüllung der strengen Zeichenregel. Vorhandene exakt gezählte Hülle als begrenzte Referenz, sofern mit denselben Daten reproduzierbar.
- Blindpaket ohne spätere Kerzen vorbereiten. Echte manuelle Urteile kann ein automatischer Lauf nicht ersetzen; bis dahin keine behauptete Übereinstimmung mit menschlicher Linienwahl.

## Verschachtelte Einstiegsprüfungen

Für Ausbruch, späteren Retest der ursprünglichen roten Linie und Grün-Abpraller getrennt, jeweils 4h und 1D:

0. Zwei unabhängige Kontakte, bekannte grüne Absicherung, bestätigter Schluss über der Aktionslinie, positive Kerze; Ausführung am ersten vorgesehenen 5m-Open frühestens fünf Minuten später. Kein angenommener Kauf zum bereits bekannten Signalschluss.
1. Mindestens drei eigenständige Kontakte an der Aktionslinie vor dem Signal (beim Retest vor dem ursprünglichen Ausbruch). Grün mindestens zwei Kontakte.
2. Zusätzlich Aktions- und Safety-Linie mindestens sieben Kalendertage alt, gemessen ab erstem Anker; tatsächlicher Bekanntheitszeitpunkt separat. Alter 14 Tage und drei grüne Kontakte als vorab festgelegte strengere Sensitivitäten.
3. Zusätzlich echter Anstieg: positive Signalbewegung mindestens 0,25 bekannte Quell-ATR und Schluss über vorherigen sechs Quellhochs. Retest: ursprünglicher Ausbruch muss dies bestanden haben; spätere positive Reaktion über vorherigem Hoch. Bounce: positive Reaktion über vorherigem Hoch.
4. Zusätzlich gepufferter Stop max(0,01; 0,25 Signal-ATR) unter Grün, positiver Stop, Abstand einschließlich Kosten höchstens zwei ATR und zehn Prozent. Geplantes Positionsrisiko separat; enge Preisabsicherung ist nicht gleich Depotrisiko.
5. Zusätzlich frischer bekannter Tages-/Wochenkontext, kein fallender Tages-/Wochen-/Monatskontext, mindestens 2R Raum zum nächsten bekannten horizontalen oder anderen roten Widerstand. Ohne verbleibenden bekannten Widerstand bei ausreichender Vorgeschichte als freier Raum kennzeichnen, nicht als Kursziel erfinden. Fehlender Kontext bleibt unbekannt.
6. Zusätzlich Unternehmensereignisfilter mit vor dem Signal bekanntem Ereigniskalender und expliziter Abdeckung für die nächsten drei Handelstage. Ohne historische Abdeckung **unbekannt**, keine vollständig regelkonformen Trades behaupten. Kursbasierte Ergebnisse separat berichten, niemals unbekannt als bestanden behandeln.

Schlusskurs über der Linie ist Hauptauslegung; gesamter Körper darüber als getrennte Sensitivität. Keine Wahl der günstigsten Auslegung nach Ergebnissen. Pro Familie/Quellkerze stärksten vorab bekannten Kandidaten wählen; Profilfilter dürfen einen anderen gültigen Kandidaten derselben Kerze wählen. Keine zukünftige Pfadvollständigkeit als Entryfilter.

## Ausstieg und Messung

- Fester anfänglicher Hardstop als Referenz.
- Nachziehen nur unter nach Einstieg bestätigten höheren Tiefs (2+2), positive Erholung mindestens 0,50 Quell-ATR über dem Tief; Stop niemals senken, Puffer anhand damals bekannter ATR. Keine zusätzliche Pflicht, dass die Verbindungslinie jedes höhere Tief erreicht.
- Getrennte Kombination aus diesem Hardstop und bestätigtem Schluss unter der ursprünglichen grünen Linie. Spätere globale Linienauswahl ändert den Trade nicht.
- Separate Freitagsausnahme: profitabel und nahe einem schon vor der Entscheidung bekannten Widerstand; nur bei im Quellintervall rechtzeitig vor Sitzungsschluss bestätigter Entscheidung und ausführbarem RTH-Open. Auf Tagesbasis kein fiktiver Freitagsverkauf nach Bekanntwerden des Schlusskurses.
- Kein festes Gewinnziel, kein erzwungener Verkauf nach zehn Tagen. Am Datenende offene Fälle zensieren und offenen Buchwert separat berichten. Gaps zum verfügbaren Open; 5m-Pfadlücken sofort als unbekannt, nicht still überspringen. Spread/Slippage/Kosten explizit.
- 5/10/20/60 Handelstage als Zwischenstände, unabhängig vom Strategieexit. Trefferzahl, Wartezeit, Filtertrichter, Signale je Aktienjahr, Aktien-/Zeitstreuung, Gewinn-/Verlustverteilung und Konzentration berichten. Überlappende Fallrenditen sind keine Depotperformance.
- Für eine deploybare Strategie wären anschließend zusätzlich Cash-/Allokationsledger, echte Ereignisabdeckung, unabhängige Zukunftsdaten und manuelle Geometriebewertungen nötig. Bisher verbrauchter Holdout wird nicht erneut als unberührt bezeichnet.

## Prüfung

Gezielte Gegenbeispiele für einseitige Kontaktbänder, Kontaktphasen, eingefrorene Qualifikation, fehlende Quellkerzen, Daily/4h, Ausführungslatenz, Ereignis-Unbekanntheit, kausales höheres Tief, Stop-Gap, fehlenden Pfad und Tagesende. Präfixvergleich vor/nach zusätzlichen zukünftigen Kerzen, unabhängige Nachrechnung der Ausstiege und Zusammenfassungen. Bestehende Python-/JS-Suiten ausführen. Private Imports, Datasets, Fälle, Blindpakete und Ergebnisse bleiben in ignorierten Laufverzeichnissen; Regeln, Werkzeuge und aggregierte Bilanz sind dokumentiert.
