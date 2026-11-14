"""Synthetic 1m examples, no provider credentials."""
from datetime import datetime
from decimal import Decimal
import os
import tempfile
import unittest
from unittest.mock import patch

from models import DataError
from paper_engine import Minute, aggregate, bucket, candle_distance, day_at, entry, market_minute, normalize_plan
from paper_store import advance, command, connection, create_account, draft, events, preview, status, store_minutes


def utc(value):
    return int(datetime.fromisoformat(value).timestamp())


FRIDAY = utc("2024-03-08T14:30:00+00:00")
MONDAY = utc("2024-03-11T13:30:00+00:00")
TUESDAY = MONDAY + 86400


def minutes(at, count, price, *, low=None, high=None):
    return [Minute.parse(at + i * 60, [price, high or price, low or price, price, 1]) for i in range(count)]


def plan(at=MONDAY, **kwargs):
    return {"symbol": "AAPL", "timeframe": "4h",
            "action": [{"at": FRIDAY, "price": "105"}, {"at": FRIDAY+14400, "price": "105"}],
            "safety": [{"at": FRIDAY, "price": "96"}, {"at": FRIDAY+14400, "price": "96"}],
            "expires_at": at + 86400 * 10, **kwargs}


class PaperTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        env = patch.dict(os.environ, {"TORI_DATA_DIR": self.temp.name})
        env.start()
        self.addCleanup(env.stop)
        self.account = create_account({"fee": "1", "slippage_bps": 5}, FRIDAY)

    def start(self, *, at=MONDAY, key="test-0001", **kwargs):
        item = draft({"request_id": key, "setup": plan(at, **kwargs)}, at-60)
        with connection() as db:
            details = preview(db, item, at)
        request = {"request_id": f"{key}-activate", "expected_updated": item["updated"],
                   "confirmation": details["confirmation"]}
        result = command(item["id"], "activate", request, at)
        self.assertEqual(command(item["id"], "activate", request, at+20), result)
        return result

    def load(self, *bars, ticker="AAPL", now=TUESDAY):
        with connection(write=True) as db:
            store_minutes(db, ticker, bars, now)

    def step(self, cutoff, *, now=TUESDAY, limit=390):
        with connection(write=True) as db:
            return advance(db, cutoff, now, limit)

    def stage_entry(self, **kwargs):
        self.start(**kwargs)
        self.load(*minutes(FRIDAY+14400, 150, 104), *minutes(MONDAY, 240, 106))
        self.step(MONDAY+14400)
        self.assertEqual(status()["plans"][0]["state"], "pending")
        self.assertEqual(status()["cash"], "10000")

    def test_dst_early_close_and_gap_preserving_geometry(self):
        self.assertEqual(candle_distance(FRIDAY, MONDAY, "4h"), 2)
        self.assertEqual(market_minute(FRIDAY+23400), MONDAY)
        early = utc("2024-11-29T14:30:00+00:00")
        self.assertEqual(bucket(early+2160, "4h"), (early, early+12600))
        rows = minutes(early, 210, 100)
        self.assertEqual(aggregate(rows, early, early+12600).volume, 210)
        self.assertIsNone(aggregate(rows[:-1], early, early+12600))
        self.assertIsNone(bucket(utc("2024-11-28T15:00:00+00:00"), "4h"))

    def test_next_open_and_gap_stop_book_once(self):
        self.stage_entry()
        at = MONDAY+14400
        self.load(*minutes(at, 1, 107), *minutes(at+60, 1, 90))
        self.step(at+120)
        first = status()
        trade = first["plans"][0]["data"]["exit"]
        self.assertEqual(trade["reason"], "hard_stop_gap")
        self.assertEqual(trade["base"], "90")
        self.assertEqual(Decimal(first["equity"]), Decimal("10000")+Decimal(first["realized_pnl"]))
        self.step(at+120)
        self.assertEqual(first["cash"], status()["cash"])
        self.assertEqual([e["kind"] for e in events()["items"]].count("exit"), 1)

    def test_missing_open_waits_for_backfill(self):
        self.stage_entry()
        at = MONDAY+14400
        self.load(*minutes(at+60, 1, 107))
        self.step(at+120)
        self.assertEqual(status()["plans"][0]["state"], "pending")
        self.assertEqual(status()["issues"][0]["kind"], "missing_or_no_trade")
        self.load(*minutes(at, 1, 106))
        self.step(at+120)
        self.assertEqual(status()["plans"][0]["state"], "open")
        self.assertFalse(status()["issues"])

    def test_ambiguous_target_stop_records_no_winner(self):
        self.stage_entry(target_price="112")
        at = MONDAY+14400
        self.load(*minutes(at, 1, 106, low=89, high=114))
        self.step(at+60)
        result = status()
        self.assertEqual(result["plans"][0]["state"], "ambiguous")
        self.assertEqual(result["realized_pnl"], "0")
        self.assertFalse(result["valuation_complete"])

    def test_revised_processed_bar_preserves_original(self):
        self.stage_entry()
        at = MONDAY+14400
        self.load(*minutes(at, 1, 106))
        self.step(at+60)
        original = status()["plans"][0]["data"]["position"]["fill"]
        self.load(*minutes(at, 1, 88), *minutes(at+60, 1, 85))
        self.step(at+120)
        self.assertEqual(status()["cursor"], at+60)
        self.assertEqual(status()["plans"][0]["data"]["position"]["fill"], original)
        self.assertEqual(status()["issues"][0]["kind"], "revision")

    def test_never_replay_signal_prior_to_activation(self):
        self.start(at=MONDAY+14400+2)
        self.load(*minutes(FRIDAY+14400, 150, 104), *minutes(MONDAY, 390, 106))
        self.step(MONDAY+23400)
        self.assertEqual(status()["plans"][0]["state"], "watching")
        self.assertFalse(any(e["kind"] == "signal" for e in events()["items"]))

    def test_sizing_respects_total_cost_and_risk(self):
        normalized = normalize_plan(plan(), MONDAY)
        pos, reason = entry(normalized, minutes(MONDAY, 1, 106)[0], self.account, Decimal(10000), Decimal(10000))
        self.assertIsNone(reason)
        self.assertLessEqual(Decimal(pos["initial_risk"]), Decimal(100))
        self.assertEqual(Decimal(pos["stop"]), Decimal("95.52"))

    def test_crash_before_commit_discards_cursor_and_fill(self):
        self.stage_entry()
        at = MONDAY+14400
        self.load(*minutes(at, 1, 106))
        with self.assertRaises(RuntimeError):
            with connection(write=True) as db:
                advance(db, at+60, TUESDAY)
                raise RuntimeError("simulated process abort")
        self.assertEqual(status()["cursor"], at)
        self.assertEqual(status()["plans"][0]["state"], "pending")
        self.step(at+60)
        self.assertEqual(status()["plans"][0]["state"], "open")
        self.assertEqual([e["kind"] for e in events()["items"]].count("entry"), 1)

    def test_event_watermark_excludes_later_appends(self):
        first = events(limit=1)
        self.start()
        still = events(after=first["next"], through=first["through"])
        self.assertEqual(still["items"], [])
        self.assertGreater(events()["through"], first["through"])

    def test_rejects_bad_confirmation(self):
        item = draft({"request_id": "test-0020", "setup": plan()}, MONDAY)
        with self.assertRaises(DataError):
            command(item["id"], "activate", {"request_id": "cmd-0020", "expected_updated": item["updated"]}, MONDAY)
        self.assertEqual(status()["plans"][0]["state"], "draft")

    def test_safety_close_has_priority_over_time_and_manual_exit(self):
        self.stage_entry(hard_stop=False, time_exit_sessions=1, horizons=[1])
        at = MONDAY+14400
        self.load(*minutes(at, 149, 106), *minutes(at+149*60, 1, 94), *minutes(TUESDAY, 1, 93))
        self.step(MONDAY+23400)
        watched = status()["plans"][0]
        self.assertIn("1", watched["data"]["horizon_marks"])
        command(watched["id"], "exit", {"request_id": "manual-0001", "expected_updated": watched["updated"]},
                MONDAY+23460)
        self.step(TUESDAY+60)
        self.assertEqual(status()["plans"][0]["data"]["exit"]["reason"], "safety_close_exit")

    def test_manual_exit_uses_real_request_time(self):
        self.stage_entry()
        at = MONDAY+14400
        self.load(*minutes(at, 1, 107))
        self.step(at+60)
        watched = status()["plans"][0]
        command(watched["id"], "exit", {"request_id": "manual-0002", "expected_updated": watched["updated"]}, at+135)
        self.load(*minutes(at+60, 3, 108))
        self.step(at+240)
        self.assertEqual(status()["plans"][0]["data"]["exit"]["at"], at+180)

    def test_ambiguous_manual_resolution_is_journaled_once(self):
        self.stage_entry(target_price="112")
        at = MONDAY+14400
        self.load(*minutes(at, 1, 106, low=89, high=114))
        self.step(at+60)
        watched = status()["plans"][0]
        request = {"request_id": "resolve-0001", "expected_updated": watched["updated"]}
        command(watched["id"], "resolve_stop", request, TUESDAY)
        command(watched["id"], "resolve_stop", request, TUESDAY+60)
        self.assertEqual(status()["plans"][0]["data"]["exit"]["reason"], "manual_resolution_stop")
        self.assertEqual([e["kind"] for e in events()["items"]].count("exit"), 1)
