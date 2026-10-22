"""Prospective capture, immutable import, transactional review and HTTP boundaries."""
from copy import deepcopy
from dataclasses import asdict, replace
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer

from datasets import digest
from entry_watch import WatchReplay
from forward_engine import advance, CaptureReplay
from forward_data import refresh, expected_last, closed_cutoff
from forward_watch import (register, load_lane, store_lane, connection, cases_page, events_page,
                           case_view, review, status, cycle, stop, get_run)
from models import DataError
from server import Handler
import test_retest_observation as observation_fixtures
import test_entry_discovery as fixtures


class ForwardEngineTests(unittest.TestCase):
    def setUp(self):
        fixture = observation_fixtures.ObservationTests()
        fixture.setUp()
        self.data,self.sources,self.start,self.first,self.last = fixture.data,fixture.sources,fixture.start,fixture.first,fixture.last

    def factory(self, data, model, start, cutoff):
        engine = CaptureReplay(data, model, start, cutoff)
        engine.candidates = [fixtures.candidate(engine.bars,False), fixtures.candidate(engine.bars,True)]
        return engine

    def run_engine(self, model, cutoff, previous=None, data=None, from_at=None):
        with patch("forward_engine.CaptureReplay",side_effect=self.factory),patch("entry_watch.Geometry.proposals",return_value=[]):
            return advance(data or self.data,model,self.start,from_at or self.start,cutoff,previous)

    def test_both_models_keep_causal_original_green_and_capture_does_not_change_entries(self):
        for model in ("hull_exact","swing_zone"):
            state,cases,events = self.run_engine(model,self.first)
            self.assertTrue(cases)
            self.assertTrue(state["records"])
            original = next(c for c in cases if c["phase"]=="breakout")
            self.assertEqual(original["green"]["a_price"],95)
            self.assertEqual(original["red"]["a_price"],110)
            self.assertTrue(all(c["knownAt"]>=self.start for c in cases))
            self.assertTrue(any(e["kind"]=="entry" for e in events))
            with patch("entry_watch.Geometry.proposals",return_value=[]):
                replay = WatchReplay(self.data,model,self.start,self.first)
                replay.candidates = [fixtures.candidate(replay.bars,False),fixtures.candidate(replay.bars,True)]
                replay.run()
            self.assertEqual(state["watch"]["entries"],replay.entries)

    def test_resume_repetition_and_future_shock(self):
        for model in ("hull_exact","swing_zone"):
            first,cases,_ = self.run_engine(model,self.first)
            persisted=json.loads(json.dumps(first))
            again,new,_ = self.run_engine(model,self.first,persisted)
            self.assertEqual(digest(first),digest(again))
            self.assertEqual(new,[])
            resumed,_,_ = self.run_engine(model,self.last,persisted)
            full,_,_ = self.run_engine(model,self.last)
            self.assertEqual(resumed["records"],full["records"])
            changed=deepcopy(self.data)
            for rows in changed["material"]["bars"].values():
                for b in rows:
                    if b["time"]>=self.first:b.update(open=200,high=201,low=199,close=200)
            shocked,other,_=self.run_engine(model,self.first,data=changed)
            self.assertEqual(first,shocked)
            self.assertEqual(cases,other)

    def test_registration_after_old_signal_never_creates_retroactive_entry(self):
        # Friday's signal exists, Tuesday's fill follows. Registration between
        # them must not label this previously known signal as a fresh entry.
        from_at = self.sources["4h"][21].end+3600
        state,cases,_ = self.run_engine("swing_zone",self.last,from_at=from_at)
        self.assertEqual(state["records"],[])
        self.assertTrue(all(c["knownAt"]>=from_at for c in cases))

    def test_known_revision_model_swap_and_time_reversal_rejected(self):
        first,_,_=self.run_engine("hull_exact",self.first)
        with self.assertRaises(ValueError):self.run_engine("swing_zone",self.last,first)
        with self.assertRaises(ValueError):self.run_engine("hull_exact",self.first-300,first)
        changed=deepcopy(self.data);changed["material"]["bars"]["5m"][0]["close"]+=.01
        with self.assertRaises(ValueError):self.run_engine("hull_exact",self.last,first,changed)


