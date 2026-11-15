
"""Regression tests for immutable updates, cache recovery and versioned readers."""
from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
from unittest import TestCase
from unittest.mock import patch

import archive_state
from chart_sources import sources_for
from daily_archive import extend, make_plan, update
from daily_review import run
from database import connection
from datasets import digest, path_for, read_dataset, save_dataset
from history_archive import archive_lock
from lab_data import NORMALIZATION, resample_regular, session_bounds
from lab_splits import sessions_between
from maintenance import backup, restore
from models import DataError
from parquet_store import FORMAT, INCREMENTAL_FORMAT, block_path, hydrate, weekly_rows
from settings import data_dir
from test_daily_archive import FakeClient, prices


def save(fine):
    frames, quality = resample_regular(fine)
    return save_dataset("AAPL", {tf: (rows, {
        "normalization": NORMALIZATION, "first": rows[0].time, "last": rows[-1].time,
        "lastClose": rows[-1].end, "rthQuality": quality
    }) for tf, rows in frames.items()}, feed="sip", adjustment="split", session="XNYS regular")


def bars_between(first, last):
    return [bar for index, day in enumerate(sessions_between(first, last))
            for bar in prices(day, 100.1 + index)]


def now(day):
    return datetime.fromisoformat(day + "T23:00:00+00:00")


def manifest(identity):
    return json.loads(path_for(identity).read_text("utf-8"))


def tape(fine, days):
    return {datetime.fromtimestamp(session_bounds(day)[0], timezone.utc):
            [bar for bar in fine if session_bounds(day)[0] <= bar.time < session_bounds(day)[1]]
            for day in days}


