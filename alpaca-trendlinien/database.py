"""Transactional, append-only SQLite migrations. Future schemas are never opened for writes."""
from contextlib import contextmanager
import sqlite3
import time

from models import DataError
from settings import data_dir

SCHEMA_VERSION = 4
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
    4: [
        "CREATE TABLE IF NOT EXISTS lab_experiments(id TEXT PRIMARY KEY,created REAL NOT NULL,updated REAL NOT NULL,spec TEXT NOT NULL,fingerprint TEXT NOT NULL,engine_hash TEXT NOT NULL,status TEXT NOT NULL,datasets TEXT,plan TEXT,selection TEXT)",
        "CREATE TABLE IF NOT EXISTS lab_attempts(id INTEGER PRIMARY KEY AUTOINCREMENT,experiment_id TEXT NOT NULL,job_id TEXT NOT NULL UNIQUE,stage TEXT NOT NULL,created REAL NOT NULL,status TEXT NOT NULL,result TEXT)",
        "CREATE TABLE IF NOT EXISTS lab_final_access(reservation TEXT PRIMARY KEY,experiment_id TEXT NOT NULL,job_id TEXT NOT NULL,created REAL NOT NULL)",
        "CREATE TABLE IF NOT EXISTS lab_audit(id INTEGER PRIMARY KEY AUTOINCREMENT,owner TEXT NOT NULL,created REAL NOT NULL,kind TEXT NOT NULL,payload TEXT NOT NULL,previous_hash TEXT NOT NULL,hash TEXT NOT NULL)",
        "CREATE TABLE IF NOT EXISTS lab_reviews(id TEXT PRIMARY KEY,created REAL NOT NULL,job_id TEXT NOT NULL,config TEXT NOT NULL,manifest TEXT NOT NULL)",
        "CREATE TABLE IF NOT EXISTS lab_review_cases(pack_id TEXT NOT NULL,id TEXT NOT NULL,sample TEXT NOT NULL,label TEXT,revealed INTEGER NOT NULL DEFAULT 0,tainted INTEGER NOT NULL DEFAULT 0,PRIMARY KEY(pack_id,id))",
        "CREATE INDEX IF NOT EXISTS lab_attempts_experiment ON lab_attempts(experiment_id,id)",
        "CREATE INDEX IF NOT EXISTS lab_audit_owner ON lab_audit(owner,id)",
        "CREATE TABLE IF NOT EXISTS lab_simulations(job_id TEXT NOT NULL,section TEXT NOT NULL,profile TEXT NOT NULL,family TEXT NOT NULL,result TEXT NOT NULL,PRIMARY KEY(job_id,section,profile,family))",
        "CREATE TABLE IF NOT EXISTS lab_final_windows(symbol TEXT NOT NULL,start_at INTEGER NOT NULL,end_at INTEGER NOT NULL,experiment_id TEXT NOT NULL,job_id TEXT NOT NULL,dataset_id TEXT NOT NULL,PRIMARY KEY(job_id,symbol))",
        "CREATE INDEX IF NOT EXISTS lab_final_window_lookup ON lab_final_windows(symbol,start_at,end_at)",
    ],
}
REQUIRED = {"jobs":{"id","created","updated","status","spec","manifest","universe","current_symbol","error","automatic"},
            "symbols":{"job_id","symbol","dataset_id","plan","done","error"},
            "trials":{"job_id","id","result"},"events":{"job_id","id","dataset_id","event"},
            "settings":{"key","value"},"job_progress":{"job_id","phase","phase_started","progress_at","detail"},
            "dataset_quality":{"dataset_id","summary"},
            "lab_experiments":{"id","spec","fingerprint","engine_hash","status","datasets","plan","selection"},
            "lab_attempts":{"id","experiment_id","job_id","stage","status","result"},
            "lab_final_access":{"reservation","experiment_id","job_id"},
            "lab_audit":{"id","owner","payload","previous_hash","hash"},
            "lab_reviews":{"id","job_id","config","manifest"},
            "lab_review_cases":{"pack_id","id","sample","label","revealed","tainted"},
            "lab_simulations":{"job_id","section","profile","family","result"},
            "lab_final_windows":{"symbol","start_at","end_at","experiment_id","job_id","dataset_id"}}


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
