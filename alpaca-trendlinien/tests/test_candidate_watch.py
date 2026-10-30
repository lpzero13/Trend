from copy import deepcopy
from dataclasses import replace
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

from candidate_board import build
import candidate_watch as watch
import candidate_api
import candidate_data
from datasets import digest,save_dataset,read_dataset
from database import connection
from models import DataError
from server import Handler
from workbench_reviews import put
from storage import references
import maintenance
import test_entry_discovery as fixture


class Candidates(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.env=patch.dict(os.environ,{'TORI_DATA_DIR':str(self.root/'runtime'),'TORI_AUTO_ENABLED':'0'});self.env.start()
        d,self.sources=fixture.dataset();self.rows=self.sources['4h'];self.now=self.sources['5m'][-1].end+900
        self.identity=save_dataset('TEST',{tf:(rows,{'normalization':d['material']['normalization'][tf]}) for tf,rows in self.sources.items()},feed='sip',adjustment='split',session='XNYS regular; fixture')
        self.data=read_dataset(self.identity);self.cutoff=self.rows[23].end
        self.run=watch.registration({'TEST':self.identity},now=self.cutoff+1)
        red={'a_index':0,'b_index':10,'a_time':self.rows[0].time,'b_time':self.rows[10].time,'a_price':110.,'b_price':110.,'slope':0.,'basis':'bars'}
        green={**red,'a_price':90.,'b_price':90.}
        self.fact={'id':'fact','symbol':'TEST','timeframe':'4h','knownAt':self.rows[20].end,'phase':'approaching',
                   'red':red,'green':green,'signalATR':10.,'warnings':['Events unbekannt'],
                   'contacts':{'contacts':3,'ageDays':30},'safetyContacts':{'contacts':2},
                   'riskATRAtClose':1.,'riskFractionAtClose':.1,'checksAtClose':{}}

    def tearDown(self):self.env.stop();self.temp.cleanup()

    def replay(self,entries=(),facts=None):
        return patch('candidate_watch.ExplainedReplay',return_value=type('R',(),{'run':lambda _:{'watchFacts':[self.fact] if facts is None else facts,'entries':list(entries)}})())

    def test_grouping_preserves_first_anchors_and_independent_alternatives(self):
        f=deepcopy(self.fact);g=deepcopy(f);g['id']='near';g['knownAt']=self.rows[21].end;g['red']['a_price']+=.2;g['red']['b_price']+=.2
        a=build([f,g],self.rows[:24],self.cutoff)
        self.assertEqual(len(a),1);self.assertEqual(a[0]['alternativeCount'],1);self.assertEqual(a[0]['original'],f)
        self.assertEqual(a,build([f,g],self.rows[:24],self.cutoff,a))
        g['phase']='retest'
        self.assertNotEqual(build([f,g],self.rows[:24],self.cutoff)[0]['state'],'retest')
        g['red']['slope']=3
        self.assertEqual(len(build([f,g],self.rows[:24],self.cutoff)),2)

    def test_missing_source_suspends_and_safety_invalidation_is_not_paper_fill(self):
        rows=self.rows[:24];a=build([self.fact],rows,self.cutoff)[0]
        missing=rows[:22]+rows[23:]
        self.assertEqual(build([self.fact],missing,self.cutoff)[0]['state'],'unclear')
        changed=list(rows);changed[22]=replace(changed[22],low=80)
        bad=build([self.fact],changed,self.cutoff)[0]
        self.assertEqual(bad['state'],'invalid');self.assertNotIn('netPnl',bad)

    def test_safety_only_bounce_has_no_action_ray_and_remains_explicitly_unclear(self):
        f=deepcopy(self.fact);f['id']='safety-only';f['red']=None;f['phase']='bounce'
        g=build([f,self.fact],self.rows[:24],self.cutoff)
        self.assertEqual(len(g),2);self.assertEqual(next(x for x in g if x['original']['red'] is None)['state'],'unclear')

    def test_bootstrap_not_new_entry_and_future_bars_do_not_change_snapshot(self):
        with self.replay():a,events,papers=watch.evaluate(self.run,self.data,self.cutoff,now=self.now)
        self.assertTrue(a['groups'][0]['bootstrap']);self.assertEqual(events,[]);self.assertEqual(papers,[])
        changed=deepcopy(self.data)
        for bars in changed['material']['bars'].values():
            for b in bars:
                if b['time']>=self.cutoff:b.update(open=500,high=501,low=499,close=500)
        with self.replay():b,_,_=watch.evaluate(self.run,changed,self.cutoff,now=self.now)
        self.assertEqual(a,b)

    def test_prefix_revision_rejected_before_replay(self):
        with self.replay():old,_,_=watch.evaluate(self.run,self.data,self.cutoff,now=self.now)
        revised=deepcopy(self.data);revised['material']['bars']['5m'][0]['close']+=.01
        with self.assertRaises(DataError):watch.evaluate(self.run,revised,self.cutoff,old,now=self.now)

    def test_atomic_resume_duplicate_journal_and_conflicting_writer(self):
        with self.replay():lane,events,papers=watch.evaluate(self.run,self.data,self.cutoff,now=self.now)
        event={'id':'one','knownAt':self.cutoff,'datasetId':self.identity}
        watch.commit(self.run,lane,[event],papers,None)
        with self.assertRaises(DataError):watch.commit(self.run,lane,[],[],None)
        watch.commit(self.run,lane,[event],papers,lane)
        self.assertEqual(len(watch.journal(self.run['id'])['items']),1)

    def test_journal_cursor_snapshot_binding_and_new_appends(self):
        with connection() as db:
            for n in range(3):put(db,'cw:event:'+self.run['id']+':'+str(n),{'id':n})
        first=watch.journal(self.run['id'],1)
        with connection() as db:put(db,'cw:event:'+self.run['id']+':new',{'id':'new'})
        rest=watch.journal(self.run['id'],20,first['page']['nextCursor'])
        self.assertEqual([r['id'] for r in rest['items']],[1,2])
        other=watch.registration({'TEST':self.identity},now=self.now)
        with self.assertRaises(DataError):watch.journal(other['id'],20,first['page']['nextCursor'])

    def test_provider_budget_skips_quiet_cycle_and_frozen_engine_blocks_resume(self):
        importer=lambda d,k,n:(d,self.cutoff)
        with self.replay():watch.cycle(self.run['id'],self.cutoff+900,importer)
        with patch('candidate_watch.refresh',side_effect=AssertionError('no implicit provider')),self.replay():
            called=[];watch.cycle(self.run['id'],self.cutoff+900,lambda *a:called.append(a))
        self.assertEqual(called,[])
        with patch('candidate_watch.fingerprint',return_value='different'):
            with self.assertRaises(DataError):watch.cycle(self.run['id'],self.now,importer)

    def test_bootstrap_is_a_local_check_not_a_successful_provider_import(self):
        def forbidden(*args):raise AssertionError('bootstrap must not import')
        with self.replay():watch.cycle(self.run['id'],self.cutoff+900,forbidden)
        lane=watch.read('cw:lane:'+self.run['id']+':TEST')
        self.assertIsNone(lane['lastImportAt']);self.assertIn('lastCheckedAt',lane)
        self.assertNotIn('lastSuccessfulImportAt',watch.load_run(self.run['id']))
        # A subsequent genuinely requested import advances the import timestamps.
        with self.replay():watch.cycle(self.run['id'],self.now+86400,lambda d,k,n:(d,self.cutoff))
        self.assertEqual(watch.load_run(self.run['id'])['lastSuccessfulImportAt'],self.now+86400)
        self.assertEqual(watch.read('cw:lane:'+self.run['id']+':TEST')['lastImportAt'],self.now+86400)

    def test_failed_first_import_is_retried_and_does_not_fake_success(self):
        def fail(*a):raise DataError('Temporär fehlen Daten',409)
        watch.cycle(self.run['id'],self.now+86400,fail)
        self.assertIsNotNone(watch.status(self.run['id'])['lanes'][0]['error'])
        with self.replay():watch.cycle(self.run['id'],self.now+86400,lambda d,k,n:(d,self.cutoff))
        self.assertIsNone(watch.status(self.run['id'])['lanes'][0]['error'])

    def test_no_retroactive_signal_fill_if_registered_between_them(self):
        e={'profile':'age7','family':'retest','signalAt':self.cutoff,'entryAt':self.cutoff+300}
        with self.replay([e]):_,_,papers=watch.evaluate(self.run,self.data,self.rows[-1].end,now=self.now)
        self.assertEqual(papers,[])

    def test_paper_closed_cutoff_id_changes_but_economics_and_events_are_immutable(self):
        with self.replay():lane,_,_=watch.evaluate(self.run,self.data,self.cutoff,now=self.now)
        p={'id':'p','entry':{'entryAt':self.cutoff},'symbol':'TEST','datasetId':self.identity,'paths':{'fixed':{'status':'closed','events':[],'outcomeId':'a','fillBarAt':self.cutoff,'netR':1}}}
        watch.commit(self.run,lane,[],[p],None)
        q=deepcopy(p);q['paths']['fixed']['outcomeId']='b'
        watch.commit(self.run,lane,[],[q],lane)
        self.assertEqual(watch.read('cw:paper:'+self.run['id']+':p')['paths']['fixed']['outcomeId'],'a')
        q['paths']['fixed']['netR']=2
        with self.assertRaises(DataError):watch.commit(self.run,lane,[],[q],lane)

    def test_backup_restore_protects_new_references_and_read_only_http(self):
        with self.replay():lane,events,papers=watch.evaluate(self.run,self.data,self.cutoff,now=self.now)
        watch.commit(self.run,lane,events,papers,None)
        with connection() as db:self.assertIn(self.identity,references(db,self.root/'runtime'))
        maintenance.backup(self.root/'backup');maintenance.restore(self.root/'backup',self.root/'restored')
        with patch.dict(os.environ,{'TORI_DATA_DIR':str(self.root/'restored')}):self.assertEqual(watch.load_run(self.run['id'])['fromAt'],self.run['fromAt'])
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.api_token='';server.allowed_hosts=[]
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base='http://127.0.0.1:'+str(server.server_port)
        try:
            with patch('alpaca._request',side_effect=AssertionError('GET is offline')):
                with urlopen(base+'/kandidaten') as r:self.assertIn(b'cw-chart',r.read())
                with urlopen(base+'/api/candidates/status?run='+self.run['id']) as r:self.assertIn('lanes',json.load(r))
                cid=lane['groups'][0]['id']
                with urlopen(base+'/api/candidates/case?run='+self.run['id']+'&id='+cid) as r:
                    p=json.load(r);self.assertFalse(p['futureShown']);self.assertTrue(all(b['end']<=self.fact['knownAt'] for b in p['bars']))
            with self.assertRaises(HTTPError) as e:urlopen(Request(base+'/api/candidates/runs',headers={'Origin':'https://evil.example'}))
            self.assertEqual(e.exception.code,403)
            server.api_token='test-secret'
            with self.assertRaises(HTTPError) as e:urlopen(base+'/api/candidates/runs')
            self.assertEqual(e.exception.code,401)
        finally:server.shutdown();thread.join();server.server_close()

    def test_synthetic_registration_is_rejected_and_sip_overlap_is_read_only(self):
        d=deepcopy(self.data);d['material']['dataKind']='synthetic'
        with patch('candidate_watch.read_dataset',return_value=d):
            with self.assertRaises(DataError):watch.registration({'TEST':self.identity},now=self.now)
        meta={'feed':'sip','adjustment':'split','quality':{'rejected':0}}
        with patch('candidate_data.load_bars',return_value=(self.sources['5m'],meta)) as load,patch('candidate_data.save_dataset',return_value=self.identity),patch('candidate_data.read_dataset',return_value=self.data):
            candidate_data.refresh(self.data,self.cutoff,self.now)
        self.assertEqual(load.call_args.kwargs['feed'],'sip');self.assertLess(load.call_args.kwargs['history_days'],100)
        changed=[replace(b,close=b.close+.01) if i==0 else b for i,b in enumerate(self.sources['5m'])]
        with patch('candidate_data.load_bars',return_value=(changed,meta)):
            with self.assertRaises(DataError):candidate_data.refresh(self.data,self.cutoff,self.now)

    def test_import_budget_blocks_without_provider_or_deleting_datasets(self):
        with connection() as db:
            r=deepcopy(self.run);r['importBudgetBytes']=1;put(db,'cw:run:'+r['id'],r)
        calls=[];watch.cycle(r['id'],self.now+86400,lambda *a:calls.append(a))
        self.assertEqual(calls,[]);self.assertTrue(watch.status(r['id'])['lanes'][0]['blocked'])
        self.assertEqual(read_dataset(self.identity)['id'],self.identity)
