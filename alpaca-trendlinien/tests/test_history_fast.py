from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

import archive_state as state
import history_fast as fast
import history_archive as old
from models import Bar, DataError
from lab_data import session_bounds
import maintenance
from history_http import Client

UTC = timezone.utc


class FastArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)/'data'
        self.env = patch.dict(os.environ, {'TORI_DATA_DIR': str(self.root)})
        self.env.start()

    def tearDown(self): self.env.stop(); self.temp.cleanup()

    def spec(self):
        return {'symbols': ['AAPL'], 'start': '2016-01-01T00:00:00Z', 'end': '2016-04-01T00:00:00Z',
                'universe': {'sources': [{'url': 'https://example.org', 'asOf': '2026-10-29'}]}}

    def bars(self, day):
        s,e = session_bounds(day)
        return [Bar(t,t+300,100.,101.,99.,100.5,20.) for t in range(s,e,300)]

    def raw(self, bars):
        return [{'t':datetime.fromtimestamp(b.time,UTC).isoformat(), 'o':b.open,'h':b.high,'l':b.low,'c':b.close,'v':b.volume} for b in bars]

    def stream(self, replies, emit=None, stop=None):
        job = fast.create(self.spec()); spec = job['spec']; emitted=[]
        with patch('history_fast.Client.request', side_effect=replies) as request:
            fast.stream('AAPL', old.stamp(spec['start']), old.stamp(spec['end']), spec,
                        request, emit or (lambda *args: emitted.append(args)), stop or (lambda:False), lambda *a:None)
        return emitted, request

    def test_multi_month_short_pages_empty_month_and_exact_boundaries(self):
        jan = self.bars('2016-01-04'); march = self.bars('2016-03-01')
        result, request = self.stream([
            {'bars': {'AAPL': self.raw(jan)}, 'next_page_token': 'next'},
            {'bars': {'AAPL': self.raw(march)}, 'next_page_token': None}])
        self.assertEqual([r[0] for r in result], ['2016-01','2016-02','2016-03'])
        self.assertEqual([len(r[3]) for r in result], [78,0,78])
        self.assertEqual(request.call_args_list[0].args[0]['end'], '2016-03-31T23:59:59+00:00')

    def test_bad_page_conflicts_order_tokens_and_wrong_symbols(self):
        raw = self.raw(self.bars('2016-01-04')[:2])
        cases = [
            [{'bars':{'AAPL':[{'t':'bad'}]}}],
            [{'bars':{'OTHER':[]}}],
            [{'bars':{'AAPL':raw[::-1]}}],
            [{'bars':{'AAPL':[raw[0],dict(raw[0],c=99.5)]}}],
            [{'bars':{'AAPL':raw},'next_page_token':'same'}]*2,
            [{'bars':{'AAPL':raw},'next_page_token':'a'},{'bars':{'AAPL':[raw[0]]}}],
        ]
        for replies in cases:
            with self.assertRaises(DataError): self.stream(replies)

    def test_duplicate_identical_page_boundary_is_allowed(self):
        raw=self.raw(self.bars('2016-01-04')[:2])
        result,_=self.stream([{'bars':{'AAPL':raw[:1]},'next_page_token':'a'}, {'bars':{'AAPL':raw}}])
        self.assertEqual(len(result[0][3]),2)
        self.assertEqual(result[0][4]['duplicateRows'],1)

    def test_pause_keeps_only_proven_month_and_resume_uses_no_expiring_token(self):
        job=fast.create(self.spec());spec=job['spec'];stop=threading.Event()
        def emit(month,start,end,bars,detail):
            state.checkpoint(job['id'],spec,'AAPL',month,{**fast.write_chunk(bars),'start':start.isoformat(),'end':end.isoformat()})
            stop.set()
        raw=self.raw(self.bars('2016-01-04')+self.bars('2016-02-01'))
        with self.assertRaises(InterruptedError):
            fast.stream('AAPL',old.stamp(spec['start']),old.stamp(spec['end']),spec,
                        lambda p:{'bars':{'AAPL':raw},'next_page_token':'still-more'},emit,stop.is_set,lambda *a:None)
        refs=state.refs(job['id'],'AAPL')
        self.assertEqual(list(refs),['2016-01'])
        missing=list(fast.missing_runs(old.months(old.stamp(spec['start']),old.stamp(spec['end'])),refs))
        self.assertEqual(missing[0][0].month,2)

    def test_direct_typed_parquet_exact_roundtrip_and_corruption(self):
        bars=self.bars('2016-01-04')
        e=fast.write_chunk(bars)
        self.assertEqual(old.read_chunk(e),bars)
        (self.root/e['path']).write_bytes(b'bad')
        with self.assertRaises(DataError):old.read_chunk(e)

    def test_small_records_atomic_cache_and_different_vintage_isolated(self):
        job=fast.create(self.spec());spec=job['spec']
        start,end=next(old.months(old.stamp(spec['start']),old.stamp(spec['end'])))
        entry={**fast.write_chunk(self.bars('2016-01-04')),'start':start.isoformat(),'end':end.isoformat()}
        state.checkpoint(job['id'],spec,'AAPL','2016-01',entry)
        state.checkpoint(job['id'],spec,'AAPL','2016-01',entry)
        self.assertEqual(state.status(job['id'])['checkpointMonths'],1)
        self.assertEqual(state.cached(spec,'AAPL')['2016-01'],entry)
        self.assertEqual(state.cached({**spec,'vintage':'2026-01-01'},'AAPL'),{})
        self.assertNotIn('stocks',state.get(job['id']))
        state.update(job['id'],pauseRequested=True)
        state.update(job['id'],metrics={'pages':5})
        self.assertTrue(state.get(job['id'])['pauseRequested'])

    def test_complete_live_contract_then_cached_second_job_no_provider(self):
        bars=self.bars('2016-01-04')+self.bars('2016-02-01')+self.bars('2016-03-01')
        job=fast.create(self.spec())
        with patch('history_fast.alpaca.credentials',return_value=('fake','fake')), \
                patch('history_fast.Client.request',return_value={'bars':{'AAPL':self.raw(bars)}}):
            result=fast.run(job['id'])
        self.assertEqual(result['status'],'completed')
        ds=old.read_dataset(result['stocks']['AAPL']['datasetId'])
        self.assertEqual(ds['sources']['5m']['mode'],fast.VERSION)
        second=fast.create(self.spec())
        with patch('history_fast.alpaca.credentials',return_value=('fake','fake')), \
                patch('history_fast.Client.request',side_effect=AssertionError('no repeated download')):
            result2=fast.run(second['id'])
        self.assertEqual(result2['status'],'completed')
        self.assertEqual(result2['stocks']['AAPL']['reusedMonths'],3)
        self.assertEqual(result['stocks']['AAPL']['datasetId'],result2['stocks']['AAPL']['datasetId'])

    def test_streamed_checkpoint_survives_real_backup_restore(self):
        job=fast.create(self.spec());spec=job['spec']
        s,e=next(old.months(old.stamp(spec['start']),old.stamp(spec['end'])))
        entry={**fast.write_chunk(self.bars('2016-01-04')),'start':s.isoformat(),'end':e.isoformat()}
        state.checkpoint(job['id'],spec,'AAPL','2016-01',entry)
        target=Path(self.temp.name)/'backup';maintenance.backup(target)
        dest=Path(self.temp.name)/'restore';maintenance.restore(target,dest)
        with patch.dict(os.environ,{'TORI_DATA_DIR':str(dest)}):
            refs=state.refs(job['id'],'AAPL')
            self.assertEqual(old.read_chunk(refs['2016-01']),self.bars('2016-01-04'))
        (target/entry['path']).unlink()
        with self.assertRaises(DataError):maintenance.verify(target)

    def test_adoption_new_job_keeps_old_job_and_rejects_changed_contract(self):
        spec=self.spec();source=old.create(spec)
        s,e=next(old.months(old.stamp(spec['start']),old.stamp(spec['end'])))
        source['stocks']={'AAPL':{'status':'paused','months':{'2016-01':{
            **old.write_chunk(self.bars('2016-01-04')),'start':s.isoformat(),'end':e.isoformat()}}}}
        source['status']='paused';old.write_job(source)
        before=old.get(source['id'])
        job=fast.create({**spec,'asof':old.stamp(spec['end']).date().isoformat()});result=fast.adopt(job['id'],source['id'])
        self.assertEqual(result['checkpointMonths'],1)
        self.assertEqual(old.get(source['id']),before)
        wrong=fast.create({**spec,'adjustment':'raw'})
        with self.assertRaises(DataError):fast.adopt(wrong['id'],source['id'])

    def test_engine_change_and_credentials_failures_visible(self):
        job=fast.create(self.spec())
        with patch('history_fast.code_hash',return_value='different'):
            with self.assertRaises(DataError):fast.run(job['id'])
        with patch('history_fast.alpaca.credentials',side_effect=DataError('Missing key',503)):
            with self.assertRaises(DataError):fast.run(job['id'])
        self.assertEqual(state.get(job['id'])['phase'],'credentials')

    def test_parallel_year_windows_cover_months_once_and_accumulate_stock_pages(self):
        job=fast.create({**self.spec(),'end':'2017-04-01T00:00:00Z'})
        spec=job['spec']
        windows=list(fast.windows(old.stamp(spec['start']),old.stamp(spec['end'])))
        self.assertEqual(len(windows),2)
        self.assertEqual(windows[0][1],windows[1][0])
        def request(params):
            days=['2016-01-04','2016-01-05','2016-01-06'] if params['start'].startswith('2016') else ['2017-01-03','2017-01-04','2017-01-05']
            return {'bars':{'AAPL':self.raw([b for d in days for b in self.bars(d)])}}
        with patch('history_fast.alpaca.credentials',return_value=('fake','fake')), \
                patch('history_fast.Client.request',side_effect=request):
            result=fast.run(job['id'])
        self.assertEqual(result['status'],'completed')
        self.assertEqual(result['checkpointMonths'],15)
        self.assertEqual(result['stocks']['AAPL']['downloadedPages'],2)
        self.assertEqual(result['stocks']['AAPL']['counts']['1D'],6)

    def test_pause_before_run_and_during_adoption_never_starts_provider(self):
        job=fast.create(self.spec());state.update(job['id'],pauseRequested=True)
        with patch('history_fast.alpaca.credentials',side_effect=AssertionError('paused')):
            result=fast.run(job['id'],reset_pause=False)
        self.assertEqual(result['status'],'paused')
        source=old.create(self.spec())
        source['stocks']={'AAPL':{'status':'paused','months':{}}}
        for start,end in old.months(old.stamp(self.spec()['start']),old.stamp(self.spec()['end'])):
            source['stocks']['AAPL']['months'][start.strftime('%Y-%m')]={'count':0,'start':start.isoformat(),'end':end.isoformat()}
        old.write_job(source);new=fast.create({**self.spec(),'asof':'2016-04-01'})
        real=state.checkpoint
        def commit(*args,**kwargs):
            real(*args,**kwargs);state.update(new['id'],pauseRequested=True)
        with patch('history_fast.state.checkpoint',side_effect=commit):
            with self.assertRaises(InterruptedError):fast.adopt(new['id'],source['id'])
        self.assertEqual(state.status(new['id'])['checkpointMonths'],1)
        self.assertEqual(old.get(source['id'])['stocks'],source['stocks'])

    def test_http_reuses_connection_and_shared_throttle_is_counted(self):
        from unittest.mock import MagicMock
        throttled=MagicMock(status=429);throttled.read.return_value=b'{}';throttled.getheader.return_value='1'
        ok=MagicMock(status=200);ok.read.return_value=b'{"bars":{}}'
        with patch('history_http.http.client.HTTPSConnection') as ctor, \
                patch('history_http.wait'),patch('history_http.cooldown') as cooldown,patch('history_http.time.sleep'):
            ctor.return_value.getresponse.side_effect=[throttled,ok,ok]
            client=Client('fake-key','fake-secret')
            client.request({});client.request({});client.close()
        self.assertEqual(ctor.call_count,1)
        self.assertEqual(client.metrics['attempts'],3)
        self.assertEqual(client.metrics['retries'],1)
        cooldown.assert_called_once_with(1)

    def test_corrupt_reusable_checkpoint_fails_closed_without_download(self):
        job=fast.create(self.spec());spec=job['spec'];start,end=next(old.months(old.stamp(spec['start']),old.stamp(spec['end'])))
        entry={**fast.write_chunk(self.bars('2016-01-04')),'start':start.isoformat(),'end':end.isoformat()}
        state.checkpoint(job['id'],spec,'AAPL','2016-01',entry)
        (self.root/entry['path']).write_bytes(b'corrupted')
        another=fast.create(self.spec())
        with patch('history_fast.alpaca.credentials',return_value=('fake','fake')), \
                patch('history_fast.Client.request',side_effect=AssertionError('must not hide corruption')):
            with self.assertRaises(DataError):fast.run(another['id'])
        self.assertEqual(state.get(another['id'])['status'],'failed')

    def test_symbol_asof_is_separate_from_historical_price_cutoff(self):
        job=fast.create({**self.spec(),'vintage':'2026-10-29'})
        self.assertEqual(job['spec']['asof'],'2026-10-29')
        self.assertTrue(job['spec']['end'].startswith('2016-04-01'))
        with self.assertRaises(DataError):fast.create({**self.spec(),'asof':'invalid'})


if __name__=='__main__':unittest.main()
