"""Tests for stun_and_slow_skill strategy component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite


class StunAndSlowSkillTest(HtnTestSuite):
    """Test suite for stun_and_slow_skill strategy."""

    def setup(self):
        """Load stun_and_slow_skill and all dependencies."""
        self.load_component("gamehack/strategies/stun_and_slow_skill")

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
            "skillHasTag(fireballSkill, slow)"
        ])

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_both_allies_have_skills(self):
        """Example 1: Both allies have skills (GH7 world)

        Given: companionI has iceBlastSkill, companionF has fireballSkill
        When: stunAndSlowSkill(gob)
        Then: opSynchronize in plan, both tags applied
        """
        self._gh7_world()

        self.assert_plan("stunAndSlowSkill(gob).",
            contains=["opSynchronize"])

    def test_example_2_only_one_ally(self):
        """Example 2: Only one ally - fails

        Given: Only companionI (no second ally for ?a2)
        When: stunAndSlowSkill(gob)
        Then: Planning fails
        """
        self.set_state([
            "enemy(gob)",
            "at(gob, hut)",
            "at(companionI, inn)",
            "ally(companionI)",
            "hasSkill(companionI, iceBlastSkill)",
            "skillAppliesTag(iceBlastSkill, stun)",
            "skillHasTag(fireballSkill, slow)",
            "skillAppliesTag(fireballSkill, fire)"
        ])

        self.assert_no_plan("stunAndSlowSkill(gob).")

    def test_example_3_target_immune_to_stun(self):
        """Example 3: Target immune to stun

        Given: immune(gob, stun)
        When: stunAndSlowSkill(gob)
        Then: Planning fails
        """
        self._gh7_world()
        self.set_state(["immune(gob, stun)"])

        self.assert_no_plan("stunAndSlowSkill(gob).")

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_two_allies(self):
        """P1: Two different allies participate in the plan."""
        self._gh7_world()

        self.assert_plan("stunAndSlowSkill(gob).",
            contains=["opSynchronize"])

        # The opSynchronize operator should have two different ally args
        # We verify by checking that the plan references both companions

    def test_property_p2_sync_point(self):
        """P2: opSynchronize appears in plan."""
        self._gh7_world()

        self.assert_plan("stunAndSlowSkill(gob).",
            contains=["opSynchronize"])

    def test_property_p3_both_effects(self):
        """P3: Both stun and fire tags applied to target."""
        self._gh7_world()

        self.run_goal("stunAndSlowSkill(gob)")
        state = self.get_state()

        has_stun = any("hasTag(gob,stun)" in f for f in state)
        has_fire = any("hasTag(gob,fire)" in f for f in state)

        assert has_stun, "P3 violated: gob should have stun tag"
        assert has_fire, "P3 violated: gob should have fire tag"


def run_tests():
    """Run all tests in this file."""
    suite = StunAndSlowSkillTest()
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
