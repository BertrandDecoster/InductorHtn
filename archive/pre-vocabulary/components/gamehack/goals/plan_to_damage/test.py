"""Tests for plan_to_damage goal component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite


class PlanToDamageTest(HtnTestSuite):
    """Test suite for plan_to_damage goal."""

    def setup(self):
        """Load plan_to_damage and all dependencies."""
        # Need all primitives + actions + both strategies + goal
        self.load_component("gamehack/primitives/gh_movement", reset_first=True)
        self.load_component("gamehack/primitives/gh_tags", reset_first=False)
        self.load_component("gamehack/primitives/gh_aggro", reset_first=False)
        self.load_component("gamehack/primitives/gh_skills", reset_first=False)
        self.load_component("gamehack/actions/gh_tag_application", reset_first=False)
        self.load_component("gamehack/strategies/stun_and_slow_skill", reset_first=False)
        self.load_component("gamehack/strategies/wet_and_electrocute", reset_first=False)
        self.load_component("gamehack/goals/plan_to_damage", reset_first=False)

    def _gh7_world(self):
        """Set up GH7-style world state."""
        self.set_state([
            "enemy(gob)",
            "at(gob, hut)",
            "at(companionI, inn)",
            "at(companionF, inn)",
            "at(player, room)",
            "ally(player)",
            "ally(companionI)",
            "ally(companionF)",
            "hasSkill(companionI, iceBlastSkill)",
            "hasSkill(companionF, fireballSkill)",
            "skillAppliesTag(iceBlastSkill, stun)",
            "skillAppliesTag(fireballSkill, fire)",
            "skillAppliesTag(lightningSkill, electrocute)",
            "skillAppliesTag(waterSkill, wet)",
            "skillHasTag(fireballSkill, slow)",
            "canGetSkillAtLocation(sea, waterSkill)",
            "canGetSkillAtLocation(mountain, iceBlastSkill)",
            "locationCanApplyTag(lake, wet)"
        ])

    def _gh4_world(self):
        """Set up GH4-style world state (no stun/slow skills)."""
        self.set_state([
            "enemy(gob)",
            "at(gob, hut)",
            "at(player, room)",
            "at(companionE, hut)",
            "at(companionW, inn)",
            "ally(player)",
            "ally(companionE)",
            "ally(companionW)",
            "hasSkill(companionE, lightningSkill)",
            "hasSkill(companionW, waterSkill)",
            "skillAppliesTag(lightningSkill, electrocute)",
            "skillAppliesTag(waterSkill, wet)",
            "locationCanApplyTag(lake, wet)",
            "locationCanApplyTag(sea, wet)"
        ])

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_gh7_world_both_strategies(self):
        """Example 1: GH7 world - both strategies produce plans

        Given: GH7 world with stun+slow and wet+electrocute paths
        When: planToDamage(gob)
        Then: Plans found
        """
        self._gh7_world()

        self.assert_plan("planToDamage(gob).", min_solutions=1)

    def test_example_2_gh4_world_only_wet_electrocute(self):
        """Example 2: GH4 world - only wetAndElectrocute works

        Given: GH4 world (no stun/slow skills)
        When: planToDamage(gob)
        Then: Plans found, using wetAndElectrocute path
        """
        self._gh4_world()

        self.assert_plan("planToDamage(gob).",
            contains=["opApplyTag(wet", "opApplyTag(electrocute"])

    def test_example_3_non_enemy_fails(self):
        """Example 3: Non-enemy target fails

        Given: No enemy(player)
        When: planToDamage(player)
        Then: Planning fails
        """
        self._gh7_world()

        self.assert_no_plan("planToDamage(player).")

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_strategy_selection_gh7(self):
        """P1: GH7 world selects stunAndSlowSkill (first method, has both allies)."""
        self._gh7_world()

        # stunAndSlowSkill uses opSynchronize - should be in first plan
        self.assert_plan("planToDamage(gob).",
            contains=["opSynchronize"])

    def test_property_p1_strategy_selection_gh4(self):
        """P1: GH4 world falls through to wetAndElectrocute."""
        self._gh4_world()

        # No stunAndSlowSkill possible (no stun/slow skills)
        # Should use wetAndElectrocute
        self.assert_plan("planToDamage(gob).",
            not_contains=["opSynchronize"])


def run_tests():
    """Run all tests in this file."""
    suite = PlanToDamageTest()
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
