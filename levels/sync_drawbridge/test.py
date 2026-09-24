"""Tests for the Sync: Drawbridge level."""

import itertools
import json
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite
from indhtnpy import HtnPlanner
from htn_components.loader import ComponentLoader
from htn_components.manifest import Manifest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../.."))
CROSS = ["pounce", "charge", "shadowStep", "translocate"]
JOB = ["gust", "magnetize", "taunt", "zap"]
POOL = CROSS + JOB

# The measured matrix: every crossing skill with every job skill, and nothing else.
WINNING = {frozenset((a, b)) for a in CROSS for b in JOB}


def _solutions(planner, goal):
    error, result = planner.FindAllPlansCustomVariables(goal)
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    return solutions


def plans_with(player, mage, porter=True):
    """All winning plans with the player knowing `player` and the mage `mage` (and the
    porter its rain, unless `porter` is False), on a fresh planner (a failed search locks
    the rule set)."""
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^knows\((player|mage), \w+\)\.\n", "", text, flags=re.M)
    if not porter:
        text = text.replace("knows(porter, rainCall).\n", "")
    planner = HtnPlanner(False)
    planner.SetMemoryBudget(256 * 1024 * 1024)
    loader = ComponentLoader(planner, ROOT, warn=lambda m: None)
    for dep in Manifest.load(os.path.join(HERE, "manifest.json")).dependencies:
        loader.load(dep)
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n"
    assert planner.HtnCompileCustomVariables(text + kit) is None
    return _solutions(planner, "win.")


def ops(plans):
    return " ".join(json.dumps(p) for p in plans).replace(" ", "")


def op(name, *args):
    return json.dumps({name: [{a: []} for a in args]}).replace(" ", "")


class SyncDrawbridgeTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/strategies/passage", reset_first=False)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_pounce_over_then_gust_it_off(self):
        self.assert_plan("win.", contains=[
            "opDash(player, dock, pier)", "opOpen(player, drawbridge)",
            "opNavigate(mage, drawbridge, pier)", "opForcedMove(mage, sentinel, ledge, cliff)",
            "opExploit(mage, sentinel, chasm, fell)"])

    def test_example_2_swap_over_then_taunt_it_across_the_cliff(self):
        text = ops(plans_with("translocate", "taunt"))
        assert op("opSwap", "player", "barrel", "dock", "pier") in text, text[:400]
        assert op("opNavigate", "mage", "stair", "overlook") in text
        assert op("opForcedMove", "mage", "sentinel", "ledge", "cliff") in text
        self._record(True, "Example 2: the swap lowers the bridge; the taunt drags it into the cliff")

    def test_example_3_charge_over_rain_then_jolt(self):
        text = ops(plans_with("zap", "charge"))
        assert op("opDash", "mage", "dock", "pier") in text
        assert op("opCast", "porter", "rainCall", "sentinel") in text
        assert op("opExploit", "player", "sentinel", "electrocuted", "dead") in text
        self._record(True, "Example 3: the porter soaks it, the player's jolt shorts it")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_sixteen_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_either_seat(self):
        assert plans_with("magnetize", "shadowStep") and plans_with("shadowStep", "magnetize")
        self._record(True, "P3: a pair wins whichever companion holds which half")

    def test_property_p4_zap_needs_the_porter(self):
        """Without the porter's rain, a jolt only stuns the machine."""
        assert plans_with("pounce", "zap"), "with the porter, pounce + zap wins"
        assert not plans_with("pounce", "zap", porter=False)
        self._record(True, "P4: pounce + zap wins only with the porter's rain")

    def test_property_p5_the_bridge_is_up_until_someone_crosses(self):
        self.assert_query("canReach(mage, dock, pier).", min_solutions=0, max_solutions=0)
        self.assert_state_after("lowerBridge.", has=["open(drawbridge)"])
        self._record(True, "P5: nobody walks over until the winch is worked from the pier")


def run_tests():
    suite = SyncDrawbridgeTest()
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
