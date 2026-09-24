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
POOL = ["net", "entangle", "sleepDart", "rainCall", "magnetize", "taunt", "gust", "collapse"]
GROUNDERS = ["net", "entangle", "sleepDart", "rainCall"]
DROPPERS = ["magnetize", "taunt", "gust", "collapse"]

# The measured matrix (htn_components combos): the pairs that win, and nothing else does.
WINNING = {
    frozenset((g, d)) for g in GROUNDERS for d in DROPPERS
    if (g, d) != ("sleepDart", "taunt")          # a taunt wakes a sleeper instead
}


def _op_text(op):
    name = list(op.keys())[0]
    args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]
    return f"{name}({','.join(args)})"


def plans_with(player, mage, goal="win.", extra=""):
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
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n" + extra
    assert planner.HtnCompileCustomVariables(text + kit) is None
    error, result = planner.FindAllPlansCustomVariables(goal)
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

    def test_example_1_net_then_pull_across_the_lava(self):
        plans = plans_with("net", "magnetize")
        ok = any(before(p, "opRemove(player,wyvern,flying)", "opForcedMove(mage,wyvern,crag,lava)")
                 and "opExploit(mage,wyvern,lava,fell)" in p for p in plans)
        assert ok, "the net should bring it down, then the hook drag it into the lava"
        self._record(True, "Example 1: net it, then hook it across the lava")

    def test_example_2_net_then_off_the_cliff(self):
        plans = plans_with("net", "gust")
        ok = any("opForcedMove(mage,wyvern,crag,cliff)" in p and "opExploit(mage,wyvern,chasm,fell)" in p
                 for p in plans)
        assert ok, "the mage should gust the grounded wyvern off the crag from the overlook"
        self._record(True, "Example 2: net it, then gust it off the crag into the cliff")

    def test_example_3_net_then_rockslide(self):
        plans = plans_with("net", "gust")
        ok = any(before(p, "opForcedMove(mage,boulder,overlook,crag)", "opSpill(mage,crag,chasm)")
                 and "opExploit(mage,wyvern,chasm,fell)" in p for p in plans)
        assert ok, "the boulder gusted onto the crag should break it under the wyvern"
        self._record(True, "Example 3: net it, then gust the boulder down to break the crag")

    def test_example_4_sleep_then_collapse(self):
        plans = plans_with("sleepDart", "collapse")
        ok = any(before(p, "opGrant(player,wyvern,asleep)", "opSpill(mage,crag,chasm)") for p in plans)
        assert ok, "the sleeping wyvern should fall with the collapsed crag"
        self._record(True, "Example 4: put it to sleep, then collapse the crag")

    def test_example_5_soak_then_taunt(self):
        plans = plans_with("rainCall", "taunt")
        ok = any("opReact(player,wyvern,flying,wet,sodden)" in p
                 and "opForcedMove(mage,wyvern,crag,lava)" in p for p in plans)
        assert ok, "soaked wings bring it down; the taunt drags it into the lava"
        self._record(True, "Example 5: soak its wings, then taunt it across the lava")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_fifteen_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_each_hand_matters(self):
        assert plans_with("collapse", "entangle") and plans_with("taunt", "net")
        self._record(True, "P3: the pairs win whichever companion holds which half")

    def test_property_p4_a_taunt_wakes_a_sleeper(self):
        assert not plans_with("sleepDart", "taunt") and not plans_with("taunt", "sleepDart")
        self._record(True, "P4: sleepDart and taunt lose - the taunt wakes it instead of pulling")

    def test_property_p5_grounded_before_it_falls(self):
        for g, d in [("net", "gust"), ("rainCall", "collapse"), ("entangle", "magnetize")]:
            for p in plans_with(g, d):
                fell = next(i for i, op in enumerate(p) if op.startswith("opExploit(") and "wyvern" in op)
                off = next(i for i, op in enumerate(p) if op == "opRemove(player,wyvern,flying)")
                assert off < fell, p
        self._record(True, "P5: in every plan the wyvern is brought down before a hazard takes it")

    def test_property_p6_aloft_it_hovers(self):
        """Pulled over the lava, pushed over the drop, or with the crag gone under
        it, a flying wyvern is still in the fight."""
        probe = ("hookIt :- if(), do(castFrom(mage, magnetize, wyvern, ledge), confirmStopped(wyvern)).\n"
                 "shoveIt :- if(), do(castFrom(mage, gust, wyvern, overlook), confirmStopped(wyvern)).\n"
                 "dropIt :- if(), do(cast(mage, collapse, wyvern), confirmStopped(wyvern)).\n")
        assert not plans_with("net", "magnetize", "hookIt.", probe)
        assert not plans_with("net", "gust", "shoveIt.", probe)
        assert not plans_with("net", "collapse", "dropIt.", probe)
        # ... and the same moves on a grounded wyvern do take it.
        assert plans_with("net", "magnetize", "grounded.",
                          probe + "grounded :- if(), do(cast(player, net, wyvern), hookIt).\n")
        self._record(True, "P6: while it flies, no hazard takes it")


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
