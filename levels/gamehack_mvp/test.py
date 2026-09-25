"""Tests for gamehack_mvp level."""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite
from indhtnpy import findAllPlansResultToPrologStringList

COMPANIONS = ("player", "frost")
PLAN = ("opStayInLocation(player), opAggro(gob, player), opMoveTo(player, room, pool), opAggroMoveTo(gob, room, pool), "
        "opMoveTo(frost, room, pool), opUseSkill(frost, frostSkill, gob), opApplyTag(stunned, gob), opApplyTag(dead, gob)")


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

    def test_property_p3_two_companions(self):
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

    def test_example_1_defeat_has_one_plan(self):
        """Example 1: one plan: the player lures gob into the pool, frost chills it there."""
        self.assert_plan_set("defeat(gob).", [PLAN])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_only_wet_and_freeze(self):
        """P1: no oil and no stun skill: only wetAndFreeze."""
        self._assert_count("oilAndBurn(gob).", 0)
        self._assert_count("stunAndSlow(gob).", 0)

    def test_property_p2_tags_applied(self):
        """P2: After defeat(gob), gob is stunned and dead."""
        self.run_goal("defeat(gob)")
        state = self.get_state()
        for tag in ("stunned", "dead"):
            assert any(f"hasTag(gob,{tag})" in f for f in state), f"P2 violated: gob should have {tag}"


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
