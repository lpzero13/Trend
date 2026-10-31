"""Synthetic-only tests of manual random selection, causal playback and HTTP boundaries."""
from copy import deepcopy
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import random
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer

from datasets import save_dataset,read_dataset
from database import connection
from lab_data import resample_regular,NORMALIZATION
from lab_splits import sessions_between
from models import DataError
from storage import references
from server import Handler
import random_replay as replay
from test_lab_data import session


class RandomReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fine=sum((session(d,100+i*.1) for i,d in enumerate(sessions_between('2025-01-02','2025-07-15'))),[])
        cls.frames,_=resample_regular(fine)
        cls.now=int(datetime(2025,7,20,tzinfo=timezone.utc).timestamp())

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.env=patch.dict(os.environ,{'TORI_DATA_DIR':self.temp.name,'TORI_AUTO_ENABLED':'0'});self.env.start()
        self.sources={tf:(rows,{'normalization':NORMALIZATION}) for tf,rows in self.frames.items()}
        self.identity=save_dataset('AAA',self.sources,feed='sip',adjustment='split',session='XNYS regular; test fixture')

    def tearDown(self):self.env.stop();self.temp.cleanup()

    def create(self):return replay.create(rng=random.Random(28),now=self.now)

    def test_uniform_asset_then_time_with_no_signal_or_outcome_selection(self):
        save_dataset('BBB',self.sources,feed='iex',adjustment='raw',session='XNYS regular; fixture')
        class Choice:
            def __init__(self):self.calls=[]
            def choice(self,items):self.calls.append(items);return items[0]
        rng=Choice()
        with patch('alpaca._request',side_effect=AssertionError('offline')):item=replay.create(rng=rng,now=self.now)
        self.assertEqual(rng.calls[0],['AAA','BBB']);self.assertGreater(len(rng.calls[1]),10)
        self.assertEqual(item['startAt'],self.frames['1D'][59].end)
        self.assertEqual(item['symbol'],'AAA');self.assertNotIn('return',item)

    def test_all_intervals_only_show_closed_known_candles_and_analysis_is_off(self):
        item=self.create()
        with patch('alpaca._request',side_effect=AssertionError('offline')):
            p=replay.view(item['id'])
        self.assertFalse(p['analysisEnabled']);self.assertEqual(p['lanes'],{})
        self.assertEqual(p['randomCase']['startAt'],item['startAt'])
        for tf,chart in p['charts'].items():
            self.assertTrue(all(b['end']<=item['startAt'] for b in chart['bars']))
            self.assertEqual(p['sources'][tf]['lastClose'],chart['bars'][-1]['end'])
        self.assertNotIn('rthQuality',p['sources']['4h'])
        self.assertNotIn('5m',p['charts'])

    def test_forward_backward_cross_interval_and_reload_preserve_origin(self):
        item=self.create();origin=item['startAt'];at=datetime.fromtimestamp(origin,timezone.utc).isoformat()
        for tf in ('1h','4h','1D','1W'):
            nxt=replay.step(item['id'],tf,at,'next')
            self.assertGreater(nxt['closedAt'],origin)
            b=replay.view(item['id'],tf,nxt['asof']);self.assertEqual(b['charts'][tf]['bars'][-1]['end'],nxt['closedAt'])
            prev=replay.step(item['id'],tf,nxt['asof'],'back')
            self.assertLessEqual(prev['closedAt'],origin)
            self.assertEqual(replay.case(item['id'])['startAt'],origin)
        self.assertEqual(replay.view(item['id'])['analysisCutoff'],origin)

    def test_future_price_shock_cannot_change_drawn_start_or_known_prefix(self):
        item=self.create();original=replay.view(item['id']);frames={}
        from dataclasses import replace
        for tf,rows in self.frames.items():
            frames[tf]=([replace(b,open=1000,high=1001,low=999,close=1000) if b.time>=item['startAt'] else b for b in rows],{'normalization':NORMALIZATION})
        altered=save_dataset('AAA',frames,feed='sip',adjustment='split',session='XNYS regular; test fixture')
        from chart_sources import clear
        clear()
        with patch('chart_sources.read_dataset',return_value=read_dataset(altered)) as load:
            p=replay.view(item['id']);self.assertEqual(original['charts'],p['charts']);load.assert_called_once()
        clear()

    def test_synthetic_short_and_corrupt_files_do_not_become_random_market_cases(self):
        with patch('random_replay.candidates',return_value={'AAA':[self.identity]}):
            d=read_dataset(self.identity);d['material']['dataKind']='synthetic'
            with patch('random_replay.read_dataset',return_value=d):
                with self.assertRaises(DataError):self.create()
        short={tf:(rows[:2],meta) for tf,(rows,meta) in self.sources.items()}
        d=read_dataset(self.identity);d['material']['bars']['1D']=d['material']['bars']['1D'][:80]
        with self.assertRaises(DataError):replay.eligible(d,self.now)
        (self.root/'datasets'/('f'*64+'.json')).write_text('{ broken','utf-8')
        self.assertIn('AAA',replay.candidates())

    def test_pinned_case_survives_newer_datasets_and_protects_cleanup_reference(self):
        item=self.create();save_dataset('AAA',self.sources,feed='iex',adjustment='raw')
        self.assertEqual(replay.case(item['id'])['datasetId'],self.identity)
        with connection() as db:self.assertIn(self.identity,references(db,self.root))

    def test_boundaries_invalid_dates_and_case_paths_are_rejected(self):
        item=self.create()
        for value in ('garbage','2025-03-09T02:30','2025-11-02T01:30'):
            with self.assertRaises(DataError):replay.view(item['id'],as_of=value)
        with self.assertRaises(DataError):replay.case('../config.local.json')
        with self.assertRaises(DataError):replay.view(item['id'],'5m')
        with self.assertRaises(DataError):replay.step(item['id'],'4h',None,'wrong')
        end=self.frames['4h'][-1].end
        with self.assertRaises(DataError):replay.step(item['id'],'4h',datetime.fromtimestamp(end,timezone.utc).isoformat(),'next')
        with self.assertRaises(DataError):replay.view(item['id'],as_of='2030-01-01T00:00:00Z')

    def test_http_analysis_freeze_and_candle_steps_are_causal_offline_in_all_engines(self):
        from snapshots import read_snapshot, list_snapshots
        item=self.create()
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.api_token='';server.allowed_hosts=[]
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base='http://127.0.0.1:'+str(server.server_port)
        def get(path):
            with urlopen(base+path) as response:return json.load(response)
        try:
            with patch('alpaca._request',side_effect=AssertionError('offline')):
                for engine in ('legacy','fan_master','fan_extreme','fan_local'):
                    route='/api/random/cases/'+item['id']
                    p=get(route+'/chart?analysis=1&engine='+engine)
                    self.assertTrue(p['analysisEnabled']);self.assertIn('analysisId',p)
                    body=json.dumps({'analysisId':p['analysisId']}).encode()
                    with urlopen(Request(base+'/api/snapshots',data=body,headers={'Content-Type':'application/json','Origin':base})) as r:fixed=json.load(r)
                    self.assertEqual(fixed['payload'],p)
                    self.assertEqual(fixed['payload']['datasetId'],self.identity)
                    self.assertEqual(fixed['payload']['randomCase']['id'],item['id'])
                    for tf,chart in fixed['payload']['charts'].items():
                        self.assertTrue(all(b['end']<=item['startAt'] for b in chart['bars']))
                        for kind in ('red','green','mainSafety'):
                            ray=p['lanes'][tf].get(kind)
                            if ray:self.assertLessEqual(ray['b_time'],item['startAt'])
                    for tf in ('1h','4h','1D','1W'):
                        nxt=get(route+'/step?timeframe='+tf+'&direction=next')
                        future=get(route+'/chart?analysis=1&engine='+engine+'&timeframe='+tf+'&asof='+str(nxt['asof']).replace('+','%2B'))
                        self.assertEqual(future['analysisCutoff'],nxt['closedAt'])
                        self.assertEqual(future['charts'][tf]['bars'][-1]['end'],nxt['closedAt'])
                    self.assertEqual(read_snapshot(fixed['id']),fixed)
                    saved=next(s for s in list_snapshots('AAA') if s['id']==fixed['id'])
                    self.assertEqual(saved['datasetId'],self.identity);self.assertEqual(saved['randomCaseId'],item['id'])
                    self.assertEqual(saved['analysisEngine'],engine)
        finally:server.shutdown();thread.join();server.server_close()

    def test_identical_candles_in_distinct_replays_never_share_a_snapshot_identity(self):
        one=self.create();two=self.create()
        self.assertEqual(one['startAt'],two['startAt'])
        first=replay.view(one['id'],analysis=True);second=replay.view(two['id'],analysis=True)
        self.assertEqual(first['lanes'],second['lanes'])
        self.assertNotEqual(first['analysisId'],second['analysisId'])

    def test_http_create_requires_origin_and_replays_are_read_only_and_private(self):
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.api_token='';server.allowed_hosts=[]
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base='http://127.0.0.1:'+str(server.server_port)
        try:
            with urlopen(base+'/zufall') as r:self.assertIn(b'random-new',r.read())
            body=b'{}';url=base+'/api/random/cases'
            for origin in (None,'https://evil.example'):
                with self.assertRaises(HTTPError) as err:urlopen(Request(url,data=body,headers={'Content-Type':'application/json',**({'Origin':origin} if origin else {})}))
                self.assertEqual(err.exception.code,403)
            with patch('alpaca._request',side_effect=AssertionError('offline')):
                with urlopen(Request(url,data=body,headers={'Content-Type':'application/json','Origin':base})) as r:item=json.load(r)
                with urlopen(url+'/'+item['id']+'/chart?analysis=0') as r:
                    p=json.load(r);self.assertTrue(all(b['end']<=p['analysisCutoff'] for b in p['charts']['1D']['bars']))
            server.api_token='unit-test'
            with self.assertRaises(HTTPError) as err:urlopen(url+'/'+item['id'])
            self.assertEqual(err.exception.code,401)
        finally:server.shutdown();thread.join();server.server_close()
