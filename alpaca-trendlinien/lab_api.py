"""Lab operations shared by authenticated HTTP and the local JSON CLI.

Transport authentication/origin checks belong to server.Handler. No route here
starts provider work synchronously; run submits to the durable worker queue.
"""
import json
import re

from database import connection
from models import DataError


def get(path,query):
    import lab_registry as registry
    import lab_reviews as reviews
    def number(name,default):return int(query.get(name,[str(default)])[0])
    if path=="/api/lab/profiles":
        from lab_profiles import PROFILES, VERSION, DEFAULTS
        return {"version":VERSION,"profiles":PROFILES,"defaults":DEFAULTS}
    if path=="/api/lab/experiments":return {"items":registry.list_experiments()}
    match=re.fullmatch(r"/api/lab/experiments/([a-f0-9]{32})(/audit)?",path)
    if match:
        if match[2]:return registry.journal(match[1],after=number("after",0),through=number("through",0) if "through" in query else None,limit=number("limit",100))
        return registry.get(match[1])
    if path=="/api/lab/reviews":
        with connection() as db:
            return {"items":[{"id":r[0],"created":r[1],"jobId":r[2],"manifest":json.loads(r[3])} for r in db.execute("SELECT id,created,job_id,manifest FROM lab_reviews ORDER BY created DESC LIMIT 100")]}
    match=re.fullmatch(r"/api/lab/reviews/([a-f0-9]{32})(?:/([a-f0-9]{24}|compare))?",path)
    if match:
        if match[2]=="compare":return reviews.compare(match[1])
        if match[2]:return reviews.view(match[1],match[2],limit=number("limit",750))
        return reviews.get(match[1],offset=number("offset",0),limit=number("limit",50))
    if path=="/api/lab/portfolio":
        from lab_jobs import portfolio
        value=lambda name:query.get(name,[""])[0]
        return portfolio(value("job"),value("section"),value("profile"),value("family"),offset=number("offset",0),limit=number("limit",100))
    raise DataError("Unbekannte Laborroute.",404)


def post(path,body):
    import lab_registry as registry
    import lab_reviews as reviews
    if not isinstance(body,dict):raise DataError("Laboranfrage benötigt ein JSON-Objekt.",400)
    match=re.fullmatch(r"/api/lab/experiments/([a-f0-9]{32})/(run|seal)",path)
    if match:
        if match[2]=="seal":
            if set(body)!={"profile","rationale"}:raise DataError("Auswahl benötigt Profil und Begründung.",400)
            return registry.seal(match[1],body["profile"],body["rationale"]),200
        if set(body)-{"stage","confirm_final_test"} or body.get("stage") not in ("development","validation","holdout","walk_forward"):
            raise DataError("Forschungsphase development/validation/holdout/walk_forward angeben.",400)
        record=registry.get(match[1]);spec=record["spec"]
        spec["lab"].update(experiment_id=match[1],stage=body["stage"],confirm_final_test=body.get("confirm_final_test",False))
        import jobs
        return jobs.submit(spec),202
    if path=="/api/lab/reviews":
        if set(body)-{"job","count","seed","profile"} or "job" not in body:raise DataError("Fallpaket benötigt einen Entwicklungsauftrag.",400)
        return reviews.create(body["job"],count=body.get("count",30),seed=body.get("seed",0),profile=body.get("profile","reference")),201
    match=re.fullmatch(r"/api/lab/reviews/([a-f0-9]{32})/([a-f0-9]{24})/(label|reveal)",path)
    if match:
        if match[3]=="label":return reviews.label(match[1],match[2],body),200
        if body:raise DataError("Offenlegung benötigt keine zusätzlichen Parameter.",400)
        return reviews.reveal(match[1],match[2]),200
    raise DataError("Unbekannte Laborroute.",404)
