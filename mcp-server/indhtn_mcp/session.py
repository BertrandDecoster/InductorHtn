"""In-process HTN session built around the indhtnpy ``HtnPlanner`` bindings.

A session owns one ``HtnPlanner`` instance and the source records needed to
rebuild it (for ``reset_state`` and snapshot restore). Tools call session
methods directly — there is no subprocess.

The previous draft of this module shelled out to ``indhtn`` over stdio and
parsed REPL prompts char-by-char. That approach couldn't reach the
decomposition tree, multi-solution selection, or named snapshots used by the
unit tests in ``src/Python/htn_test_framework.py``. This rewrite goes
through the same bindings the test framework uses so the MCP can produce
identical results.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Literal, Optional

from .bindings_loader import load_planner_class
from .result_format import (
    diff_facts,
    extract_failed_precondition,
    parse_facts,
    parse_plans,
    parse_query_solutions,
)
from .snapshots import Snapshot

logger = logging.getLogger(__name__)


Dialect = Literal["htn", "htn_custom_vars", "prolog", "prolog_custom_vars", "auto"]


@dataclass
class LoadedSource:
    kind: Literal["file", "inline"]
    dialect: Dialect
    label: str
    content: str  # For "file" this is the file path; for "inline" the raw source.


@dataclass
class PlanCache:
    goal: str
    raw_json: str
    parsed: dict
    captured_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_period(text: str) -> str:
    text = text.strip()
    if not text.endswith("."):
        text = text + "."
    return text


def _strip_trailing_period(text: str) -> str:
    text = text.strip()
    if text.endswith("."):
        return text[:-1].rstrip()
    return text


def _sanitize_engine_error(text):
    """Drop the ` -- file: <absolute path>, line:N` suffix the C++ engine
    appends to runtime_error messages. Returning the absolute developer
    path to MCP clients is noise at best and a small info leak at worst.
    Returns the input unchanged if it doesn't carry the suffix."""
    if text is None:
        return None
    cut = text.find(" -- file:")
    if cut < 0:
        return text
    return text[:cut].rstrip()


def _extract_missing_fact(error: str) -> str | None:
    """Pull the term name out of a 'Can't retract X: term -- file: ...' error."""
    marker = "doesn't exist:"
    idx = error.find(marker)
    if idx < 0:
        return None
    tail = _sanitize_engine_error(error[idx + len(marker):]).strip()
    return tail or None


class CompileError(RuntimeError):
    pass


