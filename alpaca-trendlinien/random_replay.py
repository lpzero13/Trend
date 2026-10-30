"""Outcome-blind manual replay over immutable local market datasets. No provider calls."""
from bisect import bisect_left, bisect_right
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import secrets
import time
import uuid

from analysis_service import build_chart
from database import connection
from datasets import read_dataset, source_bars, data_kind
from models import DataError, NY
from settings import data_dir
from weekly_chart import CHART_TIMEFRAMES,add_weekly,weeks

VERSION='random-manual-1'
_cached = {'stamp':None,'groups':{}}


def candidates():
    """Cheap header hints only. The selected file is always checksum-validated.

    Existing immutable dataset files put material metadata before bars. Hints
    never reach the chart and never bypass the full selected dataset validation.
    """
    folder=data_dir()/'datasets';paths=sorted(folder.glob('*.json'))
    stamp=(str(folder),tuple((p.name,p.stat().st_size,p.stat().st_mtime_ns) for p in paths))
    if stamp==_cached['stamp']:return {s:list(v) for s,v in _cached['groups'].items()}
    groups={}
    for p in paths:
        if not re.fullmatch('[a-f0-9]{64}',p.stem):continue
        try:
            with p.open(encoding='utf-8') as stream:header=stream.read(8192)
            before,sep,_=header.partition('"bars":')
            if not sep:continue
            material=json.loads(before+'"bars":{}}}')['material']
            symbol=material['symbol']
            if not re.fullmatch(r'[A-Z][A-Z0-9./-]{0,29}',symbol):continue
            if material.get('provider')!='Alpaca':continue
            score=(material.get('feed')=='sip',material.get('adjustment')=='split',p.stat().st_mtime_ns,p.stem)
            groups.setdefault(symbol,[]).append((score,p.stem))
        except (OSError,ValueError,KeyError,TypeError):continue
    groups={s:[identity for _,identity in sorted(v,reverse=True)] for s,v in groups.items()}
    _cached.update(stamp=stamp,groups=groups)
    return {s:list(v) for s,v in groups.items()}


def eligible(dataset,now=None):
    if data_kind(dataset)!='market':raise DataError('Zufall verwendet ausschließlich echte Marktdaten.',422)
    now=int(time.time()) if now is None else now
    frames={tf:[b for b in rows if b.end<=now-900] for tf,rows in source_bars(dataset).items() if tf in ('1h','4h','1D')}
    if set(frames)!={'1h','4h','1D'} or len(frames['1D'])<81 or any(len(r)<3 for r in frames.values()):
        raise DataError('Benötigt 60 vergangene und mindestens 20 weitere gespeicherte Handelstage.',422)
    first,last=frames['1D'][59].end,frames['1D'][-21].end
    choices=[b.end for b in frames['4h'] if first<=b.end<=last]
    if not choices:raise DataError('Kein geeigneter historischer Zeitpunkt im Dataset.',422)
    return frames,choices


def create(*,rng=None,now=None):
    rng=rng or secrets.SystemRandom();pool=candidates()
    while pool:
        symbol=rng.choice(sorted(pool));identities=pool.pop(symbol)
        for identity in identities:
            try:
                dataset=read_dataset(identity);frames,choices=eligible(dataset,now)
            except DataError:continue
            if dataset['material']['symbol']!=symbol:continue
            start=rng.choice(choices)
            item={'id':uuid.uuid4().hex,'version':VERSION,'datasetId':identity,'symbol':symbol,
                  'startAt':start,'createdAt':int(time.time()) if now is None else now,
                  'feed':dataset['material']['feed'],'adjustment':dataset['material']['adjustment'],
                  'selection':'Aktie gleichverteilt aus geeigneten lokal gespeicherten Aktien; anschließend geeigneter 4h-Schluss gleichverteilt. SIP/Split bevorzugt, sonst vorhandener Bestand. Keine Signal-/Gewinnfilter.'}
            with connection() as db:db.execute('INSERT INTO settings VALUES(?,?)',('random:case:'+item['id'],json.dumps(item,allow_nan=False)))
            return item
    raise DataError('Keine geeigneten lokalen Marktdaten. Zuerst eine längere Aktienhistorie importieren (mindestens 81 Handelstage in 1h, 4h und 1D).',404)


