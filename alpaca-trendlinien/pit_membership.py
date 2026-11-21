"""Point-in-time historical index membership (Dow 30, Nasdaq-100, S&P 500) & SIP importer.

Eliminates survivorship bias across 2016-2026 by combining open-source point-in-time
constituent histories (fja05680/sp500, jmccarrell/n100tickers, verified DJIA changes)
with Alpaca SIP 5m split-adjusted bars (including demoted and delisted tickers via `asof`).
All downloaded raw lists, datasets and audits live under TORI_DATA_DIR (never in Git).
"""
from bisect import bisect_right
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import re
import time

import alpaca
from daily_archive import inventory as archive_inventory
from datasets import save_dataset
from history_fast import parse_page
from history_http import Client
from lab_data import NORMALIZATION, resample_regular, session_bounds
from models import DataError
from settings import data_dir
from universe_catalog import read as read_universe

VERSION = "tori-pit-membership-1"
PIT_DIR_REL = Path("pit-membership")
PIT_FILE_NAME = "pit-membership-2016-2026.json"
AUDIT_FILE_NAME = "import-audit.json"
UTC = timezone.utc

# Verified official S&P Dow Jones Industrial Average changes (2016-01-01 .. 2026-10-29).
# Each entry: (effective_date, added_tuple, removed_tuple).
DOW30_CHANGES = (
    ("2017-09-01", ("DWDP",), ("DD",)),
    ("2018-06-26", ("WBA",), ("GE",)),
    ("2019-04-02", ("DOW",), ("DWDP",)),
    ("2020-04-06", ("RTX",), ("UTX",)),
    ("2020-08-31", ("AMGN", "CRM", "HON"), ("PFE", "RTX", "XOM")),
    ("2024-02-26", ("AMZN",), ("WBA",)),
    ("2024-11-08", ("NVDA", "SHW"), ("INTC", "DOW")),
    ("2026-06-29", ("GOOGL",), ("VZ",)),
)

# Known ticker formatting normalizations (Wikipedia/GitHub -> Alpaca SIP symbol)
DASH_TO_DOT = {"BRK-B": "BRK.B", "BF-B": "BF.B", "BRK-A": "BRK.A", "BF-A": "BF.A"}


def norm_symbol(sym):
    s = str(sym or "").strip().upper()
    if s in DASH_TO_DOT:
        return DASH_TO_DOT[s]
    # Standard share-class hyphen (e.g. BRK-B -> BRK.B), keep valid Alpaca chars
    if re.fullmatch(r"[A-Z]{1,4}-[A-Z]", s):
        return s.replace("-", ".")
    return s


def _parse_n100_yaml(text):
    """Zero-dependency parser for jmccarrell/n100tickers YAML files."""
    year = None
    jan1 = []
    changes = {}
    section = None
    cur_date = None
    cur_op = None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip() or line.strip() == "---":
            continue
        stripped = line.strip()
        if line.startswith("year:"):
            year = int(stripped.split(":", 1)[1].strip())
        elif line.startswith("tickers_on_Jan_1:"):
            section = "jan1"
        elif line.startswith("changes:"):
            section = "changes"
            cur_date = None
            cur_op = None
        elif section == "jan1" and stripped.startswith("- "):
            jan1.append(norm_symbol(stripped[2:]))
        elif section == "changes":
            m_date = re.match(r'^  ["\']?(\d{4}-\d{2}-\d{2})["\']?:\s*$', line)
            if m_date:
                cur_date = m_date.group(1)
                changes.setdefault(cur_date, {"union": [], "difference": []})
                cur_op = None
            elif line.startswith("    union:"):
                cur_op = "union"
            elif line.startswith("    difference:"):
                cur_op = "difference"
            elif cur_date and cur_op and stripped.startswith("- "):
                changes[cur_date][cur_op].append(norm_symbol(stripped[2:]))
    return year, jan1, changes


