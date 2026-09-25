"""Tests for the locomotion primitive component."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src/Python")))

from htn_test_framework import HtnTestSuite

WORLD = ["location(a)", "location(b)", "location(d)", "at(hero, a)"]


class LocomotionTest(HtnTestSuite):
    """Test suite for the locomotion primitive."""

    def setup(self):
        self.load_component("primitives/locomotion")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_one_step(self):
        """Example 1: one step, wherever the location is."""
        self.set_state(WORLD)
        self.assert_plan_set("goToLocation(hero, d).", ["opMoveTo(hero, a, d)"])
        self.assert_state_after("goToLocation(hero, d).", has=["at(hero,d)"], not_has=["at(hero,a)"])

    def test_example_2_already_there(self):
        """Example 2: already there."""
        self.set_state(WORLD)
        self.assert_plan_set("goToLocation(hero, a).", ["opStayInLocation(hero)"])

    def test_example_3_enemy_follows(self):
        """Example 3: an enemy after the agent follows it."""
        self.set_state(WORLD + ["at(orc, a)", "hasAggro(orc, hero)"])
        self.assert_plan_set("goToLocation(hero, d).", ["opMoveTo(hero, a, d), opAggroMoveTo(orc, a, d)"])

    def test_example_4_static_enemy_stays(self):
        """Example 4: a static enemy doesn't follow."""
        self.set_state(WORLD + ["at(orc, a)", "hasAggro(orc, hero)", "static(orc)"])
        self.assert_plan_set("goToLocation(hero, d).", ["opMoveTo(hero, a, d)"])

    def test_example_5_same_location(self):
        """Example 5: stand with another agent."""
        self.set_state(WORLD + ["at(orc, d)"])
        self.assert_plan_set("goToSameLocation(hero, orc).", ["opMoveTo(hero, a, d)"])

    def test_example_6_dead_enemy_stays(self):
        """Example 6: a dead enemy doesn't follow."""
        self.set_state(WORLD + ["at(orc, a)", "hasAggro(orc, hero)", "hasTag(orc, dead)"])
        self.assert_plan_set("goToLocation(hero, d).", ["opMoveTo(hero, a, d)"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_one_position(self):
        """P1: after a move the agent is at exactly one location."""
        self.set_state(WORLD)
        self.run_goal("goToLocation(hero, b)")
        positions = [f for f in self.get_state() if f.startswith("at(hero,")]
        assert positions == ["at(hero,b)"], f"P1 violated: {positions}"

    def test_property_p2_unknown_location(self):
        """P2: a destination that isn't a location has no plan."""
        self.set_state(WORLD)
        self.assert_no_plan("goToLocation(hero, nowhere).")


def run_tests():
    """Run all tests in this file."""
    suite = LocomotionTest()
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
