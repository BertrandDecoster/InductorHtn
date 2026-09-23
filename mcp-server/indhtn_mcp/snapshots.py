"""Named state snapshots for HtnSession.

A snapshot records the current facts and the count of loaded sources at
capture time. Restoring rebuilds a fresh planner, replays the sources up to
``sources_count``, and then reconciles facts to match the snapshot using
``retract`` / ``HtnCompileCustomVariables`` calls — no one-shot synthesised
operators.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Snapshot:
    name: str
    facts: list[str]
    sources_count: int
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def to_summary(self) -> dict:
        return {
            "name": self.name,
            "factsCount": len(self.facts),
            "sourcesCount": self.sources_count,
            "createdAt": self.created_at.isoformat(),
        }
