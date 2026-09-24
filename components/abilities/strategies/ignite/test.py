"""Tests for ignite."""

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
    "reaction(brittle, blunt, shatterBlow)",
    "effect(shatterBlow, target, remove(frozen))", "effect(shatterBlow, target, grant(dead))",
    "reach(shock, ranged)", "effect(shock, target, grant(shocked))",
    "reach(douse, ranged)", "effect(douse, target, grant(wet))",
    "reach(chill, ranged)", "effect(chill, target, grant(chilled))",
    "reach(ignite, ranged)", "effect(ignite, target, grant(burning))",
    "reach(gust, ranged)", "effect(gust, target, push)",
    "reach(quake, melee)", "effect(quake, target, grant(offBalance))",
    "reach(hammer, melee)", "effect(hammer, target, damage(blunt))",
    "effect(hammer, self, grant(tired))", "blockedBy(hammer, caster, tired)",
    "role(player, player)", "role(mage, companion)", "role(warden, companion)",
    "at(player, ledge)", "at(mage, ledge)", "at(warden, ledge)",
    "role(gob, enemy)", "role(wader, enemy)", "role(tender, enemy)", "role(golem, enemy)",
    "at(gob, rim)", "at(wader, pool)", "at(tender, slick)", "at(golem, rim)",
    "tag(wader, wet)", "tag(tender, oiled)",
    "immune(golem, forcedMove)",
]


class IgniteTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/strategies/ignite", reset_first=True)
        self.verify_contracts()
        self.set_state(WORLD)

    # ---------------------------------------------------------------- examples

    def test_example_1_already_oiled_takes_one_spark(self):
        self.set_state(["knows(player, ignite)"])
        self.assert_plan("ignite(tender).", contains=[
            "opCast(player, ignite, tender)",
            "opReact(player, tender, oiled, burning, blaze)"])

    def test_example_2_walked_into_the_slick(self):
        """Oiled is primed by a push into the slick, by the mage."""
        self.set_state(["beyond(ledge, pool, slick)", "role(imp, enemy)", "at(imp, pool)",
                        "knows(mage, gust)", "knows(player, ignite)"])
        self.assert_plan("ignite(imp).", contains=[
            "opForcedMove(mage, imp, pool, slick)", "opCast(player, ignite, imp)",
            "opGrant(player, imp, dead)"])

    # -------------------------------------------------------------- properties

    def test_property_p1_steam_spoils_the_blaze(self):
        """Wet first, then oiled: burning meets wet first and makes steam."""
        self.set_state(["tag(gob, wet)", "tag(gob, oiled)", "knows(player, ignite)"])
        self.assert_no_plan("ignite(gob).")

    def test_property_p2_the_primer_never_pays_off(self):
        self.set_state(["beyond(ledge, pool, slick)", "role(imp, enemy)", "at(imp, pool)",
                        "knows(player, gust)", "knows(player, ignite)"])
        self.assert_no_plan("ignite(imp).")


def run_tests():
    suite = IgniteTest()
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
