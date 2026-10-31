"""Independent signal-close features, selection membership and result aggregation."""
import argparse
from collections import Counter,defaultdict
from concurrent.futures import ProcessPoolExecutor,as_completed
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from datasets import read_dataset
from fan_study import schedule
from strategy_screen import read,write
from fan_geometry import stable_id
from event_case_study import load_block
from exit_followup import load_followup
from entry_screen import Context,features,PROFILES
from models import Bar
from tools.run_entry_screen import checked,POLICIES


def equal(a,b):
    if isinstance(a,(float,int)) and isinstance(b,(float,int)):
        assert math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-9),(a,b)
    else:assert a==b,(a,b)


def independent_checks(f):
    known=lambda *keys:all(isinstance(f.get(k),(float,int)) and math.isfinite(f[k]) for k in keys)
    return {'qualified':bool(f['geometryKnown'] and f['cohort']=='qualified' and f['family'] in ['breakout','red_retest']),
      'risk':(f['signalStopATR']>=1 and f['signalStopPct']>=2) if known('signalStopATR','signalStopPct') else None,
      'trend':f['dailyClose']>f['dailySma200'] if known('dailyClose','dailySma200') else None,
      'mature':f['actionSpanDays']>=14 and f['safetySpanDays']>=20 if known('actionSpanDays','safetySpanDays') else None,
      'convergent':0<=f['compressionRatio']<=.5 if known('compressionRatio') else None,
      'both_qualified':f['safetyQualified'],
      'not_stretched':True if f['family']!='breakout' else (f['signalStopPct']<=6 and f['signalStopATR']<=3.5 if known('signalStopPct','signalStopATR') else None)}


def stock(task):
    root,p,symbol=task
    b=load_block(p['baseRoot'],read(Path(p['baseRoot'])/'plan.json'),symbol)
    follow=load_followup(p['sourceRoot'],read(Path(p['sourceRoot'])/'plan.json'),symbol)
    block=read(Path(root)/'stocks'/(symbol+'.json.gz'))
    assert block['planId']==p['id'] and block['sourceChecksum']==b['checksum']==follow['sourceChecksum']
    assert block['checksum']==stable_id({k:v for k,v in block.items() if k!='checksum'})
    assert [v['caseId'] for v in block['cases']]==[c['id'] for c in b['cases']]==follow['caseIds']
    states={s['closedAt']:s['index'] for s in b['timeline']}
    for c,x in zip(b['cases'],block['cases']):
        f,s=x['features'],c['signal'];assert f['knownAt']==s['signalAt'] and f['sourceIndex']==states[s['signalAt']]
        checks=independent_checks(f);assert checks==x['checks']
        for name,profile in PROFILES.items():
            expected={'profile':name,'accepted':all(checks[k] is True for k in profile['rules']),
                      'failed':[k for k in profile['rules'] if checks[k] is False],
                      'unknown':[k for k in profile['rules'] if checks[k] is None]}
            assert x['selection'][name]==expected
        if f['signalStopPct'] is not None:
            equal(f['signalStopPct'],100*(s['signalClose']-s['initialStop'])/s['signalClose'])
            equal(f['signalStopATR'],(s['signalClose']-s['initialStop'])/s['features']['atr'])
    # Prefix truncation and separately computed daily SMA on two fixed samples per stock.
    candidates=[(c,x) for c,x in zip(b['cases'],block['cases']) if c['signal']['cohort']=='qualified']
    chosen=random.Random('20261031:'+symbol).sample(candidates,min(2,len(candidates)))
    if chosen:
        d=read_dataset(p['datasets'][symbol]);rows=[Bar(**v) for v in d['material']['bars']['4h']];daily=[Bar(**v) for v in d['material']['bars']['1D']]
        for c,x in chosen:
            at=c['signal']['signalAt'];prefix=[b for b in rows if b.end<=at];days=[b for b in daily if b.end<=at]
            actual=features(c['signal'],Context(prefix,days))
            for key in actual:equal(actual[key],x['features'][key])
            expected=list(schedule(daily[0].time,at,'1D'))[-200:] if daily else []
            clean=len(days)>=200 and len(expected)==200 and [(v.time,v.end) for v in days[-200:]]==expected
            sma=statistics.mean(v.close for v in days[-200:]) if clean else None
            equal(sma,x['features']['dailySma200'])
    # Return only compact outcomes to independently aggregate, not the large timelines.
    out=[]
    for c,x in zip(b['cases'],block['cases']):
        paths={**c['paths'],**follow['newPaths'][c['id']]}
        values={}
        for name in POLICIES:
            path=paths[name];value=None
            if path['status']=='closed':value=path['netReturnPct']
            elif path['status']=='open':value=path['markNetReturnPct']
            values[name]={'status':path['status'],'terminal':value,'closed':path.get('netReturnPct')}
        out.append({'id':c['id'],'family':c['signal']['family'],'window':c['window'],
                    'selection':x['selection'],'entryStatus':c['entry']['status'],'values':values})
    return symbol,out,len(chosen)


def verify(root,workers=3):
    p=checked(read(Path(root)/'plan.json'));rows=[];prefixes=0
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for result in as_completed([pool.submit(stock,(root,p,s)) for s in p['symbols']]):
            symbol,cs,n=result.result();rows.extend(cs);prefixes+=n
            print(json.dumps({'symbol':symbol,'cases':len(cs),'prefixChecks':n}),flush=True)
    r=read(Path(root)/'results.json');assert r['planId']==p['id'] and r['cases']==len(rows)
    def check(cs,stats,name):
        assert stats['signals']==len(cs)
        assert stats['statuses']==dict(Counter(c['values'][name]['status'] for c in cs))
        for field,key in [('terminal','meanTerminalPct'),('closed','meanNetReturnPct')]:
            vals=[c['values'][name][field] for c in cs if c['values'][name][field] is not None]
            equal(statistics.mean(vals) if vals else None,stats[key])
    for profile,pr in r['profiles'].items():
        chosen=[c for c in rows if c['selection'][profile]['accepted']]
        for family,g in pr['groups'].items():
            cs=[c for c in chosen if family=='all' or c['family']==family]
            common=[c for c in cs if all(c['values'][m]['terminal'] is not None for m in POLICIES)]
            assert len(cs)==g['signals'] and len(common)==g['commonCount']
            assert stable_id(sorted(c['id'] for c in common))==g['commonCaseIdsHash']
            for m in POLICIES:
                check(cs,g['policies'][m],m);check(common,g['common'][m],m)
                for w,values in g['windows'].items():check([c for c in cs if c['window']==w],values[m],m)
    playlist=read(Path(root)/'playlist.json')
    assert playlist['planId']==p['id'] and playlist['profile']==p['defaultProfile']
    assert {c['caseId'] for c in playlist['items']}=={c['id'] for c in rows if c['selection'][p['defaultProfile']]['accepted']}
    assert not any(k in json.dumps(playlist) for k in ('netReturnPct','markNetPnl','mfeR','exitAt'))
    result={'planId':p['id'],'passed':True,'cases':len(rows),'profiles':len(PROFILES),
            'independentSmaAndPrefixChecks':prefixes,'aggregationsChecked':True,'playlistOutcomeBlind':True,
            'verifierSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    write(Path(root)/'verification.json',result);return result


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('root');ap.add_argument('--workers',type=int,default=3);a=ap.parse_args()
    if not 1<=a.workers<=4:ap.error('1–4 workers')
    print(json.dumps(verify(a.root,a.workers)),flush=True)
