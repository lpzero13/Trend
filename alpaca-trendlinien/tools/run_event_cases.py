"""Run resumable independent event cases on explicitly selected local datasets."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from event_case_study import build, checked, evaluate, prepare
from strategy_run_lock import study_lock
from strategy_screen import read


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root")
    parser.add_argument("--source", help="Existing local universe plan.json; no provider calls")
    parser.add_argument("--symbols", help="Comma-separated subset, otherwise all source symbols")
    parser.add_argument("--windows", help="Comma-separated source window names")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--phase", choices=("prepare", "build", "evaluate", "all"), default="all")
    args = parser.parse_args()
    def progress(value):
        print(json.dumps(value, ensure_ascii=False), flush=True)
    with study_lock(args.root):
        if args.phase in ("prepare", "all"):
            if not args.source:
                parser.error("--source required for preparation")
            plan = prepare(args.root, args.source, args.symbols.split(",") if args.symbols else None,
                           args.windows.split(",") if args.windows else None)
        else:
            plan = checked(read(Path(args.root)/"plan.json"))
        progress({"planId": plan["id"], "stocks": len(plan["symbols"]), "phase": args.phase})
        if args.phase in ("build", "all"):
            build(args.root, plan, args.workers, progress)
        if args.phase in ("evaluate", "all"):
            result = evaluate(args.root, plan)
            progress({"cases": result["cases"], "episodes": result["episodes"], "results": str(Path(args.root)/"results.json")})


if __name__ == "__main__":
    main()
