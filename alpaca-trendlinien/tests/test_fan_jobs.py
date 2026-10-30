from copy import deepcopy
import json
import os
import tempfile
import threading
import unittest
from unittest.mock import patch

from database import connection
from datasets import save_dataset
from fan_study import run_dataset as actual_run
from jobs import events_for, get_job, report, run_job, submit, worker_loop
from lab_data import NORMALIZATION
from models import DataError
from research import validate_spec
from storage import references
from test_fan_study import fixture, spec


class FanJobsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {"TORI_DATA_DIR": self.temp.name})
        self.env.start()
        _, self.frames = fixture()
        meta = {"normalization": NORMALIZATION, "quality": {"rejected": 0}, "feed": "iex", "adjustment": "split"}
        self.dataset = save_dataset("TEST", {tf: (rows, dict(meta)) for tf, rows in self.frames.items()},
                                    feed="iex", adjustment="split", session="XNYS regular; synthetic fixture", data_kind="synthetic")
        self.spec = {**spec(self.frames), "entry_mode": "fan", "symbols": ["TEST"], "dataset_ids": {"TEST": self.dataset}}

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def test_optional_mode_validated_offline_only_and_not_in_legacy_defaults(self):
        self.assertNotIn("fan", validate_spec({}))
        self.assertEqual(validate_spec(self.spec)["fan"]["timeframe"], "4h")
        for bad in ({**self.spec, "dataset_ids": {}}, {**self.spec, "universe": "all"},
                    {"fan": {}}, {**self.spec, "fan": {"geometry": {"lookback_days": True}}}):
            with self.assertRaises(DataError):
                validate_spec(bad)

    def test_queue_persistence_paginated_results_events_and_reference_protection(self):
        job = submit(self.spec)
        self.assertEqual(job["manifest"]["entryMode"], "fan")
        self.assertTrue(worker_loop(threading.Event(), once=True))
        finished = get_job(job["id"])
        self.assertEqual(finished["status"], "succeeded")
        self.assertIsNone(finished["symbols"][0]["error"])
        first = report(job["id"], 0, 1, "entries")
        self.assertEqual(len(first["trials"]), 1)
        self.assertTrue(first["page"]["hasMore"])
        self.assertEqual(first["summary"]["originCount"], 5)
        second = report(job["id"], 1, 1, "entries")
        self.assertNotEqual(first["trials"][0]["id"], second["trials"][0]["id"])
        self.assertEqual(first["summary"], second["summary"])
        origin_page = report(job["id"], 0, 20, "origins")
        self.assertEqual(len(origin_page["trials"]), 5)
        page = events_for(job["id"], 1)
        self.assertEqual(page["page"]["order"], "append")
        next_page = events_for(job["id"], 1, page["page"]["nextCursor"])
        self.assertNotEqual(page["items"][0]["id"], next_page["items"][0]["id"])
        from pathlib import Path
        with connection() as db:
            self.assertIn(self.dataset, references(db, Path(self.temp.name)))

    def test_interrupted_replay_is_idempotent_and_matches_uninterrupted_run(self):
        interrupted = submit(self.spec)
        stop = threading.Event()
        def stop_after_first_event(dataset, spec_value, *, emit, **kwargs):
            def wrapped(item):
                emit(item)
                if "event" in item:
                    stop.set()
            return actual_run(dataset, spec_value, emit=wrapped, **kwargs)
        with patch("fan_jobs.run_dataset", side_effect=stop_after_first_event):
            self.assertFalse(run_job(interrupted["id"], stop))
        self.assertGreater(get_job(interrupted["id"])["eventCount"], 0)
        stop.clear()
        self.assertTrue(run_job(interrupted["id"], stop))
        baseline = submit(self.spec)
        self.assertTrue(run_job(baseline["id"]))
        self.assertEqual(events_for(interrupted["id"], 1000)["items"], events_for(baseline["id"], 1000)["items"])
        a, b = report(interrupted["id"]), report(baseline["id"])
        self.assertEqual(a["trials"], b["trials"])
        self.assertEqual(a["summary"], b["summary"])

    def test_changed_engine_cannot_resume_old_job(self):
        job = submit(self.spec)
        with patch("jobs.engine_hash", return_value="changed"):
            with self.assertRaises(DataError) as error:
                run_job(job["id"])
        self.assertEqual(error.exception.status, 409)


if __name__ == "__main__":
    unittest.main()
