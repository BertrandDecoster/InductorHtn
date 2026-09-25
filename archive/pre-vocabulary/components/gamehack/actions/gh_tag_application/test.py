"""Tests for gh_tag_application action component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite


class GhTagApplicationTest(HtnTestSuite):
    """Test suite for gh_tag_application action."""

    def setup(self):
        """Load gh_tag_application and all its dependencies."""
        self.load_component("gamehack/actions/gh_tag_application")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_path1_ally_has_skill(self):
        """Example 1: Path 1 - Ally has matching skill

        Given: companionW has waterSkill, skillAppliesTag(waterSkill, wet)
        When: applyTagNotPresent(wet, gob)
        Then: companionW moves to gob and applies wet
        """
        self.set_state([
            "at(companionW, inn)",
            "at(gob, hut)",
            "hasSkill(companionW, waterSkill)",
            "skillAppliesTag(waterSkill, wet)",
            "ally(companionW)"
        ])

        self.assert_plan("applyTagNotPresent(wet, gob).",
            contains=["opApplyTag(wet, gob)"])

        self.assert_state_after("applyTagNotPresent(wet, gob).",
            has=["hasTag(gob,wet)"])

    def test_example_2_path1_ally_learns_skill(self):
        """Example 2: Path 1 - Ally learns skill at location

        Given: companionI has iceBlastSkill, needs to learn waterSkill at sea
        When: applyTagNotPresent(wet, gob)
        Then: Goes to sea, swaps skill, goes to gob, applies wet
        """
        self.set_state([
            "at(companionI, inn)",
            "at(gob, hut)",
            "hasSkill(companionI, iceBlastSkill)",
            "ally(companionI)",
            "skillAppliesTag(waterSkill, wet)",
            "canGetSkillAtLocation(sea, waterSkill)"
        ])

        self.assert_plan("applyTagNotPresent(wet, gob).",
            contains=["opSwapSkill", "opApplyTag(wet, gob)"])

    def test_example_3_path2_location_applies_tag(self):
        """Example 3: Path 2 - Location applies tag via aggro lure

        Given: locationCanApplyTag(lake, wet), player is ally
        When: applyTagNotPresent(wet, gob)
        Then: Gob lured to lake via aggro
        """
        self.set_state([
            "at(gob, hut)",
            "at(player, room)",
            "locationCanApplyTag(lake, wet)",
            "ally(player)"
        ])

        self.assert_plan("applyTagNotPresent(wet, gob).",
            contains=["opAggroMoveTo(gob, hut, lake)"])

        self.assert_state_after("applyTagNotPresent(wet, gob).",
            has=["at(gob,lake)"])

    def test_example_4_path3_mob_has_skill(self):
        """Example 4: Path 3 - Non-ally mob has matching skill

        Given: teslaTower has lightningSkill (not an ally), at lake
        When: applyTagNotPresent(electrocute, gob)
        Then: Gob and teslaTower brought together
        """
        self.set_state([
            "at(gob, hut)",
            "at(teslaTower, lake)",
            "hasSkill(teslaTower, lightningSkill)",
            "skillAppliesTag(lightningSkill, electrocute)",
            "enemy(teslaTower)",
            "at(player, room)",
            "ally(player)"
        ])

        # Path 3 should work - bring gob to teslaTower or vice versa
        self.assert_plan("applyTagNotPresent(electrocute, gob).")

    def test_example_5_no_path_available(self):
        """Example 5: No path available for ice tag

        Given: No ice skills, locations, or mobs
        When: applyTagNotPresent(ice, gob)
        Then: Planning fails
        """
        self.set_state([
            "at(gob, hut)",
            "at(player, room)",
            "ally(player)"
        ])

        self.assert_no_plan("applyTagNotPresent(ice, gob).")

    # =========================================================================
    # Additional Tests
    # =========================================================================

    def test_path1_direct_with_individual_tags(self):
        """Path 1 with individual tag verification for wet."""
        self.set_state([
            "at(companionE, hut)",
            "at(gob, hut)",
            "hasSkill(companionE, lightningSkill)",
            "skillAppliesTag(lightningSkill, electrocute)",
            "ally(companionE)"
        ])

        self.assert_plan("applyTagNotPresent(electrocute, gob).",
            contains=["opApplyTag(electrocute, gob)"])

        self.assert_state_after("applyTagNotPresent(electrocute, gob).",
            has=["hasTag(gob,electrocute)"])

    def test_full_applyTag_integration(self):
        """Test applyTag dispatching through applyTagNotPresent.

        applyTag checks if tag present, delegates to applyTagNotPresent if not.
        """
        self.set_state([
            "at(companionE, hut)",
            "at(gob, hut)",
            "hasSkill(companionE, lightningSkill)",
            "skillAppliesTag(lightningSkill, electrocute)",
            "ally(companionE)"
        ])

        # applyTag should dispatch to applyTagNotPresent since gob doesn't have electrocute
        self.assert_plan("applyTag(electrocute, gob).",
            contains=["opApplyTag(electrocute, gob)"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_tag_applied(self):
        """P1: After successful plan, target has the requested tag."""
        self.set_state([
            "at(companionW, inn)",
            "at(gob, hut)",
            "hasSkill(companionW, waterSkill)",
            "skillAppliesTag(waterSkill, wet)",
            "ally(companionW)"
        ])

        self.run_goal("applyTagNotPresent(wet, gob)")
        state = self.get_state()

        has_wet = any("hasTag(gob,wet)" in f for f in state)
        assert has_wet, "P1 violated: gob should have wet tag after applyTagNotPresent"


def run_tests():
    """Run all tests in this file."""
    suite = GhTagApplicationTest()
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
