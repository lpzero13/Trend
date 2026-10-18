# Separater Tori-Einstiegsmodus

Stand: 18.10.2026 · `tori-entries-1`. Experimentelle, nachvollziehbare Operationalisierung der eingereichten Kriterien. Keine verifizierte Eins-zu-eins-Kopie der Videos, keine belegte Handelsstrategie. Keine Take-Profits, Ausstiege, Orders oder realisierten Gewinne in diesem Modus.

## Auswahl und Abgrenzung

Unter **Forschung → Untersuchungsmodus → Tori-Kriterien · alle Einstiege im Zeitraum** auswählen. Die bisherige Forschung mit Zufallsstarts bleibt separat wählbar und Standard. Bestehender Zeitplan, manuelle Chartanalyse, Rays und Messungen werden durch diese Auswahl nicht geändert. Erst „Einmal untersuchen“ startet einen Auftrag; „Automatik übernehmen“ ändert ausdrücklich den Zeitplan. Regeländerungen erfordern neue Aufträge.

Tori läuft über jede vorhandene abgeschlossene 4h-Kerze des gewählten Entwicklungszeitraums. Es gibt keine Auswahl nur des ersten Bruchs nach einem Zufallsstart. 365 Kalendertage Vorlauf und der reservierte spätere Holdout bleiben geschützt. Datumsfelder verwenden New Yorker Börsenzeit, das Enddatum ist einschließlich. Ohne Datumswahl wird der verfügbare Entwicklungsteil verwendet. Der Bericht nennt die tatsächlichen Grenzen; ein gewähltes Datum umgeht Vorlauf/Holdout nicht.

## Zwei Arten der Fixierung

- **Linienpaare verfolgen (`tracked`, Standard):** Vor jeder neuen Kerze bekannte, bestätigte Linienpaare aufnehmen. Frühere Setups behalten ihre ursprünglichen Anker und werden bis zur Ungültigkeit oder zum Ablauf weiter geprüft. Eine neue automatische Linie entfernt kein altes Setup. Die rote Ausgangslinie entspricht der gemeinsamen 4h-Auswahl; nicht jede beliebige äußere Linie wird automatisch zu einer neuen Einstiegsfamilie.
- **Nur zu X fixieren (`snapshot`):** Genau ein Linienpaar aus den abgeschlossenen Daten vor der ersten ausgewählten 4h-Kerze aufnehmen. Danach keine neuen Paare. Das ist der explizite Test „Was wäre mit den damaligen Linien passiert?“. Fehlt zu X ein bestätigtes vollständiges Paar, gibt es kein Setup. Ein anderes Startdatum wählen statt spätere Anker rückwirkend einzusetzen.

Die grüne Linie kann entweder genau wie im automatischen Chart ausgewählt werden (`chart`) oder als die nächste bereits bestätigte gültige 4h-Hüllenlinie unter dem damaligen Schluss (`nearest_confirmed`, Standard). Diese Alternative setzt den Tori-Gedanken einer näheren bestätigten Safety Line um. Sie verwendet keine späteren Tiefs. Jedes neue Ankerpaar ist eine getrennte Version. Grün wird innerhalb eines laufenden Setups nicht nachträglich ersetzt. Um exakt das im automatischen Chart ausgewählte Paar zu vergleichen, **snapshot + chart** wählen.

Die begrenzte Weiterbeobachtung einer alten roten Linie lässt auch einen vorübergehenden Docht darüber zu; ein solcher Docht erzeugt noch keinen Entry. Das ist eine ausdrücklich eigene Beobachtungsregel gegenüber der jederzeit neu aufgebauten aktuellen Wick-Hülle. Die grüne Setup-Linie darf vor dem Entry nicht verletzt werden. Alte Linien werden nicht unbegrenzt weiter als Signale verwendet.

