"""Tests for the Short Circuit level (crowd control)."""

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
POOL = ["rainCall", "glaciate", "tidalWave", "provoke", "taunt", "chainLightning", "lightningFlash"]

# The measured matrix: the pairs that win, and nothing else does.
WINNING = {
    frozenset(p) for p in [
        ("rainCall", "lightningFlash"), ("glaciate", "lightningFlash"),
        ("tidalWave", "chainLightning"), ("tidalWave", "lightningFlash"),
        ("provoke", "chainLightning"), ("provoke", "lightningFlash"),
        ("taunt", "chainLightning"), ("taunt", "lightningFlash"),
    ]
}


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


class ShortCircuitTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_pull_into_the_sump_then_chain(self):
        self.assert_plan("win.", contains=[
            "opCast(player, provoke, cog1)", "opForcedMove(player, cog1, yard, sump)",
            "opForcedMove(player, cog2, yard, sump)", "opCast(mage, chainLightning, sump)",
            "opExploit(mage, cog1, electrocuted, dead)", "opExploit(mage, cog3, electrocuted, dead)"])

    def test_example_2_rain_then_a_line_bolt(self):
        plans = plans_with("rainCall", "lightningFlash")
        ops = ops_text(plans)
        assert plans and "puddle" in ops and "opDash" in ops and "forge" in ops, \
            "rain on the yard, then a flash from the gate down the hall to the forge"
        assert ops.count("electrocuted") >= 3
        self._record(True, "Example 2: rain on the yard, one flash down the hall takes all three")

    def test_example_3_wash_into_the_sump(self):
        plans = plans_with("tidalWave", "chainLightning")
        ops = ops_text(plans)
        assert plans and '"sump"' in ops and "opForcedMove" in ops
        self._record(True, "Example 3: the wave washes the yard into the sump; one chain there")

    def test_example_4_trap_one_room_per_chain(self):
        assert not plans_with("rainCall", "chainLightning"), "a chain on the yard should miss cog3"
        assert not plans_with("glaciate", "chainLightning")
        self._record(True, "Example 4: soaked where they stand, a chain covers one room only")

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
        assert plans_with("chainLightning", "provoke") and plans_with("lightningFlash", "rainCall")
        self._record(True, "P3: the pairs win whichever companion holds which half")

    def test_property_p4_one_bolt(self):
        """Every winning plan casts exactly one bolt."""
        for a, b in [tuple(p) for p in WINNING]:
            for plan in plans_with(a, b):
                bolts = [op for op in plan if "opCast" in op
                         and list(op["opCast"][1].keys())[0] in ("chainLightning", "lightningFlash")]
                assert len(bolts) == 1, f"{a}+{b}: {len(bolts)} bolts"
        self._record(True, "P4: every winning plan uses exactly one bolt")


def run_tests():
    suite = ShortCircuitTest()
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
