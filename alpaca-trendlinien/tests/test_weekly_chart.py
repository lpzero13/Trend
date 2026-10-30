from copy import deepcopy
from dataclasses import asdict,replace
from datetime import datetime,timezone
import unittest
from unittest.mock import patch

from models import Bar,NY,DataError
from lab_splits import sessions_between
from lab_data import session_bounds
from weekly_chart import weeks,week_sessions,add_weekly,next_close
from server import chart_payload,step_payload


def days(start,end):
    rows=[]
    for i,d in enumerate(sessions_between(start,end)):
        opened,closed=session_bounds(d);p=100+i
        rows.append(Bar(opened,closed,p,p+3,p-2,p+1,100+i))
    return rows


class WeeklyTests(unittest.TestCase):
    def test_expected_ohlcv_and_missing_day_are_not_filled(self):
        rows=days('2025-03-03','2025-03-07');r=weeks(rows,rows[-1].end)
        self.assertEqual(len(r),1);self.assertEqual(r[0],Bar(rows[0].time,rows[-1].end,100,107,98,105,510))
        self.assertEqual(weeks(rows[:2]+rows[3:],rows[-1].end),[])
        self.assertEqual(weeks(rows,rows[-1].end-1),[])

    def test_good_friday_and_thanksgiving_close_on_actual_last_session(self):
        for start,end,lastday,hour in [('2025-04-14','2025-04-18',17,16),('2025-11-24','2025-11-28',28,13)]:
            rows=days(start,end);r=weeks(rows,rows[-1].end)
            self.assertEqual(len(r),1);dt=datetime.fromtimestamp(r[0].end,NY)
            self.assertEqual((dt.day,dt.hour),(lastday,hour))
            self.assertEqual(weeks(rows,rows[-1].end-300),[])

    def test_dst_and_year_boundary_are_exchange_weeks(self):
        rows=days('2025-03-03','2025-03-14');r=weeks(rows,rows[-1].end)
        self.assertEqual(len(r),2);self.assertEqual(datetime.fromtimestamp(r[0].time,timezone.utc).hour,14)
        self.assertEqual(datetime.fromtimestamp(r[1].time,timezone.utc).hour,13)
        rows=days('2024-12-30','2025-01-03');r=weeks(rows,rows[-1].end)
        self.assertEqual(len(r),1);self.assertEqual(datetime.fromtimestamp(r[0].end,NY).year,2025)

    def test_future_shocks_do_not_enter_known_week_or_change_older_sources(self):
        rows=days('2025-01-02','2025-04-08');at=next(b.end for b in rows if datetime.fromtimestamp(b.time,NY).date().isoformat()=='2025-03-12')
        a=weeks(rows,at);b=weeks([replace(x,high=999,close=998) if x.end>at else x for x in rows],at)
        self.assertEqual(a,b);self.assertTrue(all(x.end<=at for x in a))
        self.assertEqual(datetime.fromtimestamp(a[-1].end,NY).date().isoformat(),'2025-03-07')

    def test_main_chart_and_live_week_steps_only_fetch_daily_sources_not_new_raw_week_feed(self):
        daily=days('2025-01-02','2025-04-08');now=datetime(2025,4,10,tzinfo=timezone.utc)
        def loader(symbol,tf,**kwargs):
            self.assertIn(tf,('1h','4h','1D'))
            end=kwargs.get('end',now).timestamp();rows=[b for b in daily if b.end<=end]
            return rows,{'quality':{'rejected':0},'mode':'cache','cached':True}
        with patch('server.load_bars',side_effect=loader) as request,patch('server.datetime') as clock:
            clock.now.return_value=now;clock.fromtimestamp.side_effect=datetime.fromtimestamp
            p=chart_payload('TEST','1W',include_analysis=False)
        self.assertEqual(len(request.call_args_list),3);self.assertEqual(p['timeframe'],'1W')
        self.assertFalse(p['analysisEnabled']);self.assertIn('1W',p['charts'])
        self.assertEqual(datetime.fromtimestamp(p['latest']['end'],NY).date().isoformat(),'2025-04-04')
        cutoff=next(b.end for b in daily if datetime.fromtimestamp(b.time,NY).date().isoformat()=='2025-03-07')
        with patch('server.load_bars',side_effect=loader),patch('server.datetime') as clock:
            clock.now.return_value=now;clock.fromtimestamp.side_effect=datetime.fromtimestamp;clock.fromisoformat.side_effect=datetime.fromisoformat
            target=step_payload('TEST','1W',datetime.fromtimestamp(cutoff,timezone.utc).isoformat(),'next')
        self.assertEqual(datetime.fromtimestamp(target['closedAt'],NY).date().isoformat(),'2025-03-14')

    def test_short_history_keeps_old_views_and_rejects_week_view_clearly(self):
        rows=days('2025-03-03','2025-03-07');payload={'charts':{'1D':{'bars':[asdict(b) for b in rows]}},'analysisCutoff':rows[-1].end}
        result=add_weekly(deepcopy(payload),'1D')
        self.assertEqual(result['charts'],payload['charts'])
        self.assertIn('drawingAxes',result)
        with self.assertRaises(DataError):add_weekly(deepcopy(payload),'1W')
        with self.assertRaises(DataError):next_close(rows[-1].end,rows[-1].end)