class DailyDeltaTest(TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.env = patch.dict(os.environ, {"TORI_DATA_DIR": str(Path(self.directory.name) / "data")})
        self.env.start()
        self.addCleanup(self.env.stop)
        with connection() as db:
            for key in ("dow30", "nasdaq100", "sp500", "russell1000"):
                member = "RUSSONLY" if key.startswith("russell") else "AAPL"
                archive_state.put(db, "universe:v1:" + key, {"asOf": "2026-10-29", "members": [{"symbol": member}]})

    def test_reference_matches_all_rows_and_month_week_boundaries(self):
        all_bars = bars_between("2026-10-27", "2027-01-04")
        missing_day = "2026-11-27"  # XNYS closes early
        opening, _ = session_bounds(missing_day)
        first_new = session_bounds("2026-12-01")[0]
        last_old = session_bounds("2026-11-30")[0]
        omitted = {opening, opening + 300}
        prior = [bar for bar in all_bars if bar.time < first_new and bar.time not in omitted]
        base = save(prior)
        old = manifest(base)
        self.assertEqual(old["storage"]["format"], FORMAT)
        self.assertEqual(digest(read_dataset(base)["material"]), base)

        added = [bar for bar in all_bars if bar.time in omitted or bar.time >= last_old]
        added[2] = replace(added[2], volume=added[2].volume + 7)
        item = {"datasetId": base, "sessions": [missing_day, *sessions_between("2026-11-30", "2027-01-04")],
                "checkedThrough": "2026-11-30", "missingBarsBySession": {missing_day: 2}}
        result = extend("AAPL", item, {bar.time: bar for bar in added})
        current = manifest(result["datasetId"])
        self.assertEqual(current["storage"]["format"], INCREMENTAL_FORMAT)
        self.assertEqual(result["volumeRevisions"], 1)
        self.assertEqual(result["missingBarsBySession"], {})
        self.assertEqual(result["reusedBlocks"], 1)
        expected = {bar.time: bar for bar in all_bars}
        expected.update({bar.time: bar for bar in added})
        frames, _ = resample_regular(expected.values())
        dataset, weeks = hydrate(current, data_dir(), include_weekly=True)
        self.assertEqual(dataset["material"]["bars"], {tf: [asdict(bar) for bar in rows] for tf, rows in frames.items()})
        self.assertEqual(weeks, weekly_rows(dataset["material"]))
        self.assertEqual(sources_for(result["datasetId"])[0]["4h"][0], frames["4h"])
        self.assertEqual(manifest(base), old)
        self.assertEqual(read_dataset(result["datasetId"]), dataset)

        # A new ID still participates in existing dataset references and restore.
        with connection() as db:
            archive_state.put(db, "test-pinned-case", {"datasetId": result["datasetId"]})
        saved = Path(self.directory.name) / "backup"
        restored = Path(self.directory.name) / "restored"
        backup(saved)
        restore(saved, restored)
        with patch.dict(os.environ, {"TORI_DATA_DIR": str(restored)}):
            self.assertEqual(read_dataset(result["datasetId"]), dataset)
            self.assertEqual(digest(read_dataset(base)["material"]), base)

    def test_bound_catchup_then_repair_and_repeat_without_provider(self):
        bars = bars_between("2026-11-04", "2026-11-13")
        through = session_bounds("2026-11-09")[1]
        base = save([bar for bar in bars if bar.end <= through])
        end = now("2026-11-13")
        plan = make_plan(now=end)
        self.assertEqual(set(plan["universes"]), {"dow30", "nasdaq100", "sp500"})
        self.assertEqual(set(plan["symbols"]), {"AAPL"})
        with self.assertRaises(DataError):
            make_plan(["russell1000"], now=end)
        self.assertEqual(plan["symbols"]["AAPL"]["status"], "backlog")
        factory = lambda: self.fail("provider constructed for no work")
        self.assertEqual(update(now=end, client_factory=factory)["alpaca"], {})
        first = FakeClient(tape(bars, ("2026-11-09", "2026-11-10")))
        result = update(now=end, mode="catchup", max_sessions=1, client_factory=lambda: first)
        self.assertEqual(result["symbols"]["AAPL"]["checkedThrough"], "2026-11-10")
        self.assertEqual(result["symbols"]["AAPL"]["backlogSessions"], 3)

        missing_day = "2026-11-11"
        missing_stamp = session_bounds(missing_day)[0]
        partial = [bar for bar in bars if bar.time != missing_stamp]
        data = FakeClient(tape(partial, sessions_between("2026-11-10", "2026-11-13")))
        result = update(now=end, mode="catchup", max_sessions=3, client_factory=lambda: data)
        self.assertEqual(result["symbols"]["AAPL"]["missingBarsBySession"], {missing_day: 1})
        result = update(now=end, client_factory=factory)
        self.assertEqual(result["symbols"]["AAPL"]["status"], "tolerated_gaps")
        self.assertFalse(result["behindTarget"])
        repair = FakeClient(tape(bars, (missing_day, "2026-11-13")))
        result = update(now=end, mode="repair", client_factory=lambda: repair)
        self.assertEqual(result["symbols"]["AAPL"]["missingBarsBySession"], {})
        self.assertEqual(len(repair.calls), 2)
        self.assertEqual(update(now=end, client_factory=factory)["counts"], {"current": 1})
        self.assertNotEqual(result["symbols"]["AAPL"]["datasetId"], base)

    def test_restart_uses_verified_download_and_manifest_before_checkpoint(self):
        bars = bars_between("2026-11-05", "2026-11-10")
        last = session_bounds("2026-11-09")[1]
        seed = save([bar for bar in bars if bar.end <= last])
        data = FakeClient(tape(bars, ("2026-11-09", "2026-11-10")))
        end = now("2026-11-10")
        with patch("daily_delta.write_manifest", side_effect=OSError("interrupted before manifest")):
            interrupted = update(now=end, client_factory=lambda: data)
        self.assertEqual(interrupted["counts"], {"error": 1})
        self.assertEqual(make_plan(now=end)["symbols"]["AAPL"]["datasetId"], seed)
        self.assertEqual(len(data.calls), 2)
        simulated_error = archive_state.put

        def crash_on_checkpoint(db, key, value):
            if key == "daily-archive:v1:AAPL":
                raise RuntimeError("crash after durable manifest")
            simulated_error(db, key, value)

        unreachable = lambda: self.fail("download repeated")
        with patch("daily_archive.archive_state.put", side_effect=crash_on_checkpoint):
            with self.assertRaisesRegex(RuntimeError, "durable manifest"):
                update(now=end, client_factory=unreachable)
        recovered = update(now=end, client_factory=unreachable)
        self.assertEqual(recovered["counts"], {"current": 1})
        identity = recovered["symbols"]["AAPL"]["datasetId"]
        self.assertNotEqual(identity, seed)
        self.assertEqual(len(read_dataset(identity)["material"]["bars"]["5m"]), len(bars))

    def test_checksums_and_splits_fail_before_publishing(self):
        bars = bars_between("2026-10-27", "2026-11-03")
        close = session_bounds("2026-11-02")[1]
        base = save([bar for bar in bars if bar.end <= close])
        early = session_bounds("2026-11-02")[0]
        download = {b.time: b for b in bars if b.time >= early}
        item = {"datasetId": base, "sessions": ["2026-11-02", "2026-11-03"],
                "overlapSession": "2026-11-02", "checkedThrough": "2026-11-02", "missingBarsBySession": {}}
        revision = {**download, early: replace(download[early], close=34)}
        with self.assertRaisesRegex(DataError, "Split"):
            extend("AAPL", item, revision)
        path = block_path(data_dir(), manifest(base)["storage"]["blocks"][0]["path"])
        intact = path.read_bytes()
        path.write_bytes(intact[:-1] + bytes([intact[-1] ^ 1]))
        with self.assertRaisesRegex(ValueError, "checksum"):
            extend("AAPL", item, download)
        path.unlink()
        with self.assertRaises(FileNotFoundError):
            extend("AAPL", item, download)
        self.assertEqual(len(list((data_dir() / "datasets").glob("*.json"))), 1)

    def test_shared_archive_lock_and_graceful_stop(self):
        with archive_lock():
            with self.assertRaises(DataError):
                update(now=now("2026-11-10"))
        bars = bars_between("2026-11-05", "2026-11-10")
        last = session_bounds("2026-11-09")[1]
        save([bar for bar in bars if bar.end <= last])
        data = FakeClient(tape(bars, ("2026-11-09", "2026-11-10")))
        stop = Event()

        start_request = data.request

        def terminate_after_page(params):
            response = start_request(params)
            stop.set()
            return response

        with patch.object(data, "request", side_effect=terminate_after_page):
            stopped = update(now=now("2026-11-10"), client_factory=lambda: data, stop=stop)
        self.assertTrue(stopped["interrupted"])
        self.assertEqual(stopped["counts"], {"pending": 1})
        remaining = FakeClient(data.rows)
        update(now=now("2026-11-10"), client_factory=lambda: remaining)
        self.assertEqual(len(data.calls), 1)
        self.assertEqual(len(remaining.calls), 1)

    def test_review_cache_invalidates_on_changed_data(self):
        bars = bars_between("2025-10-27", "2026-11-10")
        identity = save(bars)
        stamp = now("2026-11-10")
        with patch("daily_review.make_plan", side_effect=lambda keys: make_plan(keys, stamp)):
            first = run(scan_only=True)
            warm = run(scan_only=True)
            self.assertFalse(first["cachedAnalysis"])
            self.assertTrue(warm["cachedAnalysis"])
            self.assertEqual(first["candidates"], warm["candidates"])
            path = block_path(data_dir(), manifest(identity)["storage"]["blocks"][0]["path"])
            path.write_bytes(b"damaged")
            result = run(scan_only=True)
            self.assertFalse(result["cachedAnalysis"])
            self.assertEqual(result["coverage"], {"analysis_unavailable": 1})
