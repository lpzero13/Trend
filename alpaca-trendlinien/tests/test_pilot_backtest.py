from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fan_execution import ExecutionRules, entry_contract
from fan_geometry import FanRules
from fan_observer import WatchRules
from lab_data import session_bounds
from lab_metrics import expected_grid
from models import Bar, DataError
from pilot_backtest import PilotObserver, PilotSpec, scan, execute_path, summarize, audit
from pilot_cli import save_result
from test_fan_geometry import triangle
from test_fan_observer import append


def safety(known, *, qualified=True):
    return {"id":"safety","a_index":0,"b_index":5,"a_time":known-864000,"b_time":known-50000,
            "a_price":90.,"b_price":90.5,"slope":.1,"contacts":3,"qualified":qualified,
            "reactionContacts":2,"knownAt":known,"value":90.9,"level":1}


class PilotObserverTests(unittest.TestCase):
    def test_three_families_include_existing_real_breakout_and_red_retest(self):
        rows=append(append(triangle(),111,116,100,115),111,114,110.7,113)
        observer=PilotObserver("TEST",FanRules(atr_length=2,contact_atr=.001,wick_atr=0,min_age_days=0),
                               WatchRules(clean_atr=.01,retest_atr=.01,arm_bars=1,retest_bars=5))
        found=[]
        for bar in rows:found.extend(observer.push(bar)[1])
        red=[s for s in found if s['family']!='safety_bounce']
        self.assertEqual([s['family'] for s in red],['breakout','red_retest'])
        self.assertEqual(red[0]['subtype'],'immediate')
        self.assertEqual(red[0]['line'],red[1]['line'])
        self.assertEqual(red[0]['breakInitialStop'],red[1]['breakInitialStop'])
        self.assertEqual(red[0]['breakSafety'],red[1]['breakSafety'])

    def bounce(self, *, low=91.2, qualified=True, previous_close=95., current_only=False):
        opened,closed=session_bounds('2024-01-08')
        known=opened+14400;line=safety(known,qualified=qualified)
        old={'ready':True,'greens':[] if current_only else [line],'atr':2.,'sourceClose':known,'referenceIndex':9}
        new={**old,'greens':[line],'sourceClose':closed,'referenceIndex':10}
        observer=PilotObserver('TEST');observer.snapshot=old
        observer.previous=Bar(opened,known,94,96,93,previous_close,1)
        bar=Bar(known,closed,91.5,93,low,92,1)
        def update(_):observer.red.last_snapshot=new;return []
        with patch.object(observer.red,'push',side_effect=update):return observer.push(bar)[1]

    def test_bounce_uses_previously_qualified_line_and_limited_touch(self):
        signals=self.bounce();self.assertEqual(len(signals),1)
        s=signals[0];self.assertEqual(s['family'],'safety_bounce');self.assertEqual(s['cohort'],'qualified')
        self.assertLess(s['line']['knownAt'],s['signalAt'])
        self.assertTrue(s['validRisk'])
        self.assertEqual(self.bounce(low=89),[])
        self.assertEqual(self.bounce(qualified=False),[])
        self.assertEqual(self.bounce(previous_close=90),[])
        self.assertEqual(self.bounce(current_only=True),[])

    def test_future_changes_cannot_rewrite_prefix_signal_or_its_safety(self):
        base=append(append(triangle(),111,116,100,115),111,114,110.7,113)
        tail=append(base,114,118,111,117)
        altered=[*base,replace(tail[-1],open=300,high=500,low=1,close=400)]
        rules=FanRules(atr_length=2,contact_atr=.001,wick_atr=0,min_age_days=0)
        watch=WatchRules(clean_atr=.01,retest_atr=.01)
        # Geometry fixture uses continuous artificial 4h times; calendar/gaps
        # are exercised separately on actual regular-grid pilot/integration data.
        with patch('pilot_backtest.source_gaps',return_value={}):
            first=scan('TEST',tail,base[0].end,base[-1].end,rules=rules,watch=watch)[0]
            second=scan('TEST',altered,base[0].end,base[-1].end,rules=rules,watch=watch)[0]
        self.assertGreater(len(first),0);self.assertEqual(first,second)

    def test_gap_clears_bounce_and_red_state(self):
        observer=PilotObserver('TEST');observer.armed={'old'};observer.snapshot={'ready':True}
        bar=triangle()[-1];observer.gap(bar)
        self.assertEqual(observer.armed,set());self.assertIsNone(observer.snapshot)
        self.assertIsNone(observer.previous)

    def test_red_retest_uses_current_valid_safety_but_preserves_original_break(self):
        bar=triangle()[-1];old=safety(bar.time-10000);current=safety(bar.end)
        current.update(id='new-safety',value=96.)
        event={'kind':'entry_signal','variant':'retest','safety':old,'initialStop':90.,'features':{},
               'line':{'id':'original-red'},'breakAt':bar.time-10000,'cleanAt':bar.time-10000}
        observer=PilotObserver('TEST')
        def update(_):observer.red.last_snapshot={'green':current};return [deepcopy(event)]
        with patch.object(observer.red,'push',side_effect=update):
            signal=observer.push(bar)[1][0]
        self.assertEqual(signal['line']['id'],'original-red')
        self.assertEqual(signal['breakInitialStop'],90.)
        self.assertEqual(signal['breakSafety'],old)
        self.assertEqual(signal['safety']['id'],'new-safety')
        self.assertAlmostEqual(signal['initialStop'],95.71)
        self.assertEqual(event['initialStop'],90.)
        # No current Safety means an observed but non-executable signal.
        observer=PilotObserver('TEST')
        def absent(_):observer.red.last_snapshot={'green':None};return [deepcopy(event)]
        with patch.object(observer.red,'push',side_effect=absent):signal=observer.push(bar)[1][0]
        self.assertIsNone(signal['initialStop']);self.assertFalse(signal['validRisk'])

    def test_delayed_clean_close_is_a_breakout_subtype_not_an_extra_family(self):
        rows=append(triangle(),111,113,100,111.1)
        observer=PilotObserver('TEST',FanRules(atr_length=2,contact_atr=.001,wick_atr=0,min_age_days=0),
                               WatchRules(clean_atr=.1,arm_bars=1,retest_bars=5))
        for bar in rows:observer.push(bar)
        signals=observer.push(append(rows,111.1,118,111,117)[-1])[1]
        self.assertEqual(len(signals),1);self.assertEqual(signals[0]['family'],'breakout')
        self.assertEqual(signals[0]['subtype'],'delayed')

    def test_source_geometry_matches_chart_master_for_identical_prefix(self):
        from fan_geometry import profile, analyze
        rows=triangle();rules=profile('master',{'atr_length':2,'min_age_days':0})
        observer=PilotObserver('TEST',rules)
        for bar in rows:observer.push(bar)
        chart=analyze(rows,'4h',rules=rules,symbol='TEST')
        self.assertIsNotNone(chart['green'])
        self.assertEqual(observer.snapshot['green'],chart['green'])
        self.assertEqual(observer.snapshot['reds'],chart['reds'])


