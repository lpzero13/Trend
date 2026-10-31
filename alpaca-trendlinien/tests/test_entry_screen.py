from copy import deepcopy
from dataclasses import replace
import unittest

from entry_screen import Context,features,select,PROFILES,decisions
from fan_study import schedule,timestamp
from models import Bar


def fixture():
    start,end=timestamp('2023-01-03'),timestamp('2024-04-30',upper=True)
    daily=[Bar(t,e,100,140,90,100+i*.1,1) for i,(t,e) in enumerate(schedule(start,end,'1D'))]
    rows=[Bar(t,e,120,121,119,120,1) for t,e in schedule(start,end,'4h')]
    i=420;at=rows[i].end
    red={'a_index':i-60,'a_time':rows[i-60].time,'a_price':120.,'slope':-.25,
         'knownAt':at-3600,'span_days':30.,'qualified':True,'contactPoints':[]}
    green={**red,'a_index':i-100,'a_time':rows[i-100].time,'a_price':85.,'slope':.05,'span_days':60.}
    s={'line':red,'safety':green,'signalAt':at,'signalClose':120.,'initialStop':116.,
       'family':'red_retest','cohort':'qualified','features':{'atr':2.}}
    return s,rows,daily


class ScreenTests(unittest.TestCase):
    def test_complete_setup_passes_and_all_rules_are_explicit(self):
        s,rows,daily=fixture();f=features(s,Context(rows,daily))
        self.assertTrue(select(f,'balanced')['accepted'])
        self.assertTrue(select(f,'strict')['accepted'])
        self.assertEqual(f['sourceIndex'],420)
        self.assertAlmostEqual(f['compressionRatio'],15/33)
        self.assertLessEqual(f['dailyAsOf'],s['signalAt'])
        self.assertEqual(set(decisions(f)),{'qualified','risk','trend','mature','convergent','both_qualified','not_stretched'})

    def test_future_bars_and_unfinished_daily_bar_cannot_change_selection(self):
        s,rows,daily=fixture();at=s['signalAt']
        original=features(s,Context(rows,daily))
        prefix=features(s,Context([b for b in rows if b.end<=at],[b for b in daily if b.end<=at]))
        poisoned=features(s,Context([replace(b,close=100000) if b.end>at else b for b in rows],
                                   [replace(b,close=100000) if b.end>at else b for b in daily]))
        self.assertEqual(original,prefix);self.assertEqual(original,poisoned)
        self.assertEqual({k:select(prefix,k) for k in PROFILES},{k:select(poisoned,k) for k in PROFILES})

    def test_missing_or_gapped_daily_context_is_unknown_not_a_false_pass(self):
        s,rows,daily=fixture();at=s['signalAt']
        f=features(s,Context(rows,daily[:100]))
        self.assertIn('trend',select(f,'balanced')['unknown'])
        known=[b for b in daily if b.end<=at]
        f=features(s,Context(rows,known[:-20]+known[-19:]))
        self.assertIsNone(f['dailySma200']);self.assertFalse(select(f,'balanced')['accepted'])
        f=features(s,Context(rows,known[:-1]))
        self.assertFalse(f['dailyCurrent']);self.assertIsNone(f['dailySma200'])

    def test_percent_and_atr_are_joint_checks_not_equivalent_bins(self):
        s,rows,daily=fixture();ctx=Context(rows,daily)
        s['features']['atr']=10.
        f=features(s,ctx);self.assertGreater(f['signalStopPct'],2);self.assertLess(f['signalStopATR'],1)
        self.assertFalse(select(f,'risk')['accepted'])
        s['features']['atr']=.1;s['initialStop']=119.
        f=features(s,ctx);self.assertGreater(f['signalStopATR'],1);self.assertLess(f['signalStopPct'],2)
        self.assertFalse(select(f,'risk')['accepted'])

    def test_crossed_triangle_and_future_contacts_do_not_qualify(self):
        s,rows,daily=fixture();ctx=Context(rows,daily)
        s['line']['slope']=-1.
        self.assertFalse(select(features(s,ctx),'convergent')['accepted'])
        s['line']['contactPoints']=[{'known_at':s['signalAt']+1}]
        self.assertFalse(select(features(s,ctx),'qualified')['accepted'])

    def test_stretched_breakout_excluded_without_deleting_same_episode_retest(self):
        s,rows,daily=fixture();ctx=Context(rows,daily);s['features']['atr']=.5
        s['family']='breakout'
        self.assertIn('not_stretched',select(features(s,ctx),'strict')['failed'])
        s['family']='red_retest'
        self.assertTrue(select(features(s,ctx),'strict')['accepted'])

    def test_signal_does_not_mutate_or_use_entry_outcomes(self):
        s,rows,daily=fixture();before=deepcopy(s)
        f=features(s,Context(rows,daily))
        self.assertEqual(before,s)
        self.assertNotIn('entryFill',f);self.assertNotIn('netR',f)


if __name__=='__main__':unittest.main()
