# The game's vocabulary

One word per concept, so every ruleset speaks the same language, and a new predicate stands
out as a design decision rather than a habit. The owner picked each word on 2026-09-25, from
the words the rated rulesets used (the originals are in `archive/pre-vocabulary/`).

A component or level that needs a concept not listed here should ask first. Don't coin a
synonym.

## Agents

An **agent** is any character. Every agent is exactly one of `companion`, `neutral` or
`enemy`.

| Fact | Meaning | Don't write |
|---|---|---|
| `companion(?c)` | the player's hero or a bot; all have the same abilities, they differ only by who controls them | `ally`, `agent(?c)` as a fact, `role(?c, player)`, `player` in a rule |
| `enemy(?e)` | a hostile agent | `isEnemy` |
| `neutral(?n)` | an agent on neither side | `npc` |
| `agent(?x)` | any agent: a rule, `agent(?x) :- companion(?x).` and the same for `neutral` and `enemy` | `mob`, `entity`, `actor`, `unit`, `character` |
| `object(?o)` | a thing that isn't an agent (it can grant a skill) | `item` |
| `static(?x)` | never moves; can't be lured or pushed | `immobile`, `heavy` |
| `canFillHole(?o)` | object `?o`, pushed into a hole, fills it, and the link opens | |

A level may name the controlled companion `player` (the fun metrics read that name), but a
rule never names it. Actors in a strategy are distinct: `companion(?a1), companion(?a2),
\==(?a1, ?a2)`. Roles (lurer, primer, detonator) are variables bound in a strategy's `if()`,
never facts.

## Places and movement

| Fact | Meaning | Don't write |
|---|---|---|
| `location(?l)` | an area the planner reasons about: a room, not a tile (rubric R7) | `room`, `corridor`, `zone` |
| `at(?x, ?l)` | where an agent or an object is | `npcAt`, `objectAt`, `switchAt`, `position` |
| `linked(?a, ?b)` | the map: `?a` and `?b` are adjacent (list both directions). Static | `connected`, `pathThrough` |
| `blockedLink(?a, ?b, ?blocker)` | the link is not normal: `?blocker` is `wall`, `hole` or `door(?d)`. A door's `locked(?d)` is what changes; a filled hole's `blockedLink` is removed (both directions) | `blocked`, `gateBlocking`, `blockedConnection` |
| `reachable(?from, ?to, ?means)` | provided by the game engine: how `?to` can be reached from `?from`. `?means` is `all` (walkable, so dash and teleport work too), `dash`, `teleport` or `dashTeleport` (either, but not walking) | |
| `moveCost(?from, ?to, ?cost)` | the cost of moving (not used by any ruleset yet) | `effort`, `moveEffort` |

**Where nothing blocks the way, the HTN doesn't walk paths.** An agent goes to any location in one step (`goToLocation`),
and the engine finds the path (it will account for `blockedLink`; not yet). `linked` and
`blockedLink` describe the map for strategies that need adjacency (a slide into the next
location); a strategy that depends on how a location is reached asks `reachable` in its
`if()`. A puzzle about getting past blockers walks the engine's path link by link
(`reachLocation`, `crossLink`: `Examples/CrissCross.htn`), with one method for each way past a
blocker. A hole can be dashed over, teleported over, or filled; a door opens while its plate is held.

## Skills

| Fact | Meaning | Don't write |
|---|---|---|
| `hasSkill(?who, ?s)` | an agent holds a skill | `knows`, `skill(wet)` |
| `skillAppliesTag(?s, ?tag)` | using the skill puts that tag on the target | `canApplyTag` (spell out `hasSkill` + `skillAppliesTag` in each `if()`), `skillApplyEffect` |
| `skillHasTag(?s, ?property)` | a property of the skill itself (`fireballSkill` is `slow`) | `skillKind` |
| `canGetSkillFrom(?o, ?s)` | object `?o` grants the skill to a companion who reaches it; it stays for the next one | `canGetSkillAtLocation` |
| `hasMana(?a, ?m)`, `manaCost(?s, ?cost)` | a skill's resource cost (not used by any ruleset yet) | `effort` |

Skill constants end in `Skill`: `iceBlastSkill`, `fireballSkill`. Skills are never named in
rules (rubric R8): a strategy asks for "a skill that applies `stunned`".

## Tags: status of agents and places

