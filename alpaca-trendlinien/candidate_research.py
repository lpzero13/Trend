"""Predeclared retest features and matched controls. No parameter fitting/orders.

Selection consumes only entry-time covariates. Outcome helpers are separate and
must be called after the selections have been persisted by the study runner.
"""
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from copy import copy, deepcopy
from datetime import datetime
import random
from statistics import mean

from complete_outcomes import Outcomes
from complete_strategy import RULES, source_grid
from datasets import digest
from lab_data import session_bounds
from lab_metrics import expected_grid, percentile
from lab_splits import sessions_between
from models import NY
from tori_entries import atr

VERSION='candidate-research-1'
SEED=20261022
HORIZONS=(5,10,20)
MODELS=('fixed','higher_low')


class ResearchData:
    def __init__(self,dataset,cutoff):
        self.dataset=dataset;self.base=Outcomes(dataset,'4h',cutoff);self.cutoff=cutoff
        self.rows=self.base.rows;self.fine=self.base.fine
        self.times=self.base.times;self.fine_ends=[b.end for b in self.fine]
        self.source_ends=[b.end for b in self.rows]
        self.daily=self.base.sources['1D'];self.daily_ends=[b.end for b in self.daily]
        self.by_time={b.time:b for b in self.fine}
        self.days=self.base.days;self.day_index={d:i for i,d in enumerate(self.days)}
        grid={p:n for n,p in enumerate(source_grid(self.rows[0].time,cutoff,'4h'))}
        self.grid=[grid[(b.time,b.end)] for b in self.rows]
        self.pools=defaultdict(list);self.covariates={};self.path_cache={}
        for b in self.fine:
            d=datetime.fromtimestamp(b.time,NY)
            self.pools[(d.year,(d.month-1)//3,d.hour,d.minute)].append(b)

    def covariate(self,at,price):
        # Includes only closed source history and the observed execution open.
        key=(at,price)
        if key in self.covariates:return self.covariates[key]
        i=bisect_right(self.source_ends,at-RULES['latency'])-1
        nd=bisect_right(self.daily_ends,at)
        out=None
        if i>=14 and nd>=20 and self.grid[i]-self.grid[i-14]==14:
            vol=atr(self.rows[i-14:i+1])
            if vol and price>0:out={'index':i,'atr':vol,'relativeATR':vol/price,
                'maSide':price>=mean(b.close for b in self.daily[nd-20:nd]),
                'dayIndex':self.day_index[str(datetime.fromtimestamp(at,NY).date())]}
        self.covariates[key]=out
        return out

    def controls(self,entry,start_at,end_at,count=5):
        wanted=self.covariate(entry['entryAt'],entry['entryPrice'])
        fraction=(entry['entryPrice']-entry['initialStop'])/entry['entryPrice']
        if wanted is None or not 0<fraction<1:return {'items':[],'reason':'entry_covariates_or_risk_unavailable','requested':count}
        d=datetime.fromtimestamp(entry['entryAt'],NY);pool=[]
        for b in self.pools[(d.year,(d.month-1)//3,d.hour,d.minute)]:
            if not start_at<=b.time<=end_at:continue
            got=self.covariate(b.time,b.open)
            if got is None or got['maSide']!=wanted['maSide'] or abs(got['dayIndex']-wanted['dayIndex'])<20:continue
            pool.append((abs(got['relativeATR']-wanted['relativeATR']),b,got))
        pool.sort(key=lambda r:(r[0],r[1].time))
        near=pool[:20];rng=random.Random(f'{VERSION}|{SEED}|{entry["id"]}')
        chosen=sorted(rng.sample(near,min(count,len(near))),key=lambda r:r[1].time)
        controls=[]
        for distance,b,cov in chosen:
            stop=b.open*(1-fraction);i=cov['index'];level=stop+max(.01,.25*cov['atr'])
            ray={'a_index':i-1,'b_index':i,'a_time':self.rows[i-1].time,'b_time':self.rows[i].time,
                'a_price':level,'b_price':level,'slope':0.,'basis':'bars','valid':True}
            controls.append({'id':digest([VERSION,entry['id'],b.time]),'matchedEntryId':entry['id'],
                'symbol':entry['symbol'],'entryAt':b.time,'entryPrice':b.open,'signalAt':self.rows[i].end,
                'signalIndex':i,'initialStop':stop,'signalATR':cov['atr'],'greenLevel':level,'green':ray,
                'kind':'matched_control','relativeATRDistance':distance,'initialRiskFraction':fraction,
                'meaning':'Random control with matched initial risk; horizontal green is a risk reference, not a discovered trendline.'})
        return {'items':controls,'requested':count,'eligiblePool':len(pool),'nearPool':len(near),
            'reason':None if len(controls)==count else 'fewer_predeclared_matches',
            'matching':'same stock/NY clock/quarter/known MA20 side; 20 sessions separation; nearest 20 prior ATR/price neighbours; fixed random draw'}

    def horizon_end(self,entry_at,horizon):
        day=str(datetime.fromtimestamp(entry_at,NY).date());start=bisect_right(self.days,day)
        j=start+horizon-1
        return session_bounds(self.days[j])[1] if j<len(self.days) else None

    def path(self,e,model,end):
        limit=min(end or self.cutoff,self.cutoff)
        key=(e['id'],model,limit)
        if key not in self.path_cache:
            p=copy(self.base);p.cutoff=limit;p.cache={}
            n=bisect_right(self.fine_ends,limit)
            p.fine=self.fine[:n];p.times=self.times[:n]
            p.expected=self.base.expected[:bisect_left(self.base.expected,limit)]
            p.rows=self.rows[:bisect_right(self.source_ends,limit)]
            p.source_ends=self.base.source_ends[:bisect_right(self.base.source_ends,limit)]
            # The shared evaluator's source indexes stay anchored to this prefix.
            result=p.path(e,model)
            if result['status']=='open' and (end is None or end>self.cutoff):
                result={**result,'status':'unknown','reason':'phase_boundary','netR':None,'netReturnPct':None}
            self.path_cache[key]=result
        return deepcopy(self.path_cache[key])

    def outcome(self,e,horizon):
        end=self.horizon_end(e['entryAt'],horizon)
        paths={m:self.path(e,m,end) for m in MODELS}
        for p in paths.values():
            p['valuationR']=p.get('netR') if p['status']=='closed' else p.get('markNetR') if p['status']=='open' else None
            p['valuationPct']=p.get('netReturnPct') if p['status']=='closed' else p.get('markNetReturnPct') if p['status']=='open' else None
        market={'status':'unknown','reason':'phase_boundary','netPct':None,'mfePct':None,'maePct':None,
            'safetyTouched':None,'oneRBeforeSafety':None,'intrabarAmbiguous':None}
        if end is not None and end<=self.cutoff:
            a,b=bisect_left(self.times,e['entryAt']),bisect_right(self.fine_ends,end)
            rows=self.fine[a:b];expected=list(expected_grid(e['entryAt'],end))
            complete=bool(rows) and [x.time for x in rows]==expected
            if complete:
                price=e['entryPrice'];risk=price*(1+RULES['sideCost'])-e['initialStop']
                safety=next((i for i,x in enumerate(rows) if x.low<=e['initialStop']),None)
                one=next((i for i,x in enumerate(rows) if x.high>=price+risk),None)
                ambiguous=one is not None and safety==one
                market={'status':'known','reason':None,'netPct':(rows[-1].close*(1-RULES['sideCost'])/(price*(1+RULES['sideCost']))-1)*100,
                    'mfePct':max(0,(max(x.high for x in rows)/price-1)*100),
                    'maePct':min(0,(min(x.low for x in rows)/price-1)*100),
                    'safetyTouched':safety is not None,'oneRBeforeSafety':None if ambiguous else one is not None and (safety is None or one<safety),
                    'intrabarAmbiguous':ambiguous}
            else:market['reason']='missing_expected_5m_path'
        return {'horizon':horizon,'targetEnd':end,'mature':end is not None and end<=self.cutoff,'market':market,'paths':paths}


def features(e,rows):
    info,g=e['info'],e['greenInfo'];checks=e['signalChecks'];risk=e['entryPrice']*(1+RULES['sideCost'])-e['initialStop']
    i=e['signalIndex'];bar=rows[i]
    state=lambda k:'unknown' if checks.get(k) is None else 'pass' if checks[k] else 'warn'
    age=info['ageDays']
    return {'contacts':'4+' if info['contacts']>=4 else '3','age':'7–14' if age<14 else '14–30' if age<30 else '30+',
        'riskATR':'<=2' if risk/e['signalATR']<=2 else '>2','riskATRValue':risk/e['signalATR'],
        'riskPct':risk/e['entryPrice']*100,'bodyATR':(bar.close-bar.open)/e['signalATR'],
        'momentum':state('momentum'),'context':state('context'),'room':state('room'),
        'greenContacts':'3+' if g['contacts']>=3 else '2','events':state('events')}


def metric(record,horizon,kind):
    o=record['outcomes'][str(horizon)]
    # A known early stop stays a fact, but do not compare only the stopped
    # losers near a phase boundary while its still-open peers are censored.
    if not o.get('mature',True):return None
    if kind=='market':return o['market']['netPct'] if o['market']['status']=='known' else None
    return o['paths'][kind]['valuationR']


def uncertainty(rows):
    intervals={}
    for scheme in ('stock','quarter'):
        clusters=defaultdict(list)
        for r in rows:
            d=datetime.fromtimestamp(r['entryAt'],NY)
            k=r['symbol'] if scheme=='stock' else (d.year,(d.month-1)//3)
            clusters[k].append(r['delta'])
        if len(clusters)<3:
            intervals[scheme]={'low':None,'high':None,'blocks':len(clusters)};continue
        values=list(clusters.values());rng=random.Random(f'{VERSION}|{SEED}|{scheme}');means=[]
        for _ in range(500):
            draw=[x for _ in values for x in rng.choice(values)];means.append(mean(draw))
        intervals[scheme]={'low':percentile(means,.025),'high':percentile(means,.975),'blocks':len(values)}
    known=[v for v in intervals.values() if v['low'] is not None]
    return {'low':min(v['low'] for v in known) if len(known)==2 else None,
        'high':max(v['high'] for v in known) if len(known)==2 else None,'clusters':intervals,
        'method':'Envelope of separate stock- and quarter-cluster bootstraps, 500 fixed draws each; descriptive, no multiplicity adjustment or guaranteed coverage.'}


def summarize(records):
    """All entries stay in the denominator; complete original panels for pairing."""
    def aggregate(rows):
        out={'entries':len(rows),'stocks':len({r['symbol'] for r in rows}),'horizons':{}}
        for h in HORIZONS:
            result={}
            for kind in ('market',*MODELS):
                actual=[];paired=[];controls_count=0
                for r in rows:
                    value=metric(r,h,kind)
                    if value is not None:actual.append(value)
                    cs=r['controls'];got=[metric(c,h,kind) for c in cs]
                    controls_count+=sum(v is not None for v in got)
                    if value is not None and len(cs)==5 and all(v is not None for v in got):
                        paired.append({'entryAt':r['entryAt'],'symbol':r['symbol'],'delta':value-mean(got)})
                deltas=[r['delta'] for r in paired]
                result[kind]={'knownEntries':len(actual),'unknownEntries':len(rows)-len(actual),
                    'knownControlObservations':controls_count,'pairedPanels':len(paired),'unpairedPanels':len(rows)-len(paired),
                    'meanActual':mean(actual) if actual else None,'positivePct':100*sum(v>0 for v in actual)/len(actual) if actual else None,
                    'meanExcess':mean(deltas) if deltas else None,
                    'interval':uncertainty(paired)}
            out['horizons'][str(h)]=result
        out['marketPathReasons']=dict(Counter(r['outcomes']['20']['market']['reason'] or 'known' for r in rows))
        return out
    groups={}
    for phase in ('all','2021-2023','2024-2026'):
        rows=[r for r in records if phase=='all' or r['phase']==phase]
        groups[phase]=aggregate(rows)
        for feature in ('contacts','age','riskATR','momentum','context','room','greenContacts'):
            for value in sorted({r['features'][feature] for r in rows}):
                groups[phase+'/'+feature+'/'+value]=aggregate([r for r in rows if r['features'][feature]==value])
    return {'version':VERSION,'groups':groups,'requestedControls':5,'seed':SEED,
        'meaning':'Dependent retrospective matched comparisons on known periods. Market excess in percentage points; stop-model excess in original-risk R. No fitted score or proof of profitability.'}
