import copy
from dataclasses import asdict, replace
from datetime import datetime, timedelta
import json
import os
import tempfile
import threading
import unittest
from unittest.mock import patch

import jobs
from datasets import digest, read_dataset, save_dataset, chart_dataset
from models import Bar, DataError, NY
from research import validate_spec, trial_plan
from test_research import fixture_sources
from tori_entries import EntryScanner, aggregate, contact_count, structure, summarize
from trendlines import Ray


def controlled():
    start = int(datetime(2025,1,6,8,tzinfo=NY).timestamp())
    bars = [Bar(start+i*14400,start+(i+1)*14400,100.8,102,100.2,101,100) for i in range(40)]
    bars[30] = replace(bars[30],open=101.1,high=102.1,low=101,close=102)
    bars[31] = replace(bars[31],open=101.6,high=102.3,low=101.45,close=102.2)
    bars[32] = replace(bars[32],open=102.1,high=103.2,low=102,close=103)
    hourly = [Bar(start+i*3600,start+(i+1)*3600,102,102.1,101.9,102,10) for i in range(160)]
    dataset = {"id":"a"*64,"material":{"symbol":"TEST","bars":{"4h":[asdict(b) for b in bars],"1h":[asdict(b) for b in hourly],"1D":[]}}}
    spec = validate_spec({"entry_mode":"tori","tori":{"line_policy":"snapshot","min_age_days":0,"context":"off","max_safety_pct":5,"max_safety_atr":10,"min_room_r":0}})
    plan = {"scan_start":30,"discovery_end":35,"holdout_start":bars[36].end,"candles":6}
    axis = tuple(b.time for b in bars)
    red = Ray(bars[0].time,103,bars[10].time,102.5,-.05,2,2,True,False,0,10,axis,"bars")
    green = Ray(bars[0].time,100,bars[10].time,100.01,.001,2,2,True,False,0,10,axis,"bars")
    return dataset,spec,plan,{"red":red,"green":green}


