from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from models import Bar,DataError
from targeted_data_audit import compare_day
from trigger_horizon_research import policies,paired,prepare
from strategy_screen import write,read


class DayAuditTests(unittest.TestCase):
    def test_same_provider_recheck_distinguishes_missing_recovered_and_conflicting(self):
        rows=[Bar(t,t+300,100,101,99,100,10) for t in (0,300,600)]
        summary,added=compare_day(rows[:1],rows,0,900)
        self.assertEqual(summary['recovered'],2);self.assertEqual(summary['stillAbsent'],0);self.assertEqual(added,rows[1:])
        summary,added=compare_day(rows,rows[:1],0,900)
        self.assertEqual(summary['recovered'],0);self.assertEqual(summary['missingBefore'],0)
        summary,_=compare_day(rows,[replace(rows[0],close=100.5),*rows[1:]],0,900)
        self.assertEqual(summary['conflictingOverlaps'],1)

    def test_persistent_provider_absence_is_not_filled(self):
        summary,added=compare_day([],[],0,900)
        self.assertEqual(summary['stillAbsent'],3);self.assertEqual(added,[])

    def test_conflicting_overlap_blocks_publication_and_preserves_original_ids(self):
        import hashlib
        import targeted_data_audit as module
        from fan_geometry import stable_id
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);contract={'id':'audit','code':hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
                'targets':[{'symbol':'A'}],'datasets':{'A':'original'}}
            write(root/'contract.json',contract)
            record={'contractId':'audit','symbol':'A','comparison':{'conflictingOverlaps':1},'addedBars':[{}]}
            record['checksum']=stable_id(record);write(root/'days'/'A.json.gz',record)
            with patch('targeted_data_audit.save_dataset',side_effect=AssertionError('must not publish')):
                result=module.publish(root)
            self.assertEqual(result['datasets'],{'A':'original'});self.assertFalse(result['changes'][0]['published'])

    def test_unchanged_provider_answers_do_not_create_new_datasets(self):
        import hashlib
        import targeted_data_audit as module
        from fan_geometry import stable_id
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);write(root/'contract.json',{'id':'audit','code':hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
                'targets':[{}],'datasets':{'A':'original'}})
            record={'contractId':'audit','symbol':'A','comparison':{'conflictingOverlaps':0},'addedBars':[]}
            record['checksum']=stable_id(record);write(root/'days'/'A.json.gz',record)
            with patch('targeted_data_audit.save_dataset',side_effect=AssertionError('must not publish')):
                result=module.publish(root)
            self.assertEqual(result['datasets'],{'A':'original'});self.assertEqual(result['changes'],[])


class ExitContractTests(unittest.TestCase):
    def test_exact_matrix_isolated_modes_and_horizons(self):
        for family in ('breakout','red_retest'):
            ps=policies(family);self.assertEqual(len(ps),12);self.assertEqual(len({p['id'] for p in ps}),12)
            self.assertEqual({p['horizon'] for p in ps},{40,80});self.assertTrue(all(p['quality']=='qualified' and not p['sma200'] for p in ps))

    def test_pairwise_stats_keep_common_membership_and_unknown_count(self):
        cases=[{'id':'one','entry':{'status':'filled'},'paths':{'a':{'status':'closed','netR':1.},'b':{'status':'closed','netR':2.}}},
               {'id':'two','entry':{'status':'filled'},'paths':{'a':{'status':'closed','netR':-1.},'b':{'status':'censored'}}}]
        r=paired(cases,'a','b');self.assertEqual(r['commonComplete'],1);self.assertEqual(r['notCommonComplete'],1)
        self.assertEqual(r['meanDeltaR'],1.)

    def test_repaired_data_cannot_be_mixed_with_old_frozen_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'source';audit=Path(directory)/'audit'
            write(source/'plan.json',{'id':'source'})
            write(audit/'contract.json',{'id':'a','sourcePlanId':'source'})
            write(audit/'audit-summary.json',{'contractId':'a','recoveredBars':1,'conflictingPairs':0})
            with patch('trigger_horizon_research.validate_plan',side_effect=lambda p:p):
                with self.assertRaises(DataError):prepare(Path(directory)/'new',source,audit)


if __name__=='__main__':unittest.main()
