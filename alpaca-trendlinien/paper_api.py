"""Paper status and journal are read-only; POST commands use the server's origin policy."""
import csv
from io import StringIO

from models import DataError
from paper_engine import MODEL
from paper_store import command, create_account, draft, events, plan_preview, status

COMMANDS = {"prepare", "activate", "cancel", "abandon", "exit", "resolve_stop", "resolve_target",
            "acknowledge_revision"}


def get(path, query):
    if path == "/api/paper/status":
        return status()
    if path == "/api/paper/events":
        return events(int(query.get("after", ["0"])[0]),
                      int(query["through"][0]) if "through" in query else None,
                      int(query.get("limit", ["100"])[0]))
    parts = path.split("/")
    if len(parts) == 5 and parts[3] == "plans":
        return plan_preview(parts[4])
    raise DataError("Paper-Route nicht gefunden.", 404)


def post(path, body):
    if path == "/api/paper/account":
        return create_account(body)
    if path == "/api/paper/plans":
        return draft(body)
    parts = path.split("/")
    if len(parts) == 6 and parts[3] == "plans" and parts[5] in COMMANDS:
        return command(parts[4], parts[5], body)
    raise DataError("Paper-Befehl nicht gefunden.", 404)


def trade_items():
    result = []
    next_after = 0
    through = None
    while True:
        page = events(next_after, through, 500)
        through = page["through"]
        entries = [row for row in page["items"] if row["kind"] == "exit"]
        result.extend({**row["payload"], "id": row["event_id"], "plan_id": row["plan_id"],
                       "recorded_at": row["recorded"], "symbol": row["symbol"], "model": MODEL}
                      for row in entries)
        if page["next"] == next_after or page["next"] >= through:
            return {"model": MODEL, "items": result, "through": through}
        next_after = page["next"]


def trade_csv():
    buffer = StringIO()
    fields = ("model", "id", "plan_id", "symbol", "entry_at", "quantity", "entry_fill", "initial_stop",
              "initial_risk", "at", "time_precision", "recorded_at", "reason", "base", "fill", "fee",
              "net_proceeds", "pnl", "r")
    writer = csv.DictWriter(buffer, fields, extrasaction="ignore")
    writer.writeheader()
    for row in trade_items()["items"]:
        entry = row["entry"]
        writer.writerow({**row, "entry_at": entry["at"], "quantity": entry["quantity"],
                         "entry_fill": entry["fill"], "initial_stop": entry["stop"],
                         "initial_risk": entry["initial_risk"]})
    return buffer.getvalue()
