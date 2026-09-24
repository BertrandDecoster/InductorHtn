"""Tests for the Wyvern Roost level."""

import itertools
import json
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite
from indhtnpy import HtnPlanner
from htn_components.loader import ComponentLoader

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../.."))
POOL = ["blizzard", "lightningFlash", "tidalWave", "fireball", "hook", "taunt"]

# The measured matrix (htn_components combos): the pairs that win, and nothing else does.
WINNING = {
    frozenset(p) for p in [
        # ground it (frost, lightning), then pull it across the lava or blast it over the cliff
        ("blizzard", "hook"), ("blizzard", "taunt"), ("blizzard", "fireball"),
        ("lightningFlash", "hook"), ("lightningFlash", "taunt"), ("lightningFlash", "fireball"),
        # fetch the flyer onto the ledge, then a wave soaks it and washes it into the lava
        ("hook", "tidalWave"), ("taunt", "tidalWave"),
        # cool the lava into rock, wade out, wash it over the cliff
        ("blizzard", "tidalWave"),
    ]
}


def _op_text(op):
    name = list(op.keys())[0]
    args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]
    return f"{name}({','.join(args)})"


def plans_with(player, mage):
    """Every winning plan, as lists of operator strings, with the player knowing
    `player` and the mage `mage` - on a fresh planner (a failed search locks the
    rule set)."""
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^knows\((player|mage), \w+\)\.\n", "", text, flags=re.M)
    planner = HtnPlanner(False)
    planner.SetMemoryBudget(256 * 1024 * 1024)
    loader = ComponentLoader(planner, ROOT)
    loader.load("abilities/goals/neutralize")
    loader.load("abilities/primitives/ab_catalog")
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n"
    assert planner.HtnCompileCustomVariables(text + kit) is None
    error, result = planner.FindAllPlansCustomVariables("win.")
    assert error is None, error
    sols = json.loads(result)
    if not sols or (isinstance(sols[0], dict) and "false" in sols[0]):
        return []
    return [[_op_text(op) for op in sol] for sol in sols]


def before(plan, first, then):
    return first in plan and then in plan and plan.index(first) < plan.index(then)


class WyvernRoostTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_frost_then_hook(self):
        plans = plans_with("blizzard", "hook")
        ok = any(before(p, "opRemove(player,wyvern,flying)", "opCast(mage,hook,wyvern)")
                 and "opExploit(mage,wyvern,lava,fell)" in p for p in plans)
        assert ok, "the blizzard should frost its wings, then the hook drag it into the lava"
        self._record(True, "Example 1: a blizzard frosts its wings; a hook drags it across the lava, and it falls")

    def test_example_2_ice_melts_under_the_fireball(self):
        plans = plans_with("blizzard", "fireball")
        ok = any(before(p, "opSpill(player,crag,iceSheet)", "opReshape(mage,crag,iceSheet,puddle)")
                 and "opReact(mage,wyvern,chilled,wet,freezeOver)" in p
                 and "opExploit(mage,wyvern,chasm,fell)" in p for p in plans)
        assert ok, "the fireball should melt the ice into a puddle, freeze the wyvern and blow it over"
        self._record(True, "Example 2: ice, then fire: the puddle freezes the frosted wyvern as it goes over the cliff")

    def test_example_3_fetch_and_wash_back(self):
        plans = plans_with("hook", "tidalWave")
        ok = any(before(p, "opForcedMove(player,wyvern,crag,ledge)", "opCast(mage,tidalWave,mage)")
                 and "opExploit(mage,wyvern,lava,fell)" in p for p in plans)
        assert ok, "the hook should fetch the flyer onto the ledge, and the wave wash it into the lava"
        self._record(True, "Example 3: hook the flyer over the lava, step aside, and a wave washes it back in")

    def test_example_4_cool_the_lava(self):
        plans = plans_with("blizzard", "tidalWave")
        ok = any(before(p, "opErase(player,lava,lava)", "opNavigate(mage,ledge,lava)")
                 and "opForcedMove(mage,wyvern,crag,cliff)" in p for p in plans)
        assert ok, "the blizzard should cool the lava, and the mage wade out and wave it over the cliff"
        self._record(True, "Example 4: a blizzard cools the lava to rock; a wave from it washes the wyvern over the cliff")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_nine_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_a_flyer_just_hovers(self):
        """Pulled over the lava or blasted over the cliff while flying, it
        hovers: movers alone never win."""
        for kit in [("hook", "fireball"), ("taunt", "fireball"), ("hook", "taunt")]:
            assert not plans_with(*kit), kit
        self._record(True, "P3: a flyer pulled over the lava or pushed over the cliff just hovers")

    def test_property_p4_blizzard_two_roles(self):
        """The blizzard frosts the wings (on the crag) or makes rock of the lava
        (on the channel)."""
        frost = plans_with("blizzard", "taunt")
        cool = plans_with("blizzard", "tidalWave")
        assert frost and all("opCast(player,blizzard,wyvern)" in p for p in frost)
        assert cool and all("opErase(player,lava,lava)" in p for p in cool)
        self._record(True, "P4: the blizzard grounds the wyvern, or turns the lava into ground")

    def test_property_p5_nobody_falls(self):
        for kit in [("hook", "tidalWave"), ("taunt", "tidalWave"), ("blizzard", "tidalWave")]:
            for p in plans_with(*kit):
                assert not any(re.match(r"opExploit\(\w+,(player|mage),\w+,fell\)", o) for o in p), kit
        self._record(True, "P5: no winning plan washes a companion into the lava")


def run_tests():
    suite = WyvernRoostTest()
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
