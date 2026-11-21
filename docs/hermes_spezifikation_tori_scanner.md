# Technische Spezifikation & Fachliches Pflichtenheft: Umbau des Tori-Kandidaten-Scanners (`tori_candidate_preview.py`)

**Zielsystem:** Hermes-Agent / Screening-Pipeline auf `CT118` (`/var/lib/tori/operations/preview/tori_candidate_preview.py`)  
**Ausgabeziele:** `~/.hermes/reports/trend-kandidaten-YYYY-MM-DD.md`, `.csv` sowie `/var/lib/tori/operations/preview/full/ranked-candidates.json`  
**Wissenschaftliche Grundlage:** Empirische Ergebnisse aus 4 abgeschlossenen Großstudien auf 69 bzw. 512 US-Aktien (`dow30`, `nasdaq100`, `sp500`) mit 39.440 untersuchten Signalfällen und 620.552 geprüften Vorwarnzuständen.

---

## 1. Ausgangslage: Warum der aktuelle Suchlauf (142 aus 520 Titeln) umgebaut werden muss

Der bisherige Suchlauf vom 13.11.2026 funktioniert technisch und infrastrukturell einwandfrei (kausale Berechnung auf abgeschlossenen Kerzen, `lag = 0`, keine Netzwerkzugriffe, saubere Daten-Gates). Er liefert jedoch **142 Kandidaten aus 520 geprüften Aktien**, weil der Vorfilter zu breit gefasst ist und die anschließende Stufenbildung (Stufen A bis E) sowie die 0–10-Gewichtung den empirischen Befunden unserer Backtest-Studien widersprechen.

### Die 5 konkreten Fehlsteuerungen im aktuellen Skript:

1. **Fehler in Stufe B (Unreife rote 2-Kontakt-Linien schlüpfen durch):**
   * Im Lauf vom 13.11.2026 besaßen von allen 142 Kandidaten überhaupt nur **27 Titel eine qualifizierte rote Widerstandslinie** ($\ge 3$ Kontakte und $\ge 7$ Tage Alter), aber **63 Titel eine qualifizierte grüne Linie**.
   * Weil Stufe B bisher nur verlangt: *„mindestens EINE Linie mit 3+ Kontakten“*, gelangen zahlreiche Aktien in die B-Auswahl, die zwar unten eine alte grüne Linie mit 3 Kontakten haben, oben aber nur eine junge, strukturell dünne **rote 2-Kontakt-Linie (`breakout:two`)**.
   * **Beleg aus dem 512-Aktien-Backtest:** Ausbrüche über rote 2-Kontakt-Linien (`breakout:two`, 10.957 Fälle) haben unter aktueller Safety einen Erwartungswert von $-0{,}03\%$ (Median $-1{,}04\%$). Für einen Ausbruch nach oben ist zwingend die **rote Widerstandslinie der Signalgeber** – sie muss qualifiziert sein ($\ge 3$ Kontakte).
2. **Fehler in Stufe A (Die `both_qualified`-Falle):**
   * Stufe A verlangt aktuell: *„3+ Kontakte auf BEIDEN Linien“* (nur 5 bzw. 9 Titel im gesamten Universum).
   * **Beleg aus der Filterstudie (`SIGNALFILTER-ERGEBNISSE-20261031.md`):** Das Profil `both_qualified` (Rote Linie $\ge 3$ Kontakte UND Grüne Safety beim Einstieg bereits $\ge 3$ Kontakte) führte bei Ausbrüchen wie auch bei Retests zu einem **Totalabsturz in den negativen Bereich unter allen vier Stop-Modellen** ($-0{,}69\%$ bei `original_safety`, $-0{,}09\%$ bei `fan_safety`, $-0{,}37\%$ bei Retests).
   * **Marktmechanischer Grund:** Wenn eine Aktie nach einer Abwärtskorrektur ein frisches Konsolidierungs-Dreieck aufbaut, hat das rote Widerstandsdach zwar $\ge 3$ Berührungspunkte, aber der junge steigende Boden (grüne Safety Line) besitzt vor dem Ausbruch naturgemäß erst **2 bestätigte Ankerpunkte** (das Korrekturtief und das erste höhere Zwischentief). Wer zwingend $\ge 3$ Kontakte auf Grün verlangt, filtert die besten frischen Setups aus und behält nur späte, überreife Formationen übrig.
3. **Fehlender Stop-Loss-Abstandsfilter (Keine Prüfung des `risk`-Korridors):**
   * Aktuell wird der Abstand zur grünen Safety Line zwar berechnet, aber **nicht** als Filterkriterium genutzt.
   * **Beleg aus den Studien:**
     * Liegt die grüne Safety Line zu nah am Kurs ($< 1{,}0 \times \text{ATR}_{4\text{h}}$ bzw. $< 2{,}0\%$), landet der Stop-Loss mitten im normalen Kerzenrauschen (hohe Ausstopp-Quote). Das Profil `risk` (Abstand zum Anfangsstop $\ge 1{,}0 \times \text{ATR}_{4\text{h}}$ und $\ge 2{,}0\%$) war in der Filterstudie der einzige Einzelfilter, der sowohl die Trefferquote (auf $42{,}20\%$ bei Ausbrüchen und $40{,}48\%$ bei Retests) als auch den Netto-Erwartungswert über alle Stop-Modelle hinweg signifikant gesteigert hat.
     * Liegt die grüne Safety Line dagegen extrem weit weg ($> 8{,}0\%$ bis $10{,}0\%$, wie beim Negativ-Rekord `TSLA` im 512er-Backtest mit $42{,}43\%$ Stop-Abstand und $-35{,}60\%$ Verlust), ist das Risiko für einen direkten Ausbruch viel zu groß.
4. **Blinder Fleck für aktive Signale (`grün < close < rot` wirft Ausbrüche und Retests raus):**
   * Durch die harte Bedingung $\text{grün} < \text{close} < \text{rot}$ sucht das Skript ausschließlich Aktien, die noch *zwischen* den Linien eingesperrt sind.
   * Sobald eine Aktie in der Zielsitzung den tatsächlichen Ausbruch über die rote Linie schafft ($\text{close} > \text{rot}$) oder von oben einen **roten Retest** auf die gebrochene rote Linie vollzieht ($\text{close} > \text{rot}$ mit geringem Abstand nach unten), fällt sie sofort aus der Liste heraus!
