# New Ruleset Keywords

Ruleset-language capabilities this fork added over upstream InductorHtn. Full
syntax for these (and all other keywords) is in
[`../reference/htn-syntax.md`](../reference/htn-syntax.md); the component-system
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
all `add()` additions. See [`../reference/htn-syntax.md`](../reference/htn-syntax.md)
for full semantics and failure modes.

## Typed parameters

Components and levels may opt into argument type-checking by declaring two
conventional facts:

```prolog
type(typeName, instance).
signature(predName, [argType1, argType2, ...]).
```

The engine treats both as ordinary facts and never queries them at planning
time — they exist purely for the linter (`TYP001`/`TYP002` diagnostics). The
rule is fully opt-in: rulesets with no `signature/2` declarations get no `TYP*`
diagnostics. Numeric literals satisfy the built-in `int`/`float`/`number` types
interchangeably. See [`../reference/component-system.md`](../reference/component-system.md)
for the full type-checking rules and namespace caveats.
