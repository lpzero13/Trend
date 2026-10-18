from dataclasses import replace
from datetime import datetime, timezone
import os
import tempfile
import unittest
from unittest.mock import patch

from alpaca import bar_end, parse_bars
from data_quality import audit
from datasets import save_dataset
from market_calendar import session_close
from models import Bar, DataError, NY
from providers import AlpacaProvider, fetch_sources
from test_research import fixture_sources


class QualityTests(unittest.TestCase):
    def stamp(self,day,hour=0): return int(datetime.fromisoformat(day).replace(hour=hour,tzinfo=NY).timestamp())

    def test_holiday_and_early_close_calendar(self):
        self.assertIsNone(session_close("2026-07-03"))
        self.assertIsNone(session_close("2026-11-26"))
        close=bar_end(self.stamp("2026-11-27"),"1D")
        self.assertEqual(datetime.fromtimestamp(close,NY).hour,13)
        row={"t":"2026-11-27T05:00:00Z","o":100,"h":102,"l":99,"c":101,"v":1}
        self.assertEqual(len(parse_bars([row],"1D",close)[0]),1)
        self.assertEqual(len(parse_bars([row],"1D",close-1)[0]),0)
        row["t"]="2026-11-26T05:00:00Z"
        self.assertEqual(parse_bars([row],"1D",close)[1]["rejected"],1)

    def test_us_dst_and_intraday_native_duration(self):
        for before,after,a,b in [("2026-03-06","2026-03-09",21,20),("2026-10-30","2026-11-02",20,21)]:
            self.assertEqual(datetime.fromtimestamp(bar_end(self.stamp(before),"1D"),timezone.utc).hour,a)
            self.assertEqual(datetime.fromtimestamp(bar_end(self.stamp(after),"1D"),timezone.utc).hour,b)
        t=self.stamp("2026-11-27",12)
        self.assertEqual(bar_end(t,"4h"),t+14400)

    def test_raw_split_gap_is_flagged_not_silently_repaired(self):
        a=Bar(self.stamp("2026-10-15"),self.stamp("2026-10-15",16),100,102,99,100,10)
        b=Bar(self.stamp("2026-10-16"),self.stamp("2026-10-16",16),50,51,49,50,20)
        report=audit({"1D":[a,b]},feed="iex",adjustment="raw")
        self.assertIn("large_price_discontinuities",[x["kind"] for x in report["issues"]])
        self.assertFalse(report["corporateActionsVerified"])
        self.assertEqual(b.close,50)
        adjusted=audit({"1D":[replace(a,open=50,high=51,low=49,close=50),b]},feed="iex",adjustment="all")
        self.assertNotIn("raw_corporate_actions",[x["kind"] for x in adjusted["issues"]])

    def test_dividend_like_gap_does_not_become_verified_income_or_signal(self):
        a=Bar(self.stamp("2026-10-15"),self.stamp("2026-10-15",16),100,101,99,100,1)
        b=replace(a,time=self.stamp("2026-10-16"),end=self.stamp("2026-10-16",16),open=98,close=98,low=97)
        result=audit({"1D":[a,b]},feed="iex",adjustment="raw")
        self.assertFalse(result["corporateActionsVerified"])
        self.assertIn("raw_corporate_actions",[x["kind"] for x in result["issues"]])
        self.assertNotIn("dividendIncome",result)

    def test_missing_session_excludes_holidays_and_does_not_invent_bars(self):
        bars=[Bar(self.stamp(day),self.stamp(day,16),100,101,99,100,1) for day in ("2026-11-25","2026-11-30")]
        report=audit({"1D":bars},feed="iex",adjustment="raw")
        issue=next(x for x in report["issues"] if x["kind"]=="missing_daily_sessions")
        self.assertEqual(issue["examples"],["2026-11-27"])
        self.assertEqual(len(bars),2)

    def test_mixed_adjustments_are_rejected(self):
        sources=fixture_sources()
        sources["1h"][1]["adjustment"]="split"
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{"TORI_DATA_DIR":folder}):
            with self.assertRaises(DataError): save_dataset("TEST",sources)

    def test_provider_port_is_independent_of_signal_engine(self):
        class FakeProvider:
            name="future-provider";feed="example";adjustment="raw";calendar="example"
            def load_bars(self,symbol,tf,**options): return [tf],{"provider":self.name}
        sources=fetch_sources(FakeProvider(),"TEST",history_days=900)
        self.assertEqual(set(sources),{"1h","4h","1D"})
        self.assertEqual(sources["4h"][0],["4h"])


if __name__=="__main__": unittest.main()
