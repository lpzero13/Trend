from copy import deepcopy
from dataclasses import asdict, replace
import unittest

from lab_data import resample_regular
from lab_splits import sessions_between
from models import DataError
from safety_strategy import (StrategyContext, SafetyState, strategy_path,
                             pivot_indices, validate_rules, execution_costs)
from test_lab_data import session


class SafetyStrategyTests(unittest.TestCase):
    def setUp(self):
        days = sessions_between("2025-01-02", "2025-04-08")
        self.fine = sum((session(d) for d in days), [])
        self.fine[0] = replace(self.fine[0], low=97)
        # Two 4h source buckets per normal trading day.
        self.fine[5*78] = replace(self.fine[5*78], low=98)
        self.frames, _ = resample_regular(self.fine)
        self.four = self.frames["4h"]
        a, b = 0, 10
        green = {"a_index": a, "b_index": b, "a_time": self.four[a].time,
                 "b_time": self.four[b].time, "a_price": 97, "b_price": 98,
                 "slope": .1, "basis": "bars", "valid": True, "contacts": 2}
        red = {**green, "a_price": 101, "b_price": 100, "slope": -.1}
        self.entry = {"id": "entry", "entryAt": self.four[20].time,
                      "entryPrice": 100, "signalAt": self.four[19].end,
                      "availableAt": self.four[19].end+300,
                      "initialStop": 98.9, "red": red, "green": green}
        self.source = StrategyContext(self.frames, self.fine[-1].end)
        self.contract = self.source.entry_contract(self.entry, {"spread_bps": 0, "slippage_bps": 0})

    def test_invalid_rules_and_costs_are_rejected_and_missing_atr_blocks(self):
        for bad in ({"future": 1}, {"tick": True}, {"initial_buffer_atr": float("nan")},
                    {"source_timeframe": "1h"}, {"latency_seconds": 1}):
            with self.subTest(bad=bad), self.assertRaises(DataError):
                validate_rules(bad)
        for bad in ({"slippage_bps": -1}, {"notional": 0}, {"side_cost": 0}):
            with self.assertRaises(DataError):
                execution_costs(bad)
        early = {**self.entry, "entryAt": self.four[2].time}
        contract = self.source.entry_contract(early)
        self.assertIsNone(contract["atr"])
        self.assertFalse(contract["eligible"])
        self.assertEqual(strategy_path(self.source, early, contract, "original", 5)["status"], "unavailable")

    def test_same_initial_backup_and_wick_is_not_a_close_exit(self):
        self.assertLess(self.contract["initialStop"], self.entry["initialStop"])
        index = next(i for i, b in enumerate(self.fine) if b.time == self.entry["entryAt"])+1
        fine = list(self.fine)
        fine[index] = replace(fine[index], low=98.8)
        frames, _ = resample_regular(fine)
        source = StrategyContext(frames, fine[-1].end)
        contract = source.entry_contract(self.entry, {"spread_bps": 0, "slippage_bps": 0})
        paths = [strategy_path(source, self.entry, contract, m, 5) for m in ("fixed", "original", "structure", "structure_target")]
        self.assertEqual(len({p["initialStop"] for p in paths}), 1)
        self.assertTrue(all(p["exitReason"] == "time" for p in paths))

    def test_confirmed_safety_break_exits_only_after_latency_at_next_open(self):
        fine = list(self.fine)
        close_at = self.four[20].end
        j = next(i for i, b in enumerate(fine) if b.end == close_at)
        fine[j] = replace(fine[j], low=98.8, close=98.9)
        source = StrategyContext(resample_regular(fine)[0], fine[-1].end)
        contract = source.entry_contract(self.entry, {"spread_bps": 0, "slippage_bps": 0})
        p = strategy_path(source, self.entry, contract, "original", 5)
        self.assertEqual(p["exitReason"], "safety_close")
        self.assertEqual(p["fillBarAt"], close_at+300)
        self.assertEqual(p["events"][0]["knownAt"], close_at)
        self.assertEqual(p["exitPrice"], 100)
        # Signal close cannot be used as a retroactive fill.
        self.assertNotEqual(p["exitPrice"], 98.9)

    def test_gap_and_same_bar_target_ambiguity_use_hard_stop_first(self):
        source = deepcopy(self.source)
        index = next(i for i, b in enumerate(source.fine) if b.time == self.entry["entryAt"])+1
        source.fine[index] = replace(source.fine[index], open=90, high=102, low=89)
        p = strategy_path(source, self.entry, self.contract, "original", 5)
        self.assertEqual(p["exitReason"], "hard_stop_gap")
        self.assertEqual(p["exitFill"], 90)
        source.fine[index] = replace(source.fine[index], open=100, high=105, low=90)
        contract = {**self.contract, "targetPrice": 104}
        p = strategy_path(source, self.entry, contract, "structure_target", 5)
        self.assertTrue(p["intrabarAmbiguous"])
        self.assertEqual(p["exitReason"], "hard_stop")

    def test_missing_path_and_phase_boundary_never_become_free_holds(self):
        source = deepcopy(self.source)
        index = next(i for i, b in enumerate(source.fine) if b.time == self.entry["entryAt"])+3
        source.fine.pop(index)
        self.assertEqual(strategy_path(source, self.entry, self.contract, "original", 5)["reason"], "missing_fine_path")
        source.fine[index-1] = replace(source.fine[index-1], low=90)
        self.assertEqual(strategy_path(source, self.entry, self.contract, "original", 5)["status"], "closed")
        cutoff = self.entry["entryAt"]+900
        limited = StrategyContext(self.frames, cutoff)
        self.assertEqual(strategy_path(limited, self.entry, self.contract, "original", 5)["reason"], "phase_boundary")

    def structural_source(self):
        source = deepcopy(self.source)
        for i in range(11, 28):
            source.four[i] = replace(source.four[i], low=100, high=103, close=101.5)
        source.four[21] = replace(source.four[21], high=105)
        source.four[24] = replace(source.four[24], low=99.6)
        return source

    def test_connected_higher_low_needs_two_right_bars_and_preserves_anchors(self):
        source = self.structural_source()
        state = SafetyState(source, self.entry, self.contract, "structure")
        old = deepcopy(state.ray)
        for i in range(20, 26):
            state.step(i, source.four[i].end+300)
        self.assertFalse(state.events)
        state.step(26, source.four[26].end+300)
        self.assertEqual(state.events[-1]["kind"], "safety_replace")
        self.assertEqual(state.ray["a_index"], old["b_index"])
        self.assertEqual(state.ray["b_index"], 24)
        self.assertEqual(self.entry["green"], old)
        self.assertGreaterEqual(state.hard_stop, self.contract["initialStop"])
        state.step(27, source.four[27].end+300)
        self.assertEqual(len(state.events), 1)
        with self.assertRaises(ValueError):
            state.step(29, source.four[29].end+300)

    def test_current_bar_break_checked_before_replacement_and_bad_wick_rejects_ray(self):
        source = self.structural_source()
        source.four[26] = replace(source.four[26], close=99.5)
        state = SafetyState(source, self.entry, self.contract, "structure")
        for i in range(20, 27):
            state.step(i, source.four[i].end+300)
        self.assertEqual(state.events[-1]["kind"], "safety_close")
        self.assertEqual(state.ray, self.entry["green"])
        source = self.structural_source()
        source.four[15] = replace(source.four[15], low=98.4)
        state = SafetyState(source, self.entry, self.contract, "structure")
        for i in range(20, 27):
            state.step(i, source.four[i].end+300)
        self.assertFalse(state.events)
        self.assertEqual(state.diagnostics["connected_ray_cuts_wick"], 1)

    def test_future_bars_do_not_change_entry_contract_or_past_state(self):
        changed = deepcopy(self.frames)
        for rows in changed.values():
            for i, b in enumerate(rows):
                if b.time >= self.entry["entryAt"]:
                    rows[i] = replace(b, open=500, high=1000, low=.01, close=900)
        context = StrategyContext(changed, changed["5m"][-1].end)
        self.assertEqual(self.contract, context.entry_contract(self.entry, {"spread_bps": 0, "slippage_bps": 0}))
        prefix = StrategyContext(self.frames, self.entry["entryAt"])
        self.assertEqual(self.contract, prefix.entry_contract(self.entry, {"spread_bps": 0, "slippage_bps": 0}))

    def test_zone_confirmation_prominence_and_closed_through_invalidation(self):
        source = deepcopy(self.source)
        daily = list(source.daily)
        for i, bar in enumerate(daily):
            daily[i] = replace(bar, open=95, high=100, low=90, close=95)
        daily[20] = replace(daily[20], high=120)
        source.daily = daily
        source.daily_ends = [b.end for b in daily]
        source.weekly = []
        source.week_ends = []
        before = source.known_context(daily[21].end)
        self.assertFalse(before["zones"])
        after = source.known_context(daily[22].end)
        self.assertEqual(len(after["zones"]), 1)
        self.assertEqual(after["zones"][0]["sources"][0]["knownAt"], daily[22].end)
        source.daily[23] = replace(daily[23], high=126, close=124)
        self.assertFalse(source.known_context(daily[24].end)["zones"])
        # Strict pivot ties never create several independent touches.
        self.assertEqual(pivot_indices(daily[:20], True), [])


if __name__ == "__main__":
    unittest.main()
