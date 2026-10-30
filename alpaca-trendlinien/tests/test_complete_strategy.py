"""Synthetic causal counterexamples, never market performance evidence."""
from copy import deepcopy
from dataclasses import asdict, replace
import unittest
from unittest.mock import patch

from complete_strategy import (CompleteReplay, EventCalendar, IncrementalGeometry,
                               PROFILES, RULES, qualified, source_grid, update_contact)
from complete_outcomes import Outcomes, confirmed_higher_low
from datasets import digest
from entry_geometry import at, episodes, violation
from models import Bar
from lab_data import resample_regular
import test_entry_discovery as fixture
import test_safety_strategy as safety


def candidate(rows, upper):
    old = fixture.candidate(rows, upper)
    return {**old, 'count': 3, 'exactCount': 2, 'lastTouch': 10,
            'lastExact': 10, 'separated': True, 'exactSeparated': True, 'emitted': []}


class CompleteGeometryTests(unittest.TestCase):
    def test_legal_near_touch_is_counted_but_illegal_wick_is_rejected(self):
        ray = {'a_index': 0, 'a_price': 100, 'slope': 0}
        c = {'ray': ray, 'upper': True, 'width': .05, 'atrAtCreation': 1,
             'count': 2, 'exactCount': 2, 'lastTouch': 0, 'lastExact': 0,
             'separated': True, 'exactSeparated': True}
        rows = [Bar(i, i+1, 99, 99.97, 98, 99, 1) for i in range(3)]
        update_contact(c, rows, 2)
        self.assertEqual(c['count'], 3)
        self.assertEqual(c['exactCount'], 2)
        self.assertFalse(violation(ray, rows[2], 2, True, .05))
        self.assertTrue(violation(ray, replace(rows[2], high=100.02), 2, True, .05))

    def test_adjacent_bars_are_not_three_bounces(self):
        ray = {'a_index': 0, 'a_price': 100, 'slope': 0}
        rows = [Bar(i, i+1, 99.9, 100, 99.8, 99.9, 1) for i in range(5)]
        self.assertEqual(len(episodes(ray, rows, 4, True, .1, 1)), 1)

    def test_incremental_geometry_matches_existing_geometry_at_each_known_prefix(self):
        from entry_geometry import Geometry
        highs = [110,105,104,109,104,103,108,103,102,107,102,101,101,100,100,100,100]
        rows = [Bar(1700000000+i*14400, 1700000000+(i+1)*14400, h-2, h, h-5, h-3, 1) for i,h in enumerate(highs)]
        geometry = IncrementalGeometry(rows, 'TEST', '4h', 'strict', list(range(len(rows))))
        reference = Geometry(rows, 'TEST', 'swing_envelope')
        for i in range(14, len(rows)):
            ours, old = geometry.proposals(i), reference.proposals(i)
            anchors = lambda cs: {(c['upper'], c['ray']['a_index'], c['ray']['b_index']) for c in cs}
            self.assertEqual(anchors(ours), anchors(old))

    def test_missing_source_bucket_cannot_support_a_strict_line(self):
        highs = [110,105,104,109,104,103,108,103,102,107,102,101,101,100,100]
        rows = [Bar(1700000000+i*14400, 1700000000+(i+1)*14400, h-2, h, h-5, h-3, 1) for i,h in enumerate(highs)]
        grid = [j if j < 8 else j+1 for j in range(len(rows))]
        cs = IncrementalGeometry(rows, 'TEST', '4h', 'strict', grid).proposals(14)
        self.assertFalse(any(c['ray']['a_index'] < 8 for c in cs))

    def test_event_calendar_requires_then_known_coverage_and_events(self):
        at_time = 1736355600
        self.assertIsNone(EventCalendar().check('TEST', at_time))
        coverage = {'symbol': 'TEST', 'knownAt': at_time-1, 'fromAt': at_time-1, 'throughAt': at_time+15*86400}
        c = EventCalendar({'coverage': [coverage], 'events': []})
        self.assertTrue(c.check('TEST', at_time))
        c.payload['events'] = [{'symbol': 'TEST', 'knownAt': at_time-1, 'at': at_time+86400, 'kind': 'earnings'}]
        self.assertFalse(c.check('TEST', at_time))
        c.payload['events'][0]['knownAt'] = at_time+1
        self.assertTrue(c.check('TEST', at_time))
        c.payload['coverage'][0]['knownAt'] = at_time+1
        self.assertIsNone(c.check('TEST', at_time))

    def test_profiles_are_nested_unknown_is_not_pass_and_sensitivities_are_separate(self):
        checks = {k: True for k in ('two','three','age7','momentum','safety','context','room','events','age14','green3','whole_body','exact3')}
        self.assertTrue(all(qualified(checks, p) for p in PROFILES))
        checks['events'] = None
        self.assertTrue(qualified(checks, 'context_room'))
        self.assertFalse(qualified(checks, 'all_events'))
        checks['three'] = False
        self.assertTrue(qualified(checks, 'two'))
        self.assertFalse(qualified(checks, 'three'))


