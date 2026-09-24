"""Tests for the Slipway level (elemental chemistry)."""

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
POOL = ["rainCall", "tidalWave", "zap", "chainLightning", "oilFlask", "tarPot", "gust", "magnetize"]

# The measured matrix: the pairs that win, and nothing else does.
WINNING = {
    frozenset(p) for p in [
        # short it: soak, then jolt
        ("rainCall", "zap"), ("rainCall", "chainLightning"),
        ("tidalWave", "zap"), ("tidalWave", "chainLightning"),
        # slide it: oil, then push or hook it into the dock
        ("oilFlask", "gust"), ("oilFlask", "tidalWave"), ("oilFlask", "magnetize"),
        ("tarPot", "gust"), ("tarPot", "tidalWave"), ("tarPot", "magnetize"),
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
    planner.SetMemoryBudget(256 * 1024 * 1024)
    loader = ComponentLoader(planner, ROOT)
    loader.load("abilities/goals/neutralize")
    loader.load("abilities/primitives/ab_catalog")
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n"
    assert planner.HtnCompileCustomVariables(text + kit) is None
    return _solutions(planner, "win.")


def ops(plans):
    return " ".join(json.dumps(p) for p in plans).replace(" ", "")


class SlipwayTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_oil_then_push(self):
        self.assert_plan("win.", contains=[
            "opGrant(player, crab, oiled)", "opForcedMove(mage, crab, slipway, dock)",
            "opExploit(mage, crab, deepWater, fell)"])

    def test_example_2_tar_then_hook_across(self):
        text = ops(plans_with("tarPot", "magnetize"))
        assert '"opNavigate":[{"mage":[]},{"stairs":[]},{"gantry":[]}]' in text, \
            "the mage should hook it from the gantry"
        assert '"opForcedMove":[{"mage":[]},{"crab":[]},{"slipway":[]},{"dock":[]}]' in text
        self._record(True, "Example 2: tar, then a hook from the gantry drags it into the dock")

    def test_example_3_soak_then_jolt(self):
        text = ops(plans_with("rainCall", "zap"))
        assert '{"electrocuted":[]},{"dead":[]}' in text
        self._record(True, "Example 3: rain, then a jolt, short-circuits it")

    def test_example_4_wave_serves_two_roles(self):
        soak = ops(plans_with("tidalWave", "chainLightning"))
        push = ops(plans_with("oilFlask", "tidalWave"))
        assert '{"dead":[]}' in soak and '{"fell":[]}' in push
        self._record(True, "Example 4: tidalWave soaks for the jolt, or pushes the oiled crab")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_ten_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_each_hand_matters(self):
        assert plans_with("gust", "oilFlask") and plans_with("zap", "tidalWave")
        self._record(True, "P3: the pairs win whichever companion holds which half")

    def test_property_p4_dry_jolt_and_dry_push_fail(self):
        assert not plans_with("zap", "gust"), "a dry, unoiled crab should only be stunned"
        assert not plans_with("tidalWave", "magnetize"), "a wet crab is still too heavy to move"
        self._record(True, "P4: a jolt without water, or a move without oil, does nothing")


def run_tests():
    suite = SlipwayTest()
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