def _build_dow30_snapshots(current_members, end_date="2026-10-29"):
    """Reconstruct exact 30-stock DJIA snapshots from 2016-01-01 to end_date backwards."""
    cur = {norm_symbol(s) for s in current_members}
    if len(cur) != 30:
        raise DataError(f"Dow-30 Basis hat {len(cur)} statt 30 Mitglieder.", 400)
    # Walk backwards from end_date to 2016-01-01
    dated = [(end_date, sorted(cur))]
    working = set(cur)
    for eff_date, added, removed in reversed(DOW30_CHANGES):
        if eff_date > end_date:
            continue
        # Record snapshot right AT eff_date (with the new members)
        dated.append((eff_date, sorted(working)))
        # Reverse the change to obtain composition BEFORE eff_date
        for s in added:
            working.discard(norm_symbol(s))
        for s in removed:
            working.add(norm_symbol(s))
        if len(working) != 30:
            raise DataError(f"Dow-30 Rekonstruktionsfehler vor {eff_date}: {len(working)} Titel.", 500)
    dated.append(("2016-01-01", sorted(working)))
    # Deduplicate by date keeping latest entry for each date, sorted ascending
    by_date = {}
    for d, members in dated:
        by_date[d] = members
    return [(d, by_date[d]) for d in sorted(by_date)]


def _build_nasdaq100_snapshots(raw_dir, current_members=None, current_asof="2026-10-28"):
    """Build exact dated Nasdaq-100 snapshots from 2016-01-01 through 2026 from YAML files."""
    by_date = {}
    for year in range(2016, 2027):
        ypath = Path(raw_dir) / f"n100-ticker-changes-{year}.yaml"
        if not ypath.is_file():
            continue
        _, jan1, changes = _parse_n100_yaml(ypath.read_text("utf-8"))
        active = set(jan1)
        by_date[f"{year}-01-01"] = sorted(active)
        for day in sorted(changes):
            for s in changes[day].get("difference", []):
                active.discard(s)
            for s in changes[day].get("union", []):
                active.add(s)
            by_date[day] = sorted(active)
    if current_members and current_asof > max(by_date, default=""):
        by_date[current_asof] = sorted({norm_symbol(s) for s in current_members})
    return [(d, by_date[d]) for d in sorted(by_date)]


def _build_sp500_snapshots(raw_dir, current_members=None, current_asof="2026-10-28"):
    """Build exact dated S&P 500 snapshots from 2016-01-01 through 2026 from fja05680/sp500 CSV."""
    csv_path = Path(raw_dir) / "sp500_updated.csv"
    if not csv_path.is_file():
        raise DataError(f"S&P-500-Historiendatei fehlt: {csv_path}", 404)
    by_date = {}
    last_before_2016 = None
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            d = row["date"].strip()
            tickers = sorted({norm_symbol(t) for t in row["tickers"].split(",") if t.strip()})
            if d <= "2016-01-01":
                last_before_2016 = tickers
            else:
                by_date[d] = tickers
    if last_before_2016:
        by_date["2016-01-01"] = last_before_2016
    if current_members and current_asof > max(by_date, default=""):
        by_date[current_asof] = sorted({norm_symbol(s) for s in current_members})
    return [(d, by_date[d]) for d in sorted(by_date)]


def _extract_intervals(snapshots, end_date="2026-10-29"):
    """Convert [(date, [tickers])] into {symbol: [[start, end], ...]} inclusive intervals."""
    intervals = {}
    active_start = {}
    for i, (day, members) in enumerate(snapshots):
        mset = set(members)
        # Symbols leaving on `day` had their last active day right before `day`
        prev_day = (date.fromisoformat(day) - timedelta(days=1)).isoformat()
        for sym in list(active_start):
            if sym not in mset:
                intervals.setdefault(sym, []).append([active_start.pop(sym), max(active_start.get(sym, prev_day), prev_day)])
        for sym in mset:
            if sym not in active_start:
                active_start[sym] = day
    for sym, start in active_start.items():
        intervals.setdefault(sym, []).append([start, end_date])
    return intervals


