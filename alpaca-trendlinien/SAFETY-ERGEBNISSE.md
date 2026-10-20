# Safety-Strategien: Bilanz vom 20.10.2026

## Ergebnis und Entscheidung

Die vorgeschlagenen Safety-Varianten sind als eigener optionaler Forschungsweg implementiert und technisch geprüft. **Keine Variante wird aus diesem Versuch als profitable produktive Handelsstrategie ausgewählt.** In der vorab bestimmten primären Gruppe (Momentum 2 aus 3, Ausbruch, sämtliche neuen Eintrittsprüfungen, zehn Handelstage) gibt es im Entwicklungsabschnitt nur einen vollständig vergleichbaren Fall einer Aktie; er ist negativ. Eine Auswahl nach späteren Gewinnern oder eine Grenzwertsuche bis zum Gewinn fand nicht statt.

Der neue Weg kann chronologisch Signale rekonstruieren, ursprüngliche Linien archivieren, Exits regelgebunden simulieren und für Hermes maschinenlesbare Kandidaten ausgeben. Für einen neuen universumsweiten laufenden Safety-Scanner fehlen noch die dauerhafte Zeitplanung, Ereignisdeduplizierung und Positionszustandsführung dieses separaten Wegs. Die bestehende Forschungsqueue und manuelle Webansicht bleiben erhalten. Keine Brokerorders, neue Benachrichtigungen oder Proxmox-Installation.

## Feste Stichprobe und Fallzahlen

25 vorab bestimmte heutige US-Aktien: AAPL, ADBE, AMD, AMZN, AVGO, BAC, CAT, COST, CVX, GOOGL, GS, HD, JNJ, JPM, KO, MA, META, MSFT, NVDA, ORCL, PG, UNH, V, WMT, XOM. Die fünf bisherigen Datasets wurden exakt wiederverwendet; die zusätzlichen 20 Aktien einmalig importiert. Danach sind Discovery und Studie offline, ohne zusätzliche Providerabrufe. Heutige Aktienauswahl und Überlebens-/Branchenverzerrungen bleiben Grenzen.

| Messgröße | Entwicklung 02.05.2025–18.03.2026 | Bereits bekannte spätere Phase 19.03.–02.07.2026 |
|---|---:|---:|
| Profil-/Familienfälle | 2.083 | 840 |
| Unterschiedliche Aktie/Zeit/Familie-Ereignisse über Profile hinweg | 1.299 | 529 |
| Unterschiedliche Aktie/Einstiegszeitpunkte über Profile und Familien hinweg | 1.030 | 420 |
| Fälle mit sämtlichen neuen Eintrittsprüfungen | 21 | 7 |
| Davon unterschiedliche Aktie/Zeit/Familie-Ereignisse | 19 | 5 |
| Davon unterschiedliche Aktie/Einstiegszeitpunkte | 18 | 5 |
| Modellpfade: vier Modelle × drei Horizonte | 24.996 | 10.080 |
| Geschlossene Modellpfade | 17.757 | 7.373 |
| Unvollständige Modellpfade | 7.239 | 2.707 |
| Getrennte Portfolios | 144 | 144 |
| Portfolios bis Phasenende bewertet | 36 | 72 |
| Portfolios wegen fehlendem gehaltenem Marktpfad abgebrochen | 108 | 72 |

Diese Zahlen sind **keine unabhängige Stichprobengröße**. Profile/Familien können dieselbe Marktbewegung betreffen; Horizonte und Exitvarianten vervielfachen jeden Fall rechnerisch. Die spätere Phase war aus früheren Arbeiten bereits bekannt und ist deshalb keine neue unberührte externe Prüfung. Der finale reservierte Holdout bleibt geschlossen. COST erhält wegen später erster vollständiger 4h-Quelle erst ab 11.07.2025 einen zulässigen Replaybeginn; der Titel wurde nicht anhand seiner Rendite ausgeschlossen.

## Was wirtschaftlich funktioniert hat – und wo es nicht hielt

Ein beobachtetes positives Teilresultat ist das **Grundprofil / Ausbruch / eligible / zehn Handelstage**. Es wurde nicht nachträglich zur primären Strategie erklärt:

| Exit | Entwicklung: Mittel netto R, acht gepaarte Fälle | Spätere Phase: Mittel netto R, drei gepaarte Fälle |
|---|---:|---:|
| Gleicher gepufferter fester Notstop | +0,124 | −1,634 |
| Ursprüngliche grüne Safety-Line | +0,306 | −1,267 |
| Bestätigt verbundene höhere Tiefs | +0,357 | −1,267 |
| Zusätzlich bekanntes Widerstandsziel | +0,357 | −1,267 |

