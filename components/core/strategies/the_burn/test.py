"""Tests for the_burn."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite


WORLD = [
    "region(entry)", "region(corridor)", "region(gallery)",
    "connected(entry, corridor)", "connected(corridor, entry)",
    "connected(corridor, gallery)", "connected(gallery, corridor)",
    "lineOfSight(entry, corridor)", "lineOfSight(entry, gallery)",
    "role(player, player)", "role(warden, companion)", "role(swarm, enemy)",
    "at(player, entry)", "at(warden, entry)", "at(swarm, gallery)",
    "regionHas(corridor, oil)",
    "skillElement(magnetize, pull)", "skillElement(ignite, fire)",
    "reacts(fire, oil, scorched)", "blast(fire, oil, dead)",
    "hasSkill(warden, magnetize)", "signature(warden, magnetize)",
    "hasSkill(player, ignite)", "charge(player, ignite, i1)",
    "metal(swarm)",
]


class TheBurnTest(HtnTestSuite):

    def setup(self):
        self.load_component("core/strategies/the_burn", reset_first=True)
        self.verify_contracts()
        self.set_state(WORLD)

    def test_example_1_swarm_in_the_corridor(self):
        self.assert_plan("theBurn(swarm).", contains=[
            "opLure(warden, swarm, gallery, corridor)",
            "opCastRegion(player, ignite, corridor, oil, scorched)",
            "opStatus(player, swarm, dead)",
        ])
        self.assert_state_after("theBurn(swarm).",
                                has=["regionHas(corridor,scorched)", "status(swarm,dead)"])

    def test_property_p1_shields_turn_the_burn(self):
        self.set_state(["status(swarm, shielded)"])
        self.assert_no_plan("theBurn(swarm).")

    def test_property_p2_the_oil_is_consumed(self):
        self.run_goal("theBurn(swarm)")
        assert not any(f.startswith("regionHas(") and f.endswith(",oil)") for f in self.get_state()), (
            "oil should be gone after the burn"
        )
        self._record(True, "P2: the oil is consumed")


def run_tests():
    suite = TheBurnTest()
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
