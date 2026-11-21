"""Web-only checkpoints of canonical fan *input* state, never cached geometry.

Clear the side caches before every snapshot, matching a fresh canonical analyze.
Checkpoint pushes do not inspect future quotes, and research code is untouched.
"""
from collections import OrderedDict, deque
from copy import copy
from fan_geometry import create_engine
from models import DataError


class Feeder:
    def __init__(self, symbol):
        self.symbol = symbol
        self.current = OrderedDict()
        self.checkpoints = OrderedDict()

    @staticmethod
    def clone(engine):
        # Bars, pivots, rules and row tuples are immutable. Copy only mutable
        # containers; deep-copying thousands of frozen bars costs far more.
        result = copy(engine)
        result.rows = deque(engine.rows)
        result.pivots = {side: deque(values) for side, values in engine.pivots.items()}
        result.recent = deque(engine.recent, maxlen=engine.recent.maxlen)
        result.tr_seed = list(engine.tr_seed)
        result.cache = {}
        return result

    def analyze(self, rows, timeframe, rules, gaps, clean_atr):
        key = timeframe, rules
        count = len(rows)
        current = self.current.get(key)
        if current is None or current.index >= count:
            eligible = [k for k in self.checkpoints if k[0] == key and k[1] <= count]
            current = self.clone(self.checkpoints[max(eligible, key=lambda k: k[1])]) if eligible else create_engine(self.symbol, timeframe, rules)
        for i in range(current.index+1, count):
            if i in gaps:
                current.reset_history()
            current.push(rows[i])
            if (i+1) % 128 == 0 and count-i <= 256:
                current.cache.clear()
                checkpoint = key, i+1
                if checkpoint not in self.checkpoints:
                    self.checkpoints[checkpoint] = self.clone(current)
                    while len(self.checkpoints) > 12:
                        self.checkpoints.popitem(last=False)
        self.current[key] = current
        self.current.move_to_end(key)
        while len(self.current) > 4:
            self.current.popitem(last=False)
        current.cache.clear()
        state = current.snapshot()
        if not state['ready']:
            raise DataError('Zu wenig ATR-Vorlauf für den Fächer.', 404)
        red, green = state['red'], state['green']
        if rules.algorithm == 'master':
            state['checkWindow'] = current.window_context(clean_atr)
        # Same output contract as fan_geometry.analyze, checked against it in tests.
        return {**state, 'basis': 'bars', 'sourceTimes': [b.time for b in rows],
                'outerRed': [r for r in state['reds'] if not red or r['id'] != red['id']],
                'outerGreen': [r for r in state['greens'] if not green or r['id'] != green['id']],
                'retest': None, 'event': None,
                'status': 'Fächer qualifiziert' if red and red['qualified'] else 'Fächer vorläufig' if red else 'Widerstand fehlt',
                'distance': (rows[-1].close-green['value'])/rows[-1].close*100 if green else None,
                'partial': state['capped'], 'lookbackDays': rules.lookback_days,
                'selection': 'fan_'+rules.roots, 'dataErrors': False}
