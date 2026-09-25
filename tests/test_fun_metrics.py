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

def assert_single_actor_only(profile):
    """A fixture that is one companion by construction fails F6 on
    `single_actor_plans` (GDD 2: no single entity overcomes a challenge alone)
    and on nothing that concerns the controlled companion: it is never idle.
    That keeps the fixture about what it was built for."""
    f6 = family(profile, "f6_player")
    assert f6.metrics["single_actor_plans"] > 0, f6.metrics
    assert f6.metrics["soloable_plans"] == 0, f6.metrics
    return f6


def test_single_path_trips_f1_one_idea():
    """One route, one plan: F1 must fail on strategy_classes."""
    profile = profile_for("single_path")
    result = assert_fails(profile, "f1_multiplicity")
    assert result.metrics["strategy_classes"] == 1
    assert result.metrics["plan_count"] == 1
    assert_clean(profile, "f2_distinctness")
    assert_single_actor_only(profile)


def test_fake_multiplicity_trips_f1_redundancy_and_f2_distance():
    """Two named strategies, one idea, many bindings.

    F1 must see the redundancy and F2 must see that the two classes are the
    same plan. F6 must not blame the controlled companion - the fixture is
    not about the player - which is what distinguishes this from a level that
    is merely bad; its single-companion plans do trip the cooperation pillar.
    """
    profile = profile_for("fake_multiplicity")
    f1 = assert_not_pass(profile, "f1_multiplicity")
    assert f1.metrics["redundancy"] > 10, "redundancy should exceed the band"
    assert f1.metrics["plan_count"] >= 20

    f2 = assert_fails(profile, "f2_distinctness")
    assert f2.metrics["min_pairwise_distance"] == 0.0, (
        "the two 'strategies' run identical operators"
    )
    assert_single_actor_only(profile)


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
    assert_clean(profile, "f1_multiplicity", "f2_distinctness")
    assert_single_actor_only(profile)


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
# F6 - Cooperation
# ==========================================================================

def test_companions_solo_is_a_seat_warning_not_a_pillar_failure():
    """Two companions finishing while the controlled one stands idle is
    acceptable by design (GDD 3.6). The plans are `soloable`, a seat
    diagnostic reported as a warning; none is carried by one companion
    alone, so the family must not fail."""
    profile = profile_for("companions_solo")
    result = family(profile, "f6_player")
    assert result.metrics["soloable_plans"] > 0
    assert result.metrics["single_actor_plans"] == 0
    assert result.verdict == "warn", (result.verdict, result.findings)
    assert any("seat" in finding for finding in result.findings), result.findings
    assert_clean(profile, "f1_multiplicity", "f2_distinctness")


# ==========================================================================
# F7 - Intent, and the plan-set structure metrics
# (docs/research/fun-cross-reference.md section 5)
# ==========================================================================

def test_shortcut_trips_f7_and_nothing_else_sees_it():
    """A second route the author never intended looks like good design to
    every other family. Only the declaration catches it, and it must fail
    outright rather than lower a grade."""
    profile = profile_for("shortcut")
    f7 = assert_fails(profile, "f7_intent")
    assert f7.metrics["shortcut_plans"] == {"combo": [1]}, f7.metrics
    assert any("opLure(companionA, golem)" in f for f in f7.findings), f7.findings
    assert_clean(profile, "f1_multiplicity", "f2_distinctness", "f3_depth",
                 "f6_player")
    assert family(profile, "f1_multiplicity").verdict == "pass"


def test_f7_is_skipped_when_undeclared_and_carries_no_weight():
    profile = profile_for("reference_good")
    f7 = family(profile, "f7_intent")
    assert f7.verdict == "skip"
    assert f7.metrics["declared"] is False
    assert Config.load().weight("f7_intent") == 0.0


def test_padded_variants_trip_f1_uniqueness():
    """Two extra 'strategies' that are the real plan plus a stroll. Every
    count goes up; uniqueness is what reads the set for what it is."""
    profile = profile_for("padded_variants")
    f1 = assert_not_pass(profile, "f1_multiplicity")
    assert f1.metrics["strategy_classes"] == 3
    assert f1.metrics["plan_uniqueness"] == pytest.approx(1 / 3, abs=0.01)
    bases = {base for _padded, base in f1.metrics["padded_classes"]}
    assert bases == {"defeat > soak > shock"}, f1.metrics["padded_classes"]
    assert_clean(profile, "f2_distinctness", "f3_depth", "f6_player")


