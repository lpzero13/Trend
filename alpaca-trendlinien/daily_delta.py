
"""Publish a checked SIP delta without materializing the full 5m history."""
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import json

from data_quality import audit
from datasets import SCHEMA, path_for
from lab_data import NORMALIZATION, resample_regular, session_bounds
from models import Bar, DataError, NY
from parquet_store import (INCREMENTAL_FORMAT, block_path, connect, encoded, incremental_identity,
                           read_rows, validate_manifest, verified_paths, write_block, write_manifest)
from settings import data_dir
from weekly_chart import weeks

FRAMES = ("5m", "1h", "4h", "1D")


class SplitConflict(DataError):
    pass


def trading_day(stamp):
    return datetime.fromtimestamp(stamp, NY).date().isoformat()


def month_of(stamp):
    return datetime.fromtimestamp(stamp, timezone.utc).strftime("%Y-%m")


def monday_for(day):
    date = datetime.fromisoformat(day).date()
    return (date - timedelta(days=date.weekday())).isoformat()


def patch_months(db, root, manifest, entries, paths, days, new_frames):
    """Read full partitions only when their rows are being patched."""
    storage = manifest["storage"]
    context = {key: value for key, value in manifest["material"].items() if key != "bars"}
    months = {day[:7] for day in days}
    mondays = {monday_for(day) for day in days}
    # A week is stored in the UTC month of its first trading session, possibly
    # the month before a changed daily bar. Include both candidate months.
    months.update(monday[:7] for monday in mondays)
    daily = [Bar(**row) for _, row in read_rows(db, paths.values(), "WHERE timeframe='1D'")
             if trading_day(row["time"]) not in days]
    daily = sorted(daily + new_frames["1D"], key=lambda bar: bar.time)
    affected_daily = [bar for bar in daily if monday_for(trading_day(bar.time)) in mondays]
    weekly = weeks(affected_daily, daily[-1].end)
    new_rows = {tf: [asdict(bar) for bar in rows] for tf, rows in {**new_frames, "1W": weekly}.items()}
    counts = Counter({**storage["frames"], "1W": storage["weekly"]["count"]})
    replacements, metrics = {}, Counter()
    for month in sorted(months):
        old = list(read_rows(db, [paths[month]])) if month in paths else []
        kept = [[tf, row] for tf, row in old
                if (monday_for(trading_day(row["time"])) not in mondays if tf == "1W"
                    else trading_day(row["time"]) not in days)]
        local = [[tf, row] for tf, rows in new_rows.items() for row in rows if month_of(row["time"]) == month]
        rows = sorted(kept + local, key=lambda item: (item[0], item[1]["time"]))
        if old == rows and encoded(old) == encoded(rows):
            continue
        if not rows:
            raise ValueError("unexpected empty patched month")
        counts.subtract(tf for tf, _ in old)
        counts.update(tf for tf, _ in rows)
        entry = write_block(db, root, context, month, rows)
        path, = verified_paths([entry], root)
        restored = list(read_rows(db, [path]))
        if encoded(rows) != encoded(restored):
            raise DataError("Parquet-Rückleseprüfung des Monats fehlgeschlagen.", 409)
        replacements[month] = entry
        metrics.update(changedBlocks=1, verifiedNewBytes=entry["bytes"])
    blocks = [entry for _, entry in sorted({**entries, **replacements}.items())]
    storage = {**storage, "format": INCREMENTAL_FORMAT, "blocks": blocks,
               "frames": {tf: counts[tf] for tf in FRAMES},
               "weekly": {**storage["weekly"], "count": counts["1W"]}}
    return storage, daily, {"verifiedBaseBytes": sum(entry["bytes"] for entry in entries.values()),
                            "reusedBlocks": len(blocks) - len(replacements), **metrics}


def open_base(identity, symbol, root):
    path = path_for(identity)
    manifest = json.loads(path.read_text("utf-8"))
    material = manifest["material"]
    if (path.is_symlink() or manifest["id"] != identity or material["schema"] != SCHEMA
            or material["symbol"] != symbol or material["provider"] != "Alpaca"
            or material["feed"] != "sip" or material["adjustment"] != "split"
            or material.get("dataKind") == "synthetic"
            or any(material.get("normalization", {}).get(tf) != NORMALIZATION for tf in FRAMES)):
        raise ValueError("incompatible dataset")
    if not manifest.get("storage"):
        raise DataError("Vor dem inkrementellen Update ist ein separat geprüfter Parquet-Bestand erforderlich.", 409)
    validate_manifest(manifest)
    entries = {entry["month"]: entry for entry in manifest["storage"]["blocks"]}
    paths = dict(zip(entries, verified_paths(entries.values(), root)))
    return manifest, entries, paths


