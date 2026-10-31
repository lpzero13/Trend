# Technische Strategiesuche: vorab festgelegter nächster Versuch

Festgelegt am **30.10.2026**, vor Auswertung dieses Versuchs. Keine Webentwicklung. Der bisherige MSFT/2023-Pilot ist bekannte Entwicklungsinformation und keine unabhängige Bestätigung.

## Daten und Trennung

- Acht vorhandene SIP-/Split-Aktien: **AAPL, JPM, JNJ, XOM, KO, CAT, HD, NEE**. Branchenstreuung und vorhandene lange Historie bestimmen die Auswahl, nicht die Ergebnisse dieses Versuchs. MSFT wird nicht erneut zur Auswahl verwendet.
- Entwicklung: Entry-Jahre **2019, 2020, 2022**, jeweils separat mit Vorlauf und Nachbeobachtung. Die Jahre erfassen unterschiedliche Preisphasen; Entwicklungsfolds können über ihre Nachbeobachtung abhängig sein.
- Spätere Prüfung: **2024**, erst nach gespeicherter Auswahl aus der Entwicklung.
- Zusätzliche Bestätigung: **01.04.2025 bis 31.03.2026**, nur wenn die primäre Variante die spätere Prüfung besteht. Die Nachbeobachtung der 2024-Entries endet vor Beginn der Bestätigungs-Entries. Keine Kandidatenänderung anhand der 2024-Ergebnisse.
- Dies sind innerhalb dieses neuen Versuchs abgeschirmte Blöcke, keine Behauptung, sämtliche historischen Kurse seien in älteren Arbeiten noch nie betrachtet worden. Eine spätere prospektive Beobachtung bleibt erforderlich.
- Dataset-IDs und Engine-/Studiencode werden vor dem ersten Ergebnis in einem privaten Plan gebunden. Keine Providerimporte oder Wiederaufnahme des pausierten Sammelauftrags.

## Begrenzter Variantenraum

Die Master-Geometrie und drei Entry-Hauptfamilien bleiben unverändert gegenüber dem geprüften Pilot. Zwei rote Kontaktklassen (alle / qualifiziert), Bounce nur qualifiziert. Jede Gruppe kombiniert drei Stopführungen (fest / ursprüngliche Safety / aktuelle Fächer-Safety) mit Tages-SMA200-Filter aus/an. Daraus ergeben sich **30 eindeutige Varianten**. Gemeinsam: Hard-Stop, maximal 20 Handelstage, gleiche Kosten und kausale Ausführung. Keine nachträgliche Wahl zwischen zusätzlichen Zielwerten oder Haltedauern.

Die Einzelpfade verwenden ein ausdrücklich hohes rein nominelles Rechenkapital, damit eine gute oder schlechte Signalgelegenheit nicht vor der Depotprüfung allein wegen einer Mindeststückzahl verschwindet. Das gemeinsame Depot erhält dagegen nur **2.000 USD**, ein Prozent geplantes Risiko je Entry, höchstens 25 Prozent Allokation je Position, maximal drei gleichzeitige Positionen und ganze Stückzahlen. Cash kann nicht mehrfach ausgegeben werden. Je Symbol höchstens eine offene Position. Gleichzeitige Fälle werden deterministisch nach Symbol/ID aufgelöst, nicht nach ihrem späteren Ergebnis.

## Auswahl ausschließlich in der Entwicklung

- Mindestens 20 tatsächlich akzeptierte Depot-Trades über die drei Entwicklungsfolds.
- Mindestens zwei der drei Fold-Ergebnisse positiv nach Kosten, positiver mittlerer Fold-Ertrag.
- Vollständige Pfade und geschlossene Positionen; maximal zehn Prozent gemessener 5m-Drawdown je Fold.
- Unter den zugelassenen Varianten Auswahl nach mittlerem Fold-Ertrag, anschließend kleinerem maximalem Drawdown und stabiler Varianten-ID. Eine Siegerin je Entry-Familie; die global beste davon ist die **primäre** vorab gebundene Variante.
- Wenn keine Variante diese Entwicklungstore erfüllt, erfolgt keine erzwungene Siegerauswahl. Ergebnisse und technische Diagnosen werden trotzdem gespeichert.

## Spätere Prüfung und Belastungstests

Nur die in der Entwicklung festgelegten Familiensieger werden auf 2024 geprüft. Für die primäre Variante gelten vorab: mindestens zehn Depot-Trades, positiver Nettoertrag, höchstens zehn Prozent 5m-Drawdown, positive realisierte Beiträge von mindestens vier Aktien, höchstens 50 Prozent Konzentration der positiven Aktienbeiträge auf eine Aktie. Der Nettoertrag muss auch bei verdoppelten modellierten Spread-/Slippagekosten positiv bleiben.

Zusätzlich: Beiträge je Aktie, Entwicklungsvergleich nach Weglassen einzelner Aktien für die primäre Variante und 39 vorab deterministisch gesäte Zufalls-Kontrollportfolios. Kontrollen verwenden dieselben Aktien, monatliche Signalanzahl, bekannte gültige Safety und – falls aktiv – denselben Tagesfilter; Ausführung, Stopführung und Kapitalbeschränkung bleiben gleich. Kein Auffüllen fehlender Kontrollpools mit nachträglich ausgesuchten Gewinnern. Rang gegenüber diesen Kontrollen ist eine explorative Vergleichskennzahl, kein korrigierter Signifikanzbeweis über die 30 untersuchten Varianten.

Die primäre Variante muss zusätzlich über dem 90-Prozent-Quantil dieser Kontrollrenditen liegen, bevor der Bestätigungsblock geöffnet wird. Auf dem Bestätigungsblock gelten dieselben technischen/Return-/Drawdown-/Streuungs-/Kosten-Tore. Ein negativer Prüfbefund führt nicht zur nachträglichen Umbenennung einer anderen Variante als bestätigter Siegerin. Nach Verbrauch eines Blocks wird dieser nicht erneut als unangetastet bezeichnet.

## Technischer Nachweis

Offline-Reproduzierbarkeit, Quellcodebindung, präfixkausale Signale, spätere Stopwirksamkeit, fehlerhafte Datenpfade, Cash-/Risiko-/Stückzahlgrenzen und unabhängige Nachrechnung der Geldbewegungen prüfen. Unvollständige gehaltene Pfade stoppen ein Depot an der Datenlücke; sie werden nicht anhand ihres zukünftigen Ausgangs aus der Auswahl entfernt.

Ziel ist eine belastbar weiterzuprüfende Hypothese oder ein ehrlicher negativer Befund. Ein historischer Überschuss ist keine Garantie zukünftiger Gewinne und kein Auftrag für Brokerorders, Nachrichten, Containerinstallation oder GitHub-Veröffentlichung.
