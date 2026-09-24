"""Tests for ab_effects."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite


WORLD = [
    "region(ledge)", "region(pool)",
    "connected(ledge, pool)", "feature(pool, pit, fall)",
    "role(player, player)", "role(gob, enemy)", "role(golem, enemy)",
    "at(player, ledge)", "at(gob, pool)", "at(golem, pool)",
    "group(dead, gone)", "group(fell, gone)",
    "bundles(frozen, brittle)", "bundles(frozen, offBalance)",
    "suspends(offBalance, forcedMove)",
    "onEnter(pool, soak)", "effect(soak, target, grant(wet))",
    "effect(fall, target, grant(fell))",
    "reaction(wet, shocked, electrocution)",
    "effect(electrocution, target, remove(wet))", "effect(electrocution, target, grant(dead))",
    "reaction(wet, burning, steam)", "effect(steam, target, remove(wet))",
    "reaction(brittle, blunt, shatterBlow)",
    "effect(shatterBlow, target, remove(frozen))", "effect(shatterBlow, target, grant(dead))",
    "effect(shock, target, grant(shocked))",
    "effect(gust, target, push)",
    "effect(zapPush, target, grant(shocked))", "effect(zapPush, target, push)",
    "effect(hammer, target, damage(blunt))", "effect(hammer, self, grant(tired))",
    "effect(fireball, target, damage(fire))", "effect(fireball, target, grant(burning))",
    "immune(golem, shocked)", "immune(golem, forcedMove)",
]


class AbEffectsTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/primitives/ab_effects", reset_first=True)
        self.verify_contracts()
        self.set_state(WORLD)

    # ---------------------------------------------------------------- examples

    def test_example_1_a_reaction_replaces_the_incoming_tag(self):
        self.set_state(["tag(gob, wet)"])
        self.assert_plan("applyAbility(player, shock, gob, react).", contains=[
            "opReact(player, gob, wet, shocked, electrocution)",
            "opRemove(player, gob, wet)",
            "opGrant(player, gob, dead)",
        ], not_contains=["opGrant(player, gob, shocked)"])

    def test_example_2_a_knockback_into_a_pit(self):
        """A push never changes the area: it knocks the goblin into the pit in
        the pool."""
        self.assert_plan("applyAbility(player, gust, gob, react).", contains=[
            "opKnock(player, gob, pit)", "opGrant(player, gob, fell)",
        ], not_contains=["opForcedMove"])
        self.assert_state_after("applyAbility(player, gust, gob, react).",
                                has=["at(gob,pool)", "tag(gob,fell)"])

    def test_example_3_a_blunt_blow_shatters_the_frozen(self):
        self.set_state(["tag(gob, frozen)"])
        self.assert_state_after("applyAbility(player, hammer, gob, react).",
                                has=["tag(gob,dead)", "tag(player,tired)"],
                                not_has=["tag(gob,frozen)"])

    def test_example_4_a_walk_into_water_soaks(self):
        self.assert_state_after("walkTo(player, pool).",
                                has=["at(player,pool)", "tag(player,wet)"])

    # -------------------------------------------------------------- properties

    def test_property_p1_immunity_spares_one_atom_not_the_ability(self):
        """Immune to shock but not to being moved once frozen: the push lands."""
        self.set_state(["tag(golem, frozen)"])
        self.assert_plan("applyAbility(player, zapPush, golem, react).",
                         contains=["opKnock(player, golem, pit)"],
                         not_contains=["opGrant(player, golem, shocked)"])

    def test_property_p2_reactions_do_not_chain(self):
        """A reaction's own grant lands raw: shocked on something wet stays shocked.
        (Oiled is stored first, so burning meets it before wet: the first
        stored tag with a reaction wins.)"""
        self.set_state(["tag(gob, oiled)", "tag(gob, wet)",
                        "reaction(oiled, burning, flare)", "effect(flare, target, grant(shocked))"])
        self.assert_state_after("grantTag(player, gob, burning, react).",
                                has=["tag(gob,shocked)", "tag(gob,wet)"],
                                not_has=["tag(gob,dead)"])

    def test_property_p3_steam_dries(self):
        self.set_state(["tag(gob, wet)"])
        self.assert_state_after("applyAbility(player, fireball, gob, react).",
                                not_has=["tag(gob,wet)", "tag(gob,burning)"])

    def test_property_p4_the_mover_is_credited(self):
        self.assert_plan("applyAbility(player, gust, gob, react).",
                         not_contains=["opGrant(pit,"])

    def test_property_p5_an_effect_cannot_be_skipped(self):
        """A plan may not drop the hammer's self-tiring to satisfy a later gate."""
        self.set_state(["tag(gob, frozen)"])
        self.compile_additional("needFresh(?a) :- if(not(tag(?a, tired))), do().")
        self.assert_no_plan("applyAbility(player, hammer, gob, react), needFresh(player).")

    def test_property_p6_a_push_goes_where_the_caster_aims(self):
        """Two features in the pool: each is a plan, and so is knocking it into
        nothing."""
        self.set_state(["feature(pool, slickPatch, slicked)", "effect(slicked, target, grant(oiled))"])
        self.assert_plan("applyAbility(player, gust, gob, react).",
                         contains=["opKnock(player, gob, pit)"])
        self.assert_plan("applyAbility(player, gust, gob, react).",
                         contains=["opKnock(player, gob, slickPatch)"],
                         max_solutions=3)


    def test_property_p7_an_area_hits_everyone_but_the_source(self):
        self.set_state(["at(player, pool)", "effect(nova, area, grant(chilled))"])
        self.assert_state_after("applyAbility(player, nova, pool, react).",
                                has=["tag(gob,chilled)", "tag(golem,chilled)"],
                                not_has=["tag(player,chilled)"])

    def test_property_p8_a_spill_makes_a_zone(self):
        self.set_state(["region(slick)", "effect(slickZone, target, grant(oiled))",
                        "effect(oilRain, target, spill(slickZone))"])
        self.assert_state_after("applyAbility(player, oilRain, pool, react).",
                                has=["onEnter(pool,slickZone)", "tag(gob,oiled)", "tag(golem,oiled)"])

    def test_property_p9_a_purge_takes_a_group(self):
        self.set_state(["tag(gob, cursed)", "tag(gob, weak)", "tag(gob, hasted)",
                        "group(cursed, affliction)", "group(weak, affliction)",
                        "effect(cleanse, target, purge(affliction))"])
        self.assert_state_after("applyAbility(player, cleanse, gob, react).",
                                has=["tag(gob,hasted)"], not_has=["tag(gob,cursed)", "tag(gob,weak)"])

    def test_property_p10_a_reaction_before_a_kill(self):
        """A shield absorbs a blow the target is vulnerable to; any damage type
        matches `damage`."""
        self.set_state(["tag(gob, shielded)", "vulnerable(gob, blunt)", "damageType(blunt)",
                        "reaction(shielded, damage, absorb)", "effect(absorb, target, remove(shielded))",
                        "effect(club, target, damage(blunt))"])
        self.assert_state_after("applyAbility(player, club, gob, react).",
                                not_has=["tag(gob,shielded)", "tag(gob,dead)"])

    def test_property_p11_a_weakness_answers_for_that_entity(self):
        """The same tag stuns a machine and is merely stored on anyone else;
        soaked first, the machine dies."""
        self.set_state(["tag(golem, machine)", "effect(zap, target, grant(sparked))",
                        "weakness(?e, sparked, wet, dead) :- has(?e, machine)",
                        "weakness(?e, sparked, none, stunned) :- has(?e, machine)",
                        "tag(gob, wet)"])
        self.assert_state_after("applyAbility(player, zap, golem, react), applyAbility(player, zap, gob, react).",
                                has=["tag(golem,stunned)", "tag(gob,sparked)"], not_has=["tag(golem,dead)"])

    def test_property_p12_a_hazard_takes_only_the_weak(self):
        """A gale on the pool knocks everyone into its chasm: the goblin falls
        and the bat hovers."""
        self.set_state(["region(cliff)", "at(storm, cliff)", "feature(pool, chasm1, drop)",
                        "effect(drop, target, hazard(chasm))",
                        "weakness(?e, chasm, none, fell) :- not(has(?e, flying))",
                        "role(bat, enemy)", "at(bat, pool)", "tag(bat, flying)",
                        "effect(gale, area, push)"])
        self.assert_plan("applyAbility(storm, gale, pool, react).", contains=[
            "opKnock(storm, gob, chasm1)", "opExploit(storm, gob, chasm, fell)",
            "opKnock(storm, bat, chasm1)"])
        self.assert_plan("applyAbility(storm, gale, pool, react).",
                         not_contains=["opExploit(storm, bat, chasm, fell)"])

    def test_property_p13_a_tag_can_move_its_bearer(self):
        self.set_state(["onGrant(feared, push)", "effect(scare, target, grant(feared))"])
        self.assert_state_after("applyAbility(player, scare, gob, react).",
                                has=["tag(gob,feared)", "tag(gob,fell)"])

    def test_property_p14_a_gap_takes_what_is_forced_across(self):
        """Pushed across a gap, the goblin falls in; a flyer crosses; a filler
        that falls in bridges it, and then it is walked over."""
        self.set_state(["region(ridge)", "gap(pool, ridge)", "role(bat, enemy)", "at(bat, pool)",
                        "tag(bat, flying)", "role(crate, object)", "tag(crate, filler)",
                        "at(crate, pool)",
                        "weakness(?e, gap, none, fell) :- not(has(?e, flying))"])
        self.assert_plan("applyAbility(player, gust, gob, react).",
                         contains=["opFall(player, gob, pool, ridge)", "opGrant(player, gob, fell)"])
        self.assert_plan("applyAbility(player, gust, bat, react).",
                         contains=["opForcedMove(player, bat, pool, ridge)"])
        self.assert_plan("applyAbility(player, gust, crate, react), walkTo(player, ridge).",
                         contains=["opBridge(player, pool, ridge)", "opNavigate(player, pool, ridge)"])

    def test_property_p15_a_hook_pulls_the_light_and_is_pulled_by_the_anchored(self):
        self.set_state(["effect(hk, target, hook)"])
        self.assert_state_after("applyAbility(player, hk, gob, react).",
                                has=["at(gob,ledge)", "at(player,ledge)"])
        self.assert_state_after("applyAbility(player, hk, golem, react).",
                                has=["at(golem,pool)", "at(player,pool)", "tag(player,wet)"])

    def test_property_p16_a_swap_trades_places(self):
        self.set_state(["effect(tp, target, swap)"])
        self.assert_state_after("applyAbility(player, tp, gob, react).",
                                has=["at(player,pool)", "at(gob,ledge)", "tag(player,wet)"])

    def test_property_p17_a_pull_across_a_gap_drops_it_in(self):
        self.set_state(["region(far)", "gap(ledge, far)",
                        "weakness(?e, gap, none, fell) :- not(has(?e, flying))",
                        "role(imp, enemy)", "at(imp, far)", "effect(hk, target, hook)"])
        self.assert_state_after("applyAbility(player, hk, imp, react).",
                                has=["at(imp,far)", "tag(imp,fell)"])

    def test_property_p18_a_filled_hazard_is_walked_over(self):
        self.set_state(["region(gap)", "region(far)", "connected(ledge, gap)", "connected(gap, ledge)",
                        "connected(gap, far)", "connected(far, gap)",
                        "onEnter(gap, drop)", "effect(drop, target, hazard(gap))",
                        "weakness(?e, gap, none, fell) :- not(has(?e, flying))",
                        "role(crate, object)", "tag(crate, filler)", "at(crate, gap)",
                        "tag(crate, fell)"])
        self.assert_state_after("walkTo(player, far).", has=["at(player,far)"],
                                not_has=["tag(player,fell)"])

    def test_property_p19_nobody_walks_into_a_live_hazard(self):
        self.set_state(["region(gap)", "region(far)", "connected(ledge, gap)", "connected(gap, ledge)",
                        "connected(gap, far)", "connected(far, gap)",
                        "onEnter(gap, drop)", "effect(drop, target, hazard(gap))",
                        "weakness(?e, gap, none, fell) :- not(has(?e, flying))"])
        self.assert_no_plan("walkTo(player, far).")

    def test_property_p20_blockers_and_doors_stop_a_walk(self):
        """The pool is held by a blocker; the yard is behind a closed door and
        opens to a walk once the door is open."""
        self.set_state(["region(yard)", "doorway(ledge, yard, gate)", "blocker(gob)"])
        self.assert_query("canReach(player, ledge, pool).", min_solutions=0, max_solutions=0)
        self.assert_query("canReach(player, ledge, yard).", min_solutions=0, max_solutions=0)

    def test_property_p20b_an_open_door_is_walked_through(self):
        self.set_state(["region(yard)", "doorway(ledge, yard, gate)", "open(gate)"])
        self.assert_state_after("walkTo(player, yard).", has=["at(player,yard)"])

    def test_property_p21_a_taunted_golem_discharges_on_its_taunter(self):
        """The golem answers a taunt: dragged to the taunter, it discharges on
        the region there - and the robot standing by is short-circuited."""
        self.set_state(["role(bolt, enemy)", "role(bot, enemy)", "at(bolt, pool)", "at(bot, ledge)",
                        "onGrant(taunted, pull)", "effect(taunt, target, grant(taunted))",
                        "behavior(bolt, taunted, discharge, here)",
                        "effect(discharge, area, grant(sparked))",
                        "weakness(bot, sparked, none, dead)"])
        self.assert_state_after("applyAbility(player, taunt, bolt, react).",
                                has=["at(bolt,ledge)", "tag(bot,dead)", "tag(player,sparked)"])
        self.assert_plan("applyAbility(player, taunt, bolt, react).",
                         contains=["opProvoked(bolt, taunted, discharge)",
                                   "opExploit(bolt, bot, sparked, dead)"])


    def test_property_p22_a_watched_region_is_closed_to_the_seen(self):
        self.set_state(["watches(golem, pool)", "forbids(blinded, watch)"])
        self.assert_query("canReach(player, ledge, pool).", min_solutions=0, max_solutions=0)
        self.set_state(["tag(player, stealthed)"])
        self.assert_query("canReach(player, ledge, pool).", min_solutions=1)

    def test_property_p23_a_blinded_watcher_sees_nothing(self):
        self.set_state(["watches(golem, pool)", "forbids(blinded, watch)", "tag(golem, blinded)"])
        self.assert_query("canReach(player, ledge, pool).", min_solutions=1)

    def test_property_p24_two_plates_open_together(self):
        self.set_state(["region(hall)", "connected(ledge, hall)", "doorway(hall, vault, gate)",
                        "region(vault)", "feature(ledge, p1, press1)", "feature(hall, p2, press2)",
                        "plate(p1)", "plate(p2)", "plateFor(p1, gate)", "plateFor(p2, gate)",
                        "effect(press1, target, openWhenHeld(gate))",
                        "effect(press2, target, openWhenHeld(gate))",
                        "role(mage, companion)", "at(mage, ledge)", "on(mage, p1)"])
        self.assert_state_after("walkTo(player, hall), stepOn(player, p2).", has=["open(gate)"])

    def test_property_p25_one_plate_is_not_enough(self):
        self.set_state(["region(hall)", "connected(ledge, hall)", "doorway(hall, vault, gate)",
                        "region(vault)", "feature(ledge, p1, press1)", "feature(hall, p2, press2)",
                        "plate(p1)", "plate(p2)", "plateFor(p1, gate)", "plateFor(p2, gate)",
                        "effect(press2, target, openWhenHeld(gate))"])
        self.assert_state_after("walkTo(player, hall), stepOn(player, p2).", not_has=["open(gate)"])

    def test_property_p26_a_zone_reshapes_a_zone(self):
        self.set_state(["onEnter(pool, water)", "effect(water, target, grant(wet))",
                        "effect(ice, target, grant(chilled))", "zoneReaction(water, ice, ice)",
                        "effect(frost, target, spill(ice))"])
        self.assert_state_after("applyAbility(player, frost, pool, react).",
                                has=["onEnter(pool,ice)"], not_has=["onEnter(pool,water)"])

    def test_property_p27_a_zone_can_leave_nothing(self):
        self.set_state(["onEnter(pool, water)", "effect(water, target, grant(wet))",
                        "effect(ice, target, grant(chilled))", "zoneReaction(water, ice, none)",
                        "effect(frost, target, spill(ice))"])
        self.assert_state_after("applyAbility(player, frost, pool, react).",
                                not_has=["onEnter(pool,ice)", "onEnter(pool,water)"])

    def test_property_p28_a_door_can_be_closed(self):
        self.set_state(["door(gate)", "open(gate)", "effect(shut, target, close(gate))"])
        self.assert_state_after("applyAbility(player, shut, ledge, react).", not_has=["open(gate)"])

    def test_property_p29_only_magic_is_interrupted(self):
        self.set_state(["role(brute, enemy)", "at(brute, pool)", "kind(spell, magic)",
                        "windingUp(brute, spell, player)", "effect(stop, target, interrupt)"])
        self.assert_state_after("applyAbility(player, stop, brute, react).",
                                not_has=["windingUp(brute,spell,player)"])

    def test_property_p30_a_physical_blow_goes_on(self):
        self.set_state(["role(brute, enemy)", "at(brute, pool)",
                        "windingUp(brute, slam, player)", "effect(stop, target, interrupt)"])
        self.assert_state_after("applyAbility(player, stop, brute, react).",
                                has=["windingUp(brute,slam,player)"])


def run_tests():
    suite = AbEffectsTest()
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