def test_rebinding_variants_are_not_padding():
    """reference_good has many re-bindings of two routes; none is a superset
    of another, so uniqueness must stay at 1 and no class reads as padded."""
    f1 = family(profile_for("reference_good"), "f1_multiplicity")
    assert f1.metrics["plan_uniqueness"] == 1.0
    assert f1.metrics["padded_classes"] == []


def test_solution_information_separates_a_puzzle_from_a_menu():
    """The exemplar needs several bits to solve at random; a fixture whose
    every method choice wins needs none."""
    good = family(profile_for("reference_good"), "f5_discovery").metrics
    assert good["solution_information_bits"] >= 1.0
    assert good["easiest_plan_bits"] >= good["solution_information_bits"], (
        "one plan cannot be easier to hit than hitting any plan"
    )
    assert set(good["solution_information_per_class"]) == {
        c["label"] for c in profile_for("reference_good").strategy_classes
    }
    menu = family(profile_for("one_shot"), "f5_discovery").metrics
    assert menu["solution_information_bits"] == 0.0


def test_success_probability_counts_methods_and_maxes_bindings():
    """Pure check of the trie arithmetic.

    Task t has 4 methods and 2 of them win: P = 2/4. Two sequences that
    differ only in which ground task follows (a binding variant) must not
    add up as if the policy chose between them.
    """
    from htn_metrics.structure import _success_probability

    two_of_four = [(("t/0", 1, 4),), (("t/0", 2, 4),)]
    assert _success_probability(two_of_four) == pytest.approx(0.5)

    binding_variants = [
        (("t/0", 1, 2), ("u/1", 7, 2)),
        (("t/0", 1, 2), ("v/1", 9, 2)),
    ]
    assert _success_probability(binding_variants) == pytest.approx(0.25)


def test_landmarks_and_world_chains_are_reported():
    profile = profile_for("reference_good")
    f2 = family(profile, "f2_distinctness").metrics
    assert "cleared(door)" in f2["landmark_facts"], "every route breaches the door"
    assert 0.0 < f2["landmark_ratio"] < 1.0
    f3 = family(profile, "f3_depth").metrics
    assert 0.0 <= f3["world_chain_ratio"] <= 1.0


# ==========================================================================
# Workflow: funExpect regressions and the rating log
# ==========================================================================

def test_reference_good_meets_its_declared_expectations():
    profile = profile_for("reference_good")
    assert len(profile.expectations) == 6
    missed = [e for e in profile.expectations if not e["ok"]]
    assert not missed, missed
    assert profile.expectations_met


def test_expectations_report_misses_ambiguity_and_typos():
    from htn_metrics.expect import Expectation, check_expectations

    families = profile_for("reference_good").families
    results = check_expectations([
        Expectation(None, "strategy_classes", "atLeast", 9, "too many"),
        Expectation(None, "verdict", "equals", "pass", "ambiguous"),
        Expectation(None, "no_such_metric", "atLeast", 1, "typo"),
        Expectation(None, "strategy_classes", "over", 1, "bad op"),
        Expectation("f1_multiplicity", "verdict", "equals", "pass", "ok"),
    ], families)
    by_source = {r["source"]: r for r in results}
    assert not by_source["too many"]["ok"] and by_source["too many"]["actual"] == 2
    assert "ambiguous" in by_source["ambiguous"]["reason"]
    assert "no such metric" in by_source["typo"]["reason"]
    assert "unknown operator" in by_source["bad op"]["reason"]
    assert by_source["ok"]["ok"]


def test_expectation_shorthand_for_family_verdict():
    from htn_metrics.expect import read_expectations

    [exp] = read_expectations(["funExpect(f7_intent, verdict, pass)"])
    assert (exp.family, exp.metric, exp.op, exp.expected) == (
        "f7_intent", "verdict", "equals", "pass")


def test_spearman_and_rating_records():
    from htn_metrics.calibration import correlate, rating_record, spearman

    assert spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
    assert spearman([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)
    assert spearman([1, 1, 1], [1, 2, 3]) is None

    record = rating_record(profile_for("reference_good"), 4, rater="t")
    assert record["rating"] == 4
    assert "f5_discovery.solution_information_bits" in record["metrics"]
    assert not any("class_sizes" in k for k in record["metrics"]), (
        "per-level labelled metrics must not be logged"
    )
    records = [dict(record, rating=r, metrics={"m.x": float(r)}) for r in range(1, 7)]
    [(name, rho, n)] = [row for row in correlate(records) if row[0] == "m.x"]
    assert rho == pytest.approx(1.0) and n == 6


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
