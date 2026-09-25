# The InductorHTN language

The one reference for writing `.htn` files. Every `htn` block below runs in CI
(`python scripts/htn_doctest.py docs/reference/language.md`). The `% ?- goal.` lines show what
`FindAllPlans` returns, one plan per `% =>` line. The `% ?: query.` lines show what a Prolog
query returns. If this page and the engine disagree, the test fails; the page is never
silently wrong.

InductorHTN is a SHOP-style HTN planner built on a small Prolog. A **domain** is facts, rules,
methods and operators. The planner takes a **task** and decomposes it **top-down**. A method
says how a task breaks into subtasks when its condition holds. An operator is a leaf step that
changes the state. `FindAllPlans` returns **every** plan that the methods allow.

## 1. Syntax

- Variables start with `?`: `?who`, `?to`. Everything else is a constant: `ogre`, `park2`,
  `3`, `1.5`.
- Write constants in lowercase. An uppercase name is quoted in the output (`'Alice'`).
- Names may contain `-`: `travel-to`. Lists are `[a, b, c]` and `[?head | ?tail]`.
- Comments are `% to end of line` or `/* block */`.
- Every clause ends with `.`. There is no `;` (disjunction). Write two clauses instead.

## 2. Facts and rules: the state

Facts are the world state. Rules derive facts. Rule bodies are Prolog: comma means *and*;
several clauses mean *or*.

```htn
distance(home, park, 2).
distance(home, office, 8).
weather(good).
walkable(?a, ?b) :- weather(good), distance(?a, ?b, ?d), =<(?d, 3).
% ?: walkable(home, ?where).
% => ?where = park
```

## 3. Operators: the only way the state changes

```prolog
name(?args) :- del(facts to remove), add(facts to add).
```

An operator has no condition. It deletes, then adds, and appears in the plan. The method that
calls it must make sure it applies, because the rules are strict:

- `del` of a fact that does not exist is an **error**.
- `add` of a fact that already exists is an **error**.
- `add` of a fact with an unbound variable is an **error**.
- An error **aborts the whole search**, not only that branch. Guard every operator in the
  calling method's `if()`.

```htn
t :- if(), do(opA, opA).
opA :- del(), add(done).
% ?- t.
% => error
```

```htn
t :- if(not(done)), do(opA).
t :- if(done), do().
opA :- del(), add(done).
% ?- t.
% => opA
```

**Arithmetic in task arguments is evaluated when the task is called.** This is how a
counter changes:

```htn
buy(?price) :- if(cash(?m), >=(?m, ?price)), do(pay(?m, -(?m, ?price))).
pay(?old, ?new) :- del(cash(?old)), add(cash(?new)).
cash(10).
% ?- buy(3).
% => pay(10, 7)
```

**Numeric fluents** do the same thing inside the operator. `decrease(pred(args), delta)` and
`increase(...)` find the one fact `pred(args, value)` and replace its value. If no fact
matches, the operator does not apply (no error):

```htn
t :- if(), do(spend(3), check).
spend(?n) :- decrease(mana(me), ?n).
check :- if(mana(me, 7)), do(ok).
ok :- del(), add(checked).
mana(me, 10).
% ?- t.
% => spend(3), ok
```

**`hidden`** keeps an operator out of the plan; its effects still happen. It goes in the
body: `name :- hidden, del(...), add(...).`

```htn
t :- if(), do(opA, note).
opA :- del(), add(a).
note :- hidden, del(), add(noted).
% ?- t.
% => opA
```

## 4. Methods: how a task decomposes

```prolog
task(?args) :- if(condition), do(subtask1, subtask2, ...).
```

- `if()` is a Prolog query on the **current** state (after the operators planned so far).
  `if()` is required, even when empty. `do()` may be empty: the task is then done with no step.
- **Each solution of `if()` is its own branch.** Its bindings flow into `do()`.
- **Several methods for one task are alternatives.** `FindAllPlans` returns a plan for every
  method and every binding that works, in file order.

