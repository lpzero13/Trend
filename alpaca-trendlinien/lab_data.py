"""Research-only immutable RTH sources built from explicit fine-grained data.

No native source is silently converted. Session buckets are anchored at the
exchange open. Missing fine bars invalidate the bucket; no forward filling.
"""
from datetime import datetime
from functools import lru_cache

from alpaca import load_bars
from datasets import save_dataset, read_dataset
from market_calendar import calendar, CALENDAR_VERSION
from models import Bar, DataError, NY

NORMALIZATION = "tori-rth-5m-v1"


@lru_cache(maxsize=8192)
def session_bounds(day):
    market = calendar(int(day[:4]))
    if not market.is_session(day):
        return None
    return int(market.session_open(day).timestamp()), int(market.session_close(day).timestamp())


def resample_regular(fine, *, step=300):
    if step != 300:
        raise DataError("Das Labor erwartet explizite 5-Minuten-Kerzen.", 422)
    groups = {}
    for bar in fine:
        day = str(datetime.fromtimestamp(bar.time, NY).date())
        bounds = session_bounds(day)
        if bounds and bounds[0] <= bar.time < bar.end <= bounds[1] and bar.end-bar.time == step and (bar.time-bounds[0]) % step == 0:
            groups.setdefault(day, {})[bar.time] = bar
    sources = {"5m": [], "1h": [], "4h": [], "1D": []}
    missing = {tf: [] for tf in ("1h", "4h", "1D")}
    for day, rows in sorted(groups.items()):
        opened, closed = session_bounds(day)
        sources["5m"].extend(rows[t] for t in sorted(rows))
        for tf, seconds in (("1h",3600),("4h",14400),("1D",86400)):
            for start in range(opened, closed, seconds):
                end = min(start+seconds, closed)
                wanted = list(range(start,end,step))
                absent = [t for t in wanted if t not in rows]
                if absent:
                    missing[tf].append({"start":start,"end":end,"missingBars":len(absent)})
                    continue
                bars = [rows[t] for t in wanted]
                sources[tf].append(Bar(start,end,bars[0].open,max(b.high for b in bars),min(b.low for b in bars),bars[-1].close,sum(b.volume for b in bars)))
    return sources, {"version":NORMALIZATION,"calendar":CALENDAR_VERSION,"session":"regular",
                     "executionStepSeconds":step,"missingBuckets":{tf:len(rows) for tf,rows in missing.items()},
                     "examples":{tf:rows[:10] for tf,rows in missing.items()},"gapPolicy":"reject_incomplete_bucket"}


def import_dataset(symbol, history_days=900, *, feed="iex", adjustment="split", progress=None):
    from storage import preflight
    from operations import record_dataset
    preflight(history_days=history_days*4,symbols=1)
    fine, meta = load_bars(symbol,"5m",history_days=history_days,feed=feed,adjustment=adjustment,progress=progress)
    if meta.get("warning") or meta.get("quality",{}).get("rejected"):
        raise DataError("Laborimport verweigert veraltete/fehlerhafte Feindaten.",422)
    sources, quality = resample_regular(fine)
    if any(len(rows)<3 for rows in sources.values()):
        raise DataError("Zu wenige vollständige reguläre Sitzungen für Laborimport; Feed und Datenlücken prüfen.",422)
    material = {tf:(rows,{**meta,"normalization":NORMALIZATION,"rthQuality":quality,"count":len(rows),
                          "first":rows[0].time,"last":rows[-1].time,"lastClose":rows[-1].end}) for tf,rows in sources.items()}
    identity = save_dataset(symbol,material,feed=feed,adjustment=adjustment,session="XNYS regular; open-anchored buckets; final 4h bucket may be shorter; execution 5m")
    record_dataset(read_dataset(identity),imported=True)
    return identity


def require_convention(dataset, *, allow_native=False):
    from datasets import data_kind
    material = dataset["material"]
    regular = all(material.get("normalization",{}).get(tf)==NORMALIZATION for tf in ("5m","1h","4h","1D"))
    if not regular and not allow_native:
        raise DataError("Labor benötigt normalisierte reguläre 5m-Daten. Native Altbestände nur ausdrücklich als eingeschränkten Techniktest freigeben.",422)
    return {"regular5m":regular,"executionTimeframe":"5m" if regular else "1h",
            "limitations":[] if regular else ["native aggregates; session/open timestamp precision unverified"],
            "adjustment":material["adjustment"],"feed":material["feed"],"dataKind":data_kind(dataset)}
