import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from exit_followup import prepare,checked,build,evaluate
from strategy_run_lock import study_lock
from strategy_screen import read

def main():
    ap=argparse.ArgumentParser(description='Causal Safety follow-up on frozen independent entry cases; offline only')
    ap.add_argument('root');ap.add_argument('--source');ap.add_argument('--symbols');ap.add_argument('--workers',type=int,default=2)
    ap.add_argument('--phase',choices=('prepare','build','evaluate','all'),default='all');a=ap.parse_args()
    def progress(v):print(json.dumps(v,ensure_ascii=False),flush=True)
    with study_lock(a.root):
        if a.phase in ('prepare','all'):
            if not a.source:ap.error('--source required')
            p=prepare(a.root,a.source,a.symbols.split(',') if a.symbols else None)
        else:p=checked(read(Path(a.root)/'plan.json'))
        progress({'planId':p['id'],'symbols':len(p['symbols']),'phase':a.phase})
        if a.phase in ('build','all'):build(a.root,p,a.workers,progress)
        if a.phase in ('evaluate','all'):
            r=evaluate(a.root,p);progress({'cases':r['cases'],'results':str(Path(a.root)/'results.json')})

if __name__=='__main__':main()
