import json
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import alpaca
import snapshots
from alpaca import Bar, NY, DataError, load_bars
from server import chart_payload, parse_cutoff
from trendlines import Rules, build

UTC=timezone.utc
NOW=datetime(2026,10,17,12,tzinfo=UTC)
CUTOFF=datetime(2026,10,14,13,tzinfo=NY)


def dataset(tf):
    result=[]
    for day in [8,9,12,13,14,15,16]:
        hours=[0] if tf=='1D' else [8,12] if tf=='4h' else [9,10,11,12,13,14,15]
        for hour in hours:
            t=datetime(2026,10,day,hour,tzinfo=NY)
            end=t.replace(hour=16) if tf=='1D' else t+timedelta(hours=4 if tf=='4h' else 1)
            p=100-len(result)*.1
            result.append(Bar(int(t.timestamp()),int(end.timestamp()),p,p+1,p-1,p,10))
    return result


def metadata(bars):
    return {'quality':{'rejected':0,'duplicates':0,'unfinished':0},'first':bars[0].time,'last':bars[-1].time,'lastClose':bars[-1].end,'count':len(bars),'pages':1,'mode':'cache','cached':True,'fetchedAt':NOW.isoformat()}


class CausalHistoryTests(unittest.TestCase):
    def test_cutoff_timezone_and_invalid_future_or_dst_times(self):
        self.assertEqual(parse_cutoff('2026-10-14T13:00',NOW),CUTOFF.astimezone(UTC))
        self.assertEqual(parse_cutoff('2026-10-14T17:00:00Z',NOW),CUTOFF.astimezone(UTC))
        for stamp in ['not-a-date','2026-10-18T12:00','2026-03-08T02:30','2025-11-02T01:30']:
            with self.assertRaises(DataError): parse_cutoff(stamp,NOW)

    def test_future_candles_cannot_change_historical_lines_events_or_fingerprint(self):
        def load(symbol,tf,**kwargs):
            bars=dataset(tf)
            return bars,metadata(bars)
        with patch('server.load_bars',side_effect=load):
            before=chart_payload('TEST','1h',as_of=CUTOFF.isoformat())
        def future_shock(symbol,tf,**kwargs):
            bars=[replace(b,high=999999,low=.001,close=999998) if b.end>CUTOFF.timestamp() else b for b in dataset(tf)]
            return bars,metadata(bars)
        with patch('server.load_bars',side_effect=future_shock):
            after=chart_payload('TEST','1h',as_of=CUTOFF.isoformat())
        self.assertEqual(before['lanes'],after['lanes'])
        self.assertEqual(before['charts'],after['charts'])
        self.assertEqual(before['fingerprint'],after['fingerprint'])
        self.assertEqual(before['analysisId'],after['analysisId'])
        for tf,chart in before['charts'].items():
            self.assertTrue(all(b['end']<=CUTOFF.timestamp() for b in chart['bars']))
            self.assertTrue(all(r['b_time']<=CUTOFF.timestamp() for r in [before['lanes'][tf]['red'],before['lanes'][tf]['green']] if r))
        daily=before['charts']['1D']['bars']
        self.assertEqual(datetime.fromtimestamp(daily[-1]['time'],NY).day,13)
        self.assertEqual(datetime.fromtimestamp(before['charts']['4h']['bars'][-1]['time'],NY).hour,8)
        self.assertEqual(datetime.fromtimestamp(before['charts']['1h']['bars'][-1]['time'],NY).hour,12)

    def test_past_adapter_reuses_cache_but_never_examines_future_ohlc(self):
        with tempfile.TemporaryDirectory() as directory,patch('alpaca.ROOT',Path(directory)):
            path=Path(directory)/'data/market/TEST_1h_iex_raw.json';path.parent.mkdir(parents=True)
            rows=[{'t':datetime.fromtimestamp(b.time,UTC).isoformat(),'o':b.open,'h':b.high,'l':b.low,'c':b.close,'v':b.volume} for b in dataset('1h')]
            for row in rows:
                if datetime.fromisoformat(row['t']).timestamp()>CUTOFF.timestamp(): row['h']='invalid-future-price'
            path.write_text(json.dumps({'symbol':'TEST','timeframe':'1h','feed':'iex','adjustment':'raw','requested_start':'2025-07-01T00:00:00+00:00','requested_end':NOW.isoformat(),'fetched_at':NOW.timestamp(),'pages':1,'bars':rows}),'utf-8')
            with patch('alpaca._request') as request:
                bars,meta=load_bars('TEST','1h',now=NOW,end=CUTOFF)
                request.assert_not_called()
            self.assertTrue(all(b.end<=CUTOFF.timestamp() for b in bars))
            self.assertEqual(meta['quality']['rejected'],0)

    def test_older_history_requests_a_full_window_ending_at_cutoff(self):
        end=datetime(2024,10,14,20,tzinfo=UTC)
        rows=[{'t':f'2024-10-{day:02}T14:00:00Z','o':100,'h':101,'l':99,'c':100,'v':1} for day in [10,11,14]]
        seen=[]
        def request(params,*args): seen.append(dict(params));return {'bars':{'TEST':rows}}
        with tempfile.TemporaryDirectory() as directory,patch('alpaca.ROOT',Path(directory)),patch('alpaca.credentials',return_value=('test','test')),patch('alpaca._request',side_effect=request):
            bars,meta=load_bars('TEST','1h',now=NOW,end=end)
        self.assertEqual(datetime.fromisoformat(seen[0]['end']),end)
        self.assertLess(datetime.fromisoformat(seen[0]['start']),end-timedelta(days=440))
        self.assertEqual(seen[0]['asof'],NOW.date().isoformat())

    def test_candle_slope_does_not_add_fake_weekend_bars(self):
        hours=[datetime(2026,10,9,14,tzinfo=NY),datetime(2026,10,9,15,tzinfo=NY),datetime(2026,10,12,9,tzinfo=NY),datetime(2026,10,12,10,tzinfo=NY),datetime(2026,10,12,11,tzinfo=NY)]
        bars=[Bar(int(t.timestamp()),int((t+timedelta(hours=1)).timestamp()),p,p+1,p-1,p,1) for t,p in zip(hours,[100,99,98,97,95])]
        ray=build(bars,True,Rules())[0]
        self.assertEqual(ray.basis,'bars')
        self.assertEqual(ray.slope,-1)
        self.assertAlmostEqual(ray.value(bars[2].time),99)
        self.assertEqual(ray.contacts,4)


