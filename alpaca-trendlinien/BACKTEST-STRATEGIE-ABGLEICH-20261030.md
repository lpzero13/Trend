# Strategie-Zusammenfassung: Abgleich mit der Backtest-Roadmap

Stand: **30.10.2026**. Grundlage ist die vom Nutzer am selben Tag angehängte Zusammenfassung „Die Grundidee … / Die 4 Einstiegs-Varianten …“. Ergänzt [BACKTEST-MEILENSTEINE.md](BACKTEST-MEILENSTEINE.md).

**Status: Auswertung und Planung, keine Implementierung und keine neue Ergebnisstudie.** Aussagen der Vorlage über Wirksamkeit, Häufigkeit oder Toris Originalregeln sind damit nicht als unabhängig belegt übernommen. Die Platzhalter `[cite: 9]` enthalten keine prüfbare Quellenangabe. Die nachfolgenden Entscheidungen sind Vorschläge für den späteren Versuchsvertrag.

**Spätere Umsetzung am selben Tag:** Auf anschließenden Nutzerauftrag wurde ein begrenzter [MSFT-/Zwölfmonats-Technikpilot](BACKTEST-PILOT.md) umgesetzt und geprüft. Dort sind die tatsächlich gewählten Annahmen und Ergebnisse beschrieben. Diese Datei bleibt der fachliche Abgleich; sie behauptet nicht, dass sämtliche nachfolgenden Varianten bereits umgesetzt sind.

## Gesamtbewertung

Die Vorlage beschreibt einen gut automatisierbaren Kern: kausale Fächergeometrie, bestätigte Kontakte, Schlusskursentscheidung, gebundene ursprüngliche Linien, risikobegrenzte Positionsgröße und ausschließlich aufwärts nachgezogene Stops. Sie ergänzt die bisherige Roadmap um eigenständige Safety-Rücksetzer und geometrisches Fächer-Trailing.

Es handelt sich jedoch nicht um eine vollständig eindeutige ausführbare Spezifikation. Insbesondere Linienversion, Aktivierungszeitpunkt, Retest-Art, Safety-Auswahl am späteren Einstieg und Schlusskurs-Stop müssen vereinheitlicht werden. Reine geometrische Regeln verwenden ebenfalls Vergangenheitsdaten und Pivotbestätigung; sie sind nicht verzögerungsfrei. Die beispielhaften 90 Prozent Standardtrades oder 20–35 Prozent Gewinner sind keine gemessenen Ergebnisse unseres Programms.

## 1. Geometrie: Übereinstimmungen und Abweichungen

| Thema | Vorlage | Vorhandener Master-Stand / Konsequenz |
|---|---|---|
| Horizonte | Rot 150, Safety 320 Kalendertage | Grundsätzlich vorhanden; tatsächliche Puffer-/Pivotgrenzen zusätzlich beachten |
| Stufen | Bis vier, jeweils steiler | Vorhanden; die deterministische Auswahl bei mehreren passenden Linien muss im Versuch unverändert bleiben |
| Körperverletzung | Keine | Master lässt derzeit 0,05 historischen ATR zu. Strikt 0 und 0,05 sind verschiedene Regelvarianten |
| Dochte / Kontakte | 0,15 / 0,45 ATR | Als Parameter vorhanden; historische Prüfungen verwenden den damaligen ATR, keine heutige Toleranz rückwirkend |
| Kontaktabstand | Mindestens fünf Kerzen | Master verwendet fünf für Stufe 1 und drei für spätere Stufen. Fünf auf allen Stufen wäre eine neue Variante |
| A+-Klasse | Mindestens drei Kontakte, sieben Kalendertage | Kontakt-/Altersklasse vorhanden; keine Aussage über erwartete Profitabilität |
| Zwei Kontakte | Vorläufige Gruppe | Vorhanden. Eine Hülllinie mit nur einem bestätigten Pivot darf nicht zu zwei Kontakten umetikettiert werden |
| Haupt-/enge Safety | Getrennte Auswahl | Im Master vorhanden; Auswahl muss für Signal, Stop und Bericht konsistent sein |
| Ausbruchsfenster | Letzte zwei Kerzen bei der roten Berechnung aussparen | Pine-Rückblick vorhanden. Headless verwendet vorab bekannte Episoden und erzeugt daraus keine rückdatierten Signale |

