"""Tests for indhtn_quality.plan_replay + indhtn_quality.dag.

Replay/causal-link extraction is tested against the real in-process engine:
small inline domains exercise the mechanics (causal chain through a method
precondition, parallel pseudo-operator filtering, tree-ID anomalies around
parallel blocks), and the fortress level is the integration case with known
expected depths (relay = 5 causal layers, combo challenges = 1).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve()
_MCP_SERVER = _HERE.parents[1]
_REPO = _MCP_SERVER.parent
sys.path.insert(0, str(_MCP_SERVER))
sys.path.insert(0, str(_REPO / "src" / "Python"))

from indhtn_quality.session_util import open_session  # noqa: E402
from indhtn_quality.static_model import build_static_model  # noqa: E402
from indhtn_quality.plan_replay import replay_plan  # noqa: E402

pytestmark = pytest.mark.asyncio

FORTRESS = _REPO / "prototypes" / "fortress-loadout" / "level.htn"

# A 2-layer causal chain: freeze produces the bridge fact that a later
# method's precondition consumes. The walkOver if() is checked against the
# state AFTER opBridge ran (forward decomposition), so opMove causally
# depends on opBridge.
_CHAIN = """
riverLiquid(r1).
at(hero, bankA).

opFreeze(?r) :- del(riverLiquid(?r)), add(riverFrozen(?r)).
opBridge(?a, ?b) :- del(), add(connected(?a, ?b)).
opMove(?actor, ?from, ?to) :- del(at(?actor, ?from)), add(at(?actor, ?to)).

cross(?actor) :-
    if(at(?actor, ?loc), riverLiquid(r1)),
    do(opFreeze(r1), opBridge(bankA, bankB), walkOver(?actor)).
walkOver(?actor) :-
    if(at(?actor, ?loc), connected(?loc, ?to)),
    do(opMove(?actor, ?loc, ?to)).

goals(cross(hero)).
"""

# parallel() emits beginParallel/endParallel pseudo-operators and the tree's
# node IDs go inconsistent around the block; opFuse then consumes both tags.
_PARALLEL = """
ready(t).

opTagA(?t) :- del(), add(tagA(?t)).
opTagB(?t) :- del(), add(tagB(?t)).
opFuse(?t) :- del(tagA(?t), tagB(?t)), add(fused(?t)).

combo(?t) :-
    if(ready(?t)),
    do(parallel(opTagA(?t), opTagB(?t)), opFuse(?t)).

