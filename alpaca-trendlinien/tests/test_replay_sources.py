from dataclasses import replace
from datetime import datetime,timezone
import unittest
from unittest.mock import patch

import replay_sources as replay
from analysis_service import build_chart
from server import chart_payload
from test_history import dataset,metadata,CUTOFF


class ReplaySourceTests(unittest.TestCase):
    def setUp(self):
        replay.clear();self.rows=dataset('4h');self.meta={'feed':'iex','adjustment':'raw','normalization':'native'}
    def tearDown(self):replay.clear()
    def source(self,rows):return {'4h':(rows,self.meta)}

    def test_overlap_verified_append_keeps_original_warmup_and_out_of_order_responses_do_not_shrink(self):
        key,_=replay.remember('TEST',self.source(self.rows[:6]),self.rows[5].end)
        newer,rows=replay.remember('TEST',self.source(self.rows[2:9]),self.rows[8].end,key)
        self.assertEqual(newer,key);self.assertEqual(rows['4h'][0],self.rows[:9])
        same,rows=replay.remember('TEST',self.source(self.rows[1:8]),self.rows[7].end,key)
        self.assertEqual(same,key);self.assertEqual(rows['4h'][0],self.rows[:9])
        self.assertIsNotNone(replay.covered(key,'TEST',self.rows[8].end))

    def test_revised_disappeared_and_changed_convention_start_another_source(self):
        for changed in (self.rows[:2]+[replace(self.rows[2],close=self.rows[2].close+.01)]+self.rows[3:],
                        self.rows[:2]+self.rows[3:]):
            key,_=replay.remember('TEST',self.source(self.rows[:8]),self.rows[7].end)
            other,_=replay.remember('TEST',self.source(changed),changed[-1].end,key)
            self.assertNotEqual(key,other)
        key,_=replay.remember('TEST',self.source(self.rows),self.rows[-1].end)
        other,_=replay.remember('TEST',{'4h':(self.rows,{**self.meta,'adjustment':'split'})},self.rows[-1].end,key)
        self.assertNotEqual(key,other)
        key,_=replay.remember('TEST',self.source(self.rows[:2]+self.rows[3:8]),self.rows[7].end)
        other,_=replay.remember('TEST',self.source(self.rows),self.rows[-1].end,key)
        self.assertNotEqual(key,other,'an inserted historical candle is a revision, not an append')
        key,_=replay.remember('TEST',{'4h':(self.rows,{**self.meta,'quality':{'rejected':1}})},self.rows[-1].end)
        self.assertIsNone(replay.covered(key,'TEST',self.rows[5].end))

    def test_ranges_symbols_and_memory_boundaries_are_not_silently_crossed(self):
        key,_=replay.remember('TEST',self.source(self.rows[:8]),self.rows[7].end)
        self.assertIsNone(replay.covered(key,'OTHER',self.rows[5].end))
        self.assertIsNone(replay.covered(key,'TEST',self.rows[1].end))
        self.assertIsNone(replay.covered(key,'TEST',self.rows[8].end))
        for name in ('OTHER','THIRD'):replay.remember(name,self.source(self.rows),self.rows[-1].end)
        self.assertEqual(len(replay._sources),2);self.assertIsNone(replay.covered(key,'TEST',self.rows[5].end))
        replay.clear()
        with patch.object(replay,'MAX_BARS',2):
            key,_=replay.remember('TEST',self.source(self.rows),self.rows[-1].end)
            self.assertIsNone(key);self.assertEqual(len(replay._sources),0)

    def test_backward_chart_never_calls_provider_and_each_source_interval_is_cut_before_analysis(self):
        inputs={tf:(dataset(tf),metadata(dataset(tf))) for tf in ('1h','4h','1D')}
        later=datetime.fromtimestamp(inputs['1D'][0][-1].end,timezone.utc)
        with patch('server.load_bars',side_effect=lambda symbol,tf,**kw:inputs[tf]),patch('server.remember'):
            current=chart_payload('TEST','4h',as_of=later.isoformat())
        with patch('server.load_bars',side_effect=AssertionError('No provider during rewind')),patch('server.remember'):
            prior=chart_payload('TEST','4h',as_of=CUTOFF.isoformat(),replay_source=current['replaySourceId'])
        expected=build_chart(inputs,'TEST','4h',CUTOFF,datetime.now(timezone.utc),historical=True)
        for key in ('1h','4h','1D'):
            self.assertEqual(prior['charts'][key],expected['charts'][key])
            self.assertEqual(prior['lanes'][key],expected['lanes'][key])
        self.assertTrue(all(b['end']<=CUTOFF.timestamp() for c in prior['charts'].values() for b in c['bars']))
        self.assertEqual(prior['replaySourceId'],current['replaySourceId'])


if __name__=='__main__':unittest.main()
