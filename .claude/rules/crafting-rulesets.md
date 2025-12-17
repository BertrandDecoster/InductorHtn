# Crafting & Understanding Rulesets

Tools for understanding ruleset dynamics - seeing what plans work, how state changes, and exploring facts.

## 1. Interactive REPL (`indhtn.exe`) - Quick Exploration

```bash
./build/Release/indhtn.exe Examples/Taxi.htn
```

**Key commands:**
| Command | Purpose |
|---------|---------|
| `at(?x).` | Query current facts (list all `at` facts) |
| `goals(travel-to(park)).` | Find plans without applying |
| `apply(travel-to(park)).` | Find plans AND apply state changes |
| `/t` | Toggle tracing (see method decomposition) |
| `/r` | Reset and reload |

**List all facts:** Query each predicate, e.g., `at(?x).`, `have-cash.`

## 2. Python API - Best for Programmatic Analysis

```python
from indhtnpy import HtnPlanner

planner = HtnPlanner(False)
planner.Compile(open("Examples/Taxi.htn").read())

# Get ALL current facts
error, facts = planner.GetStateFacts()  # Returns JSON list

# Find plans
error, solutions = planner.FindAllPlansCustomVariables("travel-to(uptown).")

# See what state WOULD be after a plan (without applying)
error, new_facts = planner.GetSolutionFacts(0)  # Solution index 0

# Apply a plan and update state permanently
planner.ApplySolution(0)

# Get decomposition tree (see HOW plan was derived)
error, tree = planner.GetDecompositionTree(0)
```

**Run the demo:**
```bash
python src/Python/PythonUsageTrace.py
```

## 3. GUI (`start_gui.py`) - Visual State Diff

```bash
python gui/start_gui.py
```

The GUI provides:
- **State panel** showing current facts
- **State diff** after each solution (shows added/removed/unchanged facts)
- **Decomposition tree visualization**

API endpoint: `POST /api/state/diff` returns:
```json
{
  "added": ["at(park)"],
  "removed": ["at(downtown)"],
  "unchanged": ["have-cash"]
}
```

## Best Tool by Use Case

| Goal | Best Tool |
|------|-----------|
| Quick interactive testing | `indhtn.exe` REPL |
| List all facts | Python `GetStateFacts()` |
| See state changes | Python `GetSolutionFacts()` or GUI diff |
| Understand plan decomposition | Python `GetDecompositionTree()` or `/t` tracing |
| Batch testing | `htn_test_suite.py` |

## Deep Understanding Workflow

For thorough ruleset analysis, use the Python API with these three methods together:

1. `GetStateFacts()` - Initial state (all facts before planning)
2. `GetSolutionFacts(i)` - Final state after solution i
3. `GetDecompositionTree(i)` - How the plan was derived (method choices, bindings)

This shows before/after state plus the decomposition logic explaining WHY those operators were chosen.

## MCP Tools for LLM Workflow

These MCP tools support the ruleset creation workflow:

### indhtn_lint
Validate HTN syntax and get structured errors.
```json
{
  "source": "travel(?x) :- if(at(?y)), do(walk(?y, ?x))."
}
```
Returns: diagnostics with line numbers, error codes, severity.

### indhtn_introspect
List all methods, operators, and facts in a ruleset.
```json
{
  "source": "<htn source>"
}
```
Returns: methods[], operators[], facts[] with signatures and line numbers.

### indhtn_state_diff
Preview what a plan would change (without applying).
```json
{
  "sessionId": "<id>",
  "goal": "travel-to(park)"
}
```
Returns: plan preview.

### indhtn_step
Execute one operator at a time for debugging.
```json
{
  "sessionId": "<id>",
  "operator": "walk(downtown, park)"
}
```
Returns: operator result, query facts to see new state.

---

## Prolog/HTN Optimization Patterns

Performance patterns for writing efficient InductorHTN rulesets. Patterns marked `[VALIDATED]` have been tested with resolution step counting showing >20% improvement.

### Pattern: Goal Ordering - Constraining Goal First