def extend(symbol, item, downloaded):
    from daily_archive import gap_status, missing_bars
    root = data_dir()
    manifest, entries, paths = open_base(item["datasetId"], symbol, root)
    days = set(item["sessions"])
    stamps = {trading_day(stamp) for stamp in downloaded}
    if not days or not stamps <= days:
        raise ValueError("unexpected downloaded session")
    selected = [paths[month] for month in sorted({day[:7] for day in days}) if month in paths]
    missing = dict(item["missingBarsBySession"])
    with connect() as db:
        bounds = [session_bounds(day) for day in sorted(days)]
        filters = " OR ".join('("time">=? AND "time"<?)' for _ in bounds)
        params = [stamp for window in bounds for stamp in window]
        fine = {row["time"]: Bar(**row) for _, row in read_rows(
            db, selected, f"WHERE timeframe='5m' AND ({filters})", params)}
        overlap = fine.keys() & downloaded.keys()
        # Require the dedicated comparison session for planned provider updates.
        # Existing repair overlap elsewhere must not substitute for it.
        comparison = item.get("overlapSession")
        if downloaded and (not overlap or comparison and not any(trading_day(t) == comparison for t in overlap)):
            raise SplitConflict("Keine gemeinsame Kerze zur Prüfung der Splitbereinigung.", 409)
        for stamp in overlap:
            old, new = fine[stamp], downloaded[stamp]
            if (old.open, old.high, old.low, old.close) != (new.open, new.high, new.low, new.close):
                raise SplitConflict("Kursrevision oder Split im Überlapp. Historie mit einheitlicher Splitbereinigung neu importieren.", 409)
        added = len(downloaded.keys() - fine.keys())
        revised = sum(fine[stamp].volume != downloaded[stamp].volume for stamp in overlap)
        changed = {trading_day(t) for t, bar in downloaded.items() if fine.get(t) != bar}
        fine.update(downloaded)
        for day in days:
            count = missing_bars(day, fine)
            if count:
                missing[day] = count
            else:
                missing.pop(day, None)
        quality = gap_status(missing)
        result = {"datasetId": manifest["id"], "lastSession": trading_day(manifest["sources"]["1D"]["lastClose"]),
                  "lastClose": manifest["sources"]["1D"]["lastClose"],
                  "status": "gaps" if quality == "problem" else "tolerated_gaps" if missing else "updated",
                  "gapStatus": quality, "checkedThrough": max(item["checkedThrough"], *days),
                  "missingSessions": sorted(missing), "missingBarsBySession": missing,
                  "addedBars": added, "volumeRevisions": revised}
        if not changed:
            return result
        sources, delta_quality = resample_regular([bar for stamp, bar in fine.items() if trading_day(stamp) in changed])
        storage, daily, metrics = patch_months(db, root, manifest, entries, paths, changed, sources)
        prior_lasts = {}
        for tf, meta in manifest["sources"].items():
            last = meta.get("last")
            if last is None and tf in FRAMES:
                path = paths[month_of(meta["lastClose"] - 1)]
                last, = db.execute('SELECT max("time") FROM read_parquet(?) WHERE timeframe=?',
                                   [str(path), tf]).fetchone()
            prior_lasts[tf] = last

    identity = incremental_identity(manifest["material"], storage)
    meta = {"feed": "sip", "adjustment": "split", "normalization": NORMALIZATION,
            "mode": "scheduled-sip-delta", "sourceDatasetId": manifest["id"],
            "deltaRthQuality": {**delta_quality, "sessions": sorted(changed)},
            "quality": {"rejected": 0}, "volumeRevisions": revised}
    source_meta = {}
    for tf, rows in sources.items():
        prior = manifest["sources"][tf]
        source_meta[tf] = {**meta, "count": storage["frames"][tf],
                           "first": min(prior["first"], rows[0].time) if rows else prior["first"],
                           "last": max(prior_lasts[tf], rows[-1].time) if rows else prior_lasts[tf],
                           "lastClose": max(prior["lastClose"], rows[-1].end) if rows else prior["lastClose"]}
    last_close = source_meta["1D"]["lastClose"]
    result.update(datasetId=identity, lastSession=trading_day(last_close), lastClose=last_close, **metrics)
    full_daily_audit = audit({"1D": daily}, feed="sip", adjustment="split")
    full_daily_audit["intradaySessions"] = "regular; open-anchored; incomplete buckets omitted explicitly"
    updated = {"id": identity, "material": manifest["material"], "storage": storage,
               "importedAt": datetime.now(timezone.utc).isoformat(), "sources": source_meta,
               "quality": full_daily_audit, "dailyArchive": result}
    validate_manifest(updated)
    dest = path_for(identity)
    write_manifest(updated, dest)
    published = json.loads(dest.read_text("utf-8"))
    validate_manifest(published)
    if published["id"] != identity or published["storage"] != storage:
        raise ValueError("published manifest mismatch")
    return result
