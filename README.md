# Trend · Tori Market Lab

Weboberfläche für die manuelle Aktienanalyse und Hintergrunddienst für reproduzierbare Long-Ereignisstudien mit automatischen Trendlinien.

**Repository:** <https://github.com/lpzero13/Trend> · **Anwendung:** [`alpaca-trendlinien/`](alpaca-trendlinien/)

## Einstieg für Hermes

**Zuerst [`HERMES.md`](HERMES.md) lesen.** Dort stehen das langfristige Ziel, bereits implementierte Funktionen, offene Arbeiten, die Linux-/Proxmox-Installation, Betrieb, Datenhaltung, Update-/Backup-Verfahren und die Grenzen der Ergebnisse.

Weitere Dokumentation:

- [Bedienung der Chartoberfläche](alpaca-trendlinien/README.md)
- [Forschungsmethode und JSON-Werkzeuge](alpaca-trendlinien/FORSCHUNG.md)
- [Long-Kriterien als Diskussionsentwurf](alpaca-trendlinien/LONG-KRITERIEN-ENTWURF.md)
- [Ursprünglicher Architekturplan V2/V3](alpaca-trendlinien/ARCHITEKTUR-V2-V3.md)
- [Prüfprotokoll und bekannte Grenzen](alpaca-trendlinien/VERIFICATION.md)
- [Vorlage für Hermes als Auftraggeber/Auswerter](alpaca-trendlinien/integrations/hermes/SKILL.md)

## Aktueller Stand

Die manuelle Webansicht unter `/` und die Forschungsansicht unter `/research` sind implementiert. Ein Python-Worker bearbeitet gespeicherte Aufträge ohne offenen Browser. Zufällige historische Startpunkte, Ausbruch-/Retest-Varianten, unveränderliche Datasets, eine dauerhafte Queue und JSON-Schnittstellen sind vorhanden.

Alpaca IEX ist die technische Testquelle. EODHD für europäische Aktien ist geplant, noch nicht implementiert. Ergebnisse sind explorative Kursbeobachtungen, kein vollständiger Portfolio-Backtest. Es gibt keine Brokerorders. Ein echter Proxmox-Containerbetrieb ist vorbereitet, aber noch nicht als installiert und abgenommen bestätigt.

## Lokal unter Windows starten

Python 3.11+ vorausgesetzt:

```powershell
cd alpaca-trendlinien
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Alpaca-Zugang ausschließlich lokal über `APCA_API_KEY_ID` und `APCA_API_SECRET_KEY` oder eine externe Credential-Datei konfigurieren; siehe [Anwendungs-README](alpaca-trendlinien/README.md). Anschließend:

```powershell
.\Start-Tori.ps1
```

Chart: <http://127.0.0.1:8765/> · Forschung: <http://127.0.0.1:8765/research>

**Startverhalten:** Beim ersten normalen Serverstart wird standardmäßig ein täglicher Forschungsauftrag für MSFT/AMZN mit zehn Starts je Aktie eingerichtet. Ein gespeicherter Zeitplan bleibt erhalten. Wer zunächst nur prüfen möchte, setzt vor dem allerersten Start `TORI_AUTO_ENABLED=0`; das pausiert keinen bereits gespeicherten Zeitplan.

## Tests

Aus `alpaca-trendlinien/` mit eingerichteter Python-Umgebung:

```text
python -m unittest discover -s tests -q
node --test tests/test_geometry.cjs tests/test_snapshot_view.cjs tests/test_measurements.cjs
```

Node.js wird für diese zusätzlichen Tests benötigt, nicht für den Anwendungsbetrieb. GitHub Actions führt die Tests auf Linux und Windows aus, ohne Alpaca-Zugangsdaten. Der lokale Ausgangsstand wurde mit 61 Python- und 21 JavaScript-Tests geprüft.

## Was nicht im Repository liegt

Zugangsdaten, lokale Konfiguration, Kursdaten, Datasets, Datenbanken, Snapshots, Logs, virtuelle Umgebungen und lokale Screenshots/Prüfartefakte werden nicht hochgeladen. Ein frischer Clone enthält den Code und Testfixtures; Marktdaten müssen vor Ort importiert oder aus einem eigenen Backup übernommen werden.

Die gebündelte Chartbibliothek liegt mit Apache-2.0-Lizenz und Attribution unter [`static/vendor/`](alpaca-trendlinien/static/vendor/). Eine eigene öffentliche Nutzungslizenz für den übrigen Projektcode wurde bisher nicht festgelegt.
