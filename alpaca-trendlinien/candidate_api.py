"""Bounded, read-only web/Hermes access. GET never imports provider data."""
from dataclasses import asdict
from candidate_watch import identifier,objects,load_run,status,journal,read
from database import connection
from datasets import source_bars,read_dataset
from models import DataError


def one(q,k,default=''):
    values=q.get(k,[default])
    if len(values)!=1:raise DataError('Parameter mehrfach angegeben.',400)
    return values[0]


def paging(q):
    offset=int(one(q,'offset','0'));limit=int(one(q,'limit','50'))
    if offset<0 or not 1<=limit<=100:raise DataError('Ungültige Seite.',400)
    return offset,limit


def page(items,q):
    a,n=paging(q)
    return {'items':items[a:a+n],'page':{'offset':a,'limit':n,'total':len(items),'hasMore':a+n<len(items)}}


def summary(g):
    f=g['original']
    return {k:v for k,v in g.items() if k not in ('original','facts','factIds')}|{
        'contacts':f['contacts']['contacts'],'ageDays':f['contacts']['ageDays'],
        'riskATR':f['riskATRAtClose'],'riskPct':f['riskFractionAtClose']*100,
        'checks':f['checksAtClose']}


def chart(case, q, cutoff, red, green, dataset_id):
    future=one(q,'future','0')
    if future not in ('0','1'):raise DataError('future=0/1 erwartet.',400)
    rows=source_bars(read_dataset(dataset_id))['4h']
    as_of=max(b.end for b in rows) if future=='1' else cutoff
    return {'case':case,'cutoff':cutoff,'viewAsOf':as_of,'futureShown':future=='1',
            'bars':[asdict(b) for b in rows if b.end<=as_of],
            'rays':[{'role':role,'ray':ray} for role,ray in [('red',red),('green',green)] if ray is not None],
            'meaning':'Fixierte ursprüngliche 4h-Quellanker. Spätere Kurse nur nach ausdrücklicher Auswahl.'}


def get(path,q):
    route=path.removeprefix('/api/candidates/')
    if route=='runs':
        return {'items':sorted(objects('cw:run:*'),key=lambda x:x['registeredAt'],reverse=True)}
    if route=='research':
        return {'items':sorted(objects('cw:research:*',20),key=lambda x:x['createdAt'],reverse=True)}
    if route=='cash':return read('cw:cash:'+identifier(one(q,'research')),{'items':[]})
    if route=='records':
        research=identifier(one(q,'research'));a,n=paging(q)
        # Bounded SQL paging; full paths/controls never sent in list responses.
        with connection() as db:
            pattern='cw:record:'+research+':*'
            total=db.execute('SELECT count(*) FROM settings WHERE key GLOB ?',(pattern,)).fetchone()[0]
            rows=db.execute('SELECT value FROM settings WHERE key GLOB ? ORDER BY key LIMIT ? OFFSET ?',(pattern,n,a)).fetchall()
        import json
        records=[json.loads(r[0]) for r in rows]
        return {'items':[{k:r[k] for k in ('id','symbol','entryAt','phase','features')} for r in records],
                'page':{'offset':a,'limit':n,'total':total,'hasMore':a+n<total}}
    if route=='record':
        research=identifier(one(q,'research'));case=one(q,'id')
        if len(case)!=64 or any(c not in 'abcdef0123456789' for c in case):raise DataError('Ungültiger Forschungsfall.',400)
        r=read('cw:record:'+research+':'+case)
        if r is None:raise DataError('Forschungsfall fehlt.',404)
        e=r['entry'];payload=chart({'id':r['id'],'symbol':r['symbol'],'features':r['features']},q,e['signalAt'],e['red'],e['green'],r['datasetId'])
        if payload['futureShown']:payload['evaluation']={'outcomes':r['outcomes'],'naturalPaths':r['naturalPaths'],'controlSelection':r['controlSelection']}
        return payload
    run_id=identifier(one(q,'run'));load_run(run_id)
    if route=='status':return status(run_id)
    if route=='events':return journal(run_id,int(one(q,'limit','100')),one(q,'cursor',None))
    if route=='papers':
        a,n=paging(q)
        with connection() as db:
            pattern='cw:paper:'+run_id+':*'
            total=db.execute('SELECT count(*) FROM settings WHERE key GLOB ?',(pattern,)).fetchone()[0]
            rows=db.execute('SELECT value FROM settings WHERE key GLOB ? ORDER BY key LIMIT ? OFFSET ?',(pattern,n,a)).fetchall()
        import json
        return {'items':[json.loads(r[0]) for r in rows],'page':{'offset':a,'limit':n,'total':total,'hasMore':a+n<total}}
    lanes=objects('cw:lane:'+run_id+':*')
    groups=[g for s in lanes for g in s.get('groups',[])]
    if route=='cases':
        phase=one(q,'state','active');symbol=one(q,'symbol','').upper()
        if phase not in ('active','all','approaching','breakout','retest','bounce','invalid','unclear'):raise DataError('Ungültiger Zustand.',400)
        gs=[g for g in groups if (phase=='all' or g['state']==phase or phase=='active' and g['state'] not in ('invalid','unclear')) and (not symbol or symbol==g['symbol'])]
        gs.sort(key=lambda g:(-g.get('heuristicOrder',0),-g['lastFactAt'],g['symbol']))
        return {**page([summary(g) for g in gs],q),'meaning':'Heuristische Reihenfolge nach Phase und Zeitpunkt; kein erlernter Gewinn-Score.'}
    if route=='case':
        g=next((g for g in groups if g['id']==one(q,'id')),None)
        if not g:raise DataError('Kandidat fehlt.',404)
        f=g['original'];return chart(summary(g),q,f['knownAt'],f['red'],f['green'],g['datasetId'])
    raise DataError('Unbekannte Kandidatenroute.',404)
