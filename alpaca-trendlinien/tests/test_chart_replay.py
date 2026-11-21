from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
import os
import tempfile
import unittest
from unittest.mock import patch

import chart_replay as replay
from analysis_service import build_chart
from fan_chart import apply
from fan_geometry import analyze, profile
from models import DataError
from replay_fan import Feeder
from weekly_chart import add_weekly
from test_research import fixture_sources


def canonical(inputs, cutoff, tf, engine):
    now = datetime.now(timezone.utc)
    p = build_chart(inputs, 'TEST', '1D' if tf == '1W' else tf,
                    datetime.fromtimestamp(cutoff, timezone.utc), now,
                    historical=True, include_analysis=engine == 'legacy')
    add_weekly(p, tf)
    if engine != 'legacy':
        apply(p, engine)
    return p


class ChartReplayTests(unittest.TestCase):
    def setUp(self):
        replay.clear()
        self.inputs = fixture_sources()

    def tearDown(self):
        replay.clear()

    def test_full_views_match_canonical_for_every_model_during_jumps_and_rewinds(self):
        s = replay.register(self.inputs, {'symbol': 'TEST'})
        for model in ('legacy', 'fan_extreme', 'fan_local', 'fan_master'):
            for i in (1000, 1001, 999, 1002):
                at = self.inputs['4h'][0][i].end
                actual = s.view(at, '4h', model, True, full=True)
                expected = canonical(self.inputs, at, '4h', model)
                for key in expected:
                    if key != 'generatedAt':
                        self.assertEqual(actual[key], expected[key], (model, i, key))

    def test_checkpoint_engine_matches_fresh_calculation_across_gaps_and_random_access(self):
        rows = self.inputs['4h'][0]
        for model in ('extreme', 'local', 'master'):
            feeder = Feeder('TEST')
            rules = profile(model)
            for count in (250, 251, 270, 252, 255, 130, 280):
                prefix = rows[:count]
                gaps = {140: rows[139].end, 258: rows[257].end}
                gaps = {i: v for i, v in gaps.items() if i < count}
                try:
                    expected = analyze(prefix, '4h', symbol='TEST', rules=rules, gaps=gaps)
                except DataError as error:
                    with self.assertRaises(DataError) as actual:
                        feeder.analyze(prefix, '4h', rules, gaps, .15)
                    self.assertEqual(actual.exception.status, error.status)
                else:
                    self.assertEqual(feeder.analyze(prefix, '4h', rules, gaps, .15), expected, (model, count))
            self.assertLessEqual(len(feeder.checkpoints), 12)

    def test_future_shocks_cannot_affect_known_views_or_sma_and_compact_has_no_quotes(self):
        at = self.inputs['4h'][0][1000].end
        altered = {tf: ([replace(b, open=b.open*9, high=b.high*9, low=b.low*9, close=b.close*9)
                         if b.end > at else b for b in rows], meta) for tf, (rows, meta) in self.inputs.items()}
        for model in ('legacy', 'fan_master'):
            a = replay.register(self.inputs, {'symbol': 'TEST'})
            b = replay.register(altered, {'symbol': 'TEST'})
            one, two = a.view(at, '4h', model), b.view(at, '4h', model)
            for p in (one, two):
                p.pop('generatedAt'); p.pop('replaySession')
                self.assertNotIn('bars', p)
                self.assertTrue(all('bars' not in c for c in p['charts'].values()))
                self.assertTrue(all('sourceTimes' not in c for c in p['lanes'].values()))
            self.assertEqual(one, two)
            if model == 'fan_master':
                window_a, window_b = a.window(), b.window()
                for tf, lane in one['lanes'].items():
                    for n, count in lane['context']['seriesCounts'].items():
                        self.assertEqual(window_a['smas'][tf][n][:count], window_b['smas'][tf][n][:count])

    def test_state_cache_is_copied_bounded_and_rechecks_source_guard(self):
        guard = patch.object(replay, 'MAX_STATES', 2)
        with guard, patch.object(replay, 'MAX_STATE_BYTES', 2000000):
            s = replay.register(self.inputs, {'symbol': 'TEST'})
            at = self.inputs['4h'][0][1000].end
            for offset in (0, 1, 2):
                s.view(at+offset, '4h', analysis=False)
            self.assertLessEqual(len(s.states), 2)
            self.assertLessEqual(s.state_bytes, 2000000)
            p = s.view(at+2, '4h', analysis=False)
            p['latest']['close'] = -1
            self.assertGreater(s.view(at+2, '4h', analysis=False)['latest']['close'], 0)
            def fail(): raise DataError('changed', 409)
            s.guard = fail
            with self.assertRaises(DataError): s.view(at+2, '4h', analysis=False)

    def test_expiry_bounds_and_snapshot_save_use_the_requested_visible_cutoff(self):
        s = replay.register(self.inputs, {'symbol': 'TEST'})
        at = self.inputs['4h'][0][1000].end
        s.view(at+86400, '4h', 'fan_master')
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'TORI_DATA_DIR': folder}):
            frozen = replay.freeze({'session': s.id, 'asof': datetime.fromtimestamp(at, timezone.utc).isoformat(),
                                    'timeframe': '4h', 'engine': 'fan_master'})
            self.assertEqual(frozen['analysisCutoff'], at)
            self.assertTrue(all(b['end'] <= at for c in frozen['payload']['charts'].values() for b in c['bars']))
            self.assertEqual(frozen['payload']['lanes'], s.view(at, '4h', 'fan_master', full=True)['lanes'])
        with self.assertRaises(DataError): s.view(s.through+1, '4h')
        replay.clear()
        with self.assertRaises(DataError) as error: replay.session(s.id)
        self.assertEqual(error.exception.status, 410)

    def test_native_window_loads_only_selected_stock_once_and_manual_mode_skips_geometry(self):
        from unittest.mock import Mock
        loader = Mock(side_effect=lambda symbol, tf, **kw: self.inputs[tf])
        at = self.inputs['4h'][0][1000].end
        query = {'symbol': ['TEST'], 'timeframe': ['4h'], 'analysis': ['0'],
                 'asof': [datetime.fromtimestamp(at, timezone.utc).isoformat()]}
        with patch('alpaca.load_bars', loader), patch('replay_fan.Feeder.analyze', side_effect=AssertionError('manual')):
            opened = replay.open_window(query)
        self.assertEqual(loader.call_count, 3)
        self.assertTrue(all(call.args[0] == 'TEST' and call.kwargs['history_days'] == 1098 for call in loader.call_args_list))
        self.assertFalse(opened['view']['analysisEnabled'])
        self.assertEqual(opened['view']['lanes'], {})
        with patch('alpaca.load_bars', side_effect=AssertionError('no further downloads')):
            for i in (1001, 1002, 998):
                replay.get({'session': [opened['window']['id']], 'timeframe': ['4h'], 'analysis': ['1'],
                            'engine': ['fan_master'], 'asof': [datetime.fromtimestamp(self.inputs['4h'][0][i].end, timezone.utc).isoformat()]})

    def test_invalid_window_parameters_fail_before_loading_and_pool_is_bounded(self):
        with patch('alpaca.load_bars', side_effect=AssertionError('invalid request')):
            with self.assertRaises(DataError): replay.open_window({'timeframe': ['bogus']})
            with self.assertRaises(DataError): replay.open_window({'analysis': ['2']})
        ids = [replay.register(self.inputs, {'symbol': 'TEST'}).id for _ in range(3)]
        self.assertEqual(len(replay._sessions), 2)
        with self.assertRaises(DataError): replay.session(ids[0])


if __name__ == '__main__':
    unittest.main()
