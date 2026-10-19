from copy import deepcopy
from dataclasses import replace
import unittest
from unittest.mock import patch

from exit_research import ExitSources, exit_path, horizon_close, summarize
from lab_data import resample_regular
from lab_execution import trade_path
from lab_profiles import DEFAULTS
from lab_splits import sessions_between
from test_lab_data import session
from tools.exit_study import freeze_cases
from tools.exit_study import compare
from tools.verify_exit_study import audit
from dataclasses import asdict
from exit_research import DEFAULT_COSTS, MODELS


class ExitResearchTests(unittest.TestCase):
    def setUp(self):
        self.days = sessions_between("2025-03-03", "2025-04-08")
        fine = sum((session(d) for d in self.days), [])
        self.frames, _ = resample_regular(fine)
        at = fine[0].time
        self.entry = {"entryAt": at, "entryPrice": 100, "initialStop": 98,
                      "signalAt": at-300, "availableAt": at,
                      "red": {"basis": "bars", "a_price": 99, "a_index": 0, "slope": -.01},
                      "green": {"b_time": at-86400}}
        self.costs = {"spread_bps": 0, "slippage_bps": 0}
        self.source = ExitSources(self.frames, fine[-1].end)

    def test_legacy_fixed_models_agree_and_horizon_is_sessions_after_entry(self):
        for new, old in (("time", "time"), ("safety", "stop_time"), ("target_2r", "stop_target_time")):
            got = exit_path(self.source, self.entry, new, 5, self.costs)
            before = trade_path(self.frames, self.entry, {**DEFAULTS["execution"],
                "exit": old, "holding_days": 5, "spread_bps": 0, "slippage_bps": 0}, self.source.cutoff)
            self.assertEqual(got["exitAt"], before["exitAt"])
            self.assertEqual(got["exitFill"], before["exitFill"])
        self.assertEqual(horizon_close(self.entry["entryAt"], 5), session(self.days[5])[-1].end)
        self.assertEqual(exit_path(self.source, self.entry, "time", 5, self.costs)["netPnl"], 5)

    def test_gap_ambiguity_missing_path_and_phase_boundary(self):
        self.source.fine[1] = replace(self.source.fine[1], open=95, low=94)
        self.assertEqual(exit_path(self.source, self.entry, "safety", 5, self.costs)["exitFill"], 95)
        self.source.fine[1] = replace(self.source.fine[1], open=100, low=97, high=105)
        p = exit_path(self.source, self.entry, "target_2r", 5, self.costs)
        self.assertEqual(p["exitFill"], 98)
        self.assertTrue(p["intrabarAmbiguous"])
        self.source.fine.pop(4)
        self.assertEqual(exit_path(self.source, self.entry, "safety", 5)["status"], "closed")
        self.assertEqual(exit_path(self.source, self.entry, "time", 5)["reason"], "missing_fine_path")
        short = ExitSources(self.frames, self.frames["5m"][2].end)
        self.assertEqual(exit_path(short, self.entry, "time", 5)["reason"], "phase_boundary")

    def test_fakeout_requires_close_and_latency_and_uses_original_ray(self):
        self.entry["red"]["a_price"] = 101
        current = self.source.four[0]
        p = exit_path(self.source, self.entry, "fakeout", 5, self.costs)
        self.assertEqual(p["exitReason"], "fakeout")
        self.assertEqual(p["fakeoutObservedAt"], current.end)
        self.assertEqual(p["fillBarAt"], current.end+300)
        self.assertEqual(p["exitPrice"], 100)
        # A wick below red, with the close still above, does not exit.
        self.entry["red"]["a_price"] = 100
        self.assertEqual(exit_path(self.source, self.entry, "fakeout", 5, self.costs)["exitReason"], "time")

    def test_green_is_confirmed_delayed_never_lowered_and_cannot_use_future(self):
        first = self.source.four[0]
        ray = {"basis": "bars", "a_price": 99.5, "a_index": 0, "slope": .01,
               "a_time": first.time-86400, "b_time": first.time-300, "b_index": -1}
        with patch.object(self.source, "green", return_value=ray):
            p = exit_path(self.source, self.entry, "trailing", 5, self.costs)
        self.assertEqual(p["exitReason"], "trailing_stop")
        self.assertEqual(p["fillBarAt"], first.end+300)
        self.assertEqual(p["stopUpdates"][0]["knownAt"], first.end)
        self.assertGreater(p["finalStop"], p["initialStop"])
        with patch.object(self.source, "green", return_value={**ray, "a_price": 97}):
            p = exit_path(self.source, self.entry, "trailing", 5, self.costs)
        self.assertFalse(p["stopUpdates"])
        self.entry["green"]["b_time"] = first.time
        with patch.object(self.source, "green", return_value=ray):
            p = exit_path(self.source, self.entry, "trailing", 5, self.costs)
        self.assertFalse(p["stopUpdates"])

    def test_resistance_missing_costs_invalid_inputs_and_denominators(self):
        self.entry["resistanceAtSignal"] = 100.8
        p = exit_path(self.source, self.entry, "resistance", 5)
        self.assertEqual(p["exitReason"], "target")
        buy = 100*1.00075
        self.assertAlmostEqual(p["netPnl"], (1000/buy)*(100.8*.99925-buy))
        self.entry["resistanceAtSignal"] = None
        self.assertEqual(exit_path(self.source, self.entry, "resistance", 5)["exitReason"], "time")
        self.assertEqual(exit_path(self.source, {**self.entry, "initialStop": 101}, "time", 5)["status"], "invalid")
        stats = summarize([p, {"status": "censored", "knownResistance": None, "reason": "missing_fine_path"}])
        self.assertEqual(stats["cases"], 2)
        self.assertEqual(stats["closed"], 1)
        self.assertEqual(stats["winRatePct"], 100)

    def test_frozen_cohort_deduplicates_without_future_outcome_selection(self):
        e = {**self.entry, "status": "observed", "inPhase": True, "variant": "breakout",
             "quality": "provisional", "forward": {"20": {"return_pct": 999}}}
        c = {"profile": "baseline", "symbol": "TEST", "datasetId": "a"*64,
             "sourceSetupId": "s", "startAt": self.entry["signalAt"]-1,
             "frozen": {k: self.entry[k] for k in ("red", "green")}, "variants": [e]}
        phase = {"startAt": e["entryAt"], "endAt": self.source.cutoff}
        later = deepcopy(c)
        later["startAt"] += 1
        first = freeze_cases([later, c], phase)
        later["variants"][0]["forward"]["20"]["return_pct"] = -999
        self.assertEqual(first, freeze_cases([c, later], phase))
        self.assertEqual(len(first), 1)
        self.assertEqual(first[0]["alternativeSetups"], 2)
        self.assertNotIn("forward", first[0])

    def test_independent_auditor_rejects_wrong_money_and_missing_cases(self):
        e = {**self.entry, "id": "entry", "profile": "baseline", "family": "breakout",
             "symbol": "TEST", "datasetId": "dataset"}
        phase = {"startAt": e["entryAt"], "endAt": self.source.cutoff}
        contract = {"cohorts": {"development": [], "validation": [e]},
                    "phases": {"development": phase, "validation": phase},
                    "costs": DEFAULT_COSTS, "horizons": [5,10,20], "models": list(MODELS)}
        data = {"dataset": {"material": {"symbol": "TEST", "bars": {
            tf: [asdict(b) for b in bars] for tf, bars in self.frames.items()}}}}
        result = compare(contract, data)
        checked = audit(contract, result, data)
        self.assertEqual(checked["auditedPaths"], 21)
        corrupted = deepcopy(result)
        corrupted["paths"][0]["netPnl"] += 1
        with self.assertRaises(AssertionError):
            audit(contract, corrupted, data)
        corrupted = deepcopy(result)
        next(p for p in corrupted["paths"] if p["model"] == "target_2r")["targetPrice"] += .1
        with self.assertRaises(AssertionError):
            audit(contract, corrupted, data)
        corrupted = deepcopy(result)
        corrupted["paths"].pop()
        with self.assertRaises(AssertionError):
            audit(contract, corrupted, data)


if __name__ == "__main__":
    unittest.main()
