"""Bounded web-only memoization of exact causal lane inputs; no research state."""
from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
import threading

MAX_ENTRIES=32
MAX_BYTES=8*1024*1024  # Serialized lane budget; no full input history retained.
_values=OrderedDict()
_lock=threading.RLock()
_bytes=0
_hits=0
_misses=0


def clear():
    global _bytes,_hits,_misses
    with _lock:
        _values.clear();_bytes=_hits=_misses=0


def info():
    with _lock:return {'entries':len(_values),'serializedBytes':_bytes,'hits':_hits,'misses':_misses}


def lane(context,rows,compute):
    """Hash *every* supplied OHLCV bar, not merely length/last candle."""
    global _bytes,_hits,_misses
    raw=json.dumps([(b.time,b.end,b.open,b.high,b.low,b.close,b.volume) for b in rows],
                   separators=(',',':'),allow_nan=False).encode()
    key=(context,hashlib.sha256(raw).digest())
    with _lock:
        if key in _values:
            _hits+=1;_values.move_to_end(key)
            return deepcopy(_values[key][0])
        _misses+=1
    value=compute()  # Exceptions are never cached; concurrent misses may compute twice.
    size=len(json.dumps(value,separators=(',',':'),allow_nan=False).encode())
    if size<=MAX_BYTES:
        with _lock:
            old=_values.pop(key,None)
            if old:_bytes-=old[1]
            _values[key]=(deepcopy(value),size);_bytes+=size
            while len(_values)>MAX_ENTRIES or _bytes>MAX_BYTES:
                _,(_,removed)=_values.popitem(last=False);_bytes-=removed
    return value
