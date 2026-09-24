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
POOL = ["hook", "taunt", "tidalWave", "blizzard", "lightningFlash", "fireball", "shieldBash",
        "vortex"]

# The measured matrix (htn_components combos): the pairs that win, and nothing else does.
WINNING = {
    frozenset(p) for p in [
        # fetch it (a flyer crosses), then wash it into the fire
        ("hook", "tidalWave"), ("taunt", "tidalWave"),
        # ground it, then knock it off the cliff or drag it into the chasm
        ("blizzard", "fireball"), ("blizzard", "shieldBash"), ("blizzard", "vortex"),
        ("blizzard", "hook"), ("lightningFlash", "fireball"), ("lightningFlash", "shieldBash"),
        ("lightningFlash", "vortex"), ("lightningFlash", "hook"),
        # cool the lava channel, wade out, wave
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
    planner.SetMemoryBudget(512 * 1024 * 1024)
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

    def test_example_1_fetch_then_wash_into_the_lava(self):
        plans = plans_with("hook", "tidalWave")
        ok = any(before(p, "opForcedMove(player,wyvern,crag,ledge)", "opCast(mage,tidalWave,mage)")
                 and "opExploit(mage,wyvern,lava,fell)" in p for p in plans)
        assert ok, "the player should hook the flyer over the chasm, the mage wash it into the lava pool"
        self._record(True, "Example 1: hooked over the chasm, washed into the lava pool")

    def test_example_2_cool_the_lava_and_wade_out(self):
        plans = plans_with("blizzard", "tidalWave")
        ok = any(before(p, "opErase(player,flow,lava)", "opNavigate(mage,flow,crag)")
                 and "opKnock(mage,wyvern,cliff)" in p for p in plans)
        assert ok, "the blizzard should cool the channel, and the mage walk out and wave it off the cliff"
        self._record(True, "Example 2: the lava cooled to rock, a wave on the crag sends it over the cliff")

    def test_example_3_strike_then_drag(self):
        plans = plans_with("hook", "lightningFlash")
        ok = any(before(p, "opDash(mage,ledge,crag)", "opFall(player,wyvern,crag,ledge)")
                 for p in plans)
        assert ok, "the mage should strike the crag, the player drag the grounded wyvern into the chasm"
        self._record(True, "Example 3: struck on its crag, dragged into the chasm")

    def test_example_4_taunted_it_flies_over_the_lava(self):
        plans = plans_with("taunt", "tidalWave")
        ok = any(before(p, "opNavigate(wyvern,flow,ledge)", "opWindUp(wyvern,meteor,player)")
                 and "opKnock(mage,wyvern,lavaPool)" in p for p in plans)
        assert ok, "the taunted wyvern should fly over the lava, breathe fire, and be washed in"
        self._record(True, "Example 4: taunted, it flies over the lava, breathes fire, and is washed in")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_eleven_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_each_hand_matters(self):
        assert plans_with("blizzard", "vortex") and plans_with("vortex", "blizzard")
        assert plans_with("tidalWave", "taunt") and plans_with("taunt", "tidalWave")
        self._record(True, "P3: the pairs win whichever companion holds which half")

    def test_property_p4_flying_it_hovers(self):
        """Knocked over the cliff or dragged over the chasm while it flies, it
        simply hovers."""
        assert not plans_with("fireball", "vortex") and not plans_with("hook", "fireball")
        assert not plans_with("hook", "shieldBash")
        self._record(True, "P4: nothing drops the wyvern while its wings hold")

    def test_property_p5_grounded_it_will_not_cross_the_lava(self):
        """Frosted, it no longer flies, so a taunt cannot draw it over the lava;
        a wave from the ledge never reaches the crag."""
        assert not plans_with("taunt", "blizzard") and not plans_with("lightningFlash", "tidalWave")
        self._record(True, "P5: the grounded wyvern stays on its crag; the crag is reached by a leap or cooled rock")


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
