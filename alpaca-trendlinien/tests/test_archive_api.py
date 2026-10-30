import json
import os
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import archive_state as state
import archive_api as api
import history_fast as fast
from database import connection
from server import Handler


class ArchiveApiTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.env=patch.dict(os.environ,{'TORI_DATA_DIR':self.temp.name});self.env.start()
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.url=f'http://127.0.0.1:{self.server.server_port}'
        with connection() as db:
            state.put(db,'universe:v1:dow30',{'name':'Dow test','members':[{'symbol':'AAPL'}],
                'sources':[{'url':'https://example.org','asOf':'2026-10-28','sha256':'abc'}],'asOf':'2026-10-28'})
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.env.stop();self.temp.cleanup()
    def post(self,path,body,origin=True,token=None):
        headers={'Content-Type':'application/json'}
        if origin:headers['Origin']=self.url
        if token:headers['Authorization']='Bearer '+token
        return urllib.request.urlopen(urllib.request.Request(self.url+path,json.dumps(body).encode(),headers),timeout=10)

    def test_read_only_inventory_does_not_download_or_access_credentials(self):
        with patch('alpaca.credentials',side_effect=AssertionError('credentials')), \
                patch('universe_catalog.urllib.request.urlopen',side_effect=AssertionError('provider')):
            self.assertEqual(api.get('/api/archive/universes',{})['marketProviderCalls'],0)
            self.assertEqual(api.inventory(['dow30'])['uniqueStocks'],1)
            self.assertEqual(api.get('/api/archive/jobs',{})['items'],[])

    def test_create_freezes_members_and_does_not_start_network(self):
        with patch('history_fast.alpaca.credentials',side_effect=AssertionError('no download on create')):
            with self.post('/api/archive/jobs',{'universes':['dow30'],'end':'2026-10-01T00:00:00Z'}) as response:
                job=json.load(response)
        self.assertEqual(job['status'],'pending')
        self.assertEqual(job['spec']['symbols'],['AAPL'])
        with connection() as db:state.put(db,'universe:v1:dow30',{'name':'Changed','members':[],'sources':[]})
        self.assertEqual(state.get(job['id'])['spec']['symbols'],['AAPL'])
        with self.post('/api/archive/jobs/'+job['id']+'/pause',{}) as response:paused=json.load(response)
        self.assertEqual(paused['status'],'paused')

    def test_existing_host_origin_and_bearer_guards_preserved(self):
        with self.assertRaises(urllib.error.HTTPError) as exc:self.post('/api/archive/jobs',{'universes':['dow30']},origin=False)
        self.assertEqual(exc.exception.code,403)
        self.server.api_token='TEST-ONLY'
        with self.assertRaises(urllib.error.HTTPError) as exc:self.post('/api/archive/jobs',{'universes':['dow30']})
        self.assertEqual(exc.exception.code,401)
        with self.post('/api/archive/jobs',{'universes':['dow30'],'end':'2026-10-01T00:00:00Z'},origin=False,token='TEST-ONLY') as response:
            self.assertEqual(json.load(response)['status'],'pending')

    def test_collector_static_page_available_private_sources_stay_hidden(self):
        with urllib.request.urlopen(self.url+'/sammler') as response:self.assertIn('Universen auswählen',response.read().decode())
        for path in ('/archive_state.py','/data/research/jobs.sqlite3'):
            with self.assertRaises(urllib.error.HTTPError) as exc:urllib.request.urlopen(self.url+path)
            self.assertEqual(exc.exception.code,404)

    def test_large_job_list_omits_stock_payload_and_detail_is_bounded(self):
        symbols=['Z'+str(n) for n in range(500)]
        job=fast.create({'symbols':symbols,'end':'2026-10-01T00:00:00Z',
                         'universe':{'name':'Large fixture','members':[{'symbol':s,'name':'Fixture'} for s in symbols],
                                     'sources':[{'url':'https://example.org'}]}})
        listing=api.get('/api/archive/jobs',{})
        self.assertNotIn('stocks',listing['items'][0])
        self.assertNotIn('members',listing['items'][0]['universe'])
        self.assertLess(len(json.dumps(listing)),10000)
        detail=api.get('/api/archive/jobs/'+job['id'],{'limit':['99999'],'offset':['0']})
        self.assertEqual(len(detail['stocks']),200);self.assertEqual(detail['totalStocks'],500)
        tail=api.get('/api/archive/jobs/'+job['id'],{'offset':['499']})
        self.assertEqual(len(tail['stocks']),1)
        with self.assertRaises(Exception):api.get('/api/archive/jobs/'+job['id'],{'limit':['bad']})
