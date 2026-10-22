"""Read-only watch status/cases, plus explicit local human review writes."""
import re
from models import DataError
import forward_watch as watch


def get(path, query):
    number = lambda k,d: int(query.get(k,[str(d)])[0])
    value = lambda k: query.get(k,[""])[0]
    if path == "/api/watch/status":
        return watch.status()
    if path == "/api/watch/cases":
        return watch.cases_page(value("run") or None,offset=number("offset",0),limit=number("limit",50),
            through=number("through",0) if "through" in query else None,model=value("model"),phase=value("phase"))
    if path == "/api/watch/events":
        return watch.events_page(value("run") or None,after=number("after",0),limit=number("limit",100),
            through=number("through",0) if "through" in query else None)
    match = re.fullmatch(r"/api/watch/cases/([a-f0-9]{64})",path)
    if match:
        if value("view") not in ("","signal","latest"):
            raise DataError("Unbekannte Verlaufssicht.",400)
        return watch.case_view(match[1],value("view")=="latest")
    raise DataError("Unbekannte Beobachtungsroute.",404)


def post(path, body):
    match = re.fullmatch(r"/api/watch/cases/([a-f0-9]{64})/review",path)
    if not match:
        raise DataError("Nur ausdrückliche Fallurteile können hier gespeichert werden.",405)
    return watch.review(match[1],body)
