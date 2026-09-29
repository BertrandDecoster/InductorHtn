"""Per-level quality.json config for the loadout-sweep harness.

Example (see prototypes/fortress-loadout/quality.json):
{
  "level": "level.htn",
  "memoryBudgetBytes": 268435456,
  "choice": {"kind": "pair-loadout", "poolQuery": "equippableSkill(?s).",
             "slots": 2,
             "injectFacts": ["equipped(player, {0})", "equipped(companion, {1})"]},
  "goals": {"challenges": [{"name": "...", "goal": "...()."}, ...],
            "full": "solveLevel().", "playRoot": "playLevel()."},
  "metadata": {"challengeAtoms": "challengeAtom(?c, ?a).",
               "atomMethods": "atomMethod(?a, ?m).",
               "resolveMarker": "opResolveAtom",
               "markerRequiredFor": ["...challenge names..."]},
  "properties": {"P1_choke": {"severity": "error", "minLoadoutsPerChallenge": 6},
                 "depth": {"severity": "warn", "min": 3, "max": 5}, ...}
}

severity: "error" (regression gate, non-zero exit), "warn" (aspirational,
reported only), "off" (skipped).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SEVERITIES = ("error", "warn", "off")


@dataclass
class ChoiceSpec:
    kind: str
    pool_query: str
    slots: int
    inject_facts: List[str]


@dataclass
class MetadataSpec:
    challenge_atoms: Optional[str] = None
    atom_methods: Optional[str] = None
    resolve_marker: str = "opResolveAtom"
    marker_required_for: List[str] = field(default_factory=list)


@dataclass
class PropertyCfg:
    name: str
    severity: str
    params: Dict = field(default_factory=dict)


@dataclass
class LevelConfig:
    level: Path
    memory_budget: int
    choice: ChoiceSpec
    challenges: List[Tuple[str, str]]
    full_goal: Optional[str]
    play_root: Optional[str]
    metadata: MetadataSpec
    properties: Dict[str, PropertyCfg]


def load_config(path) -> LevelConfig:
    path = Path(path)
    raw = json.loads(path.read_text(encoding="utf-8"))

    level = Path(raw["level"])
    if not level.is_absolute():
        level = path.parent / level

    choice_raw = raw.get("choice") or {}
    choice = ChoiceSpec(
        kind=choice_raw.get("kind", "pair-loadout"),
        pool_query=choice_raw["poolQuery"],
        slots=int(choice_raw.get("slots", 2)),
        inject_facts=list(choice_raw["injectFacts"]),
    )
    if choice.kind != "pair-loadout":
        raise ValueError(f"unsupported choice.kind: {choice.kind}")
    if len(choice.inject_facts) != choice.slots:
        raise ValueError("choice.injectFacts must have one template per slot")

    goals_raw = raw.get("goals") or {}
    challenges = [(c["name"], c["goal"]) for c in goals_raw.get("challenges", [])]
    if not challenges:
        raise ValueError("goals.challenges must list at least one challenge")

    meta_raw = raw.get("metadata") or {}
    metadata = MetadataSpec(
        challenge_atoms=meta_raw.get("challengeAtoms"),
        atom_methods=meta_raw.get("atomMethods"),
        resolve_marker=meta_raw.get("resolveMarker", "opResolveAtom"),
        marker_required_for=list(meta_raw.get("markerRequiredFor", [])),
    )

    properties: Dict[str, PropertyCfg] = {}
    for name, spec in (raw.get("properties") or {}).items():
        severity = spec.get("severity", "warn")
        if severity not in SEVERITIES:
            raise ValueError(f"property {name}: bad severity {severity!r}")
        params = {k: v for k, v in spec.items() if k != "severity"}
        properties[name] = PropertyCfg(name=name, severity=severity, params=params)

    return LevelConfig(
        level=level,
        memory_budget=int(raw.get("memoryBudgetBytes", 256 * 1024 * 1024)),
        choice=choice,
        challenges=challenges,
        full_goal=goals_raw.get("full"),
        play_root=goals_raw.get("playRoot"),
        metadata=metadata,
        properties=properties,
    )
