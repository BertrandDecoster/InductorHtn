"""Tests for the Powder Gallery level."""

import itertools
import json
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite
from indhtnpy import HtnPlanner
from htn_components.loader import ComponentLoader

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../.."))
POOL = ["taunt", "fireball", "lightningFlash", "blindingFlash", "tidalWave", "turnToMist",
        "vortex", "hook"]

# The measured matrix (htn_components combos): the pairs that win, and nothing else does.
WINNING = {
    frozenset(p) for p in [
        # bomb it: taunt it onto the keg's floor, and light the keg in its wind-up
        ("taunt", "fireball"), ("taunt", "lightningFlash"), ("taunt", "blindingFlash"),
        # short it: soak it, then jolt it
        ("tidalWave", "lightningFlash"), ("tidalWave", "blindingFlash"),
        # drop it: mist, then knock it into the crypt or the gap
        ("turnToMist", "fireball"), ("turnToMist", "tidalWave"), ("turnToMist", "vortex"),
        ("turnToMist", "hook"),
    ]
}


def _op_text(op):
    name = list(op.keys())[0]
    args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]
    return f"{name}({','.join(args)})"


def plans_with(player, mage):
    """Every winning plan, as lists of operator strings, with the player knowing
    `player` and the mage `mage` - on a fresh planner (a failed search locks the
    rule set)."""
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^knows\((player|mage), \w+\)\.\n", "", text, flags=re.M)
    planner = HtnPlanner(False)
    planner.SetMemoryBudget(512 * 1024 * 1024)
    loader = ComponentLoader(planner, ROOT)
    loader.load("abilities/goals/neutralize")
    loader.load("abilities/primitives/ab_catalog")
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n"
    assert planner.HtnCompileCustomVariables(text + kit) is None
    error, result = planner.FindAllPlansCustomVariables("win.")
    assert error is None, error
    sols = json.loads(result)
    if not sols or (isinstance(sols[0], dict) and "false" in sols[0]):
        return []
    return [[_op_text(op) for op in sol] for sol in sols]


def before(plan, first, then):
    return first in plan and then in plan and plan.index(first) < plan.index(then)


class PowderGalleryTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_light_the_keg_in_the_wind_up(self):
        plans = plans_with("taunt", "fireball")
        ok = any(before(p, "opWindUp(golem,groundSlam,player)", "opCast(mage,fireball,gallery)")
                 and before(p, "opCast(mage,fireball,gallery)", "opWindUp(keg,caveIn,gallery)")
                 and "opExploit(keg,golem,chasm,fell)" in p for p in plans)
        assert ok, "the golem should walk round to the gallery, and the fireball light the keg in its wind-up"
        self._record(True, "Example 1: taunted onto the keg's floor, the keg lit in the golem's wind-up")

    def test_example_2_a_friend_by_the_keg_flashes(self):
        plans = plans_with("taunt", "blindingFlash")
        ok = any(before(p, "opNavigate(mage,entry,gallery)", "opCast(player,taunt,golem)")
                 and before(p, "opWindUp(golem,groundSlam,player)", "opCast(mage,blindingFlash,mage)")
                 and "opExploit(keg,golem,chasm,fell)" in p for p in plans)
        assert ok, "the mage should wait by the keg and flash in the slam's wind-up"
        self._record(True, "Example 2: posted by the keg, the mage flashes in the wind-up: the floor goes")

    def test_example_3_soak_then_jolt(self):
        plans = plans_with("tidalWave", "lightningFlash")
        ok = any(before(p, "opGrant(player,golem,wet)", "opExploit(mage,golem,electrocuted,dead)")
                 or before(p, "opGrant(mage,golem,wet)", "opExploit(player,golem,electrocuted,dead)")
                 for p in plans)
        assert ok, "a wave in the nave, then a lightning flash, should short the golem"
        self._record(True, "Example 3: a wave in the nave soaks it, the flash shorts it")

    def test_example_4_mist_then_hook_across_the_gap(self):
        plans = plans_with("turnToMist", "hook")
        ok = any(before(p, "opCast(player,turnToMist,golem)", "opFall(mage,golem,nave,gallery)")
                 for p in plans)
        assert ok, "the mage should hook the misted golem across the broken gallery"
        self._record(True, "Example 4: mist the golem, hook it into the gap from the gallery")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_nine_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_each_hand_matters(self):
        assert plans_with("taunt", "lightningFlash") and plans_with("lightningFlash", "taunt")
        assert plans_with("turnToMist", "vortex") and plans_with("vortex", "turnToMist")
        self._record(True, "P3: the pairs win whichever companion holds which half")

    def test_property_p4_a_slammed_keg_is_a_dud(self):
        """The golem's slam stuns everything on the floor, the keg too (a
        stunned fuse is silenced): every bomb lights it before the blow."""
        for kit in [("taunt", "fireball"), ("lightningFlash", "taunt"), ("taunt", "blindingFlash")]:
            plans = plans_with(*kit)
            assert plans and not any("opBlow(golem" in " ".join(p) for p in plans), kit
        self._record(True, "P4: the keg is lit in the golem's wind-up, never after its slam")

    def test_property_p5_no_light_no_bomb(self):
        """Wet, the keg steams instead of lighting; lit alone, it caves in an
        empty floor; a dry jolt only stuns the golem."""
        assert not plans_with("tidalWave", "fireball")
        assert not plans_with("fireball", "lightningFlash")
        assert not plans_with("taunt", "tidalWave")
        self._record(True, "P5: a wet keg, a lone keg, a dry jolt: none wins")


def run_tests():
    suite = PowderGalleryTest()
    for method_name in sorted(dir(suite)):
        if method_name.startswith("test_"):
            suite.setup()
            method = getattr(suite, method_name)
            try:
                method()
            except AssertionError as e:
                suite._record(False, method_name, str(e))
            except Exception as e:
                suite._record(False, method_name, f"Error: {e}")
    print(suite.summary())
    return suite.all_passed()


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
