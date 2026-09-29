# HTN patterns, with where to see them

Retrieve examples by **pattern**, not by subject. First decide which patterns the task needs,
then read the lines listed for them. "Replenish ammo" looks like "replenish health" but is
built like "acquire a skill" (P4). Every example below was rated 4-5★ by the owner (see
`rubric.md`). Line numbers are for the current files.

| # | Pattern | Use when | Read |
|---|---|---|---|
| P1 | Strategy menu | a need can be met several distinct ways | **Combos 7-9**, Taxi 9-12, TrunkThumper 245-300 |
| P2 | Feasibility in `if()`, generic verbs in `do()` | writing any strategy | **Combos 15-44** (`wetAndFreeze`, `oilAndBurn`, `stunAndSlow`) |
| P3 | A strategy is its roles and the states to achieve | a combo is "get A, then get B" | **Combos 15-35** (`applyTag` once per role) |
| P4 | A verb whose methods are the ways | several ways to reach one state | **Combos 50-55** (`applyTag`: already, a skill, a lure onto a location), 57-60 (`prepareToUseSkill`), 125-128 (`getAggro`); Taxi 9-12 (`travel-to`) |
| P5 | Already-done case first | a verb may find its state already true | **Combos 51** (`applyTag`), 93-96 (`landTag`), 116-119 (`goToLocation`), 130-133 (`bringEnemyTo`) |
| P6 | Movement | going somewhere | game rulesets: one step, **Combos 113-123** (the engine pathfinds, `vocabulary.md`; arriving lands the location's tag); other domains: `pathNext` recursion, TrunkThumper 233-242 |
| P7 | Lure: aggro, then walk, and it follows | moving an enemy that won't go by itself | **Combos 130-133** (`bringEnemyTo`), 125-128 (`getAggro`), 121-123 (`enemiesFollow`) |
| P8 | Distinct actors, synchronized | two companions must act together | **Combos 15-44** (every strategy binds two companions with `\==`; `stunAndSlow` adds `opSynchronize`) |
| P9 | Variant selection with an `else` ladder | pick one version of an action, by priority | TrunkThumper 280-286, Game 62-70 |
| P10 | One binding with `first()` | any one of several is enough | Taxi 11 (hail one taxi) |
| P11 | Every binding with `allOf` | do it to each one that qualifies | **Combos 69-70** (a skill's tags), 103-104 (everyone at a location), 121-123 (every follower) |
| P12 | Optional consequence with `try()` | a side effect that happens when it can | `language.md` section 5 (no rated game ruleset uses it now) |
| P13 | Recursion that re-arms | a strategy that repairs its own precondition | TrunkThumper 296-300 |

`Examples/Combos.htn` is the reference for game rulesets: it uses the vocabulary of `vocabulary.md`.
Paths: `Examples/Combos.htn`, `Examples/Taxi.htn`, `Examples/TrunkThumper.htn`,
`Examples/CombatLevel1_GreaseTrap.htn`, `Examples/Game.htn`. The same ideas as reusable
components: `components/gamehack/` (P2-P8) and `components/primitives/tags` (P5).

## P1. Strategy menu

The need is a task. Each strategy is one plain method (no `else`), so `FindAllPlans` returns one
plan per strategy that works.

```prolog
defeat(?t) :- if(enemy(?t), not(hasTag(?t, dead))), do(wetAndFreeze(?t)).
defeat(?t) :- if(enemy(?t), not(hasTag(?t, dead))), do(oilAndBurn(?t)).
```

## P2. Feasibility in `if()`, generic verbs in `do()`

`if()` binds the target, the skills **by property**, and the actors, and rules out what can't
work (immunity, the same actor twice). `do()` only uses verbs that other strategies share.
See rubric R1.

## P3. A strategy is its roles and the states to achieve

```prolog
oilAndBurn(?t) :-
    if(enemy(?t), vulnerableToLocationCombo(?t, oil, burning), not(hasTag(?t, oil)),
       companion(?lurer), companion(?caster), \==(?lurer, ?caster)),
    do(applyTag(?lurer, oil, ?t), applyTag(?caster, burning, ?t)).
```

`if()` names the roles, distinct. Each subtask says **what must become true**, and whose doing it
is: the enemy has oil (the lurer's), then it is burning (the caster's). How is the verb's job
(P4): `applyTag` lures it onto the oil, or uses a skill. Not "walk to X, cast Y, wait".

## P4. A verb whose methods are the ways

```prolog
applyTag(?a, ?tag, ?t) :- if(hasTag(?t, ?tag)), do(opTagAlreadyOnTarget(?tag, ?t)).
applyTag(?a, ?tag, ?t) :- if(not(hasTag(?t, ?tag)), not(immune(?t, ?tag)), skillAppliesTag(?s, ?tag)),
    do(prepareToUseSkill(?a, ?s, ?t), useSkillOnTarget(?a, ?s, ?t)).
applyTag(?a, ?tag, ?t) :- if(not(hasTag(?t, ?tag)), not(immune(?t, ?tag)), locationCanApplyTag(?l, ?tag), not(at(?t, ?l))),
    do(bringEnemyTo(?a, ?t, ?l)).

prepareToUseSkill(?a, ?s, ?t) :- if(hasSkill(?a, ?s)), do(goToSameLocation(?a, ?t)).
prepareToUseSkill(?a, ?s, ?t) :- if(companion(?a), not(hasSkill(?a, ?s)), object(?o), canGetSkillFrom(?o, ?s)),
    do(goToSameLocation(?a, ?o), getSkillFrom(?a, ?o, ?s), goToSameLocation(?a, ?t)).
```

Like Taxi's `travel-to`, the caller states the goal and never picks the way. A new way to put a
tag on a target, or to hold a skill, is one more method here, and every strategy benefits. The
actor (`?a`) is a parameter: the strategy binds its roles, the verb finds the way for that one. Bind an actor
only in the method that needs one: binding it where nothing moves gives one identical plan per
companion.

## P5. Already-done case first

```prolog
landTag(?tag, ?t) :- if(hasTag(?t, ?tag)), do(opTagAlreadyOnTarget(?tag, ?t)).
landTag(?tag, ?t) :- if(not(hasTag(?t, ?tag)), not(immune(?t, ?tag))), do(opApplyTag(?tag, ?t)).
landTag(?tag, ?t) :- if(not(hasTag(?t, ?tag)), immune(?t, ?tag)), do().
```

The already-true case does the vocabulary's no-op operator for that state, so the plan shows
it. The conditions exclude each other, so there is no `else` to fall through (see
`language.md`, "else is not a cut").

## P6. Movement

Game rulesets move in one step; the engine finds the path:

```prolog
goToLocation(?a, ?l) :- if(at(?a, ?l)), do(opStayInLocation(?a)).
goToLocation(?a, ?l) :- if(location(?l), at(?a, ?from), \==(?from, ?l)),
    do(opMoveTo(?a, ?from, ?l), enemiesFollow(?a, ?from, ?l)).
```

Other domains with a map of `linked/2` facts navigate by `pathNext` recursion, for any
distance, never with 1-, 2- and 3-hop method ladders:

```prolog
navigateTo(?who, ?dest) :- if(at(?who, ?dest)), do().
navigateTo(?who, ?dest) :- else, if(at(?who, ?cur), pathNext(?cur, ?dest, ?next)),
    do(opMoveTo(?who, ?cur, ?next), navigateTo(?who, ?dest)).
```

## P7. Lure

```prolog
bringEnemyTo(?lurer, ?e, ?l) :- if(enemy(?e), not(static(?e)), not(at(?e, ?l))),
    do(goToSameLocation(?lurer, ?e), getAggro(?e, ?lurer), goToLocation(?lurer, ?l)).
```

The caller's `if()` chooses the lurer. `goToLocation` moves every enemy after the lurer with it
(`opAggroMoveTo`).

## P8. Distinct actors, synchronized

`companion(?a1), companion(?a2), \==(?a1, ?a2)` in `if()`. Both prepare independently, then
`opSynchronize(?a1, ?a2)` (an action for the game engine, with no state change), then both act.

## P9. Variant selection with an `else` ladder

When the methods are versions of **one** action rather than different strategies, an `else`
ladder makes exactly one apply, so it doesn't multiply the plans:

```prolog
doTrunkSlam(?t, ?e) :- if(stamina(?t, ?s), >=(?s, 4)), do(opTaunt(?t, ?e), opPowerSlam(?t, ?e)).
doTrunkSlam(?t, ?e) :- else, if(), do(opTelegraph(?t, ?e), opTrunkSlam(?t, ?e)).
```

## P10-P13

- **`first()`:** `if(first(at(?x), at-taxi-stand(?t, ?x), ...))`, when any one taxi will do.
- **`allOf`:** `enemiesFollow(?a, ?from, ?l) :- allOf, if(hasAggro(?e, ?a), at(?e, ?from), not(static(?e)), not(hasTag(?e, dead))), do(opAggroMoveTo(?e, ?from, ?l)).`
  Pair it with a method guarded by the negated condition, for when there is none.
- **`try()`:** `do(opA, try(optional), opB)`. Remember that `try` commits (`language.md`).
- **Re-arm recursion:** the strategy repairs its precondition, then calls the task again. The
  repair must make the recursive call take a different method, or it loops.