| Fact | Meaning | Don't write |
|---|---|---|
| `hasTag(?who, ?tag)` | an agent's current status | `condition`, `hasEffect`, `status` |
| `hasTag(?e, dead)` | the enemy is out of the fight | `health`, `damaged`, `cleared`, `defeated` |
| `immune(?who, ?tag)` | the tag can never be put on it | `resists` |
| `locationCanApplyTag(?l, ?tag)` | the location's one tag, which it gives to whoever arrives there: `wet`, `oil`, `burning` or `ice` | `terrain`, `roomHasHazard`, `locationProperty` |
| `locationCombo(?locationTag, ?skillTag)` | the physics: a skill's tag combines with the location tag its target has | `tagCombines` |
| `vulnerableToLocationCombo(?e, ?locationTag, ?skillTag)` | that combo defeats the enemy (the skill alone never does) | `vulnerableTo`, `weakTo` |

**Location tags land on agents.** An agent that arrives at a tagged location gets its tag
(`goToLocation`, and the enemies that follow), and so does everyone standing at a location when it
gains a tag (the oil catching fire). An agent keeps its tags when it leaves. A world that starts
an agent on a tagged location states its tag too: `at(gob, lake). hasTag(gob, wet).`
`wet`, `oil` and `ice` come only from locations; no skill applies them.

**The tags and what they do in the HTN:**

| Tag | Where it comes from | Effect in the HTN |
|---|---|---|
| `wet` | a wet location | none (half of a combo) |
| `oil` | an oil location | slowed |
| `ice` | an ice location | slowed |
| `burning` | a burning location, a skill | none (damage over time) |
| `electrified` | a skill | interrupted: loses its current action |
| `chilled` | a skill | none alone (half of a combo) |
| `stunned` | a combo, or a skill | can't act |
| `dead` | a location combo on a vulnerable enemy | out of the fight |

Not `oily`, `frozen`, `fire`, `electrocute`, `stun`, `interrupted`.

**The three location combos** (a skill's tag lands on a target that has a location's tag):

| Target's tag + skill tag | Result |
|---|---|
| `wet` + `electrified` | in water, everyone there is `electrified` and the location stays wet; elsewhere, the target alone |
| `oil` + `burning` | on the oil, everyone there is `burning` and the oil becomes `burning` (the only location tag that changes); elsewhere, the target alone |
| `wet` or `ice` + `chilled` | the target alone is `stunned` |

Each combo defeats the enemies there that are `vulnerableToLocationCombo` it. There are no other
combinations, no chains and no counters.

## Threat

| Fact | Meaning | Don't write |
|---|---|---|
| `hasAggro(?e, ?target)` | enemy `?e` is after `?target` and follows it | `aggro`, `taunted`, `lured` |

## Doors

| Fact | Meaning | Don't write |
|---|---|---|
| `locked(?d)` | the door is locked; what it guards is `blockedLink(?a, ?b, door(?d))` | `gateBlocking`, `gate` |
| `plateOpens(?p, ?d)` | standing on plate `?p` helps open door `?d` | `switchControls` |
| `onPlate(?x, ?p)` | a companion or an object holds plate `?p` down; a held plate's door stays unlocked, and it locks again when the plate is left | |

## Verbs (methods) and operators

Reuse these before writing new ones. Their reference implementation is `Examples/Combos.htn`
(and `components/gamehack/`).

