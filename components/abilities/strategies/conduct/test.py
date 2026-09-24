"""Tests for conduct."""

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
    "reaction(wet, electrocuted, electrocution)",
    "effect(electrocution, target, remove(wet))", "effect(electrocution, target, grant(dead))",
    "reaction(wet, chilled, freezeOver)",
    "effect(freezeOver, target, remove(wet))", "effect(freezeOver, target, grant(frozen))",
    "reaction(wet, burning, steam)", "effect(steam, target, remove(wet))",
    "reaction(oiled, burning, blaze)",
    "effect(blaze, target, remove(oiled))", "effect(blaze, target, grant(dead))",
    "reaction(brittle, blunt, shatterBlow)",
    "effect(shatterBlow, target, remove(frozen))", "effect(shatterBlow, target, grant(dead))",
    "reach(shock, ranged)", "effect(shock, target, grant(electrocuted))",
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


class ConductTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/strategies/conduct", reset_first=True)
        self.verify_contracts()
        self.set_state(WORLD)

    # ---------------------------------------------------------------- examples

    def test_example_1_already_wet_takes_one_shock(self):
        self.set_state(["knows(player, shock)", "knows(mage, douse)"])
        self.assert_plan("conduct(wader).",
                         contains=["opCast(player, shock, wader)",
                                   "opReact(player, wader, wet, electrocuted, electrocution)"],
                         not_contains=["douse"])

    def test_example_2_one_soaks_another_shocks(self):
        self.set_state(["knows(mage, douse)", "knows(player, shock)"])
        self.assert_plan("conduct(gob).", contains=[
            "opCast(mage, douse, gob)", "opCast(player, shock, gob)",
            "opGrant(player, gob, dead)"])

    def test_example_3_a_push_into_the_pool_soaks(self):
        self.set_state(["knows(mage, gust)", "knows(player, shock)"])
        self.assert_plan("conduct(tender).", contains=[
            "opForcedMove(mage, tender, slick, pool)", "opCast(player, shock, tender)"])

    # -------------------------------------------------------------- properties

    def test_property_p1_the_primer_never_pays_off(self):
        self.set_state(["knows(player, douse)", "knows(player, shock)"])
        self.assert_no_plan("conduct(gob).")

    def test_property_p2_immune_to_shock_no_conduct(self):
        self.set_state(["knows(mage, douse)", "knows(player, shock)", "immune(gob, electrocuted)"])
        self.assert_no_plan("conduct(gob).")

    def test_property_p3_the_world_confirms_the_recipe(self):
        """Electrocution fires but the target cannot die: the recipe fails."""
        self.set_state(["knows(mage, douse)", "knows(player, shock)", "immune(gob, dead)"])
        self.assert_no_plan("conduct(gob).")


def run_tests():
    suite = ConductTest()
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