class CompleteReplayTests(unittest.TestCase):
    def setUp(self):
        self.data, self.sources = fixture.dataset()

    def engine(self, data=None, cutoff=None):
        engine = CompleteReplay(data or self.data, cutoff=cutoff)
        engine.start_at = 0  # Explicit synthetic short-history mechanics test.
        return engine

    def run_engine(self, data=None, cutoff=None):
        engine = self.engine(data, cutoff)
        def proposals(i):
            return [candidate(engine.rows, False), candidate(engine.rows, True)] if i == 19 else []
        with patch.object(engine.geometry, 'proposals', side_effect=proposals):
            return engine, engine.run()

    def test_closed_signal_has_later_real_open_and_frozen_original_anchors(self):
        engine, result = self.run_engine()
        rows = [e for e in result['entries'] if e['profile'] == 'two' and e['family'] == 'breakout']
        self.assertTrue(rows)
        e = rows[0]
        self.assertGreaterEqual(e['entryAt'], e['signalAt']+300)
        self.assertEqual(e['entryPrice'], engine.fine_by_time[e['entryAt']].open)
        self.assertEqual(e['green']['a_price'], 95)
        self.assertFalse(e['fullyCompliant'])
        self.assertIsNone(e['checks']['events'])

    def test_future_shock_does_not_change_known_entries(self):
        cutoff = self.sources['4h'][23].end
        changed = deepcopy(self.data)
        for rows in changed['material']['bars'].values():
            for b in rows:
                if b['end'] > cutoff:
                    for k in ('open','high','low','close'): b[k] *= 3
        _, before = self.run_engine(cutoff=cutoff)
        _, after = self.run_engine(changed, cutoff)
        self.assertEqual(before['entries'], after['entries'])
        self.assertEqual(before['funnel'], after['funnel'])

    def test_later_retest_cannot_supply_a_missing_prebreak_third_contact(self):
        engine = self.engine()
        i = 23
        c, g = candidate(engine.rows, True), candidate(engine.rows, False)
        c['count'] = 6  # Even corrupt/later-increased live count is not used.
        c['breakInfo'] = {'contacts': 2, 'exactContacts': 2, 'ageDays': 20, 'momentum': True}
        detail = engine.details(c, g, 'retest', i)
        self.assertEqual(detail['info']['contacts'], 2)

    def test_daily_is_a_separate_source_engine_and_clips_future(self):
        cutoff = self.sources['1D'][30].end
        e = CompleteReplay(self.data, '1D', cutoff=cutoff)
        self.assertEqual(e.rows, [b for b in self.sources['1D'] if b.end <= cutoff])
        self.assertEqual(e.geometry.tf, '1D')


