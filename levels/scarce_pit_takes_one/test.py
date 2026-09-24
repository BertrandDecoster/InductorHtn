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
KNOCKERS = ["fireball", "tidalWave", "shieldBash", "vortex"]  # into the pit: either body
COLD = ["blizzard"]                                           # the beetle dies of the cold
JOLTS = ["lightningFlash"]                                    # the soaked drone dies
POOL = KNOCKERS + COLD + JOLTS

# The measured matrix (htn_components combos): these pairs win, nothing else does.
WINNING = (
    {frozenset((k, j)) for k in KNOCKERS for j in JOLTS}      # beetle in the pit, jolt the drone
    | {frozenset((k, c)) for k in KNOCKERS for c in COLD}     # ice the beetle, drone in the pit
    | {frozenset(("blizzard", "lightningFlash"))}             # no pit: jolt, then ice
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
    """The plans as operator strings, e.g. `opKnock(player, beetle, pit)`."""
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
            "opKnock(player, beetle, pit)", "opExploit(player, beetle, chasm, fell)",
            "opCast(mage, lightningFlash, drone)", "opExploit(mage, drone, electrocuted, dead)"],
            not_contains=["opKnock(player, drone, pit)"])

    def test_example_2_freeze_then_draw_the_drone(self):
        ops = text_of(plans_with("blizzard", "vortex"))
        assert "opExploit(player, beetle, chilled, dead)" in ops, ops
        assert "opReact(player, drone, wet, chilled, freeze)" in ops, ops
        assert "opKnock(mage, drone, pit)" in ops, ops
        self._record(True, "Example 2: the cold kills the beetle and freezes the drone; the vortex draws it in")

    def test_example_3_no_pit(self):
        plans = plans_with("blizzard", "lightningFlash")
        ops = text_of(plans)
        assert plans and "chasm" not in ops
        self._record(True, "Example 3: jolt the drone, then ice the beetle - the pit stays empty")

    def test_example_4_the_vortex_takes_the_nearer(self):
        """A vortex on the pit draws both: the beetle lands first and fills it;
        the drone is knocked onto the full pit, and stays."""
        ops = text_of(plans_with("vortex", "lightningFlash"))
        assert "opSink(player, beetle, pit)" in ops and "opKnock(player, drone, pit)" in ops, ops
        self._record(True, "Example 4: the vortex fills the pit with the beetle")

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
        assert not plans_with("fireball", "tidalWave")
        assert not plans_with("vortex", "shieldBash")
        self._record(True, "P3: the pit takes one body, never two")

    def test_property_p4_ice_before_the_jolt_loses(self):
        """The freeze dries the soaked drone: a jolt after the ice only stuns."""
        assert not plans_with("blizzard", "lightningFlash",
                              "cast(player, blizzard, crossing), neutralize(drone).")
        self._record(True, "P4: ice first, and the drone can no longer be jolted to death")

    def test_property_p5_the_vortex_before_the_ice_loses(self):
        """A vortex first fills the pit with the beetle: the frozen drone is
        left standing."""
        assert not plans_with("vortex", "blizzard", "cast(player, vortex, pit), neutralize(drone).")
        assert plans_with("vortex", "blizzard")
        self._record(True, "P5: the vortex takes the beetle first; ice first, then the vortex")

    def test_property_p6_fire_dries_the_drone(self):
        """The fireball's flames fill the crossing: the soaked drone steams dry,
        and a jolt after it only stuns. Jolt first, then the fireball."""
        self.assert_state_after("cast(player, fireball, beetle), cast(mage, lightningFlash, drone).",
                                has=["tag(beetle,fell)", "tag(drone,stunned)"],
                                not_has=["tag(drone,dead)", "tag(drone,wet)"])
        ops = text_of(plans_with("fireball", "lightningFlash"))
        assert ops.index("opCast(mage, lightningFlash, drone)") < ops.index("opCast(player, fireball")
        self._record(True, "P6: fire before the jolt dries the drone; the jolt comes first")

    def test_property_p7_each_hand_matters(self):
        assert plans_with("lightningFlash", "fireball") and plans_with("tidalWave", "blizzard")
        self._record(True, "P7: the pairs win whichever companion holds which half")


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
