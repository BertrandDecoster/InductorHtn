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
    "hazard(sludge, snared)",
]


class CoreAggroTest(HtnTestSuite):

    def setup(self):
        self.load_component("core/primitives/core_aggro", reset_first=True)
        self.verify_contracts()
        self.set_state(WORLD)

    # ---------------------------------------------------------------- examples

    def test_example_1_lure(self):
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
        self.set_state(["status(warden, anchored)"])
        self.assert_plan("lure(gob, corridor).",
                         contains=["opRelease(warden)", "opLure(warden, gob, gallery, corridor)"])

    def test_property_p2_immunity_stops_a_movement(self):
        self.set_state(["immune(gob, pull)"])
        self.assert_no_plan("lure(gob, corridor).")
        self.setup()
        self.set_state(["immune(gob, push)", "hasSkill(player, gust)", "unlimited(gust)"])
        self.assert_no_plan("push(gob, corridor).")

    def test_property_p3_arrivals_suffer_the_terrain(self):
        self.set_state(["regionHas(corridor, sludge)",
                        "hasSkill(player, dash)", "unlimited(dash)"])
        self.assert_state_after("taunt(gob, corridor).",
                                has=["status(gob,snared)", "status(player,snared)"])

    def test_property_p4_a_pull_is_paid_for(self):
        # The warden is held; the mage has one hook charge: one pull, then none.
        self.set_state(["status(warden, anchored)", "status(warden, snared)",
                        "role(mage, companion)", "at(mage, entry)",
                        "hasSkill(mage, hook)", "skillElement(hook, pull)", "charge(mage, hook, h1)"])
        self.assert_plan("lure(gob, corridor).",
                         contains=["opSpendCharge(mage, hook, h1)",
                                   "opLure(mage, gob, gallery, corridor)"])
        self.compile_additional("twoPulls :- if(), do(lure(gob, corridor), lure(gob, entry)).")
        self.assert_no_plan("twoPulls.")

    def test_property_p5_a_pull_brings_it_toward_the_puller(self):
        # entry - corridor - gallery. Pulling an imp from the corridor into
        # the gallery needs the puller in the gallery: it walks through.
        self.set_state(["role(imp, enemy)", "at(imp, corridor)", "lineOfSight(gallery, corridor)"])
        self.assert_plan("lure(imp, gallery).", contains=[
            "opNavigate(warden, corridor, gallery)", "opLure(warden, imp, corridor, gallery)"])

    def test_property_p6_a_push_sends_it_away_from_the_pusher(self):
        # Nobody stands beyond the gallery, so a push from the gallery into
        # the corridor is cast from the gallery itself.
        self.set_state(["hasSkill(player, gust)", "unlimited(gust)"])
        self.assert_plan("push(gob, corridor).", contains=[
            "opNavigate(player, corridor, gallery)", "opPush(player, gob, gallery, corridor)"])


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
