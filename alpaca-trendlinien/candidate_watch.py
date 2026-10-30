"""Separate frozen SIP prospective observer. Read-only provider; no broker actions."""
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import shutil
import time
import uuid

from candidate_board import VERSION, build
from candidate_data import closed_cutoff, expected_last, refresh
from complete_outcomes import Outcomes
from database import connection
from datasets import digest, read_dataset, source_bars, data_kind, stored_bytes
from complete_strategy import source_grid
from storage import reserve_bytes
from models import DataError
from settings import data_dir
from strategy_run_lock import study_lock
from workbench_reviews import put
from workbench_scanner import ExplainedReplay, engine_hash, prefix


def fingerprint():
    root=Path(__file__).parent
    return digest([engine_hash(), {p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in
        ('candidate_watch.py','candidate_board.py','candidate_data.py','complete_outcomes.py')}])


def identifier(value):
    if not isinstance(value,str) or not re.fullmatch('[a-f0-9]{32}',value):raise DataError('Ungültige Kandidatenkennung.',400)
    return value


def read(key, default=None):
    with connection() as db:row=db.execute('SELECT value FROM settings WHERE key=?',(key,)).fetchone()
    return json.loads(row[0]) if row else default


def objects(pattern,limit=200):
    with connection() as db:rows=db.execute('SELECT value FROM settings WHERE key GLOB ? ORDER BY key LIMIT ?',(pattern,limit)).fetchall()
    return [json.loads(r[0]) for r in rows]


def registration(datasets, now=None):
    now=int(time.time()) if now is None else now
    if not isinstance(datasets,dict) or not 1<=len(datasets)<=200:raise DataError('1–200 feste SIP-Datasets benötigt.',400)
    for symbol,identity in datasets.items():
        d=read_dataset(identity);m=d['material']
        if m['symbol']!=symbol or m['feed']!='sip' or m['adjustment']!='split' or data_kind(d)!='market':
            raise DataError('Registrierung verlangt echte SIP-Splitdaten mit passendem Symbol.',422)
    run={'id':uuid.uuid4().hex,'version':VERSION,'registeredAt':now,'fromAt':now,'engineHash':fingerprint(),
         'dataset_ids':dict(datasets),'status':'registered','phase':'Registriert','heartbeatAt':now,
         'pollSeconds':900,'stopRequested':False,'progress':0,'total':len(datasets),
         'importBudgetBytes':4*1024**3,
         'meaning':'Prospektive Papierbeobachtung ab Registrierung. Bestand beim Start zählt nicht als neues Signal. Keine Orders.'}
    with connection() as db:put(db,'cw:run:'+run['id'],run)
    return run


def load_run(run_id):
    r=read('cw:run:'+identifier(run_id))
    if r is None:raise DataError('Beobachter nicht registriert.',404)
    return r


def lock_path(run_id):return data_dir()/'candidates'/('worker-'+identifier(run_id))


def lock_held(run_id):
    try:
        with study_lock(lock_path(run_id)):pass
        return False
    except DataError:return True


def status(run_id,now=None):
    r=load_run(run_id);now=int(time.time()) if now is None else now
    lanes=objects('cw:lane:'+run_id+':*')
    return {**r,'workerLockHeld':lock_held(run_id),'heartbeatAgeSeconds':max(0,now-r['heartbeatAt']),
            'stalled':now-r['heartbeatAt']>max(1800,r['pollSeconds']*2),
            'addedDatasetBytes':sum(s.get('addedBytes',0) for s in lanes),
            'lanes':[{'symbol':s['symbol'],'datasetId':s['datasetId'],'asOf':s['asOf'],
                      'sourceClose':s.get('sourceClose'),'lastImportAt':s.get('lastImportAt'),
                      'error':s.get('error'),'blocked':s.get('blocked',False),
                      'groups':len(s.get('groups',[])), 'paperEntries':s.get('paperEntries',0)} for s in lanes]}


def heartbeat(run_id,**changes):
    with connection() as db:
        row=db.execute('SELECT value FROM settings WHERE key=?',('cw:run:'+run_id,)).fetchone()
        r=json.loads(row[0]);r.update(changes,heartbeatAt=int(time.time()));put(db,'cw:run:'+run_id,r)
    return r


def request_stop(run_id):
    load_run(run_id)
    return heartbeat(run_id,stopRequested=True,phase='Stop angefordert')


