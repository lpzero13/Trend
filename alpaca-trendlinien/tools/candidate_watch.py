"""Register/run/read/stop a separate SIP observer; shared TORI_DATA_DIR required."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from candidate_watch import registration,worker,status,journal,request_stop

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['init','run','status','events','stop'])
    p.add_argument('--id');p.add_argument('--source');p.add_argument('--once',action='store_true');p.add_argument('--cursor');a=p.parse_args()
    if a.action=='init':
        if not a.source:p.error('--source: verifiziertes SIP-Importverzeichnis benötigt')
        imports=json.loads((Path(a.source)/'imports.json').read_text('utf-8'))
        result=registration({s:d['id'] for s,d in imports.items() if d.get('id')})
    else:
        if not a.id:p.error('--id erforderlich')
        result=worker(a.id,a.once) if a.action=='run' else status(a.id) if a.action=='status' else journal(a.id,cursor=a.cursor) if a.action=='events' else request_stop(a.id)
    print(json.dumps(result,ensure_ascii=True,allow_nan=False),flush=True)
