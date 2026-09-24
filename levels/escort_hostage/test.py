"""Tests for The Hostage (escort) level."""

import itertools
import json
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite
from indhtnpy import HtnPlanner
from htn_components.loader import ComponentLoader
from htn_components.manifest import Manifest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../.."))
SEATS = ("player", "mage")
POOL = ["hook", "tidalWave", "fireball", "shieldBash", "blindingFlash", "blizzard",
        "lightningFlash"]

# The measured matrix (htn_components combos): these pairs win, whichever
# companion holds which half, and nothing else does.
WINNING = {frozenset(p) for p in [
    ("shieldBash", "hook"), ("shieldBash", "tidalWave"), ("shieldBash", "fireball"),
    ("blindingFlash", "hook"), ("tidalWave", "blizzard"), ("tidalWave", "lightningFlash")]}


def plans_with(player, mage):
    """All winning plans (as operator strings) with the player knowing `player`
    and the mage `mage`, on a fresh planner (a failed search locks the rule set)."""
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^knows\((player|mage), \w+\)\.\n", "", text, flags=re.M)
    planner = HtnPlanner(False)
    planner.SetMemoryBudget(256 * 1024 * 1024)
    loader = ComponentLoader(planner, ROOT, warn=lambda m: None)
    for dep in Manifest.load(os.path.join(HERE, "manifest.json")).dependencies:
        loader.load(dep)
    assert planner.HtnCompileCustomVariables(
        text + f"knows(player, {player}).\nknows(mage, {mage}).\n") is None
    error, result = planner.FindAllPlansCustomVariables("win.")
    assert error is None, error
    sols = json.loads(result)
    if not sols or (isinstance(sols[0], dict) and "false" in sols[0]):
        return []
    plans = []
    for sol in sols:
        ops = []
        for op in sol:
            name = list(op.keys())[0]
            args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]
            ops.append(f"{name}({','.join(args)})")
        plans.append(ops)
    return plans


def has(plan, *ops):
    return all(op in plan for op in ops)


def index(plan, prefix):
    return min(i for i, op in enumerate(plan) if op.startswith(prefix))


class EscortHostageTest(HtnTestSuite):

    def setup(self):
        for i, dep in enumerate(Manifest.load(os.path.join(HERE, "manifest.json")).dependencies):
            self.load_component(dep, reset_first=(i == 0))
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_bash_and_hook(self):
        self.assert_plan("win.", contains=[
            "opCast(player, shieldBash, warlock)", "opGrant(player, warlock, stunned)",
            "opForcedMove(mage, hostage, cell, corridor)",
            "opForcedMove(mage, hostage, corridor, gate)"],
            not_contains=["opWindUp"])

    def test_example_2_blind_him_and_break_the_meteor(self):
        plans = plans_with("blindingFlash", "hook")
        assert plans and all(has(p, "opGrant(player,warlock,blinded)",
                                 "opWindUp(warlock,meteor,cell)",
                                 "opCast(mage,hook,warlock)",
                                 "opInterrupt(mage,warlock,meteor,cell)",
                                 "opForcedMove(mage,hostage,corridor,gate)") for p in plans)
        self._record(True, "Example 2: the flash alarms him; the hook breaks the meteor, then drags the hostage out")

    def test_example_3_freeze_and_wash_out(self):
        plans = plans_with("tidalWave", "blizzard")
        assert plans and all(has(p, "opGrant(player,warlock,wet)",
                                 "opReact(mage,warlock,wet,chilled,freeze)",
                                 "opForcedMove(player,hostage,cell,corridor)",
                                 "opForcedMove(player,hostage,corridor,gate)") for p in plans)
        assert all(not any(op.startswith("opWindUp") for op in p) for p in plans)
        self._record(True, "Example 3: soaked and iced, he freezes without an alarm; two waves wash the hostage out")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_measured_pairs_win_either_way(self):
        found = {}
        for a, b in itertools.permutations(POOL, 2):
            found.setdefault(frozenset((a, b)), []).append(bool(plans_with(a, b)))
        winning = {k for k, v in found.items() if all(v)}
        one_way = {k for k, v in found.items() if any(v) and not all(v)}
        assert not one_way, f"win only one way round: {one_way}"
        assert winning == WINNING, f"extra: {winning - WINNING}, missing: {WINNING - winning}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win, either way round")

    def test_property_p3_an_unanswered_alarm_has_no_plan(self):
        """Blind, burn or dry-jolt him with nobody able to break the meteor,
        and it would fall on the hostage: no plan."""
        for a, b in [("blindingFlash", "tidalWave"), ("blindingFlash", "fireball"),
                     ("blindingFlash", "blindingFlash"), ("fireball", "hook"),
                     ("lightningFlash", "hook")]:
            assert not plans_with(a, b), (a, b)
        self._record(True, "P3: an alarm nobody can interrupt has no plan")

    def test_property_p4_the_meteor_never_lands(self):
        """In every winning plan the hostage is never struck: any wind-up is
        interrupted before the blow."""
        for a, b in WINNING:
            for p in plans_with(a, b):
                assert not any(op.startswith("opBlow") for op in p), p
                if any(op.startswith("opWindUp") for op in p):
                    assert index(p, "opWindUp") < index(p, "opInterrupt"), p
        self._record(True, "P4: the meteor is always broken; no blow lands")

    def test_property_p5_the_warlock_first(self):
        """Nobody walks into the corridor before the warlock stops watching,
        and both companions cast in every plan."""
        for a, b in [("shieldBash", "hook"), ("blizzard", "tidalWave"),
                     ("lightningFlash", "tidalWave")]:
            for p in plans_with(a, b):
                first_in = min(i for i, op in enumerate(p) if op.startswith("opNavigate") and op.endswith(",corridor)"))
                quiet = max(i for i, op in enumerate(p) if "warlock," in op and "stunned" in op)
                assert quiet < first_in, p
                casters = {op.split("(")[1].split(",")[0] for op in p if op.startswith("opCast")}
                assert casters == {"player", "mage"}, p
        self._record(True, "P5: the warlock is stopped before the corridor; both companions cast")


def run_tests():
    suite = EscortHostageTest()
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
