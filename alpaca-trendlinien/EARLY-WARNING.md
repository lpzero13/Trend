# Vorwarnscanner: Implementierung und Betrieb

Stand 01.11.2026. Eigener lokaler Forschungsweg, noch kein laufender Alarmdienst.
Die normale Webansicht, persönlichen Zeichnungen, bisherigen Forschungsaufträge
und Entry-/Exitregeln werden nicht umgestellt. Keine neue Laufzeitabhängigkeit.

## Umgesetzt

`early_warning.Radar` verarbeitet abgeschlossene Quellkerzen in streng aufsteigender
Reihenfolge. Er verwendet den gemeinsamen `PilotObserver` mit Master-Geometrie,
bestätigten Kontakten, bekannten Safety-Linien und denselben drei Signalfamilien.
Die Phasen entstehen je Familie; eine Ausbruchsbestätigung beendet nicht den
nachfolgenden roten Retest derselben Herkunft.

1. **Aufbau:** Kandidaten werden intern mit stabiler Fächerherkunft registriert.
2. **Interessant:** Abstand unterschreitet die gewählte ATR-Schwelle. Für Rot muss
   eine bekannte Unterstützung unter dem aktuellen Kurs vorliegen. Horizontale
   Unterstützung wird nicht pauschal ausgeschlossen.
3. **Unmittelbar:** Weniger als 0,5 ATR oder Berührung des Kontaktbereichs. Bei
   gleichzeitigem Erkennen von Stufe 2 und 3 zählt nur ein priorisiertes Briefing.
4. **Abschluss:** Passendes Entry-Signal, Verletzung der ursprünglichen Geometrie,
   Entfernung über 2,5 ATR, Linienablauf oder unbekannter weiterer Verlauf.

Roter Retest verwendet die ursprüngliche gebrochene rote Linie. Safety-Bounce
verwendet nur eine bereits auf der vorherigen Kerze qualifizierte steigende
grüne Linie. Eine neue Qualifikation auf der Entrykerze wird nicht rückdatiert.

Jede Kombination aus Episode, Familie, Policy und Stufe warnt höchstens einmal.
Technische Linienänderungen derselben Herkunft sind kein neuer Alarm. Zwei neue,
bereits bestätigte Kontakte können nach einem abgeschlossenen Aufbau eine neue
Episode begründen; offene Beobachtungen werden dabei nicht abgeschnitten. Alte
Retests behalten ihren ursprünglichen Elternaufbau. Bei Datenlücken werden
laufende Beobachtungen zensiert und die Herkunftsgeneration gewechselt.

## Zwölf vorab definierte Versuchsvarianten

Annäherungsschwellen: **1,5 / 1,0 / 0,5 ATR4h**. Jeweils:

- `distance`: nur Abstand und bekannte Unterstützung;
- `active`: zusätzlich aktive Kursannäherung;
- `compression`: zusätzlich geometrische Verengung;
- `combined`: beide Zusatzmerkmale.

Aktive Annäherung untersucht die letzten drei Kerzen auf derselben **jetzt bekannten**
Geometrie. Der Scanner protokolliert Kurs- und Linienbeitrag getrennt, statt eine
ATR-Veränderung oder einen Wechsel zwischen verschiedenen Linien als Kursschub
zu interpretieren. `lineKnownAtComparison` zeigt, ob die Linie schon am Anfang
des Vergleichsfensters bekannt war. Eine geometrische Rückprojektion über bekannte
Vergangenheitskurse ist keine damalige Signalentdeckung.

Verengung: fallendes Rot, nicht fallendes Grün und positive Restbreite; Restbreite
höchstens die Hälfte der geometrischen Anfangsbreite oder höchstens drei ATR.
Weitere Merkmale werden beschrieben, ohne automatisch zusätzliche Gates zu bilden:
Kontaktklasse und Alter, höhere bestätigte Tiefs, ursprünglicher gepufferter
Stopabstand, Tages-Schluss/SMA200, Datenaktualität und nächster Fächerwiderstand.
`experimentalDistanceClass` bedeutet keine validierte Risikofreigabe.

## Snapshots, Review und Wiederaufnahme

