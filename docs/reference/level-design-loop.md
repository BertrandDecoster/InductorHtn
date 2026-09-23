# Level Design Loop

How a level is iterated in this repo. The planner is an oracle for *what can
be done*; the scorecard describes *the shape of the solution space*; the
player-perspective MCP tools are the closest thing to a playtest without a
human. None of them says a level is fun. The loop below uses each for what
it is good at, and ends with a human.

## The loop

```
state one hypothesis
   -> change ONE rule (a fact, a method, a component)
   -> certify (bottom-up)
   -> play it through the MCP level tools, as the player
   -> explain + fun (afterwards, the planner's view)
   -> compare metrics and recorded decisions with the hypothesis
   -> a human tries the promising version before it is kept
```

### 1. State one hypothesis

Write it in the level's `design.md` before touching anything. It names the
experience you want and the numbers you expect to move:

> Two ideas; median plan 6-12 operators; encounter feasibility 0.2-0.4 with
> no mandatory pick; at least two player decision points; teamwork edges
> above 0.3; nobody solos.

A hypothesis without a number is a wish. A number without an experience is a
target to game.

### 2. Change one rule

One fact, one method alternative, one component at a time. The scorecard
runs many re-plans; if three things changed you will not know which one moved
the number. Prefer the cheapest source of depth: a `reacts`/`blast`/`terrain`
fact (chemistry) before a new method, a new method before a new operator, a
new operator before a new component.

### 3. Certify, bottom-up

```bash
PYTHONPATH=src/Python python -m htn_components certify core/primitives/<name>
PYTHONPATH=src/Python python -m htn_components certify core/strategies/<name>
PYTHONPATH=src/Python python -m htn_components certify core/goals/<name>
PYTHONPATH=src/Python python -m htn_components certify levels/<level>
PYTHONPATH=src/Python python -m htn_components verify <level>     # deps + tests + plan + scorecard
```

The linter only knows a dependency's `provides` after that dependency is
certified, so order matters. `verify` ends with the fun scorecard; it is
printed, never gating.

### 4. Play it as the player

Through the MCP server (`.mcp.json` starts it; `/mcp` shows `indhtn`):

```
indhtn_load_level("grease_trap")        -> levelSessionId, observation, actions
indhtn_observe(id)                      -> what the player sees, companions' intentions
indhtn_actions(id)                      -> the player's own legal moves (+ "wait")
indhtn_act(id, action)                  -> take one; companions auto-advance
indhtn_act(id, action, force=true)      -> an off-plan move; re-plans from the result
indhtn_undo(id)
```

Rules of the playtest:

- Do not call `indhtn_explain` or `indhtn_state` while playing. They are the
  planner's view. Decide from `observe` and `actions` only, the way the
  player would.
- Try the obvious thing first. If the obvious thing is the only thing, the
  level has no decision.
- Make at least one mistake with `force=true` (waste a charge, move the
  wrong companion) and see whether the level recovers or dead-ends. Both are
  fine; silent is not.
- Play every strategy class the scorecard lists. If you could not reach one
  from the player's seat, it is not a real option.

Every session writes `.playthroughs/<level>/<timestamp>.json`: what was
offered, what was chosen, what was forced. Keep them; they are the data the
playthrough-derived metrics will be built on.

### 5. Explain and score, afterwards

```
indhtn_explain(id)     -> class reached, classes missed, alternatives at each decision
indhtn_fun("grease_trap", ablate=true, loadouts=true)
```

or from the shell:

```bash
PYTHONPATH=src/Python python -m htn_components fun <level> --ablate --loadouts -v
PYTHONPATH=src/Python python -m htn_components play <level> --class theSlipstream
PYTHONPATH=src/Python python -m htn_components fun-compare <before> <after>
```

Read the families, not the composite. The composite is a diagnostic and is
never a target.

### 6. Compare with the hypothesis

For each number in the hypothesis: did it move the way you said? For the
playthrough: did the decision you meant to create show up in
`actions_offered` with at least two entries, and did `explain` list the
alternative you meant as the road not taken?

A change that improves the scorecard and removes a decision is a regression.

### 7. A human tries it

Before a version is kept, someone who did not write it plays it (the GUI, the
REPL, or the MCP tools with the rules above). Structural analysis needs
qualitative playtesting beside it; telemetry alone is how levels get worse
while their numbers get better.

## What the tools cannot see

- Timing, positioning inside a region, animation, anything the engine
  handles. The HTN is room-level by design.
- Whether a decision is *interesting* - only whether it exists and has
  consequences.
- The composite is a weighted mean of verdicts. Two levels with the same
  composite can be nothing alike.

## Where things live

| Thing | Place |
|-------|-------|
| The loop's rules | this file |
| Metric definitions, bands, blind spots | `docs/FUN_METRICS.md` |
| Bands and weights | `src/Python/htn_metrics/metrics.json` |
| Core vocabulary and operator rules | `docs/reference/component-system.md` |
| MCP tools | `docs/tools/mcp-server.md`, `mcp-server/indhtn_mcp/level_tools.py` |
| Playthrough records | `.playthroughs/` (gitignored) |
