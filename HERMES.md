# Hermes: Projektstand, Ziele und Containerbetrieb von Trend / Tori

**Chart und Replay, 30.10.2026:** [Bedienung und technischer Vertrag](alpaca-trendlinien/CHART-REPLAY-FIXIERUNG.md). Automatische Trendlinien bleiben beim Öffnen aus; per Klick kausal zum angezeigten Zeitpunkt einschaltbar. Kerzenschritte funktionieren im normalen Chart, lokalen Dataset und Zufalls-Replay. Ohne Fixierung werden Linien je Schritt neu berechnet; Fixieren archiviert den Stand, weitere Kerzen verlängern seine Originalgeraden, Lösen zeigt die aktuelle Analyse. Replay-Fixierung und bisheriger Linienfinder sind jetzt speicherbar; Dataset/Fall/Modell werden getrennt. Ausschalten der Analyse erhält die Fixierung während der geöffneten Seite, eigene Zeichnungen bleiben separat. Abnahme: 443 Python-Testfälle ohne Fehler (ein bestehender Skip), 70 Chart-/Web-JavaScript-Tests und 49 Tests des Positionsrechners bestanden. Keine Migration, kein neuer Import, keine Containerinstallation; der alte Sammelauftrag bleibt pausiert. Diese GitHub-Übergabe umfasst auch den bisher lokalen Fächer-/Master-, Forschungs-, Wochen-/Parquet- und Sammlerstand. Zugangsdaten, Kurse, Datenbanken und private Artefakte sind nicht enthalten. Frühere Angaben „noch nicht veröffentlicht“ unten beschreiben die jeweilige damalige Abnahme.

**Schneller Datensammler V2, Abschluss 30.10.2026:** [Bedienung, Datenvertrag und Hermes-CLI](alpaca-trendlinien/SAMMLER-V2.md), [Messwerte und Universumsplanung](alpaca-trendlinien/SAMMLER-V2-ERGEBNISSE.md). Das Menü `/sammler` bietet sieben Emittenten-Abbilder, eine Auswahl ohne doppelte Symbole, Zeit- und Speicherschätzungen, Start/Pause sowie geprüfte Altübernahme. Kleine SQLite-Einträge je Aktie/Monat, parallel bearbeitete Jahresfenster, gepooltes HTTPS und typisierte Parquet-Checkpoints beschleunigen den Abruf. Standardbudget: 190 Versuche pro Minute; ein ausdrücklich gesetztes globales Limit bleibt Obergrenze.

Echter Vergleich mit AAPL, GS, KO, BNY und SNDK: **356,7 Sekunden / 821 Abrufe → 237,2 Sekunden / 598 Abrufe**. Alle fünf Dataset-IDs stimmen exakt überein; sämtliche höheren Aggregate und Wochen-Caches wurden unabhängig offline nachgerechnet. Wiederverwendung: **33,2 Sekunden ohne Abrufe**. Geprüfte Übernahme der fünf v1-Testaktien: **18,1 Sekunden ohne Abrufe**, Quelle unverändert. **441 Python-Tests ohne Fehler (ein bestehender Skip) und alle 62 JavaScript-Tests bestanden**; Browserabnahme einschließlich Datumsfestsetzung erfolgreich.

Das Planungsmodell ergibt für den vollständigen S&P-500-Erstbestand etwa **7,8 Stunden und 4,1 GiB** Kurs- und Monatsdateien. Das ist kein gemessener Containerlauf. Alle sieben geladenen Abbildungen ergeben zusammen **3.002 verschiedene Symbole**. Automatische tägliche Fortschreibung splitbereinigter Daten über neue Vintages und EODHD bleiben geplant. Der alte 100er-Auftrag bleibt separat pausiert: **69 fertige Aktien und 9.074 Monatscheckpoints**. Es wurde keine Großsammlung, Veröffentlichung oder Containerinstallation gestartet. Bei geändertem Kerncode neue Aufträge anlegen; alte Hashes nicht überschreiben.

**Historien-Sammelimport, 29.10.2026:** [Datenvertrag, Wiederaufnahme, Backup und Hermes-CLI](alpaca-trendlinien/HISTORIENARCHIV.md). Neuer dateibasierter `archive-create/run/status`-Weg ab Januar 2016, SIP/split, direkte monatliche Parquet/Zstd-Checkpoints ohne großen JSON-Rohcache. Gemeinsames prozessübergreifendes Alpaca-Abrufbudget im selben Datenpfad, Monatsprüfsummen/Wiederaufnahme, unveränderliche reguläre 5m/1h/4h/1D-Datasets plus vorhandener Wochen-Cache, Qualitätszählung einschließlich vollständig fehlender Sitzungen. Kein neues DB-Schema und keine Umstellung laufender Forschungsjobs. Backup/Restore umfasst auch referenzierte unvollständige Archivbestände. Vom Nutzer gewähltes erstes Universum: heutige Dow-30 plus 70 weitere S&P-100-Aktien, Quellenstand 28.10.2026; Zusammensetzung wird im Job eingefroren, keine historische Indexmitgliedschaft behauptet. Kleiner echter AAPL-2016-Vorabtest erfolgreich. Der lokale 100er-Import wurde auf ausdrücklichen Nutzerwunsch pausiert: 69 Aktien fertig und offline nachgeprüft, 9.074 Monatscheckpoints erhalten (PFE zusätzlich104Monate); kein Löschen. Später mit derselben Archiv-ID und unverändertem Importcode fortsetzen, erst nach erneuter Nutzeraufforderung. 411 Python-Tests ohne Fehler (ein bestehender Skip),52relevanteJS-Tests; echte Offline-HTTP-Prüfung dreier Langbestände über alle vier Intervalle und Masteranalyse erfolgreich. Der Abschluss des gesamten Universums bleibt ausstehend. Keine Orders, kein Upload oder Container-Rollout.

**Neues Pine-Master-Profil vom 29.10.2026:** [Übernommene Regeln, bewusste Korrekturen und Bedienung](alpaca-trendlinien/TORI-MASTER-UPDATE-20261029.md), [gelieferte Pine-Referenz](alpaca-trendlinien/reference/tori_master_20261029.pine). Neuer Modus `fan_master` / Forschungsprofil `master`, bestehende Profile weiterhin verfügbar; normale Chartanalyse startet aus. Separate Safety-/Widerstandsfenster (320/150 Tage), Hüllkurven-Steigungsanpassung, 0,05 ATR Körperraum, kürzere spätere Fächerabstände, blaue Haupt-Safety und getrennte enge Safety; echte Kontakte statt pauschaler Zwei-Kontakt-Fallbackzählung. SMA 50/200 nur Kontext, optionale Stichtagsmarkierung, kompakte/scrollbare Infobox mit Master-Details. Datum/Stepper bleiben echte abgeschlossene Präfixe; Pine-Prüffenster ist kein rückdatiertes Signal. Gemeinsame Quelle für Chart/Headless, Haupt-/enge Safety beim Signal bindbar, effektive Profile im Manifest, keine Änderung der Ausführungsannahmen. 398 Python-Gesamtfälle (ein bestehender Skip), gezielte API-Nachprüfung und 60 JS-Tests; echter isolierter Browser-/Queue-Lauf mit lokalem MSFT-SIP-Bestand. Keine neuen Providerimporte, Migration, Produktivpfad-/Zeitplanänderung, Veröffentlichung oder Containeraktualisierung. Neue Forschungsjobs nach Enginewechsel verwenden; lokale Python-Webansicht regulär neu starten.

**Optionaler Python-Fächer und kausaler Einzelfall-Backtest, 29.10.2026:** [Bedienung, Berechnungsvertrag, Hermes-CLI und Marktversuch](alpaca-trendlinien/TORI-FAECHER.md), [Abnahmeplan](alpaca-trendlinien/TORI-FAECHER-PLAN.md). Neuer Menüpunkt `/faecher`, Chartmodelle `fan_extreme` und `fan_local`; bisherige Regeln bleiben wählbar, Chartanalyse startet weiterhin aus. Gemeinsamer Quellkern für 1h/4h/1D/1W, bestätigte Pivots, tolerante getrennte Kontakte, ursprüngliche Ausbruch-/Retest-Linien und Safety fixiert. Zufallsstarts gehen kerzenweise bis zum ersten Signal je Testgruppe oder ehrlicher Grenze. Lokale reguläre 5m-Ausführung mit nächstem erwartetem Open, Verzögerung, Kapital/Risiko, Gebühren/Spread/Slippage, Gaps, festem oder bestätigtem Higher-Low-Stop und 5/10/20-Sitzungspfaden. Keine gemeinsame Depotstrategie und keine Profitabilitätsfreigabe. Headless über bestehende Queue, Paginierung, Abbruch/Wiederholung und Enginebindung, keine neuen Runtime-Abhängigkeiten oder DB-Migration. Geometrien und Datentyp/Feed/Bereinigung werden getrennt ausgewertet; gleiche Schluss-Signale innerhalb einer Gruppe dedupliziert. Bestehender Datasetreferenzschutz/Backup greift. Neue Jobs nach Codewechsel anlegen, alte Jobs nicht unter neuer Engine fortsetzen.

**Erster technischer Marktversuch:** Drei vorhandene Aktien (AMZN/MSFT/NVDA), SIP/split, historische 4h-Präfixe bis Juni 2024, beide Geometrien und identische 30 zufällige Zeitpunkte, insgesamt 762 innerhalb der Testgruppen deduplizierte Signalfälle, 662 bedingte Modell-Entries. Positive Mittelwerte qualifizierter Gruppen, gemischte Zwei-Kontakt-/Retestbefunde; stark überlappende Fälle und heutige Gewinnerauswahl sind keine unabhängige Validierung. Konkrete Zahlen/Grenzen im Fächer-Dokument. Kein neuer Providerimport, Großabruf, Upload oder Proxmox-Rollout. Abschlussprüfung: 390 Python-Testfälle unter 3.12.10 (ein bestehender Skip, keine Fehler), 58 JavaScript-Tests bestanden. Isolierter Browser-/Queue-/CLI-Test und echter Backup/Restore identischer Fälle erfolgreich. Produktive Live-Meldungen dieser Engine, Portfolioausführung und breite unabhängige Validierung bleiben geplant.

**Browserabnahme der geraden Linien:** Bestehende rote/grüne 1D-Zeichnungen im lokalen historischen RTX-Prüffall nach Neuladen in 4h, 1W und 1h überprüft und wieder auf 1D zurückgeschaltet: jeweils durchgehend gerade, keine abgetasteten Knicke; Zeichnungen und Farben erhalten. Für diese Korrektur nur Frontend-Geometrie/Tests und Dokumentation geändert, keine neue Migration, keine Providerabrufe oder Workeränderung.

**Korrektur der manuellen Intervallprojektion, 28.10.2026:** Die unten erwähnte Erhaltung der gesamten Ursprungskurve erzeugte in 4h/1W sichtbare Zickzacklinien. Persönliche Linien werden jetzt in jedem Intervall als **eine Gerade durch dieselben zwei gespeicherten Zeit-/Preisanker** dargestellt. Ursprüngliche Basis-Metadaten bleiben lesbar, werden nicht mehr als Zwischenpunkte abgetastet. Farben, Verlängerungsarten, Bearbeitung und Undo bleiben erhalten; Trefferprüfung und Beschriftung folgen der Geraden. Zwischenwerte/Verlängerung sind eine Projektion in die jeweilige kompakte Chartachse, keine intervallunabhängigen Preiswerte oder Forschungssignale. Keine Änderung an Kursdaten, Imports oder automatischen Signalregeln. 54 JavaScript-Tests bestanden; Gegenbeispiele prüfen fixe Anker, Kollinearität und Renderer/Trefferprüfung für alte Tageslinien in 4h-/Wochenansichten. [Aktueller Zeichenvertrag](alpaca-trendlinien/PARQUET-SPEICHER.md).

**Parquet-Kursablage und feste persönliche Linien, 28.10.2026:** [Speichervertrag, Migration und Bedienung](alpaca-trendlinien/PARQUET-SPEICHER.md). Lokal alle **487 vorhandenen Datensätze derselben 60 Aktien** umgestellt, **keine neuen Providerimporte**: gleiche logische Dataset-IDs, unveränderte Originalkerzen/Prüfmetadaten, gemeinsame unveränderliche Monatsblöcke mit Parquet/Zstd, zusätzlicher vollständiger 1W-Cache. Aktive Manifeste/Blöcke zusammen **339.524.821 Bytes** statt 4.642.963.441 Bytes JSON, 9.501 eindeutige Blöcke bei 21.926 Blockreferenzen. Alte 487 JSON-Dateien bleiben unter `datasets/legacy-json/` als Rückfallkopien erhalten; deren Platz ist noch nicht freigegeben. SQLite bleibt Betriebsdatenbank; neue Runtime-Abhängigkeit `duckdb==2.0.0`, gleicher Datenpfad. Neue Backupschema-Version 2 sichert referenzierte Parquet-Blöcke einmalig; alte JSON-Backupschema-Version 1 bleibt wiederherstellbar. Numerisch exaktes Rücklesen und gleiche IDs pro Migration geprüft, echter RTX-Bestand zusätzlich gesichert/wiederhergestellt und alle vier historischen Ansichten per HTTP ohne zukünftige Kerzen geprüft. Persönliche Linien behalten ihre Ursprungskurve beim Intervallwechsel, werden erst beim absichtlichen Bearbeiten neu gebunden, individuelle Farben mit Undo. Kalenderpositionen ohne zukünftige Preise unterstützen Verlängerungen; Bruchteilpositionen der Chartbibliothek werden korrekt interpoliert. Lokale technische Abnahme: 349 Python-Gesamtfälle je 3.12/3.13 (je ein bestehender Skip), anschließende gezielte Speicher-/Backupnachprüfung einschließlich zusätzlichem Legacy-Restorefall unter beiden Versionen; 53 JS-Tests. Browserprüfung von 1h/4h/1D/1W, Farben, absichtlichem Ziehen und Undo. Manuelle Zeichnungen bleiben im Browserspeicher. Bestehende automatische Signalregeln unverändert; alte Aufträge/Beobachter wegen geändertem Enginecode nicht fortsetzen, passende neue Registrierung nötig. Webdienst weiterhin ohne Forschungsworker gestartet, kein Zeitplanwechsel, Großimport, GitHub-Upload oder Container-Rollout.

