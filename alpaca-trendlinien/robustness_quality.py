"""Read-only, window-specific checks for normalized offline research inputs."""
from collections import Counter
from datetime import datetime
import math

from lab_data import session_bounds
from lab_metrics import expected_grid
from models import NY


def check_frames(frames, start, end):
    """No imputation, corrections or future-outcome-based exclusions."""
    errors = Counter()
    counts = {}
    for tf in ('5m', '1h', '4h', '1D'):
        rows = frames.get(tf, [])
        counts[tf] = len(rows)
        for i, b in enumerate(rows):
            if i and (rows[i-1].time >= b.time or rows[i-1].end > b.time):
                errors['duplicate_or_overlap'] += 1
            if (not all(math.isfinite(v) for v in (b.open,b.high,b.low,b.close,b.volume))
                    or min(b.open,b.low,b.close) <= 0 or b.volume < 0
                    or b.low > min(b.open,b.close) or b.high < max(b.open,b.close)):
                errors['invalid_ohlcv'] += 1
    fine = {b.time:b for b in frames.get('5m', [])}
    expected = list(expected_grid(start,end))
    absent = [t for t in expected if t not in fine]
    for b in fine.values():
        bounds = session_bounds(str(datetime.fromtimestamp(b.time,NY).date()))
        if not bounds or not (bounds[0] <= b.time < b.end <= bounds[1]) or b.end-b.time != 300 or (b.time-bounds[0]) % 300:
            errors['off_session_fine'] += 1
    # Recompute every stored aggregate directly, independently of resample_regular.
    checked = Counter()
    for tf in ('1h','4h','1D'):
        for b in frames.get(tf, []):
            parts = [fine.get(t) for t in range(b.time,b.end,300)]
            if not parts or any(p is None for p in parts):
                errors['aggregate_without_complete_fine'] += 1
                continue
            values = (parts[0].open,max(p.high for p in parts),min(p.low for p in parts),parts[-1].close,sum(p.volume for p in parts))
            if not all(math.isclose(a,c,rel_tol=1e-9,abs_tol=1e-7) for a,c in zip(values,(b.open,b.high,b.low,b.close,b.volume))):
                errors['aggregate_mismatch'] += 1
            checked[tf] += 1
    daily = frames.get('1D', [])
    jumps = [{'at':b.time,'openGapPct':100*(b.open/a.close-1)} for a,b in zip(daily,daily[1:]) if abs(b.open/a.close-1) >= .25]
    return {'passedStructural':not errors,'errors':dict(errors),'counts':counts,
            'expectedFineBars':len(expected),'missingFineBars':len(absent),'missingExamples':absent[:8],
            'fineCoveragePct':100*(len(expected)-len(absent))/len(expected) if expected else None,
            'aggregatesRecomputed':dict(checked),'largeGapWarnings':jumps,
            'corporateActionsVerified':False,'dividendsIncluded':False,
            'wholeShareHistoricalPricesVerified':False,
            'meaning':'Missing bars retained as gaps; large jumps are warnings, not confirmed splits. Split-adjusted prices do not verify historical whole-share affordability.'}
