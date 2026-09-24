"""Tests for the Drowned Knight level."""

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
POOL = ["turnToMist", "taunt", "tidalWave", "fireball", "vortex", "hook"]

# The measured matrix (htn_components combos): the pairs that win, and nothing else does.
WINNING = {
    frozenset(p) for p in [
        # mist, then move it into the moat with the very next cast
        ("turnToMist", "fireball"), ("turnToMist", "tidalWave"), ("turnToMist", "vortex"),
        ("turnToMist", "hook"), ("turnToMist", "taunt"),
        # put a friend in the lake, who taunts the heavy knight in after them
        ("taunt", "tidalWave"), ("taunt", "fireball"), ("taunt", "vortex"),
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


class DrownedKnightTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_bait_with_a_wave(self):
        plans = plans_with("tidalWave", "taunt")
        ok = any(before(p, "opForcedMove(player,mage,quay,lake)", "opCast(mage,taunt,knight)")
                 and "opDash(knight,keep,lake)" in p
                 and "opExploit(knight,knight,deepWater,fell)" in p for p in plans)
        assert ok, "the player should wash the mage into the lake, and the taunted knight leap in"
        self._record(True, "Example 1: a wave washes a friend into the lake; the taunted knight leaps in and sinks")

    def test_example_2_bait_with_a_vortex(self):
        plans = plans_with("vortex", "taunt")
        ok = any("opCast(player,vortex,lake)" in p and "opForcedMove(player,mage,quay,lake)" in p
                 and "opExploit(knight,knight,deepWater,fell)" in p for p in plans)
        assert ok, "a vortex on the lake should suck the mage in, and the taunted knight follow"
        self._record(True, "Example 2: a vortex sucks a friend into the lake; the taunted knight follows")

    def test_example_3_mist_then_push(self):
        plans = plans_with("turnToMist", "fireball")
        ok = any(before(p, "opCast(player,turnToMist,knight)", "opForcedMove(mage,knight,keep,moat)")
                 for p in plans)
        assert ok, "the player should turn the knight to mist, the mage blast it into the moat"
        self._record(True, "Example 3: mist the knight, fireball it off the keep into the moat")

    def test_example_4_mist_then_pull_across(self):
        plans = plans_with("turnToMist", "hook")
        ok = any("opNavigate(mage,gate,tower)" in p and "opForcedMove(mage,knight,keep,moat)" in p
                 for p in plans)
        assert ok, "the mage should hook the misted knight across the moat from the tower"
        self._record(True, "Example 4: mist the knight, hook it across the moat from the tower")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_eight_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_each_hand_matters(self):
        assert plans_with("taunt", "tidalWave") and plans_with("tidalWave", "taunt")
        assert plans_with("turnToMist", "hook") and plans_with("hook", "turnToMist")
        self._record(True, "P3: the pairs win whichever companion holds which half")

    def test_property_p4_misted_it_does_not_drown(self):
        plans = plans_with("turnToMist", "tidalWave")
        assert plans and not any("deepWater" in " ".join(p) for p in plans)
        self._record(True, "P4: once misted, only the moat takes the knight")

    def test_property_p5_heavy_it_cannot_be_moved(self):
        """Hooked while heavy, the knight drags the hooker onto the keep; a
        taunt from dry land only brings it over: neither drops it."""
        assert not plans_with("hook", "tidalWave") and not plans_with("hook", "taunt")
        self._record(True, "P5: heavy, the knight is neither hooked nor taunted into the moat")


def run_tests():
    suite = DrownedKnightTest()
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
