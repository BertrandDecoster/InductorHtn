"""Tests for the Shellback level."""

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
POOL = ["fireball", "tidalWave", "hook", "taunt", "blizzard", "lightningFlash", "turnToMist", "vortex"]

# The measured matrix.
WINNING = {
    frozenset(p) for p in [
        # curl and roll: the partner pops the shield; fireball burns it and blasts it off
        ("fireball", "tidalWave"), ("fireball", "taunt"), ("fireball", "lightningFlash"),
        # taunt and strike: taunt pops the shield and makes it snap; the partner strikes its head
        ("taunt", "blizzard"), ("taunt", "lightningFlash"),
        # mist and roll: for a moment no shield, no weight; the partner pushes or pulls it in
        ("turnToMist", "fireball"), ("turnToMist", "tidalWave"), ("turnToMist", "hook"),
        ("turnToMist", "taunt"), ("turnToMist", "vortex"),
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


def op_strings(plan):
    """One plan as readable operators: opCast(player, taunt, shellback)."""
    out = []
    for op in plan:
        name = list(op.keys())[0]
        args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]
        out.append(f"{name}({', '.join(args)})")
    return out


def all_ops(plans):
    return {o for p in plans for o in op_strings(p)}


class ShellbackTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_pop_then_fireball(self):
        self.assert_plan("win.", contains=[
            "opCast(player, taunt, shellback)",
            "opReact(player, shellback, shielded, taunted, absorb)",
            "opCast(mage, fireball, shellback)", "opProvoked(shellback, burning, withdraw)",
            "opRemove(shellback, shellback, heavy)",
            "opForcedMove(mage, shellback, causeway, chasm)",
            "opExploit(mage, shellback, chasm, fell)"])

    def test_example_2_mist_then_hook_across(self):
        ops = all_ops(plans_with("hook", "turnToMist"))
        assert "opCast(mage, turnToMist, shellback)" in ops, ops
        assert "opForcedMove(player, shellback, causeway, chasm)" in ops, ops
        self._record(True, "Example 2: the mist lifts its weight; the hook from the islet drags it into the chasm")

    def test_example_3_taunt_then_freeze(self):
        ops = all_ops(plans_with("taunt", "blizzard"))
        assert "opProvoked(shellback, taunted, snap)" in ops and "opGrant(shellback, shellback, exhausted)" in ops
        assert "opExploit(mage, shellback, chilled, dead)" in ops, ops
        self._record(True, "Example 3: the second taunt makes it snap and spend itself; the blizzard stops it")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_the_measured_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_the_shield_eats_the_first_blow(self):
        """Without the mist, every winning plan loses one hostile tag to the shield first."""
        for pair in [("fireball", "taunt"), ("tidalWave", "fireball"), ("taunt", "blizzard")]:
            for p in plans_with(*pair):
                assert any(o.startswith("opReact(") and "shielded" in o and "absorb" in o
                           for o in op_strings(p)), f"{pair}: no shield popped"
        self._record(True, "P3: the shield always eats the first hostile tag")

    def test_property_p4_heavy_it_does_not_move(self):
        """Heavy and shielded, it holds: a hook pops no shield, so fireball's one fire is
        lost on it; frost undoes fire (thaw); and without fire or mist nothing moves it."""
        assert not plans_with("fireball", "hook")
        assert not plans_with("fireball", "blizzard")
        assert not plans_with("vortex", "hook")
        self._record(True, "P4: weight and shield hold unless burned or misted")


def run_tests():
    suite = ShellbackTest()
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
