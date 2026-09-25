"""Tests for bring_and_push."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite


WORLD = [
    "region(yard)", "region(keep)", "region(brink)",
    "connected(yard, keep)", "connected(keep, yard)",
    "connected(keep, brink)", "connected(brink, keep)",
    "connected(yard, brink)", "connected(brink, yard)",
    "connected(brink, void)", "regionHas(void, abyss)", "hazard(abyss, fallen)",
    "lineOfSight(yard, keep)", "lineOfSight(yard, brink)", "lineOfSight(brink, keep)",
    "role(player, player)", "role(warden, companion)", "role(gob, enemy)",
    "at(player, yard)", "at(warden, yard)", "at(gob, keep)",
    "skillElement(gust, push)", "skillElement(magnetize, pull)", "skillElement(dash, dash)",
]


class BringAndPushTest(HtnTestSuite):

    def setup(self):
        self.load_component("core/strategies/bring_and_push", reset_first=True)
        self.verify_contracts()
        self.set_state(WORLD)

    # ---------------------------------------------------------------- examples

    def test_example_1_pushed_over(self):
        self.set_state(["hasSkill(player, gust)", "unlimited(gust)"])
        self.assert_plan("bringAndPush(gob, fallen).", contains=[
            "opPush(player, gob, keep, brink)",
            "opPush(player, gob, brink, void)",
        ])
        self.assert_state_after("bringAndPush(gob, fallen).", has=["status(gob,fallen)"])

    def test_example_2_pulled_to_the_edge_pushed_over(self):
        # One push between them: the pull brings it, the push sends it over.
        self.set_state(["hasSkill(warden, magnetize)", "signature(warden, magnetize)",
                        "hasSkill(player, gust)", "charge(player, gust, g1)"])
        self.assert_plan("bringAndPush(gob, fallen).", max_solutions=1, contains=[
            "opLure(warden, gob, keep, brink)",
            "opPush(player, gob, brink, void)",
        ])

    def test_example_3_taunted_there_pushed_over(self):
        self.set_state(["hasSkill(player, dash)", "unlimited(dash)",
                        "hasSkill(warden, gust)", "unlimited(gust)"])
        self.assert_plan("bringAndPush(gob, fallen).", contains=[
            "opTaunt(player, gob, keep, brink)",
            "opPush(warden, gob, brink, void)",
        ])

    # -------------------------------------------------------------- properties

    def test_property_p1_a_taunt_is_not_a_forced_movement(self):
        self.set_state(["hasSkill(player, dash)", "unlimited(dash)"])
        self.assert_no_plan("bringAndPush(gob, fallen).")

    def test_property_p2_nobody_walks_into_the_drop(self):
        self.set_state(["hasSkill(player, dash)", "unlimited(dash)",
                        "hasSkill(warden, gust)", "unlimited(gust)"])
        self.assert_plan("bringAndPush(gob, fallen).",
                         not_contains=["opNavigate(player, brink, void)",
                                       "opNavigate(warden, brink, void)"])
        self.assert_state_after("bringAndPush(gob, fallen).",
                                has=["at(gob,void)"], not_has=["at(player,void)", "at(warden,void)"])

    def test_property_p4_nothing_is_pulled_into_the_drop(self):
        # Nobody stands beyond the void, so a pull brings it to the edge and no further.
        self.set_state(["hasSkill(warden, magnetize)", "signature(warden, magnetize)"])
        self.assert_no_plan("bringAndPush(gob, fallen).")

    def test_property_p3_what_has_fallen_needs_nothing(self):
        self.set_state(["hasSkill(player, gust)", "unlimited(gust)", "status(gob, fallen)"])
        self.assert_no_plan("bringAndPush(gob, fallen).")


def run_tests():
    suite = BringAndPushTest()
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
    sys.exit(0 if run_tests() else 1)
