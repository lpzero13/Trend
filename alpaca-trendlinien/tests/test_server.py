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


if __name__ == '__main__':
    unittest.main()