| Verb | What it achieves |
|---|---|
| `defeat(?t)` | goal: enemy `?t` has `dead` |
| `clearLocation(?l)` | goal: every enemy at `?l` has `dead` |
| `applyTag(?a, ?tag, ?t)` | `?t` has the tag, by `?a`'s doing: already, `?a` uses a skill that applies it, or `?a` lures `?t` onto a location that gives it. The combo strategies are two of these, one per companion |
| `landSkillTag(?tag, ?t)` | a skill's tag lands on `?t`, with the combo of the location tag `?t` has |
| `landTag(?tag, ?t)` | `?t` has the tag, unless it is immune |
| `landLocationTag(?x, ?l)` | `?x`, arriving at `?l`, gets its tag, if it has one |
| `tagEveryoneAt(?tag, ?l)` | every agent at `?l` has the tag |
| `defeatVulnerable(?e, ?locationTag, ?skillTag)`, `defeatVulnerableAt(?locationTag, ?skillTag, ?l)` | the enemies vulnerable to that combo (`?e`, or everyone at `?l`) are `dead` |
| `prepareToUseSkill(?a, ?s, ?t)` | `?a` holds `?s` and stands with `?t` |
| `getSkillFrom(?a, ?o, ?s)` | `?a` learns `?s` from object `?o` (it replaces their skill, if any) |
| `useSkillOnTarget(?a, ?s, ?t)` | the skill is used; its tags land on `?t` |
| `applySkillTags(?s, ?t)` | each of the skill's tags lands on `?t` (`landSkillTag`) |
| `goToLocation(?a, ?l)` | `?a` is at `?l` and has its tag; enemies after `?a` follow |
| `goToSameLocation(?a, ?t)` | `?a` stands with `?t` |
| `forceMove(?a, ?x, ?l)` | `?a` pushes `?x` into the next location `?l` and follows it; pushed into a hole, a `canFillHole` object fills it |
| `reachLocation(?a, ?l)` | `?a` is at `?l`: it steps off its plate and follows the engine's path, getting past each link's blocker |
| `crossLink(?a, ?from, ?to)` | `?a` gets past one link: walk, a door held open, dash or teleport over a hole, or fill the hole first |
| `pressPlate(?a, ?p)` | `?p`'s door unlocks while the plate is held: `?a` stands on it, or pushes an object onto it |
| `leavePlate(?a)` | `?a` steps off its plate; the door locks unless another of its plates is held |
| `everyoneReaches(?l)` | goal: every companion is at `?l` |
| `getAggro(?e, ?a)`, `loseAggro(?e, ?a)` | `?e` is after `?a`, or no longer (no ruleset uses `loseAggro` now) |
| `enemiesFollow(?a, ?from, ?to)` | the enemies after `?a` move with it |
| `bringEnemyTo(?lurer, ?e, ?l)` | `?lurer` lures enemy `?e` to `?l`; the caller's `if()` chooses the lurer |
| `unlockDoor(?d)` | `?d` is not locked |

| Operator | Effect |
|---|---|
| `opMoveTo(?who, ?from, ?to)` | an agent walks |
| `opAggroMoveTo(?e, ?from, ?to)` | an enemy follows its target (the engine plays a follow, not a walk) |
| `opDashTo(?who, ?from, ?to)`, `opTeleportTo(?who, ?from, ?to)` | an agent dashes or teleports over a hole |
| `opForceMove(?a, ?x, ?from, ?to)` | `?a` pushes an agent or object, and follows it |
| `opFillHole(?a, ?x, ?from, ?to)` | `?x` falls into the hole between `?from` and `?to`: the object is gone, and the link is open |
| `opPressPlate(?a, ?p)`, `opPushOntoPlate(?a, ?o, ?p)`, `opLeavePlate(?a, ?p)` | a plate is held by `?a`, or by an object `?a` pushes onto it, or left |
| `opUseSkill(?a, ?s, ?t)` | no state change; the engine plays the skill (its tags follow as `opApplyTag`) |
| `opApplyTag(?tag, ?t)` | adds `hasTag` |
| `opAddLocationTag(?tag, ?l)`, `opRemoveLocationTag(?tag, ?l)` | adds or removes `locationCanApplyTag` |
| `opAggro(?e, ?a)`, `opRemoveAggro(?e, ?a)` | sets or clears `hasAggro` |
| `opGetSkill(?a, ?s)`, `opSwapSkill(?a, ?old, ?s)` | learns a skill |
| `opSetMana(?a, ?old, ?new)` | spends mana |
| `opSynchronize(?a1, ?a2)` | no state change; two companions act together |
| `opSynchronizeOnPlates(?a1, ?a2, ?p1, ?p2)` | no state change; two companions stand on two plates together |
| `opUnlock(?d)`, `opLock(?d)` | removes or adds `locked` |

**Already true: a no-op operator named after the state.** When a verb finds its state already
true, its first method does one no-op operator, so the plan shows it:

| Verb | No-op operator |
|---|---|
| `goToLocation` | `opStayInLocation(?a)` |
| `landTag`, `applyTag` | `opTagAlreadyOnTarget(?tag, ?t)` |
| `getAggro` | `opTargetAlreadyAggroed(?e, ?a)` |
| `bringEnemyTo` | `opEnemyAlreadyAtLocation(?e, ?l)` |
| `unlockDoor` | `opDoorAlreadyUnlocked(?d)` |

A fallback that has nothing to do (no follower, no tag left to add) is not an "already true"
state: it keeps an empty `do()`, guarded by the negated condition.

**Strategies** need distinct companions working together: bind the roles (lurer, caster) in
`if()` with `\==`, and give each its state: `do(applyTag(?lurer, oil, ?t), applyTag(?caster,
burning, ?t))`. A plan one companion can manage is too simple. The current ones: `wetAndFreeze`,
`oilAndBurn`, `stunAndSlow`. An enemy that already has its combo's location tag needs only the
caster: keep enemies off their combos in a level that must need two companions.
