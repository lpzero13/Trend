# Drei Retest-Exitideen: fester Versuchsplan vom 22.10.2026

Lokaler interner Versuch; vorhandene Web-/Worker-/Safety-Modelle nicht umstellen. Keine neuen Datenimporte, Orders, Benachrichtigungen, Veröffentlichung oder Containeränderung. Drei neue Varianten nacheinander, jede gegen denselben festen anfänglichen Safety-Stop; keine Kombination oder Parametersuche nach den Ergebnissen.

## Eingaben und gemeinsame Regeln

155 unveränderte archivierte Hüllen-/Zonen-Retests aus `retest-exits-20261022-b`; Entwicklung 02.05.2025–18.03.2026 und bekannte spätere Phase 19.03.–02.07.2026. Daten und Ergebnisse dieser Zeiträume wurden bereits verwendet; keine unberührte Validierung behaupten. Finalen Holdout nicht auswerten. Entry, vorhandene ursprüngliche rote/grüne Geometrie, Signalbreite, anfänglicher bereits gepufferter Stop und Kosten unverändert. Fünf oder zehn Tage sind XNYS-Sitzungen strikt nach Entrytag.

Alle Varianten: ursprünglicher Stop gilt ab Entry, maximal zehn Sitzungen Haltedauer, Gap unter wirksamem Stop zum 5m-Open, sonst Stopberührung zum Stoppreis. Kosten: insgesamt 5bp Spread plus 5bp Slippage je Seite, keine feste Gebühr. Fraktionale Stücke. Regeln auf **geschlossene Quellkerzen** anwenden; frühestens fünf Minuten später am nächsten erwarteten regulären 5m-Open wirksam. Der alte Stop gilt bis dahin. Bei Exit am zehnten Schluss kann der tatsächlich beobachtete Schluss verwendet werden, weil die Zeitgrenze vorher feststeht; ein anhand desselben Schlusses neu beschlossenes früheres Exit wird erst später ausgeführt. Keine rückwirkende Stopanhebung auf der Bestätigungskerze.

Fehlende erwartete 5m-Kerze vor Abschluss: unbekannt, nicht überspringen. Für die neuen 4h-Regeln muss auch die seit Signal erwartete 4h-Folge bekannt sein: Eine bereits zuvor gestartete, aber in der Quelle fehlende 4h-Kerze darf nicht still übergangen werden. Fehlende Quellbestätigung wird bei frühestem vorgesehenem Wirksamkeitszeitpunkt als unbekannt markiert. Bei gleicher Zeit hat ein schon zuvor wirkender Stopkontakt Vorrang vor neuem freiwilligem Exit. Ein Gewinnschutz, der erst jetzt oberhalb des aktuellen Open wirksam wird, darf nur zum Open ausgeführt werden, nicht zum höheren Stoppreis.

Hauptgruppe, Kalendergrenzen, Lückengruppen und Kapitalannahmen wie im vorigen Retest-Exitversuch. Keine nachträgliche Entryauswahl nach zukünftiger Pfadvollständigkeit. Beide Geometrien getrennt; zwischen ihnen andere Entrygruppen, nur innerhalb jedes Exitvergleichs gepaart.

## 1. Gescheiterter Retest (`failed_retest`)

Nach dem Entry schließt eine abgeschlossene 4h-Kerze **unter der Unterkante der ursprünglich gebrochenen roten/orangefarbenen Zone**. Unterkante = eingefrorene rote Gerade am jeweiligen Quellkerzenindex minus archivierte feste Signalbreite. Keine neue rote Linie auswählen; fallende ursprüngliche Linie wird entlang ihrer unveränderten Geometrie projiziert. Ein bloßer Docht oder ein Schluss innerhalb der Zone genügt nicht. Signal nur bei Kerzenschluss nach dem Entry. Danach freiwilliger Exit frühestens fünf Minuten später zum nächsten erwarteten regulären 5m-Open. Ursprüngliche grüne Absicherung bleibt bis zum tatsächlichen Exit aktiv.

## 2. Fehlender Fortschritt nach fünf Sitzungen (`time_no_progress`)

