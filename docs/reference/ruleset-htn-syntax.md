# Ruleset HTN Syntax

> **Ruleset doc trio.** **Syntax** (this file) - what each keyword/construct
> means and when to use it. Writing (`ruleset-writing.md`) - heuristics + measured
> optimizations. Iterating (`ruleset-iterating.md`) - debug/analyze/improve a
> ruleset.

Each construct below lists what it does, its syntax, and **when it's a good idea
to use it**. (This doc is the reference; the highlighter extension under
`editors/vscode-htn/` is a separate thing.)

## Methods (task decomposition)

Methods decompose a compound task into subtasks. Parsed by `HtnCompilerBase`
(`src/FXPlatform/Htn/HtnCompiler.h`).

```prolog
methodName(?params) :- if(preconditions), do(subtask1, subtask2).

travel(?dest) :- if(at(?start), canReach(?start, ?dest)), do(move(?start, ?dest)).
move(?from, ?to) :- if(hasVehicle(?v)), do(drive(?v, ?from, ?to)).
move(?from, ?to) :- if(), do(walk(?from, ?to)).
```

**Multiple plain methods (no `else`) for one task is the default**, and the
single most important authoring choice: `FindAllPlans` enumerates *one plan per
method whose `if()` holds*, so plain alternatives = "all the genuinely different
ways to do this." Reach for `else` only when you instead want a priority ladder.

## Operators (primitive actions)

Operators change world state directly; no `if`/`do`.

```prolog
operatorName(?params) :- del(factsToRemove), add(factsToAdd).

walk(?from, ?to) :- del(at(?from)), add(at(?to)).

% Consumables are tokens, not counters: the method picks a token in if(),
% the operator deletes it. One fact per remaining use.
drive(?vehicle, ?from, ?to, ?tok) :-
    del(at(?from), fuel(?vehicle, ?tok)),
    add(at(?to)).

travel(?to) :- if(at(?from), hasVehicle(?v), first(fuel(?v, ?tok))),
               do(drive(?v, ?from, ?to, ?tok)).
```

**Operators cannot run `is()`.** `HtnCompilerBase` drops any `is()` after
`add()`, and the planner substitutes del/add with the head's MGU only
(`HtnPlanner` operator application). So `fuel(?v, ?newF)` with
`is(?newF, -(?f, 1))` silently does nothing, and every variable in
`del`/`add` must appear in the head. For a counter use a numeric fluent
(`decrease(fuel(?v), 1)`); for a consumable use tokens
(`fuel(car, f1). fuel(car, f2).`) and delete one per use.

## Method modifiers

### `else` - preference ladder

A method marked `else` runs only if all earlier non-`else` methods failed.

```prolog
travel(?dest) :- if(hasCarKey), do(drive(?dest)).
travel(?dest) :- else, if(hasBusPass), do(takeBus(?dest)).
travel(?dest) :- else, if(), do(walk(?dest)).
```

**When to use:** you want exactly the *first* applicable option, not all of them
-- a real priority order or a "nothing else applied" fallback. If you instead
want every viable strategy enumerated as separate plans, use plain methods (no
`else`). When you do use `else`, order the methods most-likely-first to cut
backtracking:

```prolog
travel(?dest) :- if(nearby(?dest)), do(walk(?dest)).      % common case first
travel(?dest) :- else, if(hasCar), do(drive(?dest)).
travel(?dest) :- else, if(), do(callTaxi(?dest)).
```

### `anyOf` - run `do()` for each binding, succeed if any succeeds

Each binding's `do()` is wrapped in `try()`; the method succeeds if at least one
works.

```prolog
attackEnemies() :- anyOf, if(inRange(?enemy)), do(attack(?enemy)).
```

**When to use:** "act on whichever targets you can, and partial success is fine"
-- e.g. attack every in-range enemy and succeed as long as one attack lands.

### `allOf` - run `do()` for each binding, succeed only if all succeed

```prolog
healAllWounded() :- allOf, if(wounded(?ally)), do(heal(?ally)).
```

**When to use:** "apply an effect to *every* match, all-or-nothing" -- e.g. one
key that must open every door it fits, or heal all wounded allies (fail if any
heal fails).

