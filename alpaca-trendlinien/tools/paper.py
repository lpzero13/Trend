"""Headless paper operations. Run from the application directory."""
import argparse
import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models import DataError
from paper_api import COMMANDS, trade_csv, trade_items
from paper_data import AlpacaPaper, cutoff_at, source_info
from paper_engine import Minute, bucket, normalize_plan, stamp, symbol
from paper_store import (
    advance, command, connection, create_account, draft, events, plan_preview, status, store_minutes,
)
from paper_worker import run
from settings import data_dir
from strategy_run_lock import study_lock


def json_file(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def replay(path):
    """Replay a pinned packet into an explicitly selected empty data root."""
    root = data_dir()
    if not os.environ.get("TORI_DATA_DIR") or root == Path(__file__).resolve().parents[1] / "data":
        raise DataError("Replay benötigt einen eigenen expliziten TORI_DATA_DIR.", 400)
    if root.exists() and any(root.iterdir()):
        raise DataError("Replay erwartet ein leeres Datenverzeichnis.", 409)
    data = json_file(path)
    now = stamp(data["activate_at"], "Replay-Aktivierung")
    end = stamp(data["through"], "Replay-Ende")
    if end <= now or end-now > 31*86400:
        raise DataError("Replay: höchstens 31 Tage und Ende nach Aktivierung.", 400)
    create_account(data.get("account", {}), now-1)
    for index, spec in enumerate(data["plans"]):
        current = draft({"request_id": f"offline-plan-{index}", "setup": spec}, now-1)
        preview = plan_preview(current["id"], now)
        command(current["id"], "activate", {"request_id": f"offline-activate-{index}",
                "expected_updated": current["updated"], "confirmation": preview["confirmation"]}, now)
    with study_lock(root / "paper" / "worker"):
        with connection(write=True) as db:
            for name, rows in data["bars"].items():
                ticker = symbol(name)
                bars = [Minute.parse(stamp(row["at"], "Replay-Minute"), row["ohlcv"]) for row in rows]
                if any(bar.at+60 > end or bucket(bar.at, "1D") is None for bar in bars):
                    raise DataError("Replay-Bar liegt außerhalb der ausgewählten regulären Zeit.", 400)
                store_minutes(db, ticker, bars, end)
        cursor = None
        while True:
            with connection(write=True) as db:
                current = advance(db, end, end, limit=1200)
            if current == cursor:
                break
            cursor = current
    return {"input_kind": "caller_pinned_packet", "status": status(), "events": events(limit=500)}


def cli(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for name in ("status", "run", "once"):
        sub.add_parser(name)
    account = sub.add_parser("account")
    account.add_argument("file")
    for name in ("validate", "draft", "replay"):
        p = sub.add_parser(name)
        p.add_argument("file")
    read = sub.add_parser("preview")
    read.add_argument("id")
    act = sub.add_parser("command")
    act.add_argument("id")
    act.add_argument("command", choices=sorted(COMMANDS))
    act.add_argument("file")
    journal = sub.add_parser("events")
    journal.add_argument("--after", type=int, default=0)
    journal.add_argument("--through", type=int)
    journal.add_argument("--limit", type=int, default=100)
    export = sub.add_parser("trades")
    export.add_argument("--csv", action="store_true")
    probe = sub.add_parser("probe")
    probe.add_argument("start")
    probe.add_argument("end")
    probe.add_argument("symbols", nargs="+")
    args = parser.parse_args(argv)
    action = args.action
    if action == "status":
        return status()
    if action in ("once", "run"):
        return run(once=action == "once")
    if action == "account":
        return create_account(json_file(args.file))
    if action == "validate":
        return normalize_plan(json_file(args.file), int(time.time()))
    if action == "draft":
        return draft(json_file(args.file))
    if action == "preview":
        return plan_preview(args.id)
    if action == "command":
        return command(args.id, args.command, json_file(args.file))
    if action == "events":
        return events(args.after, args.through, args.limit)
    if action == "trades":
        return trade_csv() if args.csv else trade_items()
    if action == "replay":
        return replay(args.file)
    start, end = stamp(args.start, "Start"), stamp(args.end, "Ende")
    if end > cutoff_at(int(time.time())) or not 0 < end-start <= 86400 or start % 60 or end % 60:
        raise DataError("Probe benötigt ein minutenbündiges Fenster bis 24 Stunden, mindestens 16 Minuten zurück.", 400)
    tick = time.perf_counter()
    provider = AlpacaPaper()
    rows = provider.bars(args.symbols, start, end)
    result = {"source": source_info(), "symbols": {key: len(value) for key, value in rows.items()},
              "pages": provider.pages, "attempts": provider.attempts, "seconds": time.perf_counter()-tick}
    return result


if __name__ == "__main__":
    try:
        result = cli()
        if result is not None:
            if isinstance(result, str):
                print(result, end="")
            else:
                print(json.dumps(result, ensure_ascii=False, indent=2))
    except (DataError, ValueError, OSError, KeyError, TypeError) as error:
        sys.exit(str(error) if isinstance(error, DataError) else "Ungültige Eingabe oder lokaler Paper-Datenfehler.")
