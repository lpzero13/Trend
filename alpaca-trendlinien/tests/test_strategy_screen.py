from copy import deepcopy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from lab_data import session_bounds
from models import DataError
from screening_portfolio import candidates, matches, ledger, development_gate, test_gate
from strategy_screen import select, write, read, load_task, later_test
from fan_geometry import stable_id
from workbench_portfolio import CloseMarks


class ScreeningLedgerTests(unittest.TestCase):
    def setUp(self):
        self.start,_=session_bounds('2024-01-08')
        self.phase={'startAt':self.start,'endAt':self.start+1800}
        self.policy=next(p for p in candidates() if p['id']=='breakout:all:fixed:sma0')
        self.contexts={s:SimpleNamespace(fine=CloseMarks([{'end':t,'close':100} for t in range(self.start+300,self.start+2100,300)])) for s in ('A','B','C','D')}

    def case(self,symbol='A',offset=300,exit_offset=900):
        return {'id':symbol+str(offset),'symbol':symbol,'datasetId':symbol,
            'signal':{'family':'breakout','cohort':'two','signalAt':self.start+offset-300},
            'context':{'dailyClose':100,'dailySma200':99},
            'entry':{'entryAt':self.start+offset,'entryPrice':100,'initialStop':95,'status':'filled',
                     'rules':{'spread_bps':0.,'slippage_bps':0.,'fee_per_order':0.}},
            'paths':{'fixed:hard_stop:20':{'status':'closed','exitAt':self.start+exit_offset,'exitPrice':102,'reason':'time'}}}

    def test_finite_cash_risk_and_whole_units_with_conflicting_signals(self):
        cases=[self.case(s) for s in ('A','B','C','D')]+[self.case('A',600)]
        value=ledger(cases,self.contexts,self.phase,self.policy)
        self.assertTrue(value['audit']['passed']);self.assertEqual(value['accepted'],3)
        self.assertEqual(value['closed'],3);self.assertEqual(value['cash'],2024)
        self.assertTrue(all(t['quantity']==4 for t in value['trades']))
        self.assertIn('max_positions',value['skippedReasons'])
        self.assertIn('already_holding_symbol',value['skippedReasons'])

    def test_capital_is_released_before_later_entry_without_new_deposit(self):
        value=ledger([self.case('A',300,600),self.case('B',600,900)],self.contexts,self.phase,self.policy)
        self.assertEqual(value['accepted'],2);self.assertEqual(value['cash'],2016)
        self.assertEqual(value['marketValue'],0)

    def test_higher_costs_change_actual_cash_fills_and_not_signal_selection(self):
        c=self.case();c['entry']['rules'].update(spread_bps=5,slippage_bps=5)
        one=ledger([c],self.contexts,self.phase,self.policy)
        two=ledger([c],self.contexts,self.phase,self.policy,cost_multiplier=2)
        self.assertEqual(one['eligibleSignals'],two['eligibleSignals'])
        self.assertLess(two['markedReturnPct'],one['markedReturnPct'])

    def test_future_missing_path_is_not_filtered_before_entry_but_halts_when_reached(self):
        case=self.case();case['paths']['fixed:hard_stop:20'].update(status='censored',missingAt=self.start+600,exitAt=None,exitPrice=None)
        result=ledger([case,self.case('B',900,1200)],self.contexts,self.phase,self.policy)
        self.assertEqual(result['accepted'],1);self.assertEqual(result['status'],'incomplete')
        self.assertEqual(result['halt']['at'],self.start+600);self.assertIsNone(result['markedReturnPct'])

    def test_filters_use_only_known_context_and_quality_not_future_path(self):
        c=self.case();before=matches(c,self.policy)
        c['paths']['fixed:hard_stop:20']['exitPrice']=1
        self.assertEqual(matches(c,self.policy),before)
        self.assertFalse(matches(c,{**self.policy,'quality':'qualified'}))
        self.assertTrue(matches(c,{**self.policy,'sma200':True}))
        c['context']['dailySma200']=None
        self.assertFalse(matches(c,{**self.policy,'sma200':True}))


