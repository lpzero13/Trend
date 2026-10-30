"""Read-only local fan catalog and immutable case chart, sharing existing auth."""
from datetime import datetime, timezone
import json
import re

from database import connection
from datasets import chart_dataset, data_kind
from fan_chart import apply, selected_engine
from lab_data import NORMALIZATION
from models import DataError
from settings import data_dir
from snapshots import remember
from weekly_chart import CHART_TIMEFRAMES, add_weekly


def catalog():
    items = []
    for file in (data_dir()/"datasets").glob("*.json"):
        if file.is_symlink() or not re.fullmatch(r"[a-f0-9]{64}\.json", file.name):
            continue
        try:
            d = json.loads(file.read_text("utf-8"))
            m = d["material"]
            if not all(m.get("normalization", {}).get(tf) == NORMALIZATION for tf in ("5m", "1h", "4h", "1D")):
                continue
            items.append({"id": d["id"], "symbol": m["symbol"], "feed": m["feed"],
                          "adjustment": m["adjustment"], "dataKind": data_kind(d),
                          "importedAt": d["importedAt"]})
        except (OSError, KeyError, ValueError, TypeError):
            continue
    return {"items": sorted(items, key=lambda x: (x["symbol"], x["feed"], x["importedAt"]), reverse=False),
            "providerCalls": 0, "meaning": "Nur vorhandene reguläre 5m-Datasets; gleicher Kursbestand für Signale und Ausführung. Historische Universumsmitgliedschaft nicht garantiert."}


def case_for(job_id, case_id):
    from jobs import get_job
    job = get_job(job_id, include_plans=False)
    if job["spec"].get("entry_mode") != "fan" or not isinstance(case_id, str) or not re.fullmatch(r"[a-f0-9]{64}", case_id):
        raise DataError("Ungültiger Fächerfall.", 400)
    with connection() as db:
        row = db.execute("SELECT result FROM trials WHERE job_id=? AND id=?", (job_id, case_id)).fetchone()
    if row is None:
        raise DataError("Fächerfall nicht gefunden.", 404)
    case = json.loads(row[0])
    if case.get("kind") != "entry":
        raise DataError("Bitte einen Fächer-Einstiegsfall auswählen.", 400)
    return job, case


def get(path, query):
    def q(name, default=None):
        values = query.get(name, [default])
        if len(values) != 1:
            raise DataError("Parameter mehrfach angegeben.", 400)
        return values[0]
    if path == "/api/fan/datasets":
        return catalog()
    if path == "/api/fan/chart":
        tf, dataset = q("timeframe", "4h"), q("dataset", "")
        if tf not in CHART_TIMEFRAMES:
            raise DataError("Ungültiges Fächer-Chartintervall.", 400)
        job, case, config = None, None, None
        if q("fan_job") or q("fan_case"):
            job, case = case_for(q("fan_job"), q("fan_case"))
            config = job["spec"]["fan"]
            if dataset != case["datasetId"]:
                raise DataError("Fächerfall gehört zu einem anderen Datenbestand.", 400)
        asof = q("asof") or (datetime.fromtimestamp(case["signal"]["signalAt"], timezone.utc).isoformat() if case else None)
        if asof is not None:
            from random_replay import cutoff as parse_at
            at = parse_at(asof, 0)
            if case is not None and at > case["cutoff"]:
                raise DataError("Ende des freigegebenen Forschungsverlaufs; der Holdout bleibt geschlossen.", 404)
            asof = datetime.fromtimestamp(at, timezone.utc).isoformat()
        payload = chart_dataset(dataset, "1D" if tf == "1W" else tf, asof, include_analysis=False)
        add_weekly(payload, tf)
        payload["sources"] = {k: {name: meta[name] for name in ("count", "first", "last", "lastClose", "normalization", "mode", "cached") if name in meta}
                              for k, meta in payload["sources"].items()}
        engine = selected_engine(query)
        if engine == "legacy":
            engine = "fan_"+(case["geometry"] if case else "extreme")
        analysis = q("analysis", "1")
        if analysis not in ("0", "1"):
            raise DataError("Analyse mit analysis=0 oder analysis=1 auswählen.", 400)
        if analysis == "1":
            apply(payload, engine, config=config, case=case)
            remember(payload)
        return payload
    raise DataError("Unbekannte Fächerroute.", 404)
