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
POOL = ["fireball", "lightningFlash", "tidalWave", "vortex", "hook", "taunt"]

# The measured matrix (htn_components combos): the pairs that win, and nothing else does.
WINNING = {
    frozenset(p) for p in [
        # open the gallery (light the keg, or strike through it), then pull the golem across
        ("fireball", "hook"), ("fireball", "taunt"),
        ("lightningFlash", "hook"), ("lightningFlash", "taunt"),
        # bring golem and keg onto one floor, then blow it
        ("vortex", "fireball"), ("vortex", "lightningFlash"),
        # lure the golem into stamping, and pull the taunter out of the blow
        ("taunt", "hook"),
        # soak it, jolt it
        ("tidalWave", "lightningFlash"),
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
    planner.SetMemoryBudget(256 * 1024 * 1024)
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

    def test_example_1_lure_it_into_stamping(self):
        plans = plans_with("taunt", "hook")
        ok = any(before(p, "opWindUp(golem,caveIn,hall)", "opCast(mage,hook,player)")
                 and before(p, "opCast(mage,hook,player)", "opBlow(golem,caveIn,hall,hall)")
                 and "opExploit(golem,golem,chasm,fell)" in p for p in plans)
        assert ok, "the taunted golem should stamp the hall, and the mage hook the player out first"
        self._record(True, "Example 1: taunt the golem into the hall; the mage hooks the player out of its stamp")

    def test_example_2_strike_through_the_keg(self):
        plans = plans_with("lightningFlash", "hook")
        ok = any(before(p, "opCast(player,lightningFlash,nave)", "opSpill(keg,gallery,chasm)")
                 and before(p, "opSpill(keg,gallery,chasm)", "opForcedMove(mage,golem,nave,gallery)")
                 and "opExploit(mage,golem,chasm,fell)" in p for p in plans)
        assert ok, "a flash over the keg should open the gallery, then the hook drag the golem in"
        self._record(True, "Example 2: a lightning flash over the keg opens the gallery; a hook drags the golem in")

    def test_example_3_bomb_to_it(self):
        plans = plans_with("vortex", "fireball")
        ok = any(before(p, "opForcedMove(player,keg,gallery,nave)", "opSpill(keg,nave,chasm)")
                 and "opExploit(keg,golem,chasm,fell)" in p for p in plans)
        assert ok, "a vortex should draw the keg into the nave, and the fireball blow it there"
        self._record(True, "Example 3: a vortex draws the keg into the nave; a fireball blows it under the golem")

    def test_example_4_short_it(self):
        plans = plans_with("tidalWave", "lightningFlash")
        assert plans and all("opExploit(mage,golem,electrocuted,dead)" in p for p in plans)
        self._record(True, "Example 4: a wave from the apse, then a jolt, short-circuits the golem")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_eight_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_a_rescue_that_takes_the_golem_too(self):
        """A wave or a vortex gets the taunter out of the stamp - and the golem
        with it."""
        assert not plans_with("taunt", "tidalWave") and not plans_with("taunt", "vortex")
        self._record(True, "P3: a wave or a vortex rescue drags the golem out of its own blow")

    def test_property_p4_a_wet_keg_does_not_light(self):
        assert not plans_with("tidalWave", "fireball")
        self._record(True, "P4: washed into the nave, the keg is wet: the fireball only steams it")

    def test_property_p5_nobody_falls(self):
        for kit in [("lightningFlash", "hook"), ("vortex", "lightningFlash"), ("taunt", "fireball")]:
            for p in plans_with(*kit):
                assert not any(re.match(r"opExploit\(\w+,(player|mage),chasm,fell\)", o) for o in p), kit
        self._record(True, "P5: no winning plan drops a companion into a pit")


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
