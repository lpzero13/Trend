"""Non-destructive SQLite sizing experiment on three pinned local market datasets."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import sqlite3
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from random_replay import candidates
from datasets import read_dataset,path_for,data_kind


def run(root):
    root=Path(root)
    if root.exists():raise ValueError('New benchmark output directory required; never overwrite an existing run')
    root.mkdir(parents=True);pool=candidates();symbols=('AAPL','JPM','XOM');chosen={s:pool[s][0] for s in symbols}
    result={'createdAt':datetime.now(timezone.utc).isoformat(),'sampleSymbols':list(symbols),'dataset_ids':chosen,
            'meaning':'Measured on three long, liquid US-stock histories. Conservative SQLite REAL storage, no price rounding. No production migration. Extrapolation is an estimate, not a complete-universe import.'}
    for mode in ('all_frames','base_5m'):
        path=root/(mode+'.sqlite3');db=sqlite3.connect(path);db.execute('PRAGMA journal_mode=DELETE')
        db.execute('CREATE TABLE series(id INTEGER PRIMARY KEY,symbol TEXT,timeframe TEXT,provider TEXT,feed TEXT,adjustment TEXT,dataset_id TEXT)')
        db.execute('CREATE TABLE bars(series_id INTEGER,at INTEGER,end_at INTEGER,o REAL,h REAL,l REAL,c REAL,v REAL,PRIMARY KEY(series_id,at)) WITHOUT ROWID')
        stats=[];raw_bytes=0;row_count=0;t0=time.monotonic();sid=0
        for symbol,identity in chosen.items():
            dataset=read_dataset(identity);assert data_kind(dataset)=='market';m=dataset['material'];raw_bytes+=path_for(identity).stat().st_size
            counts={}
            for tf,rows in m['bars'].items():
                if mode=='base_5m' and tf!='5m':continue
                sid+=1;db.execute('INSERT INTO series VALUES(?,?,?,?,?,?,?)',(sid,symbol,tf,m['provider'],m['feed'],m['adjustment'],identity))
                db.executemany('INSERT INTO bars VALUES(?,?,?,?,?,?,?,?)',((sid,b['time'],b['end'],b['open'],b['high'],b['low'],b['close'],b['volume']) for b in rows))
                assert db.execute('SELECT count(*) FROM bars WHERE series_id=?',(sid,)).fetchone()[0]==len(rows)
                # Exact stored values at ten spread-out positions; no rounded or regenerated bars.
                for i in sorted({int((len(rows)-1)*k/9) for k in range(10)}):
                    b=rows[i];got=db.execute('SELECT end_at,o,h,l,c,v FROM bars WHERE series_id=? AND at=?',(sid,b['time'])).fetchone()
                    assert got==tuple(b[k] for k in ('end','open','high','low','close','volume'))
                counts[tf]=len(rows);row_count+=len(rows)
            db.commit();fine=m['bars']['5m'];stats.append({'symbol':symbol,'counts':counts,'fromAt':fine[0]['time'],'through':fine[-1]['end']})
        db.execute('VACUUM');db.close();size=path.stat().st_size
        result[mode]={'rows':row_count,'bytes':size,'jsonBytes':raw_bytes,'bytesPerRow':size/row_count,
                      'MiBPerStock':size/(1024**2*len(symbols)),'seconds':time.monotonic()-t0,'stocks':stats,'verified':True}
    (root/'benchmark.json').write_text(json.dumps(result,ensure_ascii=False),'utf-8')
    print(json.dumps(result,ensure_ascii=True),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True);run(p.parse_args().root)
