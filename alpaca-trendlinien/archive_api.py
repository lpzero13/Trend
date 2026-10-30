"""Local collector control behind the server's existing origin/auth checks."""
import threading
import time

import archive_state as state
import history_fast as fast
import history_archive as legacy
import universe_catalog as universes
from database import connection
from models import DataError

_lock = threading.Lock()
_workers = {}


def legacy_jobs():
    with connection() as db:
        items = [v for _,v in state.rows(db,legacy.PREFIX)]
    return [{'id':j['id'],'status':j['status'],'name':j['spec']['universe'].get('name','Altbestand'),
             'start':j['spec']['start'],'end':j['spec']['end'],
             'finished':sum(s['status']=='completed' for s in j['stocks'].values()),
             'total':len(j['spec']['symbols'])} for j in items]


def inventory(keys, start=None, end=None):
    selection = universes.combine(keys)
    selected = set(selection['symbols'])
    existing = set()
    for file in (legacy.data_dir()/'datasets').glob('*.json'):
        try:
            import json
            m = json.loads(file.read_text('utf-8'))['material']
            if m['feed']=='sip' and m['adjustment']=='split' and m.get('normalization',{}).get('5m')==fast.NORMALIZATION:
                existing.add(m['symbol'])
        except (ValueError,KeyError,OSError): pass
    from archive_estimates import estimate
    from provider_budget import effective_budget
    return {'uniqueStocks':len(selected),'existingStocks':len(selected & existing),
            'newStocks':len(selected-existing),'meaning':'Bestandshinweis; Zeiträume, Vintage und Prüfsummen werden beim Lauf geprüft.',
            'universe':selection['universe'],'estimate':estimate(len(selected),start,end,effective_budget(190))}


def get(path, query):
    if path == '/api/archive/universes': return universes.catalog()
    if path == '/api/archive/jobs':
        summaries=[]
        for job in state.list_jobs():
            status=state.status(job['id'])
            summary={k:v for k,v in status.items() if k!='stocks'}
            summary['universe']={k:v for k,v in status['universe'].items() if k in ('name','ids')}
            summary['failures']=[{'symbol':s,'error':v.get('error')} for s,v in status['stocks'].items() if v['status'] in ('failed','unavailable')][:10]
            summaries.append(summary)
        return {'items':summaries,'legacy':legacy_jobs()}
    if path == '/api/archive/preview':
        return inventory(query.get('ids',[''])[0].split(','),query.get('start',[None])[0],query.get('end',[None])[0])
    if path.startswith('/api/archive/jobs/'):
        identity=path.rsplit('/',1)[-1]
        result=state.status(identity)
        result['localWorkerActive']=bool(identity in _workers and _workers[identity].is_alive())
        result['stale']=result['status']=='running' and time.time()-result['updatedAt']>180
        try:
            offset=max(0,int(query.get('offset',['0'])[0]));limit=max(1,min(200,int(query.get('limit',['50'])[0])))
        except (ValueError,TypeError):raise DataError('Ungültige Aktienseite.',400) from None
        result['totalStocks']=len(result['stocks']);result['offset']=offset;result['limit']=limit
        result['stocks']=dict(list(result['stocks'].items())[offset:offset+limit])
        result['universe']={k:v for k,v in result['universe'].items() if k in ('name','ids')}
        return result
    raise DataError('Unbekannte Sammlerroute.',404)


def start(identity):
    state.get(identity)
    with _lock:
        if any(t.is_alive() for t in _workers.values()): raise DataError('Ein lokaler Sammler arbeitet bereits.',409)
        with legacy.archive_lock(): pass
        state.update(identity,pauseRequested=False)
        def work():
            try:
                job=state.get(identity)
                if job['spec'].get('adopt_from') and not job.get('sourceJob'):
                    state.update(identity,phase='adopting')
                    fast.adopt(identity,job['spec']['adopt_from'])
                fast.run(identity,reset_pause=False)
            except InterruptedError:
                state.update(identity,status='paused',phase='user_paused',error=None)
            except Exception as exc:
                state.update(identity,status='failed',phase='failed',error=str(exc))
        thread=threading.Thread(target=work,daemon=True,name='tori-archive-'+identity)
        _workers[identity]=thread;thread.start()
    return {'id':identity,'started':True}


def post(path, body):
    if path == '/api/archive/universes/refresh':
        ids=body.get('ids',list(universes.DEFINITIONS))
        if not isinstance(ids,list):raise DataError('Universums-IDs müssen eine Liste sein.',400)
        for key in ids: universes.refresh(key)
        return universes.catalog()
    if path == '/api/archive/jobs':
        selection=universes.combine(body.get('universes',[]))
        spec={**selection,**{k:body[k] for k in ('start','end','workers') if k in body and body[k]}}
        source_id=body.get('adopt_from')
        if source_id:
            source=legacy.get(source_id)
            from datetime import datetime,timezone
            spec.update({k:source['spec'][k] for k in ('start','end','feed','adjustment')})
            spec['vintage']=datetime.fromtimestamp(source['createdAt'],timezone.utc).date().isoformat()
            spec['asof']=legacy.stamp(source['spec']['end']).date().isoformat()
            spec['adopt_from']=source_id
        return fast.create(spec)
    parts=path.split('/')
    if len(parts)==6 and parts[3]=='jobs':
        if parts[5]=='start':return start(parts[4])
        if parts[5]=='pause':return fast.pause(parts[4])
    raise DataError('Unbekannte Sammleraktion.',404)
