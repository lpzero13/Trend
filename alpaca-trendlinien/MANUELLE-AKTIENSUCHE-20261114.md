# Manuelle Aktiensuche für Tori

Überarbeitete Anleitung · 14. November 2026

Für die indexübergreifende Finviz-Suche gibt es jetzt [fertige Tori-Setups mit Begründung und Direktlinks](FINVIZ-SETUPS-20261114.md). Die Finviz-Suchen in Abschnitt 1 dieser Anleitung kannst du für einen gezielten Durchgang nach Index weiterverwenden.

## So verwendest du die Kandidatenliste

Sammle alle Treffer, die einen nachvollziehbaren Grund für eine Chartprüfung haben. Die Menge hängt von Markt und Filtern ab. Was heute liegen bleibt, behält den Status **Offen**. So kannst du in einer ruhigen Woche wenige und in einer guten Woche deutlich mehr Titel übernehmen.

Öffne die Datei [MANUELLE-KANDIDATENLISTE.html](MANUELLE-KANDIDATENLISTE.html) in deinem Browser. Füge pro Suche die Ticker ohne Spaltenüberschrift und den Namen des Suchprofils ein. Wiederholte US-Ticker werden zusammengeführt und behalten ihre Quellen, Notizen und ihren Prüfstand. Du kannst direkt zu TradingView oder für US-Symbole zum lokalen Tori-4h-Chart wechseln. Der Tori-Link verwendet die Standardadresse auf Port 8765. Die Liste speichert deine Arbeit in diesem Browser. Über **Liste sichern** exportierst du sie als JSON und kannst sie später wieder zusammenführen.

| Suchweg | Wann er dir neue Kandidaten liefert | Zugang |
|---|---|---|
| Finviz | Rücklauf im positiven größeren Verlauf oder Kurs nahe einem markanten Hoch | Geprüfte Direktlinks |
| ChartMill | Enge Konsolidierung bei technisch stärkeren Titeln | Vorkonfigurierter Screen, Zugriff abhängig vom Konto |
| TradingView | Von einer Branche oder einer Watchlist direkt in die einzelnen Charts | Screener und Heatmap, Funktionen abhängig vom Konto |
| StockCharts | Selbst definierte Handelsspanne mit nachvollziehbaren Regeln | Eigener Scan im Mitgliederbereich |

Nutze die Wege parallel. Eine Aktie mit zwei Quellen ist deshalb vor allem leichter wiederzufinden. Rücklauf und Hochzone können denselben Kursverlauf beschreiben, daher zählt die Anzahl der Trefferquellen nicht als Qualitätsnote.

## 1. Breite Vorauswahl mit Finviz

