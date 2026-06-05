# Numeric Fluents (T0.6) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `increase(F, expr)` and `decrease(F, expr)` as operator effects, equivalent to the verbose `del/add/is` pattern for incrementing/decrementing the numeric tail of a fact. Engine-level support; no syntactic macro tricks.

**Why:** The `del/add` pattern for resource accumulation is verbose and easy to get wrong (`del(mana(player, ?old)), is(?new, -(?old, 5)), add(mana(player, ?new))` plus the precondition needed to bind `?old`). With first-class fluents, operators just say `decrease(mana(player), 5)`. This is purely an ergonomic refactor — the existing `del/add` pattern continues to work unchanged, and the two are observably equivalent in the final state.

**Non-goal:** Engine-side search-time reasoning about fluent values (admissible heuristics, branch-and-bound, etc.). Fluents are still ordinary facts; the planner treats them as such. Cost-based search is a separate work item (see HDDL.md T0.3 discussion).

**Architecture:**

- A new fact predicate `numericFact` is **not** introduced. Numeric fluents are conventional facts of shape `pred(arg1, ..., argN, value)` where the last argument is an integer or float. The convention is purely in the eye of the operator effect that references them.
- Operator definitions gain two new effect clauses alongside `del()` and `add()`: `increase(head, expr)` and `decrease(head, expr)`. Here `head` is the fact pattern without the trailing value (e.g. `mana(player)`), and `expr` is an arithmetic expression evaluable by the existing `is/2` machinery (`HtnGoalResolver::RuleIs`).
- At operator application time, after `del` removals and before `add` additions, the engine processes each `increase`/`decrease`:
  1. Substitute operator-parameter variables into `head` and `expr`.
  2. Query the current state for the unique fact matching `head(?Old)` (any ground extension of `head` by one trailing arg).
  3. Evaluate `expr` to a numeric value using the existing arithmetic evaluator.
  4. Remove the matched fact; add `head(?Old + delta)` (or `?Old - delta` for `decrease`).

**Tech stack:** C++ engine changes (`HtnCompiler`, `HtnOperator`, `HtnPlanner`), plus C++ tests in `src/Tests/Htn/` and Python parity tests in `tests/cpp_parity/`.

---

## Design Reference

### Syntax

```prolog
% Operator with mixed effects
opSpendMana(?cost) :-
    decrease(mana(player), ?cost),
    add(spent(true)).

opGainXP(?amount) :-
    increase(xp(player), ?amount).

opSwapMana(?a, ?b) :-
    decrease(mana(?a), 10),
    increase(mana(?b), 10).
```

### Semantics

For `increase(head, expr)` applied in state S with the operator's parameter substitution σ:

```
let head'   = σ(head)
let expr'   = σ(expr)
let matches = { f ∈ S | f = head'(v) for some v }
require |matches| == 1     ; exactly one matching fact
let f       = matches[0]
let oldVal  = lastArg(f)
let delta   = arithEval(expr')
S' = (S \ {f}) ∪ { head'(oldVal + delta) }   ; for decrease: oldVal - delta
```

The operator's overall effect is:
1. Apply all `del()` removals.
2. Apply all `increase`/`decrease` in source order.
3. Apply all `add()` additions.

### What this enables (the verbose ↔ concise equivalence)

```prolog
% Verbose (today, still works)
spendMana(?cost) :- 
    if(mana(player, ?old), is(?new, -(?old, ?cost))),
    do(opSpendManaVerbose(?old, ?new)).
opSpendManaVerbose(?old, ?new) :- 
    del(mana(player, ?old)), 
    add(mana(player, ?new)).

% Concise (new)
spendMana(?cost) :- if(), do(opSpendManaConcise(?cost)).
opSpendManaConcise(?cost) :- 
    decrease(mana(player), ?cost).
```

Equivalence claim: for any goal that triggers `spendMana(N)`, both forms produce identical final state and identical plan operators (modulo the operator name itself).

### Errors

| Condition | Behavior |
|---|---|
| No matching fact | Planning failure (operator not applicable); same shape as a failed precondition |
| Multiple matching facts | Planning failure with a clear error message |
| Last arg of matched fact is not numeric | Planning failure with a clear error message |
| `expr` not evaluable as arithmetic | Reuse `RuleIs`'s existing diagnostic |

### Explicit MVP scope cuts