„Flachste gültige Linie“ ist allein keine vollständige Auswahlregel: Auch Kandidatenraum, mindestens erforderliche Kontakte, Extremanker, Steigungsrichtung, Fortsetzungsanker, Gleichstände und Invalidierung müssen feststehen. Sonst könnten eine triviale flache Hülle und die gewünschte kontaktgestützte Linie verschieden ausgewählt werden. Die vorhandene deterministische Master-Auslegung ist die Ausgangsreferenz.

**Vorschlag:** zunächst das vorhandene Master-Profil unverändert als Referenz halten. Abweichungen der Vorlage ausdrücklich dokumentieren; nicht gleichzeitig mit neuen Einstiegs- und Exitregeln die Geometrie austauschen.

## 2. Einstiegssystematik für M2

Die vier Beschreibungen enthalten bei genauer Trennung fünf unterscheidbare Fälle. Sie dürfen nicht als fünf unabhängige Gelegenheiten desselben Marktmoments addiert werden.

| Kennung | Fall | Einordnung und nötige Präzisierung |
|---|---|---|
| E1 | Sofort sauberer Ausbruch | Voriger Schluss auf/unter derselben zuvor bekannten roten Linie, neuer Schluss mindestens 0,15 ATR darüber. Entscheidung am Schluss, Ausführung erst danach |
| E2 | Verzögert sauberer Ausbruch | Schwacher Bruch merkt dieselbe Linie vor; später sauberer Schluss. Gleiche Ausbruchsfamilie wie E1, aber eigener Untertyp |
| E3 | Retest der gebrochenen roten Linie | Nach bestätigtem Bruch Rücklauf und Bestätigung an der ursprünglichen roten Linie. Kein nachträglicher Wechsel auf eine bequemere Linie |
| E4 | Safety-Rücksetzer nach einem Ausbruch | Rücklauf an eine ausdrücklich benannte Safety statt an Rot. Eigene Versuchsgruppe mit Verbindung zur ursprünglichen Ausbruchsepisode |
| E5 | Eigenständiger Safety-Bounce | Bestätigte steigende Safety, Rücklauf von oben, gültige Kontaktzone und bullischer Schluss darüber; kein vorheriger roter Ausbruch zwingend erforderlich |

Für E1–E3 die roten Kontaktklassen getrennt ausweisen. Für E4/E5 die Safety-Kontaktklasse angeben; eine A+-Safety macht nicht automatisch auch den Widerstand zu A+. E5 verlangt in der Vorlage eine A+-Safety. Etwaige Zwei-Kontakt-Bounces wären eine weitere ausdrücklich neue Kontrollvariante, keine stillschweigende Erweiterung.

### E2: Wartephase ist noch nicht identisch definiert

Die Vorlage nennt die unmittelbar folgende Kerze. Der bisherige Beobachter erlaubt standardmäßig bis zu 20 Quellkerzen bis zum sauberen Schluss. Für den späteren Versuch müssen Gültigkeitsdauer und Rückfallregel feststehen: Verwerfen bei erneutem Schluss unter der Linie oder begrenztes weiteres Warten? Ein erfolgloser Versuch und ein späterer frischer Bruch erhalten nachvollziehbare Episoden.

### E3/E4: Retest-Art und Wartefenster nicht vermischen

Die Vorlage nennt ein bis fünf Kerzen und einen optionalen vorherigen zu großen Stopabstand von etwa 10–12 Prozent. Der bisherige rote Retest-Beobachter erlaubt standardmäßig bis zu 60 Quellkerzen. Das sind verschiedene Experimente.

**Vorschlag:** zunächst rote Retests unabhängig vom Stopabstand beobachten und den ursprünglichen Abstand als Merkmal speichern. Eine feste Regel „nur nach übergroßem Ausbruch auf Retest warten“ später als eigene Entscheidungsstrategie bewerten. Keine nachträgliche Wahl zwischen sofortigem Einstieg und Retest anhand des später besseren Ergebnisses. Ein kombiniertes Depot entscheidet bei Signalentstehung, ob es wartet.

