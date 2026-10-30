import json
import os
from pathlib import Path
import tempfile
import threading
import subprocess
import sys
import time
import unittest
from unittest.mock import patch
from datetime import datetime, timezone

import history_archive as archive
from database import connection
from models import Bar, DataError
from provider_budget import reserve, cooldown
from lab_data import session_bounds

UTC = timezone.utc


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)/'data'
        self.env = patch.dict(os.environ, {'TORI_DATA_DIR': str(self.root), 'TORI_API_REQUESTS_PER_MINUTE': '2'})
        self.env.start()

    def tearDown(self):
        self.env.stop(); self.temp.cleanup()

    def spec(self):
        return {'symbols': ['AAPL'], 'start': '2016-01-01T00:00:00Z', 'end': '2016-02-01T00:00:00Z',
                'universe': {'sources': [{'url': 'https://example.org', 'asOf': '2026-10-28'}]}}

    def bars(self, day='2016-01-04'):
        start, end = session_bounds(day)
        return [Bar(t, t+300, 100., 101., 99., 100.5, 20.) for t in range(start, end, 300)]

    def raw(self, bars):
        return [{'t': datetime.fromtimestamp(b.time, UTC).isoformat(),
                 'o': b.open, 'h': b.high, 'l': b.low, 'c': b.close, 'v': b.volume} for b in bars]

    def test_full_2016_range_frozen_cutoff_and_universe_validation(self):
        spec = self.spec(); spec['end'] = '2026-10-01T00:00:00Z'
        job = archive.create(spec)
        self.assertEqual(len(list(archive.months(archive.stamp(job['spec']['start']), archive.stamp(job['spec']['end'])))), 129)
        for bad in ({**spec, 'symbols': ['AAPL', 'AAPL']}, {**spec, 'end': '2999-01-01T00:00:00Z'},
                    {**spec, 'universe': {}}, {**spec, 'start': '2015-01-01T00:00:00Z'}):
            with self.assertRaises(DataError): archive.create(bad)

    def test_cross_connection_rate_reservations_and_cooldown(self):
        self.assertEqual(reserve(100), 0)
        self.assertEqual(reserve(100), 0)
        self.assertEqual(reserve(101), 59)
        self.assertEqual(reserve(160), 0)
        with patch('provider_budget.time.time', return_value=160): cooldown(30)
        self.assertEqual(reserve(161), 29)

    def test_atomic_rate_reservations_under_thread_contention(self):
        results = []
        threads = [threading.Thread(target=lambda: results.append(reserve(100))) for _ in range(8)]
        # Initialize schema before concurrent use; migration race has its own tests.
        with connection(): pass
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertEqual(results.count(0), 2)
        self.assertEqual(len(results), 8)

    def test_explicit_global_limit_is_ceiling_for_fast_callers(self):
        # setUp configures two requests/minute, including callers asking for190.
        self.assertEqual(reserve(100,limit=190),0)
        self.assertEqual(reserve(100,limit=190),0)
        self.assertEqual(reserve(100,limit=190),60)

    def test_budget_is_shared_with_independent_python_processes(self):
        self.assertEqual(reserve(100), 0)
        command = [sys.executable, '-c', 'from provider_budget import reserve; print(reserve(100))']
        with subprocess.Popen(command, stdout=subprocess.PIPE, text=True) as first, \
                subprocess.Popen(command, stdout=subprocess.PIPE, text=True) as second:
            values = sorted([float(first.communicate(timeout=20)[0]), float(second.communicate(timeout=20)[0])])
            self.assertEqual((first.returncode, second.returncode), (0, 0))
        self.assertEqual(values, [0, 60])

    def test_parquet_roundtrip_corruption_and_path_guard(self):
        bars = self.bars()
        entry = archive.write_chunk(bars)
        self.assertEqual(archive.read_chunk(entry), bars)
        with self.assertRaises(DataError): archive.read_chunk({**entry, 'path': '../secret'})
        (self.root/entry['path']).write_bytes(b'broken')
        with self.assertRaises(DataError): archive.read_chunk(entry)

    def fetch(self, replies):
        spec = self.spec()
        with patch('history_archive.alpaca._request', side_effect=replies) as request:
            result = archive.fetch_month('AAPL', archive.stamp(spec['start']), archive.stamp(spec['end']),
                                         {**spec, 'feed': 'sip', 'adjustment': 'split'}, 'fake', 'fake', lambda *a: None, lambda: False)
        return result, request

    def test_pagination_empty_short_page_and_rth_filter(self):
        bars = self.bars()[:3]
        extra = Bar(bars[0].time-300, bars[0].time, 100., 101., 99., 100., 10.)
        (fine, report), request = self.fetch([
            {'bars': {'AAPL': self.raw([extra, bars[0]])}, 'next_page_token': 'next'},
            {'bars': {'AAPL': self.raw(bars[1:])}, 'next_page_token': None}])
        self.assertEqual(fine, bars)
        self.assertEqual(report['outsideRegular'], 1)
        self.assertEqual(request.call_args_list[0].args[0]['end'], '2016-01-31T23:59:59+00:00')
        self.assertEqual(report['pages'], 2)

    def test_repeated_token_bad_data_conflicting_duplicate_fail_closed(self):
        raw = self.raw(self.bars()[:1])
        cases = [
            [{'bars': {}, 'next_page_token': 'same'}]*2,
            [{'bars': {'AAPL': [{'t': 'bad'}]}}],
            [{'bars': {'AAPL': raw+[dict(raw[0], c=99.5)]}}],
            [{'bars': {'AAPL': raw}, 'next_page_token': 'a'}, {'bars': {'AAPL': [dict(raw[0], c=99.5)]}}],
        ]
        for replies in cases:
            with self.assertRaises(DataError): self.fetch(replies)

    def test_empty_whole_sessions_counted_without_filling(self):
        fine = self.bars('2016-01-04')+self.bars('2016-01-06')
        report = archive.coverage(fine, archive.stamp('2016-01-04T00:00:00Z'), archive.stamp('2016-01-07T00:00:00Z'))
        self.assertEqual(report['internalEmptySessions'], 1)
        self.assertEqual(report['missing5m'], 78)

    def test_pause_backup_restore_resume_skips_committed_months(self):
        job = archive.create(self.spec())
        stop = threading.Event()
        def fake_fetch(*args):
            return self.bars(), {'pages': 1}
        def interrupted_publish(*args):
            raise InterruptedError()
        with patch('history_archive.alpaca.credentials', return_value=('fake', 'fake')), \
                patch('history_archive.fetch_month', side_effect=fake_fetch), \
                patch('history_archive.publish', side_effect=interrupted_publish):
            archive.run(job['id'], stop)
        self.assertEqual(archive.get(job['id'])['status'], 'paused')
        import maintenance
        backup = Path(self.temp.name)/'backup'
        maintenance.backup(backup)
        restored = Path(self.temp.name)/'restored'
        maintenance.restore(backup, restored)
        with patch.dict(os.environ, {'TORI_DATA_DIR': str(restored)}), \
                patch('history_archive.alpaca.credentials', return_value=('fake', 'fake')), \
                patch('history_archive.fetch_month', side_effect=AssertionError('downloaded twice')), \
                patch('history_archive.publish', return_value={'status': 'completed'}):
            self.assertEqual(archive.run(job['id'])['status'], 'completed')
        # Backup must include staged immutable blocks, even before final datasets exist.
        self.assertTrue(list((backup/'imports/chunks').glob('*.parquet')))

    def test_engine_change_refused_before_provider_access(self):
        job = archive.create(self.spec())
        with patch('history_archive.code_hash', return_value='different'), \
                patch('history_archive.alpaca.credentials', side_effect=AssertionError('provider')):
            with self.assertRaises(DataError): archive.run(job['id'])

    def test_parallel_months_complete_out_of_order_but_publish_sorted(self):
        spec = {**self.spec(), 'end': '2016-03-01T00:00:00Z'}
        job = archive.create(spec)
        def fetch(symbol, start, *args):
            if start.month == 1:
                time.sleep(.08)
                return self.bars('2016-01-04')+self.bars('2016-01-05')+self.bars('2016-01-06'), {'pages': 1}
            return self.bars('2016-02-01')+self.bars('2016-02-02')+self.bars('2016-02-03'), {'pages': 1}
        with patch('history_archive.alpaca.credentials', return_value=('fake', 'fake')), \
                patch('history_archive.fetch_month', side_effect=fetch):
            result = archive.run(job['id'])
        stock = result['stocks']['AAPL']
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(stock['counts']['1D'], 6)
        rows = archive.read_dataset(stock['datasetId'])['material']['bars']['1D']
        self.assertEqual([r['time'] for r in rows], sorted(r['time'] for r in rows))

    def test_failed_month_keeps_other_complete_month_and_resume_only_retries_gap(self):
        spec = {**self.spec(), 'end': '2016-03-01T00:00:00Z'}
        job = archive.create(spec)
        def fetch(symbol, start, *args):
            if start.month == 1:
                time.sleep(.04)
                raise DataError('Provider unavailable', 502)
            return self.bars('2016-02-01')+self.bars('2016-02-02')+self.bars('2016-02-03'), {'pages': 1}
        with patch('history_archive.alpaca.credentials', return_value=('fake', 'fake')), \
                patch('history_archive.fetch_month', side_effect=fetch):
            partial = archive.run(job['id'])
        self.assertEqual(partial['status'], 'partial')
        self.assertEqual(list(partial['stocks']['AAPL']['months']), ['2016-02'])
        with patch('history_archive.alpaca.credentials', return_value=('fake', 'fake')), \
                patch('history_archive.fetch_month', return_value=(self.bars(), {'pages': 1})) as provider:
            result = archive.run(job['id'])
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(provider.call_count, 1)
        self.assertEqual(provider.call_args.args[1].month, 1)

    def test_real_publish_retains_feed_and_normalized_frames(self):
        spec = {**self.spec(), 'feed': 'sip', 'adjustment': 'split'}
        bars = self.bars('2016-01-04')+self.bars('2016-01-05')+self.bars('2016-01-06')
        stock = {'months': {'2016-01': archive.write_chunk(bars)}}
        result = archive.publish('AAPL', stock, spec)
        self.assertEqual(result['status'], 'completed')
        dataset = archive.read_dataset(result['datasetId'])
        self.assertEqual(dataset['material']['feed'], 'sip')
        self.assertEqual(result['counts']['1D'], 3)
        self.assertEqual(result['counts']['4h'], 6)
        self.assertEqual(result['counts']['1h'], 21)
