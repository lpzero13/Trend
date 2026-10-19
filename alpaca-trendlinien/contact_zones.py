"""Contact measurement on existing frozen rays; never selects or validates geometry."""
from trendlines import epsilon, rules_for
from tori_entries import value

VERSION = "contact-zone-1"


def episodes(ray, bars, upper, gap, tolerance):
    result = []
    last = -gap
    for i in range(ray["a_index"], len(bars)):
        distance = abs((bars[i].high if upper else bars[i].low) - value(ray, i))
        if distance <= tolerance + epsilon(value(ray, i), rules_for("4h").tick):
            if i - last >= gap:
                result.append({"firstIndex": i, "lastIndex": i, "firstTime": bars[i].time,
                               "lastTime": bars[i].time, "minimumDistance": distance})
            else:
                result[-1].update(lastIndex=i, lastTime=bars[i].time,
                                 minimumDistance=min(result[-1]["minimumDistance"], distance))
            last = i
    return result


def freeze(prefix, volatility, fraction):
    return {"version": VERSION, "knownAt": prefix[-1].end, "atrAtSetup": volatility,
            "atrFraction": fraction, "tolerance": max(.01, volatility * fraction) if volatility else None,
            "basis": "existing frozen source-4h rays; price zone only; no geometry or validity change"}


def measure(case, prefix, gap):
    measurement = case["contactMeasurement"]
    tolerance = measurement["tolerance"]
    if tolerance is None:
        return {"red": None, "green": None, "redEpisodes": [], "greenEpisodes": []}
    result = {}
    for side, upper in (("red", True), ("green", False)):
        found = episodes(case["frozen"][side], prefix, upper, gap, tolerance)
        result[side] = len(found)
        result[side + "Episodes"] = found
    return result
