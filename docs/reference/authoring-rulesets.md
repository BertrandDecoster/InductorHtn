# Authoring HTN Rulesets

End-to-end guide to writing good HTN rulesets, followed by optimization patterns
and the tools for inspecting ruleset dynamics.

A practical guide to authoring HTN rulesets for InductorHTN, distilled from
building `Examples/TrunkThumper.htn`. The engine is a **total-order
forward-decomposition planner** (the SHOP model): tasks are decomposed
left-to-right, effects are applied forward as the planner simulates, and the
search is stackless depth-first. Everything below assumes that model.

Companion references:
- `docs/reference/htn-syntax.md` — method/operator/modifier syntax
- `docs/reference/prolog-reference.md` — built-in predicates
- Optimization patterns and MCP-driven iteration: see the later sections of this guide
- `Examples/TrunkThumper.htn` — the worked example this guide is drawn from

---

## 1. Start from a real, documented domain

Don't invent a domain shape from scratch. The engine maps almost 1:1 onto
published total-order HTN domains, so port one:

- **Game AI Pro ch.12 "Exploring HTN Planners through Example"** (Troy
  Humphreys, *Transformers: Fall of Cybertron*) — the canonical game HTN. Its
  Trunk Thumper domain is the basis of `Examples/TrunkThumper.htn`.
- **IPC-2020 HTN track** domains (Barman, Transport, Satellite, Rover,
  Hiking, Monroe, Minecraft) — `github.com/panda-planner-dev/ipc2020-domains`.
- **SimpleFPS / RTS HTN** domains from the game-AI literature.

Translation map (Game AI Pro pseudocode -> InductorHTN):

| Source construct                        | InductorHTN (`?varname` dialect)            |
|-----------------------------------------|---------------------------------------------|
| Compound Task + `Method[cond]/Subtasks` | `task(...) :- if(cond), do(...).`           |
| method priority / fallthrough           | `else` modifier                             |
| Primitive Task + Operator + Effects     | `opX(...) :- del(...), add(...).` (+ fluents) |
| `Effects [WsX += -1]`                   | `decrease(x(?a), 1)`                         |
| recursive `Attack -> ... -> Attack()`   | recursive method + fluent guard             |
| `Preconditions [WsStamina > 0]`         | `if(stamina(?a,?s), >(?s,0))`               |

---

## 2. Make one goal admit several genuinely different plans

The most valuable HTN property for a game is: **one task, multiple natural
strategies**. Express each strategy as a **plain alternative method (no
`else`)**. `FindAllPlans` then enumerates one plan per method whose
precondition holds.

```prolog
% Three simultaneously-viable strategies -> three distinct plans.
attackEnemy(?t, ?e) :- if(powerUp(?t,?p), >=(?p,3), ...), do(... opWhirlwind ...).
attackEnemy(?t, ?e) :- if(trunkHealth(?t,?h), >(?h,0), ...), do(... opTrunkSlam ...).
attackEnemy(?t, ?e) :- if(boulderAvailable(?t), ...), do(opPickupBoulder, opThrowBoulderAt(?e)).
```

Set the initial facts so 2-3 preconditions are true at once — that's what makes
the plan space interesting.

**`else` vs no-`else`** — the single most important authoring decision:

| You want…                              | Use            |
|----------------------------------------|----------------|
| Enumerate every viable strategy        | plain methods (no `else`) |
| Commit to the first that applies (priority/fallback) | `else` on the lower-priority methods |

Reserve `else` for genuine priority ladders and the "nothing applies" fallback.
Using `else` everywhere collapses the plan space to one plan and defeats the
purpose.

---

## 3. Use depth and recursion — that's the "H" in HTN

A flat list of operators is a behaviour tree, not an HTN. Build a hierarchy:

```
goal (clearRoom)
  -> strategy (theBurn / theSlipstream)
       -> action (lureToRoom, applyTag)
            -> operator (opMoveTo, opApplyTag)
```

**Recursion** is where HTN out-expresses other selectors. The re-arm pattern:
when a resource is exhausted, replenish it and recurse into the same task.

```prolog
% Guard with the exhausted condition so recursion TERMINATES.
attackEnemy(?t, ?e) :-
    if(trunkHealth(?t, 0), trunkAt(?trunk, ?tloc)),
    do(navigateTo(?t, ?tloc),
       opUprootTrunk(?t, ?trunk, ?tloc),   % resets trunkHealth -> 3
       attackEnemy(?t, ?e)).             % recurse; now the slam branch fires
```

