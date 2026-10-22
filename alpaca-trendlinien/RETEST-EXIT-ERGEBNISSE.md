# Retest mit fester Safety oder nachgezogenem Stop: Bilanz vom 22.10.2026

**Der Zonen-Retest bleibt in diesem internen Modellversuch interessant. Das streng bestätigte Nachziehen bringt gegenüber dem einfachen festen Stop bisher keinen überzeugenden Vorteil.** Es gibt modellierte Gewinne nach Stopverlusten und Kosten; ein praktisch validierter Handelsvorteil ist damit noch nicht bewiesen.

Regeln wurden vor diesem Exitlauf in [RETEST-EXIT-TEST.md](RETEST-EXIT-TEST.md) festgehalten. [Alle Gruppen und Kennzahlen](RETEST-EXIT-TABELLEN.md). Webansicht, laufende Forschungsprofile und Zeitpläne bleiben unverändert. Es wurden vorhandene Daten wiederverwendet, keine Orders oder Nachrichten ausgelöst und kein Container aktualisiert.

## Vergleich und Datenbasis

- 155 archivierte Retest-Fälle: 109 Entwicklung, 46 spätere Phase. Keine neuen Einstiege gesucht oder anhand ihrer Gewinne ausgewählt. Nur `hull_exact` und `swing_zone`, jeweils getrennt; andere Familien/Geometrien bleiben außerhalb dieses Versuchs.
- 25 gepinnte splitbereinigte Alpaca-IEX-Aktien aus dem vorigen Versuch. Entwicklung 02.05.2025–18.03.2026, spätere bereits bekannte Phase 19.03.–02.07.2026. Kein unberührter Holdout; der reservierte finale Zeitraum wurde nicht ausgewertet.
- Hauptgruppe: zum Signal bereits vollständige erwartete 4h-Vorgeschichte ab frühestem Linienanker einschließlich notwendigem ATR-Vorlauf. 56 Entwicklungs- und 28 spätere Fälle erfüllen das. Fünf spätere Fälle haben ihre geplante Zehn-Tage-Grenze außerhalb der Phase; nach dieser reinen Kalenderabgrenzung verbleiben **20 + 36 Entwicklungsfälle und 9 + 16 spätere Fälle** in den beiden Geometrien. Davon sind alle Modellabschlüsse bekannt.
- Fälle mit lückenhafter Vorgeschichte bleiben in eigenen Tabellen. Bei ihnen sind teilweise auch spätere Pfade unbekannt. Unbekannt wird nicht in Gewinn, Verlust oder Null umgewandelt. Überlappende Fälle verschiedener Aktien/Geometrien sind keine unabhängigen Trades.
- `fixed`: archivierter anfänglicher gepufferter Stop, sonst Schlussverkauf zehn XNYS-Sitzungen nach Entrytag. Kein fester Take Profit.
- `higher_low_stop`: gleicher anfänglicher Stop, danach nur mit 2+2 bestätigten höheren Tiefs, höherem Zwischenhoch und gültiger verbundener grüner Linie nachziehen. Stop unter bestätigtem Tief mit 0,25 bekannter ATR, niemals lockern; frühestens fünf Minuten nach Bestätigung wirksam. Ein Schluss unter der schrägen Linie allein verkauft nicht. Das unterscheidet diesen isolierten Stoptest vom vorhandenen breiteren `structure`-Modell mit zusätzlichem Linien-Schlussexit.
- Kein doppelter ATR-Puffer: rekonstruierter Stop muss exakt zum archivierten Stop passen. Strenge frühere Entryfilter werden nicht nachträglich aufgezwungen.
- Stoplücke zum nächsten regulären verfügbaren 5m-Open, sonst Stopberührung zum Stoppreis; danach 5bp Gesamtspread plus 5bp Slippage je Seite. Fehlende erwartete Kerzen werden nicht übersprungen. Modellannahmen sind keine garantierten Brokerfüllungen.

Zwischen den Exitmodellen sind die Einstiege identisch. Zwischen den beiden Geometrien sind es unterschiedliche Entrygruppen; deren Ergebnisse dürfen nicht wie ein gepaarter Geometrieeffekt interpretiert werden.

## Einzeltrades mit vollständiger Vorgeschichte

