"""Tests for the Wet Wood level (elemental chemistry)."""

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
POOL = ["fireball", "lightningFlash", "blindingFlash", "hook", "taunt", "vortex", "turnToMist"]
FIRE = ["fireball", "lightningFlash", "blindingFlash"]

# The measured matrix: the pairs that win, and nothing else does.
WINNING = (
    {frozenset(("hook", f)) for f in FIRE + ["vortex"]}         # keg to the tree
    | {frozenset(("taunt", f)) for f in FIRE}                   # tree to the oil
    | {frozenset(("turnToMist", "fireball"))}                   # into the kiln
)


def _solutions(planner, goal):
    error, result = planner.FindAllPlansCustomVariables(goal)
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    return solutions


def names(plan):
    """A plan as a list of 'op(a, b, ...)' strings."""
    out = []
    for op in plan:
        n = list(op.keys())[0]
        args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[n]]
        out.append(f"{n}({', '.join(args)})")
    return out


def plans_with(player, mage, goal="win."):
    """All plans for `goal` with the player knowing `player` and the mage `mage`, on a
    fresh planner (a failed search locks the rule set), as lists of operator strings."""
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
    return [names(p) for p in _solutions(planner, goal)]


def some_plan_has(plans, *ops):
    return any(all(o in p for o in ops) for p in plans)


class WetWoodTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_hook_the_keg_then_fire(self):
        self.assert_plan("win.", contains=[
            "opCast(player, hook, keg)", "opForcedMove(player, keg, ramp, grove)",
            "opCast(mage, fireball, keg)", "opReact(mage, keg, oiled, burning, blaze)",
            "opExploit(mage, treant, burning, dead)"])

    def test_example_2_fire_then_keg(self):
        self.assert_plan("win.", contains=[
            "opCast(mage, fireball, grove)", "opReact(mage, treant, wet, burning, steam)",
            "opForcedMove(player, keg, ramp, grove)", "opReact(player, keg, oiled, burning, blaze)",
            "opExploit(player, treant, burning, dead)"])

    def test_example_3_hook_then_vortex_into_the_kiln(self):
        plans = plans_with("hook", "vortex")
        assert some_plan_has(plans, "opForcedMove(player, keg, ramp, grove)",
                             "opCast(mage, vortex, kiln)", "opKnock(mage, keg, kiln)",
                             "opReact(mage, keg, oiled, burning, blaze)",
                             "opExploit(mage, treant, burning, dead)")
        self._record(True, "Example 3: the keg hooked down, then knocked into the kiln")

    def test_example_4_lure_onto_the_oil_then_spark(self):
        plans = plans_with("taunt", "lightningFlash")
        assert some_plan_has(plans, "opCast(player, taunt, treant)",
                             "opNavigate(treant, grove, ramp)", "opGrant(treant, treant, oiled)",
                             "opCast(mage, lightningFlash, treant)",
                             "opReact(mage, keg, oiled, electrocuted, blaze)",
                             "opExploit(mage, treant, burning, dead)")
        self._record(True, "Example 4: lured through the slick, then sparked beside the keg")

    def test_example_5_mist_then_into_the_kiln(self):
        plans = plans_with("turnToMist", "fireball")
        assert some_plan_has(plans, "opRemove(player, treant, heavy)",
                             "opReact(mage, treant, wet, burning, steam)",
                             "opKnock(mage, treant, kiln)", "opExploit(mage, treant, burning, dead)")
        self._record(True, "Example 5: misted, dried by the flames, knocked into the kiln")

    def test_example_6_wet_wood_only_steams(self):
        assert not plans_with("fireball", "fireball")
        self._record(True, "Example 6: two fires: steam, then flames already there")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_eight_pairs_win_in_either_hand(self):
        wins = {(a, b): bool(plans_with(a, b)) for a, b in itertools.permutations(POOL, 2)}
        found = {frozenset(k) for k, w in wins.items() if w}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        one_way = sorted(k for k, w in wins.items() if w != wins[(k[1], k[0])])
        assert not one_way, f"win in one order only: {one_way}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win, in either hand")

    def test_property_p3_fire_on_the_ramp_wastes_the_oil(self):
        """Fire on the keg where it stands: slick + flames = flames, the keg blazes on the
        ramp, far from the tree; lured through the flames later, the treant only steams."""
        plan = plans_with("fireball", "taunt", "cast(player, fireball, keg).")[0]
        assert "opReshape(player, ramp, slick, flames)" in plan
        assert "opReact(player, keg, oiled, burning, blaze)" in plan
        assert not any("dead" in o for o in plan)
        plan = plans_with("fireball", "taunt",
                          "cast(player, fireball, ramp), castFrom(mage, taunt, treant, ramp).")[0]
        assert "opReact(treant, treant, wet, burning, steam)" in plan
        assert not any("dead" in o for o in plan)
        self._record(True, "P3: the oil burnt off on the ramp; the lure only steams it")

    def test_property_p4_the_kiln_needs_a_dry_treant(self):
        """A misted treant knocked into the kiln by a vortex is still wet: steam."""
        assert not plans_with("turnToMist", "vortex")
        plan = plans_with("turnToMist", "vortex",
                          "cast(player, turnToMist, treant), cast(mage, vortex, kiln).")[0]
        assert "opKnock(mage, treant, kiln)" in plan
        assert "opReact(mage, treant, wet, burning, steam)" in plan
        assert not any("dead" in o for o in plan)
        self._record(True, "P4: knocked into the kiln wet, it only steams")

    def test_property_p5_the_keg_does_not_walk(self):
        """A taunt does nothing to the keg: hook is the only way to bring it."""
        plan = plans_with("taunt", "fireball", "castFrom(player, taunt, keg, grove).")[0]
        assert "opGrant(player, keg, taunted)" not in plan
        assert not any(o.startswith("opNavigate(keg") for o in plan)
        self._record(True, "P5: the keg ignores a taunt")


def run_tests():
    suite = WetWoodTest()
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
