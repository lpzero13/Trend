# Projektstand & Zentrale Wissensbasis: Tori-Trendlinien-Projekt (`alpaca-trendlinien`)

**Stand:** November 2026  
**Zweck dieses Dokuments:** Vollständige, verlustfreie Übergabe des fachlichen Regelwerks, aller bisherigen empirischen Studienergebnisse, der Praxisanforderungen des Nutzers sowie der priorisierten nächsten Entwicklungsschritte.

---

## 1. Gesamtziel & Praxiskontext (Das „Warum“)

Ziel des Projekts ist ein vollautomatisiertes, wissenschaftlich überprüfbares Analyse- und Briefing-System für **geometrische 4H-Trendlinien-Ausbrüche und Retests** (abgeleitet vom Tori-Trades-Ansatz), das aus einem Universum von über 500 US-Aktien täglich wenige, hochqualitative Setups für die manuelle Sichtprüfung und das Trading herausfiltert.

### Reale Handels-Rahmenbedingungen des Nutzers
* **Broker & Ausführungsfenster:** Handel über **Trade Republic** und **ING**. Einstiege erfolgen gezielt während der US-Kernhandelszeit (**15:30–22:00 Uhr MEZ**), um enge Spreads (`$\approx 0{,}1\,\%$` bis `$0{,}25\,\%$`) zu sichern.
* **Aktien-Universum (Sweet Spot):** Liquide US-Wachstums- und Momentum-Aktien (Mid-Caps ab ca. 2–3 Mrd. USD und High-Beta Large-Caps, insbesondere **Nasdaq-100**), Aktienkurs `$\ge 20\text{ USD}$`, hohes Tagesvolumen (`$\ge 1{,}0$` bis `$1{,}5$` Mio. Aktien/Tag). Bewusst **kein** träger DAX und **keine** illiquiden Penny-Stocks/Micro-Caps (zu hohe Spreads, unsaubere Zufallsdochte).
* **Risikomanagement & Asymmetrie:**
  * Festes Standard-Risiko pro Trade: **`$1{,}0\,\%$` des Gesamtkapitals (`$1\text{R}$`)** – dauerhaft beibehalten, Skalierung erfolgt automatisch über Zinseszins.
  * Optionale Positions-Obergrenze pro Aktie: **`$25\,\%$` des Gesamtkapitals** (bremst das Klumpenrisiko bei sehr engen Anfangsstops).
  * **Strategische Logik:** Die Trefferquote liegt je nach Stop-Modell bei ca. `$28\,\%$` bis `$42\,\%$`; die meisten Fehlversuche enden klein (Median `$-0{,}85\,\%$` bis `$-1{,}50\,\%$` bzw. oft nur `$-0{,}3\text{R}$` bis `$-0{,}6\text{R}$` durch steigende Safety Lines). Einzelne große Trendläufer (`$+30\,\%$` bis `$+100\,\%+$` Kursgewinn, entsprechend `$+6\text{R}$` bis `$+25\text{R}+$`) bezahlen dutzende Fehlversuche und treiben die Gesamtbilanz.

---

## 2. Fachliche Kern-Mechanik (Engine, Entries, Stops & Exits)

### 2.1 Master-Fächer-Geometrie (`fan_master`, Profil `master`)
* **Zeiteinheiten:** `4H` für Trendlinien, Struktur und Signale; `1D` als Trendkontext (SMA200, `dailyRed`); `5m` für reale Ausführungs- und Stop-Simulation.
* **Maßgebliche Parameter (unverändert für Backtest-Kompatibilität):**
  * `pivot_side = 2` (Pivot-Bestätigung nach 2 Kerzen links/rechts)
  * `atr_length = 14` (`$\text{ATR}_{4\text{h}}$`)
  * `contact_atr = 0.45` (Kontakt-Toleranz / „Schaumstoffmatte“)
  * `contact_gap = 5` (Mindestabstand in Kerzen zwischen zwei gezählten Kontakten)
  * `wick_atr = 0.15`, `body_atr = 0.05` (Docht- und Körpertoleranz)
  * `min_age_days = 7` (Mindestalter für Basis-Qualifikation)
  * `lookback_days = 320` (Grün / Safety), `action_lookback_days = 150` (Rot / Action Line), `max_bars = 1800`, `levels = 4`
  * `lag = 0` im Screening (rein kausal)
