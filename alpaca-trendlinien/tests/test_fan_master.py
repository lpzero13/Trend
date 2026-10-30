from collections import deque
from copy import deepcopy
from dataclasses import asdict, replace
import unittest

from fan_geometry import FanRules, Pivot, create_engine, profile
from fan_master import MasterEngine, context
from models import Bar, DataError
from test_fan_geometry import triangle


def manual(high_at_five=115.5):
    rules = profile("master", {"atr_length":2,"min_age_days":0})
    e = MasterEngine("TEST","4h",rules)
    start = 1700000000
    rows = []
    for i in range(23):
        h = 120-i-.2
        if i in (0,10,20): h=120-i
        if i == 5: h=high_at_five
        rows.append((i,Bar(start+i*14400,start+(i+1)*14400,h-1,h,h-2,h-1,100),2.))
    pivots = [Pivot(i,rows[i][1].time,120-i,2.,i+2,rows[i+2][1].end) for i in (0,10,20)]
    e.index = 22
    return e,pivots,rows


class MasterTests(unittest.TestCase):
    def test_refit_uses_envelope_and_preserves_true_pivot_contacts(self):
        e,ps,rows = manual()
        line = e._build(True,ps,rows)[0]
        self.assertEqual(line.origin,"refit")
        self.assertGreater(line.slope,-1.)
        self.assertEqual(len(line.contacts),3)
        self.assertNotEqual(line.b_price,ps[1].price)
        self.assertAlmostEqual(line.b_price,line.at(line.b_index))
        out = line.output(22,rows[-1][1].end,e.rules)
        self.assertEqual(out["color"],"#800000")
        self.assertTrue(out["qualified"])
        # Independent slow candle inequality, not the envelope helper.
        for i,b,atr in rows:
            if i <= line.a_index+e.rules.pivot_side:continue
            p=line.at(i)
            self.assertLessEqual(max(b.open,b.close),p+e.rules.body_atr*atr+1e-9)
            self.assertLessEqual(b.high,p+e.rules.wick_atr*atr+1e-9)

    def test_envelope_fallback_does_not_invent_second_pivot_contact(self):
        e,ps,rows=manual(118.)
        line=e._build(True,ps,rows)[0]
        out=line.output(22,rows[-1][1].end,e.rules)
        self.assertTrue(out["provisionalEnvelope"])
        self.assertEqual(out["contacts"],1)
        self.assertFalse(out["qualified"])

    def test_later_fan_uses_shorter_gap_with_three_real_contacts(self):
        e,_,_=manual()
        start=1700000000
        highs=[120-.1*i-.5 if i<10 else 119-.4*(i-10)-.5 for i in range(27)]
        points={0:120,10:119,20:115,24:114}
        highs=[points.get(i,h) for i,h in enumerate(highs)]
        rows=[(i,Bar(start+i*14400,start+(i+1)*14400,h-1,h,h-2,h-1,1),2.) for i,h in enumerate(highs)]
        ps=[Pivot(i,rows[i][1].time,v,2.,i+2,rows[i+2][1].end) for i,v in points.items()]
        e.index=26
        lines=e._build(True,ps,rows)
        self.assertGreaterEqual(len(lines),2)
        self.assertEqual(lines[0].gap,5)
        self.assertEqual(lines[1].gap,3)
        self.assertEqual(len(lines[1].contacts),3)

    def test_cache_full_rebuild_prefix_and_horizon_agree(self):
        rules=profile("master",{"atr_length":2,"action_lookback_days":10})
        a,b=create_engine("T","4h",rules),create_engine("T","4h",rules)
        saved=None
        rows=triangle(170)
        for i,bar in enumerate(rows):
            a.push(bar);b.push(bar);b.cache.clear()
            for pine in (False,True):
                self.assertEqual(a.snapshot(pine=pine),b.snapshot(pine=pine),(i,pine))
            if i==90:saved=deepcopy(a.snapshot())
        self.assertLess(a.rebuilds,b.rebuilds)
        replay=create_engine("T","4h",rules)
        for bar in rows[:91]:replay.push(bar)
        self.assertEqual(saved,replay.snapshot())
        for line in a.snapshot()["reds"]:
            self.assertGreaterEqual(line["a_time"],rows[-1].end-10*86400)

    def test_main_safety_and_context_have_no_future_values(self):
        rules=profile("master",{"atr_length":2})
        e=create_engine("T","4h",rules)
        rows=triangle(90)
        base=rows[-1]
        rows += [replace(base,time=base.end+(i-90)*14400,end=base.end+(i-89)*14400,
                         open=100,close=100,high=110,low=90) for i in range(90,230)]
        for bar in rows:e.push(bar)
        snap=e.snapshot()
        self.assertEqual(snap["mainSafety"]["level"],1)
        self.assertEqual(snap["mainSafety"]["color"],"#1e88e5")
        c=context(rows)
        self.assertAlmostEqual(c["sma200"],sum(b.close for b in rows[-200:])/200)
        self.assertEqual(c["series"]["50"][0]["time"],rows[49].time)
        self.assertIsNone(context(rows[:199])["sma200"])
        prefix=context(rows[:100])
        changed=context(rows[:100]+[replace(b,open=1000,close=1000,high=1001,low=999) for b in rows[100:]])
        self.assertEqual(prefix["series"],{n:[p for p in series if p["time"]<=rows[99].time] for n,series in changed["series"].items()})
        self.assertIsNone(context(rows,{220})["sma50"])
        self.assertTrue(all(item["time"] <= rows[99].time for series in context(rows[:100])["series"].values() for item in series))

    def test_old_profile_stays_classic_and_bad_parameters_rejected(self):
        self.assertEqual(profile("extreme").algorithm,"classic")
        self.assertEqual(profile("master").algorithm,"master")
        for args in ({"body_atr":float("nan")},{"action_lookback_days":True},{"algorithm":"future"}):
            with self.assertRaises(DataError):FanRules(**args)


if __name__=="__main__":unittest.main()
