"""Bounded same-provider rechecks; never fabricate bars or resume the collector."""
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime,timezone
from pathlib import Path
import hashlib
import math

import alpaca
from datasets import read_dataset,source_bars,save_dataset
from fan_geometry import stable_id
from history_archive import fetch_month
from lab_data import resample_regular,session_bounds,NORMALIZATION
from models import DataError
from strategy_screen import read,write


def compare_day(old,new,start,end):
    old={b.time:b for b in old if start<=b.time and b.end<=end}
    new={b.time:b for b in new if start<=b.time and b.end<=end}
    missing=[t for t in range(start,end,300) if t not in old]
    conflicts=[t for t in old.keys() & new.keys() if old[t]!=new[t]]
    recovered=[new[t] for t in missing if t in new]
    return {'oldBars':len(old),'newBars':len(new),'missingBefore':len(missing),
            'recovered':len(recovered),'stillAbsent':len(missing)-len(recovered),
            'conflictingOverlaps':len(conflicts),'conflictExamples':conflicts[:8]},recovered


def check(root,source,preview,*,asof,max_pairs=40):
    """Network evidence first; publishing is a separate explicit step."""
    root=Path(root);p=read(Path(source)/'plan.json');targets=read(preview)['items']
    asof_time=datetime.fromisoformat(asof.replace('Z','+00:00'))
    if asof_time.tzinfo is None:asof_time=asof_time.replace(tzinfo=timezone.utc)
    if len(targets)>max_pairs:raise DataError('Gezielte Abfrage überschreitet die festgelegte Tagesgrenze.',400)
    version=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if (root/'contract.json').exists():
        contract=read(root/'contract.json')
        if contract['code']!=version or contract['sourcePlanId']!=p['id'] or contract['asof']!=asof or contract['targets']!=targets:
            raise DataError('Datenprüfvertrag geändert; neuen Ordner verwenden.',409)
    else:
        contract={'version':'tori-targeted-audit-1','code':version,'sourcePlanId':p['id'],'targets':targets,
                  'datasets':p['datasets'],'asof':asof,'feed':'sip','adjustment':'split','maxPairs':max_pairs}
        contract['id']=stable_id(contract);write(root/'contract.json',contract)
    key,secret=alpaca.credentials();results=[];requests=0
    by_symbol=defaultdict(list)
    for item in targets:by_symbol[item['symbol']].append(item)
    for symbol,items in sorted(by_symbol.items()):
        d=read_dataset(p['datasets'][symbol]);fine=source_bars(d)['5m']
        for item in items:
            path=root/'days'/(symbol+'-'+item['dayET']+'.json.gz')
            if path.exists():
                saved=read(path)
                if saved.get('contractId')!=contract['id'] or saved['checksum']!=stable_id({k:v for k,v in saved.items() if k!='checksum'}):
                    raise DataError('Geänderte Datenprüf-Evidenz.',409)
                results.append(saved);continue
            start,end=session_bounds(item['dayET']);counter={'n':0}
            def tick(pages,count):counter['n']=pages
            bars,detail=fetch_month(symbol,datetime.fromtimestamp(start,timezone.utc),datetime.fromtimestamp(end,timezone.utc),
                    {'feed':'sip','adjustment':'split','end':asof_time.isoformat()},key,secret,tick,lambda:False)
            comparison,added=compare_day(fine,bars,start,end);requests+=counter['n']
            saved={'contractId':contract['id'],'symbol':symbol,'day':item['dayET'],'sourceDatasetId':d['id'],
                   'comparison':comparison,'detail':detail,'newBars':[asdict(b) for b in bars],
                   'addedBars':[asdict(b) for b in added],'source':'Explicit recheck of same SIP/split provider; absence not proof of halt'}
            saved['checksum']=stable_id(saved);write(path,saved);results.append(saved)
    summary={'contractId':contract['id'],'pairs':len(results),'requestsThisInvocation':requests,
             'recoveredBars':sum(v['comparison']['recovered'] for v in results),
             'stillAbsent':sum(v['comparison']['stillAbsent'] for v in results),
             'conflictingPairs':sum(v['comparison']['conflictingOverlaps']>0 for v in results),
             'days':[{'symbol':v['symbol'],'day':v['day'],**v['comparison']} for v in results],
             'datasetsPublished':False,'collectorResumed':False}
    write(root/'audit-summary.json',summary);return summary


def publish(root):
    """Only add returned missing bars when ALL overlaps agree exactly."""
    root=Path(root);contract=read(root/'contract.json')
    if contract['code']!=hashlib.sha256(Path(__file__).read_bytes()).hexdigest():raise DataError('Geänderter Prüfcode.',409)
    if (root/'published.json').exists():return read(root/'published.json')
    grouped=defaultdict(list)
    for path in (root/'days').glob('*.json.gz'):
        v=read(path)
        if v['contractId']!=contract['id'] or v['checksum']!=stable_id({k:x for k,x in v.items() if k!='checksum'}):raise DataError('Geänderte Prüfevidenz.',409)
        grouped[v['symbol']].append(v)
    if sum(map(len,grouped.values()))!=len(contract['targets']):raise DataError('Datenprüfung noch nicht vollständig.',409)
    ids=dict(contract['datasets']);changes=[]
    from models import Bar
    for symbol,days in sorted(grouped.items()):
        if any(v['comparison']['conflictingOverlaps'] for v in days):
            changes.append({'symbol':symbol,'published':False,'reason':'Overlapping provider bars changed; no grafting across revisions'});continue
        added=[Bar(**b) for v in days for b in v['addedBars']]
        if not added:continue
        old=read_dataset(ids[symbol]);fine=source_bars(old)['5m'];times={b.time for b in fine}
        if any(b.time in times for b in added):raise DataError('Unerwartete doppelte Reparaturkerze.',409)
        sources,q=resample_regular(sorted(fine+added,key=lambda b:b.time))
        evidence={'parentDatasetId':old['id'],'auditContractId':contract['id'],'recoveredBars':len(added),
                  'days':[v['day'] for v in days],'evidenceChecksums':[v['checksum'] for v in days],
                  'policy':'Provider-returned missing bars only, exact overlapping OHLCV agreement; old datasets preserved'}
        material={tf:(rows,{**old['sources'][tf],'normalization':NORMALIZATION,'rthQuality':q,'count':len(rows),
                           'first':rows[0].time,'last':rows[-1].time,'lastClose':rows[-1].end,'targetedAudit':evidence}) for tf,rows in sources.items()}
        new=save_dataset(symbol,material,provider=old['material']['provider'],feed='sip',adjustment='split',session=old['material']['session'])
        ids[symbol]=new;changes.append({'symbol':symbol,'oldDatasetId':old['id'],'newDatasetId':new,'published':True,'recoveredBars':len(added)})
    result={'contractId':contract['id'],'datasets':ids,'changes':changes,'collectorResumed':False}
    write(root/'published.json',result);return result
