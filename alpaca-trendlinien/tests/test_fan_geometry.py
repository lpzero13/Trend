"""Independent geometric and prefix counterexamples; synthetic, not returns."""
from copy import deepcopy
from dataclasses import replace
import math
import random
import unittest

from fan_geometry import FanEngine, FanRules, analyze, violates
from models import Bar, DataError


def triangle(count=90):
    result = []
    for i in range(count):
        high = 120-.1*i-2*abs(math.sin(math.pi*i/10))
        low = 80+.1*i+2*abs(math.sin(math.pi*i/12))
        mid = (high+low)/2
        result.append(Bar(1700000000+i*14400, 1700000000+(i+1)*14400, mid, high, low, mid, 100))
    return result


def engine(rows, rules=None):
    e = FanEngine("TEST", "4h", rules or FanRules(atr_length=2, contact_atr=.001, wick_atr=0, min_age_days=0))
    for bar in rows:
        e.push(bar)
    return e


class FanGeometryTests(unittest.TestCase):
    def test_three_or_more_contacts_are_not_limited_to_two_anchors(self):
        state = engine(triangle()).snapshot()
        self.assertTrue(state["red"]["qualified"])
        self.assertGreaterEqual(state["red"]["contacts"], 3)
        self.assertGreaterEqual(state["green"]["contacts"], 3)
        self.assertAlmostEqual(state["red"]["slope"], -.1)
        self.assertAlmostEqual(state["green"]["slope"], .1)
        self.assertTrue(all(p["known_index"] <= state["referenceIndex"] for p in state["red"]["contactPoints"]))

    def test_pivot_is_unavailable_until_right_confirmation_and_equal_extreme_is_recent(self):
        rules = FanRules(atr_length=2, pivot_side=2)
        rows = [Bar(i*100, (i+1)*100, 5, h, 2, 5, 1) for i, h in enumerate([6, 7, 9, 9, 7, 6])]
        e = engine(rows[:5], rules)
        self.assertEqual(len(e.pivots[True]), 0)
        e.push(rows[5])
        self.assertEqual(e.pivots[True][0].index, 3)
        self.assertEqual(e.pivots[True][0].known_index, 5)

    def test_wilder_atr_seed_and_recurrence(self):
        e = FanEngine("T", "1h", FanRules(atr_length=3))
        for i, (lo, hi, close) in enumerate([(9, 11, 10), (8, 12, 11), (10, 13, 12), (11, 17, 13)]):
            e.push(Bar(i*100, (i+1)*100, close, hi, lo, close, 1))
            if i == 2:
                self.assertEqual(e.atr, 3)
        self.assertEqual(e.atr, 4)

    def test_cache_matches_full_rebuild_at_every_prefix(self):
        rows = triangle()
        cached, reference = engine([]), engine([])
        for i, b in enumerate(rows):
            cached.push(b)
            reference.push(b)
            reference.cache.clear()
            for pine in (False, True):
                self.assertEqual(cached.snapshot(pine=pine), reference.snapshot(pine=pine), (i, pine))
        self.assertLess(cached.rebuilds, reference.rebuilds)

    def test_old_snapshot_and_prefix_are_not_changed_by_future_shocks(self):
        rows = triangle()
        e = engine(rows[:65])
        saved = deepcopy(e.snapshot())
        for b in rows[65:]:
            e.push(replace(b, open=200, close=200, high=300, low=150))
        self.assertEqual(saved, engine(rows[:65]).snapshot())
        self.assertNotEqual(e.snapshot(), saved)

    def test_pine_window_never_counts_contact_confirmed_inside_break_window(self):
        e = engine(triangle(33))
        state = e.snapshot(pine=True)
        for line in state["reds"]:
            self.assertTrue(all(p["known_index"] <= 30 for p in line["contactPoints"]))
        self.assertEqual(state["sourceClose"], triangle(33)[-1].end)
        self.assertEqual(state["mode"], "pine_snapshot")

    def test_chart_lane_uses_source_indices_and_same_geometry(self):
        rows = triangle()
        e = engine(rows)
        lane = analyze(rows, "4h", rules=e.rules, symbol="TEST")
        self.assertEqual(lane["red"], e.snapshot()["red"])
        self.assertEqual(lane["sourceTimes"], [b.time for b in rows])
        self.assertEqual(lane["red"]["basis"], "bars")
        self.assertIsNone(lane["event"])

    def test_envelope_against_independent_slow_candle_oracle(self):
        rng = random.Random(29)
        for _ in range(15):
            rows = [replace(b, high=b.high+rng.uniform(-.2, .2), low=b.low+rng.uniform(-.2, .2)) for b in triangle(80)]
            e = engine(rows, FanRules(atr_length=2, wick_atr=.02, contact_atr=.1))
            state = e.snapshot()
            for upper, pool in ((True, state["reds"]), (False, state["greens"])):
                for line in pool:
                    for i, bar, vol in e.rows:
                        if i <= line["a_index"]:
                            continue
                        price = line["a_price"]+line["slope"]*(i-line["a_index"])
                        if upper:
                            self.assertLessEqual(max(bar.open, bar.close), price+1e-8)
                            self.assertLessEqual(bar.high, price+vol*e.rules.wick_atr+1e-8)
                        else:
                            self.assertGreaterEqual(min(bar.open, bar.close), price-1e-8)
                            self.assertGreaterEqual(bar.low, price-vol*e.rules.wick_atr-1e-8)
                # First fan line must be the shallowest valid pivot-pair slope
                # starting at the extreme. Oracle validates every candle directly.
                pivots = list(e.pivots[upper])
                a = (max if upper else min)(pivots, key=lambda p:p.price)
                valid = []
                for b in pivots:
                    if b.index-a.index < e.rules.contact_gap:
                        continue
                    slope = (b.price-a.price)/(b.index-a.index)
                    if not (slope < 0 if upper else slope > 0):
                        continue
                    okay = True
                    for i, bar, vol in e.rows:
                        if i <= a.index:
                            continue
                        price = a.price+slope*(i-a.index)
                        if (max(bar.open, bar.close) > price+1e-9 or bar.high > price+e.rules.wick_atr*vol+1e-9) if upper else (min(bar.open, bar.close) < price-1e-9 or bar.low < price-e.rules.wick_atr*vol-1e-9):
                            okay = False
                    if okay:
                        valid.append(slope)
                if pool:
                    self.assertAlmostEqual(pool[0]["slope"], (max if upper else min)(valid))

    def test_limits_and_invalid_ohlc_and_configuration(self):
        e = engine(triangle(), FanRules(atr_length=2, max_bars=50, max_pivots=3))
        self.assertEqual(len(e.rows), 50)
        self.assertTrue(all(len(p) <= 3 for p in e.pivots.values()))
        self.assertTrue(e.snapshot()["capped"])
        with self.assertRaises(DataError):
            e.push(triangle()[0])
        with self.assertRaises(DataError):
            engine([Bar(0, 10, 3, 2, 1, 2, 1)])
        for kwargs in ({"contact_atr": float("nan")}, {"roots": "future"}, {"pivot_side": True}):
            with self.assertRaises(DataError):
                FanRules(**kwargs)


if __name__ == "__main__":
    unittest.main()
