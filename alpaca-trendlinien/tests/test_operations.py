import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import jobs
import operations
from datasets import import_dataset, read_dataset, save_dataset
from models import DataError
from test_research import fixture_sources


class OperationsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {"TORI_DATA_DIR":self.temp.name,"TORI_AUTO_ENABLED":"0"})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def add_events(self, identity, ids):
        with jobs.connection() as db:
            db.executemany("INSERT INTO events VALUES(?,?,?,?)", [(identity,i,"dataset",json.dumps({"id":i})) for i in ids])

    def test_pages_pin_a_consistent_prefix_while_another_connection_appends(self):
        identity = jobs.submit({})["id"]
        self.add_events(identity, ["z", "b", "m", "a", "y"])
        page = jobs.events_for(identity, 2)
        snapshot = page["page"]["snapshot"]
        received = page["items"]
        self.add_events(identity, ["0", "new"])
        while page["page"]["hasMore"]:
            page = jobs.events_for(identity, 2, page["page"]["nextCursor"])
            self.assertEqual(page["page"]["snapshot"], snapshot)
            self.assertEqual(page["page"]["total"], 5)
            received.extend(page["items"])
        self.assertEqual([e["id"] for e in received], ["z","b","m","a","y"])
        self.assertEqual(jobs.events_for(identity)["page"]["total"], 7)
        self.assertIsNone(page["page"]["nextCursor"])

    def test_bad_limits_cursors_and_cross_job_reuse_are_rejected(self):
        first, second = jobs.submit({})["id"], jobs.submit({})["id"]
        self.add_events(first, ["a","b"])
        token = jobs.events_for(first,1)["page"]["nextCursor"]
        for limit,cursor in [(0,None),(1001,None),(True,None),(1,"bad"),(1,"x"*513)]:
            with self.assertRaises(DataError): jobs.events_for(first,limit,cursor)
        with self.assertRaises(DataError): jobs.events_for(second,1,token)
        for payload in [[], None, {"v":1,"job":first,"after":-1,"through":2}, {"v":1,"job":first,"after":True,"through":2}]:
            encoded=base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
            with self.assertRaises(DataError): jobs.events_for(first,1,encoded)
        self.assertEqual(jobs.events_for(second)["items"], [])

    def test_database_extension_preserves_existing_jobs_and_events(self):
        identity = jobs.submit({})["id"]
        self.add_events(identity,["old"])
        with jobs.connection() as db: db.execute("DROP TABLE job_progress")
        self.assertEqual(jobs.events_for(identity)["items"], [{"id":"old"}])
        operations.phase(identity,"importing",symbol="TEST")
        self.assertEqual(jobs.get_job(identity)["progress"]["phase"], "importing")

    def test_job_list_omits_large_plans_but_individual_status_preserves_them(self):
        identity = jobs.submit({})["id"]
        with jobs.connection() as db:
            db.execute("INSERT INTO symbols(job_id,symbol,plan) VALUES(?,?,?)", (identity,"TEST",json.dumps({"starts":list(range(200))})))
        self.assertNotIn("plan", jobs.list_jobs()[0]["symbols"][0])
        self.assertEqual(len(jobs.get_job(identity)["symbols"][0]["plan"]["starts"]),200)

    def worker_state(self, identity=None, now=1000):
        with jobs.connection() as db:
            operations.put(db,"worker",{"owner":"test","heartbeatAt":now,"loopAt":now,"jobId":identity,"stoppedAt":None})

    def test_worker_lock_and_heartbeat_and_progress_are_independent(self):
        identity = jobs.submit({})["id"]
        with patch("operations.time.time",return_value=1000): operations.phase(identity,"events",completed=2,total=10)
        self.worker_state(identity)
        with patch("jobs.worker_active",return_value=True):
            self.assertEqual(operations.status(now=1001)["worker"]["state"],"working")
            self.assertEqual(operations.status(now=1031)["worker"]["state"],"unresponsive")
            self.worker_state(identity,now=1400)
            value=operations.status(now=1401)
            self.assertEqual(value["worker"]["state"],"stalled")
            self.assertFalse(value["readiness"]["worker"])
        with patch("jobs.worker_active",return_value=False):
            self.assertEqual(operations.status(now=1001)["worker"]["state"],"absent")

    def test_idle_loop_stall_and_old_workers_without_telemetry_are_visible(self):
        with patch("jobs.worker_active",return_value=True):
            self.assertEqual(operations.status()["worker"]["state"],"unverified")
            with jobs.connection() as db: operations.put(db,"worker",{"jobId":None})
            self.assertEqual(operations.status()["worker"]["state"],"unverified")
            self.worker_state()
            with jobs.connection() as db:
                value=operations.setting(db,"worker")
                operations.put(db,"worker",{**value,"heartbeatAt":1400})
            self.assertEqual(operations.status(now=1401)["worker"]["state"],"stalled")

    def test_phase_start_is_preserved_and_completed_progress_is_separate(self):
        identity=jobs.submit({})["id"]
        with patch("operations.time.time",return_value=1000): operations.phase(identity,"events",completed=1,total=10)
        with patch("operations.time.time",return_value=1005): operations.phase(identity,"events",completed=2,total=10)
        progress=jobs.get_job(identity)["progress"]
        self.assertEqual(progress["phase_started"],1000)
        self.assertEqual(progress["progress_at"],1005)
        with patch("operations.time.time",return_value=1010): operations.phase(identity,"trials",completed=0,total=3)
        self.assertEqual(jobs.get_job(identity)["progress"]["phase_started"],1010)

    def test_health_reads_do_not_fetch_or_reauthenticate_with_provider(self):
        with patch("alpaca._request",side_effect=AssertionError("no network")),patch("jobs.import_dataset",side_effect=AssertionError("no import")):
            value=operations.status()
        self.assertEqual(value["readiness"]["providerAuthentication"],"not_checked_by_health")
        self.assertIsNone(value["lastSuccessfulImport"])

    def test_offline_dataset_does_not_masquerade_as_a_fresh_import(self):
        identity=save_dataset("TEST",fixture_sources())
        dataset=read_dataset(identity)
        operations.record_dataset(dataset)
        value=operations.status()
        self.assertIsNone(value["lastSuccessfulImport"])
        self.assertEqual(value["lastDataset"]["datasetId"],identity)
        self.assertIsNotNone(value["dataAge"]["4h"]["fetchAgeSeconds"])

    def test_cached_dataset_import_uses_current_check_metadata_without_rewriting_dataset(self):
        sources=fixture_sources()
        identity=save_dataset("TEST",sources)
        before=read_dataset(identity)
        def loaded(symbol,tf,**kwargs):
            kwargs["progress"](tf,1,2)
            rows,meta=sources[tf]
            return rows,{**meta,"fetchedAt":"2026-10-18T08:00:00Z","mode":"cache"}
        updates=[]
        with patch("datasets.load_bars",side_effect=loaded):
            self.assertEqual(import_dataset("TEST",progress=lambda *args:updates.append(args)),identity)
        self.assertEqual(len(updates),3)
        self.assertEqual(read_dataset(identity),before)
        self.assertEqual(operations.status()["lastSuccessfulImport"]["sources"]["4h"]["fetchedAt"],"2026-10-18T08:00:00Z")

    def test_monitor_heartbeat_keeps_running_but_does_not_forge_work_progress(self):
        with jobs.worker_lock() as locked:
            self.assertTrue(locked)
            with operations.monitor(interval=.02):
                original=operations.status()["worker"]["heartbeatAt"]
                deadline=time.monotonic()+3
                while operations.status()["worker"]["heartbeatAt"] <= original and time.monotonic()<deadline:
                    threading.Event().wait(.02)
                self.assertGreater(operations.status()["worker"]["heartbeatAt"],original)
                self.assertEqual(operations.status()["worker"]["state"],"idle")
        self.assertEqual(operations.status()["worker"]["state"],"absent")

    def test_process_kill_is_detected_and_offline_job_resumes(self):
        identity=save_dataset("TEST",fixture_sources())
        job=jobs.submit({"symbols":["TEST"],"samples":1,"dataset_ids":{"TEST":identity}})
        script="import jobs,operations,threading,time\ndef block(identity,stop):\n operations.phase(identity,'importing',symbol='TEST')\n time.sleep(60)\njobs.run_job=block\njobs.worker_loop(threading.Event(),once=True)"
        child=subprocess.Popen([sys.executable,"-c",script],cwd=Path(__file__).resolve().parents[1],
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        try:
            deadline=time.monotonic()+8
            while operations.status()["worker"]["state"]!="working" and time.monotonic()<deadline:
                threading.Event().wait(.03)
            self.assertEqual(operations.status()["worker"]["state"],"working")
            child.kill();child.wait(timeout=5)
            self.assertEqual(operations.status()["worker"]["state"],"absent")
            with patch("jobs.import_dataset",side_effect=AssertionError("offline")):
                jobs.worker_loop(threading.Event(),once=True)
            self.assertEqual(jobs.get_job(job["id"])["status"],"succeeded")
        finally:
            if child.poll() is None: child.kill();child.wait(timeout=5)


if __name__ == "__main__": unittest.main()
