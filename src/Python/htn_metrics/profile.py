"""Assemble the family results for one level into a `FunProfile`.

The profile is the deliverable: six verdicts, the numbers behind them, and a
composite that is withheld whenever it would be dishonest.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence

from .canonical import classify
from .config import Config
from .extract import PlanSpace, extract_plan_space, load_level_spec
from .metrics import FAIL, PASS, SKIP, WARN, FamilyResult, compute_all


@dataclass
class FunProfile:
    """One level's scorecard."""

    level_id: str
    goal: str
    families: List[FamilyResult] = field(default_factory=list)
    plan_count: int = 0
    strategy_classes: List[Dict[str, Any]] = field(default_factory=list)
    truncated: bool = False
    truncation_reason: str = ""
    notes: List[str] = field(default_factory=list)
    fun_score: Optional[float] = None
    score_withheld_reason: str = ""

    @property
    def overall(self) -> str:
        """Worst family verdict; `skip` families do not count against a level."""
        order = [SKIP, PASS, WARN, FAIL]
        worst = PASS
        for family in self.families:
            if family.verdict == SKIP:
                continue
            if order.index(family.verdict) > order.index(worst):
                worst = family.verdict
        return worst

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level_id": self.level_id,
            "goal": self.goal,
            "plan_count": self.plan_count,
            "truncated": self.truncated,
            "truncation_reason": self.truncation_reason,
            "overall": self.overall,
            "fun_score": self.fun_score,
            "score_withheld_reason": self.score_withheld_reason,
            "families": [f.to_dict() for f in self.families],
            "strategy_classes": self.strategy_classes,
            "notes": self.notes,
        }


def composite_score(families: Sequence[FamilyResult], cfg: Config) -> Optional[float]:
    """Weighted mean of per-family verdict scores, renormalised over the
    families that actually ran.

    The least trustworthy number this tool produces - it exists so a fitness
    function can be derived later, not because fun is one-dimensional.
    """
    total_weight = 0.0
    accumulated = 0.0
    for family in families:
        value = cfg.verdict_score(family.verdict)
        if value is None:
            continue
        weight = cfg.weight(family.key)
        total_weight += weight
        accumulated += weight * value
    if total_weight <= 0:
        return None
    return round(accumulated / total_weight, 3)


def build_profile(
    level: str,
    cfg: Optional[Config] = None,
    ablation: Optional[Dict[str, Any]] = None,
    lattice: Optional[Dict[str, Any]] = None,
    space: Optional[PlanSpace] = None,
) -> FunProfile:
    """Plan a level (unless a `PlanSpace` is supplied) and score it."""
    cfg = cfg or Config.load()
    if space is None:
        spec = load_level_spec(level)
        space = extract_plan_space(
            level,
            max_plans=cfg.cap("max_plans", 5000),
            memory_budget=cfg.cap("memory_budget_bytes", 0) or 0,
            spec=spec,
        )

    families = compute_all(space, cfg, ablation=ablation, lattice=lattice)
    classes = classify(space, cfg.fingerprint_layers, cfg.fingerprint_max_depth)

    profile = FunProfile(
        level_id=space.level_id,
        goal=space.goal,
        families=families,
        plan_count=space.plan_count,
        strategy_classes=[c.to_dict() for c in classes],
        truncated=space.truncated,
        truncation_reason=space.truncation_reason,
        notes=list(space.notes),
    )

    if space.truncated:
        profile.score_withheld_reason = (
            "plan space truncated - metrics computed over a partial plan set are "
            "meaningless, so no composite is emitted"
        )
    else:
        profile.fun_score = composite_score(families, cfg)
    return profile


def profile_level(
    level: str,
    ablate: bool = False,
    loadouts: bool = False,
    cfg: Optional[Config] = None,
    progress: Optional[Callable[[str], None]] = None,
) -> FunProfile:
    """Plan a level, run the counterfactuals asked for, and score it.

    The one entry point the CLI, the MCP tools and `verify` share. The
    counterfactual harness caches to disk, so it is closed in a `finally`:
    a probe that raises must not lose the probes that ran before it.
    """
    from .counterfactual import CounterfactualHarness, run_ablation, run_loadouts

    cfg = cfg or Config.load()
    spec = load_level_spec(level)
    space = extract_plan_space(
        level,
        max_plans=cfg.cap("max_plans", 5000),
        memory_budget=cfg.cap("memory_budget_bytes", 0) or 0,
        spec=spec,
    )

    ablation = lattice = None
    if ablate or loadouts:
        harness = CounterfactualHarness(spec, cfg)
        try:
            if ablate:
                if progress:
                    progress("running ablation (one re-plan per fact)...")
                ablation = run_ablation(harness, space, cfg)
            if loadouts:
                if progress:
                    progress("enumerating loadouts...")
                lattice = run_loadouts(harness, space, cfg)
        finally:
            harness.close()

    return build_profile(level, cfg=cfg, ablation=ablation, lattice=lattice, space=space)
