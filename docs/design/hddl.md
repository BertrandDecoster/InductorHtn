# HDDL vs InductorHTN

A comparison of the academic-standard hierarchical planning language (HDDL) against the language accepted by this engine, plus a ranked list of extensions worth bringing in.

## TL;DR

**HDDL** (Hierarchical Domain Definition Language) is a conservative, S-expression extension of PDDL 2.1 that adds *compound tasks*, *methods*, and *task networks with ordering constraints*. It was the standard input language for the IPC 2020 and 2023 hierarchical-planning tracks. Because it sits on top of PDDL, it inherits PDDL's typing, declared predicates, numeric fluents, conditional effects, action costs, and (in HDDL 2.1) durative actions and Allen-interval ordering.

**InductorHTN** is a SHOP-flavored, Prolog-grounded HTN engine focused on memory-budgeted, stackless execution. It overlaps with HDDL on the *core HTN concepts* (compound tasks, methods, primitive operators) but diverges sharply on (a) syntax — Prolog-style with `?`-prefixed variables instead of S-expressions, (b) absence of a type system and declared object/predicate sections, (c) no partial-order task networks — `do(a, b, c)` is strictly sequential, (d) no goal-state checking, conditional effects, numeric fluents, action costs, or temporal reasoning. Conversely, InductorHTN has expressive Prolog meta-predicates (`findall`, `count`, `sortBy`, `assert/retract`), priority fallback via `else`, an `anyOf`/`allOf` quantifier on methods, a hard memory budget, and a live debug surface (REPL, decomposition tree, MCP) that no HDDL planner provides out of the box.

---

## 1. HDDL feature inventory

### 1.1 Core hierarchy (HDDL 1.0)

- `(:task <name> :parameters (...))` — compound (abstract) task declarations live in the domain.
- `(:method <m> :parameters (...) :task (<task-call>) :precondition <φ> :subtasks (...) :ordering (...) :constraints (...))` — decomposition method.
- `:subtasks` lists **labeled** subtasks: `((t1 (drive ?x)) (t2 (load ?p ?x)))`. Labels enable referring to subtasks individually.
- `:ordering` lists pairwise precedence constraints `(t1 < t2)`. Listing none means the network is fully unordered (partial-order). A linear chain `(t1 < t2)(t2 < t3) ...` encodes total order.
- `:constraints` block separates parameter (in)equalities and other meta-constraints from state preconditions. This decoupling is intentional — variable constraints are not state queries.
- `(:htn :parameters (...) :tasks (...) :ordering (...) :constraints (...))` in the problem file declares the **initial task network**, not just a single goal task.
- `(:goal <φ>)` (PDDL-style state goal) is allowed *alongside or instead of* the initial task network — the planner must satisfy both.

### 1.2 Inherited from PDDL 2.1

- `:types` / `:typing` — typed parameters with subtyping hierarchy.
- `:objects` — declared per-problem constants.
- `:predicates` — declared schema for state facts.
- `:functions` — numeric fluents (with `:numeric-fluents` requirement).
- `:action :precondition :effect` — primitive actions.
- Conditional effects via `(when <cond> <eff>)`.
- Quantified preconditions/effects via `forall` and `exists`.
- Requirement flags: `:negative-preconditions`, `:equality`, `:disjunctive-preconditions`, `:universal-preconditions`, `:method-preconditions`, `:hierarchy`.
- `:action-costs` and `(:metric minimize (total-cost))` — plan optimization.

### 1.3 HDDL 2.1 additions (temporal)

- Durative actions and **durative methods** (durations are optional on methods; default to the sum of subtask durations).
- Time specifiers `start` / `end` decorate ordering operators, supporting the full Allen interval algebra (`(start t1) < (end t2)`, etc.).
- Timed preconditions: `(at start φ)`, `(at end φ)`, `(over all φ)`.
- Method constraints beyond ordering: `hold-before`, `hold-after`, `hold-between`, `hold-during`, `always`, `sometime`.

Open / future work the HDDL 2.1 paper itself flags: PDDL 3 preferences, axioms, and a unified plan validator.

---

## 2. InductorHTN feature inventory

### 2.1 Hierarchy (present)

