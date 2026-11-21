"""Resumable offline radar experiment over declared, already-known windows."""
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import statistics
import time
from unittest.mock import patch
from urllib.parse import urlencode

from datasets import read_dataset, source_bars, data_kind
from early_warning import Radar, Rules, VERSION
from entry_screen import Context
from fan_geometry import stable_id
from fan_study import timestamp, source_gaps, schedule
from lab_data import require_convention
from models import DataError, NY
from pilot_backtest import code_digest, FAMILIES
from settings import data_dir
from strategy_screen import read, write


def binding():
    names = ('early_warning.py', 'early_warning_study.py', 'entry_screen.py', 'setup_episodes.py',
             'datasets.py', 'strategy_screen.py', 'tools/early_warning.py')
    return {**code_digest()['files'], **{n: hashlib.sha256((Path(__file__).parent/n).read_bytes()).hexdigest() for n in names}}


def checked(plan):
    if plan['id'] != stable_id({k: v for k, v in plan.items() if k != 'id'}) or plan['engine'] != binding():
        raise DataError('Plan/Engine verändert: neuen Vorwarn-Studienordner verwenden.', 409)
    if plan['dataRoot'] != str(data_dir()):
        raise DataError('Anderer TORI_DATA_DIR: keine stille Wiederaufnahme.', 409)
    return plan


def prepare(root, source, *, symbols=None, rules=None):
    root = Path(root)
    if (root/'plan.json').exists():
        plan = checked(read(root/'plan.json'))
        if symbols and sorted(symbols) != plan['symbols']:
            raise DataError('Auswahl nicht beim Wiederaufnehmen ändern.', 409)
        if rules and asdict(rules) != {**plan['rules'], 'thresholds': tuple(plan['rules']['thresholds']), 'variants': tuple(plan['rules']['variants'])}:
            raise DataError('Regeln nicht beim Wiederaufnehmen ändern.', 409)
        return plan
    source = read(source)
    if source['id'] != stable_id({k: v for k, v in source.items() if k != 'id'}):
        raise DataError('Quellplan-Prüfsumme ungültig.', 409)
    selected = sorted(symbols or source['symbols'])
    if not selected or set(selected)-set(source['datasets']):
        raise DataError('Aktie fehlt im Quelluniversum.', 400)
    plan = {'version': VERSION, 'sourcePlanId': source['id'], 'dataRoot': str(data_dir()),
            'createdAt': datetime.now(timezone.utc).isoformat(), 'engine': binding(),
            'symbols': selected, 'datasets': {s: source['datasets'][s] for s in selected},
            'windows': source['windows'], 'warmupDays': source['warmupDays'], 'rules': asdict(rules or Rules()),
            'evaluation': 'All causal warnings, including nonentries; outcomes clipped at each known window end; no new holdout',
            'limitations': ['Known current-survivor universe and previously explored windows; not independent validation',
                'Signal occurrence is not a profitable fill or executable portfolio return',
                'Policies share episodes; do not sum them as independent samples',
                'Qualification at warning and at later signal are separate; no retroactive upgrade',
                'Family-specific timing: breakout clean close, retest confirmation, safety-bounce signal',
                'Nonentry watches censored at gaps/window ends; no time exits or provider requests']}
    plan['id'] = stable_id(plan)
    for name in plan['engine']:
        dest = root/'engine'/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((Path(__file__).parent/name).read_bytes())
    write(root/'plan.json', plan)
    return plan


def load_block(root, plan, symbol):
    b = read(Path(root)/'stocks'/(symbol+'.json.gz'))
    if b['planId'] != plan['id'] or b['checksum'] != stable_id({k: v for k, v in b.items() if k != 'checksum'}):
        raise DataError('Vorwarn-Ergebnisblock verändert.', 409)
    return b


