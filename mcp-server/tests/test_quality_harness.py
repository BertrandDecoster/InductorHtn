"""Tests for indhtn_quality.{config,properties,harness} — the generalized
loadout-sweep quality harness (extraction of the three prototype sweep.py
scripts into named, config-driven property checks)."""

from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve()
_MCP_SERVER = _HERE.parents[1]
_REPO = _MCP_SERVER.parent
sys.path.insert(0, str(_MCP_SERVER))
sys.path.insert(0, str(_REPO / "src" / "Python"))

from indhtn_quality.config import load_config  # noqa: E402
from indhtn_quality.harness import PlanMeta, Row, SweepContext, run_sweep  # noqa: E402
from indhtn_quality.properties import run_properties  # noqa: E402


# ----------------------------------------------------------------------
# A miniature loadout level: 3 skills, choose 2 (3 loadouts), 2 challenges.
#   c1 (openGate) solvable by fire OR ice (two atoms/methods)
#   c2 (killGolem) needs fire AND ice together (combo), golem invulnerable
# fire+ice full-clears; fire+wind and ice+wind clear only c1. wind is a
# deliberately dead skill (P3 should FAIL) and golem is marker-gated (P6).
# ----------------------------------------------------------------------
_MINI = """
equippableSkill(fire).
equippableSkill(ice).
equippableSkill(wind).
skillIdx(fire, 1).
skillIdx(ice, 2).
skillIdx(wind, 3).

challenge(openGate).
challenge(killGolem).
challengeAtom(openGate, burnGate).
challengeAtom(openGate, freezeLock).
challengeAtom(killGolem, shatter).
atomMethod(burnGate, burn).
atomMethod(freezeLock, freeze).
atomMethod(shatter, thermalShock).

opResolveAtom(?atom, ?how) :- del(), add(resolved(?atom)).
opUse(?w, ?s) :- del(), add(used(?w, ?s)).
opBlast(?w1, ?w2) :- del(), add(golemShattered).

openGate() :-
    if(equipped(?w, fire)),
    do(opUse(?w, fire), opResolveAtom(burnGate, burn)).
openGate() :-
    if(equipped(?w, ice)),
    do(opUse(?w, ice), opResolveAtom(freezeLock, freeze)).

killGolem() :-
    if(equipped(?w1, fire), equipped(?w2, ice), \\==(?w1, ?w2)),
    do(opBlast(?w1, ?w2), opResolveAtom(shatter, thermalShock)).

solveLevel() :- if(), do(openGate(), killGolem()).

opEquip(?who, ?s) :- del(), add(equipped(?who, ?s)).
playLevel() :-
    if(equippableSkill(?s1), equippableSkill(?s2),
       skillIdx(?s1, ?i1), skillIdx(?s2, ?i2), <(?i1, ?i2)),
    do(opEquip(player, ?s1), opEquip(companion, ?s2), solveLevel()).

goals(playLevel()).
"""

_MINI_CONFIG = {
    "level": "mini.htn",
    "memoryBudgetBytes": 64 * 1024 * 1024,
    "choice": {
        "kind": "pair-loadout",
        "poolQuery": "equippableSkill(?s).",
        "slots": 2,
        "injectFacts": ["equipped(player, {0})", "equipped(companion, {1})"],
    },
    "goals": {
        "challenges": [
            {"name": "openGate", "goal": "openGate()."},
            {"name": "killGolem", "goal": "killGolem()."},
        ],
        "full": "solveLevel().",
        "playRoot": "playLevel().",
    },
    "metadata": {
        "challengeAtoms": "challengeAtom(?c, ?a).",
        "atomMethods": "atomMethod(?a, ?m).",
        "resolveMarker": "opResolveAtom",
        "markerRequiredFor": ["killGolem"],
    },
    "properties": {
        "P1_choke": {"severity": "error", "minLoadoutsPerChallenge": 1},
        "P2_decision": {"severity": "error"},
        "P3_deadSkill": {"severity": "warn"},
        "P4_deadAtom": {"severity": "error"},
        "P5_methodDrift": {"severity": "error"},
        "P6_comboGated": {"severity": "error"},
        "playRootCrossCheck": {"severity": "error"},
        "depth": {"severity": "warn", "min": 3, "max": 5},
        "diversity": {"severity": "warn", "minClusters": 2},
        "minPlanLength": {"severity": "warn", "min": 3},
        "dominance": {"severity": "warn"},
        "generativity": {"severity": "warn"},
    },
}


@pytest.fixture()
def mini_config(tmp_path):
    (tmp_path / "mini.htn").write_text(_MINI, encoding="utf-8")
    cfg_path = tmp_path / "quality.json"
    cfg_path.write_text(json.dumps(_MINI_CONFIG), encoding="utf-8")
    return cfg_path


