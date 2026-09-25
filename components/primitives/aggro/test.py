"""Tests for the aggro primitive component."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src/Python")))

from htn_test_framework import HtnTestSuite

WORLD = ["location(a)", "location(b)", "location(c)", "enemy(orc)", "enemy(tower)", "static(tower)",
         "at(hero, a)", "at(orc, b)", "at(tower, c)"]


class AggroTest(HtnTestSuite):
    """Test suite for the aggro primitive."""

    def setup(self):
        self.load_component("primitives/aggro")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_first_aggro(self):
        """Example 1: first aggro."""
        self.set_state(WORLD)
        self.assert_plan_set("getAggro(orc, hero).", ["opAggro(orc, hero)"])

    def test_example_2_already_aggroed(self):
        """Example 2: already after that target."""
        self.set_state(WORLD + ["hasAggro(orc, hero)"])
        self.assert_plan_set("getAggro(orc, hero).", ["opTargetAlreadyAggroed(orc, hero)"])

    def test_example_3_switch_target(self):
        """Example 3: switching target."""
        self.set_state(WORLD + ["hasAggro(orc, other)"])
        self.assert_plan_set("getAggro(orc, hero).", ["opRemoveAggro(orc, other), opAggro(orc, hero)"])

    def test_example_4_lure(self):
        """Example 4: lure an enemy to a location."""
        self.set_state(WORLD)
        self.assert_plan_set("bringEnemyTo(hero, orc, c).", [
            "opMoveTo(hero, a, b), opAggro(orc, hero), opMoveTo(hero, b, c), opAggroMoveTo(orc, b, c)"])

    def test_example_5_already_there_or_static(self):
        """Example 5: already there, or can't move."""
        self.set_state(WORLD)
        self.assert_plan_set("bringEnemyTo(hero, orc, b).", ["opEnemyAlreadyAtLocation(orc, b)"])
        self.assert_no_plan("bringEnemyTo(hero, tower, a).")

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_lured_enemy_arrives(self):
        """P1: the lured enemy ends at the destination, with the lurer."""
        self.set_state(WORLD)
        self.assert_state_after("bringEnemyTo(hero, orc, c).", has=["at(orc,c)", "at(hero,c)"],
                                not_has=["at(orc,b)"])

    def test_property_p2_one_target(self):
        """P2: one target at a time."""
        self.set_state(WORLD + ["hasAggro(orc, other)"])
        self.assert_state_after("getAggro(orc, hero).", has=["hasAggro(orc,hero)"],
                                not_has=["hasAggro(orc,other)"])


def run_tests():
    """Run all tests in this file."""
    suite = AggroTest()
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
