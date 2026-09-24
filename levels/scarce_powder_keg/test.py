"""Tests for the Powder Keg level."""

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
MOVERS = ["gust", "tidalWave", "taunt", "magnetize", "translocate"]
IGNITERS = ["flameWall", "zap", "lightningFlash"]
POOL = MOVERS + IGNITERS

# The measured matrix (htn_components combos): one mover and one igniter win,
# nothing else does.
WINNING = {frozenset((m, i)) for m in MOVERS for i in IGNITERS}


def _solutions(planner, goal):
    error, result = planner.FindAllPlansCustomVariables(goal)
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    return solutions


def plans_with(player, mage, goal="win."):
    """All plans for `goal` with the player knowing `player` and the mage `mage`, on a
    fresh planner (a failed search locks the rule set)."""
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
    return _solutions(planner, goal)


def text_of(plans):
    """The plans as operator strings, e.g. `opCast(player, gust, drone)`."""
    out = []
    for plan in plans:
        for op in plan:
            name = list(op.keys())[0]
            args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]
            out.append(f"{name}({', '.join(args)})")
    return " ".join(out)


class PowderKegTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_push_down_then_spark(self):
        """The default kit: gust from the landing, then a zap on the keg."""
        self.assert_plan("win.", contains=[
            "opNavigate(player, gate, landing)", "opForcedMove(player, lurker, stair, yard)",
            "opCast(mage, zap, keg)", "opExploit(keg, bruiser, blasted, dead)",
            "opExploit(keg, lurker, blasted, dead)"])

    def test_example_2_drag_down_then_burn(self):
        plans = plans_with("taunt", "flameWall")
        ops = text_of(plans)
        assert plans, "a taunt from the yard, then fire on the keg, should take both"
        assert "opForcedMove(player, lurker, stair, yard)" in ops
        assert "opProvoked(keg, burning, blast)" in ops
        assert "opExploit(keg, lurker, blasted, dead)" in ops
        self._record(True, "Example 2: drag the lurker into the yard, then set the keg alight")

    def test_example_3_the_well(self):
        plans = plans_with("tidalWave", "lightningFlash")
        ops = text_of(plans)
        assert plans and "opExploit(player, lurker, chasm, fell)" in ops
        assert "opExploit(keg, bruiser, blasted, dead)" in ops
        self._record(True, "Example 3: wash the lurker into the well, then flash the keg")

    def test_example_4_trade_places(self):
        plans = plans_with("translocate", "zap")
        ops = text_of(plans)
        assert plans and "opSwap(player, lurker, yard, stair)" in ops
        self._record(True, "Example 4: swap with the lurker, then spark the keg")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_mover_and_igniter_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_one_blast(self):
        """Every winning plan sets the keg off exactly once."""
        for m, i in [("gust", "zap"), ("taunt", "flameWall"), ("tidalWave", "lightningFlash")]:
            for plan in plans_with(m, i):
                s = json.dumps(plan)
                assert s.count('"opProvoked"') == 1, f"{m}+{i}: not one blast in {s}"
        self._record(True, "P3: the keg blows once per plan")

    def test_property_p4_wrong_order_loses(self):
        """Light the keg first: it is spent, and a puller can no longer take the lurker."""
        assert plans_with("taunt", "zap")
        assert not plans_with("taunt", "zap", "detonate(keg), neutralize(lurker).")
        assert not plans_with("taunt", "zap",
                              "detonate(keg), herd(lurker, yard), confirmStopped(lurker).")
        # Spent means spent: a second spark does nothing.
        assert not plans_with("gust", "zap", "detonate(keg), detonate(keg).")
        self._record(True, "P4: lighting the keg before the lurker is down loses")

    def test_property_p5_each_hand_matters(self):
        assert plans_with("zap", "gust") and plans_with("flameWall", "magnetize")
        self._record(True, "P5: the pairs win whichever companion holds which half")


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
