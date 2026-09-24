"""Tests for ab_casting."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite


WORLD = [
    "region(ledge)", "region(pool)",
    "connected(ledge, pool)", "connected(pool, ledge)",
    "lineOfSight(ledge, pool)",
    "role(player, player)", "role(mage, companion)", "role(gob, enemy)", "role(golem, enemy)",
    "at(player, ledge)", "at(mage, ledge)", "at(gob, pool)", "at(golem, pool)",
    "group(dead, gone)",
    "onEnter(pool, soak)", "effect(soak, target, grant(wet))",
    "reach(shock, ranged)", "effect(shock, target, grant(shocked))",
    "reach(hammer, melee)", "effect(hammer, target, damage(blunt))",
    "effect(hammer, self, grant(tired))", "blockedBy(hammer, caster, tired)",
    "reach(fireball, ranged)", "manaCost(fireball, 2)", "effect(fireball, target, grant(burning))",
    "reach(bomb, ranged)", "once(bomb)", "effect(bomb, target, grant(stunned))",
    "reach(jolt, ranged)", "requires(jolt, target, wet)", "effect(jolt, target, grant(jolted))",
    "reach(rally, self)", "effect(rally, self, grant(inspired))",
    "knows(player, shock)", "knows(player, hammer)", "knows(player, fireball)",
    "knows(player, bomb)", "knows(player, jolt)", "knows(player, rally)",
    "knows(mage, shock)",
]


class AbCastingTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/primitives/ab_casting", reset_first=True)
        self.verify_contracts()
        self.set_state(WORLD)

    # ---------------------------------------------------------------- examples

    def test_example_1_a_ranged_cast_from_where_it_stands(self):
        self.assert_plan("cast(player, shock, gob).",
                         contains=["opCast(player, shock, gob)", "opGrant(player, gob, shocked)"],
                         not_contains=["opNavigate"])

    def test_example_2_melee_reaches_the_next_region(self):
        """The pool is next to the ledge: the swing lands without a step, and
        the caster stays dry."""
        self.assert_plan("cast(player, hammer, gob).", contains=["opCast(player, hammer, gob)"],
                         not_contains=["opNavigate"])
        self.assert_state_after("cast(player, hammer, gob).",
                                has=["tag(player,tired)"], not_has=["tag(player,wet)"])

    def test_example_3_mana_is_paid(self):
        self.set_state(["mana(player, 3)"])
        self.assert_plan("cast(player, fireball, gob).", contains=["opSpendMana(player, 2)"])
        self.assert_state_after("cast(player, fireball, gob).", has=["mana(player,1)"])

    def test_example_4_a_self_ability(self):
        self.assert_state_after("cast(player, rally, player).", has=["tag(player,inspired)"])

    # -------------------------------------------------------------- properties

    def test_property_p1_a_tired_caster_cannot_swing(self):
        self.set_state(["tag(player, tired)"])
        self.assert_no_plan("cast(player, hammer, gob).")

    def test_property_p2_requirements_on_the_target(self):
        self.set_state(["tag(gob, wet)"])
        self.assert_plan("cast(player, jolt, gob).", contains=["opGrant(player, gob, jolted)"])
        self.assert_no_plan("cast(player, jolt, golem).")

    def test_property_p3_no_mana_no_cast(self):
        self.set_state(["mana(player, 1)"])
        self.assert_no_plan("cast(player, fireball, gob).")

    def test_property_p4_once_means_once(self):
        self.assert_plan("cast(player, bomb, gob).", contains=["opUseUp(player, bomb)"])
        self.assert_no_plan("cast(player, bomb, gob), cast(player, bomb, golem).")

    def test_property_p5_anyone_casts_what_they_know(self):
        self.assert_plan("cast(mage, shock, gob).", contains=["opGrant(mage, gob, shocked)"])

    def test_property_p6_the_gone_are_no_targets(self):
        self.set_state(["tag(gob, dead)"])
        self.assert_no_plan("cast(player, shock, gob).")


    def test_property_p7_a_forbidden_kind_is_not_cast(self):
        self.set_state(["kind(shock, spell)", "tag(player, silenced)", "forbids(silenced, spell)"])
        self.assert_plan("cast(player, hammer, gob).")
        self.assert_no_plan("cast(player, shock, gob).")

    def test_property_p8_the_hidden_cannot_be_aimed_at(self):
        self.set_state(["tag(gob, stealthed)", "wards(stealthed, targeted)"])
        self.assert_no_plan("cast(player, shock, gob).")

    def test_property_p9_a_region_is_a_target(self):
        self.set_state(["reach(nova, ranged)", "effect(nova, area, grant(chilled))", "knows(player, nova)"])
        self.assert_state_after("cast(player, nova, pool).",
                                has=["tag(gob,chilled)", "tag(golem,chilled)"])

    def test_property_p10_melee_walks_within_reach(self):
        """Two regions away, the caster walks to the next region, no further."""
        self.set_state(["region(yard)", "connected(pool, yard)", "connected(yard, pool)",
                        "role(imp, enemy)", "at(imp, yard)"])
        self.assert_state_after("cast(player, hammer, imp).",
                                has=["at(player,pool)", "tag(player,tired)"])


def run_tests():
    suite = AbCastingTest()
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
