from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from event_case_study import _work, checked, load_block, prepare, scan_episodes, statistics_for
from fan_geometry import stable_id
from models import DataError
from strategy_screen import write
from fan_execution import ExecutionRules
from lab_data import session_bounds
from lab_metrics import expected_grid
from models import Bar
from pilot_backtest import execute_path
from setup_episodes import Episodes
from signal_path_index import CaseExecution, PathIndex, execute_unbounded, isolated_entry


def line(identity="line", a=1, b=10, contacts=None):
    return {"id": identity, "a_time": a, "a_price": 90., "b_time": b, "b_price": 91.,
            "a_index": 0, "b_index": 5, "slope": .2, "value": 92., "knownAt": 19,
            "contacts": 3, "contactPoints": contacts or [{"time": a, "known_at": a+2}, {"time": b, "known_at": b+2}],
            "qualified": True, "level": 1}


def signal(identity="s", at=20, family="breakout", ln=None, scenario="red"):
    return {"id": identity, "signalAt": at, "family": family, "cohort": "qualified",
            "line": ln or line(), "scenarioId": scenario, "initialStop": 90., "safety": line("green")}


class EpisodeTests(unittest.TestCase):
    def test_gap_journal_while_geometry_is_not_yet_ready(self):
        from test_fan_geometry import triangle
        rows = triangle()
        with patch("event_case_study.source_gaps", return_value={20: rows[19].end}):
            _, timeline, _, diagnostics = scan_episodes("TEST", rows, rows[0].time, rows[-1].end)
        reset = next(t for t in timeline if t.get("gapAt") is not None)
        self.assertEqual(reset["gapAt"], rows[19].end)
        self.assertIsNone(reset["green"])
        self.assertEqual(diagnostics["sourceGaps"], 1)

    def test_refit_or_daily_continuation_is_not_a_new_case(self):
        e = Episodes("TEST")
        self.assertEqual(len(e.accept([signal()])[0]), 1)
        s = signal("refit", 40, ln=line("new-id", b=15), scenario="next-red")
        admitted, rejected = e.accept([s])
        self.assertEqual(admitted, [])
        self.assertEqual(rejected[0]["reason"], "same_structure_and_entry_family")

    def test_two_new_confirmed_contacts_create_new_episode_without_cooldown(self):
        e = Episodes("TEST")
        old = e.accept([signal()])[0][0]
        newer = line("refit", contacts=[{"time": 1, "known_at": 3}, {"time": 25, "known_at": 27}, {"time": 30, "known_at": 32}])
        new = e.accept([signal("new", 40, ln=newer, scenario="new")])[0][0]
        self.assertNotEqual(old["episodeId"], new["episodeId"])
        self.assertEqual(new["episodeReason"], "two_new_confirmed_contacts")

    def test_one_more_contact_or_quality_upgrade_is_still_same_episode(self):
        e = Episodes("TEST")
        first = signal()
        first["cohort"] = "two"
        e.accept([first])
        three = line("third", contacts=[{"time": 1, "known_at": 3}, {"time": 10, "known_at": 12}, {"time": 25, "known_at": 27}])
        accepted, skipped = e.accept([signal("upgraded", 40, ln=three, scenario="upgraded")])
        self.assertFalse(accepted)
        self.assertEqual(len(skipped), 1)

    def test_retest_keeps_old_origin_even_after_new_episode(self):
        e = Episodes("TEST")
        old = e.accept([signal()])[0][0]
        fresh = line("new", contacts=[{"time": 25, "known_at": 27}, {"time": 30, "known_at": 32}])
        e.accept([signal("new", 40, ln=fresh, scenario="new")])
        retest = e.accept([signal("ret", 50, family="red_retest")])[0][0]
        self.assertEqual(old["episodeId"], retest["episodeId"])

    def test_child_becoming_main_inherits_fan_lineage(self):
        e = Episodes("TEST")
        first, child = line(), line("child", a=10, b=15)
        first["b_price"] = child["a_price"]
        e.observe({"ready": True, "reds": [first, child], "greens": []})
        one = e.accept([signal()])[0][0]
        e.observe({"ready": True, "reds": [child], "greens": []})
        admitted, rejected = e.accept([signal("next", 40, ln=child, scenario="child")])
        self.assertFalse(admitted)
        self.assertEqual(rejected[0]["episodeId"], one["episodeId"])

    def test_future_contact_rejected_and_same_bar_strongest_selected(self):
        e = Episodes("TEST")
        bad = line(contacts=[{"time": 10, "known_at": 99}])
        with self.assertRaises(ValueError):
            e.accept([signal(ln=bad)])
        two, qualified = signal("two"), signal("qualified", scenario="q")
        two["cohort"] = "two"
        found, skipped = e.accept([two, qualified])
        self.assertEqual([s["id"] for s in found], ["qualified"])
        self.assertEqual(len(skipped), 1)


