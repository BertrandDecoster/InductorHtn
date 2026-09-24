"""Tests for the Wall-Bang level."""

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
POOL = ["taunt", "provoke", "gust", "tidalWave", "concuss", "zap", "chainLightning"]
LURES = ["taunt", "provoke"]
FINISHERS = ["gust", "tidalWave", "concuss", "zap", "chainLightning"]

# The measured matrix: a lure and a finisher, and nothing else.
WINNING = {frozenset((l, f)) for l in LURES for f in FINISHERS}


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
    loader = ComponentLoader(planner, ROOT)
    loader.load("abilities/goals/neutralize")
    loader.load("abilities/primitives/ab_catalog")
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n"
    assert planner.HtnCompileCustomVariables(text + kit) is None
    return _solutions(planner, "win.")


def op_strings(plan):
    """One plan as readable operators: opCast(player, taunt, ram)."""
    out = []
    for op in plan:
        name = list(op.keys())[0]
        args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]
        out.append(f"{name}({', '.join(args)})")
    return out


def all_ops(plans):
    return {o for p in plans for o in op_strings(p)}


class WallBangTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_bang_then_throw(self):
        self.assert_plan("win.", contains=[
            "opCast(player, taunt, ram)", "opProvoked(ram, taunted, ramCharge)",
            "opDash(ram, arena, brink)", "opExploit(ram, ram, pillar, staggered)",
            "opCast(mage, gust, ram)", "opForcedMove(mage, ram, brink, ravine)",
            "opExploit(mage, ram, chasm, fell)"])

    def test_example_2_bang_then_shock(self):
        ops = all_ops(plans_with("zap", "provoke"))
        assert "opCast(mage, provoke, ram)" in ops and "opDash(ram, arena, brink)" in ops, ops
        assert "opExploit(player, ram, electrocuted, dead)" in ops, ops
        self._record(True, "Example 2: provoked from the brink, it crashes; the jolt stops it")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_the_measured_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_every_plan_crashes_at_the_pillar(self):
        """Nothing wins without the wall-bang: every winning plan staggers the Ram
        at the brink first."""
        for lure, fin in [("taunt", "gust"), ("provoke", "chainLightning"), ("taunt", "concuss")]:
            plans = plans_with(lure, fin)
            assert plans
            for p in plans:
                assert "opExploit(ram, ram, pillar, staggered)" in op_strings(p), \
                    f"{lure}+{fin}: a plan without the crash"
        self._record(True, "P3: every plan bangs the Ram into the pillar first")

    def test_property_p4_each_hand_matters(self):
        assert plans_with("gust", "taunt") and plans_with("chainLightning", "provoke")
        self._record(True, "P4: the pairs win whichever companion holds which half")


def run_tests():
    suite = WallBangTest()
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