5. **Zu junge Korrekturen (82 von 142 roten Linien sind $< 14$ Tage alt):**
   * Eine rote Linie von nur 7 Tagen Dauer ist im 4H-Chart lediglich eine kurze Wochen-Flagge. Ohne ein erhöhtes Mindestalter (bzw. Mindest-Kontaktspanne) für die rote Action Line wird die Liste mit kurzlebigen Mini-Korrekturen geflutet.

---

## 2. Unveränderte technische Basis & Daten-Gates (Schritte 1 & 2 beibehalten)

Die bestehende Infrastruktur auf `CT118` sowie die kausalen Daten-Gates bleiben als Fundament vollständig erhalten:

### 2.1 Daten-Gates (Ausschluss vor der Geometrie-Prüfung)
Ein Symbol aus der Vereinigungsmenge der 520 Aktien (`dow30`, `nasdaq100`, `sp500`) wird nur ausgewertet, wenn:
1. ein lokaler, split-adjustierter SIP-Datensatz (5m-Basis, reguläre XNYS-Sitzung) vorliegt (`no_local_history` entfällt),
2. das Kursupdate fehlerfrei lief (`error` entfällt),
3. in der Zielsitzung **weniger als 10 fehlende 5-Minuten-Kerzen** vorliegen ($\ge 10$ fehlende Kerzen $\rightarrow$ Status `data_problem`),
4. im 4H-Datensatz mindestens eine Kerze vorhanden ist, die nach Handelsbeginn der Zielsitzung schließt (sonst `missing_session_4h`),
5. der geometrische Vorlauf ausreicht (mindestens 320 Tage Vorlauf für den grünen Fächer und 150 Tage für den roten Fächer; sonst `analysis_unavailable`).

*Wichtig für den Report:* Die durch Daten-Gates ausgeschlossenen Symbole (zuletzt 35 Titel) werden nicht im Hauptbericht aufgelistet, sondern am Ende des Markdown-Reports in einer **einzeiligen Technik-Fußnote** zusammengefasst (inkl. expliziter Nennung der Symbole mit `data_problem` oder `missing_session_4h`, damit eventuelle Sammler-Probleme sofort auffallen).

### 2.2 Engine-Parameter (`fan_master`, Profil `master`)
Die Parameter der Master-Fächer-Engine bleiben unangetastet, um die 100-%-Kompatibilität mit den Backtests zu wahren:
* `pivot_side = 2` (Pivot-Bestätigung nach 2 Kerzen rechts/links)
* `atr_length = 14` (auf 4H-Basis: $\text{ATR}_{4\text{h}}$)
* `contact_atr = 0.45` (Schaumstoffmatte: Pivot zählt als Kontakt, wenn Abstand zur Linie $\le 0{,}45 \times \text{ATR}_{4\text{h}}$)
* `contact_gap = 5` (Spaced-Out-Regel: mindestens 5 Kerzen Abstand zwischen zwei gezählten Kontakten)
* `wick_atr = 0.15` (maximale Docht-Überschreitung), `body_atr = 0.05` (maximale Kerzenkörper-Toleranz der Engine)
* `min_age_days = 7` (Basis-Qualifikation in der Engine)
* `lookback_days = 320` (Grün / Safety), `action_lookback_days = 150` (Rot / Widerstand), `max_bars = 1800`, `levels = 4`
* `lag = 0` (streng kausale Auswertung zum Ende der Zielsitzung)

---

## 3. Die 6 harten Pflicht-Kriterien (Mandatory Gates für jedes Tori-Setup)

Damit aus den 520 Aktien am Ende nur die **10 bis 25 wirklich handlungsrelevanten Top-Kandidaten** übrig bleiben, muss ein Setup im neuen Vorfilter zwingend alle folgenden **6 Pflicht-Tore** passieren. Verfehlt eine Aktie eines dieser Tore, wird sie verworfen (und nicht mehr als Stufe C, D oder E mitgeschleppt).

### Tor 1: Rote Action Line MUSS qualifiziert und gereift sein (`A+`-Widerstand)
* **Kontaktzahl:** Die operativ ausgewählte rote Widerstandslinie muss **mindestens 3 bestätigte, zeitlich getrennte Kontakte** ($\text{contacts}_{\text{rot}} \ge 3$ mit `contact_gap >= 5`) aufweisen. Linien mit nur 2 Kontakten werden im Haupt-Screening verworfen (Ausnahme: nur das separate Beobachtungs-Szenario `SCENARIO_5_FAST_A_PLUS`, siehe Abschnitt 4).
* **Steigung:** Die rote Linie muss fallen ($\text{slope}_{\text{rot}} < 0$).
* **Reifegrad (Alter & Kontaktspanne):**
  * Das Linienalter seit dem Startanker (`age_days_red`) muss **mindestens 10 Kalendertage** betragen ($\text{age\_days\_red} \ge 10{,}0$).
  * Zwischen dem ersten und dem letzten bestätigten Kontaktpunkt der roten Linie müssen mindestens **7 Kalendertage** liegen ($\text{contact\_span\_days\_red} \ge 7{,}0$). Damit werden die 82 kurzlebigen Mini-Korrekturen aus dem alten Lauf sauber herausgefiltert.

### Tor 2: Grüne Safety Line (Unterstützung) mit $\ge 2$ Kontakten
* **Vorhandensein & Lage:** Es muss eine gültige grüne Safety Line unterhalb des aktuellen 4H-Schlusskurses existieren ($\text{grün}_t < \text{close}_t$).
* **Kontaktzahl:** Es genügen **mindestens 2 bestätigte Kontakte** ($\text{contacts}_{\text{grün}} \ge 2$). Es darf **kein** Zwang zu 3+ Kontakten auf Grün bestehen (`both_qualified`-Verbot als Sperrfilter!).
* **Steigung:** Die grüne Safety Line muss steigen ($\text{slope}_{\text{grün}} > 0$). Horizontale Unterstützungen ($\text{slope}_{\text{grün}} = 0$) sind nur zulässig, wenn sie mindestens 3 bestätigte Kontakte über $\ge 14$ Tage besitzen.

