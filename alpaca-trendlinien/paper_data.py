"""Read-only batched Alpaca imports for the delayed regular-session simulation."""
from datetime import date, datetime, timedelta, timezone
from alpaca import credentials, request_market_data
from market_calendar import CALENDAR_VERSION
from models import DataError
from paper_engine import MAX_SYMBOLS, Minute, bucket, day_at, stamp, symbol

DELAY = 16 * 60
BARS_ENDPOINT = "v2/stocks/bars"
ACTIONS_ENDPOINT = "v1/corporate-actions"


def cutoff_at(now):
    return (now - DELAY) // 60 * 60


def iso(at):
    return datetime.fromtimestamp(at, timezone.utc).isoformat()


class AlpacaPaper:
    def __init__(self, *, request=request_market_data, auth=credentials):
        self._request = request
        self._auth = auth
        self.attempts = 0
        self.pages = 0

    def _count_attempt(self):
        self.attempts += 1

    def page_stream(self, endpoint, params, limit=16):
        key, secret = self._auth()
        seen = set()
        self.pages = 0
        for _ in range(limit):
            payload = self._request(endpoint, params, key, secret, on_attempt=self._count_attempt)
            if not isinstance(payload, dict):
                raise DataError("Unerwartete Alpaca-Antwort.", 502)
            self.pages += 1
            yield payload
            token = payload.get("next_page_token")
            if token is None:
                return
            if not isinstance(token, str) or not token or token in seen:
                raise DataError("Ungültiger Alpaca-Folgeseitentoken.", 502)
            seen.add(token)
            params = {**params, "page_token": token}
        raise DataError("Zu viele Alpaca-Seiten. Abruffenster verkleinern.", 502)

    def bars(self, symbols, start, end):
        tickers = sorted({symbol(ticker) for ticker in symbols})
        if not 1 <= len(tickers) <= MAX_SYMBOLS or end-start > 8*86400 or end-start < 60:
            raise DataError("Minutenimport erwartet 1–7 Symbole und maximal acht Tage je Abruf.", 400)
        result = {ticker: {} for ticker in tickers}
        params = {"symbols": ",".join(tickers), "feed": "sip", "timeframe": "1Min",
                  "adjustment": "raw", "currency": "USD", "asof": "-", "start": iso(start),
                  "end": iso(end-60), "sort": "asc", "limit": 10000}
        for page in self.page_stream(BARS_ENDPOINT, params):
            bars = page.get("bars")
            if not isinstance(bars, dict) or not set(bars) <= set(tickers):
                raise DataError("Ungültige Symbolantwort vom Minutenfeed.", 502)
            for ticker, items in bars.items():
                if not isinstance(items, list):
                    raise DataError("Ungültige Minutenliste.", 502)
                for bar in items:
                    try:
                        at = stamp(bar["t"], "Alpaca-Minute")
                        if not start <= at <= end-60:
                            raise ValueError("out of range")
                        if bucket(at, "1D") is None:
                            continue
                        minute = Minute.parse(at, [bar[k] for k in ("o", "h", "l", "c", "v")])
                        prior = result[ticker].get(at)
                        if prior is not None and prior != minute:
                            raise ValueError("conflicting duplicate")
                        result[ticker][at] = minute
                    except (KeyError, TypeError, ValueError, DataError):
                        raise DataError("Widersprüchliche oder ungültige Alpaca-Minutenkerze.", 502) from None
        return {ticker: [items[at] for at in sorted(items)] for ticker, items in result.items()}

    def actions(self, symbols, at, *, since=None):
        tickers = sorted({symbol(ticker) for ticker in symbols})
        day = day_at(at)
        start = min(day - timedelta(days=21), since) if since else day - timedelta(days=21)
        result = {ticker: [] for ticker in tickers}
        if not tickers:
            return result
        params = {"symbols": ",".join(tickers), "start": start.isoformat(), "end": day.isoformat(),
                  "region": "us", "data_quality": "all", "limit": 1000}
        for page in self.page_stream(ACTIONS_ENDPOINT, params):
            actions = page.get("corporate_actions")
            if not isinstance(actions, dict):
                raise DataError("Ungültige Alpaca-Antwort zu Kapitalmaßnahmen.", 502)
            for kind, entries in actions.items():
                if not isinstance(entries, list):
                    raise DataError("Ungültige Kapitalmaßnahmenliste.", 502)
                for action in entries:
                    if not isinstance(action, dict) or not isinstance(action.get("id"), str):
                        raise DataError("Ungültige Kapitalmaßnahme.", 502)
                    matched = set(tickers).intersection(
                        value for key, value in action.items() if "symbol" in key and isinstance(value, str))
                    if not matched:
                        raise DataError("Kapitalmaßnahme kann keinem angefragten Symbol zugeordnet werden.", 502)
                    raw_date = (action.get("ex_date") or action.get("effective_date")
                                or action.get("execution_date") or action.get("date"))
                    try:
                        effective = date.fromisoformat(raw_date) if raw_date else None
                    except (ValueError, TypeError):
                        raise DataError("Kapitalmaßnahme enthält ein ungültiges Datum.", 502) from None
                    for ticker in matched:
                        result[ticker].append({"id": action["id"], "type": kind,
                                               "date": effective.isoformat() if effective else None})
        return result


def source_info():
    return {"feed": "sip", "adjustment": "raw", "timeframe": "1Min", "currency": "USD",
            "calendar": CALENDAR_VERSION, "delay_seconds": DELAY}
