"""Tests for the Powder Keg level (crowd control)."""

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
POOL = ["gust", "tidalWave", "magnetize", "taunt", "provoke", "flameWall", "fireball"]

# The measured matrix: a mover (the keg down, or the crowd up) and a fire.
MOVERS = ["gust", "tidalWave", "magnetize", "taunt", "provoke"]
FIRES = ["flameWall", "fireball"]
WINNING = {frozenset((m, f)) for m in MOVERS for f in FIRES}


def _solutions(planner, goal):
    error, result = planner.FindAllPlansCustomVariables(goal)
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    return solutions


def plans_with(player, mage):
    """All winning plans with the player knowing `player` and the mage `mage`, on a fresh
    planner (a failed search locks the rule set)."""
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^knows\((player|mage), \w+\)\.\n", "", text, flags=re.M)
    planner = HtnPlanner(False)
    planner.SetMemoryBudget(256 * 1024 * 1024)
    loader = ComponentLoader(planner, ROOT, warn=lambda m: None)
    loader.load("abilities/goals/neutralize")
    loader.load("abilities/primitives/ab_catalog")
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n"
    assert planner.HtnCompileCustomVariables(text + kit) is None
    return _solutions(planner, "win.")


def ops_text(plans):
    return " ".join(json.dumps(p) for p in plans)


def op_list(plan):
    """[(name, [args])] for one plan."""
    out = []
    for op in plan:
        name = list(op.keys())[0]
        out.append((name, [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]))
    return out


class PowderKegTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_roll_the_keg_down_then_light_it(self):
        self.assert_plan("win.", contains=[
            "opCast(player, gust, keg)", "opForcedMove(player, keg, ramp, grove)",
            "opCast(mage, flameWall, grove)", "opReact(mage, t1, wet, burning, steam)",
            "opReact(mage, keg, oiled, burning, blaze)", "opExploit(mage, t1, burning, dead)",
            "opExploit(mage, t3, burning, dead)"])

    def test_example_2_drag_the_crowd_up_the_ramp(self):
        plans = plans_with("provoke", "fireball")
        ops = [op_list(p) for p in plans]
        up = [p for p in ops if ("opForcedMove", ["player", "t1", "grove", "ramp"]) in p]
        assert up, "provoke from the ramp should drag the grove up to the keg"
        assert ("opCast", ["mage", "fireball", "ramp"]) in up[0]
        self._record(True, "Example 2: provoke drags the crowd round the keg; one fireball there")

    def test_example_3_drag_the_keg_in(self):
        plans = plans_with("magnetize", "flameWall")
        ops = [op_list(p) for p in plans]
        assert any(("opForcedMove", ["player", "keg", "ramp", "grove"]) in p for p in ops)
        self._record(True, "Example 3: magnetize from the grove hooks the keg in; flameWall lights it")

    def test_example_4_trap_fire_alone(self):
        assert not plans_with("flameWall", "fireball"), "fire without a gathered keg only steams"
        assert not plans_with("gust", "provoke"), "two movers, nothing to light"
        self._record(True, "Example 4: two fires, or two movers, leave the crowd standing")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_ten_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_each_hand_matters(self):
        assert plans_with("fireball", "tidalWave") and plans_with("flameWall", "taunt")
        self._record(True, "P3: the pairs win whichever companion holds which half")

    def test_property_p4_one_blaze_takes_the_crowd(self):
        """Every winning plan has one blaze, and every treant dies of it (after it)."""
        for a, b in [tuple(p) for p in WINNING]:
            for plan in plans_with(a, b):
                ops = op_list(plan)
                blaze = [i for i, (n, args) in enumerate(ops) if n == "opReact" and args[-1] == "blaze"]
                deaths = [i for i, (n, args) in enumerate(ops) if n == "opExploit" and args[-1] == "dead"]
                assert len(blaze) == 1 and len(deaths) == 3 and min(deaths) > blaze[0], f"{a}+{b}"
        self._record(True, "P4: one blaze, and all three treants burn in it")


def run_tests():
    suite = PowderKegTest()
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