* **Kontaktklassen (strikt getrennt):**
  * `qualified` (`A+`): `$\ge 3$` zeitlich getrennte Kontakte und `$\ge 7$` Kalendertage Alter.
  * `three_young`: 3 Kontakte, aber `< 7` Tage alt.
  * `two`: 2 Kontakte (keine rückwirkende Aufwertung!).

### 2.2 Episoden & Signalfamilien
* Über `setup_episodes.py` teilen Linien derselben Fächer-Herkunft eine stabile Episoden-ID, sodass kleine Winkelanpassungen keine täglichen Doppel-Signale erzeugen.
* Drei getrennte Signalfamilien:
  1. **`breakout` (Ausbruch über Rot):** 4H-Schlusskurs über der roten Widerstandslinie; Clean-Close-Schwelle liegt bei `$\text{Rot} + 0{,}15 \times \text{ATR}_{4\text{h}}$`.
  2. **`red_retest` (Roter Retest):** Nach erfolgtem Ausbruch Rücklauf von oben auf die ursprüngliche gebrochene rote Linie derselben Episode bei intakter grüner Safety.
  3. **`safety_bounce` (Abpraller an Grün):** Nur auf einer bereits auf der Vorkerze qualifizierten steigenden grünen Linie (in den Ergebnissen bisher schwach/negativ; im operativen Briefing ausblenden).

### 2.3 Stop-Loss & Ausführungsmodell (Optimiert gegenüber Tori Original)
* **Warum kein reiner 4H-Kerzenschluss-Stop:** Tori wartet im Original manuell auf einen 4H-Kerzenschluss unter der Safety Line. Unsere Exit-Studie vom 30.10.2026 zeigte jedoch, dass ein reiner 4H-Close-Stop bei plötzlichen Abstürzen das Risiko von Verlusten `$> 1\text{R}$` beim roten Retest von `$4{,}27\,\%$` (Hard-Stop) auf `$23{,}83\,\%$` erhöht (Extremfall `INTC`: `$-61{,}78\text{R}$`).
* **Verbindlicher Hard-Stop mit `$0{,}3\,\%$` Puffer:**
  $$\text{Stop}_0 = \frac{\lfloor \text{Safety} \times (1 - 0{,}003) \times 100 \rfloor}{100}$$
  Damit führen normale Berührungen oder kurze Dochte an der Safety Line nicht zum Ausstoppen, während extreme Abstürze mitten in der Kerze begrenzt werden.
* **Ausführung im Backtest:** Entscheidung am abgeschlossenen 4H-Balken; Entry und Stop-Update erst am nächsten erwarteten 5m-Open nach `$300$` Sekunden; Opening-Gap unter dem Anfangsstop verhindert den Kauf; Hard-Stop-Gaps werden realistisch zum tatsächlichen Open gefüllt; Kosten: 5 bps Spread gesamt + 5 bps Slippage je Seite; Stops bewegen sich nach dem **Ratchet-Prinzip** ausschließlich aufwärts.
* **Die 5 Exit-Varianten:**
  1. `fixed`: Fester Anfangsstop (reine Kontrolle, kein regulärer Gewinn-Exit).
  2. `original_safety`: Ursprüngliche steigende Einstiegs-Safety wird unverändert weiterprojiziert.
  3. `fan_safety` („Aktuelle Safety“): Zieht sofort auf jede neue steilere gültige Fächerlinie nach (auch mit nur 2 Kontakten) – wechselt im Schnitt schon nach 4–6 Tagen bei `$+0{,}18\text{R}$` bis `$+0{,}25\text{R}$` und würgt große Trendläufer oft zu früh ab.
  4. `qualified_fan`: Hält `original_safety` und wechselt nur auf eine höhere Fächerlinie, wenn diese bereits `qualified` (`$\ge 3$` Kontakte) ist.
  5. `r2_fan`: Hält `original_safety` bis zu einem bestätigten 4H-Schlusskurs von mindestens `$+2{,}0\text{R}$` Netto-Buchgewinn; danach wird die engere aktuelle Fächer-Safety dauerhaft zugelassen.

---

## 3. Abgeschlossene Studien & Empirische Kernergebnisse