```htn
go :- if(road(?r)), do(drive(?r)).
go :- if(), do(walk).
drive(?r) :- del(), add(driven(?r)).
walk :- del(), add(walked).
road(a). road(b).
% ?- go.
% => drive(a)
% => drive(b)
% => walk
```

**Constants in the head dispatch.** One method per case is the idiomatic way to branch on a
kind:

```htn
defeat(?e) :- if(weakTo(?e, ?how)), do(apply(?e, ?how)).
apply(?e, fall) :- if(), do(push(?e)).
apply(?e, fire) :- if(), do(ignite(?e)).
push(?e) :- del(), add(fell(?e)).
ignite(?e) :- del(), add(burnt(?e)).
weakTo(ogre, fall). weakTo(ogre, fire).
% ?- defeat(ogre).
% => push(ogre)
% => ignite(ogre)
```

**State flows forward.** A later `if()` sees what earlier operators did:

```htn
t :- if(), do(opA, after).
after :- if(not(x1)), do(opC).
after :- if(x1), do(opD).
opA :- del(), add(x1).
opC :- del(), add(c). opD :- del(), add(d).
% ?- t.
% => opA, opD
```

**Failures are silent.** A subtask with no method or operator of that name, an operator name
used inside `if()`, or a method that has no branch that works all simply give no plan. Use
`python -m htn_components check` to catch misspelled names.

## 5. Choosing and committing

This table matters most. Pick the construct by what the plans should be.

| You want | Write | Plans |
|---|---|---|
| every strategy that works | several plain methods | one per method and binding |
| one strategy, with fallbacks | methods after the first marked `else` | the first group that finds a plan |
| one binding of a query | `first(goals...)` in `if()` | only the first solution |
| do it for every binding | `allOf` method | one plan that does all of them; fails if any fails |
| do it for bindings where it works | `anyOf` method | one plan with those that succeed; fails if none do |
| an optional step | `try(task)` in `do()` | the step whenever it can run; skipped only if it can't |

### `else`: fallback, not a cut

An `else` method is tried only if the methods above it (back to the previous non-`else`
method) found **no plan**:

```htn
go :- if(road(?r)), do(drive(?r)).
go :- else, if(), do(walk).
drive(?r) :- del(), add(driven(?r)).
walk :- del(), add(walked).
road(a). road(b).
% ?- go.
% => drive(a)
% => drive(b)
```

**`else` is not a cut.** If the task that comes after fails, the planner backtracks **into**
the `else` branch. Here `drive` works, `arrive` then fails, and the planner falls back to
`walk`:

```htn
trip :- if(), do(go, arrive).
go :- if(road(?r)), do(drive(?r)).
go :- else, if(), do(walk).
arrive :- if(walked), do(rest).
drive(?r) :- del(), add(driven(?r)).
walk :- del(), add(walked).
rest :- del(), add(rested).
road(a).
% ?- trip.
% => walk, rest
```

So a do-nothing `else` branch runs every time the branch above it fails for any reason. That
can let a plan skip a cost or finish with work undone. **Guard a base case with the negation of
its condition, not with `else, if()`:**

```htn
clear :- if(first(enemy(?e), alive(?e))), do(kill(?e), clear).
clear :- if(not(enemy(?e), alive(?e))), do().
kill(?e) :- if(weapon), do(hit(?e)).
hit(?e) :- del(alive(?e)), add(dead(?e)).
enemy(orc). alive(orc).
% ?- clear.
% => no plan
```

With `else, if()` as the base case, the same world returns the empty plan, a "success" that
leaves the orc alive:

```htn
clear :- if(first(enemy(?e), alive(?e))), do(kill(?e), clear).
clear :- else, if(), do().
kill(?e) :- if(weapon), do(hit(?e)).
hit(?e) :- del(alive(?e)), add(dead(?e)).
enemy(orc). alive(orc).
% ?- clear.
% => (empty plan)
```

### `first()`

`first(g1, g2, ...)` keeps only the first solution of the conjunction:

```htn
pick :- if(first(item(?i), good(?i))), do(take(?i)).
take(?i) :- del(), add(has(?i)).
item(a). item(b). item(c). good(b). good(c).
% ?- pick.
% => take(b)
```

