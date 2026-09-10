"""Tests for core_aggro."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite


WORLD = [
    "region(entry)", "region(corridor)", "region(gallery)",
    "connected(entry, corridor)", "connected(corridor, entry)",
    "connected(corridor, gallery)", "connected(gallery, corridor)",
    "lineOfSight(entry, corridor)", "lineOfSight(entry, gallery)",
    "role(player, player)", "role(warden, companion)", "role(gob, enemy)",
    "at(player, entry)", "at(warden, entry)", "at(gob, gallery)",
    "skillElement(magnetize, pull)", "skillElement(gust, push)", "skillElement(dash, dash)",
    "hasSkill(warden, magnetize)", "signature(warden, magnetize)",
    "terrain(sludge, snared)",
]


class CoreAggroTest(HtnTestSuite):

    def setup(self):
        self.load_component("core/primitives/core_aggro", reset_first=True)
        self.verify_contracts()
        self.set_state(WORLD)

    # ---------------------------------------------------------------- examples

    def test_example_1_lure(self):
        self.set_state(["metal(gob)"])
        self.assert_plan("lure(gob, corridor).",
                         contains=["opLure(warden, gob, gallery, corridor)"],
                         not_contains=["opNavigate"])
        self.assert_state_after("lure(gob, corridor).",
                                has=["at(gob,corridor)", "at(warden,entry)"])

    def test_example_2_push(self):
        self.set_state(["hasSkill(player, gust)", "unlimited(gust)"])
        self.assert_plan("push(gob, corridor).",
                         contains=["opPush(player, gob, gallery, corridor)"])

    def test_example_3_taunt(self):
        self.set_state(["hasSkill(player, dash)", "unlimited(dash)"])
        self.assert_plan("taunt(gob, corridor).",
                         contains=["opTaunt(player, gob, gallery, corridor)"])
        self.assert_state_after("taunt(gob, corridor).",
                                has=["at(gob,corridor)", "at(player,corridor)"])

    def test_example_4_hold_position(self):
        self.assert_plan("holdPosition(warden, corridor).",
                         contains=["opNavigate(warden, entry, corridor)", "opAnchor(warden)"])

    # -------------------------------------------------------------- properties

    def test_property_p1_anchored_pullers_are_released_first(self):
        self.set_state(["metal(gob)", "status(warden, anchored)"])
        self.assert_plan("lure(gob, corridor).",
                         contains=["opRelease(warden)", "opLure(warden, gob, gallery, corridor)"])

    def test_property_p2_magnetize_only_moves_iron(self):
        self.assert_no_plan("lure(gob, corridor).")
        self.set_state(["metal(gob)", "hasSkill(player, gust)", "unlimited(gust)"])
        self.assert_no_plan("push(gob, corridor).")

    def test_property_p3_arrivals_suffer_the_terrain(self):
        self.set_state(["regionHas(corridor, sludge)",
                        "hasSkill(player, dash)", "unlimited(dash)"])
        self.assert_state_after("taunt(gob, corridor).",
                                has=["status(gob,snared)", "status(player,snared)"])


def run_tests():
    suite = CoreAggroTest()
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
