"""Tests for the Cinder level (elemental chemistry)."""

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
POOL = ["rainCall", "tidalWave", "glaciate", "iceStorm", "gust", "fireball", "magnetize", "translocate"]
DOUSE = ["rainCall", "tidalWave"]
COLD = ["glaciate", "iceStorm"]
BLAST = ["gust", "fireball"]
DRAG = ["magnetize", "translocate"]

# The measured matrix: the pairs that win, and nothing else does.
WINNING = (
    {frozenset((d, c)) for d in DOUSE for c in COLD}               # douse, then chill
    | {frozenset((q, p)) for q in DOUSE + COLD for p in DRAG}      # quench, then drag onto ice
    | {frozenset((b, f)) for b in BLAST for f in COLD + DRAG}      # dunk, then freeze
)


def _solutions(planner, goal):
    error, result = planner.FindAllPlansCustomVariables(goal)
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    return solutions


def plans_with(player, mage, goal="win."):
    """All plans for `goal` with the player knowing `player` and the mage `mage`, on a
    fresh planner (a failed search locks the rule set)."""
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
    return _solutions(planner, goal)


def names(plan):
    """A plan as a list of 'op(a, b, ...)' strings."""
    out = []
    for op in plan:
        n = list(op.keys())[0]
        args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[n]]
        out.append(f"{n}({', '.join(args)})")
    return out


class CinderTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_douse_then_chill(self):
        self.assert_plan("win.", contains=[
            "opReact(player, imp, burning, wet, extinguish)", "opCast(mage, glaciate, imp)",
            "opExploit(mage, imp, chilled, frozen)"])

    def test_example_2_dunk_then_drag_onto_ice(self):
        plan = names(plans_with("gust", "magnetize")[0])
        assert "opForcedMove(player, imp, yard, fountain)" in plan
        assert "opReact(player, imp, burning, wet, extinguish)" in plan
        assert "opForcedMove(mage, imp, fountain, pond)" in plan
        assert "opExploit(mage, imp, chilled, frozen)" in plan
        self._record(True, "Example 2: blown into the fountain, then dragged onto the frozen pond")

    def test_example_3_quench_then_swap(self):
        plan = names(plans_with("glaciate", "translocate")[0])
        assert "opReact(player, imp, burning, chilled, quench)" in plan
        assert "opSwap(mage, imp, pond, yard)" in plan
        assert "opExploit(mage, imp, chilled, frozen)" in plan
        self._record(True, "Example 3: frost quenches it; a swap from the pond puts it on the ice")

    def test_example_4_fire_is_only_a_blast(self):
        plan = names(plans_with("fireball", "iceStorm")[0])
        assert "opForcedMove(player, imp, yard, fountain)" in plan
        assert not any(o.startswith("opGrant") and "imp, burning" in o for o in plan)
        assert "opExploit(mage, imp, chilled, frozen)" in plan
        self._record(True, "Example 4: fireball's fire does nothing to the imp; its blast dunks it")

    def test_example_5_cold_twice_only_quenches(self):
        assert not plans_with("glaciate", "iceStorm")
        self._record(True, "Example 5: two frosts: a quench, then ice already there")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_twenty_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_each_hand_matters(self):
        assert plans_with("magnetize", "rainCall") and plans_with("iceStorm", "fireball")
        self._record(True, "P3: the pairs win whichever companion holds which half")

    def test_property_p4_the_ice_takes_it_once(self):
        """Dragged onto the pond while burning, the imp is only quenched, and nothing
        can bring it onto the ice again: the two drags together lose."""
        assert not plans_with("magnetize", "translocate")
        plan = names(plans_with("magnetize", "gust", "pullOnto(player, imp, pond).")[0])
        assert "opReact(player, imp, burning, chilled, quench)" in plan
        assert not any("frozen" in o for o in plan)
        self._record(True, "P4: the first arrival on the ice only quenches it")


def run_tests():
    suite = CinderTest()
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
