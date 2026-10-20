"""Physical signal identity survives immutable dataset refreshes/revisions.

Event keys deduplicate signal notifications, not trades or outcome rows. Dataset
and entry/contract hashes remain the exact versioned provenance. Pending and
observed-open views of the same confirmation share this key.
"""
from datasets import digest


def event_key(material, profile, family, signal_at):
    return digest({"namespace": "tori-safety-signal-1", "symbol": material["symbol"],
                   "feed": material.get("feed"), "adjustment": material.get("adjustment"),
                   "timeframe": "4h", "profile": profile, "family": family,
                   "signalAt": signal_at})
