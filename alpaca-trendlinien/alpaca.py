"""Read-only market-data adapter. Credentials are used only in server-side Alpaca HTTP headers."""
from __future__ import annotations

import json
import math
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from models import Bar, DataError, NY
from settings import data_dir

ROOT = Path(__file__).resolve().parent
NY = ZoneInfo("America/New_York")
UTC = timezone.utc
TIMEFRAMES = {"1h": "1Hour", "4h": "4Hour", "1D": "1Day"}
SECONDS = {"1h": 3600, "4h": 14400, "1D": 86400}
_LOCK = threading.Lock()
_DATA_LOCKS: dict[tuple[str, str], threading.Lock] = {}
_REQUEST_LOCK = threading.Lock()
_REQUEST_TIMES = deque()


def request_slot():
    """One shared per-process budget for chart and worker provider downloads."""
    try:
        budget=max(1,min(1000,int(os.environ.get("TORI_API_REQUESTS_PER_MINUTE","150"))))
    except ValueError:
        budget=150
    while True:
        with _REQUEST_LOCK:
            now=time.monotonic()
            while _REQUEST_TIMES and now-_REQUEST_TIMES[0]>=60:
                _REQUEST_TIMES.popleft()
            if len(_REQUEST_TIMES)<budget:
                _REQUEST_TIMES.append(now)
                return
        time.sleep(.25)


def data_lock(symbol: str, timeframe: str):
    # Serialize only requests for the same file, never unrelated downloads.
    with _LOCK:
        return _DATA_LOCKS.setdefault((symbol, timeframe), threading.Lock())


def credentials() -> tuple[str, str]:
    key = os.environ.get("APCA_API_KEY_ID", "").strip()
    secret = os.environ.get("APCA_API_SECRET_KEY", "").strip()
    if key and secret:
        return key, secret
    config_path = ROOT / "config.local.json"
    config = json.loads(config_path.read_text("utf-8")) if config_path.exists() else {}
    path = Path(os.environ.get("ALPACA_CREDENTIALS_FILE") or config.get("credentials_file")
                or Path.home() / "Desktop" / "Alpaca API.txt")
    try:
        blob = path.read_bytes()
        raw = blob.decode("utf-16" if blob.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise DataError("Die lokale Alpaca-Zugangsdatei ist nicht lesbar. Siehe README.", 503) from exc
    tokens = list(dict.fromkeys(token for line in raw.splitlines() if "://" not in line
                               for token in re.findall(r"[A-Za-z0-9_+/=-]{16,128}", line)))
    keys = [t for t in tokens if 20 <= len(t) <= 32]
    secrets = [t for t in tokens if 33 <= len(t) <= 128]
    if len(keys) != 1 or len(secrets) != 1:
        raise DataError("API-Key und Secret konnten nicht eindeutig gelesen werden.", 503)
    return keys[0], secrets[0]


def bar_end(timestamp: int, timeframe: str) -> int:
    if timeframe == "1D":
        from market_calendar import daily_end
        return daily_end(timestamp)
    return timestamp + SECONDS[timeframe]


def parse_bars(rows: list[dict], timeframe: str, cutoff: int) -> tuple[list[Bar], dict]:
    unique: dict[int, Bar] = {}
    rejected = duplicates = unfinished = 0
    for row in rows:
        try:
            stamp = datetime.fromisoformat(row["t"].replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                raise ValueError("Timestamp without offset")
            timestamp = int(stamp.timestamp())
            end = bar_end(timestamp, timeframe)
            if end > cutoff:
                unfinished += 1
                continue
            o, h, l, c, v = [float(row[k]) for k in ("o", "h", "l", "c", "v")]
            if not all(math.isfinite(x) for x in (o, h, l, c, v)):
                raise ValueError("Non-finite value")
            if min(o, h, l, c) <= 0 or v < 0 or h < max(o, c, l) or l > min(o, c, h):
                raise ValueError("Invalid OHLCV")
            if timestamp in unique:
                duplicates += 1
            unique[timestamp] = Bar(timestamp, end, o, h, l, c, v)
        except (KeyError, ValueError, TypeError, OverflowError):
            rejected += 1
    return sorted(unique.values(), key=lambda bar: bar.time), {
        "rejected": rejected, "duplicates": duplicates, "unfinished": unfinished,
    }


def _request(params: dict, key: str, secret: str) -> dict:
    url = "https://data.alpaca.markets/v2/stocks/bars?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={
        "APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret,
        "Accept": "application/json", "User-Agent": "Tori-Local-Prototype/0.1",
    }, method="GET")
    for attempt in range(3):
        request_slot()
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(1 + attempt)
                continue
            messages = {
                401: "Alpaca lehnt die Zugangsdaten ab (HTTP 401).",
                403: "Dieser Datenzugriff ist mit dem Alpaca-Zugang nicht freigegeben (HTTP 403).",
                429: "Alpacas Abruflimit ist erreicht. Bitte später erneut versuchen.",
                400: "Alpaca konnte die Kursabfrage nicht verarbeiten. Bitte das US-Symbol prüfen.",
                422: "Alpaca konnte das Symbol oder Intervall nicht verarbeiten.",
            }
            raise DataError(messages.get(exc.code, f"Alpaca-Datenabruf fehlgeschlagen (HTTP {exc.code}).")) from None
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            if attempt < 2:
                time.sleep(1 + attempt)
                continue
            raise DataError("Alpaca ist derzeit nicht erreichbar. Bitte die Verbindung prüfen.") from None
    raise DataError("Datenabruf fehlgeschlagen.")


