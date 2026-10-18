"""Read-only storage inventory and conservative import capacity checks."""
import json
import os
from pathlib import Path
import shutil
import threading
import time
import re

from models import DataError
from settings import data_dir

_cache = {}
_lock = threading.Lock()


def reserve_bytes():
    try: return max(0,int(os.environ.get("TORI_MIN_FREE_BYTES",str(256*1024*1024))))
    except ValueError: return 256*1024*1024


def preflight(*, history_days=0, symbols=0):
    root = data_dir()
    existing = root
    while not existing.exists(): existing=existing.parent
    free = shutil.disk_usage(existing).free
    # Budget includes raw cache, normalized datasets and temporary writes, not a size promise.
    estimate = int(history_days*symbols*32000)
    required = reserve_bytes()+estimate
    result = {"freeBytes":free,"estimatedAdditionalBytes":estimate,"reserveBytes":reserve_bytes(),
              "requiredBytes":required,"sufficient":free>=required,"estimateOnly":True}
    if free<required:
        raise DataError(f"Zu wenig freier Datenspeicher: {free//1048576} MiB frei, konservativ {required//1048576} MiB benötigt. Umfang verkleinern oder Speicher ergänzen.",507)
    return result


def usage(*, fresh=False):
    root = data_dir()
    with _lock:
        old=_cache.get(str(root))
        if old and not fresh and time.monotonic()-old[0]<30: return old[1]
        categories={key:{"bytes":0,"files":0} for key in ("market","datasets","snapshots","research","catalog","other")}
        skipped=0
        if root.exists():
            for folder, dirs, names in os.walk(root,followlinks=False):
                dirs[:]=[d for d in dirs if not (Path(folder)/d).is_symlink()]
                for name in names:
                    path=Path(folder)/name
                    if path.is_symlink(): skipped+=1;continue
                    relative=path.relative_to(root)
                    key=relative.parts[0] if relative.parts[0] in categories else "catalog" if relative.name=="assets.json" else "other"
                    try:
                        categories[key]["bytes"]+=path.stat().st_size
                        categories[key]["files"]+=1
                    except FileNotFoundError: pass  # atomic cache replacement during inventory
        existing=root
        while not existing.exists(): existing=existing.parent
        disk=shutil.disk_usage(existing)
        result={"observedAt":time.time(),"categories":categories,"totalBytes":sum(v["bytes"] for v in categories.values()),
                "freeBytes":disk.free,"diskTotalBytes":disk.total,"reserveBytes":reserve_bytes(),"skippedLinks":skipped,
                "warning":disk.free<reserve_bytes(),"cacheSeconds":30}
        _cache[str(root)]=(time.monotonic(),result)
        return result


def references(db, root):
    """Fail closed: unknown or broken reference documents disable cleanup candidates."""
    refs=set()
    def scan(value):
        if isinstance(value,dict):
            for key,item in value.items():
                if key in ("dataset_id","datasetId") and isinstance(item,str): refs.add(item)
                elif key=="dataset_ids" and isinstance(item,dict): refs.update(item.values())
                else: scan(item)
        elif isinstance(value,list):
            for item in value: scan(item)
    for table in ("symbols","events"):
        refs.update(r[0] for r in db.execute(f"SELECT DISTINCT dataset_id FROM {table} WHERE dataset_id IS NOT NULL"))
    for row in db.execute("SELECT spec FROM jobs"): scan(json.loads(row[0]))
    for row in db.execute("SELECT value FROM settings"): scan(json.loads(row[0]))
    for path in (root/"snapshots").glob("*.json"):
        if path.is_symlink(): raise DataError("Snapshot-Link: Referenzen nicht sicher bestimmbar.",409)
        scan(json.loads(path.read_text("utf-8")))
    return refs


def cleanup_preview():
    from database import connection
    root=data_dir()
    try:
        with connection() as db:
            db.execute("BEGIN")
            refs=references(db,root)
        candidates=[]
        for path in (root/"datasets").glob("*.json"):
            if not path.is_symlink() and re.fullmatch(r"[a-f0-9]{64}",path.stem) and path.stem not in refs:
                candidates.append({"id":path.stem,"bytes":path.stat().st_size})
        return {"previewOnly":True,"deletionSupported":False,"referencedDatasets":len(refs),
                "candidates":candidates,"candidateBytes":sum(v["bytes"] for v in candidates),
                "warning":"Unreferenziert ist kein Löschauftrag. Es wird nichts entfernt; Nutzung kann sich nach dieser Vorschau ändern."}
    except (ValueError,TypeError,OSError) as error:
        raise DataError("Referenzen nicht vollständig lesbar; keine Bereinigungsvorschau freigegeben.",409) from error
