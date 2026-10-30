from copy import deepcopy
from dataclasses import replace,asdict
import unittest
from unittest.mock import patch

from candidate_research import ResearchData,features,summarize,uncertainty
from complete_outcomes import Outcomes
from datasets import digest
from lab_data import resample_regular,NORMALIZATION
import test_safety_strategy as fixture


class ResearchTests(unittest.TestCase):
    def setUp(self):
        f=fixture.SafetyStrategyTests();f.setUp();self.fine=f.fine
        self.frames=f.frames;self.cutoff=self.fine[-1].end
        self.data=self.dataset(self.fine);self.ev=ResearchData(self.data,self.cutoff)
        # Explicit synthetic entry with three contacts; not market evidence.
        i=50;b=self.frames['4h'][i]
        at=b.end+300
        row=next(x for x in self.fine if x.time==at)
        green={'a_index':0,'b_index':10,'a_time':self.frames['4h'][0].time,'b_time':self.frames['4h'][10].time,
            'a_price':90.,'b_price':91.,'slope':.1,'basis':'bars','valid':True}
        self.entry={'id':'synthetic-entry','symbol':'TEST','entryAt':at,'entryPrice':row.open,
            'initialStop':90.,'greenLevel':92.,'green':green,'signalAt':b.end,'signalIndex':i,
            'signalATR':2.,'info':{'contacts':3,'ageDays':20},'greenInfo':{'contacts':2},
            'signalChecks':{'momentum':True,'context':None,'room':False}}

    def dataset(self,fine):
        frames,_=resample_regular(fine)
        material={'symbol':'TEST','provider':'synthetic','dataKind':'synthetic','feed':'sip','adjustment':'split',
            'normalization':{tf:NORMALIZATION for tf in frames},'bars':{tf:[asdict(b) for b in rows] for tf,rows in frames.items()}}
        return {'id':digest(material),'material':material}

    def test_control_selection_has_no_outcome_dependency_and_is_repeatable(self):
        with patch.object(self.ev,'outcome',side_effect=AssertionError('selection cannot evaluate future')):
            a=self.ev.controls(self.entry,self.fine[0].time,self.cutoff)
            b=self.ev.controls(self.entry,self.fine[0].time,self.cutoff)
        self.assertEqual(a,b);self.assertTrue(a['items'])
        wanted=self.ev.covariate(self.entry['entryAt'],self.entry['entryPrice'])
        for c in a['items']:
            got=self.ev.covariate(c['entryAt'],c['entryPrice'])
            self.assertGreaterEqual(abs(got['dayIndex']-wanted['dayIndex']),20)
            self.assertAlmostEqual((c['entryPrice']-c['initialStop'])/c['entryPrice'],.1)
            self.assertEqual(c['kind'],'matched_control');self.assertNotIn('outcomes',c)

    def test_future_wick_shocks_cannot_change_chosen_controls(self):
        a=self.ev.controls(self.entry,self.fine[0].time,self.cutoff)
        chosen={c['entryAt'] for c in a['items']}
        # A shock strictly after every matching timestamp cannot influence matching.
        last=max(chosen|{self.entry['entryAt']});shocked=[replace(b,high=b.high*3,low=b.low/3) if b.time>last else b for b in self.fine]
        other=ResearchData(self.dataset(shocked),self.cutoff)
        self.assertEqual(a,other.controls(self.entry,self.fine[0].time,self.cutoff))

    def test_capped_paths_equal_independent_shared_evaluator_at_same_cutoff(self):
        end=self.ev.horizon_end(self.entry['entryAt'],5)
        for model in ('fixed','higher_low'):
            reference=Outcomes(self.data,'4h',end).path(self.entry,model)
            got=self.ev.path(self.entry,model,end)
            self.assertEqual(reference,got)

    def test_future_after_horizon_does_not_change_any_metric(self):
        end=self.ev.horizon_end(self.entry['entryAt'],5);base=self.ev.outcome(self.entry,5)
        changed=[replace(b,high=b.high*2,low=1.) if b.time>=end else b for b in self.fine]
        other=ResearchData(self.dataset(changed),self.cutoff)
        self.assertEqual(base,other.outcome(self.entry,5))

    def test_gap_after_closed_stop_keeps_trade_known_but_market_unknown(self):
        start=self.entry['entryAt'];fine=list(self.fine)
        j=next(i for i,b in enumerate(fine) if b.time==start)
        fine[j]=replace(fine[j],low=89.)
        del fine[j+12]
        ev=ResearchData(self.dataset(fine),self.cutoff);o=ev.outcome(self.entry,5)
        self.assertEqual(o['market']['status'],'unknown')
        self.assertEqual(o['paths']['fixed']['status'],'closed')
        self.assertIsNotNone(o['paths']['fixed']['valuationR'])

    def test_same_bar_one_r_and_safety_is_ambiguous(self):
        fine=list(self.fine);j=next(i for i,b in enumerate(fine) if b.time==self.entry['entryAt'])
        fine[j]=replace(fine[j],high=115.,low=89.)
        market=ResearchData(self.dataset(fine),self.cutoff).outcome(self.entry,5)['market']
        self.assertTrue(market['intrabarAmbiguous']);self.assertIsNone(market['oneRBeforeSafety'])

    def test_complete_panel_required_unknowns_remain_in_denominators(self):
        known={'market':{'status':'known','netPct':2.,'reason':None},'paths':{m:{'valuationR':.1} for m in ('fixed','higher_low')}}
        controls=[{'outcomes':{str(h):deepcopy(known) for h in (5,10,20)}} for _ in range(5)]
        r={'symbol':'TEST','entryAt':self.entry['entryAt'],'phase':'2024-2026','features':features(self.entry,self.frames['4h']),
           'controls':controls,'outcomes':{str(h):deepcopy(known) for h in (5,10,20)}}
        s=summarize([r])['groups']['all']['horizons']['20']['market'];self.assertEqual(s['pairedPanels'],1)
        r['controls'][0]['outcomes']['20']['market']={'status':'unknown','netPct':None,'reason':'gap'}
        s=summarize([r])['groups']['all'];self.assertEqual(s['entries'],1)
        self.assertEqual(s['horizons']['20']['market']['pairedPanels'],0);self.assertIsNone(s['horizons']['20']['market']['meanExcess'])

    def test_small_cluster_intervals_are_unknown(self):
        x=uncertainty([{'symbol':'A','entryAt':self.entry['entryAt'],'delta':1.}])
        self.assertIsNone(x['low']);self.assertIsNone(x['high'])
