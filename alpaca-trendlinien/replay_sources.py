"""Bounded, ephemeral native-chart sources. A replay keeps its original warmup."""
from collections import OrderedDict
from copy import deepcopy
import secrets
import threading

MAX_SOURCES=2
MAX_BARS=100000
_sources=OrderedDict()
_lock=threading.RLock()


def clear():
    with _lock:_sources.clear()


def covered(identity,symbol,cutoff):
    with _lock:
        value=_sources.get(identity)
        if not value or value['symbol']!=symbol or cutoff>value['through']:return None
        if any(len(rows)<3 or rows[2].end>cutoff for rows,_ in value['sources'].values()):return None
        # Rejected provider rows have no retained causal timestamp. Re-read the
        # requested prefix rather than letting later quality flags affect it.
        if any(meta.get('quality',{}).get('rejected',0) for _,meta in value['sources'].values()):return None
        _sources.move_to_end(identity)
        return {tf:(list(rows),{**deepcopy(meta),'mode':'replay-cache','cached':True}) for tf,(rows,meta) in value['sources'].items()}


def remember(symbol,sources,cutoff,identity=None):
    """Append only after verifying every overlap; revisions start another source."""
    with _lock:
        old=_sources.get(identity)
        merged={}
        compatible=bool(old and old['symbol']==symbol and set(old['sources'])==set(sources))
        for tf,(rows,meta) in sources.items():
            if compatible:
                previous,previous_meta=old['sources'][tf]
                by_time={b.time:b for b in rows}
                old_times={b.time for b in previous}
                overlap=[b for b in previous if b.time in by_time]
                convention=('feed','adjustment','normalization')
                if not rows or rows[0].time<previous[0].time or not overlap or any(by_time[b.time]!=b for b in overlap) or any(meta.get(k)!=previous_meta.get(k) for k in convention):
                    compatible=False
                # A previously known candle may not disappear from the overlap.
                elif any(b.time>=rows[0].time and b.end<=min(previous[-1].end,rows[-1].end) and b.time not in by_time for b in previous):
                    compatible=False
                elif any(previous[0].time<=b.time<=previous[-1].time and b.time not in old_times for b in rows):
                    compatible=False
                else:merged[tf]=(list(previous)+[b for b in rows if b.time>previous[-1].time],deepcopy(meta))
        if not compatible or sum(len(r) for r,_ in merged.values())>MAX_BARS:
            if sum(len(r) for r,_ in sources.values())>MAX_BARS:
                return None,{tf:(list(rows),deepcopy(meta)) for tf,(rows,meta) in sources.items()}
            identity=secrets.token_hex(16)
            compatible=False
            merged={tf:(list(rows),deepcopy(meta)) for tf,(rows,meta) in sources.items()}
        through=max(cutoff,old['through']) if compatible else cutoff
        _sources[identity]={'symbol':symbol,'through':through,'sources':merged}
        _sources.move_to_end(identity)
        while len(_sources)>MAX_SOURCES:_sources.popitem(last=False)
        return identity,{tf:(list(rows),deepcopy(meta)) for tf,(rows,meta) in merged.items()}