Öffne die vorkonfigurierten Suchen. Der gemeinsame Startwert ist ein Kurs über 10 USD und ein durchschnittliches Tagesvolumen über 500.000 Stück. Finviz berechnet den Volumendurchschnitt über drei Monate. **Week** und **Month** beziehen sich auf fünf und 21 Handelstage. [Definitionen von Finviz](https://finviz.com/help/screener)

| Universum | Rücklauf | Hochzone |
|---|---|---|
| S&P 500 | [Öffnen](https://finviz.com/screener/stocks?v=111&ft=4&f=idx_sp500,sh_avgvol_o500,sh_price_o10,ta_perf_4wup,ta_perf2_1wdown&o=-marketcap) | [Öffnen](https://finviz.com/screener/stocks?v=111&ft=4&f=idx_sp500,sh_avgvol_o500,sh_price_o10,ta_perf_4wup,ta_highlow52w_b0to5h&o=-marketcap) |
| Russell 1000 | [Öffnen](https://finviz.com/screener/stocks?v=111&ft=4&f=idx_rui,sh_avgvol_o500,sh_price_o10,ta_perf_4wup,ta_perf2_1wdown&o=-marketcap) | [Öffnen](https://finviz.com/screener/stocks?v=111&ft=4&f=idx_rui,sh_avgvol_o500,sh_price_o10,ta_perf_4wup,ta_highlow52w_b0to5h&o=-marketcap) |

- **Rücklauf** kombiniert unter **Technical** die Einstellungen **Performance = Month Up** und **Performance 2 = Week Down**. Damit findest du einen schwächeren Abschnitt in einem insgesamt positiven Monat.
- **Hochzone** kombiniert **Month Up** mit **52-Week High/Low = 0–5 % below High**. Das Hoch liefert eine Zone, in deren Nähe du mögliche Deckelungen im Chart prüfst.
- **NASDAQ 100** und **DJIA** kannst du im Feld **Index** wählen. Der Russell 1000 dient zur Erweiterung der Suche. Seine Titel überschneiden sich mit den anderen Listen. Für Aktien außerhalb des lokalen Tori-Bestands öffnest du den Chart in TradingView und prüfst dort Symbol und Handelsplatz.

Die Links sortieren nach Marktkapitalisierung. Wenn du nur am Anfang der Ergebnisse schaust, bevorzugst du dadurch große Unternehmen. Gehe weitere Seiten durch oder sortiere probeweise nach Sektor, wenn du die Suche verbreitern willst. Wenn die Standardliste zu viele wenig brauchbare Charts liefert, schärfe gezielt einen Parameter, etwa **Average Volume = Over 1M**, oder wähle eine passende Branche. Wenn beide Profile in einer Woche zu wenige plausible Charts liefern, kannst du **Month Up** in einer getrennten Suche lockern und beobachten, ob seitwärts laufende Titel dazukommen.

Beim Abruf am 14. November lieferte Finviz für den S&P 500 **68 Rückläufe und 104 Hochzonen**. Im Russell 1000 waren es **148 und 143**. Das sind Rohzahlen je Suche. Überlappungen innerhalb und zwischen den Indizes gehen beim Übernehmen in die Arbeitsliste zusammen.

## 2. Seitwärtsphasen gezielt über ChartMill finden

1. Öffne das veröffentlichte Profil **Technical Breakout Setups** und wähle beim Start des Screens **United States**. Das Profil kombiniert einen Liquiditäts- und Preisfilter mit ChartMills **Setup Quality**, **Technical Rating** und einem Mindestwert für ATR%. [ChartMill-Profil öffnen](https://www.chartmill.com/trading-ideas/202-Technical-Breakout-Setups)
2. Überfliege die Tagescharts der Treffer. Suche mehrere Kerzen mit ähnlichen Hochs oder höher liegenden Tiefs nach einer vorherigen Bewegung. Ein gutes Beispiel für unsere Sichtung ist eine Aktie, die seit mehreren Tagen unter einem sichtbaren roten Widerstand bleibt. Übernimm sie mit der Quelle **ChartMill Konsolidierung**.
3. Verwende **Setup Quality** zur Reihenfolge, sofern deine Ansicht die Spalte anbietet. Der Anbieter beschreibt den Wert als Maß für die technische Struktur mit Merkmalen wie engeren Kursen und erkennbarer Unterstützung. Der veröffentlichte Screen nennt Setup Quality und Technical Rating jeweils ab 7. Die 4h-Linien und Kontakte prüfst du im eigenen Chart. [ChartMill zu den Bewertungen](https://www.chartmill.com/documentation/technical-analysis/indicators/87-Chartmill-Technical-Rating-and-Setup-Quality-scores)

Dieses Suchprofil ist für unser Ziel interessant, weil es eine laufende Konsolidierung als Ausgangslage sucht. ChartMill hat den direkten Abruf aus meiner Umgebung blockiert. Die Anbieterbeschreibung und die Profilparameter sind dokumentiert. Umfang der Ergebnisliste und Kontozugang habe ich nicht am Bildschirm verifiziert.

## 3. TradingView zuerst nach Branchen durchsuchen

1. Öffne die **Aktien-Heatmap** oder die Heatmap-Ansicht des **Aktienscreeners**. Wähle den US-Markt und ein verfügbares Universum wie den S&P 500. Gruppiere nach **Sektor**, färbe nach **1W** und verwende nach Möglichkeit **Mono size**, damit größere Unternehmen kleinere Werte optisch weniger überdecken. Schalte für den Vergleich auf **1M** um. [Heatmap öffnen](https://www.tradingview.com/heatmap/stock/) · [TradingView zur Heatmap-Ansicht](https://www.tradingview.com/support/solutions/43000794279-heatmap-view-mode/)
2. Öffne Gruppen, in denen mehrere Titel über die Woche zulegen oder sich gegenüber einer schwächeren Marktphase halten. Beispiel für eine vergleichbare Rechnung: Liegt eine Aktie über denselben Monat bei +1 % und der Vergleichsindex bei −4 %, beträgt der Vorsprung fünf Prozentpunkte. Prüfe die Zeiträume und nutze einen für das Universum passenden Vergleich. Die Heatmap hilft dir, Gruppen zu finden. Die relative Entwicklung kannst du aus der Performance-Spalte oder im Chart ablesen.
3. Gehe im Screener in die **Chartansicht** oder filtere den gewählten Sektor in der Tabelle. Verwende dieselben groben Preis- und Volumenwerte. Übernimm Titel, deren Tageschart nach einer Bewegung eine Pause oder einen geordneten Rücklauf zeigt. Schau auch in andere Gruppen, wenn du dort eine ähnlich klare Struktur siehst. [TradingView Aktienscreener](https://www.tradingview.com/screener/) · [Anleitung zu Filtern und Chartansicht](https://www.tradingview.com/support/solutions/43000718885-tradingview-screeners-walkthrough/)

Dieser Weg liefert ein anderes Suchsignal. Du startest bei einer Gruppe und findest darin Aktien, die dir in einer nach Marktkapitalisierung sortierten Rücklaufliste leicht entgehen. Für europäische Aktien wählst du den passenden Markt und die richtige Hauptnotierung. Übernimm dann zum Beispiel **XETR:SAP**. Preis und Volumen beurteilst du in der jeweiligen Handelswährung und am gewählten Handelsplatz. Für diese Märkte führt die Arbeitsliste zu TradingView.

## 4. Eine enge Handelsspanne mit StockCharts suchen

Wenn du bereits StockCharts nutzt, kannst du im **Advanced Scan Workbench** einen eigenen Scan manuell ausführen. Öffne **Your Scans → New Scan**, füge den Text ein, wähle den Stand des letzten Schlusskurses, klicke auf **Check Syntax** und dann **Run Scan**. [Anleitung zum Workbench](https://help.stockcharts.com/scanning-and-alerts/technical-scans/advanced-scan-workbench)

```text
[type = stock]
and [group is SP500]
and [close > 10]
and [SMA(20, volume) > 500000]
and [Max(10, high) < SMA(10, close) * 1.03]
and [Min(10, low) > SMA(10, close) * 0.97]
```

Der Entwurf sucht Aktien, deren Hochs und Tiefs über zehn Handelstage innerhalb eines Korridors von ungefähr ±3 % um den 10-Tage-Durchschnitt liegen. Er misst damit eine Handelsspanne auf Tagesbasis. Es bleibt deine Chartaufgabe, innerhalb dieser Struktur sinnvolle 4h-Linien zu finden. Sind die Treffer zu zahlreich, probiere beispielsweise einen Korridor von ±2 %. Du kannst zusätzlich ein separates Profil für **relative Stärke** erproben. Die dokumentierte Klausel `[PctRelative(10,$SPX) > 2]` verlangt mehr als zwei Prozentpunkte Vorsprung gegenüber dem S&P 500 über zehn Handelstage. [StockCharts zu Min und Max](https://help.stockcharts.com/scanning-and-alerts/scan-writing-resource-center/scanning-case-studies/writing-min-max-scans) · [StockCharts zu relativer Performance](https://help.stockcharts.com/scanning-and-alerts/scan-writing-resource-center/writing-scans)

Das ist ein kopierbarer Entwurf auf Basis der dokumentierten Syntax. Der Workbench setzt ein Mitgliedskonto voraus. Den konkreten Scan habe ich dort nicht ausgeführt.

## 5. Welche Charts in die engere Beobachtung kommen

### Tageschart in ungefähr einer Minute

- Stelle reguläre Handelszeiten ein, wenn dein Chart die Option anbietet. Schau grob auf die letzten **drei bis sechs Monate**, mit Augenmerk auf die letzten vier bis acht Wochen.
- Suche erkennbare Hochs und Tiefs, eine nachvollziehbare Bewegung und einen Bereich, an dem der Kurs schon öfter reagiert hat. Bei einer steilen Abwärtsbewegung mit offenen Kurslücken, sehr langen Einzelkerzen oder unklarem Datenstand vergibst du zunächst den Status **zurückstellen**.
- Schau optional auf **SMA 200 im Tageschart**. Notiere „darüber“, „darunter“ oder „unbekannt“ als Kontext. Das passt zur Vorwarnstudie, die Zusatzmerkmale für die Einordnung erfasst. Ein attraktiver Tageschart bleibt auch bei einem Kurs unter dem SMA ein Kandidat für die Sichtung.

### Im 4h-Chart einzeichnen

Beginne mit den Tagescharts, deren Hochs und Tiefs du am klarsten markieren kannst. Halte den Grund in einem Satz fest. Die übrigen Titel bleiben offen und können in der nächsten Runde folgen.

1. Zeige ungefähr **vier bis acht Wochen** und zeichne eine rote Linie an die sichtbaren Hochs, die den Kurs deckeln. Zeichne grün an erkennbare Tiefs, die als Unterstützung dienen. Verwende abgeschlossene Kerzen und gut erkennbare Wendepunkte. Wenn mehrere Linien plausibel sind, notiere die Anker deiner bevorzugten Linie.
2. Markiere die Kontakte je Linie. **Zwei erkennbare Kontakte** genügen für einen vorläufigen Kandidaten. **Mindestens drei über mindestens sieben Kalendertage** entsprechen der im Projekt dokumentierten Kontakt- und Zeitbedingung. Die Prüfung von Toleranz und Ankerbestätigung gehört zur jeweiligen Projektregel. Eine Handzeichnung ist ein eigener Befund.
3. Prüfe am letzten **abgeschlossenen 4h-Balken**, ob der Kurs noch unter der roten Linie liegt und die grüne Unterstützung erkennbar ist. Verwende den Linienwert auf diesem 4h-Balken. Zeichnungen aus dem Tageschart geben Kontext. Gehe zur Beurteilung des Abstands zurück in das Intervall, in dem du die Linie verankert hast.
4. Wenn du den Abstand normalisieren möchtest, füge **ATR(14) im 4h-Chart** hinzu. Für eine Annäherung von unten rechnest du **(roter Linienwert − 4h-Schluss) ÷ 4h-ATR(14)**. Bei 52 USD Widerstand, 50 USD Schluss und 2 USD ATR liegt der Kurs 1 ATR darunter. Prozentabstand zum Schlusskurs ist in dem Beispiel 4 %. Finviz-ATR und Tages-ATR% geben einen Tageskontext. Verwende für diese Rechnung denselben 4h-Chart für Kurs, Linie und ATR. Fehlt dir die 4h-ATR, notiere den Prozentabstand und sortiere vorläufig nach Linienqualität und diesem Abstand.
5. Vermerke einen anstehenden Ergebnisbericht. Bei einem Termin in den nächsten **zwei US-Handelssitzungen** kannst du den Wert mit **Earnings** markieren und nach dem Bericht neu prüfen. Bestätige den Termin bei Bedarf im Kalender des Unternehmens. Ein unbekannter Termin bleibt als „unbekannt“ erfasst. [TradingView zu Earnings-Terminen](https://www.tradingview.com/support/solutions/43000734922-how-do-earnings-date-filters-work-in-the-screener/).

### Priorität für die nächste Sichtung

- **Zeitnah prüfen** bei nachvollziehbarer roter und grüner Linie und ungefähr **0 bis 1 ATR Abstand unter Rot**. Bei gleichem Abstand gehen besser nachvollziehbare, öfter bestätigte Linien vor. Eine aktuelle Annäherung bekommt beim Gleichstand Vorrang vor einem Kurs, der sich gerade von der Linie entfernt. Wenn die letzte Kerze die Linie bereits berührt hat, notiere die Berührung mit dem Zeitstempel.
- **Beobachten** bei ungefähr **mehr als 1 bis 2 ATR** oder solange die Struktur mit zwei Ankern noch reift. Die 2-ATR-Grenze ist eine praktische Sortierhilfe für diese manuelle Liste.
- **Zurückstellen** bei unklarer Linienführung, veralteten Kursen, nahen Earnings oder mehr als etwa 2 ATR Entfernung. Wenn der letzte abgeschlossene 4h-Schluss bereits über Rot liegt, kennzeichne den Wert als **schon über Rot** und führe ihn außerhalb dieser Vor-Ausbruch-Liste.

Die Forschung zur Vorwarnung nutzte 1 ATR als einen Annäherungsfilter. In der erweiterten historischen Studie wurden 33,1 % der späteren Ausbruchs-Entries bereits ein bis zwei Handelssitzungen vor dem rohen Bruch gewarnt. Die Quote beschreibt die historische Vorwarnabdeckung für diese Projektfälle. Referenz ist die [erweiterte Vorwarnstudie](EARLY-WARNING-512-BEWERTUNG-20261101.md).

## 6. Einen wiederholbaren Rhythmus aufbauen

**Nach dem US-Schluss oder am Wochenende** startest du mit Rücklauf und Hochzone. Ergänze Kandidaten aus der letzten Runde, aus einer neuen Branche oder aus einem Scan für enge Handelsspannen. Halte in der Quelle den Datenstand und den Suchgrund fest, etwa „Finviz Russell Rücklauf, US-Schluss 13.11.“. Arbeite die offenen Charts in der Zeit durch, die du dafür hast. Markiere Fälle ohne klare Struktur als **Zurückgestellt** und ergänze einen kurzen Grund.

**An Handelstagen** beginnst du bei **Zeitnah prüfen**. Bei den beobachteten Zeichnungen reicht der Vergleich nach einem abgeschlossenen 4h-Balken. Prüfe, ob sich Abstand, Linie oder Datenstand wesentlich geändert haben. Eine bereits über Rot geschlossene Aktie erhält ihren eigenen Status. Bei noch offenen Firmenereignissen notierst du den Zeitpunkt, an dem du sie erneut sehen willst.

`Datenstand | Quelle | rote Linie und Anker | grüne Linie und Anker | Kontakte | Abstand zu Rot | nächster Ergebnistermin | Grund für den Prüfstand`

**Nach einigen Runden** vergleiche je Suchweg, wie viele gesichtete Charts du tatsächlich mit nachvollziehbaren Linien versehen hast und wie viele Titel zusätzlich zu den anderen Wegen dazukamen. So kannst du entscheiden, welchen Weg du häufiger nutzt. Bei einer geänderten Schwelle schreibst du den neuen Wert und das Datum in die Quelle. Das macht auch einen späteren Vergleich mit der Tori-Vorwarnlogik möglich.

Nutze in Tori den Chart mit deiner gewählten Kursquelle und speichere die Zeichnung dort. Die Browser-Zeichnungen sind an dieselbe Webadresse gebunden. Bei einem Vergleich zwischen Anbietern prüfe Symbol, reguläre Sitzung, Datenstand und Kursbereinigung. Konzept und Quellenintervalle sind in [HERMES](../HERMES.md#5-linien-kerzenbasis-und-bedeutung-der-darstellung) dokumentiert.

Die erweiterte Vorwarnstudie stützt es, aktive Annäherung und Verengung vorerst als Zusatznotizen zu führen. Die strengeren Pflichtbedingungen erfassten in der Studie weniger spätere Ausbruchs-Entries bei ähnlichem Anteil bestätigter Warnungen. Die Schwellen dieses Leitfadens dienen der manuellen Auswahl und stammen aus keinem Profitabilitätstest. [Vorwarnstudie](EARLY-WARNING-512-BEWERTUNG-20261101.md) · [Bilanz des Backtests](BACKTEST-UNIVERSEN-BEWERTUNG-20261101.md)