class SelectionTests(unittest.TestCase):
    def fold(self,value=1.,trades=10):
        return {'status':'marked_to_phase_end','open':0,'accepted':trades,'markedReturnPct':value,
            'max5mSampledDrawdownPct':-2.,'positiveSymbols':5,'positiveProfitConcentration':.3}

    def test_exact_preregistered_candidate_count(self):
        items=candidates();self.assertEqual(len(items),30);self.assertEqual(len({p['id'] for p in items}),30)
        self.assertTrue(all(p['quality']=='qualified' for p in items if p['family']=='safety_bounce'))

    def test_negative_development_does_not_force_a_winner(self):
        policies=candidates();result=select({p['id']:[self.fold(-1)]*3 for p in policies},policies)
        self.assertIsNone(result['primary']);self.assertEqual(result['selectedByFamily'],{})

    def test_selection_uses_development_only_and_has_deterministic_tie_order(self):
        policies=candidates();results={p['id']:[self.fold()]*3 for p in policies}
        winner=select(results,policies)
        self.assertEqual(winner['primary']['id'],min(p['id'] for p in policies))
        self.assertEqual(len(winner['selectedByFamily']),3)
        self.assertFalse(development_gate([self.fold(trades=1)]*3))

    def test_positive_test_alone_is_insufficient_when_concentrated_or_cost_fragile(self):
        base=self.fold(trades=15);stress=self.fold()
        self.assertTrue(test_gate(base,stress)['passed'])
        base['positiveProfitConcentration']=.9
        self.assertFalse(test_gate(base,stress)['passed'])
        base['positiveProfitConcentration']=.3;stress['markedReturnPct']=-.1
        self.assertFalse(test_gate(base,stress)['passed'])

    def test_confirmation_does_not_open_datasets_when_primary_failed_validation(self):
        with tempfile.TemporaryDirectory() as root:
            selection={'planId':'p','primary':{'id':'winner'}};selection['id']=stable_id(selection)
            write(Path(root)/'selection.json',selection)
            write(Path(root)/'validation-summary.json',{'primaryPassed':False})
            with patch('strategy_screen.build',side_effect=AssertionError('must stay closed')):
                result=later_test(root,{'id':'p'},'confirmation')
            self.assertFalse(result['opened'])

    def test_plan_bound_compressed_caches_detect_changes(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'case.json.gz';payload={'planId':'p','value':1};payload['checksum']=stable_id(payload)
            write(path,payload);self.assertEqual(load_task(path,{'id':'p'}),payload)
            payload['value']=2;write(path,payload)
            with self.assertRaises(DataError):load_task(path,{'id':'p'})

    def test_followup_no_winner_keeps_later_block_uncomputed(self):
        from screening_extension import validate
        with tempfile.TemporaryDirectory() as root:
            selection={'planId':'p','primary':None};selection['id']=stable_id(selection)
            write(Path(root)/'selection.json',selection)
            with patch('screening_extension.build',side_effect=AssertionError('no later test without selection')):
                self.assertFalse(validate(root,{'id':'p'},lambda v:None)['opened'])

    def test_40_day_followup_does_not_silently_use_20_day_price_path(self):
        from screening_portfolio import adapt
        case=ScreeningLedgerTests();case.setUp();item=case.case()
        policy={**case.policy,'horizon':40}
        with self.assertRaises(KeyError):adapt(item,policy)
        item['paths']['fixed:hard_stop:40']={**item['paths']['fixed:hard_stop:20'],'exitPrice':110}
        self.assertEqual(adapt(item,policy)[1]['exitFill'],110)

    def test_external_basket_inherits_frozen_policy_without_selecting_again(self):
        from tools.test_fixed_basket import prepare, SYMBOLS
        from screening_extension import binding
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'source';root=Path(directory)/'external'
            p={'engine':binding(),'folds':{'validation':[{'name':'later'}]},'symbols':['OLD'],'datasets':{'OLD':'old'}}
            policy={**candidates()[0],'horizon':40,'id':'fixed-source-policy'}
            selection={'primary':policy};selection['id']=stable_id(selection)
            write(source/'plan.json',p);write(source/'selection.json',selection)
            stocks={'stocks':{s:{'status':'completed','datasetId':s} for s in SYMBOLS}}
            with patch('tools.test_fixed_basket.get',return_value=stocks):plan=prepare(root,source)
            frozen=read(root/'selection.json')
            self.assertEqual(frozen['primary'],policy);self.assertEqual(plan['policies'],[policy])
            self.assertEqual(plan['symbols'],list(SYMBOLS))

    def test_diagnostic_rerun_preserves_existing_output(self):
        from tools.stress_strategy_screen import stress
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);write(root/'plan.json',{});write(root/'selection.json',{})
            output=root/'already-there';output.mkdir()
            with self.assertRaises(ValueError):stress(root,output)


if __name__=='__main__':unittest.main()
