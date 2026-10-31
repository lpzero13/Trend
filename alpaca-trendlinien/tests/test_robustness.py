from dataclasses import asdict, replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fan_geometry import stable_id
from lab_data import resample_regular, session_bounds
from models import Bar, DataError
from robustness_quality import check_frames
from robustness_study import prepare, validate_plan, POLICY, _cost_ledger, binding, evaluate
from screening_extension import binding as prior_binding
from strategy_screen import read, write
import test_strategy_screen as fixtures


class QualityTests(unittest.TestCase):
    def frame(self,day):
        a,b = session_bounds(day)
        return resample_regular([Bar(t,t+300,100,102,99,101,10) for t in range(a,b,300)])[0],a,b

    def test_short_session_and_dst_grids_have_no_invented_gaps(self):
        for day,count in (('2024-11-29',42),('2024-03-08',78),('2024-03-11',78)):
            frames,a,b = self.frame(day);q = check_frames(frames,a,b)
            self.assertTrue(q['passedStructural']);self.assertEqual(q['expectedFineBars'],count)
            self.assertEqual(q['missingFineBars'],0);self.assertEqual(q['aggregatesRecomputed']['1D'],1)
            self.assertFalse(q['wholeShareHistoricalPricesVerified'])

    def test_missing_execution_bar_remains_missing_and_breaks_stored_aggregate(self):
        frames,a,b = self.frame('2024-01-08');frames['5m'].pop(3)
        q = check_frames(frames,a,b)
        self.assertFalse(q['passedStructural']);self.assertEqual(q['missingFineBars'],1)
        self.assertGreater(q['errors']['aggregate_without_complete_fine'],0)

    def test_corrupted_aggregate_and_duplicate_are_detected(self):
        frames,a,b = self.frame('2024-01-08')
        frames['1D'][0] = replace(frames['1D'][0],close=100.5)
        frames['5m'].insert(1,frames['5m'][0]);q=check_frames(frames,a,b)
        self.assertIn('aggregate_mismatch',q['errors']);self.assertIn('duplicate_or_overlap',q['errors'])


class RobustnessContractTests(unittest.TestCase):
    def test_explicit_datasets_and_frozen_hypothesis_no_archive_or_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'source';root=Path(directory)/'new'
            old={'id':'source','engine':prior_binding()};selection={'planId':'source','primary':POLICY}
            selection['id']=stable_id(selection);write(source/'plan.json',old);write(source/'selection.json',selection)
            m={'symbol':'AAA','feed':'sip','adjustment':'split'}
            with patch('robustness_study.path_for',return_value=source/'metadata.json'):
                write(source/'metadata.json',{'material':m})
                p=prepare(root,source,{'AAA':'a'*64})
                self.assertEqual(p['policies'],[POLICY]);self.assertEqual(p['cohorts']['additional'],['AAA'])
                self.assertEqual(validate_plan(read(root/'plan.json')),p)
                self.assertEqual(prepare(root,source,{'AAA':'a'*64}),p)
                with self.assertRaises(DataError):prepare(root,source,{'BBB':'b'*64})
            altered={**p,'seed':1}
            with self.assertRaises(DataError):validate_plan(altered)

    def test_fees_are_paid_by_actual_ledger_not_subtracted_from_nominal_case_pnl(self):
        fixture=fixtures.ScreeningLedgerTests();fixture.setUp();c=fixture.case()
        c['signal']['cohort']='qualified';c['paths']['fixed:hard_stop:40']=c['paths']['fixed:hard_stop:20']
        free=_cost_ledger([c],fixture.contexts,fixture.phase,{'multiplier':1,'fee':0})
        fee=_cost_ledger([c],fixture.contexts,fixture.phase,{'multiplier':1,'fee':1})
        self.assertEqual(free['eligibleSignals'],fee['eligibleSignals'])
        trade=fee['trades'][0]
        self.assertEqual(trade['netPnl'],trade['quantity']*(trade['exitFill']-trade['entryFill'])-2)
        self.assertLess(trade['quantity'],free['trades'][0]['quantity'])
        self.assertEqual(fee['cash'],2000+trade['netPnl'])

    def test_unavailable_pre_ipo_symbol_never_opens_empty_control_pool(self):
        fixture=fixtures.ScreeningLedgerTests();fixture.setUp();case=fixture.case('A')
        case['signal']['cohort']='qualified';case['paths']['fixed:hard_stop:40']=case['paths']['fixed:hard_stop:20']
        fold={'name':'year'}
        p={'engine':binding(),'symbols':['A','B'],'folds':{'validation':[fold]},
           'cohorts':{'all':['A','B']},'costScenarios':[{'name':'base','multiplier':1,'fee':0},
               {'name':'double_cost','multiplier':2,'fee':0}], 'limitations':[]}
        p['id']=stable_id(p)
        with tempfile.TemporaryDirectory() as directory:
            frozen={'planId':p['id'],'primary':POLICY};frozen['id']=stable_id(frozen);write(Path(directory)/'selection.json',frozen)
            def cache(path,plan):return {'availability':'unavailable' if path.name.startswith('B-') else 'available','quality':{}}
            with patch('robustness_study.load_fold',return_value=([case],fixture.contexts,fixture.phase)),patch('robustness_study.load_task',side_effect=cache),patch('robustness_study.controls',return_value={'aboveQ90':False,'q90ReturnPct':None}) as control:
                result=evaluate(directory,p)
            self.assertEqual(control.call_args.args[1]['symbols'],['A'])
            self.assertEqual(result['windows'][0]['unavailableSymbols'],['B'])
            self.assertFalse(result['operationallyApproved'])


if __name__=='__main__':unittest.main()
