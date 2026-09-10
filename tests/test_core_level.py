"""The flagship level, measured.

`levels/grease_trap` is the first level on the core vocabulary and the one
the metrics are meant to steer. These tests pin the parts of its scorecard
that come from the metrics seeing the ruleset correctly, so a change to
either side that breaks the reading shows up here.

Run:  python -m pytest tests/test_core_level.py -v
"""

import os

from test_fun_metrics import PROJECT_ROOT, family  # noqa: E402

from htn_metrics.config import Config  # noqa: E402
from htn_metrics.canonical import classify  # noqa: E402
from htn_metrics.extract import extract_plan_space, load_level_spec  # noqa: E402
from htn_metrics.profile import build_profile  # noqa: E402

LEVEL = os.path.join(PROJECT_ROOT, "levels", "grease_trap")


def _profile():
    spec = load_level_spec(LEVEL)
    space = extract_plan_space(LEVEL, spec=spec)
    return space, build_profile(LEVEL, cfg=Config.load(), space=space)


def test_the_two_strategies_are_the_two_ideas():
    """One class per strategy, named by the strategy and nothing below it."""
    space, _profile_ = _profile()
    cfg = Config.load()
    classes = classify(space, cfg.fingerprint_layers, cfg.fingerprint_max_depth)
    labels = sorted(c.label for c in classes)
    assert len(labels) == 2, labels
    assert any("theBurn" in label for label in labels), labels
    assert any("theSlipstream" in label for label in labels), labels
    for label in labels:
        assert "gather" not in label and "finishTrap" not in label, (
            f"helpers inside a strategy component are not ideas: {label}"
        )


def test_freeze_then_snare_then_strike_is_a_chain():
    """Consequences applied through allOf methods must count: the freeze
    enables the snare, the snare enables the strike."""
    _space, profile = _profile()
    f3 = family(profile, "f3_depth")
    assert f3.metrics["causal_depth"]["best_class"] >= 3, f3.metrics


def test_the_player_is_required_and_decides():
    _space, profile = _profile()
    f6 = family(profile, "f6_player")
    assert f6.metrics["soloable_plans"] == 0
    assert f6.metrics["player_decision_points"] >= 1
    assert f6.metrics["teamwork_edge_ratio"] >= 0.3