def test_load_config_resolves_level_and_defaults(mini_config):
    cfg = load_config(mini_config)
    assert cfg.level.name == "mini.htn" and cfg.level.exists()
    assert cfg.choice.slots == 2
    assert [c[0] for c in cfg.challenges] == ["openGate", "killGolem"]
    assert cfg.properties["depth"].severity == "warn"
    assert cfg.properties["depth"].params["min"] == 3


@pytest.mark.asyncio
async def test_run_sweep_builds_context(mini_config):
    cfg = load_config(mini_config)
    ctx = await run_sweep(cfg)
    assert ctx.skills == ["fire", "ice", "wind"]
    assert len(ctx.rows) == 3  # 3 unordered pairs
    by_loadout = {r.loadout: r for r in ctx.rows}
    assert by_loadout[("fire", "ice")].cells == {"openGate": 2, "killGolem": 1}
    assert by_loadout[("fire", "wind")].cells == {"openGate": 1, "killGolem": 0}
    assert by_loadout[("fire", "ice")].full > 0
    assert by_loadout[("fire", "wind")].full == 0
    # playLevel cross-check data
    assert ctx.play_count == sum(r.full for r in ctx.rows)
    # replay-derived per-plan metadata is attached
    metas = by_loadout[("fire", "ice")].plan_metas["openGate"]
    assert all(isinstance(m, PlanMeta) for m in metas)
    assert {t for m in metas for t in m.tags} == {("burnGate", "burn"),
                                                  ("freezeLock", "freeze")}


@pytest.mark.asyncio
async def test_properties_on_mini_level(mini_config):
    cfg = load_config(mini_config)
    ctx = await run_sweep(cfg)
    results = {r.name: r for r in run_properties(ctx, cfg)}
    assert results["P1_choke"].ok             # killGolem: 1 loadout >= min 1
    assert results["P2_decision"].ok          # 1/3 full-clear: some, not all
    assert not results["P3_deadSkill"].ok     # wind is in no full-clear loadout
    assert "wind" in results["P3_deadSkill"].detail
    assert results["P4_deadAtom"].ok
    assert results["P5_methodDrift"].ok
    assert results["P6_comboGated"].ok
    assert results["playRootCrossCheck"].ok
    assert not results["depth"].ok            # everything is causally flat here
    assert not results["diversity"].ok        # killGolem has only 1 cluster
    assert "killGolem" in results["diversity"].detail
    assert not results["minPlanLength"].ok    # openGate solves in 2 ops < 3
    assert not results["generativity"].ok     # wind unlocks nothing exclusive
    assert "wind" in results["generativity"].detail


def _ctx_rows(rows):
    return SweepContext(
        skills=sorted({s for r in rows for s in r.loadout}),
        challenge_names=["c1"], rows=rows,
        declared_atoms=set(), declared_methods=set(),
        atoms_seen=set(), methods_seen=set(), play_count=0,
    )


def test_dominance_detects_proper_superset():
    strong = Row(loadout=("a", "b"),
                 cells={"c1": 2}, full=2, atoms={"x", "y"}, fight_only=[],
                 plan_metas={"c1": [PlanMeta(depth=1, length=2,
                                             tags=[("x", "m1"), ("y", "m2")])]})
    weak = Row(loadout=("a", "c"),
               cells={"c1": 1}, full=1, atoms={"x"}, fight_only=[],
               plan_metas={"c1": [PlanMeta(depth=1, length=2, tags=[("x", "m1")])]})
    ctx = _ctx_rows([strong, weak])
    from indhtn_quality.properties import check_dominance
    res = check_dominance(ctx, {})
    assert not res.ok
    assert "a+b" in res.detail and "a+c" in res.detail


def test_generativity_flags_skill_with_no_exclusive_contribution():
    r1 = Row(loadout=("a", "b"), cells={"c1": 1}, full=1, atoms={"x"}, fight_only=[],
             plan_metas={"c1": [PlanMeta(depth=1, length=2, tags=[("x", "m1")])]})
    r2 = Row(loadout=("a", "c"), cells={"c1": 1}, full=1, atoms={"x"}, fight_only=[],
             plan_metas={"c1": [PlanMeta(depth=1, length=2, tags=[("x", "m1")])]})
    ctx = _ctx_rows([r1, r2])
    from indhtn_quality.properties import check_generativity
    res = check_generativity(ctx, {})
    # 'a' is exclusive to nothing? x/m1 achieved by both loadouts, both contain a
    # -> a IS in every achieving loadout, so a gets the credit; b and c do not.
    assert not res.ok
    assert "b" in res.detail and "c" in res.detail
