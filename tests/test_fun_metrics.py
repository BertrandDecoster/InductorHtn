"""Unit tests for the fun metrics themselves.

Each fixture in `tests/fun_fixtures/` is degenerate by construction - it
isolates exactly one failure mode - and each test asserts two things:

  1. the family that *should* catch it does, with the offending metric in the
     expected range, and
  2. the families that should stay clean do.

That second half is what makes these calibration tests rather than smoke
tests. A metric that flags everything is as useless as one that flags nothing,
so a fixture tripping a family it was not built to trip is a real failure.

This is stronger grounding than ranking real levels: no current level is a
positive exemplar, so there is no agreed ordering to calibrate against.
`reference_good` supplies the other end - a level built to the design
principles, which must pass every family.

Run:  python -m pytest tests/test_fun_metrics.py -v
"""

import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
FIXTURES = os.path.join(_HERE, "fun_fixtures")

sys.path.insert(0, os.path.join(PROJECT_ROOT, "src", "Python"))

# indhtnpy locates the shared library relative to the working directory, so
# tests run from the build output. Everything else uses absolute paths.
_BUILD_DIR = os.path.join(PROJECT_ROOT, "build", "Release")
if os.path.isdir(_BUILD_DIR):
    os.chdir(_BUILD_DIR)

from htn_metrics.config import Config  # noqa: E402
from htn_metrics.counterfactual import (  # noqa: E402
    CounterfactualHarness, run_ablation, run_loadouts,
)
from htn_metrics.extract import extract_plan_space, load_level_spec  # noqa: E402
from htn_metrics.profile import build_profile  # noqa: E402

_CACHE = {}


def profile_for(fixture, ablate=False, loadouts=False):
    """Build (and memoise) a fixture's profile. Planning is the slow part."""
    key = (fixture, ablate, loadouts)
    if key in _CACHE:
        return _CACHE[key]

    cfg = Config.load()
    path = os.path.join(FIXTURES, fixture)
    spec = load_level_spec(path)
    space = extract_plan_space(path, spec=spec, max_plans=cfg.cap("max_plans", 5000))

    ablation = lattice = None
    if ablate or loadouts:
        harness = CounterfactualHarness(spec, cfg)
        if ablate:
            ablation = run_ablation(harness, space, cfg)
        if loadouts:
            lattice = run_loadouts(harness, space, cfg)
        harness.close()

    profile = build_profile(
        path, cfg=cfg, ablation=ablation, lattice=lattice, space=space
    )
    _CACHE[key] = profile
    return profile


def family(profile, key):
    for item in profile.families:
        if item.key == key:
            return item
    raise AssertionError(f"no family {key} in profile")


def assert_clean(profile, *keys):
    """The named families must not fail - the fixture is not about them."""
    for key in keys:
        result = family(profile, key)
        assert result.verdict in ("pass", "warn", "skip"), (
            f"{profile.level_id}: {key} unexpectedly FAILED "
            f"({'; '.join(result.findings)})"
        )


def assert_fails(profile, key):
    result = family(profile, key)
    assert result.verdict == "fail", (
        f"{profile.level_id}: expected {key} to FAIL, got {result.verdict} "
        f"({'; '.join(result.findings) or 'no findings'})"
    )
    return result


def assert_not_pass(profile, key):
    result = family(profile, key)
    assert result.verdict in ("fail", "warn"), (
        f"{profile.level_id}: expected {key} to be flagged, got {result.verdict}"
    )
    return result


# ==========================================================================
# F1 - Multiplicity
# ==========================================================================

def test_single_path_trips_f1_one_idea():
    """One route, one plan: F1 must fail on strategy_classes."""
    profile = profile_for("single_path")
    result = assert_fails(profile, "f1_multiplicity")
    assert result.metrics["strategy_classes"] == 1
    assert result.metrics["plan_count"] == 1
    assert_clean(profile, "f2_distinctness", "f6_player")


def test_fake_multiplicity_trips_f1_redundancy_and_f2_distance():
    """Two named strategies, one idea, many bindings.

    F1 must see the redundancy and F2 must see that the two classes are the
    same plan. Crucially F6 must stay clean - the fixture is not about the
    player - which is what distinguishes this from a level that is merely bad.
    """
    profile = profile_for("fake_multiplicity")
    f1 = assert_not_pass(profile, "f1_multiplicity")
    assert f1.metrics["redundancy"] > 10, "redundancy should exceed the band"
    assert f1.metrics["plan_count"] >= 20

    f2 = assert_fails(profile, "f2_distinctness")
    assert f2.metrics["min_pairwise_distance"] == 0.0, (
        "the two 'strategies' run identical operators"
    )
    assert_clean(profile, "f6_player")


