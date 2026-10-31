from copy import deepcopy
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import entry_history as h
from fan_geometry import stable_id
from models import DataError
from test_entry_history import sample,manifest
from test_entry_screen import fixture


class ScreenHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.env=patch.dict(os.environ,{'TORI_DATA_DIR':self.temp.name});self.env.start()
        s,self.rows,self.daily=fixture();self.at=s['signalAt']
        self.c=sample();self.c['signal'].update(s)
        self.c['entry']['entryAt']=self.at+300
        self.bad=deepcopy(self.c);self.bad['id']=stable_id('bad-case');self.bad['signal']['episodeId']='bad-episode'
        self.bad['signal']['initialStop']=119.5
        self.future=deepcopy(self.c);self.future['id']=stable_id('future-case');self.future['signal']['episodeId']='future-episode'
        self.future['signal']['signalAt']=self.rows[422].end;self.future['entry']['entryAt']=self.rows[422].end+300
        self.run=h.store_run({**manifest(),'cutoff':self.at+864000},[self.c,self.bad,self.future])
        path=Path(self.temp.name)/'manifest.json';path.write_text('{}',encoding='utf-8')
        self.path=patch('entry_history.path_for',return_value=path);self.path.start()
        self.sources=patch('entry_history._chart_sources',return_value=({'4h':(self.rows,{}),'1D':(self.daily,{})},{}));self.load=self.sources.start()
        h._screen_features.cache_clear()

    def tearDown(self):
        h._screen_features.cache_clear();self.sources.stop();self.path.stop();self.env.stop();self.temp.cleanup()

    def iso(self):return datetime.fromtimestamp(self.at,timezone.utc).isoformat()

    def test_filtered_count_page_and_marker_ids_are_causal_and_cached(self):
        page=h.cases_page(self.run,self.iso(),quality='balanced',limit=1)
        self.assertEqual([x['id'] for x in page['items']],[self.c['id']])
        self.assertEqual(page['screen']['beforeProfile'],2);self.assertEqual(page['screen']['excluded'],1)
        self.assertEqual(page['total'],1);self.assertFalse(page['hasMore'])
        self.assertNotIn('dailySma200',json.dumps(page));self.assertNotIn('futureWin',json.dumps(page))
        h.cases_page(self.run,self.iso(),quality='strict')
        self.load.assert_called_once()

    def test_profile_details_appear_before_fill_without_leaking_next_open_or_returns(self):
        detail=h.detail(self.run,self.c['id'],self.iso(),quality='balanced')
        self.assertEqual(detail['entry']['status'],'pending')
        self.assertTrue(detail['screen']['accepted']);self.assertEqual(detail['screen']['features']['knownAt'],self.at)
        self.assertNotIn('entryPrice',json.dumps(detail));self.assertNotIn('futureWin',json.dumps(detail))
        self.assertEqual(h.detail(self.run,self.bad['id'],self.iso(),quality='balanced')['state'],'filtered_out')
        self.assertEqual(h.detail(self.run,self.future['id'],self.iso(),quality='balanced')['state'],'before_signal')
        self.assertEqual(len(h.cases_page(self.run,self.iso(),quality='all')['items']),2)

    def test_unknown_sma_excludes_without_using_future_daily_bars(self):
        missing=[b for b in self.daily if b.end<=self.at][:-1]
        with patch('entry_history._chart_sources',return_value=({'4h':(self.rows,{}),'1D':(missing,{})},{})):
            self.assertEqual(h.cases_page(self.run,self.iso(),quality='balanced')['total'],0)
            self.assertEqual(h.cases_page(self.run,self.iso(),quality='qualified')['total'],2)

    def test_http_query_uses_identical_profile_and_rejects_invalid_names(self):
        page=h.get('/api/entries/cases',{'run':[self.run],'asof':[self.iso()],'quality':['balanced']})
        self.assertEqual(page['total'],1)
        for call in (lambda:h.cases_page(self.run,quality='winner_only'),lambda:h.detail(self.run,self.c['id'],quality='winner_only')):
            with self.assertRaises(DataError):call()


if __name__=='__main__':unittest.main()