R = Risiko zwischen kostenbehaftetem Kaufpreis und anfänglichem Stop. Verkaufskosten und Kurslücken können einen Verlust größer als −1R erzeugen. Die Nettorenditen hier beziehen sich auf unabhängige Einzelpositionen; die echte Modellkapitalbegrenzung folgt im nächsten Abschnitt.

| Geometrie / Phase | Exit | Fälle | Gewinnanteil | Ø Netto-R | Ø Gewinn R | Ø Verlust R | Profitfaktor R | längste Verlustserie |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Hülle / Entwicklung | fest | 20 | 35,0 % | −0,329 | +0,931 | −1,007 | 0,50 | 3 |
| Hülle / Entwicklung | nachgezogen | 20 | 35,0 % | −0,324 | +0,931 | −1,000 | 0,50 | 3 |
| Hülle / später | fest | 9 | 66,7 % | +0,420 | +0,861 | −0,462 | 3,73 | 2 |
| Hülle / später | nachgezogen | 9 | 66,7 % | +0,420 | +0,861 | −0,462 | 3,73 | 2 |
| Zonen / Entwicklung | fest | 36 | 47,2 % | **+0,263** | +1,693 | −1,017 | **1,49** | 6 |
| Zonen / Entwicklung | nachgezogen | 36 | 47,2 % | +0,269 | +1,693 | −1,006 | 1,51 | 6 |
| Zonen / später | fest | 16 | 68,8 % | **+0,581** | +1,086 | −0,531 | **4,50** | 3 |
| Zonen / später | nachgezogen | 16 | 68,8 % | +0,539 | +1,086 | −0,666 | 3,59 | 3 |

Profitfaktor R: Summe positiver R geteilt durch absolute Summe negativer R. Ein hoher Wert bei nur neun oder sechzehn Fällen ist keine belastbare zukünftige Erwartung.

Die Zonen-Gruppe mit festem Stop enthält in der Entwicklung **17 Gewinner und 19 Verlierer**. 13 Trades enden am Stop, vier mit Stoplücke, 19 am Zeitende. In der späteren Phase sind es **11 Gewinner und fünf Verlierer**, zwei Stop- und 14 Zeitexits. Gewinnerzahl und Stopzahl sind unterschiedliche Größen: Auch ein Zeitexit kann negativ sein.

Das unterstützt die Idee, kleine Gewinne zuzulassen. Das Entwicklungsplus entsteht aber nicht durch fast ausschließlich kleine Gewinne. Die durchschnittlichen Gewinner sind dort größer als die Verlierer. Einzelne Bewegungen tragen viel bei: die zwei größten Entwicklungsfälle liefern +6,80R und +6,56R, beide AMD. Ohne den besten Fall bleibt die mittlere feste Variante bei +0,076R; ohne die beiden besten läge sie bei **−0,115R**. Das ist eine nachträgliche Konzentrationsdiagnose, keine geänderte Auswahlregel. In der späteren Phase bleibt sie ohne den besten Fall bei +0,368R und ohne die beiden besten bei +0,245R. Überlappende Situationen derselben Aktie sind nicht unabhängig.

Der größte Einzelverlust der vollständigen Entwicklungs-Zonengruppe beträgt **−1,83R**. Ein vorgesehener Stop begrenzt das Kurslückenrisiko nicht exakt auf −1R.

## Bringt das Nachziehen etwas?

Gepaarte Differenz nachgezogen minus fest:

| Geometrie | Entwicklung | beschreibendes 95-%-Blockintervall | spätere Phase | Intervall |
|---|---:|---:|---:|---:|
| Hülle | +0,0046R | 0,0000 bis +0,0138R | 0,0000R | 0,0000 bis 0,0000R |
| Zonen | +0,0060R | −0,0057 bis +0,0318R | **−0,0422R** | −0,1265 bis 0,0000R |

Blockintervalle nach Aktie/Quartal sind beschreibend, bei kleinen Gruppen diskret und nicht für die vorgängige Varianten-/Familienauswahl korrigiert. Keine Signifikanzbehauptung.

Die strengen Regeln ändern nur wenige Abschlüsse: zwei Zonenfälle in der Entwicklung, einen in der späteren Phase. Im späteren XOM-Fall realisiert der nachgezogene Stop einen größeren Verlust (−0,925R) als der feste Stop mit anschließendem Zeitexit (−0,250R), weil der Kurs bis zum Zeitende einen Teil des Rückgangs aufholt. Nachziehen kann einen Rücklauf begrenzen, kann aber auch diese spätere Erholung abschneiden. Hier ist kein allgemeiner Nutzen nachgewiesen.