goals(combo(t)).
"""


async def _replay(source_or_path, goal, facts=(), plan_index=0):
    async with open_session(
        paths=[str(source_or_path)] if isinstance(source_or_path, Path) else None,
        source=source_or_path if isinstance(source_or_path, str) else None,
        facts=facts,
        memory_budget=256 * 1024 * 1024,
    ) as qs:
        model = build_static_model(qs.source_text)
        initial = await qs.state_facts()
        plans = await qs.find_plans(goal)
        assert plans["ok"], plans
        tree = await qs.tree(plan_index)
        return replay_plan(model, initial, plans["plans"][plan_index], tree), plans


async def test_chain_steps_and_ops():
    replay, _ = await _replay(_CHAIN, "cross(hero).")
    assert [s.op for s in replay.steps] == [
        "opFreeze(r1)",
        "opBridge(bankA,bankB)",
        "opMove(hero,bankA,bankB)",
    ]
    assert not replay.warnings


async def test_chain_causal_links_and_layers():
    replay, _ = await _replay(_CHAIN, "cross(hero).")
    links = {(l.producer, l.fact, l.consumer, l.via) for l in replay.links}
    # opFreeze consumes the initial river state via del()
    assert (-1, "riverLiquid(r1)", 0, "del") in links
    # opMove consumes the bridge opBridge produced, via walkOver's if()
    assert (1, "connected(bankA,bankB)", 2, "precondition") in links
    # opMove also consumes the initial at() via del()
    assert (-1, "at(hero,bankA)", 2, "del") in links
    # layers: opFreeze/opBridge need only initial facts, opMove is layer 2
    assert replay.op_layers == [1, 1, 2]
    assert replay.causal_depth == 2


async def test_chain_method_preconditions_attributed_to_first_op():
    replay, _ = await _replay(_CHAIN, "cross(hero).")
    # cross's if(at(hero,bankA), riverLiquid(r1)) attaches to opFreeze (step 0)
    step0_needs = {(n.fact, n.via) for n in replay.steps[0].needs}
    assert ("at(hero,bankA)", "precondition") in step0_needs
    assert ("riverLiquid(r1)", "precondition") in step0_needs


async def test_parallel_pseudo_ops_filtered_and_fuse_layer():
    replay, _ = await _replay(_PARALLEL, "combo(t).")
    assert [s.op for s in replay.steps] == ["opTagA(t)", "opTagB(t)", "opFuse(t)"]
    links = {(l.producer, l.fact, l.consumer, l.via) for l in replay.links}
    assert (0, "tagA(t)", 2, "del") in links
    assert (1, "tagB(t)", 2, "del") in links
    assert replay.op_layers == [1, 1, 2]


async def test_static_preconditions_become_gates_not_needs():
    replay, _ = await _replay(_PARALLEL, "combo(t).")
    # ready/1 is static (never in any del/add): a gate on step 0, not a need
    assert all(n.fact != "ready(t)" for s in replay.steps for n in s.needs)
    assert "ready(t)" in replay.steps[0].gates


@pytest.mark.slow
async def test_fortress_relay_causal_depth_is_five():
    facts = ["equipped(player, frostNova)", "equipped(companion, shadowStep)"]
    async with open_session(paths=[str(FORTRESS)], facts=facts,
                            memory_budget=256 * 1024 * 1024) as qs:
        model = build_static_model(qs.source_text)
        initial = await qs.state_facts()
        plans = await qs.find_plans("enterFortress().")
        assert plans["ok"]
        # pick the freeze plan (the river-crossing mechanic)
        idx = next(p["index"] for p in plans["plans"]
                   if any("opFreeze" in op for op in p["operators"]))
        tree = await qs.tree(idx)
        replay = replay_plan(model, initial, plans["plans"][idx], tree)
    assert replay.causal_depth == 5
    # the button relay is the deep chain: button1's opConnect enables the
    # companion's move, whose at() enables button2, whose opConnect enables
    # the final moves
    links = {(l.fact, l.via) for l in replay.links}
    assert ("connected(fortress_entrance,fortress_area2)", "precondition") in links
    assert ("connected(fortress_area2,fortress_end)", "precondition") in links


async def test_verify_replay_matches_engine_effects():
    from indhtn_quality.plan_replay import verify_replay

    async with open_session(source=_CHAIN, facts=()) as qs:
        model = build_static_model(qs.source_text)
        initial = await qs.state_facts()
        plans = await qs.find_plans("cross(hero).")
        tree = await qs.tree(0)
        replay = replay_plan(model, initial, plans["plans"][0], tree)
        mismatches = await verify_replay(qs, replay)
    assert mismatches == []


async def test_build_dag_chain_metrics_and_graph():
    from indhtn_quality.dag import build_dag

    result = await build_dag(source=_CHAIN, goal="cross(hero).")
    m = result.metrics
    assert m["planCount"] == 1
    assert m["causalDepth"] == 2
    assert m["causalDepthMin"] == 2
    assert m["minPlanLength"] == 3
    assert m["maxPlanLength"] == 3

    node_ids = {n["id"] for n in result.nodes}
    assert "o:opBridge(bankA,bankB)" in node_ids
    assert "f:connected(bankA,bankB)" in node_ids

    edges = {(e["from"], e["to"], e["kind"]) for e in result.edges}
    assert ("o:opBridge(bankA,bankB)", "f:connected(bankA,bankB)", "produces") in edges
    assert ("f:connected(bankA,bankB)", "o:opMove(hero,bankA,bankB)", "enables") in edges


@pytest.mark.slow
async def test_build_dag_fortress_relay():
    from indhtn_quality.dag import build_dag

    result = await build_dag(
        paths=[str(FORTRESS)], goal="enterFortress().",
        facts=["equipped(player, frostNova)", "equipped(companion, shadowStep)"],
        verify_replays=1,  # apply_operator must not clobber later trees
    )
    m = result.metrics
    assert m["planCount"] == 4
    assert m["causalDepth"] == 5
    assert m["causalDepthMin"] >= 3  # every plan replays, none degenerate to 0
    assert not [w for w in result.warnings if "mismatch" in w or "verify" in w]
    # every plan routes through the button-1 door: a bottleneck fact
    assert "connected(fortress_entrance,fortress_area2)" in m["bottleneckFacts"]
    # all plans resolve the same atom/method: one solution cluster
    assert len(m["clusters"]) == 1
    assert m["clusters"][0]["fingerprint"] == [["dataRelay", "relay"]]


async def test_mermaid_render_smoke():
    from indhtn_quality.dag import build_dag, render_mermaid

    result = await build_dag(source=_CHAIN, goal="cross(hero).")
    text = render_mermaid(result)
    assert "flowchart TD" in text
    assert "opFreeze" in text
    assert "connected(bankA,bankB)" in text


async def test_depth_assertion_helper():
    from indhtn_quality.dag import build_dag, check_depth

    result = await build_dag(source=_CHAIN, goal="cross(hero).")
    ok_check = check_depth(result.metrics, depth_range=(1, 3))
    assert ok_check["ok"] is True
    fail_check = check_depth(result.metrics, depth_range=(3, 5))
    assert fail_check["ok"] is False
    assert "2" in fail_check["detail"]


@pytest.mark.slow
async def test_fortress_combo_challenge_depth_reflects_state_threading():
    # Before the 2026-07-02 state-threading pass this measured 1 (a flat
    # montage: no operator consumed another's effects). opCrush now consumes
    # leverPulled + the hold tag, so holdAndCrush/distractAndStrike plans
    # measure exactly 2 causal layers under this loadout.
    facts = ["equipped(player, frostNova)", "equipped(companion, warHorn)"]
    async with open_session(paths=[str(FORTRESS)], facts=facts,
                            memory_budget=256 * 1024 * 1024) as qs:
        model = build_static_model(qs.source_text)
        initial = await qs.state_facts()
        plans = await qs.find_plans("secureWorkshop().")
        assert plans["ok"]
        tree = await qs.tree(0)
        replay = replay_plan(model, initial, plans["plans"][0], tree)
    assert replay.causal_depth == 2
