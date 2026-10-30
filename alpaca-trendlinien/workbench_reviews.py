"""Persistent blind geometry reviews in the existing backed-up settings store.

Only CLI preparation registers immutable datasets. HTTP cannot read arbitrary
paths or start a download. No future bars or trade outcomes are ever returned.
"""
from bisect import bisect_left
from copy import deepcopy
import json
import math
import re
import time

from database import connection
from datasets import digest, read_dataset, source_bars, data_kind
from models import DataError
from tori_entries import atr

VERSION='tori-workbench-reviews-1'


def key(pack,case=None):
    if not re.fullmatch(r'[a-f0-9]{32}',pack or '') or case is not None and not re.fullmatch(r'[a-f0-9]{24}',case):
        raise DataError('Ungültige Fallkennung.',400)
    return 'wb:case:'+pack+':'+case if case else 'wb:pack:'+pack


def put(db,name,value):
    db.execute('INSERT OR REPLACE INTO settings VALUES(?,?)',(name,json.dumps(value,allow_nan=False)))


def read(db,name):
    row=db.execute('SELECT value FROM settings WHERE key=?',(name,)).fetchone()
    if not row:raise DataError('Sichtprüffall nicht gefunden.',404)
    return json.loads(row[0])


def register(samples,label='Kriterien-Gesamttest und Zufallsfälle'):
    if not samples or len(samples)>200:raise DataError('1–200 Sichtprüffälle registrieren.',400)
    checked=[];cached=None
    for sample in samples:
        if cached is None or cached['id']!=sample['datasetId']:cached=read_dataset(sample['datasetId'])
        d=cached
        tf,cutoff=sample['timeframe'],sample['cutoff']
        if tf not in ('4h','1D') or type(cutoff) is not int:raise DataError('Quellintervall oder Stichtag ungültig.',400)
        known=[b for b in d['material']['bars'][tf] if b['end']<=cutoff]
        if len(known)<15 or known[-1]['end']!=cutoff:raise DataError('Stichtag benötigt eine bekannte geschlossene Quellkerze.',400)
        engine=deepcopy(sample.get('engine',{'rays':[],'resistances':[]}))
        known_times={b['time'] for b in known}
        for item in engine.get('rays',[]):
            ray=item['ray']
            if item['role'] not in ('red','green') or ray['a_time'] not in known_times or ray['b_time'] not in known_times:
                raise DataError('Engineanker müssen im bekannten Präfix liegen.',400)
        checked.append({'datasetId':d['id'],'symbol':d['material']['symbol'],'timeframe':tf,'cutoff':cutoff,
            'kind':sample.get('kind','diagnostic'),'engine':engine})
    if len({digest(s) for s in checked})!=len(checked):raise DataError('Doppelte Sichtprüffälle.',400)
    pack=digest([VERSION,checked])[:32]
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        if db.execute('SELECT 1 FROM settings WHERE key=?',(key(pack),)).fetchone():return pack
        put(db,key(pack),{'id':pack,'version':VERSION,'label':label,'count':len(checked),'createdAt':time.time(),
            'meaning':'Diagnostische Geometrieprüfung, keine Erfolgs- oder Populationstrefferquote.'})
        for s in checked:
            identity=digest([pack,s])[:24]
            put(db,key(pack,identity),{**s,'id':identity,'packId':pack,'label':None,'blindLabel':None,
                'revealed':False,'tainted':False,'revision':0})
    return pack


def packs():
    with connection() as db:
        return {'items':[json.loads(r[0]) for r in db.execute("SELECT value FROM settings WHERE key LIKE 'wb:pack:%' ORDER BY key")]}


def cases(pack,offset=0,limit=50):
    if type(offset) is not int or offset<0 or type(limit) is not int or not 1<=limit<=100:
        raise DataError('Ungültige Sichtprüfseite.',400)
    prefix=key(pack).replace('wb:pack:','wb:case:')+':'
    with connection() as db:
        db.execute('BEGIN')
        meta=read(db,key(pack))
        total=db.execute('SELECT count(*) FROM settings WHERE key LIKE ?',(prefix+'%',)).fetchone()[0]
        rows=[json.loads(r[0]) for r in db.execute('SELECT value FROM settings WHERE key LIKE ? ORDER BY key LIMIT ? OFFSET ?',(prefix+'%',limit,offset))]
    return {'pack':meta,'items':[{k:c[k] for k in ('id','symbol','timeframe','cutoff','revision','revealed','tainted')}|
        {'labelled':c['label'] is not None} for c in rows],
        'page':{'offset':offset,'limit':limit,'total':total,'hasMore':offset+len(rows)<total}}


