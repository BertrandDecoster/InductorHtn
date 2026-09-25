"""Tests for the defeat goal component."""

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
]
GUARD1 = ["enemy(guard1)", "at(guard1, storage)", "vulnerableTo(guard1, burning)"]
GUARD2 = ["enemy(guard2)", "at(guard2, corridor)", "vulnerableTo(guard2, electrified)"]
OGRE = ["enemy(ogre)", "at(ogre, corridor)", "vulnerableTo(ogre, burning)", "vulnerableTo(ogre, electrified)"]

STORAGE_BURNS = ("opUseSkill(pyro, igniteSkill, storage), opAddLocationTag(burning, storage), "
                 "opRemoveLocationTag(oily, storage), opRemoveLocationTag(burning, storage), opAddLocationTag(burning, storage), ")
CORRIDOR_FREEZES = ("opUseSkill(arcanist, freezeSkill, corridor), opAddLocationTag(frozen, corridor), "
                    "opRemoveLocationTag(wet, corridor), opRemoveLocationTag(frozen, corridor), opAddLocationTag(frozen, corridor), ")


def lure(lurer):
    return (f"opMoveTo({lurer}, camp, corridor), opAggro(ogre, {lurer}), "
            f"opMoveTo({lurer}, corridor, storage), opAggroMoveTo(ogre, corridor, storage), ")


class DefeatTest(HtnTestSuite):
    """Test suite for the defeat goal."""

    def setup(self):
        self.load_component("goals/defeat")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_burn_on_oil(self):
        """Example 1: weak to burning, standing on oil: ignited from the camp."""
        self.set_state(WORLD + GUARD1)
        self.assert_plan_set("defeat(guard1).", [
            STORAGE_BURNS + "opApplyTag(burning, guard1), opApplyTag(dead, guard1)"])

    def test_example_2_slipstream(self):
        """Example 2: weak to electrified, on a wet floor next to the generator."""
        self.set_state(WORLD + GUARD2)
        self.assert_plan_set("defeat(guard2).", [
            CORRIDOR_FREEZES + "opApplyTag(frozen, guard2), "
            "opForceMove(guard2, corridor, generator), opApplyTag(electrified, guard2), opApplyTag(dead, guard2)"])

    def test_example_3_menu(self):
        """Example 3: weak to both, one plan per strategy (and per lurer). The lurer burns with the ogre."""
        self.set_state(WORLD + OGRE)
        self.assert_plan_set("defeat(ogre).", [
            lure("arcanist") + STORAGE_BURNS + "opApplyTag(burning, arcanist), opApplyTag(burning, ogre), opApplyTag(dead, ogre)",
            lure("warden") + STORAGE_BURNS + "opApplyTag(burning, warden), opApplyTag(burning, ogre), opApplyTag(dead, ogre)",
            CORRIDOR_FREEZES + "opApplyTag(frozen, ogre), "
            "opForceMove(ogre, corridor, generator), opApplyTag(electrified, ogre), opApplyTag(dead, ogre)",
        ])

    def test_example_4_already_dead(self):
        """Example 4: an enemy already dead needs no plan."""
        self.set_state(WORLD + GUARD1 + ["hasTag(guard1, dead)"])
        self.assert_no_plan("defeat(guard1).")

    def test_example_5_no_weakness(self):
        """Example 5: no weakness, no plan."""
        self.set_state(WORLD + ["enemy(golem)", "at(golem, storage)"])
        self.assert_no_plan("defeat(golem).")

    def test_example_6_already_holds_its_weakness(self):
        """Example 6: an area effect already put a tag it is weak to on it."""
        self.set_state(WORLD + GUARD1 + ["hasTag(guard1, burning)"])
        self.assert_plan_set("defeat(guard1).", ["opApplyTag(dead, guard1)"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_enemy_dead(self):
        """P1: every plan ends with the enemy dead."""
        self.set_state(WORLD + OGRE)
        for index in range(3):
            self.run_goal("defeat(ogre)", solution_index=index)
            assert any("hasTag(ogre,dead)" in f for f in self.get_state()), f"P1 violated in plan {index}"
            self.setup()
            self.set_state(WORLD + OGRE)


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
