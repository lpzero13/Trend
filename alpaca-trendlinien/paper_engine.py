"""Deterministic rules for delayed paper simulation. Prices use Decimal throughout."""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_FLOOR
from functools import lru_cache
import re

from lab_data import session_bounds
from lab_splits import sessions_between
from models import DataError, NY

MODEL = "delayed_market_time_simulation_v1"
NORMALIZATION = "paper-rth-1m-v1"
PROFILE = "manual_breakout_v1"
TICK = Decimal("0.0001")
CENT = Decimal("0.01")
THOUSAND = Decimal(1000)
BPS = Decimal(10000)
MAX_SYMBOLS = 7
MAX_POSITIONS = 5
MAX_ACTIVE_PLANS = 28
CHANGES = "Aktivierte Pläne sind festgeschrieben. Lege für Änderungen einen neuen Entwurf an."


def number(value, label, low="0", high="1000000000"):
    if (not isinstance(value, (Decimal, str, int, float)) or isinstance(value, bool)
            or isinstance(value, str) and len(value) > 80):
        raise DataError(f"{label}: Zahl erwartet.", 400)
    try:
        result = Decimal(str(value))
        if not result.is_finite() or not Decimal(low) <= result <= Decimal(high):
            raise ValueError
        if result != result.quantize(Decimal("0.00000001")):
            raise ValueError
    except (InvalidOperation, ValueError):
        raise DataError(f"{label}: ungültiger Wert.", 400) from None
    return result


def stamp(value, label):
    if type(value) is int and 946684800 <= value <= 4102444800:
        return value
    if isinstance(value, str):
        try:
            date = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if date.tzinfo and not date.microsecond:
                return stamp(int(date.timestamp()), label)
        except (ValueError, OverflowError):
            pass
    raise DataError(f"{label}: Zeitstempel mit Zeitzone und vollen Sekunden erwartet.", 400)


def integer(value, label, lo, hi):
    if type(value) is not int or not lo <= value <= hi:
        raise DataError(f"{label}: ganze Zahl von {lo} bis {hi} erwartet.", 400)
    return value


def symbol(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Z][A-Z0-9.-]{0,11}", value):
        raise DataError("Ungültiges US-Aktiensymbol.", 400)
    return value


def day_at(at):
    return datetime.fromtimestamp(at, NY).date()


@lru_cache(maxsize=16384)
def buckets(day, tf):
    bounds = session_bounds(day.isoformat())
    if not bounds:
        return ()
    opened, closed = bounds
    width = 14400 if tf == "4h" else 86400
    return tuple((start, min(start + width, closed)) for start in range(opened, closed, width))


def bucket(at, tf):
    return next((pair for pair in buckets(day_at(at), tf) if pair[0] <= at < pair[1]), None)


@lru_cache(maxsize=512)
def session_buckets(first, last, tf):
    return tuple(pair for date_text in sessions_between(first.isoformat(), last.isoformat())
                 for pair in buckets(date.fromisoformat(date_text), tf))


@lru_cache(maxsize=8192)
def candle_distance(anchor, other, tf):
    first, last = sorted((anchor, other))
    count = sum(first <= start < last for start, _ in session_buckets(day_at(first), day_at(last), tf))
    return count if other >= anchor else -count


