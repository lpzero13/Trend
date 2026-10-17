"""Portable paths: source can be read-only; all persistent state goes in TORI_DATA_DIR."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def data_dir(root=ROOT):
    value = os.environ.get("TORI_DATA_DIR")
    return Path(value).expanduser().resolve() if value else root / "data"
