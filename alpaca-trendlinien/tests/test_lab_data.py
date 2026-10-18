from dataclasses import replace
from datetime import datetime, timezone
import os
import tempfile
import unittest
from unittest.mock import patch

from alpaca import load_bars
from datasets import save_dataset, read_dataset
from lab_data import NORMALIZATION, session_bounds, resample_regular, require_convention
from models import Bar, DataError, NY


def session(day, price=100):
    opened, closed=session_bounds(day)
    return [Bar(t,t+300,price,price+1,price-1,price+.5,10) for t in range(opened,closed,300)]


class LabDataTests(unittest.TestCase):
    def test_regular_buckets_anchor_at_open_and_shorten_last_bucket(self):
        rows, q=resample_regular(session("2025-03-07")+session("2025-03-10"))
        self.assertEqual(len(rows["4h"]),4)
        self.assertEqual([b.end-b.time for b in rows["4h"]],[14400,9000,14400,9000])
        self.assertEqual(datetime.fromtimestamp(rows["4h"][0].time,NY).hour,9)
        self.assertEqual(datetime.fromtimestamp(rows["4h"][0].time,NY).minute,30)
        self.assertEqual((rows["4h"][2].time-rows["4h"][0].time)%86400,82800)
        early,_=resample_regular(session("2026-11-27"))
        self.assertEqual(len(early["4h"]),1)
        self.assertEqual(early["4h"][0].end-early["4h"][0].time,12600)
        self.assertEqual(q["missingBuckets"]["1D"],0)

    def test_gaps_and_partial_days_are_not_forward_filled(self):
        fine=session("2025-03-10")
        rows,q=resample_regular(fine[:3]+fine[4:])
        self.assertEqual(len(rows["5m"]),77)
        self.assertEqual(len(rows["4h"]),1)
        self.assertEqual(len(rows["1D"]),0)
        self.assertEqual(q["missingBuckets"]["4h"],1)
        rows,_=resample_regular(fine[:48])
        self.assertEqual(len(rows["4h"]),1)
        self.assertEqual(len(rows["1D"]),0)
        extra=replace(fine[0],time=fine[0].time-3600,end=fine[0].end-3600)
        self.assertEqual(resample_regular([extra]+fine)[0]["5m"],fine)

    def test_fine_sources_are_immutable_and_adjustment_is_part_of_identity(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{"TORI_DATA_DIR":folder}):
            fine=sum((session(d) for d in ("2025-03-10","2025-03-11","2025-03-12")),[])
            rows,_=resample_regular(fine)
            source=lambda adj:{tf:(bars,{"feed":"iex","adjustment":adj,"normalization":NORMALIZATION,"quality":{"rejected":0},"warning":None}) for tf,bars in rows.items()}
            a=save_dataset("TEST",source("raw"))
            b=save_dataset("TEST",source("split"),adjustment="split")
            self.assertNotEqual(a,b)
            self.assertEqual(len(read_dataset(a)["material"]["bars"]["5m"]),234)
            self.assertTrue(require_convention(read_dataset(b))["regular5m"])
            native=read_dataset(a);native["material"]["normalization"]={}
            with self.assertRaises(DataError):require_convention(native)
            self.assertFalse(require_convention(native,allow_native=True)["regular5m"])

    def test_feed_adjustment_cache_keys_and_adjusted_refresh_never_merge_old_scales(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{"TORI_DATA_DIR":folder}),patch("alpaca.credentials",return_value=("test","secret")):
            now=datetime(2025,3,13,18,tzinfo=timezone.utc)
            fine=session("2025-03-12")[:4]
            raw=[{"t":datetime.fromtimestamp(b.time,timezone.utc).isoformat(),"o":b.open,"h":b.high,"l":b.low,"c":b.close,"v":b.volume} for b in fine]
            params=[]
            def response(value,*args):
                params.append(dict(value));return {"bars":{"TEST":raw}}
            with patch("alpaca._request",side_effect=response):
                load_bars("TEST","5m",now=now,history_days=30)
                load_bars("TEST","5m",now=now,history_days=30,feed="sip",adjustment="split")
                load_bars("TEST","5m",now=now,history_days=30,feed="sip",adjustment="split",force=True)
            self.assertEqual(params[0]["timeframe"],"5Min")
            self.assertEqual(params[1]["feed"],"sip")
            self.assertEqual(params[1]["adjustment"],"split")
            self.assertEqual(params[1]["start"],params[2]["start"])
            from pathlib import Path
            self.assertEqual(len(list((Path(folder)/"market").glob("*.json"))),2)

    def test_synthetic_provenance_is_visible_without_rewriting_existing_datasets(self):
        from pathlib import Path
        from datasets import chart_dataset, data_kind
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{"TORI_DATA_DIR":folder}):
            rows,_=resample_regular(sum((session(d) for d in ("2025-03-10","2025-03-11","2025-03-12")),[]))
            source={tf:(bars,{"feed":"iex","adjustment":"raw","normalization":NORMALIZATION,"quality":{"rejected":0},"warning":None}) for tf,bars in rows.items()}
            market=save_dataset("TEST",source)
            self.assertEqual(data_kind(read_dataset(market)),"market")
            self.assertNotIn("dataKind",read_dataset(market)["material"])
            synthetic=save_dataset("TEST",source,data_kind="synthetic")
            self.assertNotEqual(market,synthetic)
            self.assertEqual(chart_dataset(synthetic,"1h")["dataKind"],"synthetic")
            legacy={tf:(bars,{**meta,"mode":"synthetic-offline-fixture"}) for tf,(bars,meta) in source.items()}
            old=save_dataset("LEGACY",legacy)
            path=Path(folder)/"datasets"/(old+".json");before=path.read_bytes()
            chart=chart_dataset(old,"1h")
            self.assertEqual(chart["dataKind"],"synthetic")
            self.assertIn("Synthetischer Test",chart["company"])
            self.assertEqual(path.read_bytes(),before)
            self.assertEqual(chart_dataset(market,"1h")["dataKind"],"market")

    def test_split_like_discontinuity_is_flagged_not_silently_repaired_and_adjusted_revision_preserves_raw(self):
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{"TORI_DATA_DIR":folder}):
            raw,_=resample_regular(session("2025-03-10",100)+session("2025-03-11",50)+session("2025-03-12",50))
            adjusted,_=resample_regular(session("2025-03-10",50)+session("2025-03-11",50)+session("2025-03-12",50))
            source=lambda rows,mode:{tf:(bars,{"feed":"iex","adjustment":mode,"normalization":NORMALIZATION,"quality":{"rejected":0},"warning":None}) for tf,bars in rows.items()}
            old=save_dataset("TEST",source(raw,"raw"))
            path=Path(folder)/"datasets"/(old+".json");before=path.read_bytes()
            new=save_dataset("TEST",source(adjusted,"split"),adjustment="split")
            self.assertNotEqual(old,new);self.assertEqual(path.read_bytes(),before)
            self.assertTrue(any(i["kind"]=="large_price_discontinuities" for i in read_dataset(old)["quality"]["issues"]))
            self.assertFalse(any(i["kind"]=="large_price_discontinuities" for i in read_dataset(new)["quality"]["issues"]))
            self.assertFalse(read_dataset(new)["quality"]["corporateActionsVerified"])


if __name__=="__main__":unittest.main()
