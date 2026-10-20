"""JSON command contract: research, replayable candidates, verification; no orders."""
from datetime import datetime
import json
from pathlib import Path
import sys

from models import DataError


def add_commands(commands):
    commands.add_parser("strategy-rules", help="Versionierte Safety-Regeln und Modellbeschreibungen")
    exported = commands.add_parser("strategy-export", help="Abgeschlossene Labor-Einstiege nur lesend exportieren")
    exported.add_argument("--job", required=True)
    exported.add_argument("--phase", choices=("development", "validation"), default="development")
    exported.add_argument("--validation-job")
    exported.add_argument("--output", required=True)
    study = commands.add_parser("strategy-study", help="Offline-Vergleich A/B/C mit fixierter Kontrollgruppe")
    study.add_argument("--entries", required=True)
    study.add_argument("--output", required=True)
    study.add_argument("--stage", choices=("development", "validation"), default="development")
    study.add_argument("--resume", action="store_true")
    for name in ("strategy-report", "strategy-verify"):
        command = commands.add_parser(name)
        command.add_argument("--study", required=True)
    scan = commands.add_parser("strategy-scan", help="Kausale Kandidaten aus lokalem Dataset; keine Brokeraktion")
    scan.add_argument("--dataset", required=True)
    scan.add_argument("--asof", required=True)
    scan.add_argument("--since")
    scan.add_argument("--history-start")
    scan.add_argument("--profile", choices=("baseline", "momentum_two"), default="momentum_two")


def timestamp(value):
    try:
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if date.tzinfo is None:
            raise ValueError()
        return int(date.timestamp())
    except (ValueError, TypeError, AttributeError):
        raise DataError("Zeitpunkt als ISO-Datum einschließlich Zeitzone angeben.", 400) from None


def execute(args):
    from safety_strategy import VERSION, MODELS, validate_rules
    from strategy_research import export_entries, run_study, scan_candidates
    if args.command == "strategy-rules":
        return {"version": VERSION, "models": list(MODELS), "rules": validate_rules(),
                "status": "research_only", "brokerOrders": False,
                "meaning": "fixed: common buffered hard stop; original: 4h original Safety close; structure: confirmed connected higher-low replacements; structure_target: additional known major resistance zone"}
    if args.command == "strategy-export":
        return export_entries(args.job, args.phase, args.output, args.validation_job)
    if args.command == "strategy-study":
        return run_study(args.entries, args.output, args.stage, args.resume,
                         progress=lambda detail: print(json.dumps(detail), file=sys.stderr, flush=True))
    if args.command == "strategy-scan":
        from datasets import read_dataset
        return scan_candidates(read_dataset(args.dataset), timestamp(args.asof), args.profile,
                               timestamp(args.since) if args.since else None,
                               timestamp(args.history_start) if args.history_start else None)
    if args.command == "strategy-verify":
        from strategy_verify import verify_study
        return verify_study(Path(args.study).resolve())
    if args.command == "strategy-report":
        root = Path(args.study).resolve()
        manifest = json.loads((root/"manifest.json").read_text("utf-8"))
        result = {"version": manifest["version"], "holdout": manifest["holdout"], "stages": {}}
        for stage in ("development", "validation"):
            path = root/(stage+".json")
            if path.exists():
                data = json.loads(path.read_text("utf-8"))
                result["stages"][stage] = {"entries": len(data["entries"]), "eligible": data["eligible"],
                    "blockedBy": data["blockedBy"], "rows": data["rows"],
                    "portfolios": [{k: v for k, v in p.items() if k not in ("trades", "equity", "skipped")} for p in data["portfolios"]]}
        decision = root/"decision-before-validation.json"
        result["decision"] = json.loads(decision.read_text("utf-8")) if decision.exists() else None
        return result
    raise DataError("Unbekanntes Strategiewerkzeug.", 400)