class ToriEntryTests(unittest.TestCase):
    def scanner(self, dataset=None, changes=None):
        data,spec,plan,lines = controlled()
        if dataset is not None: data=dataset
        if changes: spec=validate_spec({**spec,"tori":{**spec["tori"],**changes}})
        emitted=[]
        scanner=EntryScanner(data,spec,plan,emitted.append)
        scanner.context=lambda at:{"daily":{"closedAt":None,"close":None,"red":None,"green":None},"structure":{"1D":"up","1W":"unknown","1M":"unknown"}}
        return scanner,emitted,lines

    def run_controlled(self, scanner, lines, end=35):
        with patch("tori_entries.pair",return_value=lines),patch("tori_entries.contact_count",return_value=2):
            scanner.advance(end)

    def test_modes_are_opt_in_and_invalid_parameters_are_rejected(self):
        self.assertNotIn("entry_mode",validate_spec({}))
        for value in ({"entry_mode":"other"},{"tori":{}},{"entry_mode":"tori","tori":{"max_safety_pct":float("nan")}},
                      {"entry_mode":"tori","tori":{"start_date":0}},{"entry_mode":"tori","tori":{"start_date":"2025-02-30"}},
                      {"entry_mode":"tori","tori":{"line_policy":"future"}}):
            with self.assertRaises(DataError): validate_spec(value)

    def test_each_step_and_one_large_jump_produce_identical_history(self):
        a,ae,lines=self.scanner();b,be,_=self.scanner()
        self.run_controlled(a,lines)
        with patch("tori_entries.pair",return_value=lines),patch("tori_entries.contact_count",return_value=2):
            for i in range(30,36): b.advance(i)
        self.assertEqual(a.cases,b.cases)
        self.assertEqual(ae,be)
        self.assertTrue(any(v["status"]=="observed" for t in a.cases.values() for v in t["variants"]))

    def test_future_prices_do_not_change_prior_decisions_or_use_entry_hour_low(self):
        a,_,lines=self.scanner();self.run_controlled(a,lines,31)
        data=copy.deepcopy(a.dataset)
        cutoff=a.bars[31].end
        for rows in data["material"]["bars"].values():
            for row in rows:
                if row["time"] >= cutoff: row.update(open=900,high=1000,low=.01,close=999)
        b,_,_=self.scanner(data);self.run_controlled(b,lines,31)
        self.assertEqual(a.cases,b.cases)
        entry=next(iter(a.cases.values()))["variants"][0]
        self.assertEqual(entry["status"],"observed")
        changed=copy.deepcopy(a.dataset)
        next(row for row in changed["material"]["bars"]["1h"] if row["time"]==entry["entryAt"])["low"]=1
        c,_,_=self.scanner(changed);self.run_controlled(c,lines,31)
        self.assertEqual(a.cases,c.cases)

    def test_snapshot_survives_later_line_selection_and_retest_uses_old_anchors(self):
        scanner,_,lines=self.scanner()
        self.run_controlled(scanner,lines,30)
        moved={"red":replace(lines["red"],a_price=200,b_price=199.5),"green":lines["green"]}
        self.run_controlled(scanner,moved)
        self.assertEqual(len(scanner.cases),1)
        case=next(iter(scanner.cases.values()))
        retest=case["variants"][2]
        self.assertEqual(retest["status"],"observed")
        self.assertEqual(retest["signal"]["red"]["a_price"],103)
        self.assertGreater(retest["signalAt"],case["signal"]["closedAt"])

    def test_tracked_mode_does_not_discard_an_older_setup_when_line_moves(self):
        scanner,_,lines=self.scanner(changes={"line_policy":"tracked"})
        scanner.bars[30]=replace(scanner.bars[30],close=101.4)
        self.run_controlled(scanner,lines,30)
        moved={"red":replace(lines["red"],a_price=105,b_price=104.5),"green":lines["green"]}
        self.run_controlled(scanner,moved)
        self.assertGreater(len(scanner.cases),1)
        original=next(c for c in scanner.cases.values() if c["frozen"]["red"]["a_price"]==103)
        self.assertTrue(any(v["status"]=="observed" for v in original["variants"]))

    def test_nearer_safety_is_selected_only_from_already_confirmed_lines(self):
        scanner,_,lines=self.scanner()
        closer=replace(lines["green"],a_price=100.4,b_price=100.41)
        future_or_invalid=replace(closer,a_price=100.8,valid=False)
        pair={**lines,"greens":[lines["green"],closer,future_or_invalid]}
        self.run_controlled(scanner,pair,30)
        self.assertEqual(next(iter(scanner.cases.values()))["frozen"]["green"]["a_price"],100.4)

    def test_green_violation_blocks_pending_retest_but_does_not_erase_an_entry(self):
        scanner,_,lines=self.scanner()
        scanner.bars[31]=replace(scanner.bars[31],low=90)
        self.run_controlled(scanner,lines)
        variants=next(iter(scanner.cases.values()))["variants"]
        self.assertEqual(variants[0]["status"],"observed")
        self.assertEqual(variants[2]["reason"],"green_violated")

    def test_drift_and_missing_context_are_not_entries(self):
        off,_,off_lines=self.scanner()
        self.run_controlled(off,off_lines,30)
        context_check=next(c for c in next(iter(off.cases.values()))["variants"][0]["checks"] if c["name"]=="context")
        self.assertEqual(context_check["state"],"unknown")
        self.assertFalse(context_check["required"])
        scanner,_,lines=self.scanner(changes={"context":"topdown"})
        self.run_controlled(scanner,lines)
        variants=next(iter(scanner.cases.values()))["variants"]
        self.assertFalse(any(v["status"]=="observed" for v in variants))
        self.assertIn("context",variants[0]["reason"])
        scanner,_,lines=self.scanner()
        scanner.bars[30]=replace(scanner.bars[30],open=102,close=102)
        self.run_controlled(scanner,lines,30)
        self.assertIn("positive_body",next(iter(scanner.cases.values()))["variants"][0]["reason"])

    def test_horizontal_waits_for_a_later_strong_confirmation(self):
        scanner,_,lines=self.scanner()
        scanner.bars[31]=replace(scanner.bars[31],open=102.2,close=102.21)
        self.run_controlled(scanner,lines,31)
        v=next(iter(scanner.cases.values()))["variants"][1]
        self.assertEqual(v["status"],"pending")
        self.assertIn("body_fraction",v["waitingFor"])
        self.run_controlled(scanner,lines)
        v=next(iter(scanner.cases.values()))["variants"][1]
        # Opening below the frozen horizontal ceiling is rejected, never filled retroactively.
        self.assertIn(v["status"],("observed","rejected"))
        self.assertEqual(v["signalAt"],scanner.bars[32].end)

    def test_risk_is_rechecked_at_real_hourly_open_and_end_is_censored(self):
        scanner,_,lines=self.scanner()
        self.run_controlled(scanner,lines,30)
        scanner.finish()
        self.assertEqual(next(iter(scanner.cases.values()))["variants"][0]["status"],"censored")
        scanner,_,lines=self.scanner()
        for i,b in enumerate(scanner.hourly):
            if b.time>=scanner.bars[30].end: scanner.hourly[i]=replace(b,open=120,high=121,close=120)
        self.run_controlled(scanner,lines)
        self.assertIn("execution:safety_distance",next(iter(scanner.cases.values()))["variants"][0]["reason"])

    def test_adjacent_touch_candles_are_not_independent_contacts(self):
        data,_,_,lines=controlled()
        bars=[Bar(i*10,(i+1)*10,1,103-.05*i,.1,1,1) for i in range(10)]
        self.assertEqual(contact_count(asdict(lines["red"]),bars,True,2),1)

    def test_summary_deduplicates_simultaneous_entries_but_keeps_rejections(self):
        scanner,_,lines=self.scanner();self.run_controlled(scanner,lines);scanner.finish()
        case=next(iter(scanner.cases.values()))
        result=summarize([case,{**copy.deepcopy(case),"id":"another"}])
        self.assertEqual(result["groups"]["breakout_provisional"]["entries"],2)
        self.assertEqual(result["groups"]["breakout_provisional"]["uniqueEntries"],1)

    def test_completed_week_and_month_never_include_an_open_period(self):
        from market_calendar import session_close
        days=["2026-11-23","2026-11-24","2026-11-25","2026-11-27"]
        bars=[Bar(int(datetime.fromisoformat(d).replace(tzinfo=NY).timestamp()),session_close(d),100,102,99,101,1) for d in days]
        self.assertEqual(aggregate(bars[:-1]),[])
        weekly=aggregate(bars)
        self.assertEqual(len(weekly),1)
        self.assertEqual(datetime.fromtimestamp(weekly[0].end,NY).hour,13)
        self.assertEqual(aggregate(bars,True),[])

    def test_real_line_engine_prefix_is_invariant_to_future_shocks(self):
        sources=fixture_sources()
        data={"id":"b"*64,"material":{"symbol":"TEST","bars":{tf:[asdict(b) for b in rows] for tf,(rows,_) in sources.items()}}}
        spec=validate_spec({"entry_mode":"tori"})
        scan_plan={"scan_start":900,"discovery_end":940,"holdout_start":sources["4h"][0][941].end,"candles":41}
        first=EntryScanner(data,spec,scan_plan);first.advance(925)
        changed=copy.deepcopy(data)
        for rows in changed["material"]["bars"].values():
            for row in rows:
                if row["time"]>sources["4h"][0][925].end:row.update(high=9999,low=.01,close=9998)
        second=EntryScanner(changed,spec,scan_plan);second.advance(925)
        self.assertTrue(first.cases)
        self.assertEqual(first.cases,second.cases)

    def test_job_is_offline_persistent_and_chart_reads_original_anchors(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{"TORI_DATA_DIR":folder,"TORI_AUTO_ENABLED":"0"}):
            identity=save_dataset("TEST",fixture_sources())
            spec={"symbols":["TEST"],"entry_mode":"tori","dataset_ids":{"TEST":identity},
                  "tori":{"start_date":"2024-07-01","end_date":"2024-07-10","context":"off"}}
            job=jobs.submit(spec)
            with patch("jobs.import_dataset",side_effect=AssertionError("offline")):
                jobs.worker_loop(threading.Event(),once=True)
            result=jobs.report(job["id"])
            self.assertEqual(result["job"]["status"],"succeeded",result["job"])
            self.assertGreater(result["summary"]["setups"],0)
            filtered=jobs.report(job["id"],limit=1,entry_filter="entries")
            self.assertEqual(filtered["summary"],result["summary"])
            self.assertTrue(all(any(v["status"]=="observed" for v in t["variants"]) for t in filtered["trials"]))
            with self.assertRaises(DataError): jobs.report(job["id"],entry_filter="invalid")
            trial=result["trials"][0]
            at=datetime.fromtimestamp(trial["startAt"],NY).isoformat()
            payload=chart_dataset(identity,"4h",at,trial["variants"][0])
            self.assertEqual(payload["lanes"]["4h"]["red"]["a_time"],trial["frozen"]["red"]["a_time"])
            self.assertEqual(result["job"]["manifest"]["studyVersion"],"tori-entries-1")
            self.assertIn("coverage",result["job"]["symbols"][0]["plan"])
            broken=next((t for t in result["trials"] if "breakIndex" in t),None)
            if broken:
                before=datetime.fromtimestamp(broken["startAt"],NY).isoformat()
                early=chart_dataset(identity,"4h",before,broken["variants"][0])
                self.assertEqual(early["lanes"]["4h"]["red"]["a_time"],broken["frozen"]["red"]["a_time"])
                self.assertIsNone(early["researchSetup"]["entryAt"])
                self.assertIsNone(early["lanes"]["4h"]["event"])
            # Replaying an interrupted setup study updates stable rows rather than duplicating them.
            with jobs.connection() as db: db.execute("UPDATE symbols SET done=0 WHERE job_id=?",(job["id"],))
            jobs.run_job(job["id"])
            self.assertEqual(jobs.report(job["id"])["trials"],result["trials"])
            self.assertEqual(jobs.get_job(job["id"])["eventCount"],result["job"]["eventCount"])
            # A partial scan persists progress; replay reconstructs pending state deterministically.
            interrupted_job=jobs.submit(spec)
            original=EntryScanner.advance
            def partial(scanner,end,cancelled=lambda:False,progress=None):
                original(scanner,scanner.plan["scan_start"]+2,progress=progress)
                return False
            with patch.object(EntryScanner,"advance",partial):
                self.assertFalse(jobs.run_job(interrupted_job["id"]))
            jobs.run_job(interrupted_job["id"])
            self.assertEqual(jobs.report(interrupted_job["id"])["trials"],result["trials"])
            plan=trial_plan(read_dataset(identity),validate_spec(spec))
            self.assertLess(plan["scanEndAt"],plan["holdout_start"])


if __name__=="__main__": unittest.main()