This works because of **forward decomposition**: the planner applies
`opUprootTrunk`'s effect before re-deciding, so the recursive call sees
`trunkHealth = 3` and drops into the melee branch. The terminating guard
(`trunkHealth = 0`) is mandatory — without it the recursion is unbounded (the
linter warns `SEM006`, which is expected and fine when you have a guard).

---

## 4. Numeric resources: prefer fluents, keep `del()` ground

For resource facts shaped `pred(args..., value)` use `increase`/`decrease`
rather than the verbose `del`+`add`+`is` pattern:

```prolog
opTrunkSlam(?t, ?e) :- decrease(trunkHealth(?t), 1), decrease(stamina(?t), 1).
opRecovery(?t)      :- increase(stamina(?t), 1).
```

Gate method selection on the value with comparisons (`>`, `>=`, `==`):

```prolog
attackEnemy(?t,?e) :- if(trunkHealth(?t,?h), >(?h,0), ...), do(...).
```

**Operator `del()` clauses must be ground at apply time.** A free variable in
`del()` (e.g. `del(powerUp(?t, ?old))` where `?old` is unbound) fails with
*"Items to be removed must be ground"*. Two fixes:

- **Pass the current value in from the method** (which bound it in its `if`):
  ```prolog
  attack(?t,?e) :- if(powerUp(?t,?p), ...), do(opWhirlwind(?t,?e,?p)).
  opWhirlwind(?t,?e,?p) :- decrease(powerUp(?t), ?p), ... .   % ?p ground
  ```
- **Use a fluent for an absolute set**, e.g. `increase(trunkHealth(?t), 3)` when
  the method guarantees the prior value (here it only fires at `trunkHealth=0`).

Effect order inside one operator: all `del()`, then `increase`/`decrease`,
then `add()`.

---

## 5. Navigation & connectivity: push graph search into a built-in

Do **not** hand-enumerate hops:

```prolog
% ANTI-PATTERN: a non-recursive 1/2/3-hop ladder over connected/2.
% Doesn't scale, caps at 3 hops, and explodes the search on dense graphs.
moveTo(?e,?d) :- else, if(at(?e,?c), connected(?c,?i), connected(?i,?d)),
                 do(opMoveTo(?e,?c,?i), opMoveTo(?e,?i,?d)).
```

Use the engine's **`pathNext/3`** built-in — a **native Dijkstra** (a *semantic
attachment*: it computes one binding on demand instead of materializing all
reachability into state). It reads `linked/2` edge facts and optional `size/2`
node weights, and returns the next hop on the shortest path. The method just
steps one hop and recurses:

```prolog
% Edges: directed linked/2 facts (list both directions for two-way links).
linked(bridge1, grove).  linked(grove, bridge1).
size(grove, 2).          % optional per-node movement cost (default 1)

% Genuinely recursive, any actor, any distance, no graph search in the planner.
navigateTo(?who, ?dest) :- if(at(?who, ?dest)), do().                 % base case
navigateTo(?who, ?dest) :-
    else, if(at(?who, ?cur), pathNext(?cur, ?dest, ?next)),
    do(opMoveTo(?who, ?cur, ?next), navigateTo(?who, ?dest)).         % step + recurse
```

Why this is correct and cheap:
- **O(E log V) per hop in C++**; the planner never branches over the graph.
- **Cannot loop**: `pathNext` fails when `from == to`, and the base case catches
  "already there", so each step strictly approaches the goal.
- **Generic**: navigates any entity with an `at/2` fact — don't write
  per-target wrappers (`navigateToEnemy`, `navigateToTrunk` are dead weight;
  callers already bind the destination location in their own `if`, so just call
  `navigateTo(?t, ?loc)`).

`pathNext` contract (`HtnGoalResolver::RulePathNext`): `from`/`to` must be
**ground**, `nextStep` a **variable**; edges come from `linked/2` **facts**
only (a `linked :- ...` *rule* is not read); weights from `size/2`; fails on
same-node, unknown source, or no path. Reference: `Examples/PathTest.htn`,
`Examples/CombatLevel1_GreaseTrap.htn` (same recursive pattern).

> This is the InductorHTN instance of a general principle: when connectivity /
> geometry / arithmetic would explode the HTN search, compute it in a built-in
> (semantic attachment) and let the method consume one answer at a time.

---

## 6. Type hints (opt-in, linter-only)

Two conventional facts give the linter a type system; the **planner ignores
them entirely**:

