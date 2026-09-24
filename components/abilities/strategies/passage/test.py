"""Tests for passage, on the standard catalogue."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite


# a - b - gap - c - d(door) - e, with a plate p off b and a stone pillar at c.
WORLD = [
    "region(a)", "region(b)", "region(gap)", "region(c)", "region(d)", "region(e)", "region(p)",
    "connected(a, b)", "connected(b, a)", "connected(b, gap)", "connected(gap, b)",
    "connected(gap, c)", "connected(c, gap)", "connected(c, d)", "connected(d, c)",
    "connected(d, e)", "connected(e, d)", "connected(b, p)", "connected(p, b)",
    "lineOfSight(a, b)", "lineOfSight(b, c)", "lineOfSight(c, b)", "lineOfSight(b, p)",
    "lineOfSight(p, b)",
    "progress(a, 0)", "progress(b, 1)", "progress(p, 1)", "progress(gap, 2)", "progress(c, 3)",
    "progress(d, 4)", "progress(e, 5)",
    "beyond(a, b, gap)", "beyond(b, gap, c)", "beyond(c, gap, b)",
    "onEnter(gap, chasm)", "onEnter(p, press)", "effect(press, target, open(d))", "door(d)",
    "role(player, player)", "at(player, a)", "mana(player, 4)",
    "role(pillar, object)", "trait(pillar, heavy)", "at(pillar, c)",
]


class PassageTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/strategies/passage", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self.set_state(WORLD)

    # ---------------------------------------------------------------- examples

    def test_example_1_a_walk(self):
        self.assert_plan("reach(player, b).", contains=["opNavigate(player, a, b)"],
                         not_contains=["opCast"])

    def test_example_2_a_leap_over_the_gap(self):
        self.set_state(["knows(player, shadowStep)"])
        self.assert_plan("reach(player, e).", contains=["opCast(player, shadowStep, c)"])

    def test_example_3_a_hook_to_the_pillar(self):
        self.set_state(["knows(player, magnetize)"])
        self.assert_state_after("reach(player, c).", has=["at(player,c)"])
        self.assert_plan("reach(player, c).", contains=["opCast(player, magnetize, pillar)",
                                                         "opDash(player, b, c)"])

    def test_example_4_a_friend_swaps_you_over(self):
        self.set_state(["role(mage, companion)", "at(mage, c)", "knows(mage, translocate)",
                        "lineOfSight(c, a)"])
        self.assert_plan("reach(player, c).", contains=["opCast(mage, translocate, player)"])

    def test_example_5_the_door_latches(self):
        self.assert_state_after("openWay(d).", has=["open(d)", "at(player,p)"])

    def test_example_6_the_crate_bridges_the_gap(self):
        self.set_state(["role(crate, object)", "trait(crate, filler)", "at(crate, b)",
                        "knows(player, gust)"])
        self.assert_state_after("span(gap), reach(player, c).",
                                has=["tag(crate,fell)", "at(player,c)"])

    # -------------------------------------------------------------- properties

    def test_property_p1_leaps_only_go_forward(self):
        """A scout across the gap may leap forward, never back."""
        self.set_state(["role(scout, companion)", "at(scout, c)", "knows(scout, shadowStep)"])
        self.assert_no_plan("reach(scout, a).")

    def test_property_p2_a_pull_across_bridges_too(self):
        self.set_state(["role(crate, object)", "trait(crate, filler)", "at(crate, c)",
                        "knows(player, magnetize)"])
        self.assert_plan("span(gap).", contains=["opForcedMove(player, crate, c, gap)"])

    def test_property_p3_nobody_crosses_a_live_gap_on_foot(self):
        self.assert_no_plan("reachWithin(player, c, 0).")


def run_tests():
    suite = PassageTest()
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