def build_pit_membership(*, root=None, end_date="2026-10-29"):
    """Assemble and persist the unified 2016-2026 Point-in-Time membership catalog."""
    base = Path(root) if root else data_dir()
    pit_dir = base / PIT_DIR_REL
    raw_dir = pit_dir / "raw"

    u_dow = read_universe("dow30")
    u_n100 = read_universe("nasdaq100")
    u_sp500 = read_universe("sp500")
    if not u_dow:
        raise DataError("Lokaler dow30-Bestand nicht gefunden.", 404)

    dow_snaps = _build_dow30_snapshots([m["symbol"] for m in u_dow["members"]], end_date=end_date)
    n100_snaps = _build_nasdaq100_snapshots(
        raw_dir,
        current_members=[m["symbol"] for m in u_n100["members"]] if u_n100 else None,
        current_asof=u_n100["asOf"] if u_n100 else end_date,
    )
    sp500_snaps = _build_sp500_snapshots(
        raw_dir,
        current_members=[m["symbol"] for m in u_sp500["members"]] if u_sp500 else None,
        current_asof=u_sp500["asOf"] if u_sp500 else end_date,
    )

    by_universe = {
        "dow30": dow_snaps,
        "nasdaq100": n100_snaps,
        "sp500": sp500_snaps,
    }
    sym_meta = {}
    for u_name, snaps in by_universe.items():
        iv_map = _extract_intervals(snaps, end_date=end_date)
        for sym, ivs in iv_map.items():
            entry = sym_meta.setdefault(sym, {"universes": {}, "firstDate": "9999-12-31", "lastDate": "0000-01-01"})
            entry["universes"][u_name] = ivs
            for s, e in ivs:
                if s < entry["firstDate"]:
                    entry["firstDate"] = s
                if e > entry["lastDate"]:
                    entry["lastDate"] = e

    # Determine optimal Alpaca `asof` date per symbol:
    # Active in late 2026 -> None (current); exited earlier -> lastDate (historical entity!)
    for sym, entry in sym_meta.items():
        entry["activeAtEnd"] = entry["lastDate"] >= end_date
        entry["asofDate"] = None if entry["activeAtEnd"] else entry["lastDate"]

    payload = {
        "version": VERSION,
        "builtAt": datetime.now(UTC).isoformat(),
        "range": ["2016-01-01", end_date],
        "sources": {
            "sp500": "github.com/fja05680/sp500 (S&P 500 Historical Components & Changes Updated) + local 2026-10-28 IVV",
            "nasdaq100": "github.com/jmccarrell/n100tickers (2016-2026 YAML) + local 2026-10-28 CNDX",
            "dow30": "Verified official S&P Dow Jones DJIA changes 2016-2026 + local 2026-10-28 DIA",
        },
        "counts": {
            "totalUniqueSymbols": len(sym_meta),
            "activeAtEnd": sum(1 for v in sym_meta.values() if v["activeAtEnd"]),
            "exMembers2016To2026": sum(1 for v in sym_meta.values() if not v["activeAtEnd"]),
            "byUniverse": {
                u: len({s for _, ms in snaps for s in ms})
                for u, snaps in by_universe.items()
            },
        },
        "snapshots": {u: snaps for u, snaps in by_universe.items()},
        "symbols": {k: sym_meta[k] for k in sorted(sym_meta)},
    }
    pit_dir.mkdir(parents=True, exist_ok=True)
    out_path = pit_dir / PIT_FILE_NAME
    tmp = out_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    tmp.replace(out_path)
    return payload, out_path