```prolog
type(troll, thumper).                 % tag a constant with a type
type(location, grove).
signature(opTrunkSlam, [troll, hero]).% declare a call's argument types
```

- **`TYP001`** — a *constant* argument at a typed call site whose declared type
  mismatches (or is undeclared).
- **`TYP002`** — duplicate `signature/2` for one `pred/arity`.
- Numeric literals auto-satisfy `int`/`float`/`number`.
- **Scope**: only constants directly in `if/do/del/add` are checked. Variables,
  compound terms, plain facts, the `goals(...)` line, and calls nested inside
  `try()/first()/and()/parallel()/forall()` are **not** checked (MVP).
- Fully opt-in: no `signature/2` -> no TYP diagnostics.

In practice most body call-site args are variables, so signatures act as
**documentation + future-proofing** that fires the moment someone hardcodes the
wrong constant into a clause.

---

## 7. Author bottom-up, iterate with the MCP tools

Workflow that catches problems early (see `docs/tools/mcp-server.md`):

1. **Write** facts -> operators -> low-level methods -> strategies -> goal.
2. **`indhtn_lint`** — fix syntax. Understand the benign warnings: numeric
   literals misread as predicates (`SEM002`), intended recursion (`SEM006`),
   empty `do()` base cases (`HTN005`), alternate-entry "dead code" reachable
   via other goals (`SEM004/005`).
3. **`indhtn_introspect`** — confirm methods/operators/facts parsed as intended.
4. **`indhtn_find_plans`** — verify the goal yields the expected *set* of plans
   (the multi-strategy headline). `indhtn_get_decomposition_tree` shows the
   hierarchy and condition bindings.
5. **`indhtn_method_failures`** — when the goal yields *fewer* plans than you
   expected, this pinpoints which method's gate or body subtask blocked, so you
   stop guessing. Run it **before** hand-flipping facts (see §8).
6. **Scenario testing** — `indhtn_snapshot_state` / `add_facts` / `remove_facts`
   / `restore_state` to flip preconditions and confirm each branch fires.
   `indhtn_apply_plan` + `indhtn_list_facts` to verify fluent effects.
7. **Watch step counts** — if a method explodes (`indhtn_get_resolution_steps`),
   reorder conditions (constraining goal first) or push work into a built-in.

Build bottom-up: validate leaf operators and low methods before the goal, so a
failure is localized.

---

## 8. Finding where a plan fails (method failure analysis)

When a goal yields **fewer** plans than you expected — a strategy silently
dropped out — don't hand-flip facts hoping to stumble on the cause. Ask the
planner directly with **`indhtn_method_failures`**. It runs a find-all pass and
reports, for every method clause the search ever tried, **where it got blocked**
across the *entire* backtracking search (not just successful plans).

The key signal is the per-method **`furthestCompleted`** histogram — an `N+1`
array for a method with `N` body subtasks:

| Reading | Meaning | Fix |
|---------|---------|-----|
| `gateFailCount > 0`, `groundingsN == 0`, `furthestCompleted == []` | the method's `if()` **precondition gate** never held — it never entered its body | add/adjust the facts the precondition queries |
| mass at index `k < N` | gate cleared, but the body consistently **blocks at subtask k** | make subtask `k` succeed (`positions[k]` names it) |
| mass at index `N` (`successS > 0`) | the method **completes locally** | the problem is downstream, not here — move on |

**Worked dogfood (TrunkThumper).** With all resources present,
`indhtn_method_failures "attackEnemy(thumper, theHero)."` shows every viable
strategy at full success (`furthestCompleted == [0,0,0,1]`) and the re-arm
strategy gated out (`gateFailCount: 1`, because `trunkHealth(?t,0)` is false at
`trunkHealth = 3`). Now remove the boulder and re-run:

```
remove_facts ["boulderAvailable(thumper)"]
indhtn_method_failures "attackEnemy(thumper, theHero)."   # planCount 3 -> 2
```

The boulder method flips to `furthestCompleted: []`, `gateFailCount: 1`,
`groundingsN: 0` — the textbook "gate failed, never entered the body" diagnosis.
That's the whole loop: read the histogram, add what the named gate/subtask
needs, re-run, watch the mass move **rightward** toward index `N`.

