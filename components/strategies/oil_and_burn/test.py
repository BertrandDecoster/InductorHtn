"""Tests for the oil_and_burn strategy component."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src/Python")))

from htn_test_framework import HtnTestSuite

WORLD = [
    "location(camp)", "location(hut)", "location(storage)", "locationCanApplyTag(storage, oil)",
    "companion(pyro)", "companion(frost)", "at(pyro, camp)", "at(frost, camp)",
    "hasSkill(pyro, fireballSkill)", "skillAppliesTag(fireballSkill, burning)",
    "hasSkill(frost, frostSkill)", "skillAppliesTag(frostSkill, chilled)",
    "enemy(gob)", "at(gob, hut)", "vulnerableToLocationCombo(gob, oil, burning)",
]
BURN = ("opRemoveLocationTag(oil, storage), opAddLocationTag(burning, storage), "
        "opApplyTag(burning, pyro), opApplyTag(burning, frost), opApplyTag(burning, gob), ")


class OilAndBurnTest(HtnTestSuite):
    """Test suite for the oil_and_burn strategy."""

    def setup(self):
        self.load_component("strategies/oil_and_burn")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_lure_then_burn(self):
        """Example 1: frost lures gob onto the oil; pyro sets it burning there. Everyone there burns."""
        self.set_state(WORLD)
        self.assert_plan_set("oilAndBurn(gob).", [
            "opMoveTo(frost, camp, hut), opAggro(gob, frost), opMoveTo(frost, hut, storage), opApplyTag(oil, frost), "
            "opAggroMoveTo(gob, hut, storage), opApplyTag(oil, gob), "
            "opMoveTo(pyro, camp, storage), opApplyTag(oil, pyro), opUseSkill(pyro, fireballSkill, gob), "
            + BURN + "opApplyTag(dead, gob)"])

    def test_example_2_not_vulnerable(self):
        """Example 2: an enemy not vulnerable to oil + burning."""
        self.set_state([f for f in WORLD if not f.startswith("vulnerableTo")])
        self.assert_no_plan("oilAndBurn(gob).")

    def test_example_3_one_companion_is_not_enough(self):
        """Example 3: a lone companion can't be both lurer and caster."""
        self.set_state([f for f in WORLD if "frost" not in f])
        self.assert_no_plan("oilAndBurn(gob).")

    def test_example_4_no_oil(self):
        """Example 4: no oil, no plan."""
        self.set_state([f for f in WORLD if not f.startswith("locationCanApplyTag")])
        self.assert_no_plan("oilAndBurn(gob).")

    def test_example_5_everyone_on_the_oil(self):
        """Example 5: a second vulnerable enemy already on the oil is defeated too."""
        self.set_state(WORLD + ["enemy(imp)", "at(imp, storage)", "hasTag(imp, oil)",
                                "vulnerableToLocationCombo(imp, oil, burning)"])
        self.assert_state_after("oilAndBurn(gob).", has=["hasTag(gob,dead)", "hasTag(imp,dead)"])

    def test_example_6_already_has_oil(self):
        """Example 6: gob starts on the oil, so it has oil: the caster alone sets it burning."""
        self.set_state([f for f in WORLD if f != "at(gob, hut)"] + ["at(gob, storage)", "hasTag(gob, oil)"])
        self.assert_plan_set("oilAndBurn(gob).", [
            "opMoveTo(pyro, camp, storage), opApplyTag(oil, pyro), opUseSkill(pyro, fireballSkill, gob), "
            "opRemoveLocationTag(oil, storage), opAddLocationTag(burning, storage), "
            "opApplyTag(burning, pyro), opApplyTag(burning, gob), opApplyTag(dead, gob)"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_oil_becomes_burning(self):
        """P1: the enemy ends dead on a burning location; the oil is gone."""
        self.set_state(WORLD)
        self.assert_state_after("oilAndBurn(gob).",
            has=["hasTag(gob,dead)", "at(gob,storage)", "locationCanApplyTag(storage,burning)"],
            not_has=["locationCanApplyTag(storage,oil)"])


def run_tests():
    """Run all tests in this file."""
    suite = OilAndBurnTest()
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
