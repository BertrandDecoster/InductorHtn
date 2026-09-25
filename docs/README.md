# InductorHTN Documentation

All documentation lives here. Root keeps only `CLAUDE.md` (AI core rules) and
`BUILD.md` (build/test commands).

## Map

| Area | Where | What |
|------|-------|------|
| **Tools** | [`TOOLS.md`](TOOLS.md) → `tools/` | Every executable/interface: REPL, tests, Python bindings, GUI, MCP server, components CLI |
| **Design** | [`DESIGN.md`](DESIGN.md) → `design/` | Why things are the way they are: legacy engine, language, HDDL, online rulesets |
| **Reference** | [`reference/`](reference/) | The language spec, planner internals, component system, build setup, challenge-play protocol |
| **Authoring** | [`authoring/`](authoring/) | The owner's rubric and the pattern catalogue |
| **Upgrades** | [`upgrades/`](upgrades/) | What this fork added over upstream: new ruleset keywords, query tracing, method-failure tracking |
| **Legacy** | [`legacy/`](legacy/) | ⚠️ Original upstream InductorHtn docs — superseded, kept for history |
| **Game design** | [`game-design/`](game-design/) | Product/game design drafts for "The Companions" |
| **Plans** | [`plans/`](plans/) | Dated design and review records |
| **Research** | [`research/`](research/) | Literature cross-references behind the fun metrics and the design loop |

## Quick links

- Writing a ruleset? → [`reference/language.md`](reference/language.md) (the language, test-backed), [`authoring/rubric.md`](authoring/rubric.md) (what good looks like), [`authoring/patterns.md`](authoring/patterns.md) (patterns and examples), and the `htn-author` skill
- New to the engine? → [`legacy/engine-readme.md`](legacy/engine-readme.md) for background, then [`reference/language.md`](reference/language.md)
- Debugging a plan? → `python -m htn_components check <file> --goal "task."`, [`tools/mcp-server.md`](tools/mcp-server.md), [`upgrades/query-tracing.md`](upgrades/query-tracing.md), [`upgrades/method-failure-tracking.md`](upgrades/method-failure-tracking.md)
