"""Tests for the Slipway level (elemental chemistry)."""

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
POOL = ["tidalWave", "lightningFlash", "turnToMist", "fireball", "hook", "vortex", "taunt"]
MOVERS = ["tidalWave", "fireball", "hook", "vortex", "taunt"]

# The measured matrix: the pairs that win, and nothing else does.
WINNING = (
    {frozenset(("tidalWave", "lightningFlash"))}                 # short it
    | {frozenset(("turnToMist", m)) for m in MOVERS}             # mist, then sink it
)


def _solutions(planner, goal):
    error, result = planner.FindAllPlansCustomVariables(goal)
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    return solutions


def names(plan):
    """A plan as a list of 'op(a, b, ...)' strings."""
    out = []
    for op in plan:
        n = list(op.keys())[0]
        args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[n]]
        out.append(f"{n}({', '.join(args)})")
    return out


def plans_with(player, mage, goal="win."):
    """All plans for `goal` with the player knowing `player` and the mage `mage`, on a
    fresh planner (a failed search locks the rule set), as lists of operator strings."""
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
    return [names(p) for p in _solutions(planner, goal)]


def some_plan_has(plans, *ops):
    return any(all(o in p for o in ops) for p in plans)


class SlipwayTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_soak_then_jolt(self):
        self.assert_plan("win.", contains=[
            "opCast(player, tidalWave, player)", "opGrant(player, crab, wet)",
            "opCast(mage, lightningFlash, crab)", "opExploit(mage, crab, electrocuted, dead)"])

    def test_example_2_mist_then_hook_across_the_dock(self):
        plans = plans_with("turnToMist", "hook")
        assert some_plan_has(plans, "opRemove(player, crab, heavy)",
                             "opNavigate(mage, stairs, gantry)",
                             "opForcedMove(mage, crab, slipway, dock)",
                             "opExploit(mage, crab, deepWater, fell)")
        self._record(True, "Example 2: misted, then hooked across the dock from the gantry")

    def test_example_3_mist_then_wash_it_in(self):
        plans = plans_with("tidalWave", "turnToMist")
        assert some_plan_has(plans, "opRemove(mage, crab, heavy)",
                             "opForcedMove(player, crab, slipway, dock)",
                             "opExploit(player, crab, deepWater, fell)")
        self._record(True, "Example 3: misted, then washed off the slipway into the dock")

    def test_example_4_fire_then_water_is_steam_not_soak(self):
        assert not plans_with("fireball", "tidalWave")
        plan = plans_with("fireball", "tidalWave",
                          "cast(player, fireball, crab), castFrom(mage, tidalWave, mage, quay).")[0]
        assert "opReact(mage, crab, burning, wet, extinguish)" in plan
        assert "opGrant(mage, crab, wet)" not in plan
        self._record(True, "Example 4: fire, then water: the fire goes out, the crab stays dry")

    def test_example_5_a_dry_jolt_only_stuns(self):
        plan = plans_with("lightningFlash", "hook", "cast(player, lightningFlash, crab).")[0]
        assert "opExploit(player, crab, electrocuted, stunned)" in plan
        assert not plans_with("lightningFlash", "hook")
        self._record(True, "Example 5: a dry machine jolted is only stunned")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_six_pairs_win_in_either_hand(self):
        wins = {(a, b): bool(plans_with(a, b)) for a, b in itertools.permutations(POOL, 2)}
        found = {frozenset(k) for k, w in wins.items() if w}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        one_way = sorted(k for k, w in wins.items() if w != wins[(k[1], k[0])])
        assert not one_way, f"win in one order only: {one_way}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win, in either hand")

    def test_property_p3_the_mist_lasts_one_cast(self):
        """Any cast between the mist and the push, and the crab is heavy again."""
        plan = plans_with("turnToMist", "tidalWave",
                          "cast(player, turnToMist, crab), castFrom(mage, tidalWave, mage, stairs), "
                          "castFrom(mage, tidalWave, mage, quay).")[0]
        assert "opGrant(crab, crab, heavy)" in plan
        assert not any("opForcedMove(mage, crab" in o for o in plan)
        self._record(True, "P3: a wasted cast after the mist, and the crab is heavy again")

    def test_property_p4_heavy_stops_every_mover(self):
        """Without the mist, no mover shifts it: a hook drags the caster to it instead."""
        plan = plans_with("hook", "vortex", "castFrom(player, hook, crab, gantry).")[0]
        assert "opDash(player, gantry, slipway)" in plan
        assert not any(o.startswith("opForcedMove") for o in plan)
        assert not plans_with("hook", "vortex") and not plans_with("fireball", "taunt")
        self._record(True, "P4: the hook on the heavy crab pulls the caster to it")


def run_tests():
    suite = SlipwayTest()
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
