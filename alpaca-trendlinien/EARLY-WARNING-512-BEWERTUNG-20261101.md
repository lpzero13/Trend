# Vorwarnstudie auf dem übertragenen Bestand: Bilanz

Stand: 01.11.2026. Wiederholung der letzten Vorwarn-/Signalstudie mit unveränderten Regeln, nicht der früheren Exit-/Depotversuche.

## Umfang und Vergleichbarkeit

Von 520 lokal vorhandenen SIP/split-Aktien erfüllen 512 in mindestens einem der vier bekannten Fenster den erforderlichen Vorlauf. Getestet wurden 2018, 2021, 2023 und April 2025 bis März 2026, insgesamt 1.004 XNYS-Sitzungen. Geeignete Aktien je Fenster: 472 / 489 / 504 / 512. CRWV, FDXF, FER, HONA, SKYD, SKYD.WS, SNDK und VYLR fehlen wegen unzureichender Historie am jeweiligen Fensteranfang; sie wurden nicht anhand ihrer Ergebnisse ausgeschlossen.

68 geeignete Aktien des alten Bestands behalten exakt dieselben Dataset-IDs, Warnungen, Episoden und Entryreferenzen. Die alte 69. Aktie SNDK war in keinem damaligen Fenster geeignet. 444 zusätzliche Aktien wurden neu berechnet. Die Kontrollblöcke wurden nur bei identischer Engine, Regeln, Fenstern und verifizierten Quelldaten wiederverwendet. Kein Providerabruf oder neuer Holdout.

## Was sich bestätigt

Basis ist die einfache Abstandswarnung bei höchstens einem ATR4h. Erfassung bedeutet Warnung vor einem späteren gültigen Entry-Signal bei noch aktiver Beobachtung, keine Gewinnerquote.

| Signalfamilie | Alter Bestand: Erfassung | Erweiterter Bestand: Erfassung | Entryreferenzen im erweiterten Bestand |
|---|---:|---:|---:|
| Ausbruch | 51,8 % | 49,7 % | 15.725 |
| Roter Retest | 34,9 % | 37,0 % | 10.781 |
| Safety-Bounce | 45,2 % | 47,7 % | 7.265 |

Das größere Universum reproduziert das bisherige Bild recht gut. Die Familien können sich wirtschaftlich überschneiden und sind keine unabhängigen Trades. Diese Wiederholung zeigt breitere historische Abdeckung, keine bestätigte zukünftige Rentabilität.

Bei Ausbrüchen wurden 5.202 von 15.725 Fällen, also **33,1 %**, bereits ein bis zwei Börsen-Sitzungsdaten vor dem ersten rohen Rot-Bruch gewarnt. Der Median unter rechtzeitig gewarnten Ausbrüchen beträgt eine 4h-Quellkerze bzw. 21,5 reale Stunden bis zum rohen Bruch. Sitzungstage sind keine garantierten vollen 24–48 Stunden. Vor der späteren Clean-Close-Entrybestätigung liegt der Median bei zwei Quellkerzen; 36,0 % aller Entries hatten dort ein bis zwei Sitzungstage Vorlauf. Diese längere Bestätigungsfrist darf nicht als Frühwarnzeit vor dem ursprünglichen Bruch ausgegeben werden.

## Was weiterhin fehlt

- **Zusätzliche Pflichtfilter helfen bisher kaum.** Bei Ausbrüchen sinkt die Erfassung von 49,7 % auf 38,8 % mit aktiver Annäherung, 45,3 % mit Verengung und 35,8 % mit beiden. Der Anteil später bestätigter Warnungen bleibt zwischen 47,1 % und 48,4 %. Beide Merkmale eignen sich vorerst zur Beschreibung und Priorisierung, nicht als begründet bessere Ausschlussregeln.
- **Die Meldungsmenge wächst deutlich.** Bei 1 ATR entstehen über alle drei Familien durchschnittlich 42,57 historische Briefings je Sitzung, am Spitzentag 125. Wiederholte Tagesansichten werden bereits dedupliziert. Für den praktischen Betrieb brauchen wir eine sortierbare Beobachtungsliste und zusammengefasste Briefings; Einzelmeldungen für jeden Fall wären viel.
- **Der Lebenszyklus bleibt der größte Ansatzpunkt.** 6.999 spätere Ausbruchs-Entries hatten zwar zuvor eine Warnung, deren Beobachtung jedoch schon geschlossen war. Diese zählen weiterhin nicht als erfolgreiche aktive Vorwarnung. Ein nächster isolierter Versuch sollte strukturell erneuerte Aufbauten begrenzt wieder zulassen und dabei Alarmwiederholungen messen. Ein späterer Entry macht eine zuvor verletzte Originalgeometrie nicht rückwirkend gültig.
- **Kontaktqualität ist zeitabhängig.** 410 später qualifizierte und rechtzeitig gewarnte Ausbrüche hatten bei der ersten Warnung erst zwei Kontakte. Ein genereller Dreikontaktfilter schon bei der Vorwarnung würde solche frühen Kandidaten verlieren. Zwei Kontakte bleiben eine gesondert gekennzeichnete Beobachtungsklasse.

## Prüfung und Einordnung

Ein unabhängiger Nachrechner hat alle 620.552 gespeicherten Warnzustände und alle 36 Vergleichsgruppen kontrolliert. Die Zustände überlappen zwischen zwölf Policies und sind keine 620.552 unabhängigen Chancen. Zusätzlich wurden 1.063 echte Warnzustände aus fünf neuen Aktien auf historischen Quellpräfixen reproduziert, auch bei veränderten zukünftigen Tageskursen. Neun gezielte Unit-Tests bestanden. Der parallelisierte Nachrechner reproduzierte zuerst auch die alte 69er-Studie vollständig.

Der Befund ist positiv für einen **historisch funktionierenden Beobachtungsscanner**, aber kein Nachweis profitabler Entries oder Exits. Heutiger Aktienbestand und bekannte Zeitfenster begrenzen die Aussage. Laufende Alarme, Web-Warnliste und Versand sind weiterhin geplant, nicht durch diesen Versuch eingerichtet. Sinnvoll ist als Nächstes der getrennte Vergleich einer begrenzten strukturellen Wiederfreigabe gegen diese unveränderte Referenz; anschließend eine ergebnisblinde Beobachtung auf neuen Daten.

[Vollständige Tabellen](EARLY-WARNING-512-ERGEBNISSE-20261101.md) · [Kontrollbestand und zusätzliche Aktien getrennt](EARLY-WARNING-512-VERGLEICH-20261101.md) · [CLI und Betriebsgrenzen](EARLY-WARNING.md)

Private Reproduktion: `artifacts/early-warning-expanded-20261101`, Plan-ID `87e42ff674ba27ce648435de66ebd3ded9aeb097528a4288dcec07b41a1f7fed`. Quellen, Pläne, Kontrollbelege, Warnsnapshots und Rohdaten bleiben außerhalb von Git.
