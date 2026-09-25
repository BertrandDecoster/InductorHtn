"""Tests for gamehack_gh4 level."""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite
from indhtnpy import findAllPlansResultToPrologStringList


class GamehackGh4Test(HtnTestSuite):
    """Test suite for gamehack_gh4 level."""

    def setup(self):
        """Load the defeat goal (and every component it depends on), then the level."""
        self.load_component("gamehack/goals/defeat")
        self.load_level("levels/gamehack_gh4")

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

    def test_example_1_defeat_plans(self):
        """Example 1: defeat(gob) has 43 plans, all wetAndElectrify."""
        plans = self._assert_count("defeat(gob).", 43)
        assert all(p.endswith("opApplyTag(dead, gob)") for p in plans)

    def test_example_2_wet_ways(self):
        """Example 2: 7 ways to wet gob: companionW's waterSkill, or a lure to the lake or the sea (3 lurers each)."""
        self._assert_count("applyTag(wet, gob).", 7)
        self.assert_plan("applyTag(wet, gob).", contains=[
            "opMoveTo(companionW, inn, hut), opUseSkill(companionW, waterSkill, gob), opApplyTag(wet, gob)",
            "opAggroMoveTo(gob, hut, lake), opApplyTag(wet, gob)",
            "opAggroMoveTo(gob, hut, sea), opApplyTag(wet, gob)"])

    def test_example_3_electrified_ways(self):
        """Example 3: 7 ways to electrify gob: companionE's lightning, or a lure to the tesla tower
        or to the electricity elemental (3 lurers each)."""
        self._assert_count("applyTag(electrified, gob).", 7)
        self.assert_plan("applyTag(electrified, gob).", contains=[
            "opStayInLocation(companionE), opUseSkill(companionE, lightningSkill, gob), opApplyTag(electrified, gob)",
            "opUseSkill(teslaTower, lightningSkill, gob)",
            "opUseSkill(electricityElemental, lightningSkill, gob)"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_only_wet_and_electrify(self):
        """P1: Only wetAndElectrify works (no stun or slow skill in GH4)."""
        self._assert_count("wetAndElectrify(gob).", 43)
        self._assert_count("stunAndSlow(gob).", 0)
        self._assert_count("stunAndBurn(gob).", 0)

    def test_property_p2_both_tags_applied(self):
        """P2: Target has wet, electrified and dead after the first plan."""
        self.run_goal("defeat(gob)")
        state = self.get_state()
        for tag in ("wet", "electrified", "dead"):
            assert any(f"hasTag(gob,{tag})" in f for f in state), f"P2 violated: gob should have {tag}"


def run_tests():
    """Run all tests in this file."""
    suite = GamehackGh4Test()
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
