"""Synthetic provider replay, HTTP origin controls and SQLite backup verification."""
from contextlib import closing
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from maintenance import backup, restore, verify
from models import DataError
from paper_data import BARS_ENDPOINT, DELAY, AlpacaPaper, iso
from paper_engine import day_at
from paper_store import DB_NAME, command, create_account, draft, events, plan_preview, status
from paper_worker import cycle
from server import Handler
from strategy_run_lock import study_lock
from test_paper_engine import FRIDAY, MONDAY, minutes, plan


class SyntheticAlpaca:
    def __init__(self, tape, actions=None):
        self.tape = tape
        self.bar_calls = []
        self.action_calls = []
        self.attempts = 0
        self.reported_actions = actions or {}

    def bars(self, tickers, start, end):
        self.bar_calls.append((tickers, start, end))
        self.attempts += 1
        return {ticker: [m for m in self.tape.get(ticker, []) if start <= m.at < end] for ticker in tickers}

    def actions(self, tickers, at, *, since=None):
        self.action_calls.append((tickers, at, since))
        self.attempts += 1
        return {ticker: self.reported_actions.get(ticker, []) for ticker in tickers}


def activate(ticker="AAPL", *, at=MONDAY, **overrides):
    current = draft({"request_id": f"draft-{ticker}", "setup": plan(at, symbol=ticker, **overrides)}, at-60)
    review = plan_preview(current["id"], at)
    return command(current["id"], "activate", {"request_id": f"activate-{ticker}",
               "expected_updated": current["updated"], "confirmation": review["confirmation"]}, at)


class IntegrationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, {"TORI_DATA_DIR": str(self.root/"live")})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_bounded_paginated_endpoint_and_absent_symbol(self):
        seen = []
        price = {"t": iso(MONDAY), "o": 100, "h": 101, "l": 99, "c": 100, "v": 10}
        def request(endpoint, parameters, key, secret, *, on_attempt):
            self.assertEqual(endpoint, BARS_ENDPOINT)
            self.assertEqual(parameters["timeframe"], "1Min")
            self.assertEqual(parameters["symbols"], "AAPL,AMZN,MSFT")
            self.assertEqual(parameters["end"], iso(MONDAY))
            self.assertEqual(parameters["asof"], "-")
            on_attempt()
            seen.append(parameters)
            if "page_token" not in parameters:
                return {"bars": {"AAPL": [price]}, "next_page_token": "second"}
            return {"bars": {"AAPL": [price], "MSFT": [price]}, "next_page_token": None}
        provider = AlpacaPaper(request=request, auth=lambda: ("key", "secret"))
        rows = provider.bars(("MSFT", "AAPL", "AMZN"), MONDAY, MONDAY+60)
        self.assertEqual({key: len(value) for key, value in rows.items()}, {"AAPL": 1, "AMZN": 0, "MSFT": 1})
        self.assertEqual(provider.attempts, 2)
        self.assertEqual(seen[1]["page_token"], "second")

    def test_catchup_matches_separate_polls_and_no_weekend_overfetch(self):
        source = {
            "AAPL": [*minutes(FRIDAY+14400, 150, 104), *minutes(MONDAY, 240, 106),
                     *minutes(MONDAY+14400, 1, 106), *minutes(MONDAY+14460, 1, 88)],
            "MSFT": [*minutes(FRIDAY+14400, 150, 104), *minutes(MONDAY, 240, 106),
                     *minutes(MONDAY+14400, 1, 106), *minutes(MONDAY+14460, 1, 88)],
        }
        snapshots = []
        for folder, cutoffs in (("short", (MONDAY+14400, MONDAY+14460, MONDAY+14520)),
                                ("long", (MONDAY+14520,))):
            with patch.dict(os.environ, {"TORI_DATA_DIR": str(self.root/folder)}):
                create_account({}, FRIDAY)
                activate()
                activate("MSFT")
                provider = SyntheticAlpaca(source)
                cycle(provider, now=MONDAY-3600)
                self.assertFalse(provider.bar_calls)
                for cutoff in cutoffs:
                    cycle(provider, now=cutoff+DELAY)
                result = status()
                cycle(provider, now=cutoff+DELAY+30)
                self.assertEqual(provider.bar_calls[-1][2], cutoff)
                snapshots.append((result["cash"], result["realized_pnl"],
                                  [(p["id"], p["state"], p["data"]) for p in result["plans"]],
                                  [(e["kind"], e["event_id"]) for e in events()["items"]]))
        self.assertEqual(*snapshots)

    def test_corporate_action_and_late_cancellation(self):
        create_account({}, FRIDAY)
        original = activate()
        provider = SyntheticAlpaca({"AAPL": [*minutes(FRIDAY+14400, 150, 104), *minutes(MONDAY, 245, 106)]})
        # The worker learns of cancellation after the simulated next open occurred.
        command(original["id"], "cancel", {"expected_updated": original["updated"],
                "request_id": "cancel-0001"}, MONDAY+14410)
        cycle(provider, now=MONDAY+14460+DELAY)
        self.assertEqual(status()["plans"][0]["state"], "open")
        provider.reported_actions = {"AAPL": [{"id": "action1", "type": "forward_split",
                                               "date": day_at(MONDAY).isoformat()}]}
        result = cycle(provider, now=MONDAY+14460+DELAY+960)
        self.assertEqual(result["phase"], "attention")
        self.assertEqual(status()["issues"][0]["kind"], "corporate_action")
        self.assertEqual(status()["cursor"], MONDAY+14460)

    def test_provider_failure_leaves_journal_untouched_and_visible(self):
        create_account({}, FRIDAY)
        activate()
        provider = SyntheticAlpaca({})
        def failed(*_):
            raise DataError("Alpacas Abruflimit ist erreicht.", 429)
        provider.bars = failed
        with self.assertRaises(DataError):
            cycle(provider, now=MONDAY+DELAY+60)
        self.assertEqual(status()["worker"]["phase"], "error")
        self.assertIsNone(status()["cursor"])
        self.assertNotIn("entry", [row["kind"] for row in events()["items"]])

    def test_backup_restore_and_single_worker(self):
        create_account({}, FRIDAY)
        activate()
        feed = SyntheticAlpaca({"AAPL": [*minutes(FRIDAY+14400, 150, 104), *minutes(MONDAY, 241, 106)]})
        cycle(feed, now=MONDAY+14460+DELAY)
        expected = status()
        path = self.root/"copy"
        backup(path)
        self.assertIn(DB_NAME, verify(path)["files"])
        new = self.root/"restored"
        restore(path, new)
        with patch.dict(os.environ, {"TORI_DATA_DIR": str(new)}):
            current = status()
            self.assertEqual(current["plans"], expected["plans"])
            self.assertEqual(current["cash"], expected["cash"])
        with study_lock(self.root/"live"/"paper"/"worker"):
            with self.assertRaises(DataError):
                with study_lock(self.root/"live"/"paper"/"worker"):
                    pass

    def test_get_is_read_only_and_writes_require_origin_and_authorization(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.api_token = "paper-test-token"
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 3)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        def request(method, path, headers=None):
            with closing(HTTPConnection("127.0.0.1", server.server_port, timeout=3)) as conn:
                conn.request(method, path, "{}" if method == "POST" else None, headers or {})
                response = conn.getresponse()
                return response.status, response.read()
        auth = {"Authorization": "Bearer paper-test-token", "Content-Type": "application/json"}
        self.assertEqual(request("GET", "/api/paper/status")[0], 401)
        self.assertEqual(request("GET", "/api/paper/status", auth)[0], 200)
        self.assertFalse((self.root/"live"/DB_NAME).exists())
        self.assertEqual(request("POST", "/api/paper/account", {**auth, "Origin": "https://other.invalid"})[0], 403)
        self.assertEqual(request("POST", "/api/paper/account", auth)[0], 200)
        self.assertEqual(request("GET", "/paper", auth)[0], 200)
        self.assertEqual(request("GET", "/api/paper/trades.csv", auth)[0], 200)
        self.assertEqual(request("GET", "/paper/paper.sqlite3", auth)[0], 404)
