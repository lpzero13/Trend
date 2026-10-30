import unittest
from archive_estimates import estimate,CALIBRATION
from models import DataError


class EstimateTests(unittest.TestCase):
    def test_measured_long_history_model_and_separate_storage_categories(self):
        value=estimate(100,CALIBRATION['start'],CALIBRATION['end'])
        self.assertAlmostEqual(value['seconds'],5554.1,places=1)
        self.assertEqual(value['estimatedPages'],14000)
        self.assertEqual(value['combinedBytes'],value['datasetBytes']+value['checkpointBytes'])
        self.assertEqual(value['datasetBytes'],489743650)
        self.assertEqual(value['checkpointBytes'],388199375)
        self.assertLess(value['lowSeconds'],value['seconds']);self.assertGreater(value['highSeconds'],value['seconds'])
        self.assertIn('not a confidence interval',value['uncertainty'])

    def test_period_scales_counts_and_zero_selection_costs_nothing(self):
        full=estimate(1,CALIBRATION['start'],CALIBRATION['end'])
        short=estimate(1,'2025-01-01T00:00:00Z','2026-01-01T00:00:00Z')
        self.assertLess(short['seconds'],full['seconds'])
        empty=estimate(0,CALIBRATION['start'],CALIBRATION['end'])
        self.assertEqual((empty['seconds'],empty['combinedBytes'],empty['estimatedPages']),(0,0,0))
        slower=estimate(1,CALIBRATION['start'],CALIBRATION['end'],95)
        self.assertAlmostEqual(slower['seconds'],full['seconds']*2,delta=.11)

    def test_invalid_period_and_stock_count_fail(self):
        for n in (-1,True,'100',20001):
            with self.assertRaises(DataError):estimate(n)
        for start,end in (('bad',CALIBRATION['end']),('2026-01-01T00:00:00Z','2025-01-01T00:00:00Z'),
                          ('2015-01-01T00:00:00Z',CALIBRATION['end'])):
            with self.assertRaises(DataError):estimate(1,start,end)