> `anyOf`/`allOf` handle multiple bindings *within one method*; they are not for
> choosing *between* methods (that's plain alternatives / `else`).

## Operator modifiers

### `hidden` - keep an operator out of the plan output

```prolog
hidden, opResolveAtom(?atom, ?how) :- del(), add(resolved(?atom)).
```

**When to use:** internal bookkeeping markers you don't want cluttering the
emitted plan (resolution markers, instrumentation), while still mutating state.

### `increase` / `decrease` - numeric fluents

For a fact shaped `pred(arg1, ..., argN, value)` with a numeric last argument, an
operator can change the value in place.

```prolog
opGain(?n)     :- increase(score(player), ?n).
opSpend(?cost) :- decrease(mana(player), ?cost).
opSwap(?a, ?b) :- decrease(mana(?a), 10), increase(mana(?b), 10).
```

Semantics: the engine finds the unique matching fact, evaluates the delta with the
`is/2` arithmetic engine (`+ - * /`, `abs`, ...), and replaces the value. Effect
order within an operator: all `del()`, then `increase`/`decrease`, then `add()`.
Fails (planner backtracks) if no fact or more than one fact matches, or the last
argument isn't numeric.

**When to use:** resource tracking (`mana`, `health`, `score`, `stamina`). Prefer
this over the verbose `del`+`add`+`is/2` form -- they are observably equivalent:

```prolog
% Verbose                              % Concise (preferred)
spend(?c) :- if(mana(player,?o), is(?n,-(?o,?c))), do(opV(?o,?n)).
opV(?o,?n) :- del(mana(player,?o)), add(mana(player,?n)).
opC(?c)    :- decrease(mana(player), ?c).
```

## Built-in constructs

### `try()` - optional execution

If the wrapped task fails, the parent method still succeeds.

```prolog
collectRewards() :- if(), do(getMainReward, try(getBonusItem)).
```

**When to use:** optional side-effects that may not be possible -- grab a bonus if
present, apply a tag only if the target is taggable -- without failing the plan.

### `first()` - first solution only

Returns just the first solution of a query and prevents backtracking into the rest.

```prolog
getTaxi() :- if(first(available(?taxi))), do(hire(?taxi)).
```

**When to use:** any single solution suffices and the alternatives are
interchangeable (pick *any* available taxi). Note: `first()` has overhead; for
small result sets it may not pay off -- measure.

### `not()` - negation as failure

`not(Goal)` succeeds when `Goal` cannot be proved.

```prolog
% bind ?loc first, THEN test it has no enemy
safeSpot(?loc) :- if(location(?loc), not(enemy(?loc))), do(camp(?loc)).
```

**When to use:** exclude candidates by a property -- "a location with no enemy",
"an item not already taken". **Always bind the variable before `not()`**: an
unbound variable makes `not()` succeed if *any* non-matching value exists, which
is almost never what you mean.

## Types (linter type checking)

Types are a **linter-only** concern — the engine never sees them. A constant's
type(s) are inferred from the **unary facts** it appears under:

```prolog
skill(frostNova).      % frostNova : skill
enemy(gateGuard).      % gateGuard : enemy
agent(gateGuard).      % ... and also : agent (an instance may have many sorts)
```

The linter infers a type for every argument position (from facts, rule bodies,
and how variables flow between goals) and emits `TYP010` when an argument's
type is **provably disjoint** from a well-determined position — including
variables. It is high-signal: it never flags a position whose sorts overlap on
some instance, nor a genuinely polymorphic/under-determined one. Unary
predicates an operator `del`/`add`s (e.g. `at/1`) are treated as mutable
*state*, not sorts.

**Optional `%::` directive.** To document or pin a contract inference can't
reach, place a directive comment directly above the rule. It's a Prolog
comment, so the engine ignores it; the linter binds the named head variables
and anchors the position's expected type:

```prolog
%:: disableEnemy(?e: enemy)
disableEnemy(?e) :- if(...), do(opFight(player, ?e)).
```

> Legacy: `type(typeName, instance).` and `signature(pred, [types]).` facts are
> no longer read by the linter. Convert `type(skill, frostNova).` to the unary
> fact `skill(frostNova).`; use a `%::` directive for an explicit contract.

## Complete example

```prolog
travel(?destination) :-
    if(at(?start), canReach(?start, ?destination)),
    do(move(?start, ?destination)).

move(?from, ?to) :- if(hasVehicle(?v)), do(driveVehicle(?v, ?from, ?to)).
move(?from, ?to) :- if(hasTicket(?from, ?to)), do(takeTransport(?from, ?to)).
move(?from, ?to) :- else, if(), do(walk(?from, ?to)).

driveVehicle(?v, ?from, ?to) :- del(at(?from), hasVehicle(?v)), add(at(?to), usedVehicle(?v)).
walk(?from, ?to)             :- del(at(?from)), add(at(?to), tired).

at(home).  hasVehicle(car).  canReach(home, work).
goals(travel(work)).
```

## Testing patterns

```cpp
compiler->ClearWithNewRuleSet();              // CRITICAL: always clear state
CHECK(compiler->Compile(program));
auto solutions = planner->FindAllPlans(factory.get(),
    compiler->compilerOwnedRuleSet(), compiler->goals());
```

Expected formats: success `"[ { op1(args), op2(args) } ]"`; empty plan `"[ { () } ]"`;
failure `"null"`; bindings `"((?X = value))"`.
