"""Internal, causal candidate generation; does not evaluate future outcomes."""
from itertools import combinations

from datasets import digest
from tori_entries import atr, contact_count
from trendlines import pair, rules_for

VERSION = "entry-discovery-1"
MODELS = ("hull_exact", "hull_episodes", "swing_envelope", "swing_zone")
RULES = {"pivot_side": 2, "windows_days": [30, 90, 365], "max_pivots": 10,
         "contact_atr": .10, "reaction_atr": .50, "contact_gap": 2,
         "near_atr": .75, "cluster_level_atr": .15, "cluster_projection_atr": .25,
         "cluster_steps": 20, "lifetime_bars": 60, "notifications_per_bar": 3,
         "stop_buffer_atr": .25, "latency_seconds": 300, "tick": .01}


def at(ray, i):
    return ray["a_price"]+ray["slope"]*(i-ray["a_index"])


def confirmed_pivots(bars, i, upper, side=2):
    """Return indices only after both right neighbours are closed."""
    price = lambda j: bars[j].high if upper else bars[j].low
    return [j for j in range(side, i-side+1)
            if all(price(j) > price(k) if upper else price(j) < price(k)
                   for k in range(j-side, j+side+1) if k != j)]


def violation(ray, bar, i, upper, width, zone=False):
    level = at(ray, i)
    eps = max(1e-7, abs(level)*1e-12)
    if upper:
        return bar.high > level+(width if zone else 0)+eps or (zone and max(bar.open, bar.close) > level+eps)
    return bar.low < level-(width if zone else 0)-eps or (zone and min(bar.open, bar.close) < level-eps)


def episodes(ray, bars, end, upper, width, volatility):
    """A later close must leave the band before a new touch can count.

    A single OHLC bar cannot establish touch -> departure ordering. Every
    departure must therefore be observed on a later closed candle.
    """
    found, separated = [], False
    for i in range(ray["a_index"], end+1):
        b, level = bars[i], at(ray, i)
        wick = b.high if upper else b.low
        near = abs(wick-level) <= width+1e-7
        if near:
            if not found or separated and i-found[-1]["lastIndex"] >= RULES["contact_gap"]:
                found.append({"firstIndex": i, "lastIndex": i, "at": b.time,
                              "minimumDistance": abs(wick-level)})
            else:
                found[-1].update(lastIndex=i, minimumDistance=min(found[-1]["minimumDistance"], abs(wick-level)))
            separated = False
        elif found and i > found[-1]["lastIndex"]:
            away = level-width-b.close if upper else b.close-level-width
            separated = separated or away >= RULES["reaction_atr"]*volatility
    return found


def measure(candidate, bars, i):
    ray, upper = candidate["ray"], candidate["upper"]
    reactions = episodes(ray, bars, i, upper, candidate["width"], candidate["atrAtCreation"])
    count = contact_count(ray, bars[:i+1], upper, RULES["contact_gap"]) if candidate["model"] == "hull_exact" else len(reactions)
    span = (reactions[-1]["at"]-reactions[0]["at"])/86400 if len(reactions)>1 else 0.
    sensitivity = .05*(1+2*max(0, i-ray["b_index"])/(ray["b_index"]-ray["a_index"]))
    return {"contacts": count, "reactionEpisodes": len(reactions), "contactSpanDays": span,
            "projectionSensitivityATR": sensitivity,
            "meanContactErrorATR": sum(r["minimumDistance"] for r in reactions)/len(reactions)/candidate["atrAtCreation"] if reactions else None}


class Geometry:
    def __init__(self, bars, symbol, model):
        if model not in MODELS:
            raise ValueError("Unknown internal geometry")
        self.bars, self.symbol, self.model = bars, symbol, model
        self.checked = set()

    def proposals(self, i):
        bars, model = self.bars, self.model
        vol = atr(bars[max(0, i-14):i+1])
        if vol is None or vol <= 0:
            return []
        width = max(RULES["tick"], RULES["contact_atr"]*vol)
        pairs = []
        if model.startswith("hull"):
            p = pair(bars[:i+1], rules_for("4h"))
            greens = [r for r in p["greens"] if r.valid and 0 < r.value(bars[i].time) < bars[i].close]
            green = max(greens, key=lambda r: r.value(bars[i].time), default=None)
            for upper, ray in ((True, p["red"]), (False, green)):
                if ray:
                    pairs.append((upper, ray.a_index, ray.b_index, 365))
        else:
            for upper in (True, False):
                pivots = confirmed_pivots(bars, i, upper, RULES["pivot_side"])
                for window in RULES["windows_days"]:
                    selected = [p for p in pivots if bars[p].time >= bars[i].end-window*86400][-RULES["max_pivots"]:]
                    pairs.extend((upper, a, b, window) for a, b in combinations(selected, 2))
        result = []
        for upper, a, b, window in pairs:
            key = (upper, a, b)
            if key in self.checked:
                continue
            self.checked.add(key)
            av = bars[a].high if upper else bars[a].low
            bv = bars[b].high if upper else bars[b].low
            slope = (bv-av)/(b-a)
            if not (slope < 0 if upper else slope > 0):
                continue
            # Even reference anchors must have two known right neighbours.
            if b+RULES["pivot_side"] > i:
                self.checked.remove(key)
                continue
            ray = {"a_index": a, "b_index": b, "a_time": bars[a].time, "b_time": bars[b].time,
                   "a_price": av, "b_price": bv, "slope": slope, "basis": "bars", "valid": True}
            if any(violation(ray, bars[j], j, upper, width, model == "swing_zone") for j in range(a, i+1)):
                continue
            identity = digest({"version": VERSION, "model": model, "symbol": self.symbol,
                               "upper": upper, "anchors": [bars[a].time, bars[b].time]})
            c = {"id": identity, "model": model, "symbol": self.symbol, "upper": upper,
                 "ray": ray, "width": width, "atrAtCreation": vol, "createdIndex": i,
                 "knownAt": bars[i].end, "windowDays": window, "active": True,
                 "state": "forming", "alternatives": 0, "notified": [], "breakIndex": None,
                 "armGreen": None, "armGreenCandidate": None, "lastFeatures": None}
            c["lastFeatures"] = measure(c, bars, i)
            result.append(c)
        return result


def equivalent(a, b, i, volatility):
    return (a["upper"] == b["upper"] and
            abs(at(a["ray"], i)-at(b["ray"], i)) <= RULES["cluster_level_atr"]*volatility and
            abs(at(a["ray"], i+RULES["cluster_steps"])-at(b["ray"], i+RULES["cluster_steps"])) <= RULES["cluster_projection_atr"]*volatility)
