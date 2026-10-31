"""Recompute paired table membership and R summaries directly from source blocks."""
import argparse
from collections import defaultdict
import csv
import json
import math
from pathlib import Path
import statistics
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from entry_exit_comparison import binding, MODELS
from fan_geometry import stable_id
from robustness_study import validate_plan, window_root
from strategy_screen import read, write, load_task, task_path
from tools.verify_strategy_screen import verify_cash


def verify(root):
    root=Path(root);p=read(root/'plan.json');r=read(root/'comparison.json')
    if stable_id({k:v for k,v in p.items() if k!='id'})!=p['id'] or p['analysisCode']!=binding():raise AssertionError('comparison binding')
    source=Path(p['sourceRoot']);sp=validate_plan(read(source/'plan.json'))
    if p['sourcePlanId']!=sp['id'] or r['planId']!=p['id']:raise AssertionError('source binding')
    paired=defaultdict(list);window_paired=defaultdict(list);records={};seen=set();counts=defaultdict(int)
    for fold in sp['folds']['validation']:
        for symbol in sp['symbols']:
            b=load_task(task_path(window_root(source,fold),'validation',symbol,fold),sp)
            for c in b['pilot']['cases']:
                if c['id'] in seen:raise AssertionError('duplicate source case')
                seen.add(c['id']);s=c['signal'];key=s['family']+':'+s['cohort'];counts[key]+=1
                common=c['entry']['status']=='filled' and all(c['paths'][f'{m}:hard_stop:40']['status']=='closed' for m in MODELS)
                if common:
                    paired[key].append(c);window_paired[fold['name'],key].append(c)
                for m in MODELS:
                    path=c['paths'][f'{m}:hard_stop:40']
                    records[c['id'],m]={'family':s['family'],'cohort':s['cohort'],'subtype':s['subtype'],'symbol':symbol,
                        'window':fold['name'],'pathStatus':path['status'],'netR':path.get('netR'),'commonComplete':common}
    def check_tables(groups,lookup):
        for key,row in groups.items():
            cases=lookup.get(key,[])
            if row['commonComplete']!=len(cases):raise AssertionError('paired membership count')
            if row['sameEntryIdsHash']!=stable_id(sorted(c['id'] for c in cases)):raise AssertionError('different entry IDs')
            for m in MODELS:
                out=row['models'][m]['sameEntries'];values=[c['paths'][f'{m}:hard_stop:40']['netR'] for c in cases]
                if out['n']!=len(values):raise AssertionError('exit denominator')
                if values:
                    for actual,expected in ((out['meanNetR'],sum(values)/len(values)),(out['medianNetR'],statistics.median(values)),
                                            (out['winPct'],100*sum(v>0 for v in values)/len(values))):
                        if not math.isclose(actual,expected,abs_tol=1e-10,rel_tol=1e-10):raise AssertionError('independent paired table arithmetic')
    check_tables(r['groups'],paired)
    if {k:v['signals'] for k,v in r['groups'].items()}!=dict(counts):raise AssertionError('group totals')
    for w in r['windows']:
        check_tables(w['groups'],{key:cases for (fold,key),cases in window_paired.items() if fold==w['fold']['name']})
    csv_seen=set()
    with (root/'entry-exit-cases.csv').open(encoding='utf-8-sig',newline='') as stream:
        for row in csv.DictReader(stream):
            key=(row['caseId'],row['exitModel']);expected=records[key]
            if key in csv_seen:raise AssertionError('CSV duplicate')
            csv_seen.add(key)
            for k,v in expected.items():
                actual=float(row[k]) if k=='netR' and row[k] else None if k=='netR' else row[k]=='True' if k=='commonComplete' else row[k]
                if actual!=v:raise AssertionError('CSV/source mismatch: '+k)
    if len(csv_seen)!=len(records):raise AssertionError('CSV omitted source paths')
    ledgers=0
    for f in root.glob('*/ledgers/*.json.gz'):
        verify_cash(read(f),0.);ledgers+=1
    if ledgers!=168:raise AssertionError('Incomplete comparison matrix')
    result={'passed':True,'sourceCases':len(seen),'csvPaths':len(csv_seen),'pairedGroups':len(r['groups']),
            'cashLedgers':ledgers,'sourceMembershipAndMeansRecomputed':True,'providerCalls':0}
    write(root/'verification.json',result);return result


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--root',required=True);args=a.parse_args()
    with patch('alpaca._request',side_effect=AssertionError('Comparison verifier offline')) as request:
        result=verify(args.root);request.assert_not_called()
    print(json.dumps(result,ensure_ascii=False))