Die rein diagnostische Auswertung auf gleicher vollständig bekannter Zehn-Tage-Strecke bestätigt das Bild: Zonen/Entwicklung 34 Fälle mit +0,339R fest gegenüber +0,346R nachgezogen; später 16 Fälle mit +0,581R gegenüber +0,539R. Diese nachträgliche Pfadvollständigkeit wird ausdrücklich **nicht zur Depot-Entryauswahl** verwendet.

## Kapital-/Risikosimulation

Jede Phase und Variante startet unabhängig mit **2.000 USD**. Modellannahmen: maximal 1 % vorgesehener Stopverlust pro Position einschließlich Kosten, maximal 25 % Kapitalallokation je Position, maximal fünf gleichzeitige Positionen, nur eine Position je Aktie, fraktionale Stücke und kein Hebel. Kein EUR-Depot oder Währungsgewinn angenommen. Kurslücken können die geplante Risikogrenze überschreiten.

Die Entryauswahl nutzt nur die damals bekannte Vorgeschichte und die Kalendergrenze. **Kein Wissen über spätere Pfadabdeckung, Stop oder Gewinn entscheidet, ob gekauft wird.** Eine Datenlücke während einer noch gehaltenen Position würde den Lauf stoppen. In diesen acht Hauptgruppenläufen kam es zu keinem solchen Halt; alle Positionen wurden geschlossen. Bei Gleichzeitigkeit gilt eine feste Reihenfolge, keine Gewinnerpriorisierung. Übersprungene Einstiege bleiben im Ledger.

| Geometrie / Phase | Exit | geschlossene Positionen | Endkapital USD | Ergebnis | maximaler Drawdown, 5m-Stichproben |
|---|---|---:|---:|---:|---:|
| Hülle / Entwicklung | fest | 19 | 1.904,27 | −4,79 % | −6,10 % |
| Hülle / Entwicklung | nachgezogen | 19 | 1.905,65 | −4,72 % | −6,03 % |
| Hülle / später | fest | 9 | 2.086,91 | +4,35 % | −1,98 % |
| Hülle / später | nachgezogen | 9 | 2.086,91 | +4,35 % | −1,98 % |
| Zonen / Entwicklung | fest | 32 | **2.244,64** | **+12,23 %** | −5,41 % |
| Zonen / Entwicklung | nachgezogen | 32 | 2.245,63 | +12,28 % | −5,41 % |
| Zonen / später | fest | 10 | **2.144,28** | **+7,21 %** | −1,85 % |
| Zonen / später | nachgezogen | 10 | 2.129,79 | +6,49 % | −2,51 % |

Die Phasen sind unabhängig gestartet, unterschiedlich lang und dürfen weder addiert noch direkt als Jahresrenditen verglichen werden. Das sind simulierte Ergebnisse auf bekannten historischen Kursen. Intrabar-Rückgänge zwischen den 5m-Bewertungen können größer sein als der ausgewiesene Stichprobendrawdown. Die 32 bzw. zehn tatsächlich angenommenen Zonenpositionen unterscheiden sich von den 36 bzw. sechzehn unabhängig betrachteten Signalpfaden, insbesondere weil nicht mehrfach gleichzeitig dieselbe Aktie gekauft werden darf.

## Technische Prüfung und Wiederholung