def load_bars(symbol: str, timeframe: str, *, force: bool = False,
              now: datetime | None = None, end: datetime | None = None,
              history_days: int = 450, progress=None) -> tuple[list[Bar], dict]:
    if not re.fullmatch(r"[A-Z][A-Z0-9./-]{0,29}", symbol):
        raise DataError("Bitte ein gültiges US-Aktiensymbol eingeben, etwa AAPL oder MSFT.", 400)
    if timeframe not in TIMEFRAMES:
        raise DataError("Dieses Intervall wird nicht unterstützt.", 400)
    if not isinstance(history_days, int) or not 30 <= history_days <= 3650:
        raise DataError("Historie muss zwischen 30 und 3650 Kalendertagen liegen.", 400)
    now = now or datetime.now(UTC)
    cutoff = int((now - timedelta(minutes=15)).timestamp())
    if end is not None:
        cutoff = min(cutoff, int(end.timestamp()))
    history_start_at = (datetime.fromtimestamp(cutoff, UTC).replace(hour=0, minute=0, second=0, microsecond=0)
                        if end is not None else now) - timedelta(days=history_days)
    # Slash is valid in some provider symbols, never in a local cache filename.
    cache_symbol = urllib.parse.quote(symbol, safe="")
    suffix = "" if end is None else "_until_" + end.astimezone(UTC).date().isoformat()
    suffix += "" if history_days == 450 else f"_history_{history_days}"
    cache_path = data_dir(ROOT) / "market" / f"{cache_symbol}_{timeframe}_iex_raw{suffix}.json"
    # Reuse recent complete history for historical analysis, but filter BEFORE analysis.
    if end is not None and not force and not cache_path.exists():
        live_path = data_dir(ROOT) / "market" / f"{cache_symbol}_{timeframe}_iex_raw.json"
        try:
            live = json.loads(live_path.read_text("utf-8"))
            required = min(history_days, 380) if history_days == 450 else history_days
            if (live.get("symbol") == symbol and live.get("timeframe") == timeframe
                    and datetime.fromisoformat(live["requested_start"]) <= end - timedelta(days=required)
                    and datetime.fromisoformat(live["requested_end"]) >= end):
                rows = [r for r in live["bars"] if datetime.fromisoformat(r["t"].replace("Z", "+00:00")).timestamp() <= cutoff]
                bars, quality = parse_bars(rows, timeframe, cutoff)
                if len(bars) >= 3:
                    return bars, {"feed":"iex", "adjustment":"raw", "cached":True,
                        "fetchedAt":datetime.fromtimestamp(live["fetched_at"], UTC).isoformat(),
                        "first":bars[0].time,"last":bars[-1].time,"lastClose":bars[-1].end,
                        "count":len(bars),"pages":live["pages"],"quality":quality,
                        "mode":"historical-cache","warning":None,
                        "normalization":"XNYS/calendar-4.13.2" if timeframe=="1D" else "native-duration-v1"}
        except (OSError, ValueError, KeyError, TypeError):
            pass
    with data_lock(symbol, timeframe + suffix):
        payload = None
        candidate = None
        if not force and cache_path.exists():
            try:
                candidate = json.loads(cache_path.read_text("utf-8"))
                if not (candidate.get("symbol") == symbol and candidate.get("timeframe") == timeframe
                        and candidate.get("feed") == "iex" and candidate.get("adjustment") == "raw"
                        and isinstance(candidate.get("bars"), list)):
                    candidate = None
                historical_covered = (end is not None and candidate
                    and datetime.fromisoformat(candidate["requested_end"]).timestamp() >= cutoff
                    and datetime.fromisoformat(candidate["requested_start"]) <= history_start_at)
                if candidate and (historical_covered or (end is None and 0 <= now.timestamp() - candidate["fetched_at"] < 300)):
                    payload = candidate
            except (OSError, ValueError, KeyError):
                candidate = None
        # A refresh updates the existing history instead of downloading it again.
        if force and cache_path.exists():
            try:
                stored = json.loads(cache_path.read_text("utf-8"))
                if (stored.get("symbol") == symbol and stored.get("timeframe") == timeframe
                        and stored.get("feed") == "iex" and stored.get("adjustment") == "raw"
                        and isinstance(stored.get("bars"), list)):
                    candidate = stored
            except (OSError, ValueError):
                pass
        cached = payload is not None
        mode = "cache" if cached else "initial"
        warning = None
        if payload is None:
            key, secret = credentials()
            start = history_start_at
            history_start = start
            if candidate and candidate.get("bars") and datetime.fromisoformat(candidate["requested_start"]) <= history_start_at:
                # Re-read seven days for revised bars and unfinished candles.
                start = max(start, datetime.fromisoformat(candidate["requested_end"]) - timedelta(days=7))
                mode = "incremental"
            params = {
                "symbols": symbol, "timeframe": TIMEFRAMES[timeframe],
                "start": start.isoformat(), "end": datetime.fromtimestamp(cutoff, UTC).isoformat(),
                "feed": "iex", "adjustment": "raw", "sort": "asc", "limit": 10000,
                "asof": now.date().isoformat(),
            }
            rows: list[dict] = []
            seen_tokens: set[str] = set()
            pages = 0
            while True:
                try:
                    result = _request(params, key, secret)
                except DataError:
                    if candidate and candidate.get("bars"):
                        payload = candidate
                        warning = "Aktualisierung fehlgeschlagen; gespeicherter Datenstand wird angezeigt."
                        mode = "stale"
                        break
                    raise
                result_bars = result.get("bars") or {}
                if not isinstance(result_bars, dict):
                    raise DataError("Alpaca lieferte ein unerwartetes Datenformat.")
                rows.extend(result_bars.get(symbol) or [])
                pages += 1
                if progress:
                    progress(timeframe, pages, len(rows))
                token = result.get("next_page_token")
                if not token:
                    break
                # Hour aggregations may paginate on underlying minute records:
                # the requested 10,000 limit does not promise 10,000 hourly bars.
                if token in seen_tokens or pages >= 512:
                    raise DataError("Die Alpaca-Seitennavigation konnte nicht vollständig abgeschlossen werden.")
                seen_tokens.add(token)
                params["page_token"] = token
            if mode != "stale":
                if candidate and mode == "incremental":
                    merged = {row["t"]: row for row in candidate["bars"]}
                    merged.update({row["t"]: row for row in rows})
                    rows = [row for row in merged.values()
                            if datetime.fromisoformat(row["t"].replace("Z", "+00:00")) >= history_start]
                payload = {
                    "symbol": symbol, "timeframe": timeframe, "feed": "iex", "adjustment": "raw",
                    "fetched_at": now.timestamp(), "requested_start": history_start.isoformat(),
                    "requested_end": datetime.fromtimestamp(cutoff, UTC).isoformat(),
                    "pages": pages, "bars": rows,
                }
            if rows and mode != "stale":
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                temporary = cache_path.with_suffix(".tmp")
                temporary.write_text(json.dumps(payload, separators=(",", ":")), "utf-8")
                temporary.replace(cache_path)
        rows = payload["bars"]
        if end is not None:
            rows = [r for r in rows if datetime.fromisoformat(r["t"].replace("Z", "+00:00")).timestamp() <= cutoff]
        bars, quality = parse_bars(rows, timeframe, cutoff)
        if len(bars) < 3:
            raise DataError(f"Für {symbol} sind im {timeframe}-Intervall nicht genügend IEX-Kurse verfügbar.", 404)
        return bars, {
            "feed": "iex", "adjustment": "raw", "cached": cached,
            "fetchedAt": datetime.fromtimestamp(payload["fetched_at"], UTC).isoformat(),
            "first": bars[0].time, "last": bars[-1].time, "lastClose": bars[-1].end,
            "count": len(bars), "pages": payload["pages"], "quality": quality,
            "mode": mode, "warning": warning,
            "normalization":"XNYS/calendar-4.13.2" if timeframe=="1D" else "native-duration-v1",
        }


