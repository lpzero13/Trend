"""Independent bookkeeping, immutable bindings and reproduction of the broad study."""
import argparse
from bisect import bisect_right
import json
from pathlib import Path
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fan_geometry import stable_id
from robustness_study import validate_plan, window_root, _cost_ledger
from screening_portfolio import compact
from strategy_screen import read, load_task, task_path, load_fold
from tools.verify_strategy_screen import verify_cash


def verify_marks(value,contexts,period,costs,datasets):
    """Revalue accepted cash flows at EVERY 5m mark, not the sparse saved curve.

    No call to simulate/mark, and no inference of drawdown from a curve that
    intentionally omits some peaks. This checks valuation, not signal selection.
    """
    from lab_metrics import expected_grid
    trades=value['trades'];opens={};releases=[]
    for i,t in enumerate(trades):
        opens.setdefault(t['openedAt'],[]).append(i)
        if t['exitAt'] is not None:releases.append((t['exitAt'],i))
    releases.sort();released=0
    cutoff=value['observedThrough']
    stamps={t+300 for t in expected_grid(period['startAt'],period['endAt'])} if value['eligibleSignals'] else set()
    # Reconstruct the producer's exact sampled clock: completed 5m bars plus
    # ALL decision timestamps (accepted and rejected). A gap exit at 09:30
    # does not by itself add a valuation sample to the closed-bar clock.
    stamps.update(opens);stamps.update(t['at'] for t in value['skipped'])
    stamps.add(min(period['endAt'],cutoff))
    indexes={s:(contexts[did].fine,list(contexts[did].fine.ends)) for s,did in datasets.items()}
    cash=value['initialCapital'];peak=cash;worst=0.;active=set();last=cash
    side=costs['spread_bps']/20000+costs['slippage_bps']/10000
    for at in sorted(t for t in stamps if t<=cutoff):
        while released<len(releases) and releases[released][0]<=at:
            _,i=releases[released];t=trades[i]
            active.remove(i);cash+=t['quantity']*t['exitFill']-costs['fee_per_order'];released+=1
        for i in opens.get(at,[]):
            t=trades[i]
            active.add(i);cash-=t['quantity']*t['entryFill']+costs['fee_per_order']
        last=cash
        for i in active:
            t=trades[i];fine,ends=indexes[t['symbol']];pos=bisect_right(ends,at)-1
            price=fine[pos].close if pos>=0 and ends[pos]>t['openedAt'] else t['entryFill']/(1+side)
            last+=t['quantity']*price
        peak=max(peak,last);worst=min(worst,100*(last/peak-1))
    if abs(last-value['markedEquity'])>1e-7 or abs(worst-value['max5mSampledDrawdownPct'])>1e-7:
        raise AssertionError('Independent 5m valuation/drawdown differs')
    expected=100*(last/value['initialCapital']-1)
    if value['status']=='incomplete':
        if value['markedReturnPct'] is not None:raise AssertionError('incomplete return advertised')
    elif abs(expected-value['markedReturnPct'])>1e-8:raise AssertionError('return arithmetic')


def verify(root):
    root=Path(root);p=validate_plan(read(root/'plan.json'));count=blocks=unavailable=cases=0
    source=read(root/'selection.json')
    if source['planId']!=p['id'] or source['primary']!=p['policies'][0] or stable_id({k:v for k,v in source.items() if k!='id'})!=source['id']:
        raise AssertionError('Changed selection')
    for fold in p['folds']['validation']:
        dest=window_root(root,fold);r=read(dest/'result.json')
        if r['planId']!=p['id'] or r['checksum']!=stable_id({k:v for k,v in r.items() if k!='checksum'}):raise AssertionError('result checksum')
        for symbol in p['symbols']:
            block=load_task(task_path(dest,'validation',symbol,fold),p);blocks+=1;cases+=len(block['pilot']['cases'])
            if not block['quality']['passedStructural']:raise AssertionError('structural quality')
            unavailable+=block['availability']!='available'
            if block['availability']!='available' and block['pilot']['cases']:raise AssertionError('unavailable signals')
        original,contexts,period=load_fold(dest,p,'validation',fold)
        for name in p['cohorts']:
            for scenario in p['costScenarios']:
                value=read(dest/'ledgers'/f'{name}-{scenario["name"]}.json.gz')
                verify_cash(value,scenario['fee']);count+=1
                costs={'spread_bps':5.*scenario['multiplier'],'slippage_bps':5.*scenario['multiplier'],'fee_per_order':scenario['fee']}
                verify_marks(value,contexts,period,costs,p['datasets'])
                if compact(value)!=r['cohorts'][name]['scenarios'][scenario['name']]:raise AssertionError('summary differs')
        for f in (dest/'validation').glob('control-ledger-*.json.gz'):
            value=read(f);verify_cash(value,0.);count+=1
            verify_marks(value,contexts,period,p['costs'],p['datasets'])
        fresh=_cost_ledger(original,contexts,period,p['costScenarios'][0])
        if compact(fresh)!=r['cohorts']['all']['scenarios']['base']:raise AssertionError('nonreproducible base portfolio')
        returns=[v['markedReturnPct'] for v in r['controls']['items'] if v['markedReturnPct'] is not None]
        expected=sorted(returns)[__import__('math').ceil(.9*len(returns))-1] if returns else None
        if expected!=r['controls']['q90ReturnPct']:raise AssertionError('control quantile')
    return {'passed':True,'cacheBlocks':blocks,'unavailableWindows':unavailable,'signalCases':cases,'cashLedgers':count,
            'allBasePortfoliosReproduced':True,'independentEvery5mValuationAndDrawdown':True,'selectionUnchanged':True,'providerCalls':0}


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--root',required=True);args=a.parse_args()
    with patch('alpaca._request',side_effect=AssertionError('Verifier offline')) as request:
        result=verify(args.root);request.assert_not_called()
    print(json.dumps(result,ensure_ascii=False))