class CompleteExitTests(unittest.TestCase):
    def setUp(self):
        self.f = safety.SafetyStrategyTests(); self.f.setUp()
        self.data = {'id': 'fixture', 'material': {'symbol': 'TEST', 'bars': {tf: [asdict(b) for b in rows] for tf, rows in self.f.frames.items()}}}
        self.entry = {**self.f.entry, 'greenLevel': 99, 'initialStop': 96}

    def evaluator(self, data=None, tf='4h'):
        return Outcomes(data or self.data, tf, self.f.fine[-1].end)

    def test_no_forced_time_exit_and_unknown_is_distinct_from_open(self):
        p = self.evaluator().path(self.entry, 'fixed')
        self.assertEqual(p['status'], 'open')
        self.assertGreater(p['markAt']-self.entry['entryAt'], 20*86400)
        self.assertFalse(p['forcedTimeExit'])
        data = deepcopy(self.data)
        fine = data['material']['bars']['5m']
        fine.pop(next(i for i,b in enumerate(fine) if b['time'] == self.entry['entryAt'])+3)
        unknown = self.evaluator(data).path(self.entry, 'fixed')
        self.assertEqual(unknown['status'], 'unknown')
        self.assertEqual(unknown['reason'], 'missing_fine_path')
        self.assertIsNone(unknown['netR'])

    def test_gap_stop_uses_available_price_and_costs(self):
        data = deepcopy(self.data)
        fine = data['material']['bars']['5m']
        j = next(i for i,b in enumerate(fine) if b['time'] == self.entry['entryAt'])+1
        fine[j].update(open=90, low=89)
        p = self.evaluator(data).path(self.entry, 'fixed')
        self.assertEqual(p['status'], 'closed')
        self.assertEqual(p['reason'], 'stop_gap')
        self.assertEqual(p['rawExit'], 90)
        self.assertLess(p['netR'], -1)

    def test_independent_auditor_rejects_tampered_fill_and_return(self):
        from tools.verify_complete_study import check_path
        data = deepcopy(self.data)
        fine = data['material']['bars']['5m']
        j = next(i for i,b in enumerate(fine) if b['time'] == self.entry['entryAt'])+1
        fine[j].update(low=95)
        evaluator = self.evaluator(data)
        p = evaluator.path(self.entry, 'fixed')
        self.assertEqual(p['status'], 'closed')
        check_path(self.entry, p, evaluator.fine, evaluator.rows, evaluator.cutoff)
        tampered = {**p, 'netR': p['netR']+1}
        with self.assertRaises(AssertionError):
            check_path(self.entry, tampered, evaluator.fine, evaluator.rows, evaluator.cutoff)
        tampered = {**p, 'rawExit': 100}
        with self.assertRaises(AssertionError):
            check_path(self.entry, tampered, evaluator.fine, evaluator.rows, evaluator.cutoff)

    def test_higher_low_waits_for_two_right_candles_and_can_raise_without_connecting_ray(self):
        rows = [Bar(i*1000, (i+1)*1000, 102, 104, 101, 103, 1) for i in range(22)]
        rows[16] = replace(rows[16], low=100)
        self.assertIsNone(confirmed_higher_low(rows, 17, rows[10].time, 99))
        known = confirmed_higher_low(rows, 18, rows[10].time, 99)
        self.assertEqual(known['pivotAt'], rows[16].time)
        self.assertEqual(known['knownAt'], rows[18].end)
        self.assertGreater(known['stop'], 99)
        self.assertIsNone(confirmed_higher_low(rows, 18, rows[10].time, 100.1))

    def test_daily_friday_is_explicitly_unsupported_not_fictitious_execution(self):
        p = self.evaluator(tf='1D').path(self.entry, 'friday')
        self.assertEqual(p['status'], 'unsupported')

    def test_missing_daily_horizon_is_not_replaced_by_next_available_day(self):
        e = self.evaluator()
        before = e.intermediate(self.entry)
        wanted = before['5']['day']
        self.assertEqual(before['5']['status'], 'known')
        del e.daily_by_day[wanted]
        self.assertEqual(e.intermediate(self.entry)['5']['status'], 'unknown')


if __name__ == '__main__': unittest.main()