### Tor 3: Geometrie-Disziplin (Umgang mit Körperverletzung & Fächerkette)
Die bisherigen 75 „Stufe-D“-Kandidaten werden nicht mehr in den Report gedruckt, sondern durch eine präzise geometrische Prüfung am Eingangstor aufgelöst:
* **Kerzenkörper-Prüfung (mit korrekter Engine-Toleranz):**
  Die Engine erlaubt über `body_atr = 0.05` minimale Berührungen. Das Audit-Skript darf eine Linie **nicht** schon bei einer Überschreitung von $10^{-8}$ als „Körperbruch“ verwerfen, sondern muss exakt die Engine-Toleranz prüfen:
  * Ein echter, unzulässiger Körperbruch vor dem Ausbruchsfenster liegt nur vor, wenn für eine Kerze $k$ zwischen Startanker `Point A` und den letzten 2 Kerzen gilt:
    $$\max(\text{Open}_k, \text{Close}_k) > \text{Rot}_k + 0{,}05 \times \text{ATR}_{4\text{h}, k}$$
    bzw. auf der Unterseite bis zur aktuellen Kerze:
    $$\min(\text{Open}_k, \text{Close}_k) < \text{Grün}_k - 0{,}05 \times \text{ATR}_{4\text{h}, k}$$
  * Linien mit echtem Körperbruch ausserhalb dieser $0{,}05 \times \text{ATR}$-Toleranz werden hart ausgeschlossen.
* **Fächerketten-Prüfung ($A_{\text{neu}} = B_{\text{alt}}$) & `refit`-Status:**
  * Wenn eine Linie der Stufe $L > 1$ als `origin == "pivot"` geführt wird, ihr Startpunkt $A_L$ aber nicht mit dem letzten Kontaktpunkt $B_{L-1}$ der übergeordneten Fächerlinie übereinstimmt, wird dies als Warn-Flag (`fan_chain_warning = True`) vermerkt.
  * Linien vom Typ `origin == "refit"` (Steigung wurde an die Hüllkurven-Grenze angepasst) bleiben zugelassen, da sie in der Master-Engine zum kausalen Standard gehören (53 von 142 Fällen), erhalten im Scoring aber 1 Punkt weniger als reine `pivot`-Linien.

### Tor 4: Dreiecks-Konvergenz (Echte Einkeilung)
* Die rote Linie fällt ($\text{slope}_{\text{rot}} < 0$), die grüne Linie steigt ($\text{slope}_{\text{grün}} > 0$).
* Die vertikale Öffnungsweite des Dreiecks am aktuellen Balken ($\text{width}_t = \text{Rot}_t - \text{Grün}_t$) muss positiv sein ($\text{width}_t > 0$) und sich gegenüber dem gemeinsamen Startzeitpunkt verengt haben.

### Tor 5: Der Stop-Loss- & Risiko-Korridor (`risk`-Gate + Obergrenze)
Für jeden Kandidaten berechnet das Skript sofort den realen, gepufferten Hard-Stop-Preis ($\text{Stop}_0$) nach unserer verbindlichen Ausführungsregel ($0{,}3\%$ Puffer unter der grünen Safety Line, auf volle Cent nach unten abgerundet):
$$\text{Stop}_0 = \frac{\lfloor \text{Grün}_t \times (1 - 0{,}003) \times 100 \rfloor}{100}$$
Daraus ergeben sich der prozentuale Stop-Abstand ($\text{Risk}_{\%}$) und der Stop-Abstand in $\text{ATR}_{4\text{h}}$-Einheiten ($\text{Risk}_{\text{ATR}}$), gemessen vom aktuellen Schlusskurs $\text{Close}_t$ (bzw. bei Vorwarnungen zusätzlich projiziert vom Ausbruchspunkt $\text{Rot}_t$):
$$\text{Risk}_{\%} = \frac{\text{Close}_t - \text{Stop}_0}{\text{Close}_t} \times 100 \quad \text{und} \quad \text{Risk}_{\text{ATR}} = \frac{\text{Close}_t - \text{Stop}_0}{\text{ATR}_{4\text{h}}}$$

Es gelten folgende verbindliche Korridor-Grenzen:
1. **Untergrenze (Schutz vor der Stop-Todeszone):**
   $$\text{Risk}_{\text{ATR}} \ge 1{,}0 \quad \text{UND} \quad \text{Risk}_{\%} \ge 1{,}8\% \text{ (am Ausbruchspunkt } \ge 2{,}0\%\text{)}$$
   *(Ausnahme: Liegt ein Dreieck extrem eng in der äußersten Spitze mit $\text{Risk}_{\text{ATR}} < 0{,}6$, darf es nur mit dem expliziten Warnhinweis `APEX_TIGHT_STOP` und einem künstlichen `Min-Risk-Floor` von $1{,}0 \times \text{ATR}_{4\text{h}}$ für die Stückzahlberechnung geführt werden).*
2. **Obergrenze für direkte Ausbrüche (Schutz vor überdehnten Verlusten wie `TSLA` $-35{,}6\%$):**
   * Für alle direkten Ausbruchs- und Vorwarn-Szenarien (Szenario 1 und 2) darf der Stop-Abstand am erwarteten Ausbruchspunkt **maximal $8{,}5\%$** (bzw. **maximal $3{,}8 \times \text{ATR}_{4\text{h}}$**) betragen:
     $$\text{Risk}_{\%,\text{Breakout}} \le 8{,}5\% \quad \text{UND} \quad \text{Risk}_{\text{ATR},\text{Breakout}} \le 3{,}8$$
   * **Was passiert, wenn $\text{Risk}_{\%,\text{Breakout}} > 8{,}5\%$ ist?** Dann ist der Weg bis zur grünen Safety Line für einen direkten Ausbruchskauf zu weit! Das Skript verwirft die Aktie für den direkten Ausbruch und verschiebt sie mit dem Vermerk `WAIT_FOR_RETEST_ONLY` in die Retest-Überwachung (Szenario 3).

