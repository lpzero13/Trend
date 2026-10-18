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

BACKUP_SCHEMA="tori-backup-1"


def checksum(path):
    value=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""): value.update(chunk)
    return value.hexdigest()


def checked_dataset(path):
    value=json.loads(path.read_text("utf-8"))
    if value["id"]!=path.stem or value["material"]["schema"]!=SCHEMA or digest(value["material"])!=path.stem:
        raise DataError("Dataset-Prüfsumme stimmt nicht; Sicherung/Wiederherstellung abgebrochen.",409)


def valid_relative(name):
    return name=="research/jobs.sqlite3" or bool(re.fullmatch(r"datasets/[a-f0-9]{64}\.json|snapshots/[a-f0-9]{24}\.json",name))


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
        # All referenced datasets were published before their references committed to SQLite.
        with closing(sqlite3.connect(db_path)) as snapshot:
            refs=references(snapshot,root)
        paths=[p for area in ("datasets","snapshots") for p in (root/area).glob("*.json")]
        present={p.stem for p in paths if p.parent.name=="datasets"}
        if not refs<=present: raise DataError("Referenziertes Dataset fehlt; kein unvollständiges Backup erstellt.",409)
        needed=sum(p.stat().st_size for p in paths)+db_path.stat().st_size
        if shutil.disk_usage(stage).free<needed+16*1024*1024: raise DataError("Zu wenig Platz am Backupziel.",507)
        for path in paths:
            relative=path.relative_to(root).as_posix()
            if path.is_symlink() or path.parent.is_symlink() or not path.resolve().is_relative_to(root) or not valid_relative(relative): raise DataError("Unerwartete Datei/Link im Datenbestand.",409)
            if path.parent.name=="datasets": checked_dataset(path)
            dest=stage/relative;dest.parent.mkdir(exist_ok=True)
            shutil.copyfile(path,dest)
        files={p.relative_to(stage).as_posix():{"sha256":checksum(p),"bytes":p.stat().st_size} for p in stage.rglob("*") if p.is_file()}
        manifest={"schema":BACKUP_SCHEMA,"createdAt":time.time(),"databaseVersion":SCHEMA_VERSION,"files":files,
                  "excluded":["credentials","market cache","catalog cache","logs","worker lock","browser local storage"]}
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
        if value["schema"]!=BACKUP_SCHEMA or not isinstance(value["files"],dict): raise ValueError()
        if "research/jobs.sqlite3" not in value["files"]: raise ValueError()
        for name,meta in value["files"].items():
            if not valid_relative(name): raise ValueError()
            path=root/name
            if any(p.is_symlink() for p in (path,path.parent)) or not path.resolve().is_relative_to(root): raise ValueError()
            if not path.is_file() or path.stat().st_size!=meta["bytes"] or checksum(path)!=meta["sha256"]: raise ValueError()
            if name.startswith("datasets/"): checked_dataset(path)
        with closing(sqlite3.connect((root/"research/jobs.sqlite3").as_uri()+"?mode=ro",uri=True)) as db:
            if db.execute("PRAGMA integrity_check").fetchone()[0]!="ok": raise ValueError()
            version=db.execute("PRAGMA user_version").fetchone()[0]
            if version>SCHEMA_VERSION or version!=value["databaseVersion"]: raise ValueError()
            required=references(db,root)
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