- No `assign(head, expr)` for absolute reset — deferred. Can be done as `del + add`.
- No multi-arg numeric tail (e.g., `pos(player, ?x, ?y)` with two numerics) — last-arg-only.
- No engine-side cost optimization — search behavior is unchanged.
- No syntactic sugar in method bodies (`if(mana(player) > 5)`-style) — preconditions still read the fact via `if(mana(player, ?m), >(?m, 5))`.

---

### Task 1: Parser support — `increase`/`decrease` as operator effect clauses

**Files:**
- Modify: `src/FXPlatform/Htn/HtnCompiler.h` (operator-clause parsing, currently around lines 95–140)
- Modify: `src/FXPlatform/Htn/HtnDomain.h` (extend `AddOperator` signature)
- Modify: `src/FXPlatform/Htn/HtnOperator.h` and `.cpp` (add `m_increases`, `m_decreases`)

**Step 1: Write the failing test.**

Create `src/Tests/Htn/HtnNumericFluentTests.cpp`:

```cpp
#include "Tests/UnitTest++/src/UnitTest++.h"
#include "FXPlatform/Htn/HtnCompiler.h"
#include "FXPlatform/Htn/HtnPlanner.h"
#include "FXPlatform/Htn/HtnOperator.h"
#include "Tests/Htn/AIHarness.h"

SUITE(HtnNumericFluentTests)
{
    TEST(ParserAcceptsIncreaseDecrease)
    {
        HtnPlanner planner;
        HtnCompiler compiler(&planner);
        compiler.ClearWithNewRuleSet();
        const string program =
            "opGain(?n) :- increase(score(player), ?n).\n"
            "opLose(?n) :- decrease(score(player), ?n).\n";
        CHECK(compiler.Compile(program));

        auto op = planner.GetOperator("opGain", 1);
        REQUIRE(op != nullptr);
        CHECK_EQUAL(1u, op->increases().size());
        CHECK_EQUAL(0u, op->decreases().size());
        CHECK_EQUAL(0u, op->additions().size());
        CHECK_EQUAL(0u, op->deletions().size());
    }
}
```

Reference an `HtnPlanner::GetOperator(name, arity)` lookup helper; if one doesn't exist, add a thin one or look up via the domain directly — match whatever pattern existing tests use (read `HtnBasicFeaturesTests.cpp` first to pick the closest idiom).

**Step 2: Run to verify failure.**

```bash
/Users/polycea/Projects/InductorHtn/build/runtests --suite HtnNumericFluentTests
```

