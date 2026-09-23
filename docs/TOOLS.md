# Tools

Every executable and interface in the project. Each tool has its own page under
[`tools/`](tools/).

| Tool | Page | Purpose |
|------|------|---------|
| Interactive REPL (`indhtn`) | [`tools/indhtn-repl.md`](tools/indhtn-repl.md) | Quick interactive exploration of a ruleset |
| Unit test runner (`runtests`) | [`tools/runtests.md`](tools/runtests.md) | Run the C++ unit test suite |
| Python bindings (`indhtnpy`) | [`tools/python-bindings.md`](tools/python-bindings.md) | Drive the planner from Python via ctypes |
| Web IDE (GUI) | [`tools/gui.md`](tools/gui.md) | Visual editor, state diff, tree visualization |
| MCP server | [`tools/mcp-server.md`](tools/mcp-server.md) | Let an AI assistant drive the planner |
| Quality toolkit (`indhtn_quality`) | [`reference/ruleset-creating.md`](reference/ruleset-creating.md) | Ruleset->DAG converter with causal-depth gates (`python -m indhtn_quality.dag`) and the config-driven loadout-sweep harness (`python -m indhtn_quality.harness <quality.json>`); lives in `mcp-server/indhtn_quality/`, run with `PYTHONPATH=mcp-server` |
| Components CLI (`htn_components`) | [`tools/htn-components.md`](tools/htn-components.md) | Build, certify, test, and assemble reusable components |

## Related reference

- Iterating on rulesets with these tools (debug/analyze/improve): [`reference/ruleset-iterating.md`](reference/ruleset-iterating.md)
- Stepping through a level with MCP: [`reference/challenge-play-protocol.md`](reference/challenge-play-protocol.md)
