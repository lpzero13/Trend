"""Transactional, append-only SQLite migrations. Future schemas are never opened for writes."""
from contextlib import contextmanager
import sqlite3
import time

from models import DataError
from settings import data_dir

SCHEMA_VERSION = 3
MIGRATIONS = {
    1: [
        "CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,created REAL NOT NULL,updated REAL NOT NULL,status TEXT NOT NULL,spec TEXT NOT NULL,manifest TEXT NOT NULL,universe TEXT,current_symbol TEXT,error TEXT,automatic INTEGER NOT NULL DEFAULT 0)",
        "CREATE TABLE IF NOT EXISTS symbols(job_id TEXT,symbol TEXT,dataset_id TEXT,plan TEXT,done INTEGER DEFAULT 0,error TEXT,PRIMARY KEY(job_id,symbol))",
        "CREATE TABLE IF NOT EXISTS trials(job_id TEXT,id TEXT,result TEXT,PRIMARY KEY(job_id,id))",
        "CREATE TABLE IF NOT EXISTS events(job_id TEXT,id TEXT,dataset_id TEXT,event TEXT,PRIMARY KEY(job_id,id))",
        "CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL)",
    ],
    2: [
        "CREATE INDEX IF NOT EXISTS events_job_sequence ON events(job_id)",
        "CREATE TABLE IF NOT EXISTS job_progress(job_id TEXT PRIMARY KEY,phase TEXT NOT NULL,phase_started REAL NOT NULL,progress_at REAL NOT NULL,detail TEXT NOT NULL)",
    ],
    3: ["CREATE TABLE IF NOT EXISTS dataset_quality(dataset_id TEXT PRIMARY KEY,summary TEXT NOT NULL)"],
}
REQUIRED = {"jobs":{"id","created","updated","status","spec","manifest","universe","current_symbol","error","automatic"},
            "symbols":{"job_id","symbol","dataset_id","plan","done","error"},
            "trials":{"job_id","id","result"},"events":{"job_id","id","dataset_id","event"},
            "settings":{"key","value"},"job_progress":{"job_id","phase","phase_started","progress_at","detail"},
            "dataset_quality":{"dataset_id","summary"}}


def migrate(db):
    version = db.execute("PRAGMA user_version").fetchone()[0]
    if version > SCHEMA_VERSION:
        raise DataError("Datenbank stammt aus einer neueren Version; Update oder passende Wiederherstellung erforderlich.",409)
    if version == SCHEMA_VERSION:
        return
    db.execute("BEGIN IMMEDIATE")
    try:
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if version > SCHEMA_VERSION:
            raise DataError("Neuere Datenbankversion wird nicht verändert.",409)
        db.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY,applied_at REAL NOT NULL)")
        for target in range(version+1, SCHEMA_VERSION+1):
            for statement in MIGRATIONS[target]:
                db.execute(statement)
            db.execute("INSERT OR REPLACE INTO schema_migrations VALUES(?,?)",(target,time.time()))
            db.execute(f"PRAGMA user_version={target}")
        for table, required in REQUIRED.items():
            found = {row[1] for row in db.execute(f"PRAGMA table_info({table})")}
            if not required <= found:
                raise DataError(f"Unbekanntes Altschema in {table}; keine automatische Überschreibung.",409)
        db.commit()
    except BaseException:
        db.rollback()
        raise


@contextmanager
def connection():
    folder = data_dir()/"research"
    folder.mkdir(parents=True,exist_ok=True)
    db = sqlite3.connect(folder/"jobs.sqlite3",timeout=10)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA busy_timeout=10000")
        migrate(db)
        db.execute("PRAGMA journal_mode=WAL")
        yield db
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()
