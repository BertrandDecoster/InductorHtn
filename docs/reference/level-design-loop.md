# Level Design Loop

How a level is iterated in this repo. The planner is an oracle for *what can
be done*; the scorecard describes *the shape of the solution space*; the
player-perspective MCP tools are the closest thing to a playtest without a
human. None of them says a level is fun. The loop below uses each for what
it is good at, and ends with a human.

## The loop

```
state one hypothesis            (numbers kept as funExpect; the idea as funIntended)
   -> change ONE rule (a fact, a method, a component)
   -> certify (bottom-up); verify gates on funExpect + F7 intent
   -> play it through the MCP level tools, as the player
   -> explain + fun (afterwards, the planner's view)
   -> compare metrics and recorded decisions with the hypothesis
   -> a human tries the promising version and records a rating (fun-rate)
```

The shape matches what the literature on generation loops converges on (see
`docs/research/fun-cross-reference.md` §4):
- The agent proposes and symbolic checks certify (ChatHTN; LLM-built PDDL).
- Hard gates are kept apart from soft signals.
- The agent reads per-family findings, never one scalar (Eureka's reflection).
- One change at a time serves as attribution.
- A human signal is held back from the agent so gaming shows up.

### 1. State one hypothesis

Write it in the level's `design.md` before touching anything. It names the
experience you want and the numbers you expect to move:

> Two ideas; median plan 6-12 operators; encounter feasibility 0.2-0.4 with
> no mandatory pick; at least two player decision points; teamwork edges
> above 0.3; no single companion carries a plan alone.

A hypothesis without a number is a wish. A number without an experience is a
target to game.

Keep the numbers in `level.htn` as well, so the hypothesis outlives this
iteration and `verify` re-checks it whenever a shared component changes:

```prolog
funExpect(strategy_classes, atLeast, 2).
funExpect(f6_player, player_decision_points, atLeast, 2).
funExpect(plan_length_median, atMost, 12).
```

Name the idea the level is *about*, and anything that must never win:

```prolog
funIntended(combo, opSynchronize).     % every plan must use a member of `combo`
funForbidden(opBribe).
```

This is "quantifying over play" (Smith et al. 2013). F7 fails any plan that
skips the idea, and nothing else in the scorecard can see a well-built
shortcut.

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
certified, so order matters. `verify` ends with the fun scorecard. The
scorecard does not gate, with two exceptions, both of them the author's own
declarations: a missed `funExpect` fails `verify`, and so does an F7 intent
fail. A gate failure rejects the change; it is not traded against score.

### 4. Play it as the player

Through the MCP server (`.mcp.json` starts it; `/mcp` shows `indhtn`):

```
indhtn_load_level("gamehack_mvp")        -> levelSessionId, observation, actions
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
indhtn_fun("gamehack_mvp", ablate=true, loadouts=true)
```

or from the shell:

```bash
PYTHONPATH=src/Python python -m htn_components fun <level> --ablate --loadouts -v
PYTHONPATH=src/Python python -m htn_components play <level> --class theSlipstream
PYTHONPATH=src/Python python -m htn_components fun-compare <before> <after>
```

Read the families, not the composite. The composite is a diagnostic and is
never a target. Three readings guard against gaming:
- **Plan count up, `plan_uniqueness` down:** the new plans are padding (a
  detour added to an existing plan).
- **`solution_information_bits` near zero:** random method choice solves the
  level, so there is nothing to find.
- **`landmark_ratio` near 1:** every route shares most of its causal work.

In F6, `single_actor_plans` is the pillar (one companion carried a plan
alone: a fail). `soloable_plans`, `player_load` and the
decision points describe the seat you gave the human; they are warnings,
and the numbers to move when that seat feels idle, never violations.

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

Record the verdict:

```bash
PYTHONPATH=src/Python python -m htn_components fun-rate <level> --rating 1..5 --rater <who> --note "<why>"
```

The rating goes to `levels/fun_ratings.jsonl` next to the level's scorecard
and source hash. It is held out: the agent iterating on a level does not
read it. Once enough ratings exist, `fun-calibrate` shows which metrics
track human judgement. That is the evidence for moving a band in
`metrics.json`, and for adding the upper band F5 deliberately lacks.

### 8. Across levels

```bash
PYTHONPATH=src/Python python -m htn_components fun-all --range solution_information_bits teamwork_edge_ratio
```

This is expressive range analysis (Smith & Whitehead 2010). If every level
lands in one cell, the loop is making one level repeatedly, however good
that cell is. Pick the next hypothesis to reach an empty cell.

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
| Human ratings (held out) | `levels/fun_ratings.jsonl` |
| Why the loop and metrics look like this | `docs/research/fun-cross-reference.md` |
