"""Tests for the defeat goal component."""

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
]
GUARD1 = ["enemy(guard1)", "at(guard1, hut)", "vulnerableToLocationCombo(guard1, oil, burning)"]
GUARD2 = ["enemy(guard2)", "at(guard2, hut)", "vulnerableToLocationCombo(guard2, wet, chilled)"]
OGRE = ["enemy(ogre)", "at(ogre, hut)", "vulnerableToLocationCombo(ogre, oil, burning)",
        "vulnerableToLocationCombo(ogre, wet, chilled)"]


def oil_and_burn(e):
    return (f"opMoveTo(frost, camp, hut), opAggro({e}, frost), opMoveTo(frost, hut, storage), opApplyTag(oil, frost), "
            f"opAggroMoveTo({e}, hut, storage), opApplyTag(oil, {e}), opMoveTo(pyro, camp, storage), opApplyTag(oil, pyro), opUseSkill(pyro, fireballSkill, {e}), "
            "opRemoveLocationTag(oil, storage), opAddLocationTag(burning, storage), "
            f"opApplyTag(burning, pyro), opApplyTag(burning, frost), opApplyTag(burning, {e}), opApplyTag(dead, {e})")


def wet_and_freeze(e):
    return (f"opMoveTo(pyro, camp, hut), opAggro({e}, pyro), opMoveTo(pyro, hut, corridor), opApplyTag(wet, pyro), "
            f"opAggroMoveTo({e}, hut, corridor), opApplyTag(wet, {e}), opMoveTo(frost, camp, corridor), opApplyTag(wet, frost), opUseSkill(frost, frostSkill, {e}), "
            f"opApplyTag(stunned, {e}), opApplyTag(dead, {e})")


class DefeatTest(HtnTestSuite):
    """Test suite for the defeat goal."""

    def setup(self):
        self.load_component("goals/defeat")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_oil_and_burn(self):
        """Example 1: vulnerable to oil + burning."""
        self.set_state(WORLD + GUARD1)
        self.assert_plan_set("defeat(guard1).", [oil_and_burn("guard1")])

    def test_example_2_wet_and_freeze(self):
        """Example 2: vulnerable to wet + chilled."""
        self.set_state(WORLD + GUARD2)
        self.assert_plan_set("defeat(guard2).", [wet_and_freeze("guard2")])

    def test_example_3_menu(self):
        """Example 3: vulnerable to both: one plan per strategy."""
        self.set_state(WORLD + OGRE)
        self.assert_plan_set("defeat(ogre).", [wet_and_freeze("ogre"), oil_and_burn("ogre")])

    def test_example_4_already_dead(self):
        """Example 4: an enemy already dead needs no plan."""
        self.set_state(WORLD + GUARD1 + ["hasTag(guard1, dead)"])
        self.assert_no_plan("defeat(guard1).")

    def test_example_5_no_vulnerability(self):
        """Example 5: vulnerable to no combo, no plan."""
        self.set_state(WORLD + ["enemy(golem)", "at(golem, hut)"])
        self.assert_no_plan("defeat(golem).")

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_enemy_dead(self):
        """P1: every plan ends with the enemy dead."""
        for index in range(2):
            self.setup()
            self.set_state(WORLD + OGRE)
            self.run_goal("defeat(ogre)", solution_index=index)
            assert any("hasTag(ogre,dead)" in f for f in self.get_state()), f"P1 violated in plan {index}"


def run_tests():
    """Run all tests in this file."""
    suite = DefeatTest()
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