Im Snapshot-Modus bleibt auch die ursprüngliche 1D-Linienüberlagerung erhalten. Kontextbedingungen werden trotzdem zum jeweiligen Bestätigungszeitpunkt mit den dann abgeschlossenen Daten geprüft und separat protokolliert. Im Verfolgungsmodus wird der Tageslinienstand am Ausbruch für das Setup archiviert.

## Drei getrennte Einstiegsvarianten

1. **Ausbruch:** Vorheriger Schluss auf/unter der ursprünglichen roten Projektion, neuer abgeschlossener Schluss darüber. Puffer, Körper, Kontext und Risikogeometrie müssen an dieser Signalkerze passen. Ein abgelehnter direkter Ausbruch verhindert nicht die beiden späteren Varianten.
2. **Ausbruch + Horizontalhoch:** Dasselbe Setup wartet zusätzlich auf einen Schluss mit Puffer über dem höchsten Hoch der festgelegten Zahl von Kerzen **vor dem Ausbruch**. Dieser Deckel bleibt fest; spätere Kerzen schieben ihn nicht nach oben. Die Bestätigung kann auf der Ausbruchskerze oder später erfolgen. Schwaches Momentum lässt diese Variante zunächst warten.
3. **Retest:** Erst eine spätere Kerze darf die Zone um die ursprünglich gebrochene rote Linie testen. Tief in der Zone, Schluss über ihrem oberen Rand und die übrigen Kriterien müssen passen. Ohne passenden Rücklauf gibt es keinen Retest-Entry. Eine schwache erste Berührung kann weiter beobachtet werden. Schluss unter dem unteren Zonenrand verwirft die ausstehende Bestätigung; Grün-Verletzung verwirft alle noch nicht eingestiegenen Varianten.

Die vollständigen Zustände sind wartend, Einstieg beobachtet, abgelehnt, abgelaufen und am Zeitraumende unvollständig. Bereits beobachtete Einstiege werden durch spätere Kerzen nicht gelöscht. Ein noch wartendes Setup am Daten-/Holdout-Rand ist kein verlorener Trade. Ohne Ausstiegsmodell werden parallele Varianten nicht als ausführbare Depotpositionen zusammengelegt.

## Konkrete Testannahmen

Alle folgenden Werte sind im Auftrag archiviert und in der Oberfläche einstellbar. Sie wurden nicht anhand späterer Gewinne optimiert.

| Merkmal | Standard und genaue Bedeutung |
|---|---|
| Kontakte | Rot mindestens 2, Grün mindestens 2; Toleranz des gemeinsamen Kerns 0,01 USD. Zusammenhängende Kontaktkerzen zählen als eine Episode; nächste Episode frühestens 2 Kerzenpositionen nach dem letzten Kontakt. |
| Alter | Mindestens 7 Kalendertage von rotem A bis zur Ausbruchsbestätigung. |
| Vorläufig / qualifiziert | Mindestens 3 eigenständige Kontakte beider Linien und mindestens 7 Tage rotes Alter ergeben die qualifizierte Gruppe. Alle übrigen Fälle bleiben separat vorläufig; keine A+/A-/B-Zertifizierung. |
| Schluss über Rot | Mindestens 10 Basispunkte über der ursprünglichen Projektion; der bloße Docht reicht nicht. |
| Körper/Momentum | Positiver Körper, mindestens 0,25 ATR, mindestens 50 % der Kerzenspanne, Schlussposition mindestens 65 % vom Tief Richtung Hoch. Die Eröffnung muss nicht schon über Rot liegen. |
| ATR | Einfacher Mittelwert von 14 True Ranges der bereits geschlossenen 4h-Kerzen vor der Bestätigung; keine Wilder-Glättung. Fehlender Pflichtwert blockiert. |
| Safety-Geometrie | Grün positiv unter Rot; Signaltief verletzt Grün nicht. Abstand vom Bestätigungsschluss zu Grün maximal 3 % und maximal 2 ATR. |
| Kontext | Standard: Tagesstruktur darf nicht fallen. Bestätigte 2-links/2-rechts-Swinghochs und -tiefs: beide höher = steigend, beide tiefer = fallend, sonst gemischt. Gemischt ist zulässig, unbekannt blockiert. Optional Tag/Woche/Monat oder Kontext nur protokollieren. |
| Woche/Monat | Aus Tagesdaten nur abgeschlossene vollständige XNYS-Sitzungsgruppen aggregieren. Offene/fehlende Perioden werden nicht vorzeitig verwendet. Reicht die Historie nicht für bestätigte Swings, bleibt der Kontext unbekannt. |
| Horizontalhoch | Höchstes Hoch der letzten 20 abgeschlossenen 4h-Kerzen vor dem Ausbruch, anschließend fest. |
| Raum nach oben | Nächster bekannter Widerstand aus bestätigten 4h-Swinghochs der letzten 250 Kerzen und der bekannten roten Tageslinie. Mindestens 2 Safety-Abstände, falls ein solcher Widerstand bekannt ist. Ohne bekannten Widerstand bleibt der Wert ausdrücklich unbekannt und ist kein harter Ausschluss. Das ist kein Take-Profit. Wochen-/Monatswiderstände sind noch nicht enthalten. |
| Laufzeit | Höchstens 60 weitere 4h-Kerzen ab Aufnahme eines Setups; horizontale/Retest-Bestätigung höchstens 12 Kerzen nach dem Ausbruch. Die frühere Grenze gilt. |
| Retest-Zone | Gemeinsamer Forschungsparameter, Standard ±20 Basispunkte um die ursprüngliche rote Projektion. |

