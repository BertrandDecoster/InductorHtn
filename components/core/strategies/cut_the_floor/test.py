"""Tests for cut_the_floor."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite


WORLD = [
    "region(yard)", "region(keep)", "region(bridge)", "region(tower)",
    "connected(yard, keep)", "connected(keep, yard)",
    "connected(keep, bridge)", "connected(bridge, keep)",
    "connected(bridge, tower)", "connected(tower, bridge)",
    "lineOfSight(yard, keep)", "lineOfSight(keep, bridge)", "lineOfSight(keep, tower)",
    "regionHas(bridge, rope)", "reacts(fire, rope, abyss)", "hazard(abyss, fallen)",
    "role(player, player)", "role(warden, companion)",
    "role(gob, enemy)", "role(bot, enemy)", "immune(bot, push)",
    "at(player, yard)", "at(warden, yard)", "at(gob, keep)", "at(bot, tower)",
    "skillElement(gust, push)", "skillElement(magnetize, pull)",
    "skillElement(dash, dash)", "skillElement(ignite, fire)",
]

FIRE = ["hasSkill(player, ignite)", "charge(player, ignite, i1)"]


class CutTheFloorTest(HtnTestSuite):

    def setup(self):
        self.load_component("core/strategies/cut_the_floor", reset_first=True)
        self.verify_contracts()
        self.set_state(WORLD)

    # ---------------------------------------------------------------- examples

    def test_example_1_one_burn_takes_both(self):
        self.set_state(FIRE + ["hasSkill(player, gust)", "unlimited(gust)",
                               "hasSkill(warden, magnetize)", "signature(warden, magnetize)"])
        self.assert_plan("cutTheFloor(gob, fallen).", contains=[
            "opPush(player, gob, keep, bridge)",
            "opLure(warden, bot, tower, bridge)",
            "opCastRegion(player, ignite, bridge, rope, abyss)",
        ])
        self.assert_state_after("cutTheFloor(gob, fallen).", has=[
            "status(gob,fallen)", "status(bot,fallen)", "regionHas(bridge,abyss)",
        ])

    def test_example_2_the_taunter_steps_off_first(self):
        self.set_state(FIRE + ["hasSkill(player, dash)", "unlimited(dash)"])
        self.assert_plan("cutTheFloor(gob, fallen).", contains=[
            "opTaunt(player, gob, keep, bridge)",
            "opNavigate(player, bridge, keep)",
        ])
        self.assert_state_after("cutTheFloor(gob, fallen).",
                                has=["status(gob,fallen)"], not_has=["status(player,fallen)"])

    # -------------------------------------------------------------- properties

    def test_property_p1_no_element_no_cut(self):
        self.set_state(["hasSkill(player, gust)", "unlimited(gust)",
                        "hasSkill(warden, magnetize)", "signature(warden, magnetize)"])
        self.assert_no_plan("cutTheFloor(gob, fallen).")

    def test_property_p2_the_ground_is_spent(self):
        self.set_state(FIRE + ["hasSkill(player, gust)", "unlimited(gust)"])
        self.run_goal("cutTheFloor(gob, fallen)")
        assert not any(f.endswith(",rope)") for f in self.get_state()), "the rope should be gone"
        self._record(True, "P2: the ground is spent")

    def test_property_p3_whoever_cannot_be_brought_is_left(self):
        self.set_state(FIRE + ["hasSkill(player, gust)", "unlimited(gust)"])
        self.assert_state_after("cutTheFloor(gob, fallen).",
                                has=["status(gob,fallen)", "at(bot,tower)"],
                                not_has=["status(bot,fallen)"])


def run_tests():
    suite = CutTheFloorTest()
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
