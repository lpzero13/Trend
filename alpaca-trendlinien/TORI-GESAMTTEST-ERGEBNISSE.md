# Bilanz: vollständigeres Tori-Regelpaket, längere Historie, 60 Aktien

Stand 22.10.2026. Lokaler Zweig `codex/tori-complete-study`. [Vorabplan](TORI-GESAMTTEST-PLAN.md), [vollständige Tabellen und Methodik](TORI-GESAMTTEST-TABELLEN.md). Kein Upload, Container-Rollout, neuer Zeitplan oder Brokerauftrag. Bestehender Chart und prospektiver Beobachter verwenden weiterhin ihre bisherigen Regeln.

## Ergebnis

Die technische Drei-Kontakt-Frage ist lösbar: Strenge Außenlinien mit einseitigem Kontaktband finden zahlreiche dritte Reaktionen, ohne Dochte zu durchschneiden. Ein wirtschaftlicher Vorteil des vollständigen Regelpakets ist dagegen **nicht nachgewiesen**. Insbesondere unsere numerische Übersetzung von „Safety nahe“, „übergeordneter Trend“ und „Weg frei“ reduziert die Anzahl sehr stark. Diese Grenzen sind experimentelle Auslegungen, keine nachgewiesenen Originalparameter von Tori.

## 1. Größerer und längerer Versuch

- 60 Aktien vorab festgelegt; 57 verwendbare Imports. CRM, KO und LOW wegen ungültiger Providerzeilen vollständig zurückgewiesen, nicht nach Renditen ausgeschlossen.
- Zehn Jahre angefragt; tatsächlich IEX-Historie ab 27.07.2020 bis 21.10.2026. 6.731.311 reguläre 5m-Kerzen, 129.220 vollständige 4h- und 57.975 vollständige Tageskerzen gespeichert. Nach einem Jahr Vorlauf rund fünf Jahre Signalsuche je Aktie, insgesamt rund 298 Kalender-Aktienjahre je Quellintervall.
- Jede abgeschlossene Quellkerze chronologisch verarbeitet; keine kurzen Zufallsfenster und kein Ablauf nach 60 Kerzen. Ausbruch, Retest und Grün-Abpraller getrennt, 4h und 1D getrennt, strenge Außenlinien und lockere Dochtzonen getrennt.
- Zusätzlich 100 feste Zufallsstarts je Aktie/Intervall/Geometrie. Bei 4h und drei Kontakten plus sieben Tagen Alter erreichen 3.508 von 5.700 Starts später einen Entry; 2.192 finden bis Datenende keinen. Median der Wartezeit unter den gefundenen Fällen: 257 Kalendertage. Wiederholte Starts zum selben Entry sind keine neuen Trades; am Datenende zensierte Wartezeiten fehlen im Median.

Der Einwand eines zu kurzen Suchfensters ist damit für diesen Versuch adressiert. Das bedeutet nicht, dass für jede Aktie oder jeden Start zwingend ein Entry existiert.

## 2. Exakte Gerade gegenüber drei unabhängigen Kontakten

In der strengen 4h-Geometrie entstehen 13.132 Kandidaten; 2.813 erreichen mindestens drei getrennte Reaktionsphasen. Unter den 1.225 2-Kontakt-Referenzfällen haben 359 mindestens drei nahe Aktionskontakte, aber nur einer drei exakt kollineare Kontakte. Auf Tagesbasis: 462 Referenzfälle, 150 mit drei nahen Kontakten und keiner mit drei exakt kollinearen Kontakten.

Das bestätigt den technischen Nutzen der Trennung: Zwei Anker bestimmen eine Gerade; weitere zulässige Reaktionen liegen in einem bei Entstehung fixierten, einseitigen Abstand. Benachbarte Kerzen zählen nicht als zusätzliche Abpraller. Der spätere Retest darf keinen fehlenden dritten Kontakt vor dem ursprünglichen Ausbruch nachliefern.

Mehrere Kandidaten bleiben erhalten. Auswahl erfolgt anhand damals bekannter Kontaktzahl, Alter und Safety, ohne spätere Renditen. Nahezu identische Alternativen der Aktionslinie zählen nicht zusätzlich als eigenständiges direkt darüberliegendes Hindernis.

**Noch nicht bestätigt:** Übereinstimmung mit menschlicher Linienwahl. 82 verblindete Fälle vorbereitet; echte manuelle Rays/Urteile fehlen. Diese können automatisierte Erfolgszahlen nicht ersetzen.

## 3. Welcher Filter reduziert die Signale?

Profil-/Familienfälle, keine unabhängigen Depottrades; Varianten können denselben physischen Entry teilen.

