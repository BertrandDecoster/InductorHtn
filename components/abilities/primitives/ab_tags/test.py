"""Tests for ab_tags."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite


WORLD = [
    "bundles(frozen, rooted)", "bundles(frozen, brittle)", "bundles(frozen, offBalance)",
    "group(dead, gone)", "group(fell, gone)", "suspends(offBalance, forcedMove)",
]


class AbTagsTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/primitives/ab_tags", reset_first=True)
        self.verify_contracts()
        self.set_state(WORLD)

    def holds_true(self, query):
        return self.assert_query(query, min_solutions=1)

    def holds_false(self, query):
        return self.assert_query(query, min_solutions=0, max_solutions=0)

    # ---------------------------------------------------------------- examples

    def test_example_1_a_composite_carries_its_atoms(self):
        self.set_state(["tag(gob, frozen)"])
        self.holds_true("has(gob, frozen).")
        self.holds_true("holds(gob, rooted).")
        self.holds_true("holds(gob, brittle).")
        self.holds_false("tag(gob, rooted).")

    def test_example_2_immunity_to_an_atom_refuses_the_composite(self):
        self.set_state(["immune(golem, rooted)"])
        self.holds_true("refuses(golem, frozen).")
        self.holds_false("canReceive(golem, frozen).")
        self.holds_true("canReceive(golem, wet).")

    def test_example_3_a_tag_suspends_an_immunity(self):
        self.set_state(["immune(golem, forcedMove)"])
        self.holds_false("receptive(golem, forcedMove).")
        self.set_state(["tag(golem, frozen)"])
        self.holds_true("receptive(golem, forcedMove).")

    def test_example_4_what_stops_an_entity(self):
        self.set_state(["tag(gob, fell)", "tag(wader, frozen)", "stops(wader, frozen)",
                        "tag(tender, frozen)"])
        self.holds_true("neutralized(gob).")
        self.holds_true("gone(gob).")
        self.holds_true("neutralized(wader).")
        self.holds_false("neutralized(tender).")

    # -------------------------------------------------------------- properties

    def test_property_p1_atoms_are_never_stored(self):
        self.set_state(["tag(gob, frozen)"])
        self.assert_state_after("opGrant(x, gob, wet).",
                                has=["tag(gob,frozen)", "tag(gob,wet)"],
                                not_has=["tag(gob,rooted)", "tag(gob,brittle)"])
        self.assert_state_after("opRemove(x, gob, frozen).", not_has=["tag(gob,frozen)"])

    def test_property_p2_the_gone_take_nothing(self):
        self.set_state(["tag(gob, dead)"])
        self.holds_false("canReceive(gob, wet).")
        self.holds_false("receptive(gob, forcedMove).")

    def test_property_p3_a_stored_tag_is_not_stored_twice(self):
        self.set_state(["tag(gob, wet)"])
        self.holds_false("canReceive(gob, wet).")
        self.holds_true("receptive(gob, wet).")


    def test_property_p4_a_tag_wards(self):
        self.set_state(["tag(harpy, flying)", "wards(flying, fell)",
                        "tag(knight, invulnerable)", "wards(invulnerable, damage)",
                        "damageType(fire)"])
        self.holds_false("receptive(harpy, fell).")
        self.holds_true("receptive(harpy, wet).")
        self.holds_false("receptive(knight, fire).")

    def test_property_p5_a_tag_forbids(self):
        self.set_state(["tag(adept, silenced)", "forbids(silenced, spell)",
                        "tag(brute, stunned)", "forbids(stunned, any)"])
        self.holds_true("forbidden(adept, spell).")
        self.holds_false("forbidden(adept, attack).")
        self.holds_true("forbidden(brute, attack).")

    def test_property_p6_control_is_not_out(self):
        """A stunned enemy is set up, not beaten; a hostile ward covers every
        hostile tag."""
        self.set_state(["tag(brute, stunned)", "forbids(stunned, any)",
                        "tag(saint, invulnerable)", "wards(invulnerable, hostile)",
                        "group(wet, hostile)", "hostile(wet)"])
        self.holds_false("neutralized(brute).")
        self.holds_false("receptive(saint, wet).")

def run_tests():
    suite = AbTagsTest()
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
