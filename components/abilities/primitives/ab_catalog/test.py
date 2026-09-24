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
    """tag -> skills that can put it on something: a grant (with the atoms of a
    composite), a zone the skill spills, or a weakness the incoming meets."""
    effects, bundles, _ = catalogue()
    weaknesses = defaultdict(set)
    for _, incoming, _, out in facts("weakness", rules=True):
        weaknesses[incoming].add(out)

    def granted(atoms):
        out = set()
        for _, atom in atoms:
            m = re.match(r"grant\((\w+)\)", atom)
            if m:
                out |= {m.group(1)} | bundles[m.group(1)]
                out |= weaknesses[m.group(1)]
            m = re.match(r"hazard\((\w+)\)", atom)
            if m:
                out |= weaknesses[m.group(1)]
        return out

    by_tag = defaultdict(set)
    for ab, _ in facts("reach"):
        tags = granted(effects[ab])
        for _, atom in effects[ab]:
            m = re.match(r"spill\((\w+)\)", atom)
            if m:
                tags |= granted(effects[m.group(1)])
        for t in tags:
            by_tag[t].add(ab)
    return by_tag


def consumers():
    """Tags that do something: react, bundle, forbid, ward, move, gate, trigger
    a weakness, or stop the fight."""
    used = {have for have, _, _ in facts("reaction")}
    used |= {t for t, _ in facts("forbids")}
    used |= {t for t, _ in facts("wards")}
    used |= {t for t, _ in facts("onGrant")}
    used |= {t for _, _, t in facts("requires")}
    used |= {c for c, _ in facts("bundles")}
    used |= {t for t, g in facts("group") if g == "gone"}
    used |= {incoming for _, incoming, _, _ in facts("weakness", rules=True)}
    return used


class AbCatalogTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/primitives/ab_catalog", reset_first=True)
        self.verify_contracts()
        self.set_state(WORLD)

    # ---------------------------------------------------------------- examples

    def test_example_1_a_robot_is_stunned_or_short_circuited(self):
        self.set_state(["trait(foe, machine)", "knows(player, zap)"])
        self.assert_state_after("cast(player, zap, foe).",
                                has=["tag(foe,stunned)"], not_has=["tag(foe,dead)"])

    def test_example_2_a_soaked_robot_dies(self):
        self.set_state(["trait(foe, machine)", "tag(foe, wet)", "knows(player, zap)"])
        self.assert_state_after("cast(player, zap, foe).", has=["tag(foe,dead)"])

    def test_example_3_a_fire_imp_freezes_solid(self):
        self.set_state(["element(foe, fire)", "knows(player, frostBolt)"])
        self.assert_state_after("cast(player, frostBolt, foe).", has=["tag(foe,frozen)"])

    def test_example_4_the_floor_gives_way(self):
        self.set_state(["role(bat, enemy)", "at(bat, floor)", "trait(bat, flier)",
                        "knows(player, collapse)"])
        self.assert_state_after("cast(player, collapse, floor).",
                                has=["tag(foe,fell)"], not_has=["tag(bat,fell)"])

    def test_example_5_fear_sends_it_running(self):
        self.set_state(["knows(player, terrify)"])
        self.assert_state_after("cast(player, terrify, foe).",
                                has=["tag(foe,feared)", "at(foe,far)"])

    # -------------------------------------------------------------- properties

    def test_property_p1_every_tag_from_two_skills(self):
        by_tag = applies()
        _, _, tags = catalogue()
        short = {t: sorted(by_tag[t]) for t in tags if len(by_tag[t]) < 2}
        assert not short, f"tags applicable by fewer than two skills: {short}"
        self._record(True, f"P1: all {len(tags)} tags applicable by two or more skills")

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
        self._record(True, "P3: no skill grants dead, frozen or fell")

    def test_property_p4_looks_map_to_tags(self):
        _, _, tags = catalogue()
        looks = facts("appearance")
        stray = [(l, t) for l, t in looks if t not in tags or l in tags]
        assert not stray, f"looks that are tags, or map to no tag: {stray}"
        self._record(True, f"P4: {len(looks)} looks, each a new name for a catalogue tag")

    def test_property_p5_a_shield_takes_the_next_hostile_tag(self):
        self.set_state(["tag(foe, shielded)", "knows(player, net)"])
        self.assert_state_after("cast(player, net, foe).",
                                has=["tag(foe,blinded)"],
                                not_has=["tag(foe,shielded)", "tag(foe,rooted)"])

    def test_property_p6_a_hit_wakes_the_sleeper(self):
        self.set_state(["tag(foe, asleep)", "knows(player, magnetize)"])
        self.assert_state_after("cast(player, magnetize, foe).",
                                not_has=["tag(foe,asleep)"])

    def test_property_p7_bosses_keep_the_atoms(self):
        self.set_state(["rank(foe, boss)", "knows(player, shieldBash)", "knows(mage, net)"])
        self.assert_state_after("cast(player, shieldBash, foe).", not_has=["tag(foe,stunned)"])
        self.assert_state_after("cast(mage, net, foe).", has=["tag(foe,rooted)"])

    def test_property_p8_haste_counters_slow(self):
        self.set_state(["tag(foe, hasted)", "knows(player, magnetize)"])
        self.assert_state_after("cast(player, magnetize, foe).", not_has=["tag(foe,slowed)"])

    def test_property_p9_only_the_hasted_blitz(self):
        self.set_state(["knows(player, blitz)", "knows(mage, haste)"])
        self.assert_plan("cast(mage, haste, player), cast(player, blitz, foe).")
        self.assert_no_plan("cast(player, blitz, foe).")


    def test_property_p10_lightning_flash_strikes_the_path(self):
        self.set_state(["role(bot, enemy)", "at(bot, floor)", "trait(bot, machine)",
                        "mana(player, 2)", "knows(player, lightningFlash)"])
        self.assert_state_after("cast(player, lightningFlash, far).",
                                has=["tag(bot,stunned)", "tag(foe,electrocuted)", "at(player,far)"])

    def test_property_p11_fireball_leaves_a_fire(self):
        self.set_state(["mana(player, 2)", "knows(player, fireball)"])
        self.assert_state_after("cast(player, fireball, foe).",
                                has=["onEnter(floor,flames)", "tag(foe,burning)", "at(foe,far)"])

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
