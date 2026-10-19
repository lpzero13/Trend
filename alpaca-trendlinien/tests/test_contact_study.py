from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from tools.contact_study import statistics_for, run


class ContactStudyTests(unittest.TestCase):
    def test_missing_horizons_are_not_losses_and_controls_use_their_own_denominator(self):
        points=[{"forward":{"5":{"complete":True,"return_pct":2}},"controls":[{"forward":{"5":{"complete":True,"return_pct":1}}}]},
                {"forward":{"5":{"complete":True,"return_pct":-1}},"controls":[]},
                {"forward":{"5":{"complete":False,"reason":"missing_daily_sessions"}}}]
        h=statistics_for(points)["5"]
        self.assertEqual((h["n"],h["incomplete"],h["positive"],h["negative"]),(2,1,1,1))
        self.assertEqual(h["positive_pct"],50)
        self.assertEqual(h["mean_pct"],.5)
        self.assertEqual((h["matched_n"],h["mean_excess_pct"]),(1,1))
        self.assertIsNone(statistics_for(points)["10"]["mean_pct"])

    def test_zero_returns_are_flat_not_success_and_empty_groups_remain_null(self):
        h=statistics_for([{"forward":{"20":{"complete":True,"return_pct":0}}}])["20"]
        self.assertEqual((h["positive"],h["negative"],h["flat"]),(0,0,1))
        self.assertEqual(h["mean_pct"],0)
        self.assertIsNone(statistics_for([])["20"]["positive_pct"])

    def test_existing_round_contract_cannot_be_silently_overwritten_or_restarted(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict("os.environ"):
            path=Path(folder)/"round-1.contract.json";path.write_text('{"immutable":true}')
            with patch("jobs.submit") as submit,self.assertRaises(ValueError):
                run(SimpleNamespace(root=folder,round=1,validation=False))
            submit.assert_not_called()
            self.assertEqual(path.read_text(),'{"immutable":true}')


if __name__=="__main__":unittest.main()
