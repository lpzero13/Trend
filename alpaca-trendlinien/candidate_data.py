"""Incremental read-only SIP import; immutable known prefixes cannot be revised."""
from datetime import datetime, timezone
from math import ceil

from alpaca import load_bars
from datasets import source_bars, save_dataset, read_dataset, digest
from lab_data import resample_regular, NORMALIZATION, require_convention
from lab_metrics import expected_grid
from models import DataError


def closed_cutoff(now):
    return (int(now)-900)//300*300


def expected_last(cutoff):
    slots = list(expected_grid(cutoff-14*86400, cutoff))
    return slots[-1]+300 if slots else None


def refresh(dataset, known_until, now):
    require_convention(dataset)
    material = dataset["material"]
    if material["feed"] != "sip" or material["adjustment"] != "split":
        raise DataError("Beobachtung benötigt SIP mit Splitbereinigung.", 422)
    cutoff = closed_cutoff(now)
    days = max(30, ceil((now-known_until)/86400)+7)
    if days > 3650:
        raise DataError("Datenpause zu groß; neue Generation importieren.", 409)
    fine, meta = load_bars(material["symbol"], "5m", history_days=days, feed="sip", adjustment="split",
                           now=datetime.fromtimestamp(now, timezone.utc))
    if meta.get("warning") or meta.get("quality", {}).get("rejected"):
        raise DataError("Fehlerhafter oder veralteter Import; alter Zustand bleibt erhalten.", 422)
    incoming = resample_regular([b for b in fine if b.end <= cutoff])[0]["5m"]
    if not incoming or incoming[-1].end < expected_last(cutoff):
        raise DataError("SIP-Datenstand erreicht die letzte erwartete reguläre 5m-Kerze noch nicht.", 409)
    sources = source_bars(dataset)
    old = {b.time: b for b in sources["5m"]}
    incoming_by_time = {b.time: b for b in incoming}
    start = now-days*86400
    for b in incoming:
        if b.end <= known_until and old.get(b.time) != b:
            raise DataError("Historische Kursrevision im bekannten Präfix; neue Generation erforderlich.", 409)
    if any(b.time >= start and b.end <= known_until and b.time not in incoming_by_time for b in old.values()):
        raise DataError("Bekannte Kerze fehlt im neuen überlappenden Providerfenster.", 409)
    # A bootstrap dataset can contain later, not-yet-observed bars. Within the
    # requested overlap the fresh provider response owns those unknown bars;
    # retaining a now-deleted unknown bar would hide a real source gap.
    merged = {t:b for t,b in old.items() if b.end <= known_until or b.time < start}
    merged.update(incoming_by_time)
    frames, quality = resample_regular(sorted(merged.values(), key=lambda b: b.time))
    previous = {tf: [b.__dict__ for b in rows if b.end <= known_until] for tf, rows in sources.items()}
    new = {tf: [b.__dict__ for b in rows if b.end <= known_until] for tf, rows in frames.items()}
    if digest(previous) != digest(new):
        raise DataError("Normalisierte Quellkerzen vor dem Beobachtungsstand wurden verändert.", 409)
    data = {tf: (rows, {**meta, "normalization": NORMALIZATION, "rthQuality": quality,"count":len(rows),
                       "first":rows[0].time,"last":rows[-1].time,"lastClose":rows[-1].end}) for tf, rows in frames.items()}
    identity = save_dataset(material["symbol"], data, feed="sip", adjustment="split", session=material["session"])
    return read_dataset(identity), cutoff
