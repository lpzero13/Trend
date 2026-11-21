# Historische Vorwarnstudie – 01.11.2026

512 vorhandene echte SIP/split-Aktien, 1004 XNYS-Handelstage in vier bereits bekannten Forschungsfenstern.
Fenster: 2018, 2021, 2023, 2025-2026.
Keine Providerabrufe, Orders, P/L-Studie, neue Holdout-Auswahl oder laufenden Nachrichten.

Die gemeinsame kausale Master-/Pilot-Entrylogik läuft erneut über die Quellen. Vorwarn-Episoden entstehen bereits bei Kandidatenerkennung; diese neue Gruppierung ist nicht die alte 1.790er-Fallauswahl. Die Entryzahlen sind je Familie/Policy episodenweise deduplizierte Bestätigungen mit gültiger Anfangsabsicherung, keine behaupteten Fills.
Je Policy dieselbe Referenzmenge. Verschiedene Policies teilen Fälle und dürfen nicht als unabhängige Stichprobe addiert werden. Ohne ausreichenden Vorlauf wird das jeweilige Aktienfenster ausgeschlossen.

## Abstandswarnungen

| Familie | ATR-Schwelle | Entries | Vorwarnungen | Entries vorher erfasst % | Davon 1–2 Sitzungstage vor Entry: Anteil aller Entries % | Median Vorlauf / Kerzen | Verpufft unter aufgelösten Warnungen % | Unentschieden | Meldungen/Tag | Spitze/Tag |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ausbruch | 1.5 | 15725 | 16892 | 48.8 | 35.3 | 2.0 | 54.0 | 200 | 18.51 | 65 |
| Roter Retest | 1.5 | 10781 | 12994 | 35.0 | 32.2 | 2.0 | 70.5 | 218 | 14.53 | 71 |
| Safety-Bounce | 1.5 | 7265 | 12882 | 49.9 | 35.0 | 2.0 | 71.3 | 250 | 15.59 | 57 |
| Ausbruch | 1 | 15725 | 16299 | 49.7 | 36.0 | 2.0 | 51.5 | 184 | 17.37 | 65 |
| Roter Retest | 1 | 10781 | 11650 | 37.0 | 32.6 | 2.0 | 65.2 | 182 | 12.60 | 53 |
| Safety-Bounce | 1 | 7265 | 11026 | 47.7 | 29.9 | 1.0 | 68.1 | 180 | 12.59 | 55 |
| Ausbruch | 0.5 | 15725 | 13402 | 45.0 | 31.6 | 1.0 | 46.7 | 115 | 13.35 | 53 |
| Roter Retest | 0.5 | 10781 | 7794 | 33.0 | 25.4 | 1.0 | 53.7 | 103 | 7.76 | 40 |
| Safety-Bounce | 0.5 | 7265 | 6181 | 24.0 | 11.3 | 1.0 | 71.4 | 82 | 6.16 | 27 |

Vorlaufmedian nur unter tatsächlich vorher gewarnten Entries. 1–2 Sitzungstage bezeichnet den Abstand der Börsen-Sitzungsdaten, keine vollen 24–48 Stunden; Kerzen werden separat gemessen. Eine Warnung auf der Entrykerze zählt nicht als rechtzeitig.
Verpufft bedeutet: Beobachtung wurde vor einem passenden gültigen Signal aufgelöst. Ein Kursverlust oder tatsächlicher Stop-Fill ist damit nicht nachgewiesen. Spätere Signale nach bereits geschlossener Beobachtung werden nicht als erfolgreiche Vorwarnung gutgeschrieben.

## Zusätzliche Merkmale als Pflichtbedingungen, jeweils 1 ATR

| Familie | Variante | Vorwarnungen | Erfasste Entries % | Bestätigung unter allen Warnungen % | Meldungen/Tag |
|---|---|---:|---:|---:|---:|
| Ausbruch | distance | 16299 | 49.7 | 47.9 | 17.37 |
| Roter Retest | distance | 11650 | 37.0 | 34.3 | 12.60 |
| Safety-Bounce | distance | 11026 | 47.7 | 31.4 | 12.59 |
| Ausbruch | active | 12604 | 38.8 | 48.4 | 13.25 |
| Roter Retest | active | 2767 | 7.7 | 30.0 | 2.88 |
| Safety-Bounce | active | 8281 | 36.3 | 31.9 | 9.34 |
| Ausbruch | compression | 15117 | 45.3 | 47.1 | 16.01 |
| Roter Retest | compression | 10516 | 35.9 | 36.8 | 11.34 |
| Safety-Bounce | compression | 8615 | 37.5 | 31.6 | 9.79 |
| Ausbruch | combined | 11747 | 35.8 | 47.9 | 12.30 |
| Roter Retest | combined | 2114 | 6.5 | 33.1 | 2.20 |
| Safety-Bounce | combined | 6467 | 28.5 | 32.0 | 7.26 |

