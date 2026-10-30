from copy import deepcopy
from dataclasses import asdict
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from urllib.request import Request,urlopen
from urllib.error import HTTPError

import maintenance
from database import connection
from datasets import save_dataset,read_dataset,digest
from models import DataError
from server import Handler
from storage import cleanup_preview
import workbench_reviews as reviews
from workbench_scanner import ExplainedReplay,scan,prefix,journal
from workbench_events import calendar,validate
from workbench_portfolio import adapt,ledger,CloseMarks
from types import SimpleNamespace
import test_entry_discovery as fixture
from test_complete_strategy import candidate
from complete_strategy import CompleteReplay


class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.runtime=Path(self.temp.name)/'runtime'
        self.env=patch.dict(os.environ,{'TORI_DATA_DIR':str(self.runtime),'TORI_AUTO_ENABLED':'0'});self.env.start()
        self.data,self.sources=fixture.dataset()
        self.identity=save_dataset('TEST',{tf:(rows,{'normalization':self.data['material']['normalization'][tf]}) for tf,rows in self.sources.items()},feed='iex',adjustment='split',data_kind='synthetic')
        self.rows=self.sources['4h'];self.cutoff=self.rows[23].end
        red=candidate(self.rows,True)['ray'];green=candidate(self.rows,False)['ray']
        self.sample={'datasetId':self.identity,'timeframe':'4h','cutoff':self.cutoff,
                     'engine':{'rays':[{'role':'red','ray':red},{'role':'green','ray':green}],'resistances':[110.]}}
        self.pack=reviews.register([self.sample]);self.case=reviews.cases(self.pack)['items'][0]['id']

    def tearDown(self):self.env.stop();self.temp.cleanup()

    def body(self,revision=0):
        ray=candidate(self.rows,False)['ray']
        return {'revision':revision,'verdict':'interesting','note':'Dritter Kontakt unabhängig prüfen',
            'rays':[{'id':'g','role':'green',**{k:ray[k] for k in ('a_time','a_price','b_time','b_price')},
                     'contacts':[ray['a_time'],ray['b_time'],self.rows[20].time]}]}

    def test_closed_prefix_no_engine_or_future_before_explicit_saved_reveal(self):
        view=reviews.view(self.pack,self.case)
        self.assertNotIn('engine',view);self.assertFalse(view['futureAvailable'])
        self.assertEqual(view['bars'][-1]['end'],self.cutoff)
        self.assertTrue(all(b['end']<=self.cutoff for b in view['bars']))
        with self.assertRaises(DataError):reviews.reveal(self.pack,self.case,{'revision':0})
        saved=reviews.label(self.pack,self.case,self.body());self.assertEqual(saved['revision'],1)
        self.assertNotIn('engine',saved);self.assertEqual(reviews.compare(self.pack)['geometry'],[])
        shown=reviews.reveal(self.pack,self.case,{'revision':1});self.assertIn('engine',shown)
        self.assertFalse(shown['tainted']);self.assertTrue(all(b['end']<=self.cutoff for b in shown['bars']))
        comparison=reviews.compare(self.pack);self.assertEqual(comparison['humanLabels'],1)
        self.assertAlmostEqual(comparison['geometry'][0]['maximumProjectionErrorATR'],0)

    def test_optimistic_conflict_biased_edit_and_original_blind_label_preserved(self):
        reviews.label(self.pack,self.case,self.body())
        with self.assertRaises(DataError):reviews.label(self.pack,self.case,self.body())
        reviews.reveal(self.pack,self.case,{'revision':1})
        body=self.body(2);body['rays']=[];body['verdict']='reject'
        edited=reviews.label(self.pack,self.case,body)
        self.assertTrue(edited['tainted']);self.assertEqual(edited['blindLabel']['verdict'],'interesting')
        self.assertEqual(edited['label']['rays'],[])
        self.assertEqual(len(reviews.compare(self.pack)['geometry']),1)
        with connection() as db:self.assertEqual(db.execute("SELECT count(*) FROM settings WHERE key LIKE 'wb:history:%'").fetchone()[0],2)

    def test_bad_future_anchor_duplicate_mark_and_nonfinite_price_rejected(self):
        for change in ('future','nan','contact','role'):
            b=self.body()
            if change=='future':b['rays'][0]['b_time']=self.rows[24].time
            if change=='nan':b['rays'][0]['a_price']=float('nan')
            if change=='contact':b['rays'][0]['contacts']*=2
            if change=='role':b['rays'][0]['role']='script'
            with self.assertRaises(DataError):reviews.label(self.pack,self.case,b)
        with self.assertRaises(DataError):reviews.register([self.sample,self.sample])
        with self.assertRaises(DataError):reviews.cases(self.pack,0,101)

    def test_backup_restore_and_cleanup_reference_preserve_review_and_dataset(self):
        reviews.label(self.pack,self.case,self.body())
        self.assertNotIn(self.identity,[x['id'] for x in cleanup_preview()['candidates']])
        backup=Path(self.temp.name)/'backup';restored=Path(self.temp.name)/'restored'
        maintenance.backup(backup);maintenance.restore(backup,restored)
        with patch.dict(os.environ,{'TORI_DATA_DIR':str(restored)}):
            self.assertEqual(reviews.view(self.pack,self.case)['blindLabel']['verdict'],'interesting')
            self.assertEqual(read_dataset(self.identity)['id'],self.identity)

    def test_source_timeframe_is_respected_for_daily_case(self):
        s={**self.sample,'timeframe':'1D','cutoff':self.sources['1D'][16].end,'engine':{'rays':[],'resistances':[]}}
        pack=reviews.register([s]);case=reviews.cases(pack)['items'][0]['id'];v=reviews.view(pack,case)
        self.assertEqual(v['timeframe'],'1D');self.assertEqual(len(v['bars']),17)

    def test_http_auth_origin_static_and_no_arbitrary_read_or_registration(self):
        http=ThreadingHTTPServer(('127.0.0.1',0),Handler);http.api_token='testing'
        thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start();base=f'http://127.0.0.1:{http.server_port}'
        def request(path,body=None,origin=None,token='testing'):
            headers={'Authorization':'Bearer '+token}
            if origin is not None:headers['Origin']=origin
            if body is not None:headers['Content-Type']='application/json'
            return urlopen(Request(base+path,data=json.dumps(body).encode() if body is not None else None,headers=headers))
        try:
            with request('/pruefung') as r:self.assertIn(b'workbench.js',r.read())
            with request('/api/workbench/packs') as r:self.assertEqual(len(json.load(r)['items']),1)
            for path,body,origin,token,code in [('/api/workbench/packs',None,None,'wrong',401),
                ('/api/workbench/packs',{},'https://evil.example','testing',403),
                ('/api/workbench/register',{},None,'testing',405),('/data/datasets/'+self.identity+'.json',None,None,'testing',404)]:
                with self.assertRaises(HTTPError) as e:request(path,body,origin,token)
                self.assertEqual(e.exception.code,code)
            with request(f'/api/workbench/packs/{self.pack}/{self.case}/label',self.body()) as r:self.assertNotIn('engine',json.load(r))
        finally:http.shutdown();http.server_close();thread.join()


