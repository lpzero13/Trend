"""Explicit synthetic counterexamples; never empirical market evidence."""
from copy import deepcopy
from dataclasses import asdict, replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from models import Bar
from datasets import digest
from entry_geometry import confirmed_pivots, episodes, violation, RULES, at, Geometry
from entry_watch import WatchReplay, execution_time
from entry_study import net_return
from entry_blind import blind_case, compare_reviews
from tools.entry_watch_scan import scan
from lab_data import NORMALIZATION, resample_regular
import test_safety_strategy as safety_fixtures


def dataset():
    f = safety_fixtures.SafetyStrategyTests()
    f.setUp()
    fine = list(f.fine)
    # Known rising support, falling resistance, then a real positive close.
    fine[0] = replace(fine[0], high=110, low=95)
    fine[5*78] = replace(fine[5*78], high=109, low=96)
    end = f.four[20].end
    j = next(j for j, b in enumerate(fine) if b.end == end)
    fine[j] = replace(fine[j], high=110, low=99, close=109)
    fine[j+1] = replace(fine[j+1], open=109, high=110, low=108, close=109)
    fine[j+2] = replace(fine[j+2], open=109, high=110, low=108, close=109)
    sources, _ = resample_regular(fine)
    material = {"symbol": "TEST", "provider": "synthetic", "dataKind": "synthetic", "feed": "iex", "adjustment": "split",
                "normalization": {tf: NORMALIZATION for tf in sources},
                "bars": {tf: [asdict(b) for b in rows] for tf, rows in sources.items()}}
    return {"id": digest(material), "material": material}, sources


def candidate(bars, upper, i=19):
    a, b = (110, 109) if upper else (95, 96)
    ray = {"a_index": 0, "b_index": 10, "a_time": bars[0].time, "b_time": bars[10].time,
           "a_price": a, "b_price": b, "slope": (b-a)/10, "basis": "bars", "valid": True}
    return {"id": "red" if upper else "green", "model": "swing_envelope", "symbol": "TEST", "upper": upper,
            "ray": ray, "width": .2, "atrAtCreation": 2., "createdIndex": i, "knownAt": bars[i].end,
            "windowDays": 30, "active": True, "state": "structure", "alternatives": 0, "notified": [],
            "breakIndex": None, "armGreen": None, "armGreenCandidate": None,
            "lastFeatures": {"contacts": 2, "reactionEpisodes": 2, "contactSpanDays": 8,
                             "projectionSensitivityATR": .1, "meanContactErrorATR": 0.}}


class GeometryTests(unittest.TestCase):
    def test_geometry_can_find_three_separate_reactions_with_frozen_band(self):
        highs = [110, 105, 104, 109, 104, 103, 108, 103, 102, 107, 102, 101, 101, 100, 100, 100, 100]
        rows = [Bar(1700000000+i*14400, 1700000000+(i+1)*14400, h-2, h, h-5, h-3, 1) for i, h in enumerate(highs)]
        geometry = Geometry(rows, "TEST", "swing_envelope")
        candidates = geometry.proposals(14)
        red = next(c for c in candidates if c["upper"] and c["ray"]["a_index"] == 3 and c["ray"]["b_index"] == 6)
        self.assertGreaterEqual(red["lastFeatures"]["reactionEpisodes"], 3)
        width = red["width"]
        geometry.proposals(16)
        self.assertEqual(red["width"], width)

    def test_pivot_is_unknown_until_second_closed_right_neighbour(self):
        rows = [Bar(i*10, i*10+10, 90, h, 80, 90, 1) for i, h in enumerate([100, 102, 110, 103, 102, 104, 108])]
        self.assertNotIn(2, confirmed_pivots(rows, 3, True))
        self.assertIn(2, confirmed_pivots(rows, 4, True))
        shocked = rows[:4]+[replace(rows[4], high=200)]+rows[5:]
        self.assertEqual(confirmed_pivots(rows, 3, True), confirmed_pivots(shocked, 3, True))

    def test_multiple_adjacent_touches_are_one_reaction_until_later_departure(self):
        ray = {"a_index": 0, "a_price": 100, "slope": 0}
        high_close = [(100, 99.8), (100, 99.8), (100, 99.8), (98, 97), (98, 97), (100, 99.8)]
        rows = [Bar(i*10, i*10+10, c, h, c-1, c, 1) for i, (h, c) in enumerate(high_close)]
        self.assertEqual(len(episodes(ray, rows, 2, True, .2, 2)), 1)
        self.assertEqual(len(episodes(ray, rows, 5, True, .2, 2)), 2)
        # Low wick on the contact candle itself cannot establish sequencing.
        rows[0] = replace(rows[0], low=50)
        self.assertEqual(len(episodes(ray, rows, 2, True, .2, 2)), 1)

    def test_experimental_wick_zone_never_silently_changes_strict_rule(self):
        ray = {"a_index": 0, "a_price": 100, "slope": 0}
        wick = Bar(0, 1, 99, 100.05, 98, 99.5, 1)
        self.assertTrue(violation(ray, wick, 0, True, .1, False))
        self.assertFalse(violation(ray, wick, 0, True, .1, True))
        self.assertTrue(violation(ray, replace(wick, high=100.2), 0, True, .1, True))
        self.assertTrue(violation(ray, replace(wick, close=100.02), 0, True, .1, True))


