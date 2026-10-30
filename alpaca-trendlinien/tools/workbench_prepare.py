"""Register diagnostic prefixes and fixed-seed random controls, never outcomes."""
import argparse
import json
from pathlib import Path
import random
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from complete_strategy import IncrementalGeometry, source_grid
from datasets import read_dataset, source_bars
from safety_strategy import StrategyContext
from workbench_reviews import register


def prepare(root,controls=20):
    root=Path(root).resolve();imports=json.loads((root/'imports.json').read_text('utf-8'))
    samples=[];cached_id=None;dataset=None;sources=None
    for p in sorted((root/'blind-private').glob('*.json')):
        private=json.loads(p.read_text('utf-8'));symbol=private['symbol'];tf=p.stem.rsplit('-',1)[1]
        identity=imports[symbol]['id']
        if identity!=cached_id:
            dataset=read_dataset(identity);sources=source_bars(dataset);cached_id=identity
        cutoff=private['cutoff'];context=StrategyContext({t:[b for b in rows if b.end<=cutoff] for t,rows in sources.items()},cutoff)
        close=next(b.close for b in sources[tf] if b.end==cutoff)
        levels=[z['lower'] for z in context.known_context(cutoff)['zones'] if z['lower']>close]
        rays=[{'role':'red' if r['upper'] else 'green','ray':r['ray']} for r in private['proposals']['strict']]
        samples.append({'datasetId':identity,'timeframe':tf,'cutoff':cutoff,'kind':'engine_selected_diagnostic',
            'engine':{'rays':rays,'resistances':sorted(levels)}})
    # Fixed seed; no inspection of entry or outcome files for controls.
    choices=[(s,tf) for s,v in sorted(imports.items()) if v.get('id') for tf in ('4h','1D')]
    chosen=random.Random('workbench-controls-20261022').sample(choices,min(controls,len(choices)))
    for symbol,tf in sorted(chosen):
        identity=imports[symbol]['id']
        if identity!=cached_id:
            dataset=read_dataset(identity);sources=source_bars(dataset);cached_id=identity
        rows=sources[tf];indices=[i for i,b in enumerate(rows) if b.end>=rows[0].time+365*86400]
        i=random.Random(f'workbench-control|{symbol}|{tf}').choice(indices);cutoff=rows[i].end;known=rows[:i+1]
        pairs=list(source_grid(rows[0].time,cutoff,tf));by_pair={p:n for n,p in enumerate(pairs)}
        geometry=IncrementalGeometry(known,symbol,tf,'strict',[by_pair[(b.time,b.end)] for b in known])
        # Proposals at the random endpoint use only known confirmed pivots.
        proposals=geometry.proposals(i)
        proposals=sorted(proposals,key=lambda c:(-c['count'],-c['ray']['b_index'],c['id']))
        rays=[]
        for upper in (True,False):
            candidate=next((c for c in proposals if c['upper']==upper),None)
            if candidate:rays.append({'role':'red' if upper else 'green','ray':candidate['ray']})
        context=StrategyContext({t:[b for b in data if b.end<=cutoff] for t,data in sources.items()},cutoff)
        levels=[z['lower'] for z in context.known_context(cutoff)['zones'] if z['lower']>known[-1].close]
        samples.append({'datasetId':identity,'timeframe':tf,'cutoff':cutoff,'kind':'fixed_random_control',
            'engine':{'rays':rays,'resistances':sorted(levels)}})
    # Group immutable dataset reads for bounded preparation memory and I/O.
    samples.sort(key=lambda s:(s['datasetId'],s['timeframe'],s['cutoff']))
    identity=register(samples,label=f'Sichtprüfung · {len(samples)-len(chosen)} Diagnosefälle + {len(chosen)} Zufallsfälle')
    print(json.dumps({'packId':identity,'cases':len(samples),'controls':len(chosen),'humanLabelsCreated':0}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True);p.add_argument('--controls',type=int,default=20)
    a=p.parse_args();prepare(a.root,a.controls)
