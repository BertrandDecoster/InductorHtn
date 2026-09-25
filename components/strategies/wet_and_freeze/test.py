"""Tests for the wet_and_freeze strategy component."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src/Python")))

from htn_test_framework import HtnTestSuite

WORLD = [
    "location(camp)", "location(hut)", "location(corridor)", "location(rink)",
    "locationCanApplyTag(corridor, wet)", "locationCanApplyTag(rink, ice)",
    "companion(pyro)", "companion(frost)", "at(pyro, camp)", "at(frost, camp)",
    "hasSkill(pyro, fireballSkill)", "skillAppliesTag(fireballSkill, burning)",
    "hasSkill(frost, frostSkill)", "skillAppliesTag(frostSkill, chilled)",
    "enemy(gob)", "at(gob, hut)", "vulnerableToLocationCombo(gob, wet, chilled)",
]


def lure_and_chill(l):
    return (f"opMoveTo(pyro, camp, hut), opAggro(gob, pyro), opMoveTo(pyro, hut, {l}), "
            f"opAggroMoveTo(gob, hut, {l}), opMoveTo(frost, camp, {l}), opUseSkill(frost, frostSkill, gob), "
            "opApplyTag(stunned, gob), opApplyTag(dead, gob)")


class WetAndFreezeTest(HtnTestSuite):
    """Test suite for the wet_and_freeze strategy."""

    def setup(self):
        self.load_component("strategies/wet_and_freeze")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_lure_into_water_then_chill(self):
        """Example 1: pyro lures gob into the water; frost chills it there: stunned, dead."""
        self.set_state(WORLD)
        self.assert_plan_set("wetAndFreeze(gob).", [lure_and_chill("corridor")])

    def test_example_2_water_or_ice(self):
        """Example 2: vulnerable in water and on ice: one plan per location."""
        self.set_state(WORLD + ["vulnerableToLocationCombo(gob, ice, chilled)"])
        self.assert_plan_set("wetAndFreeze(gob).", [lure_and_chill("corridor"), lure_and_chill("rink")])

    def test_example_3_not_vulnerable(self):
        """Example 3: stunned but not vulnerable: no plan (the strategy is to defeat)."""
        self.set_state([f for f in WORLD if not f.startswith("vulnerableTo")])
        self.assert_no_plan("wetAndFreeze(gob).")

    def test_example_4_one_companion_is_not_enough(self):
        """Example 4: a lone companion can't be both lurer and caster."""
        self.set_state([f for f in WORLD if "pyro" not in f])
        self.assert_no_plan("wetAndFreeze(gob).")

    def test_example_5_already_in_the_water(self):
        """Example 5: already standing in the water: the caster alone chills it."""
        self.set_state([f for f in WORLD if f != "at(gob, hut)"] + ["at(gob, corridor)"])
        self.assert_plan_set("wetAndFreeze(gob).", [
            "opMoveTo(frost, camp, corridor), opUseSkill(frost, frostSkill, gob), "
            "opApplyTag(stunned, gob), opApplyTag(dead, gob)"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_only_the_target(self):
        """P1: chilled stuns the target alone; the lurer standing there isn't stunned."""
        self.set_state(WORLD)
        self.assert_state_after("wetAndFreeze(gob).", has=["hasTag(gob,stunned)", "hasTag(gob,dead)"],
                                not_has=["hasTag(pyro,stunned)", "hasTag(frost,stunned)"])


def run_tests():
    """Run all tests in this file."""
    suite = WetAndFreezeTest()
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
