"""Loopback-only server for the Alpaca trendline prototype (Python 3.11+)."""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import os
import base64
import secrets
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from alpaca import DataError, ROOT, TIMEFRAMES, NY, credentials, load_bars, next_bar_close
from trendlines import RULES_VERSION, analyze
from assets import search_assets, cached_asset_name
from analysis_service import build_chart
from datasets import chart_dataset, read_dataset, source_bars
import jobs
from snapshots import remember, save_snapshot, read_snapshot, list_snapshots

APP_ID = "tori-alpaca-local"
COMPANIES = {"AAPL": "Apple Inc.", "MSFT": "Microsoft Corporation", "NVDA": "NVIDIA Corporation", "SPY": "SPDR S&P 500 ETF"}


def parse_cutoff(value: str, now: datetime) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            naive = parsed
            parsed = parsed.replace(tzinfo=NY)
            if parsed.astimezone(timezone.utc).astimezone(NY).replace(tzinfo=None) != naive:
                raise ValueError("Nonexistent local time")
            if parsed.replace(fold=1).utcoffset() != parsed.utcoffset():
                raise ValueError("Ambiguous local time")
        parsed = parsed.astimezone(timezone.utc)
        if parsed > now - timedelta(minutes=15):
            raise DataError("Der Analysezeitpunkt muss mindestens 15 Minuten zurückliegen.", 400)
        if parsed.year < 2000:
            raise DataError("Bitte einen Analysezeitpunkt ab dem Jahr 2000 wählen; die tatsächliche Datenverfügbarkeit hängt von Alpaca ab.", 400)
        return parsed
    except (ValueError, TypeError):
        raise DataError("Ungültiger oder durch die Zeitumstellung mehrdeutiger Analysezeitpunkt (New York).", 400) from None


def chart_payload(symbol: str, timeframe: str, force: bool = False, as_of: str | None = None) -> dict:
    if timeframe not in TIMEFRAMES:
        raise DataError("Erlaubte Intervalle: 1h, 4h und 1D.", 400)
    if not re.fullmatch(r"[A-Z][A-Z0-9./-]{0,29}", symbol):
        raise DataError("Bitte ein gültiges US-Symbol eingeben.", 400)
    now = datetime.now(timezone.utc)
    cutoff = parse_cutoff(as_of, now) if as_of else now - timedelta(minutes=15)
    with ThreadPoolExecutor(max_workers=3) as pool:
        kwargs = {"force":force, "now":now}
        if as_of:
            kwargs["end"] = cutoff
        futures = {tf: pool.submit(load_bars, symbol, tf, **kwargs) for tf in TIMEFRAMES}
        datasets = {tf: future.result() for tf, future in futures.items()}
    result = build_chart(datasets, symbol, timeframe, cutoff, now, historical=bool(as_of))
    remember(result)
    return result


def step_payload(symbol, timeframe, as_of, direction):
    if timeframe not in TIMEFRAMES or not re.fullmatch(r"[A-Z][A-Z0-9./-]{0,29}",symbol):
        raise DataError("Ungültige Aktie oder Intervall.",400)
    if direction not in ("back","next"):
        raise DataError("Ungültige Schrittrichtung.",400)
    now=datetime.now(timezone.utc)
    cutoff=parse_cutoff(as_of,now)
    if direction=="back":
        bars,_=load_bars(symbol,timeframe,now=now,end=cutoff)
        bars=[b for b in bars if b.end<=cutoff.timestamp()]
        if len(bars)<2:raise DataError("Keine vorherige Kerze verfügbar.",404)
        target=bars[-2].end
    else:
        target=next_bar_close(symbol,timeframe,cutoff,now=now)
    return {"closedAt":target,"asof":datetime.fromtimestamp(target,timezone.utc).isoformat(),"timeframe":timeframe}


