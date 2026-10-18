import copy
import json
import os
import tempfile
import threading
import unittest
from unittest.mock import patch

import jobs
import lab_registry as registry
from database import connection
from datasets import read_dataset, save_dataset
from lab_splits import create
from models import DataError
from research import validate_spec
from storage import cleanup_preview
from test_research import fixture_sources


class RegistryJobTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.env=patch.dict(os.environ,{"TORI_DATA_DIR":self.temp.name});self.env.start()
        self.dataset_id=save_dataset("TEST",fixture_sources())
        self.spec=validate_spec({"symbols":["TEST"],"entry_mode":"lab","dataset_ids":{"TEST":self.dataset_id},
                    "lab":{"allow_native":True,"benchmark_symbol":"","profiles":["reference","baseline"],"bootstrap_samples":50}})
        jobs.schedule({"enabled":False,"spec":{}})

    def tearDown(self):
        self.env.stop();self.temp.cleanup()

    def bound(self):
        identity=registry.register(self.spec,jobs.engine_hash());spec=copy.deepcopy(self.spec);spec["lab"]["experiment_id"]=identity
        plan=create([read_dataset(self.dataset_id)],spec)
        registry.bind_data(identity,{"TEST":self.dataset_id},plan)
        return identity,plan,spec

    def test_registration_budget_engine_data_and_final_test_are_locked(self):
        identity,plan,spec=self.bound()
        self.assertEqual(registry.register(spec,jobs.engine_hash()),identity)
        changed=copy.deepcopy(spec);changed["lab"]["profiles"]=["baseline"]
        with self.assertRaises(DataError):registry.register(changed,jobs.engine_hash())
        with self.assertRaises(DataError):registry.register(spec,"another-engine")
        with self.assertRaises(DataError):registry.bind_data(identity,{"TEST":"a"*64},plan)
        with self.assertRaises(DataError):registry.start_attempt(identity,"v"*32,"validation")
        with self.assertRaises(DataError):registry.start_attempt(identity,"h"*32,"holdout",confirm_final_test=True)
        registry.start_attempt(identity,"d"*32,"development")
        registry.start_attempt(identity,"d"*32,"development")
        registry.finish_attempt(identity,"d"*32,"succeeded",{"stage":"development"})
        registry.start_attempt(identity,"v"*32,"validation")
        registry.finish_attempt(identity,"v"*32,"succeeded",{"stage":"validation"})
        registry.seal(identity,"reference","Chosen without opening final outcomes")
        with self.assertRaises(DataError):registry.seal(identity,"baseline","Try another after looking at outcome")
        with self.assertRaises(DataError):registry.start_attempt(identity,"h"*32,"holdout")
        registry.start_attempt(identity,"h"*32,"holdout",confirm_final_test=True)
        registry.start_attempt(identity,"h"*32,"holdout",confirm_final_test=True)
        with self.assertRaises(DataError):registry.start_attempt(identity,"i"*32,"holdout",confirm_final_test=True)
        # A new experiment cannot relabel the same final data as untouched.
        other=registry.register(self.spec,jobs.engine_hash());registry.bind_data(other,{"TEST":self.dataset_id},plan)
        for stage in ("development","validation"):
            job=stage+"2";registry.start_attempt(other,job,stage);registry.finish_attempt(other,job,"succeeded",{"stage":stage})
        registry.seal(other,"baseline","Separate comparison on identical data")
        with self.assertRaises(DataError):registry.start_attempt(other,"j"*32,"holdout",confirm_final_test=True)
        # A new dataset revision with overlapping dates does not restore blindness.
        revised=copy.deepcopy(self.spec);revised["dataset_ids"]["TEST"]="e"*64
        revision=registry.register(revised,jobs.engine_hash());revised_plan=copy.deepcopy(plan);revised_plan["dataset_ids"]["TEST"]="e"*64
        registry.bind_data(revision,{"TEST":"e"*64},revised_plan)
        for stage in ("development","validation"):
            job=stage+"3";registry.start_attempt(revision,job,stage);registry.finish_attempt(revision,job,"succeeded",{"stage":stage})
        registry.seal(revision,"baseline","Testing a data revision explicitly")
        with self.assertRaises(DataError):registry.start_attempt(revision,"k"*32,"holdout",confirm_final_test=True)
        self.assertTrue(registry.get(identity)["finalOpened"])
        self.assertFalse(registry.get(revision)["finalOpened"])
        self.assertEqual(cleanup_preview()["candidates"],[])

    def test_paginated_append_only_audit_has_stable_high_water_and_detects_page_tamper(self):
        identity,_,_=self.bound();first=registry.journal(identity,limit=1)
        registry.finish_attempt(identity,"f"*32,"failed",{"stage":"development","error":"import failed"})
        second=registry.journal(identity,after=first["page"]["nextAfter"],through=first["page"]["through"],limit=1)
        self.assertFalse(second["page"]["hasMore"])
        self.assertEqual(len(registry.get(identity)["attempts"]),1)
        with connection() as db:db.execute("UPDATE lab_audit SET payload='{}' WHERE id=?",(second["items"][0]["id"],))
        with self.assertRaises(DataError):registry.journal(identity,after=first["page"]["nextAfter"],through=first["page"]["through"],limit=1)
        for args in ({"limit":1001},{"after":True},{"through":-1}):
            with self.assertRaises(DataError):registry.journal(identity,**args)

    def test_offline_queue_binds_sources_reports_all_profiles_and_reuses_data_for_validation(self):
        with patch("lab_jobs.import_dataset",side_effect=AssertionError("unexpected provider call")),patch("lab_profiles.pair",return_value={"red":None,"green":None,"reds":[],"greens":[]}):
            job=jobs.submit(self.spec)
            self.assertTrue(jobs.worker_loop(threading.Event(),once=True))
            result=jobs.report(job["id"],limit=1,entry_filter="entries")
            self.assertEqual(result["job"]["status"],"succeeded")
            exp=registry.get(job["spec"]["lab"]["experiment_id"])
            self.assertEqual(exp["attempts"][0]["status"],"succeeded")
            self.assertEqual(exp["datasets"],{"TEST":self.dataset_id})
            self.assertEqual(result["summary"]["stage"],"development")
            self.assertTrue(result["summary"]["complete"])
            spec=copy.deepcopy(job["spec"]);spec["lab"]["stage"]="validation"
            val=jobs.submit(spec);jobs.worker_loop(threading.Event(),once=True)
            self.assertEqual(jobs.get_job(val["id"])["status"],"succeeded")
            sections=jobs.get_job(val["id"])["symbols"][0]["plan"]["sections"]
            self.assertTrue(next(iter(sections.values()))["complete"])
            self.assertEqual(len(registry.get(exp["id"])["attempts"]),2)

    def test_worker_interruption_replays_same_case_ids_without_duplicate_events(self):
        job=jobs.submit(self.spec);calls=[]
        def scan(dataset,spec,phase,**kw):
            calls.append(True)
            kw["emit"]({"event":{"id":"one-event","kind":"lab_test","time":phase["startAt"],"closedAt":phase["startAt"]}})
            kw["emit"]({"trial":{"id":"one-case","profile":"reference","labPhase":"development","symbol":"TEST","datasetId":self.dataset_id,"startAt":phase["startAt"],"variants":[]}})
            return {"complete":len(calls)>1,"profiles":{}}
        with patch("lab_jobs.import_dataset",side_effect=AssertionError("unexpected provider call")),patch("lab_jobs.scan_stock",side_effect=scan):
            self.assertFalse(jobs.run_job(job["id"]))
            self.assertEqual(jobs.get_job(job["id"])["completedTrials"],1)
            jobs.worker_loop(threading.Event(),once=True)
        final=jobs.get_job(job["id"])
        self.assertEqual(final["status"],"succeeded");self.assertEqual(final["completedTrials"],1);self.assertEqual(final["eventCount"],1)
        self.assertEqual(len(registry.get(job["spec"]["lab"]["experiment_id"])["attempts"]),1)

    def test_failed_preparation_and_queued_cancellation_are_preserved(self):
        spec=copy.deepcopy(self.spec);spec["lab"]["allow_native"]=False
        job=jobs.submit(spec)
        jobs.worker_loop(threading.Event(),once=True)
        final=jobs.get_job(job["id"])
        self.assertEqual(final["status"],"failed")
        record=registry.get(job["spec"]["lab"]["experiment_id"])
        self.assertEqual(record["attempts"][0]["status"],"failed")
        second=jobs.submit(self.spec);jobs.cancel(second["id"])
        record=registry.get(second["spec"]["lab"]["experiment_id"])
        self.assertEqual(record["attempts"][0]["status"],"cancelled")


if __name__=="__main__":unittest.main()
