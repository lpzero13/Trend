"""Unit, causality, plan-binding & holdout-protection tests for scanner_backtest (Weg B)."""
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from datasets import save_dataset
from lab_data import NORMALIZATION, resample_regular, session_bounds
from lab_splits import sessions_between
from models import Bar, DataError
import scanner_backtest as sb


def _synthetic_multiyear(start_day="2023-01-03", num_sessions=420):
    """Build synthetic regular XNYS 5m/4h/1D bars spanning ~20 months with oscillating breakouts."""
    days = sessions_between(start_day, "2025-12-31")[:num_sessions]
    fine = []
    for d_i, day in enumerate(days):
        opened, closed = session_bounds(day)
        t = opened
        # Smooth upward trend with repeating 45-day consolidation wedges + breakouts
        cycle = d_i % 45
        base = 50.0 + 0.12 * d_i
        if cycle < 32:
            amp = max(0.7, 4.5 - 0.12 * cycle)
            wave = amp * math.sin(cycle * 0.7)
        else:
            wave = 1.6 + 0.35 * (cycle - 32)
        px = base + wave
        while t + 300 <= closed:
            o = round(px, 2)
            h = round(px * 1.003, 2)
            l = round(px * 0.997, 2)
            c = round(px * 1.0004, 2)
            fine.append(Bar(t, t + 300, o, max(o, h, c), min(o, l, c), c, 30000))
            t += 300
    sources, quality = resample_regular(fine)
    return days, sources, quality


