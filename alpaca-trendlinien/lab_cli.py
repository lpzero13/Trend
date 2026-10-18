"""Argument definitions and JSON commands for Hermes' registered experiments."""
import json
from pathlib import Path

from lab_api import get, post


def add_commands(commands):
    for name in ("lab-profiles","lab-experiments","lab-reviews"):commands.add_parser(name)
    for name in ("lab-experiment","lab-run","lab-seal","lab-audit","lab-review","lab-review-case","lab-review-label","lab-review-reveal","lab-review-compare"):
        command=commands.add_parser(name);command.add_argument("--id",required=True)
        if name=="lab-run":
            command.add_argument("--stage",choices=("development","validation","holdout","walk_forward"),required=True)
            command.add_argument("--confirm-final-test",action="store_true")
        if name=="lab-seal":
            command.add_argument("--profile",required=True);command.add_argument("--rationale",required=True)
        if name=="lab-audit":
            command.add_argument("--after",type=int,default=0);command.add_argument("--through",type=int)
        if name in ("lab-audit","lab-review","lab-review-case"):command.add_argument("--limit",type=int,default=100 if name=="lab-audit" else 50 if name=="lab-review" else 750)
        if name in ("lab-review-case","lab-review-label","lab-review-reveal"):command.add_argument("--case",required=True)
        if name=="lab-review-label":command.add_argument("--file",required=True)
        if name=="lab-review":command.add_argument("--offset",type=int,default=0)
    pack=commands.add_parser("lab-review-create");pack.add_argument("--job",required=True)
    pack.add_argument("--count",type=int,default=30);pack.add_argument("--seed",type=int,default=0);pack.add_argument("--profile",default="reference")
    portfolio=commands.add_parser("lab-portfolio")
    for name in ("job","section","profile","family"):portfolio.add_argument("--"+name,required=True)
    portfolio.add_argument("--offset",type=int,default=0);portfolio.add_argument("--limit",type=int,default=100)


def execute(args):
    name=args.command
    if name in ("lab-profiles","lab-experiments","lab-reviews"):return get("/api/lab/"+name[4:],{})
    if name=="lab-experiment":return get(f"/api/lab/experiments/{args.id}",{})
    if name=="lab-run":return post(f"/api/lab/experiments/{args.id}/run",{"stage":args.stage,"confirm_final_test":args.confirm_final_test})[0]
    if name=="lab-seal":return post(f"/api/lab/experiments/{args.id}/seal",{"profile":args.profile,"rationale":args.rationale})[0]
    if name=="lab-audit":
        query={"after":[str(args.after)],"limit":[str(args.limit)]}
        if args.through is not None:query["through"]=[str(args.through)]
        return get(f"/api/lab/experiments/{args.id}/audit",query)
    if name=="lab-review-create":return post("/api/lab/reviews",{"job":args.job,"count":args.count,"seed":args.seed,"profile":args.profile})[0]
    if name=="lab-review":return get(f"/api/lab/reviews/{args.id}",{"offset":[str(args.offset)],"limit":[str(args.limit)]})
    if name=="lab-review-case":return get(f"/api/lab/reviews/{args.id}/{args.case}",{"limit":[str(args.limit)]})
    if name=="lab-review-label":return post(f"/api/lab/reviews/{args.id}/{args.case}/label",json.loads(Path(args.file).read_text("utf-8-sig")))[0]
    if name=="lab-review-reveal":return post(f"/api/lab/reviews/{args.id}/{args.case}/reveal",{})[0]
    if name=="lab-review-compare":return get(f"/api/lab/reviews/{args.id}/compare",{})
    if name=="lab-portfolio":return get("/api/lab/portfolio",{key:[str(getattr(args,key))] for key in ("job","section","profile","family","offset","limit")})
    raise ValueError("Unbekanntes Laborwerkzeug.")
