"""Tests for the Crossing level."""

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
COMPANIONS = {"player", "mage", "warden"}

# Measured by `fun crossing --loadouts` (see design.md); a few are pinned here
# to keep the test fast.
WINNING = [("fireball", "frostBolt"), ("charge", "zap"), ("tidalWave", "iceStorm")]
LOSING = [("zap", "chainLightning"), ("gust", "fireball"), ("frostBolt", "iceStorm")]


def _solutions(planner, goal):
    error, result = planner.FindAllPlansCustomVariables(goal)
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    return solutions


def _actor(op):
    return list(op[list(op.keys())[0]][0].keys())[0]


def clears(pick, goal="clearCrossing."):
    """Whether the kit clears the level, on a fresh planner (a failed search
    locks the rule set)."""
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^knows\(player, \w+\)\.\n", "", text, flags=re.M)
    planner = HtnPlanner(False)
    loader = ComponentLoader(planner, ROOT)
    loader.load("abilities/goals/neutralize")
    loader.load("abilities/primitives/ab_catalog")
    kit = "".join(f"knows(player, {c}).\n" for c in pick)
    assert planner.HtnCompileCustomVariables(text + kit) is None
    return bool(_solutions(planner, goal))


class CrossingTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_the_default_kit_clears_the_crossing(self):
        self.assert_state_after("clearCrossing.", has=[
            "tag(sentry,dead)", "tag(bramble,", "tag(brute,fell)"])

    def test_example_2_the_sentry_is_soaked_then_jolted(self):
        self.assert_plan("neutralize(sentry).", contains=[
            "opCast(mage, rainCall, sentry)", "opExploit(player, sentry, electrocuted, dead)"])

    def test_example_3_the_brute_loses_its_armour_then_its_footing(self):
        self.assert_plan("neutralize(brute).", contains=[
            "opCast(warden, sunder, brute)", "opExploit(player, brute, chasm, fell)"])

    # -------------------------------------------------------------- properties

    def test_property_p1_no_companion_carries_a_plan_alone(self):
        plans = _solutions(self._planner, "clearCrossing.")
        assert plans, "the encounter must be solvable"
        for plan in plans:
            allies = {_actor(op) for op in plan} & COMPANIONS
            assert len(allies) >= 2, f"one companion carries this plan alone: {plan}"
        self._record(True, f"P1: {len(plans)} plans, none by one companion")

    def test_property_p2_the_boss_is_not_stunned(self):
        """Hard control slides off a boss; being soaked and jolted does not
        stun it either, and nothing outside its weakness list kills it."""
        self.assert_state_after("cast(warden, shieldBash, brute).",
                                not_has=["tag(brute,stunned)"])

    def test_property_p3_kits_that_win_and_lose(self):
        for pick in WINNING:
            assert clears(pick), f"{pick} should clear the crossing"
        for pick in LOSING:
            assert not clears(pick), f"{pick} should not clear the crossing"
        self._record(True, f"P3: {len(WINNING)} kits win, {len(LOSING)} lose, as measured")


def run_tests():
    suite = CrossingTest()
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