class PitMembership:
    """Fast O(log N) point-in-time index membership checker for backtests."""

    def __init__(self, payload):
        self.payload = payload
        self.symbols = payload["symbols"]
        self._dates = {}
        self._sets = {}
        for u_name, snaps in payload["snapshots"].items():
            self._dates[u_name] = [d for d, _ in snaps]
            self._sets[u_name] = [frozenset(ms) for _, ms in snaps]

    @classmethod
    def load(cls, path=None, *, root=None):
        p = Path(path) if path else (Path(root) if root else data_dir()) / PIT_DIR_REL / PIT_FILE_NAME
        if not p.is_file():
            raise DataError(f"Point-in-Time-Mitgliedschaftsdatei fehlt: {p}", 404)
        return cls(json.loads(p.read_text("utf-8")))

    def universes_on(self, symbol, day_str, *, allowed_universes=("dow30", "nasdaq100", "sp500")):
        result = set()
        for u_name in allowed_universes:
            dates = self._dates.get(u_name)
            if not dates:
                continue
            pos = bisect_right(dates, day_str) - 1
            if pos >= 0 and symbol in self._sets[u_name][pos]:
                result.add(u_name)
        return result

    def is_member(self, symbol, day_str, universe="all"):
        allowed = ("dow30", "nasdaq100", "sp500") if universe in (None, "all") else (universe,)
        return bool(self.universes_on(symbol, day_str, allowed_universes=allowed))


def _fetch_symbol_5m_sip(client, symbol, start_day, end_day, asof_day):
    """Fetch complete 5m split-adjusted SIP bars for one symbol across yearly chunks."""
    start_dt = date.fromisoformat(max("2016-01-04", start_day))
    end_dt = date.fromisoformat(min("2026-10-29", end_day))
    if start_dt > end_dt:
        return []
    bars_by_time = {}
    cur_year = start_dt.year
    while cur_year <= end_dt.year:
        y_start = max(start_dt, date(cur_year, 1, 1))
        y_end = min(end_dt, date(cur_year, 12, 31))
        s_utc = datetime(y_start.year, y_start.month, y_start.day, 0, 0, tzinfo=UTC)
        e_utc = datetime(y_end.year, y_end.month, y_end.day, 23, 59, 59, tzinfo=UTC)
        params = {
            "symbols": symbol,
            "timeframe": "5Min",
            "feed": "sip",
            "adjustment": "split",
            "start": s_utc.isoformat(),
            "end": e_utc.isoformat(),
            "sort": "asc",
            "limit": 10000,
        }
        if asof_day:
            params["asof"] = asof_day
        tokens = set()
        while True:
            page = client.request(params)
            sym_rows = (page.get("bars") or {}).get(symbol, []) if isinstance(page, dict) else []
            for bar in parse_page(sym_rows, s_utc, e_utc + timedelta(seconds=1)):
                bars_by_time[bar.time] = bar
            token = page.get("next_page_token") if isinstance(page, dict) else None
            if not token:
                break
            if token in tokens or len(tokens) >= 500:
                raise DataError("Ungültige Paginierung von Alpaca.", 502)
            tokens.add(token)
            params["page_token"] = token
        cur_year += 1
    return [bars_by_time[t] for t in sorted(bars_by_time)]