**Wochenansicht und Speicherplanung vom 28.10.2026:** Chart und Zufallsmodus unterstützen zusätzlich `1W`, einschließlich Wochen-Kerzenschritten, Zeichnungen und Messungen. Wochen aus bekannten Tagesquellen nach dem letzten tatsächlichen XNYS-Wochenschluss, nur vollständige erwartete Sitzungen; keine Monatskerzen. Bestehende Datasets und Headless-Forschungsengines bleiben unverändert. Aktuell 60 Aktien lokal; frisch gefilterter Alpaca-Katalog 13.227 aktive US-Wertpapiere inkl. ETFs/weiteren Typen, nicht durchgängig garantierte Kursabdeckung. Nicht destruktiver SQLite-Speichertest auf drei langen Historien und Plan für gemeinsame, versionierte Datenbasis/Universumslisten: [WOCHEN-UND-DATENSPEICHER.md](alpaca-trendlinien/WOCHEN-UND-DATENSPEICHER.md). Abgenommen mit 340 Python-Tests je 3.12/3.13 (je ein vorhandener Skip), 48 JS-Tests und echter lokaler HTTP-/Browserprüfung. Kein Bestandsumbau, Großimport, Rollout oder automatisches Löschen durch diesen Versuch.

**Manueller Zufallsmodus vom 28.10.2026:** Menü `/zufall`, zufällige lokal gespeicherte Aktie und historischer 4h-Schluss ohne Signal-/Ergebnisfilter; 1h/4h/1D nur mit zu diesem Zeitpunkt abgeschlossenen Kerzen, Kerzenschritte vor/zurück und Rückkehr zum Start. Fall/Dataset fest gebunden, persönliche Zeichnungen/Messungen getrennt je Fall im Browser. Gemeinsames Linienwerkzeug ergänzt um links/rechts verlängerte Rays, beidseitige Geraden, Strecken und horizontale Widerstands-/Unterstützungslinien; Löschen/Rückgängig erhalten. Lokale Registrierung `random:case:*` in bestehender Hauptdatenbank, vorhandener Referenzschutz/Backup greift. Keine Providerabrufe durch Auswahl oder Wiedergabe, keine neuen Runtime-Abhängigkeiten, keine automatische Änderung von Forschung oder laufenden Beobachtern. Lokal abgenommen: 334 Python-Tests je 3.12/3.13 (je ein vorhandener Skip), 47 JS-Tests, echte HTTP- und Browserbedienprüfung. Webansicht zur Abnahme ohne Forschungsworker gestartet; keine Zeitplanänderung oder Veröffentlichung. Bedienung, Auswahlgrenzen und API: [ZUFALLSMODUS.md](alpaca-trendlinien/ZUFALLSMODUS.md).

