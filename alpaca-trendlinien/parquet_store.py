"""Immutable Parquet blocks behind the unchanged dataset identity/API.

Manifests keep audit metadata and refer to shared content-addressed monthly
blocks containing all original frames and a disposable complete-week cache.
No provider calls, destructive cleanup, or silent legacy renormalization.
"""
from collections import defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import uuid

import duckdb

from models import Bar, DataError

FORMAT = "tori-parquet-1"
FIELDS = ("time", "end", "open", "high", "low", "close", "volume")
NUMBERS = FIELDS[2:]


def checksum(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def block_path(root, name):
    if not isinstance(name, str) or not re.fullmatch(r"datasets/chunks/[a-f0-9]{64}\.parquet", name):
        raise ValueError("invalid Parquet block path")
    path = root / name
    if path.is_symlink() or any(p.is_symlink() for p in (path.parent, path.parent.parent)):
        raise ValueError("linked Parquet block")
    return path


def connect():
    # One local in-process connection per operation. Never shared across threads.
    con = duckdb.connect(":memory:", config={"threads": 1})
    return con


def weekly_rows(material):
    # Imported lazily to avoid the datasets -> weekly -> analysis import cycle.
    from weekly_chart import weeks
    daily = [Bar(**b) for b in material["bars"]["1D"]]
    return [dict(zip(FIELDS, (b.time, b.end, b.open, b.high, b.low, b.close, b.volume)))
            for b in weeks(daily, max(b.end for b in daily))]


def prepare(payload, root):
    """Write durable blocks first; return a small, unpublished JSON manifest."""
    material = payload["material"]
    context = {k: v for k, v in material.items() if k != "bars"}
    frames = {**material["bars"], "1W": weekly_rows(material)}
    groups = defaultdict(list)
    for tf, bars in sorted(frames.items()):
        for b in bars:
            # UTC month is only a physical partition, never a candle boundary.
            month = datetime.fromtimestamp(b["time"], timezone.utc).strftime("%Y-%m")
            groups[month].append([tf, b])
    blocks = []
    root = Path(root)
    with connect() as con:
        con.execute('CREATE TABLE bars (timeframe VARCHAR, "time" BIGINT, "end" BIGINT, '
                    'open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, volume DOUBLE, '
                    'integer_mask UTINYINT, exact_integers VARCHAR)')
        for month, rows in sorted(groups.items()):
            identity = hashlib.sha256(encoded([context, rows])).hexdigest()
            name = f"datasets/chunks/{identity}.parquet"
            path = block_path(root, name)
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                temporary = path.with_name(uuid.uuid4().hex + ".tmp")
                # JSON int/float distinctions belong to old checksum identities.
                # Preserve those distinctions, including integers beyond 2**53.
                values = []
                for tf, b in rows:
                    mask = sum(1 << i for i, k in enumerate(NUMBERS) if type(b[k]) is int)
                    exact = {k: b[k] for k in NUMBERS if type(b[k]) is int and abs(b[k]) > 2**53}
                    values.append((tf, b["time"], b["end"], *(float(b[k]) for k in NUMBERS),
                                   mask, json.dumps(exact) if exact else None))
                csv_path = temporary.with_suffix(".csv")
                try:
                    with csv_path.open("w", newline="", encoding="utf-8") as stream:
                        writer = csv.writer(stream)
                        writer.writerows(values)
                    columns = {"timeframe": "VARCHAR", "time": "BIGINT", "end": "BIGINT",
                               **{k: "DOUBLE" for k in NUMBERS}, "integer_mask": "UTINYINT", "exact_integers": "VARCHAR"}
                    con.execute("DELETE FROM bars")
                    con.execute("INSERT INTO bars SELECT * FROM read_csv(?,header=false,columns=?)", [str(csv_path), columns])
                    con.execute("COPY (SELECT * FROM bars ORDER BY timeframe, \"time\") TO ? "
                                "(FORMAT PARQUET, COMPRESSION ZSTD, COMPRESSION_LEVEL 3, ROW_GROUP_SIZE 32768)", [str(temporary)])
                    with temporary.open("r+b") as stream:
                        os.fsync(stream.fileno())
                    # A concurrent publisher must never replace an existing block.
                    try:
                        os.link(temporary, path)
                    except FileExistsError:
                        pass
                finally:
                    temporary.unlink(missing_ok=True)
                    csv_path.unlink(missing_ok=True)
            blocks.append({"path": name, "sha256": checksum(path), "bytes": path.stat().st_size,
                           "month": month, "rows": len(rows)})
    return {**payload, "material": {**context, "bars": {}}, "storage": {
        "format": FORMAT, "compression": "zstd-3", "blocks": blocks,
        "frames": {tf: len(rows) for tf, rows in material["bars"].items()},
        "weekly": {"version": "xnys-complete-week-1", "count": len(frames["1W"])}}}


def hydrate(manifest, root, *, include_weekly=False):
    """Read/verify every referenced block, then recreate the exact legacy API."""
    store = manifest.get("storage")
    if not store:
        return manifest
    if store["format"] != FORMAT or manifest["material"]["bars"] != {}:
        raise ValueError("unsupported/modified Parquet manifest")
    frames = store["frames"]
    if set(frames) not in ({"1h", "4h", "1D"}, {"5m", "1h", "4h", "1D"}):
        raise ValueError("invalid frame manifest")
    paths = []
    for entry in store["blocks"]:
        path = block_path(Path(root), entry["path"])
        if path.stat().st_size != entry["bytes"] or checksum(path) != entry["sha256"]:
            raise ValueError("Parquet checksum")
        paths.append(str(path))
    if not paths or len(paths) != len(set(paths)):
        raise ValueError("empty/duplicate Parquet blocks")
    bars = {tf: [] for tf in (*frames, "1W")}
    with connect() as con:
        cursor = con.execute('SELECT * FROM read_parquet(?) ORDER BY timeframe,"time"', [paths])
        while batch := cursor.fetchmany(8192):
            for tf, at, end, *rest in batch:
                if tf not in bars:
                    raise ValueError("unexpected interval")
                values, mask, exact = rest[:5], rest[5], rest[6]
                integers = json.loads(exact) if exact else {}
                b = {"time": at, "end": end}
                for i, k in enumerate(NUMBERS):
                    b[k] = integers.get(k, int(values[i])) if mask & (1 << i) else values[i]
                bars[tf].append(b)
    weekly = bars.pop("1W")
    if any(len(bars[tf]) != n for tf, n in frames.items()):
        raise ValueError("Parquet frame count")
    value = {k: v for k, v in manifest.items() if k != "storage"}
    value["material"] = {**manifest["material"], "bars": bars}
    if include_weekly:
        return value, weekly
    return value


def publish(payload, path, *, replace=False):
    """Atomic manifest publication, always after an exact reconstruction check."""
    root = path.parent.parent
    manifest = prepare(payload, root)
    restored = hydrate(manifest, root)
    if restored != payload or encoded(restored["material"]) != encoded(payload["material"]):
        raise DataError("Parquet-Rückleseprüfung fehlgeschlagen; Original bleibt erhalten.", 409)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix("." + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(manifest, stream, ensure_ascii=False, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        if replace:
            temporary.replace(path)
        else:
            try:
                os.link(temporary, path)
            except FileExistsError:
                pass
    finally:
        temporary.unlink(missing_ok=True)
    return manifest


def migrate(identity):
    """Convert one existing JSON dataset, retaining a verified rollback copy."""
    from datasets import path_for, read_dataset
    path = path_for(identity)
    original_stat = path.stat()
    original = json.loads(path.read_text("utf-8"))
    payload = read_dataset(identity)
    if original.get("storage"):
        return {"id": identity, "status": "already_parquet"}
    archive = path.parent / "legacy-json" / path.name
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.exists():
        if checksum(archive) != checksum(path):
            raise DataError("Abweichendes JSON-Rollbackarchiv; Migration abgebrochen.", 409)
    else:
        temporary = archive.with_suffix("." + uuid.uuid4().hex + ".tmp")
        try:
            shutil.copyfile(path, temporary)
            if checksum(temporary) != checksum(path):
                raise DataError("Rollbackkopie fehlerhaft.", 409)
            os.link(temporary, archive)
        finally:
            temporary.unlink(missing_ok=True)
    manifest = publish(payload, path, replace=True)
    # Dataset catalog ordering is publication order, not migration order.
    os.utime(path, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))
    if read_dataset(identity) != payload:
        raise DataError("Dataset nach Migration abweichend.", 409)
    return {"id": identity, "status": "converted", "jsonBytes": archive.stat().st_size,
            "manifestBytes": path.stat().st_size, "blockBytes": sum(e["bytes"] for e in manifest["storage"]["blocks"])}
