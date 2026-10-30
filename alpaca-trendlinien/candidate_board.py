"""Causal lifecycle of frozen source rays. Display ordering is not a fitted score."""
from copy import deepcopy
from datasets import digest
from entry_geometry import at
from complete_strategy import source_grid

VERSION = 'sip-candidates-1'
STATES = ('approaching', 'breakout', 'retest', 'bounce', 'invalid', 'unclear')


def similar(a, b, index, volatility):
    if any(a.get(role) is None or b.get(role) is None for role in ('red','green')):return False
    return all(abs(at(a[role], i)-at(b[role], i)) <= .25*volatility
               for role in ('red', 'green') for i in (index, index+20))


def build(facts, rows, cutoff, previous=()):
    """Never replace a group's first anchors; later facts remain alternatives.

    Missing source candles suspend interpretation. A broken geometry is not a
    claim that a buffered paper stop was filled. All rays use source bar indexes.
    """
    groups=deepcopy(list(previous)); by_end={b.end:i for i,b in enumerate(rows)}
    for f in sorted(facts, key=lambda x:(x['knownAt'], x['id'])):
        i=by_end.get(f['knownAt'])
        if i is None or f['knownAt']>cutoff:continue
        if any(f['id'] in g['factIds'] for g in groups):continue
        g=next((g for g in groups if g['symbol']==f['symbol'] and g['timeframe']==f['timeframe']
                and similar(g['original'], f, i, min(g['original']['signalATR'],f['signalATR']))), None)
        if g is None:
            g={'id':digest([VERSION,f['symbol'],f['timeframe'],f['id']]),
               'symbol':f['symbol'],'timeframe':f['timeframe'],'original':deepcopy(f),
               'firstKnownAt':f['knownAt'],'factIds':[], 'facts':[]}
            groups.append(g)
        g['factIds'].append(f['id']);g['facts'].append(deepcopy(f))
    if not rows:return []
    last=len(rows)-1;latest=rows[-1]
    grid=list(source_grid(rows[0].time,cutoff,'4h'))
    for g in groups:
        f=g['original']; first=by_end.get(f['knownAt'])
        g.update(asOf=latest.end, alternativeCount=len(g['facts'])-1,
                 lastFactAt=max(x['knownAt'] for x in g['facts']), warnings=list(f['warnings']))
        if f.get('red') is None or f.get('green') is None:
            g.update(state='unclear',reason='Kein vollständiges ursprüngliches Aktions-/Safety-Linienpaar',heuristicOrder=0)
            continue
        if first is None:
            g.update(state='unclear',reason='Originaler Quellschluss fehlt');continue
        # A nearby alternative must not relabel the original ray's signal.
        primary=[x for x in g['facts'] if x['red']==f['red'] and x['green']==f['green']]
        latest_fact=max(primary,key=lambda x:(x['knownAt'],{'approaching':0,'breakout':1,'bounce':2,'retest':3}.get(x['phase'],0)))
        phase=latest_fact['phase']; broken_at=next((x['knownAt'] for x in primary if x['phase'] in ('breakout','retest')),None)
        g['alternativePhases']=sorted({x['phase'] for x in g['facts'] if x not in primary})
        needed=[p for p in grid if f['knownAt']<=p[1]<=latest.end]
        actual=[(b.time,b.end) for b in rows[first:]]
        if needed!=actual:
            g.update(state='unclear',reason='Fehlende Quellkerze seit der ersten Beobachtung');continue
        invalid=None
        for i in range(first+1,last+1):
            b=rows[i]
            if b.low<at(f['green'],i)-.1*f['signalATR']:
                invalid=(b.end,'Ursprüngliche Safety-Geometrie verletzt');break
            if broken_at and b.end>broken_at and b.close<at(f['red'],i)-.1*f['signalATR']:
                invalid=(b.end,'Schluss zurück unter der ursprünglichen Ausbruchslinie');break
        distance=(at(f['red'],last)-latest.close)/f['signalATR']
        if invalid:g.update(state='invalid',invalidAt=invalid[0],reason=invalid[1])
        elif phase=='approaching' and not 0<=distance<=.75:
            g.update(state='unclear',reason='Ursprüngliche Annäherung inzwischen verlassen')
        else:g.update(state=phase,reason='Originale Anker bleiben fixiert')
        g.update(redNow=at(f['red'],last),greenNow=at(f['green'],last),sourceClose=latest.close,
                 distanceATR=distance, heuristicOrder={'retest':4,'breakout':3,'bounce':2,'approaching':1}.get(g['state'],0))
    return sorted(groups,key=lambda g:(-g.get('heuristicOrder',0),-g['lastFactAt'],g['id']))