def import_missing_pit_symbols(
    *,
    root=None,
    workers=4,
    limit=None,
    retry_failed=False,
    progress=None,
):
    """Fetch 5m SIP split-adjusted bars from Alpaca for all PIT symbols missing locally."""
    base = Path(root) if root else data_dir()
    pit = PitMembership.load(root=base)
    all_pit = sorted(pit.symbols)
    existing = archive_inventory(set(all_pit), base)

    audit_path = base / PIT_DIR_REL / AUDIT_FILE_NAME
    audit = json.loads(audit_path.read_text("utf-8")) if audit_path.is_file() else {"version": VERSION, "symbols": {}}

    # Check which symbols are missing locally
    todo = []
    for sym in all_pit:
        if sym in existing:
            audit["symbols"][sym] = {
                "status": "already_local",
                "datasetId": existing[sym]["datasetId"],
                "firstSession": existing[sym]["firstSession"],
                "lastSession": existing[sym]["lastSession"],
            }
            continue
        prev = audit["symbols"].get(sym)
        if prev and prev.get("status") in ("imported", "no_alpaca_data", "too_few_bars") and not retry_failed:
            continue
        todo.append(sym)

    if limit is not None:
        todo = todo[:int(limit)]

    if not todo:
        audit["updatedAt"] = datetime.now(UTC).isoformat()
        audit["summary"] = dict(Counter(v["status"] for v in audit["symbols"].values()))
        audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
        return audit

    key, secret = alpaca.credentials()
    client = Client(key, secret, budget=180)
    t0 = time.monotonic()

    def _one(sym):
        meta = pit.symbols[sym]
        # Need >=320d warmup before firstDate (clamped to 2016-01-04) and +180d after lastDate for exit paths
        first_d = date.fromisoformat(meta["firstDate"])
        last_d = date.fromisoformat(meta["lastDate"])
        start_day = max(date(2016, 1, 4), first_d - timedelta(days=400)).isoformat()
        end_day = min(date(2026, 10, 29), last_d + timedelta(days=180)).isoformat()
        # Try with historical `asof` first; if delisted ticker returns empty, fallback without `asof`
        asof_day = meta.get("asofDate")
        try:
            fine = _fetch_symbol_5m_sip(client, sym, start_day, end_day, asof_day)
            used_asof = asof_day
            if not fine and asof_day:
                # Some acquired/delisted tickers only match with an earlier asof inside their active window
                mid_day = (first_d + (last_d - first_d) // 2).isoformat()
                fine = _fetch_symbol_5m_sip(client, sym, start_day, end_day, mid_day)
                used_asof = mid_day
            if not fine and asof_day:
                fine = _fetch_symbol_5m_sip(client, sym, start_day, end_day, None)
                used_asof = None
            if not fine:
                return sym, {"status": "no_alpaca_data", "asofTried": asof_day, "pitRange": [meta["firstDate"], meta["lastDate"]]}
            sources, quality = resample_regular(fine)
            if any(len(rows) < 3 for rows in sources.values()):
                return sym, {"status": "too_few_bars", "fineBars": len(fine), "pitRange": [meta["firstDate"], meta["lastDate"]]}
            material = {
                tf: (
                    rows,
                    {
                        "feed": "sip",
                        "adjustment": "split",
                        "normalization": NORMALIZATION,
                        "mode": "pit-historical-sip-import",
                        "asofUsed": used_asof,
                        "rthQuality": quality,
                        "count": len(rows),
                        "first": rows[0].time,
                        "last": rows[-1].time,
                        "lastClose": rows[-1].end,
                    },
                )
                for tf, rows in sources.items()
            }
            ds_id = save_dataset(
                sym,
                material,
                feed="sip",
                adjustment="split",
                session="XNYS regular; open-anchored buckets; final 4h bucket may be shorter; execution 5m",
            )
            first_sess = datetime.fromtimestamp(sources["1D"][0].time, timezone.utc).date().isoformat()
            last_sess = datetime.fromtimestamp(sources["1D"][-1].time, timezone.utc).date().isoformat()
            return sym, {
                "status": "imported",
                "datasetId": ds_id,
                "asofUsed": used_asof,
                "firstSession": first_sess,
                "lastSession": last_sess,
                "bars5m": len(sources["5m"]),
                "bars4h": len(sources["4h"]),
                "pitRange": [meta["firstDate"], meta["lastDate"]],
            }
        except (DataError, OSError, ValueError) as exc:
            return sym, {"status": "error", "error": str(exc), "asofTried": asof_day}

    try:
        done = 0
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = {pool.submit(_one, sym): sym for sym in todo}
            for fut in as_completed(futs):
                sym, rec = fut.result()
                done += 1
                audit["symbols"][sym] = rec
                if progress:
                    progress(done, len(todo), sym, rec)
                if done % 15 == 0 or done == len(todo):
                    audit["updatedAt"] = datetime.now(UTC).isoformat()
                    audit["summary"] = dict(Counter(v["status"] for v in audit["symbols"].values()))
                    tmp = audit_path.with_suffix(".tmp")
                    tmp.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
                    tmp.replace(audit_path)
    finally:
        client.close()

    audit["elapsedSeconds"] = round(time.monotonic() - t0, 1)
    audit["summary"] = dict(Counter(v["status"] for v in audit["symbols"].values()))
    tmp = audit_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(audit_path)
    return audit
