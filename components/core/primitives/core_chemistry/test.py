"""Tests for core_chemistry."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite


WORLD = [
    "region(pit)", "region(ledge)", "lineOfSight(ledge, pit)",
    "role(player, player)", "role(arcanist, companion)", "role(gob, enemy)",
    "at(player, pit)", "at(arcanist, ledge)", "at(gob, pit)",
    "regionHas(pit, oil)",
    "skillElement(ignite, fire)", "skillElement(freeze, freeze)",
    "reacts(fire, oil, scorched)", "reacts(freeze, oil, sludge)",
    "blast(fire, oil, dead)", "terrain(sludge, snared)", "strike(fire, dead)",
    "hasSkill(player, ignite)", "hasSkill(arcanist, freeze)",
    "signature(arcanist, freeze)",
]


class CoreChemistryTest(HtnTestSuite):

    def setup(self):
        self.load_component("core/primitives/core_chemistry", reset_first=True)
        self.verify_contracts()
        self.set_state(WORLD)

    # ---------------------------------------------------------------- examples

    def test_example_1_fire_on_oil(self):
        self.set_state(["charge(player, ignite, c1)"])
        self.assert_plan("applyToRegion(player, fire, pit).", contains=[
            "opSpendCharge(player, ignite, c1)",
            "opCastRegion(player, ignite, pit, oil, scorched)",
            "opStatus(player, gob, dead)",
        ])
        self.assert_state_after("applyToRegion(player, fire, pit).",
                                has=["regionHas(pit,scorched)", "status(gob,dead)"],
                                not_has=["regionHas(pit,oil)", "charge(player,ignite,c1)"])

    def test_example_2_signature_skill_is_free(self):
        self.assert_plan("applyToRegion(arcanist, freeze, pit).",
                         contains=["opCastRegion(arcanist, freeze, pit, oil, sludge)"],
                         not_contains=["opSpendCharge"])

    def test_example_3_strike_needs_a_snared_target(self):
        self.set_state(["charge(player, ignite, c1)"])
        self.assert_no_plan("applyToEntity(player, fire, gob).")
        self.set_state(["status(gob, snared)"])
        self.assert_plan("applyToEntity(player, fire, gob).",
                         contains=["opCastEntity(player, ignite, gob, dead)"])

    # -------------------------------------------------------------- properties

    def test_property_p1_no_charge_no_cast(self):
        self.assert_no_plan("applyToRegion(player, fire, pit).")

    def test_property_p2_shields_turn_blasts(self):
        self.set_state(["charge(player, ignite, c1)", "status(gob, shielded)"])
        self.assert_plan("applyToRegion(player, fire, pit).",
                         contains=["opCastRegion(player, ignite, pit, oil, scorched)"],
                         not_contains=["opStatus(player, gob, dead)"])

    def test_property_p3_terrain_settles(self):
        self.assert_state_after("applyToRegion(arcanist, freeze, pit).",
                                has=["status(gob,snared)", "status(player,snared)"])


def run_tests():
    suite = CoreChemistryTest()
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
