"""Immutable normalized datasets for offline causal research and chart inspection."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import uuid

from alpaca import load_bars, TIMEFRAMES
from models import Bar, DataError
from settings import data_dir

SCHEMA = "tori-dataset-1"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def path_for(identity):
    if not isinstance(identity, str) or not re.fullmatch(r"[a-f0-9]{64}", identity):
        raise DataError("Ungültige Dataset-ID.", 400)
    return data_dir() / "datasets" / (identity + ".json")


def save_dataset(symbol, sources, *, provider="Alpaca", feed="iex", adjustment="raw"):
    normalized = {}
    for tf in TIMEFRAMES:
        bars, meta = sources[tf]
        if meta.get("warning") or meta.get("quality", {}).get("rejected", 0):
            raise DataError(f"{symbol}/{tf}: veraltete oder fehlerhafte Daten; kein Forschungsimport.", 422)
        if len(bars) < 3 or any(b.end <= b.time for b in bars):
            raise DataError("Dataset enthält zu wenige oder ungültige Kerzen.", 422)
        if any(a.time >= b.time or a.end > b.time for a, b in zip(bars, bars[1:])):
            raise DataError("Kerzen sind unsortiert oder überlappen sich.", 422)
        normalized[tf] = [asdict(b) for b in bars]
    material = {"schema": SCHEMA, "symbol": symbol, "provider": provider, "feed": feed,
        "adjustment": adjustment, "timezone": "America/New_York", "basis": "bars",
        "session": "provider-native; extended hours possible; conservative daily close at 16 ET",
        "bars": normalized}
    identity = digest(material)
    path = path_for(identity)
    if not path.exists():
        payload = {"id": identity, "material": material, "importedAt": datetime.now(timezone.utc).isoformat(),
            "sources": {tf: meta for tf, (_, meta) in sources.items()}}
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix("."+uuid.uuid4().hex+".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, allow_nan=False), "utf-8")
        temporary.replace(path)
    return identity


def read_dataset(identity):
    try:
        payload = json.loads(path_for(identity).read_text("utf-8"))
        if payload["id"] != identity or payload["material"]["schema"] != SCHEMA or digest(payload["material"]) != identity:
            raise ValueError("checksum")
        return payload
    except (OSError, ValueError, KeyError, TypeError):
        raise DataError("Dataset fehlt oder seine Prüfsumme ist ungültig.", 404) from None


def source_bars(dataset):
    return {tf: [Bar(**b) for b in rows] for tf, rows in dataset["material"]["bars"].items()}


def import_dataset(symbol, history_days=900):
    now = datetime.now(timezone.utc)
    with ThreadPoolExecutor(max_workers=3) as pool:
        pending = {tf: pool.submit(load_bars, symbol, tf, now=now, history_days=history_days) for tf in TIMEFRAMES}
        sources = {tf: result.result() for tf, result in pending.items()}
    return save_dataset(symbol, sources)


def chart_dataset(identity, timeframe, as_of=None, setup=None):
    from analysis_service import build_chart
    from snapshots import remember
    dataset = read_dataset(identity)
    if timeframe not in TIMEFRAMES:
        raise DataError("Ungültiges Dataset-Intervall.",400)
    bars = source_bars(dataset)
    cutoff = datetime.fromisoformat(as_of.replace("Z", "+00:00")) if as_of else datetime.fromtimestamp(max(b.end for b in bars[timeframe]), timezone.utc)
    if cutoff.tzinfo is None:
        raise DataError("Dataset-Zeitpunkt braucht eine Zeitzone.", 400)
    sources = {tf: (rows, {**dataset["sources"][tf], "mode": "immutable-dataset", "cached": True, "warning": None}) for tf, rows in bars.items()}
    payload = build_chart(sources, dataset["material"]["symbol"], timeframe, cutoff,
        datetime.now(timezone.utc), historical=True)
    payload.update(datasetId=identity, provider=dataset["material"]["provider"], feed=dataset["material"]["feed"])
    if setup:
        from research import line_value
        signal=setup["signal"]
        if signal["closedAt"]<=int(cutoff.timestamp()):
            for tf in ("4h","1D"):
                lane=payload["lanes"][tf]
                source=signal if tf=="4h" else signal["features"]["daily"]
                position=len(payload["charts"][tf]["bars"])-1
                for kind in ("red","green"):
                    ray=source[kind]
                    lane[kind]={**ray,"value":line_value(ray,position)} if ray else None
                lane.update(outerRed=[],outerGreen=[],retest=None,status="Originalsignal fixiert")
                lane["event"]={k:signal[k] for k in ("kind","time","closedAt")} if tf=="4h" else None
                if lane["event"]:lane["event"]["price"]=signal["close"]
                lane["sourceClose"]=source["closedAt"]
                close=payload["charts"][tf]["latest"]["close"]
                lane["distance"]=(close-lane["green"]["value"])/close*100 if lane["green"] else None
            payload["researchSetup"]={"eventId":signal["id"],"signalAt":setup.get("signalAt",signal["closedAt"]),
                "variant":setup["variant"],"entryAt":setup.get("entryAt"),"entryPrice":setup.get("entryPrice"),"initialStop":setup.get("initialStop"),"validRisk":setup.get("validRisk",False)}
    remember(payload)
    return payload