### Tor 6: Praktische Handelbarkeit (Trade Republic / ING) & Volatilität
Damit keine illiquiden oder „toten“ Aktien die Liste verstopfen, prüft das Skript aus den vorhandenen Tages-/5m-Daten:
1. **Mindestpreis:** $\text{Close}_t \ge 20{,}00\text{ USD}$ (sichert präzise Cent-Rundung beim $0{,}3\%$-Puffer).
2. **Mindest-Liquidität:** Durchschnittliches tägliches Handelsvolumen der letzten 20 Sitzungen $\ge 1.000.000\text{ Aktien}$ **oder** durchschnittliches tägliches Dollar-Volumen $\ge 40\text{ Mio. USD}$.
3. **Mindest-Schwungkraft (Tages-Volatilität):** Die durchschnittliche tägliche Handelsspanne ($\text{ATR}_{14,\text{1D}} / \text{Close}_t$) sollte mindestens **$1{,}8\%$** betragen (Werte $< 1{,}5\%$ erhalten im Score einen Abzug, da langsame Defensivwerte im S&P 500 im Backtest kaum Ausreißer lieferten).

---

## 4. Die 5 operativen Einstiegs-Szenarien (Zustands-Filterung statt bloßer Lage)

Das bisherige Skript prüfte nur statisch, ob $\text{grün} < \text{close} < \text{rot}$ und $(\text{rot} - \text{close})/\text{ATR} \le 1{,}0$ gilt. Ab sofort ordnet `tori_candidate_preview.py` jede Aktie, die die Pflicht-Tore passiert, in **genau eines von fünf klar definierten Handlungs-Szenarien** ein.

Dadurch kannst du im Report (und per CLI-Filter `--scenario`) gezielt nach dem aktuellen Reifegrad des Einstiegs filtern!

---

### Szenario 1: `BREAKOUT_ACTIVE` (Der Durchbruch durch Rot ist in der Zielsitzung passiert!)
Hier liegt der Schlusskurs bereits **über** der qualifizierten roten Widerstandslinie ($\text{Close}_t > \text{Rot}_t$), nachdem der Kurs innerhalb der letzten 1 bis 2 abgeschlossenen 4H-Kerzen noch unterhalb der Linie lag ($\text{Close}_{t-1} \le \text{Rot}_{t-1}$ oder $\text{Close}_{t-2} \le \text{Rot}_{t-2}$). Wir unterscheiden zwei Unterzustände:

* **Sub-Status `1A_CLEAN_BREAKOUT` (Sofortiges Kaufsignal nach Tori-Regel):**
  * Die 4H-Kerze hat die rote Linie inklusive unseres Ausbruchs-Puffers von $+0{,}15 \times \text{ATR}_{4\text{h}}$ sauber per Schlusskurs überwunden:
    $$\text{Close}_t \ge \text{Rot}_t + 0{,}15 \times \text{ATR}_{4\text{h}}$$
  * Gleichzeitig ist der Kurs noch nicht davongelaufen (nicht mehr als $+1{,}2 \times \text{ATR}_{4\text{h}}$ über $\text{Rot}_t$) und der Stop-Abstand zu Grün liegt im erlaubten Korridor ($2{,}0\% \le \text{Risk}_{\%} \le 8{,}5\%$).
  * **Handlungsanweisung im Report:** *„Bestätigter Clean Breakout! Sofortige Sichtprüfung für Einstieg zur heutigen US-Eröffnung (15:30 Uhr MEZ).“*
* **Sub-Status `1B_ARMED_WAIT_CLEAN` („Wait for Cleaner Close“ – Vorgemerkter Bruch):**
  * Die 4H-Kerze hat zwar über der roten Linie geschlossen, aber den Sicherheitspuffer von $+0{,}15 \times \text{ATR}_{4\text{h}}$ noch **nicht** geschafft:
    $$\text{Rot}_t < \text{Close}_t < \text{Rot}_t + 0{,}15 \times \text{ATR}_{4\text{h}}$$
  * **Handlungsanweisung im Report:** *„Knapper Schluss über Rot (Armed). Noch kein Blindkauf – Einstieg erst, wenn die nächste 4H-Kerze über $\text{CleanTrigger}_{t+1}$ schließt!“*

---

### Szenario 2: `PRE_BREAKOUT_IMMEDIATE` (Stufe 3: Akuter Ausbruchs-Druck / Test läuft)
Die Aktie notiert per Schlusskurs noch unterhalb der qualifizierten roten Linie ($\text{Grün}_t < \text{Close}_t \le \text{Rot}_t$), klopft aber bereits unmittelbar am „Stahldach“ an:

* **Bedingung:**
  $$\text{Dist}_{\text{ATR}} = \frac{\text{Rot}_t - \text{Close}_t}{\text{ATR}_{4\text{h}}} \le 0{,}40$$
  **ODER** das Kerzenhoch der letzten abgeschlossenen 4H-Kerze hat die rote Linie bereits bis auf Docht-Toleranz getestet bzw. durchstochen ($\text{High}_t \ge \text{Rot}_t - 0{,}15 \times \text{ATR}_{4\text{h}}$), ohne darüber zu schließen.
* **Handlungsanweisung im Report:** *„Unmittelbar vor dem Ausbruch ($\le 0{,}40 \text{ ATR}$). Preisalarm auf $\text{CleanTrigger}_{t+1}$ für die heutige Sitzung scharfschalten!“*

---

### Szenario 3: `PRE_BREAKOUT_APPROACH` (Stufe 2: Vorwarnung 1–2 Handelstage vor Ausbruch)
Die Aktie befindet sich im Vorfeld des möglichen Ausbruchs (unser klassisches 24h–48h-Vorwarnfenster aus `early_warning.Radar`):

* **Bedingung:**
  * Schlusskurs liegt zwischen den Linien ($\text{Grün}_t < \text{Close}_t < \text{Rot}_t$).
  * Der Abstand zur qualifizierten roten Linie liegt im Korridor:
    $$0{,}40 < \frac{\text{Rot}_t - \text{Close}_t}{\text{ATR}_{4\text{h}}} \le 0{,}85$$
  * **Zusatz-Anforderung für diesen weiteren Korb (damit keine toten Seitwärtsläufer gemeldet werden):** Da bei $0{,}40$ bis $0{,}85 \text{ ATR}$ noch etwas Wegstrecke bis zur roten Linie liegt, muss in diesem Korb **mindestens eines** der beiden Dynamik-Merkmale erfüllt sein:
    1. **Aktive Kursannäherung (`active_approach == True`):** Über die letzten 3 abgeschlossenen 4H-Kerzen ist der Kurs aktiv gestiegen ($\text{Close}_t > \text{Close}_{t-3}$) und der Abstand zur selben roten Linie ist überwiegend durch den Kursanstieg (nicht nur durch das Herabsinken der schrägen Linie) geschrumpft.
    2. **Starke Dreiecks-Kompression (`compression == True`):** Die verbleibende Dreiecksbreite ($\text{Rot}_t - \text{Grün}_t$) beträgt höchstens $50\%$ der Anfangsbreite oder höchstens $2{,}5 \times \text{ATR}_{4\text{h}}$.
