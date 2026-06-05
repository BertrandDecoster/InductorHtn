# Generating Good HTN Rulesets

A practical guide to authoring HTN rulesets for InductorHTN, distilled from
building `Examples/TrunkThumper.htn`. The engine is a **total-order
forward-decomposition planner** (the SHOP model): tasks are decomposed
left-to-right, effects are applied forward as the planner simulates, and the
search is stackless depth-first. Everything below assumes that model.

Companion references:
- `.claude/rules/htn-syntax.md` — method/operator/modifier syntax
- `.claude/rules/crafting-rulesets.md` — optimization patterns, MCP tools
- `.claude/rules/prolog-reference.md` — built-in predicates
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

Workflow that catches problems early (see `.claude/rules/mcp-server.md`):

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

**Caveats** (see `docs/method-failure-analysis.md` for the full reference):
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
`.claude/rules/challenge-play-protocol.md`; use `snapshot_state` /
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
conventions: `.claude/rules/mcp-server.md`. Plan-space *richness* metrics
(entropy, difficulty) and the by-method/by-atom report in bulk live in the CLI:
`PYTHONPATH=src/Python python -m htn_components evaluate <level>`.

---

## 11. Performance patterns (validated)

From `.claude/rules/crafting-rulesets.md` (`[VALIDATED]` = measured >20% fewer
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
