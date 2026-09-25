"""Tests for wet_and_electrocute strategy component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite


class WetAndElectrocuteTest(HtnTestSuite):
    """Test suite for wet_and_electrocute strategy."""

    def setup(self):
        """Load wet_and_electrocute and all dependencies."""
        self.load_component("gamehack/strategies/wet_and_electrocute")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_both_tags_via_ally_skills(self):
        """Example 1: Both tags via ally skills (GH4-style world)

        Given: companionW has waterSkill, companionE has lightningSkill
        When: wetAndElectrocute(gob)
        Then: Plan succeeds, both tags applied
        """
        self.set_state([
            "enemy(gob)",
            "at(gob, hut)",
            "at(companionW, inn)",
            "at(companionE, hut)",
            "ally(companionW)",
            "ally(companionE)",
            "hasSkill(companionW, waterSkill)",
            "hasSkill(companionE, lightningSkill)",
            "skillAppliesTag(waterSkill, wet)",
            "skillAppliesTag(lightningSkill, electrocute)"
        ])

        self.assert_plan("wetAndElectrocute(gob).",
            contains=["opApplyTag(wet, gob)", "opApplyTag(electrocute, gob)"])

    def test_example_2_wet_via_location(self):
        """Example 2: Wet via location, electrocute via ally

        Given: lake applies wet, companionE has lightningSkill
        When: wetAndElectrocute(gob)
        Then: Gob lured to lake, then electrocuted
        """
        self.set_state([
            "enemy(gob)",
            "at(gob, hut)",
            "at(player, room)",
            "at(companionE, hut)",
            "ally(player)",
            "ally(companionE)",
            "hasSkill(companionE, lightningSkill)",
            "locationCanApplyTag(lake, wet)",
            "skillAppliesTag(lightningSkill, electrocute)"
        ])

        self.assert_plan("wetAndElectrocute(gob).",
            contains=["opApplyTag(electrocute, gob)"])

    def test_example_3_non_enemy_fails(self):
        """Example 3: Non-enemy fails

        Given: No enemy(player) fact
        When: wetAndElectrocute(player)
        Then: Planning fails
        """
        self.set_state([
            "ally(player)",
            "at(player, room)"
        ])

        self.assert_no_plan("wetAndElectrocute(player).")

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_both_tags(self):
        """P1: Target has both wet and electrocute after plan."""
        self.set_state([
            "enemy(gob)",
            "at(gob, hut)",
            "at(companionW, inn)",
            "at(companionE, hut)",
            "ally(companionW)",
            "ally(companionE)",
            "hasSkill(companionW, waterSkill)",
            "hasSkill(companionE, lightningSkill)",
            "skillAppliesTag(waterSkill, wet)",
            "skillAppliesTag(lightningSkill, electrocute)"
        ])

        self.run_goal("wetAndElectrocute(gob)")
        state = self.get_state()

        has_wet = any("hasTag(gob,wet)" in f for f in state)
        has_electrocute = any("hasTag(gob,electrocute)" in f for f in state)

        assert has_wet, "P1 violated: gob should have wet tag"
        assert has_electrocute, "P1 violated: gob should have electrocute tag"

    def test_property_p2_sequential_ordering(self):
        """P2: Wet applied before electrocute in plan.

        Verified by checking the plan string: opApplyTag(wet,...) appears
        before opApplyTag(electrocute,...). assert_operator_sequence can't
        distinguish same-name operators, so we check the raw plan string.
        """
        self.set_state([
            "enemy(gob)",
            "at(gob, hut)",
            "at(companionW, inn)",
            "at(companionE, hut)",
            "ally(companionW)",
            "ally(companionE)",
            "hasSkill(companionW, waterSkill)",
            "hasSkill(companionE, lightningSkill)",
            "skillAppliesTag(waterSkill, wet)",
            "skillAppliesTag(lightningSkill, electrocute)"
        ])

        import json
        from indhtnpy import findAllPlansResultToPrologStringList
        error, result = self._planner.FindAllPlansCustomVariables("wetAndElectrocute(gob).")
        assert error is None, f"Planning error: {error}"
        plan_strs = findAllPlansResultToPrologStringList(result)
        plan_str = plan_strs[0] if plan_strs else ""
        wet_pos = plan_str.find("opApplyTag(wet")
        elec_pos = plan_str.find("opApplyTag(electrocute")
        assert wet_pos >= 0, f"P2: opApplyTag(wet) not found in plan: {plan_str}"
        assert elec_pos >= 0, f"P2: opApplyTag(electrocute) not found in plan: {plan_str}"
        assert wet_pos < elec_pos, f"P2: wet should come before electrocute. Plan: {plan_str}"


def run_tests():
    """Run all tests in this file."""
    suite = WetAndElectrocuteTest()
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