`distance`: nur Abstand; `active`: zusätzlich aktive Annäherung; `compression`: zusätzlich Verengung; `combined`: beides. Die Gruppenmitgliedschaften unterscheiden sich; bessere Anteile sind kein kausaler Wirkungsnachweis.

## Kontaktklassen getrennt, Abstand 1 ATR

| Familie | Qualität BEI Vorwarnung | Warnungen | Später bestätigt | Verpufft | Unentschieden |
|---|---|---:|---:|---:|---:|
| Ausbruch | qualified | 3052 | 1390 | 1628 | 34 |
| Ausbruch | three_young | 4 | 3 | 1 | 0 |
| Ausbruch | two | 13243 | 6417 | 6676 | 150 |
| Roter Retest | qualified | 3523 | 1333 | 2142 | 48 |
| Roter Retest | three_young | 3 | 1 | 2 | 0 |
| Roter Retest | two | 8124 | 2659 | 5331 | 134 |
| Safety-Bounce | qualified | 11026 | 3462 | 7384 | 180 |

| Familie | Später qualifizierte Entries | Davon vorher gewarnt | Davon bei Warnung erst zwei Kontakte |
|---|---:|---:|---:|
| Ausbruch | 4831 | 1774 | 410 |
| Roter Retest | 3650 | 1303 | 46 |
| Safety-Bounce | 7265 | 3462 | 0 |

Die Qualifikation am späteren Signal darf eine frühere Zweikontakt-Warnung nicht rückwirkend aufwerten.

## Originalwarnlinie und spätere Signallinie

| Familie, 1 ATR | Auf Episodenebene erfasst | Davon identische technische Linie | Andere Linie derselben Herkunft |
|---|---:|---:|---:|
| Ausbruch | 7810 | 7699 | 111 |
| Roter Retest | 3993 | 3436 | 557 |
| Safety-Bounce | 3462 | 3257 | 205 |

Die Haupterfassungsquote bezieht sich auf Episode/Familie. Ein verwandter späterer Kandidat desselben Fächers ist nicht automatisch genau die im ersten Warnsnapshot gespeicherte Linie. Diese Fälle sind sichtbar getrennt.

## Berührung, roher Bruch und Bestätigung unterscheiden

| Familie, 1 ATR | Median bis rohe Rot-Kreuzung / Kerzen | Median bis erste Berührung / Kerzen | Vor erster Berührung gewarnte bestätigte Fälle |
|---|---:|---:|---:|
| Ausbruch | 1.0 | – | 0 |
| Roter Retest | – | 1.0 | 2739 |
| Safety-Bounce | – | 0.0 | 1460 |

Negative Berührungs-Vorlaufwerte bedeuten: Die erste Berührung war schon vor der Warnung bekannt. Eine Warnung vor der späteren Bestätigung ist dann keine Warnung vor dem ersten Kontakt. Ein roter Retest beobachtet die Originalbruchlinie; die grüne Safety bleibt eine eigene Familie.

## Ein bis zwei Sitzungstage vor dem rohen Rot-Bruch

| Policy | Ausbruchs-Entryreferenz | Bei aktivem Watch 1–2 Sitzungstage vor rohem Bruch gewarnt | Anteil aller Ausbruchs-Entries % | Median reale Stunden vor rohem Bruch |
|---|---:|---:|---:|---:|
| distance:1.5 | 15725 | 5131 | 32.6 | 24.0 |
| active:1.5 | 15725 | 4148 | 26.4 | 21.5 |
| compression:1.5 | 15725 | 4727 | 30.1 | 24.0 |
| combined:1.5 | 15725 | 3832 | 24.4 | 21.5 |
| distance:1 | 15725 | 5202 | 33.1 | 21.5 |
| active:1 | 15725 | 4050 | 25.8 | 21.5 |
| compression:1 | 15725 | 4770 | 30.3 | 21.5 |
| combined:1 | 15725 | 3742 | 23.8 | 21.5 |
| distance:0.5 | 15725 | 4469 | 28.4 | 21.5 |
| active:0.5 | 15725 | 3378 | 21.5 | 21.5 |
| compression:0.5 | 15725 | 4078 | 25.9 | 21.5 |
| combined:0.5 | 15725 | 3116 | 19.8 | 21.5 |

