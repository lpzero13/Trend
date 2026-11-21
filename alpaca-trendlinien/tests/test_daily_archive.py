"""Offline regression coverage for resuming updates and preserving datasets."""

import os
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

import archive_state
from daily_archive import available_session, extend, make_plan, update
from database import connection
from datasets import read_dataset, save_dataset
from lab_data import NORMALIZATION, resample_regular, session_bounds
from models import Bar


def utc(value):
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def prices(day, price=100):
    start, end = session_bounds(day)
    return [Bar(stamp, stamp + 300, price, price, price, price, 10)
            for stamp in range(start, end, 300)]


def seed_archive():
    dates = ("2026-11-06", "2026-11-09", "2026-11-10")
    fine = [bar for day in dates for bar in prices(day)]
    sources, _ = resample_regular(fine)
    return save_dataset("AAPL", {tf: (rows, {
        "normalization": NORMALIZATION, "first": rows[0].time, "lastClose": rows[-1].end}
    ) for tf, rows in sources.items()}, feed="sip", adjustment="split", session="XNYS regular")


class FakeClient:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def request(self, params):
        opened = utc(params["start"])
        closed = utc(params["end"])
        self.calls.append((opened, closed, params["symbols"]))
        rows = [dict(t=datetime.fromtimestamp(b.time, timezone.utc).isoformat(),
                     o=b.open, h=b.high, l=b.low, c=b.close, v=b.volume)
                for b in self.rows.get(opened, [])]
        return {"bars": {s: rows for s in params["symbols"].split(",")}, "next_page_token": None}

    def close(self):
        pass

    def snapshot(self):
        return {"attempts": len(self.calls)}


class DailyArchiveTest(TestCase):
    def test_close_delay_around_dst_and_early_close(self):
        self.assertEqual(available_session(utc("2026-10-29T20:15:59+00:00")), "2026-10-28")
        self.assertEqual(available_session(utc("2026-10-29T20:16:00+00:00")), "2026-10-29")
        self.assertEqual(available_session(utc("2026-11-02T21:16:00+00:00")), "2026-11-02")
        self.assertEqual(available_session(utc("2026-11-27T18:16:00+00:00")), "2026-11-27")
        self.assertEqual(available_session(utc("2026-11-29T22:00:00+00:00")), "2026-11-27")

    def test_catchup_deduplicates_universes_and_retries_missing_session(self):
        with TemporaryDirectory() as folder, patch.dict(os.environ, {"TORI_DATA_DIR": folder}):
            dataset = seed_archive()
            with connection() as db:
                for key in ("sp500", "nasdaq100"):
                    archive_state.put(db, "universe:v1:" + key, {"asOf": "2026-11-10", "members": [
                        {"symbol": "AAPL"}, {"symbol": "UNSAVED"}]})
            now = utc("2026-11-12T22:00:00+00:00")
            tape = {datetime.fromtimestamp(session_bounds(day)[0], timezone.utc): prices(day)
                    for day in ("2026-11-10", "2026-11-12")}
            client = FakeClient(tape)
            result = update(["sp500", "nasdaq100"], now=now, client_factory=lambda: client)
            self.assertEqual(result["counts"], {"gaps": 1, "no_local_history": 1})
            self.assertEqual(len(client.calls), 3)
            self.assertTrue(all(symbol == "AAPL" for _, _, symbol in client.calls))
            self.assertEqual(result["symbols"]["AAPL"]["missingSessions"], ["2026-11-11"])
            self.assertEqual(result["symbols"]["AAPL"]["lastSession"], "2026-11-12")
            self.assertEqual(len(read_dataset(dataset)["material"]["bars"]["1D"]), 3)
            tape[datetime.fromtimestamp(session_bounds("2026-11-11")[0], timezone.utc)] = prices("2026-11-11")
            result = update(["sp500"], now=now, client_factory=lambda: FakeClient(tape))
            self.assertEqual(result["counts"], {"updated": 1, "no_local_history": 1})
            latest = result["symbols"]["AAPL"]["datasetId"]
            self.assertEqual(len(read_dataset(latest)["material"]["bars"]["1D"]), 5)
            self.assertEqual(make_plan(["sp500"], now)["symbols"]["AAPL"]["status"], "current")
            self.assertTrue(Path(folder, "datasets", dataset + ".json").is_file())

    def test_gap_threshold_is_per_session_and_incomplete_daily_bar_stays_absent(self):
        first, second, third = "2026-11-10", "2026-11-11", "2026-11-12"
        for missing, status, quality in ((1, "tolerated_gaps", "tolerated"),
                                         (9, "tolerated_gaps", "tolerated"),
                                         (10, "gaps", "problem")):
            with self.subTest(missing=missing), TemporaryDirectory() as folder, patch.dict(
                    os.environ, {"TORI_DATA_DIR": folder}):
                item = {"datasetId": seed_archive(), "lastSession": first, "checkedThrough": first,
                        "sessions": [first, second, third], "missingBarsBySession": {}}
                bars = prices(first) + prices(second)[missing:] + prices(third)[2:]
                updated = extend("AAPL", item, {bar.time: bar for bar in bars})
                self.assertEqual(updated["status"], status)
                self.assertEqual(updated["gapStatus"], quality)
                self.assertEqual(updated["missingBarsBySession"], {second: missing, third: 2})
                self.assertEqual(updated["lastSession"], first)
                self.assertEqual(len(read_dataset(updated["datasetId"])["material"]["bars"]["1D"]), 3)
                with connection() as db:
                    archive_state.put(db, "universe:v1:sp500", {"asOf": first, "members": [{"symbol": "AAPL"}]})
                    archive_state.put(db, "daily-archive:v1:AAPL", updated)
                planned = make_plan(["sp500"], utc("2026-11-12T22:00:00+00:00"))["symbols"]["AAPL"]
                self.assertEqual(planned["status"], "pending")
                self.assertEqual(planned["gapStatus"], quality)
                self.assertEqual(planned["missingBarsBySession"], {second: missing, third: 2})
