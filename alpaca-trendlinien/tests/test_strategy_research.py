from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from models import DataError
from safety_strategy import StrategyContext, strategy_path
from strategy_cli import timestamp
from strategy_portfolio import simulate
from strategy_research import run_study, RAW_COSTS, engine_hashes
from strategy_research import scan_candidates
from lab_data import NORMALIZATION
from models import Bar
from types import SimpleNamespace
from strategy_verify import audit_contract, audit_path, audit_portfolio
import test_safety_strategy as fixtures


class StrategyResearchTests(unittest.TestCase):
    def setUp(self):
        fixture = fixtures.SafetyStrategyTests()
        fixture.setUp()
        self.fixture = fixture
        self.entry = {**fixture.entry, "symbol": "TEST", "profile": "baseline", "family": "breakout", "datasetId": "dataset"}
        self.contract = fixture.source.entry_contract(self.entry, RAW_COSTS)
        self.path = strategy_path(fixture.source, self.entry, self.contract, "original", 5)
        self.sources = {"dataset": {**fixture.frames, "5m_map": {b.time: b for b in fixture.frames["5m"]}}}
        self.phase = {"startAt": self.entry["entryAt"], "endAt": self.path["exitAt"]}

    def test_independent_oracles_and_mutated_money_target_and_eligibility(self):
        audit_contract(self.entry, self.contract, self.fixture.frames, self.fixture.source.rules, {})
        audit_path(self.entry, self.contract, self.path, self.sources["dataset"], self.fixture.source.rules, self.fixture.source.cutoff, {})
        for field in ("netPnl", "entryFill", "exitFill"):
            damaged = deepcopy(self.path)
            damaged[field] += 1
            with self.subTest(field=field), self.assertRaises(AssertionError):
                audit_path(self.entry, self.contract, damaged, self.sources["dataset"], self.fixture.source.rules, self.fixture.source.cutoff, {})
        damaged = deepcopy(self.contract)
        damaged["eligible"] = not damaged["eligible"]
        with self.assertRaises(AssertionError):
            audit_contract(self.entry, damaged, self.fixture.frames, self.fixture.source.rules, {})

    def test_cash_risk_constraints_duplicate_symbol_and_independent_ledger(self):
        second = {**self.entry, "id": "second"}
        paths = [self.path, {**self.path, "entryId": "second"}]
        portfolio = simulate([self.entry, second], paths, {"dataset": self.fixture.source}, self.phase, RAW_COSTS)
        self.assertEqual(portfolio["accepted"], 1)
        self.assertEqual(portfolio["skipped"][0]["reason"], "already_holding_symbol")
        trade = portfolio["trades"][0]
        self.assertLessEqual(trade["plannedRiskUSD"], 20)
        self.assertLessEqual(trade["quantity"]*trade["entryFill"], 500)
        self.assertTrue(all(p["cash"] >= 0 for p in portfolio["equity"]))
        audit_portfolio(portfolio, [self.entry, second], paths, self.sources, self.phase, RAW_COSTS)
        damaged = deepcopy(portfolio)
        damaged["cash"] += 1
        with self.assertRaises(AssertionError):
            audit_portfolio(damaged, [self.entry, second], paths, self.sources, self.phase, RAW_COSTS)

    def test_missing_held_path_halts_without_using_later_profit_to_skip_purchase(self):
        censored = {**self.path, "status": "censored", "exitAt": None, "exitFill": None,
                    "reason": "missing_fine_path", "missingAt": self.entry["entryAt"]+600}
        portfolio = simulate([self.entry], [censored], {"dataset": self.fixture.source}, self.phase, RAW_COSTS)
        self.assertEqual(portfolio["accepted"], 1)
        self.assertEqual(portfolio["status"], "incomplete")
        self.assertEqual(portfolio["observedThrough"], censored["missingAt"])
        self.assertIsNone(portfolio["markedReturnPct"])
        audit_portfolio(portfolio, [self.entry], [censored], self.sources, self.phase, RAW_COSTS)

    def test_no_position_releases_cash_at_fine_bar_open(self):
        # A first-bar exit at its open releases capital only when that fine bar
        # ends. An entry in the same bar cannot spend that money.
        first = {**self.path, "exitAt": self.entry["entryAt"]+300, "fillBarAt": self.entry["entryAt"], "atOpen": True}
        b = {**self.entry, "id": "b", "symbol": "ZZZ"}
        result = simulate([self.entry,b], [first,{**first,"entryId":"b"}], {"dataset":self.fixture.source}, self.phase, RAW_COSTS,
                          {"capital":2000,"allocation_fraction":1,"risk_fraction":.25,"max_positions":1})
        self.assertEqual(result["accepted"],1)
        self.assertEqual(result["skipped"][0]["reason"],"max_positions")

    def test_cli_dates_require_timezone_and_reserved_phase_rejected(self):
        self.assertEqual(timestamp("2026-10-20T12:00:00Z"), timestamp("2026-10-20T14:00:00+02:00"))
        with self.assertRaises(DataError):
            timestamp("2026-10-20")
        with self.assertRaises(DataError):
            run_study("does-not-exist", "unused", "holdout")

    def test_experiment_contract_phase_gate_and_engine_mismatch(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            source = root/"entries.json"
            source.write_text(json.dumps({"cohorts":{"development":[],"validation":[]},"phases":{"development":self.phase,"validation":self.phase}}),"utf-8")
            output = root/"study"
            with self.assertRaises(DataError):
                run_study(source, output, "validation")
            result = run_study(source, output)
            self.assertEqual(result["paths"], 0)
            self.assertTrue((output/"decision-before-validation.json").exists())
            with self.assertRaises(DataError):
                run_study(source, output)
            with patch("strategy_research.engine_hashes", return_value={"changed":"new"}):
                with self.assertRaises(DataError):
                    run_study(source, output, "validation")
            self.assertEqual(run_study(source, output, "validation")["entries"], 0)

    def test_candidate_scan_trims_future_input_and_never_calls_outcome_evaluator(self):
        cutoff = self.entry["entryAt"]+1800
        frames = deepcopy(self.fixture.frames)
        first = frames["4h"][0]
        old = first.time-366*86400
        frames["4h"].insert(0, Bar(old,old+14400,100,101,99,100,1))
        entry = deepcopy(self.entry)
        for side in ("red","green"):
            entry[side]["a_index"] += 1
            entry[side]["b_index"] += 1
        variant = {**entry,"status":"observed","variant":"breakout","quality":"provisional"}
        case = {"id":"setup","symbol":"TEST","datasetId":"a"*64,"startAt":entry["signalAt"]-300,"frozen":{k:entry[k] for k in ("red","green")},"variants":[variant]}
        data = {"id":"a"*64,"material":{"symbol":"TEST","dataKind":"synthetic","feed":"iex","adjustment":"split",
                 "normalization":{tf:NORMALIZATION for tf in frames},"bars":{tf:[asdict(b) for b in rows] for tf,rows in frames.items()}}}
        def scanner(dataset,*args,**kwargs):
            self.assertTrue(all(b["end"]<=cutoff for rows in dataset["material"]["bars"].values() for b in rows))
            return SimpleNamespace(cases={"setup":deepcopy(case)},advance=lambda *a:None,executions=lambda *a:None)
        with patch("lab_profiles.LabScanner",side_effect=scanner),patch("lab_engine.OutcomeEvaluator",side_effect=AssertionError("No future outcome evaluation allowed")):
            first = scan_candidates(data,cutoff,"baseline",since=self.entry["entryAt"])
            changed=deepcopy(data)
            for rows in changed["material"]["bars"].values():
                for row in rows:
                    if row["time"]>=cutoff:row.update(open=999,high=1000,low=.01,close=500)
            second=scan_candidates(changed,cutoff,"baseline",since=self.entry["entryAt"])
        self.assertEqual(first,second)
        self.assertEqual(first["dataKind"],"synthetic")
        self.assertEqual(len(first["observations"]),1)
        self.assertIsNone(first["observations"][0]["brokerAction"])

    def test_portfolio_sizes_including_both_fees_and_selling_friction(self):
        costs={**RAW_COSTS,"fee_per_order":1}
        contract=self.fixture.source.entry_contract(self.entry,costs)
        path=strategy_path(self.fixture.source,self.entry,contract,"fixed",5)
        result=simulate([self.entry],[path],{"dataset":self.fixture.source},self.phase,costs)
        self.assertLessEqual(result["trades"][0]["plannedRiskUSD"],20)
        audit_portfolio(result,[self.entry],[path],self.sources,self.phase,costs)


if __name__ == "__main__":
    unittest.main()
