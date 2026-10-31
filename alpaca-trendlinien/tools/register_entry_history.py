"""Register an explicitly chosen completed local event study for chart review."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from entry_history import register_study

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("study")
    args = ap.parse_args()
    print(json.dumps(register_study(args.study)), flush=True)
