"""CLI to build the 2016-2026 Point-in-Time universe (Dow 30, Nasdaq-100, S&P 500)
and import missing historical/delisted 5m SIP bars from Alpaca.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models import DataError
import pit_membership as pm


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("build", help="Point-in-Time-Mitgliedschaftskatalog (Dow + Nasdaq-100 + S&P 500) bauen")

    p_imp = sub.add_parser("import-missing", help="Fehlende historische / delisted Ex-Mitglieder via Alpaca SIP nachladen")
    p_imp.add_argument("--workers", type=int, default=4)
    p_imp.add_argument("--limit", type=int, default=None)
    p_imp.add_argument("--retry-failed", action="store_true")

    sub.add_parser("status", help="Abdeckung aller PIT-Symbole 2016-2026 anzeigen")

    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            payload, out_path = pm.build_pit_membership()
            print(json.dumps({"file": str(out_path), "counts": payload["counts"], "range": payload["range"]}, ensure_ascii=False, indent=2))
            return 0
        if args.command == "import-missing":
            def on_prog(done, total, sym, rec):
                st = rec["status"]
                extra = f"{rec.get('firstSession')}..{rec.get('lastSession')} ({rec.get('bars4h')} 4H)" if st == "imported" else rec.get("error", "")
                print(f"[{done:3d}/{total}] {sym:6s} -> {st:14s} {extra}", file=sys.stderr, flush=True)
            audit = pm.import_missing_pit_symbols(
                workers=args.workers, limit=args.limit, retry_failed=args.retry_failed, progress=on_prog
            )
            print(json.dumps({"summary": audit["summary"], "elapsedSeconds": audit.get("elapsedSeconds")}, ensure_ascii=False, indent=2))
            return 0
        pit = pm.PitMembership.load()
        from daily_archive import inventory
        from settings import data_dir
        inv = inventory(set(pit.symbols), data_dir())
        missing = sorted(set(pit.symbols) - set(inv))
        print(json.dumps({
            "pitCounts": pit.payload["counts"],
            "locallyAvailable": len(inv),
            "missingCount": len(missing),
            "missingSample": missing[:30],
        }, ensure_ascii=False, indent=2))
        return 0
    except (DataError, ValueError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
