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
POOL = ["tidalWave", "fireball", "hook", "taunt", "vortex", "lightningFlash"]

# The measured matrix (htn_components combos): these pairs win, nothing else does.
WINNING = {
    frozenset(("lightningFlash", p)) for p in ["tidalWave", "fireball", "hook", "taunt", "vortex"]
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
        plans = plans_with("tidalWave", "lightningFlash")
        ops = text_of(plans)
        assert plans, "a wave, then one flash through the hall, should take both"
        line = [p for p in plans if "opForcedMove" not in json.dumps(p)]
        assert line, "a plan soaks the drone where it stands"
        s = text_of(line)
        assert "opExploit(mage, drone, electrocuted, dead)" in s
        assert "opExploit(mage, engine, electrocuted, dead)" in s
        self._record(True, "Example 1: soak the drone, then one flash through the hall takes both")

    def test_example_2_into_the_flood(self):
        plans = plans_with("hook", "lightningFlash")
        ops = text_of(plans)
        assert plans, "a hook from the nave, then one flash, should take both"
        assert "opCast(player, hook, drone)" in ops
        assert "opForcedMove(player, drone, hall, nave)" in ops, "dragged into the flooded nave"
        assert "opExploit(mage, drone, electrocuted, dead)" in ops
        self._record(True, "Example 2: drag the drone into the flood, one flash through the nave")

    def test_example_3_the_pit(self):
        plans = plans_with("fireball", "lightningFlash")
        ops = text_of(plans)
        assert plans and "opForcedMove(player, drone, hall, pit)" in ops and "gallery" in ops
        self._record(True, "Example 3: a fireball from the gallery knocks the drone into the pit")

    def test_example_4_default_kit(self):
        """The default kit: the wave soaks (or washes) the drone, one flash takes both."""
        self.assert_plan("win.", contains=[
            "opCast(player, tidalWave, player)", "opCast(mage, lightningFlash, engine)",
            "opExploit(mage, engine, electrocuted, dead)"])

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_five_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_one_bolt(self):
        """Every winning plan casts exactly one jolt: the mana buys one."""
        for a, b in [tuple(p) for p in WINNING]:
            for plan in plans_with(a, b):
                s = json.dumps(plan)
                bolts = s.count('"lightningFlash"')
                assert bolts == 1, f"{a}+{b}: {bolts} jolts in {s}"
        self._record(True, "P3: every winning plan spends exactly one bolt")

    def test_property_p4_wrong_order_loses(self):
        """With a hook and the flash: jolting the drone first, or the engine
        before the drone is in the flood, loses."""
        assert plans_with("hook", "lightningFlash")
        assert not plans_with("hook", "lightningFlash", "neutralize(drone), neutralize(engine).")
        assert not plans_with("hook", "lightningFlash", "neutralize(engine), neutralize(drone).")
        self._record(True, "P4: jolting before the drone is wet and on the line loses")

    def test_property_p5_each_hand_matters(self):
        assert plans_with("lightningFlash", "vortex") and plans_with("taunt", "lightningFlash")
        self._record(True, "P5: the pairs win whichever companion holds which half")

    def test_property_p6_fire_does_not_soak(self):
        """A fireball into the flood arrives dry (the water puts the fire out):
        with a fireball, the drone only ever goes into the pit."""
        plans = plans_with("fireball", "lightningFlash")
        assert plans and all("pit" in json.dumps(p) for p in plans)
        self._record(True, "P6: fire and water cancel; the fireball's only road is the pit")


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
