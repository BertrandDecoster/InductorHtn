"""Tests for the Pit Takes One level."""

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
PUSHERS = ["fireball", "tidalWave", "vortex"]  # from the ledge / on the pit: either body
PULLERS = ["hook", "taunt"]                   # from the far side: only the beetle
COLD = ["blizzard"]                           # the beetle dies of the cold
JOLTS = ["lightningFlash"]                    # the soaked drone dies
POOL = PUSHERS + PULLERS + COLD + JOLTS

# The measured matrix (htn_components combos): these pairs win, nothing else does.
WINNING = (
    {frozenset((m, j)) for m in PUSHERS + PULLERS for j in JOLTS}    # beetle in the pit
    | {frozenset((c, p)) for c in COLD for p in PUSHERS}             # drone in the pit
    | {frozenset((c, j)) for c in COLD for j in JOLTS}               # no pit at all
)


def _solutions(planner, goal):
    error, result = planner.FindAllPlansCustomVariables(goal)
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    return solutions


def plans_with(player, mage, goal="win."):
    """All plans for `goal` with the player knowing `player` and the mage `mage`, on a
    fresh planner (a failed search locks the rule set)."""
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
    return _solutions(planner, goal)


def text_of(plans):
    """The plans as operator strings, e.g. `opCast(player, gust, drone)`."""
    out = []
    for plan in plans:
        for op in plan:
            name = list(op.keys())[0]
            args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]
            out.append(f"{name}({', '.join(args)})")
    return " ".join(out)


class PitTakesOneTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_beetle_first(self):
        """The default kit: a fireball knocks the beetle into the pit, the flash
        kills the drone."""
        self.assert_plan("win.", contains=[
            "opForcedMove(player, beetle, bridge, pit)", "opExploit(player, beetle, chasm, fell)",
            "opCast(mage, lightningFlash, drone)", "opExploit(mage, drone, electrocuted, dead)"],
            not_contains=["opForcedMove(player, drone, walk, pit)"])

    def test_example_2_pull_across(self):
        plans = plans_with("hook", "lightningFlash")
        ops = text_of(plans)
        assert plans and "opNavigate(player, bridge, far)" in ops
        assert "opForcedMove(player, beetle, bridge, pit)" in ops
        self._record(True, "Example 2: hook the beetle across the pit from the far side")

    def test_example_3_freeze_and_drop_the_drone(self):
        plans = plans_with("blizzard", "vortex")
        ops = text_of(plans)
        assert plans and "opExploit(player, beetle, chilled, dead)" in ops
        assert "opForcedMove(mage, drone, walk, pit)" in ops
        self._record(True, "Example 3: the cold kills the beetle; the vortex draws the drone in")

    def test_example_4_no_pit(self):
        plans = plans_with("blizzard", "lightningFlash")
        ops = text_of(plans)
        assert plans and "chasm" not in ops
        self._record(True, "Example 4: ice the beetle, jolt the drone - the pit stays empty")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_nine_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_the_pit_takes_one(self):
        """Nobody falls into the pit twice: after the first body it is filled."""
        for a, b in [tuple(p) for p in WINNING]:
            for plan in plans_with(a, b):
                s = text_of([plan])
                assert s.count(", chasm, fell)") <= 1, f"{a}+{b}: two falls in {s}"
        # Two movers: the second body finds the pit full.
        assert not plans_with("fireball", "tidalWave")
        assert not plans_with("hook", "vortex")
        self._record(True, "P3: the pit takes one body, never two")

    def test_property_p4_wrong_order_loses(self):
        """Drop the drone first (it is nearest) and the beetle can no longer be taken."""
        assert plans_with("fireball", "lightningFlash")
        assert not plans_with("fireball", "lightningFlash", "intoThePit(drone), neutralize(beetle).")
        assert plans_with("fireball", "lightningFlash", "intoThePit(beetle), neutralize(drone).")
        self._record(True, "P4: the drone in the pit first loses; the beetle first wins")

    def test_property_p5_each_hand_matters(self):
        assert plans_with("lightningFlash", "fireball") and plans_with("tidalWave", "blizzard")
        self._record(True, "P5: the pairs win whichever companion holds which half")


def run_tests():
    suite = PitTakesOneTest()
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
