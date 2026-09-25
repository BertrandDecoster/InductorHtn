"""Tests for the door challenge component."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src/Python")))

from htn_test_framework import HtnTestSuite

WORLD = ["location(hall)", "location(side)", "location(vault)", "companion(hero)", "at(hero, hall)",
         "linked(hall, side)", "linked(side, hall)", "linked(hall, vault)", "linked(vault, hall)",
         "blockedLink(hall, vault, door(door1))", "blockedLink(vault, hall, door(door1))",
         "locked(door1)", "plateOpens(plate1, door1)", "at(plate1, side)"]


class DoorTest(HtnTestSuite):
    """Test suite for the door challenge."""

    def setup(self):
        self.load_component("challenges/door")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_one_companion_one_plate(self):
        """Example 1: one companion, one plate."""
        self.set_state(WORLD)
        self.assert_plan_set("unlockDoor(door1).", ["opMoveTo(hero, hall, side), opUnlock(door1)"])

    def test_example_2_already_unlocked(self):
        """Example 2: already unlocked."""
        self.set_state([f for f in WORLD if f != "locked(door1)"])
        self.assert_plan_set("unlockDoor(door1).", ["opDoorAlreadyUnlocked(door1)"])

    def test_example_3_any_companion(self):
        """Example 3: any companion can stand on the plate."""
        self.set_state(WORLD + ["companion(scout)", "at(scout, side)"])
        self.assert_plan_set("unlockDoor(door1).", [
            "opMoveTo(hero, hall, side), opUnlock(door1)",
            "opStayInLocation(scout), opUnlock(door1)"])

    def test_example_4_two_plate_door(self):
        """Example 4: a two-plate door isn't opened by one companion."""
        self.set_state(WORLD + ["plateOpens(plate2, door1)", "at(plate2, hall)"])
        self.assert_no_plan("unlockDoor(door1).")

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_door_unlocked(self):
        """P1: after unlocking, the door is not locked."""
        self.set_state(WORLD)
        self.assert_state_after("unlockDoor(door1).", not_has=["locked(door1)"])


def run_tests():
    """Run all tests in this file."""
    suite = DoorTest()
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