# ==========================================================================
# F2 - Distinctness (the ablation payoff)
# ==========================================================================

def test_shared_linchpin_is_invisible_without_ablation():
    """Observationally this level looks healthy. That is the point.

    Three classes, distinct operators, wide pairwise distance. If F2 passed
    here without ablation and failed with it, the counterfactual harness has
    earned its cost.
    """
    profile = profile_for("shared_linchpin")
    f2 = family(profile, "f2_distinctness")
    assert f2.verdict == "pass", (
        "syntactic distinctness alone cannot see a shared linchpin; if this "
        "starts failing, the test below no longer proves anything"
    )
    assert f2.metrics["min_pairwise_distance"] >= 0.4
    assert family(profile, "f1_multiplicity").verdict == "pass"


def test_shared_linchpin_trips_f2_under_ablation():
    """With --ablate, one fact is revealed to kill all three routes."""
    profile = profile_for("shared_linchpin", ablate=True)
    f2 = assert_fails(profile, "f2_distinctness")
    assert "generatorOnline" in f2.metrics["shared_linchpin"], (
        f"expected generatorOnline as the linchpin, got "
        f"{f2.metrics['shared_linchpin']}"
    )
    assert f2.metrics["independent_class_pairs"] == 0


# ==========================================================================
# F3 - Depth
# ==========================================================================

def test_one_shot_trips_f3_length():
    """A single operator wins: F1 and F2 are fine, F3 is not."""
    profile = profile_for("one_shot")
    result = assert_fails(profile, "f3_depth")
    assert result.metrics["plan_length"]["median"] == 1
    assert result.metrics["causal_depth"]["best_class"] == 1
    assert_clean(profile, "f1_multiplicity", "f2_distinctness")


def test_chore_trips_f3_interlock_despite_good_length():
    """Eight operators that do not feed each other.

    Length alone would pass. `interlock` is the metric that separates a combo
    from a chore, and it must read zero here.
    """
    profile = profile_for("chore")
    result = assert_not_pass(profile, "f3_depth")
    assert result.metrics["plan_length"]["median"] == 8, "length is acceptable"
    assert result.metrics["interlock"]["mean"] == 0.0, "nothing enables anything"
    assert result.metrics["causal_depth"]["best_class"] == 1
    assert_clean(profile, "f1_multiplicity", "f2_distinctness", "f6_player")


# ==========================================================================
# F4 - Choice structure
# ==========================================================================

def test_any_loadout_wins_trips_f4_feasibility():
    """No scarcity: every X-of-Y pick solves every blocker."""
    profile = profile_for("any_loadout_wins", loadouts=True)
    result = assert_fails(profile, "f4_choice")
    assert result.metrics["loadout_feasibility"] == 1.0
    assert result.metrics["declared"] is True


def test_one_to_one_trips_f4_multi_use():
    """Each pick solves exactly one blocker.

    Feasibility sits inside its band and nothing is mandatory, so the counts
    look healthy. `multi_use_factor` is the only metric that sees this is a
    matching exercise rather than a puzzle.
    """
    profile = profile_for("one_to_one", loadouts=True)
    result = assert_not_pass(profile, "f4_choice")
    assert result.metrics["multi_use_factor"] < 1.5
    assert result.metrics["multi_use_factor"] == pytest.approx(1.0, abs=0.01)
    low = Config.load().band("f4_choice.loadout_feasibility_min")
    assert result.metrics["loadout_feasibility"] >= low, (
        "feasibility itself is fine here - multi_use is what should trip"
    )


def test_undeclared_choice_space_is_skipped_not_zeroed():
    """A level with no funChoice* facts must say so, not score zero."""
    profile = profile_for("one_shot")
    result = family(profile, "f4_choice")
    assert result.verdict == "skip"
    assert result.metrics["declared"] is False
    assert any("not declared" in f for f in result.findings)


# ==========================================================================
# F6 - Player centrality
# ==========================================================================

def test_companions_solo_trips_f6_hard():
    """Plans that need no player operator are a hard fail."""
    profile = profile_for("companions_solo")
    result = assert_fails(profile, "f6_player")
    assert result.metrics["soloable_plans"] > 0
    assert_clean(profile, "f1_multiplicity", "f2_distinctness")


# ==========================================================================
# The positive exemplar
# ==========================================================================

