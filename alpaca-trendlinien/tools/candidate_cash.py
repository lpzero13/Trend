"""Joint cash-constrained retest and five matched-control portfolios; offline."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from datasets import read_dataset,digest
from workbench_portfolio import CloseMarks,ledger
from workbench_reviews import put
from database import connection
from tools.complete_study_import import write


def run(root):
    root=Path(root);contract=json.loads((root/'contract.json').read_text('utf-8'))
    records=[];contexts={}
    for p in sorted((root/'stocks').glob('*.json')):
        b=json.loads(p.read_text('utf-8'))
        if b['contractHash']!=digest(contract) or b['checksum']!=digest({k:v for k,v in b.items() if k!='checksum'}):raise ValueError('Changed research block')
        records.extend(b['records'])
        d=read_dataset(b['datasetId']);contexts[d['id']]=SimpleNamespace(fine=CloseMarks(d['material']['bars']['5m']))
    boundary=int(datetime(2023,12,31,23,59,tzinfo=timezone.utc).timestamp())
    start=min(r['entryAt'] for r in records);results=[]
    for name,phase in [('2021-2023',{'startAt':start,'endAt':boundary}),('2024-2026',{'startAt':boundary+1,'endAt':contract['endAt']})]:
        rs=[r for r in records if r['phase']==name]
        for cohort in ('all_actual','matched_actual',*('control_'+str(i) for i in range(5))):
            es=[]
            for r in rs:
                if cohort!='all_actual' and len(r['controls'])!=5:continue
                c=r if cohort.endswith('actual') else r['controls'][int(cohort[-1])]
                e=r['entry'] if cohort.endswith('actual') else {k:v for k,v in c.items() if k not in ('outcomes','naturalPaths')}
                es.append({**e,'datasetId':r['datasetId'],'paths':c['naturalPaths']})
            for model in ('fixed','higher_low'):
                value=ledger(es,contexts,phase,model)
                key=name+'/'+cohort+'/'+model
                write(root/'cash'/f'{name}-{cohort}-{model}.json',value)
                # Independent bookkeeping: quantities and pre/post cash, not a second call to simulate.
                trades=value['trades'];cash=value['initialCapital']
                movements=sorted([(t['openedAt'],1,-t['quantity']*t['entryFill']) for t in trades]+
                    [(t['exitAt'],0,t['quantity']*t['exitFill']) for t in trades if t['exitAt']])
                for _,_,amount in movements:cash+=amount
                if abs(cash-value['cash'])>1e-7:raise AssertionError('Cash reconciliation')
                for t in trades:
                    if t['plannedRiskUSD']>t['equityAtEntry']*.01+1e-7:raise AssertionError('Risk budget')
                    if t['quantity']*t['entryFill']>t['equityAtEntry']*.25+1e-7:raise AssertionError('Allocation budget')
                results.append({'key':key,'phase':name,'cohort':cohort,'model':model,
                    **{k:v for k,v in value.items() if k not in ('trades','skipped','equity')},
                    'skippedReasons':dict(Counter(x['reason'] for x in value['skipped']))})
    gaps=[]
    for r in records:
        for model,p in r['naturalPaths'].items():
            if p['status']=='unknown':gaps.append({'entryId':r['id'],'symbol':r['symbol'],'model':model,'missingAt':p.get('missingAt'),'reason':p.get('reason'),'datasetId':r['datasetId']})
    result={'contractHash':digest(contract),'items':results,'gaps':gaps,'cashVerified':len(results),
            'meaning':'Separate full and matched cohorts; five random portfolios, never five times the capital. Missing held paths halt the ledger; no complete ROI then.'}
    write(root/'cash-summary.json',result)
    with connection() as db:put(db,'cw:cash:'+digest(contract)[:32],result)
    print(json.dumps({'ledgers':len(results),'statuses':dict(Counter(r['status'] for r in results)),'gaps':len(gaps)}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True);run(p.parse_args().root)
