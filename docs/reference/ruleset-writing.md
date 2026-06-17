# Ruleset Writing

> **Ruleset doc trio.** **Writing** (this file) - heuristics, examples, and
> measured optimizations for building a good ruleset. **Syntax**
> (`ruleset-htn-syntax.md`) - what each keyword means and when to use it. **Iterating**
> (`ruleset-iterating.md`) - how to interact with, debug, analyze, and improve a
> ruleset you already have.

The governing idea: **in an HTN solver the vocabulary is the design** -- the
`if()` is a rule of the world, an operator's `del`/`add` is a law of physics, a
fact is a truth about the problem. The planner reads exactly these. Each
heuristic below has a negative (avoid) and positive (prefer) example.

## Modeling -- choose the right vocabulary

- **Start from a documented domain, don't invent the shape.** Port a published
  total-order HTN (Game AI Pro ch.12 Trunk Thumper, the IPC HTN tracks: Transport,
  Rover, Barman) rather than designing the decomposition from scratch.
- **Data plus general verbs, not a script of bespoke steps.** Reusable verbs
  over world facts beat one method per situation.
  - Avoid: `crossDoorWithTeleport(?c)`, `opPressButton1(?c)`, `opRejoin(?c1,?c2)`.
  - Prefer: `goTo(?c, ?area)` reading `connected/2` + `connectedSkill/3` facts.
- **One source of truth.** Keep only the predicate your methods actually query.
  - Avoid: `type(agent, gateGuard).` *beside* `enemy(gateGuard).` -- the engine
    reads only `enemy/1`, so the `type/2` line is invisible and drifts.
  - Prefer: `enemy(gateGuard).` alone, queried by `disableEnemy(?e) :- if(enemy(?e), ...)`.
- **Full-relation arity.** Give a predicate an argument for every dimension that
  changes its meaning; don't hide an assumption a small arity can't state.
  - Avoid: `skillGrants(lightningStep, electrified).` (lands on whom?).
  - Prefer: `skillGrants(lightningStep, electrified, target).` and
    `skillGrants(lightningStep, teleport, self).`
- **Closed, minimal vocabulary.** Every term should be produced and consumed by
  something; orphans read as capabilities that don't exist.
  - Avoid: declaring `effect(overloaded)` that no skill grants and no rule derives.
  - Prefer: each effect is *granted* (`skillGrants`) or *derived*
    (`comboRule`/`effectImplies`), never declared in a vacuum.
- **Decodable names.** Name predicates and tasks after the mechanic, not the
  fiction or one hard-coded step.
  - Avoid: `dismantleCore`, `Button1`.
  - Prefer: `attackBackWhileDistracted`, `locked(door, key, from, to)`.
- **Follow the `op` naming convention (load-bearing).** Real operators (anything
  with a `del`/`add`/fluent effect) start with `op` (`opMoveTo`); the
  tree-reconstruction tooling strips that prefix, so a non-`op` operator breaks
  it. Method markers `m<N>_...` are auto-inserted by preprocessing -- never
  hand-written.

**Type hints (optional, linter-only -- how to use them).** Declare a
`signature/2` for a predicate whose call sites pass *constants*, plus `type/2`
facts for those constants; the linter then flags a wrong literal (`TYP001`):

```prolog
signature(disableEnemy, [agent]).
type(agent, gateGuard).  type(agent, sentinel).
clearGate() :- if(), do(disableEnemy(gteGuard)).   % TYP001: gteGuard is not an agent
```

It checks *only* constants written directly in `if/do/del/add` -- never variables
(the common case) -- so it is a typo-catcher for literal call sites, not a type
system. The planner ignores `type/2` and `signature/2` entirely; with no
`signature/2` declared, type hints do nothing. Skip them unless a predicate is
routinely called with literal constants.

## Logic-programming efficiency -- order the work

Numbers are from `prototypes/optimization-proofs/` (resolution steps, same query
on a slow vs fast ruleset; re-run `measure.py` to refresh).

- **Order goals by constraint, not by category.** Put the `if()` goal with the
  fewest solutions first, and resolve its variables before introducing the next.
  - Avoid: `findRich(?p) :- person(?p), rich(?p).` (enumerates every person);
    likewise never lead with `actor(?a), actor(?b), f(?a,?b)` -- that walks every
    pair before filtering.
  - Prefer: `findRich(?p) :- rich(?p), person(?p).` -- the one-solution goal binds
    first, then `person/1` just verifies it. **(31 -> 10 steps)**