R ist das Nettoergebnis relativ zum anfänglichen Kursrisiko je Position, kein Prozent des Gesamtdepots. Kosten sind enthalten. Im entsprechenden Portfolio mit 2.000 USD Anfangskapital ergibt die Strukturvariante **2.028,74 USD** am Entwicklungsende (sieben Käufe, alle geschlossen) und **1.963,16 USD** am Ende der späteren Phase (vier Käufe, drei geschlossen, eine offene Position bewertet). Jede Phase beginnt separat mit 2.000 USD; dies ist keine durchgehende Jahresrendite. Die Zielvariante schließt die spätere offene Position und endet bei 1.962,20 USD. Kleine Fallzahlen und offenes Marktwert-Risiko erlauben keinen Profitabilitätsnachweis.

Im breiteren ungefilterten Vergleich auf derselben über alle Modelle/Horizonte vollständig beobachteten Fallmenge ist häufig der einfache gepufferte Notstop besser als die zusätzlichen Ausstiege. Beispiel Grundprofil/Ausbruch/20 Tage: Entwicklung N=434, mittlere Netto-Rendite fixed +0,693 %, original +0,274 %, structure +0,112 %, structure_target −0,328 %. Spätere Phase N=167: +3,860 %, +2,680 %, +2,688 %, +1,397 %. Das sind Einzelpositionsmittel, **keine Portfoliorenditen** und wegen der vollständigen Teilmenge möglicherweise selektiv. Sie belegen insbesondere nicht, dass jede rote oder grüne Linie automatisch einen wirtschaftlichen Vorteil erzeugt.

Ein hartes Ziel an einer bekannten Widerstandszone schneidet in vielen Gruppen schlechter ab. Dass eine Zone technisch nachvollziehbar ist, macht sie nicht zum richtigen Verkaufsort. Struktur-Nachziehen kann einzelne Verluste verringern, bringt aber keinen durchgängigen Vorteil gegenüber der einfachen Kontrolle. Die vollständigen positiven und negativen Gruppen stehen in [SAFETY-ERGEBNISTABELLEN.md](SAFETY-ERGEBNISTABELLEN.md).

## Warum so wenige zulässige Einstiege übrig bleiben

| Eintrittsprüfung nicht bestanden | Entwicklung | Spätere Phase |
|---|---:|---:|
| Netto-Raum bis nächster bekannter Widerstandszone mindestens 2R | 1.948 | 780 |
| Gepufferter Stop höchstens zwei bekannte 4h-ATR entfernt | 1.833 | 746 |
| Bekannter Wochenkontext nicht abwärts | 907 | 375 |
| Bekannter Tageskontext nicht abwärts | 531 | 235 |
| Letzte abgeschlossene Woche vollständig verfügbar | 582 | 146 |
| Letzte abgeschlossene Tagessitzung vollständig verfügbar | 253 | 70 |
| Linienalter mindestens sieben Kalendertage | 193 | 67 |

Mehrere Gründe können denselben Fall sperren; die Zeilen dürfen nicht zu ausgeschlossenen Trades addiert werden. In der Entwicklung beträgt der mediane anfängliche Stopabstand einschließlich Kaufkosten/Puffer rund 3,735 bekannte 4h-ATR. Der Raum ist bei 348 Fällen unbekannt, bei 1.600 unter 2R und bei 135 mindestens 2R. Die Hauptbremse ist damit die Kombination aus weit entfernter ursprünglicher Absicherung und begrenztem bekannten Raum – zusätzlich zu Datenlücken und Kontext.

Das spricht für einen nächsten **begründeten Modelltest**, nicht für ein pauschales Aufweichen: Prüfen, ob eine bei Signalbestätigung bereits bekannte nähere Safety-Linie eine brauchbarere Absicherung liefert als die beim früheren Arming fixierte Linie. Original-Signallinie und späteres Trade-Management dabei weiterhin getrennt erhalten. Diese alternative Einstiegsschutz-Auswahl wurde hier noch nicht implementiert oder anhand späterer Gewinne ausgesucht.

## Datenqualität und technische Abnahme

