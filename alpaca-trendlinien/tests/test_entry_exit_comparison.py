from copy import deepcopy
import unittest
from types import SimpleNamespace

from entry_exit_comparison import group_cases, analyze_group, validate_case, case_rows, MODELS


def case(identity='one',cohort='qualified'):
    entry={'status':'filled','entryAt':1700000000,'entryFill':100.,'initialStop':90.,'initialRisk':10.,
           'plannedRisk':100.,'quantity':10,'rules':{'fee_per_order':0.}}
    paths={}
    for model,r in zip(MODELS,(1.,.5,.8)):
        paths[model+':hard_stop:40']={'status':'closed','exitAt':1700086400,'exitFill':100+10*r,
            'netR':r,'reason':'time','mfeR':1.5}
    return {'id':identity,'symbol':'A','foldName':'year','entry':entry,'paths':paths,
            'signal':{'family':'breakout','cohort':cohort,'subtype':'immediate','signalAt':1699999700}}


class EntryExitComparisonTests(unittest.TestCase):
    def test_quality_classes_are_disjoint_and_do_not_depend_on_later_results(self):
        cases=[case('qualified'),case('two','two'),case('young','three_young')]
        for cohort in ('qualified','two','three_young'):
            self.assertEqual(len(group_cases(cases,'breakout',cohort)),1)
        before=group_cases(cases,'breakout','qualified')
        cases[0]['paths']['fixed:hard_stop:40']['netR']=-100
        self.assertEqual(group_cases(cases,'breakout','qualified'),before)

    def test_paired_models_use_identical_entries_and_show_missing_denominator(self):
        a,b=case(),case('incomplete')
        b['paths']['fan_safety:hard_stop:40'].update(status='censored',netR=None,exitAt=None)
        result=analyze_group([a,b])
        self.assertEqual(result['filled'],2);self.assertEqual(result['commonComplete'],1)
        self.assertEqual(result['incompleteForPaired'],1)
        self.assertEqual(result['models']['fixed']['allObservedClosed']['n'],2)
        self.assertTrue(all(v['sameEntries']['n']==1 for v in result['models'].values()))
        self.assertEqual(result['pairedAgainstFixed']['original_safety']['meanDeltaR'],-.5)

    def test_rejected_entries_are_not_counted_as_losses_or_filled_samples(self):
        c=case();c['entry'].update(status='rejected',reason='invalid_signal_stop')
        for p in c['paths'].values():p.update(status='rejected',netR=None)
        result=analyze_group([c]);self.assertEqual(result['filled'],0)
        self.assertIsNone(result['models']['fixed']['sameEntries']['meanNetR'])
        self.assertEqual(result['entryReasons'],{'invalid_signal_stop':1})

    def test_saved_net_r_is_independently_recomputed_before_use(self):
        c=case();validate_case(c)
        c['paths']['original_safety:hard_stop:40']['netR']=10
        with self.assertRaises(AssertionError):validate_case(c)

    def test_sma_and_context_are_not_used_to_relabel_contact_quality(self):
        c=case();c['context']={'dailyClose':1,'dailySma200':100}
        self.assertEqual(group_cases([c],'breakout','qualified'),[c])

    def test_csv_includes_unobservable_exit_instead_of_silently_dropping_it(self):
        c=case();c['paths']['fan_safety:hard_stop:40'].update(status='censored',netR=None,exitAt=None)
        rows=list(case_rows([c]));self.assertEqual(len(rows),3)
        self.assertTrue(all(not r['commonComplete'] for r in rows))
        self.assertEqual(rows[-1]['pathStatus'],'censored')

    def test_equal_stock_window_diagnostic_exposes_high_frequency_stock_weight(self):
        cases=[case(str(i)) for i in range(3)]+[case('b')]
        cases[-1]['symbol']='B'
        cases[-1]['paths']['original_safety:hard_stop:40']['netR']=3.
        d=analyze_group(cases)['pairedAgainstFixed']['original_safety']
        self.assertEqual(d['meanDeltaR'],.125)
        self.assertEqual(d['equalStockWindowMeanDeltaR'],.75)
        self.assertEqual(d['leaveOneSymbolOutDeltaRange'],[-.5,2.])

    def test_gap_exit_verifier_uses_closed_bar_clock_without_extra_open_sample(self):
        from lab_data import session_bounds
        from screening_portfolio import ledger
        from tools.verify_robustness_study import verify_marks
        from workbench_portfolio import CloseMarks
        from test_strategy_screen import ScreeningLedgerTests
        fixture=ScreeningLedgerTests();fixture.setUp();start,end=session_bounds('2024-01-08');tomorrow,_=session_bounds('2024-01-09')
        a=fixture.case('A',300);b=fixture.case('B',300)
        a['paths']['fixed:hard_stop:20'].update(exitAt=tomorrow,exitPrice=90,reason='stop_gap')
        b['paths']['fixed:hard_stop:20'].update(exitAt=tomorrow+600,exitPrice=100)
        contexts={s:SimpleNamespace(fine=CloseMarks([{'end':start+600,'close':100},
            {'end':end,'close':95 if s=='B' else 100},{'end':tomorrow+300,'close':100},
            {'end':tomorrow+600,'close':100}])) for s in ('A','B')}
        period={'startAt':start,'endAt':tomorrow+600};v=ledger([a,b],contexts,period,fixture.policy)
        self.assertAlmostEqual(v['max5mSampledDrawdownPct'],-2.)
        verify_marks(v,contexts,period,{'spread_bps':0.,'slippage_bps':0.,'fee_per_order':0.},{'A':'A','B':'B'})


if __name__=='__main__':unittest.main()
