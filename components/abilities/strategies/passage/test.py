"""Tests for passage, on the standard catalogue."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite


# a - b ~gap~ c =door d= e, with a plate in b and a stone pillar at c.
WORLD = [
    "region(a)", "region(b)", "region(c)", "region(e)",
    "connected(a, b)", "gap(b, c)", "doorway(c, e, d)",
    "lineOfSight(a, b)", "lineOfSight(b, c)", "lineOfSight(c, b)",
    "progress(a, 0)", "progress(b, 1)", "progress(c, 3)", "progress(e, 5)",
    "feature(b, plate1, press)", "plate(plate1)", "effect(press, target, open(d))",
    "role(player, player)", "at(player, a)", "mana(player, 4)",
    "role(pillar, object)", "tag(pillar, heavy)", "at(pillar, c)",
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
        self.set_state(["knows(player, blink)", "open(d)"])
        self.assert_plan("reach(player, e).", contains=["opCast(player, blink, c)",
                                                        "opNavigate(player, c, e)"])

    def test_example_3_a_hook_to_the_pillar(self):
        self.set_state(["knows(player, hook)"])
        self.assert_state_after("reach(player, c).", has=["at(player,c)"])
        self.assert_plan("reach(player, c).", contains=["opCast(player, hook, pillar)",
                                                         "opDash(player, b, c)"])

    def test_example_4_a_friend_swaps_you_over(self):
        self.set_state(["role(mage, companion)", "at(mage, c)", "knows(mage, swapper)",
                        "reach(swapper, ranged)", "effect(swapper, target, swap)",
                        "lineOfSight(c, a)"])
        self.assert_plan("reach(player, c).", contains=["opCast(mage, swapper, player)"])

    def test_example_5_the_door_latches(self):
        self.assert_state_after("openWay(d).", has=["open(d)", "at(player,b)", "on(player,plate1)"])

    def test_example_6_the_crate_bridges_the_gap(self):
        """Knocked into the gap by a fireball, the crate falls in and bridges it."""
        self.set_state(["role(crate, object)", "tag(crate, filler)", "at(crate, b)",
                        "knows(player, fireball)"])
        self.assert_plan("bridge(b, c).", contains=["opCast(player, fireball, crate)",
                                                     "opBridge(player, b, c)"])
        self.assert_state_after("bridge(b, c), reach(player, c).",
                                has=["tag(crate,fell)", "at(player,c)"])

    # -------------------------------------------------------------- properties

    def test_property_p1_leaps_only_go_forward(self):
        """A scout across the gap may leap forward, never back."""
        self.set_state(["role(scout, companion)", "at(scout, c)", "knows(scout, blink)"])
        self.assert_no_plan("reach(scout, a).")

    def test_property_p2_a_pull_across_bridges_too(self):
        self.set_state(["role(crate, object)", "tag(crate, filler)", "at(crate, c)",
                        "knows(player, hook)"])
        self.assert_plan("bridge(b, c).", contains=["opFall(player, crate, c, b)",
                                                     "opBridge(player, c, b)"])

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
