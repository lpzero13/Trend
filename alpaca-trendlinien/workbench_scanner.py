"""Explained, source-close-only watch facts; separate from fills and outcomes.

The original replay is unchanged. A candidate is not an order or a promise that
its planned next open exists. Immutable checkpoints reject revised prefixes.
"""
from copy import deepcopy
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import re
import time

from complete_strategy import CompleteReplay, RULES
from database import connection
from datasets import digest, read_dataset
from entry_geometry import at
from models import DataError
from tori_entries import atr
from workbench_events import calendar

VERSION='tori-explained-watch-1'


def stream_name(stream):
    if not isinstance(stream,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',stream):raise DataError('Ungültige Scannerkennung.',400)
    return stream


def journal(stream,limit=100,cursor=None):
    stream_name(stream)
    if type(limit) is not int or not 1<=limit<=500:raise DataError('1–500 Journalereignisse pro Seite.',400)
    after,through=0,None
    binding=digest([VERSION,stream])[:12]
    if cursor is not None:
        if not isinstance(cursor,str) or not re.fullmatch(r'[a-f0-9]{12}:\d{1,16}:\d{1,16}',cursor) or cursor.split(':')[0]!=binding:raise DataError('Ungültiger Journalcursor.',400)
        after,through=map(int,cursor.split(':')[1:])
        if after>through:raise DataError('Ungültiger Journalcursor.',400)
    pattern='wb:fact:'+stream+':*'
    with connection() as db:
        db.execute('BEGIN')
        row=db.execute('SELECT value FROM settings WHERE key=?',('wb:scan:'+stream,)).fetchone()
        if not row:raise DataError('Scanner nicht registriert.',404)
        if through is None:through=db.execute('SELECT coalesce(max(rowid),0) FROM settings WHERE key GLOB ?',(pattern,)).fetchone()[0]
        total=db.execute('SELECT count(*) FROM settings WHERE key GLOB ? AND rowid<=?',(pattern,through)).fetchone()[0]
        rows=db.execute('SELECT rowid,value FROM settings WHERE key GLOB ? AND rowid>? AND rowid<=? ORDER BY rowid LIMIT ?',(pattern,after,through,limit+1)).fetchall()
    more=len(rows)>limit;rows=rows[:limit]
    return {'items':[json.loads(r[1]) for r in rows],'page':{'limit':limit,'total':total,'snapshot':through,'hasMore':more,
        'nextCursor':f'{binding}:{rows[-1][0]}:{through}' if more else None}}


def scans():
    with connection() as db:
        rows=db.execute("SELECT key,value FROM settings WHERE key GLOB 'wb:scan:*' ORDER BY key LIMIT 200").fetchall()
    return {'items':[{'stream':r[0][8:],'checkpoint':json.loads(r[1])} for r in rows],
        'limit':200,'meaning':'Separate erklärte Scanner; keine automatischen Aufträge oder Nachrichten.'}


def engine_hash():
    root=Path(__file__).parent
    files={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in
        ('workbench_scanner.py','complete_strategy.py','entry_geometry.py','tori_entries.py',
         'safety_strategy.py','lab_data.py','market_calendar.py','entry_watch.py','workbench_events.py','requirements.txt')}
    return digest({'files':files,'libraries':{p:version(p) for p in ('exchange-calendars','tzdata')}})


def prefix(dataset,cutoff):
    m=dataset['material']
    return digest({**{k:v for k,v in m.items() if k!='bars'},
        'bars':{tf:[b for b in rows if b['end']<=cutoff] for tf,rows in m['bars'].items()}})


def warnings(checks):
    names={'momentum':'Momentum fehlt','safety':'Safety-Abstand groß oder ungeeignet',
           'context':'Übergeordneter Kontext ungünstig','room':'Wenig Raum zum Widerstand',
           'events':'Unternehmensereignisse'}
    return [name+(' unbekannt' if checks.get(k) is None else '') for k,name in names.items() if checks.get(k) is not True]


class ExplainedReplay(CompleteReplay):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.facts=[];self.seen=set();self.current_near=[]

    def fact(self,e,phase,i,checks):
        b=self.rows[i]
        m=self.dataset['material']
        identity=digest([VERSION,m['provider'],m['feed'],m['adjustment'],self.symbol,self.tf,
            self.model,e['candidateId'],e['greenId'],phase])
        market=self.market_checks(e,b.end,b.close)
        risk=b.close*(1+RULES['sideCost'])-e['initialStop']
        # No entry price, future fill, exit or return is present here.
        fact={'id':identity,'version':VERSION,'symbol':self.symbol,'timeframe':self.tf,
            'feed':m['feed'],'adjustment':m['adjustment'],'phase':phase,'knownAt':b.end,
            'sourceClose':b.close,'red':deepcopy(e['red']),'green':deepcopy(e['green']),
            'contacts':deepcopy(e['info']),'safetyContacts':deepcopy(e['greenInfo']),
            'initialStop':e['initialStop'],'signalATR':e['signalATR'],
            'riskFractionAtClose':risk/b.close,'riskATRAtClose':risk/e['signalATR'],
            'checksAtClose':deepcopy(checks),'warnings':warnings(checks),'marketAtClose':market,
            'meaning':'Beobachtung am Quellschluss; Ausführung und spätere Kurse unbekannt.'}
        if identity not in self.seen:
            self.facts.append(fact);self.seen.add(identity)
        return fact

    def schedule(self,signals,i):
        self.current_near=[]
        start=len(self.pending)
        super().schedule(signals,i)
        for e in self.pending[start:]:
            if e['profile']=='age7':self.fact(e,e['family'],i,e['signalChecks'])
        if self.rows[i].end<self.start_at:return
        greens=self.green_choices(i)
        if not greens:return
        b=self.rows[i];vol=atr(self.rows[max(0,i-14):i+1])
        if not vol:return
        # Proximity is a displayed watch stage, not a new entry rule. Contact
        # counts here precede this candle's contact update (conservative lag).
        for c in self.candidates:
            if not c['upper'] or not c['active'] or c['breakIndex'] is not None or c['count']<3:continue
            if not 0<=at(c['ray'],i)-b.close<=.75*vol:continue
            g=greens[0];first=min(c['ray']['a_index'],g['ray']['a_index'],max(0,i-14))
            if self.grid[i]-self.grid[first]!=i-first:continue
            if min((b.end-x['ray']['a_time'])/86400 for x in (c,g))<7:continue
            e={'candidateId':c['id'],'greenId':g['id'],'family':'approaching','signalAt':b.end,
                'red':c['ray'],'green':g['ray'],'info':self.line_info(c,i),
                'greenInfo':self.line_info(g,i),'initialStop':at(g['ray'],i)-max(.01,.25*vol),
                'signalATR':vol,'otherRedLevels':[at(x['ray'],i) for x in self.candidates if
                    x['upper'] and x['active'] and x['breakIndex'] is None and x['id']!=c['id'] and at(x['ray'],i)>b.close]}
            market=self.market_checks(e,b.end,b.close);risk=b.close*(1+RULES['sideCost'])-e['initialStop']
            checks={'three':True,'age7':True,'momentum':None,
                'safety':0<e['initialStop']<b.close and 0<risk<=2*vol and risk/b.close<=.10,
                'context':market['context'],'room':market['room'],'events':self.events.check(self.symbol,b.end)}
            self.current_near.append(self.fact(e,'approaching',i,checks))

    def run(self):
        result=super().run()
        result['watchFacts']=self.facts
        result['currentNear']=self.current_near
        return result


def scan(dataset_id,timeframe,cutoff,*,stream,from_at=None,mode='prospective',now=None,events=None):
    """Repeat safely over immutable or extended datasets, with explicit origin.

    New prospective registration cannot be backdated. Historical mode must be
    explicit and is never labelled a forward validation. No provider calls.
    """
    stream_name(stream)
    if type(cutoff) is not int or mode not in ('prospective','historical'):raise DataError('Stichtag/Modus ungültig.',400)
    now=int(time.time()) if now is None else now
    if cutoff>now:raise DataError('Stichtag liegt in der Zukunft.',400)
    d=read_dataset(dataset_id);m=d['material'];fingerprint=engine_hash();name='wb:scan:'+stream
    event_calendar=calendar(events)
    def event_prefix(at):return digest({k:sorted((r for r in rows if r['knownAt']<=at),key=digest) for k,rows in event_calendar.payload.items()})
    with connection() as db:
        row=db.execute('SELECT value FROM settings WHERE key=?',(name,)).fetchone()
    old=json.loads(row[0]) if row else None
    identity=[m['provider'],m['symbol'],m['feed'],m['adjustment'],timeframe]
    if old:
        if old['engineHash']!=fingerprint or old['identity']!=identity or old['mode']!=mode:
            raise DataError('Engine, Feed oder Modus geändert; neue Scannerkennung erforderlich.',409)
        if cutoff<old['cutoff']:raise DataError('Scanner darf nur vorwärts laufen.',409)
        if prefix(d,old['cutoff'])!=old['prefixHash']:raise DataError('Bekannte Daten revidiert; neue Generation erforderlich.',409)
        if event_prefix(old['cutoff'])!=old['eventPrefixHash']:raise DataError('Damals bekannter Kalender revidiert; neue Generation erforderlich.',409)
        if from_at is not None and from_at!=old['fromAt']:raise DataError('Registrierungsbeginn unveränderlich.',409)
        origin=old['fromAt']
    else:
        origin=now if from_at is None else from_at
        if type(origin) is not int or mode=='prospective' and origin<now:
            raise DataError('Prospektiven Beginn nicht rückdatieren; für Historie Modus historical wählen.',400)
    replay=ExplainedReplay(d,timeframe,'strict',cutoff,events=event_calendar)
    result=replay.run()
    new=[{**f,'datasetId':dataset_id,'stream':stream,'mode':mode} for f in result['watchFacts']
         if origin<=f['knownAt'] and (old is None or f['knownAt']>old['cutoff'])]
    checkpoint={'version':VERSION,'datasetId':dataset_id,'identity':identity,'engineHash':fingerprint,
        'prefixHash':prefix(d,cutoff),'cutoff':cutoff,'fromAt':origin,'mode':mode,
        'eventPrefixHash':event_prefix(cutoff),
        'events':(old['events'] if old else 0)+len(new),'updatedAt':now}
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        latest=db.execute('SELECT value FROM settings WHERE key=?',(name,)).fetchone()
        if (json.loads(latest[0]) if latest else None)!=old:raise DataError('Scanner parallel verändert; bitte wiederholen.',409)
        for f in new:db.execute('INSERT OR IGNORE INTO settings VALUES(?,?)',('wb:fact:'+stream+':'+f['id'],json.dumps(f,allow_nan=False)))
        db.execute('INSERT OR REPLACE INTO settings VALUES(?,?)',(name,json.dumps(checkpoint,allow_nan=False)))
    last_source=replay.rows[-1].end
    return {'checkpoint':checkpoint,'newFacts':new,'currentNear':result['currentNear'],
        'lastSourceClose':last_source,'sourceAgeSeconds':cutoff-last_source,
        'sourceAgeAtRunSeconds':now-last_source,'sourceAfterRegistration':last_source>=origin,
        'meaning':'Historische und prospektive Beobachtungen getrennt; currentNear nur am letzten bekannten Quellschluss, nicht automatisch aktuell. Kein Ausführungsauftrag.'}
