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
POOL = ["fireball", "lightningFlash", "tidalWave", "hook", "vortex", "taunt", "turnToMist"]
BRING = ["tidalWave", "hook", "vortex", "taunt"]
IGNITE = ["fireball", "lightningFlash"]

# The measured matrix: the pairs that win, and nothing else does.
WINNING = (
    {frozenset((b, i)) for b in BRING for i in IGNITE}      # keg, then fire (or fire, then keg)
    | {frozenset(("turnToMist", "fireball"))}                # into the kiln
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

    def test_example_1_keg_then_fire(self):
        self.assert_plan("win.", contains=[
            "opCast(player, tidalWave, player)", "opForcedMove(player, keg, ramp, grove)",
            "opReact(mage, keg, oiled, burning, blaze)",
            "opExploit(mage, treant, burning, dead)"])

    def test_example_2_fire_then_keg(self):
        plans = plans_with("tidalWave", "fireball")
        assert some_plan_has(plans, "opCast(mage, fireball, grove)",
                             "opReact(mage, treant, wet, burning, steam)",
                             "opForcedMove(player, keg, ramp, grove)",
                             "opReact(player, keg, oiled, burning, blaze)",
                             "opExploit(player, treant, burning, dead)")
        self._record(True, "Example 2: the grove alight first; the keg blazes as it arrives")

    def test_example_3_hook_then_spark(self):
        plans = plans_with("hook", "lightningFlash")
        assert some_plan_has(plans, "opForcedMove(player, keg, ramp, grove)",
                             "opReact(mage, keg, oiled, electrocuted, blaze)",
                             "opExploit(mage, treant, burning, dead)")
        self._record(True, "Example 3: the keg dragged in, then sparked")

    def test_example_4_mist_then_into_the_kiln(self):
        plans = plans_with("turnToMist", "fireball")
        assert some_plan_has(plans, "opRemove(player, treant, heavy)",
                             "opReact(mage, treant, wet, burning, steam)",
                             "opForcedMove(mage, treant, grove, kiln)",
                             "opExploit(mage, treant, burning, dead)")
        self._record(True, "Example 4: misted, steamed dry and blown into the kiln")

    def test_example_5_fire_twice_only_steams(self):
        assert not plans_with("fireball", "fireball")
        self._record(True, "Example 5: two fireballs: steam, then flames already there")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_nine_pairs_win_in_either_hand(self):
        wins = {(a, b): bool(plans_with(a, b)) for a, b in itertools.permutations(POOL, 2)}
        found = {frozenset(k) for k, w in wins.items() if w}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        one_way = sorted(k for k, w in wins.items() if w != wins[(k[1], k[0])])
        assert not one_way, f"win in one order only: {one_way}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win, in either hand")

    def test_property_p3_fire_on_the_ramp_wastes_the_oil(self):
        """Fireball on the keg where it stands: flames on the slick are flames, the keg
        blazes on the ramp, and it lands in the grove with no oil left."""
        plan = plans_with("fireball", "hook", "castFrom(player, fireball, keg, landing).")[0]
        assert "opReshape(player, ramp, slick, flames)" in plan
        assert "opReact(player, keg, oiled, burning, blaze)" in plan
        assert "opForcedMove(player, keg, ramp, grove)" in plan
        assert not any("treant, burning, dead" in o for o in plan)
        self._record(True, "P3: slick + flames = flames: the keg burns out on the ramp")

    def test_property_p4_the_kiln_only_steams_the_wet(self):
        """A misted treant washed into the kiln is still wet: the kiln only steams it."""
        assert not plans_with("turnToMist", "tidalWave")
        assert not plans_with("turnToMist", "vortex")
        self._record(True, "P4: the kiln needs a dry treant: only the fireball dries and throws")


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