def next_bar_close(symbol: str, timeframe: str, cutoff: datetime, *, now=None) -> int:
    """Only return the next completed bar's close time, never future OHLC to the UI."""
    if not re.fullmatch(r"[A-Z][A-Z0-9./-]{0,29}", symbol) or timeframe not in TIMEFRAMES:
        raise DataError("Ungültige Aktie oder Intervall.", 400)
    now = now or datetime.now(UTC)
    limit = int((now-timedelta(minutes=15)).timestamp())
    at = int(cutoff.timestamp())
    start = cutoff-timedelta(days=2)
    folder = data_dir(ROOT) / "market"
    prefix = urllib.parse.quote(symbol, safe="") + "_" + timeframe + "_iex_raw"
    covered_to = at
    # A cached requested range covers empty sessions too. No invented calendar bars.
    for path in sorted(folder.glob(prefix+"*.json"), key=lambda p:p.stat().st_mtime, reverse=True):
        try:
            saved=json.loads(path.read_text("utf-8"))
            if (saved.get("symbol")!=symbol or saved.get("timeframe")!=timeframe
                    or saved.get("feed")!="iex" or saved.get("adjustment")!="raw"
                    or datetime.fromisoformat(saved["requested_start"])>start):
                continue
            requested_end=int(datetime.fromisoformat(saved["requested_end"]).timestamp())
            bars,_=parse_bars(saved["bars"],timeframe,min(limit,requested_end))
            following=[b.end for b in bars if at<b.end<=requested_end]
            if following:return min(following)
            covered_to=max(covered_to,requested_end)
        except (OSError, ValueError, KeyError, TypeError):
            continue
    if covered_to>=limit:
        raise DataError("Keine weitere abgeschlossene Kerze verfügbar.",404)
    key,secret=credentials()
    # Narrow windows instead of another 450-day download for each forward click.
    for days in (7,31,180):
        end=min(limit,int((cutoff+timedelta(days=days)).timestamp()))
        if end<=covered_to:continue
        params={"symbols":symbol,"timeframe":TIMEFRAMES[timeframe],"start":start.isoformat(),
                "end":datetime.fromtimestamp(end,UTC).isoformat(),"feed":"iex","adjustment":"raw",
                "sort":"asc","limit":10000,"asof":now.date().isoformat()}
        rows=[];tokens=set()
        while True:
            result=_request(params,key,secret)
            raw=result.get("bars") or {}
            if not isinstance(raw,dict):raise DataError("Alpaca lieferte ein unerwartetes Datenformat.")
            rows.extend(raw.get(symbol) or [])
            token=result.get("next_page_token")
            if not token:break
            if token in tokens or len(tokens)>=20:raise DataError("Seitennavigation unvollständig.")
            tokens.add(token);params["page_token"]=token
        bars,_=parse_bars(rows,timeframe,end)
        # Keep the narrow navigation window; its future prices are never chart input.
        path=folder/(prefix+"_step_"+cutoff.astimezone(UTC).date().isoformat()+".json")
        try:
            folder.mkdir(parents=True,exist_ok=True)
            saved={"symbol":symbol,"timeframe":timeframe,"feed":"iex","adjustment":"raw",
                   "requested_start":start.isoformat(),"requested_end":datetime.fromtimestamp(end,UTC).isoformat(),
                   "fetched_at":now.timestamp(),"bars":rows}
            temporary=path.with_suffix(".tmp")
            temporary.write_text(json.dumps(saved),"utf-8");temporary.replace(path)
        except OSError:
            pass
        following=[b.end for b in bars if b.end>at]
        if following:return min(following)
        covered_to=end
        if end>=limit:break
    raise DataError("Keine weitere abgeschlossene Kerze im Suchfenster von bis zu 180 Tagen verfügbar.",404)
