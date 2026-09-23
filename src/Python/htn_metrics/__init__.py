"""Fun metrics for HTN levels.

Measures the *shape of the solution space* a level presents to the player -
how many genuinely different ways exist, how deep they are, and which of the
player's X-of-Y choices actually work.

It never claims a level is fun. See `docs/FUN_METRICS.md` for the definition
of every metric, its band, the GDD principle it encodes, and its blind spots.
"""

from .config import Config
from .extract import LevelSpec, Plan, PlanSpace, extract_plan_space, load_level_spec

__all__ = [
    "Config",
    "LevelSpec",
    "Plan",
    "PlanSpace",
    "extract_plan_space",
    "load_level_spec",
]
