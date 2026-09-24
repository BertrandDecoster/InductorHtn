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
POOL = ["fireball", "flameWall", "tidalWave", "magnetize", "taunt", "frostBolt", "zap"]

# The measured matrix.
WINNING = {
    frozenset(p) for p in [
        # curl and roll: fireball burns and blasts it off; the partner pops the shield
        ("fireball", "tidalWave"), ("fireball", "magnetize"), ("fireball", "taunt"),
        ("fireball", "frostBolt"), ("fireball", "zap"),
        # curl and roll: flameWall burns; the partner pops the shield and rolls it
        ("flameWall", "tidalWave"), ("flameWall", "magnetize"),
        # taunt and freeze
        ("taunt", "frostBolt"),
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
    """One plan as readable operators: opCast(player, zap, shellback)."""
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
            "opCast(player, zap, shellback)", "opReact(player, shellback, shielded, electrocuted, absorb)",
            "opCast(mage, fireball, shellback)", "opProvoked(shellback, burning, withdraw)",
            "opGrant(shellback, shellback, curled)", "opForcedMove(mage, shellback, causeway, chasm)",
            "opExploit(mage, shellback, chasm, fell)"])

    def test_example_2_hook_the_rolled_shell_across(self):
        ops = all_ops(plans_with("flameWall", "magnetize"))
        assert "opReact(mage, shellback, shielded, slowed, absorb)" in ops, ops
        assert "opProvoked(shellback, burning, withdraw)" in ops
        assert "opForcedMove(mage, shellback, causeway, chasm)" in ops
        self._record(True, "Example 2: the hook pops the shield; flames curl it; the hook drags it into the chasm")

    def test_example_3_taunt_then_freeze(self):
        ops = all_ops(plans_with("taunt", "frostBolt"))
        assert "opProvoked(shellback, taunted, snap)" in ops and "opGrant(shellback, shellback, exhausted)" in ops
        assert "opExploit(mage, shellback, chilled, frozen)" in ops
        self._record(True, "Example 3: the taunt spends it; the frost bolt freezes it")

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
        """Every winning plan loses one hostile tag to the shield first."""
        for pair in [("fireball", "taunt"), ("flameWall", "tidalWave"), ("taunt", "frostBolt")]:
            for p in plans_with(*pair):
                assert any(o.startswith("opReact(") and "shielded" in o and "absorb" in o
                           for o in op_strings(p)), f"{pair}: no shield popped"
        self._record(True, "P3: the shield always eats the first hostile tag")

    def test_property_p4_curled_it_takes_no_tags(self):
        """Once curled it is invulnerable: after flameWall, a taunt cannot pull it into the chasm
        from the islet, and frost cannot land. (fireball wins with either, by its own blast.)"""
        assert not plans_with("flameWall", "taunt")
        assert not plans_with("flameWall", "frostBolt")
        self._record(True, "P4: curled, it refuses taunts and frost; only a push or a hook rolls it")


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
