# Retest: unabhängiger Zeitvergleich und Beobachter

Stand 22.10.2026, lokaler interner Versuch. **Technische Beobachtung funktioniert;
die bisher interessante Zonen-Retest-Hypothese hat sich im neuen Zeitabschnitt
nicht bestätigt.** Die feste Safety bleibt Vergleichsreferenz, kein als profitabel
freigegebener Standard. Webprofile und Worker bleiben unverändert.

## Was umgesetzt und eingefroren wurde

[Vorabplan](RETEST-BEOBACHTUNG-PLAN.md), [vollständige Tabellen und Diagnose](RETEST-BEOBACHTUNG-TABELLEN.md).
Neue isolierte `retest_observation.py` und CLI-Werkzeuge: ein einmaliger Vergleich
auf bisher nicht zur Ergebnisauswahl verwendeten Daten, Entwicklungsdiagnose und
wiederaufnehmbarer Beobachter. Keine neue Entry-/Exitoptimierung.

Vor Ergebnisauswertung Vertrag, Regeln, Code, Datensatz-IDs, Abdeckungszählungen
und die alten Startzustände gespeichert. Danach **alle 50 Signalzustände** für
25 Aktien × zwei Geometrien eingefroren; erst anschließend Abschlüsse berechnet.
Fortsetzung aus dem 02.07.-Watch-Zustand, ohne passend ausgewählte Neustarts.
Primär Zonen-Retest; strenge Hülle separat als Referenz. Beide nutzen weiterhin
die bestehende kausale Entry-Engine mit gleichem Latenz-/Kostenmodell.

Zeitabschnitt **06.07.–16.10.2026, 74 XNYS-Sitzungen**. Damit wird die vorherige
Reservierung genau für diesen festgelegten Vergleich aufgehoben. Frühere Aussagen
„Holdout nicht ausgewertet“ beschreiben den früheren Prüfstand. **Dieser Abschnitt
ist jetzt verbraucht und darf nicht als frische Bestätigung weiterer Anpassungen
bezeichnet werden.** Eine später veränderte Regel braucht neue Evidenz.

## Ergebnis des neuen Abschnitts

43 rohe Retestfälle insgesamt: 27 Zonen- und 16 Hüllenfälle. Hauptgruppe mit
vollständiger relevanter 4h-Vorgeschichte und zehn Sitzungen kalendarischem Nachlauf:
16 Zonenfälle aus acht Aktien und neun Hüllenfälle aus sieben Aktien. Sechs/fünf
weitere Fälle haben lückenhafte Vorgeschichte, fünf/zwei zu wenig Nachlauf.
Auch ein bereits früh gestoppter später Entry bleibt wegen der vorab einheitlichen
Nachlaufregel außerhalb der Hauptgruppe. Keine Auswahl nach künftig lückenlosem
oder gewinnbringendem Kursverlauf.

| Hauptgruppe | feste Safety | ATR-Schutz +1R / 2ATR |
|---|---:|---:|
| Zonen: positive Abschlüsse | 5 von 16 | 5 von 16 |
| Zonen: mittlerer Nettoabschluss | −0,397R | −0,385R |
| Zonen: Modell-Depotendwert aus 2.000 USD | 1.941,86 USD | 1.941,86 USD |
| Zonen: Modell-Depotrendite | −2,91 % | −2,91 % |
| Zonen: maximaler 5m-Depotdrawdown | −6,22 % | −6,22 % |
| Hülle: positive Abschlüsse | 6 von 9 | 6 von 9 |
| Hülle: mittlerer Nettoabschluss | +1,384R | +1,382R |
| Hülle: Modell-Depotrendite | +10,29 % | +10,27 % |

Je Modell separates USD-Depot mit gleichen Annahmen: 1 % geplantes Risiko, höchstens
25 % Kapital je Position, fünf gleichzeitige Positionen, eine je Aktie, Bruchteile,
kein Hebel, Kosten wie zuvor. Alle vier Depots ohne Datenhalt, alle angenommenen
Positionen geschlossen. Zwölf Zonen-/acht Hüllenpositionen tatsächlich im jeweiligen
Depot; überlappende Einzelentries sind keine zusätzlichen freien Kapitalpositionen.
5m-Schlussbewertungen können intrabar größere Rückgänge verdecken; Brokerfüllungen
und tatsächliche Kosten können abweichen. Das sind Modellresultate, keine Gewinne
oder Verluste eines realen Depots.

Der ATR-Schutz verbessert nur einen der 16 Zonen-Einzelabschlüsse, 15 bleiben gleich.
Dieser KO-Entry wird wegen einer bereits gehaltenen KO-Position von beiden Depots
ausgelassen. Deshalb etwas bessere mittlere Einzeltrade-R, aber identische Depots.
Die Auswahl erfolgte aufgrund der damaligen Position, nicht wegen des späteren
Ergebnisses. Drei Zonenaktivierungen/20 Stopanhebungen führen hier nicht automatisch
zu mehr gewinnbringenden Abschlüssen.