**Caveats** (see `docs/upgrades/method-failure-tracking.md` for the full reference):
`anyOf`/`allOf`/`parallel()` clauses are excluded from the partition (they merge
groundings) — diagnose their inner tasks via those tasks' **own** by-method
entries, or the **by-atom** rollup. Needs an engine built with
`INDHTN_CHOICE_TRACKING` (the repo's build already qualifies); otherwise the
tool returns `ok:false, code:"choice_tracking_unavailable"`.

---

## 9. The Plan Runner & the replan loop

The Game AI Pro chapter is mostly about the half InductorHTN doesn't do: the
**Plan Runner**. A planner produces a *plan* against a snapshot of the world;
the game then *executes* it while **sensors** keep mutating world state, and
**replans** the moment the running plan is invalidated. That execute → sense →
replan loop is what makes a ruleset feel alive — and you can drive the whole
thing with existing MCP tools, no engine changes:

```
indhtn_snapshot_state  "t0"                  # checkpoint the start state
indhtn_find_plans      "attackEnemy(...)."   # plan against current world
loop over the chosen plan's operators:
    indhtn_apply_operator "<next op>"        # execute one step
        -> ok: true                          # step succeeded, continue
        -> ok: false, code: preconditions_failed   # the world moved under us
    # a "sensor" fires: the world changed independently of our actions
    indhtn_add_facts / indhtn_remove_facts   # e.g. the hero fled melee range
    # on invalidation (or after any sensor change), REPLAN from the new state:
    indhtn_find_plans  "attackEnemy(...)."    # pick up the new best plan
```

`indhtn_apply_operator`'s `preconditions_failed` result **is** the
plan-invalidation signal — exactly what a Plan Runner watches for. Concretely on
Thumper: start mid trunk-slam, then `remove_facts ["inMeleeRange(thumper,
theHero)"]` (the hero backed off). The next melee operator now fails its
precondition; re-`find_plans` and the boulder branch (ranged, no melee gate)
takes over. That single transition is a complete, inspectable replan.

**Four things the chapter teaches that shape how you replan** (ch. 12.5–12.10):

- **Replan only on *exogenous* changes, not your own effects.** The chapter's
  cautionary bug (ch. 12.9): the troll's trunk-slam builds `WsPowerUp`, and the
  third slam tips it to 3 — if you replan on *that* (an effect your own operator
  applied), the higher-priority Whirlwind method hijacks the plan and cancels the
  Recovery beat meant to give the player a breather. The fix is to replan on
  **sensor**/world changes the plan didn't itself cause, not on the forward
  effects the planner already accounted for. In the loop above, that means:
  re-`find_plans` after `add_facts`/`remove_facts` (a sensor), **not** after a
  clean `apply_operator` that merely applied its own declared effects.
- **MTR (Method Traversal Record).** The chapter records, per compound task, the
  *method index* it chose, and only swaps to a freshly-found plan when every
  index is equal-or-higher priority — that's how it avoids replan thrash between
  same-priority plans. InductorHTN has no MTR, but the analog you inspect is
  `indhtn_get_decomposition_tree` (which method fired at each node) plus method
  ordering; when comparing a new plan to a running one, diff their method choices
  the same way.
- **Expected effects.** The chapter applies some effects *only during planning*
  (e.g. "after NavigateToEnemy, `WsCanSeeEnemy` will be true") so downstream
  preconditions validate. InductorHTN doesn't separate planning-only from real
  effects — every `add`/`del`/fluent is forward-simulated — so model such
  look-ahead with an ordinary effect on the navigation/setup operator.
- **Partial plans.** The chapter plans only a few steps ahead and replans at
  split points, for speed and reactivity. InductorHTN always plans the goal to
  completion; if a long horizon is costly, split the goal into shorter
  sub-goals you plan and run in sequence (a manual partial-plan boundary).

This extends the step-through protocol in
`docs/reference/challenge-play-protocol.md`; use `snapshot_state` /
`restore_state` to replay a scenario from a fixed start.

---

## 10. What tools are available (quick reference)

Authoring is a tool-driven loop. Reach for:

| Authoring question | Tool |
|--------------------|------|
| Is the syntax valid? | `indhtn_lint` |
| Did methods/operators/facts parse as I intended? | `indhtn_introspect` |
| What's true in the current state? | `indhtn_query` / `indhtn_list_facts` |
| Which strategies does this goal admit? | `indhtn_find_plans` |
| How did the goal decompose (the hierarchy)? | `indhtn_get_decomposition_tree` |
| **Why did a strategy NOT fire / why fewer plans?** | **`indhtn_method_failures`** |
| What would the state be after this plan? | `indhtn_preview_solution_facts` |
| Step a plan by hand / drive the replan loop | `indhtn_apply_operator` + `add_facts` / `remove_facts` |
| Checkpoint / undo a scenario | `indhtn_snapshot_state` / `indhtn_restore_state` |
| Is a method too expensive? | `indhtn_get_resolution_steps` |

Static, session-free analysis (`indhtn_lint`, `indhtn_introspect`) needs no
session; everything else operates on a loaded session. Full surface and response
conventions: `docs/tools/mcp-server.md`. Plan-space *richness* metrics
(entropy, difficulty) and the by-method/by-atom report in bulk live in the CLI:
`PYTHONPATH=src/Python python -m htn_components evaluate <level>`.

---

## 11. Performance patterns (validated)

From `docs/reference/authoring-rulesets.md` (`[VALIDATED]` = measured >20% fewer
resolution steps):

- **Constraining goal first** — put the condition with the fewest bindings
  first in `if(...)`. (19 -> 10 steps)
- **Pre-computed negation** — materialize the valid set as facts instead of
  runtime `not(...)`. (33 -> 11)
- **Direct `count` over `findall`+`count`** when you only need the count.
  (26 -> 15)
- **Cut for mutually-exclusive branches** — `if(>(?x,0), !)`. (15 -> 12)
- **`else` for preference ladders**, **`first()` for single-result** queries.
- **First-argument indexing** — restructure facts so the commonly-bound field is
  argument 1.

---

## 12. Gotchas

- **ASCII only.** The MCP/GUI file loaders are strict UTF-8 and choke on
  em-dashes (`—`), en-dashes, and smart quotes — they fail with
  *"'utf-8' codec can't decode byte 0xe2…"*. Use `-`, `'`, `"` in comments.
- **`del()` must be ground** — see §4.
- **`pathNext` reads `linked/2` FACTS, not rules** — a `linked :- connected`
  bridge rule won't be seen. Declare edges as facts.
- **Fact removal matches the stored string exactly** — `remove_facts`
  `"trunkHealth(thumper, 3)"` (with a space) misses `trunkHealth(thumper,3)`.
- **Use `HtnCompileCustomVariables`** (the MCP/GUI default) for any file in this
  repo — they all use `?varname`. Plain `HtnCompile` rejects `?`.
- **Numeric-fluent failure modes** (operator becomes inapplicable, planner
  backtracks): no fact matches the head pattern, more than one matches, or the
  last argument isn't numeric.

---

## 13. Naming conventions

| Layer       | Prefix   | Examples                         |
|-------------|----------|----------------------------------|
| User goals  | (none)   | `defeatEnemy`, `clearRoom`       |
| Strategies  | (none)   | `theBurn`, `theSlipstream`       |
| Actions     | (none)   | `applyTag`, `navigateTo`         |
| Triggers    | `trigger`| `triggerBurnOil`                 |
| Operators (real) | `op` | `opMoveTo`, `opTrunkSlam`, `opRecovery` |
| Method markers (dummy) | `m<N>_` | `m1_navigateTo`, `m2_attackEnemy` |

**Real operators — anything with a `del`/`add`/fluent effect — start with `op`.**
This is the repo-wide convention, and it's *load-bearing*, not cosmetic: the
tree-reconstruction preprocessing in `src/Python/PythonUsageTree.py` /
`PythonUsageBD.py` does `re.sub(r"op([A-Z])", ...)` to strip the prefix for
display, so a non-`op` operator name breaks that tooling.

**Method markers are dummy no-op operators (`:- del(), add().`) auto-inserted —
never hand-written.** `addMethodNameAndArity()` (same files) prepends one as the
first subtask of every method's `do()` so a flat `goals()` plan reveals which
methods fired; `HtnTreeReconstructor.py` then rebuilds the decomposition tree
from them. The marker is named `m<N>_<methodHead>`, where **`N` is the number of
subtasks in that method's `do()`** (the *decomposition width*, not the head's
parameter count) — e.g. `goToSameLocation(?a,?t)` whose `do()` holds one subtask
becomes `m1_goToSameLocation(?a,?t)`. You author clean source (`op` operators +
plain methods); the markers appear only when you run the preprocessing. The
richer alternative is the C++/MCP decomposition tree
(`indhtn_get_decomposition_tree`), which needs no markers.

