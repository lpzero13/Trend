from copy import deepcopy
from datetime import datetime,timezone
import unittest

from lab_data import session_bounds
from lab_metrics import expected_grid
from models import Bar
from signal_path_index import PathIndex,isolated_entry,execute_unbounded
from exit_followup import execute_policy,policy_timeline,terminal,stop_mark,unrealized_r


def setup():
    opened,_=session_bounds('2024-01-08');_,end=session_bounds('2024-01-09')
    bars=[Bar(t,t+300,100,101,99,100,1) for t in expected_grid(opened,end)]
    original={'id':'original','a_index':0,'a_price':90.,'slope':.01,'knownAt':opened-300,
              'contacts':3,'qualified':True,'span_days':10.}
    s={'id':'signal','signalAt':opened-300,'initialStop':89.7,'safety':original}
    index=PathIndex(bars,end);entry=isolated_entry(s,index)
    current={**original,'id':'current','a_price':98.7,'slope':.01,'contacts':2,'qualified':False}
    known=bars[4].end
    state={'closedAt':known,'index':10,'close':100.,'green':{**current,'knownAt':known},'gapAt':None,'gap':False}
    return {'signal':s,'entry':entry},bars,end,[state]


class FollowupTests(unittest.TestCase):
    def test_two_contact_fan_does_not_replace_original_until_qualified(self):
        case,bars,end,timeline=setup();b=bars[6];bars[6]=Bar(b.time,b.end,100,101,98,100,1)
        index=PathIndex(bars,end)
        reference=execute_unbounded(case['signal'],case['entry'],index,timeline,'original_safety')
        fan=execute_unbounded(case['signal'],case['entry'],index,timeline,'fan_safety')
        constrained=execute_policy(case,index,timeline,'qualified_fan')
        self.assertEqual(reference['status'],'open');self.assertEqual(fan['status'],'closed')
        for key in ('status','finalStop','mfeR','maeR','lastObservedAt'):
            self.assertEqual(reference[key],constrained[key],key)
        timeline[0]['green'].update(qualified=True,contacts=3,span_days=8.)
        allowed=execute_policy(case,index,timeline,'qualified_fan')
        self.assertEqual(allowed['status'],'closed')
        self.assertTrue(all(v['qualified'] for v in allowed['stopEvents'] if v['source']=='current'))
        self.assertEqual(allowed['stopEvents'][0]['effectiveAt'],bars[6].time)

    def test_gate_uses_net_closed_candle_not_intrabar_mfe_and_is_latched(self):
        case,bars,end,timeline=setup()
        b=bars[4];bars[4]=Bar(b.time,b.end,100,135,99,100,1)
        b=bars[10];bars[10]=Bar(b.time,b.end,100,132,99,130,1)
        b=bars[11];bars[11]=Bar(b.time,b.end,130,132,125,130,1)
        b=bars[12];bars[12]=Bar(b.time,b.end,125,126,98,100,1)
        known=bars[10].end
        timeline.append({**timeline[0],'closedAt':known,'index':11,'close':130.,'green':{**timeline[0]['green'],'knownAt':known}})
        timeline.append({**timeline[0],'closedAt':bars[20].end,'index':12,'close':101.})
        prepared,gate=policy_timeline(case,timeline,'r2_fan')
        self.assertEqual(gate,known)
        self.assertEqual(prepared[0]['green']['id'],'original')
        self.assertEqual(prepared[1]['green']['id'],'current')
        self.assertEqual(prepared[2]['green']['id'],'current')
        p=execute_policy(case,PathIndex(bars,end),timeline,'r2_fan')
        self.assertEqual(p['gateAt'],known)
        self.assertEqual(p['status'],'closed')
        self.assertGreaterEqual(p['fillBarAt'],known+300)

    def test_new_policy_does_not_mutate_original_entry_or_award_future_gate(self):
        case,bars,end,timeline=setup();before=deepcopy(case)
        b=bars[2];bars[2]=Bar(b.time,b.end,100,101,80,90,1)
        timeline.append({**timeline[0],'closedAt':bars[20].end,'index':20,'close':200.})
        p=execute_policy(case,PathIndex(bars,end),timeline,'r2_fan')
        self.assertEqual(p['status'],'closed');self.assertIsNone(p['gateAt'])
        self.assertEqual(case,before)
        self.assertEqual(p['stopEvents'],[])

    def test_original_candidate_remains_when_current_qualified_line_is_lower(self):
        case,_,_,timeline=setup()
        timeline[0]['green'].update(a_price=80.,qualified=True,contacts=3)
        prepared,_=policy_timeline(case,timeline,'qualified_fan')
        self.assertEqual(prepared[0]['green']['id'],'original')

    def test_open_marks_are_valuation_and_censored_cases_remain_unknown(self):
        case,_,_,_=setup();e=case['entry']
        case['paths']={'x':{'status':'open','markNetReturnPct':12.,'markNetPnl':120.,'finalStop':95.}}
        self.assertEqual(terminal(case,'x')['pct'],12.)
        self.assertFalse(terminal(case,'x')['realized'])
        self.assertAlmostEqual(stop_mark(case,'x'),unrealized_r(e,95.))
        case['paths']['x']['status']='censored'
        self.assertIsNone(terminal(case,'x'))
        self.assertIsNotNone(stop_mark(case,'x'))  # explicitly last-observed hypothetical mark only

    def test_future_known_line_is_not_admitted(self):
        case,_,_,timeline=setup();timeline[0]['green'].update(qualified=True,knownAt=timeline[0]['closedAt']+1)
        prepared,_=policy_timeline(case,timeline,'qualified_fan')
        self.assertEqual(prepared[0]['green']['id'],'original')


if __name__=='__main__':unittest.main()