def _work(task):
    root, plan, symbol = task
    checked(plan)
    path = Path(root)/'stocks'/(symbol+'.json.gz')
    if path.exists():
        b = load_block(root, plan, symbol)
        return {'symbol': symbol, 'cached': True, 'records': len(b['records'])}
    started = time.perf_counter()
    with patch('alpaca._request', side_effect=AssertionError('Radar experiment must stay offline')):
        dataset = read_dataset(plan['datasets'][symbol])
        require_convention(dataset)
        m = dataset['material']
        if data_kind(dataset) != 'market' or m['symbol'] != symbol or m['feed'] != 'sip' or m['adjustment'] != 'split':
            raise DataError('Erwartet passendes echtes reguläres SIP/split-Archiv.', 422)
        frames = source_bars(dataset)
        first = min(timestamp(w['start']) for w in plan['windows'])
        last = max(timestamp(w['end'], upper=True) for w in plan['windows'])
        rows = [b for b in frames['4h'] if b.time >= first-plan['warmupDays']*86400 and b.end <= last]
        daily = [b for b in frames['1D'] if b.end <= last]
        if not rows or not daily: raise DataError('Keine lokalen Vorwarn-Kurse verfügbar.', 422)
        gaps = source_gaps(rows, rows[-1].end, '4h')
        config = {**plan['rules'], 'thresholds': tuple(plan['rules']['thresholds']), 'variants': tuple(plan['rules']['variants'])}
        radar = Radar(symbol, rules=Rules(**config), daily_context=Context(rows, daily))
        for i, bar in enumerate(rows): radar.push(bar, gap=i in gaps)
        result = radar.result(rows[-1].end)
        windows = [(timestamp(w['start']), timestamp(w['end'], upper=True)) for w in plan['windows']]
        relevant = lambda at: at is not None and any(a <= at <= b for a, b in windows)
        records = [r for r in result['records'] if relevant(r['entry']['at'] if r['entry'] else None) or any(relevant(w['at']) for w in r['warnings'])]
        used = {r['episodeId'] for r in records}
        for r in records:
            r['datasetId'] = dataset['id']
            for w in r['warnings']:
                w['chartUrl'] = '/?'+urlencode({
                    'symbol': symbol, 'dataset': dataset['id'], 'tf': '4h', 'engine': 'fan_master',
                    'asof': datetime.fromtimestamp(w['at'], timezone.utc).isoformat()})
        b = {'planId': plan['id'], 'symbol': symbol, 'datasetId': dataset['id'],
             'records': records, 'episodes': [e for e in result['episodes'] if e['id'] in used],
             'eligibility': {w['name']: rows[0].end <= timestamp(w['start'])-320*86400 for w in plan['windows']},
             'rawSignals': result['rawSignals'], 'sourceGaps': len(gaps),
             'firstSourceAt': rows[0].end, 'lastSourceAt': rows[-1].end,
             'elapsedSeconds': time.perf_counter()-started}
        b['checksum'] = stable_id(b)
        write(path, b)
    return {'symbol': symbol, 'records': len(records), 'seconds': round(b['elapsedSeconds'], 2)}


def build(root, plan, workers=2, progress=print):
    checked(plan)
    if type(workers) is not int or not 1 <= workers <= 4: raise ValueError('1–4 Worker erforderlich.')
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for item in as_completed([pool.submit(_work, (str(root), plan, s)) for s in plan['symbols']]):
            progress(item.result())