Für jedes Wartefenster angeben, ob Kerzen seit schwachem Bruch, sauberem Bruch oder Kontakt gezählt werden und ob Kontakt- und Bestätigungskerze dieselbe sein dürfen. Fünf 4h-Kerzen sind keine fünf Handelstage.

### E5: Die angegebene Bounce-Ungleichung reicht nicht

`Low <= Safety + 0,45 ATR` erlaubt auch einen tiefen Durchbruch durch die Safety mit anschließender Erholung. Sie belegt weder eine begrenzte Berührung noch die Annäherung von oben.

Ein technischer Vorschlag für die spätere Definition ist:

- Safety und ihre Kontaktklasse waren vor der Signalkerze bekannt.
- Der vorherige Schluss lag oberhalb derselben Safety-Geometrie.
- Die Signalkerze erreicht die obere Kontaktzone, unterschreitet die Safety aber höchstens um eine separat festgelegte Docht-Toleranz, beispielsweise 0,15 ATR.
- Schluss oberhalb der Safety und oberhalb des eigenen Opens.
- Eine neue Bounce-Episode benötigt eine zwischenzeitliche Bewegung weg von der Linie; mehrere benachbarte grüne Kerzen sind keine unabhängigen Bounces.

Der zusätzliche untere Grenzwert und die Episodenbildung sind Korrekturvorschläge, keine bereits übernommenen oder getesteten Regeln. Für eine gerade erst bestätigte dritte Berührung dürfen wir die frühere Berührung nicht rückwirkend als damals verfügbares A+-Signal ausgeben.

## 3. Safety und Stückzahl am tatsächlichen Einstieg

Die Vorlage verlangt eine gültige Safety unter dem Kurs im Einstiegszeitpunkt. Der aktuelle Beobachter bindet Safety und initialen Stop dagegen bereits beim ursprünglichen Bruch und verwendet sie auch für einen späteren sauberen Schluss oder roten Retest weiter.

Diese Unterschiede müssen bei verzögerten Einstiegen ausdrücklich entschieden werden. Vorschlag: Original-Safety und Originalstop immer archivieren; eine spätere Neuauswahl oder bloße Fortschreibung derselben Safety bis zum Einstieg als benannte Variante führen. Eine bereits verletzte oder ungültige Safety wird nicht nur deshalb zugelassen, weil ihr Zahlenwert unter dem Kurs liegt.

Die 0,3-Prozent-Pufferung kann als dokumentierte Ausgangsannahme dienen. Stückzahl aus tatsächlichem modelliertem Kaufkurs, Stop, verfügbarem Kapital und Kosten berechnen. Das Risiko der ursprünglichen Position später nicht durch eine neue R-Definition umschreiben.

Die Formel mit Abrunden und Kapitalgrenze begrenzt das **geplante** Risiko unter ihren Annahmen. Sie führt nicht zu immer exakt einem Prozent Verlust: ganze Stückzahlen und Kapitalgrenze können das Risiko reduzieren, Kursgaps und Ausführungskosten es erhöhen. Ein wegen fehlendem Budget nicht ausführbares Signal bleibt im Bericht sichtbar.

## 4. Exit-Systematik für M4

Der bisherige `fan_execution.py`-Weg bietet feste Stops und Nachziehen unter bestätigten höheren Pivot-Tiefs. Das ist nicht identisch mit dem in der Vorlage beschriebenen fortlaufenden Nachziehen entlang einer schrägen Safety und dem Wechsel auf neue Fächerstufen.

Für die Planung folgende Komponenten getrennt beschreiben:

| Stopführung | Zweck |
|---|---|
| Fester ursprünglicher Stop | Vergleichsreferenz |
| Ursprüngliche Safety fortschreiben | Gleiche eingefrorene Geometrie entlang der Handelskerzen, ohne neue Fächerlinie |
| Auf neue bestätigte engere Safety wechseln | Zusätzlicher Nutzen kausal verfügbarer neuer Fächerstufen |
| Bestätigte höhere Pivot-Tiefs | Bereits vorhandener anderer Trailing-Ansatz; als Vergleich getrennt halten |

