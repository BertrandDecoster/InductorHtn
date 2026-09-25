"""Tests for the clear_location goal component."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src/Python")))

from htn_test_framework import HtnTestSuite

WORLD = [
    "location(camp)", "location(hut)", "location(storage)", "location(corridor)",
    "locationCanApplyTag(storage, oil)", "locationCanApplyTag(corridor, wet)",
    "companion(pyro)", "companion(frost)", "at(pyro, camp)", "at(frost, camp)",
    "hasSkill(pyro, fireballSkill)", "skillAppliesTag(fireballSkill, burning)",
    "hasSkill(frost, frostSkill)", "skillAppliesTag(frostSkill, chilled)",
    "enemy(guard1)", "at(guard1, hut)", "vulnerableToLocationCombo(guard1, oil, burning)",
    "enemy(guard2)", "at(guard2, hut)", "vulnerableToLocationCombo(guard2, wet, chilled)",
]


class ClearLocationTest(HtnTestSuite):
    """Test suite for the clear_location goal."""

    def setup(self):
        self.load_component("goals/clear_location")
        self.set_state(WORLD)

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_two_guards(self):
        """Example 1: guard1 is burned on the oil, then guard2 is chilled in the water."""
        self.assert_plan_set("clearLocation(hut).", [
            "opMoveTo(frost, camp, hut), opAggro(guard1, frost), opMoveTo(frost, hut, storage), "
            "opAggroMoveTo(guard1, hut, storage), opMoveTo(pyro, camp, storage), opUseSkill(pyro, fireballSkill, guard1), "
            "opRemoveLocationTag(oil, storage), opAddLocationTag(burning, storage), "
            "opApplyTag(burning, pyro), opApplyTag(burning, frost), opApplyTag(burning, guard1), opApplyTag(dead, guard1), "
            "opMoveTo(pyro, storage, hut), opAggro(guard2, pyro), opMoveTo(pyro, hut, corridor), "
            "opAggroMoveTo(guard2, hut, corridor), opMoveTo(frost, storage, corridor), opUseSkill(frost, frostSkill, guard2), "
            "opApplyTag(stunned, guard2), opApplyTag(dead, guard2)"])

    def test_example_2_nobody_to_clear(self):
        """Example 2: nobody to clear."""
        self.assert_plan_set("clearLocation(camp).", [""])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_all_dead(self):
        """P1: every enemy that was at the location ends dead."""
        self.assert_state_after("clearLocation(hut).", has=["hasTag(guard1,dead)", "hasTag(guard2,dead)"])


def run_tests():
    """Run all tests in this file."""
    suite = ClearLocationTest()
    for method_name in dir(suite):
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
