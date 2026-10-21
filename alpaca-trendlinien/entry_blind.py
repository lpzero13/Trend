"""Known-prefix visual review and numerical stability probes, no future labels."""
from dataclasses import replace
from math import isfinite
import random

from datasets import digest
from entry_geometry import Geometry, at
from tori_entries import atr


def stability(bars, symbol, model, index):
    known = bars[:index+1]
    vol = atr(known)
    original = Geometry(known, symbol, model).proposals(index)
    if not vol or not original:
        return {"candidates": 0, "matched": 0, "trials": 0}
    matched, trials = 0, 0
    for seed in range(3):
        rng = random.Random(f"entry-stability-1|{symbol}|{index}|{seed}")
        jittered = []
        for b in known:
            # Perturb known wick endpoints only, keeping each OHLC coherent.
            high = max(b.open, b.close, b.high+rng.uniform(-.02, .02)*vol)
            low = min(b.open, b.close, b.low+rng.uniform(-.02, .02)*vol)
            jittered.append(replace(b, high=high, low=low))
        variants = Geometry(jittered, symbol, model).proposals(index)
        for c in original:
            trials += 1
            matched += any(c["upper"] == v["upper"] and
                abs(at(c["ray"], index)-at(v["ray"], index)) <= .25*vol and
                abs(at(c["ray"], index+20)-at(v["ray"], index+20)) <= .25*vol for v in variants)
    return {"candidates": len(original), "matched": matched, "trials": trials,
            "meaning": "3 fixed-seed known-wick perturbations <=0.02 ATR; level and 20-bar extrapolation within 0.25 ATR. No future prices."}


def candle_svg(bars):
    rows = bars[-100:]
    lo, hi = min(b.low for b in rows), max(b.high for b in rows)
    scale = max(hi-lo, .01)
    y = lambda v: 24+(hi-v)/scale*360
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 420">',
             '<rect width="1000" height="420" fill="#111722"/>',
             '<text x="16" y="410" fill="white" font-size="13">Nur bekannte 4h-Kerzen; rechte Kante = Bewertungszeitpunkt. Keine Zukunft / Ergebnisse.</text>']
    for i, b in enumerate(rows):
        x = 15+i*970/max(1, len(rows)-1)
        color = "#16b89b" if b.close >= b.open else "#ef4c69"
        parts.extend([f'<path d="M{x:.2f},{y(b.high):.2f} V{y(b.low):.2f}" stroke="{color}"/>',
            f'<rect x="{x-3:.2f}" y="{min(y(b.open),y(b.close)):.2f}" width="6" height="{max(1,abs(y(b.open)-y(b.close))):.2f}" fill="{color}"/>'])
    return "\n".join(parts+['</svg>'])


def blind_case(symbol, bars, cutoff, proposals):
    known = [b for b in bars if b.end <= cutoff]
    base = known[-1].close
    normalized = [{"index": i, "time": b.time, "end": b.end,
                   **{k: getattr(b, k)/base*100 for k in ("open", "high", "low", "close")}}
                  for i, b in enumerate(known[-100:])]
    identity = digest(["entry-blind-1", symbol, cutoff])[:16]
    return {"caseId": identity, "cutoff": cutoff, "bars": normalized,
            "review": {"interesting": None, "reason": "", "rays": []}}, {
            "caseId": identity, "symbol": symbol, "cutoff": cutoff, "proposals": proposals,
            "basePrice": base, "originIndex": max(0, len(known)-100),
            "knownATR": atr(known)/base*100 if atr(known) else None}


def compare_reviews(cases, private, reviews):
    by_id = {c["caseId"]: c for c in cases}
    suggestions = {c["caseId"]: c for c in private}
    results = []
    for review in reviews:
        if review["caseId"] not in by_id or type(review["interesting"]) is not bool:
            raise ValueError("Known case and real boolean human judgement required")
        case = by_id[review["caseId"]]
        hidden = suggestions[review["caseId"]]
        matches = {model: [] for model in hidden["proposals"]}
        for ray in review.get("rays", []):
            if not all(type(ray.get(k)) in (int, float) and isfinite(ray[k]) for k in ("aIndex", "bIndex", "aPrice", "bPrice")):
                raise ValueError("Finite normalized prices and candle positions required")
            if not 0 <= ray["aIndex"] < ray["bIndex"] < len(case["bars"]):
                raise ValueError("Manual anchors must be within known prefix")
            if type(ray.get("upper")) is not bool:
                raise ValueError("upper=true for resistance, false for support required")
            slope = (ray["bPrice"]-ray["aPrice"])/(ray["bIndex"]-ray["aIndex"])
            last = len(case["bars"])-1
            manual = [ray["aPrice"]+slope*(last+step-ray["aIndex"]) for step in (0, 20)]
            for model, proposals in hidden["proposals"].items():
                errors = [max(abs(manual[j]-at(p["ray"], hidden["originIndex"]+last+step)/hidden["basePrice"]*100)
                              for j, step in enumerate((0, 20))) / hidden["knownATR"]
                          for p in proposals if p["upper"] == ray["upper"]] if hidden["knownATR"] else []
                matches[model].append(min(errors) if errors else None)
        results.append({"caseId": review["caseId"], "interesting": review["interesting"],
                        "manualRays": len(review.get("rays", [])),
                        "geometryErrorATR": matches,
                        "matchesWithinQuarterATR": {model: sum(e is not None and e <= .25 for e in errors) for model, errors in matches.items()},
                        "meaning": "Human judgement captured; no profitability labels were shown."})
    if len({r["caseId"] for r in results}) != len(results):
        raise ValueError("Duplicate review")
    return results
