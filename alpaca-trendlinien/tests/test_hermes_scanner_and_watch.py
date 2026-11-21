"""Unit, causality & integration tests for hermes_scanner, tori_paper_watch and /radar API."""
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.request

from datasets import save_dataset
import hermes_scanner as hs
from lab_data import NORMALIZATION, resample_regular, session_bounds
from lab_splits import sessions_between
from models import Bar
import server
import tori_paper_watch as pw


def _build_synthetic_bars(start_day="2024-01-02", num_sessions=260, *, price_fn=None, base_vol=25000):
    """Build valid 5m regular XNYS bars and resample to canonical 4h/1D/5m."""
    days = sessions_between(start_day, "2025-12-31")[:num_sessions]
    fine = []
    idx = 0
    for d_i, day in enumerate(days):
        opened, closed = session_bounds(day)
        t = opened
        while t + 300 <= closed:
            px = price_fn(d_i, idx, t, opened, closed) if price_fn else (50.0 + 0.05 * d_i + 0.4 * math.sin(d_i / 5.0))
            o = round(px, 2)
            h = round(px * 1.003, 2)
            l = round(px * 0.997, 2)
            c = round(px * 1.0005, 2)
            fine.append(Bar(t, t + 300, o, max(o, h, c), min(o, l, c), c, base_vol))
            t += 300
            idx += 1
    sources, quality = resample_regular(fine)
    return days, sources, quality