### 3.1 Gemeinsame Datenbasis
* **Universum (erweiterter Bestand):** Vereinigung lokaler, gespeicherter ETF-Bestandslisten vom 28.10.2026: Dow Jones (`DIA`, 30), Nasdaq-100 (`CNDX`, 101), S&P 500 (`IVV`, 505) = **520 eindeutige Symbole** (SIP, split-adjustiert, reguläre XNYS-Sitzungen, 5m-Basis).
* **Geeignete Aktien:** **512 Titel** erfüllen in mindestens einem Fenster den Vorlauf von `$\ge 320$` Tagen (`Dow 30`, `Nasdaq 97`, `S&P 500 499`). 8 junge Titel fehlen wegen zu kurzer Historie (`CRWV`, `FDXF`, `FER`, `HONA`, `SKYD`, `SKYD.WS`, `SNDK`, `VYLR`). 68 geeignete Kontrollaktien aus dem 69er-Altbestand (`SNDK` war ungeeignet) + 444 neue Aktien.
* **Bekannte Forschungsfenster:** `2018`, `2021`, `2023`, `April 2025 – März 2026` (`1.004` XNYS-Sitzungen), Nachbeobachtung bis `2026-10-29T15:25:00+00:00`. **Wichtig:** Dies sind bekannte Daten und heutige Überlebendenbestände – keine unabhängige Holdout-Bestätigung.

### 3.2 Studie A: Strukturfilter auf dem 69er-Bestand (`SIGNALFILTER-ERGEBNISSE-20261031.md`)
* **Umfang:** 69 Aktien, `6.668` Rohfälle, `1.790` zeichnungsfähige qualifizierte rote Fälle (`1.778` Fills), 9 vorab festgelegte Profile.
* **Kernergebnisse:**
  * **`risk` (Mindestabstand `$\ge 1{,}0\text{ ATR}_{4\text{h}}$` und `$\ge 2{,}0\,\%$` am Signal):** Einziger Einzelfilter mit durchgängiger Verbesserung gegenüber der Basisgruppe `qualified`. Ausbrüche stiegen unter `original_safety` von `$+4{,}62\,\%$` auf `$+5{,}78\,\%$`, unter `r2_fan` von `$+0{,}77\,\%$` auf `$+0{,}93\,\%$` (`fan_safety` Trefferquote `$42{,}20\,\%$`). Retests stiegen unter `original_safety` von `$+2{,}04\,\%$` auf `$+2{,}80\,\%$` (`fan_safety` Trefferquote `$40{,}48\,\%$`).
  * **`both_qualified` (Auch Safety `$\ge 3$` Kontakte):** Starker negativer Effekt in allen 4 Modellen (Ausbruch `original_safety` `$-0{,}69\,\%$`, `fan` `$-0{,}09\,\%$`; Retest `fan` `$-0{,}37\,\%$` / `$-0{,}15\text{R}$`).
  * **`strict` (Alle Regeln kombiniert, 206 Fälle, 191 gemeinsam bewertbar):** Negativ unter allen 4 Stop-Modellen (`$-1{,}54\,\%$` / `$-0{,}29\,\%$` / `$-1{,}04\,\%$` / `$-1{,}16\,\%$`).
  * **`SMA200`-Gegenprobe:** Direkte Ausbrüche *nicht* über SMA200 (`$+1{,}17\,\%$` `fan`, `$+5{,}18\,\%$` `orig`) liefen besser als über SMA200 (`$+0{,}07\,\%$` `fan`, `$+1{,}10\,\%$` `orig`). Bei Retests war `balanced` (`risk` + über SMA200) stabil stark (`$+3{,}02\,\%$` / `$+0{,}85\text{R}$` unter `orig`).
  * **Methodische Grenze:** Nachträgliches Filtern bereits archivierter Erstsignale verschluckt spätere bessere Setups derselben Episode, weil die alte Episodensperre schon beim unreifen Erstsignal zuschlug.

