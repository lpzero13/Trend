# AGENTS.md – Verbindliche Regeln & Arbeitsanweisungen für `alpaca-trendlinien`

Diese Datei ist die verbindliche Projekt-Verfassung für alle KI-Agenten (Google Antigravity, Codex, Hermes) im Repository `alpaca-trendlinien`. Lies diese Regeln vor jeder Analyse oder Codeänderung vollständig.

## 1. Projektzweck & Pflichtlektüre

* **Ziel:** Aufbau und Weiterentwicklung einer streng kausalen, deterministischen 4H-Trendlinien-Fächer-Engine (inspiriert von Tori Trades) inklusive 5m-Ausführungssimulation, lokalem Web-Replay-Viewer (Port `8877`), historischem Vorwarn-Radar (`tools/early_warning.py`) und täglichem Hermes-Kandidaten-Scanner (`tori_candidate_preview.py` auf Proxmox `CT118`).
* **Pflichtlektüre vor jedem größeren Arbeitsschritt:**
  1. Lies zuerst `docs/PROJECT_STATE.md` für den vollständigen Forschungsstand, alle Fachbegriffe, die Praxiskriterien und die priorisierte Roadmap.
  2. Lies bei allen Arbeiten am täglichen Kandidaten-Scanner oder Briefing zusätzlich `docs/HERMES-SCANNER-SPEZIFIKATION.md`.
* **Kommunikation & Arbeitsweise mit dem Nutzer:**
  * Antworte **immer auf Deutsch**.
  * Erkläre fachliche Zusammenhänge und Codeänderungen ausführlich, aber leicht verständlich.
  * Benenne bei jeder Codeänderung explizit, **welche Datei neu erstellt oder welche bestehende Datei geändert** wird.

---

## 2. Absolute „Rote Linien“ (Hard Constraints – niemals verletzen)

1. **Strenge Kausalität (`lag = 0`, kein Lookahead-Bias):**
   * Geometrie-, Signal- und Warnentscheidungen dürfen ausschließlich auf vollständig abgeschlossenen 4H-Quellkerzen und bis dahin bekannten Tageskerzen basieren.
   * Der Tages-SMA200 nutzt immer den letzten **vollständig abgeschlossenen** regulären Tagesschlusskurs, niemals den noch laufenden Signaltag.
   * Einstiege und Stop-Anpassungen erfolgen frühestens am nächsten erwarteten 5m-Open nach `$300$` Sekunden Verzögerung.
   * Im Chart-Replay und in Vorwarn-Briefings (`--asof`) dürfen niemals zukünftige Fills, Exits oder spätere Linien-Qualifikationen vorweggenommen werden. Eine zum Warnzeitpunkt bestehende 2-Kontakt-Linie (`two`) darf nicht rückwirkend als `qualified` aufgewertet werden.
2. **Ehrlicher Umgang mit Datenlücken (Niemals Ersatzkerzen erfinden):**
   * Fehlende 5m- oder 4H-Quellkerzen dürfen **niemals** interpoliert oder durch künstliche Balken aufgefüllt werden.
   * Betroffene Trade-Pfade oder laufende Beobachtungen müssen sauber als `censored` (unbekannt) markiert werden.
   * Im Live-/Tagesbetrieb müssen veraltete oder lückenhafte Daten immer explizit als Datenproblem ausgewiesen werden – niemals stillschweigend als „0 Kandidaten“ ausgeben.
3. **Unveränderlichkeit von Studien & Reproduzierbarkeit:**
   * Bestehende, verifizierte Studienordner unter `artifacts/` dürfen niemals überschrieben oder mit geänderter Engine-Logik fortgesetzt werden.
   * Jede Änderung an Engine-, Filter- oder Radar-Logik erfordert zwingend einen **neuen Studienordner** mit eigener Plan-/Code-/Dataset-Bindung.
   * Kontrollaktien (die 68 geeigneten Alttitel) müssen bei unveränderter Engine bit- bzw. zählergenau reproduzierbar bleiben.
4. **Keine ungefragten Außenaktionen & strikte Git-Hygiene:**
   * Führe ohne ausdrücklichen Auftrag **keine** Provider-/API-Abrufe (Netzwerk bleibt bei Studien/Preview gesperrt), **keine** Broker-Orders, **keine** Container-Deployments auf `CT118` und **keine** GitHub-Uploads aus.
   * Private Marktdaten, Kursbestände, Studienpläne, Artefakte, Snapshots, Detail-CSVs (`artifacts/`) und lokale Pfade unter `TORI_DATA_DIR` gehören **niemals** in Git.
   * Verwende bei allen CLI- und Serviceläufen immer dasselbe `TORI_DATA_DIR` wie der lokale Webdienst.
5. **Klare Aufgabenteilung (Python rechnet, Hermes formuliert):**
   * Alle geometrischen Berechnungen, Filter, Scores, Szenario-Zuordnungen und Stop-Werte kommen zu `$100\,\%$` deterministisch aus Python.
   * Hermes (LLM) darf nur fertige, geprüfte Ergebnisse zusammenfassen und erklären. Ein LLM-Ausfall darf die deterministische Daten- und Report-Ausgabe nicht blockieren.
