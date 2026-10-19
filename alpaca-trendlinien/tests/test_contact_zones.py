import copy
from dataclasses import replace
import unittest
from unittest.mock import patch

from contact_zones import episodes, freeze
from lab_profiles import LabScanner, profile_manifest
from research import validate_spec
from test_tori_entries import controlled
from tori_entries import check


class ContactZoneTests(unittest.TestCase):
    def scanner(self, profile):
        data,spec,plan,lines=controlled()
        spec["lab"]=validate_spec({"entry_mode":"lab","lab":{"profiles":[profile],"benchmark_symbol":""}})["lab"]
        scanner=LabScanner(data,spec,plan,profile)
        scanner.context=lambda at:{"daily":{"closedAt":None,"red":None,"green":None},"structure":{"1D":"up","1W":"unknown","1M":"unknown"}}
        return scanner,lines

    def test_price_zone_counts_near_wicks_and_continuous_run_is_one_episode(self):
        scanner,lines=self.scanner("zone_measure")
        ray=lines["red"].output(scanner.bars[29].time)
        from tori_entries import value
        bars=[replace(b,high=value(ray,i)-1) for i,b in enumerate(scanner.bars[:20])]
        for i in (0,1,2,7,12):bars[i]=replace(bars[i],high=value(ray,i)-(.08 if i==7 else 0))
        exact=episodes(ray,bars,True,2,.01);zone=episodes(ray,bars,True,2,.1)
        self.assertEqual(len(exact),2);self.assertEqual(len(zone),3)
        self.assertEqual((zone[0]["firstIndex"],zone[0]["lastIndex"]),(0,2))
        self.assertEqual(len(episodes(ray,bars,True,2,.05)),2)

    def test_measurement_keeps_geometry_validity_quality_and_entry_times_identical(self):
        baseline,lines=self.scanner("baseline");zone,_=self.scanner("zone_measure")
        with patch("lab_profiles.pair",return_value=lines):
            baseline.advance(35);zone.advance(35)
        entries=lambda s:[(v["variant"],v["status"],v.get("entryAt"),v.get("entryPrice"),v["quality"]) for c in s.cases.values() for v in c["variants"]]
        self.assertEqual(entries(baseline),entries(zone))
        self.assertTrue(any(v[1]=="observed" for v in entries(zone)))
        a,b=next(iter(baseline.cases.values())),next(iter(zone.cases.values()))
        self.assertEqual(a["frozen"],b["frozen"])
        self.assertNotIn("contactMeasurement",a)
        self.assertEqual(b["contactMeasurement"]["knownAt"],zone.bars[b["armedIndex"]].end)

    def test_zone_is_frozen_before_signal_and_future_volatility_cannot_rewrite_it(self):
        scanner,lines=self.scanner("zone_measure")
        with patch("lab_profiles.pair",return_value=lines):scanner.advance(30)
        case=next(iter(scanner.cases.values()));before=copy.deepcopy(case["contactMeasurement"])
        scanner.bars[30]=replace(scanner.bars[30],high=1000)
        with patch("lab_profiles.pair",return_value=lines):scanner.advance(31)
        self.assertEqual(before,case["contactMeasurement"])
        self.assertEqual(freeze(scanner.bars[:30],4,.05)["tolerance"],.2)
        self.assertIsNone(freeze(scanner.bars[:30],None,.05)["tolerance"])

    def test_required_contacts_are_separate_from_original_quality_and_missing_zone_blocks(self):
        scanner,_=self.scanner("zone_reference")
        checks=[check("red_contacts",False,1),check("green_contacts",False,1),
                check("zone_red_contacts",True,2),check("zone_green_contacts",True,2),
                check("contact_zone_available",True),check("positive_body",False)]
        self.assertEqual(scanner.blocked(checks),["positive_body"])
        scanner,_=self.scanner("zone_red3")
        self.assertIn("contact_zone_available",scanner.blocked([check("contact_zone_available",False)]))
        old,_=self.scanner("reference")
        self.assertEqual(profile_manifest("reference",old.lab,old.options)["version"],"tori-lab-1")
        self.assertEqual(profile_manifest("zone_red3",scanner.lab,scanner.options)["version"],"contact-zone-1")

    def test_relaxed_momentum_requires_positive_body_and_proven_votes_without_mutation(self):
        scanner,lines=self.scanner("momentum_two")
        with patch("lab_profiles.pair",return_value=lines):scanner.advance(30)
        case=next(iter(scanner.cases.values()))
        checks,_,_,_=scanner.base_checks(case,30,scanner.bars[:30])
        vote=next(c for c in checks if c["name"]=="momentum_two_of_three")
        states=[c["state"] for c in checks if c["name"] in ("body_atr","body_fraction","close_location")]
        self.assertEqual(vote["value"]["passed"],states.count("pass"))
        self.assertEqual(scanner.blocked([check("positive_body",True),check("momentum_two_of_three",True),check("body_atr",False)]),[])
        self.assertIn("positive_body",scanner.blocked([check("positive_body",False),check("momentum_two_of_three",True)]))
        self.assertIn("momentum_two_of_three",scanner.blocked([check("momentum_two_of_three",None)]))

    def test_room_change_is_isolated_and_does_not_mutate_shared_options_or_accept_unknown(self):
        scanner,_=self.scanner("room_15")
        self.assertEqual(scanner.spec["tori"]["min_room_r"],0)  # controlled fixture's unchanged value
        self.assertEqual(scanner.options["min_room_r"],1.5)
        self.assertIn("room",scanner.blocked([check("room",None,None,False)]))
        self.assertEqual(scanner.blocked([check("room",True,1.75),check("execution_room",True)]),[])

    def test_momentum_votes_never_count_unknown_as_passed(self):
        scanner,_=self.scanner("momentum_two")
        for states,expected in (([True,True,False],"pass"),([True,None,False],"unknown"),([False,None,False],"fail"),([True,True,None],"pass")):
            original=[check(name,state) for name,state in zip(("body_atr","body_fraction","close_location"),states)]
            with patch("tori_entries.EntryScanner.base_checks",return_value=(original,"provisional",1,{})):
                checks,*_=scanner.base_checks({},30,scanner.bars[:30])
            self.assertEqual(next(c for c in checks if c["name"]=="momentum_two_of_three")["state"],expected)

    def test_five_percent_safety_keeps_atr_stop_and_shared_spec_unchanged(self):
        strict,_=self.scanner("risk");loose,_=self.scanner("risk_5")
        strict.options={**strict.options,"max_safety_pct":3,"max_safety_atr":2}
        loose.options={**loose.options,"max_safety_atr":2}
        self.assertIn("safety_distance_pct",strict.blocked(strict.risk_checks(100,96,2)))
        self.assertEqual(loose.blocked(loose.risk_checks(100,96,2)),[])
        self.assertIn("safety_distance_atr",loose.blocked(loose.risk_checks(100,96,1)))
        self.assertEqual(loose.spec["tori"]["max_safety_atr"],10)
        combined,_=self.scanner("momentum_two_risk5")
        self.assertIn("momentum_two_of_three",combined.blocked([check("momentum_two_of_three",False)]))
        self.assertIn("safety_distance_atr",combined.blocked([check("safety_distance_atr",False)]))
        self.assertNotIn("room",combined.blocked([check("room",None,None,False)]))

    def test_zone_reference_preserves_custom_reference_minimum_instead_of_silently_lowering_it(self):
        scanner,lines=self.scanner("zone_reference")
        scanner.options={**scanner.options,"min_contacts":4}
        with patch("lab_profiles.pair",return_value=lines):scanner.advance(30)
        case=next(iter(scanner.cases.values()))
        with patch("contact_zones.measure",return_value={"red":3,"green":2}):
            checks,*_=scanner.base_checks(case,30,scanner.bars[:30])
        red=next(c for c in checks if c["name"]=="zone_red_contacts")
        green=next(c for c in checks if c["name"]=="zone_green_contacts")
        self.assertEqual(red["state"],"fail");self.assertEqual(green["state"],"pass")


if __name__=="__main__":unittest.main()
