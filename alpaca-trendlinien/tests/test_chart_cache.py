from copy import deepcopy
from dataclasses import replace
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch

import chart_lane_cache as lanes
import chart_sources as sources
from datasets import save_dataset,chart_dataset as original_chart,read_dataset
from fan_chart import apply
from models import DataError
from test_history import dataset,metadata,CUTOFF


class LaneCacheTests(unittest.TestCase):
    def setUp(self):lanes.clear()
    def tearDown(self):lanes.clear()

    def test_history_corrections_config_and_input_prefix_have_distinct_keys(self):
        rows=dataset('4h');fn=Mock(return_value={'nested':{'value':1}})
        lanes.lane(('master','TEST'),rows,fn);value=lanes.lane(('master','TEST'),rows,fn)
        self.assertEqual(fn.call_count,1)
        value['nested']['value']=999
        self.assertEqual(lanes.lane(('master','TEST'),rows,fn)['nested']['value'],1)
        corrected=[replace(rows[0],high=rows[0].high+1),*rows[1:]]
        lanes.lane(('master','TEST'),corrected,fn)
        lanes.lane(('legacy','TEST'),rows,fn)
        lanes.lane(('master','TEST'),rows[:-1],fn)
        self.assertEqual(fn.call_count,4)

    def test_cache_is_bounded_and_does_not_keep_failed_computations(self):
        rows=dataset('4h')
        with patch.object(lanes,'MAX_ENTRIES',2),patch.object(lanes,'MAX_BYTES',100):
            for i in range(4):lanes.lane((i,),rows,lambda:{'x':1})
            self.assertEqual(lanes.info()['entries'],2)
            self.assertLessEqual(lanes.info()['serializedBytes'],100)
            lanes.lane(('too_large',),rows,lambda:{'x':'x'*101})
            self.assertEqual(lanes.info()['entries'],2)
        fn=Mock(side_effect=DataError('no bars',404))
        for _ in range(2):
            with self.assertRaises(DataError):lanes.lane(('error',),rows,fn)
        self.assertEqual(fn.call_count,2)

    def test_all_fan_modes_match_uncached_source_calculation_before_and_after_rewind(self):
        from analysis_service import build_chart
        from test_research import fixture_sources
        inputs={tf:(rows[:100],meta) for tf,(rows,meta) in fixture_sources().items()}
        now=datetime.now(timezone.utc)
        for mode in ('fan_extreme','fan_local','fan_master'):
            for end in (95,94,95):
                cutoff=datetime.fromtimestamp(inputs['4h'][0][end].end,timezone.utc)
                base=build_chart(inputs,'TEST','4h',cutoff,now,include_analysis=False)
                expected=deepcopy(base)
                with patch('fan_chart.cached_lane',side_effect=lambda key,rows,fn:fn()):apply(expected,mode)
                apply(base,mode)
                self.assertEqual(base,expected,mode)
        self.assertGreater(lanes.info()['hits'],0)


class SourceCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.env=patch.dict(os.environ,{'TORI_DATA_DIR':self.temp.name});self.env.start()
        self.inputs={tf:(dataset(tf),metadata(dataset(tf))) for tf in ('1h','4h','1D')}
        self.identity=save_dataset('TEST',self.inputs)
        sources.clear();lanes.clear()

    def tearDown(self):
        sources.clear();lanes.clear();self.env.stop();self.temp.cleanup()

    def test_adjacent_steps_load_once_cut_every_interval_and_match_original_payload(self):
        for include in (False,True):
            for at in (CUTOFF,CUTOFF.replace(hour=12)):
                expected=original_chart(self.identity,'4h',at.isoformat(),include_analysis=include)
                with patch('chart_sources.read_dataset',wraps=read_dataset) as load:
                    actual=sources.chart_dataset(self.identity,'4h',at.isoformat(),include_analysis=include)
                    again=sources.chart_dataset(self.identity,'1h',at.isoformat(),include_analysis=include)
                    self.assertLessEqual(load.call_count,1)
                for p in (actual,again):
                    self.assertTrue(all(b['end']<=at.timestamp() for view in p['charts'].values() for b in view['bars']))
                for p in (expected,actual):p.pop('generatedAt',None);p.pop('analysisId',None)
                self.assertEqual(actual,expected)
        self.assertEqual(len(sources._cache),1)

    def test_mutating_returned_lists_or_metadata_never_mutates_cached_inputs(self):
        frames,meta=sources.sources_for(self.identity)
        frames['4h'][0].clear();frames['4h'][1]['quality']['rejected']=99;meta['symbol']='BAD'
        again,m=sources.sources_for(self.identity)
        self.assertGreater(len(again['4h'][0]),0);self.assertEqual(again['4h'][1]['quality']['rejected'],0)
        self.assertEqual(m['symbol'],'TEST');self.assertNotIn('5m',again)

    def test_changed_or_deleted_parquet_block_cannot_reuse_verified_cache(self):
        sources.sources_for(self.identity)
        m=json.loads((self.root/'datasets'/(self.identity+'.json')).read_text(encoding='utf-8'))
        path=self.root/m['storage']['blocks'][0]['path']
        original=path.read_bytes();path.write_bytes(original[:-1]+bytes([original[-1]^1]))
        with self.assertRaises(DataError):sources.sources_for(self.identity)
        path.unlink()
        with self.assertRaises(DataError):sources.sources_for(self.identity)

    def test_periodic_reverification_and_lru_limit(self):
        with patch('chart_sources.time.monotonic',return_value=0),patch('chart_sources.read_dataset',wraps=read_dataset) as load:
            sources.sources_for(self.identity);sources.sources_for(self.identity);self.assertEqual(load.call_count,1)
        with patch('chart_sources.time.monotonic',return_value=601),patch('chart_sources.read_dataset',wraps=read_dataset) as load:
            sources.sources_for(self.identity);self.assertEqual(load.call_count,1)
        for symbol in ('OTHER','THIRD'):
            identity=save_dataset(symbol,self.inputs);sources.sources_for(identity)
        self.assertEqual(len(sources._cache),2)

    def test_fixed_research_setup_uses_original_overlay_path(self):
        setup={'signal':'immutable'}
        with patch('chart_sources.original_chart_dataset',return_value={'researchSetup':'same'}) as old:
            result=sources.chart_dataset(self.identity,'4h',None,setup,include_analysis=False)
        self.assertEqual(result,{'researchSetup':'same'})
        old.assert_called_once_with(self.identity,'4h',None,setup,include_analysis=False)


if __name__=='__main__':unittest.main()
