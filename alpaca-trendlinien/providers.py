"""Provider boundary: normalized Bar objects and explicit provenance, no signal logic."""
from dataclasses import dataclass
from typing import Protocol
from models import Bar

TIMEFRAMES = ("1h","4h","1D")


class MarketDataProvider(Protocol):
    name: str
    feed: str
    adjustment: str
    calendar: str

    def load_bars(self, symbol: str, timeframe: str, **options) -> tuple[list[Bar],dict]: ...


@dataclass
class AlpacaProvider:
    loader: object
    name: str = "Alpaca"
    feed: str = "iex"
    adjustment: str = "raw"
    calendar: str = "XNYS"

    def load_bars(self, symbol, timeframe, **options):
        return self.loader(symbol,timeframe,**options)


def fetch_sources(provider: MarketDataProvider, symbol, **options):
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=3) as pool:
        pending = {tf:pool.submit(provider.load_bars,symbol,tf,**options) for tf in TIMEFRAMES}
        return {tf:future.result() for tf,future in pending.items()}
