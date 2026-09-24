"""Tests for The Envoy (escort) level."""

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
POOL = ["tidalWave", "fireball", "hook", "vortex", "blindingFlash", "shieldBash", "blizzard",
        "turnToMist"]

# The measured matrix (htn_components combos): these pairs win, whichever
# companion holds which half, and nothing else does. Any filler with a
# blinder or a basher; the soaker with the blizzard; mist with a mover.
FILLERS = ["tidalWave", "fireball", "hook", "vortex"]
WINNING = {frozenset((f, s)) for f in FILLERS for s in ("blindingFlash", "shieldBash")} | {
    frozenset(("tidalWave", "blizzard")), frozenset(("turnToMist", "tidalWave")),
    frozenset(("turnToMist", "fireball")), frozenset(("turnToMist", "vortex"))}


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


class EscortEnvoyTest(HtnTestSuite):

    def setup(self):
        for i, dep in enumerate(Manifest.load(os.path.join(HERE, "manifest.json")).dependencies):
            self.load_component(dep, reset_first=(i == 0))
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_wash_and_blind(self):
        self.assert_plan("win.", contains=[
            "opCast(player, tidalWave, player)", "opForcedMove(player, crate, yard, briars)",
            "opCast(mage, blindingFlash, mage)", "opGrant(mage, sentry, blinded)",
            "opNavigate(envoy, gatehouse, exit)"])

    def test_example_2_hook_the_crate_over(self):
        plans = plans_with("hook", "shieldBash")
        assert plans and all(has(p, "opCast(player,hook,crate)",
                                 "opForcedMove(player,crate,yard,briars)",
                                 "opCast(mage,shieldBash,sentry)") for p in plans)
        self._record(True, "Example 2: the crate is hooked into the briars from the lawn; the sentry is bashed")

    def test_example_3_mist_and_drop(self):
        plans = plans_with("vortex", "turnToMist")
        assert plans and all(has(p, "opCast(player,vortex,briars)", "opCast(mage,turnToMist,sentry)",
                                 "opCast(player,vortex,moat)",
                                 "opForcedMove(player,sentry,tower,moat)",
                                 "opExploit(player,sentry,chasm,fell)") for p in plans)
        self._record(True, "Example 3: one vortex fills the briars; the sentry turns to mist and a second drops it in the moat")

    def test_example_4_soak_and_freeze(self):
        plans = plans_with("tidalWave", "blizzard")
        assert plans and all(has(p, "opForcedMove(player,crate,yard,briars)",
                                 "opCast(mage,blizzard,sentry)",
                                 "opReact(mage,sentry,wet,chilled,freeze)") for p in plans)
        self._record(True, "Example 4: one wave fills the briars, a second soaks the sentry, the blizzard freezes it")

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

    def test_property_p3_envoy_is_never_dragged(self):
        """Pulling the envoy across the briars drops it: no winning plan moves it
        by force - it always walks."""
        for a, b in WINNING:
            for p in plans_with(a, b):
                assert not any(op.startswith("opForcedMove") and ",envoy," in op for op in p), p
                assert "opNavigate(envoy,gatehouse,exit)" in p
        self._record(True, "P3: the envoy walks out; nobody drags it over the briars")

    def test_property_p4_mist_is_a_moment(self):
        """The push that drops the misted sentry is the very next cast."""
        for a, b in [("turnToMist", "tidalWave"), ("turnToMist", "fireball"), ("turnToMist", "vortex")]:
            for p in plans_with(a, b):
                casts = [op for op in p if op.startswith("opCast")]
                i = casts.index("opCast(player,turnToMist,sentry)")
                assert casts[i + 1].startswith("opCast(mage,"), p
                assert "opExploit(mage,sentry,chasm,fell)" in p, p
        self._record(True, "P4: the sentry drops on the cast right after the mist")

    def test_property_p5_two_companions_cast(self):
        for a, b in WINNING:
            for p in plans_with(a, b):
                casters = {op.split("(")[1].split(",")[0] for op in p if op.startswith("opCast")}
                assert casters == {"player", "mage"}, p
        self._record(True, "P5: both companions cast in every winning plan")


def run_tests():
    suite = EscortEnvoyTest()
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
