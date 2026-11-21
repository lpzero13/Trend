from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from early_warning import Rules
from early_warning_study import describe, prepare, checked, briefing, review, load_block
from fan_geometry import stable_id
from strategy_screen import write, read
from models import DataError


def stamp(day, hour=20):
    return int(datetime(2024, 1, day, hour, tzinfo=timezone.utc).timestamp())


def record(name, family='breakout', at=None, outcome=None, entry=None):
    at = at or stamp(2)
    return {'id': name, 'episodeId': name, 'symbol': 'TEST', 'datasetId': 'd'*64,
        'family': family, 'policy': 'distance:1', 'createdAt': at,
        'warnings': [{'id': name+'2', 'stage': 2, 'at': at,
            'features': {'cohort': 'two', 'activeApproach': True, 'sourceIndex': 10},
            'snapshot': {'line': {'id': 'line'}, 'green': None}},
            {'id': name+'3', 'stage': 3, 'at': at, 'features': {}}],
        'outcome': outcome or {'at': stamp(5), 'reason': 'window_end', 'censored': True}, 'entry': entry}


class WarningStudyTests(unittest.TestCase):
    def plan(self):
        return {'windows': [{'name': 'test', 'start': '2024-01-02', 'end': '2024-01-05'}],
                'rules': asdict(Rules()), 'limitations': [], 'id': 'p'}

    def test_denominators_censoring_lead_and_simultaneous_stages_are_separate(self):
        entry = {'at': stamp(3), 'sourceIndex': 12, 'validRisk': True, 'activeAtSignal': True, 'cohort': 'qualified', 'lineId': 'line'}
        success = record('success', outcome={'at': stamp(3), 'reason': 'entry_signal', 'censored': False}, entry=entry)
        fail = record('fail', outcome={'at': stamp(4), 'reason': 'moved_away', 'censored': False})
        unknown = record('unknown', outcome={'at': stamp(8), 'reason': 'entry_signal', 'censored': False}, entry={**entry, 'at': stamp(8)})
        late = record('late', at=stamp(1), outcome={'at': stamp(3), 'reason': 'entry_signal', 'censored': False}, entry=entry)
        block = {'eligibility': {'test': True}, 'records': [success, fail, unknown, late]}
        result = describe(self.plan(), [block])
        g = next(g for g in result['groups'] if g['policy'] == 'distance:1' and g['family'] == 'breakout')
        self.assertEqual((g['entries'], g['coveredEntries'], g['entriesWithEarlierOutOfWindowWarning']), (2, 1, 1))
        self.assertEqual((g['warnings'], g['confirmed'], g['fizzled'], g['censored']), (3, 1, 1, 1))
        self.assertEqual(g['medianLeadBars'], 2); self.assertEqual(g['medianLeadSessions'], 1)
        self.assertEqual(g['messagesPerSession'], .75)
        self.assertEqual(g['recallPct'], 50)
        self.assertEqual(g['entryCoverageByCohort']['qualified']['warningWasTwo'], 1)

    def test_invalid_risk_and_signals_after_a_closed_watch_are_not_success(self):
        e = {'at': stamp(3), 'sourceIndex': 12, 'validRisk': False, 'activeAtSignal': True, 'cohort': 'two', 'lineId': 'line'}
        a = record('invalid', entry=e, outcome={'at': stamp(3), 'reason': 'entry_signal', 'censored': False})
        b = record('closed', entry={**e, 'validRisk': True, 'activeAtSignal': False}, outcome={'at': stamp(2), 'reason': 'moved_away', 'censored': False})
        g = next(g for g in describe(self.plan(), [{'eligibility': {'test': True}, 'records': [a, b]}])['groups']
                 if g['policy'] == 'distance:1' and g['family'] == 'breakout')
        self.assertEqual(g['entries'], 1); self.assertEqual(g['invalidRiskSignals'], 1)
        self.assertEqual(g['confirmed'], 0); self.assertEqual(g['afterClosedWatchEntries'], 1)

    def test_plan_binding_resume_checksums_and_manual_preferences_do_not_change_research(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'TORI_DATA_DIR': folder+'/data'}):
            root, source = Path(folder)/'study', Path(folder)/'source.json'
            origin = {'symbols': ['TEST'], 'datasets': {'TEST': 'd'*64}, 'windows': self.plan()['windows'], 'warmupDays': 400}
            origin['id'] = stable_id(origin); write(source, origin)
            plan = prepare(root, source)
            self.assertEqual(prepare(root, source)['id'], plan['id'])
            r = record('episode')
            block = {'planId': plan['id'], 'symbol': 'TEST', 'datasetId': 'd'*64, 'records': [r],
                     'episodes': [{'id': 'episode'}], 'eligibility': {'test': True}}
            block['checksum'] = stable_id(block); write(root/'stocks/TEST.json.gz', block)
            at = stamp(3)
            with patch('early_warning_study.time.time', return_value=stamp(2)):
                self.assertTrue(briefing(root, plan, 'TEST', 'distance:1', at=at))
                review(root, 'episode', 'breakout', 'mute')
                self.assertEqual(briefing(root, plan, 'TEST', 'distance:1', at=at), [])
                review(root, 'episode', 'breakout', 'unmute')
                view = briefing(root, plan, 'TEST', 'distance:1', at=at)[0]
                self.assertNotIn('entry', view); self.assertNotIn('outcome', view)
                review(root, 'episode', 'all', 'snooze', stamp(4))
                self.assertFalse(briefing(root, plan, 'TEST', 'distance:1', at=at))
                self.assertTrue(briefing(root, plan, 'TEST', 'distance:1', at=stamp(4)))
            self.assertEqual(load_block(root, plan, 'TEST')['checksum'], block['checksum'])
            excluded = {**block, 'eligibility': {'test': False}}
            excluded['checksum'] = stable_id({k: v for k, v in excluded.items() if k != 'checksum'})
            write(root/'stocks/TEST.json.gz', excluded)
            with patch('early_warning_study.time.time', return_value=stamp(2)):
                review(root, 'episode', 'all', 'unmute')
                self.assertFalse(briefing(root, plan, 'TEST', 'distance:1', at=stamp(3)))
            write(root/'stocks/TEST.json.gz', block)
            with patch('early_warning_study.binding', return_value={}):
                with self.assertRaises(DataError): checked(plan)
            with patch.dict(os.environ, {'TORI_DATA_DIR': folder+'/another'}):
                with self.assertRaises(DataError): checked(plan)
            write(root/'stocks/TEST.json.gz', {**block, 'symbol': 'changed'})
            with self.assertRaises(DataError): load_block(root, plan, 'TEST')


if __name__ == '__main__': unittest.main()