- Methods: `name(?args) :- if(...), do(...).` (`HtnCompiler.h`)
- Operators: `name(?args) :- del(...), add(...).` (`HtnCompiler.h`)
- Method modifiers: `else` (priority-ordered fallback), `anyOf` (try each binding, succeed if any succeed), `allOf` (try each binding, succeed only if all succeed).
- `try(t)` — optional subtask whose failure does not fail the method (`HtnPlanner.cpp` — `CheckForSpecialTask`).
- `parallel(t1, t2, ...)` — annotation used by `PlanParallelizer` to assign timesteps post-planning. Planning itself is still sequential.
- `hidden, op(...)` — operator excluded from final plan output.
- Top-level: `goals(t1, t2, ...).` — totally-ordered initial task list.

### 2.2 Logic / preconditions (Prolog backbone)

- Negation-as-failure: `not(g)`.
- Cut `!`, `first(g)`.
- Equality: `=` (unification), `==` / `\==` (structural equality / inequality).
- Arithmetic comparisons `<`, `>`, `=<`, `>=`; arithmetic via `is(?x, expr)` with `+, -, *, /, abs, min, max, float, integer`.
- Meta-predicates: `findall`, `forall`, `count`, `distinct`, `sortBy`.
- Dynamic state: `assert`, `retract`, `retractall`.
- String / type: `atom_chars`, `atom_concat`, `downcase_atom`, `atomic`.

### 2.3 Engine traits HDDL doesn't mandate

- Stackless DFS with explicit `PlanState`/`PlanNode` (`HtnPlanner.cpp`).
- Hard memory budget with graceful degradation (`SetMemoryBudget`).
- Resolution-step counting for ruleset profiling (`GetLastResolutionStepCount`).
- Decomposition tree with sibling-scope tracking.
- Live REPL (`indhtn.exe`), Python bindings, MCP server with `start_session` / `query` / `step` / `state_diff`.

---

## 3. Side-by-side comparison

| Feature | HDDL | InductorHTN | Notes |
|---|---|---|---|
| Compound tasks | `(:task ...)` declared | Implicit (any method head) | InductorHTN has no separate task-signature declaration |
| Method preconditions | `:precondition` over current state | `if(...)` Prolog goal | InductorHTN preconditions can call any Prolog rule, not just literals |
| Subtask labels | Required (`t1 t2 ...`) | None | Needed for ordering constraints |
| Partial-order subtasks | Native via `:ordering` | None | Closest is `parallel(...)` post-processor |
| Total-order subtasks | Linear `:ordering` chain or `:ordered-subtasks` | Default — `do(a,b,c)` | InductorHTN's only mode |
| Initial task network | `(:htn :tasks ... :ordering ...)` | `goals(t1, t2, ...).` | InductorHTN supports only a totally-ordered list |
| Goal state | `(:goal φ)` checked at end | None | Plan succeeds when all tasks decompose to operators |
| Types | `:types` with subtyping | None | Convention only |
| Object declarations | `(:objects ...)` per problem | Inferred from facts | No closed-world object set |
| Predicate schema | `(:predicates ...)` declared | None | Any well-formed term is admissible |
| Conditional effects | `(when c e)` | None | Workaround: branch at method level |
| Quantified effects | `forall`/`exists` in `:effect` | None | `allOf` covers some precondition cases |
| Numeric fluents | `:functions` with `increase`/`decrease` | Hand-rolled via `del`/`add` of `count(?x, n)` | Plus `is(?x, expr)` for arithmetic |
| Action costs / metric | `:action-costs`, `(:metric ...)` | None | Search is DFS, first solution |
| Durative actions | HDDL 2.1 | None | `parallel(...)` is timestep-only, no duration |
| Time specifiers (`start`/`end`) | HDDL 2.1 | None | — |
| Method constraints (`hold-before` …) | HDDL 2.1 | None | — |
| `forall`/`exists` in preconditions | Yes (with requirement flags) | `forall(Gen, Test)` and via Prolog | InductorHTN's is more meta-predicate-shaped |
| Negation in preconditions | `not` (with flag) | `not(g)` always available | — |
| Equality | `(= ?x ?y)` | `=` (unify), `==`, `\==` | InductorHTN distinguishes unification from structural equality |
| `anyOf` method modifier | No direct equivalent | Yes | InductorHTN-only |
| `allOf` method modifier | No direct equivalent | Yes | InductorHTN-only |
| `else` (priority fallback) | No direct equivalent | Yes | InductorHTN-only; relies on method ordering otherwise |
| `try(...)` (optional task) | No direct equivalent | Yes | — |
| `hidden` operators | No | Yes | — |
| Cut `!` | No | Yes | InductorHTN-only |
| `findall` / `count` / `sortBy` | No | Yes | InductorHTN-only |
| `assert` / `retract` (dynamic facts) | No | Yes | InductorHTN-only |
| Parallel execution annotation | No (use HDDL 2.1) | `parallel(...)` post-pass | InductorHTN-only mid-ground |
| Memory budget | No | Yes | Engine feature |