Precondition layering: **goals** validate everything; **actions** check key
requirements (location, capability); **triggers/operators** trust the caller.

---

## Checklist

- [ ] Domain grounded in a documented total-order HTN source
- [ ] Goal has multiple **plain** alternative methods (no spurious `else`)
- [ ] Initial facts make 2-3 strategies simultaneously viable
- [ ] Hierarchy is deep (goal -> strategy -> action -> operator)
- [ ] Recursion (if any) has a terminating fluent guard
- [ ] Resources use `increase`/`decrease`; `del()` clauses are ground
- [ ] Navigation uses recursive `navigateTo` + `pathNext` over `linked/2`
- [ ] No per-target navigation wrappers
- [ ] **Real operators start with `op`** (`opMoveTo`); dummy method markers
      (`m<N>_…`) are auto-inserted by preprocessing, not hand-written
- [ ] Type hints added for the main predicates (optional but recommended)
- [ ] ASCII-only source
- [ ] Verified: lint clean, expected plan set, fluent effects, scenario branches

---

## Crafting & Understanding Rulesets

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
# Use HtnCompileCustomVariables for ?varname-style files (everything in
# this repo: Examples/, components/**/src.htn, assembled levels). Plain
# HtnCompile() rejects `?` and only works on standard-Prolog files.
planner.HtnCompileCustomVariables(open("Examples/Taxi.htn").read())

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