**Problem:** When multiple conditions must be satisfied, checking the larger set first wastes work. Each failing combination from the large set still attempts the constraining check.

**Slow:**
```prolog
person(alice).
person(bob).
person(carol).
person(dave).
rich(dave).
findRichPerson(?p) :- if(person(?p), rich(?p)), do(...).
```

**Fast:**
```prolog
person(alice).
person(bob).
person(carol).
person(dave).
rich(dave).
findRichPerson(?p) :- if(rich(?p), person(?p)), do(...).
```

**When to apply:** When one condition produces fewer bindings than another, put the constraining condition first. This prunes the search space early.

**[VALIDATED]** Steps: 19 → 10 (47.4% improvement)

---

### Pattern: Pre-computed Negation

**Problem:** Runtime `not()` checks require attempting to prove the negated goal for each candidate, adding resolution overhead.

**Slow:**
```prolog
item(a).
item(b).
item(c).
item(d).
excluded(b).
findNonExcluded(?x) :- if(item(?x), not(excluded(?x))), do(...).
```

**Fast:**
```prolog
item(a).
item(b).
item(c).
item(d).
excluded(b).
nonExcluded(a).
nonExcluded(c).
nonExcluded(d).
findNonExcluded(?x) :- if(nonExcluded(?x)), do(...).
```

**When to apply:** When the excluded set is known at compile time and doesn't change during planning. Pre-compute the valid set as facts.

**[VALIDATED]** Steps: 33 → 11 (66.7% improvement)

---

### Pattern: Direct Count vs Redundant findall

**Problem:** Using `findall` before `count` when you only need the count duplicates work - both traverse all solutions.

**Slow:**
```prolog
member(a, team1).
member(b, team1).
member(c, team1).
teamSize(?team, ?size) :- if(findall(?m, member(?m, ?team), ?list), count(?size, member(?x, ?team))), do(...).
```

**Fast:**
```prolog
member(a, team1).
member(b, team1).
member(c, team1).
teamSize(?team, ?size) :- if(count(?size, member(?x, ?team))), do(...).
```

**When to apply:** When you only need the count, not the actual list. Use `count` directly without `findall`.

**[VALIDATED]** Steps: 26 → 15 (42.3% improvement)

---

### Pattern: Cut for Deterministic Choice

**Problem:** Mutually exclusive conditions (like comparisons) may still leave choice points, causing unnecessary backtracking attempts.

**Slow:**
```prolog
classify(?x, positive) :- if(>(?x, 0)), do(...).
classify(?x, zero) :- if(==(?x, 0)), do(...).
classify(?x, negative) :- if(<(?x, 0)), do(...).
```

**Fast:**
```prolog
classify(?x, positive) :- if(>(?x, 0), !), do(...).
classify(?x, zero) :- if(==(?x, 0), !), do(...).
classify(?x, negative) :- if(<(?x, 0)), do(...).
```

**When to apply:** When conditions are mutually exclusive and you know exactly one will match. Add `!` (cut) after the distinguishing condition to commit.

**[VALIDATED]** Steps: 15 → 12 (20.0% improvement)

---

### Pattern: else Methods for Fallback Logic

**Problem:** Without `else`, all method alternatives are tried even after one succeeds, creating unnecessary backtracking.

**Slow:**
```prolog
travel(?dest) :- if(hasCarKey), do(drive(?dest)).
travel(?dest) :- if(hasBusPass), do(takeBus(?dest)).
travel(?dest) :- if(), do(walk(?dest)).
```

**Fast:**
```prolog
travel(?dest) :- if(hasCarKey), do(drive(?dest)).
travel(?dest) :- else, if(hasBusPass), do(takeBus(?dest)).
travel(?dest) :- else, if(), do(walk(?dest)).
```

**When to apply:** When method alternatives represent a preference order and you want to commit to the first successful match. Use `else` on fallback methods.

---

### Pattern: first() for Single-Result Queries

**Problem:** When you only need one result but the query could produce many, backtracking wastes resources.

