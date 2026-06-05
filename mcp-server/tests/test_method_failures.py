"""Tests for ``indhtn_method_failures`` — the MCP surface over the planner's
choice-tracking / method-failure histogram (``docs/method-failure-analysis.md``).

These tests skip automatically when the loaded engine was built without
``INDHTN_CHOICE_TRACKING`` (the tool then returns
``ok:false, code:"choice_tracking_unavailable"``).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve()
_MCP_SERVER = _HERE.parents[1]
_REPO = _MCP_SERVER.parent
# Make the MCP package + indhtnpy / htn_evaluator importable.
sys.path.insert(0, str(_MCP_SERVER))
sys.path.insert(0, str(_REPO / "src" / "Python"))

from indhtn_mcp.server import create_server  # type: ignore  # noqa: E402

pytestmark = pytest.mark.asyncio


# A 3-subtask top method that always blocks at subtask 1 (castSpell): subtask 0
# (findEnemy) completes, but castSpell's precondition (mana) never holds, so
# lootBody (subtask 2) is never reached. Mirrors the `craft` worked example in
# docs/method-failure-analysis.md (there the histogram is [0, 5, 0]).
_RULESET = """
enemy(orc).

craft(?e) :- if(enemy(?e)), do(findEnemy(?e), castSpell(?e), lootBody(?e)).

findEnemy(?e) :- del(), add(found(?e)).
castSpell(?e) :- if(mana(player, ?m), >(?m, 0)), do(opCast(?e)).
opCast(?e) :- del(), add(casted(?e)).
lootBody(?e) :- del(), add(looted(?e)).
"""


async def _load(srv, source: str) -> str:
    sid = (await srv.call_tool_direct("indhtn_create_session", {}))["sessionId"]
    res = await srv.call_tool_direct(
        "indhtn_load_source", {"sessionId": sid, "source": source}
    )
    assert res.get("error") is None, res
    return sid


def _clause(by_method, prefix):
    return next(
        (m for m in by_method if m["clauseSignature"].startswith(prefix)), None
    )


def _skip_if_unavailable(res):
    if not res["ok"] and res.get("code") == "choice_tracking_unavailable":
        pytest.skip("engine built without INDHTN_CHOICE_TRACKING")


async def test_blocks_at_subtask_1():
    srv = create_server()
    sid = await _load(srv, _RULESET)
    res = await srv.call_tool_direct(
        "indhtn_method_failures", {"sessionId": sid, "goal": "craft(orc)."}
    )
    _skip_if_unavailable(res)
    assert res["ok"], res
    # craft has no plan: it blocks before completing its body.
    assert res["planCount"] == 0
    assert res["solvable"] is False
    craft = _clause(res["byMethod"], "craft")
    assert craft is not None, res["byMethod"]
    # 3 body subtasks; the single grounding (enemy(orc)) completes subtask 0
    # (findEnemy) but blocks at subtask 1 (castSpell), never reaching lootBody.
    # furthestCompleted is an N+1 histogram: index 1 carries the mass.
    assert craft["subtaskCount"] == 3
    assert craft["furthestCompleted"] == [0, 1, 0, 0]
    assert craft["successS"] == 0


async def test_parity_with_evaluate_view_builder():
    """The tool's byMethod must equal the same view the CLI/evaluator builds
    directly from GetChoiceStats — the projection the C++ tests trust."""
    from htn_evaluator import _build_by_method_view  # type: ignore
    from indhtnpy import HtnPlanner  # type: ignore

    srv = create_server()
    sid = await _load(srv, _RULESET)
    res = await srv.call_tool_direct(
        "indhtn_method_failures", {"sessionId": sid, "goal": "craft(orc)."}
    )
    _skip_if_unavailable(res)
    assert res["ok"], res

    # Independent reference planner over the same source + goal.
    p = HtnPlanner(False)
    assert p.HtnCompileCustomVariables(_RULESET) is None
    p.FindAllPlansCustomVariables("craft(orc).")
    ref = _build_by_method_view(p.GetChoiceStats())

    assert res["byMethod"] == ref


async def test_viable_method_shows_full_success():
    """A goal that DOES have a plan shows its top method completing (mass at N)."""
    srv = create_server()
    sid = await _load(srv, _RULESET)
    # Supply castSpell's mana precondition so the whole body completes.
    await srv.call_tool_direct(
        "indhtn_add_facts", {"sessionId": sid, "facts": ["mana(player, 5)"]}
    )
    res = await srv.call_tool_direct(
        "indhtn_method_failures", {"sessionId": sid, "goal": "craft(orc)."}
    )
    _skip_if_unavailable(res)
    assert res["ok"], res
    assert res["planCount"] == 1
    assert res["solvable"] is True
    craft = _clause(res["byMethod"], "craft")
    assert craft["furthestCompleted"] == [0, 0, 0, 1]
    assert craft["successS"] == 1
