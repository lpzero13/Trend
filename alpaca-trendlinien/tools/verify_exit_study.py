"""Independent source-price/chronology/Decimal audit of paired exit results.

Does not call exit_path or summarize. Produces a fixed-cohort cross-horizon view
and a readable report; both are descriptive, never select new entry/exit rules.
"""
import argparse
from bisect import bisect_right
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from decimal import Decimal as D
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

LABELS = {"time": "Zeitablauf", "safety": "Fester Stop", "target_2r": "Stop + 2R",
          "fakeout": "Stop + Fakeout", "trailing": "Grün nachziehen",
          "resistance": "Stop + bekannter Widerstand", "tori_combined": "Tori-Kombination"}


def digest(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def near(a, b):
    assert math.isclose(float(a), float(b), rel_tol=1e-10, abs_tol=1e-8), (a, b)


def audit(contract, result, datasets):
    from models import NY
    from market_calendar import calendar
    assert result["contractHash"] == digest(contract)
    assert set(contract["cohorts"]) == {"development", "validation"}
    entries = {e["id"]: e for pool in contract["cohorts"].values() for e in pool}
    frames = {key: data["material"]["bars"] for key, data in datasets.items()}
    maps = {key: {b["time"]: b for b in data["5m"]} for key, data in frames.items()}
    costs = contract["costs"]
    c = D(str(costs["spread_bps"]))/D(20000)+D(str(costs["slippage_bps"]))/D(10000)
    fee, nominal = D(str(costs["fee_per_order"])), D(str(costs["notional"]))
    seen = set()
    green_checks = set()
    grid_cache = {}
    outcomes = Counter()
    for p in result["paths"]:
        e = entries[p["entryId"]]
        key = (p["phase"], p["entryId"], p["days"], p["model"])
        assert key not in seen
        seen.add(key)
        assert (p["profile"], p["family"], p["symbol"], p["datasetId"]) == (e["profile"], e["family"], e["symbol"], e["datasetId"])
        assert p["entryPrice"] == e["entryPrice"] and p["initialStop"] == e["initialStop"]
        data = frames[e["datasetId"]]
        fine = maps[e["datasetId"]]
        phase_end = contract["phases"][p["phase"]]["endAt"]
        local = datetime.fromtimestamp(e["entryAt"], NY)
        cal = calendar(local.year)
        days = [s for s in cal.sessions_in_range(str(local.date()+timedelta(days=1)), str(local.date()+timedelta(days=110)))]
        planned = int(cal.session_close(days[p["days"]-1]).timestamp())
        assert planned == p["plannedTimeExit"]
        grid_key = (e["entryAt"], min(planned, phase_end))
        if grid_key not in grid_cache:
            first, last = (datetime.fromtimestamp(t, NY).date() for t in grid_key)
            grid = []
            for year in range(first.year, last.year+1):
                yearcal = calendar(year)
                for session in yearcal.sessions_in_range(max(str(first), f"{year}-01-01"), min(str(last), f"{year}-12-31")):
                    start, end = int(yearcal.session_open(session).timestamp()), int(yearcal.session_close(session).timestamp())
                    grid.extend(t for t in range(start, end, 300) if grid_key[0] <= t and t+300 <= grid_key[1])
            grid_cache[grid_key] = grid
        grid = grid_cache[grid_key]
        assert fine[e["entryAt"]]["open"] == e["entryPrice"]
        buy = D(str(e["entryPrice"]))*(1+c)
        near(p["entryFill"], buy)
        near(p["initialRisk"], buy-D(str(e["initialStop"])))
        resistance=e.get("resistanceAtSignal")
        resistance=resistance if resistance and resistance>e["entryPrice"] else None
        assert p["knownResistance"]==resistance
        expected_target=(buy+2*(buy-D(str(e["initialStop"])))) if p["model"]=="target_2r" else resistance if p["model"] in ("resistance","tori_combined") else None
        if expected_target is None:
            assert p["targetPrice"] is None
        else:
            near(p["targetPrice"],expected_target)
        if p["model"] not in ("trailing","tori_combined"):
            assert not p["stopUpdates"]
        quantity = (nominal-fee)/buy
        stop = e["initialStop"]
        updates = iter(p["stopUpdates"])
        update = next(updates, None)
        four = [b for b in data["4h"] if b["end"] <= phase_end]
        ends = [b["end"] for b in four]
        fakeouts = []
        for i, b in enumerate(four):
            if e["entryAt"] < b["end"]:
                red = e["red"]
                value = red["a_price"]+red["slope"]*(i-red["a_index"])
                if b["close"] < value:
                    fakeouts.append(b["end"])
        expected_exit = None
        first_missing = None
        for stamp in grid:
            if stamp not in fine:
                first_missing = stamp
                break
            b = fine[stamp]
            while update and update["effectiveAt"] == stamp:
                known = update["knownAt"]
                assert e["entryAt"] < known and known+costs["latency_seconds"] <= stamp
                # Effective on the earliest exchange grid open after knowledge/latency.
                assert stamp == next(t for t in grid if t >= known+costs["latency_seconds"])
                ray = update["ray"]
                j = bisect_right(ends, known)-1
                assert four[j]["end"] == known
                assert stop < update["price"] < four[j]["close"]
                assert ray["b_time"] > e["green"]["b_time"]
                gkey = (e["datasetId"], known, digest(ray))
                if gkey not in green_checks:
                    a, z = ray["a_index"], ray["b_index"]
                    assert 0 <= a < z < j
                    assert four[a]["time"] == ray["a_time"] and four[z]["time"] == ray["b_time"]
                    near(four[a]["low"], ray["a_price"])
                    near(four[z]["low"], ray["b_price"])
                    near((ray["b_price"]-ray["a_price"])/(z-a), ray["slope"])
                    assert ray["slope"] > 0 and four[z+1]["low"] > four[z]["low"]
                    assert all(row["low"]+1e-7 >= ray["a_price"]+ray["slope"]*(i-a) for i, row in enumerate(four[:j+1]) if i >= a)
                    green_checks.add(gkey)
                near(update["price"], ray["a_price"]+ray["slope"]*(j-ray["a_index"])-costs["tick"])
                stop = update["price"]
                update = next(updates, None)
            available_fakeout = next((f for f in fakeouts if f+costs["latency_seconds"] <= stamp), None)
            target = p["targetPrice"]
            use_stop = p["model"] != "time"
            if use_stop and b["open"] <= stop:
                expected_exit = (stamp, b["open"], "trailing_gap" if p["stopUpdates"] and any(u["effectiveAt"] <= stamp for u in p["stopUpdates"]) else "stop_gap", False)
            elif available_fakeout and p["model"] in ("fakeout", "tori_combined"):
                expected_exit = (stamp, b["open"], "fakeout", False)
            elif target is not None and b["open"] >= target:
                expected_exit = (stamp, target, "target_at_open", False)
            elif use_stop and b["low"] <= stop:
                expected_exit = (stamp, stop, "trailing_stop" if any(u["effectiveAt"] <= stamp for u in p["stopUpdates"]) else "stop", target is not None and b["high"] >= target)
            elif target is not None and b["high"] >= target:
                expected_exit = (stamp, target, "target", False)
            elif b["end"] == planned:
                expected_exit = (stamp, b["close"], "time", False)
            if expected_exit:
                break
        if p["status"] == "closed":
            assert expected_exit is not None and update is None
            stamp, price, reason, ambiguous = expected_exit
            assert p["fillBarAt"] == stamp and p["exitAt"] == fine[stamp]["end"] <= phase_end
            near(p["exitPrice"], price)
            assert p["exitReason"] == reason and p["intrabarAmbiguous"] == ambiguous
            sell = D(str(price))*(1-c)
            pnl = quantity*(sell-buy)-2*fee
            near(p["exitFill"], sell)
            near(p["netPnl"], pnl)
            near(p["quantity"], quantity)
            near(p["netReturnPct"], pnl/nominal*100)
            near(p["netR"], pnl/(quantity*(buy-D(str(e["initialStop"])))))
            if reason == "fakeout":
                assert p["fakeoutObservedAt"] == available_fakeout
        else:
            assert expected_exit is None and p["exitFill"] is None
            if first_missing is not None:
                assert p["reason"] == "missing_fine_path" and p["missingAt"] == first_missing
            else:
                assert p["reason"] == "phase_boundary" and planned > phase_end
        outcomes[p["status"]] += 1
    assert len(seen) == sum(len(v) for v in contract["cohorts"].values())*len(contract["models"])*3
    # Independently check EVERY report row and construct one identical cohort for
    # all models AND horizons, avoiding composition changes in the final chart.
    indexed = defaultdict(list)
    for p in result["paths"]:
        indexed[(p["phase"], p["profile"], p["family"])].append(p)
    fixed_rows = []
    for row in result["rows"]:
        key = (row["phase"], row["profile"], row["family"])
        pool = indexed[key]
        one_h = [p for p in pool if p["days"] == row["days"]]
        common = Counter(p["entryId"] for p in one_h if p["status"] == "closed")
        selected = [p for p in one_h if p["model"] == row["model"] and common[p["entryId"]] == len(contract["models"])]
        assert len(selected) == row["paired"]["closed"]
        if selected:
            near(row["paired"]["meanNetPct"], statistics.mean(p["netReturnPct"] for p in selected))
            near(row["paired"]["meanPnlPer1000USD"], statistics.mean(p["netPnl"] for p in selected))
            assert row["paired"]["positive"] == sum(p["netPnl"] > 0 for p in selected)
        all_closed = Counter(p["entryId"] for p in pool if p["status"] == "closed")
        fixed = [p for p in one_h if p["model"] == row["model"] and all_closed[p["entryId"]] == len(contract["models"])*3]
        fixed_rows.append({k: row[k] for k in ("phase", "profile", "family", "days", "model")} | {
            "n": len(fixed), "positive": sum(p["netPnl"] > 0 for p in fixed),
            "meanNetPct": statistics.mean(p["netReturnPct"] for p in fixed) if fixed else None,
            "meanPnlPer1000USD": statistics.mean(p["netPnl"] for p in fixed) if fixed else None,
            "meanNetR": statistics.mean(p["netR"] for p in fixed) if fixed else None,
            "entryIds": sorted(p["entryId"] for p in fixed),
            "exitReasons": dict(Counter(p["exitReason"] for p in fixed))})
    return {"contractHash": result["contractHash"], "auditedPaths": len(seen), "statuses": dict(outcomes),
            "verifiedGreenRays": len(green_checks), "auditedRows": len(result["rows"]),
            "fixedCohortRows": fixed_rows,
            "scope": "All stored fills, missing-path/boundary states, source grid, conservative first-hit ordering, green-anchor confirmation/validity/latency, Decimal costs/PnL/R and paired aggregate means. Not provider truth or broker fills."}


def write_report(root, contract, result, verification):
    lines = ["# Ausstiegsvergleich auf eingefrorenen Einstiegen", "",
             "Stand 19.10.2026. Echte gespeicherte MSFT/AMZN/JPM/XOM/KO-Alpaca-IEX-Daten; splitbereinigt, reguläre XNYS-Sitzungen. **Explorative Ausführungssimulation, keine validierte Strategie.**", "",
             "## Testvertrag", "",
             "Zwei unveränderte Einstiegsprofile (Grundsignal und Momentum 2 aus 3), je Ausbruch, horizontale Bestätigung und Retest. Pro Profil/Familie/Aktie/Entryzeit ein vorab kanonisch bestimmtes Linienpaar. Alle sieben Ausstiege erhalten genau dessen Entry, ursprünglichen Stop und Originalanker. Keine Auswahl anhand späterer Gewinne. Mehrere Linienpaare werden nicht als mehrere unabhängige Trades gezählt.", "",
             "Entwicklung 02.05.2025–18.03.2026; bereits vorher untersuchte Validierung 19.03.–02.07.2026. Diese spätere Phase ist für die neue Exit-Forschung **kein unberührter finaler Test**. Holdout 06.07.–16.10.2026 bleibt ungeöffnet. Keine neue Schwellenwertoptimierung oder Auswahl des besten Horizonts.", "",
             "5/10/20 Handelstage zählen strikt nach dem Entrytag. Frühere Verkäufe bleiben bis zum jeweiligen Endtag als unverzinster Geldbetrag liegen; kein Wiedereinstieg innerhalb desselben Falls. Die folgenden Tabellen verwenden pro Profil/Familie/Phase dieselben Fälle über **alle Modelle und alle drei Horizonte**. Dadurch sind die drei Spalten vergleichbar. Fehlende 5m-Strecken und Phasengrenzen sind ausgeschlossen, nie als Nullgewinn eingesetzt.", "",
             "**Geldbeträge:** jeweils 1.000 USD pro unabhängig betrachteter Position, rechnerische Bruchstücke; Spread 5 Basispunkte (davon je Seite die Hälfte), Slippage 5 Basispunkte je Seite, Ordergebühr 0. Ohne Steuern, Dividenden, Finanzierung oder EUR-Umrechnung. Ein- und Ausstieg enthalten zusammen rund 0,15 % modellierte Kosten. Keine Summe dieser überlappenden Fälle als Depotgewinn ausgeben.", "",
             "## Auslegungen der Regeln", "",
             "| Modell | Getestete Regel |", "|---|---|",
             "| Zeitablauf | Kein Schutzstop; Verkauf am Schluss von Tag 5/10/20 als Referenz. |",
             "| Fester Stop | Archivierter initialStop als fester Preis; Berührung während einer 5m-Kerze löst aus. |",
             "| Stop + 2R | Derselbe Stop; Ziel = kostenbehafteter Kaufpreis + zweimal anfänglicher Preisabstand zum Stop. |",
             "| Stop + Fakeout | Fester Stop; zusätzlich erster bestätigter 4h-Schluss unter der **ursprünglich** gebrochenen roten Linie; Verkauf am ersten regulären 5m-Open frühestens fünf Minuten später. |",
             "| Grün nachziehen | Fester Stop; nach einem bestätigten späteren grünen B-Anker wird die aktuelle gültige grüne 4h-Linie am damaligen 4h-Schluss projiziert, minus 0,01 USD. Neuer fester Stoppreis wirkt frühestens fünf Minuten später und wird nur angehoben. Auch vorläufige Zwei-Kontakt-Linien sind zugelassen. |",
             "| Stop + bekannter Widerstand | Fester Stop und zum Signal gespeichertes nächstes bekanntes Widerstandsniveau oberhalb des Kaufpreises als festes Ziel; sonst kein Gewinnziel. |",
             "| Tori-Kombination | Nachziehen + bekanntes Widerstandsziel + Fakeout-Ausstieg; weiterhin ursprünglicher Schutzstop. |", "",
             "Die Tori-Zusammenfassung nennt Safety Line, spätere Pullbacks und größere/horizontale Widerstände. Auslösung, Puffer, Teilverkäufe und Fakeout-Verkauf sind dort nicht vollständig festgelegt. Die letzten Varianten sind deshalb **unsere expliziten experimentellen Auslegungen**, kein verifiziertes Originalregelwerk. Der bekannte Widerstand stammt aus dem vorhandenen kausalen Raum-Merkmal (historische Hochs und bekannte Tageslinie); Wochen-/Monatsziele werden nicht ergänzt. Eine spätere neue rote Linie wird nie rückwirkend zum Ziel. Fehlender Widerstand wird im Rohbericht separat gezählt.", "",
             "Bei Kurslücken unter einem Stop zählt das tatsächliche nächste Open. Bei gleichzeitigem Stop-/Zielkontakt in einer 5m-Kerze gilt der Stop zuerst. Ein bereits aktiver Gap-Stop geht einem gleichzeitig fälligen Fakeout-Verkauf vor. Gewinnziele erhalten bei Gaps keine bessere Ausführung als ihr Limit. Fehlende 5m-Daten beenden die Beweisbarkeit; ein bereits davor belegter Verkauf bleibt gültig.", "",
             "## Ergebnisse: dieselben Fälle über 5/10/20 Tage", ""]
    for phase in ("development", "validation"):
        for profile in ("baseline", "momentum_two"):
            for family in ("breakout", "horizontal", "retest"):
                pool = [r for r in verification["fixedCohortRows"] if (r["phase"],r["profile"],r["family"]) == (phase,profile,family)]
                n = pool[0]["n"]
                total = sum(e["profile"] == profile and e["family"] == family for e in contract["cohorts"][phase])
                lines += [f"### {phase} / {profile} / {family}: {n} vollständig von {total} Einstiegen", "",
                          "Mittleres Nettoergebnis je 1.000 USD Einsatz; in Klammern mittlere Prozentänderung. Unterschiedliche Gruppen können dieselben physischen Einstiege enthalten.", "",
                          "| Ausstieg | 5 Tage | 10 Tage | 20 Tage |", "|---|---:|---:|---:|"]
                for model in contract["models"]:
                    values=[]
                    for days in (5,10,20):
                        r=next(r for r in pool if r["model"]==model and r["days"]==days)
                        values.append(f'{r["meanPnlPer1000USD"]:+.2f} USD ({r["meanNetPct"]:+.2f} %)' if r["n"] else "—")
                    lines.append("| "+LABELS[model]+" | "+" | ".join(values)+" |")
                lines.append("")
    lines += ["## Prüfungen und Grenzen", "",
              f'Unabhängiger Preis-/Zeit-/Dezimalaudit: {verification["auditedPaths"]:,} Pfade, davon {verification["statuses"]}, {verification["verifiedGreenRays"]} verschiedene nachgezogene grüne Linien und {verification["auditedRows"]} Vergleichszeilen. Ausführliche Fallprotokolle, Einzelaktien, je Horizont verfügbare Fälle und Verlust-vor-späterem-Gewinn-Zählungen stehen in den lokalen JSON-Dateien.', "",
              "Die Tabelle bevorzugt vollständig beobachtbare Strecken; deren Datenabdeckung kann systematisch von den ausgeschlossenen Fällen abweichen. Deshalb enthält results.json daneben alle bereits sicher beendeten Fälle und die Gründe unvollständiger Pfade. Solche Gruppen mit unterschiedlicher Abdeckung sind kein fairer direkter Modellvergleich. Fälle überlappen, fünf heutige Aktien bilden kein historisches Gesamtuniversum; keine statistische Unabhängigkeit, kein Beweis für zukünftige Gewinne. IEX ist ein Teilmarkt; Ausführung und Spreads sind Annahmen. Bruchstücke und splitbereinigte Kurse sind eine normierte Forschungseinheit, keine damalige Brokerabrechnung.", "",
              "## Wiederholen", "", "Im Anwendungsordner:", "", "```text",
              "python tools/exit_study.py --source artifacts/contact-loops-20261019-a --output artifacts/exit-study-neu",
              "python tools/verify_exit_study.py --source artifacts/contact-loops-20261019-a --output artifacts/exit-study-neu",
              "```", "",
              "Ein vorhandener Ausgabeordner wird vom Lauf verweigert. Der Vertrag wird vor der Auswertung geschrieben und enthält Kohorte, Engine-Dateihashes, Ausgangsaufträge, Kosten und Phasengrenzen. Rohdaten/Verträge/Fallprotokolle bleiben lokal unter artifacts/ und werden nicht committed. Vorliegende Archivaufträge werden nur lesend geöffnet, nicht unter neuem Engine-Code fortgesetzt. Der neue CLI-Vergleich verändert keine Web- oder Worker-Standards. Kein Browser, keine neuen Providerabrufe, keine Brokerorders.", ""]
    (root/"AUSSTIEGSVERGLEICH.md").write_text("\n".join(lines), "utf-8")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",required=True)
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    source,root=Path(args.source).resolve(),Path(args.output).resolve()
    os.environ["TORI_DATA_DIR"]=str(source/"data")
    from datasets import read_dataset
    contract=json.loads((root/"contract.json").read_text("utf-8"))
    result=json.loads((root/"results.json").read_text("utf-8"))
    for name, expected in contract["engineFiles"].items():
        assert hashlib.sha256((Path(__file__).resolve().parents[1]/name).read_bytes()).hexdigest()==expected, name
    identities={e["datasetId"] for entries in contract["cohorts"].values() for e in entries}
    verification=audit(contract,result,{key:read_dataset(key) for key in identities})
    verification["verifierHash"]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (root/"verification.json").write_text(json.dumps(verification,indent=2,allow_nan=False),"utf-8")
    write_report(root,contract,result,verification)
    print(json.dumps({k:v for k,v in verification.items() if k!="fixedCohortRows"}))


if __name__=="__main__":
    main()
