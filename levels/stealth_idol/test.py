"""Tests for the Idol level (stealth and avoidance)."""

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
GOAL = "heist."
POOL = ["vanish", "shadowStep", "sleepDart", "taunt", "flashbang", "gust"]
NAVE = ["vanish", "shadowStep", "sleepDart", "taunt"]
CRYPT = ["flashbang", "gust"]

# The measured matrix (htn_components combos): a way into the nave and a way
# past the skeleton, either companion holding either (the thief is whoever
# the plan needs: the sneak, or anyone).
WINNING = {(a, b) for a in NAVE for b in CRYPT} | {(b, a) for a in NAVE for b in CRYPT}

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


class IdolTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_sneak_in_and_shove_the_skeleton(self):
        plans = plans_with("vanish", "gust")
        assert some_plan_has(plans, "opCast(player, vanish, player)",
                             "opRemove(player, player, stealthed)", "opGrant(player, player, laden)",
                             "opForcedMove(mage, skeleton, crypt, ossuary)",
                             "opNavigate(player, crypt, exit)"), plans[:2]
        self._record(True, "Example 1: the player sneaks in for the idol; the mage shoves the skeleton into the ossuary")

    def test_example_2_a_dart_and_a_flash(self):
        plans = plans_with("sleepDart", "flashbang")
        assert some_plan_has(plans, "opGrant(player, keeper, asleep)",
                             "opNavigate(mage, entry, ledge)",
                             "opGrant(mage, skeleton, blinded)",
                             "opNavigate(player, crypt, exit)"), plans[:2]
        self._record(True, "Example 2: a dart puts the keeper to sleep; a flash from the ledge blinds the skeleton")

    def test_example_3_the_flash_that_wakes_the_dozer(self):
        plans = plans_with("flashbang", "taunt")
        assert some_plan_has(plans, "opCast(player, flashbang, keeper)",
                             "opReact(player, dozer, dozing, blinded, rouse)",
                             "opCast(mage, taunt, dozer)",
                             "opGrant(player, skeleton, blinded)"), plans[:2]
        assert some_plan_has(plans, "opCast(mage, taunt, keeper)", "opGrant(player, skeleton, blinded)")
        self._record(True, "Example 3: a flash at the altar rouses the dozer, and a taunt drags him off - or just taunt the keeper")

    def test_example_4_dash_in_hidden(self):
        plans = plans_with("shadowStep", "gust")
        assert some_plan_has(plans, "opDash(player, entry, nave)", "opGrant(player, player, stealthed)",
                             "opForcedMove(mage, skeleton, crypt, ossuary)"), plans[:2]
        self._record(True, "Example 4: shadowStep dashes into the nave, hidden")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        report = combos_report()
        assert not report.singles_winning, report.singles_winning
        assert not plans_with("flashbang", "flashbang")
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_measured_assignments_win(self):
        report = combos_report()
        found = {(w["player"][0], w["mage"][0]) for w in report.winning}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        assert report.solo_plans == 0 and not report.dead_skills and not report.failures
        self._record(True, f"P2: exactly the {len(WINNING)} measured assignments win, none solo")

    def test_property_p3_the_idol_cannot_be_hidden(self):
        assert not plans_with("vanish", "sleepDart")
        assert not plans_with("shadowStep", "vanish")
        self._record(True, "P3: sneaking gets the thief in, never out past the skeleton")

    def test_property_p4_a_flash_at_the_altar_rouses_the_dozer(self):
        assert not plans_with("flashbang", "gust")
        self._record(True, "P4: flashbang + gust has no plan - the roused dozer still watches the nave")

    def test_property_p5_the_skeleton_is_mindless_and_deaf(self):
        assert not plans_with("sleepDart", "taunt")
        self._record(True, "P5: sleepDart + taunt has no plan - no sleep, no taunt for the skeleton")


def run_tests():
    suite = IdolTest()
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
