"""Tests for the_slipstream strategy component."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src/Python")))

from htn_test_framework import HtnTestSuite

MAP = ["location(camp)", "location(corridor)", "location(generator)", "location(vault)",
       "linked(camp, corridor)", "linked(corridor, camp)",
       "linked(corridor, generator)", "linked(generator, corridor)",
       "locationCanApplyTag(generator, electrified)", "locationCanApplyTag(vault, electrified)"]
CAST = ["companion(arcanist)", "at(arcanist, camp)",
        "hasSkill(arcanist, freezeSkill)", "skillAppliesTag(freezeSkill, frozen)",
        "enemy(guard)", "at(guard, corridor)"]
WEAK = ["vulnerableTo(guard, electrified)"]
WET = ["locationCanApplyTag(corridor, wet)"]


class TheSlipstreamTest(HtnTestSuite):
    """Test suite for the_slipstream strategy."""

    def setup(self):
        self.load_component("strategies/the_slipstream")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_freeze_slide_electrified(self):
        """Example 1: freeze the wet floor, the enemy slides into the generator."""
        self.set_state(MAP + CAST + WEAK + WET)
        self.assert_plan_set("theSlipstream(guard).", [
            "opUseSkill(arcanist, freezeSkill, corridor), opAddLocationTag(frozen, corridor), "
            "opRemoveLocationTag(wet, corridor), opRemoveLocationTag(frozen, corridor), opAddLocationTag(frozen, corridor), "
            "opApplyTag(frozen, guard), "
            "opForceMove(guard, corridor, generator), opApplyTag(electrified, guard)"])

    def test_example_2_dry_floor(self):
        """Example 2: a dry floor doesn't freeze."""
        self.set_state(MAP + CAST + WEAK)
        self.assert_no_plan("theSlipstream(guard).")

    def test_example_3_not_weak(self):
        """Example 3: not weak to the hazard."""
        self.set_state(MAP + CAST + WET)
        self.assert_no_plan("theSlipstream(guard).")

    def test_example_4_static_enemy(self):
        """Example 4: a static enemy doesn't slide."""
        self.set_state(MAP + CAST + WEAK + WET + ["static(guard)"])
        self.assert_no_plan("theSlipstream(guard).")

    def test_example_5_link_blocked(self):
        """Example 5: a wall between the corridor and the generator stops the slide."""
        self.set_state(MAP + CAST + WEAK + WET + ["blockedLink(corridor, generator, wall)"])
        self.assert_no_plan("theSlipstream(guard).")

    def test_example_6_hazard_not_adjacent(self):
        """Example 6: the vault is electrified too, but not next to the corridor: one plan only."""
        self.set_state(MAP + CAST + WEAK + WET)
        self.assert_state_after("theSlipstream(guard).", has=["at(guard,generator)"], not_has=["at(guard,vault)"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_enemy_in_hazard(self):
        """P1: the enemy ends in the hazard with its tag."""
        self.set_state(MAP + CAST + WEAK + WET)
        self.assert_state_after("theSlipstream(guard).",
            has=["at(guard,generator)", "hasTag(guard,electrified)", "locationCanApplyTag(corridor,frozen)"],
            not_has=["at(guard,corridor)"])


def run_tests():
    """Run all tests in this file."""
    suite = TheSlipstreamTest()
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
