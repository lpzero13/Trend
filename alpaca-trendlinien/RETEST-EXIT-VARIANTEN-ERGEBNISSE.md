# Drei zusätzliche Retest-Exits: Bilanz vom 22.10.2026

**Keine der drei vorab festgelegten Varianten verbessert die Zonen-Rendite in beiden bekannten Phasen.** Der ATR-Gewinnschutz ist als Risikovariante am interessantesten: im Entwicklungsdepot deutlich kleinerer Rückgang bei fast gleicher Rendite. Dieser Drawdownvorteil wiederholt sich in der späteren Phase nicht. Die feste anfängliche Safety bleibt deshalb die Ertragsreferenz; eine universell bessere Exitregel ist nicht gefunden.

[Vorab festgelegte Regeln](RETEST-EXIT-VARIANTEN-PLAN.md), [alle Tabellen einschließlich Hüllen-/Lückengruppen](RETEST-EXIT-VARIANTEN-TABELLEN.md). Bestehende Webansicht, Forschungsprofile und Zeitpläne unverändert; neue isolierte Module/Werkzeuge, keine Orders, Datenimporte, Nachrichten oder Containeränderungen.

## Was genau untersucht wurde

Die drei Varianten wurden nacheinander ausgeführt, ohne ihre Parameter anhand der Ergebnisse zu verändern. Alle beginnen mit denselben eingefrorenen Retest-Entries und demselben ursprünglichen gepufferten Stop unter Grün. Die rote/orangefarbene Zone bleibt geometrisch unverändert; keine später ausgesuchte Chartlinie wird rückwirkend als Signal benutzt.

1. **Gescheiterter Retest:** 4h-Schluss unter der Unterkante der ursprünglichen orangefarbenen Zone; freiwilliger Verkauf erst frühestens fünf Minuten später am nächsten erwarteten regulären 5m-Open. Bloßer Docht oder Schluss innerhalb der Zone reicht nicht.
2. **Fehlender Fortschritt:** Am Schluss der fünften XNYS-Sitzung ist ein sofortiger Modellverkauf nach Kosten nicht positiv; dann Verkauf am nächsten erwarteten regulären Open nach der Latenz. Bei positivem Ergebnis weiterhalten. Kein rückwirkender Verkauf zum gerade geprüften Schlusskurs.
3. **ATR-Gewinnschutz:** Aktivierung erst ab +1 anfänglichem R nach Kosten per geschlossenem 4h-Kurs. Danach Stop unter höchstem seit Entry beobachteten 4h-Schluss minus zwei aktuelle bekannte ATR14; niemals lockern, mindestens fünf Minuten Bestätigungslatenz. Der Schutz muss nicht sofort über Entry liegen. Ein Open unter neuem Stop wird am Open ausgeführt, nicht zum besseren Stoppreis.

In allen Fällen bleibt bis zum tatsächlichen früheren Exit die Absicherung aktiv; spätestens am Schluss der zehnten Sitzung wird verkauft. Kein festes Gewinnziel, keine Kombination der Varianten und keine nachträgliche Schwellenoptimierung.

## Umfang und Vergleichbarkeit

- 155 unveränderte archivierte Retests, 25 gepinnte splitbereinigte IEX-Aktien. Entwicklung **02.05.2025–18.03.2026**, spätere bekannte Phase **19.03.–02.07.2026**. Beide wurden bereits mehrfach untersucht; die spätere Phase ist kein unberührter Holdout. Der reservierte finale Zeitraum wurde nicht ausgewertet.
- Je Geometrie identische Entries für Referenz und neue Variante. Hauptgruppe wie im vorigen Exitversuch: kausal vollständige erwartete 4h-Vorgeschichte samt Signal-ATR-Vorlauf; zehn Sitzungen müssen kalendarisch in der Phase liegen. **Zonen: 36 Entwicklungs- und 16 spätere Fälle; Hülle: 20 und neun.** Alle Hauptgruppenabschlüsse sind bekannt. Lückenfälle und fehlende Abschlüsse bleiben separat sichtbar, nicht als Null/Verlust/Gewinn aufgefüllt.
- Drei gepaarte Vergleiche pro archiviertem Fall: 465 Fallvergleiche mit 930 gespeicherten Pfadinstanzen. Die feste Referenz wiederholt sich; es sind **155 verschiedene feste und 465 verschiedene neue Modellpfade**, keine 930 unabhängigen Trades.
- Die feste Referenz wurde bei jedem Vergleich frisch gerechnet und auf exakte Übereinstimmung mit dem vorherigen Archiv geprüft. Originale Entries, Stops und alte Engine bleiben erhalten. Neue 4h-Entscheidungen können keine fehlende erwartete Quellkerze still überspringen.
- Kosten unverändert: 5bp Gesamtspread plus 5bp Slippage je Seite. R = kostenbehafteter Kaufpreis minus ursprünglicher Stop, Stopverkaufskosten/Gaps können Verluste größer als −1R erzeugen. Modellfüllungen sind keine bestätigten Brokerfüllungen.
- Depots starten je Phase/Modell unabhängig mit 2.000 USD, maximal 1 % geplantem Risiko, 25 % Allokation je Position, fünf gleichzeitigen Positionen und einer je Aktie; fraktional und ohne Hebel. Keine Entryauswahl nach zukünftiger Pfadvollständigkeit. Alle Hauptgruppen-Depots wurden vollständig beobachtet und geschlossen; kein datenbedingter Halt.

