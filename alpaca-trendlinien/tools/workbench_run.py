"""Run the frozen replay, independent audit and matched report after the import."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def run(root,iex,output,wait_import=False):
    root=Path(root).resolve();app=Path(__file__).resolve().parents[1]
    contract=json.loads((root/'import-contract.json').read_text('utf-8'))
    if contract.get('feed')!='sip':raise ValueError('Separate SIP import required')
    previous=-1;deadline=time.monotonic()+3600
    while True:
        imports=json.loads((root/'imports.json').read_text('utf-8'))
        if len(imports)!=previous:print(json.dumps({'imported':len(imports),'requested':len(contract['symbols'])}),flush=True);previous=len(imports)
        if set(imports)==set(contract['symbols']):break
        if not wait_import or time.monotonic()>deadline:raise ValueError('Complete import required; import may be resumed separately')
        time.sleep(5)
    commands=[['tools/complete_study.py','--root',str(root)],
        ['tools/workbench_verify_scanner.py','--root',str(root)],
        ['tools/verify_complete_study.py','--root',str(root)],
        ['tools/workbench_report.py','--iex',str(Path(iex).resolve()),'--sip',str(root),'--output',str(Path(output).resolve())]]
    for i,args in enumerate(commands):
        log=root/f'pipeline-{i+1}.log';print(json.dumps({'stage':args[0],'log':str(log)}),flush=True)
        with log.open('w',encoding='utf-8') as f:subprocess.run([sys.executable,'-u',*args],cwd=app,stdout=f,stderr=subprocess.STDOUT,check=True)
    print(json.dumps({'done':True}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True);p.add_argument('--iex',required=True)
    p.add_argument('--output',required=True);p.add_argument('--wait-import',action='store_true');a=p.parse_args()
    run(a.root,a.iex,a.output,a.wait_import)
