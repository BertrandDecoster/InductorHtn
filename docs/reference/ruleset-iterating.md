# Ruleset Iterating

> **Ruleset doc trio.** Syntax (`ruleset-htn-syntax.md`) - keywords. Writing
> (`ruleset-writing.md`) - heuristics + measured optimizations. **Iterating**
> (this file) - interact with, debug, analyze, and improve a ruleset you already
> have. Tool mechanics (REPL, Python, GUI, MCP, components CLI) live in
> [`../TOOLS.md`](../TOOLS.md); this file is the *workflows* that use them.

The engine is a total-order forward-decomposition planner (SHOP model): tasks
decompose left-to-right, effects apply forward, search is stackless DFS. You
debug a ruleset by querying the planner, not by reading it.

## The iteration loop

Work bottom-up so a failure is localized, and let the tools tell you what's wrong:

1. **`indhtn_lint`** -- fix syntax. Know the benign noise: `SEM002` (undefined
   predicate -- runtime-injected facts), `SEM004/005` (alternate-entry "dead
   code" reachable via other goals), `SEM006` (intended recursion), `HTN005`
   (empty `do()` base case), and `SYN012` on `hidden`/`parallel` used as atoms
   (the engine accepts them; the linter can't parse them). Trust the engine over
   the linter when they disagree.
2. **`indhtn_introspect`** -- confirm methods/operators/facts parsed as intended.
3. **`indhtn_find_plans`** -- verify the goal yields the expected *set* of plans;
   `indhtn_get_decomposition_tree` shows the hierarchy and bindings.
4. **`indhtn_method_failures`** -- when you get *fewer* plans than expected, this
   says which method's gate or body subtask blocked (below). Run it before
   hand-flipping facts.
5. **Scenario testing** -- `indhtn_snapshot_state` / `add_facts` / `remove_facts`
   / `restore_state` to flip preconditions and confirm each branch fires;
   `indhtn_apply_plan` + `indhtn_list_facts` to verify effects.

## Why a strategy didn't fire (method-failure analysis)

When a goal yields fewer plans than expected, `indhtn_method_failures` reports,
per method clause, a **`furthestCompleted`** histogram (an `N+1` array for a
method with `N` body subtasks):

| Reading | Meaning | Fix |
|---------|---------|-----|
| `gateFailCount > 0`, `groundingsN == 0`, `furthestCompleted == []` | the `if()` gate never held -- the body was never entered | add/adjust the facts the precondition queries |
| mass at index `k < N` | gate cleared, but the body blocks at subtask `k` | make subtask `k` succeed (`positions[k]` names it) |
| mass at index `N` (`successS > 0`) | the method completes locally | the problem is downstream -- move on |

The loop: read the histogram, add what the named gate/subtask needs, re-run, watch
the mass move rightward toward index `N`. Caveat: `anyOf`/`allOf`/`parallel()`
merge groundings -- diagnose their inner tasks via those tasks' own entries.
Needs an engine built with `INDHTN_CHOICE_TRACKING` (the repo build qualifies).
Full reference: `../upgrades/method-failure-tracking.md`.

## The execute -> sense -> replan loop

A planner plans against a snapshot; a game then *executes* while sensors mutate
the world and *replans* when the running plan is invalidated. Drive it with
existing tools, no engine changes:

```
indhtn_snapshot_state  "t0"
indhtn_find_plans      "attackEnemy(...)."     # plan against current world
# step the plan:
indhtn_apply_operator  "<next op>"             # ok:true -> continue
                                               # ok:false, preconditions_failed -> the world moved
# a sensor fires (world changed independently):
indhtn_add_facts / indhtn_remove_facts
indhtn_find_plans      "attackEnemy(...)."     # replan from the new state
```

`apply_operator`'s `preconditions_failed` result **is** the plan-invalidation
signal. Replan on *exogenous* (sensor) changes, not on your own operators'
forward effects -- otherwise a higher-priority method can hijack a plan mid-run.
See `../reference/challenge-play-protocol.md` for the step-through protocol.

## Validating an optimization

Resolution-step counting (enabled by default, `INDHTN_TRACK_RESOLUTION_STEPS=ON`)
lets you prove a rewrite is actually faster:

```python
from indhtnpy import HtnPlanner
p = HtnPlanner(False)
p.PrologCompileCustomVariables(code)          # ?-prefixed variables
p.PrologQuery(query)
steps = p.GetLastResolutionStepCount()
```

Compare slow vs fast on the *same* query; >20% fewer steps is a real win. Worked
harness with re-runnable slow/fast pairs: `prototypes/optimization-proofs/`
(see `ruleset-writing.md` for the validated patterns it proves).

## Runtime gotchas

- **`remove_facts` matches the stored string exactly** -- `"trunkHealth(t, 3)"`
  (with a space) misses `trunkHealth(t,3)`.
- **Use the custom-variables entry points** (`HtnCompileCustomVariables`,
  `PrologCompileCustomVariables`) for any `?varname` file in this repo; the plain
  `HtnCompile`/`PrologCompile` paths expect standard-Prolog capitalized variables.
- **`del()` must be ground at apply time**; a free variable fails with "Items to
  be removed must be ground."
- **Loaders are strict UTF-8** -- em/en dashes and smart quotes break file loads;
  keep sources ASCII.
- **Raise the memory budget** (`memoryBudgetBytes`) for large plan enumerations;
  the 1 MB default dies on hundreds of plans.

## See also

- [`../TOOLS.md`](../TOOLS.md) and `../tools/mcp-server.md` -- full tool surface.
- `../upgrades/method-failure-tracking.md`, `../upgrades/query-tracing.md`.
- `prototypes/fortress-loadout/sweep.py` -- balancing/tuning a finished ruleset
  (dead methods, dominant loadouts, leaked baselines).
