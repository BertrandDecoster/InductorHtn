"""MCP server for InductorHTN, built on the in-process bindings.

Each tool either operates on session state (most do) or analyses source text
without needing a planner (``indhtn_lint``, ``indhtn_introspect``). Tools
that take a ``sessionId`` look it up via ``SessionManager`` and acquire the
session's lock before calling into the bindings.

Response convention
-------------------

Every handler returns JSON with an ``ok`` boolean. The convention:

- ``ok: true`` means the call was dispatched without raising. It does NOT
  mean every item in a batch succeeded.
- ``ok: false`` is reserved for errors that prevented dispatch (invalid
  args, unknown session, bindings raised, call timeout, ...). Always
  carries a ``code`` discriminant.
- Tools that take a list of inputs (``indhtn_add_facts``,
  ``indhtn_load_files``, ``indhtn_remove_facts``) and tools that replay
  multiple sources (``indhtn_reset_state``, ``indhtn_restore_state``)
  return per-item status in ``errors[]`` / ``replay[]`` alongside the
  success list, with ``ok: true`` even on partial failure. Callers MUST
  inspect those arrays — branching only on ``ok`` for batch tools is a
  bug.

See ``mcp-server/README.md`` for the full table of which fields to
inspect per tool.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Awaitable, Callable, List, TypeVar

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .session import HtnSession, SessionManager

T = TypeVar("T")


_DEFAULT_CALL_TIMEOUT_S = 60.0


class CallTimeoutError(RuntimeError):
    """Raised when a bindings-driven call exceeds the configured timeout.

    Note: this signals timeout to the *caller*; the underlying C++ call
    cannot be hard-cancelled and may continue to run in its worker thread
    until it finishes naturally. The session lock stays held for that
    duration, so further calls on the same session will queue.
    """

# Add gui/backend to sys.path so we can import the linter and parser.
_repo_root = Path(__file__).resolve().parents[2]
_gui_backend = str(_repo_root / "gui" / "backend")
if _gui_backend not in sys.path:
    sys.path.insert(0, _gui_backend)

try:
    from htn_linter import lint_htn  # type: ignore
    _LINTER_OK = True
    _LINTER_ERR: str | None = None
except Exception as e:
    lint_htn = None  # type: ignore
    _LINTER_OK = False
    _LINTER_ERR = str(e)

try:
    from htn_parser import parse_htn  # type: ignore
    _PARSER_OK = True
    _PARSER_ERR: str | None = None
except Exception as e:
    parse_htn = None  # type: ignore
    _PARSER_OK = False
    _PARSER_ERR = str(e)


logger = logging.getLogger(__name__)


def _text(payload: Any) -> List[TextContent]:
    return [TextContent(type="text", text=json.dumps(payload, indent=2))]


def _ok_dict(**fields) -> dict:
    return {"ok": True, **fields}


def _err_dict(error: str, code: str = "error", **fields) -> dict:
    return {"ok": False, "code": code, "error": error, **fields}


class IndHTNMCPServer:
    """Tool registry + dispatch for the InductorHTN MCP server."""

    def __init__(self, planner_class=None, max_sessions: int = 10):
        self.session_manager = SessionManager(
            planner_class=planner_class, max_sessions=max_sessions
        )
        self.server = Server("indhtn")
        self._register()

    # ------------------------------------------------------------------
    # Planner-call gateway
    # ------------------------------------------------------------------

    @staticmethod
    def _call_timeout_s() -> float:
        raw = os.environ.get("INDHTN_CALL_TIMEOUT_S")
        if not raw:
            return _DEFAULT_CALL_TIMEOUT_S
        try:
            return float(raw)
        except ValueError:
            logger.warning(
                "INDHTN_CALL_TIMEOUT_S=%r is not a number; using %.1f",
                raw, _DEFAULT_CALL_TIMEOUT_S,
            )
            return _DEFAULT_CALL_TIMEOUT_S

    async def _run_in_session(
        self,
        session: HtnSession,
        fn: Callable[[], T],
        *,
        timeout: float | None = None,
    ) -> T:
        """Run ``fn`` against ``session``'s planner with the right gates.

        Holds ``session.lock`` (serialises calls on this planner) and,
        when any session is currently capturing traces, also
        ``trace_lock`` (so other sessions' planner output doesn't bleed
        into a global trace buffer). Runs the synchronous body in
        ``asyncio.to_thread`` so the event loop stays responsive. Wraps
        with ``asyncio.wait_for`` so a runaway call surfaces as
        ``CallTimeoutError`` instead of hanging the host.

        Lock ordering matches ``_h_set_trace`` / ``_h_get_traces``:
        ``trace_lock`` outer, ``session.lock`` inner.
        """
        deadline = timeout if timeout is not None else self._call_timeout_s()

        async def _body() -> T:
            async with session.lock:
                return await asyncio.wait_for(
                    asyncio.to_thread(fn), timeout=deadline
                )

        capturing = any(
            s.trace_capturing for s in self.session_manager.sessions.values()
        )
        try:
            if capturing:
                async with self.session_manager.trace_lock:
                    return await _body()
            else:
                return await _body()
        except asyncio.TimeoutError as e:
            raise CallTimeoutError(
                f"Bindings call exceeded INDHTN_CALL_TIMEOUT_S={deadline}s; "
                f"the underlying C++ work may still be running. "
                f"Session {session.session_id} will reject further calls "
                f"until that worker completes."
            ) from e

    # ------------------------------------------------------------------
    # Tool registry
    # ------------------------------------------------------------------

    def _register(self) -> None:
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:  # noqa: D401
            return self._tools()

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> List[TextContent]:
            handler = _HANDLERS.get(name)
            if handler is None:
                return _text(_err_dict(f"Unknown tool: {name}", code="unknown_tool"))
            try:
                return await handler(self, arguments or {})
            except CallTimeoutError as e:
                return _text(_err_dict(str(e), code="call_timeout"))
            except KeyError as e:
                return _text(_err_dict(str(e), code="not_found"))
            except FileNotFoundError as e:
                return _text(_err_dict(str(e), code="file_not_found"))
            except ValueError as e:
                return _text(_err_dict(str(e), code="invalid_argument"))
            except RuntimeError as e:
                return _text(_err_dict(str(e), code="runtime_error"))
            except Exception as e:  # pragma: no cover - defensive
                logger.exception("Unhandled error in %s", name)
                return _text(_err_dict(repr(e), code="unhandled"))

    def _tools(self) -> list[Tool]:
        s = lambda **p: {"type": "object", "properties": p, "required": []}

        def obj(properties: dict, required: list[str] | None = None) -> dict:
            return {
                "type": "object",
                "properties": properties,
                "required": required or [],
                "additionalProperties": False,
            }

        return [
            # ---- Lifecycle ----
            Tool(
                name="indhtn_create_session",
                description=(
                    "Create a new HTN session backed by an in-process HtnPlanner. "
                    "Returns a sessionId you'll pass to every other tool."
                ),
                inputSchema=obj({
                    "debug": {"type": "boolean", "description": "Enable debug tracing on the planner."},
                    "memoryBudgetBytes": {"type": "integer", "minimum": 0},
                }),
            ),
            Tool(
                name="indhtn_end_session",
                description="End a session and drop its planner.",
                inputSchema=obj({"sessionId": {"type": "string"}}, required=["sessionId"]),
            ),
            Tool(
                name="indhtn_list_sessions",
                description="List active sessions with their loaded sources and snapshots.",
                inputSchema=obj({}),
            ),
            Tool(
                name="indhtn_reset_state",
                description=(
                    "Drop and rebuild the planner, then replay all loaded sources. "
                    "Restores state to what the sources declare. Snapshots are kept."
                ),
                inputSchema=obj({"sessionId": {"type": "string"}}, required=["sessionId"]),
            ),
            Tool(
                name="indhtn_clear_ruleset",
                description=(
                    "Drop planner, all sources, all snapshots, and the plan cache. "
                    "Session is empty afterward; you must load new sources."
                ),
                inputSchema=obj({"sessionId": {"type": "string"}}, required=["sessionId"]),
            ),
            # ---- Loading ----
            Tool(
                name="indhtn_load_files",
                description=(
                    "Reset the session and compile one or more .htn/.pl files in order. "
                    "Uses HtnCompileCustomVariables (?-prefixed variables) by default."
                ),
                inputSchema=obj({
                    "sessionId": {"type": "string"},
                    "paths": {"type": "array", "items": {"type": "string"}},
                    "dialect": {
                        "type": "string",
                        "enum": ["htn", "htn_custom_vars", "prolog", "prolog_custom_vars", "auto"],
                        "default": "htn_custom_vars",
                    },
                }, required=["sessionId", "paths"]),
            ),
            Tool(
                name="indhtn_load_source",
                description=(
                    "Reset the session and compile a raw HTN/Prolog source string. "
                    "Use this when the ruleset is built programmatically (e.g. tests)."
                ),
                inputSchema=obj({
                    "sessionId": {"type": "string"},
                    "source": {"type": "string"},
                    "dialect": {
                        "type": "string",
                        "enum": ["htn", "htn_custom_vars", "prolog", "prolog_custom_vars", "auto"],
                        "default": "htn_custom_vars",
                    },
                    "label": {"type": "string"},
                }, required=["sessionId", "source"]),
            ),
            Tool(
                name="indhtn_append_source",
                description=(
                    "Append a source string to the current session WITHOUT resetting. "
                    "Use for incremental rule injection (e.g. adding test-specific facts)."
                ),
                inputSchema=obj({
                    "sessionId": {"type": "string"},
                    "source": {"type": "string"},
                    "dialect": {
                        "type": "string",
                        "enum": ["htn", "htn_custom_vars", "prolog", "prolog_custom_vars", "auto"],
                        "default": "htn_custom_vars",
                    },
                    "label": {"type": "string"},
                }, required=["sessionId", "source"]),
            ),
            # ---- Introspection ----
            Tool(
                name="indhtn_list_facts",
                description="Return the current world-state facts as a list of strings.",
                inputSchema=obj({
                    "sessionId": {"type": "string"},
                    "filterPredicate": {
                        "type": "string",
                        "description": "If set, only return facts whose functor matches this name.",
                    },
                }, required=["sessionId"]),
            ),
            Tool(
                name="indhtn_list_goals",
                description="Return the goals() directives declared in the loaded ruleset.",
                inputSchema=obj({"sessionId": {"type": "string"}}, required=["sessionId"]),
            ),
            Tool(
                name="indhtn_introspect",
                description=(
                    "Static parse of HTN source: return all methods, operators, and facts "
                    "with their signatures and line numbers. Does not require a session."
                ),
                inputSchema=obj({"source": {"type": "string"}}, required=["source"]),
            ),
            Tool(
                name="indhtn_lint",
                description="Lint HTN/Prolog source and return diagnostics. Does not require a session.",
                inputSchema=obj({"source": {"type": "string"}}, required=["source"]),
            ),
            # ---- Querying ----
            Tool(
                name="indhtn_query",
                description=(
                    "Execute a Prolog query (no do() clauses). Returns variable bindings. "
                    "Used for inspecting state and asking 'what's true right now?'."
                ),
                inputSchema=obj({
                    "sessionId": {"type": "string"},
                    "query": {"type": "string"},
                }, required=["sessionId", "query"]),
            ),
            # ---- Planning ----
            Tool(
                name="indhtn_find_plans",
                description=(
                    "Find all HTN plans for a goal (with do() decomposition). "
                    "Caches the result so you can apply by index, inspect the tree, etc."
                ),
                inputSchema=obj({
                    "sessionId": {"type": "string"},
                    "goal": {"type": "string"},
                    "maxPlans": {"type": "integer", "minimum": 1},
                }, required=["sessionId", "goal"]),
            ),
            Tool(
                name="indhtn_get_decomposition_tree",
                description="Return the decomposition tree for solution N (requires a cached plan).",
                inputSchema=obj({
                    "sessionId": {"type": "string"},
                    "solutionIndex": {"type": "integer", "minimum": 0, "default": 0},
                }, required=["sessionId"]),
            ),
            Tool(
                name="indhtn_preview_solution_facts",
                description=(
                    "Return what the world state would look like after applying solution N, "
                    "without actually applying it. Includes added/removed diff vs current state."
                ),
                inputSchema=obj({
                    "sessionId": {"type": "string"},
                    "solutionIndex": {"type": "integer", "minimum": 0, "default": 0},
                }, required=["sessionId"]),
            ),
            Tool(
                name="indhtn_get_parallelized_plan",
                description="Return parallelized scheduling (timesteps + dependencies) for solution N.",
                inputSchema=obj({
                    "sessionId": {"type": "string"},
                    "solutionIndex": {"type": "integer", "minimum": 0, "default": 0},
                }, required=["sessionId"]),
            ),
            # ---- Application ----
            Tool(
                name="indhtn_apply_plan",
                description=(
                    "Apply the cached plan (from indhtn_find_plans) to the world state. "
                    "Picks the solution by index. State is modified; use snapshots to undo."
                ),
                inputSchema=obj({
                    "sessionId": {"type": "string"},
                    "solutionIndex": {"type": "integer", "minimum": 0, "default": 0},
                }, required=["sessionId"]),
            ),
            Tool(
                name="indhtn_apply_operator",
                description=(
                    "Apply a single operator (del/add primitive). Fails with a structured "
                    "error if preconditions don't match, or if the call would decompose "
                    "into multiple ops (suggesting it's a method, not a primitive)."
                ),
                inputSchema=obj({
                    "sessionId": {"type": "string"},
                    "operator": {"type": "string"},
                }, required=["sessionId", "operator"]),
            ),
            # ---- Snapshots ----
            Tool(
                name="indhtn_snapshot_state",
                description=(
                    "Capture the current world state under a name. Restore later to undo "
                    "actions taken since. Snapshots also pin the loaded-source count."
                ),
                inputSchema=obj({
                    "sessionId": {"type": "string"},
                    "name": {"type": "string"},
                }, required=["sessionId", "name"]),
            ),
            Tool(
                name="indhtn_restore_state",
                description="Restore a named snapshot. Drops sources appended after capture.",
                inputSchema=obj({
                    "sessionId": {"type": "string"},
                    "name": {"type": "string"},
                }, required=["sessionId", "name"]),
            ),
            Tool(
                name="indhtn_list_snapshots",
                description="List named snapshots and when they were captured.",
                inputSchema=obj({"sessionId": {"type": "string"}}, required=["sessionId"]),
            ),
            Tool(
                name="indhtn_delete_snapshot",
                description="Delete a named snapshot.",
                inputSchema=obj({
                    "sessionId": {"type": "string"},
                    "name": {"type": "string"},
                }, required=["sessionId", "name"]),
            ),
            # ---- State manipulation ----
            Tool(
                name="indhtn_add_facts",
                description=(
                    "Inject one or more facts into the current state. "
                    "Equivalent to the test framework's set_state(...)."
                ),
                inputSchema=obj({
                    "sessionId": {"type": "string"},
                    "facts": {"type": "array", "items": {"type": "string"}},
                }, required=["sessionId", "facts"]),
            ),
            Tool(
                name="indhtn_remove_facts",
                description=(
                    "Remove one or more facts from the current state. Facts not present "
                    "are reported back as notPresent (not an error)."
                ),
                inputSchema=obj({
                    "sessionId": {"type": "string"},
                    "facts": {"type": "array", "items": {"type": "string"}},
                }, required=["sessionId", "facts"]),
            ),
            # ---- Tracing / metrics ----
            Tool(
                name="indhtn_set_trace",
                description=(
                    "Enable or disable trace capture for this session. NOTE: the underlying "
                    "trace state is process-wide in the C++ engine, so only one session "
                    "should capture at a time."
                ),
                inputSchema=obj({
                    "sessionId": {"type": "string"},
                    "enabled": {"type": "boolean"},
                    "alsoStdout": {"type": "boolean", "default": False},
                    "traceType": {"type": "integer"},
                    "traceDetail": {"type": "integer"},
                }, required=["sessionId", "enabled"]),
            ),
            Tool(
                name="indhtn_get_traces",
                description="Return captured trace text. Clears the buffer by default.",
                inputSchema=obj({
                    "sessionId": {"type": "string"},
                    "clearAfter": {"type": "boolean", "default": True},
                }, required=["sessionId"]),
            ),
            Tool(
                name="indhtn_get_resolution_steps",
                description="Return the resolution step count for the most recent query.",
                inputSchema=obj({"sessionId": {"type": "string"}}, required=["sessionId"]),
            ),
        ]

    # ------------------------------------------------------------------
    # Run loop
    # ------------------------------------------------------------------

    async def run(self) -> None:
        async with stdio_server() as (read_stream, write_stream):
            options = self.server.create_initialization_options()
            await self.server.run(read_stream, write_stream, options)

    async def call_tool_direct(self, name: str, arguments: dict) -> dict:
        """Programmatic entry point used by tests.

        Invokes the same dispatch as the stdio path but returns a Python
        dict instead of MCP TextContent. Useful for parity testing.
        """
        handler = _HANDLERS.get(name)
        if handler is None:
            return _err_dict(f"Unknown tool: {name}", code="unknown_tool")
        try:
            payload = await handler(self, arguments or {})
        except CallTimeoutError as e:
            return _err_dict(str(e), code="call_timeout")
        except KeyError as e:
            return _err_dict(str(e), code="not_found")
        except FileNotFoundError as e:
            return _err_dict(str(e), code="file_not_found")
        except ValueError as e:
            return _err_dict(str(e), code="invalid_argument")
        except RuntimeError as e:
            return _err_dict(str(e), code="runtime_error")
        # payload is List[TextContent]; the JSON is in payload[0].text
        if isinstance(payload, list) and payload and hasattr(payload[0], "text"):
            return json.loads(payload[0].text)
        return {"ok": True, "raw": payload}


# ----------------------------------------------------------------------
# Handlers
# ----------------------------------------------------------------------

async def _h_create_session(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    session = await srv.session_manager.create_session(
        debug=bool(args.get("debug", False)),
        memory_budget=args.get("memoryBudgetBytes"),
    )
    return _text(_ok_dict(sessionId=session.session_id))


async def _h_end_session(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    sid = _require_str(args, "sessionId")
    ended = await srv.session_manager.end_session(sid)
    return _text(_ok_dict(ended=ended))


async def _h_list_sessions(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    return _text(_ok_dict(sessions=srv.session_manager.list_sessions()))


async def _h_reset_state(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    sid = _require_str(args, "sessionId")
    session = srv.session_manager.get(sid)
    result = await srv._run_in_session(session, session.reset_state)
    return _text(_ok_dict(**result))


async def _h_clear_ruleset(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    sid = _require_str(args, "sessionId")
    session = srv.session_manager.get(sid)
    await srv._run_in_session(session, session.clear_ruleset)
    return _text(_ok_dict())


async def _h_load_files(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    sid = _require_str(args, "sessionId")
    paths = args.get("paths") or []
    if not isinstance(paths, list) or not all(isinstance(p, str) for p in paths):
        raise ValueError("paths must be an array of strings")
    dialect = args.get("dialect", "htn_custom_vars")
    session = srv.session_manager.get(sid)
    result = await srv._run_in_session(
        session, lambda: session.load_files(paths, dialect=dialect)
    )
    return _text(_ok_dict(**result))


async def _h_load_source(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    sid = _require_str(args, "sessionId")
    source = _require_str(args, "source")
    dialect = args.get("dialect", "htn_custom_vars")
    label = args.get("label")
    session = srv.session_manager.get(sid)
    result = await srv._run_in_session(
        session, lambda: session.load_source(source, dialect=dialect, label=label)
    )
    return _text(_ok_dict(**result))


async def _h_append_source(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    sid = _require_str(args, "sessionId")
    source = _require_str(args, "source")
    dialect = args.get("dialect", "htn_custom_vars")
    label = args.get("label")
    session = srv.session_manager.get(sid)
    result = await srv._run_in_session(
        session, lambda: session.append_source(source, dialect=dialect, label=label)
    )
    return _text(_ok_dict(**result))


async def _h_list_facts(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    sid = _require_str(args, "sessionId")
    filter_pred = args.get("filterPredicate")
    session = srv.session_manager.get(sid)
    facts = await srv._run_in_session(session, session.state_facts)
    if filter_pred:
        prefix = filter_pred + "("
        facts = [f for f in facts if f == filter_pred or f.startswith(prefix)]
    return _text(_ok_dict(facts=facts, count=len(facts)))


async def _h_list_goals(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    sid = _require_str(args, "sessionId")
    session = srv.session_manager.get(sid)
    goals = await srv._run_in_session(session, session.goals)
    return _text(_ok_dict(goals=goals))


async def _h_introspect(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    if not _PARSER_OK:
        return _text(_err_dict(
            f"Parser not available: {_PARSER_ERR}",
            code="parser_unavailable",
        ))
    source = _require_str(args, "source")
    rules, diagnostics = parse_htn(source)  # type: ignore[misc]

    methods, operators, facts = [], [], []
    for rule in rules:
        item = {
            "name": rule.head.name,
            "arity": len(rule.head.args),
            "signature": f"{rule.head.name}({', '.join(a.name for a in rule.head.args)})",
            "line": rule.line,
        }
        if rule.is_method:
            item["has_else"] = rule.has_else
            item["has_allof"] = rule.has_allof
            item["has_anyof"] = rule.has_anyof
            methods.append(item)
        elif rule.is_operator:
            item["has_hidden"] = rule.has_hidden
            operators.append(item)
        elif rule.is_fact:
            facts.append(item)

    parse_errors = [
        d.to_dict() if hasattr(d, "to_dict") else d for d in diagnostics
    ]
    return _text(_ok_dict(
        methods=methods,
        operators=operators,
        facts=facts,
        methodCount=len(methods),
        operatorCount=len(operators),
        factCount=len(facts),
        parseErrors=parse_errors,
    ))


async def _h_lint(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    if not _LINTER_OK:
        return _text(_err_dict(
            f"Linter not available: {_LINTER_ERR}",
            code="linter_unavailable",
        ))
    source = _require_str(args, "source")
    diagnostics = lint_htn(source)  # type: ignore[misc]
    return _text(_ok_dict(
        diagnostics=diagnostics,
        errorCount=sum(1 for d in diagnostics if d.get("severity") == "error"),
        warningCount=sum(1 for d in diagnostics if d.get("severity") == "warning"),
    ))


async def _h_query(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    sid = _require_str(args, "sessionId")
    query = _require_str(args, "query")
    session = srv.session_manager.get(sid)
    result = await srv._run_in_session(session, lambda: session.query(query))
    payload = {"ok": result["ok"], **result}
    return _text(payload)


async def _h_find_plans(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    sid = _require_str(args, "sessionId")
    goal = _require_str(args, "goal")
    max_plans = args.get("maxPlans")
    session = srv.session_manager.get(sid)
    result = await srv._run_in_session(
        session, lambda: session.find_plans(goal, max_plans=max_plans)
    )
    payload = {"ok": result["ok"], **result, "goal": goal}
    return _text(payload)


async def _h_get_decomposition_tree(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    sid = _require_str(args, "sessionId")
    idx = int(args.get("solutionIndex", 0))
    session = srv.session_manager.get(sid)
    tree = await srv._run_in_session(
        session, lambda: session.decomposition_tree(idx)
    )
    return _text(_ok_dict(solutionIndex=idx, tree=tree))


async def _h_preview_solution_facts(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    sid = _require_str(args, "sessionId")
    idx = int(args.get("solutionIndex", 0))
    session = srv.session_manager.get(sid)
    result = await srv._run_in_session(
        session, lambda: session.preview_solution_facts(idx)
    )
    return _text(_ok_dict(**result))


async def _h_get_parallelized_plan(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    sid = _require_str(args, "sessionId")
    idx = int(args.get("solutionIndex", 0))
    session = srv.session_manager.get(sid)
    plan = await srv._run_in_session(
        session, lambda: session.parallelized_plan(idx)
    )
    return _text(_ok_dict(solutionIndex=idx, plan=plan))


async def _h_apply_plan(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    sid = _require_str(args, "sessionId")
    idx = int(args.get("solutionIndex", 0))
    session = srv.session_manager.get(sid)
    result = await srv._run_in_session(session, lambda: session.apply_plan(idx))
    return _text(result)


async def _h_apply_operator(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    sid = _require_str(args, "sessionId")
    operator = _require_str(args, "operator")
    session = srv.session_manager.get(sid)
    result = await srv._run_in_session(
        session, lambda: session.apply_operator(operator)
    )
    return _text(result)


async def _h_snapshot_state(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    sid = _require_str(args, "sessionId")
    name = _require_str(args, "name")
    session = srv.session_manager.get(sid)
    snap = await srv._run_in_session(session, lambda: session.snapshot(name))
    return _text(_ok_dict(**snap.to_summary()))


async def _h_restore_state(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    sid = _require_str(args, "sessionId")
    name = _require_str(args, "name")
    session = srv.session_manager.get(sid)
    result = await srv._run_in_session(session, lambda: session.restore(name))
    return _text(_ok_dict(**result))


async def _h_list_snapshots(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    sid = _require_str(args, "sessionId")
    session = srv.session_manager.get(sid)
    return _text(_ok_dict(snapshots=session.list_snapshots()))


async def _h_delete_snapshot(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    sid = _require_str(args, "sessionId")
    name = _require_str(args, "name")
    session = srv.session_manager.get(sid)
    async with session.lock:
        ok = session.delete_snapshot(name)
    return _text(_ok_dict(deleted=ok))


async def _h_add_facts(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    sid = _require_str(args, "sessionId")
    facts = args.get("facts")
    if not isinstance(facts, list):
        raise ValueError("facts must be an array of strings")
    session = srv.session_manager.get(sid)
    result = await srv._run_in_session(session, lambda: session.add_facts(facts))
    return _text(_ok_dict(**result))


async def _h_remove_facts(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    sid = _require_str(args, "sessionId")
    facts = args.get("facts")
    if not isinstance(facts, list):
        raise ValueError("facts must be an array of strings")
    session = srv.session_manager.get(sid)
    result = await srv._run_in_session(session, lambda: session.remove_facts(facts))
    return _text(_ok_dict(**result))


async def _h_set_trace(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    sid = _require_str(args, "sessionId")
    enabled = bool(args.get("enabled"))
    session = srv.session_manager.get(sid)
    async with srv.session_manager.trace_lock, session.lock:
        # Only one session can capture at a time.
        if enabled:
            already = [
                s for s in srv.session_manager.sessions.values()
                if s is not session and s.trace_capturing
            ]
            if already:
                raise RuntimeError(
                    "Another session is already capturing traces "
                    f"({already[0].session_id}); stop it first."
                )
        result = session.set_trace(
            enabled=enabled,
            also_stdout=bool(args.get("alsoStdout", False)),
            trace_type=args.get("traceType"),
            trace_detail=args.get("traceDetail"),
        )
    return _text(_ok_dict(**result))


async def _h_get_traces(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    sid = _require_str(args, "sessionId")
    session = srv.session_manager.get(sid)
    clear_after = bool(args.get("clearAfter", True))
    async with srv.session_manager.trace_lock, session.lock:
        traces = session.get_traces(clear_after=clear_after)
    return _text(_ok_dict(traces=traces))


async def _h_get_resolution_steps(srv: IndHTNMCPServer, args: dict) -> List[TextContent]:
    sid = _require_str(args, "sessionId")
    session = srv.session_manager.get(sid)
    steps = await srv._run_in_session(session, session.get_resolution_steps)
    return _text(_ok_dict(steps=steps))


def _require_str(args: dict, key: str) -> str:
    value = args.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Argument {key!r} is required and must be a non-empty string.")
    return value


_HANDLERS = {
    "indhtn_create_session": _h_create_session,
    "indhtn_end_session": _h_end_session,
    "indhtn_list_sessions": _h_list_sessions,
    "indhtn_reset_state": _h_reset_state,
    "indhtn_clear_ruleset": _h_clear_ruleset,
    "indhtn_load_files": _h_load_files,
    "indhtn_load_source": _h_load_source,
    "indhtn_append_source": _h_append_source,
    "indhtn_list_facts": _h_list_facts,
    "indhtn_list_goals": _h_list_goals,
    "indhtn_introspect": _h_introspect,
    "indhtn_lint": _h_lint,
    "indhtn_query": _h_query,
    "indhtn_find_plans": _h_find_plans,
    "indhtn_get_decomposition_tree": _h_get_decomposition_tree,
    "indhtn_preview_solution_facts": _h_preview_solution_facts,
    "indhtn_get_parallelized_plan": _h_get_parallelized_plan,
    "indhtn_apply_plan": _h_apply_plan,
    "indhtn_apply_operator": _h_apply_operator,
    "indhtn_snapshot_state": _h_snapshot_state,
    "indhtn_restore_state": _h_restore_state,
    "indhtn_list_snapshots": _h_list_snapshots,
    "indhtn_delete_snapshot": _h_delete_snapshot,
    "indhtn_add_facts": _h_add_facts,
    "indhtn_remove_facts": _h_remove_facts,
    "indhtn_set_trace": _h_set_trace,
    "indhtn_get_traces": _h_get_traces,
    "indhtn_get_resolution_steps": _h_get_resolution_steps,
}


def create_server(planner_class=None, max_sessions: int = 10) -> IndHTNMCPServer:
    """Factory used by tests and the entry-point script."""
    return IndHTNMCPServer(planner_class=planner_class, max_sessions=max_sessions)


def main() -> None:
    """Entry point for the ``indhtn-mcp`` console script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    server = create_server()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
