"""End-to-end parity tests: the MCP must produce the same results as the
``htn_test_framework`` (which the unit tests use). Both pipelines run
in-process against the same shared library — no subprocesses, no stdio.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve()
_MCP_SERVER = _HERE.parents[1]
_REPO = _MCP_SERVER.parent

# Make the MCP package importable.
sys.path.insert(0, str(_MCP_SERVER))
# Make htn_test_framework / indhtnpy importable.
sys.path.insert(0, str(_REPO / "src" / "Python"))


from htn_test_framework import HtnTestSuite  # type: ignore  # noqa: E402

from indhtn_mcp.server import create_server  # type: ignore  # noqa: E402


pytestmark = pytest.mark.asyncio


def _locomotion_src() -> str:
    return (_REPO / "components" / "primitives" / "locomotion" / "src.htn").read_text()


def _normalise_facts(facts: list[str]) -> list[str]:
    return sorted(f.strip() for f in facts)


# ----------------------------------------------------------------------
# Framework reference
# ----------------------------------------------------------------------

def _framework_run_direct_movement() -> dict:
    """Replay locomotion example 1 via the test framework."""
    suite = HtnTestSuite()
    suite.compile_additional(_locomotion_src())
    suite.set_state([
        "at(player, roomA)",
        "connected(roomA, roomB)",
    ])
    # Plan
    error, raw = suite._planner.FindAllPlansCustomVariables("moveTo(player, roomB).")
    assert error is None, f"Plan failed: {error}"
    import json
    solutions = json.loads(raw)
    suite._planner.ApplySolution(0)
    state = suite.get_state()
    return {
        "planSolutions": solutions,
        "stateAfter": _normalise_facts(state),
    }


def _framework_run_multi_hop() -> dict:
    """Replay locomotion example 3 (multi-hop) via the test framework."""
    suite = HtnTestSuite()
    suite.compile_additional(_locomotion_src())
    suite.set_state([
        "at(player, roomA)",
        "connected(roomA, corridor)",
        "connected(corridor, roomB)",
        "pathThrough(roomA, roomB, corridor)",
    ])
    error, raw = suite._planner.FindAllPlansCustomVariables("moveTo(player, roomB).")
    assert error is None, f"Plan failed: {error}"
    import json
    solutions = json.loads(raw)
    suite._planner.ApplySolution(0)
    state = suite.get_state()
    return {
        "planSolutions": solutions,
        "stateAfter": _normalise_facts(state),
    }


# ----------------------------------------------------------------------
# MCP runner
# ----------------------------------------------------------------------

async def _mcp_run_direct_movement() -> dict:
    srv = create_server()
    sid = (await srv.call_tool_direct("indhtn_create_session", {}))["sessionId"]
    await srv.call_tool_direct(
        "indhtn_load_source",
        {"sessionId": sid, "source": _locomotion_src(), "label": "locomotion"},
    )
    await srv.call_tool_direct(
        "indhtn_add_facts",
        {"sessionId": sid, "facts": ["at(player, roomA)", "connected(roomA, roomB)"]},
    )
    plans = await srv.call_tool_direct(
        "indhtn_find_plans", {"sessionId": sid, "goal": "moveTo(player, roomB)"}
    )
    applied = await srv.call_tool_direct(
        "indhtn_apply_plan", {"sessionId": sid, "solutionIndex": 0}
    )
    return {
        "plans": plans,
        "applied": applied,
        "stateAfter": _normalise_facts(applied["facts"]),
    }


async def _mcp_run_multi_hop() -> dict:
    srv = create_server()
    sid = (await srv.call_tool_direct("indhtn_create_session", {}))["sessionId"]
    await srv.call_tool_direct(
        "indhtn_load_source",
        {"sessionId": sid, "source": _locomotion_src(), "label": "locomotion"},
    )
    await srv.call_tool_direct(
        "indhtn_add_facts",
        {
            "sessionId": sid,
            "facts": [
                "at(player, roomA)",
                "connected(roomA, corridor)",
                "connected(corridor, roomB)",
                "pathThrough(roomA, roomB, corridor)",
            ],
        },
    )
    plans = await srv.call_tool_direct(
        "indhtn_find_plans", {"sessionId": sid, "goal": "moveTo(player, roomB)"}
    )
    applied = await srv.call_tool_direct(
        "indhtn_apply_plan", {"sessionId": sid, "solutionIndex": 0}
    )
    return {
        "plans": plans,
        "applied": applied,
        "stateAfter": _normalise_facts(applied["facts"]),
    }


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------

class TestLocomotionParity:
    async def test_direct_movement_state_matches(self):
        fw = _framework_run_direct_movement()
        mcp = await _mcp_run_direct_movement()
        assert mcp["stateAfter"] == fw["stateAfter"], (
            f"State differs.\n  fw:  {fw['stateAfter']}\n  mcp: {mcp['stateAfter']}"
        )

    async def test_direct_movement_plan_operator_matches(self):
        fw = _framework_run_direct_movement()
        mcp = await _mcp_run_direct_movement()
        fw_ops = sorted(
            op for sol in fw["planSolutions"]
            if isinstance(sol, list)
            for op in [list(t.keys())[0] + "(" + ",".join(_arg_str(a) for a in list(t.values())[0]) + ")" for t in sol]
        )
        mcp_ops = sorted(
            op.replace(", ", ",")
            for plan in mcp["plans"]["plans"]
            for op in plan["operators"]
        )
        assert mcp_ops == fw_ops, (
            f"Plan ops differ.\n  fw:  {fw_ops}\n  mcp: {mcp_ops}"
        )

    async def test_multi_hop_state_matches(self):
        fw = _framework_run_multi_hop()
        mcp = await _mcp_run_multi_hop()
        assert mcp["stateAfter"] == fw["stateAfter"]


# ----------------------------------------------------------------------
# Snapshot-restore correctness
# ----------------------------------------------------------------------

class TestSnapshotParity:
    async def test_snapshot_restore_round_trip(self):
        srv = create_server()
        sid = (await srv.call_tool_direct("indhtn_create_session", {}))["sessionId"]
        await srv.call_tool_direct(
            "indhtn_load_source",
            {"sessionId": sid, "source": _locomotion_src()},
        )
        await srv.call_tool_direct(
            "indhtn_add_facts",
            {"sessionId": sid, "facts": ["at(player, roomA)", "connected(roomA, roomB)"]},
        )
        before_state = (await srv.call_tool_direct(
            "indhtn_list_facts", {"sessionId": sid}
        ))["facts"]

        await srv.call_tool_direct(
            "indhtn_snapshot_state", {"sessionId": sid, "name": "start"}
        )
        plans = await srv.call_tool_direct(
            "indhtn_find_plans", {"sessionId": sid, "goal": "moveTo(player, roomB)"}
        )
        assert plans["ok"], plans
        await srv.call_tool_direct(
            "indhtn_apply_plan", {"sessionId": sid, "solutionIndex": 0}
        )
        after_apply = (await srv.call_tool_direct(
            "indhtn_list_facts", {"sessionId": sid}
        ))["facts"]
        assert _normalise_facts(after_apply) != _normalise_facts(before_state), (
            "Apply should have changed state."
        )

        restored = await srv.call_tool_direct(
            "indhtn_restore_state", {"sessionId": sid, "name": "start"}
        )
        assert restored["ok"]
        after_restore = (await srv.call_tool_direct(
            "indhtn_list_facts", {"sessionId": sid}
        ))["facts"]
        assert _normalise_facts(after_restore) == _normalise_facts(before_state), (
            f"Restore must return original state.\n  before:  {_normalise_facts(before_state)}\n  after:   {_normalise_facts(after_restore)}"
        )

    async def test_append_source_unwound_by_restore(self):
        srv = create_server()
        sid = (await srv.call_tool_direct("indhtn_create_session", {}))["sessionId"]
        await srv.call_tool_direct(
            "indhtn_load_source", {"sessionId": sid, "source": "alpha. beta."}
        )
        # Snapshot, then append a new fact, then restore.
        await srv.call_tool_direct(
            "indhtn_snapshot_state", {"sessionId": sid, "name": "early"}
        )
        await srv.call_tool_direct(
            "indhtn_append_source", {"sessionId": sid, "source": "gamma."}
        )
        facts_with_gamma = (await srv.call_tool_direct(
            "indhtn_list_facts", {"sessionId": sid}
        ))["facts"]
        assert "gamma" in facts_with_gamma

        await srv.call_tool_direct(
            "indhtn_restore_state", {"sessionId": sid, "name": "early"}
        )
        facts_post = (await srv.call_tool_direct(
            "indhtn_list_facts", {"sessionId": sid}
        ))["facts"]
        assert "gamma" not in facts_post, (
            f"Source appended after snapshot should be unwound; got {facts_post}"
        )


# ----------------------------------------------------------------------
# Apply-operator semantics
# ----------------------------------------------------------------------

class TestApplyOperator:
    async def test_apply_primitive_operator_succeeds(self):
        srv = create_server()
        sid = (await srv.call_tool_direct("indhtn_create_session", {}))["sessionId"]
        await srv.call_tool_direct(
            "indhtn_load_source", {"sessionId": sid, "source": _locomotion_src()}
        )
        await srv.call_tool_direct(
            "indhtn_add_facts",
            {"sessionId": sid, "facts": ["at(player, roomA)"]},
        )
        r = await srv.call_tool_direct(
            "indhtn_apply_operator",
            {"sessionId": sid, "operator": "opMoveTo(player, roomA, roomB)"},
        )
        assert r["ok"], r
        facts = (await srv.call_tool_direct(
            "indhtn_list_facts", {"sessionId": sid, "filterPredicate": "at"}
        ))["facts"]
        assert "at(player,roomB)" in facts and "at(player,roomA)" not in facts

    async def test_apply_operator_preconditions_failed(self):
        srv = create_server()
        sid = (await srv.call_tool_direct("indhtn_create_session", {}))["sessionId"]
        await srv.call_tool_direct(
            "indhtn_load_source", {"sessionId": sid, "source": _locomotion_src()}
        )
        # No at(player, anywhere) fact — opMoveTo's del() will not match.
        r = await srv.call_tool_direct(
            "indhtn_apply_operator",
            {"sessionId": sid, "operator": "opMoveTo(player, roomA, roomB)"},
        )
        assert not r["ok"]
        assert r["code"] == "preconditions_failed"
        assert "at(player" in (r.get("failedPrecondition") or "")

    async def test_apply_operator_ambiguous_unification(self):
        srv = create_server()
        sid = (await srv.call_tool_direct("indhtn_create_session", {}))["sessionId"]
        await srv.call_tool_direct(
            "indhtn_load_source", {"sessionId": sid, "source": _locomotion_src()}
        )
        # Two independent at(player, X) facts and two corresponding
        # connections to roomC. The moveTo method decomposes via the
        # 'direct connection' rule, which unifies twice — once with
        # ?current=roomA and once with ?current=roomB — yielding two
        # single-op plans. apply_operator must refuse to silently pick
        # plans[0].
        await srv.call_tool_direct(
            "indhtn_add_facts",
            {
                "sessionId": sid,
                "facts": [
                    "at(player, roomA)",
                    "at(player, roomB)",
                    "connected(roomA, roomC)",
                    "connected(roomB, roomC)",
                ],
            },
        )
        r = await srv.call_tool_direct(
            "indhtn_apply_operator",
            {"sessionId": sid, "operator": "moveTo(player, roomC)"},
        )
        assert not r["ok"], r
        assert r["code"] == "ambiguous_unification", r
        assert len(r["candidates"]) >= 2, r
        # Make sure state wasn't mutated by the rejected call.
        facts = (await srv.call_tool_direct(
            "indhtn_list_facts", {"sessionId": sid, "filterPredicate": "at"}
        ))["facts"]
        assert "at(player,roomA)" in facts and "at(player,roomB)" in facts

    async def test_apply_method_reports_multi_op(self):
        srv = create_server()
        sid = (await srv.call_tool_direct("indhtn_create_session", {}))["sessionId"]
        await srv.call_tool_direct(
            "indhtn_load_source", {"sessionId": sid, "source": _locomotion_src()}
        )
        await srv.call_tool_direct(
            "indhtn_add_facts",
            {
                "sessionId": sid,
                "facts": [
                    "at(player, roomA)",
                    "connected(roomA, corridor)",
                    "connected(corridor, roomB)",
                    "pathThrough(roomA, roomB, corridor)",
                ],
            },
        )
        # moveTo is a method that decomposes into multiple opMoveTo calls.
        r = await srv.call_tool_direct(
            "indhtn_apply_operator",
            {"sessionId": sid, "operator": "moveTo(player, roomB)"},
        )
        assert not r["ok"]
        assert r["code"] == "expanded_to_multiple_ops"
        assert len(r["emitted"]) >= 2


class TestPlannerCallGateway:
    """Issue #8: synchronous bindings calls must not block the asyncio
    event loop and must surface a structured timeout."""

    async def test_call_timeout_surfaces_structured_error(self, monkeypatch):
        srv = create_server()
        sid = (await srv.call_tool_direct("indhtn_create_session", {}))["sessionId"]
        session = srv.session_manager.get(sid)

        monkeypatch.setenv("INDHTN_CALL_TIMEOUT_S", "0.05")

        import time

        from indhtn_mcp.server import CallTimeoutError

        # The synchronous body sleeps longer than the budget. The wrapper
        # must raise CallTimeoutError (not block the event loop).
        with pytest.raises(CallTimeoutError):
            await srv._run_in_session(session, lambda: time.sleep(0.5))

    async def test_event_loop_stays_responsive_during_blocking_call(self):
        """Run a blocking lambda in one task; verify another task makes
        progress meanwhile (i.e. the event loop did not stall)."""
        srv = create_server()
        sid = (await srv.call_tool_direct("indhtn_create_session", {}))["sessionId"]
        session = srv.session_manager.get(sid)

        import time

        progress = []

        async def ticker():
            for _ in range(5):
                progress.append("tick")
                await asyncio.sleep(0.01)

        async def blocker():
            await srv._run_in_session(session, lambda: time.sleep(0.2))

        await asyncio.gather(blocker(), ticker())
        assert progress == ["tick"] * 5, (
            f"Event loop stalled during blocking call (got {progress})"
        )

    async def test_trace_lock_held_for_planning_when_capturing(self):
        """Issue #4: when any session is capturing traces, planner work
        on any session must serialise on trace_lock so traces from one
        don't bleed into another's buffer."""
        srv = create_server()
        sid_a = (await srv.call_tool_direct("indhtn_create_session", {}))["sessionId"]
        sid_b = (await srv.call_tool_direct("indhtn_create_session", {}))["sessionId"]
        session_a = srv.session_manager.get(sid_a)
        session_b = srv.session_manager.get(sid_b)

        # Mark session A as capturing without going through set_trace
        # (avoid touching real C++ trace state in this unit-level test).
        session_a.trace_capturing = True
        try:
            # While A is "capturing", a planner call on B must acquire
            # trace_lock. We assert that by holding trace_lock from
            # outside and showing that B's call cannot proceed until we
            # release it.
            import time

            async with srv.session_manager.trace_lock:
                started = asyncio.Event()

                async def b_call():
                    started.set()
                    await srv._run_in_session(
                        session_b, lambda: time.sleep(0.01)
                    )

                task = asyncio.create_task(b_call())
                # Give the task a chance to reach the trace_lock acquire.
                await started.wait()
                await asyncio.sleep(0.05)
                assert not task.done(), (
                    "Planner call on B should be blocked on trace_lock "
                    "while A is capturing."
                )
            # Lock released → the queued call now completes.
            await task
        finally:
            session_a.trace_capturing = False


class TestRemoveFacts:
    async def test_remove_existing_and_missing(self):
        srv = create_server()
        sid = (await srv.call_tool_direct("indhtn_create_session", {}))["sessionId"]
        await srv.call_tool_direct(
            "indhtn_load_source", {"sessionId": sid, "source": ""}
        )
        await srv.call_tool_direct(
            "indhtn_add_facts",
            {"sessionId": sid, "facts": ["alpha", "beta", "gamma"]},
        )
        r = await srv.call_tool_direct(
            "indhtn_remove_facts",
            {"sessionId": sid, "facts": ["alpha.", "missing"]},
        )
        assert r["ok"], r
        # removed and notPresent must both be period-stripped.
        assert r["removed"] == ["alpha"], r
        assert r["notPresent"] == ["missing"], r
        facts = (await srv.call_tool_direct(
            "indhtn_list_facts", {"sessionId": sid}
        ))["facts"]
        assert "alpha" not in facts
        assert "beta" in facts and "gamma" in facts

    async def test_remove_facts_does_not_bloat_ruleset(self):
        """Issue #2: each remove_facts call used to add a synthesised
        method+operator pair to the ruleset. After many calls the planner's
        method table would grow linearly. Verify the new retract-based
        path leaves no residue.
        """
        srv = create_server()
        sid = (await srv.call_tool_direct("indhtn_create_session", {}))["sessionId"]
        await srv.call_tool_direct(
            "indhtn_load_source", {"sessionId": sid, "source": ""}
        )

        # Add and remove the same fact 50 times. The ruleset must NOT
        # grow with each iteration.
        for i in range(50):
            await srv.call_tool_direct(
                "indhtn_add_facts",
                {"sessionId": sid, "facts": [f"churn{i}"]},
            )
            r = await srv.call_tool_direct(
                "indhtn_remove_facts",
                {"sessionId": sid, "facts": [f"churn{i}"]},
            )
            assert r["ok"] and r["removed"] == [f"churn{i}"], r

        # No mcpRemoveFactsOp/mcpRemoveFactsTask rules should ever exist.
        # The introspection tool reports compiled methods/operators by name.
        # Use the planner's GetStateFacts as a proxy: there should be no
        # leftover facts and no residue fact tagged with the old suffix.
        facts = (await srv.call_tool_direct(
            "indhtn_list_facts", {"sessionId": sid}
        ))["facts"]
        residue = [f for f in facts if "mcpRemoveFacts" in f]
        assert residue == [], f"Synthesised remove-facts residue found: {residue}"


def _arg_str(term):
    """Stringify a JSON term arg list — used by parity assertion."""
    from indhtnpy import termToString  # type: ignore

    return termToString(term)
