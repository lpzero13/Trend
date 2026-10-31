"""Chart-only, closed XNYS weeks from existing daily sources; frozen research stays unchanged."""
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime,timedelta
from functools import lru_cache
import hashlib
import json

from market_calendar import calendar
from models import Bar,NY,DataError

CHART_TIMEFRAMES=('1h','4h','1D','1W')
VERSION='xnys-complete-week-1'


@lru_cache(maxsize=4096)
def week_sessions(monday):
    day=datetime.fromisoformat(monday).date();market=calendar(day.year)
    return tuple((str(s.date()),int(market.session_open(s).timestamp()),int(market.session_close(s).timestamp()))
                 for s in market.sessions_in_range(str(day),str(day+timedelta(days=4))))


def weeks(daily,cutoff):
    groups=defaultdict(dict)
    for b in daily:
        if b.end>cutoff:continue
        day=datetime.fromtimestamp(b.time,NY).date();monday=day-timedelta(days=day.weekday())
        groups[str(monday)][str(day)]=b
    result=[]
    for monday,known in sorted(groups.items()):
        sessions=week_sessions(monday)
        if not sessions or sessions[-1][2]>cutoff or set(known)!={d for d,_,_ in sessions}:continue
        rows=[known[d] for d,_,_ in sessions]
        if any(b.end!=end for b,(_,_,end) in zip(rows,sessions)):continue
        result.append(Bar(sessions[0][1],sessions[-1][2],rows[0].open,max(b.high for b in rows),
                          min(b.low for b in rows),rows[-1].close,sum(b.volume for b in rows)))
    return result


def add_weekly(payload,timeframe):
    """Add the prefix only; no mutation of stored dataset or original source axes."""
    daily=[Bar(**b) for b in payload['charts']['1D']['bars']]
    rows=weeks(daily,payload['analysisCutoff'])
    if len(rows)<3:
        if timeframe=='1W':raise DataError('Für 1W fehlen mindestens drei vollständige abgeschlossene Handelswochen.',404)
        from drawing_axes import add_drawing_axes
        add_drawing_axes(payload)
        return payload
    bars=[asdict(b) for b in rows];last,previous=rows[-1],rows[-2]
    view={'bars':bars,'axis':[b.time for b in rows],'reference':last.time,'latest':{
        'close':last.close,'time':last.time,'end':last.end,'change':last.close-previous.close,
        'changePercent':(last.close/previous.close-1)*100}}
    payload['charts']['1W']=view
    payload['sources']['1W']={**payload['sources']['1D'],'normalization':VERSION,'count':len(rows),
        'first':rows[0].time,'last':last.time,'lastClose':last.end,'derivedFrom':'1D',
        'weekPolicy':'XNYS Monday–Friday; complete expected sessions only; no partial week'}
    if payload.get('analysisEnabled'):
        from trendlines import analyze
        from chart_lane_cache import lane
        payload['lanes']['1W']=lane(('legacy',payload.get('symbol','CHART'),'1W',last.time,False),rows,
                                  lambda:analyze(rows,'1W',last.time,data_errors=False))
    if timeframe=='1W':
        payload.update(view,timeframe='1W',fingerprint=hashlib.sha256(json.dumps(bars,sort_keys=True).encode()).hexdigest()[:16])
    from drawing_axes import add_drawing_axes
    add_drawing_axes(payload)
    return payload


def next_close(cutoff,limit):
    day=datetime.fromtimestamp(cutoff,NY).date();monday=day-timedelta(days=day.weekday())
    for offset in range(3):
        sessions=week_sessions(str(monday+timedelta(days=offset*7)))
        if sessions and cutoff<sessions[-1][2]<=limit:return sessions[-1][2]
    raise DataError('Noch keine weitere abgeschlossene Handelswoche verfügbar.',404)
