"""Tests for the Short Circuit level (crowd control)."""

import functools
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
POOL = ["tidalWave", "vortex", "shieldBash", "taunt", "hook", "lightningFlash", "blindingFlash"]
SOAKERS = ["tidalWave", "vortex", "shieldBash"]
MOVERS = ["taunt", "hook"]
JOLTS = ["lightningFlash", "blindingFlash"]

# The measured matrix (htn_components combos: 32 of 49). Every pair of two
# different kinds wins: a soaker and a jolt (short them in the yard), a mover
# and a jolt (herd them into the sump, or bring the ogre and set it off), a
# mover and a knocker (herd them into the forge, knock them into the slag).
# Two of the same kind never do.
WINNING = {frozenset((a, b)) for a in SOAKERS + MOVERS for b in JOLTS} |           {frozenset((a, b)) for a in SOAKERS for b in MOVERS}


def _solutions(planner, goal):
    error, result = planner.FindAllPlansCustomVariables(goal)
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    return solutions


@functools.lru_cache(maxsize=None)
def plans_with(player, mage):
    """All winning plans with the player knowing `player` and the mage `mage`, on a fresh
    planner (a failed search locks the rule set)."""
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^knows\((player|mage), \w+\)\.\n", "", text, flags=re.M)
    planner = HtnPlanner(False)
    planner.SetMemoryBudget(256 * 1024 * 1024)
    loader = ComponentLoader(planner, ROOT, warn=lambda m: None)
    loader.load("abilities/goals/neutralize")
    loader.load("abilities/primitives/ab_catalog")
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n"
    assert planner.HtnCompileCustomVariables(text + kit) is None
    return tuple(_solutions(planner, "win."))


def op_list(plan):
    """[(name, [args])] for one plan."""
    out = []
    for op in plan:
        name = list(op.keys())[0]
        out.append((name, [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]))
    return out


def has_op(plans, name, args):
    return any((name, args) in op_list(p) for p in plans)


def drones_out(plan):
    """How each drone left the fight in `plan`: {drone: incoming}."""
    out = {}
    for n, args in op_list(plan):
        if n == "opExploit" and args[1] in ("cog1", "cog2", "cog3") and args[-1] in ("dead", "fell"):
            out[args[1]] = args[2]
    return out


class ShortCircuitTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_soak_the_yard_then_one_bolt(self):
        self.assert_plan("win.", contains=[
            "opCast(player, vortex, coolant)", "opKnock(player, cog1, coolant)",
            "opKnock(player, cog3, coolant)", "opCast(mage, lightningFlash, cog1)",
            "opExploit(mage, cog1, electrocuted, dead)", "opExploit(mage, cog3, electrocuted, dead)"])

    def test_example_2_herd_them_into_the_slag(self):
        plans = plans_with("taunt", "tidalWave")
        assert plans
        for c in ("cog1", "cog2", "cog3"):
            assert has_op(plans, "opNavigate", [c, "yard", "forge"]), c
            assert has_op(plans, "opExploit", ["mage", c, "lava", "fell"]), c
        assert has_op(plans, "opCast", ["mage", "tidalWave", "mage"])
        self._record(True, "Example 2: taunted into the forge, the wave throws the crowd into the slag")

    def test_example_3_the_floor_gives_way(self):
        plans = plans_with("hook", "blindingFlash")
        assert has_op(plans, "opForcedMove", ["player", "ogre", "forge", "yard"])
        assert has_op(plans, "opBlow", ["ogre", "caveIn", "yard", "yard"])
        for c in ("cog1", "cog2", "cog3"):
            assert has_op(plans, "opExploit", ["ogre", c, "chasm", "fell"]), c
        plans = plans_with("taunt", "lightningFlash")
        assert has_op(plans, "opNavigate", ["ogre", "forge", "yard"])
        assert has_op(plans, "opBlow", ["ogre", "caveIn", "yard", "yard"])
        self._record(True, "Example 3: the ogre brought among the drones, dazzled or jolted: the yard falls in")

    def test_example_4_one_skill_two_roles(self):
        assert has_op(plans_with("vortex", "lightningFlash"), "opCast", ["player", "vortex", "coolant"])
        assert has_op(plans_with("vortex", "taunt"), "opCast", ["player", "vortex", "slag"])
        assert has_op(plans_with("shieldBash", "lightningFlash"), "opKnock", ["player", "cog1", "coolant"])
        assert has_op(plans_with("shieldBash", "hook"), "opKnock", ["player", "cog1", "slag"])
        assert has_op(plans_with("tidalWave", "hook"), "opExploit", ["player", "cog1", "lava", "fell"])
        self._record(True, "Example 4: vortex, shieldBash and tidalWave soak in the yard or drop into the slag")

    def test_example_5_traps(self):
        assert not plans_with("lightningFlash", "blindingFlash"), "dry drones are only stunned"
        assert not plans_with("tidalWave", "vortex"), "two soaks: nothing jolts"
        assert not plans_with("taunt", "hook"), "two herders: nothing knocks or jolts"
        self._record(True, "Example 5: two jolts, two soaks, two herders")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_the_measured_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_each_hand_matters(self):
        for a, b in [tuple(p) for p in WINNING]:
            assert plans_with(a, b) and plans_with(b, a), f"{a}+{b}"
        self._record(True, "P3: the pairs win whichever companion holds which half")

    def test_property_p4_shorted_wet_or_dropped(self):
        """In every winning plan all three drones are out: short-circuited (a jolt on a wet
        drone) or fallen (the slag, the chasm)."""
        for a, b in [tuple(p) for p in WINNING]:
            for plan in plans_with(a, b):
                out = drones_out(plan)
                assert len(out) == 3, f"{a}+{b}: {out}"
                assert set(out.values()) <= {"electrocuted", "lava", "chasm"}, f"{a}+{b}: {out}"
        self._record(True, "P4: every plan shorts the soaked drones or drops them")


def run_tests():
    suite = ShortCircuitTest()
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