def evaluate(run,dataset,as_of,old=None,now=None):
    """Pure replay before the atomic commit; can be checked offline and resumed."""
    now=int(time.time()) if now is None else now
    if old and old.get('prefixHash') and (as_of<old['asOf'] or prefix(dataset,old['asOf'])!=old['prefixHash']):
        raise DataError('Bekannte Daten revidiert oder Rücksprung; neue Generation erforderlich.',409)
    symbol=dataset['material']['symbol'];identity=dataset['id']
    result=ExplainedReplay(dataset,'4h','strict',as_of).run()
    rows=[b for b in source_bars(dataset)['4h'] if b.end<=as_of]
    groups=build(result['watchFacts'],rows,as_of,old.get('groups',[]) if old else ())
    for g in groups:g['bootstrap']=g['firstKnownAt']<run['fromAt'];g['datasetId']=identity
    events=[]
    prior={g['id']:g for g in old.get('groups',[])} if old else {}
    for g in groups:
        p=prior.get(g['id'])
        if (p is None or p['state']!=g['state']) and g['asOf']>=run['fromAt']:
            # Bootstrap facts are visible, but never advertised as new entries.
            events.append({'id':digest([run['id'],g['id'],g['state'],g['asOf']]),'kind':'bootstrap' if p is None and g['bootstrap'] else 'transition',
                'candidateId':g['id'],'symbol':symbol,'state':g['state'],'knownAt':g['asOf'],
                'datasetId':identity,'bootstrap':g['bootstrap'],'reason':g['reason']})
    entries=[e for e in result['entries'] if e['profile']=='age7' and e['family']=='retest'
             and e['signalAt']>=run['fromAt'] and e['entryAt']>=run['fromAt']]
    ev=Outcomes(dataset,'4h',as_of);papers=[]
    for e in entries:
        frozen={k:v for k,v in e.items() if k not in ('paths','intermediate')}
        papers.append({'id':e['id'],'runId':run['id'],'symbol':symbol,'datasetId':identity,'entry':frozen,
                       'asOf':as_of,'paths':{m:ev.path(frozen,m) for m in ('fixed','higher_low')}})
    lane={'symbol':symbol,'datasetId':identity,'asOf':as_of,'sourceClose':rows[-1].end,
          'prefixHash':prefix(dataset,as_of),'groups':groups,'paperEntries':len(papers),
          'activePapers':sum(any(p['status']=='open' for p in x['paths'].values()) for x in papers),
          'lastImportAt':old.get('lastImportAt') if old else None,'lastCheckedAt':now,'error':None,'blocked':False}
    return lane,events,papers


def commit(run,lane,events,papers,old):
    name='cw:lane:'+run['id']+':'+lane['symbol']
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute('SELECT value FROM settings WHERE key=?',(name,)).fetchone()
        if (json.loads(row[0]) if row else None)!=old:raise DataError('Paralleler Kandidaten-Checkpoint verändert.',409)
        for p in papers:
            key='cw:paper:'+run['id']+':'+p['id'];before=db.execute('SELECT value FROM settings WHERE key=?',(key,)).fetchone()
            if before:
                before=json.loads(before[0])
                if before['entry']!=p['entry']:raise DataError('Fixierter Einstieg nachträglich verändert.',409)
                for model,path in before['paths'].items():
                    nxt=p['paths'][model]
                    if path['events']!=nxt['events'][:len(path['events'])]:raise DataError('Bekannte Stoppfolge nachträglich verändert.',409)
                    if path['status']=='closed':
                        if {k:v for k,v in path.items() if k!='outcomeId'}!={k:v for k,v in nxt.items() if k!='outcomeId'}:
                            raise DataError('Bereits abgeschlossener Papierpfad verändert.',409)
                        p['paths'][model]=path
            else:
                events.append({'id':digest([run['id'],p['id'],'entry']),'kind':'paper_entry','symbol':p['symbol'],
                    'knownAt':p['entry']['entryAt']+300,'datasetId':p['datasetId'],'paperId':p['id']})
            for model,path in p['paths'].items():
                if path['status']=='closed':events.append({'id':digest([run['id'],p['id'],model,'closed']),
                    'kind':'paper_closed','symbol':p['symbol'],'knownAt':path['fillBarAt']+300,
                    'datasetId':p['datasetId'],'paperId':p['id'],'model':model,'netR':path['netR']})
            put(db,key,p)
        for e in events:db.execute('INSERT OR IGNORE INTO settings VALUES(?,?)',('cw:event:'+run['id']+':'+e['id'],json.dumps(e,allow_nan=False)))
        put(db,name,lane)


