"""Tests for the Wall-Bang level."""

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
POOL = ["blindingFlash", "taunt", "hook", "vortex", "fireball", "tidalWave", "lightningFlash"]
FINISHERS = ["taunt", "hook", "vortex", "fireball", "tidalWave", "lightningFlash"]

# The measured matrix: the flash and any finisher; or a taunt and a partner who
# pulls the taunter clear of the charge (hook, vortex) and then drops the Ram.
WINNING = {frozenset(("blindingFlash", f)) for f in FINISHERS} | {
    frozenset(("taunt", "hook")), frozenset(("taunt", "vortex"))}


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
    """One plan as readable operators: opCast(player, taunt, ram)."""
    out = []
    for op in plan:
        name = list(op.keys())[0]
        args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]
        out.append(f"{name}({', '.join(args)})")
    return out


def all_ops(plans):
    return {o for p in plans for o in op_strings(p)}


class WallBangTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_flash_then_throw(self):
        self.assert_plan("win.", contains=[
            "opCast(player, blindingFlash, player)", "opProvoked(ram, blinded, ramCharge)",
            "opWindUp(ram, ramCharge, brink)", "opBlow(ram, ramCharge, brink, brink)",
            "opDash(ram, arena, brink)", "opExploit(ram, ram, pillar, staggered)",
            "opCast(mage, fireball, ram)", "opForcedMove(mage, ram, brink, ravine)",
            "opExploit(mage, ram, chasm, fell)"])

    def test_example_2_taunt_and_hook_clear(self):
        ops = all_ops(plans_with("taunt", "hook"))
        assert "opWindUp(ram, ramCharge, brink)" in ops, ops
        assert "opForcedMove(mage, player, brink, pen)" in ops, "the hook should pull the taunter clear"
        assert "opExploit(mage, ram, chasm, fell)" in ops, ops
        self._record(True, "Example 2: taunted, it charges; the hook pulls the taunter clear, then drops the Ram")

    def test_example_3_flash_then_jolt(self):
        ops = all_ops(plans_with("lightningFlash", "blindingFlash"))
        assert "opProvoked(ram, blinded, ramCharge)" in ops, ops
        assert "opExploit(player, ram, electrocuted, dead)" in ops, ops
        self._record(True, "Example 3: blinded, it crashes; the jolt stops its open heart")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_the_measured_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_every_plan_crashes_at_the_pillar(self):
        """Nothing wins without the wall-bang: every winning plan winds up the charge and
        staggers the Ram at the brink."""
        for pair in [("blindingFlash", "tidalWave"), ("taunt", "vortex"), ("blindingFlash", "hook")]:
            plans = plans_with(*pair)
            assert plans, pair
            for p in plans:
                ops = op_strings(p)
                assert "opWindUp(ram, ramCharge, brink)" in ops, f"{pair}: no charge"
                assert "opExploit(ram, ram, pillar, staggered)" in ops, f"{pair}: no crash"
        self._record(True, "P3: every plan provokes the charge and bangs the Ram into the pillar")

    def test_property_p4_a_push_is_no_rescue(self):
        """The charge is physical: nothing interrupts it. A partner who can only push
        (fireball, tidalWave) throws the taunter into the ravine: no plan."""
        assert not plans_with("taunt", "fireball")
        assert not plans_with("tidalWave", "taunt")
        self._record(True, "P4: pushing the taunter off the brink is no rescue")

    def test_property_p5_each_hand_matters(self):
        assert plans_with("hook", "taunt") and plans_with("fireball", "blindingFlash")
        self._record(True, "P5: the pairs win whichever companion holds which half")


def run_tests():
    suite = WallBangTest()
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
