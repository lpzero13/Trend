"""Offline early-warning experiment and local episode preferences; never sends messages."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from early_warning_study import prepare, build, checked, evaluate, review, briefing
from fan_study import timestamp
from strategy_screen import read
from strategy_run_lock import study_lock


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('all', 'prepare', 'build', 'evaluate', 'review', 'briefing', 'show'))
    parser.add_argument('--root', required=True)
    parser.add_argument('--source')
    parser.add_argument('--symbols', help='Comma-separated subset of the frozen source universe')
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--episode')
    parser.add_argument('--family', default='all')
    parser.add_argument('--mode', choices=('mute', 'unmute', 'snooze'))
    parser.add_argument('--until')
    parser.add_argument('--symbol')
    parser.add_argument('--policy', default='distance:1')
    parser.add_argument('--asof')
    args = parser.parse_args()
    emit = lambda value: print(json.dumps(value, ensure_ascii=False), flush=True)
    with study_lock(args.root):
        if args.phase in ('all', 'prepare'):
            if not args.source: parser.error('--source is required')
            plan = prepare(args.root, args.source, symbols=args.symbols.split(',') if args.symbols else None)
        else: plan = checked(read(Path(args.root)/'plan.json'))
        if args.phase in ('all', 'build'): build(args.root, plan, args.workers, emit)
        if args.phase in ('all', 'evaluate'):
            result = evaluate(args.root, plan)
            emit({'planId': plan['id'], 'symbols': result['symbols'], 'groups': len(result['groups']),
                  'results': str(Path(args.root)/'results.json')})
        if args.phase == 'review': emit(review(args.root, args.episode, args.family, args.mode, timestamp(args.until) if args.until else None))
        if args.phase == 'briefing': emit(briefing(args.root, plan, args.symbol, args.policy, at=timestamp(args.asof) if args.asof else None))
        if args.phase == 'show':
            from early_warning_study import load_block
            emit([r for r in load_block(args.root, plan, args.symbol)['records'] if r['episodeId'] == args.episode
                  and r['policy'] == args.policy and (args.family == 'all' or r['family'] == args.family)])


if __name__ == '__main__': main()
