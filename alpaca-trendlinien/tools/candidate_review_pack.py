"""Twenty fixed random SIP prefixes, independent of future signals/outcomes."""
import argparse
import json
from pathlib import Path
import random
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from datasets import read_dataset,source_bars
from complete_strategy import IncrementalGeometry,source_grid
from safety_strategy import StrategyContext
from workbench_reviews import register


def prepare(source):
    imports=json.loads((Path(source)/'imports.json').read_text('utf-8'))
    eligible=[(s,tf) for s,v in sorted(imports.items()) if v.get('id') for tf in ('4h','1D')]
    chosen=random.Random('sip-human-prefixes-20261022').sample(eligible,20)
    samples=[]
    for symbol,tf in sorted(chosen):
        d=read_dataset(imports[symbol]['id'])
        if d['material']['feed']!='sip':raise ValueError('SIP required')
        sources=source_bars(d);rows=sources[tf]
        valid=[i for i,b in enumerate(rows) if b.end>=rows[0].time+365*86400]
        i=random.Random(f'sip-human|{symbol}|{tf}').choice(valid);cutoff=rows[i].end;known=rows[:i+1]
        grid={p:n for n,p in enumerate(source_grid(rows[0].time,cutoff,tf))}
        cs=IncrementalGeometry(known,symbol,tf,'strict',[grid[(b.time,b.end)] for b in known]).proposals(i)
        cs.sort(key=lambda c:(-c['count'],-c['ray']['b_index'],c['id']))
        rays=[]
        for upper in (True,False):
            c=next((c for c in cs if c['upper']==upper),None)
            if c:rays.append({'role':'red' if upper else 'green','ray':c['ray']})
        context=StrategyContext({t:[b for b in data if b.end<=cutoff] for t,data in sources.items()},cutoff)
        levels=[z['lower'] for z in context.known_context(cutoff)['zones'] if z['lower']>known[-1].close]
        samples.append({'datasetId':d['id'],'timeframe':tf,'cutoff':cutoff,'kind':'fixed_random_sip',
            'engine':{'rays':rays,'resistances':sorted(levels)}})
    samples.sort(key=lambda s:s['datasetId'])
    identity=register(samples,label='SIP · 20 zufällige Präfixe · eigene Linien zuerst')
    print(json.dumps({'packId':identity,'cases':20,'humanLabelsCreated':0}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True);prepare(p.parse_args().source)