## Ergebnis 1: Exit beim gescheiterten Retest

In der Zonen-Entwicklung verbessern sich acht Einzeltrades, sechs verschlechtern sich, 22 bleiben gleich. Trotzdem sinkt die mittlere Entwicklung von **+0,263R auf +0,148R**, weil die Verschlechterungen insgesamt größer ausfallen. Fünf ursprüngliche Gewinner werden durch den frühen Exit zu Verlusten.

In der späteren Phase verbessern sich zwei, sechs verschlechtern sich, acht bleiben gleich. Vier ursprüngliche Gewinner werden zu Verlusten. Die mittlere Entwicklung sinkt von **+0,581R auf +0,306R**. Acht der 16 Fälle enden durch die neue Regel; Stopkontakte werden verhindert, aber spätere Erholungen ebenfalls abgeschnitten.

**Urteil:** Für die Zonen-Retests in dieser Form kein guter Standardexit. Ein bestätigtes Zurückfallen unter die alte Zone ist hier nicht zuverlässig gleichbedeutend mit dauerhaft gescheitertem Trade. Die Hüllengruppe verbessert ihre mittleren R leicht, bleibt in der Entwicklung jedoch negativ; das spätere Hüllendepot wird trotz leicht höherer mittlerer Einzeltrade-R etwas schlechter. Unterschiedliche Risikobeträge und Kapitalzeitpunkte sind mitzubeachten.

## Ergebnis 2: Zeitexit nach fünf Sitzungen ohne Nettoplus

Zonen/Entwicklung: acht vorzeitige Zeitexits, mittlere Entwicklung **+0,226R** statt +0,263R; vier spätere Gewinner werden zu Verlusten. Spätere Phase: sechs vorzeitige Zeitexits, **+0,367R** statt +0,581R; drei spätere Gewinner werden zu Verlusten.

**Urteil:** Die feste Fünf-Tage-Geduld ist für diese Fälle zu kurz bzw. die Nullschwelle unterscheidet nicht zuverlässig Erholungskandidaten von dauerhaft schwachen Trades. Auch die Hüllenvarianten verschlechtern ihre Depotergebnisse. Daraus folgt keine belegte bessere Frist von sechs, sieben oder acht Tagen; diese nachträglich auf denselben Fällen zu suchen wäre eine neue Optimierungsrunde.

## Ergebnis 3: Gewinnschutz ab +1R mit zwei ATR Abstand

Zonen/Entwicklung: zwölf Aktivierungen, 53 protokollierte Anhebungen. Vier Fälle verbessern sich, zwei verschlechtern sich, 30 bleiben gleich. Der Gewinnanteil steigt von **47,2 % auf 52,8 %**, die mittlere Entwicklung sinkt aber leicht von **+0,263R auf +0,252R**. Die beiden größten ursprünglichen Entwicklungsgewinne zusammen werden von +13,36R auf +9,54R reduziert. Eine höhere Trefferquote bedeutet hier nicht automatisch höheren Erwartungswert.

Spätere Zonenphase: sechs Aktivierungen und 34 Anhebungen. Zwei Fälle verschlechtern sich, 14 bleiben gleich, kein Fall verbessert seinen Abschluss. Mittlere Entwicklung **+0,544R** statt +0,581R, Gewinnanteil unverändert 68,8 %. Die beiden größten Gewinner bleiben in dieser Phase erhalten.

