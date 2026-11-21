# Historische Vorwarnstudie – 01.11.2026

69 vorhandene echte SIP/split-Aktien, 1004 XNYS-Handelstage in vier bereits bekannten Forschungsfenstern.
Fenster: 2018, 2021, 2023, 2025-2026.
Keine Providerabrufe, Orders, P/L-Studie, neue Holdout-Auswahl oder laufenden Nachrichten.

Die gemeinsame kausale Master-/Pilot-Entrylogik läuft erneut über die Quellen. Vorwarn-Episoden entstehen bereits bei Kandidatenerkennung; diese neue Gruppierung ist nicht die alte 1.790er-Fallauswahl. Die Entryzahlen sind je Familie/Policy episodenweise deduplizierte Bestätigungen mit gültiger Anfangsabsicherung, keine behaupteten Fills.
Je Policy dieselbe Referenzmenge. Verschiedene Policies teilen Fälle und dürfen nicht als unabhängige Stichprobe addiert werden. Ohne ausreichenden Vorlauf wird das jeweilige Aktienfenster ausgeschlossen.

## Abstandswarnungen

| Familie | ATR-Schwelle | Entries | Vorwarnungen | Entries vorher erfasst % | Davon 1–2 Sitzungstage vor Entry: Anteil aller Entries % | Median Vorlauf / Kerzen | Verpufft unter aufgelösten Warnungen % | Unentschieden | Meldungen/Tag | Spitze/Tag |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ausbruch | 1.5 | 2770 | 2911 | 50.7 | 37.0 | 2.0 | 51.5 | 17 | 3.17 | 15 |
| Roter Retest | 1.5 | 1874 | 2200 | 32.9 | 30.0 | 2.0 | 71.7 | 24 | 2.47 | 20 |
| Safety-Bounce | 1.5 | 1294 | 2271 | 46.1 | 32.7 | 2.0 | 73.5 | 24 | 2.73 | 16 |
| Ausbruch | 1 | 2770 | 2818 | 51.8 | 37.5 | 2.0 | 48.8 | 15 | 2.99 | 22 |
| Roter Retest | 1 | 1874 | 1955 | 34.9 | 30.7 | 2.0 | 66.2 | 20 | 2.13 | 16 |
| Safety-Bounce | 1 | 1294 | 1937 | 45.2 | 28.2 | 1.0 | 69.5 | 17 | 2.23 | 12 |
| Ausbruch | 0.5 | 2770 | 2327 | 46.9 | 32.7 | 1.0 | 44.0 | 9 | 2.32 | 14 |
| Roter Retest | 0.5 | 1874 | 1313 | 31.3 | 24.1 | 1.0 | 54.9 | 12 | 1.31 | 11 |
| Safety-Bounce | 0.5 | 1294 | 1039 | 22.0 | 9.9 | 1.0 | 72.4 | 6 | 1.03 | 11 |

Vorlaufmedian nur unter tatsächlich vorher gewarnten Entries. 1–2 Sitzungstage bezeichnet den Abstand der Börsen-Sitzungsdaten, keine vollen 24–48 Stunden; Kerzen werden separat gemessen. Eine Warnung auf der Entrykerze zählt nicht als rechtzeitig.
Verpufft bedeutet: Beobachtung wurde vor einem passenden gültigen Signal aufgelöst. Ein Kursverlust oder tatsächlicher Stop-Fill ist damit nicht nachgewiesen. Spätere Signale nach bereits geschlossener Beobachtung werden nicht als erfolgreiche Vorwarnung gutgeschrieben.

## Zusätzliche Merkmale als Pflichtbedingungen, jeweils 1 ATR

| Familie | Variante | Vorwarnungen | Erfasste Entries % | Bestätigung unter allen Warnungen % | Meldungen/Tag |
|---|---|---:|---:|---:|---:|
| Ausbruch | distance | 2818 | 51.8 | 51.0 | 2.99 |
| Roter Retest | distance | 1955 | 34.9 | 33.5 | 2.13 |
| Safety-Bounce | distance | 1937 | 45.2 | 30.2 | 2.23 |
| Ausbruch | active | 2154 | 40.1 | 51.5 | 2.26 |
| Roter Retest | active | 469 | 7.8 | 31.1 | 0.49 |
| Safety-Bounce | active | 1477 | 35.6 | 31.2 | 1.67 |
| Ausbruch | compression | 2596 | 47.3 | 50.4 | 2.73 |
| Roter Retest | compression | 1778 | 34.4 | 36.2 | 1.94 |
| Safety-Bounce | compression | 1512 | 35.2 | 30.2 | 1.73 |
| Ausbruch | combined | 1990 | 36.9 | 51.3 | 2.08 |
| Roter Retest | combined | 367 | 6.8 | 34.9 | 0.38 |
| Safety-Bounce | combined | 1157 | 27.4 | 30.6 | 1.29 |