---

## 4. Most interesting extensions, ranked

Each entry: **what** it is — **why** it matters here — **rough cost** (S/M/L) — **compatibility risk**.

A note on what *isn't* worth lifting from HDDL: a few features that look attractive at first turn out to be syntactic sugar over things the engine already provides, or are already covered by existing constructs. They appear in the "Demoted" subsection at the end.

### Tier 1 — high payoff, modest cost

1. **Labeled subtasks with `:ordering`-style partial order.**
   - **What it is:** subtasks are written `(t1 (taskA ...)) (t2 (taskB ...))` with separate ordering constraints `(t1 < t2)`. Listing no constraint between two subtasks means they are unordered.
   - **Why it isn't a combinatorial explosion:** the planner does not enumerate the N! linearizations. It returns *one plan* whose output is a partial order (a DAG). Linearization happens at execution time, often by a separate scheduler. The actual benefit is search-side: in a totally-ordered planner, two independent tasks `A` and `B` create a spurious `A,B` vs `B,A` choice that backtracking has to traverse if a later task fails. Least-commitment planning adds an ordering edge only when a precondition forces it, so the search visits each independent ordering once instead of `k!` times.
   - **Why it matters here:** the engine already has `parallel(...)` as a post-pass annotation. Promoting it into a planning-time concept would (a) give multi-agent puzzles a real partial-order plan as output, (b) let `parallel(...)` go away as a special case, (c) interop cleanly with HDDL benchmarks. For this codebase's mostly-causal puzzle/game domains the search-compression win is smaller than for logistics, but the cleaner output story is worth it on its own.
   - **Cost: M.** Touches `HtnPlanner.cpp` task-list management, decomposition tree, and the JSON plan emitter.
   - **Compatibility risk: low.** `do(a, b, c)` becomes shorthand for a totally-ordered network.

2. **Typed parameters.**
   - Even without a full PDDL `:types` hierarchy, a lightweight `type(?r, room).` convention validated by the linter would catch the most common authoring bug — passing an enemy where a room is expected, or a tag where an entity is expected. This is especially valuable given the component system's deep stacks of reusable methods.
   - **Cost: M** as a runtime feature; **S** as a linter-only check first.
   - **Compatibility risk: low** if opt-in.

3. **Action costs + plan metric.**
   - Depth-first first-solution is fine for "is there a plan?" but the puzzle/game domains naturally have *better* and *worse* solutions. Action costs combined with the existing `is(?x, expr)` arithmetic would let users ask `findall` to rank plans by length, energy, or risk. Hooks well into `GetParallelizedPlan` JSON output too.
   - **Cost: M.** Search becomes branch-and-bound; needs a cost accumulator on `PlanNode`.
   - **Compatibility risk: low** (default cost = 1 reproduces current behavior).

### Tier 2 — interesting, but bigger lift or more niche

4. **Conditional effects in operators (`when`).**
   - **What it is:** an operator effect like `(when <condition> <effect>)`. A single operator can have multiple `when` clauses that fire independently based on the current state.
   - **Why it isn't just "N method alternatives":** for *mutually exclusive* conditions, branching at the method level (one method per condition) works. The cross-product hits when conditions are *independent*: a room that is both a hazard and a treasure room needs methods for `{¬H ∧ ¬T, H ∧ ¬T, ¬H ∧ T, H ∧ T}` — `2^N` methods. Conditional effects scale with N. The win shows up when the codebase has independent flags that compose: tags + aggro + room properties applied by the same `opMove`.
   - **Cost: M.** Operator-application semantics become richer; affects state-diff tools.

5. **Abstract-task preconditions / effects.**
   - HDDL allows annotating compound tasks with their own preconditions/effects, letting a planner reason about a compound task at a higher level without first decomposing it. Useful for landmark-style heuristics later.
   - **Cost: M–L.** Dovetails with the existing decomposition-tree infrastructure but introduces a verification obligation — the abstract effects must be consistent with the decomposition.

