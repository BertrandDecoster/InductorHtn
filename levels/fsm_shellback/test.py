"""Tests for the Shellback level."""

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
POOL = ["fireball", "tidalWave", "hook", "taunt", "blizzard", "lightningFlash", "turnToMist", "vortex"]

# The measured matrix (unordered pairs; each wins whichever companion holds which half).
WINNING = {
    frozenset(p) for p in [
        # curl and roll: the partner pops the shield; fireball burns it, it curls, the blast knocks it in
        ("fireball", "tidalWave"), ("fireball", "taunt"), ("fireball", "lightningFlash"),
        ("fireball", "vortex"),
        # taunt and strike: taunt pops the shield, then makes it follow, snap and spend itself
        ("taunt", "blizzard"), ("taunt", "lightningFlash"),
        # mist and roll: for a moment no shield, no weight; the partner knocks or hooks it in
        ("turnToMist", "fireball"), ("turnToMist", "tidalWave"), ("turnToMist", "hook"),
        ("turnToMist", "vortex"),
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


class ShellbackTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_pop_then_curl_and_roll(self):
        self.assert_plan("win.", contains=[
            "opCast(player, taunt, shellback)",
            "opReact(player, shellback, shielded, taunted, absorb)",
            "opCast(mage, fireball, shellback)", "opProvoked(shellback, burning, withdraw)",
            "opRemove(shellback, shellback, heavy)",
            "opKnock(mage, shellback, abyss)", "opExploit(mage, shellback, chasm, fell)"])

    def test_example_2_mist_then_hook_across(self):
        ops = all_ops(plans_with("hook", "turnToMist"))
        assert "opCast(mage, turnToMist, shellback)" in ops, ops
        assert "opFall(player, shellback, causeway, islet)" in ops, ops
        self._record(True, "Example 2: the mist lifts its weight; a hook from the islet drops it in the chasm")

    def test_example_3_taunt_follow_snap_freeze(self):
        ops = all_ops(plans_with("taunt", "blizzard"))
        assert "opNavigate(shellback, causeway, shore)" in ops, ops
        assert "opProvoked(shellback, taunted, snap)" in ops and "opGrant(shellback, shellback, exhausted)" in ops
        assert "opExploit(mage, shellback, chilled, dead)" in ops, ops
        self._record(True, "Example 3: taunted, it follows to the shore and snaps itself spent; the blizzard stops it")

    def test_example_4_vortex_pops_then_gathers(self):
        ops = all_ops(plans_with("vortex", "fireball"))
        assert "opReact(player, shellback, shielded, rooted, absorb)" in ops, ops
        assert "opCast(player, vortex, abyss)" in ops and "opKnock(player, shellback, abyss)" in ops, ops
        self._record(True, "Example 4: the vortex's roots pop the shield; once it curls, a vortex draws it in")

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
        assert len(report.methods) == 10 and not report.dead_skills, (report.methods, report.dead_skills)
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win ({len(report.winning)} of 64), "
                           "10 methods, no dead skill")

    def test_property_p3_the_shield_eats_the_first_blow(self):
        """Without the mist, every winning plan loses one hostile tag to the shield first."""
        for pair in [("fireball", "taunt"), ("tidalWave", "fireball"), ("taunt", "blizzard"),
                     ("vortex", "fireball")]:
            for p in plans_with(*pair):
                assert any(o.startswith("opReact(") and "shielded" in o and "absorb" in o
                           for o in op_strings(p)), f"{pair}: no shield popped"
        self._record(True, "P3: the shield always eats the first hostile tag")

    def test_property_p4_heavy_it_does_not_move(self):
        """Heavy and shielded, it holds: a hook pops no shield, so the one fire is lost on
        it; frost then fire only melts into a puddle; nothing moves the heavy shell."""
        assert not plans_with("fireball", "hook")
        assert not plans_with("blizzard", "fireball")
        assert not plans_with("vortex", "hook")
        self._record(True, "P4: weight and shield hold unless burned or misted")

    def test_property_p5_knockbacks_stay_on_the_causeway(self):
        """It goes down where it stands: into the abyss or over the edge into the chasm - it
        is never knocked onto the shore."""
        for pair in [("taunt", "fireball"), ("turnToMist", "tidalWave")]:
            for o in all_ops(plans_with(*pair)):
                assert not (o.startswith("opForcedMove(") and "shellback" in o), o
        self._record(True, "P5: a knockback never moves it to another area")


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
