from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer

from database import connection
import entry_history as h
from fan_geometry import stable_id
from models import DataError
from server import Handler
from storage import references


def sample(n=1, status="filled"):
    at=1704724200+n*14400
    ln={"id":"line", "a_time":at-864000, "b_time":at-432000, "a_price":110., "b_price":105.,
        "knownAt":at-14400, "contacts":3,"contactPoints":[{"time":at-432000,"known_at":at-400000}],
        "span_days":10.,"slope":-.1,"a_index":0,"b_index":10}
    green={**ln,"id":"green","a_price":90.,"b_price":95.,"slope":.1}
    return {"id":stable_id(["case",n]),"symbol":"TEST","datasetId":"d"*64,
        "signal":{"id":stable_id(["signal",n]),"episodeId":stable_id(["episode",n]),"family":"breakout",
                  "cohort":"qualified","signalAt":at,"initialStop":94.,"line":ln,"safety":green,"features":{"atr":2.}},
        "entry":{"status":status,"entryAt":at+300,"entryPrice":103.,"entryFill":104.,"initialStop":94.},
        "features":{"stopDistanceUSD":10.,"futureOpenDerived":104.},
        "paths":{"fan_safety":{"futureWin":999.}}}


def manifest():
    return {"symbol":"TEST","datasetId":"d"*64,"cutoff":1705000000,"windows":[{"name":"test","start":"2024-01-01","end":"2024-01-10"}],
            "source":"test","timeframe":"4h","caseCount":3,"feed":"sip","adjustment":"split"}


class EntryHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.env=patch.dict(os.environ,{"TORI_DATA_DIR":self.temp.name});self.env.start()
        self.c=sample();self.run=h.store_run(manifest(),[self.c,sample(2,"cancelled"),sample(3)])

    def tearDown(self):
        h._chart_sources.cache_clear()
        self.env.stop();self.temp.cleanup()

    def test_fixed_cases_paginate_and_do_not_leak_future_cases_or_prices(self):
        p=h.cases_page(self.run,offset=0,limit=1)
        self.assertEqual(p['total'],2);self.assertTrue(p['hasMore'])
        next_page=h.cases_page(self.run,offset=1,limit=1)
        self.assertNotEqual(p['items'][0]['id'],next_page['items'][0]['id'])
        self.assertFalse(next_page['hasMore'])
        at=self.c['signal']['signalAt']
        before=h.cases_page(self.run,datetime.fromtimestamp(at-1,timezone.utc).isoformat())
        self.assertEqual(before['items'],[])
        p=h.cases_page(self.run,datetime.fromtimestamp(at,timezone.utc).isoformat())
        self.assertEqual(len(p['items']),1)
        self.assertNotIn('entryPrice',json.dumps(p))
        self.assertNotIn('futureWin',json.dumps(p))

    def test_cancelled_future_fill_does_not_retroactively_hide_known_signal(self):
        c=sample(2,'cancelled');at=c['signal']['signalAt']
        p=h.cases_page(self.run,datetime.fromtimestamp(at,timezone.utc).isoformat())
        self.assertIn(c['id'],[v['id'] for v in p['items']])
        after=h.cases_page(self.run)
        self.assertNotIn(c['id'],[v['id'] for v in after['items']])

    def test_future_fill_and_entry_derived_features_hidden_until_entry(self):
        at=self.c['signal']['signalAt']
        before=h.detail(self.run,self.c['id'],datetime.fromtimestamp(at-1,timezone.utc).isoformat())
        self.assertEqual(before,{'id':self.c['id'],'state':'before_signal'})
        now=h.detail(self.run,self.c['id'],datetime.fromtimestamp(at,timezone.utc).isoformat())
        self.assertEqual(now['entry']['status'],'pending')
        self.assertNotIn('stopDistanceUSD',json.dumps(now))
        self.assertNotIn('futureOpenDerived',json.dumps(now))
        self.assertNotIn('futureWin',json.dumps(now))
        later=h.detail(self.run,self.c['id'])
        self.assertEqual(later['entry']['entryPrice'],103.)
        self.assertEqual(later['signal'],self.c['signal'])
        self.assertNotIn('paths',later)

    def test_idempotent_registration_preserves_review_and_atomic_duplicate_rejection(self):
        h.review(self.run,self.c['id'],'wrong_line','Kontakt unplausibel')
        self.assertEqual(h.store_run(manifest(),[self.c,sample(2,'cancelled'),sample(3)]),self.run)
        self.assertEqual(h.detail(self.run,self.c['id'])['review']['verdict'],'wrong_line')
        changed=deepcopy(self.c);changed['signal']['line']['b_price']+=1
        with self.assertRaises(DataError):h.store_run(manifest(),[changed,sample(2,'cancelled'),sample(3)])
        duplicate=deepcopy(self.c);duplicate['id']=stable_id('duplicate')
        with self.assertRaises(DataError):h.store_run({**manifest(),'source':'other'},[self.c,duplicate])
        self.assertEqual(len(h.get('/api/entries/runs',{'symbol':['TEST']})['items']),1)

    def test_review_delete_leaves_case_and_future_contacts_rejected(self):
        h.review(self.run,self.c['id'],'plausible','test')
        h.review(self.run,self.c['id'],delete=True)
        self.assertIsNone(h.detail(self.run,self.c['id'])['review'])
        self.assertEqual(h.case_value(self.run,self.c['id'])['signal'],self.c['signal'])
        with self.assertRaises(DataError):h.review(self.run,self.c['id'],'not-a-verdict')
        bad=deepcopy(self.c);bad['signal']['line']['contactPoints'][0]['known_at']=bad['signal']['signalAt']+1
        with self.assertRaises(DataError):h.store_run({**manifest(),'source':'bad'},[bad])

    def test_indexed_datasets_remain_referenced_and_tampering_fails(self):
        with connection() as db:
            self.assertIn('d'*64,references(db,Path(self.temp.name)))
            db.execute('UPDATE entry_cases SET checksum=? WHERE id=?',('bad',self.c['id']))
        with self.assertRaises(DataError):h.detail(self.run,self.c['id'])

    def test_chart_uses_bound_dataset_and_manual_candles_only(self):
        payload={'datasetId':'d'*64,'analysisEnabled':False}
        path=Path(self.temp.name)/'dataset.json';path.write_text('{}',encoding='utf-8')
        with patch('entry_history.path_for',return_value=path),patch('entry_history._chart_sources',return_value=({},{})) as sources,patch('entry_history.build_chart',return_value=payload) as build,patch('entry_history.add_weekly') as weekly:
            p=h.chart(self.run,'1W')
        self.assertFalse(build.call_args.kwargs['include_analysis'])
        self.assertEqual(sources.call_args.args[1],'d'*64)
        self.assertEqual(build.call_args.args[1:3],('TEST','1D'))
        weekly.assert_called_once_with(payload,'1W')
        self.assertTrue(p['entryHistory']['fixed'])

    def test_no_local_data_means_no_provider_request(self):
        with patch('random_replay.candidates',return_value={}),patch('alpaca._request',side_effect=AssertionError('offline')):
            with self.assertRaises(DataError):h.submit({'symbol':'MISSING'})
        for bad in ('../../private','x'*64,None):
            with self.assertRaises(DataError):h.run_info(bad)

    def test_background_failure_and_stale_job_are_explicit_not_silently_resumed(self):
        job='a'*64
        with connection() as db:
            db.execute('INSERT INTO entry_searches VALUES(?,?,?,?,?,?,?)',(job,'queued',0,'{}','{}',None,None))
        self.assertEqual(h.search_status(job)['status'],'interrupted')
        with patch('entry_history.read_dataset',side_effect=DataError('Dataset fehlt',404)),patch('entry_history.search_binding',return_value={}):
            h._calculate(job,{'datasetId':'d'*64}, {})
        self.assertEqual(h.search_status(job)['status'],'failed')
        self.assertEqual(h.search_status(job)['error'],'Dataset fehlt')

    def test_cached_chart_still_filters_future_candles_and_avoids_rehydrating(self):
        from dataclasses import asdict
        from test_history import dataset,metadata,CUTOFF,NOW
        sources={tf:dataset(tf) for tf in ('1h','4h','1D')}
        d={'id':'d'*64,'material':{'symbol':'TEST','provider':'Alpaca','feed':'sip','adjustment':'split','session':'Regular',
            'bars':{tf:[asdict(b) for b in bs] for tf,bs in sources.items()}},
            'sources':{tf:metadata(bs) for tf,bs in sources.items()}}
        run=h.store_run({**manifest(),'cutoff':int(NOW.timestamp())},[self.c])
        path=Path(self.temp.name)/'manifest.json';path.write_text('{}',encoding='utf-8')
        with patch('entry_history.path_for',return_value=path),patch('entry_history.read_dataset',return_value=d) as load:
            first=h.chart(run,'4h',CUTOFF.isoformat())
            second=h.chart(run,'1h',CUTOFF.isoformat())
        load.assert_called_once()
        for payload in (first,second):
            self.assertFalse(payload['analysisEnabled'])
            self.assertTrue(all(b['end']<=CUTOFF.timestamp() for view in payload['charts'].values() for b in view['bars']))

    def test_http_get_and_write_origin_protection(self):
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.api_token='';server.allowed_hosts=[]
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base=f'http://127.0.0.1:{server.server_port}'
        try:
            with urlopen(base+'/api/entries/cases?run='+self.run) as response:
                self.assertEqual(json.load(response)['total'],2)
            body=json.dumps({'run':self.run,'case':self.c['id'],'verdict':'plausible'}).encode()
            bad=Request(base+'/api/entries/review',data=body,headers={'Content-Type':'application/json','Origin':'https://untrusted.test'})
            with self.assertRaises(HTTPError) as error:urlopen(bad)
            self.assertEqual(error.exception.code,403)
            good=Request(base+'/api/entries/review',data=body,headers={'Content-Type':'application/json','Origin':base})
            with urlopen(good) as response:self.assertTrue(json.load(response)['saved'])
            self.assertEqual(h.detail(self.run,self.c['id'])['review']['verdict'],'plausible')
        finally:
            server.shutdown();server.server_close();thread.join(timeout=2)

    def test_actual_backup_restore_preserves_cases_reviews_and_dataset_reference(self):
        from datasets import save_dataset
        from test_research import fixture_sources
        import maintenance
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            with patch.dict(os.environ,{'TORI_DATA_DIR':str(root/'live')}):
                dataset=save_dataset('TEST',fixture_sources())
                c=sample();c['datasetId']=dataset
                run=h.store_run({**manifest(),'datasetId':dataset},[c])
                h.review(run,c['id'],'wrong_line','Backup test')
                maintenance.backup(root/'backup')
                maintenance.restore(root/'backup',root/'restored')
            with patch.dict(os.environ,{'TORI_DATA_DIR':str(root/'restored')}):
                self.assertEqual(h.detail(run,c['id'])['review']['note'],'Backup test')
                self.assertEqual(h.run_info(run)['datasetId'],dataset)
                self.assertTrue((root/'restored'/'datasets'/(dataset+'.json')).is_file())
