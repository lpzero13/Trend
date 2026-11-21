"""CLI for Watchlist & isolated 1.000-EUR Papertrade tracking."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models import DataError
import tori_paper_watch as pw


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="Alle Watchlist- und Papertrade-Positionen anzeigen")
    p_list.add_argument("--archived", action="store_true")

    p_add = sub.add_parser("add", help="Symbol aus dem letzten Scan auf die Watchlist setzen")
    p_add.add_argument("--symbol", required=True)
    p_add.add_argument("--capital", type=float, default=pw.DEFAULT_CAPITAL_EUR)
    p_add.add_argument("--stop-policy", choices=pw.VALID_POLICIES, default=pw.DEFAULT_STOP_POLICY)
    p_add.add_argument("--max-watch", type=int, default=20)
    p_add.add_argument("--note", default="")

    p_eval = sub.add_parser("evaluate", help="Alle aktiven Einträge kausal aktualisieren")
    p_eval.add_argument("--asof-session", default=None, help="Optionaler historischer Stichtag YYYY-MM-DD")

    p_upd = sub.add_parser("updates", help="Chronologische Entwicklungs-Updates anzeigen")
    p_upd.add_argument("--limit", type=int, default=30)
    p_upd.add_argument("--id", default=None)

    sub.add_parser("summary", help="Gesamtbilanz aller 1.000-EUR-Einzelpositionen")

    p_arch = sub.add_parser("archive", help="Eintrag archivieren")
    p_arch.add_argument("--id", required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            result = {"items": pw.list_items(include_archived=args.archived), "summary": pw.portfolio_summary()}
        elif args.command == "add":
            scan = pw.load_latest_scan()
            if not scan:
                raise DataError("Kein gespeicherter Scan vorhanden. Zuerst tools/tori_candidate_preview.py ausführen.", 404)
            sym = args.symbol.upper().strip()
            pool = (scan.get("candidates") or []) + (scan.get("fastAPlus") or [])
            cand = next((c for c in pool if c["symbol"] == sym), None)
            if cand is None:
                raise DataError(f"{sym} nicht im letzten Scan enthalten.", 404)
            result = pw.add_candidate(
                cand,
                capital_eur=args.capital,
                stop_policy=args.stop_policy,
                max_watch_sessions=args.max_watch,
                note=args.note,
            )
        elif args.command == "evaluate":
            result = pw.evaluate_all(asof_session=args.asof_session)
        elif args.command == "updates":
            result = {"items": pw.recent_updates(limit=args.limit, item_id=args.id)}
        elif args.command == "summary":
            result = pw.portfolio_summary()
        else:
            result = pw.archive_item(args.id)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (DataError, ValueError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