A later failure does not revisit the solutions `first` threw away:

```htn
t :- if(first(p(?x))), do(op(?x), need2(?x)).
need2(?x) :- if(==(?x, 2)), do().
op(?a) :- del(), add(s(?a)).
p(1). p(2).
% ?- t.
% => no plan
```

### `allOf` and `anyOf`

```htn
all :- allOf, if(item(?i)), do(take(?i)).
any :- anyOf, if(item(?i)), do(maybe(?i)).
maybe(?i) :- if(good(?i)), do(take(?i)).
take(?i) :- del(), add(has(?i)).
item(a). item(b). item(c). good(b). good(c).
% ?- all.
% => take(a), take(b), take(c)
% ?- any.
% => take(b), take(c)
```

If `if()` has no solution, both fail. An empty `if()` runs `do()` once.

### `try()`: optional, and it commits

`try(task)` runs the task whenever it can, and is skipped only when it can't. Each binding
still gives its own plan:

```htn
t :- if(), do(opA, try(opt), opB).
opt :- if(bonus(?x)), do(get(?x)).
opA :- del(), add(a). opB :- del(), add(b). get(?x) :- del(), add(got(?x)).
bonus(1). bonus(2).
% ?- t.
% => opA, get(1), opB
% => opA, get(2), opB
```

Once the `try` body has succeeded, the planner never goes back to try the plan without it.
Here the `try` spends the coin the next task needs, so there is no plan:

```htn
t :- if(), do(try(spend), buy).
spend :- if(coin), do(opSpend).
buy :- if(coin), do(opBuy).
opSpend :- del(coin), add().
opBuy :- del(coin), add(bought).
coin.
% ?- t.
% => no plan
```

### `parallel()`

`parallel(a, b)` marks tasks that may run at the same time. The plan carries markers, and
`GetParallelizedPlan` schedules them. Planning is unchanged:

```htn
t :- if(), do(parallel(a1, a2), b1).
a1 :- del(), add(x1). a2 :- del(), add(x2). b1 :- del(), add(y).
% ?- t.
% => beginParallel(1), a1, a2, endParallel(1), b1
```

## 6. Recursion

A recursive task needs a base case and a condition that makes progress. Navigation uses the
built-in `pathNext(?from, ?to, ?next)`, the first hop of a shortest route over `linked/2`
facts. It fails when `?from == ?to`, so the base case is a separate method:

```htn
navigate(?who, ?to) :- if(at(?who, ?to)), do().
navigate(?who, ?to) :- else, if(at(?who, ?here), pathNext(?here, ?to, ?next)),
    do(opMoveTo(?who, ?here, ?next), navigate(?who, ?to)).
opMoveTo(?who, ?from, ?to) :- del(at(?who, ?from)), add(at(?who, ?to)).
linked(a, b). linked(b, a). linked(b, c). linked(c, b). linked(c, d). linked(d, c).
at(hero, a).
% ?- navigate(hero, d).
% => opMoveTo(hero, a, b), opMoveTo(hero, b, c), opMoveTo(hero, c, d)
```

Here `else` is correct: the two methods exclude each other, and the base case does nothing
that could be skipped.

## 7. Built-ins

These are all of them (`HtnGoalResolver.cpp`, `HtnTerm.cpp`). Anything else is a fact or rule
you define, and an undefined name is simply false.

| Group | Built-ins |
|---|---|
| Logic | `not(g...)`, `first(g...)`, `forall(generator, test)`, `=`, `==`, `\==` |
| Compare | `<`, `>`, `=<`, `>=` (numbers) |
| Arithmetic | `is(?x, expr)` with `+ - * /`, `min(a,b)`, `max(a,b)`, `abs(a)`, `float(a)`, `integer(a)` |
| Aggregates | `count(?n, g...)`, `sum(?s, ?v, g...)`, `min(?m, ?v, g...)`, `max(?m, ?v, g...)`, `findall(?t, g, ?list)`, `distinct(?key, g...)`, `sortBy(?key, <(g...))` or `>(g...)` |
| Graph | `pathNext(?from, ?to, ?next)` over `linked/2` |
| Atoms | `atomic(?x)`, `atom_chars`, `atom_concat`, `downcase_atom` |
| Debug | `print`, `write`, `writeln`, `nl`, `showTraces`, `failureContext` |
| Database | `assert`, `retract`, `retractall` (avoid in domains: use operators) |

