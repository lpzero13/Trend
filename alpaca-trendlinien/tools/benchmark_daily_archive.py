
"""Compare old and incremental archive runs on deterministic offline XNYS fixtures."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1]
START, ANCHOR = "2016-01-04", "2026-11-23"
SYMBOLS = ["FXA", "FXB", "FXC"]
SCENARIOS = {
    "one_session": (SYMBOLS[:1], "2026-11-24"),
    "three_symbols": (SYMBOLS, "2026-11-24"),
    "three_sessions": (SYMBOLS[:1], "2026-11-27"),
}


def fixture(day, index):
    import math
    from lab_data import session_bounds
    from models import Bar
    opened, closed = session_bounds(day)
    result = []
    for stamp in range(opened, closed, 300):
        phase = (stamp - 1450000000) / 86400
        price = round(76 + 32 * math.sin(phase / 150) + 6 * math.sin(phase / 10)
                      + math.sin(phase * 1.7) + index * 12 + phase / 256, 4)
        result.append(Bar(stamp, stamp + 300, price, price + .35, price - .23, price + .04,
                          float((stamp // 300 * 249731 + index * 43291) % 107233 + 10)))
    return result


def seed(root):
    sys.path.insert(0, str(APP))
    from archive_state import put
    from database import connection
    from datasets import save_dataset
    from lab_data import NORMALIZATION, resample_regular
    from lab_splits import sessions_between
    os.environ["TORI_DATA_DIR"] = str(root)
    identities = {}
    days = sessions_between(START, ANCHOR)
    for index, symbol in enumerate(SYMBOLS):
        bars = [bar for day in days for bar in fixture(day, index)]
        frames, quality = resample_regular(bars)
        sources = {tf: (rows, {"normalization": NORMALIZATION, "rthQuality": quality, "count": len(rows),
                                "first": rows[0].time, "last": rows[-1].time, "lastClose": rows[-1].end})
                   for tf, rows in frames.items()}
        identities[symbol] = save_dataset(symbol, sources, feed="sip", adjustment="split", session="XNYS regular")
    with connection() as db:
        put(db, "universe:v1:sp500", {"asOf": ANCHOR, "members": [{"symbol": symbol} for symbol in SYMBOLS]})
    return {"sessions": len(days), "fineBarsPerSymbol": len(bars), "symbols": identities,
            "kind": "synthetic OHLCV; no provider access"}


class OfflineClient:
    attempts = 0

    def request(self, params):
        self.attempts += 1
        day = params["start"][:10]
        bars = {}
        for symbol in params["symbols"].split(","):
            bars[symbol] = [dict(t=datetime.fromtimestamp(b.time, timezone.utc).isoformat(),
                                 o=b.open, h=b.high, l=b.low, c=b.close, v=b.volume)
                            for b in fixture(day, SYMBOLS.index(symbol))]
        return {"bars": bars, "next_page_token": None}

    def close(self):
        pass

    def snapshot(self):
        return {"attempts": self.attempts}


def io_counters():
    path = Path("/proc/self/io")
    return {key: int(value) for key, value in
            (line.split(":") for line in path.read_text().splitlines())} if path.exists() else {}


def memory_counters():
    # VmHWM is the current program's high-water mark. getrusage().ru_maxrss
    # can carry the launching image's high-water mark through exec on Linux.
    status = Path("/proc/self/status").read_text().splitlines()
    peak = next(int(line.split()[1]) for line in status if line.startswith("VmHWM:"))
    cgroup = Path("/sys/fs/cgroup") / Path("/proc/self/cgroup").read_text().strip().split("::")[-1].lstrip("/")
    result = {"peakProcessRssKiB": peak}
    for name in ("memory.peak", "memory.swap.peak", "memory.max", "memory.swap.max"):
        path = cgroup / name
        if path.exists():
            value = path.read_text().strip()
            result[name] = int(value) if value.isdecimal() else value
    return result


def compare_files(before, after):
    new = after.keys() - before.keys()
    return {"filesWritten": len(new), "retainedBytes": sum(after[name] for name in new),
            "parquetWritten": sum(name.endswith(".parquet") for name in new),
            "parquetWrittenBytes": sum(after[name] for name in new if name.endswith(".parquet"))}


def child(args):
    if hasattr(os, "sched_getaffinity"):
        os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    sys.path.insert(0, args.code)
    import daily_archive
    import parquet_store
    from archive_state import put
    from database import connection
    from datasets import digest
    from settings import data_dir

    members, target = SCENARIOS[args.scenario]
    current = datetime.fromisoformat(target + "T23:00:00+00:00")
    root = data_dir()
    with connection() as db:
        put(db, "universe:v1:sp500", {"asOf": ANCHOR, "members": [{"symbol": s} for s in members]})
    raw_hash = parquet_store.checksum
    checked = 0

    def checksum(path):
        nonlocal checked
        checked += path.stat().st_size
        return raw_hash(path)

    parquet_store.checksum = checksum

    def files():
        return {path.name: path.stat().st_size
                for path in (root / "datasets").rglob("*") if path.is_file()}

    def measure(task):
        nonlocal checked
        checked = 0
        files_before, io_before = files(), io_counters()
        wall, cpu = time.perf_counter(), time.process_time()
        result = task()
        elapsed = {"wallSeconds": time.perf_counter() - wall, "cpuSeconds": time.process_time() - cpu}
        io_after = io_counters()
        return result, {**elapsed, **memory_counters(), **compare_files(files_before, files()),
                        "checksumReadBytes": checked, "processIo": {
                            key: io_after[key] - value for key, value in io_before.items()
                            if key in ("rchar", "wchar", "read_bytes", "write_bytes")}}

    extra = {"mode": "catchup", "max_sessions": 3} if args.new and args.scenario == "three_sessions" else {}

    def update():
        return daily_archive.update(["sp500"], now=current, workers=1, client_factory=OfflineClient, **extra)

    with patch("history_http.Client.request", side_effect=AssertionError("network disabled")):
        result, cold = measure(update)
        repeated, warm = measure(update)
        cold["fixtureRequests"] = result["alpaca"].get("attempts", 0)
        warm["fixtureRequests"] = repeated["alpaca"].get("attempts", 0)
        first_ids = {symbol: item["datasetId"] for symbol, item in result["symbols"].items()}
        assert first_ids == {symbol: item["datasetId"] for symbol, item in repeated["symbols"].items()}
        assert cold["fixtureRequests"] and not warm["fixtureRequests"] and not warm["filesWritten"]
        cold["reusedBlocks"] = sum(len(json.loads((root / "datasets" / (identity + ".json")).read_text())[
            "storage"]["blocks"]) for identity in first_ids.values()) - cold["parquetWritten"]
        read_metrics = {"coldUpdate": cold, "warmRepeat": warm, "externalProviderRequests": 0}

        if args.scenario == "three_symbols":
            from daily_review import run
            with patch("daily_review.make_plan", side_effect=lambda keys: daily_archive.make_plan(keys, current)):
                report, first_scan = measure(lambda: run(["sp500"], scan_only=True))
                repeated_report, second_scan = measure(lambda: run(["sp500"], scan_only=True))
            read_metrics.update(firstReview=first_scan, repeatReview=second_scan,
                                reviewCandidates=len(report["candidates"]),
                                cachedReview=repeated_report.get("cachedAnalysis", False))
            for candidate in report["candidates"]:
                del candidate["datasetId"]
                del candidate["chartPath"]
            review_hash = digest([report[k] for k in ("coverage", "candidates", "issues", "checkedSymbols")])
        else:
            review_hash = None

    # Validation is outside the measured worker, including cgroup limits.
    print(json.dumps({"metrics": read_metrics, "datasetIds": first_ids,
                      "reviewHash": review_hash, "target": target}))


def validate(root, results, comparison):
    from datasets import digest
    from parquet_store import hydrate
    for label, result in results.items():
        data_root = root / label
        hashes = {}
        for symbol, identity in result["datasetIds"].items():
            manifest = json.loads((data_root / "datasets" / (identity + ".json")).read_text())
            payload, weeks = hydrate(manifest, data_root, include_weekly=True)
            hashes[symbol] = digest([payload["material"]["bars"], weeks, payload["quality"]])
        if comparison is None:
            comparison = (hashes, result["reviewHash"])
        else:
            assert comparison == (hashes, result["reviewHash"]), (label, hashes)
    return comparison


def harness(args):
    with tempfile.TemporaryDirectory(prefix="tori-daily-benchmark-", dir=args.scratch) as folder:
        root = Path(folder)
        seed_data = seed(root / "seed")
        report = {"platform": platform.platform(), "python": sys.version, "allowedCpuCount": 1,
                  "fixture": {"start": START, "anchor": ANCHOR, "sessions": seed_data["sessions"],
                              "fineBarsPerSymbol": seed_data["fineBarsPerSymbol"], "symbols": SYMBOLS,
                              "kind": seed_data["kind"]},
                  "method": "fresh Python process per scenario and path; warm in-process repeat; OS page cache not purged",
                  "scenarios": {}}
        for name, (members, target) in SCENARIOS.items():
            results = {}
            case_root = root / name
            case_root.mkdir()
            variants = [("reference", args.baseline, args.comparison_cap_mib),
                        ("incremental", str(APP), args.comparison_cap_mib)]
            if args.cap_mib:
                variants.append(("incrementalLimited", str(APP), args.cap_mib))
            for label, code, cap in variants:
                destination = case_root / label
                shutil.copytree(root / "seed", destination, copy_function=os.link,
                                ignore=shutil.ignore_patterns("research"))
                command = [sys.executable, str(Path(__file__).resolve()), "--child", "--code", code, "--scenario", name]
                if label != "reference":
                    command.append("--new")
                if cap:
                    command = ["systemd-run", "--user", "--scope", "--quiet", "-p", f"MemoryMax={cap}M",
                               "-p", "MemorySwapMax=0", "--", *command]
                env = {**os.environ, "TORI_DATA_DIR": str(destination), "OPENBLAS_NUM_THREADS": "1",
                       "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}
                measured = subprocess.run(command, env=env, check=True, capture_output=True, text=True)
                results[label] = json.loads(measured.stdout)
                print(f"{name} {label}: {results[label]['metrics']['coldUpdate']['wallSeconds']:.2f}s",
                      file=sys.stderr, flush=True)
            hashes, review = validate(case_root, results, None)
            report["scenarios"][name] = {"symbols": members, "target": target, "exactFrameAndAuditHashes": hashes,
                                         "exactReviewHash": review,
                                         **{label: result["metrics"] for label, result in results.items()}}
            Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", help="Application directory of the baseline worktree")
    parser.add_argument("--output", help="Path for JSON measurements")
    parser.add_argument("--scratch", help="Parent directory for disposable benchmark data")
    parser.add_argument("--cap-mib", type=int, help="Additional limit for the optimized child in a Linux user scope")
    parser.add_argument("--comparison-cap-mib", type=int, help="Same limit for baseline and optimized children")
    parser.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--code", help=argparse.SUPPRESS)
    parser.add_argument("--scenario", choices=SCENARIOS, help=argparse.SUPPRESS)
    parser.add_argument("--new", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not sys.platform.startswith("linux"):
        parser.error("Run on Linux or WSL for /proc and cgroup measurements")
    if args.child:
        child(args)
    else:
        if not args.baseline or not args.output:
            parser.error("--baseline and --output are required")
        harness(args)
