from copy import deepcopy
from dataclasses import replace
import unittest

from fan_geometry import FanRules
from fan_observer import FanObserver, WatchRules
from models import Bar
from test_fan_geometry import triangle


def append(rows, op, hi, lo, cl):
    start = rows[-1].end
    return [*rows, Bar(start, start+14400, op, hi, lo, cl, 100)]


def run(rows, observer=None):
    o = observer or FanObserver("TEST", "4h", FanRules(atr_length=2, contact_atr=.001, wick_atr=0, min_age_days=0), WatchRules(clean_atr=.01, retest_atr=.01))
    events = []
    for b in rows:
        events += o.push(b)
    return o, events


class FanObserverTests(unittest.TestCase):
    def test_break_and_later_red_line_retest_have_frozen_geometry_and_safety(self):
        base = triangle()
        rows = append(base, 111, 116, 100, 115)
        rows = append(rows, 111, 114, 110.7, 113)
        o, events = run(rows)
        signals = [e for e in events if e["kind"] == "entry_signal"]
        self.assertEqual([e["variant"] for e in signals], ["breakout", "retest"])
        breakout, retest = signals
        self.assertLess(breakout["knownAt"], retest["knownAt"])
        self.assertEqual(breakout["line"], retest["line"])
        self.assertEqual(breakout["initialStop"], retest["initialStop"])
        self.assertTrue(breakout["validRisk"])
        self.assertLess(breakout["candidateAt"], breakout["signalAt"])
        self.assertEqual(breakout["cohort"], "qualified")
        self.assertLess(breakout["line"]["knownAt"], breakout["signalAt"])

    def test_two_contacts_not_upgraded_by_breakout_or_later_pivot(self):
        rows = append(triangle(27), 119, 125, 105, 124)
        o, events = run(rows)
        signals = [e for e in events if e["kind"] == "entry_signal"]
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0]["cohort"], "two")
        self.assertEqual(signals[0]["line"]["contacts"], 2)
        frozen = deepcopy(signals[0])
        for b in append(append(rows, 123, 124, 120, 122), 122, 123, 119, 121)[-2:]:
            o.push(b)
        self.assertEqual(signals[0], frozen)

    def test_weak_close_can_wait_but_same_break_bar_cannot_be_retest(self):
        rows = append(triangle(), 111, 113, 100, 111.1)
        o = FanObserver("TEST", "4h", FanRules(atr_length=2, contact_atr=.001, wick_atr=0, min_age_days=0), WatchRules(clean_atr=.1))
        o, events = run(rows, o)
        self.assertTrue(any(e["kind"] == "break" for e in events))
        self.assertFalse(any(e["kind"] == "entry_signal" for e in events))
        events2 = o.push(append(rows, 111.1, 118, 111, 117)[-1])
        self.assertEqual([e["variant"] for e in events2 if e["kind"] == "entry_signal"], ["breakout"])

    def test_safety_touch_is_not_a_retest_of_broken_red(self):
        rows = append(triangle(), 111, 116, 100, 115)
        rows = append(rows, 97, 100, 90, 99)
        _, events = run(rows)
        self.assertFalse(any(e["kind"] == "entry_signal" and e["variant"] == "retest" for e in events))

    def test_full_scan_and_incremental_scan_have_identical_prefix_events(self):
        rows = append(triangle(), 111, 116, 100, 115)
        rows = append(rows, 111, 114, 110.7, 113)
        _, expected = run(rows)
        o, first = run(rows[:-2])
        first += o.push(rows[-2])
        prefix = deepcopy(first)
        first += o.push(rows[-1])
        self.assertEqual(first, expected)
        self.assertEqual(prefix, [e for e in expected if e["knownAt"] <= rows[-2].end])

    def test_gap_invalidates_pending_geometry_and_keeps_source_coordinates(self):
        o, events = run(triangle())
        index = o.engine.index
        next_bar = append(triangle(), 100, 110, 90, 101)[-1]
        gaps = o.gap(next_bar)
        self.assertTrue(any(e["kind"] == "invalidated" for e in gaps))
        self.assertEqual(o.engine.index, index)
        self.assertEqual(o.active, {})
        self.assertFalse(o.push(next_bar))


if __name__ == "__main__":
    unittest.main()
