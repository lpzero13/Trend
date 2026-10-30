from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import json
import unittest

from datasets import digest
from fan_study import run_dataset, summarize, temporal_plan, validate
from lab_data import NORMALIZATION, resample_regular, session_bounds
from lab_metrics import expected_grid
from lab_splits import sessions_between
from models import Bar, DataError
from test_fan_geometry import triangle


def fixture():
    fine, source_index = [], 0
    base = triangle()
    for day in sessions_between("2024-01-02", "2024-05-31"):
        opened, closed = session_bounds(day)
        for start in range(opened, closed, 14400):
            end = min(start+14400, closed)
            if source_index < len(base):
                row = base[source_index]
                op, hi, lo, cl = row.open, row.high, row.low, row.close
            elif source_index == 90:
                op, hi, lo, cl = 111, 116, 100, 115
            elif source_index == 91:
                op, hi, lo, cl = 111, 114, 110.7, 113
            else:
                op, hi, lo, cl = 115, 117, 114, 116
            fine.extend(Bar(t, t+300, op, hi, lo, cl, 100) for t in range(start, end, 300))
            source_index += 1
    frames, _ = resample_regular(fine)
    material = {"symbol": "TEST", "feed": "iex", "adjustment": "split", "dataKind": "synthetic",
                "normalization": {tf: NORMALIZATION for tf in frames},
                "bars": {tf: [asdict(b) for b in rows] for tf, rows in frames.items()}}
    return {"id": digest(material), "material": material}, frames


def spec(frames, **config):
    iso = lambda t: datetime.fromtimestamp(t, timezone.utc).isoformat()
    return {"samples": 5, "seed": 29, "holdout_fraction": .2, "horizons": [5, 10, 20],
            "fan": validate({"warmup_bars": 20, "origin_start": iso(frames["4h"][80].end),
                             "origin_end": iso(frames["4h"][88].end),
                             "geometry": {"atr_length": 2, "contact_atr": .001, "wick_atr": 0, "min_age_days": 0},
                             "watch": {"clean_atr": .01, "retest_atr": .01},
                             "execution": {"capital": 10000, "risk_fraction": .1}, **config})}


class FanStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset, cls.frames = fixture()

    def run_study(self, spec_value=None, dataset=None):
        output = []
        result = run_dataset(dataset or self.dataset, spec_value or spec(self.frames), emit=output.append)
        return result, output

    def test_random_origins_walk_forward_to_first_entry_and_deduplicate(self):
        plan, output = self.run_study()
        trials = [e["trial"] for e in output if "trial" in e]
        origins = [t for t in trials if t["kind"] == "origin"]
        entries = [t for t in trials if t["kind"] == "entry"]
        self.assertEqual(len(origins), 5)
        self.assertTrue(all(o["atStart"]["snapshot"]["sourceClose"] == o["startAt"] for o in origins))
        self.assertEqual(len(entries), 2)
        self.assertEqual({e["variant"] for e in entries}, {"breakout", "retest"})
        self.assertTrue(all(e["entry"]["status"] == "filled" for e in entries))
        selections = [s for o in origins for s in o["selections"] if s["cohort"] == "qualified" and s["variant"] == "breakout"]
        self.assertEqual(len({s["entryId"] for s in selections}), 1)
        self.assertTrue(all(s["status"] == "filled" for s in selections))
        summary = summarize(trials)
        group = next(g for g in summary["groups"] if g["variant"] == "breakout" and g["cohort"] == "qualified")
        self.assertEqual(group["origins"], 5)
        self.assertEqual(group["uniqueSignals"], 1)
        self.assertEqual(group["selectedUniqueSignals"], 1)
        self.assertEqual(len(entries[0]["paths"]), 6)
        self.assertTrue(all(e["signal"]["signalAt"] < e["entry"]["entryAt"] for e in entries))
        json.dumps(output, allow_nan=False)

    def test_seed_repeat_and_holdout_never_reach_signal_or_outcome_code(self):
        first, out = self.run_study()
        second, replay = self.run_study()
        self.assertEqual((first, out), (second, replay))
        self.assertTrue(all(e["event"]["knownAt"] <= first["cutoff"] for e in out if "event" in e))
        self.assertLessEqual(first["cutoff"], first["holdoutFrom"])
        for item in out:
            if "trial" in item and item["trial"]["kind"] == "entry":
                for p in item["trial"]["paths"].values():
                    if p["exitAt"] is not None:
                        self.assertLessEqual(p["exitAt"], first["cutoff"])
        changed = deepcopy(self.dataset)
        for rows in changed["material"]["bars"].values():
            for row in rows:
                if row["end"] > first["cutoff"]:
                    row.update(open=1000, close=1000, high=1100, low=900)
        self.assertEqual(self.run_study(dataset=changed), (first, out))

    def test_multiple_lines_at_same_close_are_not_independent_entries(self):
        _, output = self.run_study(spec(self.frames, geometry_variants=["local"]))
        cases = [e["trial"] for e in output if "trial" in e and e["trial"]["kind"] == "entry"]
        keys = [(c["startAt"], c["variant"], c["cohort"]) for c in cases]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertTrue(any(c["alternativeSignalIds"] for c in cases))
        raw = [e["event"] for e in output if "event" in e and e["event"]["kind"] == "entry_signal"]
        self.assertGreater(len(raw), len(cases))

    def test_gap_between_origin_and_entry_is_unknown_not_a_later_success(self):
        frames = self.frames
        cut = frames["4h"][84].time
        fine = [b for b in frames["5m"] if b.time != cut]
        after, _ = resample_regular(fine)
        data = deepcopy(self.dataset)
        data["material"]["bars"] = {tf: [asdict(b) for b in rows] for tf, rows in after.items()}
        iso = datetime.fromtimestamp(frames["4h"][80].end, timezone.utc).isoformat()
        config = spec(frames, origin_start=iso, origin_end=iso)
        plan, output = self.run_study(config, data)
        self.assertGreater(plan["sourceGaps"], 0)
        origin = next(e["trial"] for e in output if "trial" in e and e["trial"]["kind"] == "origin")
        self.assertTrue(all(s["status"] == "unknown_source_gap" for s in origin["selections"]))

    def test_zero_entries_are_explicit_and_do_not_force_entries(self):
        iso = datetime.fromtimestamp(self.frames["4h"][105].end, timezone.utc).isoformat()
        plan, output = self.run_study(spec(self.frames, origin_start=iso, origin_end=iso))
        origins = [e["trial"] for e in output if "trial" in e and e["trial"]["kind"] == "origin"]
        self.assertEqual(len(origins), 1)
        self.assertTrue(all(s["status"] == "no_signal_before_boundary" for s in origins[0]["selections"]))
        empty_summary = summarize(origins)
        self.assertEqual(empty_summary["uniqueSignals"], 0)
        self.assertEqual(len(empty_summary["groups"]), 6)

    def test_interruption_and_bad_config_do_not_silently_run(self):
        self.assertIsNone(run_dataset(self.dataset, spec(self.frames), interrupted=lambda: True))
        for value in ({"models": []}, {"geometry_variants": [None]}, {"timeframe": "1m"},
                      {"origin_start": "2024-01-01T00:00"}, {"execution": {"risk_fraction": float("inf")}}):
            with self.assertRaises(DataError):
                validate(value)

    def test_report_streams_and_does_not_pool_feeds_or_synthetic_cases(self):
        _, output = self.run_study()
        records = [i["trial"] for i in output if "trial" in i]
        market = [{**deepcopy(r), "id": r["id"]+"market", "dataKind":"market", "feed":"sip"} for r in records]
        result = summarize(iter(records+market+records))
        self.assertEqual(result["originCount"], 10)  # duplicate rows ignored
        self.assertEqual(result["uniqueSignals"], 4)
        self.assertEqual(result["dataKinds"], ["market", "synthetic"])
        self.assertTrue(all(g["feed"] == ("iex" if g["dataKind"] == "synthetic" else "sip") for g in result["groups"]))

    def test_other_source_intervals_include_complete_weeks_without_future_candles(self):
        fine = list(self.frames["5m"])
        for day in sessions_between("2024-06-03", "2024-12-31"):
            opened, closed = session_bounds(day)
            fine.extend(Bar(t,t+300,115,117,114,116,10) for t in range(opened,closed,300))
        frames, _ = resample_regular(fine)
        data = deepcopy(self.dataset)
        data["material"]["bars"] = {tf:[asdict(b) for b in rows] for tf,rows in frames.items()}
        for tf in ("1h", "1D", "1W"):
            output = []
            config = spec(frames, timeframe=tf, origin_start=None, origin_end=None)
            result = run_dataset(data, config, emit=output.append)
            self.assertEqual(result["sourceGaps"], 0)
            self.assertEqual(len(result["origins"]), 5)
            self.assertTrue(all(i["event"]["knownAt"] <= result["cutoff"] for i in output if "event" in i))

    def test_updated_master_profile_entries_and_tail_changes_stay_causal(self):
        config=spec(self.frames, geometry_variants=["master"])
        result,output=self.run_study(config)
        entries=[i["trial"] for i in output if "trial" in i and i["trial"]["kind"]=="entry"]
        self.assertEqual({c["variant"] for c in entries},{"breakout","retest"})
        self.assertTrue(all(c["geometry"]=="master" and c["signal"]["line"]["algorithm"]=="master" for c in entries))
        self.assertTrue(all(c["signal"]["line"]["contacts"]>=2 for c in entries))
        changed=deepcopy(self.dataset)
        for rows in changed["material"]["bars"].values():
            for bar in rows:
                if bar["end"]>result["cutoff"]:bar.update(open=1000,close=1000,high=1001,low=999)
        self.assertEqual((result,output),self.run_study(config,changed))


if __name__ == "__main__":
    unittest.main()
