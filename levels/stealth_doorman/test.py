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
POOL = ["blink", "lightningFlash", "shieldBash", "hook", "fireball", "vortex", "taunt",
        "turnToMist"]
# Past the sentry: slip into the courtyard, or answer it from the yard.
SENTRY = ["blink", "lightningFlash", "shieldBash", "hook", "fireball", "vortex"]
# After turnToMist, one of these serves both guards.
MIST_PARTNERS = ["shieldBash", "hook", "fireball", "vortex"]


def _both_ways(pairs):
    return set(pairs) | {(b, a) for a, b in pairs}


# The measured matrix (htn_components combos): a sentry answer and a taunt
# for the doorman, or turnToMist and a skill that serves both guards.
WINNING = _both_ways([(s, "taunt") for s in SENTRY] +
                     [("turnToMist", m) for m in MIST_PARTNERS])

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

    def test_example_1_blink_and_taunt(self):
        plans = plans_with("blink", "taunt")
        assert some_plan_has(plans, "opTeleport(player, tower, court)",
                             "opCast(mage, taunt, doorman)",
                             "opNavigate(doorman, court, yard)",
                             "opNavigate(player, hall, vault)"), plans[:2]
        self._record(True, "Example 1: the player blinks over the moat into the courtyard; "
                           "the mage taunts the doorman out to the yard")

    def test_example_2_hook_the_sentry_into_the_moat(self):
        plans = plans_with("hook", "taunt")
        assert some_plan_has(plans, "opFall(player, sentry, tower, yard)",
                             "opGrant(player, sentry, fell)",
                             "opCast(mage, taunt, doorman)",
                             "opNavigate(player, hall, vault)"), plans[:2]
        self._record(True, "Example 2: hooked across the moat, the sentry falls in")

    def test_example_3_mist_and_hook(self):
        plans = plans_with("turnToMist", "hook")
        assert some_plan_has(plans, "opRemove(player, doorman, heavy)",
                             "opForcedMove(mage, doorman, hall, court)",
                             "opNavigate(mage, hall, vault)"), plans[:2]
        self._record(True, "Example 3: the doorman turns to mist and the thief hooks him out "
                           "into the courtyard, then walks past")

    def test_example_4_vortex_twice(self):
        plans = plans_with("vortex", "turnToMist")
        assert some_plan_has(plans, "opKnock(player, sentry, murderHole)",
                             "opKnock(player, doorman, cellarSteps)",
                             "opGrant(player, doorman, fell)"), plans[:2]
        self._record(True, "Example 4: a vortex on the murder hole, then - the doorman misted - "
                           "one on the cellar steps")

    def test_example_5_short_the_sentry(self):
        plans = plans_with("lightningFlash", "taunt")
        assert some_plan_has(plans, "opGrant(player, sentry, stunned)",
                             "opDash(player, yard, tower)"), plans[:2]
        self._record(True, "Example 5: lightning shorts the clockwork sentry")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        report = combos_report()
        assert not report.singles_winning, report.singles_winning
        for s in ["blink", "taunt", "hook"]:
            assert not plans_with(s, s), s
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_measured_assignments_win(self):
        report = combos_report()
        found = {(w["player"][0], w["mage"][0]) for w in report.winning}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        assert report.solo_plans == 0 and not report.dead_skills and not report.failures
        assert len(report.methods) == 10, report.methods
        self._record(True, f"P2: exactly the {len(WINNING)} measured assignments win "
                           f"({len(report.methods)} methods), none solo, no dead skill")

    def test_property_p3_the_hall_is_hushed(self):
        # blink + blink: the thief blinks into the hall and is hushed; the
        # vault stays under the doorman's eyes.
        assert not plans_with("blink", "lightningFlash")
        for p in plans_with("blink", "taunt"):
            assert "opGrant(player, player, silenced)" in p or \
                   "opGrant(mage, mage, silenced)" in p, p
        self._record(True, "P3: whoever enters the hall is hushed; two ways in are no way past")

    def test_property_p4_the_heavy_doorman(self):
        # Without turnToMist, only a taunt moves him.
        assert not plans_with("hook", "fireball")
        assert not plans_with("shieldBash", "vortex")
        self._record(True, "P4: nothing but a taunt moves the heavy doorman, unless he is mist")

    def test_property_p5_the_sentry_cannot_be_taunted(self):
        assert not plans_with("taunt", "turnToMist")
        self._record(True, "P5: the sentry cannot walk off its tower: a taunt breaks")

    def test_property_p6_one_skill_two_roles(self):
        plans = plans_with("turnToMist", "fireball")
        assert plans and all("opCast(mage, fireball, sentry)" in p and
                             "opCast(mage, fireball, doorman)" in p for p in plans), plans[:2]
        self._record(True, "P6: with turnToMist, fireball clears both guards")


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