**Example:**
```prolog
available(taxi1).
available(taxi2).
available(taxi3).
getTaxi(?t) :- if(first(available(?t))), do(hire(?t)).
```

**When to apply:** Use `first()` when any single solution suffices and you want to prevent backtracking through alternatives.

**Note:** `first()` has overhead in InductorHTN. For small result sets, the overhead may exceed savings. Measure before applying.

---

### Pattern: First-Argument Indexing

**Problem:** Prolog indexes facts by first argument. Queries with a variable in the first position scan all facts.

**Slow:**
```prolog
data(1, a, x).
data(2, b, y).
data(3, c, z).
lookup(?val, ?key) :- if(data(?key, ?val, ?extra)), do(...).
```

**Fast:**
```prolog
dataByVal(a, 1, x).
dataByVal(b, 2, y).
dataByVal(c, 3, z).
lookup(?val, ?key) :- if(dataByVal(?val, ?key, ?extra)), do(...).
```

**When to apply:** When queries typically have a bound value that isn't the first argument. Restructure facts to put the commonly-queried field first.

---

### Pattern: Ground Variables Before not()

**Problem:** `not()` with unbound variables gives unexpected results (negation as failure semantics).

**Wrong:**
```prolog
% ?x unbound - not(enemy(?x)) succeeds if there exists ANY non-enemy
findSafe(?x) :- if(location(?x), not(enemy(?x))), do(...).
```

**Correct:**
```prolog
% ?x bound first, then check if that specific ?x is not an enemy
findSafe(?x) :- if(location(?x), not(enemy(?x))), do(...).  % OK if location binds ?x
```

**When to apply:** Always ensure variables in `not()` are bound by earlier goals. If unsure, add an explicit binding goal.

---

### HTN-Specific: Method Ordering by Likelihood

**Problem:** Trying unlikely methods first wastes decomposition effort.

**Principle:** Order methods so the most commonly successful ones are tried first:

```prolog
% Common case first
travel(?dest) :- if(nearby(?dest)), do(walk(?dest)).
% Less common
travel(?dest) :- else, if(hasCar), do(drive(?dest)).
% Rare fallback
travel(?dest) :- else, if(), do(callTaxi(?dest)).
```

**When to apply:** When you know the statistical distribution of cases. Put common cases first to minimize backtracking.

---

### HTN-Specific: anyOf vs allOf Selection

**anyOf** - Use when ANY successful binding suffices:
```prolog
attackAny() :- anyOf, if(enemy(?e), inRange(?e)), do(attack(?e)).
```
Succeeds if at least one enemy can be attacked.

**allOf** - Use when ALL bindings must succeed:
```prolog
healAll() :- allOf, if(wounded(?ally)), do(heal(?ally)).
```
Succeeds only if all wounded allies are healed.

**When to apply:** Use `anyOf` for "try until one works" scenarios. Use `allOf` for "must handle all" scenarios.

---

## Validation Methodology

Patterns marked `[VALIDATED]` were tested by measuring Prolog resolution steps. To validate patterns yourself:

1. Build (resolution tracking is enabled by default):
   ```bash
   cmake ../src
   cmake --build . --config Release
   ```
   To disable: `cmake -DINDHTN_TRACK_RESOLUTION_STEPS=OFF ../src`

2. Use Python API to measure:
   ```python
   from indhtnpy import HtnPlanner

   planner = HtnPlanner(False)
   planner.PrologCompile(code)
   error, result = planner.PrologQuery(query)
   steps = planner.GetLastResolutionStepCount()
   ```

3. Compare slow vs fast implementations - >20% improvement qualifies as validated.

# Writing rulesets

0. Understand the philosophy of a level, the ways to solve it and translate it to facts, operators and methods
1. Write ruleset that combine the  facts, operators and methods
2. Fix syntax errors
3. Check that methods / operators are working properly by going bottom/up. Start with methods close to the leaves and go your way up
4. Monitor the amount of steps a method needs, if it explodes (thousand of steps) look at how to compute it more efficiently
5. Now that high level methods that solve the level are functional, generate a full plan, apply the operators and check that all the states match the design of the ruleset