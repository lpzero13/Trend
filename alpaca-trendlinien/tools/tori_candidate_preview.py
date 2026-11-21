"""CLI for the deterministic daily Tori candidate scanner (Hermes / Proxmox CT118).

Default mode is strictly offline (reads local SIP datasets in TORI_DATA_DIR).
Pass --update to run daily_archive.update() after US market close first.
Pass --evaluate-watchlist to also update all Watchlist & 1.000-EUR papertrades.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hermes_scanner import TIER_LABELS, render_markdown, scan_universe, write_outputs
from models import DataError
import tori_paper_watch as pw


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario",
        choices=("all", "breakout", "immediate", "approach", "retest", "fast_a"),
        default="all",
        help="Nur bestimmte Einstiegs-Szenarien ausgeben (Default: all).",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=0,
        help="Mindest-Score 0..10 (Default: 0).",
    )
    parser.add_argument(
        "--universe",
        choices=("all", "nasdaq100", "sp500", "dow30"),
        default="all",
        help="Aktien-Universum (Default: all = dow30 + nasdaq100 + sp500).",
    )
    parser.add_argument(
        "--include-safety-bounce",
        action="store_true",
        default=False,
        help="Forschungsoption: Safety-Bounce zusätzlich aktivieren (Standard: aus).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Anzahl der Top-Kandidaten für die Sofort-Übersicht (Default: 10).",
    )
    parser.add_argument(
        "--session",
        default="auto",
        help="Zielsitzung: 'auto' (letzte abgeschlossene US-Sitzung), 'latest' (neuester lokaler Archivtag) oder YYYY-MM-DD.",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        default=False,
        help="Vor dem Scan das tägliche SIP-Kursupdate nach US-Börsenschluss ausführen.",
    )
    parser.add_argument(
        "--update-workers",
        type=int,
        default=2,
        help="Parallele Worker für --update (Default: 2).",
    )
    parser.add_argument(
        "--evaluate-watchlist",
        action="store_true",
        default=False,
        help="Nach dem Scan auch alle aktiven Watchlist- & 1.000-EUR-Papertrades aktualisieren.",
    )
    parser.add_argument(
        "--earnings-file",
        default=None,
        help="Optionale lokale JSON/CSV-Datei mit Earnings-Terminen (offline).",
    )
    parser.add_argument("--md-out", default=None, help="Pfad für Markdown-Report.")
    parser.add_argument("--csv-out", default=None, help="Pfad für CSV-Datei.")
    parser.add_argument("--json-out", default=None, help="Pfad für ranked-candidates.json.")
    parser.add_argument(
        "--no-store-latest",
        action="store_true",
        default=False,
        help="Ergebnis nicht als latest-scan.json für das Web-UI speichern.",
    )
    parser.add_argument(
        "--print-markdown",
        action="store_true",
        default=False,
        help="Markdown-Report direkt auf stdout ausgeben statt kompaktem JSON.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args(argv)
    try:
        update_report = None
        if args.update:
            from daily_archive import update as archive_update
            keys = ("dow30", "nasdaq100", "sp500") if args.universe == "all" else (args.universe,)
            update_report = archive_update(keys=keys, workers=args.update_workers, extra_symbols=("SPY", "QQQ"))

        report = scan_universe(
            universe=args.universe,
            session=args.session,
            scenario=args.scenario,
            min_score=args.min_score,
            top_n=args.top,
            include_safety_bounce=args.include_safety_bounce,
            earnings_file=args.earnings_file,
        )
        if update_report is not None:
            report["dataUpdate"] = {
                "targetSession": update_report.get("targetSession"),
                "counts": update_report.get("counts"),
                "behindTarget": update_report.get("behindTarget"),
                "alpaca": update_report.get("alpaca"),
            }

        written = write_outputs(
            report,
            md_out=args.md_out,
            csv_out=args.csv_out,
            json_out=args.json_out,
            store_latest=not args.no_store_latest,
        )

        watch_report = None
        if args.evaluate_watchlist:
            watch_report = pw.evaluate_all()

        if args.print_markdown:
            print(render_markdown(report))
        else:
            output = {
                "version": report["version"],
                "session": report["session"],
                "elapsedSeconds": report["elapsedSeconds"],
                "marketRegime": report.get("marketRegime"),
                "counts": report["counts"],
                "audit": report["audit"],
                "top10": [
                    {
                        "rank": i + 1,
                        "symbol": c["symbol"],
                        "tier": c.get("signal_tier", "BASIS"),
                        "tier_label": TIER_LABELS.get(c.get("signal_tier", "BASIS"), c.get("signal_tier", "BASIS")),
                        "scenario": c["scenario"],
                        "score": c["score"],
                        "close_4h": c["close_4h"],
                        "clean_trigger_next1": c["clean_trigger_next1"],
                        "stop_0_3_pct": c["stop_0_3_pct"],
                        "risk_pct": c["risk_pct"],
                        "risk_atr": c["risk_atr"],
                        "atr_1d_pct": c.get("atr_1d_pct"),
                        "low_daily_volatility": c.get("low_daily_volatility"),
                        "active_approach": c.get("active_approach"),
                        "high_maturity": bool((c.get("red_age_days") or 0) >= 21.0 or (c.get("red_contacts") or 0) >= 4),
                        "quality_core": c.get("quality_core"),
                        "red_contacts": c.get("red_contacts"),
                        "red_age_days": c.get("red_age_days"),
                        "target_plus_2r_price": c["target_plus_2r_price"],
                        "strategy_tag": c["strategy_tag"],
                        "chart_path": c["chart_path"],
                    }
                    for i, c in enumerate(report["top10"])
                ],
                "written": written,
            }
            if watch_report is not None:
                output["watchlistEvaluation"] = watch_report
            print(json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (DataError, ValueError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
