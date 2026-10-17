import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import alpaca
import assets
from alpaca import DataError, load_bars

NOW = datetime(2026, 10, 17, 12, tzinfo=timezone.utc)


def rows():
    return [{'t': f'2026-10-{day:02}T14:00:00Z', 'o': 100, 'h': 105, 'l': 99, 'c': 102, 'v': 10}
            for day in (12, 13, 14, 15, 16)]


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.patch = patch('alpaca.ROOT', self.root)
        self.patch.start()
        self.auth = patch('alpaca.credentials', return_value=('fake', 'fake'))
        self.auth.start()

    def tearDown(self):
        self.auth.stop()
        self.patch.stop()
        self.temp.cleanup()

    def test_long_intraday_import_follows_more_than_twenty_small_pages(self):
        start=NOW-timedelta(days=30)
        pages=[]
        for i in range(23):
            row={'t':(start+timedelta(hours=i)).isoformat(),'o':100,'h':105,'l':99,'c':102,'v':10}
            pages.append({'bars':{'MSFT':[row]},**({'next_page_token':f'page-{i+1}'} if i<22 else {})})
        with patch('alpaca._request',side_effect=pages) as request:
            bars,meta=load_bars('MSFT','1h',now=NOW,history_days=900)
        self.assertEqual(request.call_count,23)
        self.assertEqual(meta['pages'],23)
        self.assertEqual(len(bars),23)

    def test_initial_pagination_then_no_network_then_incremental_correction(self):
        with patch('alpaca._request', side_effect=[{'bars': {'MSFT': rows()[:3]}, 'next_page_token': 'p2'},
                                                   {'bars': {'MSFT': rows()[3:]}}]) as request:
            bars, meta = load_bars('MSFT', '1h', now=NOW)
            self.assertEqual(len(bars), 5)
            self.assertEqual(meta['pages'], 2)
            self.assertEqual(request.call_args_list[0].args[0]['page_token'], 'p2')
        with patch('alpaca._request') as request:
            again, meta = load_bars('MSFT', '1h', now=NOW + timedelta(seconds=60))
            request.assert_not_called()
            self.assertTrue(meta['cached'])
            self.assertEqual(again, bars)
        params_seen = []
        def revised(params, *args):
            params_seen.append(dict(params))
            return {'bars': {'MSFT': [dict(rows()[-1], c=104)]}}
        with patch('alpaca._request', side_effect=revised):
            updated, meta = load_bars('MSFT', '1h', now=NOW + timedelta(minutes=6))
        self.assertEqual(meta['mode'], 'incremental')
        self.assertEqual(len(updated), 5)
        self.assertEqual(updated[-1].close, 104)
        self.assertGreater(datetime.fromisoformat(params_seen[0]['start']), NOW - timedelta(days=8))
        with patch('alpaca._request', side_effect=revised) as request:
            load_bars('MSFT', '1h', now=NOW + timedelta(minutes=7), force=True)
            self.assertEqual(request.call_count, 1)
        self.assertGreater(datetime.fromisoformat(params_seen[-1]['start']), NOW - timedelta(days=8))

    def test_failed_update_reports_stale_and_preserves_disk(self):
        with patch('alpaca._request', return_value={'bars': {'MSFT': rows()}}):
            load_bars('MSFT', '1h', now=NOW)
        path = self.root / 'data/market/MSFT_1h_iex_raw.json'
        original = path.read_bytes()
        with patch('alpaca._request', side_effect=DataError('offline')):
            bars, meta = load_bars('MSFT', '1h', force=True, now=NOW+timedelta(days=1))
        self.assertEqual(len(bars), 5)
        self.assertEqual(meta['mode'], 'stale')
        self.assertTrue(meta['warning'])
        self.assertEqual(path.read_bytes(), original)

    def test_different_intervals_download_in_parallel(self):
        barrier = threading.Barrier(3, timeout=3)
        def download(*args):
            barrier.wait()
            return {'bars': {'MSFT': rows()}}
        with patch('alpaca._request', side_effect=download):
            with ThreadPoolExecutor(max_workers=3) as pool:
                results = list(pool.map(lambda tf: load_bars('MSFT', tf, now=NOW), ['1h','4h','1D']))
        self.assertTrue(all(len(bars)==5 for bars, _ in results))

    def test_same_file_requests_share_download(self):
        with patch('alpaca._request', return_value={'bars': {'MSFT': rows()}}) as download:
            with ThreadPoolExecutor(max_workers=3) as pool:
                list(pool.map(lambda _: load_bars('MSFT', '1h', now=NOW), range(3)))
        self.assertEqual(download.call_count, 1)

    def test_symbol_with_slash_cannot_make_subdirectories(self):
        with patch('alpaca._request', return_value={'bars': {'BRK/A': rows()}}):
            load_bars('BRK/A', '1h', now=NOW)
        self.assertTrue((self.root/'data/market/BRK%2FA_1h_iex_raw.json').exists())


class AssetTests(unittest.TestCase):
    def test_only_listed_active_equities_and_no_fixed_symbol_whitelist(self):
        base={'symbol':'NEW','name':'New Company','exchange':'NASDAQ','class':'us_equity','status':'active','tradable':True}
        data=assets.normalize_assets([base, dict(base,symbol='PINK',exchange='OTC'),
            dict(base,symbol='OLD',status='inactive'),dict(base,symbol='COIN',**{'class':'crypto'}),
            dict(base,symbol='BRK/A'),dict(base,symbol='A/B',tradable=False)])
        self.assertEqual([a['symbol'] for a in data], ['A/B','BRK/A','NEW'])

    def test_name_search_ranking_pagination_and_favorite_filter(self):
        catalog={'items':[{'symbol':f'AAA{i}','name':'Alpha Company','exchange':'NYSE'} for i in range(105)] +
            [{'symbol':'MSFT','name':'Microsoft Corporation','exchange':'NASDAQ'}], 'fetchedAt':0}
        with patch('assets.directory',return_value=(catalog,False)):
            self.assertEqual(assets.search_assets('microsoft')['items'][0]['symbol'],'MSFT')
            self.assertEqual(len(assets.search_assets('Alpha')['items']),100)
            self.assertEqual(len(assets.search_assets('Alpha',offset=100)['items']),5)
            self.assertEqual(assets.search_assets(exchange='NASDAQ')['total'],1)
            self.assertEqual(assets.search_assets(symbols=set())['total'],0)
            self.assertEqual(assets.search_assets(symbols={'MSFT'})['total'],1)


if __name__ == '__main__': unittest.main()
