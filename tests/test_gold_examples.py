"""The gold examples keep producing exactly the plans their authors intended."""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src", "Python"))

from htn_test_framework import HtnTestSuite  # noqa: E402

KILL = "opApplyTag(dead, gob)"
TAG = {"lake": "wet", "kitchen": "oil"}   # arriving at a tagged location lands its tag


def _arrive(who, frm, to, move="opMoveTo"):
    tag = f"opApplyTag({TAG[to]}, {who}), " if to in TAG else ""
    return f"{move}({who}, {frm}, {to}), {tag}"


def _lure(lurer, to):
    return (f"opMoveTo({lurer}, camp, hut), opAggro(gob, {lurer}), "
            + _arrive(lurer, "hut", to) + _arrive("gob", "hut", to, "opAggroMoveTo"))


def _learn_fireball(who, old, to):
    return (f"opMoveTo({who}, camp, forge), opSwapSkill({who}, {old}, fireballSkill), "
            + _arrive(who, "forge", to))


def _ignite(caster, burned):
    burns = "".join(f"opApplyTag(burning, {a}), " for a in burned)
    return (f"opUseSkill({caster}, fireballSkill, gob), opRemoveLocationTag(oil, kitchen), "
            f"opAddLocationTag(burning, kitchen), {burns}{KILL}")


WET_AND_FREEZE = [
    # gob is wet (a lurer brings it into the lake), then chilled (frost, a second companion)
    _lure(lurer, "lake") + _arrive("frost", "camp", "lake") + "opUseSkill(frost, frostSkill, gob), "
    "opApplyTag(stunned, gob), " + KILL
    for lurer in ("player", "pyro")
]
OIL_AND_BURN = [
    # gob has oil (a lurer brings it onto the oil), then burns (a second companion); everyone there burns
    _lure("player", "kitchen") + _arrive("pyro", "camp", "kitchen") + _ignite("pyro", ["player", "pyro", "gob"]),
    _lure("player", "kitchen") + _learn_fireball("frost", "frostSkill", "kitchen") + _ignite("frost", ["player", "frost", "gob"]),
    _lure("pyro", "kitchen") + _learn_fireball("player", "iceBlastSkill", "kitchen") + _ignite("player", ["player", "pyro", "gob"]),
    _lure("pyro", "kitchen") + _learn_fireball("frost", "frostSkill", "kitchen") + _ignite("frost", ["pyro", "frost", "gob"]),
    _lure("frost", "kitchen") + _learn_fireball("player", "iceBlastSkill", "kitchen") + _ignite("player", ["player", "frost", "gob"]),
    _lure("frost", "kitchen") + _arrive("pyro", "camp", "kitchen") + _ignite("pyro", ["pyro", "frost", "gob"]),
]
STUN_AND_SLOW = [
    "opMoveTo(player, camp, hut), opMoveTo(pyro, camp, hut), opSynchronize(player, pyro), "
    "opUseSkill(player, iceBlastSkill, gob), opApplyTag(stunned, gob), "
    "opUseSkill(pyro, fireballSkill, gob), opApplyTag(burning, gob), " + KILL,
    "opMoveTo(player, camp, hut), " + _learn_fireball("frost", "frostSkill", "hut") + "opSynchronize(player, frost), "
    "opUseSkill(player, iceBlastSkill, gob), opApplyTag(stunned, gob), "
    "opUseSkill(frost, fireballSkill, gob), opApplyTag(burning, gob), " + KILL,
]


def _suite(extra_facts="", drop=(), tmp_path=None):
    path = "Examples/Combos.htn"
    if drop:
        source = open(os.path.join(ROOT, path), encoding="utf-8").read()
        for fact in drop:
            assert fact in source, fact
            source = source.replace(fact, "")
        path = str(tmp_path / "Combos.htn")
        open(path, "w", encoding="utf-8").write(source)
    suite = HtnTestSuite(path)
    if extra_facts:
        suite._planner.HtnCompileCustomVariables(extra_facts)
        suite._reload_file = lambda: None
    return suite


def test_combos_plans_for_the_sample_world():
    suite = _suite()
    assert suite.assert_plan_set("defeat(gob).", WET_AND_FREEZE + OIL_AND_BURN + STUN_AND_SLOW), \
        suite.results[-1].details


def test_combos_every_plan_needs_two_companions():
    for plan in WET_AND_FREEZE + OIL_AND_BURN + STUN_AND_SLOW:
        actors = {c for c in ("player", "pyro", "frost") if f"opMoveTo({c}," in plan}
        assert len(actors) >= 2, plan


def test_combos_a_location_combo_defeats_only_the_vulnerable(tmp_path):
    # without its vulnerabilities, gob is only defeated by the synchronized stun and slow
    suite = _suite(drop=("vulnerableToLocationCombo(gob, wet, chilled).",
                         "vulnerableToLocationCombo(gob, oil, burning)."), tmp_path=tmp_path)
    assert suite.assert_plan_set("defeat(gob).", STUN_AND_SLOW), suite.results[-1].details


def test_combos_electrified_water_hits_everyone_there():
    # the electricity combo: every agent in the lake is electrified, the vulnerable defeated
    # (a world states the tag of every agent that starts on a tagged location)
    suite = _suite("enemy(imp). at(imp, lake). at(gob, lake). hasSkill(zap, lightningSkill). "
                   "skillAppliesTag(lightningSkill, electrified). companion(zap). at(zap, lake). "
                   "hasTag(imp, wet). hasTag(gob, wet). hasTag(zap, wet). "
                   "vulnerableToLocationCombo(imp, wet, electrified).")
    assert suite.assert_state_after("useSkillOnTarget(zap, lightningSkill, gob).",
                                    has=["hasTag(gob,electrified)", "hasTag(imp,electrified)",
                                         "hasTag(zap,electrified)", "hasTag(imp,dead)"],
                                    not_has=["hasTag(gob,dead)"]), suite.results[-1].details


def test_combos_arriving_lands_the_location_tag():
    suite = _suite()
    assert suite.assert_state_after("goToLocation(player, lake).", has=["hasTag(player,wet)"]),         suite.results[-1].details


def test_combos_an_oiled_enemy_needs_only_the_caster():
    # gob already has oil and stands on it: oilAndBurn is one companion's burning skill
    suite = _suite("hasTag(gob, oil).")
    assert suite.assert_plan("oilAndBurn(gob).", contains=["opMoveTo(pyro, camp, hut), opUseSkill(pyro, fireballSkill, gob), "
                                                           "opApplyTag(burning, gob), " + KILL],
                             not_contains=["opAggro("]), suite.results[-1].details


def test_combos_a_dead_enemy_needs_no_plan():
    suite = _suite("hasTag(gob, dead).")
    assert suite.assert_no_plan("defeat(gob).")
