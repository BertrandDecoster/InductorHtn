"""Tests for the_slipstream."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite


WORLD = [
    "region(entry)", "region(corridor)", "region(gallery)",
    "connected(entry, corridor)", "connected(corridor, entry)",
    "connected(corridor, gallery)", "connected(gallery, corridor)",
    "lineOfSight(entry, corridor)", "lineOfSight(entry, gallery)", "lineOfSight(gallery, corridor)",
    "role(player, player)", "role(warden, companion)", "role(arcanist, companion)",
    "role(swarm, enemy)",
    "at(player, entry)", "at(warden, entry)", "at(arcanist, entry)", "at(swarm, gallery)",
    "regionHas(corridor, oil)",
    "skillElement(magnetize, pull)", "skillElement(freeze, freeze)",
    "skillElement(gust, push)", "skillElement(lightning, lightning)",
    "reacts(freeze, oil, sludge)", "reacts(lightning, sludge, scorched)",
    "terrain(sludge, snared)", "strike(lightning, dead)", "blast(lightning, sludge, dead)",
    "hasSkill(warden, magnetize)", "signature(warden, magnetize)", "signature(warden, shield)",
    "hasSkill(arcanist, freeze)", "signature(arcanist, freeze)",
    "hasSkill(player, lightning)", "charge(player, lightning, l1)",
]


class TheSlipstreamTest(HtnTestSuite):

    def setup(self):
        self.load_component("core/strategies/the_slipstream", reset_first=True)
        self.verify_contracts()
        self.set_state(WORLD)

    def test_example_1_push_them_in(self):
        self.set_state(["hasSkill(player, gust)", "unlimited(gust)"])
        self.assert_plan("theSlipstream(swarm).", contains=[
            "opCastRegion(arcanist, freeze, corridor, oil, sludge)",
            "opAnchor(warden)",
            "opPush(player, swarm, gallery, corridor)",
            "opStatus(player, swarm, snared)",
            "opCastEntity(player, lightning, swarm, dead)",
        ])

    def test_example_2_drag_them_in(self):
        self.set_state(["metal(swarm)"])
        self.assert_plan("theSlipstream(swarm).", contains=[
            "opRelease(warden)",
            "opLure(warden, swarm, gallery, corridor)",
        ], not_contains=["opPush"])

    def test_example_3_blast_the_lot(self):
        self.set_state(["hasSkill(player, gust)", "unlimited(gust)"])
        self.assert_plan("theSlipstream(swarm).", contains=[
            "opCastRegion(player, lightning, corridor, sludge, scorched)",
            "opStatus(player, swarm, dead)",
        ])

    def test_property_p1_the_enemy_ends_dead(self):
        self.set_state(["hasSkill(player, gust)", "unlimited(gust)"])
        self.assert_state_after("theSlipstream(swarm).", has=["status(swarm,dead)"])

    def test_property_p2_nothing_moves_an_unreachable_enemy(self):
        self.assert_no_plan("theSlipstream(swarm).")


def run_tests():
    suite = TheSlipstreamTest()
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