Die Hüllenreferenz ist diesmal positiv. Ihr größter Einzelabschluss ist ein
MSFT-Fall mit +9,64R; ohne diesen liegt die mittlere Einzeltrade-R bei +0,352R.
Nur neun Fälle, zwei davon MSFT; sieben physische Entryzeitpunkte überschneiden
sich mit der Zonenhauptgruppe. Unterschiedliche Linien/Stops und Gelegenheiten
erlauben keinen einfachen kausalen Geometrievergleich. Nach diesem Ergebnis die
Hülle zum Gewinner zu erklären und dieselben Monate erneut zur Bestätigung zu
verwenden wäre eine weitere Auswahl auf bekannten Daten.

## Vorab festgelegtes Entscheidungstor

Für eine erste beschreibende Bestätigung: mindestens 30 Paare aus acht Aktien,
höchstens 0,05R mittlerer Ertragsverzicht, mindestens 20 % relativ geringerer
Depotdrawdown, vollständige Hauptgruppenpfade und ununterbrochene geschlossene
Depots. **Nicht bestanden:** nur 16 Paare und 0 % Drawdownverbesserung. Die kleine
Verbesserung von +0,012R pro Einzelentry reicht nicht. Die Zonen-Entryhypothese
selbst ist hier negativ; ein Stopmodell kann daraus keinen gesicherten Vorteil
machen. Keine Parameteränderung nach diesem Ergebnis.

## Was die Einstiegsdiagnose zeigt

Ausschließlich alte Entwicklung: 36 vollständige Zonenfälle, 17 positiv/19
nichtpositiv. Kontakte und unabhängige Reaktionen haben in beiden Gruppen Median
zwei. Mehr mathematisch erzeugte Kontakte sind damit weiterhin keine belegte
Lösung für die Entryqualität.

Die positiven Entwicklungsfälle haben sogar einen größeren medianen ursprünglichen
Safety-Abstand (5,83 % gegen 2,32 %) und mehr Signalrisiko in ATR (3,48 gegen 1,97).
Auch die bekannte Tages-/Wochenrichtung trennt diese kleinen Gruppen nicht klar.
Das bedeutet **nicht**, dass ein weiter Stop bessere Trades verursacht. Aktien,
Marktphase, Volatilität und wenige große Gewinner können diese Unterschiede
erklären. Keine daraus abgeleitete Mindestdistanz, kein gelernter Entryfilter;
der neue Zeitvergleich bleibt vollständig davon unbeeinflusst. Ein fehlender
Raumwert bleibt fehlend und wird nicht auf null gesetzt.

## Beobachter für Hermes

`tools/retest_observe.py` arbeitet auf einem vorhandenen unveränderlichen Dataset,
ohne Anbieter-/Brokeraufruf. Er speichert atomar:

- Watch-Zustand mit ursprünglichen Linien, Kandidaten und Erklärungen;
- Retest-Entry mit damaligem Stop, Merkmalen und Vorgeschichtsqualität;
- beide getrennten Modellpfade und ihr Ereignisjournal mit stabilen IDs;
- Code-/Regelhash, Datenpräfix und den zuletzt untersuchten Zeitpunkt.

Gleicher Aufruf liefert `newEvents: []`. Ein neues Dataset darf mit identischem
alten Präfix fortsetzen; korrigierte alte Kerzen, veränderte Regeln und rückwärts
gesetzte Zeit erfordern eine neue Generation. Geschlossene Abschlüsse und alte
Stopentscheidungen dürfen sich nicht ändern. `phase_boundary` bei `censored`
bedeutet noch nicht vollständig beobachtet, nicht Verlust oder Gewinn.
`missing_fine_path`/`missing_source_path` bleiben ungeklärt; Daten nicht auffüllen.
Ein Journalereignis ist keine Order oder automatische Handlungsempfehlung.

Journal und Datensätze sind private Laufdaten. `newEvents` ist eine Komfortausgabe;
ein späterer zuverlässiger Sender muss aus dem gespeicherten Journal lesen und
selbst bestätigte Ereignis-IDs führen. Ein Absturz nach Dateischreiben und vor
Stdout darf keine Meldung dauerhaft verlieren. Journal nach `knownAt,eventKey`
sortieren; darin gespeicherte unabhängige Beobachtungen nicht als Depot behandeln.
Die vorhandene `tools/entry_watch_scan.py` liefert separat frühe Near-/Ausbruch-/
Pullback-Erklärungen; dieser neue Beobachter ergänzt die tatsächlichen Retestpfade.

