"""Tests for gamehack_mvp level."""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite
from indhtnpy import findAllPlansResultToPrologStringList

PLAN = ("opStayInLocation(player), opUseSkill(player, waterSkill, gob), opApplyTag(wet, gob), "
        "opStayInLocation(player), opUseSkill(player, lightningSkill, gob), opApplyTag(electrified, gob), "
        "opApplyTag(dead, gob)")


class GamehackMvpTest(HtnTestSuite):
    """Test suite for gamehack_mvp level."""

    def setup(self):
        """Load the defeat goal (and every component it depends on), then the level."""
        self.load_component("gamehack/goals/defeat")
        self.load_level("levels/gamehack_mvp")

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

    # =========================================================================
    # Example Tests
    # =========================================================================

    def test_example_1_defeat_has_one_plan(self):
        """Example 1: defeat(gob) has one plan: the player wets, then electrifies, gob."""
        self.assert_plan_set("defeat(gob).", [PLAN])

    def test_example_2_wet_via_water_skill(self):
        """Example 2: applyTag(wet, gob) uses the player's waterSkill."""
        self.assert_plan_set("applyTag(wet, gob).",
            ["opStayInLocation(player), opUseSkill(player, waterSkill, gob), opApplyTag(wet, gob)"])

    def test_example_3_electrified_via_lightning_skill(self):
        """Example 3: applyTag(electrified, gob) uses the player's lightningSkill."""
        self.assert_plan_set("applyTag(electrified, gob).",
            ["opStayInLocation(player), opUseSkill(player, lightningSkill, gob), opApplyTag(electrified, gob)"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_no_stun_and_slow(self):
        """P1: no slow skill and one companion -> stunAndSlow fails."""
        self._assert_count("stunAndSlow(gob).", 0)

    def test_property_p2_both_tags_applied(self):
        """P2: After defeat(gob), gob is wet, electrified and dead."""
        self.run_goal("defeat(gob)")
        state = self.get_state()
        for tag in ("wet", "electrified", "dead"):
            assert any(f"hasTag(gob,{tag})" in f for f in state), f"P2 violated: gob should have {tag}"

    def test_property_p3_no_movement(self):
        """P3: companion and target stand together -> no move operators."""
        self.assert_plan("defeat(gob).", not_contains=["opMoveTo", "opAggroMoveTo"])


def run_tests():
    """Run all tests in this file."""
    suite = GamehackMvpTest()
    suite.setup()

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