6. **Numeric fluents as first-class state.**
   - **What it is:** PDDL/HDDL distinguish boolean **predicates** from numeric **functions**. A function is a typed, addressable cell with an integer or float value. You declare them in `:functions`, initialise with `(= (energy player) 10)`, query with `(>= (energy ?a) 5)`, and update with `(decrease (energy ?a) 5)` — no del/add of the old value, the engine owns the cell.
   - **What it gives you over the current pattern:** today a numeric value is a fact like `energy(player, 10)`, so to spend energy the operator must (a) take the old value as a parameter, (b) `del` the old fact, (c) compute the new value with `is/2`, (d) `add` the new fact. With first-class fluents, the operator just says "decrement energy by 5." More concise, and the engine guarantees atomic update on backtrack.
   - **Why it's tier 2:** the current pattern works. The win is concision and a slightly cleaner search semantics for resource-style state (energy, ammo, money, time). Worth doing only if the engine starts seeing domains where resources dominate; for tag-and-aggro puzzles the payoff is small.
   - **Cost: M–L.** Touches `HtnTerm`, the rule store, the arithmetic built-ins, and the linter.

### Tier 3 — only if going industrial

7. **HDDL 2.1 durative actions + Allen-interval ordering.**
   - Overlaps with the parallel-execution feature but is much heavier. Worth it only if the engine starts targeting domains with real time (satellite scheduling, robotics).
   - **Cost: L.**

8. **HDDL parser front-end.**
   - Read/write `.hddl` files for interop with PANDA, pyhddl, etc. A thin transpiler from HDDL to InductorHTN syntax would let this engine use the IPC 2020 benchmark suite directly — a strong correctness and performance signal.
   - **Cost: M, mostly mechanical.** Needs an S-expression lexer/parser and a name-mangling scheme for the `?`-prefix variable convention.

### Demoted — already covered, or syntactic sugar

- **Goal-state checking (`:goal`).** A method `checkSolved(?level) :- if(solved(?level)), do().` added to `goals(...)` is functionally equivalent. The marginal differences (cleaner error message, separation of "what the level is" from "what tasks to run") don't justify a feature add. Convention only.
- **Quantified effects (`forall ?x. del(...)/add(...)`).** Already expressible in InductorHTN via `allOf` method modifiers: `removeAllAggro(?e) :- allOf, if(hasAggro(?x, ?e)), do(opLoseAggro(?x, ?e)).` covers the canonical case. The remaining gap is purely ergonomic — saving one level of method indirection — and is not worth a runtime change.

---

## 5. What InductorHTN already does better than HDDL

To balance the picture:

- **Live debugging surface.** REPL with `/t` tracing, decomposition-tree visualisation, step-by-step execution via the MCP `indhtn_apply_operator` tool, state diffs via `indhtn_preview_solution_facts`, and Python bindings for programmatic exploration. PANDA/SHOP-family planners typically expose only a final plan and (sometimes) a search log.
- **Hard memory budgeting.** `SetMemoryBudget` with graceful degradation (return partial solution rather than abort) is uncommon in academic HTN planners.
- **Embedded Prolog backbone.** `findall`, `count`, `distinct`, `sortBy`, `assert`/`retract` are very expressive for puzzle preconditions. HDDL inherits only the static PDDL fragment, which is much less than this.
- **`else`-based method fallbacks.** Priority-ordered strategies are a one-keyword affair. HDDL has no equivalent and relies on the planner's method-ordering heuristics.
- **`parallel(...)` post-pass.** A pragmatic mid-ground between sequential planning and full partial-order planning — domain authors mark independent tasks; the post-processor assigns timesteps without exploding the search space.
- **Resolution-step counting.** `GetLastResolutionStepCount` enables direct, quantitative ruleset profiling — a feature explicitly leveraged by the project's optimization-pattern documentation.

---

## 6. Sources

- Höller, D. et al. *HDDL — A Language to Describe Hierarchical Planning Problems.* AAAI 2020. <https://arxiv.org/pdf/1911.05499>
- Pellier, D. et al. *HDDL 2.1: Towards Defining an HTN Formalism with Time.* 2022. <https://ar5iv.labs.arxiv.org/html/2206.01822>
- IPC 2020 Hierarchical Planning Domains. <https://github.com/panda-planner-dev/ipc2020-domains>
- HDDL overview. <https://www.emergentmind.com/topics/hierarchical-domain-definition-language-hddl>