Am vorher festgelegten Schluss der fünften Sitzung Netto-Liquidationsergebnis einschließlich bisherigem Kauf und modelliertem Verkauf prüfen. Ist dieses **kleiner oder gleich null**, Exit frühestens fünf Minuten später am nächsten erwarteten regulären 5m-Open. Ist es positiv, weiter mit ursprünglichem Stop und unverändertem Zehn-Tage-Maximum. Keine Mindestgewinn-/R-Prozentoptimierung, kein nachträglicher Tageswechsel. Ein kleiner Bruttogewinn, der nach Kosten negativ wäre, zählt als fehlender Fortschritt.

## 3. Gewinnschutz mit Bewegungsraum (`atr_gain_stop`)

Aktivierung erst, wenn ein geschlossener 4h-Kurs nach Kosten mindestens **+1 anfängliches Vertrags-R** erreicht. R wie bisher: kostenbehafteter Kaufpreis minus anfänglicher Stop. Kein vor Entry beobachtetes Hoch und keine Aktivierung durch einen bloßen Intrabar-Docht.

Ab dann höchste **beobachtete 4h-Schlusskurse seit Entry** fortschreiben. Neuer Schutzstop = Maximum aus bisher wirksamem/geplantem Stop und höchstem solchen Schluss minus **2 aktueller bekannter 4h-ATR14**. ATR aus geschlossenen Kerzen, nie lockern, kein zusätzlicher Breakeven oder Take Profit. Nach Bestätigung mindestens fünf Minuten warten. Liegt der neu wirksame Stop wegen Rücklauf/Gaps bereits über dem nächsten Open, wird nur am Open ausgeführt. Ein aktivierter Schutz muss nicht sofort über Entry liegen; das ist keine garantierte Gewinnsicherung.

Die Werte 5 Sitzungen, +1R und 2ATR sind vorab feste Forschungsannahmen. Sie werden in diesem Versuch nicht auf bessere Renditen angepasst.

## Reihenfolge, Kennzahlen und Abnahme

Vor allen Ergebnissen Vertrag mit Quellchecksummen, eingefrorenen Entries, Regeln und Enginehashes schreiben. Dann Variante 1 Entwicklung und Entscheidungsprotokoll, spätere Phase; anschließend 2 und 3 ebenso. Keine Übernahme erfolgreicher Parameter aus einer vorherigen Variante. Für jede Variante denselben festen Referenzpfad exakt reproduzieren und gegen Archiv vergleichen.

Ausweisen: geschlossene/unbekannte Fälle, Nettogewinnanteil, mittlere Netto-R und prozentuale Einzelpositionsrendite, durchschnittlicher Gewinn/Verlust R, Profitfaktor, längste Verlustserie, Stop-/Exitgründe, Wegfall bester Gewinne sowie gepaarte R-Differenz mit beschreibendem Aktie-/Quartal-Intervall. Zusätzliche Diagnose auf gleicher vollständiger Zehn-Tage-Strecke, ohne diese Zukunftsinformation zum Entryfilter zu machen. Vergleiche zwischen mehreren neuen Varianten bleiben explorativ.

Je Phase unabhängiges 2.000-USD-Depot, maximal 1 % geplantes Risiko, 25 % Allokation je Position, fünf gleichzeitige Positionen, eine je Aktie. Cash-/Risikoledger unverändert wiederverwenden. Neue Exits können Kapital früher freigeben und dadurch andere spätere archivierte Entries ermöglichen; gepaarte Trade- und Depotergebnisse getrennt erklären. Datenlücke in einer gehaltenen Position stoppt den Depotlauf; kein scheinbar vollständiger Phasenvergleich bei unterschiedlichen Haltepunkten.

Gegenbeispiele und unabhängiger Nachrechner: feste Originalzone, keine Zukunftsdaten, geschlossene Bestätigung, Latenz/Overnight und alter Stop bis Exit, Nettokosten am fünften Schluss, positive Fortsetzung bis zehn, +1R nur per Schluss, ATR-Puffer/Monotonie/Gap, fehlende Quellkerzen, Missing-Pfade, identischer Referenzstop, unabhängige Decimal-P/L/R und Cashledger. Bestehende Python-/JS-Suiten erhalten. Keine Browserprüfung, da keine Webänderung.
