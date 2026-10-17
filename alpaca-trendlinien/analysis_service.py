"""Shared chart/analysis service. No HTTP, credentials, or provider calls."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
import hashlib
import json
from models import DataError
from trendlines import RULES_VERSION, analyze
from assets import cached_asset_name

COMPANIES = {"AAPL": "Apple Inc.", "MSFT": "Microsoft Corporation", "NVDA": "NVIDIA Corporation", "SPY": "SPDR S&P 500 ETF"}


def build_chart(datasets, symbol, timeframe, cutoff, now, *, historical=False):
    # Hard boundary even if an adapter or a cached provider response contains later rows.
    datasets = {tf: ([bar for bar in bars if bar.end <= int(cutoff.timestamp())], dict(meta))
                for tf, (bars, meta) in datasets.items()}
    for tf, (bars, meta) in datasets.items():
        if len(bars) < 3:
            raise DataError(f"Für {symbol} liegen zum gewählten Zeitpunkt im Intervall {tf} nicht genügend abgeschlossene Kerzen vor.", 404)
        meta.update(count=len(bars), first=bars[0].time, last=bars[-1].time, lastClose=bars[-1].end)
    chart_bars, chart_meta = datasets[timeframe]
    # Source lanes retain their own last closed candle; the frontend projects anchors into its chart.
    reference = chart_bars[-1].time
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {tf: pool.submit(analyze, bars, tf, bars[-1].time,
                                  data_errors=meta["quality"]["rejected"] > 0)
                   for tf, (bars, meta) in datasets.items()}
        lanes = {tf: future.result() for tf, future in futures.items()}
    serialized = [asdict(bar) for bar in chart_bars]
    axis = [bar.time for bar in chart_bars]
    fingerprint = hashlib.sha256(json.dumps(serialized, sort_keys=True).encode()).hexdigest()[:16]
    latest, previous = chart_bars[-1], chart_bars[-2]
    result = {
        "symbol": symbol, "company": cached_asset_name(symbol) or COMPANIES.get(symbol, "US-Aktie / ETF"), "currency": "USD",
        "timeframe": timeframe, "bars": serialized, "axis": axis, "lanes": lanes,
        "sources": {tf: meta for tf, (_, meta) in datasets.items()},
        "latest": {"close": latest.close, "time": latest.time, "end": latest.end,
                   "change": latest.close - previous.close,
                   "changePercent": (latest.close / previous.close - 1) * 100},
        "reference": reference, "generatedAt": now.isoformat(), "fingerprint": fingerprint,
        "rulesVersion": RULES_VERSION, "feed": "iex", "adjustment": "raw",
        "timezone": "America/New_York", "provider": "Alpaca",
        "session": "Alpaca-Aggregation; Intraday kann erweiterte Handelszeiten enthalten",
        "rulesSource": "Tori_Trendline_Automator_v5.pine",
        "basis": "bars", "historical": historical, "analysisCutoff": int(cutoff.timestamp()),
    }
    # Ship every downloaded view once; interval switches need no new HTTP request.
    result["charts"] = {}
    for tf, (bars, _) in datasets.items():
        view_axis = [bar.time for bar in bars]
        result["charts"][tf] = {"bars": [asdict(b) for b in bars], "axis": view_axis,
            "reference": bars[-1].time, "latest": {"close": bars[-1].close,
            "time": bars[-1].time, "end": bars[-1].end,
            "change": bars[-1].close - bars[-2].close,
            "changePercent": (bars[-1].close / bars[-2].close - 1) * 100}}
    return result
