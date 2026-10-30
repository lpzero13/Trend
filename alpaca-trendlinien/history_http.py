"""Fixed-host, read-only Alpaca HTTP sessions, one connection per worker thread."""
import http.client
import json
import threading
import time
from urllib.parse import urlencode
from models import DataError
from provider_budget import wait, cooldown


class Client:
    def __init__(self, key, secret, budget=190):
        self.key, self.secret = key, secret
        self.budget = budget
        self.interrupted = None
        self.local = threading.local()
        self.lock = threading.Lock()
        self.connections = []
        self.metrics = {'attempts': 0, 'pages': 0, 'waitSeconds': 0., 'httpSeconds': 0., 'retries': 0, 'bytes': 0}

    def record(self, **values):
        with self.lock:
            for key, value in values.items(): self.metrics[key] += value

    def snapshot(self):
        with self.lock: return dict(self.metrics)

    def close(self):
        for connection in self.connections:
            try: connection.close()
            except OSError: pass

    def request(self, params):
        for attempt in range(4):
            started = time.perf_counter(); wait(self.budget, self.interrupted)
            if self.interrupted and self.interrupted(): raise InterruptedError()
            self.record(waitSeconds=time.perf_counter()-started, attempts=1, retries=bool(attempt))
            connection = getattr(self.local, 'connection', None)
            if connection is None:
                connection = http.client.HTTPSConnection('data.alpaca.markets', timeout=35)
                self.local.connection = connection
                with self.lock: self.connections.append(connection)
            started = time.perf_counter()
            try:
                connection.request('GET', '/v2/stocks/bars?'+urlencode(params), headers={
                    'APCA-API-KEY-ID': self.key, 'APCA-API-SECRET-KEY': self.secret,
                    'Accept': 'application/json', 'User-Agent': 'Tori-History/2'})
                response = connection.getresponse()
                raw = response.read()
                self.record(httpSeconds=time.perf_counter()-started, bytes=len(raw))
                if response.status == 200:
                    result = json.loads(raw)
                    self.record(pages=1)
                    return result
                if response.status == 429:
                    try: seconds = float(response.getheader('Retry-After', '60'))
                    except ValueError: seconds = 60
                    cooldown(seconds)
                if response.status not in (429, 500, 502, 503, 504) or attempt == 3:
                    raise DataError(f'Alpaca-Historienabruf fehlgeschlagen (HTTP {response.status}).', 502)
            except (OSError, http.client.HTTPException, json.JSONDecodeError):
                connection.close(); self.local.connection = None
                if attempt == 3: raise DataError('Alpaca-Historienverbindung unterbrochen.', 502) from None
            time.sleep(min(3, 1+attempt))
        raise DataError('Alpaca-Historienabruf fehlgeschlagen.', 502)
