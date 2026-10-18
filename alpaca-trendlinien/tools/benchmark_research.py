"""Offline P1 resource probe: isolated synthetic journals and a real fixture worker.

Run from the application folder: python tools/benchmark_research.py
No credentials, downloads, existing data directories or production jobs are used.
"""
import argparse
import ctypes
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import threading
import time
import tracemalloc
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]


def peak_rss_bytes():
    if os.name != "nt":
        import resource
        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(value if sys.platform == "darwin" else value * 1024)
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_ = [("cb",wintypes.DWORD),("PageFaultCount",wintypes.DWORD)] + [(key,ctypes.c_size_t) for key in
            ("PeakWorkingSetSize","WorkingSetSize","QuotaPeakPagedPoolUsage","QuotaPagedPoolUsage",
             "QuotaPeakNonPagedPoolUsage","QuotaNonPagedPoolUsage","PagefileUsage","PeakPagefileUsage")]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    kernel = ctypes.WinDLL("kernel32",use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi = ctypes.WinDLL("psapi",use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(counters),counters.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return counters.PeakWorkingSetSize


def journal_case(count):
    import jobs
    from research import causal_events
    from datasets import save_dataset, read_dataset
    from test_research import fixture_sources
    from server import Handler
    dataset = read_dataset(save_dataset("TEST",fixture_sources()))
    template = next(causal_events(dataset,900,first_index=850))
    identity = jobs.submit({})["id"]
    start = time.perf_counter()
    with jobs.connection() as db:
        db.executemany("INSERT INTO events VALUES(?,?,?,?)", ((identity,str(i),dataset["id"],
            json.dumps({**template,"id":str(i)})) for i in range(count)))
    seeded = time.perf_counter()-start
    class QuietHandler(Handler):
        def log_message(self,*args): pass
    server = ThreadingHTTPServer(("127.0.0.1",0),QuietHandler)
    thread = threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}"
    try:
        def fetch(query="limit=250"):
            with urllib.request.urlopen(url+f"/api/research/jobs/{identity}/events?"+query) as response:
                raw = response.read()
            return json.loads(raw),len(raw)
        baseline = peak_rss_bytes()
        tracemalloc.start()
        started = time.perf_counter()
        page,size = fetch()
        first_ms = (time.perf_counter()-started)*1000
        _,heap = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        total = len(page["items"])
        pages,max_size = 1,size
        while page["page"]["hasMore"]:
            page,size = fetch(urllib.parse.urlencode({"limit":250,"cursor":page["page"]["nextCursor"]}))
            total += len(page["items"])
            pages += 1
            max_size = max(max_size,size)
        elapsed = time.perf_counter()-started
        if total != count: raise AssertionError("Incomplete export")
        health_start=time.perf_counter()
        with urllib.request.urlopen(url+"/api/health") as response: json.load(response)
        return {"case":"synthetic_journal_http","events":count,"pages":pages,"pageLimit":250,
                "seedSeconds":seeded,"exportSeconds":elapsed,"firstPageMilliseconds":first_ms,
                "maxResponseBytes":max_size,"firstPagePythonPeakBytes":heap,
                "peakRssBeforePagingBytes":baseline,"peakRssBytes":peak_rss_bytes(),
                "healthMilliseconds":(time.perf_counter()-health_start)*1000,
                "databaseBytes":sum(p.stat().st_size for p in Path(os.environ["TORI_DATA_DIR"]).rglob("*.sqlite3*"))}
    finally:
        server.shutdown();server.server_close();thread.join()


def worker_case():
    import jobs
    from datasets import save_dataset
    from test_research import fixture_sources
    identity=save_dataset("TEST",fixture_sources())
    job=jobs.submit({"symbols":["TEST"],"samples":3,"dataset_ids":{"TEST":identity}})
    started=time.perf_counter()
    jobs.worker_loop(threading.Event(),once=True)
    job=jobs.get_job(job["id"])
    if job["status"]!="succeeded": raise AssertionError(job["status"])
    return {"case":"offline_fixture_worker","stocks":1,"sourceDays":800,"samples":3,
            "seconds":time.perf_counter()-started,"peakRssBytes":peak_rss_bytes(),
            "events":job["eventCount"],"completedTrials":job["completedTrials"]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case",choices=["journal","worker"])
    parser.add_argument("--count",type=int,default=10000)
    args=parser.parse_args()
    if args.case:
        if not 1<=args.count<=1000000: parser.error("count must be 1..1000000")
        with tempfile.TemporaryDirectory(prefix="tori-benchmark-") as folder:
            os.environ.update(TORI_DATA_DIR=folder,TORI_AUTO_ENABLED="0")
            result=journal_case(args.count) if args.case=="journal" else worker_case()
        print(json.dumps(result))
    else:
        results=[]
        for mode,count in [("journal",10000),("journal",50000),("journal",100000),("worker",1)]:
            result=subprocess.check_output([sys.executable,__file__,"--case",mode,"--count",str(count)],cwd=ROOT,
                creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            results.append(json.loads(result))
        print(json.dumps({"python":platform.python_version(),"platform":platform.platform(),
                          "synthetic":True,"productionCapacityProven":False,"measurements":results},indent=2))


if __name__ == "__main__": main()
