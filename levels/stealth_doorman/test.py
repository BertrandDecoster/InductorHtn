"""Tests for the Doorman level (stealth and avoidance)."""

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
GOAL = "win."
POOL = ["vanish", "smokeBomb", "flashbang", "sleepDart", "lullaby", "taunt", "magnetize", "gust"]
SENTRY = ["vanish", "smokeBomb", "flashbang", "sleepDart", "lullaby"]
DOORMAN = ["taunt", "magnetize", "gust"]

# The measured matrix (htn_components combos): a sentry answer and a doorman
# answer, held by either companion - except that vanish only hides its
# caster, and the thief is whoever holds it (still either seat).
WINNING = {(s, d) for s in SENTRY for d in DOORMAN} | {(d, s) for s in SENTRY for d in DOORMAN}

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


class DoormanTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_sneak_and_shove(self):
        plans = plans_with("vanish", "gust")
        assert some_plan_has(plans, "opCast(player, vanish, player)",
                             "opNavigate(mage, yard, garden)",
                             "opForcedMove(mage, doorman, door, cellar)",
                             "opNavigate(player, door, vault)"), plans[:2]
        self._record(True, "Example 1: the player vanishes; the mage shoves the doorman down the cellar steps")

    def test_example_2_blind_and_lure(self):
        plans = plans_with("flashbang", "taunt")
        assert some_plan_has(plans, "opGrant(player, sentry, blinded)",
                             "opGrant(mage, doorman, taunted)",
                             "opNavigate(mage, door, vault)"), plans[:2]
        self._record(True, "Example 2: a flash on the wall; the mage taunts the doorman out and walks in")

    def test_example_3_sleep_and_hook(self):
        plans = plans_with("sleepDart", "magnetize")
        assert some_plan_has(plans, "opGrant(player, sentry, asleep)",
                             "opCast(mage, magnetize, doorman)"), plans[:2]
        self._record(True, "Example 3: a dart puts the sentry to sleep; a hook drags the doorman out")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        report = combos_report()
        assert not report.singles_winning, report.singles_winning
        for s in ["vanish", "flashbang", "taunt"]:
            assert not plans_with(s, s), s
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_measured_assignments_win(self):
        report = combos_report()
        found = {(w["player"][0], w["mage"][0]) for w in report.winning}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        assert report.solo_plans == 0 and not report.dead_skills and not report.failures
        self._record(True, f"P2: exactly the {len(WINNING)} measured assignments win, none solo")

    def test_property_p3_vanish_makes_a_thief(self):
        plans = plans_with("vanish", "taunt")
        assert plans and all("opNavigate(player, door, vault)" in p for p in plans)
        self._record(True, "P3: vanish hides only its caster - the vanisher is always the thief")

    def test_property_p4_a_blind_doorman_still_blocks(self):
        assert not plans_with("flashbang", "sleepDart")
        assert not plans_with("vanish", "lullaby")
        self._record(True, "P4: blinding or sleeping the doorman never clears the door")

    def test_property_p5_nothing_moves_the_sentry(self):
        assert not plans_with("taunt", "gust")
        assert not plans_with("magnetize", "taunt")
        self._record(True, "P5: two movers leave the sentry watching")


def run_tests():
    suite = DoormanTest()
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