class ExplainedScannerTests(unittest.TestCase):
    def result(self,data,cls,cutoff=None):
        engine=cls(data,cutoff=cutoff);engine.start_at=0
        with patch.object(engine.geometry,'proposals',side_effect=lambda i:[candidate(engine.rows,False),candidate(engine.rows,True)] if i==19 else []):return engine.run()

    def test_adding_facts_does_not_change_entries_and_facts_have_no_future_fill(self):
        d,_=fixture.dataset();old=self.result(d,CompleteReplay);new=self.result(d,ExplainedReplay)
        self.assertEqual(old['entries'],new['entries']);self.assertTrue(new['watchFacts'])
        for f in new['watchFacts']:
            self.assertNotIn('entryPrice',f);self.assertNotIn('paths',f);self.assertNotIn('netReturnPct',f)
            self.assertIn('Unternehmensereignisse unbekannt',f['warnings'])
            self.assertGreaterEqual(f['contacts']['contacts'],3)

    def test_cutoff_and_future_shock_preserve_facts_exactly(self):
        d,sources=fixture.dataset();cutoff=sources['4h'][20].end
        baseline=self.result(d,ExplainedReplay,cutoff)
        changed=deepcopy(d)
        for bars in changed['material']['bars'].values():
            for b in bars:
                if b['end']>cutoff:
                    for k in ('open','high','low','close'):b[k]*=100
        changed['id']=digest(changed['material'])
        self.assertEqual(self.result(changed,ExplainedReplay,cutoff)['watchFacts'],baseline['watchFacts'])
        self.assertEqual(prefix(d,cutoff),prefix(changed,cutoff))

    def test_checkpoint_replay_quiet_and_feed_engine_revision_backward_guards(self):
        d,sources=fixture.dataset();cutoff=sources['4h'][23].end
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'TORI_DATA_DIR':folder}),patch('workbench_scanner.read_dataset',return_value=d):
            a=scan(d['id'],'4h',cutoff,stream='test',mode='historical',from_at=0)
            b=scan(d['id'],'4h',cutoff,stream='test',mode='historical');self.assertEqual(b['newFacts'],[])
            self.assertEqual(a['checkpoint']['prefixHash'],b['checkpoint']['prefixHash'])
            with self.assertRaises(DataError):scan(d['id'],'4h',cutoff-1,stream='test',mode='historical')
            with patch('workbench_scanner.engine_hash',return_value='different'):
                with self.assertRaises(DataError):scan(d['id'],'4h',cutoff,stream='test',mode='historical')
            changed=deepcopy(d);changed['material']['bars']['5m'][0]['close']+=.01
            with patch('workbench_scanner.read_dataset',return_value=changed):
                with self.assertRaises(DataError):scan(d['id'],'4h',cutoff,stream='test',mode='historical')
            changed=deepcopy(d);changed['material']['feed']='sip'
            with patch('workbench_scanner.read_dataset',return_value=changed):
                with self.assertRaises(DataError):scan(d['id'],'4h',cutoff,stream='test',mode='historical')
            with self.assertRaises(DataError):scan(d['id'],'4h',cutoff,stream='new',from_at=0)
            future_calendar={'coverage':[{'symbol':'TEST','knownAt':cutoff+1,'fromAt':cutoff,'throughAt':cutoff+1000000}],'events':[]}
            # A later publication cannot change an already registered prefix.
            scan(d['id'],'4h',cutoff,stream='test',mode='historical',events=future_calendar)
            future_calendar['coverage'][0]['knownAt']=cutoff-1
            with self.assertRaises(DataError):scan(d['id'],'4h',cutoff,stream='test',mode='historical',events=future_calendar)

    def test_calendar_unknown_and_publication_time_validation(self):
        self.assertIsNone(calendar().check('TEST',1736355600))
        p={'coverage':[{'symbol':'TEST','knownAt':1736355599,'fromAt':1736355500,'throughAt':1737655600}],'events':[]}
        self.assertTrue(calendar(p).check('TEST',1736355600))
        p['events']=[{'symbol':'TEST','knownAt':1736355700,'at':1736355600,'kind':'earnings'}]
        with self.assertRaises(ValueError):validate(p)
        with self.assertRaises(ValueError):validate({'coverage':[],'events':[],'success':True})

    def test_unknown_held_path_halts_ledger_instead_of_cherry_picking_complete_winners(self):
        _,sources=fixture.dataset();fine=sources['5m'];first=fine[100];missing=fine[110].time
        entry={'id':'e','symbol':'TEST','datasetId':'d','entryAt':first.time,'entryPrice':100.,'initialStop':95.,
            'paths':{'fixed':{'status':'unknown','buy':100.075,'initialRisk':5.075,'missingAt':missing,'reason':'missing_fine_path'}}}
        p=adapt(entry,entry['paths']['fixed']);self.assertEqual(p['status'],'censored')
        contexts={'d':SimpleNamespace(fine=CloseMarks([asdict(b) for b in fine]))}
        result=ledger([entry],contexts,{'startAt':first.time,'endAt':fine[150].end},'fixed')
        self.assertEqual(result['accepted'],1);self.assertEqual(result['status'],'incomplete')
        self.assertIsNone(result['markedReturnPct']);self.assertEqual(result['halt']['at'],missing)
        self.assertLessEqual(result['trades'][0]['plannedRiskUSD'],20.)
        self.assertGreaterEqual(result['cash'],0.)

    def test_cash_release_is_conservatively_at_fine_close_even_for_open_exit(self):
        e={'id':'e','entryAt':100,'initialStop':95}
        p={'status':'closed','buy':100.075,'sell':105,'initialRisk':5.075,'fillBarAt':400,'exitAt':400}
        self.assertEqual(adapt(e,p)['exitAt'],700)

    def test_durable_journal_pages_pin_append_boundary_and_do_not_mix_underscore_streams(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'TORI_DATA_DIR':folder}):
            with connection() as db:
                db.execute('INSERT INTO settings VALUES(?,?)',('wb:scan:a_b','{}'))
                db.execute('INSERT INTO settings VALUES(?,?)',('wb:scan:axb','{}'))
                for name in ('a_b:one','a_b:two','axb:foreign'):
                    db.execute('INSERT INTO settings VALUES(?,?)',('wb:fact:'+name,json.dumps({'id':name})))
            page=journal('a_b',1);self.assertEqual(page['page']['total'],2)
            with connection() as db:db.execute('INSERT INTO settings VALUES(?,?)',('wb:fact:a_b:new','{"id":"new"}'))
            next_page=journal('a_b',1,page['page']['nextCursor'])
            self.assertEqual([r['id'] for r in page['items']+next_page['items']],['a_b:one','a_b:two'])
            self.assertFalse(next_page['page']['hasMore']);self.assertEqual(journal('a_b')['page']['total'],3)
            with self.assertRaises(DataError):journal('axb',1,page['page']['nextCursor'])
