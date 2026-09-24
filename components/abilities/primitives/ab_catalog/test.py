"""Tests for ab_catalog."""

import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src.htn")

# A small arena: companions on a ledge above a floor, a chasm beyond it.
WORLD = [
    "region(ledge)", "region(floor)", "region(far)",
    "connected(ledge, floor)", "connected(floor, ledge)",
    "lineOfSight(ledge, floor)", "lineOfSight(ledge, far)",
    "beyond(ledge, floor, far)", "beyond(floor, floor, far)",
    "role(player, player)", "role(mage, companion)",
    "at(player, ledge)", "at(mage, ledge)",
    "role(foe, enemy)", "at(foe, floor)",
]


# ------------------------------------------------------------------ static


def facts(pred, rules=False):
    """Facts of `pred` in the catalogue, as argument lists. With `rules`, rule
    heads too (their ?variables left in place)."""
    out = []
    with open(SRC, encoding="utf-8") as f:
        for line in f:
            m = re.match(rf"^{pred}\((.*?)\)(\.| :-)", line.strip())
            if not m or (m.group(2) != "." and not rules):
                continue
            if "?" in m.group(1) and not rules:
                continue
            out.append([a.strip() for a in re.split(r",\s*(?![^()]*\))", m.group(1))])
    return out


def catalogue():
    effects = defaultdict(list)
    for ab, who, atom in facts("effect"):
        effects[ab].append((who, atom))
    bundles = defaultdict(set)
    for c, a in facts("bundles"):
        bundles[c].add(a)
    tags = {t for t, _ in facts("group")} | {a for _, a in facts("bundles")}
    return effects, bundles, tags


def applies():
    """tag -> what can put it on something: a skill's grant (with the atoms of
    a composite), a zone it spills, a weakness the incoming meets, or a
    reaction to a tag a skill lands."""
    effects, bundles, _ = catalogue()
    weaknesses = defaultdict(set)
    for _, incoming, _, out in facts("weakness", rules=True):
        weaknesses[incoming].add(out)
    reactions = defaultdict(set)
    for _, incoming, ab in facts("reaction"):
        reactions[incoming].add(ab)

    def granted(atoms, depth=0):
        out = set()
        for _, atom in atoms:
            m = re.match(r"grant\((\w+)\)", atom)
            if m:
                t = m.group(1)
                out |= {t} | bundles[t] | weaknesses[t]
                if depth == 0:
                    for rab in reactions[t]:
                        out |= granted(effects[rab], 1)
            m = re.match(r"hazard\((\w+)\)", atom)
            if m:
                out |= weaknesses[m.group(1)]
            m = re.match(r"spill\((\w+)\)", atom)
            if m and depth < 2:
                out |= granted(effects[m.group(1)], depth)
        return out

    by_tag = defaultdict(set)
    zones = {z for z, _, a in facts("effect") if a.startswith("grant") or a.startswith("hazard")}
    for ab in {ab for ab, _ in facts("reach")} | zones:
        for t in granted(effects[ab]):
            by_tag[t].add(ab)
    return by_tag


def consumers():
    """Tags that do something: react, bundle, forbid, ward, move, gate, trigger
    a weakness, suspend or disable, or stop the fight."""
    used = {have for have, _, _ in facts("reaction")}
    used |= {t for t, _ in facts("forbids")}
    used |= {t for t, _ in facts("wards")}
    used |= {t for t, _ in facts("onGrant")}
    used |= {t for _, _, t in facts("requires")}
    used |= {c for c, _ in facts("bundles")}
    used |= {t for t, _ in facts("suspends")}
    used |= {t for t, _ in facts("disables")}
    used |= {t for t, g in facts("group") if g == "gone"}
    used |= {incoming for _, incoming, _, _ in facts("weakness", rules=True)}
    used |= {have for _, _, have, _ in facts("weakness", rules=True)}
    return used


def movers():
    """Skills that move something (a push, pull, hook, dash, relocate, pull-in,
    or a tag that drags its bearer)."""
    effects, _, _ = catalogue()
    dragging = {t for t, _ in facts("onGrant")}
    out = set()
    for ab, _ in facts("reach"):
        for _, atom in effects[ab]:
            m = re.match(r"grant\((\w+)\)", atom)
            if atom in ("push", "pull", "hook", "dash", "relocate", "swap") \
                    or atom.startswith("pullIn") or (m and m.group(1) in dragging):
                out.add(ab)
    return out


class AbCatalogTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/primitives/ab_catalog", reset_first=True)
        self.verify_contracts()
        self.set_state(WORLD)

    # ---------------------------------------------------------------- examples

    def test_example_1_a_robot_is_stunned_or_short_circuited(self):
        self.set_state(["trait(foe, machine)", "mana(player, 2)", "knows(player, lightningFlash)"])
        self.assert_state_after("cast(player, lightningFlash, foe).",
                                has=["tag(foe,stunned)"], not_has=["tag(foe,dead)"])

    def test_example_2_a_soaked_robot_dies(self):
        self.set_state(["trait(foe, machine)", "tag(foe, wet)", "mana(player, 2)",
                        "knows(player, lightningFlash)"])
        self.assert_state_after("cast(player, lightningFlash, foe).", has=["tag(foe,dead)"])

    def test_example_3_a_fire_imp_freezes_solid(self):
        self.set_state(["element(foe, fire)", "mana(player, 2)", "knows(player, blizzard)"])
        self.assert_state_after("cast(player, blizzard, floor).", has=["tag(foe,dead)"])

    def test_example_4_soak_then_freeze(self):
        """The wave soaks the foe and washes it to the far side; the blizzard
        there freezes it."""
        self.set_state(["mana(player, 2)", "mana(mage, 2)",
                        "knows(player, tidalWave)", "knows(mage, blizzard)"])
        self.assert_state_after("cast(player, tidalWave, player), cast(mage, blizzard, far).",
                                has=["at(foe,far)", "tag(foe,frozen)", "tag(player,wet)"],
                                not_has=["tag(foe,wet)"])

    def test_example_5_a_frozen_foe_shatters(self):
        self.set_state(["tag(foe, frozen)", "knows(player, shieldBash)"])
        self.assert_state_after("cast(player, shieldBash, foe).", has=["tag(foe,dead)"])

    def test_example_6_the_magnet_takes_the_armour_while_it_lasts(self):
        """Inside the field the guard's armour does nothing: it is bashed out,
        and wears its armour again beyond."""
        self.set_state(["tag(foe, armored)", "mana(mage, 2)",
                        "knows(mage, magneticOrb)", "knows(player, shieldBash)"])
        self.assert_state_after("cast(mage, magneticOrb, floor), cast(player, shieldBash, foe).",
                                has=["at(foe,far)", "tag(foe,armored)"])
        self.assert_no_plan("cast(player, shieldBash, foe), ensureMoved(foe, floor).")

    def test_example_7_the_vortex_takes_friends_too(self):
        self.set_state(["connected(floor, far)", "connected(far, floor)",
                        "role(imp, enemy)", "at(imp, far)", "knows(player, vortex)"])
        self.assert_state_after("cast(player, vortex, floor).",
                                has=["at(imp,floor)", "at(mage,floor)", "at(player,ledge)"])

    # -------------------------------------------------------------- properties

    def test_property_p1_every_hostile_tag_has_a_skill(self):
        by_tag = applies()
        hostile = {t for t, g in facts("group") if g == "hostile"}
        short = sorted(t for t in hostile if not by_tag[t])
        assert not short, f"hostile tags no skill or zone leads to: {short}"
        self._record(True, f"P1: all {len(hostile)} hostile tags come from a skill or a zone")

    def test_property_p2_every_tag_does_something(self):
        _, _, tags = catalogue()
        idle = sorted(tags - consumers())
        assert not idle, f"tags nothing reads: {idle}"
        self._record(True, "P2: every tag reacts, bundles, forbids, wards, moves, gates or stops")

    def test_property_p3_no_skill_grants_an_outcome(self):
        gone = {t for t, g in facts("group") if g == "gone"}
        effects, _, _ = catalogue()
        bad = sorted(ab for ab, _ in facts("reach")
                     for _, atom in effects[ab]
                     if re.match(r"grant\((\w+)\)", atom)
                     and re.match(r"grant\((\w+)\)", atom).group(1) in gone)
        assert not bad, f"skills granting an outcome: {bad}"
        self._record(True, "P3: no skill grants dead or fell")

    def test_property_p4_looks_map_to_tags(self):
        _, _, tags = catalogue()
        looks = facts("appearance")
        stray = [(l, t) for l, t in looks if t not in tags or l in tags]
        assert not stray, f"looks that are tags, or map to no tag: {stray}"
        self._record(True, f"P4: {len(looks)} looks, each a new name for a catalogue tag")

    def test_property_p5_most_skills_move_something(self):
        skills = {ab for ab, _ in facts("reach")}
        still = sorted(skills - movers())
        assert still == ["blindingFlash", "blizzard"], still
        self._record(True, f"P5: {len(skills) - 2} of {len(skills)} skills move something")

    def test_property_p6_a_shield_takes_the_next_hostile_tag(self):
        self.set_state(["tag(foe, shielded)", "knows(player, taunt)"])
        self.assert_state_after("cast(player, taunt, foe).",
                                not_has=["tag(foe,shielded)", "tag(foe,taunted)"])

    def test_property_p7_bosses_cannot_be_stunned_or_frozen(self):
        self.set_state(["rank(foe, boss)", "tag(foe, wet)", "mana(mage, 2)",
                        "knows(player, shieldBash)", "knows(mage, blizzard)"])
        self.assert_state_after("cast(player, shieldBash, foe).",
                                has=["at(foe,far)"], not_has=["tag(foe,stunned)"])
        self.assert_state_after("cast(mage, blizzard, floor).", not_has=["tag(foe,frozen)"])

    def test_property_p8_lightning_flash_strikes_the_path(self):
        self.set_state(["role(bot, enemy)", "at(bot, floor)", "trait(bot, machine)",
                        "mana(player, 2)", "knows(player, lightningFlash)"])
        self.assert_state_after("cast(player, lightningFlash, far).",
                                has=["tag(bot,stunned)", "at(player,far)"])

    def test_property_p9_fireball_leaves_a_fire(self):
        self.set_state(["mana(player, 2)", "knows(player, fireball)"])
        self.assert_state_after("cast(player, fireball, foe).",
                                has=["onEnter(floor,flames)", "tag(foe,burning)", "at(foe,far)"])

    def test_property_p10_translocate_swaps_or_blinks(self):
        self.set_state(["knows(player, translocate)"])
        self.assert_state_after("cast(player, translocate, foe).",
                                has=["at(player,floor)", "at(foe,ledge)"])
        self.assert_state_after("cast(player, translocate, far).", has=["at(player,far)"])

    def test_property_p11_hook_plucks_a_flyer(self):
        self.set_state(["tag(foe, flying)", "knows(player, hook)"])
        self.assert_state_after("cast(player, hook, foe).",
                                has=["at(foe,ledge)"], not_has=["tag(foe,flying)"])

    # ----------------------------------------------------------- heavy attacks

    OGRE = ["role(ogre, enemy)", "at(ogre, floor)", "trait(ogre, living)",
            "behavior(ogre, taunted, groundSlam, source)", "at(mage, far)"]

    def ogre(self, extra):
        """The arena with the mage out of the way, an ogre on the floor."""
        self.load_component("abilities/primitives/ab_catalog", reset_first=True)
        self.set_state([f for f in WORLD if f != "at(mage, ledge)"] + self.OGRE + extra)

    def test_property_p12_a_heavy_blow_must_be_survived(self):
        """Taunted, the ogre is dragged to the player and slams where they
        stand. Nobody can answer: no plan."""
        self.ogre(["knows(player, taunt)"])
        self.assert_no_plan("cast(player, taunt, ogre).")

    def test_property_p13_phase_through_it(self):
        self.ogre(["knows(player, taunt)", "knows(player, blindingFlash)"])
        self.assert_state_after("cast(player, taunt, ogre).",
                                has=["at(player,ledge)", "tag(ogre,blinded)"],
                                not_has=["tag(player,phased)", "windingUp(ogre,ledge)"])
        self.assert_plan("cast(player, taunt, ogre).",
                         contains=["opCast(player, blindingFlash, player)",
                                   "opBlow(ogre, groundSlam, ledge)"])

    def test_property_p14_interrupt_it(self):
        self.ogre(["knows(player, taunt)", "knows(player, shieldBash)"])
        self.assert_plan("cast(player, taunt, ogre).",
                         contains=["opCast(player, shieldBash, ogre)",
                                   "opInterrupt(ogre, groundSlam, ledge)"])

    def test_property_p15_swap_an_enemy_in(self):
        """Translocate out: to an empty region, or by swapping with the imp
        far off - and then the slam lands on the imp."""
        self.ogre(["role(imp, enemy)", "at(imp, far)",
                   "knows(player, taunt)", "knows(player, translocate)"])
        self.assert_plan("cast(player, taunt, ogre).",
                         contains=["opSwap(player, imp, ledge, far)",
                                   "opGrant(ogre, imp, stunned)"])
        self.assert_plan("cast(player, taunt, ogre).",
                         contains=["opDash(player, ledge, floor)", "opBlow(ogre, groundSlam, ledge)"])


def run_tests():
    suite = AbCatalogTest()
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