**Urteil:** Keine bestätigte Ertragsverbesserung. Als mögliche Risikovariante interessanter als die beiden Frühverkaufsregeln, weil sich der Entwicklungs-Depotdrawdown deutlich reduziert. Dieser Vorteil ist bisher nur in einer Phase beobachtet. Nicht als allgemein überlegenen Gewinnschutz bezeichnen.

## Modellierte Zonen-Depots

| Exit | Entwicklung | max. 5m-Drawdown | spätere Phase | max. 5m-Drawdown |
|---|---:|---:|---:|---:|
| Feste anfängliche Safety | **+12,23 %** | −5,41 % | **+7,21 %** | −1,85 % |
| Gescheiterter Retest | +7,45 % | −5,41 % | +5,59 % | −2,80 % |
| Fünf Tage ohne Fortschritt | +11,70 % | −5,41 % | +6,11 % | −2,70 % |
| Gewinnschutz +1R / 2ATR | +12,17 % | **−3,49 %** | +6,89 % | −1,85 % |

Jeweils eigenständiger Start mit 2.000 USD; keine EUR-Umrechnung. Entwicklung umfasst 220, die spätere Phase 73 Sitzungen. Phasenrenditen weder addieren noch als Jahresrenditen behandeln. Bei früheren Exits wird Kapital früher frei: feste Referenz 32/zehn angenommene Zonenpositionen, gescheiterter Retest 33/13, Zeitexit 33/elf und ATR-Schutz 34/zehn. Es sind die gleichen verfügbaren Signalgelegenheiten, aber nicht zwingend die gleichen tatsächlich gehaltenen Positionen. Der Depotvergleich enthält diesen legitimen Kapital-/Zeitplaneffekt. Ein niedrigerer Depotdrawdown ist deshalb nicht gleichbedeutend mit höherer gepaarter Einzeltrade-R.

Der gemessene Drawdown nutzt 5m-Schlussbewertungen; zwischen den Bewertungen können größere Rückgänge auftreten. Ein Datenloch während einer gehaltenen Position hätte den Lauf angehalten. Die zusätzlichen Entries wurden nicht mit Wissen über spätere Gewinne oder Kursabdeckung ausgewählt.

## Unsicherheit und Grenzen

Die gepaarte R-Differenz ist bei den Zonen in beiden Phasen für alle drei neuen Varianten negativ. Die beschreibenden Aktie-/Quartal-Blockintervalle sind in den vollständigen Tabellen erhalten. Sie sind nicht für die Auswahl zwischen Geometrien, Familien und mehreren Exitideen korrigiert und bei kleinen Gruppen teils diskret. Keine Behauptung statistisch gesicherter Überlegenheit oder zukünftiger Gewinnwahrscheinlichkeit.

Die feste Referenz hängt in der Entwicklung deutlich an zwei großen AMD-Gewinnern; ohne beide wäre ihre mittlere R negativ. Die neuen Varianten beseitigen diese Konzentration nicht zuverlässig. Die Hauptauswahl mit vollständiger Vorgeschichte verbessert die Vergleichbarkeit, ersetzt aber keine vollständigere Marktdatenquelle, breitere vorab definierte Aktienauswahl oder frische unabhängige Zeiträume. Es gibt weiterhin keinen Vergleich aller hier getesteten Exits mit passenden zufälligen Entries und denselben Ausstiegsregeln; Markt-/Entry-Überlegenheit ist damit nicht bewiesen.

## Prüfung, Werkzeuge und Betrieb

Neue isolierte `retest_variants.py`, `tools/retest_variant_study.py`, `tools/retest_variant_verify.py` und `tools/retest_variant_report.py`; keine Änderung der vorhandenen Entry-, Safety-, Web- oder Worker-Defaults. Vorbereiteter Gesamtvertrag vor allen Läufen, feste Reihenfolge der drei Varianten und gespeicherte Entwicklungsentscheidung vor jeder späteren Phase. Laufdateien prüfen Regeln, Quell-/Codehashes und Checksummen; geänderter Code erfordert neues Ausgabeverzeichnis.

