import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from server import APP_ID, Handler
from alpaca import DataError


class ServerTests(unittest.TestCase):
    def test_large_json_uses_negotiated_gzip_without_changing_content_or_cache_policy(self):
        import gzip
        expected={'bars':['known-candle']*3000}
        with patch('server.chart_payload',return_value=expected):
            for encoding,compressed in [('gzip',True),('gzip;q=0',False),('identity',False)]:
                request=urllib.request.Request(self.url+'/api/chart?symbol=TEST',headers={'Accept-Encoding':encoding})
                with urllib.request.urlopen(request) as response:
                    raw=response.read()
                    self.assertEqual(response.headers.get('Content-Encoding'), 'gzip' if compressed else None)
                    self.assertEqual(response.headers.get('Cache-Control'),'no-store')
                    self.assertIn('Accept-Encoding',response.headers.get('Vary',''))
                    self.assertEqual(len(raw),int(response.headers['Content-Length']))
                    if compressed:
                        self.assertLess(len(raw),len(json.dumps(expected).encode())/10)
                        raw=gzip.decompress(raw)
                    self.assertEqual(json.loads(raw),expected)

    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.env = patch.dict(os.environ, {"TORI_DATA_DIR":cls.temp.name})
        cls.env.start()
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.env.stop()
        cls.temp.cleanup()

    def test_health_has_no_secrets(self):
        with patch('server.credentials', return_value=('TEST-KEY', 'TEST-SECRET')):
            with urllib.request.urlopen(self.url + '/api/health') as response:
                body = response.read().decode()
                data = json.loads(body)
        self.assertEqual(data['app'], APP_ID)
        self.assertTrue(data['readOnly'])
        self.assertNotIn('TEST-KEY', body)
        self.assertNotIn('TEST-SECRET', body)

    def test_private_files_cannot_be_served(self):
        for path in ['/config.local.json', '/alpaca.py', '/../config.local.json', '/data/market/AAPL_4h_iex_raw.json', '/data/snapshots/abc.json']:
            with self.assertRaises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(self.url + path)
            self.assertEqual(error.exception.code, 404)

    def test_foreign_host_is_rejected(self):
        request = urllib.request.Request(self.url + '/api/health', headers={'Host': 'foreign.example'})
        with self.assertRaises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(request)
        self.assertEqual(error.exception.code, 403)

    def test_foreign_origin_is_rejected(self):
        request = urllib.request.Request(self.url + '/api/health', headers={'Origin': 'https://foreign.example'})
        with self.assertRaises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(request)
        self.assertEqual(error.exception.code, 403)

    def test_posts_are_rejected(self):
        request = urllib.request.Request(self.url + '/api/chart', data=b'{}', method='POST')
        with self.assertRaises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(request)
        self.assertEqual(error.exception.code, 405)

    def test_symbol_is_validated_before_network(self):
        with patch('server.load_bars') as loader:
            with self.assertRaises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(self.url + '/api/chart?symbol=../../file')
            self.assertEqual(error.exception.code, 400)
            loader.assert_not_called()

    def test_asset_search_route_passes_filters_and_pagination(self):
        with patch('server.search_assets', return_value={'items': [], 'total': 0}) as search:
            with urllib.request.urlopen(self.url + '/api/assets?q=Apple&exchange=NASDAQ&offset=100&symbols=AAPL,MSFT') as response:
                self.assertEqual(json.load(response)['total'], 0)
            search.assert_called_once_with('Apple', 'NASDAQ', 100, {'AAPL', 'MSFT'})

    def test_bad_asset_offset_is_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(self.url + '/api/assets?offset=invalid')
        self.assertEqual(error.exception.code, 400)

    def test_chart_analysis_flag_is_optional_and_explicit(self):
        for query, enabled in [("", True), ("&analysis=0", False), ("&analysis=1", True)]:
            with patch("server.chart_payload", return_value={"analysisEnabled": enabled}) as chart:
                with urllib.request.urlopen(self.url + "/api/chart?symbol=TEST" + query) as response:
                    self.assertEqual(json.load(response)["analysisEnabled"], enabled)
                chart.assert_called_once_with("TEST", "4h", False, None, include_analysis=enabled)
        for value in ("", "true", "no", "1&analysis=0"):
            with patch("server.chart_payload") as chart:
                with self.assertRaises(urllib.error.HTTPError) as error:
                    urllib.request.urlopen(self.url + "/api/chart?symbol=TEST&analysis=" + value)
                self.assertEqual(error.exception.code, 400)
                chart.assert_not_called()

    def test_manual_dataset_link_does_not_resolve_a_research_signal(self):
        with patch("server.chart_dataset", return_value={"analysisEnabled": False}) as chart, \
             patch('server.add_weekly') as weekly, \
             patch("server.jobs.get_trial", side_effect=AssertionError("No signal lookup")) as trial:
            with urllib.request.urlopen(self.url + "/api/dataset-chart?dataset=pinned&job=job&trial=trial&analysis=0") as response:
                self.assertFalse(json.load(response)["analysisEnabled"])
            trial.assert_not_called()
            chart.assert_called_once_with("pinned", "4h", None, None, include_analysis=False)
            weekly.assert_called_once_with({'analysisEnabled':False},'4h')

    def post_snapshot(self, body=b'{}', **headers):
        return urllib.request.urlopen(urllib.request.Request(self.url+'/api/snapshots', data=body,
            headers={'Origin':self.url, 'Content-Type':'application/json', **headers}, method='POST'))

    def test_snapshot_requires_local_origin(self):
        with patch('server.save_snapshot') as save:
            for origin in ['', 'https://foreign.example']:
                with self.assertRaises(urllib.error.HTTPError) as error:
                    self.post_snapshot(Origin=origin)
                self.assertEqual(error.exception.code,403)
            save.assert_not_called()

    def test_snapshot_bad_bodies_are_rejected(self):
        for body, headers in [(b'bad',{}),(b'[]',{}),(b'x'*1025,{}),(b'{}',{'Content-Type':'text/plain'})]:
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.post_snapshot(body,**headers)
            self.assertEqual(error.exception.code,400)

    def test_snapshot_exact_id_and_storage_failure(self):
        with patch('server.save_snapshot',return_value={'id':'abc'}) as save:
            with self.post_snapshot(b'{"analysisId":"abc"}') as response:
                self.assertEqual(response.status,201)
                self.assertEqual(json.load(response),{'id':'abc'})
            save.assert_called_once_with('abc')
        for failure,status in [(OSError('private disk path'),500),(DataError('Reload',409),409)]:
            with patch('server.save_snapshot',side_effect=failure):
                with self.assertRaises(urllib.error.HTTPError) as error:
                    self.post_snapshot(b'{"analysisId":"abc"}')
                self.assertEqual(error.exception.code,status)
                self.assertNotIn('private disk path',error.exception.read().decode())

    def test_replay_transport_routes_keep_origin_and_snapshot_protection(self):
        from test_research import fixture_sources
        import chart_replay
        rows = fixture_sources()
        at = rows['4h'][0][1000].end
        from datetime import datetime, timezone
        stamp = datetime.fromtimestamp(at, timezone.utc).isoformat()
        from urllib.parse import urlencode
        with patch('alpaca.load_bars', side_effect=lambda symbol, tf, **kw: rows[tf]):
            url = self.url+'/api/replay/open?'+urlencode(dict(symbol='TEST', asof=stamp, timeframe='4h', analysis='0'))
            with urllib.request.urlopen(url) as response:
                opened = json.load(response)
        self.assertIn('window', opened)
        self.assertNotIn('bars', opened['view'])
        q = dict(session=opened['window']['id'], asof=stamp, timeframe='4h', analysis='1', engine='fan_master')
        with urllib.request.urlopen(self.url+'/api/replay/view?'+urlencode(q)) as response:
            view = json.load(response)
        self.assertTrue(view['analysisEnabled'])
        self.assertNotIn('bars', view)
        body = json.dumps({'replay': {k: v for k, v in q.items() if k != 'analysis'}}).encode()
        with self.post_snapshot(body) as response:
            snapshot = json.load(response)
            self.assertEqual(snapshot['analysisCutoff'], at)
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.post_snapshot(body, Origin='https://foreign.example')
        self.assertEqual(error.exception.code, 403)
        chart_replay.clear()


if __name__ == '__main__':
    unittest.main()
