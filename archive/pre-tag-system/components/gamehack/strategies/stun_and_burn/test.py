"""Tests for stun_and_burn strategy component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite

SKILLED_WORLD = [
    "location(room)", "location(inn)", "location(hut)",
    "enemy(gob)", "at(gob, hut)", "at(companionI, inn)", "at(companionF, inn)",
    "companion(companionI)", "companion(companionF)",
    "hasSkill(companionI, iceBlastSkill)", "hasSkill(companionF, fireballSkill)",
    "skillAppliesTag(iceBlastSkill, stunned)", "skillAppliesTag(fireballSkill, burning)",
]


class StunAndBurnTest(HtnTestSuite):
    """Test suite for stun_and_burn strategy."""

    def setup(self):
        """Load stun_and_burn and all dependencies."""
        self.load_component("gamehack/strategies/stun_and_burn")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_no_way_to_stun_fails(self):
        """Example 1: nothing applies stunned or burning: no plan."""
        self.set_state(["location(room)", "location(hut)", "enemy(gob)", "at(gob, hut)",
                        "at(player, room)", "companion(player)"])
        self.assert_no_plan("stunAndBurn(gob).")

    def test_example_2_world_with_the_skills(self):
        """Example 2: companionI stuns, then companionF burns."""
        self.set_state(SKILLED_WORLD)
        self.assert_plan_set("stunAndBurn(gob).", [
            "opMoveTo(companionI, inn, hut), opUseSkill(companionI, iceBlastSkill, gob), opApplyTag(stunned, gob), "
            "opMoveTo(companionF, inn, hut), opUseSkill(companionF, fireballSkill, gob), opApplyTag(burning, gob)",
        ])

    def test_example_3_individual_tag_works(self):
        """Example 3: the building block applyTag works on its own."""
        self.set_state(["location(inn)", "location(hut)", "at(companionW, inn)", "at(gob, hut)",
                        "companion(companionW)", "hasSkill(companionW, waterSkill)", "skillAppliesTag(waterSkill, wet)"])
        self.assert_plan_set("applyTag(wet, gob).",
            ["opMoveTo(companionW, inn, hut), opUseSkill(companionW, waterSkill, gob), opApplyTag(wet, gob)"])

    def test_example_4_immune_to_burning(self):
        """Example 4: a target immune to burning rules the strategy out."""
        self.set_state(SKILLED_WORLD + ["immune(gob, burning)"])
        self.assert_no_plan("stunAndBurn(gob).")

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_fails_without_skills(self):
        """P1: No plan when nothing applies stunned or burning."""
        self.set_state(["location(room)", "location(hut)", "enemy(gob)", "at(gob, hut)", "at(player, room)",
                        "companion(player)", "at(companionE, hut)", "companion(companionE)",
                        "hasSkill(companionE, lightningSkill)", "skillAppliesTag(lightningSkill, electrified)"])
        self.assert_no_plan("stunAndBurn(gob).")

    def test_property_p2_works_with_skills(self):
        """P2: With the skills, the target ends stunned and burning."""
        self.set_state(SKILLED_WORLD)
        self.run_goal("stunAndBurn(gob)")
        state = self.get_state()
        assert any("hasTag(gob,stunned)" in f for f in state), "P2 violated: gob should be stunned"
        assert any("hasTag(gob,burning)" in f for f in state), "P2 violated: gob should be burning"


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
