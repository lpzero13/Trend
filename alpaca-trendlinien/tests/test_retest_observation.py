"""Causal observation/resume and preregistered decision counterexamples."""
from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from datasets import digest
from entry_watch import WatchReplay
from lab_data import resample_regular
from retest_observation import observe, assessment, diagnose
from tools.retest_observe import scan
from tools.retest_exit_study import checked
import test_entry_discovery as fixtures


class ObservationTests(unittest.TestCase):
    def setUp(self):
        self.data, self.sources = fixtures.dataset()
        fine = list(self.sources["5m"])
        end = self.sources["4h"][21].end
        opened = self.sources["4h"][21].time
        fine = [replace(b, open=100) if b.time == opened else b for b in fine]
        j = next(i for i, b in enumerate(fine) if b.end == end)
        fine[j] = replace(fine[j], close=108.5, high=109)
        fine = [replace(b, open=108.5, high=109, low=108, close=108.5)
                if b.time == self.sources["4h"][22].time else b for b in fine]
        self.sources, _ = resample_regular(fine)
        self.data["material"]["bars"] = {tf: [asdict(b) for b in bars] for tf, bars in self.sources.items()}
        self.data["id"] = digest(self.data["material"])
        self.start = self.sources["4h"][20].end
        self.first = self.sources["4h"][23].end
        self.last = self.sources["5m"][-1].end

    def engine(self, data, model, start, cutoff):
        engine = WatchReplay(data, model, start, cutoff)
        engine.candidates = [fixtures.candidate(engine.bars, False), fixtures.candidate(engine.bars, True)]
        return engine

    def observation(self, asof, prior=None, data=None):
        with patch("retest_observation.WatchReplay", side_effect=self.engine), patch("entry_watch.Geometry.proposals", return_value=[]):
            return observe(data or self.data, self.start, self.start, asof, prior)

    def test_original_entry_and_both_paths_survive_resume_and_same_cutoff_is_quiet(self):
        first, events = self.observation(self.first)
        self.assertTrue(first["records"])
        self.assertTrue(any(e["kind"] == "entry" for e in events))
        again, new = self.observation(self.first, first)
        self.assertEqual(first, again)
        self.assertEqual(new, [])
        resumed, _ = self.observation(self.last, first)
        full, _ = self.observation(self.last)
        self.assertEqual(resumed["records"], full["records"])
        self.assertEqual({e["eventKey"] for e in resumed["journal"]}, {e["eventKey"] for e in full["journal"]})
        self.assertTrue(all(p["status"] == "closed" for r in resumed["records"] for p in r["paths"].values()))
        self.assertEqual(first["records"][0]["entry"], resumed["records"][0]["entry"])

    def test_future_changes_cannot_change_current_observations(self):
        data = deepcopy(self.data)
        for rows in data["material"]["bars"].values():
            for b in rows:
                if b["time"] >= self.first:
                    b.update(open=200, high=201, low=199, close=200)
        # Same identity is intentional in this unit test: only the trimmed prefix is observed.
        a, events_a = self.observation(self.first)
        b, events_b = self.observation(self.first, data=data)
        self.assertEqual(a, b)
        self.assertEqual(events_a, events_b)

    def test_changed_known_price_or_code_or_time_reversal_rejects_resume(self):
        state, _ = self.observation(self.first)
        changed = deepcopy(self.data)
        changed["material"]["bars"]["5m"][0]["close"] += .01
        with self.assertRaises(ValueError):
            self.observation(self.last, state, changed)
        with self.assertRaises(ValueError):
            self.observation(self.first-300, state)
        state["config"]["engine"]["entry_watch.py"] = "changed"
        with self.assertRaises(ValueError):
            self.observation(self.last, state)

    def test_missing_fine_path_is_unresolved_and_not_a_loss_or_win(self):
        data = deepcopy(self.data)
        state, _ = self.observation(self.first)
        entry = state["records"][0]["entry"]
        rows = data["material"]["bars"]["5m"]
        data["material"]["bars"]["5m"] = [b for b in rows if b["time"] != entry["entryAt"]+300]
        result, events = self.observation(self.last, data=data)
        paths = result["records"][0]["paths"]
        self.assertTrue(all(p["status"] == "censored" and p["reason"] == "missing_fine_path" for p in paths.values()))
        self.assertTrue(any(e["kind"] == "unresolved" for e in events))
        self.assertFalse(any(e["kind"] == "closed" and e["entryId"] == entry["id"] for e in events))

    def test_new_dataset_identity_with_identical_prefix_can_continue(self):
        state, _ = self.observation(self.first)
        changed = deepcopy(self.data)
        changed["id"] = "appended-dataset"
        resumed, _ = self.observation(self.last, state, changed)
        self.assertEqual(resumed["datasetId"], changed["id"])
        self.assertEqual(state["records"][0]["entry"], resumed["records"][0]["entry"])

    def test_closed_path_or_old_event_cannot_be_silently_rewritten(self):
        closed, _ = self.observation(self.last)
        closed["records"][0]["paths"]["fixed"]["exitFill"] += 1
        with self.assertRaises(ValueError):
            self.observation(self.last, closed)

    def test_cli_atomically_persists_idempotent_outbox_and_detects_corruption(self):
        with tempfile.TemporaryDirectory() as folder, patch("tools.retest_observe.read_dataset", return_value=self.data), \
             patch("retest_observation.WatchReplay", side_effect=self.engine), patch("entry_watch.Geometry.proposals", return_value=[]):
            path = Path(folder)/"observer.json"
            first = scan(self.data["id"], self.start, self.start, self.first, path)
            again = scan(self.data["id"], self.start, self.start, self.first, path)
            self.assertTrue(first["newEvents"])
            self.assertEqual(again["newEvents"], [])
            self.assertTrue(checked(path)["records"])
            path.write_text(path.read_text().replace('"swing_zone"', '"corrupt"'))
            with self.assertRaises(ValueError):
                scan(self.data["id"], self.start, self.start, self.first, path)


