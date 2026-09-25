"""Tests for the clear_location goal component."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src/Python")))

from htn_test_framework import HtnTestSuite

WORLD = [
    "location(camp)", "location(storage)", "location(corridor)", "location(generator)",
    "linked(camp, storage)", "linked(storage, camp)", "linked(camp, corridor)", "linked(corridor, camp)",
    "linked(corridor, generator)", "linked(generator, corridor)",
    "locationCanApplyTag(storage, oily)", "locationCanApplyTag(corridor, wet)",
    "locationCanApplyTag(generator, electrified)",
    "companion(pyro)", "companion(arcanist)", "companion(warden)",
    "at(pyro, camp)", "at(arcanist, camp)", "at(warden, camp)",
    "hasSkill(pyro, igniteSkill)", "skillAppliesTag(igniteSkill, burning)",
    "hasSkill(arcanist, freezeSkill)", "skillAppliesTag(freezeSkill, frozen)",
    "enemy(guard1)", "at(guard1, storage)", "vulnerableTo(guard1, burning)",
    "enemy(imp)", "at(imp, storage)", "vulnerableTo(imp, burning)",
    "enemy(guard2)", "at(guard2, corridor)", "vulnerableTo(guard2, electrified)",
    "enemy(ogre)", "at(ogre, corridor)", "vulnerableTo(ogre, burning)", "vulnerableTo(ogre, electrified)",
]


class ClearLocationTest(HtnTestSuite):
    """Test suite for the clear_location goal."""

    def setup(self):
        self.load_component("goals/clear_location")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_one_fire_takes_out_both(self):
        """Example 1: one fire takes out both enemies on the oil."""
        self.set_state(WORLD)
        self.assert_plan_set("clearLocation(storage).", [
            "opUseSkill(pyro, igniteSkill, storage), opAddLocationTag(burning, storage), "
            "opRemoveLocationTag(oily, storage), opRemoveLocationTag(burning, storage), opAddLocationTag(burning, storage), "
            "opApplyTag(burning, guard1), opApplyTag(burning, imp), "
            "opApplyTag(dead, guard1), opApplyTag(dead, imp)"])

    def test_example_2_nobody_to_clear(self):
        """Example 2: nobody to clear."""
        self.set_state(WORLD)
        self.assert_plan_set("clearLocation(camp).", [""])

    def test_example_3_order_matters(self):
        """Example 3: freezing the corridor for guard2 leaves the ogre with no way."""
        self.set_state(WORLD)
        self.assert_no_plan("clearLocation(corridor).")

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_all_dead(self):
        """P1: every enemy that was at the location ends dead."""
        self.set_state(WORLD)
        self.assert_state_after("clearLocation(storage).", has=["hasTag(guard1,dead)", "hasTag(imp,dead)"])


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
