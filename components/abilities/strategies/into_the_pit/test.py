"""Tests for into_the_pit."""

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
    "immune(golem, forcedMove)", "suspends(frozen, forcedMove)",
]


class IntoThePitTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/strategies/into_the_pit", reset_first=True)
        self.verify_contracts()
        self.set_state(WORLD)

    # ---------------------------------------------------------------- examples

    def test_example_1_push_it_in(self):
        self.set_state(["knows(player, gust)"])
        self.assert_plan("intoThePit(gob).", contains=[
            "opForcedMove(player, gob, rim, pit)", "opGrant(player, gob, fell)"])

    def test_example_2_unbalance_then_push(self):
        self.set_state(["knows(player, quake)", "knows(mage, gust)"])
        self.assert_plan("intoThePit(golem).", contains=[
            "opCast(player, quake, golem)", "opForcedMove(mage, golem, rim, pit)"])

    def test_example_3_freeze_then_push(self):
        self.set_state(["knows(mage, douse)", "knows(player, chill)", "knows(player, gust)"])
        self.assert_plan("intoThePit(golem).", contains=[
            "opCast(mage, douse, golem)", "opCast(player, chill, golem)",
            "opForcedMove(player, golem, rim, pit)"])

    # -------------------------------------------------------------- properties

    def test_property_p1_the_golem_does_not_move_on_its_own(self):
        self.set_state(["knows(player, gust)"])
        self.assert_no_plan("intoThePit(golem).")

    def test_property_p2_the_unbalancer_does_not_push(self):
        self.set_state(["knows(player, quake)", "knows(player, gust)"])
        self.assert_no_plan("intoThePit(golem).")

    def test_property_p3_no_pit_no_recipe(self):
        """The wader stands in the pool; no line from anywhere lands it in the pit."""
        self.set_state(["knows(player, gust)"])
        self.assert_no_plan("intoThePit(wader).")


    def test_property_p4_a_flyer_is_brought_down_first(self):
        self.set_state(["tag(gob, flying)", "wards(flying, fell)",
                        "reach(net, ranged)", "effect(net, target, remove(flying))",
                        "knows(mage, net)", "knows(player, gust)"])
        self.assert_plan("intoThePit(gob).", contains=[
            "opCast(mage, net, gob)", "opForcedMove(player, gob, rim, pit)",
            "opGrant(player, gob, fell)"])


    def test_property_p5_armour_comes_off_first(self):
        self.set_state(["tag(gob, armored)", "wards(armored, forcedMove)",
                        "reach(sunder, melee)", "effect(sunder, target, remove(armored))",
                        "knows(warden, sunder)", "knows(player, gust)"])
        self.assert_plan("intoThePit(gob).", contains=[
            "opCast(warden, sunder, gob)", "opForcedMove(player, gob, rim, pit)"])

    def test_property_p6_dragged_across_the_pit(self):
        """A hook from the ledge on something beyond the pit drags it in."""
        self.set_state(["region(far)", "beyond(ledge, pit, far)", "role(imp, enemy)", "at(imp, far)",
                        "lineOfSight(ledge, far)", "reach(hookSkill, ranged)",
                        "effect(hookSkill, target, hook)", "knows(player, hookSkill)",
                        "onEnter(pit, drop)", "effect(drop, target, hazard(pitfall))",
                        "weakness(?e, pitfall, none, fell) :- role(?e, enemy)"])
        self.assert_plan("intoThePit(imp).", contains=[
            "opCast(player, hookSkill, imp)", "opForcedMove(player, imp, far, pit)"])

def run_tests():
    suite = IntoThePitTest()
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