| Aufeinander aufbauende Prüfung | 4h | 1D |
|---|---:|---:|
| Zwei unabhängige Kontakte | 1.225 | 462 |
| Drei Aktionskontakte | 359 | 151 |
| Zusätzlich mindestens sieben Tage Alter | 310 | 151 |
| Zusätzlich Momentum und Zwischenhoch | 206 | 106 |
| Zusätzlich enge Safety | 20 | 17 |
| Zusätzlich Kontext und Raum | 1 | 0 |
| Zusätzlich historischer Ereignisfilter | unbekannt | unbekannt |

In den Ausgangsfällen besteht der separate Raumtest nur bei 89 von 1.225 4h-Fällen und 32 von 462 Tagesfällen. Der Kontext ist bei 595 beziehungsweise 202 Ausgangsfällen unbekannt. Bei 4h reduziert die Safety-Prüfung die bereits momentumqualifizierte Gruppe von 206 auf 20 Fälle.

Wichtig: Wir verlangen in diesem Versuch höchstens zwei Quell-ATR und zehn Prozent Abstand zum gepufferten Stop, mindestens 2R zum nächsten bekannten Widerstand sowie keinen fallenden Tages-, Wochen- oder Monatskontext. Das ist eine **strenge operationalisierte Hypothese**. Besonders frühe Trendwenden können daran scheitern. Die Ergebnisse widerlegen deshalb nicht die subjektive Methode des Textes. Grenzen nach Sichtung der Gewinne einfach zu lockern wäre aber auch kein sauberer Erfolgsnachweis.

Sensitivitäten für 14 Tage Alter, drei grüne Kontakte, ganzen Kerzenkörper und exakte dritte Kontakte wurden ebenfalls berechnet. Nach der bereits fast leeren Kontextgruppe lassen sie sich wirtschaftlich kaum beurteilen; ihre einzelnen Bestehenszahlen stehen zusätzlich in der marginalen Diagnose der Tabellen.

## 4. Gibt es wenigstens interessante Teilgruppen?

Ja, als Forschungsbefund insbesondere bei 4h-Retests:

- Zwei Kontakte: 282 Fälle, davon 264 bekannte 20-Sitzungs-Schlusskurse. 59,47 % positiv, durchschnittlich +2,38 % nach den angesetzten Kosten.
- Drei Kontakte und mindestens sieben Tage Alter: 64 Fälle, davon 59 bekannte 20-Sitzungs-Schlusskurse. 74,58 % positiv, durchschnittlich +5,20 %.
- Aufgeteilt bleibt die zweite Gruppe in beiden Zeitabschnitten positiv: 2021–2023 bei 26 bekannten Beobachtungen durchschnittlich +5,31 %, 2024–2026 bei 33 Beobachtungen +5,10 %.

**Das sind Schlusskursbeobachtungen unabhängig davon, ob vorher ein Stop ausgelöst wurde.** Kein Beleg für +5,20 % erzielbare Handelsrendite, keine Depotperformance und kein Vergleich gegen ein zeit-/risikoangepasstes Marktbenchmark. Die Gruppen überlappen und die spätere Phase ist kein unberührter Holdout. Die zusätzliche Momentumprüfung lässt hier nur 18 Retests übrig; sie zeigt keinen eindeutigen allgemeinen Mehrwert.

## 5. Natürliche Ausstiege statt Zehn-Tage-Abbruch

Fester anfänglicher Stop; Stop unter bestätigten höheren Tiefs; Kombination mit Schluss unter ursprünglichem Grün; separate rechtzeitig ausführbare Freitagsausnahme. Kein fixes Gewinnziel und kein erzwungener Verkauf nach zehn Tagen. Höhere Tiefs brauchen zwei geschlossene rechte Nachbarn; Änderungen werden erst mit Latenz wirksam. Gaps zum verfügbaren Open. Tages-Freitagsausstieg nach Kenntnis des Schlusskurses wird nicht fiktiv vorverlegt.

In der genannten 64er-Retestgruppe schließt der höhere-Tief-Stop 59 Fälle: 28 positiv, durchschnittlich +0,196R, Median −0,086R. Vier Pfade sind unbekannt, einer bleibt offen. Ohne den größten Gewinner beträgt das Mittel nur +0,061R. Aktienweise Bootstrapintervalle umfassen in beiden Zeitabschnitten Null; die Fallmengen sind abhängig und die Intervalle beziehen sich nur auf bekannte geschlossene Fälle.

Das ist ein vorsichtig interessanter Ansatz, keine belastbare Profitabilität. Auf den 46 Fällen mit für feste Safety, höheres Tief und Grün-Schluss gemeinsam bekanntem vollständigem Pfad ergibt die Bewertung einschließlich offener Buchwerte sogar +0,117R für den festen Stop gegenüber −0,192R für den höheren-Tief-Stop und −0,141R für die Kombination. Auch diese Auswahl nach vollständigem Pfad ist nur Diagnose. Ein genereller Mehrertrag des Nachziehens ist damit nicht gezeigt.

