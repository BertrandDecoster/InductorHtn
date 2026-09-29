# What good HTN looks like here

This rubric comes from the owner's ratings of 34 rulesets (2026-09-25). Gold: `Examples/Taxi.htn`,
`Examples/Game.htn`, `Examples/TrunkThumper.htn`, and `Examples/Combos.htn` (the reference game
ruleset). Good architecture (4★): `Examples/CombatLevel1_GreaseTrap.htn`,
`Examples/GameHack8AgentAtTop.htn` and the original `components/{primitives,strategies,goals}`;
`components/gamehack/` was rated 3★. All of them were rewritten in the words of
`vocabulary.md` on 2026-09-25 (the originals are in `archive/pre-vocabulary/`).
Slop: the deleted `components/core/` and `components/abilities/` trees and the levels built
on them (in git history before `6ffa1e9`). The language itself is in
`docs/reference/language.md`.

Each rule has an ID. The reviewer and the linter cite it.

## R1. A strategy states what makes it possible, then does it with generic verbs

The strategy's `if()` lists every property the plan needs: the target, what it is not immune
to, which skills produce which tags, and who the actors are (distinct). Its `do()` is a handful
of generic verbs, parameterized by what `if()` found.

Good (`Examples/Combos.htn`):

```prolog
stunAndSlow(?t) :-
    if(enemy(?t), not(immune(?t, stunned)),
       skillAppliesTag(?stun, stunned), skillHasTag(?slow, slow),
       companion(?a1), companion(?a2), \==(?a1, ?a2)),
    do(prepareToUseSkill(?a1, ?stun, ?t), prepareToUseSkill(?a2, ?slow, ?t),
       opSynchronize(?a1, ?a2),
       useSkillOnTarget(?a1, ?stun, ?t), useSkillOnTarget(?a2, ?slow, ?t)).
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

Good (`Examples/Combos.htn`): `prepareToUseSkill` has two cases, "already has the skill" and
"get it from an object first"; every strategy that uses a skill calls it.

```prolog
prepareToUseSkill(?a, ?s, ?t) :- if(hasSkill(?a, ?s)), do(goToSameLocation(?a, ?t)).
prepareToUseSkill(?a, ?s, ?t) :- if(companion(?a), not(hasSkill(?a, ?s)), object(?o), canGetSkillFrom(?o, ?s)),
    do(goToSameLocation(?a, ?o), getSkillFrom(?a, ?o, ?s), goToSameLocation(?a, ?t)).
```

Then a strategy is just its roles and its states: in `oilAndBurn(?t)`, `?t` has oil by a
lurer's doing (`applyTag(?lurer, oil, ?t)`, a lure onto the oil), then burning by a second
companion's (`applyTag(?caster, burning, ?t)`, a skill; `applyTag` calls `prepareToUseSkill`,
`useSkillOnTarget`).

**Slop:** helpers used by exactly one strategy (`makeTrap`, `coverAt`, `gatherIntoTrap`,
`finishTrap`).

## R3. Plain game words, and few of them

The vocabulary is the game's, one word per concept (`vocabulary.md`): `companion`, `enemy`,
`at`, `reachable`, `hasSkill`, `skillAppliesTag`, `immune`, `hasTag`, `locationCanApplyTag`,
`hasAggro`. A new predicate needs a reason that the existing ones can't express, and the
owner's agreement.

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
defeat(?t) :- if(enemy(?t), not(hasTag(?t, dead))), do(wetAndFreeze(?t)).
defeat(?t) :- if(enemy(?t), not(hasTag(?t, dead))), do(oilAndBurn(?t)).
```

## R6. Operators are game actions with one clear effect

Operators are named `op...`, change only what that action changes, and are what the game
engine executes. An operator with no state effect is fine if it helps the rendering engine
perform (`opSynchronize(?a1, ?a2)`), and so is the no-op operator a verb does when its state is
already true (`opStayInLocation`, `opTagAlreadyOnTarget`: the table in `vocabulary.md`).

## R7. The right level of abstraction

Plan at the level the game needs decisions at: rooms, not tiles; character tags, not stamina
arithmetic. The engine does low-level pathfinding and timing. TrunkThumper is good, but too
fine-grained for this game (health and stamina bookkeeping).

## R8. Levels are facts; components hold no level specifics

A level file is the world (facts) plus its goal. Reusable components don't name specific
characters, areas or skills. killGoblin() is too specific. Skills themselves are not 
named, instead, they have properties, and when you plan, you use skills with said properties

## R9. Short comments that say what a method is for

`% Case 2: the companion doesn't have the skill - get it from an object, then go to the target.` One line per method or
case, and a header that says what the file is. No essays, no design history in the headers.
