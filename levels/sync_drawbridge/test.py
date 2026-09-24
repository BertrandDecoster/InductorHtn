"""Tests for the Sync: Drawbridge level."""

import functools
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
CROSS = ["blink", "lightningFlash"]
THROW = ["fireball", "tidalWave", "hook", "vortex", "shieldBash"]
POOL = CROSS + THROW

# The measured matrix: each crossing skill with each thrower.
WINNING = {frozenset((a, b)) for a in CROSS for b in THROW}


@functools.lru_cache(maxsize=None)
def plans_with(player, mage, porter=True):
    """All winning plans (lists of (operator, args)) with the player knowing `player` and
    the mage `mage` (and the porter its mist, unless `porter` is False), on a fresh
    planner (a failed search locks the rule set)."""
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^knows\((player|mage), \w+\)\.\n", "", text, flags=re.M)
    if not porter:
        text = text.replace("knows(porter, turnToMist).\n", "")
    planner = HtnPlanner(False)
    planner.SetMemoryBudget(256 * 1024 * 1024)
    loader = ComponentLoader(planner, ROOT, warn=lambda m: None)
    for dep in Manifest.load(os.path.join(HERE, "manifest.json")).dependencies:
        loader.load(dep)
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n"
    assert planner.HtnCompileCustomVariables(text + kit) is None
    error, result = planner.FindAllPlansCustomVariables("win.")
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    plans = []
    for sol in solutions:
        plan = []
        for op in sol:
            name = list(op.keys())[0]
            plan.append((name, tuple(list(a.keys())[0] if isinstance(a, dict) else str(a)
                                     for a in op[name])))
        plans.append(plan)
    return plans


def has(plans, name, *args):
    return any((name, tuple(args)) in plan for plan in plans)


def casts(plan):
    return [args for name, args in plan if name == "opCast"]


class SyncDrawbridgeTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/strategies/passage", reset_first=False)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_blink_over_mist_then_fireball(self):
        self.assert_plan("win.", contains=[
            "opTeleport(player, dock, pier)", "opStepOn(player, player, winch)",
            "opOpen(player, drawbridge)", "opNavigate(porter, dock, pier)",
            "opCast(porter, turnToMist, sentinel)", "opRemove(porter, sentinel, heavy)",
            "opCast(mage, fireball, sentinel)", "opKnock(mage, sentinel, cliff)",
            "opExploit(mage, sentinel, chasm, fell)"])

    def test_example_2_flash_over_mist_then_hook_it_across_the_gap(self):
        plans = plans_with("lightningFlash", "hook")
        assert has(plans, "opDash", "player", "dock", "pier"), plans[:1]
        assert has(plans, "opNavigate", "mage", "pier", "overlook")
        assert has(plans, "opFall", "mage", "sentinel", "ledge", "overlook")
        assert has(plans, "opExploit", "mage", "sentinel", "gap", "fell")
        self._record(True, "Example 2: the flash lowers the bridge; misted, the hook drags the "
                           "sentinel into the gap below the overlook")

    def test_example_3_soak_then_jolt_no_mist(self):
        plans = plans_with("tidalWave", "lightningFlash")
        short = [p for p in plans if ("opExploit", ("mage", "sentinel", "electrocuted", "dead")) in p]
        assert short, plans[:1]
        assert all(c[1] != "turnToMist" for p in short for c in casts(p))
        self._record(True, "Example 3: the mage flashes over; the wave soaks the sentinel, the "
                           "mage's second flash shorts it")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_the_measured_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_either_seat(self):
        assert plans_with("hook", "blink") and plans_with("blink", "hook")
        self._record(True, "P3: a pair wins whichever companion holds which half")

    def test_property_p4_the_throw_is_the_cast_right_after_the_mist(self):
        """Every throw rides the porter's moment: the cast after the mist is
        the throw, and without the porter only the short circuit is left."""
        for thrower in THROW:
            for plan in plans_with("blink", thrower):
                cs = casts(plan)
                i = cs.index(("porter", "turnToMist", "sentinel"))
                assert cs[i + 1][1] == thrower, (thrower, cs)
        without = {t for t in THROW if plans_with("blink", t, porter=False)}
        assert not without, without
        assert plans_with("lightningFlash", "tidalWave", porter=False)
        self._record(True, "P4: mist, then throw - back to back; the short needs no mist")

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
