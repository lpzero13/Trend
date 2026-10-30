"""29 Oct Pine Master hull/refit profile, with explicit causal corrections.

Never invent a second confirmed contact for an envelope fallback. Side horizons
remain hard bounds. All historical comparisons use their historical ATR.
"""
from dataclasses import asdict, dataclass
from collections import deque

from fan_geometry import FanEngine, FanLine, stable_id

VERSION = "tori-pine-master-20261029-1"
RED = ("#800000", "#f23645", "#ff9800", "#ffbe00", "#ffbe00")
GREEN = ("#1e88e5", "#00a088", "#00d46a", "#00d46a", "#00d46a")


@dataclass(frozen=True)
class MasterLine(FanLine):
    origin: str = "pivot"
    gap: int = 5

    def output(self, index, known_at, rules):
        result = super().output(index, known_at, rules)
        result.update(origin=self.origin, contactGap=self.gap, algorithm="master",
                      color=(RED if self.upper else GREEN)[self.level-1],
                      provisionalEnvelope=self.origin == "envelope")
        return result


def violates_master(line, bar, index, atr, rules):
    if index <= line.a_index+rules.pivot_side:
        return False
    price = line.at(index)
    body = rules.body_atr*atr
    wick = rules.wick_atr*atr
    return (max(bar.open, bar.close) > price+body+1e-9 or bar.high > price+wick+1e-9) if line.upper else (
        min(bar.open, bar.close) < price-body-1e-9 or bar.low < price-wick-1e-9)


