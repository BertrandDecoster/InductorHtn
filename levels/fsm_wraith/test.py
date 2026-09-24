"""Tests for the Soulfire Wraith level."""

import json
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite
from indhtnpy import HtnPlanner
from htn_components.loader import ComponentLoader
from htn_components.combos import run_combos

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../.."))
POOL = ["blindingFlash", "taunt", "tidalWave", "blizzard", "fireball", "vortex", "hook", "shieldBash"]

# The measured matrix (unordered pairs; each wins whichever companion holds which half).
WINNING = {
    frozenset(p) for p in [
        # flash and ...: the flash sets off the soulfire and passes through it; the partner drops it
        ("blindingFlash", "tidalWave"), ("blindingFlash", "fireball"), ("blindingFlash", "vortex"),
        ("blindingFlash", "hook"), ("blindingFlash", "shieldBash"),
        # ice first: its own flames melt the ice into the puddle that drowns it
        ("blindingFlash", "blizzard"), ("taunt", "blizzard"),
        # reveal and taunt: the revealer steps out, then knocks it into the well
        ("taunt", "tidalWave"), ("taunt", "fireball"),
    ]
}

_REPORT = []


def combos():
    """The combos report, computed once (every replan on a fresh planner)."""
    if not _REPORT:
        _REPORT.append(run_combos(HERE, ROOT))
    return _REPORT[0]


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
    error, result = planner.FindAllPlansCustomVariables("win.")
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    return solutions


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


class WraithTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_flash_then_wave_into_the_well(self):
        # (on a fresh planner with a larger memory budget: the window's answers are many)
        ops = all_ops(plans_with("blindingFlash", "tidalWave"))
        for o in ["opCast(player, blindingFlash, player)", "opProvoked(wraith, blinded, soulfire)",
                  "opBlow(wraith, soulfire, crypt, crypt)", "opRemove(wraith, player, disjoint)",
                  "opGrant(wraith, wraith, exhausted)", "opCast(mage, tidalWave, mage)",
                  "opExploit(mage, wraith, chasm, fell)"]:
            assert o in ops, o
        self._record(True, "Example 1: the flash sets off the soulfire and passes through it; the wave drops it")

    def test_example_2_ice_first_and_it_drowns(self):
        ops = all_ops(plans_with("taunt", "blizzard"))
        assert "opCast(mage, blizzard, crypt)" in ops and "opProvoked(wraith, chilled, flinch)" in ops, ops
        assert "opProvoked(wraith, taunted, soulfire)" in ops, ops
        assert "opReshape(wraith, crypt, iceSheet, puddle)" in ops, ops
        assert "opExploit(wraith, wraith, wet, dead)" in ops, ops
        self._record(True, "Example 2: the frost shows it; taunted, its own flames melt the ice and it drowns")

    def test_example_3_reveal_step_out_taunt(self):
        ops = all_ops(plans_with("taunt", "tidalWave"))
        assert "opProvoked(wraith, wet, flinch)" in ops and "opNavigate(mage, crypt, mist)" in ops, ops
        assert "opProvoked(wraith, taunted, soulfire)" in ops, ops
        self._record(True, "Example 3: the wave shows it, the waver steps out, the taunt spends it, the wave drops it")

    def test_example_4_flash_then_hook_across_the_well(self):
        ops = all_ops(plans_with("hook", "blindingFlash"))
        assert "opFall(player, wraith, crypt, balcony)" in ops, ops
        self._record(True, "Example 4: spent and wingless, it is hooked across the well from the balcony")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        report = combos()
        assert not report.singles_winning, f"a single skill wins: {report.singles_winning}"
        assert report.solo_plans == 0, f"{report.solo_plans} solo plans"
        self._record(True, "P1: no skill wins alone, even held by both companions; no solo plan")

    def test_property_p2_the_measured_pairs_win(self):
        report = combos()
        found = {frozenset(s for v in a.values() for s in v) for a in report.winning}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        assert len(report.winning) == 2 * len(WINNING), len(report.winning)
        assert len(report.methods) == 9 and not report.dead_skills, (report.methods, report.dead_skills)
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win ({len(report.winning)} of 64), "
                           "9 methods, no dead skill")

    def test_property_p3_the_soulfire_spends_it(self):
        for pair in [("taunt", "fireball"), ("vortex", "blindingFlash"), ("blizzard", "blindingFlash")]:
            for p in plans_with(*pair):
                ops = op_strings(p)
                assert "opBlow(wraith, soulfire, crypt, crypt)" in ops, pair
                assert "opGrant(wraith, wraith, exhausted)" in ops, pair
                assert not any(o.startswith("opInterrupt(") for o in ops), pair
        self._record(True, "P3: every plan lets the soulfire land and spend it; none interrupts it")

    def test_property_p4_revealing_is_not_spending(self):
        assert not plans_with("tidalWave", "fireball")
        assert not plans_with("blizzard", "fireball")
        assert not plans_with("taunt", "hook")
        self._record(True, "P4: a reveal alone never spends it; a taunt needs a reveal")

    def test_property_p5_the_crypt_sears_who_stays(self):
        """With the wave's reveal, the waver always steps out of the crypt before the taunt:
        whoever stays is silenced by the soulfire and finishes nothing."""
        for p in plans_with("tidalWave", "taunt"):
            ops = op_strings(p)
            assert "opNavigate(player, crypt, mist)" in ops, ops
            assert not any(o.endswith(", silenced)") and o.startswith("opGrant(wraith, player") for o in ops)
        self._record(True, "P5: the revealer leaves the crypt before the soulfire, or no plan")


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