Im Entwicklungsabschnitt liegen die 5m-Abdeckungen zwischen 76,84 % und 100 %, Median 99,68 %. Durch die strikte Aggregation führt bereits ein fehlendes erwartetes 5m-Intervall zu einer unvollständigen größeren Quellkerze. Die 4h-Abdeckung reicht deshalb von 22,88 % bis 100 %, Median 91,30 %; Tagesabdeckung von 14,55 % bis 100 %, Median 85,45 %. Ein fehlender IEX-Balken ist kein Beweis für einen kaputten API-Abruf: Es können zulässige Trades auf diesem Teilmarkt fehlen. Keine künstlichen Kerzen und kein Überspringen eines unbekannten gehaltenen Verlustpfads.

- Kausaler Scan: alle abgeschlossenen Quellkerzen chronologisch prüfen, bestätigte Signale erst am erlaubten späteren Open ausführen. Gleiche ursprüngliche physische Einstiege für alle fünf bisherigen Aktien/Profile/Phasen reproduziert. Zukunftsauswertung ist nicht Teil des neuen Scans.
- Signal-Schlüssel `eventKey` hängen von Aktie, Feed, Adjustierung, Profil, Familie und Bestätigungszeit ab, nicht von der bei jedem Import wechselnden Dataset-ID. Pending und beobachteter Open können so gemeinsam dedupliziert werden. Exakte Entry-/Vertrags-IDs behalten die Datenversion für Nachprüfbarkeit. Eine historische Meldung wird dadurch noch nicht automatisch heute handelbar.
- Separater Auditor prüft alle 35.076 Modellpfade und 288 Portfolios: bekannte Kontext-/Zonendaten, ursprüngliche Verträge, bestätigte Safety-Wechsel, Latenz, Gap-/Stop-/Zielreihenfolge, Decimal-P/L/R, chronologische Cashfreigabe, Positionsgröße und 5m-Bewertung.
- Tatsächlicher Prozessabbruch nach einem Dataset-Checkpoint, automatische Freigabe der OS-Sperre und explizite Wiederaufnahme getestet. Alle Entries, Verträge, Pfade, Zeilen, Portfolios und Blocker des wiederaufgenommenen Fünfaktienlaufs entsprechen dem ununterbrochenen Lauf exakt.
- Technische Kriterien und Ergebnisregeln wurden vor der jeweiligen Auswertung gespeichert. Fehlerkorrekturen bekommen neue Versuchsordner; alte Ergebnisse bleiben erhalten. Abschlussvergleich bestätigt unveränderte Handelsresultate nach Ergänzung der importübergreifenden Signalidentität.
- Lokale Python-/JS-Abnahme und genaue Artefakte sind in [VERIFICATION.md](VERIFICATION.md) dokumentiert. Keine neue Browserprüfung, kein Container-/Broker-/Tickdaten-Nachweis.

## Sinnvolle nächste Forschungsreihenfolge

1. Datengrundlage für vollständige Ausführungspfade verbessern beziehungsweise die IEX-Grenze vor wirtschaftlicher Bewertung bewusst akzeptieren. Die aktuelle Technikbasis genügt nicht für einen belastbaren Produktionsentscheid über das gesamte Universum.
2. Einstiegsabsicherung beim Signalzeitpunkt als eigene vorab begründete Hypothese untersuchen; blockierende Gründe und Grenzen getrennt ausweisen. Erst danach eine kleine nachvollziehbare Filteränderung testen, statt zahlreiche Schwellen auszuprobieren.
3. Zunächst feste Kontrolle gegen ursprüngliche Safety und bestätigte Struktur vergleichen. Widerstandsziele nicht zum Standard machen, solange ein Zusatznutzen fehlt. Kosten, Gap-Risiko und einzelne abhängige Bewegungen beibehalten.
4. Erst einen ausreichend belegten Kandidaten einfrieren und außerhalb bisher genutzter Daten prüfen. Im ersten Schritt können parallele Papierbeobachtungen ohne Orders laufen. Der Holdout ist kein Optimierungsdatensatz.
5. Für einen ausgewählten Papierkandidaten den neuen Scanner dauerhaft planen, `eventKey` persistent deduplizieren, importierte Datenfrische überwachen und einen fortsetzbaren Positionszustand führen. Hermes erklärt protokollierte Fakten; es erfindet keine historischen Signale oder Ausführungskurse.

Regeln, Implementierung, genaue CLI-Befehle und Einschränkungen: [SAFETY-STRATEGIEN.md](SAFETY-STRATEGIEN.md).