def describe(plan, blocks):
    """Per-window censoring, family-specific denominators and zero-alert days."""
    groups = {}
    for policy, _, _ in Rules(**{**plan['rules'], 'thresholds': tuple(plan['rules']['thresholds']), 'variants': tuple(plan['rules']['variants'])}).policies():
        for family in FAMILIES:
            groups[policy, family] = {'policy': policy, 'family': family, 'entries': 0, 'coveredEntries': 0,
                'covered1to2Sessions': 0, 'entriesWithEarlierOutOfWindowWarning': 0, 'warnings': 0,
                'confirmed': 0, 'fizzled': 0, 'censored': 0, 'invalidRiskSignals': 0,
                'afterClosedWatchEntries': 0, 'sameLineConfirmations': 0,
                'leadBars': [], 'leadSessions': [], 'warningCohorts': Counter(), 'entryCohorts': Counter(),
                'rawBreakLeadBars': [], 'firstTouchLeadBars': [], 'coveredBeforeFirstTouch': 0,
                'entryCoverageByCohort': {}, 'warningResultsByCohort': {},
                'daily': Counter(), 'warningApproach': Counter(), 'confirmedApproach': Counter()}
    dates = set()
    for window in plan['windows']:
        start, end = timestamp(window['start']), timestamp(window['end'], upper=True)
        trading_dates = sorted({datetime.fromtimestamp(t, NY).date().isoformat() for t, _ in schedule(start, end, '4h')})
        dates.update(trading_dates)
        # Session ordinals include both boundaries; weekend hours are not trading days.
        ordinal = {d: i for i, d in enumerate(trading_dates)}
        session_at = lambda at: ordinal.get(datetime.fromtimestamp(at, NY).date().isoformat())
        for block in blocks:
            if not block['eligibility'][window['name']]: continue
            for r in block['records']:
                g = groups[r['policy'], r['family']]
                ws = sorted(r['warnings'], key=lambda w: (w['at'], w['stage']))
                first = next((w for w in ws if w['stage'] == 2), None)
                e = r['entry']
                entry_in = bool(e and start <= e['at'] <= end and e['validRisk'])
                warning_in = bool(first and start <= first['at'] <= end)
                if e and start <= e['at'] <= end and not e['validRisk']: g['invalidRiskSignals'] += 1
                if entry_in:
                    g['entries'] += 1; g['entryCohorts'][e['cohort']] += 1
                    ec = g['entryCoverageByCohort'].setdefault(e['cohort'], {'entries': 0, 'covered': 0, 'early1to2Sessions': 0, 'warningWasTwo': 0})
                    ec['entries'] += 1
                    early = bool(first and first['at'] < e['at'] and e['activeAtSignal'])
                    if early and not warning_in: g['entriesWithEarlierOutOfWindowWarning'] += 1
                    if early and warning_in:
                        g['coveredEntries'] += 1
                        ec['covered'] += 1
                        ec['warningWasTwo'] += first['features']['cohort'] == 'two'
                        lead = e['sourceIndex']-first['features']['sourceIndex']
                        days = session_at(e['at'])-session_at(first['at'])
                        g['leadBars'].append(lead); g['leadSessions'].append(days)
                        if r.get('rawBreakIndex') is not None:
                            g['rawBreakLeadBars'].append(r['rawBreakIndex']-first['features']['sourceIndex'])
                        if r.get('touchIndex') is not None and r['touchAt'] <= e['at']:
                            before_touch = r['touchIndex']-first['features']['sourceIndex']
                            g['firstTouchLeadBars'].append(before_touch)
                            if before_touch > 0: g['coveredBeforeFirstTouch'] += 1
                        if 1 <= days <= 2:
                            g['covered1to2Sessions'] += 1; ec['early1to2Sessions'] += 1
                    if first and not e['activeAtSignal']: g['afterClosedWatchEntries'] += 1
                # Count deliveries once per episode/family/close: simultaneous
                # stage 2+3 is one high-priority briefing, not two messages.
                for at in {w['at'] for w in ws if start <= w['at'] <= end}:
                    g['daily'][datetime.fromtimestamp(at, NY).date().isoformat()] += 1
                if not warning_in: continue
                g['warnings'] += 1; g['warningCohorts'][first['features']['cohort']] += 1
                wc = g['warningResultsByCohort'].setdefault(first['features']['cohort'], {'warnings': 0, 'confirmed': 0, 'fizzled': 0, 'censored': 0})
                wc['warnings'] += 1
                approach = 'active' if first['features']['activeApproach'] is True else 'passive' if first['features']['activeApproach'] is False else 'unknown'
                g['warningApproach'][approach] += 1
                outcome = r['outcome']
                if entry_in and e['activeAtSignal'] and first['at'] < e['at']:
                    g['confirmed'] += 1; g['confirmedApproach'][approach] += 1
                    wc['confirmed'] += 1
                    if first['snapshot']['line']['id'] == e['lineId']: g['sameLineConfirmations'] += 1
                elif outcome['at'] > end or outcome['censored'] or outcome['reason'] == 'data_end':
                    g['censored'] += 1
                    wc['censored'] += 1
                else:
                    g['fizzled'] += 1; wc['fizzled'] += 1
    result = []
    for g in groups.values():
        bar_leads, session_leads = g.pop('leadBars'), g.pop('leadSessions')
        g['recallPct'] = 100*g['coveredEntries']/g['entries'] if g['entries'] else None
        g['early1to2SessionRecallPct'] = 100*g['covered1to2Sessions']/g['entries'] if g['entries'] else None
        g['confirmedWarningPct'] = 100*g['confirmed']/g['warnings'] if g['warnings'] else None
        known = g['confirmed']+g['fizzled']
        g['fizzlePctAmongResolved'] = 100*g['fizzled']/known if known else None
        g['medianLeadBars'] = statistics.median(bar_leads) if bar_leads else None
        g['medianLeadSessions'] = statistics.median(session_leads) if session_leads else None
        for field, label in (('rawBreakLeadBars', 'medianRawBreakLeadBars'), ('firstTouchLeadBars', 'medianFirstTouchLeadBars')):
            values = g.pop(field); g[label] = statistics.median(values) if values else None
        daily = [g['daily'][d] for d in sorted(dates)]
        g['messagesPerSession'] = statistics.mean(daily) if daily else None
        g['peakMessagesPerSession'] = max(daily, default=0)
        for field in ('warningCohorts', 'entryCohorts', 'daily', 'warningApproach', 'confirmedApproach'): g[field] = dict(g[field])
        result.append(g)
    return {'planId': plan['id'], 'symbols': len(blocks), 'sessions': len(dates), 'groups': result,
            'eligibility': {w['name']: sum(b['eligibility'][w['name']] for b in blocks) for w in plan['windows']},
            'limitations': plan['limitations']}


