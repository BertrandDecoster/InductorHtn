"""Tests for core_world."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite


WORLD = [
    "region(a)", "region(b)", "region(c)",
    "connected(a, b)", "connected(b, a)", "connected(b, c)", "connected(c, b)",
    "lineOfSight(b, c)",
    "role(player, player)",
]


class CoreWorldTest(HtnTestSuite):

    def setup(self):
        self.load_component("core/primitives/core_world", reset_first=True)
        self.verify_contracts()
        self.set_state(WORLD)

    # ---------------------------------------------------------------- examples

    def test_example_1_one_hop(self):
        self.set_state(["at(player, a)"])
        self.assert_plan("navigate(player, b).", contains=["opNavigate(player, a, b)"])
        self.assert_state_after("navigate(player, b).", has=["at(player,b)"], not_has=["at(player,a)"])

    def test_example_2_two_hops(self):
        self.set_state(["at(player, a)"])
        self.assert_plan("navigate(player, c).",
                         contains=["opNavigate(player, a, b)", "opNavigate(player, b, c)"])

    def test_example_3_already_there(self):
        self.set_state(["at(player, a)"])
        self.assert_plan("navigate(player, a).", not_contains=["opNavigate"])

    def test_example_4_take_a_vantage(self):
        self.set_state(["at(player, a)"])
        self.assert_plan("takeVantage(player, c).", contains=["opNavigate(player, a, b)"])

    # -------------------------------------------------------------- properties

    def test_property_p1_anchored_agents_hold(self):
        self.set_state(["at(player, a)", "status(player, anchored)"])
        self.assert_no_plan("navigate(player, b).")

    def test_property_p2_snared_agents_are_stuck(self):
        self.set_state(["at(player, a)", "status(player, snared)"])
        self.assert_no_plan("navigate(player, b).")


def run_tests():
    suite = CoreWorldTest()
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