`distance`: nur Abstand; `active`: zusätzlich aktive Annäherung; `compression`: zusätzlich Verengung; `combined`: beides. Die Gruppenmitgliedschaften unterscheiden sich; bessere Anteile sind kein kausaler Wirkungsnachweis.

## Kontaktklassen getrennt, Abstand 1 ATR

| Familie | Qualität BEI Vorwarnung | Warnungen | Später bestätigt | Verpufft | Unentschieden |
|---|---|---:|---:|---:|---:|
| Ausbruch | qualified | 533 | 255 | 274 | 4 |
| Ausbruch | two | 2285 | 1181 | 1093 | 11 |
| Roter Retest | qualified | 566 | 212 | 347 | 7 |
| Roter Retest | two | 1389 | 442 | 934 | 13 |
| Safety-Bounce | qualified | 1937 | 585 | 1335 | 17 |

| Familie | Später qualifizierte Entries | Davon vorher gewarnt | Davon bei Warnung erst zwei Kontakte |
|---|---:|---:|---:|
| Ausbruch | 812 | 317 | 68 |
| Roter Retest | 622 | 208 | 9 |
| Safety-Bounce | 1294 | 585 | 0 |

Die Qualifikation am späteren Signal darf eine frühere Zweikontakt-Warnung nicht rückwirkend aufwerten.

## Originalwarnlinie und spätere Signallinie

| Familie, 1 ATR | Auf Episodenebene erfasst | Davon identische technische Linie | Andere Linie derselben Herkunft |
|---|---:|---:|---:|
| Ausbruch | 1436 | 1413 | 23 |
| Roter Retest | 654 | 547 | 107 |
| Safety-Bounce | 585 | 546 | 39 |

Die Haupterfassungsquote bezieht sich auf Episode/Familie. Ein verwandter späterer Kandidat desselben Fächers ist nicht automatisch genau die im ersten Warnsnapshot gespeicherte Linie. Diese Fälle sind sichtbar getrennt.

## Berührung, roher Bruch und Bestätigung unterscheiden

| Familie, 1 ATR | Median bis rohe Rot-Kreuzung / Kerzen | Median bis erste Berührung / Kerzen | Vor erster Berührung gewarnte bestätigte Fälle |
|---|---:|---:|---:|
| Ausbruch | 1.0 | – | 0 |
| Roter Retest | – | 1.0 | 470 |
| Safety-Bounce | – | 0.0 | 259 |

Negative Berührungs-Vorlaufwerte bedeuten: Die erste Berührung war schon vor der Warnung bekannt. Eine Warnung vor der späteren Bestätigung ist dann keine Warnung vor dem ersten Kontakt. Ein roter Retest beobachtet die Originalbruchlinie; die grüne Safety bleibt eine eigene Familie.

## Ein bis zwei Sitzungstage vor dem rohen Rot-Bruch

| Policy | Ausbruchs-Entryreferenz | Bei aktivem Watch 1–2 Sitzungstage vor rohem Bruch gewarnt | Anteil aller Ausbruchs-Entries % | Median reale Stunden vor rohem Bruch |
|---|---:|---:|---:|---:|
| distance:1.5 | 2770 | 952 | 34.4 | 24.0 |
| active:1.5 | 2770 | 763 | 27.5 | 21.5 |
| compression:1.5 | 2770 | 865 | 31.2 | 21.5 |
| combined:1.5 | 2770 | 691 | 24.9 | 21.5 |
| distance:1 | 2770 | 953 | 34.4 | 21.5 |
| active:1 | 2770 | 734 | 26.5 | 21.5 |
| compression:1 | 2770 | 875 | 31.6 | 21.5 |
| combined:1 | 2770 | 674 | 24.3 | 21.5 |
| distance:0.5 | 2770 | 818 | 29.5 | 21.5 |
| active:0.5 | 2770 | 593 | 21.4 | 21.5 |
| compression:0.5 | 2770 | 739 | 26.7 | 21.5 |
| combined:0.5 | 2770 | 542 | 19.6 | 21.5 |

