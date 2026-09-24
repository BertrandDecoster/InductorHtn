"""Tests for the Powder Gallery level."""

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
POOL = ["flameWall", "zap", "gust", "magnetize", "taunt", "shieldBash", "tidalWave", "rainCall"]

# The measured matrix (htn_components combos): the pairs that win, and nothing else does.
WINNING = {
    frozenset(p) for p in [
        ("flameWall", "gust"), ("flameWall", "magnetize"), ("flameWall", "taunt"),
        ("flameWall", "shieldBash"), ("flameWall", "tidalWave"),
        ("zap", "gust"), ("zap", "magnetize"), ("zap", "taunt"),
        ("zap", "shieldBash"), ("zap", "tidalWave"), ("zap", "rainCall"),
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


class PowderGalleryTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_open_then_pull_across(self):
        plans = plans_with("zap", "taunt")
        ok = any(before(p, "opSpill(keg,gallery,chasm)", "opForcedMove(mage,golem,nave,gallery)")
                 and "opExploit(mage,golem,chasm,fell)" in p for p in plans)
        assert ok, "the keg should open the gallery, then the taunt drag the golem into it"
        self._record(True, "Example 1: zap blows the keg, a taunt drags the golem into the new chasm")

    def test_example_2_floor_under_it(self):
        plans = plans_with("flameWall", "gust")
        ok = any(before(p, "opForcedMove(mage,golem,nave,gallery)", "opSpill(keg,gallery,chasm)")
                 and "opExploit(keg,golem,chasm,fell)" in p for p in plans)
        assert ok, "the golem should be pushed onto the powder floor, then the floor blown"
        self._record(True, "Example 2: gust the golem onto the keg's floor, then blow it")

    def test_example_3_bomb_to_it(self):
        plans = plans_with("flameWall", "gust")
        ok = any(before(p, "opForcedMove(mage,keg,gallery,nave)", "opSpill(keg,nave,chasm)")
                 and "opExploit(keg,golem,chasm,fell)" in p for p in plans)
        assert ok, "the keg should be pushed into the nave and blown there"
        self._record(True, "Example 3: gust the keg into the nave, then blow it under the golem")

    def test_example_4_short_it(self):
        plans = plans_with("rainCall", "zap")
        assert plans and all("opExploit(mage,golem,electrocuted,dead)" in p for p in plans)
        self._record(True, "Example 4: rain, then a jolt, short-circuits the golem")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_eleven_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_each_hand_matters(self):
        assert plans_with("gust", "flameWall") and plans_with("rainCall", "zap")
        self._record(True, "P3: the pairs win whichever companion holds which half")

    def test_property_p4_default_kit_three_ways(self):
        plans = plans_with("flameWall", "gust")
        assert len({" ".join(p) for p in plans}) >= 3, plans
        self._record(True, "P4: flameWall + gust wins three ways (open then drop, floor, bomb)")


def run_tests():
    suite = PowderGalleryTest()
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
