"""Tests for defeat_group."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite


WORLD = [
    "region(entry)", "region(corridor)", "region(gallery)",
    "connected(entry, corridor)", "connected(corridor, entry)",
    "connected(corridor, gallery)", "connected(gallery, corridor)",
    "lineOfSight(entry, corridor)", "lineOfSight(gallery, corridor)",
    "role(player, player)", "role(warden, companion)", "role(arcanist, companion)",
    "role(swarm, enemy)",
    "at(player, entry)", "at(warden, entry)", "at(arcanist, entry)", "at(swarm, gallery)",
    "regionHas(corridor, oil)",
    "skillElement(magnetize, pull)", "skillElement(freeze, freeze)", "skillElement(ignite, fire)",
    "skillElement(gust, push)", "skillElement(lightning, lightning)",
    "reacts(fire, oil, scorched)", "reacts(freeze, oil, sludge)", "blast(fire, oil, dead)",
    "terrain(sludge, snared)", "strike(fire, dead)", "strike(lightning, dead)",
    "hasSkill(warden, magnetize)", "signature(warden, magnetize)", "signature(warden, shield)",
    "hasSkill(arcanist, freeze)", "signature(arcanist, freeze)",
    "hasSkill(player, ignite)", "charge(player, ignite, i1)",
    "hasSkill(player, gust)", "unlimited(gust)",
    "hasSkill(player, lightning)", "charge(player, lightning, l1)",
]


class DefeatGroupTest(HtnTestSuite):

    def setup(self):
        self.load_component("core/goals/defeat_group", reset_first=True)
        self.verify_contracts()
        self.set_state(WORLD)

    def test_example_1_two_ways(self):
        self.assert_plan("defeatGroup(swarm).", min_solutions=2,
                         contains=["opCastRegion(player, ignite, corridor, oil, scorched)"])
        self.assert_plan("defeatGroup(swarm).",
                         contains=["opCastEntity(player, "])

    def test_property_p1_dead_enemies_need_nothing(self):
        self.set_state(["status(swarm, dead)"])
        self.assert_plan("defeatGroup(swarm).", not_contains=["op"])


def run_tests():
    suite = DefeatGroupTest()
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