def case(identity):
    if not isinstance(identity,str) or not re.fullmatch('[a-f0-9]{32}',identity):raise DataError('Ungültige Zufallsfall-ID.',400)
    with connection() as db:row=db.execute('SELECT value FROM settings WHERE key=?',('random:case:'+identity,)).fetchone()
    if not row:raise DataError('Zufallsfall nicht gefunden.',404)
    return json.loads(row[0])


def cutoff(value,default):
    if value is None:return default
    try:
        dt=datetime.fromisoformat(value.replace('Z','+00:00'))
        if dt.tzinfo is None:
            local=dt.replace(tzinfo=NY)
            if local.astimezone(timezone.utc).astimezone(NY).replace(tzinfo=None)!=dt or local.replace(fold=1).utcoffset()!=local.utcoffset():raise ValueError()
            dt=local
        return int(dt.timestamp())
    except (ValueError,TypeError,AttributeError):raise DataError('Ungültiger oder mehrdeutiger Zeitpunkt (New York).',400) from None


def view(identity,timeframe='4h',as_of=None,analysis=False):
    item=case(identity);dataset=read_dataset(item['datasetId']);frames,_=eligible(dataset)
    if timeframe not in CHART_TIMEFRAMES:raise DataError('Erlaubte Intervalle: 1h, 4h, 1D, 1W.',400)
    at=cutoff(as_of,item['startAt'])
    if at>max(b.end for b in frames['1h']):raise DataError('Ende des gespeicherten Verlaufs erreicht.',404)
    m=dataset['material']
    # Do not ship whole-dataset metadata or future OHLC through another interval.
    sources={tf:(rows,{'quality':{'rejected':0},'cached':True,'mode':'random-replay',
                     'normalization':m['normalization'][tf]}) for tf,rows in frames.items()}
    payload=build_chart(sources,item['symbol'],'1D' if timeframe=='1W' else timeframe,datetime.fromtimestamp(at,timezone.utc),datetime.now(timezone.utc),historical=True,include_analysis=analysis)
    add_weekly(payload,timeframe)
    payload.update(datasetId=item['datasetId'],feed=m['feed'],adjustment=m['adjustment'],provider=m['provider'],
                   session=m['session'],dataKind='market',randomCase={'id':item['id'],'startAt':item['startAt'],'selection':item['selection']})
    if analysis:
        from snapshots import remember
        remember(payload)
    return payload


def step(identity,timeframe,as_of,direction):
    item=case(identity);frames,_=eligible(read_dataset(item['datasetId']))
    if timeframe=='1W':frames['1W']=weeks(frames['1D'],int(time.time())-900)
    if timeframe not in frames or direction not in ('back','next'):raise DataError('Ungültiger Kerzenschritt.',400)
    at=cutoff(as_of,item['startAt']);ends=[b.end for b in frames[timeframe]]
    i=bisect_right(ends,at) if direction=='next' else bisect_left(ends,at)-1
    # Every interval still needs three known candles when going backwards.
    if any(len(rows)<3 for rows in frames.values()):raise DataError('Zu wenige vollständige Kerzen für diesen Schritt.',404)
    earliest=max(rows[2].end for rows in frames.values())
    if not 0<=i<len(ends) or ends[i]<earliest:raise DataError('Rand des gespeicherten Verlaufs erreicht.',404)
    return {'closedAt':ends[i],'asof':datetime.fromtimestamp(ends[i],timezone.utc).isoformat(),'timeframe':timeframe}


def get(path,query):
    match=re.fullmatch(r'/api/random/cases/([a-f0-9]{32})(?:/(chart|step))?',path)
    if not match:raise DataError('Unbekannte Zufallsroute.',404)
    def q(name,default=None):
        values=query.get(name,[default])
        if len(values)!=1:raise DataError('Parameter mehrfach angegeben.',400)
        return values[0]
    identity,action=match.groups()
    if action=='chart':
        analysis=q('analysis','0')
        if analysis not in ('0','1'):raise DataError('analysis=0/1 erwartet.',400)
        return view(identity,q('timeframe','4h'),q('asof'),analysis=='1')
    if action=='step':return step(identity,q('timeframe','4h'),q('asof'),q('direction'))
    return case(identity)


def post(path,body):
    if path!='/api/random/cases':raise DataError('Unbekannte Zufallsroute.',404)
    if body!={}:raise DataError('Neue Zufallsauswahl erwartet ein leeres JSON-Objekt.',400)
    return create()
