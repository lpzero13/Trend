import random
import unittest
from datetime import datetime, timezone
from dataclasses import replace

from alpaca import Bar, bar_end, parse_bars
from trendlines import DAY, Rules, analyze, build, choose, cut, pair


def bars_from(values, *, step=DAY):
    start = int(datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp())
    return [Bar(start + i * step, start + i * step + step,
                value, value + 1, value - 1, value, 100) for i, value in enumerate(values)]


def brute_chain(bars, upper, rules):
    """Independent O(N²) reference: search the envelope's next slope directly."""
    level = lambda i: bars[i].high if upper else bars[i].low
    anchor = max(range(len(bars)), key=level) if upper else min(range(len(bars)), key=level)
    result = []
    while anchor < len(bars) - 1:
        best = None
        slope = None
        for b in range(anchor + 1, len(bars)):
            value = (level(b) - level(anchor)) / ((b-anchor) if rules.basis == "bars" else (bars[b].time-bars[anchor].time))
            if slope is None or (value >= slope if upper else value <= slope):
                best, slope = b, value
        if not (slope < 0 if upper else slope > 0):
            break
        if len(bars) - 1 - best < rules.pullback_bars:
            break
        if any((level(best + k) >= level(best) if upper else level(best + k) <= level(best))
               for k in range(1, rules.pullback_bars + 1)):
            break
        result.append((bars[anchor].time, bars[best].time))
        anchor = best
    return result


class GeometryTests(unittest.TestCase):
    def test_matches_independent_envelope_search(self):
        rng = random.Random(20261017)
        rules = Rules()
        for _ in range(120):
            bars = bars_from([rng.uniform(20, 250) for _ in range(90)])
            # Uneven elapsed times must not alter a candle-based envelope.
            offset = 0
            irregular = []
            for bar in bars:
                offset += rng.choice([0, 0, 2 * DAY])
                irregular.append(replace(bar, time=bar.time+offset, end=bar.end+offset))
            bars = irregular
            for upper in (True, False):
                rays = build(bars, upper, rules)
                self.assertEqual([(r.a_time, r.b_time) for r in rays], brute_chain(bars, upper, rules))
                for ray in rays:
                    self.assertAlmostEqual(ray.value(ray.b_time), ray.b_price)
                    # Every ray must also envelope all later wicks, beyond anchor B.
                    for bar in bars:
                        if bar.time >= ray.a_time:
                            self.assertFalse(cut(bar.high if upper else bar.low, ray.value(bar.time), upper, rules))

    def test_followup_confirmation_is_required(self):
        self.assertEqual(build(bars_from([100, 97, 96]), True, Rules()), [])
        self.assertTrue(build(bars_from([100, 99, 95]), True, Rules()))

    def test_collinear_contacts_and_minimum_span(self):
        bars = bars_from([100, 99, 98, 97, 95], step=4 * DAY)
        ray = build(bars, True, Rules())[0]
        self.assertEqual(ray.contacts, 4)
        self.assertEqual(ray.span_days, 12)
        self.assertTrue(ray.qualified)
        short = build(bars_from([100, 99, 98, 97, 95], step=3600), True, Rules())[0]
        self.assertFalse(short.qualified)

    def test_quality_selection_and_inner_selection(self):
        rays = build(bars_from([100, 99, 98, 97, 95, 90, 80, 60]), True, Rules())
        self.assertGreaterEqual(len(rays), 2)
        rays[0] = replace(rays[0], qualified=True)
        for i in range(1, len(rays)):
            rays[i] = replace(rays[i], qualified=False)
        self.assertIs(choose(rays, Rules()), rays[0])
        self.assertIs(choose(rays, Rules(selection='inner')), rays[-1])

    def test_zero_slope_is_not_a_trend(self):
        for upper in (True, False):
            self.assertEqual(build(bars_from([100] * 8), upper, Rules()), [])

    def test_does_not_modify_input(self):
        bars = bars_from([100, 99, 97, 94, 96])
        original = list(bars)
        first = analyze(bars, '4h', bars[-1].time)
        second = analyze(bars, '4h', bars[-1].time)
        self.assertEqual(first, second)
        self.assertEqual(bars, original)

    def test_projection_interpolates_between_source_candles(self):
        bars = bars_from([100, 99, 95])
        ray = build(bars, True, Rules())[0]
        self.assertAlmostEqual(ray.value(ray.a_time + DAY // 2), 100.5)


class DataTests(unittest.TestCase):
    def test_validate_sort_deduplicate_and_drop_unfinished(self):
        row = {'t': '2026-10-16T14:00:00Z', 'o': 100, 'h': 103, 'l': 99, 'c': 102, 'v': 100}
        rows = [dict(row, t='2026-10-16T16:00:00Z'), row, dict(row, c=101), dict(row, h=98)]
        cutoff = int(datetime(2026, 10, 16, 15, tzinfo=timezone.utc).timestamp())
        bars, quality = parse_bars(rows, '1h', cutoff)
        self.assertEqual(len(bars), 1)
        self.assertEqual(bars[0].close, 101)
        self.assertEqual(quality, {'rejected': 1, 'duplicates': 1, 'unfinished': 1})

    def test_daily_close_respects_daylight_saving(self):
        summer = int(datetime(2026, 7, 1, 4, tzinfo=timezone.utc).timestamp())
        winter = int(datetime(2026, 1, 2, 5, tzinfo=timezone.utc).timestamp())
        self.assertEqual(datetime.fromtimestamp(bar_end(summer, '1D'), timezone.utc).hour, 20)
        self.assertEqual(datetime.fromtimestamp(bar_end(winter, '1D'), timezone.utc).hour, 21)

    def test_incomplete_candle_is_not_analyzed(self):
        cutoff = int(datetime(2026, 10, 16, 15, tzinfo=timezone.utc).timestamp())
        rows = [{'t': '2026-10-16T14:00:00Z', 'o': 100, 'h': 102, 'l': 99, 'c': 101, 'v': 100}]
        complete, _ = parse_bars(rows, '1h', cutoff)
        future, _ = parse_bars(rows + [dict(rows[0], t='2026-10-16T16:00:00Z', h=1000)], '1h', cutoff)
        self.assertEqual(complete, future)


if __name__ == '__main__':
    unittest.main()