Ein ausschließlich fester Stop unter dem Einstieg realisiert ohne anderen Exit definitionsgemäß nur Verluste, während Gewinner offen bleiben. Seine geschlossene Trefferquote von null Prozent darf nicht gegen die realisierten Gewinne anderer Modelle als Gesamtperformance verglichen werden.

## 6. Daten und unbekannte Ereignisse begrenzen die Aussage

Median der 5m-Abdeckung 98,48 %, nach strenger Aggregation jedoch nur 78,94 % der 4h- und 72,45 % der Tageskerzen. Die Forderung nach jeder einzelnen 5m-Kerze verwirft bei manchen Aktien sehr viele Aggregate und kann lange Gewinnerpfade zensieren.

Das sind nicht automatisch Providerfehler: Laut [Alpacas Market Data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq) entsteht ohne geeignete Trades keine Bar; IEX ist ein einzelner Handelsplatz. Aus fehlender IEX-Aktivität darf man keinen bekannten Gesamtmarkt-Stopverlauf konstruieren. In dieser Studie wurde die bestehende konservative Datenkonvention beibehalten, keine konstante Kerze erfunden und kein Feed still gewechselt.

Historische Ereignisse mit damaligem Bekanntheitszeitpunkt und expliziter Abdeckung fehlen. Daher ist der letzte Filter **unbekannt**, nicht „bestanden“ oder „die Strategie liefert null echte Chancen“. Die CLI kann künftig über `--events` einen solchen Kalender erhalten; bloße rückblickende Terminlisten reichen nicht.

## 7. Nächster sinnvoller Schritt

1. Einen Teil der 82 Blindfälle ohne Zukunft ansehen und eigene Rays einzeichnen. Prüfen, ob Kontaktband, Kontaktphasen und Widerstandsauswahl der beabsichtigten manuellen Methode entsprechen.
2. Die Datenkonvention für einen einzelnen Handelsplatz fachlich klären beziehungsweise später mit vollständigerem Marktdatenfeed vergleichen. Das besonders strenge Raster nicht mit tatsächlicher Abwesenheit eines Aktienmarkts verwechseln.
3. Drei Kontakte plus Mindestalter als Kandidatenmerkmal weiter beobachten. Momentum, Safety-Abstand und Raum zunächst nachvollziehbar als Merkmale ausweisen; Änderungen der harten Grenzen vor einem neuen Versuch definieren, nicht nach Gewinnen auswählen.
4. Danach Ereigniskalender, Cash-/Positionsledger und unabhängige Zukunftsbeobachtung ergänzen, bevor ein automatisierter Handelsstandard behauptet wird. Ein Hermes-Hinweis zur manuellen Prüfung ist früher möglich als eine bestätigte automatische Entry-/Exitstrategie.

## Technische Abnahme und Betrieb

290 Python-Testfälle je unter 3.12/3.13 bestanden, jeweils ein vorhandener Plattform-Skip; 38 JavaScript-Tests bestanden. Darunter 16 neue gezielte Gegenbeispiele für Kontaktphasen, Dochtregel, Ereignis-Unbekanntheit, Daily/4h, zukünftige Kursschocks, Originalanker, Ausführungslatenz, Stop-Gaps und manipulierte Ausstiegswerte.

Separater Nachrechner: 228 Aktien-/Intervall-/Geometrieblöcke, 8.084 überlappende Entry-/Profil-Datensätze, 16.096 unterschiedliche Modellpfade und 20.365.238 Pfadkerzen kontrolliert. Originale Signalsätze wurden vor den Outcomes gespeichert. Der erste AAPL-Technikpilot diente zusätzlich zur Abnahme; für den vollständigen Lauf wurden nur Auditfelder, unveränderte Inputbindung und die Behandlung nahezu identischer Widerstandsalternativen präzisiert. Keine Kontakt-, Risiko-, Momentum- oder Exit-Schwellen anhand der Ergebnisse optimiert. Der Prüfalgorithmus wurde anschließend ohne Änderung der Ergebnisse beschleunigt und erneut vollständig ausgeführt.

Private Datasets im bestehenden lokalen `TORI_DATA_DIR`, Importmanifest und Pilot unter `artifacts/tori-complete-20261022-a`, finaler unveränderlicher Auftrag unter `artifacts/tori-complete-20261022-b`. Diese Dateien und Zugangsdaten werden nicht versioniert. Regeln und CLI stehen in diesem Repository, vollständige Befehle in den Tabellen. Keine neue Runtime-Abhängigkeit und keine Änderung bestehender Engine-Dateien, Zeitpläne oder Produktionspfade.
