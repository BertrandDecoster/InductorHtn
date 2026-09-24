"""Tests for the Powder Keg level (crowd control)."""

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
POOL = ["hook", "taunt", "vortex", "tidalWave", "fireball", "blindingFlash", "lightningFlash"]

# The measured matrix (htn_components combos: 14 of 49). The keg: brought
# into the grove (hook it from the grove; vortex, or a wave on the ramp,
# knocks it over the lip) and lit by a fireball. The meteor: the priest
# brought among the trees (taunt, hook) and set off (blindingFlash,
# lightningFlash).
WINNING = {
    frozenset(p) for p in [
        ("hook", "fireball"), ("vortex", "fireball"), ("tidalWave", "fireball"),
        ("hook", "blindingFlash"), ("hook", "lightningFlash"),
        ("taunt", "blindingFlash"), ("taunt", "lightningFlash"),
    ]
}


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


class PowderKegTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_over_the_lip_then_light_it(self):
        self.assert_plan("win.", contains=[
            "opCast(player, vortex, lip)", "opKnock(player, keg, lip)",
            "opForcedMove(player, keg, ramp, grove)", "opCast(mage, fireball, grove)",
            "opReact(mage, keg, oiled, burning, blaze)",
            "opExploit(mage, t1, burning, dead)", "opExploit(mage, t3, burning, dead)"])

    def test_example_2_the_meteor_on_the_grove(self):
        plans = plans_with("taunt", "blindingFlash")
        assert plans
        assert has_op(plans, "opNavigate", ["priest", "shrine", "grove"])
        assert has_op(plans, "opCast", ["mage", "blindingFlash", "mage"])
        assert has_op(plans, "opBlow", ["priest", "meteor", "grove", "grove"])
        for t in ("t1", "t2", "t3"):
            assert has_op(plans, "opExploit", ["priest", t, "burning", "dead"]), t
        self._record(True, "Example 2: the taunted priest walks among the trees; dazzled, its meteor burns them")

    def test_example_3_hook_two_roles(self):
        assert has_op(plans_with("hook", "fireball"), "opForcedMove", ["player", "keg", "ramp", "grove"])
        assert has_op(plans_with("hook", "blindingFlash"),
                      "opForcedMove", ["player", "priest", "shrine", "grove"])
        assert has_op(plans_with("hook", "lightningFlash"), "opBlow", ["priest", "meteor", "grove", "grove"])
        self._record(True, "Example 3: the hook fetches the keg, or the priest")

    def test_example_4_traps(self):
        assert not plans_with("fireball", "fireball"), "fire on the keg first: it blazes alone"
        assert not plans_with("hook", "hook"), "nothing lit"
        assert not plans_with("taunt", "fireball"), "the keg does not walk; the priest is not set off"
        assert not plans_with("vortex", "blindingFlash"), "the vortex moves nothing out of its area"
        assert not plans_with("lightningFlash", "lightningFlash"), "the meteor falls on the shrine"
        self._record(True, "Example 4: fire first, two movers, the wrong mover, the priest at home")

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

    def test_property_p4_through_the_wet(self):
        """In every winning plan the treants burn only after a blaze or a meteor: fire cast on
        them only steams them."""
        for a, b in [tuple(p) for p in WINNING]:
            for plan in plans_with(a, b):
                ops = op_list(plan)
                hot = [i for i, (n, args) in enumerate(ops)
                       if (n == "opReact" and args[-1] == "blaze") or n == "opBlow"]
                dead = [i for i, (n, args) in enumerate(ops)
                        if n == "opExploit" and args[1] in ("t1", "t2", "t3") and args[-1] == "dead"]
                assert len(dead) == 3 and hot and min(hot) < min(dead), f"{a}+{b}"
        self._record(True, "P4: every plan burns the grove with a blaze or a meteor, never a fireball alone")


def run_tests():
    suite = PowderKegTest()
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
