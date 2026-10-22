"""Run each preregistered Retest exit sequentially, offline, on pinned entries."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from datasets import digest, read_dataset, source_bars
from retest_exits import contract_for, complete_history
from retest_variants import VERSION, VARIANTS, RULES, path, summarize
from safety_strategy import StrategyContext, execution_costs
from strategy_portfolio import simulate
from strategy_run_lock import study_lock
from strategy_research import write_json
from tools.retest_exit_study import read, checked, save


def run(args):
    root,archive,data_root=[Path(v).resolve() for v in (args.root,args.archive,args.data)]
    os.environ["TORI_DATA_DIR"]=str(data_root)
    parent=read(archive/"contract.json")
    frozen=read(archive/"frozen-entries.json")
    if any(digest(frozen[s]) != value for s,value in parent["entryHashes"].items()):
        raise ValueError("Changed pinned entry list")
    code=Path(__file__).resolve().parents[1]
    names=tuple(parent["engine"])+("retest_variants.py","tools/retest_variant_study.py")
    engine={n:hashlib.sha256((code/n).read_bytes()).hexdigest() for n in names}
    for name,value in parent["engine"].items():
        if engine[name] != value:
            raise ValueError("Archived reference engine changed; preserve prior replay semantics")
    blocks={}
    for stage in parent["phases"]:
        for file in sorted((archive/stage).glob("*.json")):
            block=checked(file)
            if block["contractHash"] != digest(parent):
                raise ValueError("Archived block contract mismatch")
            blocks[stage+"/"+file.name]=block["checksum"]
    contract={"version":VERSION,"engine":engine,"rules":RULES,"variants":list(VARIANTS),
        "parentHash":digest(parent),"sourceBlocks":blocks,"entryHashes":parent["entryHashes"],
        "entryCounts":parent["entryCounts"],"datasets":parent["datasets"],"phases":parent["phases"],
        "costs":parent["costs"],"portfolio":parent["portfolio"],
        "preregistrationHash":hashlib.sha256((code/"RETEST-EXIT-VARIANTEN-PLAN.md").read_bytes()).hexdigest()}
    with study_lock(root),patch("alpaca._request",side_effect=AssertionError("Variants are offline")):
        root.mkdir(parents=True,exist_ok=True)
        if (root/"contract.json").exists():
            if read(root/"contract.json") != contract or read(root/"frozen-entries.json") != frozen:
                raise ValueError("Changed inputs/code: use a new study generation")
        else:
            write_json(root/"contract.json",contract)
            write_json(root/"frozen-entries.json",frozen)
        if args.stage == "prepare":
            print(json.dumps({"contractHash":digest(contract),"entries":parent["entryCounts"]}))
            return
        variant=args.variant
        if variant is None:
            raise ValueError("--variant required for an actual run")
        index=VARIANTS.index(variant)
        if index and not (root/VARIANTS[index-1]/"validation-results.json").exists():
            raise ValueError("Complete preceding variant first; keep the fixed sequence")
        if args.stage == "validation":
            decision=checked(root/variant/"development-decision.json")
            if decision["contractHash"] != digest(contract):
                raise ValueError("Development decision mismatch")
        phase=parent["phases"][args.stage]
        contexts={}
        records=[]
        symbols=sorted({e["symbol"] for e in frozen[args.stage]})
        for symbol in symbols:
            old=checked(archive/args.stage/(symbol+".json"))
            identity=parent["datasets"][symbol]["id"]
            context=StrategyContext(source_bars(read_dataset(identity)),phase["endAt"])
            contexts[identity]=context
            output=root/variant/args.stage/(symbol+".json")
            if output.exists():
                block=checked(output)
                if block["contractHash"] != digest(contract):
                    raise ValueError("Checkpoint mismatch")
            else:
                rows=[]
                for original in old["records"]:
                    e=original["entry"]
                    if e not in frozen[args.stage]:
                        raise ValueError("Unpinned entry")
                    c=contract_for(context,e,parent["costs"])
                    fixed=path(context,e,c,"fixed")
                    if fixed != original["paths"]["fixed"] or complete_history(context.sources,e) != original["history"]:
                        raise ValueError("Reference replay/history no longer matches archive")
                    rows.append({"entry":e,"contract":c,"history":original["history"],
                        "calendarFits":original["calendarFits"],"fullHorizonPath":original["fullHorizonPath"],
                        "paths":{"fixed":fixed,variant:path(context,e,c,variant)}})
                block={"contractHash":digest(contract),"records":rows}
                save(output,block)
            records.extend(block["records"])
            print(json.dumps({"variant":variant,"stage":args.stage,"symbol":symbol,"cases":len(block["records"])}),flush=True)
        portfolios={}
        for geometry in ("hull_exact","swing_zone"):
            selected=[r for r in records if r["entry"]["model"] == geometry and r["history"]["complete"] and r["calendarFits"]]
            for model in ("fixed",variant):
                portfolios[geometry+"/"+model]=simulate([r["entry"] for r in selected],[r["paths"][model] for r in selected],
                    contexts,phase,execution_costs(parent["costs"]),parent["portfolio"])
        result={"contractHash":digest(contract),"variant":variant,"stage":args.stage,"rawEntries":len(records),
                "groups":summarize(records,variant),"portfolios":portfolios}
        save(root/variant/(args.stage+"-results.json"),result)
        if args.stage == "development":
            decision={"contractHash":digest(contract),"resultHash":result["checksum"],"variant":variant,
                "deltas":{g:result["groups"][g+"/complete_history"]["meanDeltaR"] for g in ("hull_exact","swing_zone")},
                "decision":"Rules stay fixed. Later phase is already known; no parameters selected from this result."}
            save(root/variant/"development-decision.json",decision)
        print(json.dumps({"done":variant+"/"+args.stage,"records":len(records)}),flush=True)


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive",required=True)
    p.add_argument("--data",required=True)
    p.add_argument("--root",required=True)
    p.add_argument("--variant",choices=VARIANTS)
    p.add_argument("--stage",required=True,choices=("prepare","development","validation"))
    run(p.parse_args())
