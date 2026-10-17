import copy
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
import json
import math
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from models import Bar, DataError, NY
from datasets import digest, read_dataset, save_dataset, source_bars, chart_dataset
from research import validate_spec, trial_plan, causal_events, evaluate_trial, outcomes, find_retest, summarize
from trendlines import analyze
import jobs


def fixture_sources():
    sources={tf:[] for tf in ('1h','4h','1D')}
    start=datetime(2023,1,2,tzinfo=NY)
    for day in range(800):
        candles=[]
        for k,hour in enumerate((8,12)):
            i=day*2+k
            value=110+22*math.sin(i/27)+4*math.sin(i/4)
            stamp=(start+timedelta(days=day)).replace(hour=hour)
            candles.append(Bar(int(stamp.timestamp()),int((stamp+timedelta(hours=4)).timestamp()),value-.5,value+1,value-1,value+.5,100))
        sources['4h'].extend(candles)
        sources['1h'].extend(replace(b,end=b.time+3600) for b in candles)
        stamp=start+timedelta(days=day)
        sources['1D'].append(Bar(int(stamp.timestamp()),int(stamp.replace(hour=16).timestamp()),candles[0].open,max(b.high for b in candles),min(b.low for b in candles),candles[-1].close,200))
    return {tf:(bars,{'quality':{'rejected':0},'warning':None,'mode':'fixture','cached':True,'fetchedAt':'2026-01-01T00:00:00Z'}) for tf,bars in sources.items()}


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.env=patch.dict(os.environ,{'TORI_DATA_DIR':self.temp.name})
        self.env.start()
        self.sources=fixture_sources()
        self.identity=save_dataset('TEST',self.sources)
        self.dataset=read_dataset(self.identity)
        self.spec=validate_spec({'symbols':['TEST'],'samples':3,'dataset_ids':{'TEST':self.identity}})
        self.plan=trial_plan(self.dataset,self.spec)

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def test_dataset_revisions_are_new_versions_and_tampering_fails(self):
        changed=dict(self.sources)
        bars,meta=changed['4h']
        changed['4h']=([*bars[:-1],replace(bars[-1],volume=101)],meta)
        second=save_dataset('TEST',changed)
        self.assertNotEqual(second,self.identity)
        self.assertEqual(read_dataset(self.identity)['material'],self.dataset['material'])
        path=Path(self.temp.name)/'datasets'/f'{second}.json'
        value=json.loads(path.read_text('utf-8'))
        value['material']['bars']['4h'][0]['high']=9999
        path.write_text(json.dumps(value),'utf-8')
        with self.assertRaises(DataError):read_dataset(second)

    def test_sampling_is_repeatable_and_independent_of_future_prices(self):
        self.assertEqual(self.plan,trial_plan(self.dataset,self.spec))
        self.assertEqual(len(set(self.plan['starts'])),3)
        shocked=copy.deepcopy(self.dataset)
        for row in shocked['material']['bars']['4h'][self.plan['discovery_end']+1:]:
            row.update(high=99999,low=.01,close=10000)
        self.assertEqual(self.plan,trial_plan(shocked,self.spec))
        self.assertTrue(all(i<=self.plan['discovery_end'] for i in self.plan['starts']))

    def test_future_shocks_cannot_change_prefix_events_or_daily_context(self):
        cutoff=900
        before=list(causal_events(self.dataset,cutoff,first_index=cutoff-50))
        self.assertTrue(before)
        shocked=copy.deepcopy(self.dataset)
        closed=self.sources['4h'][0][cutoff].end
        for rows in shocked['material']['bars'].values():
            for row in rows:
                if row['end']>closed:row.update(high=999999,low=.001,close=999998)
        self.assertEqual(before,list(causal_events(shocked,cutoff,first_index=cutoff-50)))
        for event in before:
            self.assertLessEqual(event['features']['daily']['closedAt'],event['closedAt'])
            bars=self.sources['4h'][0][:event['index']+1]
            expected=analyze(bars,'4h',bars[-1].time)['event']
            self.assertEqual(expected['closedAt'],event['closedAt'])
            self.assertEqual(expected['kind'],event['kind'])

    def test_no_signal_is_a_persistable_result_not_discarded(self):
        trial=evaluate_trial(self.dataset,self.spec,self.plan,self.plan['starts'][0],[])
        self.assertEqual(trial['status'],'no_entry')
        self.assertEqual(summarize([trial],self.spec['horizons'])['no_entry'],1)

    def test_execution_occurs_after_availability_and_original_stop_is_retained(self):
        bars=self.sources['4h'][0]
        start=self.plan['starts'][0]
        i=start+2
        event={'id':'synthetic-signal','redBreak':True,'index':i,'closedAt':bars[i].end,
            'quality':'provisional','red':{'a_index':i-1,'a_price':bars[i].close+2,'slope':-1},
            'green':{'a_index':i-1,'a_price':bars[i].close-10,'slope':.1}}
        trial=evaluate_trial(self.dataset,self.spec,self.plan,start,[event])
        entry=trial['variants'][0]
        self.assertEqual(entry['status'],'observed')
        self.assertGreaterEqual(entry['entryAt'],entry['availableAt'])
        self.assertGreater(entry['entryIndex'],i)
        self.assertAlmostEqual(entry['initialStop'],bars[i].close-9.9)

    def test_research_chart_preserves_signal_anchors_when_moving_forward(self):
        event=next(e for e in causal_events(self.dataset,900,first_index=850) if e['redBreak'])
        at=datetime.fromtimestamp(self.sources['4h'][0][900].end,timezone.utc).isoformat()
        chart=chart_dataset(self.identity,'4h',at,{'signal':event,'variant':'breakout'})
        red=chart['lanes']['4h']['red']
        self.assertEqual(red['a_time'],event['red']['a_time'])
        self.assertEqual(red['b_time'],event['red']['b_time'])
        self.assertEqual(chart['researchSetup']['eventId'],event['id'])
        self.assertAlmostEqual(red['value'],red['a_price']+red['slope']*(900-red['a_index']))

    def test_observations_never_cross_the_reserved_boundary(self):
        bars=self.sources['4h'][0]
        metrics=outcomes(bars,self.plan['discovery_end'],90,[1,5],5,self.plan['discovery_end'])
        self.assertTrue(metrics['1']['complete'])
        self.assertFalse(metrics['5']['complete'])

    def test_retest_requires_a_later_bar_and_uses_original_line(self):
        bar=Bar(100,104,100,101,100,100.5,1)
        bars=[bar,replace(bar,time=104,end=108,low=99,close=99.5)]
        event={'index':0,'red':{'a_price':100,'a_index':0,'slope':-1}}
        self.assertEqual(find_retest(bars,event,self.spec,0),(None,'retest_censored'))
        self.assertEqual(find_retest(bars,event,self.spec,1),(1,None))
        failed=[bar,replace(bars[1],close=97)]
        self.assertEqual(find_retest(failed,event,self.spec,1),(None,'retest_invalidated'))

    def test_returns_costs_and_ambiguous_stop_order_are_explicit(self):
        bars=[Bar(0,4,100,104,97,102,1)]
        value=outcomes(bars,0,98,[1],5,0)['1']
        self.assertAlmostEqual(value['return_pct'],2)
        self.assertAlmostEqual(value['net_return_pct'],(102*.9995/(100*1.0005)-1)*100)
        self.assertTrue(value['stop_touched'])
        self.assertTrue(value['intrabar_ambiguous'])
        self.assertFalse(value['one_r_before_stop'])
        self.assertFalse(value['two_r_before_stop'])
        self.assertIsNone(outcomes(bars,0,101,[1],0,0)['1']['terminal_r'])

    def test_repeated_origin_does_not_double_count_summary(self):
        entry={'group':'breakout_provisional','status':'observed','eventId':'same','entryAt':100,'outcomes':{'5':{'complete':True,'net_return_pct':2,'mfe_pct':3,'mae_pct':-1,'intrabar_ambiguous':False}}}
        trial={'status':'observed','variants':[entry]}
        group=summarize([trial,trial],[5])['groups']['breakout_provisional']
        self.assertEqual(group['observed'],2)
        self.assertEqual(group['uniqueSignals'],1)
        self.assertEqual(group['horizons']['5']['n'],1)

    def test_job_checkpoint_restart_is_offline_and_idempotent(self):
        job=jobs.submit(self.spec)
        stop=threading.Event()
        original=jobs.evaluate_trial
        def interrupted(*args):
            value=original(*args)
            stop.set()
            return value
        with jobs.connection() as db:db.execute("UPDATE jobs SET status='running' WHERE id=?",(job['id'],))
        with patch('jobs.evaluate_trial',side_effect=interrupted),patch('jobs.import_dataset',side_effect=AssertionError('network forbidden')):
            self.assertFalse(jobs.run_job(job['id'],stop))
        self.assertEqual(jobs.get_job(job['id'])['completedTrials'],1)
        with patch('jobs.import_dataset',side_effect=AssertionError('network forbidden')):
            self.assertTrue(jobs.worker_loop(threading.Event(),once=True))
        result=jobs.report(job['id'])
        self.assertEqual(result['job']['status'],'succeeded')
        self.assertEqual(result['summary']['trials'],3)
        self.assertEqual(len(set(t['id'] for t in result['trials'])),3)
        # A fresh run on the pinned dataset produces the same business result.
        second=jobs.submit(self.spec)
        jobs.worker_loop(threading.Event(),once=True)
        self.assertEqual(result['summary'],jobs.report(second['id'])['summary'])
        self.assertEqual(result['trials'],jobs.report(second['id'])['trials'])
        page=jobs.report(second['id'],offset=1,limit=1)
        self.assertEqual(page['page']['total'],3)
        self.assertEqual(len(page['trials']),1)
        self.assertEqual(page['summary'],result['summary'])

    def test_schedule_enqueue_and_cancel_do_not_duplicate_jobs(self):
        jobs.schedule({'enabled':True,'interval_hours':24,'spec':self.spec})
        jobs.schedule_due();jobs.schedule_due()
        items=jobs.list_jobs()
        self.assertEqual(len(items),1)
        self.assertTrue(items[0]['automatic'])
        self.assertEqual(jobs.cancel(items[0]['id'])['status'],'cancelled')

    def test_only_one_worker_can_own_the_local_queue(self):
        self.assertFalse(jobs.worker_active())
        with jobs.worker_lock() as acquired:
            self.assertTrue(acquired)
            self.assertTrue(jobs.worker_active())
            with jobs.worker_lock() as second:self.assertFalse(second)

    def test_claim_is_atomic_and_does_not_resurrect_cancelled_jobs(self):
        from concurrent.futures import ThreadPoolExecutor
        cancelled=jobs.submit(self.spec)
        jobs.cancel(cancelled['id'])
        a,b=jobs.submit(self.spec),jobs.submit(self.spec)
        with ThreadPoolExecutor(max_workers=2) as pool:
            claimed=list(pool.map(lambda _:jobs.claim_next(),range(2)))
        self.assertEqual(set(claimed),{a['id'],b['id']})
        self.assertEqual(jobs.get_job(cancelled['id'])['status'],'cancelled')

    def test_chart_reads_immutable_dataset_without_provider(self):
        cutoff=datetime.fromtimestamp(self.sources['4h'][0][900].end,timezone.utc).isoformat()
        with patch('alpaca._request',side_effect=AssertionError('network forbidden')):
            chart=chart_dataset(self.identity,'4h',cutoff)
        self.assertEqual(chart['datasetId'],self.identity)
        self.assertTrue(all(b['end']<=chart['analysisCutoff'] for b in chart['bars']))

    def test_invalid_specs_and_stale_imports_are_rejected(self):
        for value in ({'samples':True},{'holdout_fraction':float('nan')},{'symbols':['../secret']},{'horizons':[0]},{'unknown':1}):
            with self.assertRaises(DataError):validate_spec(value)
        bars,meta=self.sources['4h']
        self.sources['4h']=(bars,{**meta,'warning':'stale'})
        with self.assertRaises(DataError):save_dataset('TEST',self.sources)


if __name__=='__main__':unittest.main()
