"""Tests for neutralize."""

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


class NeutralizeTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.verify_contracts()
        self.set_state(WORLD)

    # ---------------------------------------------------------------- examples

    def test_example_1_already_out(self):
        self.set_state(["tag(gob, fell)"])
        self.assert_plan_complexity("neutralize(gob).", min_operators=0, max_operators=0)

    def test_example_2_each_recipe_is_a_plan(self):
        self.set_state(["beyond(ledge, pool, pit)", "stops(wader, frozen)",
                        "knows(player, shock)", "knows(player, chill)", "knows(mage, gust)"])
        self.assert_plan("neutralize(wader).", min_solutions=3, contains=[
            "opReact(player, wader, wet, electrocuted, electrocution)",
            "opReact(player, wader, wet, chilled, freezeOver)",
            "opForcedMove(mage, wader, pool, pit)"])

    def test_example_3_improvise_on_a_mook(self):
        self.set_state(["vulnerable(gob, fire)", "reach(bolt, ranged)",
                        "effect(bolt, target, damage(fire))", "knows(player, bolt)"])
        self.assert_plan("neutralize(gob).", contains=["opCast(player, bolt, gob)",
                                                       "opGrant(player, gob, dead)"])

    # -------------------------------------------------------------- properties

    def test_property_p1_a_tag_that_stops_is_one_step(self):
        self.set_state(["stops(gob, stunned)", "reach(stun, ranged)",
                        "effect(stun, target, grant(stunned))", "knows(mage, stun)"])
        self.assert_plan("neutralize(gob).", contains=["opGrant(mage, gob, stunned)"])

    def test_property_p2_nothing_works_no_plan(self):
        self.set_state(["knows(player, douse)"])
        self.assert_no_plan("neutralize(golem).")

    def test_property_p3_a_guard_comes_off_first(self):
        """On the catalogue: a stealthed treant cannot be aimed at; a blinding
        flash next to it strips the stealth, then fire plays its weakness."""
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.set_state(["region(ledge)", "region(floor)", "lineOfSight(ledge, floor)",
                        "connected(ledge, floor)", "connected(floor, ledge)",
                        "role(player, player)", "role(mage, companion)",
                        "at(player, ledge)", "at(mage, ledge)", "mana(player, 2)",
                        "role(treant, enemy)", "at(treant, floor)", "tag(treant, stealthed)",
                        "trait(treant, wooden)",
                        "knows(mage, blindingFlash)", "knows(player, fireball)"])
        self.assert_plan("neutralize(treant).", contains=[
            "opCast(mage, blindingFlash, mage)", "opRemove(mage, treant, stealthed)",
            "opCast(player, fireball, treant)", "opExploit(player, treant, burning, dead)"])


def run_tests():
    suite = NeutralizeTest()
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
