"""Causal structural identity above the unchanged chart/entry observer.

A changed fitted endpoint, contact count or technical ID is not a new setup.
Rules here are experimental sample construction, not profitability filters.
"""
from copy import deepcopy

from fan_geometry import stable_id

VERSION = "tori-structural-episodes-1"


class Episodes:
    def __init__(self, symbol):
        self.symbol = symbol
        self.anchors, self.lines, self.scenarios = {}, {}, {}
        self.current, self.records = {}, {}

    def observe(self, snapshot):
        if not snapshot or not snapshot.get("ready"):
            return
        for side, name in (("red", "reds"), ("green", "greens")):
            fan = snapshot.get(name, [])
            if not fan:
                continue
            root = fan[0]
            key = (side, root["a_time"], root["a_price"])
            lineage = self.anchors.get(key) or stable_id([VERSION, self.symbol, key])
            # A child becoming the main line inherits the previous fan's origin.
            # Do not merge all historical roots via overlapping old contact sets.
            for line in fan:
                self.lines.setdefault(line["id"], lineage)
                for prefix in ("a", "b"):
                    self.anchors.setdefault((side, line[prefix+"_time"], line[prefix+"_price"]), lineage)

    def _lineage(self, signal):
        line = signal["line"]
        side = "green" if signal["family"] == "safety_bounce" else "red"
        key = (side, line["a_time"], line["a_price"])
        identity = self.lines.get(line["id"]) or self.anchors.get(key)
        if identity is None:
            identity = stable_id([VERSION, self.symbol, key])
            self.anchors[key] = identity
        self.lines.setdefault(line["id"], identity)
        return identity

    def accept(self, found):
        accepted, suppressed = [], []
        # Prefer quality already known on this close, never a future outcome.
        rank = {"qualified": 0, "three_young": 1, "two": 2}
        for s in sorted(found, key=lambda v: (rank.get(v["cohort"], 3), -v["line"]["contacts"], v["id"])):
            at, family = s["signalAt"], s["family"]
            line = s["line"]
            if line["knownAt"] >= at or any(p["known_at"] > at for p in line.get("contactPoints", [])):
                raise ValueError("Future or same-close signal line")
            lineage = self._lineage(s)
            scenario = s.get("scenarioId")
            old_id = self.scenarios.get(scenario) if scenario else None
            episode = self.records.get(old_id) if old_id else self.current.get(lineage)
            reason = "first_structure"
            if episode and old_id is None:
                fresh = {p["time"] for p in line.get("contactPoints", [])
                         if episode["createdAt"] < p["time"] and p["known_at"] < at}
                if len(fresh) >= 2:
                    episode, reason = None, "two_new_confirmed_contacts"
            if episode is None:
                identity = stable_id([VERSION, self.symbol, lineage, at])
                episode = {"id": identity, "lineageId": lineage, "createdAt": at,
                           "reason": reason, "families": {}, "firstLine": deepcopy(line)}
                self.current[lineage] = episode
                self.records[identity] = episode
            if scenario:
                self.scenarios.setdefault(scenario, episode["id"])
            detail = {"signalId": s["id"], "episodeId": episode["id"], "family": family,
                      "signalAt": at, "lineageId": lineage}
            if family in episode["families"]:
                suppressed.append({**detail, "reason": "same_structure_and_entry_family",
                                   "firstSignalId": episode["families"][family]})
                continue
            episode["families"][family] = s["id"]
            accepted.append({**deepcopy(s), "episodeId": episode["id"], "lineageId": lineage,
                             "episodeReason": episode["reason"]})
        return accepted, suppressed
