"""Tests for gamehack_multipath level."""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite
from indhtnpy import findAllPlansResultToPrologStringList


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

    # =========================================================================
    # Example Tests
    # =========================================================================

    def test_example_1_wet_and_electrify_viable(self):
        """Example 1: 36 wetAndElectrify plans."""
        self._assert_count("wetAndElectrify(gob).", 36)
        self.assert_plan("defeat(gob).", contains=["opApplyTag(wet, gob)", "opApplyTag(electrified, gob)"])

    def test_example_2_stun_and_slow_viable(self):
        """Example 2: 12 stunAndSlow plans (two companions synchronize)."""
        self._assert_count("stunAndSlow(gob).", 12)
        self.assert_plan("defeat(gob).", contains=["opSynchronize"])

    def test_example_3_stun_and_burn_viable(self):
        """Example 3: 48 stunAndBurn plans."""
        self._assert_count("stunAndBurn(gob).", 48)
        self.assert_plan("defeat(gob).", contains=["opApplyTag(stunned, gob)", "opApplyTag(burning, gob)"])

    def test_example_4_many_distinct_plans(self):
        """Example 4: defeat(gob) returns 96 distinct plans (12 + 36 + 48)."""
        plans = self._assert_count("defeat(gob).", 96)
        assert all(p.endswith("opApplyTag(dead, gob)") for p in plans)

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_companion_skill_way_for_wet(self):
        """P1: some plan wets gob with a companion's waterSkill (it also lands clean; the other ways don't)."""
        self.assert_plan("defeat(gob).", contains=["opUseSkill(companionA, waterSkill, gob), opApplyTag(wet, gob), opApplyTag(clean, gob)"])

    def test_property_p2_location_way_for_wet(self):
        """P2: some plan wets gob by luring it to the lake shore, some to the sea."""
        self.assert_plan("defeat(gob).", contains=[
            "opAggroMoveTo(gob, arena, lakeShore), opApplyTag(wet, gob)",
            "opAggroMoveTo(gob, arena, sea), opApplyTag(wet, gob)"])

    def test_property_p3_agent_skill_way_for_electrified(self):
        """P3: some plan electrifies gob with the static tesla tower's skill."""
        self.assert_plan("defeat(gob).", contains=["opUseSkill(teslaTower, lightningSkill, gob), opApplyTag(electrified, gob)"])

    def test_property_p4_location_and_agent_ways_for_stunned(self):
        """P4: at the glacier, gob gets stunned by the location or by the ice elemental's skill."""
        self.assert_plan("defeat(gob).", contains=[
            "opAggroMoveTo(gob, arena, glacier), opApplyTag(stunned, gob)",
            "opAggroMoveTo(gob, arena, glacier), opUseSkill(iceElemental, iceBlastSkill, gob), opApplyTag(stunned, gob)"])

    def test_property_p5_state_after_wet_and_electrify(self):
        """P5: running wetAndElectrify(gob) tags gob with wet and electrified."""
        self.run_goal("wetAndElectrify(gob)")
        state = self.get_state()
        assert any("hasTag(gob,wet)" in f for f in state), f"P5 violated: gob should be wet. State: {state}"
        assert any("hasTag(gob,electrified)" in f for f in state), f"P5 violated: gob should be electrified. State: {state}"
        self._record(True, "P5: gob is wet and electrified after wetAndElectrify")

    def test_property_p6_state_after_stun_and_burn(self):
        """P6: running stunAndBurn(gob) tags gob with stunned and burning."""
        self.run_goal("stunAndBurn(gob)")
        state = self.get_state()
        assert any("hasTag(gob,stunned)" in f for f in state), f"P6 violated: gob should be stunned. State: {state}"
        assert any("hasTag(gob,burning)" in f for f in state), f"P6 violated: gob should be burning. State: {state}"
        self._record(True, "P6: gob is stunned and burning after stunAndBurn")

    def test_property_p7_skill_learning_in_stun_and_slow(self):
        """P7: some stunAndSlow plan gets a skill from a shrine."""
        self.assert_plan_matches_any("stunAndSlow(gob).", [
            {"contains": ["opSwapSkill", "opSynchronize"]},
            {"contains": ["opGetSkill", "opSynchronize"]},
        ])


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