class RefreshTests(unittest.TestCase):
    def setUp(self):
        self.data,self.sources=fixtures.dataset()
        self.data["material"]["session"]="XNYS regular; test fixture"
        self.known=self.sources["4h"][23].end
        self.now=self.sources["5m"][-1].end+900
        self.meta={"feed":"iex","adjustment":"split","quality":{"rejected":0}}

    def test_same_prefix_can_append_without_provider_orders_or_full_history_download(self):
        short=deepcopy(self.data)
        short["material"]["bars"]={tf:[b for b in rows if b["end"]<=self.known] for tf,rows in short["material"]["bars"].items()}
        short["id"]=digest(short["material"])
        with patch("forward_data.load_bars",return_value=(self.sources["5m"],self.meta)) as load, \
             patch("forward_data.save_dataset",return_value="new") as save,patch("forward_data.read_dataset",return_value={"id":"new"}):
            result,cutoff=refresh(short,self.known,self.now)
        self.assertEqual(result["id"],"new")
        self.assertEqual(cutoff,closed_cutoff(self.now))
        self.assertLess(load.call_args.kwargs["history_days"],100)
        self.assertEqual(save.call_args.kwargs["adjustment"],"split")

    def test_changed_or_deleted_overlap_and_stale_data_cannot_advance(self):
        rows=list(self.sources["5m"])
        changed=[replace(b,close=b.close+.01) if b.time==rows[0].time else b for b in rows]
        deleted=[b for b in rows if b.end!=self.known]
        for fine in (changed,deleted,rows[:-2]):
            with patch("forward_data.load_bars",return_value=(fine,self.meta)),patch("forward_data.save_dataset") as save:
                with self.assertRaises(DataError):refresh(self.data,self.known,self.now)
                save.assert_not_called()

    def test_provider_stale_fallback_and_rejected_bars_do_not_become_success(self):
        for extra in ({"warning":"stale"},{"quality":{"rejected":1}}):
            with patch("forward_data.load_bars",return_value=(self.sources["5m"],{**self.meta,**extra})):
                with self.assertRaises(DataError):refresh(self.data,self.known,self.now)

    def test_unobserved_bootstrap_bar_deleted_by_provider_is_not_silently_retained(self):
        missing=self.sources["5m"][-20].time
        incoming=[b for b in self.sources["5m"] if b.time!=missing]
        with patch("forward_data.load_bars",return_value=(incoming,self.meta)), \
             patch("forward_data.save_dataset",return_value="new") as save, \
             patch("forward_data.read_dataset",return_value={"id":"new"}):
            refresh(self.data,self.known,self.now)
        saved=save.call_args.args[1]["5m"][0]
        self.assertNotIn(missing,[b.time for b in saved])


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.env=patch.dict(os.environ,{"TORI_DATA_DIR":self.tmp.name});self.env.start()
        self.run=register(["TEST"])
        self.body={"id":"one","symbol":"TEST","model":"swing_zone","phase":"near","knownAt":100,
                   "sourceIndex":20,"candidateId":"red","red":None,"green":None}
        self.state={"datasetId":"dataset","asOf":100,"records":[],"watch":{}}

    def tearDown(self):
        self.env.stop();self.tmp.cleanup()

    def add(self, number):
        item={**self.body,"id":str(number)}
        store_lane(self.run,"TEST","swing_zone",self.state,[item],[{"id":str(number),"kind":"candidate","caseId":str(number),"knownAt":100}])

    def test_transaction_repeat_stable_pages_and_durable_event_cursor(self):
        self.add(1);self.add(2);self.add(2)
        first=cases_page(limit=1)
        self.add(3)
        second=cases_page(limit=1,offset=first["nextOffset"],through=first["through"])
        self.assertNotEqual(first["items"][0]["id"],second["items"][0]["id"])
        self.assertIsNone(second["nextOffset"])
        events=events_page(limit=1)
        self.assertEqual(events["items"][0]["caseId"],digest([self.run,"1"]))
        self.assertEqual(len(events_page(after=events["after"],through=events["through"])["items"]),2)
        self.assertEqual(load_lane(self.run,"TEST","swing_zone"),self.state)

    def test_case_review_history_and_server_remembers_unblinding(self):
        self.add(1);case_id=digest([self.run,"1"])
        review(case_id,{"verdict":"interesting","note":"manual","unblinded":False})
        with connection() as db:db.execute("INSERT INTO reveals VALUES(?,?)",(case_id,100))
        review(case_id,{"verdict":"reject","note":"changed","unblinded":False})
        row=cases_page()["items"][0]
        self.assertTrue(row["review"]["unblinded"])
        self.assertTrue(row["revealed"])
        with connection() as db:self.assertEqual(db.execute("SELECT COUNT(*) FROM reviews").fetchone()[0],2)

    def test_failed_transaction_does_not_commit_state_without_cases(self):
        bad={**self.body,"features":float("nan")}
        with self.assertRaises(ValueError):store_lane(self.run,"TEST","swing_zone",self.state,[bad],[])
        self.assertIsNone(load_lane(self.run,"TEST","swing_zone"))
        self.assertEqual(cases_page()["items"],[])

    def test_status_is_local_and_new_registration_cannot_silently_replace_active_run(self):
        with patch("alpaca._request",side_effect=AssertionError("network")):
            self.assertTrue(status()["configured"])
        with self.assertRaises(DataError):register(["OTHER"])
        with self.assertRaises(DataError):register(["TEST"],from_at=100)
        stop(self.run)
        self.assertNotEqual(register(["OTHER"]),self.run)

    def test_invalid_review_and_pagination_are_rejected(self):
        for body in ({},{"verdict":"buy","note":"","unblinded":False},{"verdict":"unclear","note":"x"*2001,"unblinded":False}):
            with self.assertRaises(DataError):review("absent",body)
        for kw in ({"limit":101},{"offset":-1},{"model":"unknown"}):
            with self.assertRaises(DataError):cases_page(**kw)

    def test_model_future_outcomes_hidden_in_signal_view(self):
        self.add(1);case_id=digest([self.run,"1"])
        data,sources=fixtures.dataset()
        item={**self.body,"knownAt":sources["4h"][23].end,"sourceIndex":23}
        with connection() as db:db.execute("UPDATE cases SET body=? WHERE id=?",(json.dumps(item),case_id))
        state={**self.state,"asOf":sources["4h"][30].end,"records":[{"entry":{"sourceSetupId":"red"},"future":"outcome"}]}
        store_lane(self.run,"TEST","swing_zone",state,[],[])
        with patch("forward_watch.read_dataset",return_value=data):
            signal=case_view(case_id)
            latest=case_view(case_id,True)
        self.assertEqual(signal["records"],[])
        self.assertTrue(all(b["end"]<=item["knownAt"] for b in signal["bars"]))
        self.assertEqual(latest["records"],state["records"])
        self.assertTrue(cases_page()["items"][0]["revealed"])

    def test_worker_imports_once_resumes_both_models_and_blocks_revision_without_losing_state(self):
        fixture=ForwardEngineTests();fixture.setUp()
        stop(self.run)
        self.run=register(["TEST"],now=fixture.start+900)
        def fresh(data,known,now):return data,closed_cutoff(now)
        with patch("forward_watch.import_dataset",return_value=fixture.data["id"]) as importer, \
             patch("forward_watch.read_dataset",return_value=fixture.data),patch("forward_watch.data_kind",return_value="market"), \
             patch("forward_watch.start_time",return_value=fixture.start), \
             patch("forward_watch.refresh",side_effect=fresh) as fetch, \
             patch("forward_engine.CaptureReplay",side_effect=fixture.factory),patch("entry_watch.Geometry.proposals",return_value=[]):
            result=cycle(self.run,now=fixture.first+900)
            self.assertEqual(result["errors"],[])
            self.assertTrue(cases_page()["items"])
            before={m:load_lane(self.run,"TEST",m) for m in ("hull_exact","swing_zone")}
            self.assertTrue(all(before.values()))
            repeat=cycle(self.run,now=fixture.first+900)
            self.assertEqual(repeat["errors"],[])
            self.assertEqual(importer.call_count,1)
            self.assertEqual(fetch.call_count,1)
            fetch.side_effect=DataError("Historische Kursrevision im bekannten Präfix; neue Generation erforderlich.",409)
            failed=cycle(self.run,now=fixture.first+86400+900)
            self.assertTrue(failed["errors"])
            cycle(self.run,now=fixture.first+2*86400+900)
            self.assertEqual(fetch.call_count,2)
            self.assertEqual({m:load_lane(self.run,"TEST",m) for m in before},before)
            self.assertEqual(status()["items"][0]["status"],"blocked")