Jede Warnstufe enthält einen unveränderlichen Erkennungszeitpunkt, Originalrot,
Originalgrün, Quellindex, Kontaktbekanntheit und Merkmale. Projektionen verwenden
die unveränderte Linie und den aktuellen ATR, niemals den zukünftigen ATR. Der
geometrische Offset ist kein zusätzlicher Entryfilter, insbesondere kein neuer
Safety-Bounce-Trigger. Die späteren Entryinformationen bleiben getrennt.

Die Studie speichert atomare, geprüfte Aktienblöcke mit Plan-/Code-/Datasetbindung
und OS-Schreiblock. Bei Abbruch bleiben fertige Aktien erhalten; eine unterbrochene
Aktie wird deterministisch neu gerechnet. Es gibt noch keinen persistenten
Kerzen-für-Kerzen-Livecheckpoint. Geänderter Code verlangt einen neuen Studienordner;
keine alte Studie unter neuer Engine fortsetzen.

`review` speichert Stummschaltung, Aufhebung oder Snooze je Familie oder kompletter
Episode. Die Forschungsauswertung ignoriert diese manuellen Präferenzen vollständig.
`briefing --asof` liefert nur aus geeigneten deklarierten historischen Fenstern bis dahin bekannte, noch offene Warnungen samt
Originalsnapshot. Zukünftige Entries/Ausgänge werden nicht ausgegeben. `show` ist
dagegen eine ausdrückliche Forschungsansicht einschließlich späterer Ergebnisse.

## CLI

Aus `alpaca-trendlinien/` mit demselben `TORI_DATA_DIR` wie der Dienst:

```powershell
.venv/Scripts/python.exe tools/early_warning.py all --root artifacts/radar-neu --source artifacts/event-cases-wide-v2-20261031/plan.json --workers 2
.venv/Scripts/python.exe tools/early_warning.py build --root artifacts/radar-neu --workers 2
.venv/Scripts/python.exe tools/early_warning.py evaluate --root artifacts/radar-neu
.venv/Scripts/python.exe tools/verify_early_warning.py --root artifacts/radar-neu --workers 4
.venv/Scripts/python.exe tools/verify_warning_prefix.py --root artifacts/radar-neu --symbols AAPL MSFT AMZN JPM XOM
.venv/Scripts/python.exe tools/report_early_warning.py --root artifacts/radar-neu --output RADAR-ERGEBNISSE.md
```

Optional bei der ersten Vorbereitung `--symbols AAPL,MSFT,AMZN,JPM,XOM` für einen
Pilot. Ein bestehender Quellplan ist erforderlich; diese Werkzeuge importieren
keine Aktien und verweigern Providerabrufe. Ein Git-Clone enthält keine privaten
Quellpläne oder Marktdatasets. Hermes muss auf dem Container einen eigenen passenden
Quellplan aus den vorhandenen verifizierten Beständen verwenden.

```powershell
.venv/Scripts/python.exe tools/early_warning.py briefing --root artifacts/radar-neu --symbol AAPL --policy distance:1 --asof 2023-06-01T20:00:00Z
.venv/Scripts/python.exe tools/early_warning.py show --root artifacts/radar-neu --symbol AAPL --episode EPISODEN_ID --family breakout --policy distance:1
.venv/Scripts/python.exe tools/early_warning.py review --root artifacts/radar-neu --episode EPISODEN_ID --family breakout --mode mute
.venv/Scripts/python.exe tools/early_warning.py review --root artifacts/radar-neu --episode EPISODEN_ID --family all --mode snooze --until 2026-11-10T20:00:00Z
.venv/Scripts/python.exe tools/early_warning.py review --root artifacts/radar-neu --episode EPISODEN_ID --family all --mode unmute
```

Die Chartlinks öffnen das passende Dataset/Datum mit dem normalen Chart. Die
Webansicht bleibt zunächst ohne Tori-Analyse. Für die exakten, beim Alarm gespeicherten
Originalkandidaten ist der beigefügte Snapshot maßgeblich: Der normale Linienfinder
kann zu diesem Datum andere aktuelle Kandidaten auswählen. Eine automatische
Warnsnapshot-Ebene mit Umschalter und Reviewknöpfen ist noch **nicht** eingebaut.

