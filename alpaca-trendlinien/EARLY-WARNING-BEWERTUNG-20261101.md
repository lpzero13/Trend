# Bewertung des Vorwarnscanners – 01.11.2026

Die technische Grundlage und der historische Vorwarnversuch sind umgesetzt.
Als Unterstützung einer manuellen Beobachtungsliste ist der Ansatz brauchbar.
Das Ziel, ein bis zwei Tage vor möglichst jedem Ausbruch informiert zu werden,
wird bisher nur teilweise erreicht. Ein laufender Alarmdienst ist noch nicht eingerichtet.

## Was funktioniert

- Drei getrennte Familien und kausale, gemeinsame Master-/Pilotberechnung.
- Stabile Kandidatenherkunft vor dem Entry, getrennte Phasen, Originalsnapshots
  und keine täglichen Wiederholungen desselben Warnzustands.
- Variantenvergleich auf 69 echten lokalen Aktien, vier bekannten Zeitfenstern
  und 1.004 Handelstagen. Je Fenster erfüllen 65–68 Aktien den notwendigen Vorlauf.
- Zwölf identisch versorgte Varianten; keine nachträgliche Optimierung der
  Schwellen anhand des großen Laufs. Der Standard `distance:1` bleibt eine
  Versuchsannahme, keine freigegebene Handelsregel.
- Kontaktqualität am Warnzeitpunkt, spätere Qualität und ursprünglich gewarnte
  Linie werden nicht rückwirkend miteinander gleichgesetzt.
- Kopflose CLI, atomare Wiederaufnahme je Aktie, Plan-/Code-/Datasetbindung,
  Stummschaltung/Snooze und ergebnisblinde historische Briefings.

## Konkreter Nutzen der einfachen 1-ATR-Ausbruchsbeobachtung

Referenz sind 2.770 gültig abgesicherte, episodenweise Ausbruchs-Entrybestätigungen.
1.436 davon wurden bei noch aktiver Beobachtung vorher angekündigt: **51,8 %**.
Bei 1.413 dieser Fälle war auch die technische Warnlinie dieselbe wie beim Signal;
23 spätere Signale betrafen eine andere Linie derselben Herkunft.

Bei **953 Fällen bzw. 34,4 % aller Ausbruchs-Entries** lag die aktive Warnung ein
bis zwei Sitzungstage vor dem rohen Rot-Bruch der Episode. Der Median unter den
vorher gewarnten Ausbrüchen beträgt eine Quellkerze bzw. 21,5 reale Stunden bis
zum rohen Bruch. Bis zur späteren Entrybestätigung beträgt der Median zwei Kerzen.
Diese verschiedenen Endpunkte dürfen nicht als dieselbe Vorbereitungszeit ausgegeben werden.

Die Ausbruchsbeobachtung allein erzeugt einschließlich Warnstufen-Upgrades im
Mittel **2,99 hypothetische Meldungen je Handelstag**, am Spitzentag 22. Für die
Sichtprüfung ist eine priorisierte Liste nötig; ein garantiertes Kontingent von
höchstens vier interessanten Fällen pro Tag ergibt sich daraus nicht.

Unter den aufgelösten Ausbruchsbeobachtungen verlaufen **48,8 %** ohne passenden
gültigen Entry bei noch aktivem Watch. Das bedeutet keine entsprechende
Verlustquote: Es wurden hier keine Käufe, Fills oder Exitpfade simuliert.

## Was die Zusatzbedingungen bringen

Bei Ausbrüchen senkt aktive Annäherung als Pflichtbedingung die Erfassung von
51,8 auf 40,1 %. Aktive Annäherung plus Verengung senkt sie auf 36,9 %.
Der Anteil später bestätigter Fälle unter allen Warnungen bleibt dabei mit
51,0 / 51,5 / 51,3 % nahezu gleich. Unterschiedliche Fallgruppen und bekannte
historische Daten erlauben daraus keinen kausalen Qualitätsnachweis.

Deshalb würde ich aktive Annäherung, Verengung, Kontaktklasse und Tageskontext
zunächst **anzeigen und zur Sichtprüfung sortierbar machen**, aber nicht gemeinsam
als zwingendes Eingangstor verwenden. Eine entsprechende neue Priorisierungslogik
wurde noch nicht als erfolgreiche Auswahl validiert.

