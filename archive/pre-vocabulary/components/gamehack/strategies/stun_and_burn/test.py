"""Tests for stun_and_burn strategy component (documented failure)."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite


class StunAndBurnTest(HtnTestSuite):
    """Test suite for stun_and_burn strategy (documented failure)."""

    def setup(self):
        """Load stun_and_burn and all dependencies."""
        self.load_component("gamehack/strategies/stun_and_burn")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_standard_world_fails(self):
        """Example 1: Standard world - no ice/fire path available

        Given: No skills or locations for ice or fire
        When: stunAndBurn(gob)
        Then: Planning fails
        """
        self.set_state([
            "enemy(gob)",
            "at(gob, hut)",
            "at(player, room)",
            "ally(player)"
        ])

        self.assert_no_plan("stunAndBurn(gob).")

    def test_example_2_hypothetical_world_with_skills(self):
        """Example 2: Hypothetical world with ice+fire skills

        Given: Allies with iceSkill and fireballSkill
        When: stunAndBurn(gob)
        Then: Plan succeeds, both tags applied
        """
        self.set_state([
            "enemy(gob)",
            "at(gob, hut)",
            "at(companionI, inn)",
            "at(companionF, inn)",
            "ally(companionI)",
            "ally(companionF)",
            "hasSkill(companionI, iceSkill)",
            "hasSkill(companionF, fireballSkill)",
            "skillAppliesTag(iceSkill, ice)",
            "skillAppliesTag(fireballSkill, fire)"
        ])

        self.assert_plan("stunAndBurn(gob).",
            contains=["opApplyTag(ice, gob)", "opApplyTag(fire, gob)"])

    def test_example_3_individual_tag_works(self):
        """Example 3: Individual building block works (wet via ally)

        Given: companionW has waterSkill
        When: applyTag(wet, gob) (individual tag, not stunAndBurn)
        Then: Plan succeeds
        """
        self.set_state([
            "at(companionW, inn)",
            "at(gob, hut)",
            "ally(companionW)",
            "hasSkill(companionW, waterSkill)",
            "skillAppliesTag(waterSkill, wet)"
        ])

        self.assert_plan("applyTag(wet, gob).",
            contains=["opApplyTag(wet, gob)"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_fails_without_skills(self):
        """P1: No plan when ice/fire skills absent from world."""
        self.set_state([
            "enemy(gob)",
            "at(gob, hut)",
            "at(player, room)",
            "ally(player)",
            "at(companionE, hut)",
            "ally(companionE)",
            "hasSkill(companionE, lightningSkill)",
            "skillAppliesTag(lightningSkill, electrocute)"
            # Note: no ice or fire skills available
        ])

        self.assert_no_plan("stunAndBurn(gob).")

    def test_property_p2_works_with_skills(self):
        """P2: Plan succeeds when ice/fire skills provided."""
        self.set_state([
            "enemy(gob)",
            "at(gob, hut)",
            "at(companionI, hut)",
            "at(companionF, hut)",
            "ally(companionI)",
            "ally(companionF)",
            "hasSkill(companionI, iceSkill)",
            "hasSkill(companionF, fireballSkill)",
            "skillAppliesTag(iceSkill, ice)",
            "skillAppliesTag(fireballSkill, fire)"
        ])

        self.run_goal("stunAndBurn(gob)")
        state = self.get_state()

        has_ice = any("hasTag(gob,ice)" in f for f in state)
        has_fire = any("hasTag(gob,fire)" in f for f in state)

        assert has_ice, "P2 violated: gob should have ice tag"
        assert has_fire, "P2 violated: gob should have fire tag"


def run_tests():
    """Run all tests in this file."""
    suite = StunAndBurnTest()
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
