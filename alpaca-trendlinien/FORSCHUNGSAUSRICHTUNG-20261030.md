# Verbindliche nächste Forschungsrichtung: jedes Signal bis zum regelbasierten Exit

Nutzerentscheidung vom **30.10.2026**, für die Fortsetzung nach der heutigen Pause und spätere Arbeiten. Diese fachliche Ausrichtung hat Vorrang vor älteren Roadmaps, die feste Tagesexits und begrenzte gemeinsame Depotplätze als Hauptversuch behandeln.

**Historischer Stand am 30.10.: ausschließlich gespeichert und pausiert. Fortsetzung am 31.10.2026 beauftragt und umgesetzt:** [Signalstudie/CLI](SIGNALFALLSTUDIE.md), [Ergebnisse](SIGNALFALL-ERGEBNISSE-20261031.md), [Bewertung](SIGNALFALL-BEWERTUNG-20261031.md). Eigenständiger neuer Modus; frühere Ergebnisse, Versuchskonfigurationen und funktionierende Programmteile bleiben erhalten. Keine Providerimporte, Orders, Daemons, GitHub-Publikation oder Containeränderung.

## Fragestellung

Für jedes nach den festgelegten Einstiegskriterien erkannte Signal nachvollziehen: Wie entwickelt es sich bis zum regelbasierten Exit? Wie viele Fälle enden positiv/negativ, wie groß sind typische Gewinne/Verluste, und tragen wenige Ausreißer den gesamten positiven Ertrag?

**Präzisierung desselben Tages:** „Jedes Signal“ meint eine echte neue regelkonforme Einstiegsgelegenheit, nicht jede weitere Kerze eines weiterhin gut aussehenden Dreiecks. Beispiel: Eine am ersten Tag erkannte und ausgelöste Struktur bleibt am zweiten und dritten Tag derselbe Fall. Entsteht später, beispielsweise am zehnten Tag, eine tatsächlich neue geeignete Struktur beziehungsweise neu bestätigte Einstiegsepisode, kann daraus ein neuer Fall werden. Zehn Tage sind ein Beispiel, keine Wartefrist.

## Szenarien statt täglicher Wiederholungssignale

- Fortschreibung einer Linie, neue Linienversion, weiterer Kontakt oder weiterhin erfüllte Bedingungen allein erzeugen keinen neuen Trade-Fall. Eine bloß andere technische Linien-ID reicht ebenfalls nicht als neue Gelegenheit.
- Ein Setup bekommt eine über seine Entwicklung beständige Szenario-/Episodenzuordnung. Beobachtung, Bestätigung, Entry, Linien-/Stopupdates sowie Abschluss/Invalidierung werden als Ereignisse desselben Szenarios gespeichert.
- Eine neue Gelegenheit muss anhand vorab definierter, damals bekannter Struktur-/Ereignisbedingungen begründet sein: etwa eine neue tragfähige Ankerstruktur oder ein nach eindeutiger Invalidierung/Trennung neu aufgebautes und bestätigtes Setup. Diese Abgrenzung ist vor dem großen Lauf formal festzulegen; kein willkürlicher Tages-Cooldown und keine Auswahl nach späterem Gewinn.
- Ausbruch und späterer roter Retest derselben Struktur behalten eine gemeinsame Herkunft. Sie können als unterschiedliche Entryvarianten verglichen werden, zählen aber nicht als zwei statistisch unabhängige neue Dreiecke. Dasselbe gilt für verschiedene Exitvarianten desselben Einstiegs.
- Eine noch offene ältere Position verhindert keine tatsächlich neue Gelegenheit, da diese Forschungsstufe keine gemeinsamen Kapital-/Slotsperren hat. Das erlaubt keine täglichen Wiederholungsentries im unveränderten Setup.
- „Sinnvoll/gut“ bezeichnet die zu diesem Zeitpunkt erfüllten Struktur-/Einstiegskriterien, nicht einen im Nachhinein erfolgreichen Kursverlauf. Auch später verlorene oder vorher invalidierte Setups bleiben dokumentiert, mit getrennten Status-/Nennern.

Die bisherigen 5-/10-/20-/40-/80-Tage-Auswertungen waren ursprünglich Beobachtungshorizonte für die technische Einschätzung von Signalen. Sie sind **keine gewünschten verbindlichen Strategie-Exits**. Die inzwischen daraus abgeleiteten Zeitexit-/Depotversuche bleiben historische Vergleichsstudien; ihre Optimierung ist nicht mehr die nächste Hauptaufgabe.

## Keine gemeinsame Kapital- oder Slotbegrenzung

