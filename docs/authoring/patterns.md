# HTN patterns, with where to see them

Retrieve examples by **pattern**, not by subject. First decide which patterns the task needs,
then read the lines listed for them. "Replenish ammo" looks like "replenish health" but is
built like "acquire a skill" (P4). Every example below was rated 4-5★ by the owner (see
`rubric.md`). Line numbers are for the current files.

| # | Pattern | Use when | Read |
|---|---|---|---|
| P1 | Strategy menu | a need can be met several distinct ways | **Combos 7-9**, Taxi 9-12, TrunkThumper 245-300 |
| P2 | Feasibility in `if()`, generic verbs in `do()` | writing any strategy | **Combos 21-27** (`stunAndSlow`), GreaseTrap 239-267 |
| P3 | A strategy is the states to achieve | a combo is "get A, then get B" | **Combos 16-18, 30-32** (`wetAndElectrocute`, `oilAndFire`) |
| P4 | A verb whose methods are the ways | several ways to reach one state | **Combos 43-51** (`applyTagNotPresent`), 53-55 (`prepareToUseSkill`), 88-90 (`bringMobsTogether`) |
| P5 | Already-done case first | a verb may find its state already true | **Combos 39-40** (`applyTag`), 73-74 (`goToLocation`) |
| P6 | Movement | going somewhere | game rulesets: one step, **Combos 73-78** (the engine pathfinds, `vocabulary.md`); other domains: `pathNext` recursion, TrunkThumper 233-242 |
| P7 | Lure: aggro, then walk, and it follows | moving an enemy that won't go by itself | **Combos 81-85**, 77-78 (`enemiesFollow`) |
| P8 | Distinct actors, synchronized | two companions must act together | **Combos 21-27** (`\==(?a1, ?a2)`, `opSynchronize`) |
| P9 | Variant selection with an `else` ladder | pick one version of an action, by priority | TrunkThumper 280-286, Game 62-70 |
| P10 | One binding with `first()` | any one of several is enough | Taxi 11 (hail one taxi) |
| P11 | Every binding with `allOf` | do it to each one that qualifies | **Combos 64-67** (a skill's tags), 77-78 (every follower) |
| P12 | Optional consequence with `try()` | a side effect that happens when it can | GreaseTrap 162-168 (burning also burns the oil) |
| P13 | Recursion that re-arms | a strategy that repairs its own precondition | TrunkThumper 296-300 |

`Examples/Combos.htn` is the reference for game rulesets: it uses the vocabulary of `vocabulary.md`.
Paths: `Examples/Combos.htn`, `Examples/Taxi.htn`, `Examples/TrunkThumper.htn`,
`Examples/CombatLevel1_GreaseTrap.htn`, `Examples/Game.htn`. The same ideas as reusable
components: `components/gamehack/` (P2-P8) and `components/primitives/tags` (P5).

## P1. Strategy menu

The need is a task. Each strategy is one plain method (no `else`), so `FindAllPlans` returns one
plan per strategy that works.

```prolog
planToDamage(?t) :- if(enemy(?t)), do(stunAndSlowSkill(?t)).
planToDamage(?t) :- if(enemy(?t)), do(wetAndElectrocute(?t)).
```

## P2. Feasibility in `if()`, generic verbs in `do()`

`if()` binds the target, the skills **by property**, and the actors, and rules out what can't
work (immunity, the same actor twice). `do()` only uses verbs that other strategies share.
See rubric R1.

## P3. A strategy is the states to achieve

```prolog
wetAndElectrocute(?t) :- if(enemy(?t)), do(applyTag(wet, ?t), applyTag(electrocute, ?t)).
```

Each subtask says **what must become true**. How is the verb's job (P4). Not "walk to X, cast
Y, wait".

## P4. A verb whose methods are the ways

```prolog
applyTagNotPresent(?tag, ?t) :- if(ally(?a), skillAppliesTag(?s, ?tag)),
    do(prepareToUseSkill(?a, ?s, ?t), useSkillOnTarget(?a, ?s, ?t)).
applyTagNotPresent(?tag, ?t) :- if(locationCanApplyTag(?l, ?tag)),
    do(bringMobToLocation(?t, ?l), useLocationToApplyTag(?l, ?tag, ?t)).
applyTagNotPresent(?tag, ?t) :- if(hasSkill(?m, ?s), \==(?m, ?t), not(ally(?m)), skillAppliesTag(?s, ?tag)),
    do(bringMobsTogether(?t, ?m), useMobSkillToApplyTag(?m, ?s, ?t)).
```

A new way to get a tag is one more method here, and every strategy benefits.

## P5. Already-done case first

```prolog
applyTag(?tag, ?t) :- if(hasTag(?t, ?tag)), do().
applyTag(?tag, ?t) :- if(not(hasTag(?t, ?tag))), do(applyTagNotPresent(?tag, ?t)).
```

The two conditions exclude each other, so there is no `else` to fall through (see
`language.md`, "else is not a cut").

## P6. Navigation by `pathNext` recursion

```prolog
navigateTo(?who, ?dest) :- if(at(?who, ?dest)), do().
navigateTo(?who, ?dest) :- else, if(at(?who, ?cur), pathNext(?cur, ?dest, ?next)),
    do(opMoveTo(?who, ?cur, ?next), navigateTo(?who, ?dest)).
```

Works for any distance. No 1-, 2- and 3-hop method ladders. If the game engine does the
pathfinding and areas aren't linked, move in one step (GameHack8 `goToLocation`).

## P7. Lure

```prolog
bringEnemyTo(?lurer, ?enemy, ?destination) :-
    if(ally(?lurer), at(?enemy, ?enemyLoc)),
    do(navigateTo(?lurer, ?enemyLoc), opGetAggro(?lurer, ?enemy),
       navigateTo(?lurer, ?destination), opAggroFollow(?enemy, ?enemyLoc, ?destination)).
```

## P8. Distinct actors, synchronized

`ally(?a1), ally(?a2), \==(?a1, ?a2)` in `if()`. Both prepare independently, then
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
- **`allOf`:** `triggerBurnEnemies(?loc) :- allOf, if(at(?e, ?loc), enemy(?e), health(?e, healthy)), do(opInstakill(?e)).`
- **`try()`:** `do(opApplyCondition(?loc, burning), try(triggerBurnOil(?loc)), try(triggerBurnEnemies(?loc)))`.
  Remember that `try` commits (`language.md`).
- **Re-arm recursion:** the strategy repairs its precondition, then calls the task again. The
  repair must make the recursive call take a different method, or it loops.
