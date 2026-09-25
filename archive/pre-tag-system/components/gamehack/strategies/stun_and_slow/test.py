"""Tests for stun_and_slow strategy component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite

GH7_WORLD = [
    "location(room)", "location(inn)", "location(hut)",
    "enemy(gob)", "at(gob, hut)",
    "companion(player)", "companion(companionI)", "companion(companionF)",
    "at(companionI, inn)", "at(companionF, inn)", "at(player, room)",
    "hasSkill(companionI, iceBlastSkill)", "hasSkill(companionF, fireballSkill)",
    "skillAppliesTag(iceBlastSkill, stunned)", "skillAppliesTag(fireballSkill, burning)",
    "skillHasTag(fireballSkill, slow)",
]
PLAN = ("opMoveTo(companionI, inn, hut), opMoveTo(companionF, inn, hut), opSynchronize(companionI, companionF), "
        "opUseSkill(companionI, iceBlastSkill, gob), opApplyTag(stunned, gob), "
        "opUseSkill(companionF, fireballSkill, gob), opApplyTag(burning, gob)")


class StunAndSlowTest(HtnTestSuite):
    """Test suite for stun_and_slow strategy."""

    def setup(self):
        """Load stun_and_slow and all dependencies."""
        self.load_component("gamehack/strategies/stun_and_slow")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_both_companions_have_skills(self):
        """Example 1: companionI stuns while companionF's slow fireball lands.
        The player holds no skill and there is no object to learn from: one plan."""
        self.set_state(GH7_WORLD)
        self.assert_plan_set("stunAndSlow(gob).", [PLAN])

    def test_example_2_only_one_companion(self):
        """Example 2: one companion can't do both parts."""
        self.set_state([
            "location(inn)", "location(hut)", "enemy(gob)", "at(gob, hut)",
            "companion(companionI)", "at(companionI, inn)", "hasSkill(companionI, iceBlastSkill)",
            "skillAppliesTag(iceBlastSkill, stunned)", "skillHasTag(fireballSkill, slow)",
            "skillAppliesTag(fireballSkill, burning)",
        ])
        self.assert_no_plan("stunAndSlow(gob).")

    def test_example_3_target_immune_to_stunned(self):
        """Example 3: a target immune to stunned rules the strategy out."""
        self.set_state(GH7_WORLD + ["immune(gob, stunned)"])
        self.assert_no_plan("stunAndSlow(gob).")

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_two_companions(self):
        """P1: Two different companions take part."""
        self.set_state(GH7_WORLD)
        self.assert_plan("stunAndSlow(gob).", contains=["opSynchronize(companionI, companionF)"])

    def test_property_p2_sync_point(self):
        """P2: opSynchronize comes before either skill is used."""
        self.set_state(GH7_WORLD)
        self.assert_plan_set("stunAndSlow(gob).", [PLAN])

    def test_property_p3_both_effects(self):
        """P3: Both stunned and burning land on the target."""
        self.set_state(GH7_WORLD)
        self.run_goal("stunAndSlow(gob)")
        state = self.get_state()
        assert any("hasTag(gob,stunned)" in f for f in state), "P3 violated: gob should be stunned"
        assert any("hasTag(gob,burning)" in f for f in state), "P3 violated: gob should be burning"


def run_tests():
    """Run all tests in this file."""
    suite = StunAndSlowTest()
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
