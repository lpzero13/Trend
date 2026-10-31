"""Post-result contribution sensitivity; exclusions are NEVER future trading rules."""
import argparse,hashlib,json
from pathlib import Path
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from trigger_horizon_research import checked
from screening_portfolio import ledger,compact
from strategy_screen import read,write,load_fold
from tools.verify_strategy_screen import verify_cash
from tools.verify_robustness_study import verify_marks


def stress(source,output):
    source,output=Path(source),Path(output)
    if output.exists():raise ValueError('New diagnostic folder required; preserve old evidence')
    p=checked(read(source/'plan.json'));r=read(source/'results.json')
    tasks=[]
    for w in r['windows']:
        book=w['books']['red_retest:qualified:original_safety:hard_stop:80']['base']
        if book['markedReturnPct'] is None:continue
        winners=sorted(((s,v) for s,v in book['pnlBySymbol'].items() if v>0),key=lambda x:(-x[1],x[0]))
        tasks.append({'fold':w['fold'],'excludeTop1':[s for s,_ in winners[:1]],'excludeTop3':[s for s,_ in winners[:3]]})
    contract={'version':'tori-posthoc-contribution-1','sourcePlanId':p['id'],'sourceEngine':p['engine'],
              'code':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'tasks':tasks,
              'meaning':'Outcome-selected exclusions only to diagnose dependence. Not causal selection, not a deployable filter or independent validation.'}
    write(output/'contract.json',contract);rows=[]
    for task in tasks:
        fold=task['fold'];cases,contexts,period=load_fold(source,p,'validation',fold)
        baseline=next(w for w in r['windows'] if w['fold']['name']==fold['name'])
        for label in ('excludeTop1','excludeTop3'):
            excluded=task[label];values={}
            for h in (40,80):
                policy=next(q for q in p['policies'] if q['family']=='red_retest' and q['model']=='original_safety' and q['stopMode']=='hard_stop' and q['horizon']==h)
                value=ledger([c for c in cases if c['symbol'] not in excluded],contexts,period,policy)
                verify_cash(value,0.);verify_marks(value,contexts,period,p['costs'],p['datasets'])
                write(output/'ledgers'/f'{fold["name"]}-{label}-{h}.json.gz',value);values[str(h)]=compact(value)
            rows.append({'fold':fold['name'],'diagnostic':label,'excluded':excluded,'books':values,
                'baseline40':baseline['books']['red_retest:qualified:original_safety:hard_stop:40']['base']['markedReturnPct'],
                'baseline80':baseline['books']['red_retest:qualified:original_safety:hard_stop:80']['base']['markedReturnPct']})
    result={'sourcePlanId':p['id'],'rows':rows,'verifiedBooks':len(rows)*2,'providerCalls':0,'meaning':contract['meaning']}
    write(output/'results.json',result);return result


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--source',required=True);a.add_argument('--output',required=True);args=a.parse_args()
    with patch('alpaca._request',side_effect=AssertionError('Posthoc diagnostic offline')) as request:
        result=stress(args.source,args.output);request.assert_not_called()
    print(json.dumps({'verifiedBooks':result['verifiedBooks'],'rows':[{'fold':r['fold'],'diagnostic':r['diagnostic'],'excluded':r['excluded'],
          'return40':r['books']['40']['markedReturnPct'],'return80':r['books']['80']['markedReturnPct']} for r in result['rows']]},ensure_ascii=False))