## Auswertung und Grenzen

Die bekannten Fenster 2018, 2021, 2023 und April 2025–März 2026 werden aus dem
referenzierten Plan übernommen. Keine neue Holdout-Auswertung. Pro Aktienfenster
sind mindestens 320 Tage geometrischer Vorlauf erforderlich. Zwischenfenster werden
zur Zustandsfortführung durchlaufen, aber nicht als weitere Testfenster gezählt.

Erfassungsquote bezieht sich auf neu episodenweise deduplizierte gemeinsame
Entry-Signale mit gültiger Anfangsabsicherung. Das ist nicht dieselbe Fallauswahl
wie der frühere 1.790er-Filter und kein Nachweis eines tatsächlichen Fills.
Kontaktqualität bei Warnung und Qualität am späteren Entry werden separat berichtet.

Gemessen werden Warnungen, später erfasste Signale, Vorlauf in Quellkerzen und
Sitzungsdaten, Tageslast einschließlich Nulltagen, Spitzen, bekannte Auflösungen
und zensierte Beobachtungen. Der Rohbruch bzw. die erste Berührung werden zusätzlich
zur späteren Bestätigung ausgewiesen. Negative Berührungsvorläufe dürfen nicht
als rechtzeitiger Landeanflug bezeichnet werden.

Eine am Ende des jeweiligen Fensters noch offene Beobachtung ist unbekannt,
kein Fehlsignal. Eine vorher geschlossene Beobachtung wird durch einen späteren
Entry nicht rückwirkend erfolgreich. Unterschiedliche Schwellen können deshalb
unterschiedliche aktive Erfassungsquoten liefern, ohne dass die größere Schwelle
automatisch eine Obermenge aller erfolgreichen Warnungen ist.

## Noch geplant

- Ein ausgewähltes, versioniertes Scannerprofil im laufenden Betrieb, mit
  inkrementellem Import nach tatsächlichen XNYS-Quellschlüssen und belastbarem
  Datenalter-/Lückenstatus; keine stillschweigende Feedumstellung.
- Datenbankgestützte Zustands-/Versandwarteschlange, Wiederaufnahme nach Neustart
  und überprüfbare Nachrichtendeduplizierung.
- Warnliste in der Webansicht, Originalsnapshot/Aktuell-Umschalter und Reviewknöpfe.
- Explizit eingerichteter Hermes-/Nachrichtenkanal. Python entscheidet; Hermes
  kann formulieren. Ein LLM-Ausfall darf die deterministische Ausgabe nicht verhindern.
- Unabhängige spätere Beobachtung auf neuen Daten. Kein als profitabel bestätigtes
  Handelsprofil, keine Brokerorders oder automatische Containerinstallation.

Erweiterter Bestand: [512-Aktien-Bilanz](EARLY-WARNING-512-BEWERTUNG-20261101.md), [Tabellen](EARLY-WARNING-512-ERGEBNISSE-20261101.md), [unveränderte Kontrollen und zusätzliche Aktien](EARLY-WARNING-512-VERGLEICH-20261101.md). Ursprünglicher Bestand: [69er-Tabellen](EARLY-WARNING-ERGEBNISSE-20261101.md), [Bewertung](EARLY-WARNING-BEWERTUNG-20261101.md).

Der unabhängige Prüfer unterstützt optional bis zu vier Prozesse; ohne `--workers`
bleibt er seriell. Alle Shards müssen disjunkt den vollständigen Bestand abdecken,
bevor die Gesamtzähler verglichen und der Prüfbeleg geschrieben werden.
`tools/compare_early_warning.py --baseline ALTER_ORDNER --expanded NEUER_ORDNER --output VERGLEICH.md`
verlangt geprüfte Läufe, identische Regeln/Fenster und exakt unveränderte Kontrollen.
Die zusätzlichen Aktien werden aus additiven Differenzzählern separat berichtet;
Mediane werden nicht aus Gruppenmedianen gemittelt. Beide Werkzeuge verändern
weder Signallogik noch Parameter oder bestehende Studienblöcke.
