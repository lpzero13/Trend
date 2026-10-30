from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
import unittest

from fan_execution import ExecutionRules, entry_contract, holding_close, next_open_time, path, stop_changes
from lab_data import session_bounds
from lab_metrics import expected_grid
from models import Bar
from models import DataError


class FanExecutionTests(unittest.TestCase):
    def setUp(self):
        self.open, self.close = session_bounds("2024-01-08")
        self.fine = [Bar(t, t+300, 100, 101, 99, 100, 10) for t in expected_grid(self.open, self.close+4*86400)]
        self.rules = ExecutionRules(latency_seconds=0, capital=2000, risk_fraction=.1, spread_bps=0, slippage_bps=0)
        self.signal = {"id": "signal", "signalAt": self.open-1, "initialStop": 95}
        self.contract = entry_contract(self.signal, self.fine, self.close+4*86400, self.rules)

    def test_next_open_after_signal_not_signal_close_or_later_available_open(self):
        self.assertEqual(self.contract["entryAt"], self.open)
        self.assertEqual(self.contract["entryPrice"], 100)
        self.assertEqual(next_open_time(self.close), session_bounds("2024-01-09")[0])
        self.assertEqual(entry_contract(self.signal, self.fine[1:], self.close, self.rules)["reason"], "missing_expected_entry_open")
        self.assertEqual(entry_contract(self.signal, self.fine, self.open, self.rules)["status"], "pending")

    def test_gap_under_stop_cancels_instead_of_inventing_a_valid_entry(self):
        fine = [replace(self.fine[0], open=94, low=93), *self.fine[1:]]
        self.assertEqual(entry_contract(self.signal, fine, self.close, self.rules)["status"], "cancelled")

    def test_stop_gap_and_ambiguous_target_are_conservative(self):
        r = replace(self.rules, target_r=1)
        entry = entry_contract(self.signal, self.fine, self.close, r)
        both = [replace(self.fine[0], low=94, high=106), *self.fine[1:]]
        got = path(entry, both, [], self.close, 1, rules=r)
        self.assertEqual(got["reason"], "stop")
        self.assertTrue(got["intrabarAmbiguous"])
        gap = [self.fine[0], replace(self.fine[1], open=90, low=89, high=92, close=91), *self.fine[2:]]
        got = path(entry, gap, [], self.close, 1, rules=r)
        self.assertEqual(got["reason"], "stop_gap")
        self.assertEqual(got["exitPrice"], 90)
        self.assertLess(got["netPnl"], -entry["plannedRisk"])

    def test_missing_path_is_not_skipped_to_later_stop_or_profit(self):
        fine = [self.fine[0], *self.fine[2:]]
        got = path(self.contract, fine, [], self.close+4*86400, 1, rules=self.rules)
        self.assertEqual(got["status"], "censored")
        self.assertEqual(got["missingAt"], self.open+300)
        self.assertIsNone(got["netPnl"])

    def test_time_exit_counts_following_trading_sessions_and_costs_both_sides(self):
        self.assertEqual(holding_close(self.open, 1), session_bounds("2024-01-09")[1])
        r = replace(self.rules, fee_per_order=1, spread_bps=5, slippage_bps=5)
        entry = entry_contract(self.signal, self.fine, self.close+4*86400, r)
        got = path(entry, self.fine, [], self.close+4*86400, 1, rules=r)
        self.assertEqual(got["status"], "closed")
        self.assertEqual(got["reason"], "time")
        self.assertLess(got["netPnl"], -2)
        self.assertAlmostEqual(got["netReturnPct"], got["netPnl"]/entry["plannedCash"]*100)
        self.assertLessEqual(entry["plannedCash"], r.capital)
        self.assertLessEqual(entry["plannedRisk"], r.capital*r.risk_fraction)

    def test_unfinished_observation_has_no_fabricated_realized_pnl(self):
        got = path(self.contract, self.fine, [], self.close, 20, rules=self.rules)
        self.assertEqual(got["status"], "open")
        self.assertIsNone(got["netPnl"])

    def test_higher_low_stop_is_confirmed_and_effective_only_after_latency(self):
        at = self.open
        source = [Bar(at+i*300, at+(i+1)*300, 100, 102, low, 101, 10)
                  for i, low in enumerate([99, 98, 96, 98, 99, 100, 99])]
        r = replace(self.rules, pivot_side=2, latency_seconds=300)
        # Entry availability is still at the opening bar; all path assumptions
        # must be the ones already bound to that entry contract.
        self.contract = entry_contract({**self.signal, "signalAt": at-300}, self.fine, self.close, r)
        changes = list(stop_changes(source, self.contract, r))
        self.assertEqual(changes[0]["knownAt"], at+1500)
        self.assertEqual(changes[0]["effectiveAt"], at+1800)
        original = deepcopy(changes)
        # A plunge after the confirmation cannot rewrite the earlier raise.
        source.append(Bar(at+2100, at+2400, 99, 100, 90, 95, 10))
        self.assertEqual(list(stop_changes(source, self.contract, r))[0], original[0])
        fine = list(self.fine)
        fine[3] = replace(fine[3], low=95.2)  # below later stop, before it exists
        fine[6] = replace(fine[6], low=95.2)  # same low after stop's activation
        got = path(self.contract, fine, source, self.close, 1, "higher_low", r)
        self.assertEqual(got["reason"], "stop")
        self.assertEqual(got["fillBarAt"], at+1800)
        self.assertGreater(got["finalStop"], self.contract["initialStop"])

    def test_path_cannot_silently_change_entry_assumptions(self):
        with self.assertRaises(DataError):
            path(self.contract, self.fine, [], self.close, 1, rules=replace(self.rules, fee_per_order=3))


if __name__ == "__main__":
    unittest.main()