Frühe Zweikontakt-Warnungen sind relevant: Unter den 317 vorher angekündigten,
später qualifizierten Ausbruchs-Entries waren 68 zum Warnzeitpunkt erst Zweikontaktfälle.
Sie sollten entsprechend markiert bleiben, statt pauschal entfernt oder später
rückwirkend als qualifiziert ausgegeben zu werden.

## Retest und Safety-Bounce

Bei 1 ATR werden 34,9 % der roten Retestbestätigungen bzw. 45,2 % der
Safety-Bounce-Bestätigungen auf Episodenebene vorher erfasst. Die Beobachtungen
erzeugen zusammen zusätzlich etwa 4,35 Meldungen pro Tag; alle drei Familien
zusammen ergeben rund 7,34 Meldungen täglich, maximal 33 am selben Tag.

Vorwarnung vor der Bestätigung ist nicht immer Vorwarnung vor der ersten
Berührung. Beim roten Retest lag der Median bis zum ersten Kontakt bei einer
Kerze, beim Safety-Bounce bei null Kerzen. Diese Familien würde ich deshalb
als getrennte zusätzliche Radare behandeln und nicht als bereits gelöste
Ein-bis-zwei-Tage-Vorwarnung verkaufen.

## Wichtigste nächste Verbesserung

Bei 1.210 späteren Ausbruchs-Entries gab es bereits eine Vorwarnung, deren
Beobachtung aber vor dem Entry geschlossen war. Die ursprüngliche Linie oder
Safety war nicht mehr intakt, die Distanz war zu groß geworden oder der Aufbau
war abgelaufen. Ein späterer Entry macht diesen früheren Abschluss nicht falsch.

Hier liegt ein konkreter nächster Versuch: nach einem **wirklich erneuerten**
Aufbau begrenzt erneut freigeben, ohne kleine Linienänderungen oder jeden
weiteren Tag zu neuen Alarmen zu machen. Eine neue Safety-Herkunft und neu
bestätigte Kontakte könnten dafür getrennt geprüfte Kriterien sein. Die Fälle
sind aktuell weiterhin als nicht aktiv erfasst gezählt. Eine lockerere
Wiederfreigabe wurde nicht heimlich zur Ergebnisverbesserung eingebaut.

## Technische Abnahme

- 586 Python-Tests ohne Fehler, ein bestehender Skip; alle 104 JS-Prüfungen bestanden.
- Unabhängiger Nachrechner für alle 106.333 gespeicherten Warnzustände über die
  zwölf überlappenden Policies: ATR separat rekonstruiert, Preise/Abstände,
  Tages-SMA-Kontext, Bekanntheitsgrenzen, Projektionen und alle 36 Gruppen nachgerechnet.
- Fünf echte Quellen separat bis zu einem historischen Zeitpunkt abgeschnitten:
  759 Warnzustände entsprechen dem großen Lauf. Stark veränderte zukünftige
  Tageskurse ändern diese Präfixwarnungen ebenfalls nicht.
- Abschlusskorrekturen betrafen ausschließlich geeignete Briefingfenster und
  die fehlende Rot-Clean-Close-Schwelle beim Safety-Bounce. Alle 36 Ergebnisgruppen
  des erneuten 69-Aktien-Laufs stimmen mit der vorherigen Fassung überein.
- Keine Providerabrufe, Browserbedienung, Brokerorders, laufenden Nachrichten,
  neuen Daemons, Containerinstallation oder GitHub-Veröffentlichung.

Der Versuch verwendet bekannte Daten und ein heutiges Überlebendenuniversum.
Er ist eine Funktions-/Beobachtungsstudie und keine unabhängige Gewinnbestätigung.
Private Endfassung: `artifacts/early-warning-wide-final-20261101`, Planbindung
`4904c6bf1ab0ad9fe6b2f25df6cb44e20495afc124e8b0ff15e87b90c4277e85`.

Alle Tabellen: [EARLY-WARNING-ERGEBNISSE-20261101.md](EARLY-WARNING-ERGEBNISSE-20261101.md).
Werkzeuge, implementierte Funktionen und geplanter Livebetrieb:
[EARLY-WARNING.md](EARLY-WARNING.md).