Ausdrücke wie „sauber“, „kräftig“ und „nahe“ werden damit prüfbar, aber nicht endgültig als beste Definition behauptet. Deutsche Uhrzeitverbote werden nicht auf den Alpaca-US-Test übertragen. Erweiterte Sitzungen sind möglich und nicht automatisch ausgeschlossen. Bounce-Einstiege an Grün bilden weiterhin eine eigene, noch nicht implementierte Familie.

## Signal und beobachteter Einstieg

Bestätigung am geschlossenen 4h-Balken, Verfügbarkeit standardmäßig 900 Sekunden später. Dann wird die erste vorhandene **1h-Eröffnung** verwendet. Dabei wird nur deren Eröffnungspreis gelesen; ihr späteres Hoch/Tief entscheidet nicht rückwirkend über den Kauf. Vorher bereits verfügbar gewordene Stunden-/4h-Kerzen dürfen die Safety-Bedingung ungültig machen.

An der Eröffnung werden Safety-Abstand, Lage über dem Auslöser und Raum zum damals bekannten Widerstand erneut geprüft. Ein ungünstiges Gap kann einen bestätigten Kandidaten deshalb noch ausschließen. Die Safety-Referenz bleibt der bei der Bestätigung bekannte Preis der fixierten grünen Linie; sie ist keine simulierte Stoporder. Eine spätere Verletzung nach dem Entry wird hier nicht als Ausstieg berechnet.

Das Stundenraster ist gröber als eine echte Ausführung. Spread, verfügbare Quotes, Slippage und tatsächliche Fill-Verfügbarkeit sind nicht bewiesen. Historische Daten enthalten den heutigen Anbieterstand, IEX ist ein Einzelplatz, Rohkurse können Kapitalmaßnahmen enthalten. Es gibt keinen Live-Scanner mit Orderausführung.

## Bericht und Chart

Standardmäßig zeigt der Tori-Bericht **nur Setups mit Einstieg**; „Alle Setups einschließlich Ablehnungen“ zeigt auch Fehlversuche. Die Tabelle blättert in Seiten von 50 Linienpaaren. Die Zusammenfassung umfasst immer alle Paare. Je Variante/Qualitätsgruppe werden rohe Entries und eindeutige Kombinationen aus Dataset/Einstiegszeit getrennt gezählt. Dieselbe Kerze unter zwei verschiedenen Linienpaaren ist nicht zweimal unabhängige Evidenz; auch Ausbruch/Horizontal/Retest können denselben Einstieg ergeben.

