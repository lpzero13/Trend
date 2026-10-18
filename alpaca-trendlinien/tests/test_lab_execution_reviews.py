import copy
from dataclasses import asdict, replace
import json
import os
import tempfile
import unittest
from unittest.mock import patch

import jobs
from database import connection
from datasets import read_dataset, save_dataset
from lab_execution import simulate, trade_path
from lab_profiles import DEFAULTS
import lab_reviews as reviews
from lab_splits import sessions_between
from models import DataError
from test_lab_data import session
from test_research import fixture_sources


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.options={**DEFAULTS["execution"],"capital":2000,"holding_days":5,"spread_bps":0,"slippage_bps":0,"allocation_fraction":1,"risk_fraction":.1}
        self.days=sessions_between("2025-03-03","2025-03-14")
        self.fine=sum((session(day) for day in self.days),[])
        self.sources={"5m":self.fine,"1h":self.fine,"1D":[],"4h":[]}
        self.entry={"entryAt":self.fine[0].time,"entryPrice":100,"initialStop":98}
        self.cutoff=self.fine[-1].end

    def test_stop_gap_ambiguous_order_target_open_and_time_exit(self):
        self.sources["5m"][1]=replace(self.fine[1],open=95,high=101,low=94,close=100)
        result=trade_path(self.sources,self.entry,self.options,self.cutoff)
        self.assertEqual(result["exitReason"],"stop_gap");self.assertEqual(result["exitFill"],95)
        self.sources["5m"][1]=replace(self.fine[1],open=100,high=105,low=97,close=100)
        result=trade_path(self.sources,self.entry,{**self.options,"exit":"stop_target_time"},self.cutoff)
        self.assertEqual(result["exitReason"],"stop");self.assertTrue(result["intrabarAmbiguous"])
        self.sources["5m"][1]=replace(self.fine[1],open=106,high=107,low=97,close=100)
        result=trade_path(self.sources,self.entry,{**self.options,"exit":"stop_target_time"},self.cutoff)
        self.assertEqual(result["exitReason"],"target_at_open");self.assertEqual(result["exitFill"],104)
        result=trade_path(self.sources,self.entry,{**self.options,"exit":"time"},self.cutoff)
        self.assertEqual(result["exitReason"],"time");self.assertEqual(result["exitAt"],session(self.days[5])[-1].end)

    def test_missing_path_does_not_invent_an_exit_and_later_gaps_do_not_erase_known_stops(self):
        self.sources["5m"]=self.fine[:3]+self.fine[4:]
        self.assertEqual(trade_path(self.sources,self.entry,self.options,self.cutoff)["reason"],"missing_fine_path")
        self.sources["5m"][1]=replace(self.fine[1],low=97)
        self.assertEqual(trade_path(self.sources,self.entry,self.options,self.cutoff)["status"],"closed")
        self.sources["5m"]=self.fine[1:]
        self.assertEqual(trade_path(self.sources,self.entry,self.options,self.cutoff)["status"],"unavailable")
        self.assertEqual(trade_path({"1h":self.fine},self.entry,self.options,self.cutoff)["reason"],"fine_execution_data_required")
        partial=trade_path({**self.sources,"5m":self.fine},self.entry,self.options,self.fine[5].end)
        self.assertEqual(partial["status"],"censored");self.assertIsNone(partial["exitFill"])

    def test_capital_competing_positions_fees_and_future_prices_do_not_choose_entries(self):
        data=lambda symbol:{"id":symbol,"material":{"symbol":symbol,"bars":{tf:[asdict(b) for b in bars] for tf,bars in self.sources.items()}}}
        datasets={s:data(s) for s in ("A","B")}
        datasets["UNUSED"]={"descriptorOnly":True,"id":"z"*64}
        def case(symbol,id):
            return {"id":id,"profile":"reference","datasetId":symbol,"symbol":symbol,"variants":[{**self.entry,"variant":"breakout","status":"observed"}]}
        records=[case("B","b"),case("A","a"),case("A","clone")]
        phase={"startAt":self.fine[0].time,"endAt":self.cutoff}
        options={**self.options,"max_positions":1,"fee_per_order":1,"spread_bps":10,"slippage_bps":10}
        result=simulate(records,datasets,options,phase,profile="reference",family="breakout")
        self.assertEqual(result["summary"]["accepted"],1);self.assertEqual(result["summary"]["skipped"],1)
        self.assertEqual(result["trades"][0]["entry"]["symbol"],"A")
        self.assertEqual(result["trades"][0]["quantity"],19)
        self.assertEqual(result["summary"]["feesPaid"],2)
        self.assertEqual(result["summary"]["executionSourceCachePeak"],1)
        self.assertTrue(all(p["cash"]>=0 for p in result["equity"]))
        changed=copy.deepcopy(datasets)
        for b in changed["B"]["material"]["bars"]["5m"]:
            if b["time"]>self.entry["entryAt"]:b.update(open=500,high=1000,low=400,close=900)
        again=simulate(records,changed,options,phase,profile="reference",family="breakout")
        self.assertEqual(result,again)
        entry=result["trades"][0]
        expected=entry["quantity"]*(entry["path"]["exitFill"]-entry["path"]["entryFill"])-2
        self.assertAlmostEqual(result["summary"]["realizedNetPnl"],expected)


class BlindReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.env=patch.dict(os.environ,{"TORI_DATA_DIR":self.temp.name});self.env.start()
        self.dataset_id=save_dataset("TEST",fixture_sources());self.dataset=read_dataset(self.dataset_id)
        rows=self.dataset["material"]["bars"]["4h"];self.cutoff=rows[900]["end"]
        self.job=jobs.submit({"entry_mode":"lab","symbols":["TEST"],"dataset_ids":{"TEST":self.dataset_id},"lab":{"allow_native":True,"benchmark_symbol":""}})
        phase={"startAt":rows[899]["time"],"endAt":rows[910]["end"]}
        case={"id":"case","profile":"reference","symbol":"TEST","datasetId":self.dataset_id,
              "signal":{"closedAt":self.cutoff},"frozen":{"red":{},"green":{}},
              "variants":[{"variant":"breakout","status":"observed","signalAt":self.cutoff,"availableAt":self.cutoff+900,
                           "checks":[{"name":"context","state":"pass"}],"forward":{"20":{"return_pct":12345}}}]}
        with connection() as db:
            metadata=self.job["manifest"];metadata["temporalPlan"]={"phases":{"development":phase}}
            db.execute("UPDATE jobs SET status='succeeded',universe=?,manifest=? WHERE id=?",(json.dumps(["TEST"]),json.dumps(metadata),self.job["id"]))
            db.execute("INSERT INTO symbols(job_id,symbol,dataset_id,done) VALUES(?,?,?,1)",(self.job["id"],"TEST",self.dataset_id))
            db.execute("INSERT INTO trials VALUES(?,?,?)",(self.job["id"],case["id"],json.dumps(case)))
        self.pack=reviews.create(self.job["id"],count=8,seed=7)

    def tearDown(self):
        self.env.stop();self.temp.cleanup()

    def test_blind_views_cannot_leak_future_bars_engine_decisions_or_outcomes(self):
        for case in self.pack["cases"]:
            view=reviews.view(self.pack["id"],case["id"])
            self.assertNotIn("engine",view);self.assertNotIn("datasetId",view)
            self.assertNotIn("forward",json.dumps(view));self.assertNotIn("12345",json.dumps(view))
            self.assertTrue(all(b["end"]<=view["cutoff"] for bars in view["bars"].values() for b in bars))
            with self.assertRaises(DataError):reviews.reveal(self.pack["id"],case["id"])

    def test_labels_persist_reveal_is_explicit_and_post_reveal_edits_are_excluded(self):
        case=self.pack["cases"][0];identity=case["id"];pack=self.pack["id"]
        value={"entry":"no","red":None,"green":None,"reason":"No convincing confirmation"}
        saved=reviews.label(pack,identity,value)
        self.assertEqual(saved["label"],value);self.assertNotIn("engine",saved)
        revealed=reviews.reveal(pack,identity);self.assertIn("engine",revealed)
        self.assertIn("reviewPath",revealed["engine"])
        self.assertEqual(reviews.compare(pack)["counts"]["compared"],1)
        self.assertFalse(reviews.label(pack,identity,value)["tainted"])
        value["entry"]="yes"
        self.assertTrue(reviews.label(pack,identity,value)["tainted"])
        result=reviews.compare(pack)
        self.assertEqual(result["counts"]["tainted"],1);self.assertEqual(result["counts"]["compared"],0)

    def test_random_case_disclosure_has_hypothetical_path_without_creating_an_engine_trade(self):
        case=next(c for c in self.pack["cases"] if c["cutoff"]==self.cutoff)
        pack=self.pack["id"];before=jobs.get_job(self.job["id"])["completedTrials"]
        reviews.label(pack,case["id"],{"entry":"wait","red":None,"green":None,"reason":"Technical test of future path disclosure"})
        value=reviews.reveal(pack,case["id"])["engine"]["reviewPath"]
        self.assertTrue(value["available"]);self.assertGreater(value["entryAt"],self.cutoff)
        self.assertIsNone(value["initialStop"]);self.assertEqual(set(value["forward"]),{"5","10","20"})
        self.assertEqual(jobs.get_job(self.job["id"])["completedTrials"],before)

    def test_future_anchors_invalid_payloads_and_holdout_reviews_are_rejected(self):
        case=self.pack["cases"][0];pack=self.pack["id"]
        rows=self.dataset["material"]["bars"]["4h"]
        value={"entry":"yes","red":{"a_time":rows[0]["time"],"a_price":100,"b_time":rows[-1]["time"],"b_price":101},"green":None,"reason":"Testing known anchors"}
        with self.assertRaises(DataError):reviews.label(pack,case["id"],value)
        with self.assertRaises(DataError):reviews.label(pack,case["id"],{"entry":"yes"})
        with connection() as db:
            spec=self.job["spec"];spec["lab"]["stage"]="holdout"
            db.execute("UPDATE jobs SET spec=? WHERE id=?",(json.dumps(spec),self.job["id"]))
        with self.assertRaises(DataError):reviews.create(self.job["id"])

    def test_backup_restore_preserves_blind_labels_audit_and_experiment_only_dataset_references(self):
        from pathlib import Path
        from maintenance import backup, verify, restore
        from lab_registry import register, bind_data
        from lab_splits import create
        from research import validate_spec
        from storage import cleanup_preview
        import lab_registry
        identity=self.pack["id"];case=self.pack["cases"][0]["id"]
        judgement={"entry":"wait","red":None,"green":None,"reason":"Saved before outcome disclosure"}
        reviews.label(identity,case,judgement)
        other_id=save_dataset("OTHER",fixture_sources())
        spec=validate_spec({"entry_mode":"lab","symbols":["OTHER"],"lab":{"benchmark_symbol":"","allow_native":True}})
        experiment_id=register(spec,jobs.engine_hash())
        bind_data(experiment_id,{"OTHER":other_id},create([read_dataset(other_id)],spec))
        self.assertEqual(cleanup_preview()["candidates"],[])
        with tempfile.TemporaryDirectory() as parent:
            destination=Path(parent)/"backup";target=Path(parent)/"restored"
            backup(destination);verify(destination);restore(destination,target)
            with patch.dict(os.environ,{"TORI_DATA_DIR":str(target)}):
                value=reviews.view(identity,case)
                self.assertEqual(value["label"],judgement);self.assertNotIn("engine",value)
                self.assertTrue(lab_registry.journal(identity)["pageChainValid"])
                self.assertEqual(lab_registry.get(experiment_id)["datasets"],{"OTHER":other_id})
                self.assertEqual(cleanup_preview()["candidates"],[])


if __name__=="__main__":unittest.main()
