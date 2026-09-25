"""Tests for gh_doors primitive component."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite

PLATES = ["plateOpens(plate1, door1)", "plateOpens(plate2, door1)"]
COMPANIONS = ["companion(companion1)", "companion(companion2)"]


class GhDoorsTest(HtnTestSuite):
    """Test suite for gh_doors primitive."""

    def setup(self):
        self.load_component("gamehack/primitives/gh_doors")

    def test_example_1_basic_unlock(self):
        """Locked door, two plates, two companions -> synchronize on the plates, then unlock.
        Each companion can take either plate: four plans."""
        self.set_state(["locked(door1)"] + PLATES + COMPANIONS)
        self.assert_plan_set("unlockDoor(door1).", [
            "opSynchronizeOnPlates(companion1, companion2, plate1, plate2), opUnlock(door1)",
            "opSynchronizeOnPlates(companion1, companion2, plate2, plate1), opUnlock(door1)",
            "opSynchronizeOnPlates(companion2, companion1, plate1, plate2), opUnlock(door1)",
            "opSynchronizeOnPlates(companion2, companion1, plate2, plate1), opUnlock(door1)",
        ])
        self.assert_state_after("unlockDoor(door1).", not_has=["locked(door1)"])

    def test_example_2_already_unlocked(self):
        """No `locked` fact -> the plan shows opDoorAlreadyUnlocked."""
        self.set_state(PLATES + COMPANIONS)
        self.assert_plan_set("unlockDoor(door1).", ["opDoorAlreadyUnlocked(door1)"])

    def test_example_3_no_companions_fails(self):
        """Locked door with plates but no companions -> planning fails."""
        self.set_state(["locked(door1)"] + PLATES)
        self.assert_no_plan("unlockDoor(door1).")

    def test_example_4_one_plate_fails(self):
        """Only one plate linked -> planning fails (two distinct plates are needed)."""
        self.set_state(["locked(door1)", "plateOpens(plate1, door1)"] + COMPANIONS)
        self.assert_no_plan("unlockDoor(door1).")

    def test_property_p2_distinct_plates_bound(self):
        """The plan binds both distinct plates."""
        self.set_state(["locked(door1)"] + PLATES + COMPANIONS)
        self.assert_plan("unlockDoor(door1).", contains=["plate1", "plate2"])


def run_tests():
    suite = GhDoorsTest()
    suite.setup()
    for method_name in sorted(dir(suite)):
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
