"""Controlled causal counterexamples, not empirical market evidence."""
from copy import deepcopy
from dataclasses import replace
import unittest

import test_safety_strategy as fixtures
from exit_research import horizon_close
from lab_data import resample_regular
from safety_strategy import StrategyContext
from retest_exits import contract_for
from retest_variants import path, execution_open, stats
from tools.retest_variant_verify import audit_variant


class VariantTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.SafetyStrategyTests()
        self.f.setUp()
        self.entry={**self.f.entry,"rawSafety":self.f.entry["initialStop"],
                    "initialStop":self.f.contract["initialStop"],"signalWidth":.2}

    def context(self, changes=None):
        fine=list(self.f.fine)
        for stamp,values in (changes or {}).items():
            i=next(i for i,b in enumerate(fine) if b.time == stamp)
            fine[i]=replace(fine[i],**values)
        return StrategyContext(resample_regular(fine)[0],fine[-1].end)

    def run_path(self, model, source=None, costs=None):
        source=source or self.f.source
        contract=contract_for(source,self.entry,costs or {"spread_bps":5,"slippage_bps":5})
        return path(source,self.entry,contract,model)

    def test_failed_retest_uses_original_zone_and_later_open(self):
        known=self.f.four[20].end
        source=self.context({known-300:{"close":98.7,"low":98.7}})
        original=deepcopy(self.entry["red"])
        actual=self.run_path("failed_retest",source)
        self.assertEqual(actual["exitReason"],"failed_retest")
        self.assertEqual(actual["fillBarAt"],known+300)
        self.assertEqual(actual["events"][0]["knownAt"],known)
        self.assertEqual(actual["exitPrice"],100)
        self.assertEqual(self.entry["red"],original)
        self.assertEqual(self.run_path("fixed",source)["exitReason"],"time")

    def test_wick_or_close_inside_zone_does_not_fail_retest(self):
        known=self.f.four[20].end
        source=self.context({known-300:{"close":98.9,"low":98.6}})
        self.assertEqual(self.run_path("failed_retest",source)["exitReason"],"time")

    def test_old_safety_remains_active_during_failure_exit_latency(self):
        known=self.f.four[20].end
        source=self.context({known-300:{"close":98.7,"low":98.7},known:{"low":98}})
        actual=self.run_path("failed_retest",source)
        self.assertEqual(actual["exitReason"],"hard_stop")
        self.assertEqual(actual["fillBarAt"],known)

    def test_failure_at_session_close_waits_until_next_regular_open(self):
        known=self.f.four[21].end
        source=self.context({known-300:{"close":98.6,"low":98.6}})
        actual=self.run_path("failed_retest",source)
        self.assertEqual(actual["fillBarAt"],execution_open(known))
        self.assertGreater(actual["fillBarAt"]-known,3600)

    def test_fifth_session_uses_net_costs_and_never_fills_same_close(self):
        known=horizon_close(self.entry["entryAt"],5)
        source=self.context({known-300:{"close":100.05}})
        actual=self.run_path("time_no_progress",source)
        self.assertEqual(actual["exitReason"],"time_no_progress")
        self.assertEqual(actual["fillBarAt"],execution_open(known))
        self.assertLess(actual["events"][0]["netPnl"],0)
        self.assertGreater(actual["fillBarAt"],known)

    def test_positive_fifth_session_continues_to_original_tenth_limit(self):
        actual=self.run_path("time_no_progress")
        self.assertEqual(actual["exitReason"],"time")
        self.assertEqual(actual["exitAt"],horizon_close(self.entry["entryAt"],10))
        self.assertFalse(actual["events"][0]["exit"])

    def test_exactly_zero_net_progress_is_an_exit(self):
        known=horizon_close(self.entry["entryAt"],5)
        source=self.context({known-300:{"close":100}})
        actual=self.run_path("time_no_progress",source,{"spread_bps":0,"slippage_bps":0})
        self.assertEqual(actual["events"][0]["netPnl"],0)
        self.assertTrue(actual["events"][0]["exit"])

    def test_activation_needs_close_not_intrabar_high(self):
        known=self.f.four[20].end
        source=self.context({known-300:{"high":108}})
        actual=self.run_path("atr_gain_stop",source)
        self.assertFalse(any(e["kind"] == "gain_activate" for e in actual["events"]))
        self.assertEqual(actual["exitReason"],"time")

    def test_atr_stop_not_applied_to_confirmation_or_latency_bar(self):
        known=self.f.four[20].end
        source=self.context({known-300:{"close":104,"high":104.1,"low":103.9}})
        actual=self.run_path("atr_gain_stop",source)
        raised=next(e for e in actual["events"] if e["kind"] == "atr_stop_raise")
        self.assertEqual(raised["knownAt"],known)
        self.assertEqual(actual["fillBarAt"],known+300)
        self.assertEqual(actual["exitReason"],"hard_stop")
        self.assertGreater(raised["hardStop"],self.entry["initialStop"])
        self.assertEqual(actual["exitPrice"],raised["hardStop"])

    def test_new_stop_above_open_fills_open_and_can_never_loosen(self):
        known=self.f.four[20].end
        source=self.context({known-300:{"close":106,"high":106.1,"low":105.9}})
        actual=self.run_path("atr_gain_stop",source)
        self.assertEqual(actual["exitReason"],"hard_stop_gap")
        self.assertEqual(actual["exitPrice"],100)
        self.assertGreater(actual["finalHardStop"],actual["exitPrice"])
        self.assertTrue(all(e["hardStop"] >= e["previousHardStop"] for e in actual["events"] if "hardStop" in e))

    def test_missing_source_cannot_be_silently_skipped_but_time_rule_is_independent(self):
        source=deepcopy(self.f.source)
        source.four.pop(20)
        for model in ("failed_retest","atr_gain_stop"):
            # Contract frozen before the missing post-entry source bar.
            actual=path(source,self.entry,self.f.contract,model)
            self.assertEqual(actual["reason"],"missing_source_path")
            self.assertEqual(actual["status"],"censored")
        self.assertEqual(path(source,self.entry,self.f.contract,"time_no_progress")["exitReason"],"time")

    def test_missing_fine_bar_and_unavailable_entry_do_not_become_wins(self):
        source=deepcopy(self.f.source)
        k=source.times.index(self.entry["entryAt"])+1
        source.fine.pop(k)
        source.times.pop(k)
        for model in ("failed_retest","time_no_progress","atr_gain_stop"):
            actual=path(source,self.entry,self.f.contract,model)
            self.assertEqual(actual["reason"],"missing_fine_path")
            invalid=path(self.f.source,{**self.entry,"availableAt":self.entry["entryAt"]+300},self.f.contract,model)
            self.assertEqual(invalid["status"],"invalid")

    def test_future_prices_do_not_change_earlier_paths(self):
        changed=deepcopy(self.f.source)
        cutoff=horizon_close(self.entry["entryAt"],10)
        for name in ("fine","four"):
            setattr(changed,name,[replace(b,open=500,high=1000,low=.01,close=900) if b.time >= cutoff else b for b in getattr(changed,name)])
        for model in ("failed_retest","time_no_progress","atr_gain_stop"):
            self.assertEqual(self.run_path(model),self.run_path(model,changed))

    def test_mixed_decision_events_are_not_miscounted_as_stop_raises(self):
        result=stats([{"status":"censored","events":[{"kind":"gain_activate"},
            {"kind":"atr_stop_raise","previousHardStop":90,"hardStop":91}]}])
        self.assertEqual(result["stopRaises"],1)
        self.assertEqual(result["eventCounts"]["gain_activate"],1)

    def test_independent_oracle_checks_events_and_rejects_wrong_knowledge_time(self):
        known=self.f.four[20].end
        progress=horizon_close(self.entry["entryAt"],5)
        examples={"failed_retest":{known-300:{"close":98.7,"low":98.7}},
                  "time_no_progress":{progress-300:{"close":100.05}},
                  "atr_gain_stop":{known-300:{"close":104,"high":104.1,"low":103.9}}}
        for model,changes in examples.items():
            source=self.context(changes)
            contract=contract_for(source,self.entry,{"spread_bps":5,"slippage_bps":5})
            actual=path(source,self.entry,contract,model)
            record={"entry":self.entry,"contract":contract,"paths":{model:actual}}
            audit_variant(record,source.sources,source.cutoff,model)
            broken=deepcopy(record)
            broken["paths"][model]["events"][0]["knownAt"]-=300
            with self.assertRaises(AssertionError):
                audit_variant(broken,source.sources,source.cutoff,model)

    def test_independent_oracle_confirms_missing_source_is_unknown(self):
        source=deepcopy(self.f.source)
        source.four.pop(20)
        actual=path(source,self.entry,self.f.contract,"failed_retest")
        record={"entry":self.entry,"contract":self.f.contract,"paths":{"failed_retest":actual}}
        audit_variant(record,source.sources,source.cutoff,"failed_retest")


if __name__ == "__main__":
    unittest.main()
