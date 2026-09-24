"""Tests for the Two Hands level."""

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
POOL = ["turnToMist", "fireball", "tidalWave", "hook", "taunt", "vortex", "lightningFlash"]

# The measured matrix: the pairs that win, and nothing else does.
WINNING = {
    frozenset(p) for p in [
        ("turnToMist", "fireball"), ("turnToMist", "tidalWave"), ("turnToMist", "hook"),
        ("turnToMist", "taunt"), ("turnToMist", "vortex"),
        ("tidalWave", "lightningFlash"),
    ]
}


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
    loader = ComponentLoader(planner, ROOT)
    loader.load("abilities/goals/neutralize")
    loader.load("abilities/primitives/ab_catalog")
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n"
    assert planner.HtnCompileCustomVariables(text + kit) is None
    return _solutions(planner, "win.")


class TwoHandsTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_mist_then_push(self):
        self.assert_plan("win.", contains=[
            "opCast(player, turnToMist, sentinel)", "opCast(mage, fireball, sentinel)",
            "opForcedMove(mage, sentinel, bridge, pit)", "opExploit(mage, sentinel, chasm, fell)"])

    def test_example_2_mist_then_pull_across(self):
        plans = plans_with("turnToMist", "hook")
        ops = " ".join(json.dumps(p) for p in plans)
        assert plans and "overlook" in ops, "the mage should hook it across the pit from the overlook"
        self._record(True, "Example 2: mist, then a hook from the overlook drops it")

    def test_example_3_soak_then_jolt(self):
        plans = plans_with("tidalWave", "lightningFlash")
        ops = " ".join(json.dumps(p) for p in plans)
        assert plans and "electrocuted" in ops and "dead" in ops
        self._record(True, "Example 3: a wave soaks it, the flash short-circuits it")

    def test_example_4_draw_it_down(self):
        plans = plans_with("turnToMist", "vortex")
        ops = " ".join(json.dumps(p) for p in plans)
        assert plans and '"pit"' in ops and "fell" in ops
        self._record(True, "Example 4: mist, then a vortex on the pit draws it in")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_six_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_each_hand_matters(self):
        """Swapping who holds which skill still wins: the combo is about the
        pair, not the seat."""
        assert plans_with("fireball", "turnToMist") and plans_with("lightningFlash", "tidalWave")
        self._record(True, "P3: the pairs win whichever companion holds which half")

    def test_property_p4_the_mist_is_a_moment(self):
        """The mist lasts through one more cast: a push then lands. With the
        sentinel heavy again, nothing moves it."""
        assert not plans_with("fireball", "fireball")
        assert not plans_with("turnToMist", "turnToMist")
        self._record(True, "P4: mist alone or a push alone leaves the sentinel standing")


def run_tests():
    suite = TwoHandsTest()
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
