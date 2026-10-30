# Pine-Master-Update vom 29.10.2026

Das vom Nutzer gelieferte [Pine-Skript](reference/tori_master_20261029.pine) ist als zusätzlicher Python-Modus eingebaut. Kennung `fan_master`, Profil `master`, Rechenkern `tori-pine-master-20261029-1`. Die bisherigen Modelle `legacy`, `fan_extreme` und `fan_local` bleiben auswählbar. Es wurde kein fremdes Repository installiert und keine Runtime-Abhängigkeit ergänzt.

## Bedienung

Im Chart **Analysemodell → Pine Master · 29.10.** wählen und **Tori-Analyse einschalten**. Beim normalen Seitenstart bleibt die Analyse ausgeschaltet. 1h, 4h, 1D und 1W benutzen denselben Quellkern. Die bisherigen Datumswahl-/Pfeilfunktionen blättern tatsächliche abgeschlossene Handelskerzen vor und zurück; Wochenenden benötigen keine Sonderbedienung.

In der Werkzeugleiste lassen sich **SMA 50/200** und **Stichtagslinie** getrennt ein-/ausschalten. Die blaue gestrichelte Markierung steht an der letzten ausgewerteten Chartkerze; das Schild nennt ihren tatsächlichen Schluss. Die gesamte MTF-Analyse bleibt durch den globalen Stichtag begrenzt. Es werden keine noch nicht abgeschlossenen Tages-/Wochenkerzen ergänzt.

Die Haupt-Safety ist blau, folgende Safety-Stufen türkis/grün. Widerstände verwenden die Fächerfarben Dunkelrot/Rot/Orange/Gelb. Dickere Linien zeigen die ausgewählte Geometrie, durchgezogene Linien mindestens drei bestätigte Kontakte und genügend Alter; vorläufige Linien sind gestrichelt. Beschriftungen nennen Intervall, Stufe und tatsächliche Kontaktzahl. **Äußere** blendet weitere Fächerstufen ein. Haupt-Safety und engere ausgewählte Safety bleiben unterscheidbar. Orange Bruchlinien eines Forschungsfalls behalten ihre bisherige Bedeutung als ursprüngliche Signallinie.

Die Infobox enthält Haupt-Safety, ausgewählte Safety und SMA-Kontext. **Master-Details** zeigt Clean-Close-Schwelle, Pine-Prüffenster und ein hypothetisches Schlusskurs-Größenmodell. Die Box ist weiterhin einklappbar, auf die verfügbare Höhe begrenzt und bei Bedarf scrollbar; Zusatzwerte verkleinern nicht die Schrift. Große Modellzahlen dürfen nicht als tatsächliche ausführbare Brokerstücke verstanden werden, insbesondere bei splitbereinigten historischen Kursen.

Unter **Fächer-Test** ist das neue Profil für neue Formulare vorausgewählt. Alte Profile sowie ein getrennter Vergleich aller drei Profile sind möglich. Unter **Linien und Bestätigung** stehen zusätzliche Parameter: Safety-Horizont, Widerstands-Horizont, Körper-ATR-Toleranz und Auswahl zwischen engster Safety und Haupt-Safety für den Stop. Die Körper- und separate Widerstandsregel gelten nur im neuen Master-Profil. Alle Parameter werden im Auftrag und als effektive `engineProfiles` im Manifest gespeichert. Ein gebundener Fallchart verwendet diese Parameter; der normale Master-Chart verwendet Standardwerte.

## Übertragene Geometrie

| Bestandteil | Python-Umsetzung |
|---|---|
| Separate Suchräume | Standard 320 Kalendertage für Safety und 150 für Widerstände; gemeinsamer Puffer groß genug für beide |
| Hüllkurve | Historischer Körper-/Dochtvergleich mit jeweiligem damaligem Wilder-ATR |
| Kleine Körperverletzung | Standard 0,05 ATR, Docht wie bisher 0,15 ATR |
| Umgebung des Startpivots | Hüllprüfung erst nach dem konfigurierten rechten Pivotabstand, wie im gelieferten Pine |
| Angepasste Steigung | Ungeeignete rohe Pivotsteigung darf auf die Hülle verschoben werden, wenn der zweite Pivot in seiner historischen ATR-Kontaktzone bleibt |
| Echte Zeichenanker | Zweiter Zeichenpreis liegt auf der angepassten Geraden, Rohpivot bleibt als Kontaktmerkmal erhalten |
| Fächer | Erste Stufe Kontaktabstand fünf Kerzen, spätere Stufen standardmäßig drei; maximal vier Stufen |
| Stufenfortsetzung | Folgt dem letzten passenden bestätigten Kontakt, wie im Update |
| Qualifikation | Mindestens drei getrennt gezählte bestätigte Pivotkontakte und sieben Kalendertage; keine neue Behauptung unabhängiger Reaktionen |
| Haupt-Safety | Erste Safety-Stufe, separat von der engsten gültigen steigenden Safety unter dem Quellschluss |
| Prüffenster | Der Pine-Schnappschuss mit ausgesparten letzten zwei roten Prüfkerzen bleibt als beschriebener Rückblick verfügbar |
| SMA | 50/200 abgeschlossene Quellkerzen, nur Kontext, kein zusätzlicher versteckter Einstiegsausschluss |