class ScannerBacktestTests(unittest.TestCase):
    def test_strict_causality_future_shock_preserves_train_entries(self):
        days, sources, _ = _synthetic_multiyear(start_day="2023-01-03", num_sessions=410)
        train_end = days[360]
        _, train_cutoff = session_bounds(train_end)
        _, outcome_cutoff = session_bounds(days[-1])
        splits = {
            "train": (days[250], train_end),
            "validation": (days[361], days[385]),
            "holdout": (days[386], days[400]),
        }

        base = sb.backtest_symbol(
            "CAUSAL",
            sources["4h"], sources["1D"], sources["5m"],
            dataset_id="a" * 64, universes={"nasdaq100"},
            splits=splits, outcome_cutoff=outcome_cutoff,
        )

        # Violently shock ALL bars strictly after train_cutoff (+80%)
        s4 = [Bar(b.time, b.end, b.open * 1.8, b.high * 1.8, b.low * 1.8, b.close * 1.8, b.volume) if b.end > train_cutoff else b for b in sources["4h"]]
        s1 = [Bar(b.time, b.end, b.open * 1.8, b.high * 1.8, b.low * 1.8, b.close * 1.8, b.volume) if b.end > train_cutoff else b for b in sources["1D"]]
        s5 = [Bar(b.time, b.end, b.open * 1.8, b.high * 1.8, b.low * 1.8, b.close * 1.8, b.volume) if b.end > train_cutoff else b for b in sources["5m"]]
        shocked = sb.backtest_symbol(
            "CAUSAL", s4, s1, s5,
            dataset_id="a" * 64, universes={"nasdaq100"},
            splits=splits, outcome_cutoff=outcome_cutoff,
        )

        # Every entry signal & its features in train MUST be 100% identical!
        base_train = [(t["id"], t["entryDay"], t["scenario"], t["features"]) for t in base["trades"] if t["split"] == "train" and t["entryDay"] <= train_end]
        shocked_train = [(t["id"], t["entryDay"], t["scenario"], t["features"]) for t in shocked["trades"] if t["split"] == "train" and t["entryDay"] <= train_end]
        self.assertEqual(base_train, shocked_train)

    def test_plan_binding_resume_and_holdout_protection(self):
        days, sources, quality = _synthetic_multiyear(start_day="2023-01-03", num_sessions=410)
        splits = {
            "train": (days[250], days[350]),
            "validation": (days[351], days[380]),
            "holdout": (days[381], days[400]),
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "data"
            out = Path(tmp) / "study"
            with patch("datasets.data_dir", return_value=root), \
                 patch("database.data_dir", return_value=root), \
                 patch("daily_archive.data_dir", return_value=root), \
                 patch("scanner_backtest.data_dir", return_value=root):
                material = {
                    tf: (rows, {"feed": "sip", "adjustment": "split", "normalization": NORMALIZATION,
                                "rthQuality": quality, "count": len(rows),
                                "first": rows[0].time, "last": rows[-1].time, "lastClose": rows[-1].end})
                    for tf, rows in sources.items()
                }
                save_dataset("SYNTH", material, feed="sip", adjustment="split", session="XNYS regular")

                # First run creates plan + block
                res1 = sb.run_study(
                    out, symbols=["SYNTH"], splits=splits,
                    outcome_cutoff=days[-1], workers=1, resume=True, root=root,
                )
                self.assertEqual(res1["processedNow"], 1)
                self.assertEqual(res1["skippedResume"], 0)
                self.assertEqual(res1["errors"], 0)

                # Resume skips already completed block
                res2 = sb.run_study(
                    out, symbols=["SYNTH"], splits=splits,
                    outcome_cutoff=days[-1], workers=1, resume=True, root=root,
                )
                self.assertEqual(res2["processedNow"], 0)
                self.assertEqual(res2["skippedResume"], 1)

                # Inject a fake holdout trade to verify holdout lock in report
                bp = out / "blocks" / "SYNTH.json"
                blk = json.loads(bp.read_text("utf-8"))
                blk["trades"].append({
                    "id": "holdout_test_1", "symbol": "SYNTH", "split": "holdout", "year": "2024",
                    "watchDay": days[385], "entryDay": days[385], "entrySource": "direct_1A",
                    "scenario": "1A_CLEAN_BREAKOUT", "entryStatus": "filled", "entryReason": None,
                    "entryPrice": 100.0, "initialStop": 95.0,
                    "features": {
                        "score": 9, "strategy_tag": "TREND_FOLLOW", "above_sma200": True,
                        "active_approach": True, "compression": True, "high_maturity": True,
                        "red_origin": "pivot", "stop_sweet_spot": True, "high_beta": True,
                        "clear_sky": True, "overhead_roof_near": False, "low_daily_volatility": False,
                        "risk_pct": 5.0, "risk_atr": 2.0, "red_contacts": 3, "red_age_days": 25.0,
                        "red_contact_span_days": 15.0, "green_contacts": 2, "atr_1d_pct": 3.0,
                        "universes": "nasdaq100", "close_4h": 100.0, "stop_0_3_pct": 95.0,
                    },
                    "outcomes": {
                        p: {"status": "closed", "reason": "stop", "pnlEur": 120.0, "returnPct": 12.0,
                            "netR": 2.4, "mfeR": 3.0, "maeR": -0.2, "r2Activated": True, "holdingDays": 12.0}
                        for p in sb.STOP_POLICIES
                    },
                })
                bp.write_text(json.dumps(blk), encoding="utf-8")

                # Default report MUST hide holdout!
                rep_locked = sb.build_report(out, reveal_holdout=False)
                self.assertGreaterEqual(rep_locked["hiddenHoldoutTrades"], 1)
                self.assertNotIn("holdout_test_1", Path(rep_locked["files"]["tradesCsv"]).read_text("utf-8"))

                # Explicit reveal_holdout MUST include holdout!
                rep_open = sb.build_report(out, reveal_holdout=True)
                self.assertEqual(rep_open["hiddenHoldoutTrades"], 0)
                self.assertIn("holdout_test_1", Path(rep_open["files"]["tradesCsv"]).read_text("utf-8"))
                self.assertIn("## 1. Vergleich der Stop-Modelle", Path(rep_open["files"]["report"]).read_text("utf-8"))

                # Tampering with plan code binding MUST raise 409
                plan_path = out / "plan.json"
                plan_data = json.loads(plan_path.read_text("utf-8"))
                plan_data["engine"]["scanner_backtest.py"] = "0" * 64
                plan_path.write_text(json.dumps(plan_data), encoding="utf-8")
                with self.assertRaises(DataError) as err:
                    sb._load_plan(out)
                self.assertEqual(err.exception.status, 409)

    def test_point_in_time_membership_blocks_entries_outside_index_window(self):
        days, sources, _ = _synthetic_multiyear(start_day="2023-01-03", num_sessions=410)
        _, outcome_cutoff = session_bounds(days[-1])
        splits = {"train": (days[250], days[390]), "validation": (days[391], days[400]), "holdout": ("2026-01-01", "2026-06-30")}
        # Allow membership ONLY during a narrow 10-day window (days[300]..days[310])
        narrow_start, narrow_end = days[300], days[310]
        pit_intervals = {"sp500": [[narrow_start, narrow_end]]}
        res = sb.backtest_symbol(
            "PITTEST",
            sources["4h"], sources["1D"], sources["5m"],
            dataset_id="b" * 64, universes={"sp500"},
            splits=splits, outcome_cutoff=outcome_cutoff,
            pit_intervals=pit_intervals,
        )
        # Every watch/direct signal must have originated strictly within [narrow_start .. narrow_end]!
        for trade in res["trades"]:
            self.assertGreaterEqual(trade["watchDay"], narrow_start)
            self.assertLessEqual(trade["watchDay"], narrow_end)


if __name__ == "__main__":
    unittest.main()