class PathTests(unittest.TestCase):
    def setup_path(self, end="2024-08-01"):
        opened, _ = session_bounds("2024-01-08")
        _, cutoff = session_bounds(end)
        stamps = list(expected_grid(opened, cutoff))
        bars = [Bar(t, t+300, 100., 101., 99., 100., 1) for t in stamps]
        s = signal(at=opened-300)
        s["safety"].update(knownAt=opened-300, slope=.01)
        return s, bars, cutoff

    def test_no_economic_budget_rejection_and_no_exit_after_80_days(self):
        s, bars, cutoff = self.setup_path()
        index = PathIndex(bars, cutoff)
        entry = isolated_entry(s, index, CaseExecution(notional=1.))
        self.assertEqual(entry["status"], "filled")
        self.assertLess(entry["quantity"], 1)
        p = execute_unbounded(s, entry, index, [], "fixed")
        self.assertEqual((p["status"], p["reason"]), ("open", "data_end"))
        self.assertIsNone(p["exitAt"])
        self.assertGreater(p["lastObservedAt"]-entry["entryAt"], 180*86400)
        self.assertNotIn("plannedTimeExit", p)

    def test_gap_censors_one_case_and_later_entry_runs(self):
        s, bars, cutoff = self.setup_path("2024-01-09")
        missing = bars[10].time
        del bars[10]
        index = PathIndex(bars, cutoff)
        p = execute_unbounded(s, isolated_entry(s, index), index, [], "fixed")
        self.assertEqual((p["status"], p["missingAt"]), ("censored", missing))
        later = signal("later", bars[20].time-300)
        p2 = execute_unbounded(later, isolated_entry(later, index), index, [], "fixed")
        self.assertEqual(p2["status"], "open")

    def test_gap_at_import_tail_does_not_shorten_data_end(self):
        s, bars, cutoff = self.setup_path("2024-01-09")
        wanted = bars[-1].time
        index = PathIndex(bars[:-1], cutoff)
        p = execute_unbounded(s, isolated_entry(s, index), index, [], "fixed")
        self.assertEqual((p["status"], p["missingAt"]), ("censored", wanted))

    def test_missing_open_is_not_replaced_by_next_available_bar(self):
        s, bars, cutoff = self.setup_path("2024-01-09")
        index = PathIndex(bars[1:], cutoff, start=bars[0].time)
        e = isolated_entry(s, index)
        self.assertEqual((e["status"], e["reason"]), ("unavailable", "missing_expected_entry_open"))

    def test_open_below_safety_cancels_entry_even_with_unlimited_capital(self):
        s, bars, cutoff = self.setup_path("2024-01-09")
        s["initialStop"] = 101.
        e = isolated_entry(s, PathIndex(bars, cutoff))
        self.assertEqual(e["status"], "cancelled")

    def test_new_stop_only_effective_after_confirmation_and_latency(self):
        s, bars, cutoff = self.setup_path("2024-01-09")
        known = bars[4].end
        # Low between the decision and its +300s activation must use old stop.
        b = bars[5]
        bars[5] = Bar(b.time, b.end, 100, 101, 94, 100, 1)
        green = line("new-green")
        green.update(a_price=95., a_index=0, slope=.1, knownAt=known)
        timeline = [{"closedAt": known, "index": 1, "close": 100., "green": green, "gapAt": None}]
        # A following opening gap hits the newly active stop at the raw open.
        b = bars[6]
        bars[6] = Bar(b.time, b.end, 94, 101, 93, 100, 1)
        index = PathIndex(bars, cutoff)
        entry = isolated_entry(s, index)
        p = execute_unbounded(s, entry, index, timeline, "fan_safety")
        self.assertEqual(p["fillBarAt"], bars[6].time)
        self.assertEqual(p["exitPrice"], 94)
        self.assertEqual(p["stopEvents"][0]["effectiveAt"], bars[6].time)

    def test_index_matches_bruteforce_random_ranges(self):
        rng = random.Random(123)
        s, bars, cutoff = self.setup_path("2024-01-09")
        bars = [Bar(b.time, b.end, 100, 100+rng.random()*10, 90+rng.random()*10, 100, 1) for b in bars]
        index = PathIndex(bars, cutoff)
        for _ in range(100):
            left = rng.randrange(len(bars)-1)
            right = rng.randrange(left+1, len(bars)+1)
            stop = 90+rng.random()*10
            wanted = next((i for i in range(left, right) if bars[i].low <= stop), None)
            self.assertEqual(index.first_touch(left, right, stop), wanted)
            self.assertEqual(index.extrema(left, right), (min(b.low for b in bars[left:right]), max(b.high for b in bars[left:right])))

    def test_fixed_stop_loss_includes_costs_and_excludes_exit_bar_high(self):
        s, bars, cutoff = self.setup_path("2024-01-09")
        b = bars[3]
        bars[3] = Bar(b.time, b.end, 100, 1000, 89, 90, 1)
        index = PathIndex(bars, cutoff)
        entry = isolated_entry(s, index)
        p = execute_unbounded(s, entry, index, [], "fixed")
        self.assertAlmostEqual(p["netR"], -1)
        self.assertLess(p["mfeR"], 1)

    def test_against_existing_per_bar_engine_before_its_time_limit(self):
        s, bars, cutoff = self.setup_path("2024-01-09")
        s["safety"].update(a_price=90, a_index=0, slope=1.)
        known = bars[3].end
        timeline = [{"closedAt": known, "index": 9, "close": 101., "green": s["safety"], "gap": False, "gapAt": None}]
        b = bars[5]
        bars[5] = Bar(b.time, b.end, 100, 101, 98, 100, 1)
        index = PathIndex(bars, cutoff)
        entry = isolated_entry(s, index)
        reference_entry = {**entry, "rules": asdict(ExecutionRules())}
        for model in ("original_safety", "fan_safety"):
            fast = execute_unbounded(s, entry, index, timeline, model)
            old = execute_path(s, reference_entry, bars, timeline, cutoff, 40, model, "hard_stop")
            for key in ("status", "reason", "exitAt", "exitFill", "netPnl", "netR", "mfeR", "maeR"):
                self.assertEqual(fast[key], old[key], key)


