"""Tests for the Soulfire Wraith level."""

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
POOL = ["blindingFlash", "taunt", "lightningFlash", "tidalWave", "fireball", "vortex", "hook"]
FINISHERS = ["taunt", "lightningFlash", "tidalWave", "fireball", "vortex", "hook"]

# The measured matrix: the flash and any finisher; or a revealer (a jolt, a wave)
# that lets a taunt set off the soulfire, and then finishes it.
WINNING = {frozenset(("blindingFlash", f)) for f in FINISHERS} | {
    frozenset(("lightningFlash", "taunt")), frozenset(("tidalWave", "taunt"))}


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
    """One plan as readable operators: opCast(player, taunt, wraith)."""
    out = []
    for op in plan:
        name = list(op.keys())[0]
        args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]
        out.append(f"{name}({', '.join(args)})")
    return out


def all_ops(plans):
    return {o for p in plans for o in op_strings(p)}


class WraithTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_flash_then_jolt(self):
        self.assert_plan("win.", contains=[
            "opCast(player, blindingFlash, player)", "opProvoked(wraith, blinded, soulfire)",
            "opWindUp(wraith, soulfire, crypt)", "opBlow(wraith, soulfire, crypt, crypt)",
            "opGrant(wraith, wraith, exhausted)", "opExploit(mage, wraith, electrocuted, dead)"])

    def test_example_2_reveal_taunt_jolt(self):
        ops = all_ops(plans_with("lightningFlash", "taunt"))
        assert "opCast(player, lightningFlash, ossuary)" in ops, "the bolt flies through the crypt"
        assert "opProvoked(wraith, electrocuted, flinch)" in ops, ops
        assert "opProvoked(wraith, taunted, soulfire)" in ops, ops
        assert "opExploit(player, wraith, electrocuted, dead)" in ops, ops
        self._record(True, "Example 2: the bolt shows it; the taunt spends it; the second bolt ends it")

    def test_example_3_flash_then_hook_into_the_well(self):
        ops = all_ops(plans_with("hook", "blindingFlash"))
        assert "opRemove(wraith, wraith, flying)" in ops, ops
        assert "opForcedMove(player, wraith, crypt, well)" in ops, ops
        assert "opExploit(player, wraith, chasm, fell)" in ops, ops
        self._record(True, "Example 3: spent and sunk, it is hooked across the well and falls")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_the_measured_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_every_plan_spends_it_with_soulfire(self):
        for pair in [("blindingFlash", "vortex"), ("tidalWave", "taunt"), ("blindingFlash", "taunt")]:
            plans = plans_with(*pair)
            assert plans, pair
            for p in plans:
                ops = op_strings(p)
                assert "opBlow(wraith, soulfire, crypt, crypt)" in ops, f"{pair}: no soulfire"
                assert "opGrant(wraith, wraith, exhausted)" in ops, f"{pair}: not spent"
        self._record(True, "P3: every plan lets the soulfire land and spend the Wraith")

    def test_property_p4_the_flash_survives_the_blow(self):
        """A flasher standing in the crypt is disjoint when the soulfire lands: the blow
        spends the disjoint and passes through."""
        plans = plans_with("blindingFlash", "fireball")
        assert any("opRemove(wraith, player, disjoint)" in op_strings(p) for p in plans),             "the flasher should be in the crypt, disjoint, when the blow lands"
        self._record(True, "P4: the flash's disjoint lets its caster stand in the soulfire")

    def test_property_p5_revealing_is_not_spending(self):
        """A jolt and a wave only show it: without a taunt or a flash it is never spent.
        Fire alone does nothing lasting."""
        assert not plans_with("lightningFlash", "tidalWave")
        assert not plans_with("fireball", "taunt")
        self._record(True, "P5: a reveal without the soulfire, or fire on it, wins nothing")


def run_tests():
    suite = WraithTest()
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
