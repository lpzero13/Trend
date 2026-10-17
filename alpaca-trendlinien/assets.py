"""Read-only Alpaca listed-US-equity directory. No order/account endpoints."""
import json
import re
import threading
import time
import urllib.error
import urllib.request

from alpaca import ROOT, DataError, credentials
from settings import data_dir

_lock = threading.Lock()
_catalog = None
LISTED_EXCHANGES = {"NYSE", "NASDAQ", "ARCA", "AMEX", "BATS", "NYSEARCA"}


def normalize_assets(rows):
    result = {}
    for row in rows:
        symbol = row.get("symbol", "")
        if (row.get("status") == "active" and row.get("class") == "us_equity"
                and row.get("exchange") in LISTED_EXCHANGES
                and re.fullmatch(r"[A-Z][A-Z0-9./-]{0,29}", symbol)):
            result[symbol] = {"symbol": symbol, "name": row.get("name", symbol),
                              "exchange": row["exchange"], "tradable": bool(row.get("tradable"))}
    return sorted(result.values(), key=lambda a: a["symbol"])


def directory():
    global _catalog
    with _lock:
        path = data_dir(ROOT) / "assets.json"
        if _catalog is None and path.exists():
            try:
                _catalog = json.loads(path.read_text("utf-8"))
            except (ValueError, OSError):
                pass
        if _catalog and 0 <= time.time() - _catalog["fetchedAt"] < 86400:
            return _catalog, False
        key, secret = credentials()
        # Keys may belong to either environment; these are the only two allowed hosts.
        for host in ("https://paper-api.alpaca.markets", "https://api.alpaca.markets"):
            request = urllib.request.Request(host + "/v2/assets?status=active&asset_class=us_equity",
                headers={"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}, method="GET")
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    rows = json.load(response)
                if not isinstance(rows, list):
                    raise ValueError("Unexpected directory")
                items = normalize_assets(rows)
                if not items:
                    raise ValueError("Empty directory")
                _catalog = {"fetchedAt": time.time(), "items": items}
                path.parent.mkdir(parents=True, exist_ok=True)
                temporary = path.with_suffix(".tmp")
                temporary.write_text(json.dumps(_catalog, ensure_ascii=False), "utf-8")
                temporary.replace(path)
                return _catalog, False
            except urllib.error.HTTPError as exc:
                if exc.code in (401, 403):
                    continue
                break
            except (OSError, ValueError):
                break
        if _catalog:
            return _catalog, True
        raise DataError("Das Aktienverzeichnis konnte nicht geladen werden. Bitte erneut versuchen.", 503)


def search_assets(query="", exchange="", offset=0, symbols=None):
    catalog, stale = directory()
    words = query.casefold().split()
    items = [a for a in catalog["items"]
             if (not exchange or a["exchange"] == exchange)
             and (symbols is None or a["symbol"] in symbols)
             and all(word in (a["symbol"] + " " + a["name"]).casefold() for word in words)]
    if query.strip():
        q = query.strip().upper()
        items.sort(key=lambda a: (a["symbol"] != q, not a["symbol"].startswith(q), a["symbol"]))
    return {"items": items[offset:offset + 100], "total": len(items), "offset": offset,
            "catalogTotal": len(catalog["items"]), "fetchedAt": catalog["fetchedAt"], "stale": stale,
            "exchanges": sorted({a["exchange"] for a in catalog["items"]})}


def cached_asset_name(symbol):
    """Decorate charts without ever blocking their load on a catalog network request."""
    catalog = _catalog
    if catalog is None:
        try:
            catalog = json.loads((data_dir(ROOT) / "assets.json").read_text("utf-8"))
        except (OSError, ValueError):
            return None
    return next((a["name"] for a in catalog.get("items", []) if a["symbol"] == symbol), None)
