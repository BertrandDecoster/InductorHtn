"""Tests for shatter."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite


# A small arena: a ledge overlooking a pool, an oil slick, and a pit.
WORLD = [
    "region(ledge)", "region(rim)", "region(pool)", "region(slick)", "region(pit)",
    "connected(ledge, rim)", "connected(rim, ledge)",
    "connected(rim, pool)", "connected(pool, rim)",
    "connected(rim, slick)", "connected(slick, rim)",
    "lineOfSight(ledge, rim)", "lineOfSight(ledge, pool)", "lineOfSight(ledge, slick)",
    "beyond(ledge, rim, pit)", "beyond(rim, rim, pit)", "beyond(ledge, slick, pool)",
    "onEnter(pool, soak)", "effect(soak, target, grant(wet))",
    "onEnter(slick, slicked)", "effect(slicked, target, grant(oiled))",
    "onEnter(pit, fall)", "effect(fall, target, grant(fell))",
    "group(dead, gone)", "group(fell, gone)",
    "bundles(frozen, brittle)", "bundles(frozen, offBalance)",
    "suspends(offBalance, forcedMove)",
    "reaction(wet, shocked, electrocution)",
    "effect(electrocution, target, remove(wet))", "effect(electrocution, target, grant(dead))",
    "reaction(wet, chilled, freezeOver)",
    "effect(freezeOver, target, remove(wet))", "effect(freezeOver, target, grant(frozen))",
    "reaction(wet, burning, steam)", "effect(steam, target, remove(wet))",
    "reaction(oiled, burning, blaze)",
    "effect(blaze, target, remove(oiled))", "effect(blaze, target, grant(dead))",
    "weakness(gob, stunned, frozen, dead)",
    "reach(shock, ranged)", "effect(shock, target, grant(shocked))",
    "reach(douse, ranged)", "effect(douse, target, grant(wet))",
    "reach(chill, ranged)", "effect(chill, target, grant(chilled))",
    "reach(ignite, ranged)", "effect(ignite, target, grant(burning))",
    "reach(gust, ranged)", "effect(gust, target, push)",
    "reach(quake, melee)", "effect(quake, target, grant(offBalance))",
    "reach(hammer, melee)", "effect(hammer, target, grant(stunned))",
    "effect(hammer, self, grant(tired))", "blockedBy(hammer, caster, tired)",
    "role(player, player)", "role(mage, companion)", "role(warden, companion)",
    "at(player, ledge)", "at(mage, ledge)", "at(warden, ledge)",
    "role(gob, enemy)", "role(wader, enemy)", "role(tender, enemy)", "role(golem, enemy)",
    "at(gob, rim)", "at(wader, pool)", "at(tender, slick)", "at(golem, rim)",
    "tag(wader, wet)", "tag(tender, oiled)",
    "immune(golem, forcedMove)",
]


class ShatterTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/strategies/shatter", reset_first=True)
        self.verify_contracts()
        self.set_state(WORLD)

    # ---------------------------------------------------------------- examples

    def test_example_1_frozen_is_enough(self):
        self.set_state(["stops(wader, frozen)", "knows(player, chill)"])
        self.assert_plan("shatter(wader).",
                         contains=["opReact(player, wader, wet, chilled, freezeOver)"],
                         not_contains=["hammer"])
        self.assert_state_after("shatter(wader).", has=["tag(wader,frozen)"])

    def test_example_2_frozen_then_broken(self):
        self.set_state(["knows(mage, douse)", "knows(player, chill)", "knows(warden, hammer)"])
        self.assert_plan("shatter(gob).", contains=[
            "opCast(mage, douse, gob)", "opCast(player, chill, gob)",
            "opCast(warden, hammer, gob)",
            "opExploit(warden, gob, stunned, dead)"])

    # -------------------------------------------------------------- properties

    def test_property_p1_a_blow_that_cannot_land(self):
        self.set_state(["knows(mage, douse)", "knows(player, chill)", "knows(warden, hammer)",
                        "immune(gob, stunned)"])
        self.assert_no_plan("shatter(gob).")

    def test_property_p2_the_primer_neither_chills_nor_breaks(self):
        self.set_state(["knows(mage, douse)", "knows(mage, chill)", "knows(mage, hammer)"])
        self.assert_no_plan("shatter(gob).")


def run_tests():
    suite = ShatterTest()
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
