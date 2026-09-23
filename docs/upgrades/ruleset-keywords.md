# New Ruleset Keywords

Ruleset-language capabilities this fork added over upstream InductorHtn. Full
syntax for these (and all other keywords) is in
[`../reference/ruleset-htn-syntax.md`](../reference/ruleset-htn-syntax.md); the component-system
type rules are in [`../reference/component-system.md`](../reference/component-system.md).

## `parallel()` — parallel execution

The `parallel()` keyword marks tasks for concurrent execution through
post-processing.

```prolog
% Tasks within parallel() can execute concurrently
workflow() :- if(), do(setup, parallel(movePlayer, moveWarden), cleanup).
movePlayer :- del(playerAt(a)), add(playerAt(b)).
moveWarden :- del(wardenAt(x)), add(wardenAt(y)).
```

**How it works:**
- During planning: tasks are planned sequentially (no search explosion).
- Plan output: contains `beginParallel`/`endParallel` markers.
- Post-processing: `PlanParallelizer` assigns timesteps for parallel execution.

**Key files:**
- `src/FXPlatform/Htn/HtnPlanner.cpp` — `parallel()` handling in `CheckForSpecialTask()`
- `src/FXPlatform/Htn/PlanParallelizer.h/cpp` — post-processor for timestep assignment
- `src/Tests/Htn/HtnParallelTests.cpp` — test suite

**Python API:**
```python
error, parallelized = planner.GetParallelizedPlan(solutionIndex)
# JSON: {"operators": [{"operator": "taskA", "timestep": 0, "scopeId": 1, "dependsOn": []}, ...]}
```

**Design notes:**
- The domain author is responsible for ensuring tasks within `parallel()` are truly independent.
- Tasks in the same parallel scope get the same timestep (can run concurrently).
- Avoids the exponential complexity of partial-order planning.

## Numeric fluent effects — `increase` / `decrease`

For facts of shape `pred(arg1, ..., argN, value)` with a numeric `value`,
operators may modify the value directly instead of the verbose `del`+`add`+`is`
pattern:

```prolog
opGain(?n) :- increase(score(player), ?n).
opLose(?n) :- decrease(score(player), ?n).
opSwap(?a, ?b) :- decrease(mana(?a), 10), increase(mana(?b), 10).
```

The delta expression uses the same arithmetic engine as `is/2`. Effect ordering
within one operator: all `del()` removals, then all `increase`/`decrease`, then
all `add()` additions. See [`../reference/ruleset-htn-syntax.md`](../reference/ruleset-htn-syntax.md)
for full semantics and failure modes.

## Typed parameters

The linter infers argument types from the **unary facts** a ruleset already
declares (`skill(frostNova).` ⇒ `frostNova : skill`) and emits `TYP010` when an
argument's type is provably disjoint from its position — including variables.
An optional `%:: pred(?v: type, ...)` comment directive above a rule pins a
contract the engine ignores. The old `type/2`/`signature/2` facts are no longer
read. See [`../reference/component-system.md`](../reference/component-system.md)
and [`../reference/ruleset-htn-syntax.md`](../reference/ruleset-htn-syntax.md)
("Types") for the full rules.
