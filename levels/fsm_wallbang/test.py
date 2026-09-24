"""Tests for the Wall-Bang level."""

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
POOL = ["blindingFlash", "taunt", "hook", "vortex", "fireball", "tidalWave", "shieldBash"]

# The measured matrix: (player, mage) assignments. The player starts on the brink.
LURES = ["blindingFlash", "taunt"]
FINISHERS = ["fireball", "tidalWave", "vortex", "hook", "shieldBash"]
WINNING = ({(lure, f) for lure in LURES for f in FINISHERS}
           | {(survivor, lure) for lure in LURES for survivor in ("hook", "shieldBash")})

_REPORT = []


def combos():
    """The combos report, computed once (every replan on a fresh planner)."""
    if not _REPORT:
        _REPORT.append(run_combos(HERE, ROOT))
    return _REPORT[0]


def plans_with(player, mage, start=None):
    """All winning plans with the player knowing `player` and the mage `mage`, on a fresh
    planner (a failed search locks the rule set)."""
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^knows\((player|mage), \w+\)\.\n", "", text, flags=re.M)
    for who, area in (start or {}).items():
        text = re.sub(rf"^at\({who}, \w+\)\.", f"at({who}, {area}).", text, flags=re.M)
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

    def test_example_1_flash_crash_blast(self):
        self.assert_plan("win.", contains=[
            "opCast(player, blindingFlash, player)", "opProvoked(ram, blinded, ramCharge)",
            "opBlow(ram, ramCharge, brink, brink)", "opDash(ram, arena, brink)",
            "opGrant(ram, ram, staggered)", "opRemove(ram, ram, heavy)",
            "opCast(mage, fireball, ram)", "opExploit(mage, ram, chasm, fell)"])

    def test_example_2_taunt_then_hook_from_the_ledge(self):
        ops = all_ops(plans_with("taunt", "hook"))
        assert "opProvoked(ram, taunted, ramCharge)" in ops, ops
        assert "opNavigate(mage, gallery, ledge)" in ops and "opFall(mage, ram, brink, ledge)" in ops, ops
        self._record(True, "Example 2: taunted, it crashes; the hook from the ledge drags it into the ravine")

    def test_example_3_hook_out_of_the_way(self):
        """The brink holder hooks the heavy Ram in the window: the anchor drags it into the
        arena, and the gore finds an empty brink; then it walks round to the ledge."""
        ops = all_ops(plans_with("hook", "taunt"))
        assert "opDash(player, brink, arena)" in ops, ops
        assert "opFall(player, ram, brink, ledge)" in ops, ops
        assert not any(o.startswith("opInterrupt(") for o in ops), ops
        self._record(True, "Example 3: a hook at the heavy Ram pulls its caster clear of the charge")

    def test_example_4_the_shield_takes_the_gore(self):
        ops = all_ops(plans_with("shieldBash", "blindingFlash"))
        assert "opRemove(ram, player, shielded)" in ops, ops
        assert "opCast(player, shieldBash, ram)" in ops, ops
        self._record(True, "Example 4: the bash's shield takes the gore, and the second bash knocks it in")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        report = combos()
        assert not report.singles_winning, f"a single skill wins: {report.singles_winning}"
        assert report.solo_plans == 0, f"{report.solo_plans} solo plans"
        self._record(True, "P1: no skill wins alone, even held by both companions; no solo plan")

    def test_property_p2_the_measured_assignments_win(self):
        report = combos()
        found = {(a["player"][0], a["mage"][0]) for a in report.winning}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        assert len(report.methods) == 10 and not report.dead_skills, (report.methods, report.dead_skills)
        self._record(True, f"P2: exactly the {len(WINNING)} measured assignments win (of 49), "
                           "10 methods, no dead skill")

    def test_property_p3_every_plan_crashes_the_ram(self):
        for pair in [("blindingFlash", "tidalWave"), ("taunt", "vortex"), ("shieldBash", "taunt")]:
            for p in plans_with(*pair):
                ops = op_strings(p)
                assert "opBlow(ram, ramCharge, brink, brink)" in ops, pair
                assert "opGrant(ram, ram, staggered)" in ops, pair
        self._record(True, "P3: every plan provokes the charge, and the Ram crashes into the pillar")

    def test_property_p4_heavy_it_does_not_move(self):
        """Nothing but the crash takes its weight: without a lure, no pair wins."""
        assert not plans_with("fireball", "vortex")
        assert not plans_with("tidalWave", "hook")
        self._record(True, "P4: before the crash, nothing moves it")

    def test_property_p5_the_brink_holder_is_gored(self):
        """The finisher on the brink is gored by the charge and finishes nothing; the same
        finisher waiting in the pen wins."""
        assert not plans_with("fireball", "taunt")
        assert not plans_with("tidalWave", "blindingFlash")
        assert plans_with("fireball", "taunt", start={"player": "pen"})
        assert not plans_with("taunt", "fireball", start={"mage": "brink"})
        self._record(True, "P5: whoever waits on the brink is gored; a physical charge only a shield or a "
                           "way out survives")


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
