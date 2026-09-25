"""Tests for the_burn strategy component."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src/Python")))

from htn_test_framework import HtnTestSuite

WORLD = ["location(camp)", "location(hut)", "location(storage)",
         "companion(pyro)", "hasSkill(pyro, igniteSkill)", "skillAppliesTag(igniteSkill, burning)",
         "enemy(gob)", "vulnerableTo(gob, burning)", "at(pyro, camp)"]
WARDEN = ["companion(warden)", "at(warden, camp)"]
OIL = ["locationCanApplyTag(storage, oily)"]
STORAGE_BURNS = ("opUseSkill(pyro, igniteSkill, storage), opAddLocationTag(burning, storage), "
                 "opRemoveLocationTag(oily, storage), opRemoveLocationTag(burning, storage), opAddLocationTag(burning, storage), ")


class TheBurnTest(HtnTestSuite):
    """Test suite for the_burn strategy."""

    def setup(self):
        self.load_component("strategies/the_burn")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_lure_then_ignite(self):
        """Example 1: a second companion lures the enemy onto the oil, then it is ignited from afar.
        The lurer stands on the oil with the enemy, so it burns too."""
        self.set_state(WORLD + WARDEN + OIL + ["at(gob, hut)"])
        self.assert_plan_set("theBurn(gob).", [
            "opMoveTo(warden, camp, hut), opAggro(gob, warden), opMoveTo(warden, hut, storage), "
            "opAggroMoveTo(gob, hut, storage), " + STORAGE_BURNS + "opApplyTag(burning, warden), opApplyTag(burning, gob)"])

    def test_example_2_already_on_the_oil(self):
        """Example 2: the enemy already stands on the oil; nobody moves."""
        self.set_state(WORLD + WARDEN + OIL + ["at(gob, storage)"])
        self.assert_plan_set("theBurn(gob).", [STORAGE_BURNS + "opApplyTag(burning, gob)"])

    def test_example_3_no_oil(self):
        """Example 3: no oil, no plan."""
        self.set_state(WORLD + WARDEN + ["at(gob, hut)"])
        self.assert_no_plan("theBurn(gob).")

    def test_example_4_not_weak_to_burning(self):
        """Example 4: an enemy not weak to burning isn't burned to death."""
        self.set_state([f for f in WORLD if not f.startswith("vulnerableTo")] + WARDEN + OIL + ["at(gob, hut)"])
        self.assert_no_plan("theBurn(gob).")

    def test_example_5_immune(self):
        """Example 5: an enemy immune to burning."""
        self.set_state(WORLD + WARDEN + OIL + ["at(gob, hut)", "immune(gob, burning)"])
        self.assert_no_plan("theBurn(gob).")

    def test_example_6_nobody_to_lure(self):
        """Example 6: the igniter alone doesn't lure."""
        self.set_state(WORLD + OIL + ["at(gob, hut)"])
        self.assert_no_plan("theBurn(gob).")

    def test_example_7_frozen_enemy(self):
        """Example 7: a frozen enemy would melt to wet, not burn."""
        self.set_state(WORLD + WARDEN + OIL + ["at(gob, hut)", "hasTag(gob, frozen)"])
        self.assert_no_plan("theBurn(gob).")

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_enemy_burns_on_burning_location(self):
        """P1: the enemy ends burning, on a burning location."""
        self.set_state(WORLD + WARDEN + OIL + ["at(gob, hut)"])
        self.assert_state_after("theBurn(gob).",
            has=["hasTag(gob,burning)", "at(gob,storage)", "locationCanApplyTag(storage,burning)",
                 "at(pyro,camp)"],
            not_has=["locationCanApplyTag(storage,oily)"])


def run_tests():
    """Run all tests in this file."""
    suite = TheBurnTest()
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
