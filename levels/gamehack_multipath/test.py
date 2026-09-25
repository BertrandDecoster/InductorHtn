"""Tests for gamehack_multipath level."""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite
from indhtnpy import findAllPlansResultToPrologStringList

COMPANIONS = ("player", "companionA", "companionB", "companionC")


class GamehackMultipathTest(HtnTestSuite):
    """Test suite for gamehack_multipath level."""

    def setup(self):
        """Load the defeat goal (and every component it depends on), then the level."""
        self.load_component("gamehack/goals/defeat")
        self.load_level("levels/gamehack_multipath")

    def load_level(self, level_path):
        """Load a level's HTN file."""
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        level_file = os.path.join(base_path, level_path, "level.htn")
        with open(level_file, "r", encoding="utf-8") as f:
            content = f.read()
        error = self._planner.HtnCompileCustomVariables(content)
        if error:
            raise RuntimeError(f"Failed to compile level: {error}")

    def _plans(self, goal):
        """Every plan for the goal, as strings (empty if none)."""
        self._reload_file()
        error, result = self._planner.FindAllPlansCustomVariables(goal)
        assert error is None, f"Planning error: {error}"
        solutions = json.loads(result)
        if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
            return []
        return findAllPlansResultToPrologStringList(result)

    def _assert_count(self, goal, n):
        plans = self._plans(goal)
        assert len(plans) == n, f"{goal}: expected {n} plans, got {len(plans)}"
        assert len(plans) == len(set(plans)), f"{goal}: duplicate plans"
        return plans

    def test_property_p5_two_companions(self):
        """Every plan ends with gob dead, and two different companions act in it."""
        plans = self._plans("defeat(gob).")
        assert plans, "expected plans"
        for p in plans:
            assert p.endswith("opApplyTag(dead, gob)"), p
            actors = {c for c in COMPANIONS
                      if f"opMoveTo({c}," in p or f"opUseSkill({c}," in p or f"opAggro(gob, {c})" in p
                      or f"opStayInLocation({c})" in p}
            assert len(actors) >= 2, f"one companion only: {p}"

    # =========================================================================
    # Example Tests
    # =========================================================================

    def test_example_1_wet_and_freeze(self):
        """Example 1: 36 wetAndFreeze plans (the lake shore, the sea or the glacier; a lurer and a chilled caster)."""
        self._assert_count("wetAndFreeze(gob).", 36)

    def test_example_2_stun_and_slow(self):
        """Example 2: 12 stunAndSlow plans (two companions synchronize)."""
        self._assert_count("stunAndSlow(gob).", 12)

    def test_example_3_oil_and_burn(self):
        """Example 3: 12 oilAndBurn plans (gob lured into the refinery)."""
        self._assert_count("oilAndBurn(gob).", 12)

    def test_example_4_many_distinct_plans(self):
        """Example 4: defeat(gob) returns 60 distinct plans (36 + 12 + 12)."""
        self._assert_count("defeat(gob).", 60)

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_water_and_ice(self):
        """P1: gob is frozen in water (the lake shore, the sea) and on ice (the glacier)."""
        self.assert_plan("wetAndFreeze(gob).", contains=[
            "opAggroMoveTo(gob, arena, lakeShore)", "opAggroMoveTo(gob, arena, sea)", "opAggroMoveTo(gob, arena, glacier)"])

    def test_property_p2_held_skill(self):
        """P2: companionA, who holds frostSkill, chills gob while another companion lures it."""
        self.assert_plan("wetAndFreeze(gob).", contains=["opUseSkill(companionA, frostSkill, gob), opApplyTag(stunned, gob)"])

    def test_property_p3_skill_from_a_shrine(self):
        """P3: some stunAndSlow plan gets a skill from a shrine."""
        self.assert_plan_matches_any("stunAndSlow(gob).", [
            {"contains": ["opSwapSkill", "opSynchronize"]},
            {"contains": ["opGetSkill", "opSynchronize"]},
        ])

    def test_property_p4_state_after_oil_and_burn(self):
        """P4: oilAndBurn leaves the refinery burning and gob dead."""
        self.run_goal("oilAndBurn(gob)")
        state = self.get_state()
        assert any("locationCanApplyTag(refinery,burning)" in f for f in state), f"P4 violated. State: {state}"
        assert any("hasTag(gob,dead)" in f for f in state), f"P4 violated: gob should be dead. State: {state}"


def run_tests():
    suite = GamehackMultipathTest()

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
    success = run_tests()
    sys.exit(0 if success else 1)
