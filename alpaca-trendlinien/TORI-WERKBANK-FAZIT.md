# Bilanz: mehr nachvollziehbare Kandidaten, noch keine bestätigte Handelsstrategie

22.10.2026. [Vollständige Zahlen und Methoden](TORI-WERKBANK-ERGEBNISSE.md), [Bedienung und Hermes-Vertrag](TORI-WERKBANK.md), [vorab festgelegter Versuch](TORI-WERKBANK-PLAN.md). Lokal umgesetzt und durchgerechnet. Kein Upload, Container-Rollout oder automatischer Handel.

## Was es gebracht hat

**Die Datenquelle war eine wesentliche Einschränkung.** Historische SIP-Abfragen funktionieren mit dem vorhandenen Zugang; es wurde kein Abo verändert. 60 von 60 Imports verwendbar. Hauptvergleich auf denselben 57 Aktien wie zuvor, Juli 2020–Oktober 2026, ein Jahr Vorlauf. Die Medianabdeckung vollständiger 4h-Kerzen steigt von 78,94 auf 99,78 Prozent, bei Tageskerzen von 72,45 auf 99,74 Prozent. Dieselben strengen Linienregeln finden dadurch wesentlich mehr Fälle. SIP enthält außerdem andere Hochs/Tiefs als der einzelne Handelsplatz IEX; es handelt sich nicht einfach um dieselben Signale mit ergänzten Kerzen.

| Hauptgruppe | Bisher IEX | Jetzt SIP |
|---|---:|---:|
| 4h, drei Aktionskontakte + sieben Tage Alter | 310 Fälle / 308 Aktienzeitpunkte | 1.351 Fälle / 1.339 Aktienzeitpunkte |
| Davon 4h-Retests | 64 | 335 |
| 1D, drei Aktionskontakte + sieben Tage Alter | 151 Fälle / 150 Aktienzeitpunkte | 684 Fälle / 681 Aktienzeitpunkte |

„Fälle“ sind getrennte Ausbruch-/Retest-/Grün-Abpraller-Beobachtungen. Sie sind nicht alle unabhängige oder gleichzeitig finanzierbare Trades. Die Anker und Regeln wurden für diesen Vergleich nicht anhand späterer Gewinne verändert. Drei Kontakte beziehen sich in dieser Hauptgruppe auf die Aktionslinie; die Safety besitzt mindestens zwei Kontakte, ihr eigenes Alter und ihre Qualität sind zusätzlich sichtbar. Das strengere Safety-Drei-Kontakt-Profil bleibt separat.

**Die frühere hohe positive Quote bestätigt sich im größeren Feed nicht.** Bei 4h-Retests liegen 190 von 317 bekannten 20-Sitzungs-Endpunkten im Plus: 59,94 Prozent statt zuvor 74,58 Prozent. Mittel nach den modellierten Kurskosten +2,23 statt +5,20 Prozent. Das ist weiterhin eine interessante Forschungshypothese, aber kein getesteter Gewinn pro ausgeführtem Trade: Ein Stop kann vorher ausgelöst worden sein. Die beiden Zeitabschnitte liegen bei ungefähr +2,24 und +2,23 Prozent. Beide sind inzwischen bekannte Forschungszeiträume, keine neue unabhängige Bestätigung.

Die eigenständigen 1D-Retests sind mit −0,21 Prozent mittlerer 20-Sitzungs-Änderung nicht überzeugend. Das widerlegt nicht den Nutzen von Tageslinien als übergeordnetem Kontext für einen 4h-Einstieg. Marktrendite, Dividenden und marktgleiche Zufallskontrollen sind durch diese absoluten Endkursbeobachtungen nicht herausgerechnet.

## Kapital und Exits: gemischtes, teilweise ungeklärtes Ergebnis

Zwölf getrennte Cashversuche: drei Einstiegsfamilien, zwei Exitvarianten, zwei Zeitabschnitte. Je 2.000 USD Modellkapital, ein Prozent geplantes Risiko, maximal 25 Prozent pro Position, fünf Positionen, Bruchteile, Kosten und Kurslücken berücksichtigt. Splitbereinigte Modellkurse ohne Dividenden-/Corporate-Action-Depotjournal; keine Rekonstruktion echter Brokerabrechnungen.

**Acht der zwölf Versuche stoppen an einem unbekannten gehaltenen Kurspfad.** Ihre Gesamtrendite bleibt ausdrücklich unbekannt. Diese Fälle wurden nicht nachträglich entfernt, um einen besseren Bericht zu erhalten. Vier Versuche reichen bis zum jeweiligen Periodenende:

- 2021–2023, Grün-Abpraller: feste Safety −7,89 Prozent, bestätigte höhere Tiefs −2,41 Prozent.
- 2024–2026, Retest mit fester Safety: markierte Veränderung +20,49 Prozent. Endwert 2.409,82 USD; sieben geschlossene Positionen zusammen **−105,83 USD realisiert**, fünf Positionen weiterhin offen. Der positive Endwert entsteht aus deren unrealisierter Bewertung, nicht aus zwölf erfolgreich abgeschlossenen Trades. Maximaler auf dem 5m-Raster beobachteter Rückgang rund 16,11 Prozent.
- 2024–2026, Grün-Abpraller mit höheren Tiefs: markierte Veränderung +13,08 Prozent; zwei Positionen offen.