### 3.3 Studie B: Historisches Vorwarn-Radar auf 512 Aktien (`EARLY-WARNING-512-ERGEBNISSE-20261101.md`)
* **Umfang:** 512 Aktien, `620.552` unabhängig geprüfte Warnzustände über 12 überlappende Policies (`0.5 / 1.0 / 1.5 ATR` `$\times$` `distance / active / compression / combined`). `15.725` Ausbruchs-, `10.781` Retest- und `7.265` Bounce-Referenzen.
* **Kernergebnisse (`distance:1` als bester Schwellen-Kompromiss):**
  * **Out-of-Sample-Stabilität:** Die 444 neuen Aktien bestätigen die 68 Kontrollaktien fast 1:1. Aktive Erfassung Ausbruch: `$49{,}2\,\%$` (neu) vs. `$51{,}8\,\%$` (alt), Gesamt **`$49{,}7\,\%$`** (`7.810` Fälle). Roter Retest: `$37{,}5\,\%$` (neu) vs. `$34{,}9\,\%$` (alt), Gesamt **`$37{,}0\,\%$`** (`3.993` Fälle).
  * **Vorlauf & Linien-Treue:** Median-Vorlauf `$2{,}0$` 4H-Kerzen bis Clean-Close-Entry (`$36{,}0\,\%$` 1–2 Sitzungstage vorher) bzw. `$1{,}0$` Kerze (`$21{,}5$` reale Stunden) bis zum ersten rohen Rot-Bruch (`$33{,}1\,\%$` bzw. `5.202` Fälle 1–2 Sitzungstage vorher). Bei `7.699` von `7.810` erfassten Ausbrüchen (**`$98{,}6\,\%$`**) war die ursprünglich gewarnte technische Linie identisch mit der späteren Signallinie.
  * **Tageslast & Kontaktklassen:** Alle 3 Familien zusammen erzeugen `$42{,}57$` Briefings/Tag (Spitze `125`). Ursache: `$13.243$` von `$16.299$` Ausbruchswarnungen sind `two`-Linien (nur `$3.052$` `qualified` `$\approx 3{,}04/\text{Tag}$`); Retest hat `$3.523$` `qualified` (`$\approx 3{,}51/\text{Tag}$`). `410` später qualifizierte Ausbrüche waren bei Erstwarnung noch `two`.
  * **Zusatzmerkmale:** `active` und `compression` als harte Gates senken die Erfassung deutlich (`$38{,}8\,\%$` / `$45{,}3\,\%$` / `$35{,}8\,\%$`), ohne die Bestätigungsquote (`$47{,}1\,\%$` bis `$48{,}4\,\%$`) zu verbessern.
  * **Größter offener Hebel (Lebenszyklus / Re-Arming):** `6.999` spätere Ausbruchs-Entries (`$44{,}5\,\%$`) hatten bereits eine Vorwarnung, deren Watch vor dem Entry geschlossen wurde (z. B. Entfernung `$> 2{,}5\text{ ATR}$`). Zusammen mit den `7.810` aktiv erfassten hat das Radar **`$94{,}2\,\%$` (`14.809 / 15.725`)** aller Ausbrüche gesehen (Retest: `3.993` aktiv + `3.629` vorzeitig geschlossen).

### 3.4 Studie C: Universen- & Exit-Backtest auf 512 Aktien (`BACKTEST-UNIVERSEN-ERGEBNISSE-20261101.md`)
* **Umfang:** 512 Aktien, `39.440` Fälle aus `27.072` Episoden (`59.847` Wiederholungen unterdrückt), `35.424` modellierte Fills, `$1.000\text{ USD}$` nominal je Fall, `197.200` Modellzeilen in `trades-by-universe.csv`.
* **Universen-Vergleich (`Aktuelle Safety`, qualifiziert, geschlossen):**
  * **Nasdaq-100 (`CNDX`):** Ausbruch **`$+0{,}49\,\%$`** (`1.240` Trades), Retest **`$+0{,}26\,\%$`**, Bounce `$+0{,}13\,\%$`.
  * **Dow Jones (`DIA`):** Ausbruch `$+0{,}35\,\%$`, Retest `$+0{,}28\,\%$`, Bounce `$+0{,}19\,\%$`.
  * **S&P 500 (`IVV`):** Ausbruch `$+0{,}13\,\%$`, Retest `$+0{,}07\,\%$`, Bounce `$-0{,}09\,\%$` (breite S&P-500-Werte verwässern den Schnitt gegenüber dem Nasdaq-100 um fast den Faktor 4).
* **Exit-Treppe (qualifiziert, alle jeweils geschlossenen Fälle):**
  * Ausbruch: `$+0{,}14\,\%$` (`Aktuelle Safety`, `$36{,}02\,\%$` Treffer) `$\rightarrow$` `$+0{,}30\,\%$` (`qualified_fan`, `$31{,}54\,\%$`) `$\rightarrow$` `$+0{,}40\,\%$` (`r2_fan`, `$28{,}63\,\%$`).
  * Roter Retest: `$+0{,}06\,\%$` (`Aktuelle Safety`, `$33{,}77\,\%$`) `$\rightarrow$` `$+0{,}33\,\%$` (`qualified_fan`, `$31{,}27\,\%$`) `$\rightarrow$` `$+0{,}44\,\%$` (`r2_fan`, `$28{,}23\,\%$`).
  * Gemeinsam bewertbare Teilmenge (`5.743` Ausbrüche / `3.733` Retests): `Aktuelle Safety` `$-0{,}02\,\%$` / `$-0{,}06\,\%$`, `qualified_fan` `$+0{,}07\,\%$` / `$+0{,}13\,\%$`, `r2_fan` `$+0{,}12\,\%$` / `$+0{,}15\,\%$`, `original_safety` `$+2{,}45\,\%$` / `$+1{,}50\,\%$` (inkl. 60/35 offener Buchwerte; Datenlücken zensieren länger laufende Modelle stärker: 334–481 Lücken vs. 198 bei `Aktuelle Safety`).
