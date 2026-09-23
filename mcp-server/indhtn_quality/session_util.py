"""In-process MCP session helpers shared by the DAG tool and the harness.

Wraps indhtn_mcp.server.create_server behind a small async context manager so
drivers stop copy-pasting session setup/teardown (the pattern lifted from
prototypes/fortress-loadout/sweep.py).
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from indhtn_mcp.server import create_server

DEFAULT_MEMORY_BUDGET = 256 * 1024 * 1024


class QualitySession:
    """One planner session over a loaded level, with the raw source kept
    around for static analysis."""

    def __init__(self, srv, sid: str, source_text: str):
        self._srv = srv
        self.sid = sid
        self.source_text = source_text

    async def call(self, tool: str, **args) -> dict:
        return await self._srv.call_tool_direct(tool, {"sessionId": self.sid, **args})

    async def query_all(self, q: str) -> List[dict]:
        res = await self.call("indhtn_query", query=q)
        return res.get("solutions", []) or []

    async def find_plans(self, goal: str, max_plans: Optional[int] = None) -> dict:
        args = {"goal": goal, "includeRaw": True}
        if max_plans is not None:
            args["maxPlans"] = max_plans
        return await self.call("indhtn_find_plans", **args)

    async def tree(self, solution_index: int = 0) -> List[dict]:
        res = await self.call("indhtn_get_decomposition_tree", solutionIndex=solution_index)
        nodes = res.get("tree", []) or []
        # The engine returns nodes for every solution up to solutionIndex;
        # keep only the requested solution's tree.
        return [n for n in nodes if n.get("solutionID", solution_index) == solution_index]

    async def state_facts(self) -> List[str]:
        res = await self.call("indhtn_list_facts")
        return res.get("facts", []) or []

    async def add_facts(self, facts: Iterable[str]) -> dict:
        return await self.call("indhtn_add_facts", facts=list(facts))

    async def reset_state(self) -> dict:
        return await self.call("indhtn_reset_state")

    async def close(self) -> None:
        await self.call("indhtn_end_session")


class open_session:
    """Async context manager: open a session over files or inline source.

    async with open_session(paths=[...], facts=[...]) as qs: ...
    """

    def __init__(self, *, paths: Optional[Sequence[str]] = None,
                 source: Optional[str] = None,
                 facts: Iterable[str] = (),
                 memory_budget: Optional[int] = DEFAULT_MEMORY_BUDGET):
        if (paths is None) == (source is None):
            raise ValueError("provide exactly one of paths= or source=")
        self._paths = [str(p) for p in paths] if paths else None
        self._source = source
        self._facts = list(facts)
        self._memory_budget = memory_budget
        self._qs: Optional[QualitySession] = None

    async def __aenter__(self) -> QualitySession:
        srv = create_server()
        args = {}
        if self._memory_budget is not None:
            args["memoryBudgetBytes"] = self._memory_budget
        sid = (await srv.call_tool_direct("indhtn_create_session", args))["sessionId"]
        if self._paths is not None:
            load = await srv.call_tool_direct(
                "indhtn_load_files", {"sessionId": sid, "paths": self._paths})
            source_text = "\n".join(
                Path(p).read_text(encoding="utf-8") for p in self._paths)
        else:
            load = await srv.call_tool_direct(
                "indhtn_load_source", {"sessionId": sid, "source": self._source})
            source_text = self._source
        if not load.get("ok", False):
            await srv.call_tool_direct("indhtn_end_session", {"sessionId": sid})
            raise RuntimeError(f"failed to load level: {load}")
        qs = QualitySession(srv, sid, source_text)
        if self._facts:
            await qs.add_facts(self._facts)
        self._qs = qs
        return qs

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._qs is not None:
            await self._qs.close()


def run(coro):
    """Sync wrapper for CLI entry points."""
    return asyncio.run(coro)
