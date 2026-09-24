"""Tests for ab_acts."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite


WORLD = [
    "region(ledge)", "region(pool)", "region(slick)",
    "connected(ledge, pool)", "connected(pool, ledge)",
    "connected(ledge, slick)", "connected(slick, ledge)",
    "lineOfSight(ledge, pool)", "lineOfSight(ledge, slick)",
    "connected(slick, pool)", "feature(pool, pit, fall)", "feature(slick, pond, soak)",
    "role(player, player)", "role(mage, companion)",
    "role(gob, enemy)", "role(tender, enemy)", "role(golem, enemy)",
    "at(player, ledge)", "at(mage, ledge)",
    "at(gob, pool)", "at(tender, slick)", "at(golem, pool)",
    "group(dead, gone)", "group(fell, gone)",
    "onEnter(pool, soak)", "effect(soak, target, grant(wet))",
    "effect(fall, target, grant(fell))",
    "immune(golem, forcedMove)",
    "reach(shock, ranged)", "effect(shock, target, grant(shocked))",
    "reach(douse, ranged)", "effect(douse, target, grant(wet))",
    "reach(gust, ranged)", "effect(gust, target, push)",
    "knows(player, shock)", "knows(mage, shock)",
    "knows(player, douse)", "knows(mage, douse)",
    "knows(player, gust)",
]


class AbActsTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/primitives/ab_acts", reset_first=True)
        self.verify_contracts()
        self.set_state(WORLD)

    # ---------------------------------------------------------------- examples

    def test_example_1_an_act_excludes_a_companion(self):
        self.assert_plan("inflict(shocked, gob, player).",
                         contains=["opCast(mage, shock, gob)"],
                         not_contains=["opCast(player, shock, gob)"])

    def test_example_2_knocked_into_the_pit(self):
        self.assert_plan("knockInto(gob, pit, none).", contains=[
            "opCast(player, gust, gob)", "opKnock(player, gob, pit)",
            "opGrant(player, gob, fell)"])

    def test_example_3_a_zone_primes(self):
        """Wet by a knock into the pond is priming too."""
        self.assert_plan("primeAs(player, wet, tender).",
                         contains=["opKnock(player, tender, pond)",
                                   "opGrant(player, tender, wet)"])

    def test_example_4_what_is_there_needs_no_supplier(self):
        self.set_state(["tag(gob, wet)"])
        self.assert_plan_complexity("supply(none, wet, gob).", min_operators=0, max_operators=0)

    # -------------------------------------------------------------- properties

    def test_property_p1_an_act_never_makes_its_own_prerequisites(self):
        """The golem cannot be moved; knockInto does not go looking for a way to
        unbalance it - that is a recipe's job."""
        self.assert_no_plan("knockInto(golem, pit, none).")

    def test_property_p2_one_supplier_per_companion(self):
        self.compile_additional(
            "soakBy(?e) :- if(supplier(?p, wet, ?e)), do(supply(?p, wet, ?e)).")
        self.assert_plan("soakBy(tender).", min_solutions=3, max_solutions=3,
                         contains=["opCast(mage, douse, tender)",
                                   "opCast(player, douse, tender)",
                                   "opKnock(player, tender, pond)"])

    def test_property_p3_a_recipe_is_confirmed_against_the_world(self):
        self.assert_no_plan("confirmStopped(gob).")


    def test_property_p4_a_combo_names_its_halves(self):
        self.set_state(["reaction(wet, shocked, zap)", "effect(zap, target, grant(dead))"])
        """Either companion may prime; the other one delivers."""
        self.assert_plan("combo(wet, shocked, gob).", min_solutions=2, contains=[
            "opCast(mage, douse, gob)", "opCast(player, shock, gob)",
            "opCast(player, douse, gob)", "opCast(mage, shock, gob)"])

    def test_property_p5_unset_takes_a_tag_off(self):
        self.set_state(["tag(gob, shielded)", "reach(dispel, ranged)",
                        "effect(dispel, target, remove(shielded))", "knows(mage, dispel)"])
        self.assert_state_after("unset(shielded, gob).", not_has=["tag(gob,shielded)"])

    def test_property_p6_dislodge_brings_it_elsewhere(self):
        """Only a pull (or a taunt) moves it out of its area."""
        self.set_state(["reach(hk, melee)", "effect(hk, target, hook)", "knows(mage, hk)"])
        self.assert_plan("dislodge(gob).", contains=["opForcedMove(mage, gob, pool, ledge)"])

def run_tests():
    suite = AbActsTest()
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
