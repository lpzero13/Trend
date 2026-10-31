from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fan_geometry import stable_id
from models import Bar, DataError
from signal_journal import initialize, advance, status


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'journal.sqlite3';self.start=1700000000;self.now=self.start+100000
        # Gapped synthetic clock only here; real calendar/source geometry exercised by integration.
        self.rows=[Bar(self.start-390*86400,self.start-390*86400+14400,100,101,99,100,10)]
        self.rows += [Bar(t,t+14400,100,101,99,100,10) for t in (self.start-14400,self.start,self.start+14400)]
        self.dataset={'id':'d1','material':{'symbol':'AAA','feed':'sip','adjustment':'split',
                      'bars':{'4h':[asdict(b) for b in self.rows]}}}
        self.reader=patch('signal_journal.read_dataset',side_effect=lambda _:deepcopy(self.dataset));self.reader.start();self.addCleanup(self.reader.stop)
        self.convention=patch('signal_journal.require_convention');self.convention.start();self.addCleanup(self.convention.stop)
        self.kind=patch('signal_journal.data_kind',return_value='market');self.kind.start();self.addCleanup(self.kind.stop)
        self.scan=patch('signal_journal.scan',side_effect=self.fake_scan);self.scan.start();self.addCleanup(self.scan.stop)

    def fake_scan(self,symbol,rows,start,end):
        found=[]
        for b in rows:
            if start<=b.end<=end:
                found.append({'id':str(b.end),'signalAt':b.end,'knownAt':b.end,'family':'breakout','cohort':'qualified',
                              'validRisk':True,'line':{'id':'original','knownAt':b.end-14400},'safety':{'value':95},'initialStop':94.71})
        return found,[],[],{}

    def init(self,mode='replay'):
        return initialize(self.path,{'AAA':'d1'},self.start,mode=mode,now=self.now)

    def test_step_and_batch_match_restart_deduplicates_and_lines_stay_frozen(self):
        self.init();advance(self.path,step=True,now=self.now)
        first=status(self.path,now=self.now)['events'][0]['payload']
        advance(self.path,step=True,now=self.now)
        report=status(self.path,now=self.now);self.assertEqual(len(report['events']),2)
        self.assertEqual(report['events'][0]['payload'],first)
        self.assertEqual(advance(self.path,as_of=self.rows[-1].end,now=self.now)['eventsAdded'],0)
        other=Path(self.tmp.name)/'batch.sqlite3';initialize(other,{'AAA':'d1'},self.start,now=self.now)
        advance(other,as_of=self.rows[-1].end,now=self.now)
        self.assertEqual([e['payload'] for e in report['events']],[e['payload'] for e in status(other)['events']])

    def test_changed_observed_history_rolls_back_cursor_and_keeps_evidence(self):
        self.init();advance(self.path,step=True,now=self.now);before=status(self.path)
        self.dataset['material']['bars']['4h'][1]['close']=999
        with self.assertRaises(DataError):advance(self.path,step=True,now=self.now)
        self.assertEqual(status(self.path)['cursor'],before['cursor']);self.assertEqual(status(self.path)['events'],before['events'])

    def test_append_only_new_dataset_is_accepted(self):
        self.init();advance(self.path,step=True,now=self.now)
        self.dataset['id']='d2';advance(self.path,datasets={'AAA':'d2'},step=True,now=self.now)
        self.assertEqual(status(self.path)['sources'][0]['dataset_id'],'d2')

    def test_transaction_failure_does_not_commit_partial_events_or_cursor(self):
        self.init();before=status(self.path)
        with patch('signal_journal.scan',side_effect=RuntimeError('worker crash')):
            with self.assertRaises(RuntimeError):advance(self.path,step=True,now=self.now)
        after=status(self.path);self.assertEqual(after['events'],[]);self.assertEqual(after['cursor'],before['cursor'])
        self.assertEqual(advance(self.path,step=True,now=self.now)['eventsAdded'],1)

    def test_pages_hold_upper_bound_while_new_events_arrive(self):
        self.init();advance(self.path,step=True,now=self.now);one=status(self.path,limit=1)
        advance(self.path,step=True,now=self.now)
        next_page=status(self.path,after=one['nextAfter'],upper_seq=one['upperSeq'])
        self.assertEqual(next_page['events'],[]);self.assertEqual(status(self.path)['upperSeq'],2)

    def test_prospective_cannot_be_backdated_and_replay_does_not_become_prospective(self):
        with self.assertRaises(DataError):self.init('prospective')
        self.init();self.assertEqual(status(self.path)['mode'],'replay')
        with self.assertRaises(DataError):initialize(self.path,{'AAA':'d1'},self.start,now=self.now)

    def test_no_backward_future_or_beyond_dataset_checkpoint(self):
        self.init()
        for cutoff in (self.start-1,self.now+1,self.rows[-1].end+1):
            with self.assertRaises(DataError):advance(self.path,as_of=cutoff,now=self.now)
        self.assertEqual(status(self.path)['cursor'],self.start)

    def test_engine_change_refuses_resume_and_preserves_previous_journal(self):
        self.init();before=status(self.path)
        with patch('signal_journal.binding',return_value={'changed':True}):
            with self.assertRaises(DataError):advance(self.path,step=True,now=self.now)
        self.assertEqual(status(self.path)['cursor'],before['cursor'])

    def test_backup_restore_and_cleanup_preserve_journal_and_dataset_references(self):
        import os
        import maintenance
        from datasets import save_dataset
        from storage import cleanup_preview
        from test_research import fixture_sources
        runtime=Path(self.tmp.name)/'runtime'
        with patch.dict(os.environ,{'TORI_DATA_DIR':str(runtime)}):
            did=save_dataset('AAA',fixture_sources())
            self.path=runtime/'signal-journals'/'example.sqlite3'
            initialize(self.path,{'AAA':did},self.start,now=self.now)
            advance(self.path,step=True,now=self.now)
            self.assertNotIn(did,[c['id'] for c in cleanup_preview()['candidates']])
            saved=Path(self.tmp.name)/'backup';maintenance.backup(saved)
            manifest=maintenance.verify(saved)
            self.assertEqual(manifest['schema'],'tori-backup-3')
            self.assertIn('signal-journals/example.sqlite3',manifest['files'])
            restored=Path(self.tmp.name)/'restored';maintenance.restore(saved,restored)
            self.assertEqual(status(restored/'signal-journals'/'example.sqlite3')['events'],status(self.path)['events'])


if __name__=='__main__':unittest.main()
