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
POOL = ["blindingFlash", "shieldBash", "fireball", "tidalWave", "taunt", "hook", "vortex"]
WARDEN = ["blindingFlash", "shieldBash"]          # the lever, by blinding the warden
CRATE = ["fireball", "tidalWave"]                 # the crate: on the lever, or cover
LURES = ["taunt", "hook"]                         # the lamplighter off his post
HALL = LURES + ["vortex"] + CRATE


def _both_ways(pairs):
    return set(pairs) | {(b, a) for a, b in pairs}


# The measured matrix (htn_components combos): the warden blinded and any
# hall answer, or the crate on the lever and a lure. A vortex on the lamps
# needs the other companion on the lever, away from the street: it wins only
# with a warden answer.
WINNING = _both_ways([(w, h) for w in WARDEN for h in HALL] +
                     [(c, l) for c in CRATE for l in LURES])

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

    def test_example_1_the_crate_on_the_lever_and_a_taunt(self):
        plans = plans_with("fireball", "taunt")
        assert some_plan_has(plans, "opForcedMove(player, crate, yard, guardroom)",
                             "opOpen(player, gate)",
                             "opForcedMove(mage, lamplighter, post, lamps)",
                             "opNavigate(player, gate, exit)",
                             "opNavigate(mage, gate, exit)"), plans[:2]
        self._record(True, "Example 1: a fireball blows the crate onto the lever; a taunt drags the lamplighter off his post")

    def test_example_2_a_flash_and_cover(self):
        plans = plans_with("blindingFlash", "tidalWave")
        assert some_plan_has(plans, "opGrant(player, warden, blinded)",
                             "opNavigate(player, start, guardroom)",
                             "opForcedMove(mage, crate, yard, hall)",
                             "opNavigate(mage, hall, gate)"), plans[:2]
        self._record(True, "Example 2: a flash blinds the warden; a wave from the lamps washes the crate into the hall as cover")

    def test_example_3_a_bash_and_a_vortex(self):
        plans = plans_with("shieldBash", "vortex")
        assert some_plan_has(plans, "opGrant(player, warden, stunned)",
                             "opCast(mage, vortex, lamps)",
                             "opForcedMove(mage, lamplighter, post, lamps)"), plans[:2]
        self._record(True, "Example 3: a bash stuns the warden; with the player on the lever, a vortex draws the lamplighter off his post")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        report = combos_report()
        assert not report.singles_winning, report.singles_winning
        assert not plans_with("fireball", "fireball")
        self._record(True, "P1: no skill wins alone, even held by both companions - fireball twice included")

    def test_property_p2_measured_assignments_win(self):
        report = combos_report()
        found = {(w["player"][0], w["mage"][0]) for w in report.winning}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        assert report.solo_plans == 0 and not report.dead_skills and not report.failures
        self._record(True, f"P2: exactly the {len(WINNING)} measured assignments win, none solo")

    def test_property_p3_one_crate(self):
        assert not plans_with("fireball", "tidalWave")
        self._record(True, "P3: the crate cannot be on the lever and in the hall")

    def test_property_p4_the_lantern_and_the_blind_room(self):
        # Nothing blinds or stuns the lamplighter; nobody sees into the
        # guardroom, so no lure reaches the warden.
        assert not plans_with("blindingFlash", "shieldBash")
        assert not plans_with("taunt", "hook")
        self._record(True, "P4: two warden answers or two lures leave one obstacle")

    def test_property_p5_the_vortex_trap(self):
        # With the crate on the lever, the other companion has nowhere to
        # stand clear of the street: a vortex on the lamps would root them.
        assert not plans_with("fireball", "vortex")
        self._record(True, "P5: fireball + vortex has no plan - the vortex would draw in and root a companion")

    def test_property_p6_crate_two_roles(self):
        lever = plans_with("fireball", "hook")
        cover = plans_with("shieldBash", "fireball")
        assert lever and all("opForcedMove(player, crate, yard, guardroom)" in p for p in lever)
        assert cover and all("opForcedMove(mage, crate, yard, hall)" in p for p in cover)
        self._record(True, "P6: fireball puts the crate on the lever, or in the hall as cover")


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
