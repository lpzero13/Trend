"""Outcome-blind, signal-close screening shared by research and chart replay."""
from bisect import bisect_right
import math

from fan_study import source_gaps,schedule

VERSION = 'tori-entry-screen-1'
RULES = {
    'qualified': 'Qualifizierter Ausbruch oder roter Retest',
    'risk': 'Signalabstand zum Anfangsstop mindestens 1 ATR4h und 2 %',
    'trend': 'Letzter vollständig geschlossener Tageskurs über sauberem Tages-SMA200',
    'mature': 'Kontaktspanne Rot mindestens 14 und Safety mindestens 20 Kalendertage',
    'convergent': 'Rot fällt, Safety steigt; positive Dreiecksbreite seit gemeinsamem Ankerbeginn mindestens halbiert',
    'both_qualified': 'Auch die beim Signal gewählte Safety bereits qualifiziert',
    'not_stretched': 'Direkter Ausbruch höchstens 3,5 ATR4h und 6 % über Anfangsstop; Retest separat',
}
PROFILES = {
    'all': {'label':'Alle Rohsignale', 'rules':[]},
    'qualified': {'label':'Qualifizierte Ausbrüche / Retests', 'rules':['qualified']},
    'risk': {'label':'Qualifiziert + Stopabstand', 'rules':['qualified','risk']},
    'trend': {'label':'Qualifiziert + Tagestrend', 'rules':['qualified','trend']},
    'mature': {'label':'Qualifiziert + Linienreife', 'rules':['qualified','mature']},
    'convergent': {'label':'Qualifiziert + Verengung', 'rules':['qualified','convergent']},
    'both_qualified': {'label':'Beide Linien qualifiziert', 'rules':['qualified','both_qualified']},
    'balanced': {'label':'Struktur + Abstand + Tagestrend · experimentell', 'rules':['qualified','risk','trend']},
    'strict': {'label':'Streng: alle Strukturregeln · experimentell',
               'rules':['qualified','risk','trend','mature','convergent','both_qualified','not_stretched']},
}
DEFAULT = 'balanced'  # Declared before outcomes; never replaced with the best historical profile.


def finite(value):
    return isinstance(value,(float,int)) and not isinstance(value,bool) and math.isfinite(value)


class Context:
    """Immutable source bars; each decision uses only its already closed prefix."""
    def __init__(self, hourly4, daily):
        self.rows, self.daily = hourly4, daily
        self.ends = [b.end for b in hourly4]
        self.positions = {b.time:i for i,b in enumerate(hourly4)}
        self.daily_ends = [b.end for b in daily]
        all_rows=hourly4+daily
        self.expected_daily_ends=[e for _,e in schedule(min(b.time for b in all_rows),max(b.end for b in all_rows),'1D')] if all_rows else []
        self.sums=[0.]
        for b in daily:self.sums.append(self.sums[-1]+b.close)
        gaps=source_gaps(daily,daily[-1].end,'1D') if daily else {}
        self.gaps=[0]
        for i in range(len(daily)):self.gaps.append(self.gaps[-1]+int(i in gaps))

    def index(self, signal):
        i=bisect_right(self.ends,signal['signalAt'])-1
        line=signal['line'];anchor=self.positions.get(line.get('a_time'))
        if i<0 or anchor is None or self.rows[i].end!=signal['signalAt']:return None
        return line['a_index']+i-anchor

    def daily_at(self, at):
        count=bisect_right(self.daily_ends,at)
        if not count:return {'dailyAsOf':None,'dailyClose':None,'dailySma200':None,'dailyCurrent':False}
        begin=count-200
        expected=bisect_right(self.expected_daily_ends,at)
        current=expected>0 and self.daily[count-1].end==self.expected_daily_ends[expected-1]
        # A gap preceding the first candle of the selected window is irrelevant.
        clean=current and begin>=0 and self.gaps[count]-self.gaps[begin+1]==0
        return {'dailyAsOf':self.daily[count-1].end,'dailyClose':self.daily[count-1].close,
                'dailySma200':(self.sums[count]-self.sums[begin])/200 if clean else None,'dailyCurrent':current}


def features(signal, context):
    """Does not accept fills, outcomes, MFE, exit paths or future stop events."""
    red,green=signal['line'],signal.get('safety')
    at=signal['signalAt'];close=signal.get('signalClose');stop=signal.get('initialStop')
    atr=signal.get('features',{}).get('atr')
    distance=close-stop if all(finite(x) for x in (close,stop)) and close>0 and stop>0 else None
    f={'version':VERSION,'knownAt':at,'family':signal['family'],'cohort':signal['cohort'],
       'signalClose':close,'initialStop':stop,
       'signalStopPct':100*distance/close if distance is not None else None,
       'signalStopATR':distance/atr if distance is not None and finite(atr) and atr>0 else None,
       'actionSpanDays':red.get('span_days'),'safetySpanDays':green.get('span_days') if green else None,
       'compressionRatio':None,'safetyQualified':bool(green and green.get('qualified')),
       **context.daily_at(at)}
    idx=context.index(signal)
    f['sourceIndex']=idx
    known=lambda ln:ln and ln.get('knownAt',math.inf)<=at and all(p['known_at']<=at for p in ln.get('contactPoints',[]))
    f['geometryKnown']=bool(known(red) and known(green))
    if f['geometryKnown'] and idx is not None and red['slope']<0 and green['slope']>0:
        start=max(red['a_index'],green['a_index'])
        width=lambda i:(red['a_price']+red['slope']*(i-red['a_index']))-(green['a_price']+green['slope']*(i-green['a_index']))
        beginning,current=width(start),width(idx)
        if idx>start and beginning>0 and current>0:f['compressionRatio']=current/beginning
    return f


def decisions(f):
    minimum=lambda key,x: None if not finite(f.get(key)) else f[key]>=x
    sma=f.get('dailySma200');daily=f.get('dailyClose')
    risk=None if any(not finite(f.get(k)) for k in ('signalStopPct','signalStopATR')) else f['signalStopPct']>=2 and f['signalStopATR']>=1
    mature=None if any(not finite(f.get(k)) for k in ('actionSpanDays','safetySpanDays')) else f['actionSpanDays']>=14 and f['safetySpanDays']>=20
    return {'qualified':f['geometryKnown'] and f['family'] in ('breakout','red_retest') and f['cohort']=='qualified',
            'risk':risk,'trend':None if not finite(sma) or not finite(daily) else daily>sma,
            'mature':mature,'convergent':minimum('compressionRatio',0) and f['compressionRatio']<=.5,
            'both_qualified':f['safetyQualified'],
            'not_stretched':True if f['family']!='breakout' else (None if risk is None else f['signalStopPct']<=6 and f['signalStopATR']<=3.5)}


def select(f, profile=DEFAULT):
    checks=decisions(f);needed=PROFILES[profile]['rules']
    return {'profile':profile,'accepted':all(checks[k] is True for k in needed),
            'failed':[k for k in needed if checks[k] is False],
            'unknown':[k for k in needed if checks[k] is None]}
