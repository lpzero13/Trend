"""HTTP API handlers for /api/radar/* (daily Top-10 scanner, Watchlist & 1.000-EUR papertrades).

Strictly offline: reads local SIP datasets in TORI_DATA_DIR, never calls Alpaca
or external hosts, never places broker orders.
"""
from hermes_scanner import SCENARIO_GROUPS, scan_universe, write_outputs
from models import DataError
import tori_paper_watch as pw


def _first(query, key, default=None):
    values = query.get(key)
    return values[0] if values else default


def get(path, query):
    if path == "/api/radar/state":
        scan = pw.load_latest_scan()
        return {
            "scan": scan,
            "watchlist": pw.list_items(include_archived=_first(query, "archived") == "1"),
            "updates": pw.recent_updates(limit=int(_first(query, "limit", "40"))),
            "summary": pw.portfolio_summary(),
        }
    if path == "/api/radar/watchlist":
        return {
            "items": pw.list_items(include_archived=_first(query, "archived") == "1"),
            "summary": pw.portfolio_summary(),
        }
    if path == "/api/radar/updates":
        item_id = _first(query, "itemId")
        limit = max(1, min(200, int(_first(query, "limit", "50"))))
        return {"items": pw.recent_updates(limit=limit, item_id=item_id)}
    raise DataError("Unbekannter Radar-Endpunkt.", 404)


def post(path, body):
    if not isinstance(body, dict):
        raise DataError("JSON-Objekt erwartet.", 400)

    if path == "/api/radar/scan":
        universe = str(body.get("universe") or "all")
        if universe not in ("all", "dow30", "nasdaq100", "sp500"):
            raise DataError("Ungültiges Universum.", 400)
        scenario = str(body.get("scenario") or "all")
        if scenario not in SCENARIO_GROUPS:
            raise DataError("Ungültiges Szenario.", 400)
        session = str(body.get("session") or "latest")
        min_score = int(body.get("minScore", 0))
        top_n = max(1, min(50, int(body.get("topN", 10))))
        quality_filter = str(body.get("qualityFilter") or "all")
        if quality_filter not in ("all", "focus", "quiet", "core", "tier_c"):
            raise DataError("Ungültiger Qualitäts-Filter.", 400)
        include_bounce = bool(body.get("includeSafetyBounce", False))
        report = scan_universe(
            universe=universe,
            session=session,
            scenario=scenario,
            min_score=min_score,
            top_n=top_n,
            quality_filter=quality_filter,
            include_safety_bounce=include_bounce,
        )
        write_outputs(report, store_latest=True)
        return {"scan": report}

    if path == "/api/radar/watchlist/add":
        symbol = str(body.get("symbol") or "").upper().strip()
        candidate = body.get("candidate")
        if candidate is None:
            if not symbol:
                raise DataError("Symbol oder Kandidat erforderlich.", 400)
            scan = pw.load_latest_scan()
            if not scan:
                raise DataError("Kein aktueller Scan vorhanden. Bitte zuerst den Tages-Scan ausführen.", 404)
            pool = (scan.get("candidates") or []) + (scan.get("fastAPlus") or [])
            candidate = next((c for c in pool if c["symbol"] == symbol), None)
            if candidate is None:
                raise DataError(f"{symbol} ist im aktuellen Scan nicht als Kandidat enthalten.", 404)
        capital = float(body.get("capitalEur", pw.DEFAULT_CAPITAL_EUR))
        stop_policy = str(body.get("stopPolicy") or pw.DEFAULT_STOP_POLICY)
        max_watch = int(body.get("maxWatchSessions", 20))
        note = str(body.get("note") or "")
        result = pw.add_candidate(
            candidate,
            capital_eur=capital,
            stop_policy=stop_policy,
            max_watch_sessions=max_watch,
            note=note,
        )
        # Immediately run one causal evaluation up to the latest local dataset bar
        eval_res = pw.evaluate_all()
        items = pw.list_items()
        refreshed = next((it for it in items if it["id"] == result["item"]["id"]), result["item"])
        return {
            **result,
            "item": refreshed,
            "watchlist": items,
            "summary": eval_res["summary"],
            "updates": pw.recent_updates(limit=40),
        }

    if path == "/api/radar/watchlist/evaluate":
        asof_session = body.get("asofSession") or None
        eval_res = pw.evaluate_all(asof_session=asof_session)
        return {
            **eval_res,
            "watchlist": pw.list_items(),
            "updates": pw.recent_updates(limit=40),
        }

    if path == "/api/radar/watchlist/note":
        item_id = str(body.get("id") or "")
        item = pw.update_note(item_id, body.get("note") or "")
        return {"item": item, "watchlist": pw.list_items()}

    if path == "/api/radar/watchlist/archive":
        item_id = str(body.get("id") or "")
        item = pw.archive_item(item_id)
        return {
            "item": item,
            "watchlist": pw.list_items(),
            "summary": pw.portfolio_summary(),
            "updates": pw.recent_updates(limit=40),
        }

    if path == "/api/radar/watchlist/delete":
        item_id = str(body.get("id") or "")
        deleted = pw.delete_item(item_id)
        return {
            **deleted,
            "watchlist": pw.list_items(),
            "summary": pw.portfolio_summary(),
            "updates": pw.recent_updates(limit=40),
        }

    raise DataError("Unbekannter Radar-Endpunkt.", 404)