Die effektiven Parameter sind konfigurierbare Versuchsannahmen. Ein A+-Label ist weiterhin diese vereinfachte Kontakt-/Altersklasse, nicht das gesamte subjektive Tori-Regelwerk oder ein Rentabilitätsbeleg. Die begrenzten Puffer von standardmäßig 1.800 Quellkerzen / 80 Pivots je Seite bleiben bestehen.

## Bewusste Korrekturen gegenüber dem gelieferten Pine

1. **Kein erfundener zweiter Kontakt:** Der Pine-Fallback setzt `bestTouches := 2`, obwohl seine Ersatzlinie nur einen bestätigten Pivot haben kann. Python kennzeichnet sie als **Hülle**, zeigt die reale bestätigte Kontaktzahl und qualifiziert sie nicht künstlich. Eine Hülle mit nur einem bestätigten Pivot wird nicht als Zwei-Kontakt-Einstieg registriert. Kontaktmarkierungen verwenden die tatsächlichen bestätigten Kontaktpunkte.
2. **Kein Zurückfallen auf beliebig alte Widerstände:** Im Pine kann der alternative Root-Suchlauf die separate Zeitgrenze wieder verlassen. Python hält das Seitenfenster auch für den Fallback ein. Ein noch ungebrochener Master-Kandidat läuft beim Erreichen seines Widerstandshorizonts ab; bereits entstandene Bruch-/Retestepisoden behalten ihre ursprüngliche Geometrie.
3. **Rückwärtsschritt aus dem damaligen Präfix:** Das Pine verschiebt einen Array-Zeiger nach hinten, nachdem die Puffer bereits am späteren Ausgangspunkt beschnitten wurden. Python lädt und berechnet den tatsächlich damaligen Präfix neu. Spätere Kontakte, Pufferverluste und Kerzen können dadurch nicht in den früheren Stand gelangen.
4. **Kerzenschluss bleibt die Wissensgrenze:** `includeTargetBar` aus dem Pine kann eine an ihrem Öffnungszeitpunkt ausgewählte Kerze vollständig auswerten und bei Mitternacht den ganzen Tag hinzunehmen. Python zeigt die vollständige Kerze erst ab ihrem Schluss. Datumswahl bezeichnet weiterhin den Zeitpunkt des verfügbaren Wissens in New Yorker Zeit. Das ist absichtlich keine rückwirkende Freigabe des noch zukünftigen Tagesverlaufs.
5. **SMA nach Datenlücken:** Die Vorlaufzählung beginnt nach einer unbekannten Quellenlücke neu. Alte SMA-Werte werden nicht weiter als aktuelle Werte ausgewiesen; die Plotserie erhält eine Unterbrechung.
6. **Keine vorgezogenen MTF-Entry-Marker:** Ein Einstieg wird nur einer abgeschlossenen Chartkerze zugeordnet, deren Zeitspanne ihn tatsächlich enthält. Ein Einstieg in einer noch offenen Woche wird nicht auf die davor bereits geschlossene Wochenkerze zurückgesetzt.

Ein Chartvergleich mit dem gelieferten Pine ist daher kein Versprechen gleicher Pixel oder gleicher Signale. Neben diesen dokumentierten Korrekturen können Datenfeed, Sessions, Bereinigungsstand und Ladetiefe Unterschiede verursachen.

## Forschung und Ausführung

Der fortlaufende Master-Beobachter verwendet ausschließlich damals verfügbare, bestätigte Quellpivots. Er verfolgt vorab bekannte Linien und friert Originalwiderstand, Kontaktklasse, gewählte Safety und initialen Stop einer Episode ein. Das Pine-Prüffenster in der Infobox ist ein **Schnappschuss-Rückblick** und erzeugt keine rückdatierten Backtest-Entries. Deshalb darf dort „kein neuer Bruch“ stehen, obwohl eine länger verfolgte Originalepisode gerade ein Signal liefert.

Ausbruch und späterer Retest der gebrochenen roten Linie bleiben getrennte Versuche. Haupt-/enge Safety-Auswahl wird beim ursprünglichen Bruch gebunden, nicht nach zukünftigen Ergebnissen ausgetauscht. Nachträglich neu entstehende Fächerlinien ersetzen keine alte Episode. Die Ausführungsregeln aus [TORI-FAECHER.md](TORI-FAECHER.md) gelten unverändert: erwarteter nächster regulärer 5m-Open plus Verzögerung, Kapital-/Risikogrenze, Kosten, Stop-Gaps, konservative OHLC-Reihenfolge und getrennte 5/10/20-Sitzungspfade.

