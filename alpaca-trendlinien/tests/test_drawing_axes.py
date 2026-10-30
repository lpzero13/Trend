import copy
from dataclasses import asdict
from datetime import datetime
import unittest
from models import NY
from drawing_axes import add_drawing_axes
from test_weekly_chart import days


class DrawingAxisTests(unittest.TestCase):
    def test_future_positions_cross_weekends_dst_and_holidays_without_future_candles(self):
        rows=days('2025-02-03','2025-03-07')
        payload={'charts':{'1D':{'bars':[asdict(b) for b in rows]}},'sources':{'1D':{'normalization':'tori-rth-5m-v1'}}}
        before=copy.deepcopy(payload['charts']);add_drawing_axes(payload)
        axis=payload['drawingAxes']['1D']
        self.assertEqual(payload['charts'],before)
        self.assertEqual(axis[:len(rows)],[b.time for b in rows])
        future=[datetime.fromtimestamp(t,NY) for t in axis[len(rows):]]
        self.assertEqual(future[0].date().isoformat(),'2025-03-10')
        self.assertEqual((future[0].hour,future[0].minute),(9,30))
        self.assertNotIn('2025-04-18',[d.date().isoformat() for d in future])
        self.assertTrue(all(d.weekday()<5 for d in future))
        self.assertEqual(axis,sorted(set(axis)))

    def test_future_hour_buckets_respect_short_sessions_and_weekly_first_session(self):
        rows=days('2025-11-03','2025-11-26')
        payload={'charts':{tf:{'bars':[asdict(b) for b in rows]} for tf in ('1h','4h','1W')},
                 'sources':{tf:{'normalization':'tori-rth-5m-v1'} for tf in ('1h','4h','1W')}}
        add_drawing_axes(payload)
        for tf,count in [('1h',4),('4h',1)]:
            friday=[datetime.fromtimestamp(t,NY) for t in payload['drawingAxes'][tf] if datetime.fromtimestamp(t,NY).date().isoformat()=='2025-11-28']
            self.assertEqual(len(friday),count)
        self.assertTrue(all(datetime.fromtimestamp(t,NY).date().isoformat()!='2025-11-27' for t in payload['drawingAxes']['4h']))