class Handler(BaseHTTPRequestHandler):
    server_version = "ToriLocal/0.1"

    def log_message(self, fmt, *args):
        # Never log request headers, provider responses or credential files.
        print(f"{self.address_string()} {self.command} {urlparse(self.path).path}", flush=True)

    def send_bytes(self, body: bytes, status: int, content_type: str):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store" if self.path.startswith("/api/") else "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload: dict, status=200):
        self.send_bytes(json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8"), status, "application/json; charset=utf-8")

    def allowed_hosts(self):
        return {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"} | set(getattr(self.server,"allowed_hosts",()))

    def authorized(self):
        token=getattr(self.server,"api_token","")
        if not token:
            return True
        authorization=self.headers.get("Authorization","")
        supplied=""
        if authorization.startswith("Bearer "):
            supplied=authorization[7:]
        elif authorization.startswith("Basic "):
            try:
                supplied=base64.b64decode(authorization[6:],validate=True).decode().split(":",1)[1]
            except (ValueError,IndexError,UnicodeError):
                pass
        if supplied and secrets.compare_digest(supplied.encode(),token.encode()):
            return True
        self.send_response(401)
        self.send_header("WWW-Authenticate",'Basic realm="Tori", charset="UTF-8"')
        self.send_header("Content-Length","0")
        self.end_headers()
        return False

    def do_GET(self):
        allowed = self.allowed_hosts()
        if self.headers.get("Host", "") not in allowed:
            return self.send_json({"error": "Nur lokale Zugriffe sind erlaubt."}, 403)
        origin = self.headers.get("Origin")
        if origin and origin not in {scheme+host for scheme in ("http://","https://") for host in allowed}:
            return self.send_json({"error": "Unerlaubter Ursprung."}, 403)
        if not self.authorized():
            return
        path = urlparse(self.path).path
        try:
            if path == "/api/health":
                from operations import status
                try:
                    credentials()
                    configured = True
                except DataError:
                    configured = False
                return self.send_json({"app": APP_ID, "credentialsConfigured": configured,
                                       "rulesVersion": RULES_VERSION, "readOnly": True,
                                       "marketDataReadOnly": True, "localSnapshots": True,
                                       "research":True,"studyVersion":jobs.STUDY_VERSION,
                                       "operations":status()})
            if path == "/api/research/jobs":
                from operations import status
                operational = status()
                return self.send_json({"items":jobs.list_jobs(),"schedule":jobs.schedule(),"workerActive":operational["worker"]["lockHeld"],"operations":operational})
            if path == "/api/research/schedule":
                return self.send_json(jobs.schedule())
            if path.startswith("/api/research/jobs/"):
                parts=path.split("/")
                if len(parts)==5:
                    return self.send_json(jobs.get_job(parts[4]))
                if len(parts)==6 and parts[5] in ("report","events"):
                    query=parse_qs(urlparse(self.path).query)
                    return self.send_json(jobs.report(parts[4],int(query.get("offset",["0"])[0]),int(query.get("limit",["250"])[0])) if parts[5]=="report" else jobs.events_for(parts[4],int(query.get("limit",["250"])[0]),query.get("cursor",[None])[0]))
                raise DataError("Unbekannte Forschungsroute.",404)
            if path == "/api/dataset-chart":
                query=parse_qs(urlparse(self.path).query)
                setup=None
                dataset_id=query.get("dataset",[""])[0]
                if "job" in query and "trial" in query:
                    trial,setup=jobs.get_trial(query["job"][0],query["trial"][0],query.get("variant",["breakout"])[0])
                    if trial["datasetId"]!=dataset_id:
                        raise DataError("Forschungsfall gehört zu einem anderen Dataset.",400)
                return self.send_json(chart_dataset(dataset_id,query.get("timeframe",["4h"])[0],query.get("asof",[None])[0],setup))
            if path == "/api/chart":
                query = parse_qs(urlparse(self.path).query)
                return self.send_json(chart_payload(query.get("symbol", ["AAPL"])[0].strip().upper(),
                                                    query.get("timeframe", ["4h"])[0],
                                                    query.get("refresh", ["0"])[0] == "1",
                                                    query.get("asof", [None])[0]))
            if path == "/api/step":
                query=parse_qs(urlparse(self.path).query)
                if "dataset" in query:
                    from bisect import bisect_left, bisect_right
                    tf=query.get("timeframe",[""])[0]
                    direction=query.get("direction",[""])[0]
                    if tf not in TIMEFRAMES or direction not in ("back","next"):
                        raise DataError("Ungültiger Dataset-Schritt.",400)
                    at=datetime.fromisoformat(query.get("asof",[""])[0].replace("Z","+00:00"))
                    if at.tzinfo is None: raise DataError("Zeitzone fehlt.",400)
                    closes=[b.end for b in source_bars(read_dataset(query["dataset"][0]))[tf]]
                    i=bisect_right(closes,at.timestamp()) if direction=="next" else bisect_left(closes,at.timestamp())-1
                    if not 0<=i<len(closes): raise DataError("Keine weitere Dataset-Kerze verfügbar.",404)
                    return self.send_json({"closedAt":closes[i],"asof":datetime.fromtimestamp(closes[i],timezone.utc).isoformat(),"timeframe":tf})
                return self.send_json(step_payload(query.get("symbol",[""])[0].upper(),
                    query.get("timeframe",[""])[0],query.get("asof",[""])[0],query.get("direction",[""])[0]))
            if path == "/api/snapshots":
                query = parse_qs(urlparse(self.path).query)
                symbol = query.get("symbol", [""])[0].upper()
                if not re.fullmatch(r"[A-Z][A-Z0-9./-]{0,29}", symbol):
                    raise DataError("Ungültiges Symbol.", 400)
                return self.send_json({"items":list_snapshots(symbol)})
            if path.startswith("/api/snapshots/"):
                return self.send_json(read_snapshot(path.rsplit("/", 1)[-1]))
            if path == "/api/assets":
                query = parse_qs(urlparse(self.path).query, keep_blank_values=True)
                try:
                    offset = max(0, min(100000, int(query.get("offset", ["0"])[0])))
                except ValueError:
                    raise DataError("Ungültige Seitennummer.", 400)
                symbols = set(query["symbols"][0].split(",")) if "symbols" in query else None
                return self.send_json(search_assets(query.get("q", [""])[0][:100],
                    query.get("exchange", [""])[0], offset, symbols))
            files = {
                "/": "index.html", "/app.js": "app.js", "/style.css": "style.css",
                "/research": "research.html", "/research.js":"research.js", "/research.css":"research.css",
                "/drawings.js": "drawings.js",
                "/analysis.js": "analysis.js",
                "/measurements.js": "measurements.js", "/api.js": "api.js",
                "/vendor/lightweight-charts.js": "vendor/lightweight-charts.js",
                "/vendor/LICENSE": "vendor/LICENSE", "/vendor/NOTICE": "vendor/NOTICE",
            }
            if path not in files:
                return self.send_json({"error": "Nicht gefunden."}, 404)
            file = ROOT / "static" / files[path]
            content_type = mimetypes.guess_type(file.name)[0] or "text/plain"
            if file.suffix == ".js":
                content_type = "text/javascript"
            return self.send_bytes(file.read_bytes(), 200, content_type + "; charset=utf-8")
        except DataError as exc:
            self.send_json({"error": str(exc)}, exc.status)
        except (ValueError,TypeError):
            self.send_json({"error":"Ungültige Anfrageparameter."},400)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            self.send_json({"error": "Die Anfrage konnte nicht abgeschlossen werden. Bitte den lokalen Server neu starten."}, 500)

    def do_POST(self):
        path=urlparse(self.path).path
        research=path in ("/api/research/jobs","/api/research/schedule") or (path.startswith("/api/research/jobs/") and path.endswith("/cancel"))
        if path != "/api/snapshots" and not research:
            return self.send_json({"error": "Schreibzugriffe sind nur zum lokalen Speichern eines Analysestands vorgesehen."}, 405)
        allowed = self.allowed_hosts()
        machine=bool(getattr(self.server,"api_token","") and self.headers.get("Authorization","").startswith("Bearer "))
        origin=self.headers.get("Origin")
        valid_origins={scheme+host for scheme in ("http://","https://") for host in allowed}
        if self.headers.get("Host") not in allowed or (origin not in valid_origins and not (machine and origin is None)):
            return self.send_json({"error":"Lokaler Ursprung erforderlich."}, 403)
        if not self.authorized():
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > (65536 if research else 1024) or self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                raise DataError("Ungültige Speicheranfrage.", 400)
            body = json.loads(self.rfile.read(length))
            if research:
                if path == "/api/research/jobs":
                    return self.send_json(jobs.submit(body),202)
                if path == "/api/research/schedule":
                    return self.send_json(jobs.schedule(body))
                return self.send_json(jobs.cancel(path.split("/")[4]))
            return self.send_json(save_snapshot(body.get("analysisId", "")), 201)
        except DataError as exc:
            self.send_json({"error":str(exc)}, exc.status)
        except (ValueError, TypeError, AttributeError):
            self.send_json({"error":"Ungültige Speicheranfrage."}, 400)
        except OSError:
            self.send_json({"error":"Der Stand konnte nicht auf dem Rechner gespeichert werden. Bitte Speicherplatz und Schreibrechte prüfen."}, 500)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", default=os.environ.get("TORI_BIND","127.0.0.1"))
    parser.add_argument("--allowed-host", action="append", default=[])
    parser.add_argument("--no-worker", action="store_true",help="Nur Webansicht; separaten Worker verwenden")
    args = parser.parse_args()
    token=os.environ.get("TORI_API_TOKEN","")
    if args.host not in ("127.0.0.1","localhost","::1") and (not token or not args.allowed_host):
        parser.error("Netzwerkbindung erfordert TORI_API_TOKEN und mindestens einen --allowed-host HOST:PORT.")
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.allowed_hosts=args.allowed_host
    server.api_token=token
    worker=None
    if not args.no_worker:
        if os.environ.get("TORI_AUTO_ENABLED","1") == "1":
            jobs.ensure_default_schedule()
        worker=jobs.start_worker()
    print(f"Tori Alpaca · Local: http://127.0.0.1:{args.port}", flush=True)
    print("Read-only market data. Stop with Ctrl+C.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if worker:
            worker[0].set()
            worker[1].join(timeout=5)
        server.server_close()


if __name__ == "__main__":
    main()