* **Zwei klar getrennte Großverlust-Ursachen:**
  1. **Überdehnte Anfangsstops:** `TSLA` (`$-35{,}60\,\%$`, aber nur `$-0{,}84\text{R}$` wegen `$42{,}43\,\%$` Stop-Abstand!), `MU` (`$-17{,}62\,\%$`, `$-1{,}00\text{R}$`), `ALAB` (`$-17{,}57\,\%$`, `$-0{,}95\text{R}$`).
  2. **Earnings-Overnight-Gaps:** `FTNT` (`$-21{,}34\,\%$` / `$-10{,}41\text{R}$` und `$-22{,}13\,\%$` / `$-7{,}37\text{R}$`), `GNRC` (`$-19{,}56\,\%$` / `$-3{,}13\text{R}$`, `$-18{,}95\,\%$` / `$-4{,}51\text{R}$`), `TWLO`, `LULU`.
* **Einzelaktien-Muster:** High-Beta-Wachstumstitel liefern die größten Ausreißer (`CVNA +166,19 % / +9,49R`, `ASML +156,76 % / +147,49R`, `PLTR +93,78 % / +12,29R`, `RKLB +76,78 %`, `MU +69,80 %`, `APP +60,49 %`, `DDOG`, `COIN`). Aber Zwillingswerte wie `SMCI` (`$-3{,}40\,\%$` aus 21 Fällen) und `ALAB` (`$-3{,}44\,\%$` aus 13 Fällen) zeigen, dass historische Gewinnernamen keine Vorab-Garantie sind.

---

## 4. Aktueller Software-, Werkzeug- & Infrastrukturstand

### Vorhandene Werkzeuge & Dienste
* **Lokale Web-Oberfläche (Port `8877`):** Läuft ohne allgemeinen Worker auf demselben `TORI_DATA_DIR`. Enthält unter **Historische Einstiege -> Signalauswahl** alle 9 Profile aus der Filterstudie (Standard: `qualified`), Schnell-Cache (`$\approx 0{,}01\text{ s}$` warm), Replay-Stepper und Bewertungsfeld ohne Zukunftsspoiler. Persönliche Zeichnungen sind streng getrennt.
* **Vorwarn-CLI (`tools/early_warning.py`):** Unterstützt `all`, `build`, `evaluate`, `briefing --asof`, `show`, `review` (`mute`/`snooze`/`unmute`). Begleittools: `tools/verify_early_warning.py` (bis 4 Worker), `tools/verify_warning_prefix.py`, `tools/report_early_warning.py`, `tools/compare_early_warning.py`.
* **Backtest- & Filter-CLI:** `tools/run_event_cases.py`, `tools/run_exit_followup.py`, `tools/run_entry_screen.py` samt zugehöriger `verify_*`- und `report_*`-Skripte.
* **Hermes-Tages-Preview auf Proxmox `CT118`:** `/var/lib/tori/operations/preview/tori_candidate_preview.py`, ausgeführt per `systemd-run` als `tori` (`CPUQuota=60%`, `MemoryMax=420M`, `MemorySwapMax=0`, Netzwerk gesperrt). Letzter Lauf vom 13.11.2026: `110,7 s` für 520 Titel -> `142` Rohkandidaten (`5 A`, `23 B`, `14 C`, `25 E`, `75 D`). Muss gemäß `docs/HERMES-SCANNER-SPEZIFIKATION.md` umgebaut werden.
* **Private Artefakt-Ordner (außerhalb von Git):**
  * `artifacts/entry-screen-20261031`
  * `artifacts/early-warning-wide-final-20261101` (69er Vorwarnung)
  * `artifacts/early-warning-expanded-20261101` (512er Vorwarnung)
  * `artifacts/exit-followup-population-20261101` (512er P/L-Studie inkl. `trades-by-universe.csv`, `stock-overview.csv`, `stock-summary.csv`, `universe-summary.csv`, `window-summary.csv`, `coverage.csv`, `largest-winners.csv`, `largest-losers.csv`)