* **Handlungsanweisung im Report:** *„Vorwarnung (1–2 Tage Vorlauf). In Ruhe Chartstruktur prüfen und bei Gefallen auf die Watchlist für morgen/übermorgen setzen.“*

---

### Szenario 4: `RETEST_RED` (Der Rote Retest nach erfolgtem Ausbruch)
In unseren Backtests über 69 und 512 Aktien erzielte der **qualifizierte rote Retest** das beste Chance-Risiko-Verhältnis in $\text{R}$ ($+0{,}24\text{R}$ bzw. $+0{,}85\text{R}$ im `balanced`-Profil sowie $+0{,}44\%$ unter `r2_fan` im 512er-Bestand), weil er nach einem Ausbruch näher an der Unterstützungsstruktur kauft.

* **Wie die Engine dieses Szenario erkennt:**
  * Es existiert eine qualifizierte rote Widerstandslinie ($\ge 3$ Kontakte vor dem Bruch, Alter $\ge 10$ Tage), die innerhalb der **letzten 2 bis 16 abgeschlossenen 4H-Kerzen (1 bis 8 Handelstage)** bereits per Schlusskurs nach oben durchbrochen wurde.
  * Die untere grüne Safety Line ist weiterhin voll intakt ($\text{Close}_t > \text{Grün}_t$).
  * Der aktuelle Kurs befindet sich wieder im Rücklauf von oben auf die weiterprojizierte (gebrochene) rote Linie zu:
    $$-0{,}15 \le \frac{\text{Close}_t - \text{Rot}_t}{\text{ATR}_{4\text{h}}} \le 0{,}75$$
* **Zwei Sub-Status für den Retest:**
  * **`4A_RETEST_TRIGGER` (Abpraller bestätigt):** Das Tief der aktuellen oder vorherigen 4H-Kerze hat die gebrochene rote Linie von oben getestet ($\text{Low}_t \le \text{Rot}_t + 0{,}30 \times \text{ATR}_{4\text{h}}$), der Schlusskurs liegt wieder über der roten Linie ($\text{Close}_t \ge \text{Rot}_t$) und die aktuelle 4H-Kerze ist grün ($\text{Close}_t > \text{Open}_t$).
  * **`4B_RETEST_APPROACH` (Retest im Landeanflug):** Der Kurs fällt von einem Zwischenhoch nach dem Ausbruch zurück ($\text{Close}_t < \text{Close}_{t-2}$) und schwebt aktuell $0{,}20$ bis $0{,}75 \times \text{ATR}_{4\text{h}}$ oberhalb der gebrochenen roten Linie.

---

### Szenario 5 (Nur kleiner Anhang): `FAST_A_PLUS` (2-Kontakt-Linie unmittelbar vor dem 3. Kontakt)
Unsere Vorwarnstudie auf 512 Aktien hat gezeigt, dass 410 später qualifizierte Ausbrüche bei der ersten Annäherung erst 2 Kontakte hatten, weil sie genau durch das Anlaufen ihren 3. Kontakt ausbildeten. Um die Liste aber nicht mit 13.000 unfertigen `two`-Linien zu fluten, gelten hierfür extrem strenge Kriterien:
* Rote Linie hat aktuell exakt **2 bestätigte Kontakte**, ist aber bereits **mindestens 14 Kalendertage alt** ($\text{age\_days\_red} \ge 14{,}0$).
* Der letzte Kontakt an der roten Linie liegt mindestens **5 Kerzen zurück** (`contact_gap >= 5`), sodass ein heutiger Kontakt sofort als 3. Kontakt zählen kann.
* Der Kurs steht unmittelbar an der roten Linie ($\text{Dist}_{\text{ATR}} \le 0{,}25$), und die untere grüne Safety Line erfüllt alle Pflichtkriterien aus Tor 2 und Tor 5.
* Es werden im Report **maximal die Top 3** dieser `FAST_A_PLUS`-Kandidaten in einem kleinen separaten Anhang angezeigt.

*(Hinweis zum **Safety-Bounce**: Das Kaufen eines Abprallers an der unteren grünen Linie ohne vorherigen roten Ausbruch war im 512-Aktien-Backtest unter allen vier nachgezogenen Stop-Modellen im Schnitt negativ ($-0{,}02\%$ bis $-0{,}19\%$, Trefferquote nur $20\%$ bis $25\%$). Dieses Szenario wird im täglichen Hermes-Report **standardmäßig deaktiviert** und nur bei explizitem CLI-Flag `--include-safety-bounce` berechnet).*

---

## 5. Was Hermes für jeden Kandidaten konkret berechnen & ausgeben muss (Trade-Parameter)

Damit du beim Öffnen des Morgen-Reports nicht erst selbst Linienwerte und Stop-Puffer im Kopf ausrechnen musst, berechnet `tori_candidate_preview.py` für jeden Kandidaten folgende ausführungsfertige Felder:

### 5.1 Projektion der Ausbruchsschwelle für den anstehenden Handelstag
Da der US-Handelstag aus zwei regulären 4H-Kerzen besteht (Kerze $t+1$: 15:30–19:30 Uhr MEZ; Kerze $t+2$: 19:30–22:00 Uhr MEZ) und die rote Linie mit jeder 4H-Kerze um $\text{slope}_{\text{rot}}$ fällt, gibt das Skript die exakten Zielkurse für heute an:
* **Linienwert Kerze $t+1$ (heute Nachmittag):**
  $$\text{Rot}_{t+1} = \text{Rot}_t + \text{slope}_{\text{rot}}$$
* **Verbindliche Kauf-Schwelle (`Clean-Close-Trigger` bei $+0{,}15 \times \text{ATR}_{4\text{h}}$):**
  $$\text{Trigger}_{t+1} = \text{Rot}_{t+1} + 0{,}15 \times \text{ATR}_{4\text{h}}$$
  $$\text{Trigger}_{t+2} = \text{Rot}_t + 2 \times \text{slope}_{\text{rot}} + 0{,}15 \times \text{ATR}_{4\text{h}}$$

