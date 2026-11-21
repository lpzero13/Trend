"""Web-only reuse of exact legacy pairs inside its unchanged event window.

The common hull/selection/break functions remain authoritative. Never carry
forward an event outside the canonical rolling budget or change its timestamp.
"""
from collections import OrderedDict
from dataclasses import asdict
from trendlines import DAY, rules_for, window_start, pair, detect_break, outer_rays


class Legacy:
    def __init__(self):
        self.pairs = OrderedDict()

    def analyze(self, bars, timeframe, *, data_errors=False):
        rules = rules_for(timeframe)
        def get(count):
            key = timeframe, count
            if key not in self.pairs:
                self.pairs[key] = pair(bars[:count], rules)
            self.pairs.move_to_end(key)
            while len(self.pairs) > 96:
                self.pairs.popitem(last=False)
            return self.pairs[key]
        ending = len(bars)-1
        start = window_start(bars[-1].end, rules.lookback_days)
        window_size = sum(bar.time >= start for bar in bars)
        budget = min(rules.event_bars, max(1, 4000//max(1, window_size)))
        first = max(1, ending-budget)
        previous = get(first+1)
        broken = event = None
        for i in range(first+1, len(bars)):
            current, before = bars[i], bars[i-1]
            red = previous['red']
            step_event, red_break = detect_break(previous, before, current, i, rules,
                partial=bars[0].time > window_start(before.end, rules.lookback_days), data_errors=data_errors)
            if step_event:
                event = step_event
            if red_break:
                broken = {'ray': red, 'time': current.time, 'closedAt': current.end}
            previous = get(i+1)
        red, green = previous['red'], previous['green']
        partial = bars[0].time > start
        status = ('Qualifiziert' if red.qualified and green.qualified else 'Vorläufig') if red and green else 'Linienpaar fehlt'
        reference = bars[-1].time
        if red and green and green.value(reference) >= red.value(reference):
            status = 'Linien gekreuzt'
        if green and bars[-1].close < green.value(reference):
            status = 'Grün unterschritten'
        distance = (bars[-1].close-green.value(reference))/bars[-1].close*100 if green else None
        axis = tuple(bar.time for bar in bars)
        return {'basis': 'bars', 'sourceTimes': list(axis), 'timeframe': timeframe,
                'red': red.output(reference, axis) if red else None,
                'green': green.output(reference, axis) if green else None,
                'outerRed': [r.output(reference, axis) for r in outer_rays(previous['reds'], red)],
                'outerGreen': [r.output(reference, axis) for r in outer_rays(previous['greens'], green)],
                'retest': ({'ray': broken['ray'].output(reference, axis), 'time': broken['time'], 'closedAt': broken['closedAt']}
                           if broken and bars[-1].end-broken['closedAt'] <= 30*DAY else None),
                'event': event, 'status': status, 'distance': distance, 'partial': partial,
                'lookbackDays': rules.lookback_days, 'selection': rules.selection,
                'sourceClose': bars[-1].end, 'sourceFirst': bars[0].time, 'searchedBars': ending-first,
                'dataErrors': data_errors, 'rules': asdict(rules)}