- **245 Python-Tests je unter 3.12/3.13**, jeweils ein bestehender Windows-Symlink-Skip, **35 JS-Tests**. 16 neue Gegenbeispiele: feste Zone/Docht/Schluss, Latenz und Overnight, alte Safety bis Exit, Netto-/Nullgrenze am fünften Tag, positive Fortsetzung, keine Aktivierung durch Hoch allein, ATR-Monotonie/Gap, Missing-Quellen/-Pfad, Entryverfügbarkeit, Zukunftsimmunität sowie unabhängige Bestätigungszeitprüfung und Negativproben.
- Separater Prüfer rekonstruiert **155 eindeutige feste Referenzen, 465 neue Pfade, 357 Entscheidungs-/Stopereignisse und 24 Kapitalledger**. Eigene Kalender-/Quellfolge, manuelle ATR-/Zonenentscheidung, unabhängige Decimal-P/L/R und bestehender separater Cash-/Risikoauditor. Modellkonsistenz ist keine unabhängige Marktvalidierung.
- Keine Browserprüfung, weil keine Webkomponente geändert wurde. Keine Providerabrufe, Orders, Nachrichten, Containeränderungen oder neuer Upload. Persönliche Zeichnungen, Datenbanken und Secrets bleiben unverändert.

Aus dem Anwendungsordner, zuerst vorbereiten:

```text
python tools/retest_variant_study.py --archive artifacts/retest-exits-20261022-b --data artifacts/safety-universe-20261020-b/data --root artifacts/retest-variants-20261022-a --stage prepare
```

Dann in der Reihenfolge `failed_retest`, `time_no_progress`, `atr_gain_stop` jeweils denselben Befehl mit `--variant NAME --stage development`, anschließend `--variant NAME --stage validation` ausführen. Vorherige Variante muss abgeschlossen sein; keine Übernahme besser aussehender Parameter. Prüfen und Tabellen erzeugen:

```text
python tools/retest_variant_verify.py --root artifacts/retest-variants-20261022-a --data artifacts/safety-universe-20261020-b/data
python tools/retest_variant_report.py --root artifacts/retest-variants-20261022-a --output RETEST-EXIT-VARIANTEN-TABELLEN.md
```

`--data` ist der tatsächliche bestehende Datenpfad mit `datasets/`; im Container denselben `TORI_DATA_DIR` erhalten, keinen zweiten Produktionsbestand anlegen. Exakte Wiederholung benötigt die privaten gepinnten Daten und das vorherige Retest-Archiv. Laufartefakte/Marktdaten sind nicht Teil des Repositorys. Finaler lokaler Vertrag `faf62307eb52ac09691b9d9de38698e21a66ca130d6ed3efcd2b936b4024eb21`, Belege unter `artifacts/retest-variants-20261022-a`.

## Fazit und Verbesserungsvorschläge

1. **Feste grüne Absicherung als Ertragsreferenz behalten.** Keine der drei Varianten rechtfertigt, sie automatisch zu ersetzen. Insbesondere beide Frühverkaufsregeln nicht pauschal kombinieren; ihre beobachteten Nachteile würden dadurch nicht automatisch verschwinden.
2. **ATR-Schutz als getrennte Risikohypothese erhalten.** Vor weiteren Ergebnissen festlegen, wie viel Ertrag man für weniger Rückgang abgeben würde. Auf frischen Daten prüfen, ob der Drawdownvorteil wiederkehrt. Nicht nachträglich 1,5/2,5/3ATR auf diesen Fällen durchprobieren und den besten Wert zum Standard erklären.
3. **Die schwachen Entries genauer beschreiben.** Verfügbare Tages-/Wochenstruktur, Abstand zur Safety, ursprüngliche Reaktionszahl und Raum als Diagnosemerkmale auswerten. Der bloße Rückfall unter Orange und die fünftägige Nullschwelle trennen spätere Gewinner hier nicht ausreichend. Neue Entrygrenzen erst als eigene Hypothese mit getrennter Prüfung behandeln.
4. **Mehr unabhängige Evidenz vor mehr Exitkomplexität.** Vollständigere Datenabdeckung, vorab definiertes breiteres Universum und bislang nicht zur Auswahl verwendete Zeiträume. Große Gewinner/Verlustserien, Depotdrawdown und einzelne Branchen-/Aktienbewegungen getrennt beobachten. Die zehn Tage sind weiterhin eine Forschungsgrenze, kein belegtes optimales Take Profit.
5. **Hermes zunächst als Beobachter einsetzen.** Ursprüngliche Linien, Entrygrund, Schutzstop, Modellstatus und späteren tatsächlichen Modellabschluss speichern/erklären. Die interne JSON-Grundlage ist da; ein neuer Dauerlauf oder Benachrichtigungsdienst wurde in diesem Versuch nicht eingerichtet.