„Prüfung“ zeigt gemessene Werte, bestandene, fehlgeschlagene und unbekannte Bedingungen. Das Ereignisjournal enthält Aufnahme, Ausbruch, Warten, Bestätigung, Entry, Ablehnung, Ablauf und Abschneiden des Beobachtungsfensters. „Linienstand“ öffnet den archivierten Stand; „Entry-Kerze“ zeigt die betreffende abgeschlossene 1h-Kerze. Vor dem späteren Ausbruch verwendet der Fallchart den ursprünglichen Aufnahmestand und zeigt keine zukünftigen Entrypreise. Chartprojektionen bleiben Darstellung; Quellwerte erzeugen die Signale.

## Hermes / CLI / API

Beispiel für einen neuen, optional gepinnten Offline-Auftrag:

```json
{
  "symbols": ["AMZN"],
  "entry_mode": "tori",
  "tori": {
    "line_policy": "snapshot",
    "safety_selection": "chart",
    "start_date": "2025-09-04",
    "end_date": "2025-09-20",
    "context": "daily"
  }
}
```

`tori-tool submit --spec <datei.json>`; für Offline-Wiederholung zusätzlich eine passende `dataset_ids`-Zuordnung setzen. `tori-tool report --id <id> --entry-filter entries --limit 50` oder HTTP `GET /api/research/jobs/<id>/report?entry_filter=entries&limit=50`. `entry_filter=all` erhält Ablehnungen. Dieser Filter gilt nur für Tori; die Zusammenfassung bleibt ungefiltert. Bestehende Legacy-Aufrufe/Parameter funktionieren weiter. Journal wie bisher über paginierte `events` lesen.

Der Worker speichert stabile Setup-IDs und atomare Ereignis-/Zustandsupdates in der bestehenden SQLite-Datenbank (Schema bleibt 3). Bei Unterbrechung wird der deterministische Abschnitt erneut durchlaufen und per Upsert fortgeschrieben; keine doppelten finalen Setups. Ein noch nicht abgeschlossener Scan bleibt als solcher erkennbar. Ein Engine-Hash-Wechsel wird weiterhin nicht umgangen. Quellcode bleibt schreibgeschützt betreibbar, Zustand liegt unter `TORI_DATA_DIR`.

## Prüfung vom 18.10.2026

15 zusätzliche Tests: Einzelschritte gegen großen Sprung, zukünftige Schocks, spätere Änderungen der Entry-Stundenkerze, alte Setups trotz neuer Linien, Snapshot-Retest, bestätigte nähere Safety, Kontakt-Episoden, Momentum, fehlender Kontext, Safety-Verletzung, verzögerte horizontale Bestätigung, Eröffnungsprüfung, unvollständiger Rand, geschlossene Wochen/Monate, Deduplizierung, Offline-Queue, Chartanker und Wiederaufnahme ohne Duplikate. Vollständige Suites: 113 Python-Tests jeweils unter Windows/Python 3.12 und 3.13, je ein übersprungener Windows-Symlinktest; 24 JavaScript-Tests erfolgreich.

Echter vorhandener AMZN-Bestand, ohne neue Providerimporte: 674 4h-Kerzen geprüft, 284 Linienpaare. Unter den protokollierten Standardannahmen: direkter Ausbruch kein Entry; horizontale Bestätigung und Retest jeweils zwei Setup-Treffer, aber **derselbe eine eindeutige Einstieg** am 10.09.2025 um 09:00 New York zu 237,34 USD. Das belegt technische Erkennung und Deduplizierung; keine Profitabilitätsaussage und keine vier Trades. Der manuelle Chart, alte Berichte und der bestehende Zeitplan bleiben separat nutzbar. Vor lokalem Dienstupdate konsistentes Backup erstellt. Kein Proxmox-Rollout oder GitHub-Push durch diese Arbeit.
