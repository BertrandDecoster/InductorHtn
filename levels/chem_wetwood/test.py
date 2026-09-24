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
POOL = ["flameWall", "fireball", "zap", "cleanse", "gust", "magnetize", "tidalWave", "taunt"]
FIRE = ["flameWall", "fireball"]
MOVERS = ["gust", "magnetize", "tidalWave", "taunt"]

# The measured matrix: the pairs that win, and nothing else does.
WINNING = (
    {frozenset((f, "cleanse")) for f in FIRE}            # dry, then burn
    | {frozenset((f, m)) for f in FIRE for m in MOVERS}  # keg + fire
    | {frozenset(("zap", m)) for m in MOVERS}            # keg + spark
)


def _solutions(planner, goal):
    error, result = planner.FindAllPlansCustomVariables(goal)
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    return solutions


def plans_with(player, mage):
    """All winning plans with the player knowing `player` and the mage `mage`, on a fresh
    planner (a failed search locks the rule set)."""
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
    return _solutions(planner, "win.")


def names(plan):
    """A plan as a list of 'op(a, b, ...)' strings."""
    out = []
    for op in plan:
        n = list(op.keys())[0]
        args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[n]]
        out.append(f"{n}({', '.join(args)})")
    return out


class WetWoodTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_dry_then_burn(self):
        self.assert_plan("win.", contains=[
            "opRemove(player, treant, wet)", "opCast(mage, flameWall, treant)",
            "opExploit(mage, treant, burning, dead)"])

    def test_example_2_keg_then_spark(self):
        plans = [names(p) for p in plans_with("gust", "zap")]
        assert plans, "gust + zap should win"
        plan = plans[0]
        assert "opForcedMove(player, keg, ramp, grove)" in plan
        assert "opReact(mage, keg, oiled, electrocuted, blaze)" in plan
        assert "opExploit(mage, treant, burning, dead)" in plan
        self._record(True, "Example 2: the keg is pushed into the grove, and a spark sets it off")

    def test_example_3_fire_then_keg(self):
        plans = [names(p) for p in plans_with("flameWall", "gust")]
        fire_first = [p for p in plans if "opCast(player, flameWall, grove)" in p
                      and p.index("opCast(player, flameWall, grove)") < p.index("opCast(mage, gust, keg)")]
        assert fire_first, "a plan should set the grove alight first"
        assert "opReact(mage, keg, oiled, burning, blaze)" in fire_first[0]
        self._record(True, "Example 3: the grove burns first; the keg blazes as it arrives")

    def test_example_4_wet_wood_only_steams(self):
        plans = [names(p) for p in plans_with("flameWall", "fireball")]
        assert not plans, "two fires should only steam it"
        self._record(True, "Example 4: two fires, no keg: steam, then a fire zone that relights nothing")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_fourteen_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_each_hand_matters(self):
        assert plans_with("cleanse", "fireball") and plans_with("taunt", "zap")
        self._record(True, "P3: the pairs win whichever companion holds which half")

    def test_property_p4_the_blaze_is_raw(self):
        """The soak does not save the treant from the keg's blaze: in the spark method,
        nothing dries it, and it still burns."""
        plan = names(plans_with("magnetize", "zap")[0])
        assert not any("treant, wet)" in o and o.startswith("opRemove") for o in plan)
        assert "opExploit(mage, treant, burning, dead)" in plan
        self._record(True, "P4: the blaze burns the treant through its soak")


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