* **Letzter geprüfter Teststand (21.11.2026, Branch `codex/hermes-scanner-watchlist`):** 602 Python-Tests bestanden (1 bekannter Skip; inkl. 7 Scanner-/Watchlist-/Papertrade-/API-Tests + 3 Weg-B-Backtest-/Kausalitäts-/PIT-/Holdout-Tests) und 113 JS-Tests bestanden.
* **Neu umgesetzt (Paket 1 + Watchlist & 1.000-€-Papertrade-Tracker + Point-in-Time-Universum + Weg-B-Kriterien-Backtest, lokal geprüft):**
  * **Survivorship-Bias-freies Point-in-Time-Universum (2016–2026):** `pit_membership.py` + CLI `tools/pit_universe.py`. Führt historische Index-Bestandsänderungen für **Dow 30 (`41` Titel)**, **Nasdaq-100 (`206` Titel)** und **S&P 500 (`751` Titel)** zu **802 eindeutigen Symbolen** zusammen (`520` aktuelle 2026er-Mitglieder + `282` ausgeschiedene/delistete/übernommene Ex-Mitglieder wie `SIVB`, `SBNY`, `BBBY`, `WBA`, `ATVI`, `TWTR`, `ZM`, `SEDG`). **802 / 802 Titel** vollständig als verifizierte 5m-SIP-Parquet-Daten (split-adjustiert, reguläre XNYS-Sitzungen, inkl. historischer `asof`-Abfragen) lokal importiert (`data/pit-membership/pit-membership-2016-2026.json` & `import-audit.json`, privat außerhalb Git).
  * **Weg-B-Mehrjahres-Backtest im PIT-Modus (`artifacts/scanner-backtest-pit-20261121`, privat außerhalb Git):** `scanner_backtest.py` + CLI `tools/run_scanner_backtest.py` + `tests/test_scanner_backtest.py`. Vollständiger Lauf über **802 Aktien** in `11,4 min` mit **0 Fehlern** (`799 ok`, `3 insufficient_bars`): **`12.232` sichtbare Trades** (`train` `2017-07-01..2023-12-31`: `10.690` gefüllt / `10.053` geschlossen; `validation` `2024-01-01..2024-12-31`: `1.464` gefüllt / `1.403` geschlossen) sowie **`2.577` gesperrte Holdout-Trades** (`2025-01-01..2026-06-30`, weiterhin ungeöffnet).
    * **Empirisch gemessener Survivorship-Bias (`r2_fan`):** Heutige 520 Mitglieder vs. 282 Ex-Mitglieder im `train`-Split: `$-0{,}009\text{ R}$` (`$-1.047\text{ €}$`, `7.928` Trades) vs. **`$-0{,}152\text{ R}$`** (`$-10.667\text{ €}$`, `2.125` Trades); in `validation` (2024): `$+0{,}077\text{ R}$` vs. **`$-0{,}172\text{ R}$`**. Ohne PIT wäre der Backtest massiv geschönt gewesen.
    * **Stop-Modelle (`train` / `validation` / `holdout`):** `r2_fan` (`-0,039 R` / `+0,053 R` / `+0,003 R`, ex-Top-3 `-0,045` / `+0,027` / `-0,021 R`) schlägt `qualified_fan` in allen 3 Splits und ist auch robuster als `original_safety` (`-0,174 R` in `train`, `-0,029 R` ex-Top-3 im `holdout`).
    * **Einmalige Holdout-Gegenprobe (`2025-01 .. 2026-06`, `2.577` Trades / `2.468` bewertbar, `report.md` mit `--reveal-holdout` aktualisiert):**
      * **In ALLEN 3 Zeiträumen (`train`, `validation`, `holdout` = `14.809` Trades) bestätigt:**
        1. `Niedrige Tages-Vola (< 1,5 % ATR)`: **`+0,130 R`** / **`+0,288 R`** / **`+0,362 R`** (ex-Top-3 in allen 3 Splits klar positiv: `+0,082` / `+0,114` / `+0,209 R`!).
        2. `Aktive Annäherung = Ja`: `-0,033` / `+0,083` / `+0,008 R` (vs. `Nein` in allen 3 Splits negativ: `-0,077` / `-0,128` / `-0,026 R`).
        3. `Direkteinstieg (1A/4A)` vor `watch_to_entry`: `-0,033/-0,023` / `+0,104/+0,081` / `+0,008 R` vs. `-0,063` / `-0,036` / `-0,009 R`.
        4. `Hohe Reife (>= 21T / >= 4K) = Ja`: `-0,023` / `+0,067` / `+0,006 R` vs. `-0,100` / `+0,004` / `-0,008 R`.
      * **Im Holdout NICHT bestätigt / widerlegt:**
        * `Stop 2,5–3,5 ATR` brach im Holdout weg (`-0,076 R` vs. `+0,031 R` beim Rest → Profil `P2` fiel im Holdout auf `-0,093 R` / `-20,5 %` Depot).
        * Starre Markt-Kaufsperre `SPY > SMA200` / `QQQ > SMA200` schnitt systematisch die stärksten Post-Crash-Bodenausbrüche ab (`2019`, `2020`, `2023` und April-2025-Selloff: `SPY <= SMA200` lieferte im Holdout `+0,153 R` / `+5.747 €`!).
        * Reparierter Einzelaktien-`SMA200` ist regime-abhängig (`train`: unter SMA200 besser; `validation`: über SMA200 besser) und bleibt daher Info-Tag.
      * **Realistische 10.000-€-Depot-Simulation (1 % Risiko, 25 % Cap, max. 8 Pos., 9 Jahre 2017–2026):** Ungefilterte Basis `8.047 €` (`-19,5 %`, MaxDD `54,7 %`); `P1` (`7.253 €`, MaxDD `45,4 %`); `P2` (`10.479 €`, `+4,8 %`, MaxDD `24,9 %`, aber Holdout `-20,5 %`). Belegt ehrlich: 4H-Trendlinien-Ausbrüche sind kein blinder vollautomatischer Profit-Bot, sondern ein Struktur- und Risiko-Werkzeug für selektive Sichtprüfung.
    * **Umgesetzte Scanner-Bereinigung (Schritt 4, `hermes_scanner.py` + `/radar`):**
      * `SMA200`-Lücken-Fallback (toleriert bis zu 2 einzelne Sonderfeiertags-Lücken im 200-Tage-Fenster statt 200 Tage `UNKNOWN`).
      * Empirisch bereinigtes 10-Punkte-Scoring (alte `-1`-Strafe auf `low_daily_volatility` entfernt und durch `+1` ersetzt; `direct_entry +1`, `active_approach +2`, `high_maturity +2`; kein unbestätigter `2,5–3,5 ATR`-Zwang).
      * Informative **Marktlage-Leiste** (`SPY` & `QQQ` lokal importiert, 2016–2026 SIP, Anzeige im `/radar` ohne harte Kaufsperre), optionales Dropdown **3/3-Kern (Direkt + Aktiv + Reife)** sowie klare Badges **`3/3-Kern`** und **`Ruhige Vola`**.
  * `hermes_scanner.py` + CLI `tools/tori_candidate_preview.py`: Vollständige Umsetzung von `docs/hermes_spezifikation_tori_scanner.md` (5 Daten-Gates, 6 Pflicht-Tore, 5 Szenarien inkl. `5_FAST_A_PLUS`, 10-Punkte-Scoring, Top-10-Ranking, Markdown/CSV/JSON, optionales `--update` nach US-Börsenschluss und `--evaluate-watchlist`). Offline-Test auf dem 520er-Archiv (`2026-10-29`): 501/520 geprüft, 14 veraltet, 5 Vorlauf <320d, 0 Fehler → 36 qualifizierte Setups / Top 10 / 3 Fast-A+.
  * `tori_paper_watch.py` + CLI `tools/tori_paper_watch.py` + `radar_api.py` + Web-UI `/radar` (`static/radar.html`, `static/radar.js`, `static/radar.css`): Eigene SQLite-DB (`TORI_DATA_DIR/paper-watch/watchlist.sqlite3`), 1-Klick-Chart-Sichtprüfung, Watchlist-Übernahme (auch für Vorwarnungen kurz vor Trigger), automatische kausale Überführung in unabhängige **1.000-€-Papertrades je Aktie** (`signal_path_index` + `exit_followup` `r2_fan`/`qualified_fan`/`original_safety`, 0,3-%-Hard-Stop, 5 bps Spread + 5 bps Slippage, ehrliche `censored`-Markierung bei 5m-Lücken) und chronologisches Entwicklungs-Update-Log.
  * Proxmox-CT118-Vorlagen (noch nicht installiert): `deploy/tori-daily-radar.service` und `deploy/tori-daily-radar.timer` (23:00 Uhr `Europe/Berlin` Mo–Fr).
  * **Audit-Hinweis für CT118-Update:** Beim Zusammenführen auf `CT118` das speicheroptimierte inkrementelle Tagesupdate aus Branch `codex/incremental-daily-archive` (~163 MiB Peak-RSS statt ~586 MiB) mitnehmen.