class PilotExecutionTests(unittest.TestCase):
    def setUp(self):
        self.open,self.close=session_bounds('2024-01-08')
        self.cutoff=session_bounds('2024-01-10')[1]
        self.fine=[Bar(t,t+300,105,106,100,105,10) for t in expected_grid(self.open,self.cutoff)]
        self.rules=ExecutionRules(latency_seconds=0,capital=2000,risk_fraction=.1,spread_bps=0,slippage_bps=0)
        self.signal={'id':'signal','signalAt':self.open-1,'initialStop':95,'safety':safety(self.open-2)}
        self.entry=entry_contract(self.signal,self.fine,self.cutoff,self.rules)

    def call(self,fine=None,timeline=(),model='fixed',mode='hard_stop',horizon=1,entry=None):
        return execute_path(self.signal,entry or self.entry,self.fine if fine is None else fine,timeline,self.cutoff,horizon,model,mode)

    def test_existing_fixed_execution_agrees_with_independent_pilot_path(self):
        from fan_execution import path
        reference=path(self.entry,self.fine,[],self.cutoff,1)
        actual=self.call()
        self.assertEqual(actual['netPnl'],reference['netPnl'])
        self.assertEqual(actual['reason'],reference['reason'])

    def test_hard_stop_gap_is_not_assumed_to_fill_at_stop(self):
        fine=[self.fine[0],replace(self.fine[1],open=90,high=92,low=89,close=91),*self.fine[2:]]
        actual=self.call(fine)
        self.assertEqual(actual['reason'],'stop_gap');self.assertEqual(actual['exitPrice'],90)
        self.assertLess(actual['netR'],-1)

    def test_missing_expected_entry_or_path_is_not_skipped(self):
        missing=entry_contract(self.signal,self.fine[1:],self.cutoff,self.rules)
        self.assertEqual(missing['reason'],'missing_expected_entry_open')
        actual=self.call([self.fine[0],*self.fine[2:]])
        self.assertEqual(actual['status'],'censored');self.assertEqual(actual['missingAt'],self.fine[1].time)

    def test_new_stop_never_applies_to_past_low_of_its_confirming_source_bar(self):
        close=self.open+14400
        line=safety(close);line.update(a_price=99.7,slope=.1)
        timeline=[{'closedAt':close,'index':10,'close':105,'green':line,'atr':2,'gap':False}]
        r=replace(self.rules,latency_seconds=300)
        entry={**self.entry,'rules':dict(self.entry['rules'],latency_seconds=300)}
        fine=[replace(b,low=96) if b.end<=close else b for b in self.fine]
        hit=next(i for i,b in enumerate(fine) if b.time==close+300)
        fine[hit]=replace(fine[hit],low=98)
        result=self.call(fine,timeline,'fan_safety',entry=entry)
        self.assertEqual(result['reason'],'stop')
        self.assertEqual(result['fillBarAt'],close+300)
        self.assertEqual(result['stopEvents'][0]['knownAt'],close)
        self.assertGreaterEqual(result['stopEvents'][0]['effectiveAt'],close+300)

    def test_close_stop_waits_for_source_close_then_later_fill(self):
        close=self.open+14400
        timeline=[{'closedAt':close,'index':10,'close':94,'green':None,'atr':2,'gap':False}]
        entry={**self.entry,'rules':dict(self.entry['rules'],latency_seconds=300)}
        fine=list(self.fine);hit=next(i for i,b in enumerate(fine) if b.time==close+300)
        fine[hit]=replace(fine[hit],open=90,high=92,low=89,close=91)
        result=self.call(fine,timeline,mode='close_stop',entry=entry)
        self.assertEqual(result['reason'],'close_stop');self.assertEqual(result['exitAt'],close+300)
        self.assertEqual(result['exitPrice'],90)
        # An earlier wick alone is ignored by this explicit close-stop model.
        fine[1]=replace(fine[1],low=80)
        self.assertEqual(self.call(fine,timeline,mode='close_stop',entry=entry)['exitAt'],close+300)

    def test_ratchet_does_not_lower_stop_with_flatter_replacement(self):
        one=self.open+14400;two=self.close
        high=safety(one);high.update(a_price=96,slope=.1)
        low=safety(two);low.update(a_price=90,slope=.1)
        timeline=[{'closedAt':one,'index':10,'close':105,'green':high,'atr':2,'gap':False},
                  {'closedAt':two,'index':11,'close':105,'green':low,'atr':2,'gap':False}]
        result=self.call(timeline=timeline,model='fan_safety')
        self.assertEqual(len(result['stopEvents']),1)
        self.assertGreater(result['finalStop'],95)

    def test_unaffordable_entries_remain_rejected_in_every_path(self):
        r=replace(self.rules,capital=1)
        entry=entry_contract(self.signal,self.fine,self.cutoff,r)
        self.assertEqual(entry['status'],'rejected')
        self.assertEqual(self.call(entry=entry)['status'],'rejected')

    def test_source_gap_censors_at_first_missing_close_not_later_recovery(self):
        missing=self.open+14400
        timeline=[{'closedAt':self.close,'gap':True,'gapAt':missing,'index':10,'close':105,'green':None,'atr':2}]
        result=self.call(timeline=timeline)
        self.assertEqual(result['status'],'censored');self.assertEqual(result['missingAt'],missing)

    def test_close_stop_ignores_wick_if_source_close_remains_above_stop(self):
        close=self.open+14400
        timeline=[{'closedAt':close,'index':10,'close':105,'green':None,'atr':2,'gap':False}]
        fine=list(self.fine);fine[1]=replace(fine[1],low=90)
        hard=self.call(fine,timeline)
        soft=self.call(fine,timeline,mode='close_stop')
        self.assertEqual(hard['reason'],'stop');self.assertEqual(soft['reason'],'time')

    def test_stop_decision_does_not_inspect_future_fan_replacement(self):
        current=self.open+14400
        high=safety(current);high.update(a_price=103,slope=.1)
        future={'closedAt':self.cutoff+3600,'index':100,'close':110,'green':high,'atr':2,'gap':False}
        base=self.call(model='fan_safety')
        self.assertEqual(base,self.call(timeline=[future],model='fan_safety'))


class PilotContractTests(unittest.TestCase):
    def test_bounded_window_and_inputs(self):
        PilotSpec().bounds()
        for spec in (PilotSpec(end='2025-01-01'),PilotSpec(start='bad'),PilotSpec(warmup_days=20),
                     PilotSpec(horizons=(0,)),PilotSpec(stop_modes=('bad',)),PilotSpec(arm_bars=0)):
            with self.assertRaises(DataError):spec.bounds()

    def test_empty_families_are_explicit_not_silently_omitted(self):
        result=summarize([],PilotSpec())
        self.assertEqual(set(result),{'breakout','red_retest','safety_bounce'})
        self.assertTrue(all(v['signals']==0 for v in result.values()))

    def test_saved_results_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(DataError):save_result(folder,{})

    def test_audit_rejects_future_line(self):
        case={'id':'x','signal':{'signalAt':100,'line':{'knownAt':101}},'entry':{'status':'rejected'},'paths':{}}
        result=audit([case],90,110)
        self.assertFalse(result['passed']);self.assertEqual(result['errors'][0][1],'signal_time_or_line_availability')


if __name__=='__main__':unittest.main()
