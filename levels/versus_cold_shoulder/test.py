"""Tests for the Cold Shoulder level."""

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
POOL = ["taunt", "provoke", "terrify", "roar", "charm", "magnetize", "translocate", "gust"]

# The measured matrix: the pairs that win, and nothing else does.
WINNING = {
    frozenset(p) for p in [
        # two moods: a fear first, then a drag
        ("terrify", "taunt"), ("terrify", "provoke"), ("roar", "taunt"), ("roar", "provoke"),
        # gather the imps, then one mood there
        ("gust", "taunt"), ("gust", "terrify"), ("gust", "roar"),
        ("magnetize", "taunt"), ("magnetize", "provoke"), ("magnetize", "terrify"),
        ("magnetize", "roar"),
        ("translocate", "taunt"), ("translocate", "provoke"), ("translocate", "terrify"),
        ("translocate", "roar"),
        # both imps brought to the troll, then charmed where it stands
        ("magnetize", "charm"), ("translocate", "charm"),
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


class ColdShoulderTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_fear_then_taunt(self):
        self.assert_plan("win.", contains=[
            "opCast(player, terrify, troll)", "opForcedMove(player, troll, cave, kiln)",
            "opProvoked(troll, feared, frost)", "opExploit(troll, imp2, chilled, frozen)",
            "opCast(mage, taunt, troll)", "opForcedMove(mage, troll, kiln, forge)",
            "opProvoked(troll, taunted, frost)", "opExploit(troll, imp1, chilled, frozen)"])

    def test_example_2_blow_one_imp_over_then_scare_the_troll(self):
        plans = plans_with("gust", "roar")
        ops = ops_text(plans)
        assert plans and "opForcedMove(player,imp1,forge,kiln)" in ops, ops[:400]
        assert "opForcedMove(mage,troll,cave,kiln)" in ops
        assert "opExploit(troll,imp1,chilled,frozen)" in ops and "opExploit(troll,imp2,chilled,frozen)" in ops
        self._record(True, "Example 2: gust the forge imp into the kiln, roar the troll in after it")

    def test_example_3_hook_both_then_charm(self):
        plans = plans_with("magnetize", "charm")
        ops = ops_text(plans)
        assert plans and "opForcedMove(player,imp1,forge,cave)" in ops and "opForcedMove(player,imp2,kiln,cave)" in ops
        assert "opProvoked(troll,charmed,frost)" in ops
        self._record(True, "Example 3: hook both imps into the cave, charm the troll")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_measured_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_one_breath_per_mood(self):
        """Two skills giving the same mood: the troll breathes once, one imp stays hot."""
        assert not plans_with("taunt", "provoke") and not plans_with("terrify", "roar")
        self._record(True, "P3: the same mood twice is one breath")

    def test_property_p4_charm_does_not_travel(self):
        """Charm makes it breathe where it stands; no other mood follows a charm."""
        assert not any(plans_with("charm", s) for s in ["taunt", "provoke", "terrify", "roar", "gust"])
        self._record(True, "P4: charm needs both imps brought into the cave")


def run_tests():
    suite = ColdShoulderTest()
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
