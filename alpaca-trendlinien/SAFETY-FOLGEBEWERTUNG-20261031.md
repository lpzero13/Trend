# Bewertung des Safety-Folgeexperiments

## Urteil

Die technische Erweiterung ist sinnvoll: Wir können Stopwechsel jetzt gezielt untersuchen, statt aus einer Closed-Trade-Tabelle auf die beste Strategie zu schließen. Die beiden neuen Varianten verbessern den mittleren Nettoertrag qualifizierter Ausbrüche und roter Retests in diesen bekannten Daten. Sie verbessern aber nicht die Mehrheit der Fälle, nicht die Mediane und nicht jedes Zeitfenster. Eine belastbar profitable automatische Strategie ist damit weiterhin nicht nachgewiesen.

Die neuen Regeln bleiben separate Forschungsvarianten. Eine automatische Umstellung der bestehenden Strategie wäre zu früh. Entrylogik, Episodenabgrenzung und ursprüngliche Anfangsstops wurden nicht verändert; sämtliche Vergleiche verwenden dieselben 6.668 Originalfälle. Keine Tagesexits und keine gemeinsamen Kapital- oder Positionslimits.

Details, Prüfzahlen, alle Kontaktklassen und Zeitfenster: [Ergebnistabellen](SAFETY-FOLGEERGEBNISSE-20261031.md). Definitionen und Reproduktion: [Versuchsplan](SAFETY-FOLGEPLAN-20261031.md).

## Was tatsächlich besser wurde

Bei den jeweils geschlossenen qualifizierten Fällen ergibt sich folgendes mittleres Nettoergebnis pro gleich großem nominalem Einzelfall:

| Stopführung | Ausbruch | Roter Retest |
|---|---:|---:|
| Bisherige aktuelle Safety | +0,60 % | +0,47 % |
| Aktuelle Safety nur mit bestätigter Qualifikation | +0,86 % | +0,73 % |
| Aktuelle Safety erst ab +2R am bestätigten 4h-Schluss | +1,07 % | +0,78 % |

Die Auswertbarkeit unterscheidet sich zwischen Modellen. Deshalb ist der zusätzliche Vergleich auf **identischen, in allen vier Safety-Modellen bewertbaren Fällen** entscheidend. Er berücksichtigt offene Fälle mit ihrem Netto-Buchwert und lässt datenbedingt unbekannte Pfade aus:

| Stopführung | 1.003 qualifizierte Ausbrüche | 672 qualifizierte Retests |
|---|---:|---:|
| Ursprüngliche Safety einschließlich offener Bewertung | +4,62 % | +2,04 % |
| Bisherige aktuelle Safety | +0,50 % | +0,42 % |
| Qualifizierte aktuelle Safety | +0,59 % | +0,57 % |
| Aktuelle Safety ab +2R | +0,77 % | +0,59 % |

Damit bleibt ein kleinerer Vorteil beider neuer Varianten gegenüber der bisherigen aktuellen Safety bestehen. Die ursprüngliche Safety führt bei dieser Bewertung wegen weniger sehr großer offener Gewinner deutlich. **Das ist kein Vergleich finanzierbarer Depots:** Die Haltedauern unterscheiden sich, Buchwerte sind nicht realisiert und durch Datenlücken ausgeschlossene Fälle können systematisch anders sein.

Auch ohne die besten drei bewertbaren Fälle bleibt der Mittelwert beider neuen Varianten bei qualifizierten Ausbrüchen und Retests positiv. Das ist eine Sensitivitätsbeschreibung derselben bekannten Daten, keine unabhängige Bestätigung und kein nachträglicher Handelsfilter.

## Welche Vermutung bestätigt wurde

Die bisherige aktuelle Safety zieht häufig auf sehr junge Linien nach. Bei qualifizierten Ausbrüchen gibt es 543 erste Wechsel auf eine tatsächlich engere andere Linie; davon haben 540 nur zwei Kontakte und lediglich zwei sind bereits qualifiziert. Der Wechsel erfolgt im Median nach rund sechs Kalendertagen bei gerade +0,25R am damaligen 4h-Schluss. Bei qualifizierten Retests: 348 solche Wechsel, 343 mit zwei Kontakten, vier qualifiziert, Median rund vier Tage und +0,18R.

Die Diagnose zählt nicht jede Fortschreibung der ursprünglichen Linie als neuen Wechsel. Sie vergleicht den tatsächlichen neuen Stop mit dem gleichzeitig zulässigen Stop der Ursprungslinie. Damit ist die frühe Zulassung vorläufiger Linien als Mechanismus belegt. Daraus folgt nicht, dass jeder frühe Exit falsch war.