### indhtn_preview_solution_facts
Preview the state that would result from applying a cached plan, without
modifying state. Call `indhtn_find_plans` first to populate the cache.
```json
{
  "sessionId": "<id>",
  "solutionIndex": 0
}
```
Returns: `{facts, added, removed}` — full post-apply state plus the diff
vs. current.

### indhtn_apply_operator
Apply a single primitive operator (one `del()`/`add()` step). Useful for
step-by-step debugging when you want to walk a plan by hand rather than
let the planner pick the decomposition.
```json
{
  "sessionId": "<id>",
  "operator": "opMoveTo(player, roomA, roomB)"
}
```
Returns: `{ok, operator, facts, added, removed}` on success. On failure
returns `{ok: false, code: ...}` with one of these discriminants:
- `preconditions_failed` — `del()` clauses didn't match current state
- `expanded_to_multiple_ops` — the call decomposed into multiple ops
  (looks like a method, not a primitive)
- `ambiguous_unification` — multiple plans matched the call; the
  alternatives are returned in `candidates[]`

### indhtn_query
Run a Prolog query against current state without planning. Use this to
ask "what's true right now?" — `at(?x).`, `count(?n, enemy(?e)).`, etc.

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

### Numeric resources

For resource-tracking facts (`mana(player, 50)`, `xp(player, 0)`, etc.), prefer `increase`/`decrease` over the verbose `del/add/is` pattern:

```prolog
% Old (still works)
opSpend(?cost) :-
    if(mana(player, ?old), is(?new, -(?old, ?cost))),  % in calling method
    do(opSpendInner(?old, ?new)).
opSpendInner(?old, ?new) :- del(mana(player, ?old)), add(mana(player, ?new)).

% Preferred
opSpend(?cost) :- decrease(mana(player), ?cost).
```

The two forms are observably equivalent. See `docs/reference/htn-syntax.md` for full semantics.

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

## Writing rulesets

0. Understand the philosophy of a level, the ways to solve it and translate it to facts, operators and methods
1. Write ruleset that combine the  facts, operators and methods
2. Fix syntax errors
3. Check that methods / operators are working properly by going bottom/up. Start with methods close to the leaves and go your way up
4. Monitor the amount of steps a method needs, if it explodes (thousand of steps) look at how to compute it more efficiently
5. Now that high level methods that solve the level are functional, generate a full plan, apply the operators and check that all the states match the design of the ruleset

---

## Naming Convention

| Layer | Prefix | Examples | Description |
|-------|--------|----------|-------------|
| User goals | (none) | `defeatEnemy`, `clearRoom` | Top-level, full validation |
| Strategies | (none) | `theBurn`, `theSlipstream` | Named tactical plans |
| Actions | (none) | `applyTag`, `bringEnemyTo`, `navigateTo` | Reusable building blocks, key checks |
| Triggers | `trigger` | `triggerBurnOil`, `triggerSnareEnemies` | Internal reactions, minimal checks |
| Operators | `op` | `opMoveTo`, `opApplyCondition` | Primitive state changes (del/add) |

**Precondition Layering:**
- **User-facing goals**: Full validation - checks everything needed
- **Reusable actions**: Check key requirements (location, capability)
- **Internal triggers**: Minimal checks - trust caller already validated