Expected: compile error or assertion (the `increase` keyword isn't recognized yet).

**Step 3: Implement parser support.**

In `HtnCompiler.h`, in the loop that handles operator clauses (currently dispatches on `item->name() == "del"` and `== "add"`), add two more branches for `"increase"` and `"decrease"`. Each accumulates its argument list into a new local vector. After the loop, pass these vectors through to `HtnDomain::AddOperator`.

In `HtnOperator.h`/`.cpp`, add:

```cpp
std::vector<std::shared_ptr<HtnTerm>> m_increases;
std::vector<std::shared_ptr<HtnTerm>> m_decreases;
// constructor accepts these
// public accessors increases() / decreases() / dynamicSize() updated
```

In `HtnDomain.h`, extend `AddOperator` to take `increases` and `decreases` as additional parameters (default to empty for backward compat). Update all implementations of `AddOperator` in the codebase.

**Step 4: Re-run.** Test passes.

**Step 5: Commit.**

```bash
git add src/FXPlatform/Htn/HtnCompiler.h src/FXPlatform/Htn/HtnOperator.h src/FXPlatform/Htn/HtnOperator.cpp src/FXPlatform/Htn/HtnDomain.h src/Tests/Htn/HtnNumericFluentTests.cpp src/Tests/Htn/CMakeLists.txt
git commit -m "feat(htn): parse increase/decrease operator effect clauses"
```

---

### Task 2: Engine application — apply `increase`/`decrease` at operator-invocation time

**Files:**
- Modify: `src/FXPlatform/Htn/HtnPlanner.cpp` (the operator-application block around lines 539–544)
- Modify: `src/Tests/Htn/HtnNumericFluentTests.cpp` (add behavior tests)

**Step 1: Write the failing test.**

Append to `HtnNumericFluentTests.cpp`:

```cpp
TEST(IncreaseUpdatesFact)
{
    HtnPlanner planner;
    HtnCompiler compiler(&planner);
    compiler.ClearWithNewRuleSet();
    const string program =
        "score(player, 10).\n"
        "opGain(?n) :- increase(score(player), ?n).\n"
        "goal :- if(), do(opGain(5)).\n";
    CHECK(compiler.Compile(program));

    auto solutions = planner.FindAllPlans(compiler.compilerOwnedRuleSet(), compiler.goals());
    REQUIRE(solutions != nullptr);
    REQUIRE_EQUAL(1u, solutions->size());

    auto finalState = planner.GetSolutionFacts(solutions->at(0).get());
    CHECK(StateContains(finalState, "score(player,15)"));
    CHECK(!StateContains(finalState, "score(player,10)"));
}

TEST(DecreaseUpdatesFact)
{
    // analogous, score(player, 10) → opLose(3) → score(player, 7)
}

TEST(NoMatchingFactFails)
{
    HtnPlanner planner;
    HtnCompiler compiler(&planner);
    compiler.ClearWithNewRuleSet();
    const string program =
        "opGain(?n) :- increase(score(player), ?n).\n"
        "goal :- if(), do(opGain(5)).\n";
    CHECK(compiler.Compile(program));
    auto solutions = planner.FindAllPlans(compiler.compilerOwnedRuleSet(), compiler.goals());
    CHECK(solutions == nullptr || solutions->empty());   // no plan: fact missing
}

TEST(MultipleMatchesFails)
{
    // two facts score(player, 10) and score(player, 20) → increase fails
}
```

Use existing `StateContains` / equivalent helpers from `AIHarness.h`. If they don't exist, write them in-test.

**Step 2: Run to verify failure.**

Tests fail (engine ignores `increase`/`decrease` so far).

**Step 3: Implement engine application.**

Locate `HtnPlanner.cpp:539-544` — the block that calls `SubstituteUnifiers` for `additions`/`deletions` and invokes `state->Update`. Add an intermediate step:

```cpp
shared_ptr<vector<shared_ptr<HtnTerm>>> finalRemovals = SubstituteUnifiers(factory, *mgu, op->deletions());
shared_ptr<vector<shared_ptr<HtnTerm>>> finalAdditions = SubstituteUnifiers(factory, *mgu, op->additions());

// NEW: process increase/decrease into extra removals + extra additions
shared_ptr<vector<shared_ptr<HtnTerm>>> finalIncreases = SubstituteUnifiers(factory, *mgu, op->increases());
shared_ptr<vector<shared_ptr<HtnTerm>>> finalDecreases = SubstituteUnifiers(factory, *mgu, op->decreases());
if (!ApplyFluentDeltas(factory, node->state.get(), *finalIncreases, +1, *finalRemovals, *finalAdditions))
    return false;   // no/multiple matches → operator not applicable
if (!ApplyFluentDeltas(factory, node->state.get(), *finalDecreases, -1, *finalRemovals, *finalAdditions))
    return false;

node->state->Update(factory, *finalRemovals, *finalAdditions);
```

Implement `ApplyFluentDeltas` as a new static helper on `HtnPlanner`. For each `(head, expr)` pair:
1. Build a query term `head(?_v)` with a fresh variable as the trailing arg.
2. Use `HtnGoalResolver` (or the rule-set's direct query API) to find all matching ground facts.
3. If count != 1, return false.
4. Use the existing arithmetic evaluator (the same one `RuleIs` invokes) on `expr` → numeric value.
5. Append the matched fact to `finalRemovals`, append the replacement (with new tail) to `finalAdditions`.

Reuse `HtnGoalResolver::RuleIs`'s arithmetic-evaluation entry point — refactor it into a public/static helper if it isn't one. Reading `RuleIs` first will tell you whether the arithmetic kernel is already callable directly or needs extraction.

**Step 4: Re-run.** All four behavior tests pass.

**Step 5: Commit.**

```bash
git add src/FXPlatform/Htn/HtnPlanner.cpp src/FXPlatform/Htn/HtnPlanner.h src/Tests/Htn/HtnNumericFluentTests.cpp
git commit -m "feat(htn): apply increase/decrease as operator effects"
```

---

### Task 3: Arithmetic expressions in deltas

**Files:**
- Modify: `src/Tests/Htn/HtnNumericFluentTests.cpp`

**Step 1: Test.**

```cpp
TEST(IncreaseAcceptsArithmeticExpression)
{
    HtnPlanner planner;
    HtnCompiler compiler(&planner);
    compiler.ClearWithNewRuleSet();
    const string program =
        "score(player, 10).\n"
        "opAddBonus(?base, ?mult) :- increase(score(player), *(?base, ?mult)).\n"
        "goal :- if(), do(opAddBonus(3, 4)).\n";
    CHECK(compiler.Compile(program));
    auto solutions = planner.FindAllPlans(compiler.compilerOwnedRuleSet(), compiler.goals());
    REQUIRE(solutions != nullptr && solutions->size() == 1);
    auto finalState = planner.GetSolutionFacts(solutions->at(0).get());
    CHECK(StateContains(finalState, "score(player,22)"));   // 10 + 3*4
}
```

**Step 2.** Should already pass if Task 2 routed `expr` through the existing arithmetic evaluator. If not, fix the routing.

**Step 3: Commit.**

```bash
git add src/Tests/Htn/HtnNumericFluentTests.cpp
git commit -m "test(htn): pin arithmetic expression handling in fluent deltas"
```

---

### Task 4: Verbose ↔ concise equivalence test (the headline guarantee)

**Files:**
- Modify: `src/Tests/Htn/HtnNumericFluentTests.cpp` (or new file `HtnFluentEquivalenceTests.cpp`)

**Step 1: Test.**

```cpp
TEST(FluentEquivalentToDelAdd)
{
    // Two rulesets that compute the same thing, one verbose, one concise.
    const string verbose =
        "mana(player, 50). xp(player, 0).\n"
        "spend(?c) :- if(mana(player, ?o), is(?n, -(?o, ?c))),\n"
        "             do(opVerboseSpend(?o, ?n)).\n"
        "opVerboseSpend(?o, ?n) :- del(mana(player, ?o)), add(mana(player, ?n)).\n"
        "gain(?a) :- if(xp(player, ?o), is(?n, +(?o, ?a))),\n"
        "            do(opVerboseGain(?o, ?n)).\n"
        "opVerboseGain(?o, ?n) :- del(xp(player, ?o)), add(xp(player, ?n)).\n"
        "goal :- if(), do(spend(15), gain(7), spend(5)).\n";

    const string concise =
        "mana(player, 50). xp(player, 0).\n"
        "spend(?c) :- if(), do(opConciseSpend(?c)).\n"
        "opConciseSpend(?c) :- decrease(mana(player), ?c).\n"
        "gain(?a) :- if(), do(opConciseGain(?a)).\n"
        "opConciseGain(?a) :- increase(xp(player), ?a).\n"
        "goal :- if(), do(spend(15), gain(7), spend(5)).\n";

    set<string> verboseState = PlanAndCollectFluentFacts(verbose);
    set<string> conciseState = PlanAndCollectFluentFacts(concise);

    // After the goal, both should leave mana(player, 30) and xp(player, 7).
    CHECK(verboseState == conciseState);
    CHECK(verboseState.count("mana(player,30)") == 1);
    CHECK(verboseState.count("xp(player,7)") == 1);
}
```

Implement `PlanAndCollectFluentFacts(program)` as a test helper that compiles, plans, applies solution 0, and returns the set of `mana/2` and `xp/2` facts as strings.

Add two further equivalence cases for coverage:
- `FluentEquivalentUnderMultipleOperatorCalls` — same goal called 50 times in a chain.
- `FluentEquivalentWithBranchingMethods` — methods with `else` alternatives where the cheap branch uses concise and the expensive branch uses verbose; verify the chosen plan is identical (modulo operator names).

**Step 2: Run.** Should pass if Tasks 1–3 are correct. If not, the divergence pinpoints a semantic gap to fix.

**Step 3: Commit.**

```bash
git add src/Tests/Htn/HtnNumericFluentTests.cpp
git commit -m "test(htn): pin verbose-del-add ↔ concise-fluent equivalence"
```

---

### Task 5: Python binding parity

**Files:**
- Modify: `src/Python/indhtnpy.py` if any new C++ symbols need exposing (probably nothing — the syntax is at compile time, and `Compile` already exists)
- Create: `tests/cpp_parity/test_numeric_fluents.py`

**Step 1: Test.**

```python
def test_increase_via_python():
    p = HtnPlanner(False)
    p.HtnCompile("""
        score(player, 10).
        opGain(?n) :- increase(score(player), ?n).
        goal :- if(), do(opGain(5)).
    """)
    err, sols = p.FindAllPlansCustomVariables("goal.")
    assert err == 0
    err, facts = p.GetSolutionFacts(0)
    assert err == 0
    assert any("score(player,15)" in serialize_fact(f) for f in facts)
```

Add a second test that parallels `FluentEquivalentToDelAdd` from Python — compile both rulesets, run, compare fact sets.

**Step 2: Run.**

```bash
source /Users/polycea/Projects/InductorHtn/.venv/bin/activate
cd /Users/polycea/Projects/InductorHtn/tests/cpp_parity
python -m pytest test_numeric_fluents.py -v
```

**Step 3: Commit.**

```bash
git add tests/cpp_parity/test_numeric_fluents.py
git commit -m "test(python): numeric fluent parity through Python bindings"
```

---

### Task 6: Documentation

**Files:**
- Modify: `.claude/rules/htn-syntax.md` (add `increase`/`decrease` to the operator-effects section)
- Modify: `.claude/rules/crafting-rulesets.md` (add a "Numeric resources" subsection that contrasts the two patterns)
- Modify: `CLAUDE.md` (one-line mention if the HTN-syntax cheatsheet lives there)

**Step 1: Update `htn-syntax.md`.**

Under the existing "Operators" section, add:

```markdown
### Numeric fluent effects (`increase` / `decrease`)

For facts of shape `pred(arg1, ..., argN, value)` where `value` is numeric, operators may use:

```prolog
opGain(?n) :- increase(score(player), ?n).
opLose(?n) :- decrease(score(player), ?n).
```

Semantics: at apply time, the engine finds the unique fact matching the head pattern, removes it, and adds the same pattern with `value ± delta`. The delta expression supports the same arithmetic as `is/2` (`+`, `-`, `*`, `/`, `abs`, ...).

Failure modes (operator becomes inapplicable):
- No fact matches the head pattern.
- More than one fact matches.
- The matched fact's last argument is not numeric.

This is sugar for the verbose `del/add` + `is/2` pattern. Both forms are observably equivalent — see `HtnNumericFluentTests.cpp::FluentEquivalentToDelAdd`.
```

**Step 2: Update `crafting-rulesets.md`.**

Add a "Numeric resources" section that walks through the verbose vs concise comparison and notes that the concise form is preferred for new code.

**Step 3: Commit.**

```bash
git add .claude/rules/htn-syntax.md .claude/rules/crafting-rulesets.md
git commit -m "docs: document increase/decrease numeric fluent effects"
```

---

## Verification (end-to-end)

```bash
# C++
cmake --build /Users/polycea/Projects/InductorHtn/build --config Release
/Users/polycea/Projects/InductorHtn/build/runtests --suite HtnNumericFluentTests
/Users/polycea/Projects/InductorHtn/build/runtests   # all suites, regression sweep

# Python
source /Users/polycea/Projects/InductorHtn/.venv/bin/activate
cd /Users/polycea/Projects/InductorHtn/tests/cpp_parity
python -m pytest -v
```

Manual sanity check against an existing puzzle level (which uses neither `increase` nor `decrease`):

```bash
PYTHONPATH=src/Python python -m htn_components assemble puzzle1 --verify-only
```

Expected: assembly succeeds; existing del/add-based rulesets are untouched.

---

## Out of scope (defer)

- **`assign(head, expr)`** — absolute set instead of delta. Implementable with the same machinery if a use case appears.
- **Per-arg-position fluents** — e.g., `pos(player, ?x, ?y)` with two numeric tails. MVP fixes the value to the last arg.
- **Search-time optimization using fluent values** — branch-and-bound, admissible heuristics. Different work item; see HDDL.md T0.3 discussion.
- **`increase`/`decrease` in method bodies** as a precondition shortcut (`if(mana(player) > 5)`-style). Methods still read fluents via the existing `if(mana(player, ?m), >(?m, 5))` pattern.
- **Linter rule** detecting "you wrote a verbose del/add/is pattern; consider concise increase/decrease" — quality-of-life, not core.
