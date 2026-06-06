# InductorHTN Documentation

All documentation lives here. Root keeps only `CLAUDE.md` (AI core rules) and
`BUILD.md` (build/test commands).

## Map

| Area | Where | What |
|------|-------|------|
| **Tools** | [`TOOLS.md`](TOOLS.md) → `tools/` | Every executable/interface: REPL, tests, Python bindings, GUI, MCP server, components CLI |
| **Design** | [`DESIGN.md`](DESIGN.md) → `design/` | Why things are the way they are: legacy engine, language, HDDL, online rulesets |
| **Reference** | [`reference/`](reference/) | Deep manuals: HTN syntax, Prolog, planner internals, component system, authoring guide, build setup, challenge-play protocol |
| **Upgrades** | [`upgrades/`](upgrades/) | What this fork added over upstream: new ruleset keywords, query tracing, method-failure tracking |
| **Legacy** | [`legacy/`](legacy/) | ⚠️ Original upstream InductorHtn docs — superseded, kept for history |
| **Game design** | [`game-design/`](game-design/) | Product/game design drafts for "The Companions" |
| **Plans** | [`plans/`](plans/) | Dated design and review records |

## Quick links

- New to the engine? → [`legacy/engine-readme.md`](legacy/engine-readme.md) for background, then [`reference/authoring-rulesets.md`](reference/authoring-rulesets.md)
- Writing a ruleset? → [`reference/authoring-rulesets.md`](reference/authoring-rulesets.md)
- Debugging a plan? → [`tools/mcp-server.md`](tools/mcp-server.md), [`upgrades/query-tracing.md`](upgrades/query-tracing.md), [`upgrades/method-failure-tracking.md`](upgrades/method-failure-tracking.md)
