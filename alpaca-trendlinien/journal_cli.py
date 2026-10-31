"""Explicit headless journal commands; the web chart and personal drawings are untouched."""
import json
from pathlib import Path

from models import DataError


def add_commands(commands):
    init = commands.add_parser('journal-init',help='Signaljournal ausdrücklich als Replay oder prospektiv anlegen')
    init.add_argument('--name',required=True);init.add_argument('--datasets',required=True)
    init.add_argument('--start',required=True);init.add_argument('--mode',choices=('replay','prospective'),default='replay')
    tick = commands.add_parser('journal-advance',help='Eine abgeschlossene 4h-Kerze oder bis zu einem Zeitpunkt beobachten')
    tick.add_argument('--name',required=True);tick.add_argument('--datasets')
    choice = tick.add_mutually_exclusive_group(required=True);choice.add_argument('--step',action='store_true');choice.add_argument('--asof')
    status = commands.add_parser('journal-status',help='Journalstatus und begrenzte Ereignisse ohne Datenabruf')
    status.add_argument('--name',required=True);status.add_argument('--after',type=int,default=0);status.add_argument('--limit',type=int,default=100)
    status.add_argument('--upper-seq',type=int,help='Obergrenze der ersten Seite für konsistente weitere Seiten')


def _timestamp(value):
    from datetime import datetime
    try:
        d = datetime.fromisoformat(value.replace('Z','+00:00'))
        if d.tzinfo is None:raise ValueError('timezone required')
        return int(d.timestamp())
    except (ValueError,TypeError):raise DataError('Journalzeit braucht ISO-Datum mit Zeitzone.',400) from None


def execute(args):
    from signal_journal import state_path,initialize,advance,status
    path = state_path(args.name)
    if args.command=='journal-init':
        return initialize(path,json.loads(Path(args.datasets).read_text('utf-8-sig')),_timestamp(args.start),mode=args.mode)
    if args.command=='journal-advance':
        ids = json.loads(Path(args.datasets).read_text('utf-8-sig')) if args.datasets else None
        return advance(path,datasets=ids,as_of=_timestamp(args.asof) if args.asof else None,step=args.step)
    return status(path,after=args.after,limit=args.limit,upper_seq=args.upper_seq)
