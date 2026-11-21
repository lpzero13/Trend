# Wiederholung der Entry-/Exit-Fallstudie auf drei Universen

Vorab festgelegt am 01.11.2026. Auftrag: den früheren Gewinner-/Verlierer-Versuch auf dem übertragenen lokalen Kursbestand wiederholen, nach Einstiegsart, Exitmodell, Aktie und Universum auswerten. Dies ist ausdrücklich mehr als die zuletzt durchgeführte Vorwarnstudie.

## Bestand und Zeitgrenzen

- Eingefrorene, bereits lokal gespeicherte ETF-Bestandslisten vom 28.10.2026: Dow Jones/DIA (30), Nasdaq-100/CNDX (101 Aktienklassen) und S&P 500/IVV (505 Aktienklassen).
- Vereinigung: 520 unterschiedliche Symbole, alle lokal vorhanden. 512 erfüllen in mindestens einem bisherigen Entryfenster den historischen Vorlauf. Acht ausgeschlossene junge Bestände und alle einzelnen Fenster-Ausschlüsse bleiben dokumentiert. Keine Auswahl nach Gewinnen oder Verlusten.
- Geeignete Bestände: Dow 30, Nasdaq 97, S&P 500 499. Diese Zahlen überlappen; die Gesamtstudie zählt jede Aktie und jeden Fall einmal. Ein Fall darf in beiden getrennten Universumstabellen erscheinen, wenn die Aktie beiden angehört. Tabellen deshalb nicht addieren.
- Unveränderte Entryfenster: 2018, 2021, 2023, April 2025 bis März 2026. Gleicher Nachbeobachtungsabschluss wie zuvor: 29.10.2026, 15:25 UTC. Später importierte Kerzen werden abgeschnitten. Das stellt eine gemeinsame deklarierte Datenendgrenze trotz zweier Importstände her.
- SIP/split, reguläre Sitzungen, 4h-Entscheidungen, reale 5m-Ausführung. Keine neue API-Abfrage. Heutige Mitgliedschaft ersetzt keinen historischen Index einschließlich damals später delisteter Titel.

## Unveränderte wissenschaftliche Regeln

Kausale Master-/Pilot-Engine und bestehender Episodenfilter. Ein Fortschreiben oder Nachjustieren derselben Struktur erzeugt keinen täglichen neuen Einstieg. Höchstens ein Ausbruch, roter Retest und Safety-Bounce je eigener Strukturherkunft. Zwei-Kontakt- und qualifizierte Fälle werden getrennt berichtet; keine nachträgliche Hochstufung.

Je Fall 1.000 USD nominal, fraktionale Stückzahl, keine gemeinsamen Kapital-, Slot- oder Ein-Position-pro-Aktie-Grenzen. Kosten: 5 Basispunkte Spread insgesamt plus 5 Basispunkte Slippage je Seite. Signalentscheidung erst am abgeschlossenen Quellbalken; Entry und neue Stops erst am nächsten erwarteten 5m-Open nach 300 Sekunden. Openinggap unter dem Anfangsstop verhindert den Kauf. Hard-Stop-Gaps werden zum tatsächlichen Open ausgeführt. Safety-Puffer 0,3 %, Centabrundung, Stops ausschließlich aufwärts.

Fünf bereits früher geprüfte Varianten:

1. `fixed`: Anfangsstop unverändert als Kontrolle, kein regulärer Gewinnexit.
2. `original_safety`: ursprüngliche steigende Safety weiterprojizieren.
3. `fan_safety`: aktuelle gültige steigende Safety nachziehen, auch mit zwei Kontakten.
4. `qualified_fan`: ursprüngliche Safety; zusätzlich höhere aktuelle Safety nur bei bereits bekannter Qualifikation.
5. `r2_fan`: ursprüngliche Safety bis bestätigtem Netto-Buchplus von zwei Anfangsrisiken; danach dauerhaft aktuelle Safety zulassen.

Keine Zeitexits, Take Profits, neu optimierten Filter oder Auswahl anhand künftiger Pfadvollständigkeit. Offene Fälle bleiben offen. Fehlende tatsächliche Quellenintervalle zensieren den betroffenen Fall; keine künstlichen Ersatzkerzen.

## Wiederverwendung, Prüfung und Bericht

68 geeignete Kontrollaktien behalten identische Dataset-IDs und den identischen Nachlauf. Ihre bereits geprüften Blöcke dürfen erst nach identischer Engine-/Regel-/Quellbindung in einen neuen Studienplan übernommen werden; alte Studien werden nicht verändert. 444 zusätzliche Aktien werden berechnet. Die alte SNDK-Kontrolle war in keinem alten Fenster geeignet.

Alle Fall-IDs, Entry-/Stop-Zeitgrenzen und modellierten Kosten werden geprüft, ausgewählte tatsächliche 5m-Pfade unabhängig nachgerechnet. Zusätzlich CSV-Zählungen und Mittelwerte gegen Originalpfade abgleichen; Kontrollfälle müssen unverändert bleiben. Private Pläne, Daten, Blöcke, Detail-CSV und Prüfprotokolle bleiben außerhalb von Git.

Der Ergebnisbericht trennt:

- geschlossene Gewinner, Verlierer, Nullfälle und ihre Netto-Prozent-/R-Ergebnisse;
- offene Netto-Buchwerte zum vorhandenen Datenende;
- unbekannte Datenlücken und nicht gefüllte Signale;
- alle drei Entryfamilien, Kontaktklassen und fünf Exitvarianten;
- Universen, einzelne Aktien, Zeitfenster und große positive/negative Einzelbeiträge;
- unterschiedliche verfügbare Pfade und identische gemeinsam bewertbare Vergleichsfälle.

Mittelwerte gleicher nominaler Einzelfälle sind **keine Depot-, Index- oder annualisierte Rendite**. Ein häufiges Signal in denselben Aktien und derselben Marktphase ist keine unabhängige Beobachtung. Gewinnerlisten sind nachträgliche Beschreibungen, keine im Voraus handelbaren Filter. Keine neue Holdout-/Profitabilitätsfreigabe, keine Containerinstallation, Brokerorder oder Benachrichtigung.
