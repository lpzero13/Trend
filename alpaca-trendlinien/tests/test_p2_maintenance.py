from contextlib import closing
import copy
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import database
import jobs
import maintenance
from models import DataError
from datasets import save_dataset, read_dataset
from storage import cleanup_preview, preflight, usage
from test_research import fixture_sources


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)/"runtime"
        self.env=patch.dict(os.environ,{"TORI_DATA_DIR":str(self.root),"TORI_AUTO_ENABLED":"0"})
        self.env.start()

    def tearDown(self):
        self.env.stop();self.temp.cleanup()

    def fixture(self):
        identity=save_dataset("TEST",fixture_sources())
        job=jobs.submit({"symbols":["TEST"],"samples":1,"dataset_ids":{"TEST":identity}})
        return identity,job

    def test_existing_unversioned_data_is_migrated_transactionally_and_repeatably(self):
        identity,job=self.fixture()
        with database.connection() as db:
            db.execute("PRAGMA user_version=0")
        with database.connection() as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0],database.SCHEMA_VERSION)
            self.assertEqual(db.execute("SELECT count(*) FROM schema_migrations").fetchone()[0],database.SCHEMA_VERSION)
        self.assertEqual(jobs.get_job(job["id"])["spec"]["dataset_ids"]["TEST"],identity)

    def test_failed_migration_rolls_back_all_steps(self):
        with patch.dict(database.MIGRATIONS,{2:["THIS IS NOT SQL"]}):
            with self.assertRaises(sqlite3.Error):
                with database.connection(): pass
        with closing(sqlite3.connect(self.root/"research/jobs.sqlite3")) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0],0)
            self.assertEqual(db.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0],0)

    def test_future_schema_is_rejected_without_rewriting_it(self):
        with database.connection() as db: db.execute("PRAGMA user_version=999")
        with self.assertRaises(DataError):
            with database.connection(): pass
        with closing(sqlite3.connect(self.root/"research/jobs.sqlite3")) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0],999)

    def test_unknown_legacy_columns_are_not_silently_replaced(self):
        folder=self.root/"research";folder.mkdir(parents=True)
        with closing(sqlite3.connect(folder/"jobs.sqlite3")) as db:
            db.execute("CREATE TABLE jobs(private_payload TEXT)");db.commit()
        with self.assertRaises(DataError):
            with database.connection(): pass
        with closing(sqlite3.connect(folder/"jobs.sqlite3")) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0],0)
            self.assertEqual(db.execute("PRAGMA table_info(jobs)").fetchone()[1],"private_payload")

    def test_backup_restore_can_run_the_original_job_offline(self):
        identity,job=self.fixture()
        cache=self.root/"market";cache.mkdir()
        (cache/"private-cache.json").write_text('{"secret":"not backed up"}')
        jobs.worker_loop(threading.Event(),once=True)
        expected=jobs.report(job["id"])
        destination=Path(self.temp.name)/"backup"
        maintenance.backup(destination)
        self.assertFalse((destination/"market").exists())
        self.assertEqual(maintenance.verify(destination)["databaseVersion"],database.SCHEMA_VERSION)
        restored=Path(self.temp.name)/"restored"
        maintenance.restore(destination,restored)
        with patch.dict(os.environ,{"TORI_DATA_DIR":str(restored)}):
            self.assertEqual(jobs.report(job["id"])["trials"],expected["trials"])
            repeated=jobs.submit({"symbols":["TEST"],"samples":1,"dataset_ids":{"TEST":identity}})
            with patch("jobs.import_dataset",side_effect=AssertionError("offline")):
                jobs.worker_loop(threading.Event(),once=True)
            self.assertEqual(jobs.report(repeated["id"])["summary"],expected["summary"])

    def test_backup_during_append_uses_consistent_database_snapshot(self):
        identity,job=self.fixture()
        original=maintenance.shutil.copyfile
        appended=[]
        def copy_and_append(src,dest):
            if not appended:
                appended.append(jobs.submit({"symbols":["TEST"],"samples":1,"dataset_ids":{"TEST":identity}})["id"])
            return original(src,dest)
        target=Path(self.temp.name)/"backup"
        with patch("maintenance.shutil.copyfile",side_effect=copy_and_append): maintenance.backup(target)
        with closing(sqlite3.connect(target/"research/jobs.sqlite3")) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM jobs").fetchone()[0],1)
        self.assertEqual(len(jobs.list_jobs()),2)

    def test_tampering_and_path_traversal_are_rejected_before_restore(self):
        identity,_=self.fixture()
        saved=Path(self.temp.name)/"backup";maintenance.backup(saved)
        path=saved/"datasets"/(identity+".json")
        path.write_text("corrupt")
        with self.assertRaises(DataError): maintenance.restore(saved,Path(self.temp.name)/"target")
        self.assertFalse((Path(self.temp.name)/"target").exists())
        manifest=json.loads((saved/"manifest.json").read_text("utf-8"))
        manifest["files"]["../private.txt"]={"bytes":0,"sha256":"anything"}
        (saved/"manifest.json").write_text(json.dumps(manifest))
        with self.assertRaises(DataError): maintenance.verify(saved)

    def test_existing_backup_and_restore_targets_are_never_overwritten(self):
        self.fixture()
        saved=Path(self.temp.name)/"backup";maintenance.backup(saved)
        with self.assertRaises(DataError): maintenance.backup(saved)
        with self.assertRaises(DataError): maintenance.restore(saved,self.root)
        with self.assertRaises(DataError): maintenance.restore(saved,self.root/"nested-restore")
        with self.assertRaises(DataError): maintenance.backup(self.root/"recursive")

    def test_preview_preserves_jobs_schedule_and_snapshot_references(self):
        identity,job=self.fixture()
        other=save_dataset("OTHER",fixture_sources())
        orphan=save_dataset("ORPHAN",fixture_sources())
        frozen=save_dataset("FROZEN",fixture_sources())
        (self.root/"snapshots").mkdir()
        (self.root/"snapshots"/("a"*24+".json")).write_text(json.dumps({"id":"a"*24,"basis":"bars","payload":{"datasetId":frozen}}))
        with database.connection() as db:
            db.execute("INSERT OR REPLACE INTO settings VALUES(?,?)",("schedule",json.dumps({"spec":{"dataset_ids":{"OTHER":other}}})))
        preview=cleanup_preview()
        self.assertTrue(preview["previewOnly"])
        self.assertFalse(preview["deletionSupported"])
        self.assertEqual([v["id"] for v in preview["candidates"]],[orphan])
        self.assertTrue((self.root/"datasets"/(identity+".json")).exists())

    def test_backup_rejects_symlinked_dataset_files(self):
        identity,_=self.fixture()
        file=self.root/"datasets"/(identity+".json")
        external=Path(self.temp.name)/"external.json"
        shutil_copy=file.read_bytes();external.write_bytes(shutil_copy)
        file.unlink()
        try:
            file.symlink_to(external)
        except OSError:
            file.write_bytes(shutil_copy)
            self.skipTest("Symlinks unavailable for this account")
        with self.assertRaises(DataError): maintenance.backup(Path(self.temp.name)/"backup")

    def test_corrupt_reference_documents_disable_preview(self):
        _,job=self.fixture()
        with database.connection() as db: db.execute("UPDATE jobs SET spec='invalid' WHERE id=?",(job["id"],))
        with self.assertRaises(DataError): cleanup_preview()

    def test_low_disk_is_reported_before_provider_or_job_write(self):
        with patch("storage.shutil.disk_usage",return_value=SimpleNamespace(free=1,total=100)),patch("jobs.import_dataset") as provider:
            with self.assertRaises(DataError) as error: jobs.submit({})
            self.assertEqual(error.exception.status,507)
            provider.assert_not_called()
        self.assertEqual(jobs.list_jobs(),[])
        self.assertTrue(usage(fresh=True)["categories"]["research"]["bytes"]>0)


if __name__=="__main__": unittest.main()
