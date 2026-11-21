"""Fast, read-only local SIP archive lookup and 16-symbol LRU chart cache.

Serves 1h/4h/1D bars directly from local Parquet datasets without materializing
~200k 5m execution bars, cutting initial chart opens for all 802 archived US
stocks from 15-40s down to ~0.1s (cold) / <2ms (warm).
"""
from collections import OrderedDict
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import threading

from models import Bar, DataError
from parquet_store import block_path, connect
from settings import data_dir

MAX_CACHED_SYMBOLS = 16
UTC = timezone.utc

_LOCK = threading.RLock()
_INDEX_STATE = {}  # root_str -> (dir_stamp, {symbol: meta_dict})
_BARS_CACHE = OrderedDict()  # (root_str, dataset_id) -> (manifest_stamp, sources_dict, meta_dict)


def clear():
    with _LOCK:
        _INDEX_STATE.clear()
        _BARS_CACHE.clear()


def _dir_stamp(ds_dir: Path):
    try:
        st = ds_dir.stat()
        count = sum(1 for _ in ds_dir.glob("*.json"))
        return (st.st_mtime_ns, count)
    except OSError:
        return None


def _build_index(root: Path):
    ds_dir = root / "datasets"
    if not ds_dir.is_dir():
        return {}
    best = {}
    for path in ds_dir.glob("*.json"):
        if path.is_symlink():
            continue
        try:
            raw = json.loads(path.read_text("utf-8"))
        except (OSError, ValueError):
            continue
        mat = raw.get("material") or {}
        if mat.get("dataKind") == "synthetic":
            continue
        sym = (mat.get("symbol") or "").upper().strip()
        ds_id = raw.get("id")
        if not sym or not ds_id:
            continue
        sources = raw.get("sources") or {}
        if not all(tf in sources for tf in ("1h", "4h", "1D")):
            continue
        last_close = max((int(sources[tf].get("lastClose") or 0) for tf in ("4h", "1D")), default=0)
        first_bar = min((int(sources[tf].get("first") or 0) for tf in ("4h", "1D")), default=0)
        is_sip = 1 if mat.get("feed") == "sip" else 0
        is_split = 1 if mat.get("adjustment") == "split" else 0
        has_storage = 1 if raw.get("storage") else 0
        rank = (is_sip, is_split, has_storage, last_close, -first_bar, ds_id)
        prev = best.get(sym)
        if prev is None or rank > prev["rank"]:
            best[sym] = {
                "symbol": sym,
                "datasetId": ds_id,
                "feed": mat.get("feed") or "sip",
                "adjustment": mat.get("adjustment") or "split",
                "session": mat.get("session") or "",
                "lastClose": last_close,
                "firstBar": first_bar,
                "rank": rank,
            }
    return best


def lookup_symbol(symbol: str, *, root=None):
    """Return best local SIP dataset metadata for `symbol`, or None."""
    sym = (symbol or "").upper().strip()
    if not sym:
        return None
    base = Path(root) if root else data_dir()
    ds_dir = base / "datasets"
    stamp = _dir_stamp(ds_dir)
    if stamp is None:
        return None
    key = str(base.resolve())
    with _LOCK:
        cached = _INDEX_STATE.get(key)
        if cached is None or cached[0] != stamp:
            idx = _build_index(base)
            _INDEX_STATE[key] = (stamp, idx)
        else:
            idx = cached[1]
        rec = idx.get(sym)
        return dict(rec) if rec else None


def _read_chart_frames(base: Path, dataset_id: str):
    ds_path = base / "datasets" / f"{dataset_id}.json"
    if not ds_path.is_file():
        return None, None
    st = ds_path.stat()
    mstamp = (st.st_size, st.st_mtime_ns)
    cache_key = (str(base.resolve()), dataset_id)
    with _LOCK:
        hit = _BARS_CACHE.get(cache_key)
        if hit is not None and hit[0] == mstamp:
            _BARS_CACHE.move_to_end(cache_key)
            return hit[1], hit[2]

    manifest = json.loads(ds_path.read_text("utf-8"))
    mat = manifest.get("material") or {}
    sources_meta = manifest.get("sources") or {}
    storage = manifest.get("storage")

    frames = {"1h": [], "4h": [], "1D": []}
    if storage:
        paths = []
        for entry in storage.get("blocks", []):
            p = block_path(base, entry["path"])
            if not p.is_file():
                return None, None
            paths.append(str(p))
        if not paths:
            return None, None
        with connect() as con:
            rows = con.execute(
                'SELECT timeframe, time, "end", open, high, low, close, volume '
                "FROM read_parquet(?) WHERE timeframe IN ('1h','4h','1D') ORDER BY timeframe, time",
                [paths],
            ).fetchall()
        for tf, t, end, o, h, l, c, v in rows:
            frames[tf].append(Bar(int(t), int(end), float(o), float(h), float(l), float(c), float(v)))
    else:
        raw_bars = mat.get("bars") or {}
        for tf in ("1h", "4h", "1D"):
            frames[tf] = [Bar(**b) for b in raw_bars.get(tf, [])]

    if any(len(frames[tf]) < 3 for tf in ("1h", "4h", "1D")):
        return None, None

    packed = {}
    for tf in ("1h", "4h", "1D"):
        m = deepcopy(sources_meta.get(tf) or {})
        m.setdefault("quality", {"rejected": 0, "duplicates": 0, "unfinished": 0})
        m.update(
            feed=mat.get("feed") or "sip",
            adjustment=mat.get("adjustment") or "split",
            cached=True,
            mode="local-sip-archive",
            warning=None,
        )
        packed[tf] = (frames[tf], m)

    meta = {
        "symbol": mat.get("symbol"),
        "datasetId": dataset_id,
        "feed": mat.get("feed") or "sip",
        "adjustment": mat.get("adjustment") or "split",
        "session": mat.get("session") or "",
        "lastClose": max(frames["4h"][-1].end, frames["1D"][-1].end),
    }

    with _LOCK:
        _BARS_CACHE[cache_key] = (mstamp, packed, meta)
        _BARS_CACHE.move_to_end(cache_key)
        while len(_BARS_CACHE) > MAX_CACHED_SYMBOLS:
            _BARS_CACHE.popitem(last=False)
    return packed, meta


def load_local_chart_sources(symbol: str, cutoff_ts: int, *, root=None):
    """Return (datasets_dict, meta) for an archived symbol <= cutoff_ts, or (None, None)."""
    info = lookup_symbol(symbol, root=root)
    if info is None:
        return None, None
    base = Path(root) if root else data_dir()
    try:
        packed, meta = _read_chart_frames(base, info["datasetId"])
    except (OSError, ValueError, KeyError, DataError):
        return None, None
    if packed is None:
        return None, None
    out = {}
    for tf, (bars, m) in packed.items():
        sliced = [b for b in bars if b.end <= cutoff_ts]
        if len(sliced) < 3:
            return None, None
        out[tf] = (sliced, dict(m))
    return out, dict(meta)
