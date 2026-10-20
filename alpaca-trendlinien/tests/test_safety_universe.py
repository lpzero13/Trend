"""Availability selection uses dates only, never future performance."""
from datetime import datetime
import unittest

from models import NY
from tools.safety_universe import history_start
from strategy_identity import event_key


class UniverseAvailabilityTests(unittest.TestCase):
    def test_common_start_and_late_first_complete_source(self):
        stamp = lambda value: int(datetime.fromisoformat(value).replace(tzinfo=NY).timestamp())
        common = stamp("2025-05-02T09:30:00")
        early = {"material": {"bars": {"4h": [{"time": stamp("2024-04-23T09:30:00")}]}}}
        late = {"material": {"bars": {"4h": [{"time": stamp("2024-07-11T09:30:00")}]}}}
        self.assertEqual(history_start(early, common), common)
        self.assertEqual(history_start(late, common), stamp("2025-07-11T00:00:00"))
        late["material"]["bars"]["4h"][0]["close"] = 999999
        self.assertEqual(history_start(late, common), stamp("2025-07-11T00:00:00"))

    def test_no_complete_source_is_unavailable(self):
        self.assertIsNone(history_start({"material": {"bars": {"4h": []}}}, 1))

    def test_signal_key_survives_dataset_refresh_but_separates_profiles_and_feeds(self):
        material = {"symbol": "TEST", "feed": "iex", "adjustment": "split", "bars": {"4h": []}}
        key = event_key(material, "baseline", "breakout", 1234)
        refreshed = {**material, "bars": {"4h": [{"time": 9999, "close": 500}]}, "downloadedAt": 9999}
        self.assertEqual(key, event_key(refreshed, "baseline", "breakout", 1234))
        for profile, family, at, feed in [("momentum_two", "breakout", 1234, "iex"),
                                         ("baseline", "retest", 1234, "iex"),
                                         ("baseline", "breakout", 1235, "iex"),
                                         ("baseline", "breakout", 1234, "sip")]:
            self.assertNotEqual(key, event_key({**material, "feed": feed}, profile, family, at))