class DecisionTests(unittest.TestCase):
    def rows(self, n=32, delta=-.04):
        return [{"entry": {"model": "swing_zone", "symbol": "S"+str(i % 8)}, "calendarFits": True,
                 "history": {"complete": True}, "paths": {"fixed": {"status": "closed", "netR": .3},
                 "atr_gain_stop": {"status": "closed", "netR": .3+delta}}} for i in range(n)]

    def portfolios(self, atr_dd=-3):
        return {"swing_zone/"+m: {"max5mSampledDrawdownPct": d, "status": "marked_to_phase_end", "open": 0}
                for m, d in (("fixed", -5), ("atr_gain_stop", atr_dd))}

    def test_predeclared_risk_budget_requires_sample_return_and_drawdown_together(self):
        self.assertEqual(assessment(self.rows(), self.portfolios())["decision"], "risk_hypothesis_passed_descriptive_gate")
        for rows, books in ((self.rows(29), self.portfolios()), (self.rows(delta=-.06), self.portfolios()),
                            (self.rows(), self.portfolios(-4.5))):
            self.assertEqual(assessment(rows, books)["decision"], "not_established_keep_fixed_reference")

    def test_missing_paths_and_halted_portfolio_cannot_pass_on_survivors(self):
        rows = self.rows(40)
        rows[0]["paths"]["atr_gain_stop"]["status"] = "censored"
        result = assessment(rows, self.portfolios())
        self.assertFalse(result["checks"]["complete_paths"])
        books = self.portfolios()
        books["swing_zone/fixed"]["status"] = "halted"
        self.assertFalse(assessment(self.rows(), books)["checks"]["uninterrupted_portfolios"])

    def test_empty_sample_and_zero_drawdown_are_unknown_not_success(self):
        books = self.portfolios()
        books["swing_zone/fixed"]["max5mSampledDrawdownPct"] = 0
        result = assessment([], books)
        self.assertIsNone(result["relativeDrawdownReduction"])
        self.assertIsNone(result["meanDeltaR"])
        self.assertEqual(result["decision"], "not_established_keep_fixed_reference")

    def test_diagnostic_keeps_missingness_and_does_not_propose_a_fitted_threshold(self):
        rows = self.rows(2)
        for i, r in enumerate(rows):
            r["entry"].update(entryPrice=100, initialStop=95, features={"contacts": 2+i}, context={"daily": "up"})
            r["paths"]["fixed"]["netR"] = 1 if i else -1
        result = diagnose(rows)
        self.assertEqual(result["groups"]["positive"]["numeric"]["contacts"]["median"], 3)
        self.assertEqual(result["groups"]["all"]["numeric"]["netRoomR"]["missing"], 2)
        self.assertEqual(result["groups"]["all"]["numeric"]["safetyDistancePct"]["median"], 5)
        self.assertNotIn("threshold", result)
