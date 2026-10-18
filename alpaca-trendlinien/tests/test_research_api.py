import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from server import Handler


class ResearchApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.env=patch.dict(os.environ,{'TORI_DATA_DIR':cls.temp.name})
        cls.env.start()
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.server.api_token='test-token-only'
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.url=f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join()
        cls.env.stop();cls.temp.cleanup()

    def request(self,path,body=None,headers=None):
        request=urllib.request.Request(self.url+path,data=json.dumps(body).encode() if body is not None else None,
            headers={'Authorization':'Bearer test-token-only','Content-Type':'application/json',**(headers or {})})
        with urllib.request.urlopen(request) as response:return response.status,json.load(response)

    def test_machine_job_roundtrip_status_cancel_and_report(self):
        status,job=self.request('/api/research/jobs',{'symbols':['MSFT'],'samples':2})
        self.assertEqual(status,202)
        identity=job['id']
        self.assertEqual(self.request('/api/research/jobs/'+identity)[1]['status'],'queued')
        self.assertEqual(self.request('/api/research/jobs/'+identity+'/report')[1]['summary']['trials'],0)
        self.assertEqual(self.request('/api/research/jobs/'+identity+'/events')[1]['items'],[])
        self.assertEqual(self.request('/api/research/jobs/'+identity+'/cancel',{})[1]['status'],'cancelled')

    def test_remote_access_requires_auth_and_same_origin(self):
        for path in ('/research','/api/research/jobs'):
            with self.assertRaises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(self.url+path)
            self.assertEqual(error.exception.code,401)
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request('/api/research/jobs',{}, {'Origin':'https://foreign.example'})
        self.assertEqual(error.exception.code,403)

    def test_invalid_research_and_dataset_requests_do_not_start_download(self):
        with patch('jobs.import_dataset') as imported:
            for path,body in [('/api/research/jobs',{'samples':-1}),('/api/research/schedule',{'enabled':'yes'})]:
                with self.assertRaises(urllib.error.HTTPError) as error:self.request(path,body)
                self.assertEqual(error.exception.code,400)
            with self.assertRaises(urllib.error.HTTPError) as error:self.request('/api/dataset-chart?dataset=../private')
            self.assertEqual(error.exception.code,400)
            imported.assert_not_called()

    def test_research_static_files_are_available_but_database_is_not(self):
        for path in ('/research','/research.js','/research.css'):
            request=urllib.request.Request(self.url+path,headers={'Authorization':'Bearer test-token-only'})
            with urllib.request.urlopen(request) as response:self.assertEqual(response.status,200)
        with self.assertRaises(urllib.error.HTTPError) as error:self.request('/data/research/jobs.sqlite3')
        self.assertEqual(error.exception.code,404)

    def test_events_cursor_http_and_cli_return_the_same_bounded_page(self):
        import jobs
        import subprocess
        import sys
        import urllib.parse
        identity=jobs.submit({})['id']
        with jobs.connection() as db:
            db.executemany('INSERT INTO events VALUES(?,?,?,?)',[(identity,str(i),'dataset',json.dumps({'id':str(i)})) for i in range(4)])
        page=self.request('/api/research/jobs/'+identity+'/events?limit=2')[1]
        cli=json.loads(subprocess.check_output([sys.executable,'tori.py','events','--id',identity,'--limit','2'],env=os.environ))
        self.assertEqual(page,cli)
        following=self.request('/api/research/jobs/'+identity+'/events?limit=2&cursor='+urllib.parse.quote(page['page']['nextCursor']))[1]
        self.assertEqual([e['id'] for e in following['items']],['2','3'])
        for query in ('limit=0','limit=1001','cursor=garbage'):
            with self.assertRaises(urllib.error.HTTPError) as error:self.request('/api/research/jobs/'+identity+'/events?'+query)
            self.assertEqual(error.exception.code,400)

    def test_health_has_local_operating_state_without_market_download(self):
        with patch('alpaca._request',side_effect=AssertionError('no provider call')):
            value=self.request('/api/health')[1]
        self.assertIn('heartbeatAgeSeconds',value['operations']['worker'])
        self.assertEqual(value['operations']['readiness']['providerAuthentication'],'not_checked_by_health')


if __name__=='__main__':unittest.main()