Jeweils unterscheiden: intrabar ausgelöster Hard-Stop und erst am Quellkerzenschluss entschiedener Close-Stop. Nicht sofort sämtliche Kombinationen optimieren: zunächst Referenz und geometrische Fortschreibung vergleichen, danach neue Fächerstufen und Auslöseart gezielt hinzufügen.

### Hard-Stop und Close-Stop brauchen unterschiedliche Verträge

- Hard-Stop: vor der jeweiligen Ausführungskerze gültiger Stop; Kursgap am verfügbaren Open, ansonsten konservativer Stop-Fill zuzüglich Kosten. Mit 5m-OHLC bleibt die genaue Tickausführung unbekannt.
- Close-Stop: Vorlage nennt zunächst `Close < Safety - 0,15 ATR`, in der Schleife aber `Close < ActiveStop`, wobei ActiveStop aus einem 0,3-Prozent-Puffer stammt. Diese Schwellen sind nicht gleich. Safety-Version, ATR-Zeitpunkt, eventuelle Ratchet-Regel und entscheidendes Quellintervall müssen vorab festgelegt werden.
- Ein 4h-Close-Stop wird am 4h-Schluss entschieden, nicht bei jedem 5m-Schluss. Für ein reales nachgelagertes Entscheidungsmodell erfolgt die Ausführung erst nach dem Signal. Der auslösende Close ist kein garantierter nachträglich erreichbarer Kauf-/Verkaufskurs.
- Ein reiner Close-Stop begrenzt den zwischenzeitlichen Verlust nicht wie ein Hard-Stop. Eine Kombination mit zusätzlichem Notstop wäre ein drittes ausdrücklich benanntes Modell.

### Ratchet und zeitliche Wirksamkeit

`neuerStop = max(bisherigerStop, gültigerKandidat)` ist als Grundsatz sinnvoll. Ein am Schluss neu bestätigter Pivot oder neu gezeichneter Fächer darf aber nicht auf das bereits vergangene Tief derselben Kerze angewandt werden.

Auch eine bekannte steigende Gerade braucht einen Ausführungsvertrag: Wird der Stop nur an 4h-Schlüssen angehoben oder an jedem 5m-Schritt anhand der vorher bekannten Geometrie? Für einen ersten Vergleich empfiehlt sich das Quellkerzenraster; feinere Updates später gesondert testen. Alle Projektionen verwenden die definierte Handelskerzenbasis, keine unbeabsichtigten Kalendertage oder Chart-MTF-Projektionen als neue Signale.

## 5. Zu korrigierende Erfolgsaussagen

- **„Hard-Stop bedeutet exakt −1R“:** nicht garantiert. Gaps, Slippage, Gebühren und Stückzahl verändern das Ergebnis.
- **„Stop über Einstieg bedeutet kein Verlust mehr möglich“:** nicht garantiert. Auch ein nachgezogener Stop garantiert keinen Ausführungskurs; Gebühren können den Netto-Break-even zusätzlich verschieben.
- **„Cleaner Close schützt zuverlässig“:** plausible Hypothese, kein bisher belegtes Ergebnis. Verzögerung kann Fehlsignale vermeiden, aber gute Ausbrüche verpassen oder den Einstieg verteuern.
- **„Kein festes Ziel“:** passt zur vorgeschlagenen Trendfolge als Hauptidee. 2R, Teilverkauf oder Zeitstopp bleiben Vergleichsmodelle; sie werden nicht zum zwingenden Bestandteil der Strategie.

