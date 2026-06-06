# Method Failure Analysis — finding where a method's decomposition fails

> Reference doc (not auto-loaded). Reached from `src/Python/htn_evaluator.py`.
> Built on the planner's in-flight instrumentation (`INDHTN_CHOICE_TRACKING` /
> `GetChoiceStats` — "choice" there refers to the method *choice points* the
> planner branches on). The *mechanism* (how the histogram is computed) lives in
> `docs/reference/planner-internals.md`; this file is the *usage* guide.

The planner records, across the **entire** backtracking search (not just
successful plans), *where every method got blocked*. Use it to debug and tune
rulesets: it pinpoints whether a method dies at its **precondition gate**, at a
specific **body subtask**, or completes — so you know exactly which facts/methods
to add.

## Turning it on / getting the data

- Build with `cmake -DINDHTN_CHOICE_TRACKING=ON -DINDHTN_TREE_SIBLING_TRACKING=ON`
  (both default-on except CHOICE_TRACKING). It compiles to nothing otherwise.
- Python: `planner.GetChoiceStats()` → `{"byAtom": [...], "byMethod": [...]}`
  (raises `RuntimeError` if not compiled in). `evaluate_level()` adds a
  `"choice_stats"` key.
- CLI: `PYTHONPATH=src/Python python -m htn_components evaluate <level>` prints the
  **By atom** and **By method** sections.

## What it produces

**By method** — one entry per method clause that was ever tried:

| field | meaning |
|-------|---------|
| `groundingsN` | # times the precondition passed (one body attempt per grounding) |
| `gateFailCount` | # times the precondition gate FAILED (method never entered its body) |
| `subtaskCount` (N) | # body subtasks |
| `furthestCompleted` | size N+1 histogram (see below); **sums to `groundingsN`** |
| `successS` | `furthestCompleted[N]` — groundings whose whole body completed |
| `positions[k]` | per body slot: `atomFunctor`, `tested`, `clears` (which resolving methods cleared their gate) |

**`furthestCompleted` is the key signal.** Index `k < N` = "completed subtasks
0..k-1 but blocked at subtask k"; index `N` = "completed the whole body". It is
**local**: completion is measured against the method's *own* body, so a downstream
sibling failing does NOT count against this method.

**By atom** — global rollup per task functor: `tested`, `fail` (times this atom
was the local blocker), and `clears` (per overloaded method, how often its gate
cleared — e.g. `TravelTo: Walk 3, Taxi 7`).

## How to read it (diagnosis)

- **`gateFailCount > 0`, `groundingsN == 0`** → the method's `if()` precondition
  never holds. The **gate** is the blocker. Fix: add/adjust the facts the
  precondition queries.
- **`furthestCompleted` mass at index `k < N`** → the method clears its gate but
  its body consistently dies at **subtask k** (`positions[k].atomFunctor` names
  it). Fix: make that subtask succeed — add the facts/methods it needs, or fix
  *its* precondition.
- **mass at index `N` (`successS > 0`)** → the method completes locally. If the
  overall plan still fails, the problem is **downstream** (a later sibling), not
  here — move on.
- **subtask/method absent from the stats** → it was never reached because an
  earlier sibling blocked first. Fix the earlier blocker before touching it.
- **mixed histogram** (e.g. `[0,1,1]` over 2 groundings) → the method succeeds for
  some bindings and blocks for others; cross-reference which grounding fails.

## Iteration workflow

1. Run `evaluate` / `GetChoiceStats` on the goal.
2. Walk methods top-down. Find the **first** with a failure: `gateFailCount > 0`,
   or `furthestCompleted` mass at index `< N`.
3. That index names the blocking gate or subtask. Add the facts (or fix the
   precondition) it needs.
4. Re-run. The histogram mass should move **rightward** (toward `N`). Repeat until
   the top-level method's `furthestCompleted[N] > 0` (a plan exists).

### Worked example

`craft :- if(...), do(find_enemy(?e), cast_spell(?s,?e), loot_body(?e)).`

`craft.furthestCompleted == [0, 5, 0]` (N=3) means: every grounding found an enemy
(subtask 0 completed) but **always blocked at `cast_spell`** (subtask 1) and never
reached `loot_body`. Don't touch movement or looting — fix what `cast_spell`'s gate
or body requires (e.g. add a `mana(player, _)` fact, or a method for `cast_spell`
whose precondition the state satisfies). Re-run; success when mass reaches index 3.

## Semantics caveats

- Counts aggregate over the **whole find-all search**: a subtask re-resolved via
  backtracking (e.g. a later sibling has multiple solutions) shows a higher
  `tested`/`groundingsN`. `furthestCompleted` always sums to `groundingsN`.
- `anyOf`/`allOf` clauses are **excluded** from the histogram (`methodType` labels
  them; report shows `partition=N/A`) because they merge groundings.
- **`parallel()` is not analyzed either.** A `parallel(...)` wrapper in a method's
  `do()` is treated as bookkeeping: it occupies no subtask position and its inner
  tasks are **not** tagged, so they get no by-method position attribution and do not
  count toward that method's `subtaskCount`/`furthestCompleted`. A method whose real
  work lives inside `parallel()` will therefore show a misleadingly short histogram —
  diagnose those inner tasks via their **own** by-method entries (or the by-atom view)
  instead. Same limitation, same reason as `anyOf`/`allOf`: the block doesn't expose a
  single linear grounding partition.
  - **TODO / known false-positive:** if a method's *entire* `do()` is a single
    `parallel(...)` (or is made up solely of wrapper terms), it has `subtaskCount == 0`,
    so the grounding is recorded as a **full success** (`successS++`) **even when the
    inner parallel work fails** — unlike `try()`, `parallel()` does not absorb failure.
    Until `parallel()` inner tasks are tagged as first-class subtasks, do not trust the
    by-method success count for such methods; read their inner tasks' own entries.
- The local-completion signal needs `INDHTN_TREE_SIBLING_TRACKING`; without it the
  histogram degrades to a continuation-based (less local) measure.
- **Repeated identical subtask in one `do()`** (known limitation): if a method body
  calls the *same fully-ground* subtask at two positions — e.g.
  `do(foo(x), foo(x))` — the by-method view attributes both to the **last**
  position, because attribution keys on the (interned, hence shared) term pointer.
  This only mis-slots between two positions of that one method; the **by-atom**
  counts and every other method are exact. Arithmetic-bearing subtasks
  (`opGain(+(2,3))`) are *not* affected — those are resolved and pinned before
  attribution. A decomposition-tree fix for the repeated-subtask case was
  considered and declined (too invasive vs. how rarely a body calls the identical
  ground subtask twice).

## Living examples (and how to extend)

These tests double as executable specs and generators:

- `src/Python/tests/test_choice_histogram_combinations.py` — exhaustive 256-case
  sweep (2 subtasks × 2 overloaded methods × 4 result states) with an independent
  predictive model; `make_ruleset(a,b,c,d)` generates rulesets by number.
- `src/Python/tests/test_choice_histogram_2unif.py` — 2-unification head with
  per-(method, grounding) result control, producing *mixed* histograms like
  `[0,1,1]`.
- `src/Tests/Htn/HtnChoiceTrackingTests.cpp` — C++ unit tests incl. the
  `furthestCompleted` partition invariant and the single-unification fail@1/2/3
  matrix.