Daraus lässt sich kein allgemeiner Exit-Sieger ableiten. Gerade ein Vergleich „feste Safety gegen Nachziehen“ ist nicht abgeschlossen, wenn eine Variante wegen Datenlücken abbricht. Endmarkierungen sind keine erzwungenen Verkäufe.

Eine zusätzliche direkte Providerprobe an zwei bekannten Lücken bestätigte die fehlende Abdeckung auch bei 1-Minuten-Abfragen: COST 23.08.2024 und CVX 25.10.2021. Ein Wechsel auf kleinere Kerzen löst diese Beispiele also nicht einfach. Es wurden keine Ersatzkurse erzeugt. Ursache bzw. fehlende Daten mit dem Anbieter oder einer späteren separaten Quelle klären; alte Datasets und Ergebnisse unverändert erhalten.

## Was technisch jetzt nutzbar ist

1. **Sichtprüfung unter `/pruefung`:** 102 unterschiedliche bekannte Quellpräfixe, davon 82 bisherige Diagnose- und 20 feste Zufallsfälle. Eigene rote/grüne Rays, horizontale Widerstände und Kontaktmarkierungen; löschen/rückgängig; serverseitig speichern; erst danach Engine aufdecken. Ursprüngliche unbeeinflusste Bewertung und spätere Änderungen bleiben nachvollziehbar. Keine Zukunftskurse, keine erfundenen menschlichen Urteile.
2. **Erklärter headless Scanner:** Originalanker, Quellschluss, Kontaktqualität, Safety-/ATR-Abstand, Kontext, Raum und unbekannte Ereignisse. Annäherung, Ausbruch, Retest und Grün-Abpraller getrennt. Stabile Phasenkennungen und dauerhaftes paginiertes Journal. Kein stilles Wiederaufnehmen nach einer Daten- oder Engineänderung. Historische Tests und neue Vorwärtsregistrierungen getrennt.
3. **Konkretes Listenbeispiel zum 21.10.2026:** AXP in 4h und 1D, INTU in 4h, JNJ in 4h befinden sich in der vorab definierten Annäherungszone. Alle haben relevante Zusatzwarnungen. Es sind drei Aktien in vier Intervallansichten, keine Kaufempfehlungen oder belegten Einstiege. Genau solche Merkmale kann Hermes später für „bitte genauer ansehen“ nutzen.
4. **Technische Prüfung:** 303 Python-Tests jeweils unter 3.12/3.13 mit bekanntem Windows-Symlink-Skip, 41 JS-Tests; tatsächliche lokale HTTP-Abnahme und Controller-Test. 120 Quellreplays mit 13.096 exakt unveränderten ursprünglichen Profil-Entries und unveränderten Ablehnungen/Trichtern. 4.540 zusätzliche Beobachtungsfakten. Unabhängiger Audit von 69.420 Modellpfaden und 149.180.622 Pfadkerzen bestanden. Zusätzliche unabhängige Cash-Nachrechnung aller zwölf Ledger mit 361 angenommenen Positionen bestanden: chronologische Abbuchungen/Freigaben, damalige Bewertungen, Risiko-/Allokationsgrenzen und Endkapital. Keine Browser-Sichtprüfung.

Bestehender manueller Chart, persönliche Browserzeichnungen und laufender bisheriger Beobachter bleiben erhalten. Die neue Variante ist noch kein installierter Proxmox-Dauerdienst oder automatisch priorisierender Nachrichtenscanner.

## Was ich als Nächstes tun würde

Zuerst 15–20 Fälle selbst vor der Engine-Offenlegung einzeichnen, insbesondere dritte Kontakte und Widerstände. Daraus lässt sich eine konkrete geometrische Abweichung messen; weitere willkürliche Filter bringen uns dabei nicht weiter. Danach bekannte Kurspfadlücken mit belastbaren echten Daten schließen bzw. betroffene Perioden als ungeklärt belassen. Abschließend eine einzige festgelegte 4h-Kandidatenvariante mit diesen erklärten Merkmalen unabhängig vorwärts beobachten, ohne ihre Regeln währenddessen zu optimieren. Der bestehende Beobachter darf nicht nachträglich unter seinen alten Kennungen umgestellt werden.

**Urteil:** Die automatisierte Suche nach prüfenswerten Long-Kandidaten ist technisch gut vorbereitet und findet ausreichend historische Gelegenheiten. Eine dauerhaft gewinnbringende vollautomatische Ein-/Ausstiegsstrategie ist damit noch nicht belegt. Der nächste belastbare Fortschritt entsteht aus menschlicher Linienübereinstimmung, vollständigen Kurspfaden und einer unveränderten neuen Vorwärtsbeobachtung.
