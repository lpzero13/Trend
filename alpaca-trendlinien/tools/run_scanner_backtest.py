"""CLI for the multi-year causal scanner feature-comparison backtest (Weg B).

Examples (run from alpaca-trendlinien/):
  Full 520-stock study (resumable, 4 workers):
    python tools/run_scanner_backtest.py run --output artifacts/scanner-backtest-20261121 --workers 4
  Generate / refresh feature-comparison report (holdout stays locked by default):
    python tools/run_scanner_backtest.py report --output artifacts/scanner-backtest-20261121
  Check progress:
    python tools/run_scanner_backtest.py status --output artifacts/scanner-backtest-20261121
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models import DataError
import scanner_backtest as sb


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="Kausalen Mehrjahres-Backtest starten oder fortsetzen")
    p_run.add_argument("--output", required=True, help="Privater Studienordner (z. B. artifacts/scanner-backtest-YYYYMMDD)")
    p_run.add_argument("--universe", choices=("all", "dow30", "nasdaq100", "sp500"), default="all")
    p_run.add_argument("--symbols", nargs="+", default=None, help="Optional: nur ausgewählte Symbole für Kurztests")
    p_run.add_argument("--workers", type=int, default=4, help="Parallele Prozesse (Default: 4)")
    p_run.add_argument("--capital", type=float, default=1000.0, help="Separates Kapital pro Trade in EUR (Default: 1000)")
    p_run.add_argument("--outcome-cutoff", default=sb.DEFAULT_OUTCOME_CUTOFF, help="Nachbeobachtungsende YYYY-MM-DD")
    p_run.add_argument(
        "--pit-membership",
        nargs="?",
        const="auto",
        default=None,
        help="Point-in-Time-Mitgliedschaft (2016-2026) aktivieren (Default-Pfad bei Flag ohne Argument: auto).",
    )
    p_run.add_argument("--no-resume", action="store_true", help="Bereits fertige Blöcke nicht überspringen")
    p_run.add_argument("--no-report", action="store_true", help="Nach dem Lauf keinen Report erstellen")
    p_run.add_argument("--policy", choices=sb.STOP_POLICIES, default="r2_fan")
    p_run.add_argument("--quiet", action="store_true")

    p_rep = sub.add_parser("report", help="Kriterien-Vergleich (report.md + CSVs) erzeugen")
    p_rep.add_argument("--output", required=True)
    p_rep.add_argument("--policy", choices=sb.STOP_POLICIES, default="r2_fan")
    p_rep.add_argument(
        "--reveal-holdout",
        action="store_true",
        default=False,
        help="Gesperrten Holdout-Zeitraum für die einmalige Gegenprobe mit ausgeben.",
    )

    p_st = sub.add_parser("status", help="Fortschritt eines Backtest-Ordners prüfen")
    p_st.add_argument("--output", required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "status":
            out = Path(args.output)
            plan = sb._load_plan(out, verify_engine=False)
            if plan is None:
                raise DataError(f"Kein plan.json unter {out} gefunden.", 404)
            done = sum(1 for s in plan["symbols"] if (out / "blocks" / f"{s}.json").is_file())
            result = {
                "planId": plan["id"],
                "outputDir": str(out),
                "doneSymbols": done,
                "totalSymbols": len(plan["symbols"]),
                "remainingSymbols": len(plan["symbols"]) - done,
                "splits": plan["splits"],
                "outcomeCutoffSession": plan["outcomeCutoffSession"],
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

        if args.command == "run":
            def on_progress(done, total, sym, status, trades, sec):
                if not args.quiet:
                    print(
                        f"[{done:3d}/{total}] {sym:6s} -> {status:6s} | {trades:3d} Einstiege | {sec:5.1f}s",
                        file=sys.stderr,
                        flush=True,
                    )

            run_res = sb.run_study(
                args.output,
                universe=args.universe,
                symbols=args.symbols,
                outcome_cutoff=args.outcome_cutoff,
                capital_eur=args.capital,
                pit_membership_path=args.pit_membership,
                workers=args.workers,
                resume=not args.no_resume,
                progress=on_progress,
            )
            output = {"run": run_res}
            if not args.no_report:
                output["report"] = sb.build_report(args.output, policy=args.policy, reveal_holdout=False)
            print(json.dumps(output, ensure_ascii=False, indent=2))
            return 0

        rep_res = sb.build_report(args.output, policy=args.policy, reveal_holdout=args.reveal_holdout)
        print(json.dumps(rep_res, ensure_ascii=False, indent=2))
        return 0
    except (DataError, ValueError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