6. **Kein Wechsel auf generische Backtest-Frameworks:**
   * Die bestehende Engine ist maßgeschneidert für 4H-Fächer-Geometrie, Episoden-Deduplizierung und 5m-Ausführung. Führe keine generischen Backtest-Frameworks (wie PyBroker) ein.

---

## 3. Empirisch widerlegte Hypothesen („Sackgassen-Verbot“)

Schlage folgende Ideen **nicht** erneut als harte Pflichtfilter oder „Verbesserungen“ vor – sie wurden in unseren Studien bereits auf 69 bzw. 512 Aktien widerlegt:

* **Verbot von `both_qualified` als Pflicht-Gate:** Zu verlangen, dass beim Einstieg sowohl die rote Widerstandslinie als auch die grüne Safety Line bereits `$\ge 3$` Kontakte haben, führte in `SIGNALFILTER-ERGEBNISSE-20261031.md` zu negativen Durchschnittserträgen unter allen vier Stop-Modellen (`$-0{,}69\,\%$` bis `$-0{,}09\,\%$` bei Ausbrüchen; `$-0{,}37\,\%$` bei Retests). **Regel:** Die rote Action Line muss qualifiziert sein (`$\ge 3$` Kontakte), für die grüne Safety Line genügen beim Einstieg `$2$` bestätigte Kontakte.
* **Verbot von `SMA200` als hartem Ausschlussfilter für Ausbrüche:** Direkte Ausbrüche *unterhalb* des Tages-SMA200 (frühe Trendwenden) schnitten in der Filterstudie besser ab als oberhalb (`$+1{,}17\,\%$` vs. `$+0{,}07\,\%$` unter aktueller Safety; `$+5{,}18\,\%$` vs. `$+1{,}10\,\%$` unter ursprünglicher Safety). **Regel:** Tages-SMA200 nur als Kontext-Etikett (`TREND_FOLLOW` vs. `REVERSAL`) ausweisen, niemals direkte Ausbrüche pauschal ausschließen.
* **Verbot von `active` und `compression` als harten Vorwarn-Sperren:** Im 512-Aktien-Vorwarnlauf (`EARLY-WARNING-512-ERGEBNISSE-20261101.md`) senkten diese Pflichtbedingungen die Ausbruchs-Erfassung von `$49{,}7\,\%$` auf `$38{,}8\,\%$` (`active`) bzw. `$35{,}8\,\%$` (`combined`), ohne die Bestätigungsquote (`$47{,}1\,\%$` bis `$48{,}4\,\%$`) zu verbessern. Beim roten Retest fiel die Erfassung durch `active` sogar auf `$7{,}7\,\%$`. **Regel:** Primär als Beschreibungs- und Sortiermerkmale nutzen (Ausnahme: kombinierte Dynamik-Anforderung ausschließlich im weiteren Vorwarnkorb `$0{,}40$` bis `$0{,}85\text{ ATR}$` des täglichen Briefings gemäß `docs/HERMES-SCANNER-SPEZIFIKATION.md`).
* **Kein Hochpriorisieren von `Safety-Bounce`:** Auf 512 Aktien (`BACKTEST-UNIVERSEN-ERGEBNISSE-20261101.md`) war `Safety-Bounce` auf gemeinsamen Fällen unter allen vier Stop-Modellen negativ (`$-0{,}02\,\%$` bis `$-0{,}19\,\%$`) und hatte im Radar einen Median-Vorlauf von `$0{,}0$` Kerzen bis zur ersten Berührung. **Regel:** In der Forschung als getrennte Familie dokumentieren, im operativen Tages-Briefing standardmäßig deaktivieren.
* **Kein blindes Stapeln aller Strukturfilter (`strict`):** Die strenge Kombination aller Filter reduzierte die 69er-Studie auf 206 Fälle, lieferte aber unter allen vier Stop-Modellen negative Mittelwerte (`$-1{,}54\,\%$` bis `$-0{,}29\,\%$`).
* **Keine Übernahme historischer Gewinnerlisten als Handelsregel:** Alle bisherigen Studien nutzen heutige ETF-Bestände (Survivorship-Bias) und bereits mehrfach ausgewertete Zeitfenster (`2018`, `2021`, `2023`, `2025-2026`). Eine echte Strategiebestätigung benötigt unangetastete Daten (Holdout).

---

## 4. Qualitätssicherung & Pflicht-Checks nach Änderungen

Vor dem Abschluss jeder technischen Änderung müssen die relevanten lokalen Prüfungen erfolgreich durchlaufen:

1. **Standard-Testsuite:** Bestehende Python-Tests (586+ Tests) und relevante JS-Tests (104+ Tests) ausführen.
2. **Bei Änderungen an `early_warning.py`:** Unabhängigen Nachrechner (`tools/verify_early_warning.py`) sowie den Kausalitäts-Präfixtest (`tools/verify_warning_prefix.py`) gegen synthetische Zukunftsschocks ausführen.
3. **Bei Änderungen an Backtest-/Auswertungs-Tools:** Unabhängige 5m-Pfad-Nachrechnung und CSV-Aggregationsprüfung durchführen; unveränderte Kontrollfälle gegen Referenz abgleichen.
4. **Doku-Pflege:** Am Ende jeder größeren Arbeitssitzung `docs/PROJECT_STATE.md` um den neuen Stand, ausgeführte Prüfungen und offene Punkte aktualisieren.