**Eigenständige Rechner-Übergabe vom 24.10.2026:** Auf ausdrücklichen Nutzerauftrag wurde ausschließlich der Positionsrechner 1.1 inklusive Tests und Dokumentation nach [lpzero13/Rechner](https://github.com/lpzero13/Rechner) auf `main` übertragen, Commit `c61d8253afae6d531894e313a673d5b059dd7525`. Eigener lokaler Checkout unter `C:\Users\chris\Documents\ChatGPT\Rechner`; die Rechnerdateien liegen dort im Repository-Stamm. Die bisherigen Angaben „lokal/keine Veröffentlichung“ beschreiben den Stand vor dieser getrennten Übergabe. Tori-Code, lokale Daten und Zugangsdaten wurden nicht übertragen; kein Website-Deployment oder Container-Rollout.

**Separater lokaler Aktien-Positionsrechner vom 24.10.2026, Version 1.1:** [Bedienung und Berechnungsvertrag](alpaca-trendlinien/positionsrechner/README.md). Eigenständige statische Browser-App unter `alpaca-trendlinien/positionsrechner/index.html`, ohne Backend, Build, Speicherung oder Providerzugriff. Manuelle Euro-Eingaben, ganze Aktien nach Risiko- und Depotwertgrenze, exakte BigInt-Centberechnung. Auf Nutzerauftrag nun Kostenmodelle für Trade Republic Best-/Direktpreis, ING Standard/Young plus Handelsplatzzuschlag und manuelle Gesamtkosten; Kauf- und Stop-Verkaufskosten im Risikobudget, Kaufkosten auch in der Kapitalgrenze. Sichtbares 3:1-Kursziel vor Kosten mit Nettogewinn/-CRV sowie separater Gewinnschwelle und Kurs für mindestens 3:1 nach Kosten. Gebührenmodelle anhand offizieller Angaben am 24.10.2026 geprüft, keine Tarif-/Ausführungsgarantie, keine Steuern oder Spreadschätzung. Überarbeiteter Dark Mode mit System/Hell/Dunkel und mobilem Layout. Kein automatischer Einstieg oder garantierter Maximalverlust. Keine neue Route im Tori-Dienst, keine Änderung an Chart, Forschung, laufenden Beobachtern oder Datenpfad; keine Veröffentlichung oder Containerinstallation. Der konkrete Abnahmestand steht in der Rechner-README.

**Lokale Abnahme des SIP-Kandidatenversuchs abgeschlossen:** 326 Python-Tests je 3.12/3.13 (je ein bestehender Skip), 43 JS-Tests und 21 echte HTTP-Prüfungen bestanden. Webserver mit `/kandidaten` aktualisiert, bestehender Forschungszeitplan erhalten. Getrennter SIP-Worker aktiv, alle 60 Aktien ohne Spurfehler initialisiert, noch keine neuen prospektiven Papier-Einstiege. Startbestand bleibt als solcher gekennzeichnet; tatsächliche Vorwärtsvalidierung und menschliche Blindbewertungen sind ausstehend. Bestehender IEX-Worker unverändert aktiv. Keine visuelle Browserabnahme, kein Container-Rollout oder GitHub-Upload.

**Separater SIP-Kandidatenversuch, 22.10.2026:** [Betrieb und API](alpaca-trendlinien/TORI-KANDIDATEN.md), [vorab gespeicherter Plan](alpaca-trendlinien/TORI-KANDIDATEN-PLAN.md), [Ergebnisse und Grenzen](alpaca-trendlinien/TORI-KANDIDATEN-ERGEBNISSE.md). Neu: `/kandidaten`, 20 zusätzliche blinde SIP-Präfixe (keine menschlichen Urteile), 349 4h-Retests in 60 Aktien mit passenden Zufallskontrollen, 5/10/20-Sitzungsbewertung, zwei Stoppmodelle und 28 getrennte Kapitalledger. Erklärte Gruppierung ähnlicher Geometrien bewahrt die ersten Anker; alternative Linien erzeugen kein Signal der Originallinie. Neuer eigener SIP-Papierbeobachter mit nicht rückdatierter Registrierung, eingefrorener Enginebindung, Präfix-/Stoppfolgeschutz, Checkpoints, Herzschlag, paginiertem Journal und Speicherbudget. Persistenz in bestehender Hauptdatenbank `cw:*`, Sicherung/Restore und Referenzschutz mitgenutzt. Bisheriger IEX-Beobachter und manuelle Chartdefaults bleiben erhalten. Historische Vorteile sind zeitphasenabhängig; 19/28 Kapitalledger unvollständig, keine Profitabilitätsfreigabe. Langzeitbetrieb benötigt bessere inkrementelle Datasetablage; aktuelle Vollsnapshots sind mit 4 GiB Importbudget je Registrierung begrenzt. Kein Container-Rollout, keine neuen externen Nachrichten oder Orders.

**Neue lokale Werkbank vom 22.10.2026:** [Bedienung, Scanner-/API-Vertrag und Betriebsgrenzen](alpaca-trendlinien/TORI-WERKBANK.md), [Bilanz und Folgerungen](alpaca-trendlinien/TORI-WERKBANK-FAZIT.md), [Vorabplan](alpaca-trendlinien/TORI-WERKBANK-PLAN.md), [SIP/IEX-Vergleich und Kapitalrechnung](alpaca-trendlinien/TORI-WERKBANK-ERGEBNISSE.md). Implementiert: eigener Menüpunkt `/pruefung` mit 102 bekannten Präfixen (82 Diagnose- und 20 feste Zufallsfälle), eigenen Rays/Widerständen/Kontaktmarkierungen, Löschen/Rückgängig, serverseitiger Speicherung, expliziter Engine-Offenlegung und unverändert erhaltener unbeeinflusster Bewertung. Keine menschlichen Urteile erzeugt. Separater erklärter JSON-Scanner für drei Kontakte + sieben Tage Alter, weitere Kriterien als Merkmale/Warnungen, ursprüngliche Anker, unveränderlicher Beginn, Engine-/Quell-/Kalenderpräfixschutz, append-festes paginiertes Journal und Offline-Wiederholung. Neue Dokumente in der bestehenden `settings`-Tabelle unter `wb:*`; Datasetreferenzschutz und bestehendes Backup/Restore gelten. Keine neue Runtime-Abhängigkeit. Historischer SIP-Zugriff mit vorhandenem Alpaca-Zugang erfolgreich; Echtzeit-SIP dadurch nicht freigeschaltet. Separater gleicher 60-Aktien-/Zeitraum-Vergleich mit unverändertem vollständigem Replay und unabhängigem Pfadaudit; maßgebliche abgeschlossene Zahlen stehen im verlinkten Ergebnisbericht. Vorhandenes Cashledger für separate Machbarkeitsrechnung wiederverwendet; bei unbekanntem gehaltenem Pfad keine Gesamtrendite. Noch offen: echte Point-in-time-Ereignisdaten, tatsächliche menschliche Geometrieprüfung, unabhängige Vorwärtsvalidierung dieser Variante und universumsweite Meldepriorisierung. Bestehender `forward_watch`-Lauf, manuelle Browserzeichnungen und Chartstandard bleiben erhalten. Neue Werkbank-CLI ist kein neu installierter Dauerdienst. Nur lokal entwickelt; kein Upload oder Container-Rollout.


**Größerer separater Kriterien-Gesamttest vom 22.10.2026 (lokal):** [Bilanz und nächste Schritte](alpaca-trendlinien/TORI-GESAMTTEST-ERGEBNISSE.md), [Vorabplan](alpaca-trendlinien/TORI-GESAMTTEST-PLAN.md), [vollständige Tabellen](alpaca-trendlinien/TORI-GESAMTTEST-TABELLEN.md). 60 festgelegte US-Aktien, 57 gültige IEX-Imports, echte Historie ab Juli 2020 bis 21.10.2026, ein Jahr Vorlauf und danach kontinuierlicher 4h-/1D-Replay. Separate `complete_strategy.py`/`complete_outcomes.py` und `tools/complete_study*.py`: einseitige Kontaktbänder ohne Dochtschnitt, unabhängige Reaktionen, mehrere Pivotpaare, eingefrorene Vor-Ausbruch-Qualifikation, gestufte Kriterien und natürliche Exits ohne Zehn-Tage-Zwang. 4h: 359 Drei-Kontakt-Fälle, mit sieben Tagen Alter 310; davon 64 Retests mit interessanten, aber nicht als Handelsrendite interpretierbaren 20-Sitzungs-Kursbeobachtungen. Strenge zusätzliche Safety-/Kontext-/Raumprüfungen lassen nur einen 4h-Fall und keinen Tagesfall übrig; fehlender historischer Ereigniskalender bleibt unbekannt. Kein nachgewiesener Profitabilitäts- oder allgemeiner Trailingvorteil; 82 Blindfälle noch ohne menschliche Urteile. Einzelplatz-IEX ohne Trades kann fehlende Bars erzeugen; das konservative vollständige 5m-Raster beschränkt Datenabdeckung und lange Pfade deutlich. 290 Python-Tests je 3.12/3.13 mit bestehendem Skip, 38 JS; unabhängige Prüfung von 16.096 Modellpfaden. Bestehender Chart, Queue und laufender Beobachter unverändert; keine Veröffentlichung, Containeränderung oder Orders. Werkzeuge sind ein datierter Offline-Forschungsversuch, kein neuer automatischer Dienst. Bestehenden `TORI_DATA_DIR` erhalten; Rohkurse, Imports, Fälle und private JSON-Ausgaben bleiben lokal.

**Lokale prospektive Beobachtung vom 22.10.2026:** [Bedienung, feste Regeln und Betrieb](alpaca-trendlinien/FORWARD-BEOBACHTUNG.md). Neuer separater `tools/forward_watch.py`-Dienst für die bisherige feste Liste von 25 US-Aktien, beide unveränderten Geometrien `hull_exact`/`swing_zone`, je neuem Retest feste Safety und bestehender +1R/2ATR-Schutz. Registrierung speichert Beginn/Engine vor neuen Daten; alter Forschungs-Holdout bleibt verbraucht. Erstimport einer konsistenten 910-Tage-IEX/Split-Historie, anschließend überlappende Aktualisierung und Prüfung alle 15 Minuten; ohne neue reguläre Kerze kein Providerabruf. Kurspräfixrevisionen sperren die betroffene Aktie. Eigener Menüpunkt `/watch` mit eingefrorenem Ereignisstand, ausdrücklich zuschaltbarem Verlauf und historisierten menschlichen Urteilen; spätere Verlaufssicht wird dauerhaft vermerkt und beeinflusst keine Regeln. Checkpoints/Fälle/Journal atomar in `/var/lib/tori/forward/watch.sqlite3` (lokal entsprechender bestehender `TORI_DATA_DIR`); paginierte API/CLI, Backup-/Restore und Referenzschutz ergänzt. **Lokal registriert und Hintergrundprozess gestartet; Erstimport aller 25 Aktien und 50 Modellzustände abgeschlossen, keine aktuellen Importfehler. Noch keine prospektiven Fälle/Erfolgsaussage oder ausgefüllten menschlichen Urteile.** 274 Python-Testfälle je 3.12/3.13 mit bestehendem Skip, 38 JS bestanden; echte lokale HTTP-Abnahme. Keine Browserprüfung, keine Orders, Nachrichten oder automatische Parameteränderung. Bestehende Webanalyse bleibt beim Öffnen aus. Keine Containerinstallation oder Veröffentlichung; `deploy/tori-watch.service` ist nur eine noch nicht unter Linux abgenommene Vorlage. Webserver startet den Beobachter nicht automatisch; später eigener Service mit gleicher Datenbasis/Secrets und dort neu registrierter Lauf-ID.

**Unabhängiger Retest-Zeitvergleich und Beobachter, 22.10.2026 (lokal):** [Vorabplan](alpaca-trendlinien/RETEST-BEOBACHTUNG-PLAN.md), [Bilanz, CLI und Betriebsgrenzen](alpaca-trendlinien/RETEST-BEOBACHTUNG-ERGEBNISSE.md), [Tabellen/Entwicklungsdiagnose](alpaca-trendlinien/RETEST-BEOBACHTUNG-TABELLEN.md). Einmaliger unveränderter Vergleich fester Safety gegen +1R/2ATR auf 06.07.–16.10.2026, 25 Aktien, Fortsetzung gespeicherter Watch-Zustände; alle Signale vor Ergebnissen eingefroren. **Der zuvor reservierte Zeitraum ist damit verbraucht; frühere Reservierungsaussagen unten sind historisch.** Zonenhauptgruppe 16 Fälle, fünf positiv, feste/ATR-Depots jeweils −2,91 %, kein wiederholter Drawdownvorteil. Hüllenreferenz neun Fälle positiv, kleiner/konzentrierter Vergleich, keine automatische neue Modellwahl. Vorabtor der ATR-Risikohypothese nicht bestanden; keine validierte Strategie. Neue isolierte `retest_observation.py`/`tools/retest_independent_*.py`/`tools/retest_observe.py`: ursprüngliche Entries, beide Modellpfade, stabiles privates Journal und Präfix-/Codeprüfung; historische Wiederaufnahme nachgewiesen, noch kein prospektiver Dauerdienst. Generischer CLI-Weg, zwei private Beispielzustände vorbereitet; universumsweiter Import, Zeitplan und Zustellung bleiben geplant. Bestehende Web-/Worker-Defaults unverändert, keine Orders, Anbieterabrufe oder Containeränderungen; kein neuer Upload. 256 Python-Tests je 3.12/3.13, 35 JS; 86 Pfade, 109 ATR-Ereignisse und vier Cash-/Risikoledger separat geprüft. Gleichen `TORI_DATA_DIR` erhalten, Code-/Quellrevisionen erfordern neue Beobachtungsgeneration; private Kurse/Zustände nicht committen.

**Drei weitere interne Retest-Exits vom 22.10.2026 (lokal):** Gescheiterter Retest an ursprünglicher Orange-Zone, Fünf-Sitzungs-Zeitexit ohne Nettoplus und Gewinnschutz ab +1R mit zwei ATR Abstand nacheinander auf denselben archivierten Entries getestet. [Feste Vorabregeln](alpaca-trendlinien/RETEST-EXIT-VARIANTEN-PLAN.md), [Fazit und Verbesserungsvorschläge](alpaca-trendlinien/RETEST-EXIT-VARIANTEN-ERGEBNISSE.md), [alle Tabellen](alpaca-trendlinien/RETEST-EXIT-VARIANTEN-TABELLEN.md). Keine neue Variante verbessert die Zonen-Rendite in beiden bekannten Phasen; ATR-Schutz senkt nur im Entwicklungsdepot den gemessenen Rückgang deutlich bei fast gleicher Rendite. Feste Safety bleibt Forschungsreferenz, ATR eine offene Risikohypothese. 155 unterschiedliche feste und 465 neue Modellpfade sowie 24 Cash-/Risikoledger separat nachgerechnet. Neue isolierte `retest_variants.py`/`tools/retest_variant_*.py`, keine Änderung bestehender Entry-/Web-/Worker-/Safety-Defaults, keine Scheduler, Orders, Nachrichten, Providerimporte oder Containeränderung. Neue 4h-Entscheidungen übergehen keine fehlenden erwarteten Quellkerzen. Alle Zeiträume waren bereits bekannt; finalen Holdout nicht ausgewertet, kein belegter zukünftiger Handelsvorteil. Private Laufdaten bleiben lokal; noch kein neuer Upload dieses Versuchs.

**Interner Retest-Exitvergleich vom 22.10.2026 (lokal):** Zwei Stopmodelle auf unveränderten archivierten Hüllen-/Zonen-Retests implementiert und geprüft: fester anfänglicher Stop gegen ausschließlich unter bestätigten höheren Tiefs nachgezogenen Stop, jeweils maximal zehn XNYS-Sitzungen. [Regeln](alpaca-trendlinien/RETEST-EXIT-TEST.md), [Bilanz und CLI](alpaca-trendlinien/RETEST-EXIT-ERGEBNISSE.md), [vollständige Tabellen](alpaca-trendlinien/RETEST-EXIT-TABELLEN.md). 155 eingefrorene Fälle/310 Modellpfade; Hauptgruppe mit kausal vollständiger 4h-Vorgeschichte, Lücken separat. Bestehendes Cash-/Risikoledger auf acht unabhängigen Modell-Depots mit 2.000 USD, 1 % geplantem Positionsrisiko, max. 25 % Allokation je Position verwendet; keine Auswahl nach zukünftiger Pfadvollständigkeit. Zonen-Retests im begrenzten bekannten Datensatz positiv, größere Gewinner tragen deutlich bei; Nachziehen kein überzeugender Mehrwert. Separater Prüfer kontrolliert alle Pfade und Depots. Neue interne `retest_exits.py`/`tools/retest_exit_*.py`, keine Änderung bisheriger Web-/Worker-/Safety-Defaults, keine neuen Scheduler, Orders oder Meldungen. Finaler Holdout nicht ausgewertet. Private Laufdaten nicht im Repository; kein neuer Upload oder Container-Rollout.

**Interne Einstiegssuche vom 21.10.2026 (lokal, eigener Versuch):** Zusätzliche bestätigte Wendepunktlinien, feste ATR-Reaktionsepisoden, getrennte strenge Hüllen/Zonen, persistierte Beobachtungszustände und JSON-Frühwarnungen sind in separaten `entry_*`-Modulen umgesetzt. Webprofile, laufende Queue und Zeitpläne verwenden diesen Versuch nicht automatisch. [Umsetzung, Regeln, CLI und Bilanz](alpaca-trendlinien/EINSTIEGSSUCHE-ERGEBNISSE.md), [vorab festgelegter Vertrag](alpaca-trendlinien/EINSTIEGSSUCHE-INTERN.md), [vollständige Vergleichstabellen](alpaca-trendlinien/EINSTIEGSSUCHE-TABELLEN.md). Offline auf 25 gepinnten IEX-Aktien: 2.504 überlappende Modell-/Familienfälle; zusätzliche Ausbruchsabdeckung, aber kein belegter Qualitätsgewinn direkter Entries. Retests sind eine offene Hypothese, Datenlücken und kleine Gruppen begrenzen die Aussage. 24 Blindfälle vorbereitet, echte manuelle Urteile noch offen. Scanner speichert Zustand/Ereignisschlüssel, versendet keine Nachrichten und richtet keinen Dauerlauf ein. Kein Upload oder Container-Rollout dieses Versuchs; keine Orders. Für einen späteren Containerlauf denselben `TORI_DATA_DIR` erhalten; neue Engine braucht neuen Versuch/Zustand. Private Kursdaten/Artefakte bleiben lokal.

**Manueller Chartstart vom 21.10.2026 (lokal):** Die Chart-Weboberfläche startet bei jedem Öffnen/Neuladen mit **Tori-Analyse aus**. Kerzen, eigene Rays und Messungen funktionieren sofort; automatische rote/grüne/orange Linien, Signalmarker und Infobox erscheinen erst über „Tori-Analyse: An“. Der Schalter bleibt während der geöffneten Seite bei Intervall-/Aktienwechseln erhalten, wird aber nicht als aktive Voreinstellung gespeichert. Datum/Replay und Forschungslinks aktivieren Tori nicht. Gespeicherte Fixierungen bleiben erhalten und können über Datum ausdrücklich geöffnet werden. Im manuellen Modus ruft die Oberfläche `analysis=0` ab; der Server überspringt Linienberechnung, Forschungs-Signalauflösung und das Registrieren einer neuen fixierbaren Analyse. `analysis=1` schaltet den bestehenden Chartanalyseweg zu. Fehlender Parameter bleibt für bisherige API-/CLI-Aufrufer kompatibel aktiv. Forschungsprofile, Zeitpläne und Safety-CLI sind davon unabhängig. Lokaler Dienst aktualisiert; noch kein neuer GitHub-Upload/Container-Rollout dieser Änderung. [Bedienung](alpaca-trendlinien/README.md), [Prüfung](alpaca-trendlinien/VERIFICATION.md).

**GitHub-Übergabe vom 20.10.2026:** Diese Übergabe auf `main` und `codex/safety-strategies` enthält die Kontaktzonenforschung, den Vergleich von sieben Exitmodellen sowie die neuen Safety-Strategien, Kriterien, vollständigen Ergebnistabellen und JSON-Werkzeuge. Die früheren Angaben „lokal/nicht veröffentlicht“ unten beschreiben den jeweiligen damaligen Prüfstand. Quellcode und Dokumentation werden übergeben; lokale Marktdatasets, Zugangsdaten, Datenbanken und private Prüfartefakte sind nicht enthalten. **Der Container wird durch den Upload nicht aktualisiert.** Für ein Update bestehenden Datenpfad/Secrets erhalten, vorher sichern und alte unterbrochene Aufträge nicht unter einer geänderten Engine fortsetzen. Der neue Safety-Scanner ist per CLI ausführbar; seine dauerhafte universumsweite Zeitplanung, gespeicherte Meldungsdeduplizierung und Positionszustandsführung sind noch nicht eingerichtet. Keine als profitabel bestätigte Strategie und keine Brokerorders.

**Neue lokale Safety-Strategien vom 20.10.2026:** Eigener optionaler CLI-Weg mit ursprünglicher Safety-Line, bestätigten verbundenen höheren Tiefs und bekannten Tages-/Wochenwiderständen; einheitlicher gepufferter Notstop plus feste Kontrollgruppe. Dazu kausale Kandidatensuche ohne Zukunfts-Evaluator, unabhängiger Nachrechner und echtes Cash-/Risikoledger. [Regeln, Werkzeugvertrag und Betriebsgrenzen](alpaca-trendlinien/SAFETY-STRATEGIEN.md). Bestehende Webansicht, Standardprofile, Queue und Zeitpläne werden nicht automatisch umgestellt. Keine Orders, keine neu eingerichteten Meldungen oder Containerinstallation. Technisch ausführbare Forschungsvarianten sind noch kein belegter profitabler Handelsstandard. Die datierten früheren Abnahmen unten bleiben historisch.

**Neuer lokaler Ausstiegsvergleich vom 19.10.2026:** `exit_research.py` und `tools/exit_study.py` vergleichen sieben explizite Exit-Auslegungen auf unveränderten archivierten Einstiegen (Grundsignal/Momentum 2 aus 3; drei Einstiegsfamilien; 5/10/20 XNYS-Sitzungen). Fester Stop, 2R, Originalrot-Fakeout, bestätigtes Grün-Nachziehen, vorher bekannter Widerstand und kombinierte Tori-Auslegung; Kosten, Gap-/OHLC-Regeln, kausale Wirksamkeit und unvollständige Pfade sind protokolliert. [Ergebnisse, Regeln und CLI](alpaca-trendlinien/AUSSTIEGSVERGLEICH.md). Ein separater Auditor prüfte alle 14.994 Modellpfade, 884 nachgezogene grüne Linien und 252 Vergleichszeilen. Geldbeträge sind **je 1.000 USD pro Einzelposition**, keine summierte Depotperformance. Der Vergleich verwendet Entwicklung und die bereits bekannte spätere Validierung; der finale Holdout bleibt geschlossen. Neue CLI, keine automatische Web-/Worker-Umstellung, kein Rollout und keine Brokerorders.

**Neue lokale Kontaktforschung vom 19.10.2026:** Auf `codex/contact-research-loops` sind feste ATR-Kontaktzonen auf unveränderter Geometrie, getrennte Kontaktqualitäten und zusätzliche versionierte Momentum-/Raum-/Safety-Profile implementiert. Drei Entwicklungsrunden plus getrennte Validierung wurden ohne Browser auf echten MSFT/AMZN/JPM/XOM/KO-IEX-Daten durchgeführt. Regeln, Entscheidungen, konkrete Ergebnisse und Grenzen: [KONTAKTZONEN-EXPERIMENTE.md](alpaca-trendlinien/KONTAKTZONEN-EXPERIMENTE.md); alle Familien/Profile/Horizonte: [Ergebnistabellen](alpaca-trendlinien/KONTAKTZONEN-ERGEBNISSE.md). Referenz, alte Qualitätsklassen und vorhandene Zeitpläne bleiben unverändert. 170 Python-Tests je unter 3.12/3.13, 27 JS-Tests. Kein neuer validierter Handelsstandard; der reservierte Holdout bleibt geschlossen. Lokale isolierte Forschungsdaten werden nicht ins Repository aufgenommen. Dieses Update ist noch nicht veröffentlicht oder im Container installiert.

Stand: **22.10.2026**. Dieses Dokument ist der zentrale Einstieg für Hermes und künftige Entwickler. Es beschreibt den tatsächlich implementierten Stand und trennt ihn von Vorhaben. Änderungen am Verhalten, an Schnittstellen oder am Betrieb müssen hier nachvollzogen werden.

**Zusätzlicher lokal abgenommener Entwicklungszweig:** `codex/research-lab` ergänzt den vollständigen Forschungsablauf als eigenen Modus `entry_mode: "lab"` mit `/lab`, versionierten Profilen, gemeinsamen Prüfphasen, Diagnose-/Vergleichsberichten, verblindeten Fallpaketen und optionaler Ausführungssimulation. Beschreibung und Werkzeugvertrag: [FORSCHUNGSLABOR.md](alpaca-trendlinien/FORSCHUNGSLABOR.md). Schema 4 ergänzt die bisherigen Tabellen. **Lokale technische Abnahme abgeschlossen:** 158 Python-Tests je unter 3.12/3.13, 27 JavaScript-Tests, isolierter Offline-Gesamtlauf einschließlich Backup/Restore und anschließende Browserprüfung. Einzelne Nachweise und Daten-/Modellgrenzen: [FORSCHUNGSLABOR-UMSETZUNG.md](alpaca-trendlinien/FORSCHUNGSLABOR-UMSETZUNG.md). SYNTHA/SYNTHB sind ausdrücklich gekennzeichnete künstliche Technikdaten, keine Marktstudie. Dieser lokale Stand ist noch nicht auf Proxmox installiert; unten dokumentierte frühere Rollouts bleiben historisch davon getrennt. Bestehende Zeitpläne werden nicht automatisch auf Labor umgestellt.

**Lokale Weiterentwicklung nach diesem Rollout:** Zusätzlich sind jetzt zufällige Tori-Suchfenster und eine getrennte Schlusskursbeobachtung nach 5/10/20 Handelstagen implementiert. Anleitung: [TORI-KURSBEOBACHTUNG.md](alpaca-trendlinien/TORI-KURSBEOBACHTUNG.md). Diese Erweiterung wurde lokal entwickelt; sie ist nicht Bestandteil des von Hermes laut Nutzerbericht installierten Commits `82d88eb`. Keine automatische Umstellung bestehender Zeitpläne.

**Präzisierung der gewünschten Forschung:** `tori.sampling="origins"` zieht verschiedene zufällige Starttage und prüft danach jede 4h-Kerze bis zum ersten Einstieg je Variante oder bis zum Ende der Entwicklungsdaten, ohne die frühere 60-Kerzen-Suchgrenze. `random` bezeichnet weiterhin den alten begrenzten Fenstervergleich. Im Starttagmodus begrenzen Ab-/Bis-Datum nur die gezogenen Starttage. Holdout bleibt reserviert. Mehrere Starttage können denselben späteren Einstieg erreichen; Starts mit Entry und eindeutige Entryzeitpunkte werden deshalb getrennt berichtet. Ein Entry ist nicht garantiert. Neue Webaufträge und das Beispiel wählen zunächst `origins`; vorhandene Aufträge/Zeitpläne werden nicht umgeschrieben.

**Update-Übergabe vom 18.10.2026:** Der zusammengeführte Stand für `main` umfasst die Forschungsnavigation und Messungsbedienung, P1/P2, die Scrollkorrektur sowie den optionalen Tori-Einstiegsmodus. Alle drei Kriterien-Dokumente sind enthalten: `LONG-KRITERIEN-ENTWURF.md`, `TORI-KRITERIEN-ARBEITSNOTIZ.md` und `TORI-EINSTIEGSMODUS.md` unter `alpaca-trendlinien/`. Für eine bestehende Containerinstallation Abschnitt 12 und `BETRIEB-P2.md` verwenden: Dienst vor dem Update stoppen und Bestand sichern, denselben Datenpfad und lokale Secrets erhalten, Python-Abhängigkeiten aktualisieren und Schema 3 berücksichtigen. Alte unterbrochene Aufträge nicht unter verändertem Engine-Hash fortsetzen. Der Tori-Modus bleibt ausdrücklich wählbar; bestehende Zeitpläne werden nicht automatisch umgestellt. Ein GitHub-Upload aktualisiert den Container nicht selbst.

## 1. Auftrag und langfristiges Ziel

Tori soll Aktien anhand automatischer Trendlinien untersuchen und dem Nutzer manuelle Sichtkontrolle ermöglichen. Langfristig soll ein Dienst auf Proxmox ein festgelegtes Aktienuniversum regelmäßig prüfen, interessante **Long**-Situationen erkennen und aufbereitete Kandidaten melden. Hermes bzw. ein lokales LLM kann Ergebnisse erklären, Fälle voranalysieren und Forschungsaufträge steuern.

Der Nutzer möchte möglichst wenig Routinearbeit. Die Webansicht bleibt dennoch ein fester Bestandteil: Aktien selbst suchen, Intervalle wechseln, Linien betrachten, vergangene Zeitpunkte ansehen, eigene Rays zeichnen und Abstände messen.

Aktueller Entwicklungsschwerpunkt ist die **explorative Untersuchung**: je Aktie X zufällige historische Startpunkte ziehen, anschließend mögliche Einstiege beobachten und deren Verlauf untersuchen. Abstand, Kontakte und Tageskontext werden zunächst als Merkmale erfasst. Aus mehreren nachvollziehbaren Untersuchungen sollen später Hypothesen und prüfbare Regeln entstehen. Eine fertige Strategie mit behaupteter Profitabilität ist nicht vorgegeben.

### Vereinbarte Leitplanken

- Long, keine Short-Strategie.
- Ausbruch und Ausbruch mit anschließendem Retest getrennt untersuchen.
- Vorläufige Linien mit zwei Kontakten mittesten; qualifizierte Linien separat ausweisen. Die derzeitige vorläufige Gruppe enthält auch andere nicht vollständig qualifizierte Paare; exakte Kontaktzahlen bleiben verfügbar.
- Alpaca mit kostenlosem IEX-Feed als technische Testbasis. EODHD für den späteren eigentlichen Lauf, insbesondere europäische Aktien, ist geplant.
- Keine Brokerorders, kein automatischer Handel im aktuellen Projekt.
- Deterministischer Rechenkern; Hermes steuert und erklärt. Ein LLM ersetzt weder OHLC-Daten noch Berechnung und Ausführungsmodell.
- Zunächst lokal fertigstellen und prüfen. Der Repository-Upload ist freigegeben; eine bestehende Proxmox-/Hermes-Installation wird dadurch nicht verändert. Die eigentliche spätere Installation soll Hermes übernehmen.

## 2. Repository, Verzeichnis und Dokumente

**Kanonisches Repository:** <https://github.com/lpzero13/Trend>

```text
Trend/                                  Git-Checkout, Dokumentation und CI
  README.md
  HERMES.md                             dieses Dokument
  AGENTS.md                             Arbeitskonventionen für Coding-Agenten
  .github/workflows/tests.yml
  alpaca-trendlinien/                    eigentlicher Anwendungsordner
    server.py                           Webserver und HTTP-Schnittstellen
    models.py, settings.py              gemeinsame Datenverträge und Datenpfad
    alpaca.py, assets.py                 lesende Provideranbindung und Katalog
    trendlines.py, analysis_service.py   Geometrie und gemeinsame Chartanalyse
    datasets.py                         unveränderliche normalisierte Bestände
    research.py                         kausale Ereignisstudie
    jobs.py                             SQLite-Aufträge und Hintergrundworker
    tori.py                             CLI mit JSON-Ausgaben
    snapshots.py                        manuelle Analysestände
    static/                             Chart- und Forschungsoberfläche
    reference/                          bisherige Pine-Referenz
    deploy/                             Unit, Wrapper und Konfigurationsbeispiele
    integrations/hermes/SKILL.md         Vorlage für den späteren Agenten
    tests/                              Python- und JavaScript-Tests
```

**Wichtig:** Ein Clone nach `/opt/trend` enthält den Code unter `/opt/trend/alpaca-trendlinien`. Die mitgelieferten Betriebsdateien erwarten den Anwendungsordner unter `/opt/tori`. Abschnitt 10 beschreibt dafür einen eindeutigen Symlink. Nicht versehentlich `server.py` im Repository-Stamm suchen oder die Queue in einem zweiten Datenverzeichnis betreiben.

Weitere Informationen:

| Dokument | Zweck |
|---|---|
| [SAFETY-STRATEGIEN.md](alpaca-trendlinien/SAFETY-STRATEGIEN.md) | Neuer optionaler CLI-Weg: Safety-Zustand, gemeinsame Eintrittsprüfung, Kandidatenscan, Cashledger und Hermes-Befehle |
| [SAFETY-ERGEBNISSE.md](alpaca-trendlinien/SAFETY-ERGEBNISSE.md) | Bilanz auf 25 Aktien, gescheiterte/positive Teilgruppen, Datenabdeckung und nächste Schritte; noch keine produktive Gewinnstrategie |
| [Anwendungs-README](alpaca-trendlinien/README.md) | Bedienung, Linienregeln, Windows-Start und Datenhinweise |
| [FORSCHUNG.md](alpaca-trendlinien/FORSCHUNG.md) | Ablauf der Ereignisstudie, Ergebnisse, CLI und API |
| [BETRIEB-P1.md](alpaca-trendlinien/BETRIEB-P1.md) | Ereignisseiten, Betriebszustand, Lastmessung und Kompatibilität beim Update |
| [BETRIEB-P2.md](alpaca-trendlinien/BETRIEB-P2.md) | Kalender-/Qualitätsaudit, Speicherprüfung, Schema 3, Backup/Restore, Berichte und Deploymenttests |
| [LONG-KRITERIEN-ENTWURF.md](alpaca-trendlinien/LONG-KRITERIEN-ENTWURF.md) | Diskussionsgrundlage; Vorschläge sind keine als optimal belegten Grenzen |
| [TORI-KRITERIEN-ARBEITSNOTIZ.md](alpaca-trendlinien/TORI-KRITERIEN-ARBEITSNOTIZ.md) | Eingereichte Tori-Zusammenfassung vom 18.10.2026, separate Einschätzung, offene Definitionen und spätere Testideen; keine aktivierten Regeln |
| [TORI-EINSTIEGSMODUS.md](alpaca-trendlinien/TORI-EINSTIEGSMODUS.md) | Separat wählbarer vollständiger Einstiegsmodus, Fixierung zu X, Testschwellen, Kriterien und Grenzen |
| [TORI-KURSBEOBACHTUNG.md](alpaca-trendlinien/TORI-KURSBEOBACHTUNG.md) | Zufällige Suchfenster, erster Einstieg je Variante, Schlusskurse nach Handelstagen und Grenzen der Stichprobe |
| [ARCHITEKTUR-V2-V3.md](alpaca-trendlinien/ARCHITEKTUR-V2-V3.md) | ursprünglicher Umbauplan, teilweise umgesetzt; enthält auch spätere Arbeiten |
| [VERIFICATION.md](alpaca-trendlinien/VERIFICATION.md) | bisherige Tests und bewusst genannte Grenzen |
| [Hermes-Skillvorlage](alpaca-trendlinien/integrations/hermes/SKILL.md) | Bedienung der Werkzeuge durch einen Agenten, noch nicht im Agenten installiert |

Lokale Screenshots und Replay-Nachweise aus dem Prüfprotokoll sind absichtlich keine Repositorydateien. Ein Clone bringt auch keine Zugangsdaten, Marktdaten oder bestehende Versuchsergebnisse mit.

## 3. Was implementiert ist

| Bereich | Implementierter Stand |
|---|---|
| Manuelle Webansicht | Kerzenchart, Aktien-/Namenssuche, Börsenfilter, Favoriten, 1h/4h/1D, Hell/Dunkel, Zoom/Pan und Zurücksetzen |
| Optionaler Fächer-Test | Python-Port des korrigierten Pine Master, bestätigte Quellpivots, eingefrorene Signallinien, Ausbruch/roter Retest und bedingte 5m-Einzelfallpfade; Details im aktuellen Fächer-Dokument |
| Automatische Linien | Wick-Hülle, gerichtete Linien, Bestätigung, Kontakte, Kontaktspanne und Auswahl im Python-Kern |
| Mehrere Intervalle | 4h/1D als Kontext, 1h zusätzlich im 1h-Chart; Ebenen ein-/ausblendbar, Linien mit Intervallbeschriftung |
| Manuelle Zeichnung | Rays mit Bearbeitung, Löschen und Rückgängig, browserlokal je Aktie |
| Messungen | Zwei Punkte, absolute/relative Änderung und Kerzenschritte; blau aufwärts, rot abwärts; Speichern, Auswahl am Rahmen, Löschen und Wiederherstellen; gemeinsamer Rückgängig-Verlauf mit Rays |
| Historische Sicht | Datumswahl in New Yorker Zeit, tatsächlich vorhandene Kerzen vor-/zurückschalten, harte Stichtagsgrenzen |
| Manuelle Fixierung | unveränderliche lokale Stände mit damaligen Rohkerzen und Ankern |
| Forschungsansicht | Über die feste Hauptnavigation „Chart / Forschung“ erreichbar; Aufträge, Zeitplan, vier Qualitäts-/Einstiegsgruppen, Merkmale, Einzelfälle, Chartlinks und JSON-Berichte |
| Forschungsseiten-Layout | Eigenes Dokumentlayout mit vertikalem Seitenscrollen und fest sichtbarer Navigation; die Scrollsperre des Vollbildcharts gilt dort nicht |
| Optionaler Tori-Modus | Vollständiger 4h-Durchlauf, Zufallsstarts bis zum Entry/Datenende oder begrenzte Zufallsfenster, ursprüngliche Linienpaare verfolgen oder zu X fixieren, drei Einstiegsvarianten, Kriterienprotokoll und 1h-Eröffnungsprüfung; optional Schlusskursänderungen nach Handelstagen |
| Automatisierung | Hintergrundworker, dauerhafte Queue, täglicher Standardzeitplan, Abbruch und Wiederaufnahme nach Prozessabbruch |
| Betriebsanzeige | Getrennte Lebenszeichen und Arbeitsphasen, Fortschrittswarnung, Datenalter und Import-/Fehlerstände ohne Providerabruf im Healthcheck |
| Datenqualität | Versionierter XNYS-Tageskalender, Rohkurs-/IEX-Hinweise, beschreibendes Audit neuer Datasets; keine automatische Verifikation von Kapitalmaßnahmen |
| Datenbetrieb | Speicherinventur und Importprüfung, transaktionale Migrationen bis Schema 4, geprüfte Backup-/Restore-CLI und reine Bereinigungsvorschau |
| Reproduzierbarkeit | Dataset-Prüfsummen, archivierte Parameter und Universen, Seed, Engine-/Regelversion und Ereignisse |
| Hermes-Schnittstelle | CLI/JSON und authentifizierbare HTTP-Job-API; Berechnung benötigt keinen Browser und kein LLM |
| Linux-Vorbereitung | systemd-Unit, externer persistenter Datenpfad, Token-/Host-Konfiguration und CLI-Wrapper |
| Repository-Tests | Python-/JavaScript-Tests, GitHub Actions für Linux und Windows; keine Provider-Schlüssel für Unit-Tests |

Laut Nutzerbericht vom 18.10.2026 hat Hermes Commit `82d88eb` einschließlich P1/P2 und Tori-Einstiegsmodus auf CT118 installiert, Schema 0 auf 3 migriert, alle 113 damaligen Python-Tests ohne Skip sowie echten Import, Offline-Forschung, Ereignisseiten, Zugriffsschutz und Anwendungsbackup/-restore geprüft. Der neue Zufallsfenster-/Handelstage-Modus wurde danach lokal entwickelt und ist dort noch nicht installiert oder abgenommen. Ein vollständiger Proxmox-Containerrestore und ein Volluniversum-Kapazitätsnachweis liegen laut Bericht weiterhin nicht vor.

## 4. Was noch nicht implementiert ist

- EODHD-Adapter und Abgleich europäischer Instrumente, Währungen und Handelssitzungen.
- Börsengetakteter Live-Kandidatenscanner mit deduplizierten Benachrichtigungen. Der Zeitplan startet derzeit wiederkehrende Forschungsaufträge.
- Vollständige Portfolio-/Broker-Simulation mit Cash, Stückzahlen, gleichzeitigen Positionen, Stopausführung, Trailing und Ausstiegen.
- Endgültige Einstiegsfilter und eine validierte Handelsstrategie.
- Automatische Analyse von Earnings, Ex-Dividenden, Splits, Liquidität und Spreads für die Eignung eines Einstiegs.
- Vollständiger historischer Instrumentenbestand einschließlich delisteter Titel und echter damaliger Datenveröffentlichungen.
- Vollständige Kalender-/Verfügbarkeitsmodelle für verkürzte Sitzungen, reguläre/erweiterte Zeiten und beide künftigen Provider.
- Automatische Regeloptimierung, unberührte externe Strategievalidierung und eine feste Entscheidung über produktive Regeln.
- Nachrichtenbasierte historische LLM-Signale. Heutiges LLM-Wissen darf nicht rückwirkend in alte Einstiege gelangen.
- Serverseitige, geräteübergreifende Ablage persönlicher Rays/Messungen. Diese liegen bisher im Browser.
- Bestätigte Volluniversum-Lasttests und eine belastbare Ressourcenplanung für Tausende Aktien.
- Automatisches Containerprovisioning, ein ausgeführter Proxmox-Rollout oder Installation der Skillvorlage im Hermes-Agenten.

## 5. Linien, Kerzenbasis und Bedeutung der Darstellung

Die Pine-Datei unter `reference/` ist eine Referenz. Die Python-Version verwendet bewusst **Abstände vorhandener Quellkerzen** statt vergangener Kalenderzeit als Steigungsbasis. Dadurch bleiben Geraden im Chart ohne reservierte Handelspausen gerade. Das ist eine Regeländerung gegenüber der früheren zeitbasierten Pine-Fassung; numerische Gleichheit wird nicht behauptet.

- 4h/1D: standardmäßig 365 Kalendertage Rückblick, Qualität zuerst.
- 1h: standardmäßig 60 Kalendertage Rückblick, innere bestätigte Linie.
- Eine qualifizierte Linie braucht mindestens drei Kontakte über mindestens sieben Kalendertage. Vorläufige Linien bleiben sichtbar/untersuchbar.
- Kontakt-Toleranz aktuell ein Tick von 0,01 USD. Das ist eine Prototypannahme, keine schon universelle Lösung für alle späteren Märkte.
- Neue Anker brauchen die vorgesehene Folgekerzenbestätigung. Nur bis zum Stichtag bekannte Informationen dürfen in die Auswahl eingehen.

Rot kennzeichnet die rote Widerstandslinie, Grün die grüne Unterstützungslinie. Eine grüne oder rote Farbe allein beweist keinen übergeordneten Auf-/Abwärtstrend. Orange markiert eine bereits gebrochene rote Linie; sie ist **noch keine Bestätigung eines Retests**. Eine später neu gewählte rote Linie ist weder der rückwirkende Einstiegsauslöser noch automatisch ein Take-Profit.

Die gleiche Quelllinie wird in anderen Chartintervallen als Gerade zwischen ihren Ankern dargestellt. Diese MTF-Darstellung ist eine **Chartprojektion** und kann wegen unterschiedlicher Kerzenverteilung von ihrem Quellintervallwert abweichen. Signale stammen aus dem Quellintervall. Ein grafischer Schnittpunkt in einem anderen Chart erzeugt kein zusätzliches Signal.

Die Infobox zeigt für den Abstand:

```text
(letzter abgeschlossener Chartschluss - grüne Chartprojektion)
/ letzter abgeschlossener Chartschluss * 100
```

Das ist kein bereits erzielter Gewinn und kein vollständiges Positionsrisiko. Negative Werte bedeuten Schluss unter der grünen Projektion. Bei Forschungsfällen werden ursprüngliche 4h-/1D-Signallinien verlängert, ohne ihre Anker neu auszuwählen. Die separat gezeichnete ursprüngliche Schutzmarke ist ein fester Preis; sie ist nicht dasselbe wie eine schräg weiterlaufende grüne Linie.

Die normale Chartanalyse sucht derzeit nur in einem kurzen Abschnitt nach Brüchen (höchstens zwölf Quellkerzen, teilweise weniger). Ihre letzte Bruchanzeige ist kein vollständiges Journal. Der Forschungsstrom erfasst die Ereignisfolge im jeweils untersuchten Abschnitt ab dem frühesten Zufallsstart.

## 6. Explorative Untersuchung und Standardparameter

### Ablauf

1. Die ausgewählten Aktien bzw. den dann aktuellen aktiven US-Katalog für den Auftrag festhalten.
2. Daten der drei Intervalle abrufen und prüfen. Bei fehlerhaften Kerzen oder veraltetem Ersatzcache keinen erfolgreichen Forschungsimport vortäuschen.
3. Normalisierte Daten und ihre Herkunft unveränderlich archivieren. Spätere Korrekturen ergeben neue Dataset-Versionen.
4. Nach ausreichend Linienvorlauf zufällige vorhandene 4h-Zeitpunkte ohne Zurücklegen auswählen. Die Ziehung verwendet keine späteren OHLC-Ergebnisse.
5. Den späteren Anteil der nach Vorlauf möglichen Starts reservieren. Such- und Beobachtungsfenster dürfen nicht in diesen Holdout reichen.
6. Vom jeweiligen Start aus den ersten bestätigten Schlussbruch einer zuvor bekannten roten 4h-Linie suchen. Fälle ohne Ereignis oder mit abgeschnittenem Suchfenster ebenfalls speichern.
7. Den Ausbruch und den späteren Retest als getrennte Varianten beobachten. Ein Rücklauf braucht eine spätere Kerze; die Ausbruchskerze zählt nicht als ihr eigener Retest.
8. Originale Linien und Merkmale am Ereignis sichern. Neue automatische Linien dürfen alte Ergebnisse nicht umschreiben.
9. Einen Einstieg frühestens mit einem nach Signalverfügbarkeit beginnenden Anbieterbalken beobachten. Die geschlossene Signalkerze ist kein garantiert verfügbarer Kaufkurs.
10. Zukünftige Kurse ausschließlich in der Auswertung nutzen. Keine späteren Hochs/Tiefs in die damalige Linienwahl oder die Merkmale zurückspielen.

### Parameter des derzeitigen Standards

| Parameter | Standard | Bedeutung |
|---|---|---|
| `symbols` | MSFT, AMZN | kleine technische Ausgangsliste |
| `universe` | explizite Liste | alternativ `all` für den angebotenen aktuellen US-Katalog |
| `samples` | 10 | angeforderte zufällige Starts pro Aktie |
| `seed` | 20261017 | wiederholbare Ziehung bei identischer Zeitbasis/Dataset |
| `history_days` | 900 | Forschungsimport; normale Chartladehistorie ist davon getrennt |
| `search_bars` | 60 | maximales Suchfenster nach jedem Start, in vorhandenen 4h-Kerzen |
| `horizons` | 5, 10, 20 | Beobachtungsfenster ab Entry, **keine Handelstage** |
| `holdout_fraction` | 0,20 | reservierter späterer Anteil nach dem Vorlauf |
| `retest_bars` | 12 | maximaler Rücklaufzeitraum |
| `retest_bps` | 20 | ±0,20 % um die ursprüngliche rote Linie |
| `latency_seconds` | 900 | angenommene Verfügbarkeit nach Kerzenschluss |
| `cost_bps` | 5 | angenommene Kosten je Kauf- und Verkaufsseite |
| `stop_buffer_bps` | 0 | Puffer auf die ursprüngliche grüne Schutzmarke |

Die Grenzwerte sind konfigurierbare Forschungsannahmen. Im bisherigen Standardmodus gibt es keinen zusätzlichen harten Filter auf kleinen Abstand, drei Kontakte oder einen bestimmten Tagestrend. Vorläufig/qualifiziert wird nach dem damaligen Paar getrennt ausgewiesen; bei gemischten Qualitäten zählt die schwächere Linie.

### Optional: vollständige Tori-Einstiegsprüfung

`entry_mode: "tori"` aktiviert separat `tori_entries.py` / `tori-entries-1`. Die Oberfläche bietet dafür „Tori-Kriterien · alle Einstiege im Zeitraum“. Statt Zufallsstarts wird jede abgeschlossene 4h-Kerze nach dem Vorlauf und vor dem Holdout geprüft. `tracked` nimmt bestätigte neue Linienpaare auf und behält alte befristet; `snapshot` fixiert nur das Paar aus den damals abgeschlossenen Daten zu X. Die grüne Auswahl kann der Chartauswahl entsprechen oder die nächste bereits bestätigte gültige 4h-Hüllenlinie unter dem Kurs verwenden. Keine späteren Anker ersetzen das laufende Setup rückwirkend.

Ausbruch, zusätzliche horizontale Bestätigung und späterer Retest sind drei getrennte Varianten. Eigenständige Kontakte, Alter, positiver Körper/Momentum, Safety-Abstand, bestätigte Tages-/optional Wochen-/Monatsstruktur und Raum zu bekannten Widerständen werden explizit geprüft. Alle Schwellen und Zustände werden archiviert; unbekannter Pflichtkontext blockiert, unbekannter freier Raum bleibt ein Hinweis. Ein Entry wird frühestens an einer nach Signalverfügbarkeit liegenden 1h-Eröffnung geprüft, mit erneutem Abstand-/Trigger-/Raumcheck. Optional `tori.sampling="origins"` für Starttage mit Suche bis zum Entry/Datenende oder `"random"` für begrenzte Zufallsfenster und `tori.observe_forward=true` für rohe Schlusskursänderungen nach `horizons` Handelstagen wählen. Dabei zählt je Fenster/Variante der erste Entry; fehlende Sitzungen und Holdout-Grenzen ergeben unvollständige Beobachtungen. Keine Ausstiege, Kosten oder Depot-P/L in dieser Tori-Auswertung. Keine A+/A-/B-Zertifizierung und noch keine Grün-Bounce-Familie. Definitionen in TORI-EINSTIEGSMODUS.md und TORI-KURSBEOBACHTUNG.md.

Setupzustände und Journal werden atomar im bestehenden Schema 3 gespeichert. Wiederaufnahme spielt den Abschnitt deterministisch nach und aktualisiert stabile IDs, statt Duplikate zu erzeugen. Der Bericht zeigt standardmäßig nur Setups mit Entry; alle Ablehnungen bleiben abrufbar. Filter `entry_filter=entries` bzw. CLI `report --entry-filter entries` gilt nur für Tori; Zusammenfassung immer ungefiltert, Oberfläche 50 Linienpaare je Seite. Identische Einstiegszeitpunkte werden je Variante/Qualität/Dataset zusätzlich dedupliziert. Variante und Linienpaar sind keine unabhängigen Trades. Der bestehende Zeitplan bleibt bis zu einer ausdrücklichen Änderung unverändert.

Im bisherigen Zufallsmodus erfolgt der grobe Einstieg an der ersten 4h-Eröffnung, die nach Signalverfügbarkeit liegt. Mit 15 Minuten Verzögerung kann das erheblich später als der nächste unmittelbar anschließende Balken sein. Der optionale Tori-Modus prüft stattdessen die erste vorhandene 1h-Eröffnung nach Signalverfügbarkeit. Vor-/Nachbörse ist möglich. Für eine spätere präzise Ausführungssimulation braucht es ein feineres Raster und eine festgelegte Sitzung.

### Ergebnisse richtig lesen

- Kursänderung und Netto-Kursänderung sind Schlusskursbeobachtungen nach dem jeweiligen Fenster. Der Abzug von Basispunkten ersetzt noch keine genaue Spread-/Slippage-Abrechnung.
- MFE/MAE sind bester/schlechtester Zwischenverlauf, nicht automatisch realisierte Ergebnisse.
- R ist nur bei positiver Distanz zwischen Einstieg und ursprünglicher Schutzmarke definiert.
- Bei +1R/+2R und Schutzmarke in derselben OHLC-Kerze ist die Reihenfolge unbekannt. Der Fall wird als mehrdeutig markiert und kein gleichzeitiger Treffer als Erfolg gutgeschrieben.
- Ein berührter Stop wird noch nicht als exakt ausführbarer Verkauf simuliert; insbesondere Gaps können schlechtere Ausführungen bedeuten.
- Fehlende Zukunft ist ein unvollständiges Fenster, keine Nullrendite und kein Erfolg.
- Mehrere Ursprünge können denselben Entry finden. Die Gruppentabelle dedupliziert diesen; einzelne Fälle bleiben sichtbar. Verschiedene überlappende Signale und wiederholte Aufträge sind weiterhin statistisch abhängig.
- Die vier Gruppen sind Ausbruch/Retest × vorläufig/qualifiziert. Nicht nachträglich nur die erfolgreichen Beispiele auswählen.

Der Holdout ist noch kein Beweis für eine profitable Strategie. Neue Hypothesen sollten auf einem festgelegten Entwicklungsteil entstehen und anschließend auf wirklich unberührten Daten geprüft werden. Ein ständig betrachteter Holdout ist nicht mehr unberührt.

## 7. Datenquelle und Datenqualität

Alpaca wird ausschließlich lesend angesprochen: historische Marktdaten und Wertpapierkatalog. Kein Konto- oder Orderzugriff. IEX ist ein einzelner US-Handelsplatz, kein konsolidierter Gesamtmarktfeed. Fehlende Feed-Transaktionen werden nicht durch künstliche Kerzen aufgefüllt. Volumen ist nicht ohne Weiteres Gesamtmarktvolumen.

Normale Chartabrufe laden standardmäßig 450 Kalendertage. Frische Daten werden gecacht; danach erfolgen inkrementelle Abrufe mit sieben Tagen Überlappung für Korrekturen. Ältere Providerrevisionen können außerhalb dieses Überlappungsfensters liegen. Die Forschungsimporte können andere explizite Historienlängen verwenden.

Intraday-Abschluss wird aus Start plus Intervall bestimmt. Neu normalisierte Tageskerzen verwenden den regulären XNYS-Schluss aus `exchange-calendars==4.13.2`, einschließlich Feiertagen, Sommerzeit und verkürzten Tagen. Alte unveränderliche Datasets behalten ihren gespeicherten Abschluss, gegebenenfalls den früheren konservativen 16-Uhr-Wert. Tatsächliche damalige Veröffentlichungslatenzen werden nicht rekonstruiert. Zeitzonen-/Kalenderversionen sind festgelegt; Instrument-/Kalenderabgleich bleibt für spätere Provider wichtig.

Neue Datasets speichern ein beschreibendes Qualitätsaudit: fehlende Sitzungen, Schlussmodellunterschiede, große Kurslücken sowie Rohkurs-/IEX-Grenzen. Das ist keine verifizierte Split-/Dividendenhistorie und kein damaliger Einstiegsfilter. Ältere Datasets ohne Audit werden im Bericht als solche ausgewiesen. Der Providervertrag trennt Abruf von Signalen; ein EODHD-Adapter ist damit noch nicht implementiert. Details in BETRIEB-P2.md.

Historische Abfragen verwenden heute verfügbare Anbieterbestände und Symbolzuordnungen. Alpacas `asof` zur Symbolzuordnung ist keine Versionierung damals publizierter Kursdaten. Rohkurse können Splits/Dividenden enthalten. Der heutige aktive Katalog ersetzt kein historisches Universum mit delisteten Titeln. Diese Grenzen müssen auch im Bericht von Hermes sichtbar bleiben.

Der gemeinsame Marktdatenabruf begrenzt Anfragen pro Prozess und wiederholt ausgewählte temporäre Fehler. Lange Stundenaggregate können trotz angefordertem Limit viele kleine Antwortseiten haben. Die Verarbeitung folgt bis zu 512 Seiten und erkennt wiederholte Tokens. Unabhängige zusätzliche CLI-Importer teilen das Prozessbudget nicht; für Routineaufträge den vorhandenen Worker verwenden.

## 8. Datenhaltung und Aufträge

Alle folgenden Verzeichnisse sind Laufzeitdaten und bleiben außerhalb Git:

| Pfad unter `TORI_DATA_DIR` | Inhalt |
|---|---|
| `market/` | veränderlicher Rohdaten-/Abfragecache |
| `assets.json` | aktuelles zwischengespeichertes Wertpapierverzeichnis |
| `datasets/<sha256>.json` | unveränderliche normalisierte Kursbestände mit Metadaten und Prüfsumme |
| `snapshots/` | manuell gespeicherte Analysestände samt damaligen Kursen |
| `research/jobs.sqlite3` | Queue, Parameter, Universen, Symbole, Pläne, Ereignisse und Versuche |
| `research/jobs.sqlite3-wal`, `-shm` | SQLite-WAL-Laufzeitdateien |
| `research/worker.lock` | Betriebssystem-Dateisperre für einen Worker |

Ohne `TORI_DATA_DIR` verwendet die Anwendung ihren eigenen `data/`-Unterordner. Unter der Linux-Unit ist **`/var/lib/tori`** der gemeinsame Datenpfad. Auch jeder direkte CLI-Zugriff muss diesen Pfad verwenden. Sonst entstehen zwei scheinbar unabhängige Auftragsbestände.

SQLite bleibt auf lokalem persistentem Speicher. Hermes in einem anderen Container nutzt HTTP statt einer gemeinsam eingebundenen SQLite-Netzwerkdatei.

### Zustände und Wiederaufnahme

- `queued`: gespeichert, noch nicht übernommen.
- `running`: vom gesperrten Worker übernommen.
- `succeeded`: Auftrag abgeschlossen ohne Titelfehler.
- `partial`: ein Teil der Titel ist mit Fehler/Auslassungsgrund beendet.
- `failed`: Auftrag oder sämtliche bearbeiteten Titel konnten nicht erfolgreich abgeschlossen werden.
- `cancel_requested`: Abbruch angefordert; kann noch auf einen Providerzugriff warten.
- `cancelled`: abgebrochen, Archiv bleibt erhalten.

Auftragsübernahme ist transaktional. Nach einem Prozessabbruch gibt die OS-Sperre den Worker frei; der nächste Worker übernimmt unterbrochene Aufträge erneut. Jeder fertig ausgewertete Versuch wird einzeln mit stabiler ID gespeichert. Importierter Dataset-Verweis und Zufallsplan bleiben erhalten. Eine unterbrochene Ereignisberechnung kann erneut ausgeführt werden; bestehende Versuche werden nicht dupliziert.

Ein Engine-Hash bindet den Auftrag an die verwendete Kernversion. Werden relevante Quelldateien verändert, darf ein alter unterbrochener Auftrag nicht stillschweigend unter neuer Logik weiterlaufen. Dafür gibt es eine verständliche Fehlermeldung; für die neue Version wird ein neuer Auftrag angelegt. Ein Hash allein archiviert noch keinen alten Code: für spätere Wiederholungen zusätzlich den zugehörigen Git-Commit festhalten.

Browserdaten liegen separat im Local Storage: Favoriten, Thema, eigene Rays/Messungen und Auswahl einer Fixierung. Ein Wechsel von Host, Port oder Browser erzeugt einen anderen Speicherbereich. Diese Daten werden beim Umzug in den LXC nicht automatisch übertragen. Die eigentlichen serverseitigen Snapshotdateien gehören dagegen in das Datenbackup.

Die Zeichenleiste und Entf/Strg+Z gelten für eigene Rays und Messungen. Neue und aus der Messungsliste geöffnete Messungen sind ausgewählt; der Rahmen lässt sich im Auswahlmodus erneut anklicken. Entf löscht die ausgewählte Zeichnung, Strg+Z nimmt die jüngste Linien- oder Messänderung zurück (auch das Anlegen einer Messung). Ein angefangener Entwurf wird zuerst abgebrochen. Der gemeinsame Verlauf umfasst maximal 40 Änderungen und bleibt bei Intervall- und Datumssprüngen derselben Aktie erhalten; Neuladen oder Aktienwechsel setzt ihn zurück. Gelöschte gespeicherte Messungen bleiben unabhängig davon über die Messungsliste wiederherstellbar. Bei fehlgeschlagener Speicherung wird ein Rückgängig-Schritt nicht verbraucht.

## 9. Konfiguration

| Einstellung | Zweck |
|---|---|
| `APCA_API_KEY_ID`, `APCA_API_SECRET_KEY` | bevorzugte Zugangsdaten für den Linux-Dienst |
| `ALPACA_CREDENTIALS_FILE` | alternativ externer Credential-Dateipfad |
| `config.local.json` | optional lokale Konfiguration des externen Dateipfads; nicht in Git |
| `TORI_DATA_DIR` | gemeinsamer persistenter Datenpfad |
| `TORI_BIND` / `--host` | Bind-Adresse, Standard `127.0.0.1` |
| `--port` | HTTP-Port, Standard 8765 |
| `--allowed-host` | erlaubter HTTP-Host; mehrfach möglich |
| `TORI_API_TOKEN` | gemeinsames Steuer-/Zugriffstoken für HTTP |
| `TORI_AUTO_ENABLED` | steuert nur das erstmalige Einrichten des Standardzeitplans |
| `TORI_API_REQUESTS_PER_MINUTE` | Prozessbudget für Marktdatenabrufe, Standard 150; an tatsächliche Providerfreigabe anpassen |
| `TORI_MIN_FREE_BYTES` | Freiplatzreserve für Importprüfung, Standard 268435456 Bytes; zusätzlich konservative Umfangsschätzung |
| `--no-worker` | nur Webserver starten; separater Worker übernimmt die Queue |

**Wichtige Besonderheit:** `TORI_AUTO_ENABLED=0` pausiert keinen schon gespeicherten Zeitplan. Zum Pausieren die Webansicht oder die Schedule-API/CLI verwenden. Der tägliche Standard für MSFT/AMZN mit zehn Starts wird nur bei fehlender gespeicherter Einstellung eingerichtet.

Ein entfernter HTTP-Start verlangt Token und expliziten erlaubten Host. Für den Browser ist HTTP Basic vorgesehen (beispielsweise Benutzer `tori`, Passwort = Token); maschinell `Authorization: Bearer ...`. Es gibt derzeit keine getrennten Rollen für Lesen und Steuern. Tokeninhaber können daher auch Aufträge und Zeitplan verändern.

`TORI_ALLOWED_HOST` in der Beispiel-Environment-Datei ist eine Konvention für die Unit, die den Wert an `--allowed-host` weitergibt. Die Anwendung liest diesen Namen nicht selbst. Er muss dem tatsächlichen Host-Header entsprechen: bei direktem Port 8765 etwa `container-name:8765`; hinter HTTPS am Standardport normalerweise der Hostname ohne `:8765`.

## 10. Spätere Erstinstallation im Linux-LXC

Dieser Abschnitt ist eine **Anleitung für einen später autorisierten Rollout**, kein Protokoll einer bereits ausgeführten Installation. Ziel-LXC, Hostname, Reverse Proxy, Backupziel und Secrets werden beim Rollout konkret festgelegt. Für den Start ist ein eigener Linux-LXC vorgesehen; Hermes kann in einem anderen Container bleiben. Lokale LLM-Inferenz ist keine Abhängigkeit von Tori.

### 10.1 Voraussetzungen

- Unterstütztes Linux mit systemd, Python 3.12 oder 3.13 inklusive `venv` (lokal geprüfte Versionen), Git und CA-Zertifikaten.
- Ausgehendes HTTPS für Alpaca und für die Installation der Python-Abhängigkeit.
- Persistenter lokaler Datenträger für `/var/lib/tori`.
- Tatsächlich bereitgestellte Alpaca-Zugangsdaten und ein eigenes langes zufälliges Zugriffstoken.
- Node.js nur für die JavaScript-Tests. CI verwendet Node 24, der Dienst braucht Node nicht.

Für Debian/Ubuntu kann Hermes die passenden Systempakete über die Paketverwaltung installieren. Konkrete Distribution und vorhandene Pakete vorher prüfen. Es gibt noch kein automatisch ausgeführtes Provisionierungsskript und keinen festgelegten Container-Ressourcenbedarf aus einem Lasttest.

### 10.2 Checkout und eindeutiger Anwendungspfad

Für eine frische Installation, nach Prüfung, dass die Ziele noch nicht belegt sind:

```bash
git clone https://github.com/lpzero13/Trend.git /opt/trend
ln -s /opt/trend/alpaca-trendlinien /opt/tori
python3 -m venv /opt/tori/.venv
/opt/tori/.venv/bin/python -m pip install -r /opt/tori/requirements.txt
```

Existieren `/opt/trend` oder `/opt/tori` bereits, zuerst deren Herkunft, Git-Status und den Symlink mit `readlink -f` prüfen. Keine fremde Installation löschen, kein unbesehenes `git reset --hard`, kein zweiter Clone über einen vorhandenen Datenordner. Der Symlink hält die mitgelieferten Unit-/Wrapperpfade gültig; der tatsächliche Git-Checkout bleibt `/opt/trend`.

Dienstbenutzer `tori` anlegen, falls er noch nicht existiert. Der Benutzer benötigt Schreibrechte auf seinen Datenpfad, nicht auf Quellcode oder Zugangsdatenkonfiguration. Für direkte Agenten-CLI-Aufrufe passende Dienstbenutzer-/Gruppenrechte festlegen; ein anderer Container nutzt besser die HTTP-Schnittstelle.

### 10.3 Secrets und Dienst

- `/etc/tori` anlegen und die Beispielwerte aus `/opt/tori/deploy/tori.env.example` nur dann als neue Datei `/etc/tori/tori.env` übernehmen, wenn dort noch keine echte Konfiguration liegt.
- Die Platzhalter lokal durch echte Schlüssel, erlaubten Host und ein zufälliges Token ersetzen. Kein Secret in Chat, Commit, Kommandozeilenargumente, URLs oder Diagnoseausgaben schreiben.
- Die Environment-Datei nur für die Dienstverwaltung lesbar machen (beispielsweise root-eigen, Modus 0600). systemd liest sie für den Dienst; der Webprozess veröffentlicht sie nicht.
- Unit `/opt/tori/deploy/tori.service` nach `/etc/systemd/system/tori.service` installieren.
- Optional den Wrapper `/opt/tori/deploy/tori-tool` ausführbar als `/usr/local/bin/tori-tool` installieren. Er setzt `/var/lib/tori` als Standard-Datenpfad, lädt jedoch keine Secrets in die Agentenausgabe.

Danach, für den ausdrücklich vorgesehenen Rollout:

```bash
systemctl daemon-reload
systemctl enable --now tori
systemctl status tori
journalctl -u tori -n 100 --no-pager
```

Die Unit verwendet `StateDirectory=tori`, startet Web und Worker, startet nach einem Fehler neu und hält den Quellbereich schreibgeschützt. Der Dienst bindet intern an `0.0.0.0:8765`; Hostprüfung und Token bleiben aktiv. Netzwerk/Firewall auf die vorgesehenen internen Clients begrenzen. Für Fernzugriff den bestehenden internen HTTPS-Proxy verwenden und dessen Host-Konfiguration passend setzen; keine ungefragte öffentliche Freigabe.

### 10.4 Abnahme im tatsächlichen Container

1. Exakten Git-Commit, Python-Version und effektiven Datenpfad dokumentieren.
2. Python-Tests ausführen; JavaScript-Tests, wenn Node für die Abnahme vorhanden ist.
3. Authentifizierten Zugriff auf `/api/health`, `/` und `/research` prüfen. `credentialsConfigured` bedeutet nur, dass Zugangsdaten gelesen werden können; es ist kein erfolgreicher Online-Authentifizierungsnachweis.
4. Einen kleinen echten Forschungsauftrag starten. Import und Fehlergründe prüfen, nicht sofort den gesamten Katalog laden.
5. Einen Einzelfall im Chart öffnen, Intervall wechseln und vor-/zurückschalten. Originalanker und Schutzmarke müssen nachvollziehbar bleiben.
6. Einen gepinnten Dataset-Lauf ohne erneuten Providerabruf wiederholen und Ergebnisse vergleichen.
7. Dienstneustart und gegebenenfalls Containerneustart prüfen: gleiche Queue, gespeicherte Ergebnisse, ein aktiver Worker und erhaltener Zeitplan.
8. Backup und Wiederherstellung an einem getrennten Testziel prüfen. Erst dann den Zielbetrieb als abgenommen kennzeichnen.

## 11. Werkzeuge für Hermes

### Direkte CLI im Tori-Container

Als Benutzer mit Zugriff auf den gemeinsamen Datenordner:

```text
tori-tool list
tori-tool health
tori-tool submit --spec /opt/tori/deploy/experiment.example.json
tori-tool status --id <job-id>
tori-tool report --id <job-id> --offset 0 --limit 250
tori-tool events --id <job-id>
tori-tool cancel --id <job-id>
tori-tool schedule
```

Ohne installierten Wrapper:

```bash
TORI_DATA_DIR=/var/lib/tori /opt/tori/.venv/bin/python /opt/tori/tori.py list
```

`submit/status/report` benötigen selbst keine Alpaca-Schlüssel: der laufende Dienst lädt Daten für Aufträge. Direkte `import`-Aufrufe dagegen brauchen Providerzugang im jeweiligen Prozess. Nicht versehentlich Secrets aus `/etc/tori/tori.env` in eine Agentensitzung ausgeben.

`worker --once` bearbeitet höchstens einen Auftrag; `worker` läuft dauerhaft. Eine OS-Sperre verhindert einen zweiten Worker auf derselben Queue. Normalerweise arbeitet bereits der Webdienst. `server.py --no-worker` ist für eine bewusst getrennte Web-/Worker-Konfiguration gedacht.

Die CLI liefert JSON. Berichte enthalten Gesamtergebnisse und paginierte Einzelfälle; Standard 250 pro Seite, höchstens 1.000. Für weitere Fälle Offset erhöhen. Einzelfallseiten nicht als den gesamten Versuch missverstehen. Das Ereignisjournal liefert jetzt über HTTP und CLI `{items, page}`, Standard 250, höchstens 1.000. `page.nextCursor` für weitere Seiten verwenden, bis `hasMore` falsch ist; der erste Lesestand bleibt trotz neuer Ereignisse stabil. Die CLI lieferte vorher eine vollständige Liste: bestehende Hermes-Parser anpassen. Eine einzelne Seite ist kein vollständiger Export. Details stehen in BETRIEB-P1.md.

Für einen Offline-Auftrag `dataset_ids` explizit zuordnen. Die IDs müssen zum Symbol gehören und lokal vorhanden sein. Bei identischem Code, Dataset und Parametern sind die fachlichen Ergebnisse wiederholbar; Erstellungszeit und Auftrags-ID sind Laufmetadaten.

### HTTP aus einem separaten Hermes-Container

Alle folgenden Maschinenaufrufe tragen den Bearer-Header; Token nicht in der URL. Beim Browser wird der normale Basic-Dialog verwendet. Host- und Originprüfung nicht zur Bequemlichkeit entfernen.

| Methode/Pfad | Ergebnis |
|---|---|
| `GET /api/health` | Anwendung, Regel-/Studienversion, Konfigurationsstatus und `operations` ohne Anbieterabruf |
| `GET /api/research/jobs` | letzte 50 Aufträge ohne große Symbolpläne, Zeitplan, Worker-Sperre und `operations` |
| `POST /api/research/jobs` | validierte Parameter, Antwort HTTP 202 mit Job-ID |
| `GET /api/research/jobs/<id>` | Status, Fortschritt, Manifest und Symbolstände |
| `GET /api/research/jobs/<id>/report?offset=0&limit=250` | Zusammenfassung und Einzelfallseite |
| `GET /api/research/jobs/<id>/events?limit=250&cursor=...` | feste Ereignisseite mit Fortsetzungscursor; erste Seite ohne Cursor |
| `POST /api/research/jobs/<id>/cancel` | Abbruch anfordern, Body `{}` |
| `GET /api/research/schedule` | Zeitplan lesen |
| `POST /api/research/schedule` | Zeitplan ändern, Body mit `enabled`, `interval_hours`, `spec` |

Lange Arbeit wird nicht im offenen HTTP-Request erledigt. Nach Submit die Job-ID behalten und den Status in sinnvollen Abständen prüfen. Wiederholte Statusabfragen sind keine neuen Aufträge. Es gibt derzeit keinen frei wählbaren Client-Idempotenzschlüssel für Submit; nach einem Netzwerkabbruch zuerst den Auftragsbestand prüfen, statt blind mehrfach zu senden.

Der Schedule läuft in Stundenabständen, standardmäßig 24. Er richtet keine börsengetakteten Echtzeit-Einstiegsscans ein. Ein fälliger automatischer Auftrag wird nicht parallel zu einem noch aktiven automatischen Auftrag gestartet. Nach einem längeren Ausfall entsteht kein ganzer Stapel nachzuholender identischer Perioden.

## 12. Regelbetrieb, Backup und Updates

### Täglich bzw. bei Fehlern prüfen

- Dienst erreichbar und genau ein Worker aktiv?
- Fortschritt aktueller Aufträge, letzter erfolgreicher Import, Fehler/Auslassungen je Titel?
- Zeitplan wirklich aktiv oder nur `TORI_AUTO_ENABLED=1` gesetzt?
- Freier Speicher für unveränderliche Datenversionen und SQLite-WAL?
- Wiederholte alte Datasets/Experimente als Wiederholungen erkennen, nicht als zusätzliche unabhängige Evidenz zählen.

Ein aktiver Prozess oder eine gehaltene Worker-Sperre allein beweist keinen gesunden Datenfluss. Ein `running`-Auftrag kann beim Provider warten. Die neue Betriebsanzeige trennt Lebenszeichen, Hauptschleife und Arbeitsfortschritt. Überfällige Lebenszeichen und längerer fehlender Fortschritt erscheinen als Warnung, ohne Aufträge automatisch zu beenden. Healthchecks lesen ausschließlich lokale Daten. Details und Grenzwerte stehen in BETRIEB-P1.md. Speicher nach Datenkategorie und freier Plattenplatz werden angezeigt (30 Sekunden Cache); vor Imports erfolgt eine konservative Platzprüfung. Externe Benachrichtigungen fehlen weiterhin.

### Backups

Datasets, Forschungsdatenbank, manuelle Snapshots und nötige Metadaten gemeinsam sichern. Credential-Dateien getrennt und geschützt sichern. Persönliche Browserzeichnungen benötigen eine eigene spätere Export-/Migrationslösung.

Die neue CLI `backup --output <neuer-ordner>` verwendet die SQLite-Backup-API und sichert Datasets/Snapshots samt Prüfmanifest. `verify-backup --path <backup>` prüft Integrität; `restore --backup <backup> --target <neuer-ordner>` stellt ausschließlich außerhalb des aktiven Datenpfads wieder her und schaltet keinen Dienst um. Markt-/Katalogcache, Secrets, Logs und Browserzeichnungen sind nicht enthalten. Vollständige Befehle und Restore-Prüfung stehen in BETRIEB-P2.md. Beim Update von einer alten Version den Dienst stoppen und mit den bisherigen Mitteln konsistent sichern, bevor neuer Code die DB öffnet. Keine gerade beschriebene SQLite-Datei isoliert kopieren und dabei WAL-Dateien ignorieren.

`storage` liefert die Größenübersicht. `cleanup-preview` schützt Dataset-Verweise in Jobs, Einstellungen, Ereignissen und Snapshots; es gibt keinen automatischen Löschbefehl. Nicht lesbare Referenzen blockieren die Vorschau.

### Codeupdate aus diesem Repository

1. Aktuellen Commit und `git status` im Checkout prüfen. Fremde lokale Änderungen erhalten und getrennt bewerten.
2. Laufende Arbeiten sinnvoll beenden oder bewusst abbrechen; anschließend Dienst stoppen und Backup erstellen.
3. Einen geprüften Commit beziehen. Für unveränderte `main`-Checkouts kann `git pull --ff-only` verwendet werden; keine divergierende lokale Arbeit durch Force-/Hard-Reset verwerfen.
4. Python-Abhängigkeiten nur entsprechend der geprüften `requirements.txt` aktualisieren. `.venv` stammt vom Zielsystem, nicht von Windows kopieren.
5. Tests ausführen. Vor Änderungen an Unit/Environment die lokalen Anpassungen vergleichen; eine echte `tori.env` niemals durch die Beispieldatei überschreiben.
6. Bei geänderter Unit `systemctl daemon-reload`, dann Dienst starten. Health, Datenpfad, Zeitplan und einen kleinen Auftrag prüfen.
7. Neue Engine-Version nicht über alte unterbrochene Aufträge hinwegtäuschen. Fehlerhafte Altaufträge im Archiv lassen und bei Bedarf neue Experimente anlegen.

Für einen Rollback auf Codeebene zunächst alte/aktuelle DB-Schemaverträglichkeit prüfen. Transaktionale Vorwärtsmigrationen sind bis Schema 4 implementiert; neuere Schemata werden abgewiesen. Es gibt keine automatische Rückwärtsmigration. Alte P1-Versionen besitzen diesen Schutz noch nicht: altes Programm nicht blind gegen eine geänderte Datenbank starten. Git-Commits identifizieren den Code; Datenbank- und Dataset-Backups gehören separat dazu.

## 13. Fehlerbehebung

| Beobachtung | Prüfung und Vorgehen |
|---|---|
| „Failed to fetch“ / lokale Verbindung fehlt | Dienst/Port/Proxy prüfen; Windows `Start-Tori.ps1`, Linux `systemctl status` und Journal. Bisherige Chartansicht kann sichtbar geblieben sein. |
| HTTP 401 | Token/Basic-/Bearer-Anmeldung prüfen; kein Beweis für einen Alpaca-Fehler. |
| HTTP 403 | erlaubten Host/Origin und Proxy-Hostheader prüfen; keine pauschale Freigabe aller Ursprünge als Lösung. |
| Alpaca lehnt Zugriff ab | Providerzugang, Feed-/Abofreigabe und genaue Anbietermeldung prüfen; keine Schlüssel protokollieren. |
| Rate-Limit / viele kleine Seiten | vorhandenen Worker, Prozessbudget und Seitennavigation verwenden; keine parallelen Vollabrufe als Umgehung starten. |
| Kein Worker verbunden | Datenpfad und OS-Sperre prüfen; bei `--no-worker` muss ein separater Worker vorhanden sein. |
| CLI sieht keine Aufträge | zuerst `TORI_DATA_DIR` und Dateirechte vergleichen; keine zweite Queue zur vermeintlichen Reparatur anlegen. |
| Auftrag bleibt bei einem Titel | Import kann lange dauern; Journal, Statuszeit und Providerfehler prüfen. Ein Abbruch muss auf laufende I/O warten können. |
| Engine-Version geändert | neue Untersuchung mit aktueller Version anlegen oder den ursprünglichen Code in separater Umgebung wiederherstellen. |
| Zu wenig Vorlauf | längeren historischen Bestand importieren oder den Titel als nicht auswertbar kennzeichnen. |
| Dataset fehlt/Prüfsumme ungültig | passende Sicherung suchen; nicht stillschweigend mit frischen Kursen unter alter ID ersetzen. |
| Keine qualifizierten Fälle | vorläufige/qualifizierte Gruppen und exakte Kontakte prüfen. Kein automatischer Nachweis, dass es allgemein keine solchen Setups gibt. |
| Alte Zeichnungen nach Hostwechsel weg | browserlokalen Origin beachten; Daten sind nicht automatisch im neuen Host gespeichert. |
| Fixierung vor ihrem Stichtag nicht verfügbar | erwartete Kausalitätsgrenze; vorherige Datenansicht ohne späteren Stand oder einen passenden älteren Stand wählen. |

## 14. Nachweise und Testverfahren

Der aktuelle lokale Stand wurde unter Windows mit **127 Python-Tests jeweils unter Python 3.12 und 3.13.12** sowie **24 JavaScript-Tests** geprüft; je Python-Lauf ein übersprungener Symlinktest wegen fehlender Windows-Berechtigung. Dazu zählen Geometrie gegen unabhängige Referenzsuche, Kerzenschluss-/DST-Grenzen, Schocks in Zukunftsdaten, Ereignisstrom/Chart-Vergleich, Retestzeitpunkt, Ausführungsverfügbarkeit, unveränderte Schutzmarken/Anker, Kostenbeobachtungen, OHLC-Mehrdeutigkeit, Deduplizierung, Offline-Wiederaufnahme, Ergebnisseiten, atomare Queueübernahme, Abbruch, Dateisperre, Authentifizierung und private HTTP-Pfade. P2 ergänzt Feiertage/Halbtage, Rohkursgrenzen, Migrationen, Backup/Restore, Platzprüfung, Überlappungen und einen echten Proxy-/Subprozess-Test mit externem Datenpfad. Die Zeichentests prüfen gemischte Linien-/Messänderungen, fehlgeschlagene Speicherung beim Rückgängigmachen und die Auswahl sichtbarer Messrahmen.

Zusätzlich wurde der echte lokale Datenbestand in einen neuen Ordner wiederhergestellt: zwei Datasets, fünf lesbare Snapshots und eine Offline-Wiederholung mit drei AMZN-Starts, identischen Fällen und identischer Zusammenfassung. P2-Messungen und Grenzen stehen in BETRIEB-P2.md.

Zusätzlich gab es einen echten lokalen Alpaca-Lauf für MSFT/AMZN mit 900 Tagen Import und je zehn Starts: 20 Starts, einer ohne beobachteten Einstieg, 194 archivierte Linienereignisse. Ein anschließender CLI-Lauf mit denselben Datasets und ohne Zugangsdaten lieferte dieselben fachlichen Fälle und dieselbe Zusammenfassung. Das belegt die technische Reproduzierbarkeit dieses Versuchs, nicht Profitabilität oder Volluniversum-Eignung.

Im Browser wurden Hell/Dunkel, Forschungsübersicht, Originalanker über einen Kerzenschritt und der Wechsel zwischen Intervallen geprüft. Ein früher Entwicklungslauf scheiterte am alten 20-Seiten-Limit; dieser Fehler wurde behoben und bleibt im lokalen Archiv nachvollziehbar.

Zusätzlich wurden die Hauptnavigation Chart/Forschung sowie Anlegen, Löschen und Rückgängigmachen einer Messung über Zeichenleiste, Entf und Strg+Z im Chrome-Browser geprüft. Rückgängig nach einem Intervallwechsel stellt den vorherigen Messungsbestand wieder her.

Aus dem Anwendungsordner:

```text
python -m unittest discover -s tests -q
node --test tests/test_geometry.cjs tests/test_snapshot_view.cjs tests/test_measurements.cjs
```

Die Repository-CI ist für dieselben Suites auf Linux und Windows mit Python 3.12 und 3.13 eingerichtet. Sie importiert keine echten Zugangsdaten und stellt keinen Container bereit. Das jeweils konkrete Ergebnis ist im Actions-Lauf des betreffenden Commits zu prüfen; die lokale Ausführung bestätigt keinen Remote-Lauf.

## 15. Roadmap und nächste sinnvolle Schritte

### Nächste lokale Entwicklung

1. Mehr Aktien und unterschiedliche Marktphasen untersuchen, zunächst begrenzte feste Listen statt sofort Volluniversum.
2. Einzelne positive und negative Fälle gegen den archivierten Chart prüfen. Kontaktzahl, Tageskontext, Abstand und Risikodistanz als Merkmale vergleichen.
3. Berichte für diese Merkmale verständlicher machen; Roh-JSON bleibt eine überprüfbare Grundlage, nicht die einzige künftige Benutzeroberfläche.
4. Datenkontrollen und Session-/Verfügbarkeitsmodell vervollständigen. Kapitalmaßnahmen und bekannte unzuverlässige Abschnitte markieren.
5. Erst dann konkrete Einstiegs-/Ausstiegshypothesen festlegen und Entwicklungs-/Validierungszeiträume vor dem Test trennen.

### Danach: echter Strategie-Backtest

Explizite Regel für Kauf, Rücklauf, initialen Stop, Stopnachziehen, Teil-/Gesamtausstieg und Ende des Testzeitraums. Stückzahlen, Kapital-/Risikobudget, Kosten, Slippage, Kurslücken und gleichzeitige Kandidaten berücksichtigen. Ausführung auf einem passenden feineren Raster simulieren. Vier Testgruppen sauber vergleichen; keine A/B-Einstiege doppelt als unabhängige Positionen in dasselbe Portfolio addieren.

### Danach: Container, Datenanbieter und produktiver Scanner

Den LXC nach Abschnitt 10 installieren und abnehmen. Hermes an die Job-API anbinden. EODHD als zweiten Adapter mit eigenem Datenvertrag ergänzen; Datenunterschiede zunächst gegentesten. Erst mit festgelegten Kriterien nach tatsächlichen Quellabschlüssen scannen, verpasste Abschlüsse nachholen und Nachrichten über eine deduplizierte Ausgangsqueue senden.

Die konkrete Meldeplattform und relevanten Situationen sind noch festzulegen. Ohne neuen Auftrag keine Nachrichten an Dritte senden. Ein rein technischer Hintergrundlauf ist von einer öffentlichen Veröffentlichung oder einer Handelsausführung getrennt.

### Späterer Ausbau

Portfolioversuche, unabhängige Validierung, externe Überwachung, Datenaufbewahrung/Archivierung, regelmäßige Restore-Übungen im Zielcontainer, serverseitige Zeichnungen und bessere Berichtexporte. Vorwärtsmigrationen, Backup/Restore und Aufräumvorschau sind bereits implementiert. Bei gemessenem Bedarf Arbeit auf mehrere Prozesse/Worker aufteilen und Datenbankwahl prüfen; kein Ressourcenversprechen für das gesamte Aktienuniversum aus dem bisherigen Zweititeltest ableiten.

## 16. Arbeitsweise für Hermes

Vorhandene Jobs und Berichte zuerst lesen. Für neue Versuche Parameter und Zweck festhalten. Änderungen an Parametern ergeben neue Experimente; frühere Ergebnisse nicht passend umdeuten. Gespeicherte Originalsignale zitieren, fehlende Daten/Beobachtungen nennen und Stichprobenabhängigkeit erklären.

Hermes darf im jeweils beauftragten Umfang installieren, konfigurieren, Aufträge einreichen und technische Fehler untersuchen. Die Skillvorlage ist eine Hilfe, keine schon eingerichtete Integration. Für Containerinstallation, andere Secretquellen oder Nachrichtenwege den tatsächlichen Nutzerauftrag und die vorhandene Umgebung berücksichtigen. Dieses öffentliche Repository enthält absichtlich keine Zugangsdaten und ist selbst keine Aufforderung, eine bestehende Infrastruktur sofort umzubauen.

Keine Brokerorders ergänzen und keine profitablen Regeln behaupten, bevor dafür eine eigene, geprüfte Aufgabe und belastbare Evidenz vorliegen. Das Ziel ist nachvollziehbare Forschung mit einer dauerhaft nutzbaren manuellen Webansicht.
