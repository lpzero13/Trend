import copy
from dataclasses import asdict, replace
from datetime import datetime
import os
import tempfile
import threading
import unittest
from unittest.mock import patch

import jobs
from datasets import read_dataset, save_dataset
from market_calendar import calendar, session_close
from models import Bar, DataError, NY
from research import validate_spec, trial_plan
from test_research import fixture_sources
from tori_observations import forward_closes, observe_cases, sample_windows, summarize_observations
import test_tori_entries as entry_tests


def stamp(day, hour=10):
    return int(datetime.fromisoformat(day).replace(hour=hour, tzinfo=NY).timestamp())


def daily_rows():
    return [Bar(stamp(str(s.date()),0),session_close(str(s.date())),100,120,90,100+i,1)
            for i,s in enumerate(calendar(2025).sessions_in_range("2025-01-01","2025-04-01"))]


def case(at, price=100, name="retest", dataset="a"*64):
    return {"datasetId":dataset,"symbol":"TEST","variants":[{"variant":name,"group":name+"_provisional",
            "status":"observed","entryAt":at,"entryPrice":price}]}


class ToriObservationTests(unittest.TestCase):
    def test_same_anchors_in_different_windows_keep_distinct_records(self):
        helper=entry_tests.ToriEntryTests()
        a,_,lines=helper.scanner();b,_,_=helper.scanner()
        a.plan["windowId"]="first";b.plan["windowId"]="second"
        helper.run_controlled(a,lines);helper.run_controlled(b,lines)
        self.assertTrue(set(a.cases).isdisjoint(b.cases))
        self.assertEqual(next(iter(a.cases.values()))["frozen"],next(iter(b.cases.values()))["frozen"])

    def test_future_close_changes_observation_but_not_any_entry_decision(self):
        helper=entry_tests.ToriEntryTests()
        scanner,_,lines=helper.scanner()
        helper.run_controlled(scanner,lines);scanner.finish()
        before=copy.deepcopy(list(scanner.cases.values()))
        entry_at=next(v["entryAt"] for c in before for v in c["variants"] if v["status"]=="observed")
        date=datetime.fromtimestamp(entry_at,NY).date()
        rows=daily_rows()
        dataset={"material":{"bars":{"1D":[asdict(b) for b in rows]}}}
        a,b=copy.deepcopy(before),copy.deepcopy(before)
        observe_cases(a,dataset,{"horizons":[5]}, {"observation_end":stamp("2025-04-02")})
        for row in dataset["material"]["bars"]["1D"]:
            if datetime.fromtimestamp(row["time"],NY).date()>date: row["close"]*=2
        observe_cases(b,dataset,{"horizons":[5]}, {"observation_end":stamp("2025-04-02")})
        self.assertNotEqual(a,b)
        for c in a+b:
            for v in c["variants"]:
                v.pop("forward",None);v.pop("observationSelected",None)
        self.assertEqual(a,b)
        self.assertEqual(a,before)

    def test_horizons_follow_calendar_not_present_bars_and_skip_holiday(self):
        rows=daily_rows()
        # Friday before MLK Day: first session is Tuesday, fifth is Monday 27th.
        result=forward_closes(rows,stamp("2025-01-17"),100,[1,5,10,20],stamp("2025-04-02"))
        self.assertEqual(result["1"]["targetDate"],"2025-01-21")
        self.assertEqual(result["5"]["targetDate"],"2025-01-27")
        close=next(b.close for b in rows if b.end==result["5"]["closedAt"])
        self.assertAlmostEqual(result["5"]["return_pct"],close-100)
        missing=forward_closes([b for b in rows if b.time!=stamp("2025-01-22",0)],stamp("2025-01-17"),100,[5],stamp("2025-04-02"))["5"]
        self.assertFalse(missing["complete"])
        self.assertEqual(missing["targetDate"],"2025-01-27")
        self.assertEqual(missing["missingDates"],["2025-01-22"])

    def test_holdout_never_supplies_an_observation(self):
        r=forward_closes(daily_rows(),stamp("2025-01-17"),100,[1,5],session_close("2025-01-21"))
        self.assertTrue(r["1"]["complete"])
        self.assertFalse(r["5"]["complete"])
        self.assertNotIn("close",r["5"])
        rows=[replace(b,close=99999) if b.end>session_close("2025-01-21") else b for b in daily_rows()]
        self.assertEqual(r,forward_closes(rows,stamp("2025-01-17"),100,[1,5],session_close("2025-01-21")))

    def test_only_closes_not_entry_day_range_or_costs_are_observed(self):
        rows=daily_rows()
        a=forward_closes(rows,stamp("2025-01-17",15),100,[5],stamp("2025-04-02"))
        changed=[replace(b,high=999999,low=.001) for b in rows]
        self.assertEqual(a,forward_closes(changed,stamp("2025-01-17",15),100,[5],stamp("2025-04-02")))
        self.assertEqual(set(a["5"]),{"complete","targetDate","targetCloseAt","closedAt","unit","close","return_pct"})

    def test_large_horizon_crosses_calendar_years(self):
        r=forward_closes([],stamp("2025-12-29"),100,[250],stamp("2028-01-01"))
        self.assertEqual(r["250"]["reason"],"missing_daily_sessions")
        self.assertTrue(r["250"]["targetDate"].startswith("2026"))

    def test_random_windows_repeat_and_ignore_all_prices(self):
        bars=[Bar(i*14400,(i+1)*14400,100,101,99,100,1) for i in range(400)]
        spec=validate_spec({"entry_mode":"tori","samples":5,"search_bars":30,"tori":{"sampling":"random"}})
        a=sample_windows(bars,10,399,spec,"TEST")
        b=sample_windows([replace(b,close=999,high=1000) for b in bars],10,399,spec,"TEST")
        self.assertEqual(a,b)
        self.assertEqual(a["actual_samples"],5)
        for x,y in zip(a["windows"],a["windows"][1:]):
            self.assertLess(x["discovery_end"],y["scan_start"])
        self.assertNotEqual(a,sample_windows(bars,10,399,{**spec,"seed":2},"TEST"))
        small=sample_windows(bars,10,39,spec,"TEST")
        self.assertEqual(small["actual_samples"],1)
        with self.assertRaises(DataError): sample_windows(bars,10,20,spec,"TEST")

    def test_first_entry_per_variant_and_ties_not_later_entries_selected(self):
        cases=[case(stamp("2025-01-17")),case(stamp("2025-01-21")),case(stamp("2025-01-17")),case(stamp("2025-01-21"),name="horizontal")]
        dataset={"material":{"bars":{"1D":[asdict(b) for b in daily_rows()]}}}
        spec={"horizons":[5]}
        observe_cases(cases,dataset,spec,{"observation_end":stamp("2025-04-02")},random_window=True)
        self.assertEqual([c["variants"][0]["observationSelected"] for c in cases],[True,False,True,True])
        self.assertNotIn("forward",cases[1]["variants"][0])
        r=summarize_observations(cases,[5])
        self.assertEqual(r["groups"]["retest_provisional"]["uniqueEntries"],1)
        self.assertEqual(r["groups"]["retest_provisional"]["horizons"]["5"]["n"],1)
        self.assertEqual(r["uniqueEntriesAcrossVariants"],2)

    def test_summaries_separate_incomplete_and_flag_overlap(self):
        rows=daily_rows(); cases=[case(stamp(d)) for d in ("2025-01-17","2025-01-21","2025-03-31")]
        for c in cases:
            v=c["variants"][0];v["observationSelected"]=True
            v["forward"]=forward_closes(rows,v["entryAt"],100,[5],stamp("2025-04-02"))
        r=summarize_observations(cases,[5])["groups"]["retest_provisional"]["horizons"]["5"]
        self.assertEqual((r["n"],r["incomplete"],r["overlapping_entries"]),(2,1,2))

    def test_sampling_and_forward_job_offline_restart_and_old_mode_unchanged(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{"TORI_DATA_DIR":folder,"TORI_AUTO_ENABLED":"0"}):
            identity=save_dataset("TEST",fixture_sources())
            data=read_dataset(identity)
            spec=validate_spec({"symbols":["TEST"],"dataset_ids":{"TEST":identity},"entry_mode":"tori","samples":3,"search_bars":20,
                               "tori":{"sampling":"random","observe_forward":True,"context":"off"}})
            plan=trial_plan(data,spec)
            self.assertEqual(len(plan["windows"]),3)
            self.assertLess(plan["observation_end"],plan["holdout_start"])
            changed=copy.deepcopy(data)
            for rows in changed["material"]["bars"].values():
                for row in rows: row.update(high=9999,close=999)
            self.assertEqual(trial_plan(data,spec),trial_plan(changed,spec))
            job=jobs.submit(spec)
            with patch("jobs.import_dataset",side_effect=AssertionError("offline")):
                jobs.worker_loop(threading.Event(),once=True)
            first=jobs.report(job["id"])
            self.assertEqual(first["job"]["status"],"succeeded",first["job"])
            self.assertEqual(len(first["job"]["symbols"][0]["plan"]["coverage"]["windows"]),3)
            self.assertIn("observations",first["summary"])
            with jobs.connection() as db: db.execute("UPDATE symbols SET done=0 WHERE job_id=?",(job["id"],))
            jobs.run_job(job["id"])
            repeated=jobs.report(job["id"])
            self.assertEqual(first["trials"],repeated["trials"])
            self.assertEqual(first["summary"],repeated["summary"])
            self.assertEqual(first["job"]["eventCount"],repeated["job"]["eventCount"])
            self.assertTrue(all("windowId" in c for c in first["trials"]))
            interrupted=jobs.submit(spec)
            advance=entry_tests.EntryScanner.advance
            def partial(scanner,end,cancelled=lambda:False,progress=None):
                advance(scanner,scanner.plan["scan_start"]+2,progress=progress)
                return False
            with patch.object(entry_tests.EntryScanner,"advance",partial):
                self.assertFalse(jobs.run_job(interrupted["id"]))
            self.assertFalse(jobs.get_job(interrupted["id"])["symbols"][0]["plan"]["coverage"]["windows"][0]["complete"])
            jobs.run_job(interrupted["id"])
            resumed=jobs.report(interrupted["id"])
            self.assertEqual(resumed["trials"],first["trials"])
            self.assertEqual(resumed["summary"],first["summary"])
            self.assertEqual(resumed["job"]["eventCount"],first["job"]["eventCount"])
            # Mark this deliberately direct-run job complete before starting the next queue worker.
            with jobs.connection() as db: db.execute("UPDATE jobs SET status='succeeded' WHERE id=?",(interrupted["id"],))
            old=jobs.submit({"symbols":["TEST"],"dataset_ids":{"TEST":identity},"entry_mode":"tori","tori":{"start_date":"2024-07-01","end_date":"2024-07-04"}})
            jobs.worker_loop(threading.Event(),once=True)
            self.assertNotIn("observations",jobs.report(old["id"])["summary"])


if __name__=="__main__": unittest.main()