def evaluate(root, plan):
    checked(plan)
    result = describe(plan, [load_block(root, plan, s) for s in plan['symbols']])
    write(Path(root)/'results.json', result)
    return result


def review(root, episode, family, mode, until=None):
    """Local manual preferences only; never remove cases from research metrics."""
    if family not in (*FAMILIES, 'all') or mode not in ('mute', 'unmute', 'snooze'):
        raise DataError('Ungültige Stummschaltung.', 400)
    plan = checked(read(Path(root)/'plan.json'))
    if not any(any(e['id'] == episode for e in load_block(root, plan, s)['episodes']) for s in plan['symbols']):
        raise DataError('Episode nicht in dieser Studie.', 404)
    if mode == 'snooze' and (type(until) is not int or until <= time.time()):
        raise DataError('Snooze benötigt einen zukünftigen Zeitpunkt.', 400)
    path = Path(root)/'reviews.json'
    values = read(path) if path.exists() else {}
    values[episode+':'+family] = {'mode': mode, 'until': until, 'updatedAt': int(time.time())}
    write(path, values)
    return values[episode+':'+family]


def briefing(root, plan, symbol, policy, *, at=None):
    block = load_block(root, plan, symbol)
    preferences = read(Path(root)/'reviews.json') if (Path(root)/'reviews.json').exists() else {}
    at = int(time.time()) if at is None else at
    window = next((w for w in plan['windows'] if timestamp(w['start']) <= at <= timestamp(w['end'], upper=True)), None)
    if window is None or not block['eligibility'].get(window['name'], False): return []
    items = []
    for r in block['records']:
        if r['policy'] != policy: continue
        choices = [preferences.get(r['episodeId']+':'+family, {}) for family in ('all', r['family'])]
        if any(p.get('mode') == 'mute' or p.get('mode') == 'snooze' and p.get('until', 0) > at for p in choices): continue
        warnings = [w for w in r['warnings'] if w['at'] <= at]
        if not warnings: continue
        if r['outcome']['at'] <= at: continue
        warning = max(warnings, key=lambda w: (w['at'], w['stage']))
        # Deliberately omit future entry/outcome fields from an as-of briefing.
        items.append({k: r[k] for k in ('id', 'symbol', 'episodeId', 'family', 'datasetId')} | {'warning': warning})
    return sorted(items, key=lambda r: (-r['warning']['at'], -r['warning']['stage'], r['id']))
