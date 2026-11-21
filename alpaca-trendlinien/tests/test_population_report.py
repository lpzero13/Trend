import unittest
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory
import csv
from tools.report_population_backtest import Bucket,report
from strategy_screen import write,read


class PopulationReportingTests(unittest.TestCase):
    def test_closed_winners_open_marks_and_missing_paths_are_separate(self):
        b=Bucket()
        def add(status,pct=None,mark=None,entry='filled'):
            b.add({'symbol':'TEST','entry':{'status':entry}},
                  {'status':status,'netReturnPct':pct,'netR':pct,'markNetReturnPct':mark})
        add('closed',10);add('closed',-4);add('closed',0)
        add('open',mark=100);add('censored',pct=999,mark=999)
        add('invalid_stop',entry='invalid_stop')
        s=b.summary()
        self.assertEqual(s['signals'],6);self.assertEqual(s['filled'],5)
        self.assertEqual((s['wins'],s['losses'],s['flat']),(1,1,1))
        self.assertEqual((s['closed'],s['open'],s['censored'],s['noFill']),(3,1,1,1))
        self.assertAlmostEqual(s['winPctClosed'],100/3)
        self.assertEqual(s['meanClosedPct'],2)
        self.assertEqual(s['meanWinnerPct'],10);self.assertEqual(s['meanLoserPct'],-4)
        self.assertEqual(s['meanValuedPct'],26.5)
        self.assertEqual(s['medianValuedPct'],5)
        self.assertEqual(s['meanValuedWithoutBest3'],-4)

    def test_no_outcomes_are_unknown_not_zero_return_or_zero_win_rate(self):
        b=Bucket();s=b.summary()
        self.assertIsNone(s['meanClosedPct']);self.assertIsNone(s['meanValuedPct'])
        self.assertIsNone(s['winPctClosed']);self.assertEqual(s['signals'],0)

    def test_report_exports_overlap_once_and_keeps_excluded_roster_members(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)/'follow';source=Path(folder)/'source'
            p={'id':'follow','sourceRoot':str(source),'sourcePlanId':'base','symbols':['A'],
               'cutoff':300,'windows':[{'name':'test'}]}
            sp={'id':'base','windows':p['windows']}
            write(root/'plan.json',p);write(source/'plan.json',sp)
            write(root/'verification.json',{'passed':True,'planId':'follow'})
            write(source/'verification.json',{'passed':True,'planId':'base'})
            write(source/'population.json',{'planId':'base','universes':{
                'dow30':{'name':'Dow','members':[{'symbol':'A'}]},
                'nasdaq100':{'name':'Nasdaq','members':[{'symbol':'A'},{'symbol':'B'}]},
                'sp500':{'name':'SP','members':[{'symbol':'A'}]}},
                'excluded':[{'symbol':'B','reason':'insufficient history'}]})
            path={'status':'closed','netReturnPct':5.,'netR':.5,'exitAt':200}
            case={'id':'one','symbol':'A','window':'test','signal':{'episodeId':'episode',
                'family':'breakout','cohort':'qualified','signalAt':90},
                'entry':{'status':'filled','entryAt':100,'entryPrice':100,'initialStop':90},
                'features':{},'paths':{m:{**path} for m in ('fixed','original_safety','fan_safety')}}
            block={'checksum':'sum','cases':[case],'eligibility':{'test':True},'suppressed':[]}
            follow={'sourceChecksum':'sum','caseIds':['one'],'newPaths':{'one':{m:{**path} for m in ('qualified_fan','r2_fan')}}}
            write(root/'results.json',{'planId':'follow','cases':1,'groups':{'breakout:qualified':{
                m:{'signals':1,'wins':1,'losses':0,'meanNetReturnPct':5.,'meanTerminalPct':5.}
                for m in ('fixed','original_safety','fan_safety','qualified_fan','r2_fan')}}})
            with patch('tools.report_population_backtest.checked',lambda x:x),\
                 patch('tools.report_population_backtest.source_plan',lambda x:x),\
                 patch('tools.report_population_backtest.load_block',return_value=block),\
                 patch('tools.report_population_backtest.load_followup',return_value=follow):
                result=report(root,Path(folder)/'report.md')
            self.assertEqual(result['cases'],1);self.assertEqual(result['csvRows'],5)
            self.assertTrue(result['csvAuditPassed'])
            with (root/'coverage.csv').open(encoding='utf-8-sig',newline='') as f:coverage=list(csv.DictReader(f))
            self.assertEqual(len(coverage),2);self.assertEqual(coverage[1]['reason'],'insufficient history')
            data=read(root/'population-report.json')
            self.assertEqual(len(data['groups']),20) # ALL plus three overlapping universes, five models each.


if __name__=='__main__':unittest.main()