class PersistenceTests(unittest.TestCase):
    def test_resume_checks_plan_engine_and_blocks_without_provider_access(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source, metadata, root = base/"source.json", base/"metadata.json", base/"study"
            p = {"symbols": ["TEST"], "datasets": {"TEST": "a"*64}, "folds": {"validation": [
                {"name": "2023", "start": "2023-01-01", "end": "2023-12-31"}]}}
            p["id"] = stable_id(p)
            write(source, p)
            write(metadata, {"sources": {"5m": {"requestedEnd": "2026-10-29T15:25:47+00:00"}}})
            with patch("event_case_study.path_for", return_value=metadata):
                plan = prepare(root, source)
                self.assertEqual(prepare(root, source), plan)
            block = {"planId": plan["id"], "cases": []}
            block["checksum"] = stable_id(block)
            write(root/"stocks"/"TEST.json.gz", block)
            with patch("event_case_study.read_dataset", side_effect=AssertionError("must not reload")):
                self.assertTrue(_work((str(root), plan, "TEST"))["cached"])
            changed = deepcopy(plan)
            changed["execution"]["notional"] *= 2
            with self.assertRaises(DataError):
                checked(changed)
            with patch("event_case_study.binding", return_value={"changed": "engine"}):
                with self.assertRaises(DataError):
                    checked(plan)
            block["cases"] = ["tampered"]
            write(root/"stocks"/"TEST.json.gz", block)
            with self.assertRaises(DataError):
                load_block(root, plan, "TEST")


if __name__ == "__main__":
    unittest.main()