- Jede echte neue Einstiegsgelegenheit erhält einen eigenen simulierten Fall; wiederholte Kerzen desselben Setups nicht. Kein Ausschluss wegen fehlender Depotplätze, belegten Kapitals, 25-Prozent-Allokation oder bereits gehaltener Position derselben Aktie.
- „Unendliches Kapital“ bedeutet für diese Untersuchung keine gemeinsame knappe Geldbörse. Eine Million USD war eine illustrative Größenordnung, kein neues verbindliches Startkapital und kein Ersatz durch ein lediglich größeres weiterhin begrenztes Depot.
- Auch zeitlich überlappende Signale derselben Aktie können getrennt untersucht werden. Identische doppelt gelieferte Ereignisse werden weiterhin dedupliziert; unterschiedliche Szenarien behalten eigene stabile IDs.
- Ein einheitlicher Nominalbetrag beziehungsweise eine normierte Einzelposition kann später für Vergleiche festgelegt werden. Neben R bleiben prozentuale Kursrendite und gegebenenfalls Gewinn/Verlust bei identischem Einsatz sichtbar. Keine Addition aller Einzelfälle zu einer angeblich finanzierbaren Depotkurve.
- Alle erkannten Signale bleiben im Bestand. Wenn ein regelkonformer Entry tatsächlich nicht feststellbar ist, etwa wegen fehlendem Entrykurs oder inzwischen ungültiger Safety, bekommt der Fall einen dokumentierten Status. Unbegrenztes Kapital erfindet keine Ausführung und ändert nicht die Entryregeln.

## Kein zeitgesteuerter Zwangsverkauf

- Keine Schließung nur deshalb, weil Tag 5, 10, 20, 40 oder 80 erreicht wurde. Kein versteckter Ersatz wie eine andere feste maximale Haltedauer.
- Ausstiege folgen den ausdrücklich definierten Trendlinien-/Safety-/Stopregeln. Ursprüngliche Safety fortschreiben oder eine zulässige neue Safety übernehmen sind getrennte nachvollziehbare Varianten; eine neue Linie darf nur nach tatsächlicher Bestätigung wirksam werden.
- Einen zusätzlichen Notstop dürfen wir als klar benannte Variante prüfen. Stopauslösung, Puffer, Aktualisierungszeitpunkt und Ausführung müssen vorab eindeutig feststehen. Keine Garantie eines Fills genau am Stop bei Gaps.
- Zwischenstände nach einer bestimmten Tageszahl können optional beschreibende Messpunkte bleiben. Sie erzwingen keinen Exit und haben derzeit keine Priorität.
- Ein begrenztes Entry-Suchfenster für einen technisch überschaubaren Versuch ist weiterhin möglich. Es darf keine daraus entstandene Position still am Fensterende schließen.

## Endliche Daten und vollständige Fallverwaltung

„Kein Zeitexit“ hebt das Ende der tatsächlich vorhandenen Historie nicht auf. Ist dort noch kein regelbasierter Exit aufgetreten, bleibt der Fall offen beziehungsweise am Datenende rechtszensiert. Letzter beobachteter Buchgewinn wird gesondert ausgewiesen, nicht als abgeschlossener Trade verbucht.

Datenlücken können einzelne Fälle nicht abschließend bewertbar machen. Sie dürfen weder erfundene Kerzen noch einen erzwungenen Exit erzeugen. Ein solcher Fall stoppt **nicht die Auswertung aller anderen Signal-Fälle**. Erneute Datenbeschaffung oder Wiederholung der bisherigen Zeitreihen-/Depotstudien ist zunächst keine Priorität; vorhandene Daten verwenden und Grenzen sichtbar halten.

Stabile Zuordnung pro Fall: Dataset/Engine/Regelversion, Aktie, Quellintervall, Szenario/Signal-ID, Kontaktklasse, Signal-/Entryzeit, ursprüngliche Linien und Safety, initiales Risiko, aktive Stop-/Safety-Änderungen samt Verfügbarkeits-/Wirksamkeitszeitpunkt, Exitregel/-grund/-kurs, Kosten und Status.

Für spätere begründete Regelverbesserungen zusätzlich möglichst vollständige **am Entry bekannte Merkmale** speichern: Dreiecks-/Ankergeometrie und Linienherkunft, Kontaktzahl/-abstände, Alter/Steigung der Linien, Entrytyp, initiale Safety-/Stopwahl, Kursabstand zur Safety und zum tatsächlichen Stop in USD/Prozent/ATR, damals bekannter ATR samt Quellintervall und bestätigter übergeordneter Kontext. Spätere Pfadmerkmale wie MFE/MAE, Stopberührungen, Umbauten, Exit und Ergebnis bleiben klar als nachfolgende Beobachtungen getrennt.

