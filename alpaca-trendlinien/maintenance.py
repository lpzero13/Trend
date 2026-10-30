"""Consistent SQLite backups plus immutable datasets. Restore only to a new directory."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import tempfile
import time
from contextlib import closing

from models import DataError
from settings import data_dir
from database import connection, SCHEMA_VERSION
from datasets import digest, SCHEMA
from storage import references

BACKUP_SCHEMA="tori-backup-2"


def checksum(path):
    value=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""): value.update(chunk)
    return value.hexdigest()


def checked_dataset(path):
    from parquet_store import hydrate
    from duckdb import Error as ParquetError
    try:
        if path.is_symlink() or path.parent.is_symlink():raise ValueError("link")
        value=hydrate(json.loads(path.read_text("utf-8")),path.parent.parent)
        if value["id"]!=path.stem or value["material"]["schema"]!=SCHEMA or digest(value["material"])!=path.stem:
            raise ValueError("checksum")
    except (ValueError,TypeError,KeyError,OSError,ParquetError):
        raise DataError("Dataset-Prüfsumme stimmt nicht; Sicherung/Wiederherstellung abgebrochen.",409) from None


def valid_relative(name):
    return name in ("research/jobs.sqlite3","forward/watch.sqlite3") or bool(re.fullmatch(r"datasets/[a-f0-9]{64}\.json|datasets/chunks/[a-f0-9]{64}\.parquet|imports/chunks/[a-f0-9]{64}\.parquet|snapshots/[a-f0-9]{24}\.json",name))


def new_target(target):
    path=Path(target).expanduser().resolve()
    if path.exists(): raise DataError("Ziel existiert bereits; nur ein neuer Zielordner ist erlaubt.",409)
    if not path.parent.is_dir(): raise DataError("Übergeordneten Zielordner zuerst anlegen.",400)
    return path


def backup(target):
    target=new_target(target)
    root=data_dir()
    if target.is_relative_to(root): raise DataError("Backupziel muss außerhalb des aktiven Datenordners liegen.",400)
    db_source=root/"research/jobs.sqlite3"
    initial_bytes=db_source.stat().st_size if db_source.exists() else 0
    if shutil.disk_usage(target.parent).free<initial_bytes+16*1024*1024:
        raise DataError("Zu wenig Platz am Backupziel.",507)
    root.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".tori-backup-",dir=target.parent) as folder:
        stage=Path(folder)
        (stage/"research").mkdir()
        db_path=stage/"research/jobs.sqlite3"
        with connection() as source, closing(sqlite3.connect(db_path)) as destination:
            source.backup(destination)
        watch=root/"forward/watch.sqlite3"
        if watch.exists():
            if watch.is_symlink() or watch.parent.is_symlink():raise DataError("Beobachtungsdatenbank darf kein Link sein.",409)
            (stage/"forward").mkdir()
            with closing(sqlite3.connect(watch.as_uri()+"?mode=ro",uri=True)) as source, closing(sqlite3.connect(stage/"forward/watch.sqlite3")) as destination:
                source.backup(destination)
        # All referenced datasets were published before their references committed to SQLite.
        with closing(sqlite3.connect(db_path)) as snapshot:
            refs=references(snapshot,root,forward_root=stage)
            from history_archive import backup_chunks
            archive_paths=backup_chunks(snapshot,root)
            from archive_state import backup_chunks as fast_chunks
            archive_paths.update(fast_chunks(snapshot,root))
        paths=[p for area in ("datasets","snapshots") for p in (root/area).glob("*.json")]
        # Snapshot immutable manifests before resolving their shared block graph.
        # Never copy unrelated orphan/temp chunks or a local rollback archive.
        chunks=set()
        from parquet_store import block_path
        for path in list(paths):
            if path.parent.name=="datasets":
                checked_dataset(path)
                value=json.loads(path.read_text("utf-8"))
                for entry in value.get("storage",{}).get("blocks",[]):
                    chunks.add(block_path(root,entry["path"]))
        paths.extend(sorted(chunks))
        paths.extend(root/name for name in archive_paths)
        present={p.stem for p in paths if p.parent.name=="datasets"}
        if not refs<=present: raise DataError("Referenziertes Dataset fehlt; kein unvollständiges Backup erstellt.",409)
        needed=sum(p.stat().st_size for p in paths)+db_path.stat().st_size
        if shutil.disk_usage(stage).free<needed+16*1024*1024: raise DataError("Zu wenig Platz am Backupziel.",507)
        for path in paths:
            relative=path.relative_to(root).as_posix()
            if path.is_symlink() or path.parent.is_symlink() or not path.resolve().is_relative_to(root) or not valid_relative(relative): raise DataError("Unerwartete Datei/Link im Datenbestand.",409)
            if path.parent.name=="datasets": checked_dataset(path)
            dest=stage/relative;dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(path,dest)
        files={p.relative_to(stage).as_posix():{"sha256":checksum(p),"bytes":p.stat().st_size} for p in stage.rglob("*") if p.is_file()}
        manifest={"schema":BACKUP_SCHEMA,"createdAt":time.time(),"databaseVersion":SCHEMA_VERSION,"files":files,
                  "excluded":["credentials","market cache","catalog cache","logs","worker lock","browser local storage","legacy-json rollback archive"]}
        (stage/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),"utf-8")
        verify(stage)
        # Rename a completed directory, never expose a partial backup under its final name.
        stage.rename(target)
    return {"backup":str(target),"files":len(files),"bytes":sum(v["bytes"] for v in files.values()),"schema":BACKUP_SCHEMA}


def verify(folder):
    root=Path(folder).expanduser().resolve()
    if not root.is_dir() or (root/"manifest.json").is_symlink(): raise DataError("Ungültiger Sicherungsordner.",400)
    try:
        value=json.loads((root/"manifest.json").read_text("utf-8"))
        if value["schema"] not in ("tori-backup-1",BACKUP_SCHEMA) or not isinstance(value["files"],dict): raise ValueError()
        if "research/jobs.sqlite3" not in value["files"]: raise ValueError()
        for name,meta in value["files"].items():
            if not valid_relative(name): raise ValueError()
            if value["schema"]=="tori-backup-1" and name.endswith('.parquet'):raise ValueError("old backup schema")
            path=root/name
            if any(p.is_symlink() for p in (path,path.parent)) or not path.resolve().is_relative_to(root): raise ValueError()
            if not path.is_file() or path.stat().st_size!=meta["bytes"] or checksum(path)!=meta["sha256"]: raise ValueError()
        # All files must be present/hash-checked before a manifest is hydrated.
        for name in value["files"]:
            if re.fullmatch(r"datasets/[a-f0-9]{64}\.json",name):
                path=root/name
                checked_dataset(path)
                document=json.loads(path.read_text("utf-8"))
                if any(e["path"] not in value["files"] for e in document.get("storage",{}).get("blocks",[])):
                    raise ValueError("backup missing Parquet block")
        if "forward/watch.sqlite3" in value["files"]:
            with closing(sqlite3.connect((root/"forward/watch.sqlite3").as_uri()+"?mode=ro",uri=True)) as watch:
                if watch.execute("PRAGMA integrity_check").fetchone()[0]!="ok":raise ValueError()
        with closing(sqlite3.connect((root/"research/jobs.sqlite3").as_uri()+"?mode=ro",uri=True)) as db:
            if db.execute("PRAGMA integrity_check").fetchone()[0]!="ok": raise ValueError()
            version=db.execute("PRAGMA user_version").fetchone()[0]
            if version>SCHEMA_VERSION or version!=value["databaseVersion"]: raise ValueError()
            required=references(db,root)
            from history_archive import backup_chunks
            archive_paths=backup_chunks(db,root)
            from archive_state import backup_chunks as fast_chunks
            archive_paths.update(fast_chunks(db,root))
            if any(name not in value['files'] for name in archive_paths): raise ValueError('backup missing archive checkpoint')
            if not all(f"datasets/{identity}.json" in value["files"] for identity in required): raise ValueError()
        return value
    except (ValueError,KeyError,TypeError,OSError,sqlite3.Error) as error:
        raise DataError("Backupprüfung fehlgeschlagen; nichts wiederhergestellt.",409) from error


def restore(folder, target):
    target=new_target(target)
    value=verify(folder)
    source=Path(folder).expanduser().resolve()
    if target.is_relative_to(source) or target.is_relative_to(data_dir()): raise DataError("Anderen, neuen Zielordner außerhalb des aktiven Datenordners verwenden.",400)
    needed=sum(meta["bytes"] for meta in value["files"].values())
    if shutil.disk_usage(target.parent).free<needed+16*1024*1024: raise DataError("Zu wenig Platz am Restoreziel.",507)
    with tempfile.TemporaryDirectory(prefix=".tori-restore-",dir=target.parent) as folder:
        stage=Path(folder)
        for name in value["files"]:
            dest=stage/name;dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source/name,dest)
            if checksum(dest)!=value["files"][name]["sha256"]: raise DataError("Backup während Restore verändert.",409)
        stage.rename(target)
    return {"restoredTo":str(target),"files":len(value["files"]),"overwrite":False,
            "next":"Separaten Testdienst mit TORI_DATA_DIR auf dieses Ziel starten; aktive Installation bleibt unverändert."}