Sachgrundlage zum Unterschied zwischen Stop- und Ausführungspreis: [SEC / Investor.gov: Types of Orders](https://www.investor.gov/introduction-investing/investing-basics/how-stock-markets-work/types-orders). Keine Aussage der Vorlage wird durch diese Quelle als insgesamt validierte Handelsstrategie bestätigt.

## 6. Optionale Module erst nach den Kernvergleichen

- SMA200-Filter zunächst als Merkmal erfassen, danach gezielt als Filter gegen die ungefilterte Referenz prüfen. Das Intervall des SMA benennen; 200 Tageskerzen und 200 4h-Kerzen sind verschieden.
- Teilverkauf oder Break-even am äußeren Dach als getrennte Alternativen führen. Vorab festlegen, welche zum Entry bekannte Dachlinie gilt, ob sie fortgeschrieben wird und was ohne darüberliegenden gültigen Widerstand passiert. Kein nachträgliches Zeichnen eines besseren Ziels.
- Zeitstopp „10 Kerzen ohne +0,5R“ präzisieren: aktuelle Schlussperformance oder zu keinem Zeitpunkt erreichtes +0,5R? Quellkerzen, Datum des Beginns, Kostenbezug und Ausführung nach der Entscheidung festlegen.
- Keine Strategie nach dem besten Einzelfall zwischen Haupt-/enger Safety, Ausbruch/Retest, Stoparten oder Zielvarianten umschalten lassen. Alle Alternativen einschließlich erfolgloser Versuche protokollieren. [Forschung zur Backtest-Überanpassung](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf).

## 7. Kausale Ereignisreihenfolge für den späteren Vertrag

1. Vor der nächsten Ausführungskerze gelten nur bereits verfügbare Orders, Positionen, Stops und bekannte Linienversionen.
2. Erwartete 5m-Kerzen chronologisch abarbeiten: verfügbare Entries, Gaps und vorhandene Hard-Stops korrekt der Position zuordnen. Vor dem Einstieg berührte Tiefs lösen keinen späteren Stop aus.
3. Am Schluss einer Quellkerze diese Kerze und ihren nun bekannten ATR ergänzen. Einen Close-Exit anhand der für diese Entscheidung festgelegten Linie/Schwelle prüfen.
4. Neu bestätigte Pivots/Kontakte und neue Linienversionen nach ihrem Verfügbarkeitsvertrag registrieren. Sie dürfen keine frühere Kontaktklasse oder Ausbruchslinie rückwirkend verbessern.
5. Neue Entry-Entscheidungen und Stopänderungen erzeugen; Wirksamkeitszeitpunkt nach Entscheidung und Verzögerung festhalten. Stückzahl zum modellierten tatsächlichen Fill prüfen.
6. Wiederholungssignale und Re-Entry nach einem Exit nach einer vorab festgelegten Regel behandeln. Nicht durch dieselbe Kerze beliebig oft aus- und einsteigen.

Die Vorlage enthält bereits den richtigen Kern „alten Stop prüfen, danach anheben“. Ihre vorgeschaltete Neuberechnung aller Linien und der Einstieg zum gleichen Close reichen allein aber noch nicht als Nachweis vollständiger Zukunftsfreiheit. Dafür brauchen wir die Präfix-, Zeitstempel- und Zukunftsschockprüfungen aus M1.

## Einbindung in die Meilensteine

- **M0:** Unterschiede und offene Definitionen dieser Datei entscheiden und als versionierten Vertrag festhalten.
- **M1:** Vorab bekannte rote und Safety-Episoden mit stabilen Identitäten verfolgen.
- **M2:** Sofort/verzögert sauberer Ausbruch getrennt kennzeichnen; roten Retest, Safety-Rücksetzer nach Ausbruch und eigenständigen Bounce unterscheiden.
- **M3:** identische Verlaufsmessung für jede Gruppe, ohne abhängige Fälle mehrfach zu zählen.
- **M4:** feste Safety, geometrisches Fortschreiben, Fächerwechsel und Auslöseart schrittweise vergleichen; feste Ziele nur als Kontrollvarianten.
- **M5–M7:** Robustheit, echtes Kapitalbuch und prospektive Hermes-Beobachtung unverändert erforderlich.

Die universumsweite Planung von **M0** bleibt erforderlich. Der später beauftragte Technikpilot deckt einen begrenzten Teilumfang ab; die Roadmap wird nicht durch eine vermeintlich schon bewiesene Komplettstrategie ersetzt.
