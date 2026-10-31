"""Independent candidate admission, causal stop and 5m replay verification."""
import argparse
from collections import Counter
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import random
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from datasets import read_dataset,source_bars
from event_case_study import load_block,checked as check_source
from exit_followup import checked,load_followup,NEW
from fan_execution import next_open_time
from strategy_screen import read,write
from tools.verify_event_cases import reference,close

next_open_time=lru_cache(maxsize=100000)(next_open_time)


def independently_select(case,timeline,policy):
    e,s=case['entry'],case['signal'];r=e['rules'];fee=r['fee_per_order']
    cost=r['spread_bps']/20000+r['slippage_bps']/10000
    original=s['safety'];active=False;gate=None;out=[]
    def level(line,index):return line['a_price']+line['slope']*(index-line['a_index'])
    def valid(line,state):
        return line is not None and line['knownAt']<=state['closedAt'] and line['slope']>0 and 0<level(line,state['index'])<state['close']
    for state in timeline:
        if state['closedAt']<=e['entryAt']:
            out.append({**state,'green':None});continue
        current=state['green']
        if policy=='qualified_fan':
            chosen=original if valid(original,state) else None
            if valid(current,state) and current['qualified'] and (chosen is None or level(current,state['index'])>level(chosen,state['index'])):
                chosen=current
        else:
            net=e['quantity']*(state['close']*(1-cost)-e['entryFill'])-2*fee
            if not active and net/e['plannedRisk']>=2:
                active=True;gate=state['closedAt']
            chosen=current if active else original
            if not valid(chosen,state):chosen=None
        out.append({**state,'green':chosen})
    return out,gate


def verify(root,samples=2):
    p=checked(read(Path(root)/'plan.json'));sp=check_source(read(Path(p['sourceRoot'])/'plan.json'))
    assert p['sourcePlanId']==sp['id']
    rng=random.Random(20261031);cases=paths=replays=0;sample_ids=[]
    for symbol in p['symbols']:
        base=load_block(p['sourceRoot'],sp,symbol);value=load_followup(root,p,symbol)
        assert value['sourceChecksum']==base['checksum']
        assert value['caseIds']==[c['id'] for c in base['cases']]
        states={s['closedAt']:s for s in base['timeline']}
        for c in base['cases']:
            cases+=1;e=c['entry'];rules=e.get('rules',{})
            for policy,path in value['newPaths'][c['id']].items():
                paths+=1
                assert path['model']==policy and 'plannedTimeExit' not in path and path.get('reason')!='time'
                if e['status']!='filled':
                    assert path['status']==e['status'];continue
                prepared,gate=independently_select(c,base['timeline'],policy)
                lines={s['closedAt']:s['green'] for s in prepared}
                observed=path['exitAt'] if path['status']=='closed' else path['lastObservedAt']
                assert path['gateAt']==(gate if gate is not None and gate<=observed else None)
                previous=e['initialStop']
                for ev in path['stopEvents']:
                    state=states[ev['knownAt']];ln=lines[ev['knownAt']]
                    assert ln and ln['id']==ev['lineId']
                    assert all(point['known_at']<=ev['knownAt'] for point in ln.get('contactPoints',[]))
                    level=ln['a_price']+ln['slope']*(state['index']-ln['a_index'])
                    close(ev['newStop'],math.floor(level*(1-rules['buffer_pct']/100)/rules['tick'])*rules['tick'])
                    assert ev['newStop']>previous;previous=ev['newStop']
                    assert ev['effectiveAt']==next_open_time(ev['knownAt']+rules['latency_seconds'])
                    if ev['source']=='current' and policy=='qualified_fan':assert ev['qualified']
                    if path['status']=='closed':assert ev['effectiveAt']<=path['fillBarAt']
                close(previous,path['finalStop'])
                if path['status']=='closed':
                    side=rules['spread_bps']/20000+rules['slippage_bps']/10000
                    net=e['quantity']*(path['exitPrice']*(1-side)-e['entryFill'])-2*rules['fee_per_order']
                    close(net,path['netPnl']);close(net/e['plannedRisk'],path['netR'])
                else:assert path['netR'] is None and path['exitAt'] is None
        filled=[c for c in base['cases'] if c['entry']['status']=='filled']
        selected=rng.sample(filled,min(samples,len(filled)))
        if selected:
            fine=[b for b in source_bars(read_dataset(p['datasets'][symbol]))['5m'] if b.end<=p['cutoff']]
            for c in selected:
                sample_ids.append(c['id'])
                for policy in NEW:
                    timeline,_=independently_select(c,base['timeline'],policy)
                    actual=value['newPaths'][c['id']][policy]
                    ref=reference({**c,'paths':{policy:actual}},fine,timeline,p['cutoff'])[policy]
                    for k,v in ref.items():
                        try:close(actual.get(k),v)
                        except AssertionError as exc:raise AssertionError((symbol,c['id'],policy,k,str(exc))) from exc
                    replays+=1
        print(json.dumps({'symbol':symbol,'casesVerified':cases,'independentReplays':replays}),flush=True)
    result={'planId':p['id'],'passed':True,'cases':cases,'newPaths':paths,'independent5mReplays':replays,
            'sampleIds':sample_ids,'sampleSeed':20261031,'verifierSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    write(Path(root)/'verification.json',result)
    return result


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('root');ap.add_argument('--samples',type=int,default=2);a=ap.parse_args()
    r=verify(a.root,a.samples);print(json.dumps({k:v for k,v in r.items() if k!='sampleIds'}),flush=True)
