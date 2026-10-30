"""Offline planning estimates from the documented five-stock cold benchmark.

Not a guarantee or a statistical confidence interval. In particular a Windows
measurement does not benchmark a Proxmox container or a small-cap universe.
"""
from datetime import datetime, timedelta, timezone
import math

from history_archive import stamp
from models import DataError

CALIBRATION = {
    'version': 'archive-throughput-20261029-v1',
    'measuredAt': '2026-10-29',
    'start': '2016-01-01T00:00:00+00:00',
    'end': '2026-10-29T15:25:47+00:00',
    'benchmarkStocks': ['AAPL', 'GS', 'KO', 'BNY', 'SNDK'],
    'planningStocks': ['AAPL', 'GS', 'KO', 'BNY'],
    'sampleDays': 3954.6429050925926,
    'measuredColdSeconds': 237.2379571000347,
    'measuredColdPages': 598,
    'longHistoryPagesPerStock': 140.,
    'longHistorySecondsPerStock': 55.540658852850925,
    'longHistoryDatasetBytesPerStock': 4897436.5,
    'longHistoryCheckpointBytesPerStock': 3881993.75,
    'environment': 'Local Windows, 8 download workers, budget 190/min, SIP/split; no cache hits',
}


def estimate(stocks, start=None, end=None, request_budget=190):
    if type(stocks) is not int or not 0 <= stocks <= 20000:
        raise DataError('Ungültige Aktienzahl für Schätzung.',400)
    if type(request_budget) is not int or not 1<=request_budget<=190:
        raise DataError('Ungültiges Abrufbudget für Schätzung.',400)
    try:
        start_at=stamp(start or CALIBRATION['start'])
        end_at=stamp(end) if end else datetime.now(timezone.utc)-timedelta(minutes=16)
    except (ValueError,TypeError,AttributeError):
        raise DataError('Ungültiger Schätzzeitraum.',400) from None
    if start_at>=end_at:raise DataError('Schätzbeginn muss vor dem Ende liegen.',400)
    if start_at<stamp(CALIBRATION['start']):raise DataError('Alpaca-Hochrechnung beginnt frühestens 2016.',400)
    days=(end_at-start_at).total_seconds()/86400
    scale=days/CALIBRATION['sampleDays']
    seconds=stocks*max(1.,CALIBRATION['longHistorySecondsPerStock']*scale)*190/request_budget
    dataset=math.ceil(stocks*CALIBRATION['longHistoryDatasetBytesPerStock']*scale)
    checkpoints=math.ceil(stocks*CALIBRATION['longHistoryCheckpointBytesPerStock']*scale)
    return {'stocks':stocks,'start':start_at.isoformat(),'end':end_at.isoformat(),'days':round(days,2),
            'seconds':round(seconds,1),'lowSeconds':round(seconds*.7,1),'highSeconds':round(seconds*1.4,1),
            'datasetBytes':dataset,'checkpointBytes':checkpoints,'combinedBytes':dataset+checkpoints,
            'estimatedPages':math.ceil(stocks*CALIBRATION['longHistoryPagesPerStock']*scale),
            'calibration':CALIBRATION['version'],'sampleEnvironment':CALIBRATION['environment'],
            'requestBudget':request_budget,'rateAssumption':'Conservative proportional scaling below measured 190/min setting.',
            'basis':'Cold first import; long-history stock model. Existing-stock hints are not subtracted.',
            'uncertainty':'0.7–1.4 planning factor, not a confidence interval. Container, latency, data density, listing age and retries may change duration.',
            'storageScope':'Published Parquet/manifest plus monthly checkpoint files. Excludes operational SQLite, logs, backups, other existing data and temporary/free-space reserve.'}