def cycle(run_id,now=None,importer=refresh):
    run=load_run(run_id);now=int(time.time()) if now is None else now
    if run['engineHash']!=fingerprint():raise DataError('Beobachter-Engine geändert; neue Registrierung erforderlich.',409)
    cutoff=closed_cutoff(now)
    source_last=list(source_grid(cutoff-14*86400,cutoff,'4h'))[-1][1]
    for n,(symbol,identity) in enumerate(sorted(run['dataset_ids'].items())):
        if load_run(run_id)['stopRequested']:break
        heartbeat(run_id,status='running',phase='Import und Quellreplay',currentSymbol=symbol,progress=n)
        key='cw:lane:'+run_id+':'+symbol;old=read(key)
        if old and old.get('blocked'):continue
        if old and not old.get('error') and expected_last(cutoff)<=expected_last(old['asOf']):continue
        if old and not old.get('error') and not old.get('activePapers') and source_last<=old['sourceClose']:continue
        data=read_dataset(old['datasetId'] if old else identity)
        known=old['asOf'] if old else min(cutoff,max(b['end'] for b in data['material']['bars']['5m']))
        try:
            size=stored_bytes(data['id'])
            used=sum(l.get('addedBytes',0) for l in objects('cw:lane:'+run_id+':*'))
            if used+size*2>run['importBudgetBytes'] or shutil.disk_usage(data_dir()).free<reserve_bytes()+size*3:
                raise DataError('Importbudget oder Speicherreserve erreicht; keine automatische Löschung. Neue Generation nach Speicherprüfung.',507)
            # Bootstrap needs no provider call before a new source close.
            bootstrap=old is None and source_last<=max(b['end'] for b in data['material']['bars']['4h'])
            if bootstrap:
                updated,as_of=data,known
            else:updated,as_of=importer(data,known,now)
            lane,events,papers=evaluate(run,updated,as_of,old,now)
            if not bootstrap:lane['lastImportAt']=now
            lane['addedBytes']=(old.get('addedBytes',0) if old else 0)+(stored_bytes(updated['id']) if updated['id']!=data['id'] else 0)
            commit(run,lane,events,papers,old)
            if not bootstrap:heartbeat(run_id,lastSuccessfulImportAt=now)
        except (DataError,OSError,ValueError) as exc:
            blocked=isinstance(exc,DataError) and (exc.status==507 or exc.status==409 and any(w in str(exc).lower() for w in ('revidiert','revision','verändert','neue generation erforderlich')))
            lane=deepcopy(old) if old else {'symbol':symbol,'datasetId':identity,'asOf':known,'groups':[],'paperEntries':0}
            lane.update(error=str(exc),errorAt=now,blocked=blocked)
            with connection() as db:put(db,key,lane)
    r=load_run(run_id)
    return heartbeat(run_id,phase='Gestoppt' if r['stopRequested'] else 'Wartet auf neue reguläre Kerzen',
                     status='stopped' if r['stopRequested'] else 'waiting',progress=len(run['dataset_ids']),currentSymbol=None)


def worker(run_id,once=False):
    with study_lock(lock_path(run_id)):
        while True:
            try:r=cycle(run_id)
            except Exception as exc:
                heartbeat(run_id,status='blocked',phase=str(exc) if isinstance(exc,(DataError,OSError,ValueError)) else 'Interner Beobachterfehler ('+type(exc).__name__+'); Protokoll prüfen')
                raise
            if once or r['stopRequested']:return
            until=time.monotonic()+r['pollSeconds']
            while time.monotonic()<until:
                if load_run(run_id)['stopRequested']:
                    heartbeat(run_id,status='stopped',phase='Gestoppt');return
                heartbeat(run_id)
                time.sleep(min(5,max(0,until-time.monotonic())))


def journal(run_id,limit=100,cursor=None):
    identifier(run_id);load_run(run_id)
    if type(limit) is not int or not 1<=limit<=200:raise DataError('1–200 Ereignisse pro Seite.',400)
    binding=digest([VERSION,run_id])[:12];after=0;through=None
    if cursor:
        if not re.fullmatch(binding+r':\d{1,16}:\d{1,16}',cursor):raise DataError('Ungültiger Journalcursor.',400)
        _,a,t=cursor.split(':');after,through=int(a),int(t)
        if after>through:raise DataError('Ungültiger Journalcursor.',400)
    with connection() as db:
        db.execute('BEGIN');pattern='cw:event:'+run_id+':*'
        if through is None:through=db.execute('SELECT coalesce(max(rowid),0) FROM settings WHERE key GLOB ?',(pattern,)).fetchone()[0]
        rows=db.execute('SELECT rowid,value FROM settings WHERE key GLOB ? AND rowid>? AND rowid<=? ORDER BY rowid LIMIT ?',(pattern,after,through,limit+1)).fetchall()
    more=len(rows)>limit;rows=rows[:limit]
    return {'items':[json.loads(r[1]) for r in rows],'page':{'snapshot':through,'hasMore':more,
            'nextCursor':f'{binding}:{rows[-1][0]}:{through}' if more else None}}
