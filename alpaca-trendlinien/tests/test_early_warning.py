from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
import unittest

from early_warning import Radar, Rules, allows
from fan_geometry import FanRules
from fan_observer import WatchRules
from models import Bar
from pilot_backtest import PilotObserver
from test_fan_geometry import triangle
from test_fan_observer import append


def scanner():
    return Radar('TEST', observer=PilotObserver('TEST',
        FanRules(atr_length=2, contact_atr=.001, wick_atr=0, min_age_days=0),
        WatchRules(clean_atr=.01, retest_atr=.01, arm_bars=1, retest_bars=5)))


class EarlyWarningTests(unittest.TestCase):
    def test_warnings_precede_real_signals_and_retest_keeps_the_parent_episode(self):
        rows = append(append(triangle(), 111, 116, 100, 115), 111, 114, 110.7, 113)
        radar = scanner()
        for bar in rows: radar.push(bar)
        records = radar.result()['records']
        entries = [r for r in records if r['entry'] and r['policy'] == 'distance:1']
        self.assertEqual({r['family'] for r in entries}, {'breakout', 'red_retest'})
        a, b = next(r for r in entries if r['family'] == 'breakout'), next(r for r in entries if r['family'] == 'red_retest')
        self.assertEqual(a['episodeId'], b['episodeId'])
        self.assertTrue(a['warnings'])
        self.assertTrue(all(w['at'] < a['entry']['at'] for w in a['warnings']))
        self.assertEqual(b['warnings'], [], 'an immediate next-bar retest has no advance warning')
        for r in records:
            self.assertEqual(len({w['stage'] for w in r['warnings']}), len(r['warnings']))
            for w in r['warnings']:
                self.assertTrue(all(p['known_at'] <= w['at'] for p in w['snapshot']['line']['contactPoints']))
                if r['family'] == 'safety_bounce': self.assertIsNone(w['features']['projection']['cleanThresholdAtCurrentATR'])

    def test_future_price_shocks_do_not_change_historical_warnings_or_snapshots(self):
        prefix = triangle()
        tail = append(append(prefix, 111, 116, 100, 115), 111, 114, 110.7, 113)
        changed = [*prefix, *[replace(b, open=400, high=600, low=1, close=500) for b in tail[len(prefix):]]]
        outputs = []
        for rows in (tail, changed):
            r = scanner()
            for b in rows: r.push(b)
            outputs.append(sorted([(v['id'], [w for w in v['warnings'] if w['at'] <= prefix[-1].end])
                                   for v in r.result()['records'] if any(w['at'] <= prefix[-1].end for w in v['warnings'])]))
        self.assertTrue(outputs[0]); self.assertEqual(*outputs)

    def test_gaps_censor_existing_watches_and_never_reuse_the_old_episode(self):
        radar = scanner()
        rows = triangle()
        for b in rows: radar.push(b)
        prior = {r['episodeId'] for r in radar.result()['records'] if r['warnings']}
        self.assertTrue(prior)
        radar.push(append(rows, 100, 110, 90, 100)[-1], gap=True)
        for r in radar.result()['records']:
            if r['warnings'] and r['outcome']['reason'] == 'source_gap': self.assertTrue(r['outcome']['censored'])
        self.assertEqual(radar.generation, 1)
        self.assertFalse(radar.current)

    def test_line_refits_share_identity_but_two_fresh_confirmed_contacts_can_rearm(self):
        radar = scanner()
        line = {'id': 'one', 'a_time': 1, 'a_price': 120, 'b_time': 2, 'b_price': 110, 'contactPoints': []}
        radar.lineage.lines.update(one='origin', two='origin', three='origin')
        first = radar.group(line, 10, 'breakout', 's1')
        self.assertEqual(radar.group({**line, 'id': 'two'}, 12, 'breakout', 's2')['id'], first['id'])
        first['terminalAt'] = 15
        updated = {**line, 'id': 'three', 'contactPoints': [{'time': 11, 'known_at': 13}, {'time': 14, 'known_at': 16}]}
        new = radar.group(updated, 17, 'breakout', 's3')
        self.assertNotEqual(new['id'], first['id'])
        self.assertEqual(radar.group(line, 18, 'red_retest', 's1')['id'], first['id'])

    def test_ablation_variants_do_not_treat_unknown_approach_as_active(self):
        f = {'activeApproach': None, 'compressed': True}
        self.assertTrue(allows(f, 'distance')); self.assertTrue(allows(f, 'compression'))
        self.assertFalse(allows(f, 'active')); self.assertFalse(allows(f, 'combined'))
        f['activeApproach'] = True
        self.assertTrue(allows(f, 'combined'))

    def test_no_time_reversal_and_no_duplicate_policy_definitions(self):
        r = scanner(); bar = triangle()[0]; r.push(bar)
        with self.assertRaises(ValueError): r.push(bar)
        for config in ({'thresholds': (float('nan'),)}, {'thresholds': (1., 1.)},
                       {'variants': ('distance', 'distance')}, {'approach_bars': 0}):
            with self.assertRaises(ValueError): Rules(**config)


if __name__ == '__main__': unittest.main()