- **Pre-compute instead of `not()` at query time.**
  - Avoid: `ok(?x) :- item(?x), not(excluded(?x)).` (re-proves the negation per item).
  - Prefer: materialize the allowed set as facts -- `ok(?x) :- okItem(?x).`
    **(61 -> 15 steps)** Always bind a variable before it appears in `not()`.
- **Count directly; don't build a list only to discard it.**
  - Avoid: `teamSize(?n) :- findall(?m, member(?m,t), ?l), count(?n, member(?x,t)).`
  - Prefer: `teamSize(?n) :- count(?n, member(?x, t)).` **(34 -> 19 steps)**
- **Commit with a cut when exactly one branch should apply.**
  - Avoid: three mutually-exclusive `classify/2` clauses left as open choice points.
  - Prefer: `classify(?x, positive) :- >(?x, 0), !.` (and so on). **(12 -> 9 steps)**

> *First-argument indexing* is a classic Prolog win, but our harness measured
> **no gain on this engine** (identical steps and wall-clock, slow == fast at
> 8000 facts), so don't rely on it here -- order a fact's arguments for
> readability instead.

## Recursion and search -- don't let it explode

- **Be wary of recursion** -- the easiest path to exponential blow-up or
  non-termination; depth/hierarchy is good, unbounded recursion is not.
  - Avoid: `reach(?a,?c) :- linked(?a,?b), reach(?b,?c).` -- no guard, loops on cycles.
  - Prefer: a base case plus a step that strictly shrinks the problem, or push it
    to a built-in (below).
- **Push heavy computation into built-ins.** Connectivity, shortest paths,
  arithmetic, and counting belong in C++, not in planner-level search.
  - Avoid: a recursive `reachable/2` the planner branches over.
  - Prefer: `pathNext(?from, ?to, ?next)` (native Dijkstra), stepped one hop at a time.
- **Carry state forward; cache derived facts.**
  - Avoid: recomputing a derived set inside every method's `if()`.
  - Prefer: derive it once via an axiom -- `canApply(?s,?e,?t) :- ...` -- that the
    rest of the ruleset queries.

## HTN structure -- use the hierarchy

- **Build depth** (goal -> strategy -> action -> operator); a flat list of
  operators is a behaviour tree, not an HTN.
- **Preconditions are your search control**: gate each method so impossible
  decompositions are pruned before the planner enters the body, cheapest and most
  constraining check first.
- **One method per genuinely different strategy**: list real alternatives as plain
  methods so the planner enumerates every viable plan; reserve `else` for a true
  preference ladder.
- **Layer precondition strictness**: goals validate everything, reusable actions
  check the key requirements, operators and triggers trust their caller.
- **Author bottom-up and trust the engine over the linter**: validate leaf
  operators before the goal; when they disagree, believe `find_plans` (e.g. the
  linter rejects `hidden`/`parallel` as atoms, but the engine accepts them).

## Validated optimization patterns

Proven by `prototypes/optimization-proofs/measure.py` (each pattern is a slow/fast
`.pl` pair computing the same answer; numbers are this engine's resolution steps):

| Pattern | slow -> fast | improvement |
|---------|--------------|-------------|
| Constraining goal first        | 31 -> 10 | 68% |
| Pre-computed negation          | 61 -> 15 | 75% |
| Direct count vs findall+count  | 34 -> 19 | 44% |
| Cut for deterministic choice   | 12 -> 9  | 25% |

## See also

- `ruleset-htn-syntax.md` -- keyword/construct reference (`else`, `anyOf`/`allOf`,
  `first`, `not`, `try`, numeric fluents).
- `ruleset-iterating.md` -- interact with, debug, analyze, and improve a ruleset.
- Worked example: Challenge 1 of `prototypes/fortress-loadout/level.htn`
  (the data-plus-verbs model).

## Sources

Triska, *Efficiency of Prolog* (metalevel.at/prolog/efficiency); Covington et al.,
*Coding Guidelines for Prolog* (arXiv:0911.2899); *Learn Prolog Now!* (clause/goal
ordering, termination); SWI-Prolog manual (clause indexing); Nau et al., *SHOP2*
(arXiv:1106.4869); Georgievski & Aiello, *An Overview of HTN Planning*
(arXiv:1403.7426).