Dieser strengere Vorlauf endet bereits bei der ersten beobachteten Rot-Kreuzung der Episode. Die Clean-Close-Entrybestätigung kann später liegen; ihre längere Vorlaufzeit darf nicht als dieselbe Frühwarnzeit ausgegeben werden.

## Spätere Einstiege nach bereits geschlossener Beobachtung

| Familie, Abstand 1 ATR | Entryreferenz | Vorwarnung vorhanden, aber Watch vor Entry schon beendet |
|---|---:|---:|
| Ausbruch | 15725 | 6999 |
| Roter Retest | 10781 | 3629 |
| Safety-Bounce | 7265 | 1855 |

Hier besteht ein wichtiger Forschungsansatz für begrenzte erneute Freigaben nach einem tatsächlich neuen Aufbau. Ein späterer Entry beweist nicht rückwirkend, dass die ursprüngliche Warngeometrie intakt geblieben war. Diese Fälle sind daher weiterhin nicht als erfolgreiche aktive Vorwarnungen gezählt.

## Gesamte hypothetische Nachrichtenlast

| Policy | Meldungen/Tag, alle Familien | Spitzentag |
|---|---:|---:|
| active:0.5 | 16.90 | 51 |
| active:1 | 25.47 | 86 |
| active:1.5 | 29.22 | 134 |
| combined:0.5 | 14.82 | 49 |
| combined:1 | 21.76 | 74 |
| combined:1.5 | 24.72 | 111 |
| compression:0.5 | 24.04 | 74 |
| compression:1 | 37.13 | 120 |
| compression:1.5 | 42.60 | 137 |
| distance:0.5 | 27.27 | 77 |
| distance:1 | 42.57 | 125 |
| distance:1.5 | 48.64 | 144 |

Zeitgleiche Stufe 2 und 3 derselben Episode/Familie sind ein Briefing. Wiederholte Tagesansichten erzeugen keine weiteren Warnungen. Die genannten Häufigkeiten sind historische Lasten des jeweiligen Universums, kein erzwungenes Tageskontingent.

## Technische Prüfung und Grenzen

Unabhängiger Nachrechner: 620,552 gespeicherte Warnzustände, 512 Aktien und alle 36 aggregierten Gruppen geprüft. ATR wird separat Kerze für Kerze rekonstruiert; Abstände, Zeitgrenzen, Kontaktbekanntheit, SMA-Kontext, Projektionen und Zählungen werden aus den gespeicherten Quellen nachgerechnet.
Quellfenster mit ausreichendem Vorlauf: 2018: 472 Aktien, 2021: 489 Aktien, 2023: 504 Aktien, 2025-2026: 512 Aktien.
Zusätzlich synthetische Zukunftsschocks, Episodenwechsel, Datenlücken, Snapshotgrenzen, manuelle Stummschaltung und Wiederaufnahme geprüft.
Die Originalgeometrie wird je Warnstufe gespeichert. Eine Rückprojektion derselben aktuell bekannten Linie über vergangene Kurse ist eine aktuelle Merkmalsmessung, kein damals bereits bekanntes Signal; `lineKnownAtComparison` kennzeichnet die Unterscheidung.
Die ATR-Projektion ist ein Szenario mit unveränderter Linie und heutigem ATR. Der tatsächliche Entry kommt ausschließlich aus dem gemeinsamen Entry-Modul; insbesondere erzeugt der projizierte Offset keinen Safety-Bounce-Trigger.

Dieses bekannte Überlebendenuniversum und diese bereits ausgewerteten Zeitfenster sind keine unabhängige Strategiebestätigung. Es wird weder Rentabilität noch eine verlässliche Vorhersage eines Ausbruchs in ein bis zwei Tagen behauptet.

Werkzeugvertrag und nächste Schritte: [EARLY-WARNING.md](EARLY-WARNING.md). Private Pläne, Kursdaten, Snapshots, Blöcke, Reviews und Rohmessungen unter dem Studienordner bleiben außerhalb von Git.
