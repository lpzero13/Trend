"""Adapt frozen complete-study paths to the existing cash ledger, without filtering gaps."""
from array import array
from types import SimpleNamespace
from strategy_portfolio import simulate


class CloseMarks:
    """Compact ledger-only 5m marks. Not an OHLC source for signal calculations."""
    def __init__(self,bars):
        self.ends=array('q',(b['end'] for b in bars));self.closes=array('d',(b['close'] for b in bars))
    def __len__(self):return len(self.ends)
    def __iter__(self):
        return (SimpleNamespace(end=t,close=c) for t,c in zip(self.ends,self.closes))
    def __getitem__(self,i):return SimpleNamespace(end=self.ends[i],close=self.closes[i])


def adapt(e,p):
    common={'entryId':e['id'],'entryAt':e['entryAt'],'entryFill':p.get('buy'),
        'initialStop':e['initialStop'],'initialRisk':p.get('initialRisk'),
        'exitAt':p.get('fillBarAt',0)+300 if p['status']=='closed' else None,
        'exitFill':p.get('sell'),'exitReason':p.get('reason')}
    if p['status']=='invalid' or p.get('buy') is None:
        return {**common,'status':'unavailable','reason':p.get('reason','entry_unavailable')}
    if p['status']=='unknown':return {**common,'status':'censored','missingAt':p['missingAt']}
    if p['status'] not in ('closed','open'):raise ValueError('Unsupported path convention')
    return {**common,'status':p['status']}


def ledger(entries,contexts,phase,model):
    # Events from different families are deliberately not pooled into a strategy.
    paths=[adapt(e,e['paths'][model]) for e in entries]
    return simulate(entries,paths,contexts,phase,{'spread_bps':5.,'slippage_bps':5.,'fee_per_order':0.})