Die 14 unter der ursprünglichen Safety noch offenen qualifizierten Ausbruchsgewinner erreichen unter der bisherigen aktuellen Safety durchschnittlich +13,62 %, unter der Qualitätsregel +24,71 % und unter der +2R-Regel +30,01 %. Die neuen Regeln erhalten bei diesen nachträglich ausgewählten Läufern mehr vom Trend. Trotzdem bleiben unter beiden neuen Regeln keine dieser Positionen am Datenende offen; die ganz langen Bewegungen der ursprünglichen Safety werden nicht vollständig gehalten. Diese ausgewählten Beispiele ersetzen nicht den Gesamttest.

## Was nicht besser wurde

Auf den gemeinsamen 1.003 Ausbruchsfällen sinkt die positive Bewertungsquote von 38,68 % bei aktueller Safety auf 33,90 % mit Qualitätsprüfung beziehungsweise 30,61 % ab +2R. Der Median verschlechtert sich von −0,80 % auf −1,17 % beziehungsweise −1,39 %. Bei Retests sinkt die Quote von 36,61 % auf 32,44 % beziehungsweise 28,72 %; Median −0,73 % gegenüber −1,03 % beziehungsweise −1,25 %.

Die +2R-Regel ist gegenüber bisheriger aktueller Safety bei 214 Ausbruchsfällen besser, bei 307 schlechter und bei 482 gleich. Bei Retests: 155 besser, 206 schlechter, 311 gleich. **Der größere Mittelwert entsteht durch stärkere positive Beiträge einiger Fälle, nicht durch allgemein zuverlässigere Einstiege oder eine höhere Trefferquote.**

Der Zeitfenstervergleich bestätigt keinen universellen Sieger. 2021 liegt die +2R-Regel bei qualifizierten Ausbrüchen unter der bisherigen aktuellen Safety; bei qualifizierten Retests wird ihr Mittel sogar leicht negativ. Die späteren Fenster tragen wesentlich zur Gesamtverbesserung bei. Bereits bekannte Zeitfenster sind kein neuer Holdout.

Safety-Bounces bleiben schwach: Auf identischen bewertbaren qualifizierten Fällen liegen die Mittel bei +0,072 % für aktuelle Safety, +0,008 % für Qualitätsprüfung und +0,067 % ab +2R. Beide neuen Regeln liefern hier keine überzeugende Verbesserung. Bounce bleibt eine getrennte Forschungsgruppe.

## Was wir nicht aus der Rückmeldung übernehmen sollten

Ein Stop ist kein garantiert gesicherter Gewinn. Der Export nennt deshalb ein **hypothetisches Netto-R bei Fill am letzten aktiven Stop**, einschließlich Beobachtungsdatum. Bei Kurslücken kann der tatsächliche Fill schlechter sein. Für zensierte Fälle gilt nur der letzte zusammenhängend beobachtbare Zeitpunkt, nicht das globale Datenende.

Die 75 abgesagten Entries mit Open unter Anfangsstop lagen sämtlich in einer späteren Handelssitzung, 17,5 bis 89,5 Stunden nach dem Signal. Das belegt keinen engen Stop, der innerhalb von fünf Minuten überlaufen wurde. Eine tiefere Fächer-Safety als Entryalternative darf nicht nachträglich aus erfolgreicher Zukunft gewählt werden. Dafür wäre ein neuer kausaler Entryversuch mit schon damals verfügbaren Alternativen und neuem Risiko nötig.

Ein Median der Differenz nahe null bedeutet außerdem keine Mehrheit gleicher Trades. Die medianen Anfangsstop-Abstände von Ausbruch und Retest unterscheiden sich hier moderat: 3,39 % und 2,98 %. Ein hoher mittlerer R-Wert allein begründet weder größere Positionsgrößen noch ein besseres Depot.

## Sinnvoller nächster Schritt

1. Ursprüngliche Safety als wichtige Referenz behalten. Die zwei neuen Regeln als alternative Gewinnschutzmodelle weiterführen, noch keinen Standard austauschen.
2. Einige frühe Stopwechsel, große Gewinner und unterdrückte Folgeepisoden visuell prüfen. Zuerst klären, ob die kausale Linien-/Episodenstruktur fachlich unserem Ansatz entspricht.
3. Danach wenige vorab festgelegte Varianten auf tatsächlich unangetasteten Daten bestätigen, einschließlich Kostenempfindlichkeit und Herkunft der Datenlücken. Nicht weitere Schwellen an denselben Ergebnissen optimieren.
4. Einen alternativen tieferen Anfangsstop nur als getrennten kausalen Entryversuch untersuchen. Die jetzigen Exitverbesserungen rechtfertigen keine pauschale Verbreiterung.

Wir haben damit ein besseres Forschungsinstrument und einen begrenzten empirischen Fortschritt beim Exit. Der letzte Schritt zur verlässlichen automatischen Auswahl guter Signale ist noch offen.