Das Größenmodell im normalen Chart ist wie im Pine ausdrücklich hypothetisch zum bekannten **Quellschluss ohne Kosten/Gaps**. Forschungsfälle zeigen separat den tatsächlichen bedingten Modell-Open und festen Signalstop; ihre Stückzahl verwendet den ausführlicheren Kosten-/Risikovertrag. Kein 3R-Ziel hinzugefügt und keine Brokerorder eingerichtet.

## Hermes / CLI / Betriebsgrenzen

Der API- und Queuevertrag bleibt erhalten. Beispiel für einen Forschungsauftrag mit einer vorhandenen lokalen Dataset-ID:

```json
{
  "entry_mode": "fan",
  "symbols": ["MSFT"],
  "dataset_ids": {"MSFT": "HIER_DIE_VORHANDENE_64STELLIGE_DATASET_ID_EINTRAGEN"},
  "fan": {
    "geometry_variants": ["master"],
    "timeframe": "4h",
    "geometry": {"lookback_days": 320, "action_lookback_days": 150, "body_atr": 0.05},
    "watch": {"safety_choice": "tight"}
  }
}
```

```bash
python tori.py submit --spec DATEI.json
python tori.py analyze --dataset DATASET_ID --engine fan_master --timeframe 4h --asof 2024-06-28T20:00:00Z
```

Alle Befehle mit demselben `TORI_DATA_DIR` wie der Dienst ausführen; im Container `/var/lib/tori`. Normale Chart-/Dataset-/Zufallsrouten verstehen `engine=fan_master`, gebundene Fälle zusätzlich ihren bisherigen Job-/Fallkontext. Alte Geometrien werden numerisch nicht auf die neue Master-Regel umgestellt, gespeicherte persönliche Zeichnungen bleiben getrennt.

Durch den veränderten Enginecode **neue Forschungsjobs anlegen**; alte Aufträge/Beobachter nicht unter neuer Engine fortsetzen. Keine DB-Migration, keine Änderung des produktiven Datenpfads, kein neuer Providerimport und keine zusätzlichen automatischen Benachrichtigungen. Lokalen Dienst nach dem Update regulär neu starten, damit die Python-Routen den neuen Modus kennen. GitHub und Proxmox wurden durch diesen Auftrag nicht aktualisiert.

## Prüfung

- 398 Python-Gesamtfälle unter 3.12.10, ein bestehender Skip, keine Fehler; danach gezielter erneuter API-Test der abschließenden Darstellungsänderung bestanden.
- 60 JavaScript-Tests einschließlich tatsächlichem Chartcontroller, optionaler Aktivierung, farbiger Master-Safety, SMA ein/aus, manueller Chart-Erhaltung und MTF-Marker-Gegenbeispiel.
- Geometrie-Gegenbeispiele für Hüllen-Anpassung, echte drei Kontakte, kürzere spätere Fächerabstände, Ein-Pivot-Hülle ohne erfundene Qualifikation, Cache gegen ungecachte Präfixe und getrennten Widerstandshorizont. Zukunftsänderungen und SMA-Lücken geprüft.
- Master-Forschungsfälle und gebundener Chart verwenden denselben Kern; Auswahl der Haupt-Safety, Stopfixierung, effektives Profilmanifest, Ausbruch/Retest und unveränderter Holdout in automatisierten Tests geprüft.
- Isolierter echter Browser-/Queue-Durchlauf auf vorhandenen lokalen MSFT-SIP-Daten: Formular, Auftrag, Ergebnisse, Originalfall, Vor-/Zurück, Tages-/Wochenwechsel, SMA-/Stichtagsschalter und weitere Fächerstufen. Chart startet ohne Analyse, keine Test-Profitabilität behauptet.
- Kleiner zusätzlicher Offline-Techniklauf mit denselben bekannten MSFT-SIP-Daten bis Juni 2024: 202 Signalfälle (einschließlich überlappender Kontakt-/Einstiegsgruppen), davon 35 qualifizierte Ausbruchfälle und 17 qualifizierte Retestfälle, keine 4h-Quellenlücke. Laufzeit inklusive Einzelfallpfaden etwa 6,5 Sekunden. Das belegt Funktionsfähigkeit, keinen Vorteil gegenüber den bisherigen Varianten. Der gesonderte UI-Auftrag lief bis zur späteren regulären 20%-Holdoutgrenze und enthält deshalb andere Fallzahlen.

Private Technikläufe bleiben ausschließlich unter dem ignorierten lokalen `artifacts/master-update-20261029/`. Keine Marktdatasets, Datenbanken, Zugangsdaten oder persönlichen Zeichnungen gehören ins Repository.