---

## 5. Priorisierte Roadmap (Nächste Arbeitspakete)

1. **Paket 1 (Operativ / Sofort): Umbau von `tori_candidate_preview.py` (Hermes-Scanner)**
   * Umsetzung der vollständigen Spezifikation in `docs/HERMES-SCANNER-SPEZIFIKATION.md`:
     * Alte Stufen A–E entfernen; **6 harte Pflicht-Tore** einbauen (Rot `$\ge 3$` Kontakte & `$\ge 10$` Tage, Grün `$\ge 2$` Kontakte steigend ohne `both_qualified`-Zwang, Körperbruch-Prüfung mit korrekter Engine-Toleranz `body_atr = 0.05`, Konvergenz, Stop-Korridor `$2{,}0\,\%$` bis `$8{,}5\,\%$` & `$\ge 1{,}0\text{ ATR}_{4\text{h}}$`, Liquidität/Preis `$\ge 20\text{ USD}$`).
     * Umstellung von bloßer Lage (`grün < close < rot`) auf **5 operative Einstiegs-Szenarien** (`1A_CLEAN_BREAKOUT`, `1B_ARMED_WAIT_CLEAN`, `2_IMMEDIATE_TEST`, `3_APPROACH_WATCH`, `4A/4B_RETEST_RED`, plus Mini-Anhang `5_FAST_A_PLUS`). `Safety-Bounce` standardmäßig aus.
     * Neues 10-Punkte-Scoring, Berechnung von `Trigger K1/K2`, `Stop 0,3 %`, `$+2\text{R}$`-Freigabepreis, Referenz-Stückzahl (`$10.000$` Depot, `$1\,\%$` Risiko, `$25\,\%$` Cap), `TREND_FOLLOW`/`REVERSAL`-Tag und kompaktem Daten-/Earnings-Audit.