def market_minute(at):
    """First regular open at or after a timestamp, never a substitute for missing data."""
    at = ((at + 59) // 60) * 60
    day = day_at(at)
    for start, end in session_buckets(day, day + timedelta(days=14), "1D"):
        if at < end:
            return max(at, start)
    raise ValueError("No regular session in calendar window")


def previous_bucket(open_at, tf):
    day = day_at(open_at)
    return next(pair for pair in reversed(session_buckets(day - timedelta(days=14), day, tf))
                if pair[1] <= open_at)


def line_price(line, tf, bar_start, offset=Decimal(0)):
    a, b = line
    width = candle_distance(a["at"], b["at"], tf)
    x = Decimal(candle_distance(a["at"], bar_start, tf)) + offset
    return Decimal(a["price"]) + (Decimal(b["price"]) - Decimal(a["price"])) * x / width


def line_close(plan, name, bar_start):
    return line_price(plan[name], plan["timeframe"], bar_start)


def line_open(plan, name, at):
    start, end = bucket(at, plan["timeframe"])
    # Chart anchor price is evaluated at its candle's close. Between closes
    # progress through the new bucket, with no weekends or overnight seconds.
    return line_price(plan[name], plan["timeframe"], start, Decimal(at - end) / Decimal(end - start))


def normalize_plan(raw, now):
    if not isinstance(raw, dict):
        raise DataError("Setup-Objekt erwartet.", 400)
    fields = {"symbol", "timeframe", "action", "safety", "expires_at", "effective_from",
              "hard_stop", "buffer_pct", "risk_pct", "priority", "max_entry",
              "target_price", "time_exit_sessions", "horizons", "note"}
    if set(raw) - fields:
        raise DataError("Unbekanntes Feld im Setup.", 400)
    tf = raw.get("timeframe")
    if tf not in ("4h", "1D"):
        raise DataError("Signalintervall muss 4h oder 1D sein.", 400)
    ticker = symbol(raw.get("symbol"))
    out = {"symbol": ticker, "timeframe": tf, "profile": PROFILE}
    for name in ("action", "safety"):
        anchors = raw.get(name)
        if not isinstance(anchors, list) or len(anchors) != 2:
            raise DataError(f"{name}: zwei Zeit-/Preisanker erwartet.", 400)
        points = []
        for anchor in anchors:
            if not isinstance(anchor, dict) or set(anchor) != {"at", "price"}:
                raise DataError(f"{name}: at und price erwartet.", 400)
            at = stamp(anchor["at"], name)
            if not now - 730 * 86400 <= at < now or not any(at == start and end <= now
                    for start, end in buckets(day_at(at), tf)):
                raise DataError(f"{name}: Anker muss am Beginn einer schon geschlossenen regulären Strategiekerze liegen (maximal zwei Jahre zurück).", 400)
            points.append({"at": at, "price": str(number(anchor["price"], name, "0.0001"))})
        if points[0]["at"] >= points[1]["at"]:
            raise DataError(f"{name}: Anker müssen chronologisch und auf verschiedenen Kerzen liegen.", 400)
        out[name] = points
    effective = raw.get("effective_from")
    effective = None if effective is None else stamp(effective, "Gültig ab")
    expires = stamp(raw.get("expires_at"), "Ablauf")
    if not now <= (effective or now) < expires <= now + 90 * 86400:
        raise DataError("Ablauf muss nach dem Wirksamkeitsbeginn und innerhalb von 90 Tagen liegen.", 400)
    out.update(effective_from=effective, expires_at=expires)
    hard = raw.get("hard_stop", True)
    if type(hard) is not bool:
        raise DataError("Hard Stop: Wahr/Falsch erwartet.", 400)
    horizons = raw.get("horizons", [5, 10, 20])
    if not isinstance(horizons, list) or len(horizons) > 12:
        raise DataError("Horizonte: Liste mit bis zu zwölf Sitzungslängen erwartet.", 400)
    note = raw.get("note", "")
    if not isinstance(note, str) or len(note) > 2000:
        raise DataError("Notiz zu lang.", 400)
    out.update(hard_stop=hard, buffer_pct=str(number(raw.get("buffer_pct", "0.5"), "Stop-Puffer", "0", "10")),
               risk_pct=str(number(raw.get("risk_pct", "1"), "Positionsrisiko", "0.01", "2")),
               priority=integer(raw.get("priority", 100), "Priorität", 0, 9999),
               horizons=sorted(set(integer(x, "Horizont", 1, 90) for x in horizons)), note=note)
    for name in ("max_entry", "target_price"):
        value = raw.get(name)
        out[name] = None if value is None else str(number(value, name, "0.0001"))
    time_exit = raw.get("time_exit_sessions")
    out["time_exit_sessions"] = None if time_exit is None else integer(time_exit, "Zeitexit", 1, 90)
    return out


@dataclass(frozen=True)
class Minute:
    at: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

    @classmethod
    def parse(cls, at, payload):
        if type(at) is not int or at % 60:
            raise DataError("Minutenbar hat einen ungültigen Zeitstempel.", 422)
        if not isinstance(payload, (tuple, list)) or len(payload) != 5:
            raise DataError("Minutenbar muss vollständige OHLCV-Werte enthalten.", 422)
        o, h, l, c = (number(value, "OHLC", "0.0001") for value in payload[:4])
        v = integer(payload[4], "Volumen", 1, 10**12)
        if h < max(o, l, c) or l > min(o, h, c):
            raise DataError("Minutenbar hat widersprüchliche OHLC-Werte.", 422)
        return cls(at, o, h, l, c, v)

    def prices(self):
        return [format(value.normalize(), "f") for value in (self.open, self.high, self.low, self.close)] + [self.volume]


def aggregate(rows, start, end):
    if len(rows) != (end - start) // 60 or any(row.at != start + i * 60 for i, row in enumerate(rows)):
        return None
    return Minute(start, rows[0].open, max(row.high for row in rows), min(row.low for row in rows),
                  rows[-1].close, sum(row.volume for row in rows))


def crossed(plan, prev, current):
    return prev.close <= line_close(plan, "action", prev.at) and current.close > line_close(plan, "action", current.at)


def order_fill(base, bps, buying):
    sign = 1 if buying else -1
    rounding = ROUND_CEILING if buying else ROUND_FLOOR
    return (base * (1 + sign * Decimal(bps) / BPS)).quantize(TICK, rounding=rounding)


def entry(plan, minute, account, cash, equity):
    safety = line_open(plan, "safety", minute.at)
    stop = (safety * (1 - Decimal(plan["buffer_pct"]) / 100)).quantize(TICK, rounding=ROUND_FLOOR)
    bps, fee = account["slippage_bps"], Decimal(account["fee"])
    fill = order_fill(minute.open, bps, True)
    target = Decimal(plan["target_price"]) if plan["target_price"] else None
    if stop <= 0 or safety >= fill or minute.open <= stop:
        return None, "invalid_safety_at_entry"
    if plan["max_entry"] and fill > Decimal(plan["max_entry"]):
        return None, "above_entry_limit"
    if target is not None and fill >= target:
        return None, "target_already_reached"
    risk_per_share = fill - order_fill(stop, bps, False)
    risk_budget = equity * Decimal(plan["risk_pct"]) / 100
    quantity = int(min((cash - fee) // fill, (risk_budget - 2 * fee) // risk_per_share))
    if quantity < 1:
        return None, "insufficient_cash_or_risk"
    return {"at": minute.at, "quantity": quantity, "fill": str(fill), "base": str(minute.open),
            "fee": str(fee), "entry_cost": str(quantity * fill + fee), "stop": str(stop),
            "safety_at_entry": str(safety), "target": str(target) if target is not None else None,
            "initial_risk": str(quantity * risk_per_share + 2 * fee), "mark": str(minute.open),
            "mark_at": minute.at, "sessions": 0}, None


def exit_at_open(plan, position, minute, pending):
    stop = Decimal(position["stop"])
    if plan["hard_stop"] and minute.open <= stop:
        return "hard_stop_gap", minute.open
    if pending:
        return pending, minute.open
    if position["target"] and minute.open >= Decimal(position["target"]):
        return "target_gap", Decimal(position["target"])
    return None


def exit_inside_minute(plan, position, minute):
    stop = Decimal(position["stop"])
    target = Decimal(position["target"]) if position["target"] else None
    hits_stop = plan["hard_stop"] and minute.low <= stop
    hits_target = target is not None and minute.high >= target
    if hits_stop and hits_target:
        return "ambiguous_stop_target", None
    if hits_stop:
        return "hard_stop_touch", stop
    if hits_target:
        return "target_touch", target
    return None


def settle(position, minute, outcome, account):
    reason, base = outcome
    fee = Decimal(account["fee"])
    fill = order_fill(base, account["slippage_bps"], False)
    proceeds = position["quantity"] * fill - fee
    pnl = proceeds - Decimal(position["entry_cost"])
    return {"at": minute.at, "time_precision": "minute", "reason": reason, "base": str(base),
            "fill": str(fill), "fee": str(fee), "net_proceeds": str(proceeds), "pnl": str(pnl),
            "r": str((pnl / Decimal(position["initial_risk"])).quantize(TICK))}
