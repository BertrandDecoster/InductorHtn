"""Tests for complete_toy_level goal component."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite


class CompleteToyLevelTest(HtnTestSuite):
    """Test suite for the M0 toy-level goal."""

    def setup(self):
        self.load_component("gamehack/primitives/gh_movement", reset_first=True)
        self.load_component("gamehack/primitives/gh_tags", reset_first=False)
        self.load_component("gamehack/primitives/gh_aggro", reset_first=False)
        self.load_component("gamehack/primitives/gh_skills", reset_first=False)
        self.load_component("gamehack/primitives/gh_doors", reset_first=False)
        self.load_component("gamehack/actions/gh_tag_application", reset_first=False)
        self.load_component("gamehack/strategies/stun_and_slow_skill", reset_first=False)
        self.load_component("gamehack/strategies/wet_and_electrocute", reset_first=False)
        self.load_component("gamehack/goals/plan_to_damage", reset_first=False)
        self.load_component("gamehack/goals/complete_toy_level", reset_first=False)

    def _toy_world(self):
        """Initial facts for the M0 toy_two_step level.

        Two rooms, door1 locked, gob1 in room2.
        Two plates linked to door1. Puddle applies wet; conduit applies electrocute.
        Two allies available, no stun/slow skills -> forces wetAndElectrocute path.
        """
        self.set_state([
            "locked(door1)",
            "plateOpens(plate1, door1)",
            "plateOpens(plate2, door1)",
            "enemy(gob1)",
            "at(gob1, room2)",
            "at(companion1, room1)",
            "at(companion2, room1)",
            "at(plate1, room1)",
            "at(plate2, room1)",
            "at(puddle1, room1)",
            "at(conduit1, room1)",
            "ally(companion1)",
            "ally(companion2)",
            "locationCanApplyTag(puddle1, wet)",
            "locationCanApplyTag(conduit1, electrocute)",
        ])

    def test_example_1_full_sequence(self):
        """Locked door + enemy alive -> unlock then damage."""
        self._toy_world()

        self.assert_plan("completeToyLevel().",
            contains=[
                "opUnlock(door1)",
                "opApplyTag(wet",
                "opApplyTag(electrocute",
            ])

    def test_example_1b_both_ops_in_full_plan(self):
        """Sanity: full plan contains both the unlock op and a wet-tag op.

        TODO(M1): verify ordering explicitly (opUnlock must precede opApplyTag).
        HTN's `do()` sequence preserves order structurally, but `assert_plan`'s
        contains-list does not. The set-state reset quirk that blocked a manual
        plan-string inspection in M0 is deferred to a follow-up.
        """
        self._toy_world()

        self.assert_plan("completeToyLevel().",
            contains=["opUnlock(door1)", "opApplyTag(wet"])

    def test_example_2_door_already_unlocked(self):
        """Door unlocked -> skip unlock, still damage."""
        self.set_state([
            "plateOpens(plate1, door1)",
            "plateOpens(plate2, door1)",
            "enemy(gob1)",
            "at(gob1, room2)",
            "at(companion1, room1)",
            "at(companion2, room1)",
            "at(plate1, room1)",
            "at(plate2, room1)",
            "at(puddle1, room1)",
            "at(conduit1, room1)",
            "ally(companion1)",
            "ally(companion2)",
            "locationCanApplyTag(puddle1, wet)",
            "locationCanApplyTag(conduit1, electrocute)",
        ])

        self.assert_plan("completeToyLevel().",
            contains=["opApplyTag(wet", "opApplyTag(electrocute"],
            not_contains=["opUnlock"])

    def test_example_3_enemy_gone(self):
        """No enemy -> empty plan (level already complete)."""
        self.set_state([
            "locked(door1)",
            "plateOpens(plate1, door1)",
            "plateOpens(plate2, door1)",
            "ally(companion1)",
            "ally(companion2)",
        ])

        self.assert_plan("completeToyLevel().",
            not_contains=["opUnlock", "opApplyTag"])


def run_tests():
    suite = CompleteToyLevelTest()
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
