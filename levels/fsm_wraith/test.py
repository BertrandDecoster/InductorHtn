"""Tests for the Lunging Wraith level."""

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
POOL = ["provoke", "flashbang", "taunt", "chainLightning", "zap", "frostBolt", "flameWall"]
LURES = ["provoke", "flashbang"]
STRIKES = ["chainLightning", "zap", "frostBolt", "flameWall"]

# The measured matrix: an area lure and a strike, or a taunt after a chain.
WINNING = {frozenset((l, s)) for l in LURES for s in STRIKES} | {frozenset(("taunt", "chainLightning"))}


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
    """One plan as readable operators: opCast(player, provoke, crypt)."""
    out = []
    for op in plan:
        name = list(op.keys())[0]
        args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]
        out.append(f"{name}({', '.join(args)})")
    return out


def all_ops(plans):
    return {o for p in plans for o in op_strings(p)}


class WraithTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_provoke_then_jolt(self):
        self.assert_plan("win.", contains=[
            "opCast(player, provoke, crypt)", "opProvoked(wraith, taunted, lunge)",
            "opGrant(wraith, wraith, exhausted)", "opGrant(wraith, player, stunned)",
            "opExploit(mage, wraith, electrocuted, dead)"])

    def test_example_2_lure_into_fire(self):
        plans = plans_with("flameWall", "flashbang")
        trap = [p for p in plans
                if "opExploit(wraith, wraith, burning, dead)" in op_strings(p)]
        assert trap, "the Wraith should lunge, spent, into flames laid where the lure stood"
        ops = op_strings(trap[0])
        lure = ops.index("opCast(mage, flashbang, crypt)")
        assert any(o.startswith("opSpill(player") for o in ops[:lure]), "the flames come first"
        self._record(True, "Example 2: flames laid first; the blinded Wraith lunges into them and burns")

    def test_example_3_shake_then_taunt(self):
        ops = all_ops(plans_with("taunt", "chainLightning"))
        assert "opProvoked(wraith, electrocuted, flinch)" in ops, ops
        assert "opCast(player, taunt, wraith)" in ops and "opExploit(mage, wraith, electrocuted, dead)" in ops
        self._record(True, "Example 3: the chain shakes it out of hiding; the taunt spends it; the chain ends it")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_the_measured_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_the_mist_hides_it_again(self):
        """Provoked from the mist, it lunges back into hiding: a frost bolt cannot be aimed
        at it, so every provoke+frostBolt plan lures it from elsewhere."""
        plans = plans_with("provoke", "frostBolt")
        assert plans
        for p in plans:
            assert "opDash(wraith, crypt, mist)" not in op_strings(p)
        plans = plans_with("provoke", "chainLightning")
        assert any("opDash(wraith, crypt, mist)" in op_strings(p) for p in plans), \
            "a chain (an area) still reaches it back in the mist"
        self._record(True, "P3: lured into the mist it hides again; only an area reaches it there")

    def test_property_p4_the_lure_is_stunned(self):
        """Whoever sets off the lunge is flattened, so the strike is always the other's."""
        for lure, strike in [("provoke", "zap"), ("flashbang", "frostBolt")]:
            for p in plans_with(lure, strike):
                ops = op_strings(p)
                assert "opGrant(wraith, player, stunned)" in ops, ops
                assert not any(o.startswith("opCast(player") for o in ops[ops.index(
                    "opGrant(wraith, player, stunned)"):]), "a stunned lure casts nothing more"
        self._record(True, "P4: the lure is stunned by the lunge; the other companion strikes")


def run_tests():
    suite = WraithTest()
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