def view(pack,case):
    with connection() as db:c=read(db,key(pack,case))
    d=read_dataset(c['datasetId'])
    known=[b for b in d['material']['bars'][c['timeframe']] if b['end']<=c['cutoff']]
    bars=known[-5000:]
    out={k:c[k] for k in ('id','packId','symbol','timeframe','cutoff','label','blindLabel','revision','revealed','tainted')}
    out.update(bars=bars,firstIndex=len(known)-len(bars),feed=d['material']['feed'],
        adjustment=d['material']['adjustment'],dataKind=data_kind(d),
        futureAvailable=False)
    if c['revealed']:out['engine']=c['engine']
    return out


def validate_label(c,value):
    if not isinstance(value,dict) or set(value)!={'revision','verdict','note','rays'} or type(value['revision']) is not int:
        raise DataError('Beurteilung benötigt Revision, Urteil, Notiz und Linien.',400)
    if value['revision']!=c['revision']:raise DataError('Fall wurde inzwischen verändert; bitte neu laden.',409)
    if value['verdict'] not in ('interesting','unclear','reject') or not isinstance(value['note'],str) or not 3<=len(value['note'].strip())<=3000:
        raise DataError('Urteil und Begründung mit 3–3000 Zeichen angeben.',400)
    if not isinstance(value['rays'],list) or len(value['rays'])>16:raise DataError('Höchstens 16 eigene Linien.',400)
    d=read_dataset(c['datasetId'])
    known={b['time'] for b in d['material']['bars'][c['timeframe']] if b['end']<=c['cutoff']}
    seen=set()
    for r in value['rays']:
        if not isinstance(r,dict) or set(r)!={'id','role','a_time','a_price','b_time','b_price','contacts'}:
            raise DataError('Linie benötigt Rolle, zwei Anker und Kontaktmarkierungen.',400)
        if not isinstance(r['id'],str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',r['id']) or r['id'] in seen:
            raise DataError('Eindeutige Linienkennung erforderlich.',400)
        seen.add(r['id'])
        if r['role'] not in ('red','green','resistance'):raise DataError('Unbekannte Linienrolle.',400)
        if any(type(r[k]) is not int or r[k] not in known for k in ('a_time','b_time')) or r['a_time']>=r['b_time']:
            raise DataError('Anker müssen abgeschlossene bekannte Quellkerzen sein.',400)
        if any(type(r[k]) not in (int,float) or not math.isfinite(r[k]) or r[k]<=0 for k in ('a_price','b_price')):
            raise DataError('Positive endliche Ankerpreise erforderlich.',400)
        if r['role']=='resistance' and r['a_price']!=r['b_price']:raise DataError('Widerstand horizontal einzeichnen.',400)
        if not isinstance(r['contacts'],list) or len(r['contacts'])>24 or any(type(t) is not int or t not in known for t in r['contacts']) or len(set(r['contacts']))!=len(r['contacts']):
            raise DataError('Kontaktmarkierungen benötigen unterschiedliche bekannte Quellkerzen.',400)
    return {k:deepcopy(value[k]) for k in ('verdict','note','rays')}


def label(pack,case,value):
    with connection() as db:
        db.execute('BEGIN IMMEDIATE');c=read(db,key(pack,case))
        new=validate_label(c,value)
        if new!=c['label']:
            c['revision']+=1;c['label']=new
            if c['revealed']:c['tainted']=True
            else:c['blindLabel']=deepcopy(new)
            put(db,'wb:history:'+pack+':'+case+':'+str(c['revision']).zfill(8),
                {'at':time.time(),'revision':c['revision'],'label':new,'afterReveal':c['revealed']})
            put(db,key(pack,case),c)
    return view(pack,case)


def reveal(pack,case,body):
    with connection() as db:
        db.execute('BEGIN IMMEDIATE');c=read(db,key(pack,case))
        if not isinstance(body,dict) or set(body)!={'revision'} or type(body['revision']) is not int or body['revision']!=c['revision']:
            raise DataError('Aktuelle Revision für Offenlegung erforderlich.',409)
        if c['label'] is None:raise DataError('Zuerst eine eigene Beurteilung speichern.',409)
        if not c['revealed']:
            c['revealed']=True;c['revealedAt']=time.time();c['revision']+=1
            put(db,key(pack,case),c)
    return view(pack,case)


def compare(pack):
    prefix=key(pack).replace('wb:pack:','wb:case:')+':'
    result=[];labels=0
    with connection() as db:
        read(db,key(pack))
        records=[json.loads(r[0]) for r in db.execute('SELECT value FROM settings WHERE key LIKE ? ORDER BY key',(prefix+'%',))]
    for c in records:
        own=c['blindLabel']
        if own is None:continue
        labels+=1
        # Aggregate projections stay hidden until that case's explicit reveal.
        if not c['revealed']:continue
        rows=source_bars(read_dataset(c['datasetId']))[c['timeframe']]
        rows=[b for b in rows if b.end<=c['cutoff']]
        times=[b.time for b in rows];last=len(rows)-1;vol=atr(rows)
        for r in own['rays']:
            a,b=bisect_left(times,r['a_time']),bisect_left(times,r['b_time'])
            slope=(r['b_price']-r['a_price'])/(b-a)
            val=lambda i:r['a_price']+slope*(i-a)
            errors=[]
            if r['role']=='resistance':
                errors=[abs(r['a_price']-p)/vol for p in c['engine'].get('resistances',[]) if vol]
            else:
                for engine in c['engine'].get('rays',[]):
                    if engine['role']!=r['role']:continue
                    p=engine['ray'];auto=lambda i:p['a_price']+p['slope']*(i-p['a_index'])
                    if vol:errors.append(max(abs(val(i)-auto(i)) for i in (last,last+20))/vol)
            violations=sum((rows[i].low<val(i)-1e-7 if r['role']=='green' else rows[i].high>val(i)+1e-7) for i in range(a,last))
            result.append({'caseId':c['id'],'role':r['role'],'humanContactMarks':len(r['contacts']),
                'maximumProjectionErrorATR':min(errors) if errors else None,
                'withinQuarterATR':min(errors)<=.25 if errors else None,'wickCrossingsBeforeLastCandle':violations,
                'lastCandleCrosses':rows[last].low<val(last)-1e-7 if r['role']=='green' else rows[last].high>val(last)+1e-7,
                'currentLabelTainted':c['tainted'],'comparisonUses':'last_saved_blind_label'})
    return {'cases':len(records),'humanLabels':labels,'revealed':sum(c['revealed'] for c in records),
        'geometry':result,'meaning':'Geometrische Übereinstimmung nach ausdrücklicher Offenlegung; keine Gewinnquote. Vorwissen des Menschen ist nicht prüfbar.'}


def get(path,query):
    if path=='/api/workbench/scans':
        from workbench_scanner import scans
        return scans()
    scan_route=re.fullmatch(r'/api/workbench/scans/([A-Za-z0-9_-]{1,64})/facts',path)
    if scan_route:
        from workbench_scanner import journal
        return journal(scan_route[1],int(query.get('limit',['100'])[0]),query.get('cursor',[None])[0])
    if path=='/api/workbench/packs':return packs()
    m=re.fullmatch(r'/api/workbench/packs/([a-f0-9]{32})(?:/([a-f0-9]{24}|compare))?',path)
    if m:
        if m[2]=='compare':return compare(m[1])
        if m[2]:return view(m[1],m[2])
        return cases(m[1],int(query.get('offset',['0'])[0]),int(query.get('limit',['50'])[0]))
    raise DataError('Unbekannte Sichtprüfroute.',404)


def post(path,body):
    m=re.fullmatch(r'/api/workbench/packs/([a-f0-9]{32})/([a-f0-9]{24})/(label|reveal)',path)
    if not m:raise DataError('Nur eigene Beurteilungen oder ausdrückliche Offenlegung speichern.',405)
    return label(m[1],m[2],body) if m[3]=='label' else reveal(m[1],m[2],body)