Ziel ist eine breite auswertbare Fallbasis für Fragen wie geeigneter Mindeststopabstand und zulässige Safety-Nachführung. Nicht für jede weitere Tageskerze ein Duplikat erzeugen. Neue aus diesen Daten abgeleitete Grenzwerte zunächst als Hypothesen behandeln und an anderen vorher getrennten Daten beziehungsweise prospektiv prüfen; keine Optimierung und Erfolgsbestätigung auf derselben Stichprobe.

Wiederaufnahme muss ohne verlorene oder doppelte Fälle funktionieren. Technische Parallelität ist eine Ressourcenfrage; sie ist keine ökonomische Slotbegrenzung. Unabhängig simulierte Fälle sind statistisch weiterhin abhängig, wenn sie dieselbe Aktie, Bewegung oder Marktphase betreffen.

## Wichtigste Auswertung

Getrennt nach Einstiegsfamilie (Ausbruch, roter Retest, Safety-Bounce), Kontaktklasse und Exitvariante:

- Alle erkannten Signale, feststellbare Entries, abgeschlossene Gewinne/Verluste, offene und datenbedingt nicht bewertbare Fälle mit ehrlichen Nennern.
- Trefferquote der abgeschlossenen Fälle, Mittelwert **und** Median von Netto-R und Kursrendite, typische und extreme Verluste.
- Haltedauer als Ergebnis der Exitregel, MFE/MAE und zwischenzeitliche Rückgänge.
- Anteil weniger großer Gewinner, Beitragsverteilung über Aktien/Zeiträume und Sensitivität gegenüber Ausreißern. Keine nachträgliche Auswahl nur erfolgreicher Fälle.
- Keine Behauptung „die Signale sind überwiegend gut“, wenn das Resultat nur auf einer durch Datenende/Beobachtbarkeit günstigen Teilmenge beruht. Bestehende positive Befunde bleiben Forschungsbefunde, keine bereits validierte Handelsfreigabe.

## Priorität für die Fortsetzung

1. Vorhandene kausale Signalerkennung und Ausführung wiederverwenden; eine eigenständige Signal-/Exit-Untersuchung von gemeinsamer Depotsteuerung trennen. Bestehenden manuellen Chart und alte Versuche erhalten.
2. Echte neue Szenarien/Einstiegsereignisse von Fortschreibungen und Wiederholungssignalen abgrenzen. Deren Entrydaten und erklärende Merkmale unveränderlich registrieren. Keine Kapital-/Slot-/Ein-Position-pro-Aktie-Sperre in diesem Forschungsmodus.
3. Bis zu den jeweiligen regelbasierten Exits beziehungsweise dem echten Datenende fortschreiten. Bestehende Funktionen mit festem Horizont nicht unverändert als vermeintlich unbegrenzten Modus verwenden.
4. Ursprüngliche und aktuelle Safety-Varianten auf denselben Signalen vergleichen; Notstop gegebenenfalls als zusätzliche getrennte Variante. Wenige klar benannte Regeln statt gleichzeitiger Kombination aller Verbesserungsideen.
5. Zunächst technisch überschaubaren Ausschnitt prüfen, danach vorhandenen Bestand auswerten und die oben genannten Fall-/Qualitätsstatistiken erstellen.

## Zurückgestellt

40-gegen-80-Tage-Optimierung, Verlängerungs-Gate an Tag 40, drei Depotplätze, begrenztes Gesamt-/Allokationskapital und Auswahl „besserer“ Trades wegen freier Slots gehören derzeit nicht zur Hauptfrage. Ebenso keine erneuten großen Providerimporte oder alleinige Wiederholung vorhandener Zeitfenster. Die verzögerte enge Safety und ein Risiko-Floor bleiben optionale Forschungsnotizen; sie werden nicht heute gleichzeitig eingebaut oder als bewiesene Verbesserungen behandelt.

Ein echtes gemeinsames Depot, ausführbare Stückzahlen, Kapitalbelegung und Portfolio-P/L können später als eigener Schritt folgen. Am 30.10. war diese Ausrichtung nur gespeichert und die Forschung auf Nutzerwunsch beendet. Am 31.10. erfolgte der erneute Auftrag; der neue Einzelfallmodus ist umgesetzt und mit vorhandenen Daten durchgelaufen. Weitere subjektive Exitbestandteile und unabhängige Validierung bleiben offen; siehe verlinkte Einordnung.
