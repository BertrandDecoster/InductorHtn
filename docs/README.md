# InductorHTN Documentation

All documentation lives here. Root keeps only `CLAUDE.md` (AI core rules) and
`BUILD.md` (build/test commands).

## Map

| Area | Where | What |
|------|-------|------|
| **Tools** | [`TOOLS.md`](TOOLS.md) → `tools/` | Every executable/interface: REPL, tests, Python bindings, GUI, MCP server, components CLI |
| **Design** | [`DESIGN.md`](DESIGN.md) → `design/` | Why things are the way they are: legacy engine, language, HDDL, online rulesets |
| **Reference** | [`reference/`](reference/) | Deep manuals: ruleset writing / syntax / creating / iterating (the quartet) plus the design-policy register (`ruleset-policies.md`), Prolog, planner internals, component system, build setup, challenge-play protocol; [`reference/exemplars/`](reference/exemplars/) holds classic HTN domains (Blocks World, Logistics, Barman, Rover) translated to InductorHTN syntax |
| **Upgrades** | [`upgrades/`](upgrades/) | What this fork added over upstream: new ruleset keywords, query tracing, method-failure tracking |
| **Legacy** | [`legacy/`](legacy/) | ⚠️ Original upstream InductorHtn docs — superseded, kept for history |
| **Game design** | [`game-design/`](game-design/) | Product/game design drafts for "The Companions" |
| **Other games** | [`other_games/`](other_games/) | Team-coordination beats from great team-based games, mined into reusable HTN method/operator patterns |
| **Plans** | [`plans/`](plans/) | Dated design and review records |

## Quick links

- New to the engine? → [`legacy/engine-readme.md`](legacy/engine-readme.md) for background, then [`reference/ruleset-writing.md`](reference/ruleset-writing.md)
- Writing a ruleset? → [`reference/ruleset-writing.md`](reference/ruleset-writing.md) (heuristics, examples, validated optimizations)
- Creating a level from a design brief? → [`reference/ruleset-creating.md`](reference/ruleset-creating.md) (the end-to-end workflow with the fun gates: causal depth 3-5, diversity, dominance) or the `/htn-create` slash command
- Is the ruleset actually *interesting*? → the DAG tool (`python -m indhtn_quality.dag`) and the loadout-sweep harness (`python -m indhtn_quality.harness`), or the `/htn-audit` slash command
- A recurring design call (latent mechanics, combos, benign lint)? → [`reference/ruleset-policies.md`](reference/ruleset-policies.md) (the policy register; POL-7 is the canonical benign-lint list)
- Want a worked example to copy? → [`reference/exemplars/`](reference/exemplars/) (classic HTN domains in InductorHTN syntax, one per design pattern)
- Improving a ruleset from an instruction? → the `/htn-improve` slash command (`.claude/commands/htn-improve.md`): loads the syntax docs + exemplars, edits in place, verifies by planning
- Which keyword, and when? → [`reference/ruleset-htn-syntax.md`](reference/ruleset-htn-syntax.md) (syntax/keyword reference)
- Debugging / improving a ruleset? → [`reference/ruleset-iterating.md`](reference/ruleset-iterating.md), [`tools/mcp-server.md`](tools/mcp-server.md), [`upgrades/method-failure-tracking.md`](upgrades/method-failure-tracking.md)
