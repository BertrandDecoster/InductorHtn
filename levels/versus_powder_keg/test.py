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
POOL = ["taunt", "magnetize", "translocate", "gust", "concuss", "shieldBash", "charge", "thunderclap"]
MOVERS = ["taunt", "magnetize", "translocate", "gust", "concuss"]
STUNNERS = ["shieldBash", "charge", "thunderclap"]

# The measured matrix: every mover with every stunner, and nothing else.
WINNING = {frozenset((m, s)) for m in MOVERS for s in STUNNERS}


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


class PowderKegTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_taunt_the_mule_down_then_bash_it(self):
        self.assert_plan("win.", contains=[
            "opCast(player, taunt, mule)", "opForcedMove(player, mule, ridge, grove)",
            "opCast(mage, shieldBash, mule)", "opProvoked(mule, stunned, keg)",
            "opExploit(mule, ent, burning, dead)"])

    def test_example_2_swap_the_ent_up_to_the_keg(self):
        plans = plans_with("translocate", "charge")
        ops = ops_text(plans)
        assert plans and "opSwap(player,ent,ridge,grove)" in ops, ops[:400]
        assert "opCast(mage,charge,mule)" in ops and "opExploit(mule,ent,burning,dead)" in ops
        self._record(True, "Example 2: swap the ent up onto the ridge, charge the mule")

    def test_example_3_shove_it_off_the_crag(self):
        plans = plans_with("thunderclap", "concuss")
        ops = ops_text(plans)
        assert plans and "opNavigate(mage,ridge,crag)" in ops
        assert "opForcedMove(mage,mule,ridge,grove)" in ops
        assert "opCast(player,thunderclap,mule)" in ops
        self._record(True, "Example 3: shove the mule down from the crag, thunderclap it")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_measured_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_the_keg_blows_once(self):
        """Two stunners: the first knocks the mule down on the ridge, the keg is spent."""
        assert not plans_with("shieldBash", "charge") and not plans_with("thunderclap", "shieldBash")
        self._record(True, "P3: two stunners and no mover: the keg goes off on the ridge")

    def test_property_p4_nobody_burns_the_ent(self):
        """Two movers: keg and ent meet, and nothing knocks the mule down."""
        assert not plans_with("taunt", "gust") and not plans_with("magnetize", "translocate")
        self._record(True, "P4: two movers and no stun: nothing goes off")


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