class MasterEngine(FanEngine):
    def _side(self, upper, lag):
        rows = list(self.rows)
        if len(rows) <= lag:
            return []
        valid = rows[:len(rows)-lag] if lag else rows
        until = valid[-1][0]
        days = self.rules.action_lookback_days if upper else self.rules.lookback_days
        cutoff = valid[-1][1].end-days*86400
        pivots = [p for p in self.pivots[upper] if p.known_index <= until and p.time >= cutoff]
        eligible = tuple(p.index for p in pivots[:-1] if self.index-p.index >= self.rules.contact_gap)
        # Ref-bar eligibility matters even without a newly confirmed pivot.
        signature = (tuple(p.index for p in pivots), eligible, valid[0][0])
        cached = self.cache.get((upper, lag))
        if cached and cached[0] == signature and not any(
            violates_master(line, b, i, atr, self.rules)
            for i,b,atr in valid if i > cached[1] for line in cached[2]):
            lines = cached[2]
        else:
            self.rebuilds += 1
            lines = self._build(upper, pivots, valid)
        self.cache[upper, lag] = (signature, until, lines)
        return [line for line in lines if line.at(self.index) > 0]

    def _build(self, upper, pivots, rows):
        if len(pivots) < 2:
            return []
        eligible = [i for i,p in enumerate(pivots[:-1]) if self.index-p.index >= self.rules.contact_gap]
        if not eligible:
            eligible = [i for i,p in enumerate(pivots[:-1]) if self.index-p.index >= 2]
        if not eligible:
            return []
        current = (max if upper else min)(eligible, key=lambda i:pivots[i].price)
        result, previous = [], None
        for level in range(self.rules.levels):
            a = pivots[current]
            gap = self.rules.contact_gap if level == 0 else max(2, self.rules.contact_gap-2)
            bounds = []
            for i,b,atr in rows:
                if i > a.index+self.rules.pivot_side:
                    boundary = max(max(b.open,b.close)-self.rules.body_atr*atr, b.high-self.rules.wick_atr*atr) if upper else min(
                        min(b.open,b.close)+self.rules.body_atr*atr, b.low+self.rules.wick_atr*atr)
                    bounds.append(((boundary-a.price)/(i-a.index),i,b))
            if not bounds:
                break
            bound, bound_index, bound_bar = (max if upper else min)(bounds, key=lambda item:item[0])
            best = None
            for b in pivots[current+1:]:
                if b.index-a.index < gap:
                    continue
                raw = (b.price-a.price)/(b.index-a.index)
                slope = raw
                invalid = raw < bound if upper else raw > bound
                if invalid and abs(a.price+bound*(b.index-a.index)-b.price) <= self.rules.contact_atr*b.atr:
                    slope = bound
                direction = slope < 0 if upper else slope > 0
                steeper = previous is None or (slope < previous-1e-6 if upper else slope > previous+1e-6)
                envelope = slope >= bound-1e-10 if upper else slope <= bound+1e-10
                if not (direction and steeper and envelope):
                    continue
                contacts, next_anchor = [a], None
                for m in range(current+1,len(pivots)):
                    p = pivots[m]
                    if abs(p.price-a.price-slope*(p.index-a.index)) <= self.rules.contact_atr*p.atr:
                        next_anchor = m
                        if p.index-contacts[-1].index >= gap:
                            contacts.append(p)
                if len(contacts) >= 2 and (best is None or (slope > best[0] if upper else slope < best[0]) or
                                          (abs(slope-best[0]) < 1e-10 and len(contacts) > len(best[2]))):
                    best = slope,b,tuple(contacts),next_anchor,"refit" if slope != raw else "pivot"
            if best is None and level == 0 and bound_index-a.index >= gap and (bound < 0 if upper else bound > 0):
                # Geometric support from a candle is NOT a confirmed pivot contact.
                best = bound,None,(a,),None,"envelope"
            if best is None:
                break
            slope,b,contacts,next_anchor,origin = best
            bi,bt = (b.index,b.time) if b else (bound_index,bound_bar.time)
            bp = a.price+slope*(bi-a.index)  # fitted endpoint, not raw pivot price
            key = stable_id([VERSION,self.symbol,self.timeframe,asdict(self.rules),upper,a.time,a.price,bt,bp])
            reactions = 1
            for left,right in zip(contacts,contacts[1:]):
                reactions += any(((a.price+slope*(i-a.index)-bar.close) if upper else
                                  (bar.close-a.price-slope*(i-a.index))) >= self.rules.reaction_atr*left.atr
                                 for i,bar,_ in rows if left.index < i < right.index)
            result.append(MasterLine(key,upper,a.index,a.time,a.price,bi,bt,bp,slope,contacts,reactions,level+1,origin,gap))
            previous,current = slope,next_anchor
            if current is None or current >= len(pivots)-1:
                break
        return result

    def snapshot(self, *, pine=False):
        state = super().snapshot(pine=pine)
        if state["ready"]:
            state.update(version=VERSION, mainSafety=next((line for line in state["greens"] if line["level"] == 1),None))
        return state

    def window_context(self, clean_atr=.15):
        line = self.snapshot(pine=True).get("red")
        rows = list(self.rows)
        armed, clean_at = False, None
        if line and len(rows) > self.rules.breakout_window:
            for k in range(len(rows)-self.rules.breakout_window,len(rows)):
                i,bar,atr = rows[k]
                pi,previous,_ = rows[k-1]
                def price(index):return line["a_price"]+line["slope"]*(index-line["a_index"])
                if previous.close <= price(pi) and bar.close > price(i):armed=True
                if armed and clean_at is None and bar.close >= price(i)+clean_atr*atr:clean_at=bar.end
        above = bool(line and rows[-1][1].close >= line["value"]+clean_atr*rows[-1][2])
        return {"line":line,"armed":armed,"cleanAt":clean_at,"closeAbove":above,
                "status":"Sauberer Schluss im Prüffenster" if clean_at and above else "Bruch vorgemerkt" if armed else "Kein neuer Bruch im Prüffenster",
                "meaning":"Pine-Schnappschuss, kein rückdatiertes Einstiegssignal"}


def context(rows, gaps=()):
    """SMA is context only. Never a hidden entry gate or extrapolated future."""
    buffers = {n:deque() for n in (50,200)}
    sums = {n:0. for n in buffers}
    series = {str(n):[] for n in buffers}
    for i,bar in enumerate(rows):
        if i in gaps:
            for n in buffers:
                buffers[n].clear()
                sums[n] = 0.
                series[str(n)].append({"time":bar.time})
        for n,buf in buffers.items():
            buf.append(bar.close)
            sums[n] += bar.close
            if len(buf) > n:
                sums[n] -= buf.popleft()
            if len(buf) == n:
                series[str(n)].append({"time":bar.time,"value":sums[n]/n})
    return {"sma50":sums[50]/50 if len(buffers[50]) == 50 else None,
            "sma200":sums[200]/200 if len(buffers[200]) == 200 else None, "series":series,
            "meaning":"Nur bekannte Quellkerzen; Kontext, kein Einstiegsausschluss"}