class HermesScannerAndWatchTests(unittest.TestCase):
    def test_stop_price_rounding_and_buffer(self):
        # floor(100.00 * 0.997 * 100) / 100 = 99.70
        self.assertEqual(hs.stop_price(100.0), 99.70)
        # floor(185.40 * 0.997 * 100) / 100 = floor(18484.38)/100 = 184.84
        self.assertEqual(hs.stop_price(185.40), 184.84)
        self.assertIsNone(hs.stop_price(0.0))
        self.assertIsNone(hs.stop_price(None))

    def test_ten_point_scoring_rewards_validated_drivers_and_low_vol(self):
        score, comp, low_vol = hs._compute_score(
            active_approach=True,
            compression_ratio=0.40,
            width_atr=2.0,
            red_age_days=25.0,
            red_contacts=4,
            red_origin="pivot",
            risk_pct=4.0,
            risk_atr=1.8,
            universes={"sp500"},
            atr_1d_pct=1.2,
            clear_sky=True,
            direct_entry=True,
        )
        self.assertEqual(score, 10)  # 2+2+1+1+1+1+1+1 = 10
        self.assertTrue(comp)
        self.assertTrue(low_vol)

        # refit (0), high vol >=1.5% (0), not direct (0), not clear sky (0)
        score2, _, low_vol2 = hs._compute_score(
            active_approach=True,
            compression_ratio=0.40,
            width_atr=2.0,
            red_age_days=25.0,
            red_contacts=3,
            red_origin="refit",
            risk_pct=4.0,
            risk_atr=1.8,
            universes={"nasdaq100"},
            atr_1d_pct=3.1,
            clear_sky=False,
            direct_entry=False,
        )
        self.assertFalse(low_vol2)
        self.assertEqual(score2, 6)  # 2+2+1+0+0+1+0+0 = 6

    def test_body_violation_respects_exact_005_atr_tolerance(self):
        rules = hs.profile("master")
        # Horizontal-ish red line at 100.0 for simplicity
        line = {"upper": True, "a_index": 0, "a_price": 100.0, "slope": 0.0}
        # Bar at idx=5 with ATR=2.0 -> body_atr * atr = 0.10 -> close 100.09 is ALLOWED
        bar_ok = Bar(1000, 2000, 99.5, 100.2, 99.0, 100.09, 1000)
        self.assertFalse(hs._has_body_violation(line, [(5, bar_ok, 2.0)], 10, rules, upper_exclude_tail=2))
        # Close 100.12 exceeds 100.0 + 0.10 -> VIOLATION
        bar_bad = Bar(1000, 2000, 99.5, 100.2, 99.0, 100.12, 1000)
        self.assertTrue(hs._has_body_violation(line, [(5, bar_bad, 2.0)], 10, rules, upper_exclude_tail=2))

    def test_strict_causality_future_shock_cannot_change_scanner_output(self):
        # Construct a converging triangle with >= 320 calendar days of history
        def px(d_i, idx, t, opened, closed):
            if d_i < 220:
                return 40.0 + 0.15 * d_i + 2.5 * math.sin(d_i / 6.0)
            # Converging wedge between day 220..255
            k = d_i - 220
            amp = max(0.8, 6.0 - 0.14 * k)
            return 72.0 + 0.04 * k + amp * math.sin(k * 0.9)

        days, sources, _ = _build_synthetic_bars(start_day="2024-01-02", num_sessions=260, price_fn=px)
        cutoff_day = days[250]
        _, cutoff = session_bounds(cutoff_day)

        base_res = hs.evaluate_symbol(
            "TEST",
            sources["4h"],
            sources["1D"],
            target_session=cutoff_day,
            cutoff=cutoff,
            dataset_id="a" * 64,
            universes={"nasdaq100"},
        )

        # Violently mutate all bars strictly after cutoff (+80% jump)
        shocked_4h = [
            Bar(b.time, b.end, b.open * 1.8, b.high * 1.8, b.low * 1.8, b.close * 1.8, b.volume)
            if b.end > cutoff else b
            for b in sources["4h"]
        ]
        shocked_1d = [
            Bar(b.time, b.end, b.open * 1.8, b.high * 1.8, b.low * 1.8, b.close * 1.8, b.volume)
            if b.end > cutoff else b
            for b in sources["1D"]
        ]
        shocked_res = hs.evaluate_symbol(
            "TEST",
            shocked_4h,
            shocked_1d,
            target_session=cutoff_day,
            cutoff=cutoff,
            dataset_id="a" * 64,
            universes={"nasdaq100"},
        )
        self.assertEqual(base_res, shocked_res)

    def test_watchlist_isolated_1000_eur_papertrade_lifecycle_and_updates(self):
        # Build a clean uptrend with a breakout at day 240 -> rise -> pullback stop-out
        def px(d_i, idx, t, opened, closed):
            if d_i < 238:
                return 80.0 + 0.08 * d_i + 1.2 * math.sin(d_i / 4.0)
            if d_i < 248:
                # Breakout rally (+18%)
                return 100.0 + 1.8 * (d_i - 238)
            # Sharp pullback triggering stop
            return max(85.0, 118.0 - 4.0 * (d_i - 248))

        days, sources, quality = _build_synthetic_bars(start_day="2024-01-02", num_sessions=258, price_fn=px)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("datasets.data_dir", return_value=root), \
                 patch("database.data_dir", return_value=root), \
                 patch("tori_paper_watch.data_dir", return_value=root), \
                 patch("daily_archive.data_dir", return_value=root):
                material = {
                    tf: (rows, {"feed": "sip", "adjustment": "split", "normalization": NORMALIZATION,
                                "rthQuality": quality, "count": len(rows),
                                "first": rows[0].time, "last": rows[-1].time, "lastClose": rows[-1].end})
                    for tf, rows in sources.items()
                }
                ds_id = save_dataset("TESTA", material, feed="sip", adjustment="split", session="XNYS regular")
                ds_id2 = save_dataset("TESTB", material, feed="sip", adjustment="split", session="XNYS regular")

                # Add TESTA right at day 239 as an active 1A_CLEAN_BREAKOUT candidate with 1.000 EUR
                day_entry = days[239]
                _, cutoff_entry = session_bounds(day_entry)
                bars_4h = [b for b in sources["4h"] if b.end <= cutoff_entry]
                anchor_bar = bars_4h[-20]
                last_bar = bars_4h[-1]
                green_line = {
                    "id": "g1", "upper": False, "a_index": len(bars_4h) - 20, "a_time": anchor_bar.time,
                    "a_price": round(last_bar.close * 0.92, 2), "b_index": len(bars_4h) - 5,
                    "b_time": bars_4h[-5].time, "b_price": round(last_bar.close * 0.94, 2),
                    "slope": (last_bar.close * 0.02) / 15.0, "value": round(last_bar.close * 0.95, 2),
                    "contacts": 2, "qualified": False, "knownAt": last_bar.end,
                }
                red_line = {
                    "id": "r1", "upper": True, "a_index": len(bars_4h) - 20, "a_time": anchor_bar.time,
                    "a_price": round(last_bar.close * 1.02, 2), "b_index": len(bars_4h) - 5,
                    "b_time": bars_4h[-5].time, "b_price": round(last_bar.close * 0.99, 2),
                    "slope": -(last_bar.close * 0.03) / 15.0, "value": round(last_bar.close * 0.98, 2),
                    "contacts": 3, "qualified": True, "knownAt": last_bar.end,
                }
                cand_a = {
                    "symbol": "TESTA", "session": day_entry, "cutoff": cutoff_entry, "dataset_id": ds_id,
                    "scenario": "1A_CLEAN_BREAKOUT", "score": 8, "strategy_tag": "TREND_FOLLOW",
                    "close_4h": last_bar.close, "clean_trigger_next1": last_bar.close,
                    "stop_0_3_pct": hs.stop_price(green_line["value"]),
                    "target_plus_2r_price": round(last_bar.close * 1.10, 2),
                    "chart_path": "/?symbol=TESTA",
                    "geometry": {"red": red_line, "green": green_line, "source_index": len(bars_4h) - 1,
                                 "bar_end": last_bar.end, "atr_4h": 1.5, "stop_0_3_pct": hs.stop_price(green_line["value"])},
                }
                cand_b = {**cand_a, "symbol": "TESTB", "dataset_id": ds_id2, "chart_path": "/?symbol=TESTB"}

                res_a = pw.add_candidate(cand_a, capital_eur=1000.0, stop_policy="r2_fan", root=root)
                res_b = pw.add_candidate(cand_b, capital_eur=1000.0, stop_policy="r2_fan", root=root)
                self.assertTrue(res_a["created"])
                self.assertTrue(res_b["created"])
                # Duplicate active add is blocked cleanly
                dup = pw.add_candidate(cand_a, capital_eur=1000.0, root=root)
                self.assertFalse(dup["created"])

                # Evaluate at day 245 (rally -> both trades should be OPEN with positive P/L, each with 1.000 EUR!)
                ev1 = pw.evaluate_all(asof_session=days[245], root=root)
                self.assertEqual(ev1["evaluated"], 2)
                self.assertEqual(ev1["summary"]["counts"].get("open"), 2)
                self.assertEqual(ev1["summary"]["openCapitalEur"], 2000.0)
                self.assertGreater(ev1["summary"]["openPnlEur"], 0.0)
                self.assertGreaterEqual(len(ev1["newUpdates"]), 2)

                # Evaluate through end (day 257 -> pullback triggers stop -> CLOSED with realized P/L)
                ev2 = pw.evaluate_all(asof_session=days[257], root=root)
                self.assertEqual(ev2["summary"]["counts"].get("closed"), 2)
                self.assertIsNotNone(ev2["summary"]["realizedPnlEur"])
                updates = pw.recent_updates(limit=20, root=root)
                event_types = {u["event_type"] for u in updates}
                self.assertIn("papertrade_opened", event_types)
                self.assertIn("papertrade_closed", event_types)

    def test_pre_breakout_watchlist_triggers_days_later_and_honors_missing_5m_gap(self):
        # Day 235: price below red (watching); Day 240: clean breakout above red -> opens papertrade!
        def px(d_i, idx, t, opened, closed):
            if d_i < 240:
                return 90.0 + 0.02 * d_i + 0.5 * math.sin(d_i / 4.0)
            return 97.2 + 0.9 * (d_i - 240)

        days, sources, quality = _build_synthetic_bars(start_day="2024-01-02", num_sessions=250, price_fn=px)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("datasets.data_dir", return_value=root), \
                 patch("database.data_dir", return_value=root), \
                 patch("tori_paper_watch.data_dir", return_value=root), \
                 patch("daily_archive.data_dir", return_value=root):
                material = {
                    tf: (rows, {"feed": "sip", "adjustment": "split", "normalization": NORMALIZATION,
                                "rthQuality": quality, "count": len(rows),
                                "first": rows[0].time, "last": rows[-1].time, "lastClose": rows[-1].end})
                    for tf, rows in sources.items()
                }
                ds_id = save_dataset("WATCHX", material, feed="sip", adjustment="split", session="XNYS regular")
                day_watch = days[235]
                _, cutoff_watch = session_bounds(day_watch)
                bars_4h = [b for b in sources["4h"] if b.end <= cutoff_watch]
                last_bar = bars_4h[-1]
                anchor_bar = bars_4h[-20]
                # Red line sits ABOVE close at day 235 (around 96.5), gently falling -> broken at day 240 (99.0)!
                red_line = {
                    "id": "rw1", "upper": True, "a_index": len(bars_4h) - 20, "a_time": anchor_bar.time,
                    "a_price": 98.0, "b_index": len(bars_4h) - 5, "b_time": bars_4h[-5].time,
                    "b_price": 96.8, "slope": -1.2 / 15.0, "value": 96.4,
                    "contacts": 3, "qualified": True, "knownAt": last_bar.end,
                }
                green_line = {
                    "id": "gw1", "upper": False, "a_index": len(bars_4h) - 20, "a_time": anchor_bar.time,
                    "a_price": 86.0, "b_index": len(bars_4h) - 5, "b_time": bars_4h[-5].time,
                    "b_price": 87.5, "slope": 1.5 / 15.0, "value": 88.0,
                    "contacts": 2, "qualified": False, "knownAt": last_bar.end,
                }
                cand = {
                    "symbol": "WATCHX", "session": day_watch, "cutoff": cutoff_watch, "dataset_id": ds_id,
                    "scenario": "2_IMMEDIATE_TEST", "score": 7, "strategy_tag": "TREND_FOLLOW",
                    "close_4h": last_bar.close, "clean_trigger_next1": 96.7,
                    "stop_0_3_pct": hs.stop_price(88.0), "target_plus_2r_price": 114.0,
                    "chart_path": "/?symbol=WATCHX",
                    "geometry": {"red": red_line, "green": green_line, "source_index": len(bars_4h) - 1,
                                 "bar_end": last_bar.end, "atr_4h": 1.2, "stop_0_3_pct": hs.stop_price(88.0)},
                }
                pw.add_candidate(cand, capital_eur=1000.0, stop_policy="r2_fan", root=root)
                # At day 237 (still below red): remains watching!
                ev_wait = pw.evaluate_all(asof_session=days[237], root=root)
                self.assertEqual(ev_wait["summary"]["counts"].get("watching"), 1)
                self.assertEqual(ev_wait["summary"]["counts"].get("open", 0), 0)
                # At day 245 (after day 240 breakout): automatically entered 1.000-EUR papertrade!
                ev_open = pw.evaluate_all(asof_session=days[245], root=root)
                self.assertEqual(ev_open["summary"]["counts"].get("open"), 1)
                self.assertEqual(ev_open["summary"]["openCapitalEur"], 1000.0)
                self.assertGreater(ev_open["summary"]["openPnlEur"], 0.0)

    def test_radar_http_page_and_api_routes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("tori_paper_watch.data_dir", return_value=root), \
                 patch("hermes_scanner.data_dir", return_value=root), \
                 patch("settings.data_dir", return_value=root):
                httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
                port = httpd.server_address[1]
                thread = threading.Thread(target=httpd.serve_forever, daemon=True)
                thread.start()
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/radar") as resp:
                        self.assertEqual(resp.status, 200)
                        html = resp.read().decode("utf-8")
                        self.assertIn("Tages-Radar", html)
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/radar/state") as resp:
                        self.assertEqual(resp.status, 200)
                        payload = json.loads(resp.read().decode("utf-8"))
                        self.assertIn("watchlist", payload)
                        self.assertIn("summary", payload)
                        self.assertEqual(payload["summary"]["capitalPerStockDefaultEur"], 1000.0)
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/backtest") as resp:
                        self.assertEqual(resp.status, 200)
                        bhtml = resp.read().decode("utf-8")
                        self.assertIn("Backtest-Explorer", bhtml)
                finally:
                    httpd.shutdown()
                    httpd.server_close()

    def test_tier_classification_and_backtest_explorer_api(self):
        self.assertEqual(
            hs.classify_tier(direct_entry=True, active_approach=True, high_maturity=True, low_daily_volatility=True),
            "C",
        )
        self.assertEqual(
            hs.classify_tier(direct_entry=False, active_approach=True, high_maturity=True, low_daily_volatility=True),
            "B",
        )
        self.assertEqual(
            hs.classify_tier(direct_entry=False, active_approach=False, high_maturity=False, low_daily_volatility=True),
            "4",
        )
        self.assertEqual(
            hs.classify_tier(direct_entry=True, active_approach=True, high_maturity=True, low_daily_volatility=False),
            "A",
        )
        self.assertEqual(
            hs.classify_tier(direct_entry=False, active_approach=False, high_maturity=False, low_daily_volatility=False),
            "BASIS",
        )
        import backtest_api as ba
        with tempfile.TemporaryDirectory() as tmp:
            art = Path(tmp)
            study = art / "scanner-backtest-pit-test"
            (study / "blocks").mkdir(parents=True)
            (study / "plan.json").write_text(
                json.dumps({"id": "abc", "pointInTime": True, "symbols": ["TEST"], "datasets": {"TEST": {"datasetId": "ds1"}}}),
                encoding="utf-8",
            )
            (study / "blocks" / "TEST.json").write_text(
                json.dumps({
                    "symbol": "TEST",
                    "datasetId": "ds1",
                    "status": "ok",
                    "trades": [{
                        "id": "t1", "symbol": "TEST", "split": "holdout", "year": "2026",
                        "watchDay": "2026-01-15", "entryDay": "2026-01-15",
                        "entrySource": "direct_1A", "scenario": "1A_CLEAN_BREAKOUT",
                        "entryStatus": "filled", "entryPrice": 100.0, "initialStop": 97.0,
                        "features": {"score": 9, "active_approach": True, "high_maturity": True, "low_daily_volatility": True, "red_origin": "pivot", "red_contacts": 4, "red_age_days": 30.0, "green_contacts": 3, "risk_pct": 3.0, "risk_atr": 2.0, "atr_1d_pct": 1.2, "universes": "sp500"},
                        "outcomes": {"r2_fan": {"status": "closed", "reason": "stop", "pnlEur": 85.0, "returnPct": 8.5, "netR": 2.8, "mfeR": 3.1, "maeR": -0.2, "r2Activated": True, "holdingDays": 12.0}},
                    }],
                }),
                encoding="utf-8",
            )
            ba._CACHE.clear()
            with patch("backtest_api.ARTIFACTS_DIR", art):
                res = ba.get("/api/backtest/trades", {"tier": ["C"], "year": ["2026"]})
                self.assertEqual(res["summary"]["totalSignals"], 1)
                self.assertEqual(res["items"][0]["tier"], "C")
                self.assertIn("symbol=TEST", res["items"][0]["replayUrl"])
                self.assertIn("dataset=ds1", res["items"][0]["replayUrl"])
                self.assertIn("asof=2026-01-15", res["items"][0]["replayUrl"])


if __name__ == "__main__":
    unittest.main()