```htn
item(a, 3). item(b, 5). item(c, 5).
% ?: count(?n, item(?x, ?y)).
% => ?n = 3
% ?: sum(?s, ?y, item(?x, ?y)).
% => ?s = 13
% ?: max(?m, ?y, item(?x, ?y)).
% => ?m = 5
% ?: findall(?x, item(?x, 5), ?l).
% => ?l = [b, c]
% ?: sortBy(?y, >(item(?x, ?y))).
% => ?y = 5, ?x = b
% => ?y = 5, ?x = c
% => ?y = 3, ?x = a
% ?: distinct(?y, item(?x, ?y)).
% => ?y = 3, ?x = a
% => ?y = 5, ?x = b
```

Numbers: `/` on two integers is integer division. Use a float to get a fraction. There is no
unary minus, so write `-(0, ?x)`. `==` is structural: `==(1, 1.0)` fails, while `=<` and `>=`
compare values.

```htn
n(1).
% ?: is(?x, /(7, 2)).
% => ?x = 3
% ?: is(?x, /(7.0, 2)).
% => ?x = 3.500000000
% ?: ==(1, 1.0).
% => false
```

## 8. This is not SWI-Prolog

These are **silently false** (no error), so a condition that uses them never holds:

| SWI-Prolog | Here |
|---|---|
| `\+ g` | `not(g)` |
| `X \= Y` | `not(=(?x, ?y))` or `\==(?x, ?y)` |
| `member(X, L)` | a fact per element, or `[?h \| ?t]` recursion in a rule |
| `append`, `length`, `nth0`, `call`, `=..`, `bagof`, `setof` | not available |
| `X is Y` (infix) | `is(?x, ?y)`, always prefix |

These fail to **compile**: `;` (disjunction), `->`, and a method without `if()`. `<=` and `=>`
are errors at run time: write `=<` and `>=`.

```htn
p(a).
% ?: \=(a, b).
% => false
% ?: member(?x, [a, b]).
% => false
```

## 9. Glossary: HTN terms in this dialect

| Term | Here |
|---|---|
| compound task | any head that has methods |
| primitive task | an operator; the only thing that appears in a plan |
| method | `task :- if(...), do(...).`, one way to decompose a task |
| precondition | the method's `if()`. **Operators have none.** |
| effect | the operator's `del`/`add`/`increase`/`decrease`. **Methods have none.** |
| method order | the order plans are returned in, and the grouping for `else` |
| state | facts plus rules; rules are recomputed on every query |
| problem | the facts of a level or scenario, kept apart from the domain |

## 10. Things from other HTN systems that do not exist here

- **Operator preconditions:** put the condition in the method that calls the operator.
- **Runtime operator code** (C#/C++ callbacks): an operator is only `del`/`add`.
- **Method effects:** a method only decomposes; state changes come from operators.
- **Utility or random selection, costs, replanning during execution:** the planner returns
  every plan, and the caller chooses.
- **Partial order:** tasks in `do()` run in order. `parallel()` is only a marker.
- **Goal networks** (`achieve(fact)`): write a task that tests the fact in `if()` and
  decomposes toward it.

## 11. Running

- Python: `HtnPlanner.HtnCompileCustomVariables(text)`, then
  `FindAllPlansCustomVariables("task(args).")`. Every call returns `(error, json)`.
- The REPL: `./build/Release/indhtn.exe file.htn`. The MCP tools are listed in `docs/tools/`.
- A file may end with `goals(task1, task2).` for the REPL and tests.
- After a search that finds no plan, use a fresh planner (see `docs/reference/planner-internals.md`).