class WatchTests(unittest.TestCase):
    def setUp(self):
        self.data, self.sources = dataset()
        self.start = self.sources["4h"][20].end
        self.cutoff = self.sources["4h"][23].end

    def engine(self, data=None, cutoff=None):
        engine = WatchReplay(data or self.data, "swing_envelope", self.start, cutoff or self.cutoff)
        engine.candidates = [candidate(engine.bars, False), candidate(engine.bars, True)]
        engine.candidates[1]["armGreen"] = deepcopy(engine.candidates[0]["ray"])
        return engine

    def test_real_price_break_is_recorded_on_original_anchors_and_later_open(self):
        with patch("entry_watch.Geometry.proposals", return_value=[]):
            engine = self.engine()
            original = deepcopy(engine.candidates[1]["ray"])
            result = engine.run()
        entries = [e for e in result["entries"] if e["family"] == "breakout"]
        self.assertEqual(len(entries), 1)
        e = entries[0]
        self.assertEqual(e["entryAt"], self.sources["4h"][20].end+300)
        self.assertEqual(e["entryPrice"], 109)
        self.assertEqual({k: e["red"][k] for k in original}, original)
        self.assertLess(e["initialStop"], e["rawSafety"])
        self.assertEqual(len([m for m in result["messages"] if m["state"] == "breakout"]), 1)

    def test_missing_expected_open_is_not_skipped_to_a_later_available_price(self):
        target = execution_time(self.sources["4h"][20].end)
        with patch("entry_watch.Geometry.proposals", return_value=[]):
            engine = self.engine()
            del engine.fine[target]
            result = engine.run()
        self.assertFalse(any(e["family"] == "breakout" for e in result["entries"]))
        self.assertIn("missing_expected_execution", [e["status"] for e in result["executions"]])

    def test_future_prices_do_not_change_past_signals_or_notifications(self):
        changed = deepcopy(self.data)
        for rows in changed["material"]["bars"].values():
            for b in rows:
                if b["end"] > self.cutoff:
                    b.update(open=1000, high=2000, low=1, close=1800)
        with patch("entry_watch.Geometry.proposals", return_value=[]):
            a, b = self.engine().run(), self.engine(changed).run()
        self.assertEqual(a, b)

    def test_round_trip_resume_and_revised_prefix_rejection(self):
        with patch("entry_watch.Geometry.proposals", return_value=[]):
            original = self.engine()
            original.step(20)
            saved = json.loads(json.dumps(original.state()))
            restored = self.engine()
            restored.restore(saved)
            self.assertEqual(original.run(), restored.run())
            revised = deepcopy(self.data)
            revised["material"]["bars"]["5m"][0]["volume"] += 1
            with self.assertRaises(ValueError):
                self.engine(revised).restore(saved)

    def test_stable_event_keys_ignore_dataset_refresh_ids(self):
        changed = {**self.data, "id": "new-dataset-version"}
        with patch("entry_watch.Geometry.proposals", return_value=[]):
            a, b = self.engine().run(), self.engine(changed).run()
        self.assertEqual([m["eventKey"] for m in a["messages"]], [m["eventKey"] for m in b["messages"]])
        self.assertEqual([e["eventKey"] for e in a["entries"]], [e["eventKey"] for e in b["entries"]])

    def test_flat_price_drift_does_not_generate_a_breakout(self):
        with patch("entry_watch.Geometry.proposals", return_value=[]):
            engine = self.engine(cutoff=self.sources["4h"][20].end)
            old = engine.bars[19].close
            engine.bars[20] = replace(engine.bars[20], open=old, close=old)
            c = engine.candidates[1]
            c["ray"].update(a_price=old+1.95, b_price=old+.95, slope=-.1)
            c["width"] = .01
            engine.run()
        self.assertFalse(any(m["state"] == "breakout" for m in engine.messages))

    def test_retest_must_be_later_and_keeps_original_action_ray(self):
        with patch("entry_watch.Geometry.proposals", return_value=[]):
            engine = self.engine()
            engine.step(20)
            self.assertFalse(any(e["family"] == "retest" for e in engine.pending))
            original = deepcopy(engine.candidates[1]["ray"])
            b = engine.bars[21]
            level = at(original, 21)
            engine.bars[21] = replace(b, open=level, high=level+2, low=level, close=level+1)
            engine.step(21)
            retest = next(e for e in engine.pending if e["family"] == "retest")
            self.assertEqual({k: retest["red"][k] for k in original}, original)
            self.assertGreater(retest["signalIndex"], 20)

    def test_nearer_known_safety_is_separate_from_original_safety(self):
        with patch("entry_watch.Geometry.proposals", return_value=[]):
            engine = self.engine()
            nearer = deepcopy(engine.candidates[0])
            nearer["id"] = "nearer-green"
            nearer["ray"].update(a_price=96, b_price=97)
            engine.candidates.append(nearer)
            result = engine.run()
        e = next(e for e in result["entries"] if e["family"] == "breakout")
        self.assertEqual(e["green"]["a_price"], 96)
        self.assertEqual(e["armGreen"]["a_price"], 95)

    def test_scanning_has_no_outcome_or_provider_access(self):
        with patch("alpaca._request", side_effect=AssertionError("network")), patch("lab_metrics.OutcomeEvaluator.evaluate", side_effect=AssertionError("future labels")):
            result = WatchReplay(self.data, "swing_envelope", self.start, self.cutoff).run()
        self.assertEqual(result["asOf"], self.cutoff)