- **229 Python-Tests je unter Python 3.12/3.13**, jeweils ein bestehender Windows-Symlink-Skip, **35 JS-Tests**. Neun neue gezielte Tests für Puffer, Schluss unter Diagonale, Pivotnachbarn, Stopwirksamkeit/Latenz, keine Lockerung/Ankermutation, Gap-/Fehlkurse, Zukunftsimmunität, kausale Historienauswahl, Verfügbarkeit und getrennte Struktur-/Stopzähler.
- Separater Nachrechner kontrolliert **155 eingefrorene Fälle, 310 Modellpfade, 35 Strukturereignisse und acht Kapitalledger**. Eigene Stop-/Pivotrekonstruktion ohne `SafetyState`/`path`, separate Kalender-/Pfaditeration, Decimal-P/L/R und bestehender unabhängiger Cash-/Risikoauditor. Modellkonsistenz ist keine Bestätigung echter Brokerfüllungen oder einer unabhängigen Marktstichprobe.
- Entwicklungsentscheidung vor der späteren Phase gespeichert; unveränderte Parameter. Nach der Präzisierung eines Statistikzählers wurde der finale Lauf in einem neuen Verzeichnis neu gerechnet. Strukturwechsel und tatsächliche horizontale Stopanhebung werden nun separat gezählt; keine Entry-/Exitregel geändert. Private Zwischenläufe bleiben als solche getrennt.
- Kein Browser erforderlich: keine Webkomponente geändert. Bestehende Web-/Forschungs-/Safety-Engines wurden nicht umgestellt. Neue Werkzeuge laufen ausschließlich offline auf vorhandenen gepinnten Datasets; keine persönlichen Zeichnungen, Datenbanken oder Secrets geändert.

Aus dem Anwendungsordner:

```text
python tools/retest_exit_study.py --entries artifacts/entry-discovery-20261021-b --data artifacts/safety-universe-20261020-b/data --root artifacts/retest-exits-20261022-b --stage prepare
python tools/retest_exit_study.py --entries artifacts/entry-discovery-20261021-b --data artifacts/safety-universe-20261020-b/data --root artifacts/retest-exits-20261022-b --stage development
python tools/retest_exit_study.py --entries artifacts/entry-discovery-20261021-b --data artifacts/safety-universe-20261020-b/data --root artifacts/retest-exits-20261022-b --stage validation
python tools/retest_exit_verify.py --root artifacts/retest-exits-20261022-b --data artifacts/safety-universe-20261020-b/data
python tools/retest_exit_report.py --root artifacts/retest-exits-20261022-b --output RETEST-EXIT-TABELLEN.md
```

`--data` ist der explizite bestehende Datenpfad, der `datasets/` enthält. In Proxmox denselben produktiven `TORI_DATA_DIR` verwenden, keinen zweiten stillen Datenbestand anlegen. Archive/Datasets gehören nicht ins Repository. Eine exakte Wiederholung benötigt die privaten gepinnten Dateien; der Code importiert keinen Ersatzbestand.

Vertrag/Enginehashes und Eingabeblockchecksummen werden fixiert. `frozen-entries.json` enthält keine Zukunftslabels aus den früheren Beobachtungen. Der spätere Lauf erfordert die gespeicherte Entwicklungsentscheidung. Checkpoints je Aktie; nach Code-/Regeländerung neuer Laufordner, keine Fortsetzung alter Ergebnisse unter neuem Code. Kapitalergebnisse sind deterministisch wiederholbar.

Finaler lokaler Lauf: `artifacts/retest-exits-20261022-b`. Vertrag `44b6b5f2a5c701a78a930c097c94a99d7787e9634402147dca0f02fd71873298`. Enthält eingefrorene Entries, Phasenblöcke, Ergebnisse, Entscheidung und `verification.json`. Nur Regeln, Werkzeuge und aggregierte Dokumentation werden versioniert.

## Schlussfolgerung

Die einfache Zonen-Retest-Variante mit fester anfänglicher Safety und Zehn-Tage-Zeitexit ist eine brauchbare **Forschungsreferenz**. Sie hat diesen begrenzten Test einschließlich Kosten, Stopverlusten und Kapitalgrenzen bestanden. Das strenge Nachziehen würde ich auf Basis dieser Zahlen nicht als Verbesserung übernehmen. Die Hüllen-Retests sind über beide Phasen weniger konsistent.

Das Entwicklungsplus hängt deutlich an einzelnen großen Gewinnen; kleine Fallzahlen, überlappende Aktienbewegungen, heutige feste Aktienauswahl, IEX-Datenabdeckung und bereits bekannte Zeiträume bleiben wichtige Grenzen. Kein Vergleich dieses Exitversuchs beweist einen Vorteil gegenüber dem Markt oder passenden zufälligen Entries mit identischem Exitmodell. Als nächster Schritt wären unveränderte Regeln auf weiterer unabhängiger Kursabdeckung und anschließend ein gespeicherter Beobachtungslauf sinnvoll. Eine automatische Handelsfreigabe ergibt sich daraus noch nicht.
