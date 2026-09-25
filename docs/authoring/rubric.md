# What good HTN looks like here

This rubric comes from the owner's ratings of 34 rulesets (2026-09-25). Gold: `Examples/Taxi.htn`,
`Examples/Game.htn`, `Examples/TrunkThumper.htn`. Good architecture:
`Examples/CombatLevel1_GreaseTrap.htn`, `Examples/GameHack8AgentAtTop.htn`,
`components/gamehack/`, and the original `components/{primitives,strategies,goals,challenges}`.
Slop: the deleted `components/core/` and `components/abilities/` trees and the levels built
on them (in git history before `6ffa1e9`). The language itself is in
`docs/reference/language.md`.

Each rule has an ID. The reviewer and the linter cite it.

## R1. A strategy states what makes it possible, then does it with generic verbs

The strategy's `if()` lists every property the plan needs: the target, what it is not immune
to, which skills produce which tags, and who the actors are (distinct). Its `do()` is a handful
of generic verbs, parameterized by what `if()` found.

Good (`components/gamehack/strategies/stun_and_slow_skill`):

```prolog
stunAndSlowSkill(?t) :-
    if(enemy(?t), not(immune(?t, stun)),
       skillHasTag(?slowSkill, slow), not(immune(?t, slow)),
       skillAppliesTag(?stunSkill, stun),
       ally(?a1), ally(?a2), \==(?a1, ?a2)),
    do(prepareToUseSkill(?a1, ?stunSkill, ?t),
       prepareToUseSkill(?a2, ?slowSkill, ?t),
       opSynchronize(?a1, ?a2),
       useSkillOnTarget(?a1, ?stunSkill, ?t),
       useSkillOnTarget(?a2, ?slowSkill, ?t)).
```

Slop (the deleted core `the_slipstream`): imperative programming. A chain of one-off helpers,
each very specific, with the feasibility hidden inside them:

```prolog
theSlipstream(?e) :-
    if(role(?e, enemy), not(status(?e, dead)), hazard(?trap, snared), trapSite(?r, ?trap, ?p)),
    do(makeTrap(?r, ?trap, ?p), coverAt(?r), bringTo(?e, ?r), try(gatherIntoTrap(?e, ?r)),
       finishTrap(?e, ?r, ?p)).
```

**Test:** could someone read the `if()` alone and say when this strategy works? Is each
subtask in `do()` a verb that other strategies use too?

## R2. Verbs are reusable, and each verb's methods are the ways to do it

A verb like "get this tag onto that target" has one method per **way** to achieve it. Every
strategy that needs the tag calls the verb.

Good (`components/gamehack/actions/gh_tag_application`): three ways to apply a tag.

```prolog
applyTagNotPresent(?tag, ?t) :- if(ally(?a), skillAppliesTag(?s, ?tag)),
    do(prepareToUseSkill(?a, ?s, ?t), useSkillOnTarget(?a, ?s, ?t)).
applyTagNotPresent(?tag, ?t) :- if(locationCanApplyTag(?l, ?tag)),
    do(bringMobToLocation(?t, ?l), useLocationToApplyTag(?l, ?tag, ?t)).
applyTagNotPresent(?tag, ?t) :- if(hasSkill(?m, ?s), \==(?m, ?t), not(ally(?m)), skillAppliesTag(?s, ?tag)),
    do(bringMobsTogether(?t, ?m), useMobSkillToApplyTag(?m, ?s, ?t)).
```

Good (`gh_skills`): `prepareToUseSkill` has two cases, "already has the skill" and "go learn it
first". Then a sequential strategy is just its needs:
`wetAndElectrocute(?t) :- if(enemy(?t)), do(applyTag(wet, ?t), applyTag(electrocute, ?t)).`

**Slop:** helpers used by exactly one strategy (`makeTrap`, `coverAt`, `gatherIntoTrap`,
`finishTrap`).

## R3. Plain game words, and few of them

The vocabulary is the game's: `ally`, `enemy`, `at`, `linked`, `hasSkill`, `skillAppliesTag`,
`immune`, `hasTag`, `terrain`, `aggro`. A new predicate needs a reason that the existing ones
can't express.

**Slop:** an invented ontology, e.g. `primer`, `vantage`, `holder`, `exposed`, `guarded`,
`open`, `blast/3`, `reacts/3`, `strike/2`, `mark/2`, `signature/2` as a skill kind,
`suspension`, `ward`, `moment`. Each coined term is one more thing the reader and the planner
must learn.

## R4. Top down, not bottom up

Methods are actually "find a way to achieve state 1", "find a way to achieve state 2"...

The wrong way is to state what to do : "scout the Area, deploy trap, hide in ambush..."

## R5. The goal is a menu of strategies

The top task's methods are plain alternatives, one per strategy. `FindAllPlans` returns one
plan per strategy that works. `else` is only for "prefer this, else that".

```prolog
planToDamage(?t) :- if(enemy(?t)), do(stunAndSlowSkill(?t)).
planToDamage(?t) :- if(enemy(?t)), do(wetAndElectrocute(?t)).
```

## R6. Operators are game actions with one clear effect

Operators are named `op...`, change only what that action changes, and are what the game
engine executes. An operator with no state effect is fine if it helps the rendering engine
perform (`opSynchronize(?a1, ?a2)`).

## R7. The right level of abstraction

Plan at the level the game needs decisions at: rooms, not tiles; character tags, not stamina
arithmetic. The engine does low-level pathfinding and timing. TrunkThumper is good, but too
fine-grained for this game (health and stamina bookkeeping).

## R8. Levels are facts; components hold no level specifics

A level file is the world (facts) plus its goal. Reusable components don't name specific
characters, areas or skills. killGoblin() is too specific. Skills themselves are not 
named, instead, they have properties, and when you plan, you use skills with said properties

## R9. Short comments that say what a method is for

`% Case 2: Ally doesn't have skill - go learn it, then go to target.` One line per method or
case, and a header that says what the file is. No essays, no design history in the headers.