class StudyTests(unittest.TestCase):
    def test_persisted_scan_is_offline_idempotent_and_rejects_backward_reuse(self):
        data, sources = dataset()
        start, end = sources["4h"][20].end, sources["4h"][23].end
        with tempfile.TemporaryDirectory() as folder, patch("tools.entry_watch_scan.read_dataset", return_value=data):
            state = Path(folder)/"watch.json"
            first = scan(data["id"], "swing_envelope", start, end, state)
            again = scan(data["id"], "swing_envelope", start, end, state)
            self.assertEqual(again["newMessages"], [])
            self.assertEqual(again["newEntries"], [])
            self.assertTrue(state.exists())
            with self.assertRaises(ValueError):
                scan(data["id"], "swing_envelope", start, end-1, state)

    def test_manual_geometry_comparison_uses_only_supplied_human_rays(self):
        _, sources = dataset()
        known = sources["4h"][:20]
        ray = candidate(known, True)["ray"]
        case, hidden = blind_case("TEST", known, known[-1].end, {"swing_envelope": [{"upper": True, "ray": ray}]})
        review = {"caseId": case["caseId"], "interesting": True, "rays": [
            {"upper": True, "aIndex": 0, "bIndex": 10, "aPrice": 110/hidden["basePrice"]*100, "bPrice": 109/hidden["basePrice"]*100}]}
        result = compare_reviews([case], [hidden], [review])
        self.assertEqual(result[0]["matchesWithinQuarterATR"]["swing_envelope"], 1)

    def test_costs_are_two_sided_and_blind_review_cannot_fake_a_missing_judgement(self):
        self.assertAlmostEqual(net_return(0), ((1-.00075)/(1+.00075)-1)*100)
        _, sources = dataset()
        bars = sources["4h"][:20]
        case, private = blind_case("TEST", bars, bars[-1].end, {})
        self.assertTrue(all(b["end"] <= case["cutoff"] for b in case["bars"]))
        with self.assertRaises(ValueError):
            compare_reviews([case], [private], [{"caseId": case["caseId"], "interesting": None}])
        with self.assertRaises(ValueError):
            compare_reviews([case], [private], [{"caseId": case["caseId"], "interesting": True,
                "rays": [{"aIndex": 0, "bIndex": 1000, "aPrice": 90, "bPrice": 100}]}])