Historischer Realtest mit vorab gewählten AAPL/AMZN: Zwischenstand am 18.08.
speichern, neu einlesen, bis 16.10. fortsetzen und mit Einmallauf vergleichen.
Keine AAPL-Retests, drei AMZN-Retests einschließlich unvollständiger Beobachtung;
alle Entries/Pfade/Watch-Zustände identisch, gleiche Ereignis-IDs, Wiederholung
ohne neue Ereignisse. Für diese beiden Beispiele ist ein neuer flacher
Beobachtungszustand ab 16.10. vorbereitet. **Keine prospektive Performance und
kein gestarteter Dauerdienst.** Werkzeug für weitere Aktien vorhanden; universums-
weiter Import, Zeitplanung, Altersüberwachung und Meldungszustellung noch anbinden.

## Wiederholen und betreiben

Aus dem Anwendungsordner mit den bestehenden privaten Laufbeständen:

```text
python tools/retest_independent_study.py --source artifacts/safety-universe-20261020-b --archive artifacts/entry-discovery-20261021-b --root artifacts/retest-independent-20261022-a --stage prepare
```

Danach unverändert `--stage signals`, erst danach `--stage evaluate`. Keine neue
Konfiguration an ein altes Ausgabeverzeichnis hängen. Vertragskennung
`e7f4112bb6e6fc14ccd6976d83202e2179874a08ab0255acbb4d9b0305e9be14`.

```text
python tools/retest_independent_verify.py --root artifacts/retest-independent-20261022-a --data artifacts/safety-universe-20261020-b/data
python tools/retest_observation_report.py --root artifacts/retest-independent-20261022-a --development artifacts/retest-exits-20261022-b --output RETEST-BEOBACHTUNG-TABELLEN.md
python tools/retest_observation_replay_check.py --root artifacts/retest-independent-20261022-a --archive artifacts/entry-discovery-20261021-b --data artifacts/safety-universe-20261020-b/data
```

Generischer Beobachter: `TORI_DATA_DIR` muss auf den tatsächlichen Bestand mit
`datasets/` zeigen, im Container der bestehende `/var/lib/tori`. Nicht den
Produktionspfad ändern, um einen lokalen Beispielordner nachzubilden.

```text
python tools/retest_observe.py --dataset DATASET_ID --start-at ORIGINAL_REPLAY_START_EPOCH --from-at FIRST_NEW_OBSERVATION_EPOCH --asof CLOSED_DATA_CUTOFF_EPOCH --state PRIVATE_STATE_FILE --seed CHECKED_WATCH_BLOCK
```

`--seed` optional nur beim ersten Start: geprüfter Watch-Block mit `state`,
gleicher Engine/Aktie/Startzeit und `asOf <= fromAt`. Danach dieselbe State-Datei
ohne Seed verwenden. Ein frischer Zustand mit `fromAt=asof` übernimmt keine alten
Positionen; bereits offene reale Positionen müssten ausdrücklich anders erfasst
werden. Keine solche Bestands-/Orderintegration implementiert.

## Prüfung und nächste Entscheidung

**256 Python-Tests je unter 3.12 und 3.13**, jeweils ein bestehender Windows-
Symlink-Skip, **35 JS-Tests**. Elf zusätzliche Gegenbeispiele für Zukunftsimmunität,
Zeit-/Code-/Preisänderung, identischen Präfix unter neuer Dataset-ID, atomaren
Speicherweg, Deduplizierung, unbekannte Pfade, unveränderliche Abschlüsse,
Entscheidungstore und fehlende Diagnosewerte. Separater Prüfer rekonstruiert
**43 Fälle / 86 Exitpfade, 109 ATR-Ereignisse und vier Kapitalledger** mit eigener
Kalender-/ATR-/Decimal-Rechnung. Das belegt Implementierungskonsistenz, nicht
zukünftige Handelsgüte. Keine neue Browserprüfung, Providerimporte, Orders,
Nachrichten, Änderungen am Container oder Upload.

Technisch bereit zur weiteren internen Beobachtung, **fachlich noch nicht bereit
für automatisches Handeln**. Sinnvoll ist jetzt eine unveränderte prospektive
Beobachtung von Hülle und Zone als getrennten Hypothesen, mit manueller Prüfung
der ersten neuen Fälle und sauberer Erfassung ihrer ursprünglichen Linien.
Nicht die Kontakt-/Stopgrenzen so lange auf diesen Monaten drehen, bis das Ergebnis
positiv aussieht. Danach ein vorab definierter Vergleich mit passenden Kontroll-
Entries und denselben Exit-/Kapitalregeln auf neuer Evidenz. Vollständigere
europäische/US-Daten sind ein eigener Adapter-/Datenqualitätsauftrag, kein durch
diese Studie bereits gelöstes Problem.