class HtnSession:
    """One game session = one HtnPlanner + bookkeeping."""

    def __init__(
        self,
        session_id: str,
        planner_class,
        debug: bool = False,
        memory_budget: Optional[int] = None,
    ):
        self.session_id = session_id
        self.planner_class = planner_class
        self.debug = debug
        self.memory_budget = memory_budget

        self.planner = self._make_planner()
        self.sources: list[LoadedSource] = []
        self.snapshots: dict[str, Snapshot] = {}
        self.last_plan_result: Optional[PlanCache] = None
        self.trace_capturing = False
        self.created_at = _now()
        self.last_accessed = _now()
        self.lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Planner lifecycle
    # ------------------------------------------------------------------

    def _make_planner(self):
        planner = self.planner_class(self.debug)
        if self.memory_budget is not None:
            planner.SetMemoryBudget(self.memory_budget)
        return planner

    def _recreate_planner(self):
        """Drop the current planner and create a fresh one. Forget plan cache."""
        try:
            del self.planner
        except Exception:
            pass
        self.planner = self._make_planner()
        self.last_plan_result = None

    def touch(self) -> None:
        self.last_accessed = _now()

    # ------------------------------------------------------------------
    # Compilation
    # ------------------------------------------------------------------

    def _compile_with(self, dialect: Dialect, content: str) -> Optional[str]:
        """Compile a string with the requested dialect. Returns error or None."""
        if dialect == "htn":
            return self.planner.HtnCompile(content)
        if dialect == "htn_custom_vars":
            return self.planner.HtnCompileCustomVariables(content)
        if dialect == "prolog":
            return self.planner.PrologCompile(content)
        if dialect == "prolog_custom_vars":
            return self.planner.PrologCompileCustomVariables(content)
        if dialect == "auto":
            return self.planner.Compile(content)
        raise ValueError(f"Unknown dialect: {dialect!r}")

    def _read_file(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _replay_one(self, source: LoadedSource) -> Optional[str]:
        content = (
            self._read_file(source.content)
            if source.kind == "file"
            else source.content
        )
        return self._compile_with(source.dialect, content)

    def _replay_sources(self, up_to: Optional[int] = None) -> list[dict]:
        """Recompile stored sources into the current planner.

        Returns a list of ``{"label": ..., "error": str or None}``.
        """
        limit = len(self.sources) if up_to is None else up_to
        results = []
        for src in self.sources[:limit]:
            err = self._replay_one(src)
            results.append({"label": src.label, "error": _sanitize_engine_error(err)})
        return results

    # ------------------------------------------------------------------
    # Loading APIs
    # ------------------------------------------------------------------

    def load_files(self, paths: list[str], dialect: Dialect = "htn_custom_vars") -> dict:
        """Drop planner state, then compile each file in order."""
        new_sources: list[LoadedSource] = []
        for p in paths:
            abs_path = os.path.abspath(p)
            if not os.path.exists(abs_path):
                raise FileNotFoundError(f"File not found: {p}")
            new_sources.append(
                LoadedSource(
                    kind="file",
                    dialect=dialect,
                    label=os.path.basename(abs_path),
                    content=abs_path,
                )
            )

        self._recreate_planner()
        self.sources = []
        errors = []
        loaded = []
        for src in new_sources:
            err = self._replay_one(src)
            if err is not None:
                errors.append({"file": src.label, "error": _sanitize_engine_error(err)})
            else:
                self.sources.append(src)
                loaded.append(src.label)
        return {"loaded": loaded, "errors": errors}

    def load_source(
        self,
        source: str,
        dialect: Dialect = "htn_custom_vars",
        label: Optional[str] = None,
    ) -> dict:
        """Drop planner state, then compile a single inline source string."""
        self._recreate_planner()
        self.sources = []
        return self.append_source(source, dialect, label)

    def append_source(
        self,
        source: str,
        dialect: Dialect = "htn_custom_vars",
        label: Optional[str] = None,
    ) -> dict:
        """Compile a source string into the current planner (no reset)."""
        if label is None:
            label = f"inline-{uuid.uuid4().hex[:8]}"
        err = self._compile_with(dialect, source)
        if err is not None:
            return {"label": label, "error": _sanitize_engine_error(err)}
        self.sources.append(
            LoadedSource(kind="inline", dialect=dialect, label=label, content=source)
        )
        return {"label": label, "error": None}

    def reset_state(self) -> dict:
        """Drop planner, replay all stored sources to get fresh state.

        Loaded sources stay registered.
        """
        self._recreate_planner()
        replay = self._replay_sources()
        return {"replay": replay, "factsCount": len(self.state_facts())}

    def clear_ruleset(self) -> None:
        """Drop planner, sources, snapshots, plan cache — back to empty."""
        self._recreate_planner()
        self.sources = []
        self.snapshots = {}
        self.last_plan_result = None

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def state_facts(self) -> list[str]:
        error, facts_json = self.planner.GetStateFacts()
        if error is not None:
            raise RuntimeError(f"GetStateFacts: {error}")
        return parse_facts(facts_json)

    def goals(self, custom_variables: bool = True) -> list[str]:
        error, goals = self.planner.GetGoals(customVariables=custom_variables)
        if error is not None:
            raise RuntimeError(f"GetGoals: {error}")
        return list(goals) if goals else []

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def query(self, query: str) -> dict:
        q = _ensure_period(query)
        error, raw = self.planner.PrologQuery(q)
        if error is not None:
            raise RuntimeError(f"PrologQuery: {error}")
        result = parse_query_solutions(raw)
        result["lastResolutionStepCount"] = self.planner.GetLastResolutionStepCount()
        return result

    # ------------------------------------------------------------------
    # Planning
    # ------------------------------------------------------------------

    def find_plans(self, goal: str, max_plans: Optional[int] = None) -> dict:
        g = _ensure_period(goal)
        error, raw = self.planner.FindAllPlansCustomVariables(g)
        if error is not None:
            raise RuntimeError(f"FindAllPlans: {error}")
        parsed = parse_plans(raw)
        self.last_plan_result = PlanCache(goal=g, raw_json=raw, parsed=parsed)

        result = dict(parsed)
        if max_plans is not None and result.get("ok"):
            result["plans"] = result["plans"][:max_plans]
        # NOTE: GetLastResolutionStepCount is only updated by the Prolog
        # ResolveAll paths (PrologQuery, PrologSolveGoals) — see
        # PythonInterface.cpp. HtnFindAllPlans* does not thread a counter
        # through HtnPlanner::FindAllPlans, so reading the counter here would
        # return stale data from the previous query (or 0). Use indhtn_query
        # when you need a step count.
        return result

    def method_failures(self, goal: str) -> dict:
        """Report WHERE a goal's methods block, via the choice-tracking histogram.

        Runs a find-all pass (which accumulates the planner's cross-search
        choice stats) and projects the by-method / by-atom views the CLI
        ``evaluate`` command already uses.

        We call ``GetChoiceStats()`` directly rather than through
        ``htn_evaluator.evaluate_level`` on purpose: ``evaluate_level``
        early-returns and DROPS the choice stats when the goal yields zero
        plans — which is exactly the case you most need to analyse. The view
        builders are reused, since they are the same projection the C++
        component tests trust.

        Read-only w.r.t. state: this plans but never applies. Returns
        ``ok: False, code: "choice_tracking_unavailable"`` when the engine was
        built without ``-DINDHTN_CHOICE_TRACKING=ON``.
        """
        # Imported lazily: htn_evaluator lives in src/Python, which
        # bindings_loader puts on sys.path when the planner class is loaded.
        from htn_evaluator import _build_by_method_view, _build_by_atom_view

        g = _ensure_period(goal)
        error, raw = self.planner.FindAllPlansCustomVariables(g)
        if error is not None:
            raise RuntimeError(f"FindAllPlans: {error}")
        parsed = parse_plans(raw)
        # Cache so subsequent decomposition-tree / preview queries compose,
        # mirroring find_plans (the same find-all pass just ran).
        self.last_plan_result = PlanCache(goal=g, raw_json=raw, parsed=parsed)
        plan_count = parsed.get("planCount", 0) if parsed.get("ok") else 0

        try:
            stats = self.planner.GetChoiceStats()
        except (RuntimeError, ValueError):
            stats = None
        if stats is None:
            return {
                "ok": False,
                "code": "choice_tracking_unavailable",
                "goal": g,
                "note": (
                    "Method-failure analysis requires the engine built with "
                    "-DINDHTN_CHOICE_TRACKING=ON."
                ),
                "solvable": plan_count > 0,
                "planCount": plan_count,
            }
        return {
            "ok": True,
            "goal": g,
            "solvable": plan_count > 0,
            "planCount": plan_count,
            "byMethod": _build_by_method_view(stats),
            "byAtom": _build_by_atom_view(stats),
        }

    def apply_plan(self, solution_index: int = 0, include_facts: bool = False) -> dict:
        if self.last_plan_result is None:
            raise RuntimeError(
                "No plan cached. Call find_plans first to populate the solution list."
            )
        cache = self.last_plan_result
        if not cache.parsed.get("ok"):
            raise RuntimeError("Cached plan result has no solutions.")
        if solution_index < 0 or solution_index >= cache.parsed["planCount"]:
            raise RuntimeError(
                f"solutionIndex {solution_index} out of range "
                f"(have {cache.parsed['planCount']} solutions)"
            )
        facts_before = self.state_facts()
        ok = self.planner.ApplySolution(solution_index)
        if not ok:
            raise RuntimeError(
                f"ApplySolution({solution_index}) reported the index was out of range."
            )
        facts_after = self.state_facts()
        diff = diff_facts(facts_before, facts_after)
        operators = cache.parsed["plans"][solution_index]["operators"]
        result = {
            "ok": True,
            "solutionIndex": solution_index,
            "applied": operators,
            "added": diff["added"],
            "removed": diff["removed"],
        }
        if include_facts:
            result["facts"] = facts_after
        return result

    def apply_operator(self, operator: str, include_facts: bool = False) -> dict:
        """Plan ``operator`` as a single-task goal and apply the result.

        Returns a structured result. On precondition failure, returns
        ``{"ok": False, "code": "preconditions_failed", ...}`` rather than
        raising.
        """
        g = _ensure_period(operator)
        operator_clean = _strip_trailing_period(operator)
        # Snapshot state BEFORE planning. For direct primitive-operator goals
        # (no method decomposition above them), FindAllPlansCustomVariables
        # already mutates the rule set as part of resolving the operator —
        # so taking facts_before AFTER planning would yield a no-op diff
        # against facts_after, even though the operator clearly changed state.
        facts_before = self.state_facts()
        error, raw = self.planner.FindAllPlansCustomVariables(g)
        if error is not None:
            # The engine raises a runtime_error during plan construction when
            # a del() clause references a fact not in state. That's the
            # operator-level precondition signal — surface it as
            # preconditions_failed rather than a generic compile error.
            if "Can't retract" in error or "doesn't exist" in error:
                return {
                    "ok": False,
                    "code": "preconditions_failed",
                    "operator": operator_clean,
                    "failedPrecondition": _extract_missing_fact(error),
                    "error": _sanitize_engine_error(error),
                }
            return {
                "ok": False,
                "code": "compile_error",
                "operator": operator_clean,
                "error": _sanitize_engine_error(error),
            }
        parsed = parse_plans(raw)
        if not parsed.get("ok"):
            failed = extract_failed_precondition(parsed.get("rawFailure", []))
            return {
                "ok": False,
                "code": "preconditions_failed",
                "operator": operator_clean,
                "failedPrecondition": failed,
                "failureContext": parsed.get("failureContext", []),
            }
        if parsed.get("planCount", len(parsed.get("plans", []))) > 1:
            # Multiple distinct unifications resolved the call. Refuse to
            # silently pick one — the caller almost certainly didn't mean
            # to apply a non-determined operator.
            candidates = [
                {"operators": p["operators"]}
                for p in parsed["plans"]
            ]
            return {
                "ok": False,
                "code": "ambiguous_unification",
                "operator": operator_clean,
                "candidates": candidates,
                "note": (
                    "The operator unified with multiple bindings against "
                    "current state. Disambiguate by binding the free "
                    "variables before applying, or call apply_plan after "
                    "find_plans to pick a specific solution."
                ),
            }
        ops = parsed["plans"][0]["operators"]
        if len(ops) != 1:
            return {
                "ok": False,
                "code": "expanded_to_multiple_ops",
                "operator": operator_clean,
                "emitted": ops,
                "note": (
                    "The requested call decomposed into multiple operators — "
                    "looks like a method, not a primitive operator. Use "
                    "apply_plan if that's intended."
                ),
            }
        # Cache so subsequent decomposition-tree / preview queries work.
        self.last_plan_result = PlanCache(goal=g, raw_json=raw, parsed=parsed)
        ok = self.planner.ApplySolution(0)
        if not ok:
            return {
                "ok": False,
                "code": "apply_failed",
                "operator": operator_clean,
            }
        facts_after = self.state_facts()
        diff = diff_facts(facts_before, facts_after)
        result = {
            "ok": True,
            "operator": ops[0],
            "added": diff["added"],
            "removed": diff["removed"],
        }
        if include_facts:
            result["facts"] = facts_after
        return result

    # ------------------------------------------------------------------
    # Plan inspection
    # ------------------------------------------------------------------

    def decomposition_tree(self, solution_index: int = 0) -> Any:
        if self.last_plan_result is None:
            raise RuntimeError("No plan cached. Call find_plans first.")
        error, raw = self.planner.GetDecompositionTree(solution_index)
        if error is not None:
            raise RuntimeError(f"GetDecompositionTree: {error}")
        return json.loads(raw) if raw else []

    def preview_solution_facts(self, solution_index: int = 0) -> dict:
        if self.last_plan_result is None:
            raise RuntimeError("No plan cached. Call find_plans first.")
        error, raw = self.planner.GetSolutionFacts(solution_index)
        if error is not None:
            raise RuntimeError(f"GetSolutionFacts: {error}")
        after = parse_facts(raw)
        before = self.state_facts()
        diff = diff_facts(before, after)
        return {
            "solutionIndex": solution_index,
            "facts": after,
            "added": diff["added"],
            "removed": diff["removed"],
        }

    def parallelized_plan(self, solution_index: int = 0) -> Any:
        if self.last_plan_result is None:
            raise RuntimeError("No plan cached. Call find_plans first.")
        error, raw = self.planner.GetParallelizedPlan(solution_index)
        if error is not None:
            raise RuntimeError(f"GetParallelizedPlan: {error}")
        return json.loads(raw) if raw else {}

    # ------------------------------------------------------------------
    # State manipulation
    # ------------------------------------------------------------------

    def add_facts(self, facts: Iterable[str]) -> dict:
        # Route adds through the engine's ``assert/1`` rule rather than
        # ``HtnCompileCustomVariables``. The compile path adds rules to
        # the shared (immutable-at-runtime) rule store, which the engine
        # refuses to do while there are pending runtime fact diffs (e.g.
        # from a prior ``retract``). Using ``assert`` keeps both add and
        # remove on the same diff layer so they compose: callers can
        # freely add → remove → add → remove a fact without hitting an
        # ``AddRule`` precondition assert.
        added: list[str] = []
        errors: list[dict] = []
        for fact in facts:
            fact_clean = _strip_trailing_period(fact)
            if "?" in fact_clean:
                errors.append({
                    "fact": fact,
                    "error": (
                        "Fact must be ground (no '?' variables). Got: "
                        f"{fact_clean!r}"
                    ),
                })
                continue
            error, _raw = self.planner.PrologQuery(f"assert({fact_clean}).")
            if error is not None:
                errors.append({"fact": fact, "error": _sanitize_engine_error(error)})
            else:
                added.append(fact_clean)
        return {"added": added, "errors": errors}

    def remove_facts(self, facts: Iterable[str]) -> dict:
        # Drive removal through the engine's built-in ``retract/1`` rule
        # instead of synthesising and compiling a one-shot HTN
        # operator+method pair per call. The previous approach grew the
        # ruleset's method table linearly with the number of remove_facts
        # calls in a session; ``retract`` mutates the same fact database
        # without adding rules.
        current = set(self.state_facts())
        to_remove = [
            _strip_trailing_period(f)
            for f in facts
            if _strip_trailing_period(f) in current
        ]
        missing = [
            _strip_trailing_period(f)
            for f in facts
            if _strip_trailing_period(f) not in current
        ]
        if not to_remove:
            return {"removed": [], "notPresent": missing}

        removed: list[str] = []
        for fact in to_remove:
            error, _raw = self.planner.PrologQuery(f"retract({fact}).")
            if error is not None:
                raise RuntimeError(
                    f"retract failed for {fact!r}: {error}"
                )
            removed.append(fact)
        return {"removed": removed, "notPresent": missing}

    # ------------------------------------------------------------------
    # Snapshots
    # ------------------------------------------------------------------

    def snapshot(self, name: str) -> Snapshot:
        snap = Snapshot(
            name=name,
            facts=self.state_facts(),
            sources_count=len(self.sources),
        )
        self.snapshots[name] = snap
        return snap

    def restore(self, name: str) -> dict:
        snap = self.snapshots.get(name)
        if snap is None:
            raise KeyError(f"Snapshot {name!r} not found")

        # Rebuild planner from sources up to the snapshot point. Sources
        # added after the snapshot are dropped. Sources kept at restore
        # time stay in self.sources even when their replay errors, so a
        # subsequent reset_state will fail loudly rather than silently
        # forget them (callers can spot the failure via replay[].error
        # per the response convention documented in server.py).
        self._recreate_planner()
        kept_sources = self.sources[: snap.sources_count]
        self.sources = list(kept_sources)
        replay_results = []
        for src in kept_sources:
            err = self._replay_one(src)
            replay_results.append({"label": src.label, "error": _sanitize_engine_error(err)})

        current = self.state_facts()
        current_set = set(current)
        target_set = set(snap.facts)
        to_add = sorted(target_set - current_set)
        to_remove = sorted(current_set - target_set)

        if to_add:
            add_result = self.add_facts(to_add)
            if add_result["errors"]:
                raise RuntimeError(
                    f"Snapshot restore: failed to add facts: {add_result['errors']}"
                )
        if to_remove:
            self.remove_facts(to_remove)

        return {
            "name": name,
            "factsCount": len(self.state_facts()),
            "replay": replay_results,
            "factsAdded": to_add,
            "factsRemoved": to_remove,
        }

    def list_snapshots(self) -> list[dict]:
        return [s.to_summary() for s in self.snapshots.values()]

    def delete_snapshot(self, name: str) -> bool:
        return self.snapshots.pop(name, None) is not None

    # ------------------------------------------------------------------
    # Tracing
    # ------------------------------------------------------------------

    def set_trace(
        self,
        enabled: bool,
        also_stdout: bool = False,
        trace_type: Optional[int] = None,
        trace_detail: Optional[int] = None,
    ) -> dict:
        self.planner.SetDebugTracing(enabled)
        if trace_type is not None and trace_detail is not None:
            self.planner.SetLogLevel(trace_type, trace_detail)
        if enabled and not self.trace_capturing:
            self.planner.StartTraceCapture(alsoOutputToStdout=also_stdout)
            self.trace_capturing = True
        elif (not enabled) and self.trace_capturing:
            self.planner.StopTraceCapture()
            self.trace_capturing = False
        return {"enabled": enabled, "alsoStdout": also_stdout}

    def get_traces(self, clear_after: bool = True) -> str:
        traces = self.planner.GetCapturedTraces()
        if clear_after:
            self.planner.ClearTraceBuffer()
        return traces or ""

    def get_resolution_steps(self) -> int:
        return self.planner.GetLastResolutionStepCount()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def summary(self) -> dict:
        return {
            "sessionId": self.session_id,
            "createdAt": self.created_at.isoformat(),
            "lastAccessed": self.last_accessed.isoformat(),
            "debug": self.debug,
            "memoryBudget": self.memory_budget,
            "loadedSources": [
                {"label": s.label, "kind": s.kind, "dialect": s.dialect}
                for s in self.sources
            ],
            "snapshots": [s.to_summary() for s in self.snapshots.values()],
            "hasPlanCache": self.last_plan_result is not None,
            "traceCapturing": self.trace_capturing,
        }


class SessionManager:
    """Owns and dispatches HtnSession instances."""

    def __init__(self, planner_class=None, max_sessions: int = 10):
        if planner_class is None:
            planner_class = load_planner_class()
        self.planner_class = planner_class
        self.sessions: dict[str, HtnSession] = {}
        self.max_sessions = max_sessions
        # Global trace state in the C++ side is process-wide; serialize.
        self.trace_lock = asyncio.Lock()

    async def create_session(
        self, debug: bool = False, memory_budget: Optional[int] = None
    ) -> HtnSession:
        if len(self.sessions) >= self.max_sessions:
            self._evict_oldest()
        session = HtnSession(
            session_id=str(uuid.uuid4()),
            planner_class=self.planner_class,
            debug=debug,
            memory_budget=memory_budget,
        )
        self.sessions[session.session_id] = session
        logger.info("Created session %s", session.session_id)
        return session

    def get(self, session_id: str) -> HtnSession:
        session = self.sessions.get(session_id)
        if session is None:
            raise KeyError(f"Session {session_id!r} not found")
        session.touch()
        return session

    async def end_session(self, session_id: str) -> bool:
        session = self.sessions.pop(session_id, None)
        if session is None:
            return False
        try:
            del session.planner
        except Exception:
            pass
        logger.info("Ended session %s", session_id)
        return True

    async def end_all(self) -> int:
        ids = list(self.sessions.keys())
        for sid in ids:
            await self.end_session(sid)
        return len(ids)

    def list_sessions(self) -> list[dict]:
        return [s.summary() for s in self.sessions.values()]

    def _evict_oldest(self) -> None:
        if not self.sessions:
            return
        oldest = min(self.sessions.values(), key=lambda s: s.last_accessed)
        logger.info("Evicting oldest session %s", oldest.session_id)
        self.sessions.pop(oldest.session_id, None)
