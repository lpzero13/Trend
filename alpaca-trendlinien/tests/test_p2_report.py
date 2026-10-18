import unittest
from research import summarize


class ReportTests(unittest.TestCase):
    def trial(self,event,start,end,*,complete=True,dataset="same"):
        return {"status":"observed","datasetId":dataset,"variants":[{"group":"breakout_provisional","status":"observed","eventId":event,
            "entryAt":start,"outcomes":{"5":{"complete":complete,"closedAt":end,"net_return_pct":2,
            "mfe_pct":3,"mae_pct":-1,"intrabar_ambiguous":False}}}]}

    def test_origins_entries_incomplete_and_overlapping_windows_are_distinct(self):
        a=self.trial("a",100,110)
        trials=[a,a,self.trial("b",105,115),self.trial("c",200,None,complete=False)]
        group=summarize(trials,[5])["groups"]["breakout_provisional"]
        self.assertEqual(group["observed"],4)
        self.assertEqual(group["uniqueEntries"],3)
        self.assertEqual(group["horizons"]["5"]["n"],2)
        self.assertEqual(group["horizons"]["5"]["n_incomplete"],1)
        self.assertEqual(group["horizons"]["5"]["overlapping_entries"],1)
        self.assertEqual(group["horizons"]["5"]["unknown_windows"],1)

    def test_overlap_counter_does_not_treat_different_datasets_as_same_instrument(self):
        values=[self.trial("a",100,110),self.trial("b",105,115,dataset="other")]
        result=summarize(values,[5])["groups"]["breakout_provisional"]["horizons"]["5"]
        self.assertEqual(result["overlapping_entries"],0)

    def test_unobserved_retest_reason_is_retained(self):
        trial={"status":"no_entry","variants":[{"group":"retest_provisional","status":"no_entry","reason":"retest_censored"}]}
        result=summarize([trial],[5])["groups"]["retest_provisional"]
        self.assertEqual(result["withoutEntry"],1)
        self.assertEqual(result["reasons"],{"retest_censored":1})


if __name__=="__main__": unittest.main()
