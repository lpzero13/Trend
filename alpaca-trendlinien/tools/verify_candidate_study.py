"""Independent raw-path arithmetic and panel audit for the frozen candidate study."""
import argparse
from bisect import bisect_left,bisect_right
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
from statistics import mean
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from datasets import digest,read_dataset
from lab_metrics import expected_grid
from models import NY
from candidate_research import summarize
from tools.candidate_study import signature
from tools.complete_study_import import write


def run(root,source):
    root,source=Path(root),Path(source);contract=json.loads((root/'contract.json').read_text('utf-8'))
    assert contract['engine']==signature()
    assert contract['planHash']==hashlib.sha256((Path(__file__).resolve().parents[1]/'TORI-KANDIDATEN-PLAN.md').read_bytes()).hexdigest()
    records=[];raw_count=control_count=0
    for file in sorted((root/'stocks').glob('*.json')):
        b=json.loads(file.read_text('utf-8'));s=json.loads((root/'selections'/file.name).read_text('utf-8'))
        for value in (b,s):assert value['checksum']==digest({k:v for k,v in value.items() if k!='checksum'})
        assert b['selectionHash']==s['checksum'];assert b['contractHash']==digest(contract)
        selected={v['entry']['id']:v for v in s['selections']}
        original=json.loads((source/'studies'/(b['symbol']+'-4h-strict.json')).read_text('utf-8'))
        old={e['id']:e for e in original['entries'] if e['profile']=='age7' and e['family']=='retest'}
        assert set(old)==set(selected)=={r['id'] for r in b['records']}
        data=read_dataset(b['datasetId']);fine=data['material']['bars']['5m'];times=[x['time'] for x in fine];ends=[x['end'] for x in fine]
        for r in b['records']:
            e=r['entry'];assert e==selected[r['id']]['entry'];assert r['naturalPaths']=={m:old[r['id']]['paths'][m] for m in ('fixed','higher_low')}
            assert [c['id'] for c in r['controls']]==[c['id'] for c in selected[r['id']]['controlSelection']['items']]
            target=datetime.fromtimestamp(e['entryAt'],NY)
            for c in r['controls']:
                dt=datetime.fromtimestamp(c['entryAt'],NY)
                assert (dt.year,(dt.month-1)//3,dt.hour,dt.minute)==(target.year,(target.month-1)//3,target.hour,target.minute)
                assert abs((c['entryPrice']-c['initialStop'])/c['entryPrice']-(e['entryPrice']-e['initialStop'])/e['entryPrice'])<1e-12
                control_count+=1
            for row,entry in [(r,e),*((c,c) for c in r['controls'])]:
                for h,o in row['outcomes'].items():
                    end=o['targetEnd'];m=o['market']
                    if not o['mature']:assert m['netPct'] is None;continue
                    bars=fine[bisect_left(times,entry['entryAt']):bisect_right(ends,end)]
                    complete=bool(bars) and [b['time'] for b in bars]==list(expected_grid(entry['entryAt'],end))
                    assert (m['status']=='known')==complete
                    if not complete:continue
                    price=entry['entryPrice'];value=(bars[-1]['close']*.99925/(price*1.00075)-1)*100
                    assert abs(value-m['netPct'])<1e-10
                    assert abs(max(0,(max(x['high'] for x in bars)/price-1)*100)-m['mfePct'])<1e-10
                    assert abs(min(0,(min(x['low'] for x in bars)/price-1)*100)-m['maePct'])<1e-10
                    assert any(x['low']<=entry['initialStop'] for x in bars)==m['safetyTouched'];raw_count+=1
            records.append(r)
    result=json.loads((root/'summary.json').read_text('utf-8'))
    for h in ('5','10','20'):
        for kind in ('market','fixed','higher_low'):
            vals=[]
            def v(r):
                o=r['outcomes'][h]
                return None if not o['mature'] else o['market']['netPct'] if kind=='market' else o['paths'][kind]['valuationR']
            for r in records:
                a=v(r);cs=[v(c) for c in r['controls']]
                if a is not None and len(cs)==5 and all(x is not None for x in cs):vals.append(a-sum(cs)/5)
            got=result['groups']['all']['horizons'][h][kind]
            assert len(vals)==got['pairedPanels'];assert abs(mean(vals)-got['meanExcess'])<1e-10
    # Matched old feed universe, reported separately rather than changing the primary cohort.
    matched=[r for r in records if r['symbol'] not in ('CRM','KO','LOW')]
    write(root/'matched57-summary.json',summarize(matched))
    audit={'passed':True,'contractHash':digest(contract),'entries':len(records),'controlObservations':control_count,
           'independentFineHorizonPaths':raw_count,'pairedComparisons':9,'matchedOldUniverseEntries':len(matched),
           'limits':'Bootstrap is descriptive; aggregate subgroup reproducibility uses the shared summarizer. No blind human labels or prospective outcomes fabricated.'}
    write(root/'candidate-verification.json',audit);print(json.dumps(audit))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True);p.add_argument('--source',required=True);a=p.parse_args();run(a.root,a.source)