class SnapshotTests(unittest.TestCase):
    def test_snapshot_is_exact_immutable_and_survives_memory_reset(self):
        with tempfile.TemporaryDirectory() as directory,patch('snapshots.ROOT',Path(directory)):
            with patch('server.load_bars',side_effect=lambda symbol,tf,**kw:(dataset(tf),metadata(dataset(tf)))):
                payload=chart_payload('TEST','1h',as_of=CUTOFF.isoformat())
            identity=payload['analysisId']
            saved=snapshots.save_snapshot(identity)
            original=json.dumps(saved,sort_keys=True)
            payload['charts']['1h']['bars'][-1]['close']=100000
            snapshots._analyses.pop(identity,None)
            reopened=snapshots.read_snapshot(identity)
            self.assertEqual(json.dumps(reopened,sort_keys=True),original)
            self.assertEqual(snapshots.save_snapshot(identity),reopened)
            self.assertEqual(snapshots.list_snapshots('TEST')[0]['id'],identity)
            self.assertEqual(snapshots.list_snapshots('OTHER'),[])
            self.assertLessEqual(saved['validFrom'],saved['analysisCutoff'])

    def test_snapshot_paths_and_unknown_analysis_are_rejected(self):
        for identity in ['../private','none','x'*24]:
            with self.assertRaises(DataError): snapshots.read_snapshot(identity)
        with tempfile.TemporaryDirectory() as directory,patch('snapshots.ROOT',Path(directory)):
            with self.assertRaises(DataError) as error: snapshots.save_snapshot('a'*24)
            self.assertEqual(error.exception.status,409)


if __name__=='__main__':unittest.main()