2. **Paket 2 (Forschung / Größter Radar-Hebel): Isolierter „Re-Arming“-Versuch**
   * Gezielter Folgelauf in `early_warning.py` gegen die unveränderte 512er-Referenz (`artifacts/early-warning-expanded-20261101`): Begrenzte Wiederfreigabe einer vorzeitig geschlossenen Beobachtung (`6.999` Ausbrüche / `3.629` Retests), sobald ein **echter neuer Struktur-Fortschritt** vorliegt (z. B. neuer bestätigter Kontakt oder neue Safety-Herkunft), bei exakter Messung von Erfassungsgewinn vs. zusätzlicher Tageslast.
3. **Paket 3 (Forschung / Bestehende Daten ohne neuen Lauf): Stop-Korridor-, `R`- und Monte-Carlo-Auswertung**
   * Auswertung direkt auf `artifacts/exit-followup-population-20261101/trades-by-universe.csv`: Getrennte Analyse sehr weiter Anfangsstops (`$> 8\,\%$` / `$> 10\,\%$`) und sehr enger Mini-Stops (`$< 1\,\%$`), Vergleich von risikonormiertem `Netto R` (mit Mini-Stop-Deckel) über Dow / Nasdaq-100 / S&P 500 sowie realistische Depot-Simulation (`$10.000\text{ EUR}$`, `$1\,\%$` Risiko, `$25\,\%$` Positions-Cap, Bootstrapping/Drawdown-Verteilung).
4. **Paket 4 (Forschung): Kausaler Beobachtungs- und Erstfreigabe-Scanner**
   * Eine neue Episode verbraucht ihr Entry-Ticket nicht mehr beim ersten unreifen 2-Kontakt-Signal, sondern bleibt im Beobachtungsmodus, bis Qualitätskriterien und Einstiegstrigger gleichzeitig erfüllt sind.
5. **Paket 5 (Web-UI & Livebetrieb auf Proxmox):**
   * Einbau der Vorwarn-Liste in die Web-App (Port `8877`) mit **Snapshot/Aktuell-Umschalter** und **Mute/Snooze-Buttons**.
   * Aufbau des versionierten Live-Daemons nach XNYS-Börsenkalender (inkrementeller Import, Datenalter-/Lücken-Check, DB-Versandwarteschlange, Hermes-Anbindung) sowie anschließende ergebnisblinde Beobachtung auf **neuen, unangetasteten Daten (Holdout)**.