class WatchHTTPTests(unittest.TestCase):
    def test_routes_share_host_origin_and_payload_protection(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{"TORI_DATA_DIR":tmp}):
            server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            url=f"http://127.0.0.1:{server.server_port}"
            try:
                with urllib.request.urlopen(url+"/watch") as response:self.assertIn(b'watch-chart',response.read())
                with patch("alpaca._request",side_effect=AssertionError("network")):
                    with urllib.request.urlopen(url+"/api/watch/status") as response:self.assertFalse(json.load(response)["configured"])
                request=urllib.request.Request(url+"/api/watch/status",headers={"Host":"foreign.example"})
                with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(request)
                self.assertEqual(e.exception.code,403)
                request=urllib.request.Request(url+"/api/watch/cases/"+"a"*64+"/review",data=b'{}',headers={"Content-Type":"application/json"},method="POST")
                with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(request)
                self.assertEqual(e.exception.code,403)
            finally:server.shutdown();server.server_close();thread.join()


class ForwardBackupTests(unittest.TestCase):
    def test_backup_restore_retains_reviews_states_and_protects_frozen_datasets(self):
        import maintenance
        from datasets import save_dataset
        from storage import cleanup_preview
        from test_research import fixture_sources
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{"TORI_DATA_DIR":str(Path(folder)/"runtime")}):
            identity=save_dataset("TEST",fixture_sources())
            run=register(["TEST"])
            state={"datasetId":identity,"asOf":100,"records":[],"watch":{}}
            case={"id":"case","phase":"near","knownAt":100}
            store_lane(run,"TEST","hull_exact",state,[case],[])
            key=digest([run,"case"])
            review(key,{"verdict":"interesting","note":"preserve","unblinded":False})
            self.assertEqual(cleanup_preview()["candidates"],[])
            target=Path(folder)/"backup"
            maintenance.backup(target)
            self.assertIn("forward/watch.sqlite3",maintenance.verify(target)["files"])
            restored=Path(folder)/"restored"
            maintenance.restore(target,restored)
            with patch.dict(os.environ,{"TORI_DATA_DIR":str(restored)}):
                self.assertEqual(load_lane(run,"TEST","hull_exact"),state)
                self.assertEqual(cases_page()["items"][0]["review"]["note"],"preserve")
                self.assertFalse(status()["workerLock"])

    def test_newer_watch_schema_is_rejected_without_rewriting(self):
        import sqlite3
        from contextlib import closing
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{"TORI_DATA_DIR":folder}):
            with connection() as db:db.execute("PRAGMA user_version=99")
            with self.assertRaises(DataError):
                with connection():pass
            with closing(sqlite3.connect(Path(folder)/"forward/watch.sqlite3")) as db:
                self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0],99)
