"""Tests for the Lamplighter level (stealth and avoidance)."""

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
GOAL = "escape."
POOL = ["blindingFlash", "shieldBash", "tidalWave", "blizzard", "taunt", "fireball", "vortex"]
# The winch: the warden blinded or stunned.
WARDEN = ["blindingFlash", "shieldBash"]
# The street: the lamplighter lured off his post, knocked onto his rope, or
# the lamps frosted over.
STREET = ["taunt", "fireball", "vortex", "blizzard"]


def _both_ways(pairs):
    return set(pairs) | {(b, a) for a, b in pairs}


# The measured matrix (htn_components combos): a warden answer and a street
# answer, or tidalWave and blizzard (soak and freeze the warden; frost the
# lamps), held by either companion.
WINNING = _both_ways([(w, s) for w in WARDEN for s in STREET] + [("tidalWave", "blizzard")])

_REPORT = None


def combos_report():
    global _REPORT
    if _REPORT is None:
        _REPORT = run_combos(HERE, ROOT)
    return _REPORT


def flat(plan):
    out = []
    for op in plan:
        name = list(op.keys())[0]
        args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]
        out.append(f"{name}({', '.join(args)})")
    return out


def plans_with(player, mage):
    """All winning plans with the player knowing `player` and the mage `mage`,
    on a fresh planner (a failed search locks the rule set)."""
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^knows\((player|mage), \w+\)\.\n", "", text, flags=re.M)
    planner = HtnPlanner(False)
    planner.SetMemoryBudget(256 * 1024 * 1024)
    loader = ComponentLoader(planner, ROOT, warn=lambda m: None)
    loader.load("abilities/goals/neutralize")
    loader.load("abilities/primitives/ab_catalog")
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n"
    assert planner.HtnCompileCustomVariables(text + kit) is None
    error, result = planner.FindAllPlansCustomVariables(GOAL)
    assert error is None, error
    sols = json.loads(result)
    if not sols or (isinstance(sols[0], dict) and "false" in sols[0]):
        return []
    return [flat(s) for s in sols]


def some_plan_has(plans, *ops):
    return any(all(o in p for o in ops) for p in plans)


class LamplighterTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_a_bash_and_a_taunt(self):
        plans = plans_with("shieldBash", "taunt")
        assert some_plan_has(plans, "opGrant(player, warden, stunned)",
                             "opStepOn(player, player, winch)", "opOpen(player, gate)",
                             "opNavigate(lamplighter, post, street)",
                             "opNavigate(mage, street, exit)"), plans[:2]
        self._record(True, "Example 1: the warden stunned, the winch turned; the lamplighter "
                           "taunted off his post")

    def test_example_2_onto_his_own_rope(self):
        plans = plans_with("blindingFlash", "fireball")
        assert some_plan_has(plans, "opGrant(player, warden, blinded)",
                             "opKnock(mage, lamplighter, lampRope)",
                             "opReshape(mage, street, lamplight, shadows)",
                             "opGrant(player, player, stealthed)"), plans[:2]
        self._record(True, "Example 2: a flash blinds the warden; a fireball knocks the "
                           "lamplighter onto his own lamp rope and the street goes dark")

    def test_example_3_soak_and_freeze(self):
        plans = plans_with("tidalWave", "blizzard")
        assert some_plan_has(plans, "opGrant(player, warden, wet)",
                             "opReact(mage, warden, wet, chilled, freeze)",
                             "opGrant(mage, warden, stunned)",
                             "opReshape(mage, street, lamplight, iceSheet)"), plans[:2]
        self._record(True, "Example 3: a wave soaks the warden and a blizzard freezes him; a "
                           "second blizzard frosts the lamps")

    def test_example_4_the_vortex_on_the_rope(self):
        plans = plans_with("vortex", "blindingFlash")
        assert some_plan_has(plans, "opCast(player, vortex, lampRope)",
                             "opStepOn(player, lamplighter, lampRope)"), plans[:2]
        self._record(True, "Example 4: a vortex on the rope pulls the lamplighter onto it")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        report = combos_report()
        assert not report.singles_winning, report.singles_winning
        for s in ["blizzard", "taunt"]:
            assert not plans_with(s, s), s
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_measured_assignments_win(self):
        report = combos_report()
        found = {(w["player"][0], w["mage"][0]) for w in report.winning}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        assert report.solo_plans == 0 and not report.dead_skills and not report.failures
        assert len(report.methods) == 9, report.methods
        self._record(True, f"P2: exactly the {len(WINNING)} measured assignments win "
                           f"({len(report.methods)} methods), none solo, no dead skill")

    def test_property_p3_the_lantern(self):
        assert not plans_with("blindingFlash", "shieldBash")
        self._record(True, "P3: nothing blinds or stuns the lamplighter")

    def test_property_p4_the_rooted_warden(self):
        assert not plans_with("taunt", "fireball")
        assert not plans_with("vortex", "blizzard")
        self._record(True, "P4: the warden cannot be lured or moved; dry, a blizzard only chills him")

    def test_property_p5_blizzard_two_roles(self):
        plans = plans_with("tidalWave", "blizzard")
        assert plans and all("opCast(mage, blizzard, street)" in p and
                             "opGrant(mage, warden, stunned)" in p for p in plans), plans[:2]
        self._record(True, "P5: one blizzard freezes the soaked warden, another frosts the lamps")


def run_tests():
    suite = LamplighterTest()
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
