"""Calendar-only future positions for personal drawings; never signal/OHLC data."""
from collections import Counter
from datetime import datetime, timedelta
from functools import lru_cache

from market_calendar import calendar, CALENDAR_VERSION
from models import NY


@lru_cache(maxsize=256)
def sessions(start, finish):
    first=datetime.fromisoformat(start).date();last=datetime.fromisoformat(finish).date()
    result=[]
    for year in range(first.year,last.year+1):
        market=calendar(year)
        for session in market.sessions_in_range(max(start,f'{year}-01-01'),min(finish,f'{year}-12-31')):
            result.append((int(market.session_open(session).timestamp()),int(market.session_close(session).timestamp())))
    return tuple(result)


def add_drawing_axes(payload):
    axes={}
    for tf,view in payload['charts'].items():
        if tf not in ('1h','4h','1D','1W') or not view['bars']:continue
        rows=view['bars'];axis=[b['time'] for b in rows]
        last=datetime.fromtimestamp(axis[-1],NY)
        # Three years of planned exchange sessions, no future observed bars/prices.
        future=sessions(last.date().isoformat(),(last.date()+timedelta(days=3*366)).isoformat())
        regular=payload.get('sources',{}).get(tf,{}).get('normalization')=='tori-rth-5m-v1'
        clocks=Counter((datetime.fromtimestamp(b['time'],NY).hour,datetime.fromtimestamp(b['time'],NY).minute)
                       for b in rows[-120:])
        template=sorted(k for k,n in clocks.items() if n>=max(clocks.values())*.5)
        seen_weeks=set()
        for opened,closed in future:
            day=datetime.fromtimestamp(opened,NY)
            if tf=='1W':
                week=day.date()-timedelta(days=day.weekday())
                if week in seen_weeks:continue
                seen_weeks.add(week);values=[opened]
            elif tf=='1D':
                values=[opened if regular else int(day.replace(hour=last.hour,minute=last.minute,second=last.second).timestamp())]
            elif regular:
                values=range(opened,closed,3600 if tf=='1h' else 14400)
            else:
                # Native series retain their observed clock convention; no
                # conversion to research RTH or invented future candles.
                values=[int(day.replace(hour=h,minute=m,second=0).timestamp()) for h,m in template]
            axis.extend(t for t in values if t>axis[-1])
        axes[tf]=axis
    payload['drawingAxes']=axes
    payload['drawingAxesPolicy']={'version':'personal-calendar-axis-1','calendar':CALENDAR_VERSION,
                                  'future':'planned positions only; no candles or signals','years':3}
    return payload
