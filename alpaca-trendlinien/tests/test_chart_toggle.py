"""Manual charts must not execute or archive automatic analyses."""
from dataclasses import asdict
from unittest.mock import patch
import unittest

from analysis_service import build_chart
from datasets import chart_dataset
from server import chart_payload
from test_history import dataset, metadata, NOW, CUTOFF


class ManualChartTests(unittest.TestCase):
    def sources(self):
        return {tf: (dataset(tf), metadata(dataset(tf))) for tf in ("1h", "4h", "1D")}

    def test_manual_and_analyzed_views_have_identical_causal_candles(self):
        full = build_chart(self.sources(), "TEST", "1h", CUTOFF, NOW, historical=True)
        with patch("analysis_service.analyze", side_effect=AssertionError("Manual chart must not analyze")):
            manual = build_chart(self.sources(), "TEST", "1h", CUTOFF, NOW,
                                 historical=True, include_analysis=False)
        self.assertFalse(manual["analysisEnabled"])
        self.assertEqual(manual["lanes"], {})
        for key in ("charts", "bars", "axis", "latest", "fingerprint", "analysisCutoff"):
            self.assertEqual(manual[key], full[key], key)
        self.assertTrue(all(b["end"] <= CUTOFF.timestamp() for b in manual["bars"]))
        self.assertTrue(full["analysisEnabled"])
        self.assertEqual(set(full["lanes"]), {"1h", "4h", "1D"})

    def test_manual_live_api_payload_does_not_create_freezable_analysis(self):
        with patch("server.load_bars", side_effect=lambda symbol, tf, **kw: self.sources()[tf]), \
             patch("analysis_service.analyze", side_effect=AssertionError("No analysis")), \
             patch("server.remember") as remember:
            payload = chart_payload("TEST", "4h", as_of=CUTOFF.isoformat(), include_analysis=False)
        remember.assert_not_called()
        self.assertNotIn("analysisId", payload)
        self.assertEqual(payload["lanes"], {})

    def test_manual_research_dataset_ignores_signal_overlays_and_never_archives(self):
        sources = self.sources()
        data = {"id": "pinned", "material": {"symbol": "TEST", "provider": "Alpaca",
            "feed": "iex", "adjustment": "split", "session": "Regular",
            "bars": {tf: [asdict(b) for b in bars] for tf, (bars, _) in sources.items()}},
            "sources": {tf: meta for tf, (_, meta) in sources.items()}}
        with patch("datasets.read_dataset", return_value=data), \
             patch("analysis_service.analyze", side_effect=AssertionError("No analysis")), \
             patch("snapshots.remember") as remember:
            payload = chart_dataset("pinned", "1h", CUTOFF.isoformat(),
                                    {"deliberately": "no readable signal"}, include_analysis=False)
        remember.assert_not_called()
        self.assertFalse(payload["analysisEnabled"])
        self.assertEqual(payload["adjustment"], "split")
        self.assertEqual(payload["datasetId"], "pinned")
        self.assertNotIn("researchSetup", payload)
        self.assertNotIn("analysisId", payload)
