"""JSON tools for Hermes: no browser, no account or order operations."""
import argparse
import json
from pathlib import Path
import signal
import sys
import threading

import jobs
from datasets import chart_dataset, import_dataset
from models import DataError


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest="command",required=True)
    submit=commands.add_parser("submit",help="Forschungsauftrag einreichen")
    submit.add_argument("--spec",required=True)
    for name in ("status","report","events","cancel"):
        command=commands.add_parser(name)
        command.add_argument("--id",required=True)
        if name=="report":
            command.add_argument("--offset",type=int,default=0)
            command.add_argument("--limit",type=int,default=250)
        if name=="events":
            command.add_argument("--limit",type=int,default=250)
            command.add_argument("--cursor")
    commands.add_parser("list")
    commands.add_parser("health",help="Lokaler Betriebszustand ohne Providerabruf")
    commands.add_parser("storage",help="Speicherübersicht im gemeinsamen Datenordner")
    commands.add_parser("cleanup-preview",help="Nur Vorschau; keine Dateien werden gelöscht")
    backup_command=commands.add_parser("backup")
    backup_command.add_argument("--output",required=True)
    verification=commands.add_parser("verify-backup")
    verification.add_argument("--path",required=True)
    restoration=commands.add_parser("restore")
    restoration.add_argument("--backup",required=True)
    restoration.add_argument("--target",required=True)
    worker=commands.add_parser("worker")
    worker.add_argument("--once",action="store_true")
    schedule=commands.add_parser("schedule")
    schedule.add_argument("--spec",help="JSON mit enabled, interval_hours, spec; ohne Datei nur lesen")
    imported=commands.add_parser("import")
    imported.add_argument("--symbol",required=True)
    imported.add_argument("--history-days",type=int,default=900)
    analyze=commands.add_parser("analyze")
    analyze.add_argument("--dataset",required=True)
    analyze.add_argument("--asof")
    analyze.add_argument("--timeframe",choices=("1h","4h","1D"),default="4h")
    args=parser.parse_args()
    try:
        if args.command=="submit": result=jobs.submit(json.loads(Path(args.spec).read_text("utf-8-sig")))
        elif args.command=="status": result=jobs.get_job(args.id)
        elif args.command=="report": result=jobs.report(args.id,args.offset,args.limit)
        elif args.command=="events": result=jobs.events_for(args.id,args.limit,args.cursor)
        elif args.command=="health":
            from operations import status
            result=status()
        elif args.command=="storage":
            from storage import usage
            result=usage(fresh=True)
        elif args.command=="cleanup-preview":
            from storage import cleanup_preview
            result=cleanup_preview()
        elif args.command=="backup":
            from maintenance import backup
            result=backup(args.output)
        elif args.command=="verify-backup":
            from maintenance import verify
            result=verify(args.path)
        elif args.command=="restore":
            from maintenance import restore
            result=restore(args.backup,args.target)
        elif args.command=="cancel": result=jobs.cancel(args.id)
        elif args.command=="list": result=jobs.list_jobs()
        elif args.command=="schedule": result=jobs.schedule(json.loads(Path(args.spec).read_text("utf-8-sig")) if args.spec else None)
        elif args.command=="import": result={"datasetId":import_dataset(args.symbol.upper(),args.history_days)}
        elif args.command=="analyze": result=chart_dataset(args.dataset,args.timeframe,args.asof)
        else:
            stop=threading.Event()
            for name in (signal.SIGINT,signal.SIGTERM): signal.signal(name,lambda *_:stop.set())
            result={"workerAcquired":jobs.worker_loop(stop,once=args.once)}
        print(json.dumps(result,ensure_ascii=False,allow_nan=False))
    except (DataError,ValueError,OSError) as error:
        print(json.dumps({"error":str(error)},ensure_ascii=False))
        return 1
    return 0


if __name__=="__main__": sys.exit(main())
