"""Bands, weights and caps for the fun metrics.

Everything tunable lives in `metrics.json` next to this file, so calibrating
the metrics means editing data, not code. `Config` is a thin typed reader with
dotted-path lookup and a merge hook for per-level overrides.
"""

import json
import os
from typing import Any, Dict, List, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_PATH = os.path.join(_HERE, "metrics.json")


class Config:
    """Read-only view over metrics.json with dotted-path access.

        cfg = Config.load()
        cfg.band("f1_multiplicity.strategy_classes_min")   # -> 2
        cfg.cap("max_plans")                               # -> 5000
    """

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    # ------------------------------------------------------------- loading

    @classmethod
    def load(cls, path: Optional[str] = None) -> "Config":
        with open(path or DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as f:
            return cls(json.load(f))

    def with_overrides(self, overrides: Dict[str, Any]) -> "Config":
        """Return a copy with `overrides` deep-merged on top.

        Used for per-level tuning and for tests that need a tighter cap
        without mutating the shared default.
        """
        merged = _deep_merge(json.loads(json.dumps(self._data)), overrides)
        return Config(merged)

    # -------------------------------------------------------------- access

    def get(self, dotted: str, default: Any = None) -> Any:
        node: Any = self._data
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def band(self, dotted: str, default: Any = None) -> Any:
        return self.get(f"bands.{dotted}", default)

    def cap(self, name: str, default: Any = None) -> Any:
        return self.get(f"caps.{name}", default)

    def weight(self, family: str) -> float:
        return float(self.get(f"weights.{family}", 0.0))

    def verdict_score(self, verdict: str) -> Optional[float]:
        return self.get(f"verdict_scores.{verdict}")

    @property
    def fingerprint_layers(self) -> List[str]:
        return list(self.get("fingerprint_layers", ["goals", "strategies"]))

    @property
    def fingerprint_max_depth(self) -> int:
        """How deep a method choice can sit and still count as a *strategy*."""
        return int(self.get("fingerprint_max_depth", 2))

    @property
    def player_atom(self) -> str:
        return str(self.get("player_atom", "player"))

    @property
    def raw(self) -> Dict[str, Any]:
        return self._data


def _deep_merge(base: Dict[str, Any], top: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in top.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base
