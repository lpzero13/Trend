"""Coverage and provenance checks for the close-of-session watchlist."""

from datetime import datetime, timezone
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
import os

from daily_review import build_report, latest, review_pair, run
from lab_data import session_bounds
from models import Bar


def sample_lane(red=101):
    return {"close": 100, "atr": 2, "red": {
        "value": red, "slope": -1, "valid": True, "contacts": 3, "qualified": True, "id": "a",
    }, "green": {"value": 98, "slope": 1, "valid": True, "contacts": 2, "qualified": False}}


class DailyReviewTest(TestCase):
    def test_candidate_requires_two_valid_lines_and_proximity(self):
        self.assertIsNone(review_pair(sample_lane(100)))
        self.assertIsNone(review_pair(sample_lane(102.01)))
        self.assertEqual(review_pair(sample_lane(102))["distanceAtr"], 1)
        lane = sample_lane()
        lane["green"]["contacts"] = 1
        self.assertIsNone(review_pair(lane))

    def test_scan_uses_target_session_and_marks_partial_context(self):
        day = "2026-11-13"
        opened, closed = session_bounds(day)
        previous_open, previous_close = session_bounds("2026-11-12")
        four_hours = Bar(opened, opened + 14400, 100, 101, 99, 100, 10)
        previous = Bar(previous_open, previous_close, 100, 101, 99, 100, 10)
        snapshot = {"targetSession": day, "universes": {"nasdaq100": {"symbols": []}}, "symbols": {
            "PARTIAL": {"datasetId": "a" * 64, "status": "tolerated_gaps", "missingBarsBySession": {day: 3}},
            "GAPS": {"datasetId": "b" * 64, "status": "gaps", "missingBarsBySession": {day: 10}},
            "STALE": {"datasetId": "c" * 64, "status": "pending"},
            "UNSAVED": {"status": "no_local_history"},
        }}

        def frames(_db, dataset, cutoff, _month):
            self.assertEqual(cutoff, closed)
            self.assertNotEqual(dataset, "b" * 64)
            return {"4h": [four_hours] if dataset.startswith("a") else [],
                    "1D": [previous]}

        earlier = {"session": "2026-11-12", "candidates": [
            {"symbol": "PARTIAL", "redLineId": "a", "distanceAtr": 0.8}]}
        with patch("daily_review.read_frames", side_effect=frames), patch(
                "daily_review.analyze", return_value=sample_lane()):
            report = build_report(snapshot, earlier)
        self.assertEqual(report["coverage"], {"candidate": 1, "data_problem": 1,
                                             "missing_session_4h": 1, "no_local_history": 1})
        only, = report["candidates"]
        self.assertEqual(only["change"], "closer")
        self.assertFalse(only["completeDailyClose"])
        self.assertFalse(only["complete4hClose"])
        query = parse_qs(urlsplit(only["chartPath"]).query)
        self.assertEqual(query["dataset"], ["a" * 64])
        self.assertEqual(query["analysis"], ["1"])
        self.assertEqual(query["asof"], [datetime.fromtimestamp(closed, timezone.utc).isoformat()])

    def test_offline_report_is_persisted_and_same_day_is_not_previous(self):
        snapshot = {"targetSession": "2026-11-13", "symbols": {}, "universes": {"nasdaq100": {}}}
        with TemporaryDirectory() as directory, patch.dict(os.environ, {"TORI_DATA_DIR": directory}), patch(
                "daily_review.make_plan", return_value=snapshot), patch("daily_review.update") as updater:
            self.assertIsNone(latest())
            run(scan_only=True)
            report = run(scan_only=True, base_url="https://tori.example.org")
            updater.assert_not_called()
            self.assertIsNone(report["previousSession"])
            self.assertTrue(report["cachedAnalysis"])
            self.assertEqual(report["url"], "https://tori.example.org/pruefung#abend-watchlist")
            self.assertEqual(latest()["session"], snapshot["targetSession"])
            self.assertNotIn("url", latest())

    def test_combined_command_scans_result_of_update(self):
        snapshot = {"targetSession": "2026-11-13", "symbols": {}, "universes": {"nasdaq100": {}}}
        with TemporaryDirectory() as directory, patch.dict(os.environ, {"TORI_DATA_DIR": directory}), patch(
                "daily_review.update", return_value=snapshot) as updater:
            report = run(["nasdaq100"], workers=2, max_minutes=25)
            updater.assert_called_once_with(["nasdaq100"], workers=2, max_minutes=25, stop=None, progress=None, budget=90)
            self.assertEqual(report["session"], "2026-11-13")
            self.assertEqual(report, latest())
