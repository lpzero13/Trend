"""Synthetic stop counterexamples; no provider credentials or market claims."""
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
import unittest

import test_safety_strategy as fixtures
from retest_exits import HigherLowStop, path, contract_for, complete_history, trade_stats
from exit_research import horizon_close


class RetestExitTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.SafetyStrategyTests()
        self.f.setUp()
        self.e = {**self.f.entry, "rawSafety": self.f.entry["initialStop"], "initialStop": self.f.contract["initialStop"]}

    def test_archive_stop_is_buffered_exactly_once_and_mutation_rejected(self):
        c = contract_for(self.f.source, self.e, {"spread_bps": 0, "slippage_bps": 0})
        self.assertAlmostEqual(c["initialStop"], self.e["initialStop"])
        with self.assertRaises(ValueError):
            contract_for(self.f.source, {**self.e, "initialStop": self.e["initialStop"]-1}, {"spread_bps": 0, "slippage_bps": 0})

    def test_close_below_projected_line_is_not_a_stop_only_exit(self):
        source = deepcopy(self.f.source)
        source.four[20] = replace(source.four[20], low=98.8, close=98.9)
        result = path(source, self.e, self.f.contract, "higher_low_stop")
        self.assertEqual(result["exitReason"], "time")
        self.assertTrue(all(e["kind"] == "safety_replace" for e in result["events"]))

    def test_confirmed_raise_needs_two_right_bars_and_does_not_loosen(self):
        source = self.f.structural_source()
        state = HigherLowStop(source, self.e, self.f.contract, "structure")
        original = deepcopy(state.ray)
        for i in range(20, 26):
            state.step(i, source.four[i].end+300)
        self.assertFalse(state.events)
        state.step(26, source.four[26].end+300)
        self.assertEqual(len(state.events), 1)
        self.assertEqual(state.events[0]["knownAt"], source.four[26].end)
        self.assertGreater(state.hard_stop, self.f.contract["initialStop"])
        self.assertEqual(self.e["green"], original)
        old_stop = state.hard_stop
        state.step(27, source.four[27].end+300)
        self.assertGreaterEqual(state.hard_stop, old_stop)
        with self.assertRaises(ValueError):
            state.step(29, source.four[29].end+300)

    def test_stop_raise_applies_after_latency_not_on_confirmation_bar(self):
        source = self.f.structural_source()
        state = HigherLowStop(source, self.e, self.f.contract, "structure")
        for i in range(20, 27):
            state.step(i, source.four[i].end+300)
        raised = state.hard_stop
        known = source.four[26].end
        for stamp in (known-300, known):
            j = source.times.index(stamp)
            source.fine[j] = replace(source.fine[j], low=(raised+self.f.contract["initialStop"])/2)
        j = source.times.index(known+300)
        source.fine[j] = replace(source.fine[j], low=raised-.01)
        actual = path(source, self.e, self.f.contract, "higher_low_stop")
        fixed = path(source, self.e, self.f.contract, "fixed")
        self.assertEqual(actual["fillBarAt"], known+300)
        self.assertEqual(actual["exitPrice"], raised)
        self.assertEqual(fixed["exitReason"], "time")

    def test_gap_costs_and_missing_path_are_not_free_holds(self):
        source = deepcopy(self.f.source)
        j = source.times.index(self.e["entryAt"])+1
        source.fine[j] = replace(source.fine[j], open=90, high=102, low=89)
        c = contract_for(source, self.e, {"spread_bps": 0, "slippage_bps": 0})
        for model in ("fixed", "higher_low_stop"):
            p = path(source, self.e, c, model)
            self.assertEqual(p["exitReason"], "hard_stop_gap")
            self.assertEqual(p["exitPrice"], 90)
            expected = (Decimal(90)/Decimal(100)-1)*100
            self.assertAlmostEqual(p["netReturnPct"], float(expected))
        source = deepcopy(self.f.source)
        source.fine.pop(j)
        source.times.pop(j)
        for model in ("fixed", "higher_low_stop"):
            p = path(source, self.e, self.f.contract, model)
            self.assertEqual(p["status"], "censored")
            self.assertEqual(p["reason"], "missing_fine_path")

    def test_history_selection_is_causal_and_future_path_has_no_effect(self):
        history = complete_history(self.f.frames, self.e)
        self.assertTrue(history["complete"])
        revised = deepcopy(self.f.frames)
        revised["4h"].pop(15)
        self.assertFalse(complete_history(revised, self.e)["complete"])
        changed = deepcopy(self.f.source)
        cutoff = horizon_close(self.e["entryAt"], 10)
        for name in ("fine", "four"):
            setattr(changed, name, [replace(b, open=500, high=1000, low=.01, close=900) if b.time >= cutoff else b for b in getattr(changed, name)])
        for model in ("fixed", "higher_low_stop"):
            self.assertEqual(path(self.f.source, self.e, self.f.contract, model), path(changed, self.e, self.f.contract, model))

    def test_trade_metrics_keep_unknowns_separate_and_use_r_for_profit_factor(self):
        paths = [{"entryId":str(i),"exitAt":i,"status":"closed","netR":v,"netReturnPct":v,"events":[],"exitReason":"time"}
                 for i,v in enumerate([.2, .2, -1., -.5, .4])]
        result = trade_stats(paths+[{"status":"censored","events":[]}])
        self.assertEqual(result["unknown"], 1)
        self.assertEqual(result["longestLossStreak"], 2)
        self.assertAlmostEqual(result["profitFactorR"], .8/1.5)

    def test_entry_cannot_be_filled_before_it_is_available(self):
        entry = {**self.e, "availableAt": self.e["entryAt"]+300}
        for model in ("fixed", "higher_low_stop"):
            p = path(self.f.source, entry, self.f.contract, model)
            self.assertEqual(p["status"], "invalid")
            self.assertEqual(p["reason"], "invalid_entry_knowledge_or_grid")

    def test_ray_replacement_and_actual_stop_raise_are_separate_counters(self):
        result = trade_stats([{"status":"censored","events":[
            {"previousHardStop":90,"hardStop":91}, {"previousHardStop":91,"hardStop":91}]}])
        self.assertEqual(result["structureUpdates"], 2)
        self.assertEqual(result["stopRaises"], 1)


if __name__ == "__main__":
    unittest.main()