Dieser strengere Vorlauf endet bereits bei der ersten beobachteten Rot-Kreuzung der Episode. Die Clean-Close-Entrybestätigung kann später liegen; ihre längere Vorlaufzeit darf nicht als dieselbe Frühwarnzeit ausgegeben werden.

## Spätere Einstiege nach bereits geschlossener Beobachtung

| Familie, Abstand 1 ATR | Entryreferenz | Vorwarnung vorhanden, aber Watch vor Entry schon beendet |
|---|---:|---:|
| Ausbruch | 2770 | 1210 |
| Roter Retest | 1874 | 648 |
| Safety-Bounce | 1294 | 351 |

Hier besteht ein wichtiger Forschungsansatz für begrenzte erneute Freigaben nach einem tatsächlich neuen Aufbau. Ein späterer Entry beweist nicht rückwirkend, dass die ursprüngliche Warngeometrie intakt geblieben war. Diese Fälle sind daher weiterhin nicht als erfolgreiche aktive Vorwarnungen gezählt.

## Gesamte hypothetische Nachrichtenlast

| Policy | Meldungen/Tag, alle Familien | Spitzentag |
|---|---:|---:|
| active:0.5 | 2.90 | 14 |
| active:1 | 4.42 | 21 |
| active:1.5 | 5.09 | 34 |
| combined:0.5 | 2.54 | 13 |
| combined:1 | 3.75 | 17 |
| combined:1.5 | 4.27 | 27 |
| compression:0.5 | 4.11 | 17 |
| compression:1 | 6.40 | 28 |
| compression:1.5 | 7.32 | 26 |
| distance:0.5 | 4.66 | 18 |
| distance:1 | 7.34 | 33 |
| distance:1.5 | 8.37 | 30 |

Zeitgleiche Stufe 2 und 3 derselben Episode/Familie sind ein Briefing. Wiederholte Tagesansichten erzeugen keine weiteren Warnungen. Die genannten Häufigkeiten sind historische Lasten des jeweiligen Universums, kein erzwungenes Tageskontingent.

## Technische Prüfung und Grenzen

Unabhängiger Nachrechner: 106,333 gespeicherte Warnzustände, 69 Aktien und alle 36 aggregierten Gruppen geprüft. ATR wird separat Kerze für Kerze rekonstruiert; Abstände, Zeitgrenzen, Kontaktbekanntheit, SMA-Kontext, Projektionen und Zählungen werden aus den gespeicherten Quellen nachgerechnet.
Quellfenster mit ausreichendem Vorlauf: 2018: 65 Aktien, 2021: 66 Aktien, 2023: 67 Aktien, 2025-2026: 68 Aktien.
Zusätzlich synthetische Zukunftsschocks, Episodenwechsel, Datenlücken, Snapshotgrenzen, manuelle Stummschaltung und Wiederaufnahme geprüft.
Die Originalgeometrie wird je Warnstufe gespeichert. Eine Rückprojektion derselben aktuell bekannten Linie über vergangene Kurse ist eine aktuelle Merkmalsmessung, kein damals bereits bekanntes Signal; `lineKnownAtComparison` kennzeichnet die Unterscheidung.
Die ATR-Projektion ist ein Szenario mit unveränderter Linie und heutigem ATR. Der tatsächliche Entry kommt ausschließlich aus dem gemeinsamen Entry-Modul; insbesondere erzeugt der projizierte Offset keinen Safety-Bounce-Trigger.

Dieses bekannte Überlebendenuniversum und diese bereits ausgewerteten Zeitfenster sind keine unabhängige Strategiebestätigung. Es wird weder Rentabilität noch eine verlässliche Vorhersage eines Ausbruchs in ein bis zwei Tagen behauptet.

Werkzeugvertrag und nächste Schritte: [EARLY-WARNING.md](EARLY-WARNING.md). Private Pläne, Kursdaten, Snapshots, Blöcke, Reviews und Rohmessungen unter dem Studienordner bleiben außerhalb von Git.
