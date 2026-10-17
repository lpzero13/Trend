"""Immutable local analysis snapshots; no provider or account writes."""
from collections import OrderedDict
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import re
import threading

from alpaca import ROOT, NY, DataError
from settings import data_dir

_lock = threading.Lock()
_analyses = OrderedDict()


def remember(payload):
    material = {k: payload[k] for k in ("symbol", "analysisCutoff", "rulesVersion", "charts", "lanes")}
    identity = hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()[:24]
    payload["analysisId"] = identity
    with _lock:
        _analyses[identity] = deepcopy(payload)
        _analyses.move_to_end(identity)
        while len(_analyses) > 32:
            _analyses.popitem(last=False)
    return identity


def snapshot_path(identity):
    if not isinstance(identity, str) or not re.fullmatch(r"[a-f0-9]{24}", identity):
        raise DataError("Ungültige Stand-ID.", 400)
    return data_dir(ROOT) / "snapshots" / (identity + ".json")


def read_snapshot(identity):
    path = snapshot_path(identity)
    try:
        result = json.loads(path.read_text("utf-8"))
        if result["id"] != identity or result["basis"] != "bars":
            raise ValueError("Invalid snapshot")
        return result
    except (OSError, ValueError, KeyError):
        raise DataError("Dieser gespeicherte Stand ist nicht verfügbar.", 404) from None


def save_snapshot(identity):
    path = snapshot_path(identity)
    with _lock:
        if path.exists():
            return read_snapshot(identity)
        payload = _analyses.get(identity)
        if payload is None:
            raise DataError("Der angezeigte Stand ist nicht mehr im Server-Speicher. Bitte zuerst die Analyse neu laden.", 409)
        valid_from = max(source["lastClose"] for source in payload["sources"].values())
        result = {"id": identity, "basis": "bars", "symbol": payload["symbol"],
            "createdAt": datetime.now(timezone.utc).isoformat(), "validFrom": valid_from,
            "analysisCutoff": payload["analysisCutoff"], "rulesVersion": payload["rulesVersion"],
            "label": payload["symbol"] + " · " + datetime.fromtimestamp(payload["analysisCutoff"], NY).strftime("%d.%m.%Y %H:%M ET"),
            "payload": deepcopy(payload)}
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(result, ensure_ascii=False, allow_nan=False), "utf-8")
        temporary.replace(path)
        return result


def list_snapshots(symbol):
    result = []
    folder = data_dir(ROOT) / "snapshots"
    for path in sorted(folder.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            item = read_snapshot(path.stem)
            if item["symbol"] == symbol:
                result.append({k: item[k] for k in ("id", "symbol", "createdAt", "analysisCutoff", "validFrom", "label", "rulesVersion")})
        except DataError:
            continue
        if len(result) == 100:
            break
    return result
