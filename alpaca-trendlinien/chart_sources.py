"""Verified immutable chart inputs, isolated from headless dataset readers."""
from collections import OrderedDict
from copy import deepcopy
from datetime import datetime,timezone
import json
from functools import lru_cache
import threading
import time

from datasets import read_dataset,path_for,data_kind,chart_dataset as original_chart_dataset
from models import Bar,DataError
from settings import data_dir

MAX_DATASETS=2
REVERIFY_SECONDS=600
_cache=OrderedDict()
_lock=threading.RLock()


def clear():
    with _lock:_cache.clear();_manifest_blocks.cache_clear()


@lru_cache(maxsize=4)
def _manifest_blocks(root,path,stamp):
    from parquet_store import block_path
    from pathlib import Path
    m=json.loads(Path(path).read_text(encoding='utf-8'))
    return tuple(block_path(Path(root),b['path']) for b in m.get('storage',{}).get('blocks',[]))


def signature(identity):
    """Detect changed/missing manifests and blocks before using a warm entry."""
    root=data_dir();path=path_for(identity)
    try:
        stat=path.stat();stamp=(stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns,stat.st_ino)
        paths=[path,*_manifest_blocks(str(root),str(path),stamp)]
        return (str(root),identity,tuple((str(p),s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_ino)
                for p in paths for s in [p.stat()]))
    except (OSError,ValueError,KeyError,TypeError):
        raise DataError('Dataset fehlt oder seine Prüfsumme ist ungültig.',404) from None


def sources_for(identity):
    key=signature(identity)
    with _lock:
        item=_cache.get(key)
        if item is None or time.monotonic()-item[0]>=REVERIFY_SECONDS:
            d=read_dataset(identity)  # Full existing checksum verification, including 5m blocks.
            if signature(identity)!=key:raise DataError('Dataset wurde während der Prüfung geändert.',409)
            m=d['material']
            sources={tf:([Bar(**b) for b in bars],deepcopy(d['sources'][tf]))
                     for tf,bars in m['bars'].items() if tf in ('1h','4h','1D')}
            meta={k:m[k] for k in ('symbol','provider','feed','adjustment','session')}
            meta.update(datasetId=identity,dataKind=data_kind(d))
            meta['normalization']=deepcopy(m.get('normalization',{}))
            item=(time.monotonic(),sources,meta);_cache[key]=item
            # Old signatures of the same dataset must not accumulate.
            for old in list(_cache):
                if old!=key and old[:2]==key[:2]:del _cache[old]
        _cache.move_to_end(key)
        while len(_cache)>MAX_DATASETS:_cache.popitem(last=False)
        _,sources,meta=item
        return {tf:(list(rows),deepcopy(m)) for tf,(rows,m) in sources.items()},deepcopy(meta)


def chart_dataset(identity,timeframe,as_of=None,setup=None,*,include_analysis=True):
    # Preserve the existing fixed research-case overlay path exactly.
    if setup is not None:
        return original_chart_dataset(identity,timeframe,as_of,setup,include_analysis=include_analysis)
    from analysis_service import build_chart
    from snapshots import remember
    if timeframe not in ('1h','4h','1D'):raise DataError('Ungültiges Dataset-Intervall.',400)
    sources,meta=sources_for(identity)
    cutoff=datetime.fromisoformat(as_of.replace('Z','+00:00')) if as_of else datetime.fromtimestamp(sources[timeframe][0][-1].end,timezone.utc)
    if cutoff.tzinfo is None:raise DataError('Dataset-Zeitpunkt braucht eine Zeitzone.',400)
    sources={tf:(rows,{**m,'mode':'immutable-dataset','cached':True,'warning':None}) for tf,(rows,m) in sources.items()}
    payload=build_chart(sources,meta['symbol'],timeframe,cutoff,datetime.now(timezone.utc),
                        historical=True,include_analysis=include_analysis)
    payload.update({k:v for k,v in meta.items() if k!='normalization'})
    if meta['dataKind']=='synthetic':payload['company']=meta['symbol']+' · Synthetischer Test'
    if include_analysis:remember(payload)
    return payload
