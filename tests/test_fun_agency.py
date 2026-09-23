"""Tests for what F6 calls player participation, and for the plan trie.

The GDD's pillar is "no single companion can solo the map, whoever controls
it"; how much the controlled companion does is a seat diagnostic beside it.
A metric that counts every operator whose arguments mention the player would
read the seat off a no-op. These tests pin down the stronger reading:

  - an operator is the player's when the player is its *actor* (first
    argument by convention, or the argument a `funActor/2` fact names), and
    it is *consequential* when it changes the world and is not declared a
    `funNoop/1`;
  - a plan is soloable when it has no consequential player-actor operator
    (a seat finding, a warning), and single-actor when one companion's
    operators are all of it (the pillar, a fail);
  - teamwork is visible in the causal graph as edges between operators of
    different actors;
  - the player has a decision when the plan trie forks on player operators.

Run:  python -m pytest tests/test_fun_agency.py -v
"""

import os

import pytest

from test_fun_metrics import FIXTURES, assert_clean, assert_fails, family, profile_for  # noqa: E402

from htn_metrics.config import Config  # noqa: E402
from htn_metrics.extract import extract_plan_space, load_level_spec  # noqa: E402
from htn_metrics.profile import build_profile  # noqa: E402


def _space_for(fixture):
    path = os.path.join(FIXTURES, fixture)
    spec = load_level_spec(path)
    return path, spec, extract_plan_space(path, spec=spec)


# ==========================================================================
# F6 - agency, not mention
# ==========================================================================

def test_nominal_player_trips_f6_despite_being_mentioned_everywhere():
    """Waiting and being shielded are not actions. The plan is soloable."""
    profile = profile_for("nominal_player")
    f6 = assert_fails(profile, "f6_player")
    assert f6.metrics["soloable_plans"] == 1
    assert f6.metrics["player_load"] == 0.0
    assert f6.metrics["passive_involvement"] > 0.0, (
        "being the target of opShield is passive involvement, reported apart"
    )
    # One plan by construction, so F1 is not what this fixture is about.
    assert_clean(profile, "f2_distinctness", "f3_depth")


def test_actor_override_and_noop_declarations_are_honoured():
    """funActor(opCast, 1) makes the cast the player's; funNoop(opShout)
    removes the shout from the count."""
    profile = profile_for("actor_override")
    f6 = family(profile, "f6_player")
    assert f6.metrics["soloable_plans"] == 0
    assert f6.metrics["player_load"] == 1.0
    assert f6.metrics["consequential_operators"] == 1


def test_reference_good_shows_teamwork_and_player_decisions():
    """Companions set up what the player finishes and vice versa, and the
    plan forks on a player operator at least once."""
    profile = profile_for("reference_good", ablate=True, loadouts=True)
    f6 = family(profile, "f6_player")
    assert f6.metrics["teamwork_edge_ratio"] >= 0.3
    assert f6.metrics["player_causal_out"] > 0.0
    assert f6.metrics["player_decision_points"] >= 1
    assert f6.verdict == "pass", f6.findings


# ==========================================================================
# The plan trie
# ==========================================================================

def test_plan_trie_forks_where_the_plans_diverge():
    """reference_good: every plan opens with the same three clears, then
    forks on the player's first route move."""
    from htn_metrics.agency import ActorConvention
    from htn_metrics.trie import PlanTrie

    _path, _spec, space = _space_for("reference_good")
    cfg = Config.load()
    trie = PlanTrie(space, ActorConvention.from_space(space, cfg))

    root = trie.children(())
    assert len(root) == 1, "all plans start with the same clear"
    assert len(trie.surviving(())) == space.plan_count

    prefix = trie.auto_advance_companions(())
    assert len(prefix) == 3, "three companion clears, then the player is asked"
    fork = trie.children(prefix)
    player_options = [c for c in fork.values() if c.actor == "player"]
    assert len(player_options) >= 2
    assert trie.player_decision_points() >= 1

    chosen = player_options[0]
    narrowed = trie.surviving(prefix + (chosen.text,))
    assert 0 < len(narrowed) < space.plan_count


# ==========================================================================
# Thresholds are data; the scorecard rewards the right things
# ==========================================================================

def test_thresholds_live_in_config():
    """Every verdict-defining number is in metrics.json."""
    saturated = Config.load().with_overrides(
        {"bands": {"f4_choice": {"feasibility_saturated_at": 1.01}}}
    )
    path = os.path.join(FIXTURES, "any_loadout_wins")
    base = profile_for("any_loadout_wins", loadouts=True)
    lattice = {k: v for k, v in family(base, "f4_choice").metrics.items()}
    lattice.setdefault("loadouts_evaluated", 6)
    relaxed = build_profile(path, cfg=saturated, lattice=lattice)
    assert family(relaxed, "f4_choice").verdict != "fail"

    lenient = Config.load().with_overrides(
        {"bands": {"f6_player": {"soloable_plans_max": 999}}}
    )
    path = os.path.join(FIXTURES, "companions_solo")
    assert family(build_profile(path, cfg=lenient), "f6_player").verdict != "fail"


def test_no_dead_choices_is_not_a_warning():
    """An option can be useful somewhere and still take judgement to pick."""
    from htn_metrics.metrics import f4_choice

    _path, _spec, space = _space_for("reference_good")
    healthy = {
        "space": "kit", "pick": 2, "choices": ["a", "b", "c", "d"],
        "blockers": ["x", "y"], "loadouts_evaluated": 6, "loadouts_total": 6,
        "subsets_evaluated": 11, "subsets_total": 11, "sampled": False,
        "loadout_feasibility": 0.33, "loadout_feasibility_independent": 0.33,
        "winning_loadout_count": 2, "winning_loadouts": [["a", "b"], ["c", "d"]],
        "winning_loadouts_independent": [["a", "b"], ["c", "d"]],
        "shared_resource_loadouts": [], "minimal_cover_count": 2,
        "multi_use_factor": 2.0, "mandatory_choices": [], "dead_choices": [],
        "near_miss_count": 2, "unknown_probes": 0,
    }
    result = f4_choice(space, Config.load(), healthy)
    assert result.verdict == "pass", result.findings
    assert not any("dead" in f for f in result.findings)


def test_unused_scenery_is_not_required():
    """Red herrings are a tool, not a requirement: no minimum band."""
    assert Config.load().band("f5_discovery.red_herring_ratio_min") is None
    for fixture in ("one_shot", "single_path", "fake_multiplicity"):
        f5 = family(profile_for(fixture), "f5_discovery")
        assert not any("rule out" in f for f in f5.findings), (fixture, f5.findings)
