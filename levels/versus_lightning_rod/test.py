"""Tests for the Lightning Rod level."""

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
POOL = ["rainCall", "tidalWave", "gust", "magnetize", "taunt", "provoke", "terrify", "roar"]

# The measured matrix: the pairs that win, and nothing else does.
WINNING = {
    frozenset(p) for p in [
        ("rainCall", "taunt"), ("rainCall", "provoke"), ("rainCall", "terrify"), ("rainCall", "roar"),
        ("tidalWave", "taunt"), ("tidalWave", "terrify"), ("tidalWave", "roar"),
        ("gust", "taunt"), ("gust", "terrify"), ("gust", "roar"),
        ("magnetize", "taunt"), ("magnetize", "terrify"), ("magnetize", "roar"),
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
    loader = ComponentLoader(planner, ROOT)
    loader.load("abilities/goals/neutralize")
    loader.load("abilities/primitives/ab_catalog")
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n"
    assert planner.HtnCompileCustomVariables(text + kit) is None
    return _solutions(planner, "win.")


def ops_text(plans):
    """Every operator of every plan, as `name(a,b,...)` strings joined by spaces."""
    out = []
    for plan in plans:
        for op in plan:
            name = list(op.keys())[0]
            args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]
            out.append(f"{name}({','.join(args)})")
    return " ".join(out)


class LightningRodTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_rain_then_taunt(self):
        self.assert_plan("win.", contains=[
            "opCast(player, rainCall, robot)", "opCast(mage, taunt, golem)",
            "opForcedMove(mage, golem, forge, hall)", "opProvoked(golem, taunted, discharge)",
            "opExploit(golem, robot, electrocuted, dead)"])

    def test_example_2_scare_it_down_the_sluice(self):
        plans = plans_with("gust", "terrify")
        ops = ops_text(plans)
        assert plans and "opForcedMove(player,robot,hall,fountain)" in ops, ops[:400]
        assert "opNavigate(mage,forge,chimney)" in ops, "the mage scares it from the chimney"
        assert "opExploit(golem,robot,electrocuted,dead)" in ops
        self._record(True, "Example 2: gust into the fountain, scare the golem down the sluice")

    def test_example_3_provoke_from_next_door(self):
        plans = plans_with("provoke", "rainCall")
        ops = ops_text(plans)
        assert plans and "opCast(player,provoke,golem)" in ops
        assert "opProvoked(golem,taunted,discharge)" in ops
        self._record(True, "Example 3: rain, then provoke from the hall")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_measured_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_a_dry_jolt_only_stuns(self):
        """Luring the golem onto a dry robot stuns it: not a win."""
        assert not plans_with("taunt", "provoke")
        self._record(True, "P3: two lures and no water: the robot is only stunned")

    def test_property_p4_provoke_cannot_follow_to_the_fountain(self):
        """Once the robot is in the fountain, provoke (melee, next door only) is out of reach."""
        assert not plans_with("gust", "provoke") and not plans_with("tidalWave", "provoke")
        self._record(True, "P4: provoke only works while the robot stays in the hall")


def run_tests():
    suite = LightningRodTest()
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
