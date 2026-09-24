"""Tests for the One Bolt level."""

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
POOL = ["rainCall", "frostBolt", "tidalWave", "gust", "taunt", "magnetize",
        "lightningFlash", "chainLightning"]

# The measured matrix (htn_components combos): these pairs win, nothing else does.
WINNING = {
    frozenset(p) for p in [
        ("lightningFlash", "rainCall"), ("lightningFlash", "frostBolt"),
        ("lightningFlash", "tidalWave"), ("lightningFlash", "gust"),
        ("chainLightning", "tidalWave"), ("chainLightning", "gust"),
        ("chainLightning", "taunt"), ("chainLightning", "magnetize"),
    ]
}


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


class OneBoltTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_line_them_up(self):
        plans = plans_with("rainCall", "lightningFlash")
        ops = text_of(plans)
        assert plans, "rain, then one flash through the hall, should take both"
        assert ops.count("lightningFlash") == len(plans), "exactly one bolt per plan"
        assert "drone" in ops and "engine" in ops and "dead" in ops
        self._record(True, "Example 1: soak the drone, then one flash through the hall takes both")

    def test_example_2_into_the_flood(self):
        plans = plans_with("magnetize", "chainLightning")
        ops = text_of(plans)
        assert plans, "a hook from the nave, then one chain, should take both"
        assert "opCast(player, magnetize, drone)" in ops
        assert "opForcedMove(player, drone, hall, nave)" in ops, "dragged into the flooded nave"
        assert "opExploit(mage, drone, electrocuted, dead)" in ops
        self._record(True, "Example 2: drag the drone into the flood, one chain over the nave")

    def test_example_3_the_pit(self):
        plans = plans_with("tidalWave", "lightningFlash")
        ops = text_of(plans)
        assert plans and "pit" in ops and "gallery" in ops
        self._record(True, "Example 3: wave the drone into the pit from the gallery, flash the engine")

    def test_example_4_push_into_the_flood(self):
        """The default kit: gust drives the drone into the nave, one chain takes both."""
        self.assert_plan("win.", contains=[
            "opForcedMove(player, drone, hall, nave)", "opCast(mage, chainLightning, drone)",
            "opExploit(mage, engine, electrocuted, dead)", "opExploit(mage, drone, electrocuted, dead)"])

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_eight_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_one_bolt(self):
        """Every winning plan casts exactly one jolt: the mana buys one."""
        for a, b in [tuple(p) for p in WINNING]:
            for plan in plans_with(a, b):
                s = json.dumps(plan)
                bolts = s.count('"lightningFlash"') + s.count('"chainLightning"')
                assert bolts == 1, f"{a}+{b}: {bolts} jolts in {s}"
        self._record(True, "P3: every winning plan spends exactly one bolt")

    def test_property_p4_wrong_order_loses(self):
        """Soak the drone and jolt it, then the engine: the bolt is gone."""
        assert plans_with("rainCall", "lightningFlash")
        assert not plans_with("rainCall", "lightningFlash", "neutralize(drone), neutralize(engine).")
        # Jolt the engine first while the drone is dry: the drone is only stunned.
        assert not plans_with("rainCall", "lightningFlash", "neutralize(engine), neutralize(drone).")
        # Rain and a chain: the chain on the hall takes only the drone.
        assert not plans_with("rainCall", "chainLightning")
        self._record(True, "P4: jolting before both machines are wet and together loses")

    def test_property_p5_each_hand_matters(self):
        assert plans_with("lightningFlash", "rainCall") and plans_with("gust", "chainLightning")
        self._record(True, "P5: the pairs win whichever companion holds which half")


def run_tests():
    suite = OneBoltTest()
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
