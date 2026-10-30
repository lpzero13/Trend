"""Headless archive commands for Hermes, using the application's data directory."""
import json
from pathlib import Path
import signal
import threading


def add_commands(commands):
    create = commands.add_parser('archive-create', help='Historischen Sammelauftrag mit eingefrorenem Universum anlegen')
    choice = create.add_mutually_exclusive_group(required=True)
    choice.add_argument('--spec')
    choice.add_argument('--universes', help='IDs kommasepariert; zuerst archive-universes --refresh all')
    create.add_argument('--start', default='2016-01-01T00:00:00Z')
    create.add_argument('--end')
    create.add_argument('--workers', type=int, default=8)
    create.add_argument('--adopt-from',help='Übernimmt nach Prüfung einen v1-Bestand; ursprünglicher Stichtag bleibt erhalten')
    for name in ('archive-run', 'archive-status', 'archive-pause'):
        command = commands.add_parser(name)
        command.add_argument('--id', required=True)
    adopt = commands.add_parser('archive-adopt')
    adopt.add_argument('--id', required=True); adopt.add_argument('--source', required=True)
    commands.add_parser('archive-list')
    universe = commands.add_parser('archive-universes')
    universe.add_argument('--refresh', help='Universums-ID oder all; lädt nur Listen, keine Kursdaten')
    estimate=commands.add_parser('archive-estimate',help='Offline-Hochrechnung für deduplizierte Universen')
    estimate.add_argument('--universes',required=True)
    estimate.add_argument('--start',default='2016-01-01T00:00:00Z')
    estimate.add_argument('--end')


def execute(args):
    import history_archive as archive
    import history_fast as fast
    import archive_state as state
    import universe_catalog as universes
    if args.command == 'archive-universes':
        if args.refresh:
            keys = list(universes.DEFINITIONS) if args.refresh == 'all' else [args.refresh]
            for key in keys: universes.refresh(key)
        return universes.catalog()
    if args.command == 'archive-list':
        from archive_api import legacy_jobs
        return {'items': [{k:v for k,v in j.items() if k!='spec'} for j in state.list_jobs()], 'legacy':legacy_jobs()}
    if args.command == 'archive-estimate':
        from archive_estimates import estimate
        from provider_budget import effective_budget
        selected=universes.combine(args.universes.split(','))
        return {'universe':selected['universe']['name'],**estimate(len(selected['symbols']),args.start,args.end,effective_budget(190))}
    if args.command == 'archive-create':
        spec = json.loads(Path(args.spec).read_text('utf-8-sig')) if args.spec else {
            **universes.combine(args.universes.split(',')), 'start': args.start, 'workers': args.workers,
            **({'end': args.end} if args.end else {})}
        if args.adopt_from:
            from datetime import datetime,timezone
            source=archive.get(args.adopt_from)
            spec.update({k:source['spec'][k] for k in ('start','end','feed','adjustment')})
            spec['vintage']=datetime.fromtimestamp(source['createdAt'],timezone.utc).date().isoformat()
            spec['asof']=archive.stamp(source['spec']['end']).date().isoformat()
            spec['adopt_from']=args.adopt_from
        return fast.create(spec)
    if args.command == 'archive-adopt': return fast.adopt(args.id, args.source)
    if args.command == 'archive-pause': return fast.pause(args.id)
    if args.command == 'archive-status':
        return state.status(args.id) if state.exists(args.id) else archive.status(args.id)
    stop = threading.Event()
    for name in (signal.SIGINT, signal.SIGTERM):
        signal.signal(name, lambda *_: stop.set())
    if state.exists(args.id):
        job=state.get(args.id)
        if job['spec'].get('adopt_from') and not job.get('sourceJob'):
            state.update(args.id,pauseRequested=False)
            fast.adopt(args.id,job['spec']['adopt_from'])
        return fast.run(args.id, stop)
    archive.run(args.id, stop)
    return archive.status(args.id)
