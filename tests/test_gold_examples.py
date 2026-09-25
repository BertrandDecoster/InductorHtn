"""The gold examples keep producing exactly the plans their authors intended."""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src", "Python"))

from htn_test_framework import HtnTestSuite  # noqa: E402

LURE_FROST = "opMoveTo(frost, camp, hut), opAggro(gob, frost), "
LURE_PYRO = "opMoveTo(pyro, camp, hut), opAggro(gob, pyro), "
FIRE = "opApplyTag(fire, gob), opApplyTag(dead, gob)"

WET_AND_ELECTROCUTE = [
    # lured to the lake (wet), then to the static tower (electrocuted); gob follows its lurer
    LURE_FROST + "opMoveTo(frost, hut, lake), opMoveTo(gob, hut, lake), opApplyTag(wet, gob), "
    "opMoveTo(frost, lake, peak), opMoveTo(gob, lake, peak), opUseSkill(tower, lightning, gob), opApplyTag(electrocute, gob), opApplyTag(dead, gob)",
    LURE_PYRO + "opMoveTo(pyro, hut, lake), opMoveTo(gob, hut, lake), opApplyTag(wet, gob), "
    "opMoveTo(pyro, lake, peak), opMoveTo(gob, lake, peak), opUseSkill(tower, lightning, gob), opApplyTag(electrocute, gob), opApplyTag(dead, gob)",
]
STUN_AND_SLOW = [
    "opMoveTo(frost, camp, hut), opMoveTo(pyro, camp, hut), opSynchronize(frost, pyro), "
    "opUseSkill(frost, iceBlast, gob), opApplyTag(stun, gob), opUseSkill(pyro, fireball, gob), " + FIRE,
]
OIL_AND_FIRE = [
    # lured onto the kitchen's oil (oily), then set on fire: lurer x who brings the fire
    LURE_FROST + "opMoveTo(frost, hut, kitchen), opMoveTo(gob, hut, kitchen), opApplyTag(oily, gob), "
    "opMoveTo(frost, kitchen, forge), opMoveTo(gob, kitchen, forge), opSwapSkill(frost, iceBlast, fireball), "
    "opUseSkill(frost, fireball, gob), " + FIRE,
    LURE_FROST + "opMoveTo(frost, hut, kitchen), opMoveTo(gob, hut, kitchen), opApplyTag(oily, gob), "
    "opMoveTo(pyro, camp, kitchen), opUseSkill(pyro, fireball, gob), " + FIRE,
    LURE_PYRO + "opMoveTo(pyro, hut, kitchen), opMoveTo(gob, hut, kitchen), opApplyTag(oily, gob), "
    "opMoveTo(frost, camp, forge), opSwapSkill(frost, iceBlast, fireball), opMoveTo(frost, forge, kitchen), "
    "opUseSkill(frost, fireball, gob), " + FIRE,
    LURE_PYRO + "opMoveTo(pyro, hut, kitchen), opMoveTo(gob, hut, kitchen), opApplyTag(oily, gob), "
    "opUseSkill(pyro, fireball, gob), " + FIRE,
]


def _suite(extra_facts=""):
    suite = HtnTestSuite("Examples/Combos.htn")
    if extra_facts:
        suite._planner.HtnCompileCustomVariables(extra_facts)
        suite._reload_file = lambda: None
    return suite


def test_combos_plans_for_the_sample_world():
    suite = _suite()
    assert suite.assert_plan_set("defeat(gob).", WET_AND_ELECTROCUTE + STUN_AND_SLOW + OIL_AND_FIRE), \
        suite.results[-1].details


def test_combos_a_fire_immune_enemy_is_not_burned():
    # stun+slow still works: the slow skill's fire tag just doesn't land
    stun = [p.replace("opUseSkill(pyro, fireball, gob), opApplyTag(fire, gob), ",
                      "opUseSkill(pyro, fireball, gob), ") for p in STUN_AND_SLOW]
    suite = _suite("immune(gob, fire).")
    assert suite.assert_plan_set("defeat(gob).", WET_AND_ELECTROCUTE + stun), suite.results[-1].details


def test_combos_a_dead_enemy_needs_no_plan():
    suite = _suite("hasTag(gob, dead).")
    assert suite.assert_no_plan("defeat(gob).")
