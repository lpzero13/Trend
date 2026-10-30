from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from datasets import save_dataset
from fan_api import catalog, get
from fan_chart import apply
from fan_geometry import FanEngine, FanRules
from fan_study import source_gaps
from jobs import run_job, submit, report
from lab_data import NORMALIZATION
from models import DataError
from server import Handler
from test_fan_study import fixture, spec


class FanApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {"TORI_DATA_DIR": self.temp.name})
        self.env.start()
        _, self.frames = fixture()
        meta = {"normalization": NORMALIZATION, "quality": {"rejected": 0}, "feed": "iex", "adjustment": "split"}
        self.dataset = save_dataset("TEST", {tf:(rows, dict(meta)) for tf,rows in self.frames.items()},
                                    feed="iex", adjustment="split", data_kind="synthetic")
        self.spec = {**spec(self.frames), "entry_mode":"fan", "symbols":["TEST"], "dataset_ids":{"TEST":self.dataset}}
        self.job = submit(self.spec)
        run_job(self.job["id"])
        self.case = report(self.job["id"], entry_filter="entries")["trials"][0]

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def query(self, **more):
        return {k:[v] for k,v in {"dataset":self.dataset, "fan_job":self.job["id"], "fan_case":self.case["id"], "engine":"fan_extreme", **more}.items()}

    def test_catalog_is_local_and_marks_synthetic_provenance(self):
        result = catalog()
        self.assertEqual(result["providerCalls"], 0)
        self.assertEqual(result["items"][0]["dataKind"], "synthetic")
        self.assertNotIn("bars", json.dumps(result))

    def test_case_chart_freezes_original_line_and_never_exposes_future_entry_or_result(self):
        at = self.case["signal"]["signalAt"]
        before = datetime.fromtimestamp(at-1, timezone.utc).isoformat()
        early = get("/api/fan/chart", self.query(asof=before))
        self.assertEqual(early["fanCase"]["status"], "before_signal")
        self.assertNotIn("researchSetup", early)
        signal_view = get("/api/fan/chart", self.query())
        self.assertEqual(signal_view["fanCase"]["status"], "signal_available")
        self.assertIsNone(signal_view["researchSetup"]["entryPrice"])
        self.assertEqual(signal_view["lanes"]["4h"]["retest"]["ray"]["id"], self.case["signal"]["line"]["id"])
        self.assertNotIn("paths", signal_view)
        self.assertNotIn("netReturnPct", json.dumps(signal_view))
        for view in (early, signal_view):
            self.assertTrue(all(b["end"] <= view["analysisCutoff"] for chart in view["charts"].values() for b in chart["bars"]))
        later = datetime.fromtimestamp(self.frames["4h"][94].end, timezone.utc).isoformat()
        advanced = get("/api/fan/chart", self.query(asof=later))
        self.assertEqual(advanced["fanCase"]["status"], "entered")
        self.assertEqual(advanced["researchSetup"]["initialStop"], self.case["signal"]["initialStop"])
        self.assertEqual(advanced["lanes"]["4h"]["retest"]["ray"]["a_price"], signal_view["lanes"]["4h"]["retest"]["ray"]["a_price"])

    def test_chart_and_observer_geometry_share_source_prefix_calculation(self):
        payload = get("/api/fan/chart", {"dataset":[self.dataset], "asof":[datetime.fromtimestamp(self.frames["4h"][80].end, timezone.utc).isoformat()], "engine":["fan_extreme"]})
        rules = FanRules()
        rows = self.frames["4h"][:81]
        engine = FanEngine("TEST", "4h", rules)
        gaps = source_gaps(rows, rows[-1].end, "4h")
        for i, bar in enumerate(rows):
            if i in gaps:
                engine.reset_history()
            engine.push(bar)
        self.assertEqual(payload["lanes"]["4h"]["red"], engine.snapshot()["red"])
        self.assertIn("1W", payload["charts"])

    def test_holdout_and_wrong_case_cannot_be_used_through_case_chart_even_when_analysis_off(self):
        later = datetime.fromtimestamp(self.case["cutoff"]+1, timezone.utc).isoformat()
        for analysis in ("0", "1"):
            with self.assertRaises(DataError):
                get("/api/fan/chart", self.query(dataset="a"*64, analysis=analysis))
            with self.assertRaises(DataError) as exc:
                get("/api/fan/chart", self.query(asof=later, analysis=analysis))
            self.assertEqual(exc.exception.status, 404)
        with self.assertRaises(DataError):
            get("/api/fan/chart", self.query(engine="fan_local"))
        manual = get("/api/fan/chart", self.query(analysis="0"))
        self.assertFalse(manual["analysisEnabled"])
        self.assertEqual(manual["lanes"], {})

    def test_http_static_catalog_chart_and_origin_protection(self):
        server = ThreadingHTTPServer(("127.0.0.1",0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{server.server_port}"
        try:
            for route in ("/faecher", "/fan.js", "/fan-view.js", "/fan.css", "/api/fan/datasets"):
                with urllib.request.urlopen(url+route) as response:
                    self.assertEqual(response.status,200)
            bad = urllib.request.Request(url+"/api/research/jobs", data=json.dumps(self.spec).encode(),
                                         headers={"Content-Type":"application/json", "Origin":"https://foreign.example"})
            with self.assertRaises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(bad)
            self.assertEqual(error.exception.code,403)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_master_case_uses_shared_profile_and_original_safety(self):
        from fan_geometry import create_engine, profile
        value=deepcopy(self.spec)
        value["fan"]["geometry_variants"]=["master"]
        value["fan"]["watch"]["safety_choice"]="main"
        job=submit(value)
        self.assertIn("master-20261029",job["manifest"]["rulesVersion"])
        self.assertEqual(job["manifest"]["engineProfiles"]["master"]["algorithm"],"master")
        run_job(job["id"])
        entry=report(job["id"],entry_filter="entries")["trials"][0]
        query=self.query(fan_job=job["id"],fan_case=entry["id"],engine="fan_master")
        chart=get("/api/fan/chart",query)
        self.assertEqual(chart["analysisEngine"],"fan_master")
        source=[b for b in self.frames["4h"] if b.end<=chart["analysisCutoff"]]
        engine=create_engine("TEST","4h",profile("master",value["fan"]["geometry"]))
        for b in source:engine.push(b)
        self.assertEqual(chart["lanes"]["4h"]["mainSafety"],engine.snapshot()["mainSafety"])
        self.assertEqual(chart["researchSetup"]["initialStop"],entry["signal"]["initialStop"])
        self.assertEqual(chart["lanes"]["4h"]["retest"]["ray"]["id"],entry["signal"]["line"]["id"])
        self.assertIn("checkWindow",chart["lanes"]["4h"])
        self.assertIn("sma200",chart["lanes"]["1D"]["context"])


if __name__ == "__main__":
    unittest.main()
