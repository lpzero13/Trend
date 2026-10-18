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

from alpaca import load_bars
from providers import TIMEFRAMES, AlpacaProvider, fetch_sources
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
        if meta.get("feed",feed)!=feed or meta.get("adjustment",adjustment)!=adjustment:
            raise DataError("Gemischte Feeds oder Kursbereinigungen im Dataset sind nicht erlaubt.",422)
        if meta.get("warning") or meta.get("quality", {}).get("rejected", 0):
            raise DataError(f"{symbol}/{tf}: veraltete oder fehlerhafte Daten; kein Forschungsimport.", 422)
        if len(bars) < 3 or any(b.end <= b.time for b in bars):
            raise DataError("Dataset enthält zu wenige oder ungültige Kerzen.", 422)
        if any(a.time >= b.time or a.end > b.time for a, b in zip(bars, bars[1:])):
            raise DataError("Kerzen sind unsortiert oder überlappen sich.", 422)
        normalized[tf] = [asdict(b) for b in bars]
    material = {"schema": SCHEMA, "symbol": symbol, "provider": provider, "feed": feed,
        "adjustment": adjustment, "timezone": "America/New_York", "basis": "bars",
        "session": "provider-native; extended hours possible; daily closure follows stored normalization",
        "normalization": {tf:meta.get("normalization","external-or-legacy") for tf,(_,meta) in sources.items()},
        "bars": normalized}
    identity = digest(material)
    path = path_for(identity)
    if not path.exists():
        from data_quality import audit
        payload = {"id": identity, "material": material, "importedAt": datetime.now(timezone.utc).isoformat(),
            "quality":audit({tf:rows for tf,(rows,_) in sources.items()},feed=feed,adjustment=adjustment),
            "sources": {tf: meta for tf, (_, meta) in sources.items()}}
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix("."+uuid.uuid4().hex+".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, allow_nan=False), "utf-8")
        temporary.replace(path)
    quality = json.loads(path.read_text("utf-8")).get("quality")
    if quality:
        from database import connection
        summary={**quality,"issues":[{k:v for k,v in issue.items() if k!="examples"} for issue in quality["issues"]]}
        with connection() as db:
            db.execute("INSERT OR IGNORE INTO dataset_quality VALUES(?,?)",(identity,json.dumps(summary)))
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


def import_dataset(symbol, history_days=900, *, progress=None):
    from storage import preflight
    preflight(history_days=history_days, symbols=1)
    now = datetime.now(timezone.utc)
    extra = {"progress":progress} if progress else {}
    provider = AlpacaProvider(load_bars)
    sources = fetch_sources(provider,symbol,now=now,history_days=history_days,**extra)
    identity = save_dataset(symbol, sources)
    from operations import record_dataset
    # Use this import's source metadata, even when identical candles reuse an older immutable dataset.
    dataset = read_dataset(identity)
    record_dataset({**dataset,"sources":{tf:meta for tf, (_,meta) in sources.items()}}, imported=True)
    return identity


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
        if setup.get("entryMode") == "tori" and signal["closedAt"] > int(cutoff.timestamp()):
            signal=setup["armedSignal"]
        if signal["closedAt"]<=int(cutoff.timestamp()):
            for tf in ("4h","1D"):
                lane=payload["lanes"][tf]
                source=signal if tf=="4h" else signal["features"]["daily"]
                position=len(payload["charts"][tf]["bars"])-1
                for kind in ("red","green"):
                    ray=source[kind]
                    lane[kind]={**ray,"value":line_value(ray,position)} if ray else None
                lane.update(outerRed=[],outerGreen=[],retest=None,status="Tori-Linienstand fixiert" if setup.get("entryMode")=="tori" else "Originalsignal fixiert")
                lane["event"]={k:signal[k] for k in ("kind","time","closedAt")} if tf=="4h" and signal["kind"]!="tori_setup" else None
                if lane["event"]:lane["event"]["price"]=signal["close"]
                lane["sourceClose"]=source["closedAt"]
                close=payload["charts"][tf]["latest"]["close"]
                lane["distance"]=(close-lane["green"]["value"])/close*100 if lane["green"] else None
            payload["researchSetup"]={"eventId":signal["id"],"signalAt":setup.get("signalAt",signal["closedAt"]),
                "variant":setup["variant"],"entryAt":setup.get("entryAt"),"entryPrice":setup.get("entryPrice"),"initialStop":setup.get("initialStop"),"validRisk":setup.get("validRisk",False)}
            if setup.get("entryMode") == "tori":
                state=payload["researchSetup"]
                state["entryMode"]="tori"
                if state["signalAt"] > int(cutoff.timestamp()):
                    state["signalAt"]=None
                    state["initialStop"]=None
                    state["validRisk"]=False
                if state["entryAt"] is None or state["entryAt"] > int(cutoff.timestamp()):
                    state["entryAt"]=state["entryPrice"]=None
    remember(payload)
    return payload
