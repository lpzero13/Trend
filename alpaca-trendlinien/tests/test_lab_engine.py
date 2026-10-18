import copy
from dataclasses import asdict, replace
from datetime import datetime
import os
import tempfile
import unittest
from unittest.mock import patch

from datasets import read_dataset, save_dataset
from lab_data import resample_regular, session_bounds
from lab_engine import scan_stock, training_choice
from lab_metrics import OutcomeEvaluator, evaluate, summarize, matched_controls, benchmark_outcomes, blocked_interval
from lab_profiles import LabScanner
from lab_splits import create, walk_folds, member
from models import DataError
from research import validate_spec
from test_lab_data import session
from test_research import fixture_sources
from test_tori_entries import controlled
from tori_entries import EntryScanner


def spec_for(**lab):
    return validate_spec({"entry_mode":"lab","symbols":["TEST"],"lab":{"benchmark_symbol":"",**lab}})


class LabEngineTests(unittest.TestCase):
    def test_contract_validation_and_reference_profile_do_not_change_existing_defaults(self):
        self.assertNotIn("lab",validate_spec({"entry_mode":"tori"}))
        for lab in ({"profiles":[[]]},{"profiles":["reference","baseline"],"variant_budget":1},
                    {"analysis_start":0},{"experiment_id":False},{"benchmark_symbol":0},
                    {"primary_horizon":True},{"primary_family":"future"},
                    {"membership":[{"symbol":"bad","start":"","end":"","source":"x"}]}):
            with self.subTest(lab=lab),self.assertRaises(DataError):spec_for(**lab)
        with self.assertRaises(DataError):validate_spec({"entry_mode":"lab","tori":{"line_policy":"snapshot"}})
        data,spec,plan,lines=controlled();spec["lab"]=spec_for()["lab"]
        old=EntryScanner(data,spec,plan);new=LabScanner(data,spec,plan,"reference")
        context=lambda at:{"daily":{"closedAt":None,"red":None,"green":None},"structure":{"1D":"up","1W":"unknown","1M":"unknown"}}
        old.context=new.context=context
        with patch("tori_entries.pair",return_value=lines),patch("lab_profiles.pair",return_value=lines),patch("tori_entries.contact_count",return_value=2):
            old.advance(35);new.advance(35)
        entries=lambda s:[(e["variant"],e["status"],e.get("entryAt"),e.get("entryPrice"),e.get("reason")) for c in s.cases.values() for e in c["variants"]]
        self.assertEqual(entries(old),entries(new))
        self.assertTrue(any(v[1]=="observed" for v in entries(new)))

    def test_retest_confirmation_can_differ_without_weakening_breakout_or_mutating_shared_checks(self):
        data,spec,plan,lines=controlled();spec["lab"]=spec_for()["lab"]
        from tori_entries import check
        checks=[check("body_atr",False,.05),check("retest_held",True),check("room",None,{"r":None,"resistance":None},False)]
        case={"id":"case","frozen":{"green":lines["green"].output(data["material"]["bars"]["4h"][30]["time"]),"red":lines["red"].output(data["material"]["bars"]["4h"][30]["time"])}}
        strict=LabScanner(data,spec,plan,"reference");alternative=LabScanner(data,spec,plan,"retest_hold")
        a={"variant":"retest","status":"pending","phase":"retest"};b=copy.deepcopy(a)
        strict.confirm(case,a,31,checks,1);alternative.confirm(case,b,31,checks,1)
        self.assertEqual(a["phase"],"retest");self.assertEqual(b["phase"],"execution")
        self.assertTrue(checks[0]["required"])
        direct={"variant":"breakout","status":"pending","phase":"breakout"}
        alternative.confirm(case,direct,31,checks,1)
        self.assertEqual(direct["status"],"rejected")
        room=LabScanner(data,spec,plan,"room")
        self.assertIn("room",room.blocked([check("room",None,{"r":None,"resistance":None},False)]))

    def test_historical_membership_is_inclusive_and_unsupported_dates_are_not_assumed_eligible(self):
        from models import NY
        lab=spec_for(membership=[{"symbol":"TEST","start":"2025-03-03","end":"2025-03-07","source":"synthetic IPO/delisting boundaries"}])["lab"]
        stamp=lambda day:int(datetime.fromisoformat(day).replace(hour=12,tzinfo=NY).timestamp())
        self.assertFalse(member("TEST",stamp("2025-02-28"),lab))
        self.assertTrue(member("TEST",stamp("2025-03-03"),lab));self.assertTrue(member("TEST",stamp("2025-03-07"),lab))
        self.assertFalse(member("TEST",stamp("2025-03-10"),lab));self.assertFalse(member("OTHER",stamp("2025-03-05"),lab))

    def test_controls_are_reproducible_without_selecting_future_winners_and_missing_benchmark_clock_stays_missing(self):
        source=fixture_sources();dataset={"id":"a"*64,"material":{"bars":{tf:[asdict(b) for b in rows] for tf,(rows,_) in source.items()}}}
        spec=spec_for();bars=source["4h"][0]
        point={"entryAt":bars[1100].time,"entryPrice":bars[1100].open}
        phase={"startAt":bars[1000].time,"endAt":bars[1200].end,"labelEndAt":bars[1200].end}
        def output(sign):
            return lambda dataset,entry,horizons,cutoff:{str(h):{"complete":True,"return_pct":sign*entry["entryAt"]} for h in horizons}
        with patch("lab_metrics.evaluate",side_effect=output(1)):a=matched_controls(dataset,point,phase,spec)
        with patch("lab_metrics.evaluate",side_effect=output(-1)):b=matched_controls(dataset,point,phase,spec)
        self.assertTrue(a);self.assertEqual([v["entryAt"] for v in a],[v["entryAt"] for v in b])
        missing=benchmark_outcomes(dataset,{**point,"entryAt":point["entryAt"]+1},[5],phase["endAt"])
        self.assertEqual(missing["5"]["reason"],"benchmark_clock_missing")
        sample=[{"symbol":"TEST","entryAt":bars[i].time,"metric":i} for i in (100,300,500,700)]
        self.assertEqual(blocked_interval(sample,"metric",samples=50),blocked_interval(sample,"metric",samples=50))
        self.assertIsNone(blocked_interval(sample[:1],"metric",samples=50)["low"])

    def test_full_scans_are_stable_distinct_by_profile_and_immune_to_future_changes(self):
        data,old,plan,lines=controlled();spec=spec_for(profiles=["baseline","reference"])
        spec["tori"]={**old["tori"],"line_policy":"tracked"}
        bars=data["material"]["bars"]["4h"]
        phase={"startAt":bars[30]["time"],"endAt":bars[35]["end"],"labelEndAt":bars[35]["end"]}
        def run(dataset):
            rows={};events={}
            def emit(item):
                if "trial" in item:rows[item["trial"]["id"]]=item["trial"]
                else:events[item["event"]["id"]]=item["event"]
            with patch("lab_profiles.pair",return_value=lines),patch("tori_entries.pair",return_value=lines),patch("tori_entries.contact_count",return_value=2):
                result=scan_stock(dataset,spec,phase,emit=emit)
            return result,rows,events
        first,rows,events=run(data)
        self.assertTrue(first["complete"]);self.assertEqual({r["profile"] for r in rows.values()},{"reference","baseline"})
        self.assertEqual(len(rows),2)
        self.assertLessEqual(first["geometryCachePeak"],len(spec["lab"]["profiles"]))
        self.assertEqual({e["profile"] for e in events.values()},{"reference","baseline"})
        shocked=copy.deepcopy(data)
        for source in shocked["material"]["bars"].values():
            for row in source:
                if row["time"]>=phase["endAt"]:row.update(open=500,close=600,high=700,low=.01)
        self.assertEqual((first,rows,events),run(shocked))
        self.assertEqual((first,rows,events),run(data))

    def test_temporal_boundaries_are_common_and_walk_selection_has_no_future_labels(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{"TORI_DATA_DIR":folder}):
            a=read_dataset(save_dataset("TEST",fixture_sources()));b=copy.deepcopy(a);b["id"]="b"*64;b["material"]["symbol"]="OTHER"
            spec=spec_for(walk_train_sessions=40,walk_test_sessions=20,min_train_events=2)
            plan=create([a,b],spec)
        phases=list(plan["phases"].values())
        self.assertTrue(all(left["endAt"]<right["startAt"] for left,right in zip(phases,phases[1:])))
        folds=walk_folds(plan,spec["lab"]);self.assertTrue(folds)
        for fold in folds:
            self.assertLess(fold["training"]["labelEndAt"],fold["evaluation"]["startAt"])
            self.assertLess(fold["evaluation"]["endAt"],plan["phases"]["holdout"]["startAt"])
        def case(profile,at,value,complete=True,family="breakout"):
            return {"profile":profile,"datasetId":"a","variants":[{"variant":family,"status":"observed","entryAt":at,"forward":{"10":{"complete":complete,"return_pct":value}},"controls":[{"forward":{"10":{"complete":True,"return_pct":1}}}]}]}
        training=[case("reference",1,3),case("reference",2,3),case("baseline",1,2),case("baseline",2,2),case("baseline",3,1000,False),case("baseline",4,1000,True,"retest")]
        choice=training_choice(training,spec)
        self.assertEqual(choice["profile"],"reference");self.assertEqual(choice["scores"]["baseline"]["n"],2)

    def test_phase_replay_preserves_expired_setup_identities_and_does_not_rearm_old_lines(self):
        data,old,plan,lines=controlled();spec=spec_for(profiles=["baseline"])
        spec["tori"]={**old["tori"],"line_policy":"tracked","setup_bars":5}
        bars=data["material"]["bars"]["4h"]
        phase={"startAt":bars[30]["time"],"endAt":bars[35]["end"],"labelEndAt":bars[35]["end"],"historyStartAt":bars[1]["time"]}
        records={}
        def save(item):
            if "trial" in item:records[item["trial"]["id"]]=item["trial"]
        with patch("lab_profiles.pair",return_value=lines),patch("tori_entries.pair",return_value=lines),patch("tori_entries.contact_count",return_value=2):
            result=scan_stock(data,spec,phase,emit=save)
        self.assertTrue(result["complete"])
        self.assertEqual(len(records),1)
        self.assertFalse(any(e["status"]=="observed" for c in records.values() for e in c["variants"]))
        self.assertEqual(result["profiles"]["baseline"]["warmupCandles"],29)

    def test_red_break_without_safety_is_retained_as_rejected_not_silently_lost(self):
        data,old,plan,lines=controlled();spec=spec_for(profiles=["reference"])
        spec["tori"]={**old["tori"],"line_policy":"tracked"};lines["green"]=None
        bars=data["material"]["bars"]["4h"]
        phase={"startAt":bars[30]["time"],"endAt":bars[35]["end"],"labelEndAt":bars[35]["end"]}
        records={}
        def save(item):
            if "trial" in item:records[item["trial"]["id"]]=item["trial"]
        with patch("lab_profiles.pair",return_value=lines),patch("tori_entries.pair",return_value=lines):
            result=scan_stock(data,spec,phase,emit=save)
        self.assertTrue(result["complete"])
        self.assertGreater(result["profiles"]["reference"]["withoutGreen"],0)
        self.assertTrue(records)
        entry=next(iter(records.values()))["variants"][0]
        self.assertEqual(entry["status"],"rejected");self.assertEqual(entry["reason"],"missing_safety")
        self.assertIn("hypothetical",entry);self.assertIsNone(entry["hypothetical"]["initialStop"])

    def test_path_uses_only_post_entry_bars_and_marks_missing_or_cut_off_sessions(self):
        from lab_splits import sessions_between
        days=sessions_between("2025-03-03","2025-03-21")
        fine=sum((session(d,100+i) for i,d in enumerate(days)),[])
        at=session_bounds(days[0])[0]+3600
        fine[0]=replace(fine[0],high=999,low=.01)
        sources,_=resample_regular(fine)
        dataset={"id":"d"*64,"material":{"bars":{tf:[asdict(b) for b in rows] for tf,rows in sources.items()}}}
        point={"entryAt":at,"entryPrice":100,"initialStop":98}
        ev=OutcomeEvaluator(dataset);cutoff=session_bounds(days[-1])[1]
        result=ev.evaluate(point,[5,10,20],cutoff)
        self.assertTrue(result["5"]["pathComplete"])
        self.assertLess(result["5"]["mfe_pct"],10);self.assertGreater(result["5"]["mae_pct"],-10)
        self.assertFalse(result["20"]["complete"])
        self.assertEqual(result,evaluate(dataset,point,[5,10,20],cutoff))
        limited=ev.evaluate(point,[5],session_bounds(days[3])[1])
        self.assertFalse(limited["5"]["complete"])
        missing=copy.deepcopy(dataset);missing["material"]["bars"]["5m"].pop(25)
        self.assertFalse(evaluate(missing,point,[5],cutoff)["5"]["pathComplete"])
        missing["material"]["bars"]["1D"].pop(2)
        self.assertEqual(evaluate(missing,point,[5],cutoff)["5"]["reason"],"missing_daily_sessions")

    def test_diagnostics_dedupe_cohorts_and_path_coverage_are_explicit(self):
        point={"variant":"breakout","status":"observed","quality":"provisional","entryAt":1,"entryPrice":100,
               "signalAt":0,"checks":[{"name":"line_age","state":"fail","value":4,"required":True}],
               "forward":{"5":{"complete":True,"closedAt":100,"return_pct":2,"pathComplete":False,"mfe_pct":1000,"mae_pct":-99}}}
        one={"profile":"reference","datasetId":"a","symbol":"TEST","variants":[point]}
        clone=copy.deepcopy(one);second=copy.deepcopy(one);second["variants"][0]["entryAt"]=50
        result=summarize([one,clone,second],[5])
        group=next(iter(result["groups"].values()));h=group["horizons"]["5"]
        self.assertEqual(group["rawRecords"],3);self.assertEqual(group["uniqueEntries"],2)
        self.assertIsNone(h["mean_mfe_pct"]);self.assertEqual(h["dependence"]["sameStockEpisodes"],1)
        self.assertEqual(h["dependence"]["sameStockOverlappingEntries"],1)
        self.assertEqual(result["diagnostics"]["reference"]["soleBlocker"]["line_age"],1)
        self.assertTrue(any(k.endswith("age_days|under7") for k in result["cohorts"]))


if __name__=="__main__":unittest.main()