### 5.2 Initialer Stop-Loss & Risikokennzahlen
* **Aktueller Wert der grünen Safety Line:** $\text{Grün}_t$ (und Projektion $\text{Grün}_{t+1} = \text{Grün}_t + \text{slope}_{\text{grün}}$).
* **Gepufferter Broker-Hard-Stop ($\text{Stop}_0$):**
  $$\text{Stop}_0 = \frac{\lfloor \text{Grün}_t \times 0{,}997 \times 100 \rfloor}{100}$$
* **Geplantes Risiko bis zum Stop (ab Einstiegs-Trigger $\text{Trigger}_{t+1}$):**
  $$\text{UnitRisk}_{\text{USD}} = \text{Trigger}_{t+1} - \text{Stop}_0$$
  $$\text{Risk}_{\%} = \frac{\text{UnitRisk}_{\text{USD}}}{\text{Trigger}_{t+1}} \times 100 \quad \text{sowie} \quad \text{Risk}_{\text{ATR}} = \frac{\text{UnitRisk}_{\text{USD}}}{\text{ATR}_{4\text{h}}}$$

### 5.3 Referenz-Positionsgröße & `+2R`-Schwellenpreis (für das Stop-Nachziehen)
Auf Basis eines normierten Referenzdepots von $10.000\text{ USD/EUR}$ mit $1{,}0\%$ Risikobudget ($1\text{R} = 100\text{ USD/EUR}$) und einer maximalen Einzelpositionsgröße von $25\%$ ($2.500\text{ USD/EUR}$) gibt das Skript an:
* **Referenz-Stückzahl:**
  $$\text{Shares}_{10\text{k}} = \left\lfloor \min\left(\frac{100}{\text{UnitRisk}_{\text{USD}}}, \; \frac{2500}{\text{Trigger}_{t+1}}\right) \right\rfloor$$
* **Der `+2R`-Kursziel-Meilenstein ($\text{Price}_{+2\text{R}}$):**
  Unsere Safety-Folgestudie hat bewiesen, dass der Stop-Loss zu Beginn auf der **ursprünglichen Safety Line (`original_safety`)** bleiben muss und erst ab einem bestätigten 4H-Schlusskurs von **mindestens $+2\text{R}$ Gewinn (`r2_fan`)** (oder wenn eine neue Fächerlinie bereits 3 bestätigte Kontakte hat, `qualified_fan`) auf steilere Fächerlinien umgeschaltet werden darf. Das Skript berechnet daher direkt die $+2\text{R}$-Freigabeschwelle:
  $$\text{Price}_{+2\text{R}} = \text{Trigger}_{t+1} + 2{,}0 \times \text{UnitRisk}_{\text{USD}}$$

### 5.4 Tages-Kontext & Strategie-Klassifizierung (`TREND_FOLLOW` vs. `REVERSAL`)
Statt den Tages-SMA200 als starren Ausschlussfilter zu missbrauchen, berechnet das Skript den sauber abgeschlossenen Tages-SMA200 und Tages-SMA50 und vergibt ein klares Strategie-Etikett:
* **`TREND_FOLLOW` (Über SMA200):** Letzter Tagesschlusskurs liegt über dem Tages-SMA200 ($\text{Close}_{1\text{D}} \ge \text{SMA}_{200}$). Ideal für **Szenario 4 (`RETEST_RED`)** und Trendfolge-Ausbrüche.
* **`REVERSAL_SETUP` (Unter SMA200):** Letzter Tagesschlusskurs liegt unter dem Tages-SMA200 ($\text{Close}_{1\text{D}} < \text{SMA}_{200}$). In unseren Studien die stärkste Gruppe für **direkte Ausbrüche (Szenario 1–3)** nach tiefen Korrekturen ($+5{,}18\%$ unter `original_safety` bzw. $+1{,}54\%$ unter `r2_fan`).
* **Übergeordnetes Fächer-Dach (`outer_resistance_distance`):** Falls im 4H-Fächer (oder im 1D-Chart über `dailyRed`) oberhalb der aktuellen roten Action Line noch eine flachere Haupt-Widerstandslinie verläuft, wird deren Abstand in $\text{R}$ angegeben. Liegt dieses Hauptdach näher als $+1{,}5\text{R}$ über dem Trigger, wird ein Warn-Flag (`OVERHEAD_ROOF_NEAR`) gesetzt.

---

## 6. Neues 10-Punkte-Scoring (Reihenfolge innerhalb der Szenario-Körbe)

Da alle verbleibenden Kandidaten bereits zwingend eine qualifizierte rote Linie ($\ge 3$ Kontakte, $\ge 10$ Tage), eine gültige grüne Safety Line ($\ge 2$ Kontakte), vollständige Sitzungskerzen, echte Körperfreiheit und den gesunden Stop-Korridor ($2{,}0\%$ bis $8{,}5\%$, $\ge 1{,}0 \text{ ATR}_{4\text{h}}$) besitzen, verschwenden wir im neuen 10-Punkte-Score keine Punkte mehr für Selbstverständlichkeiten.

Der neue Score (0 bis 10 Punkte) misst ausschließlich die **strukturelle Explosivität und Sauberkeit** zur Sortierung innerhalb jedes Szenario-Korbs:

| Nr. | Kriterium (Berechnung in `tori_candidate_preview.py`) | Punkte | Fachliche Begründung aus den Backtest-Studien |
| :---: | :--- | :---: | :--- |
| **1** | **Aktive Kursannäherung (`active_approach == True`)**<br>Kurs über die letzten 3 Kerzen gestiegen ($\text{Close}_t > \text{Close}_{t-3}$) und Distanz-Reduktion zu $\ge 50\%$ durch Kursanstieg statt Linien-Gefälle | **+2** | Trennt echten institutionellen Kaufdruck unter dem Widerstand von passivem Herabsinken einer steilen Linie auf einen stagnierenden Kurs. |
| **2** | **Starke Dreiecks-Kompression (`compression == True`)**<br>Aktuelle Breite $(\text{Rot}_t - \text{Grün}_t) \le 0{,}45 \times \text{Anfangsbreite}$ oder $\le 2{,}2 \times \text{ATR}_{4\text{h}}$ | **+2** | Misst den Spannungsaufbau in der Dreiecksspitze unmittelbar vor der Richtungsentscheidung. |
| **3** | **Hohe Reife der roten Action Line**<br>$\text{age\_days\_red} \ge 21\text{ Tage}$ **oder** $\text{contacts}_{\text{rot}} \ge 4$ | **+2** | Große, mehrwöchige Widerstandsdächer (3 bis 12 Wochen) liefern deutlich nachhaltigere Ausbruchswellen als das 10-Tage-Minimum. |
| **4** | **Echte Pivot-Verankerung der roten Linie**<br>`red_origin == "pivot"` (beide Anker liegen exakt auf bestätigten Swing-Pivots, kein `refit`) | **+1** | Reine Pivot-Linien sind für das menschliche Auge im Chart sofort als klassische Lehrbuch-Trendlinien erkennbar. |
| **5** | **Optimaler Stop-Loss-Sweet-Spot**<br>$2{,}2\% \le \text{Risk}_{\%} \le 5{,}5\%$ **und** $1{,}2 \le \text{Risk}_{\text{ATR}} \le 2{,}5$ | **+1** | Liegt perfekt außerhalb des Kerzenrauschens, erlaubt aber gleichzeitig eine hohe Stückzahl bei $1\%$ Depotrisiko. |
| **6** | **Universums- & Schwungkraft-Bonus (`High-Beta`)**<br>Mitglied im `nasdaq100` **oder** tägliche Schwankungsbreite $\text{ATR}_{1\text{D}}\% \ge 2{,}8\%$ | **+1** | Im 512-Aktien-Backtest erzielte der Nasdaq-100 bei Ausbrüchen ($+0{,}49\%$) fast den vierfachen Durchschnittsertrag des breiten S&P 500 ($+0{,}13\%$). |
| **7** | **Freie Bahn nach oben (`clear_sky == True`)**<br>Kein übergeordneter 4H-Fächerwiderstand (`outerPrice`) und kein `dailyRed` innerhalb der nächsten $+2{,}5\text{R}$ oberhalb des Triggers | **+1** | Stellt sicher, dass der Ausbruch nicht sofort nach $+1\text{R}$ gegen eine darüberliegende Haupt-Widerstandslinie prallt. |

---

## 7. Verbindliche Entscheidungen zu Abschnitt 13 & Neues Report-Layout

Hiermit werden die vier offenen Fragen aus Abschnitt 13 des bisherigen Berichts verbindlich festgelegt:

1. **Welche Kandidaten zeigt die Morgenliste?**
   * Die alte Buchstaben-Einteilung (A, B, C, D, E) entfällt komplett.
   * Angezeigt werden ausschließlich Kandidaten, die **alle 6 Pflicht-Tore (Abschnitt 3)** bestehen, gegliedert nach den **4 Haupt-Szenarien** (`Szenario 1: Frischer Ausbruch`, `Szenario 2: Unmittelbar vor Ausbruch <= 0.40 ATR`, `Szenario 3: Vorwarnung 0.40–0.85 ATR`, `Szenario 4: Roter Retest`).
   * Dadurch reduziert sich die Morgenliste von 142 Roh-Treffern auf **ca. 8 bis 20 hochqualitative Setups**, die nach Handlungsdringlichkeit gruppiert sind.
2. **Wie wird mit den bisherigen D-Titeln (Geometrie-/Datenhinweis) verfahren?**
   * Kandidaten mit echten Körperbrüchen ($> 0{,}05 \times \text{ATR}_{4\text{h}}$) werden **komplett ausgeschlossen** und erscheinen nicht im Report.
   * Kandidaten, die lediglich die Engine-interne Mini-Toleranz ($\le 0{,}05 \times \text{ATR}_{4\text{h}}$) nutzen oder eine `refit`-Linie verwenden, sind **keine** Fehler und werden normal in den Szenarien geführt (mit entsprechender Kennzeichnung in der Geometrie-Spalte).
3. **Wie werden Datenprobleme und Earnings dargestellt?**
   * **Datenprobleme:** Keine Einzelzeilen in der Kandidatenliste, sondern eine kompakte Statuszeile ganz unten im Report (`Daten-Audit: 485/520 geprüft | 21x Vorlauf < 320d | 10x fehlende 4H-Kerze [Liste] | 4x 5m-Lücken [Liste]`).
   * **Earnings (sofern lokal/aus Metadaten bekannt):** Als direktes Warn-Badge `⚠️ EARNINGS (Xd)` in der Kandidatenzeile.
4. **Werden künftig Zustände statt bloßer Nähe gemeldet?**
   * **Ja, zwingend.** Jede Zeile im Report und in der CSV trägt das Feld `scenario` (`1A_CLEAN_BREAKOUT`, `1B_ARMED_WAIT_CLEAN`, `2_IMMEDIATE_TEST`, `3_APPROACH_WATCH`, `4A_RETEST_TRIGGER`, `4B_RETEST_APPROACH`, `5_FAST_A_PLUS`) sowie das Feld `strategy_tag` (`TREND_FOLLOW` über SMA200 vs. `REVERSAL` unter SMA200).

---

### Vorlage für den neuen täglichen Markdown-Report (`~/.hermes/reports/trend-kandidaten-YYYY-MM-DD.md`)

Der generierte Markdown-Report soll ab sofort exakt dieser übersichtlichen Struktur folgen:

```markdown
# 🎯 Tori Trendlinien-Radar · Zielsitzung: YYYY-MM-DD

**Geprüfte Aktien:** 485 / 520 (aus `dow30`, `nasdaq100`, `sp500`)  
**Qualifizierte Treffer (Tore 1–6 erfüllt):** XX Kandidaten (absteigend nach Score 0–10 sortiert)

---

## 🚨 SZENARIO 1: Frische Ausbrüche über Rot (Sofort-Prüfung!)
*Die 4H-Kerze hat die qualifizierte rote Widerstandslinie (3+ Kontakte, >= 10d) in der Zielsitzung bereits per Schlusskurs überquert.*

| Symbol | Sub-Status | Score | Schluss | Rot (Bruch) | Clean-Trigger | Grün (Stop 0,3%) | Risiko (% / ATR) | +2R Ziel | Rot (Kont./Alter) | Kontext (1D) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **ANET** | `1A_CLEAN` | **9/10** | 194,20 $ | 192,80 $ | **193,45 $** (OK) | 185,40 $ (**184,84 $**) | 4,8 % / 1,9 ATR | 212,06 $ | 4K / 38d (`pivot`) | `TREND_FOLLOW` (>SMA200) |

---

## 🔥 SZENARIO 2: Unmittelbar vor dem Ausbruch (<= 0,40 ATR / Test läuft)
*Der Kurs drückt unmittelbar von unten gegen das qualifizierte rote Widerstandsdach. Entscheidung in den nächsten 1–2 Kerzen möglich.*

| Symbol | Status / Dynamik | Score | Schluss | Abstand Rot | Trigger (Morgen K1 / K2) | Stop-Kurs (0,3%) | Risiko (% / ATR) | +2R Ziel | Rot (Kont./Alter) | Kontext (1D) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **PLTR** | `2_IMMEDIATE` (Aktiv+Kompr.) | **8/10** | 42,10 $ | **0,22 ATR** (0,8%) | **42,65 $** / 42,52 $ | **40,35 $** | 5,4 % / 1,6 ATR | 47,25 $ | 3K / 24d (`pivot`) | `TREND_FOLLOW` (>SMA200) |

---

## 🔭 SZENARIO 3: Vorwarnung 1–2 Handelstage (0,40 bis 0,85 ATR + Aktive Dynamik)
*Frühzeitige Beobachtungsliste: Struktur verengt sich oder Kurs läuft aktiv auf die qualifizierte rote Linie zu.*

| Symbol | Dynamik | Score | Schluss | Abstand Rot | Trigger (Morgen K1) | Stop-Kurs (0,3%) | Risiko (% / ATR) | Rot (Kont./Alter) | Grün (Kont./Alter) | Kontext (1D) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **MU** | `3_APPROACH` (Aktiv) | **7/10** | 108,20 $ | **0,68 ATR** (2,1%) | **111,05 $** | **104,58 $** | 5,8 % / 2,1 ATR | 3K / 19d (`pivot`) | 2K / 31d | `REVERSAL` (<SMA200) |

---

## 🔵 SZENARIO 4: Roter Retest (Rücklauf von oben auf gebrochenes A+-Rot)
*Qualifizierte rote Linie wurde kürzlich nach oben durchbrochen; Kurs setzt bei intakter grüner Safety von oben auf die rote Linie zurück.*

| Symbol | Sub-Status | Score | Schluss | Gebrochenes Rot | Abstand zu Rot | Stop-Kurs (0,3%) | Risiko (% / ATR) | +2R Ziel | Bruch vor | Kontext (1D) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **AMZN** | `4A_TRIGGER` (Grüne Kerze) | **8/10** | 214,10 $ | 212,80 $ | **+0,35 ATR** (+0,6%) | **204,10 $** | 4,7 % / 1,8 ATR | 234,10 $ | 4 Kerzen | `TREND_FOLLOW` (>SMA200) |

---

## 👀 ANHANG: Fast-A+ Watchlist (Max. Top 3 mit 2 Kontakten unmittelbar vor Kontakt Nr. 3)
*(Nur zur Vormerkung: Linien mit >= 14 Tagen Alter und <= 0,25 ATR Abstand, die heute ihren 3. Kontakt ausbilden können)*
...

---
**Technik- & Daten-Audit (CT118):**  
Laufzeit: XX,X s | Geprüft: 485/520 | Ausgeschlossen: 21x Vorlauf < 320d, 10x `missing_session_4h` (...), 4x `data_problem` (...).  
*Hinweis zur Ausführung: Alle Stop-Kurse enthalten bereits den 0,3-%-Puffer (abgerundet auf volle Cent). Stop-Nachführung erst ab Erreichen des `+2R Ziel`-Schlusskurses (`r2_fan`) oder auf 3-Kontakt-Safety (`qualified_fan`) verengen.*
```

---

## 8. Zusätzliche Spalten für die CSV- und JSON-Ausgabe (`trend-kandidaten-YYYY-MM-DD.csv`)

Damit die Ergebnisse sowohl im Web-Viewer (Port 8877) als auch in späteren Auswertungen direkt nach Szenarien und Risikoklassen gefiltert werden können, muss die erzeugte CSV-Datei pro Kandidat folgende Pflichtspalten enthalten:

1. `symbol`, `universes` (z. B. `nasdaq100|sp500`)
2. `scenario` (`1A_CLEAN_BREAKOUT`, `1B_ARMED_WAIT_CLEAN`, `2_IMMEDIATE_TEST`, `3_APPROACH_WATCH`, `4A_RETEST_TRIGGER`, `4B_RETEST_APPROACH`, `5_FAST_A_PLUS`)
3. `score` (0 bis 10), `strategy_tag` (`TREND_FOLLOW` oder `REVERSAL`)
4. `close_4h`, `atr_4h`, `atr_1d_pct`
5. `red_price_now`, `red_price_next1`, `red_price_next2`, `clean_trigger_next1`, `clean_trigger_next2`
6. `dist_to_red_atr`, `dist_to_red_pct`
7. `green_price_now`, `stop_0_3_pct` (abgerundeter Hard-Stop), `risk_usd`, `risk_pct`, `risk_atr`
8. `target_plus_2r_price`, `ref_shares_10k`
9. `red_contacts`, `red_age_days`, `red_contact_span_days`, `red_origin` (`pivot` / `refit`)
10. `green_contacts`, `green_age_days`, `green_origin`
11. `active_approach` (`True`/`False`), `compression` (`True`/`False`), `clear_sky` (`True`/`False`)
12. `daily_close`, `daily_sma200`, `above_sma200` (`True`/`False`), `overhead_roof_r`

---

## 9. Neue CLI-Parameter für `tori_candidate_preview.py`

Bitte ergänze das Skript um folgende optionale Filter-Flags für gezielte Abfragen, ohne dass der Standardlauf (der immer alle Szenarien 1 bis 5 in die Markdown- und CSV-Datei schreibt) verändert werden muss:

* `--scenario {all,breakout,immediate,approach,retest,fast_a}` (Default: `all`)
* `--min-score INT` (Default: `0`, erlaubt z. B. `--min-score 6` für extrem komprimierte Kurzbriefings)
* `--universe {all,nasdaq100,sp500,dow30}` (Default: `all`)
* `--include-safety-bounce` (Default: `False`; aktiviert den im Standard ausgeblendeten Safety-Bounce nur für Forschungszwecke)