def test_reference_good_passes_every_family():
    """The documented target pattern must satisfy all six families.

    If this breaks, either the bands drifted or the exemplar did - and the
    failing family's numbers say which.
    """
    profile = profile_for("reference_good", ablate=True, loadouts=True)
    failures = [
        f"{f.key}={f.verdict} ({'; '.join(f.findings)})"
        for f in profile.families
        if f.verdict == "fail"
    ]
    assert not failures, "reference_good should pass everything: " + "; ".join(failures)
    assert profile.overall == "pass", (
        "reference_good should be clean, not merely non-failing: "
        + "; ".join(
            f"{f.key}: {'; '.join(f.findings)}"
            for f in profile.families if f.verdict == "warn"
        )
    )
    assert profile.fun_score == pytest.approx(1.0, abs=0.001)


def test_reference_good_choice_lattice_has_the_target_shape():
    """The X-of-Y structure the whole design is aimed at.

    Several different pairs win, no pick is mandatory, some picks are dead
    ends, near misses exist, and the picks that matter each cover more than
    one blocker. That last property is what makes it a puzzle rather than a
    form to fill in.
    """
    profile = profile_for("reference_good", ablate=True, loadouts=True)
    lattice = family(profile, "f4_choice").metrics

    assert lattice["pick"] == 2
    assert len(lattice["choices"]) == 6
    assert len(lattice["blockers"]) == 3
    assert lattice["winning_loadout_count"] > 1, "more than one answer"
    assert 0.05 <= lattice["loadout_feasibility"] <= 0.4
    assert lattice["multi_use_factor"] >= 1.5
    assert not lattice["mandatory_choices"], "no pick should be a tax"
    assert lattice["dead_choices"], "some picks should be red herrings"
    assert lattice["near_miss_count"] > 0


def test_reference_good_routes_are_independent_under_ablation():
    """The two routes must not share a load-bearing fact."""
    profile = profile_for("reference_good", ablate=True, loadouts=True)
    f2 = family(profile, "f2_distinctness")
    assert not f2.metrics["shared_linchpin"]
    assert f2.metrics["independent_class_pairs"] >= 1


# ==========================================================================
# Machinery
# ==========================================================================

def test_intermediate_states_match_the_planner():
    """Replaying del/add must reproduce the planner's own final state.

    Everything causal rests on this: if the reconstruction drifts, causal
    depth, interlock and insight depth are all quietly wrong.
    """
    import json

    from htn_metrics.extract import LevelPlanner

    path = os.path.join(FIXTURES, "reference_good")
    spec = load_level_spec(path)
    space = extract_plan_space(path, spec=spec)

    planner, _loader = LevelPlanner(spec).build()
    error, _ = planner.FindAllPlansCustomVariables(space.goal + ".")
    assert not error
    error, facts_json = planner.GetSolutionFacts(0)
    assert not error

    expected = set(json.loads(facts_json))
    plan = space.plans[0]
    actual = plan.state_at(plan.length, space.initial_facts)
    assert actual == expected, (
        f"reconstruction drift: only-in-replay={sorted(actual - expected)}, "
        f"only-in-planner={sorted(expected - actual)}"
    )


def test_decomposition_path_matches_operator_sequence():
    """Path reconstruction must recover exactly the plan's own operators.

    `GetDecompositionTree(i)` returns everything explored up to solution i, so
    a plan's own path has to be recovered from it. If that recovery slips,
    every strategy fingerprint is drawn from the wrong nodes.
    """
    from htn_metrics.extract import _path_matches_operators

    space = extract_plan_space(os.path.join(FIXTURES, "reference_good"))
    mismatched = [p.index for p in space.plans if not _path_matches_operators(p)]
    assert not mismatched, f"path/operator mismatch for plans {mismatched}"
    assert not space.notes, space.notes


def test_truncation_withholds_the_composite_score():
    """Metrics over a partial plan set are meaningless, so no score is given."""
    cfg = Config.load().with_overrides({"caps": {"max_plans": 3}})
    path = os.path.join(FIXTURES, "reference_good")
    spec = load_level_spec(path)
    space = extract_plan_space(path, spec=spec, max_plans=3)

    assert space.truncated
    profile = build_profile(path, cfg=cfg, space=space)
    assert profile.fun_score is None
    assert "truncated" in profile.score_withheld_reason


def test_config_overrides_do_not_mutate_the_shared_default():
    cfg = Config.load()
    before = cfg.band("f3_depth.plan_length_min")
    tweaked = cfg.with_overrides({"bands": {"f3_depth": {"plan_length_min": 99}}})
    assert tweaked.band("f3_depth.plan_length_min") == 99
    assert cfg.band("f3_depth.plan_length_min") == before
