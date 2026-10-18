"""Versioned regular-session calendar; native intraday aggregates remain unchanged."""
from datetime import datetime
from functools import lru_cache
from models import NY, DataError

CALENDAR_VERSION = "XNYS/exchange-calendars-4.13.2"


@lru_cache(maxsize=12)
def calendar(year):
    import exchange_calendars
    return exchange_calendars.get_calendar("XNYS",start=f"{year-1}-01-01",end=f"{year+1}-12-31")


@lru_cache(maxsize=8192)
def session_close(day):
    year = int(day[:4])
    market = calendar(year)
    if not market.is_session(day):
        return None
    return int(market.session_close(day).timestamp())


def daily_end(timestamp):
    day = datetime.fromtimestamp(timestamp,NY).date().isoformat()
    close = session_close(day)
    if close is None:
        raise ValueError("Daily bar outside a regular session")
    return close
