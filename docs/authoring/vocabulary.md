# The game's vocabulary

One word per concept, so every ruleset speaks the same language, and a new predicate stands
out as a design decision rather than a habit. The words come from the owner's 4-5★ files
(mostly GameHack) and from `docs/game-design/GDD.md`; the owner settled the open choices on
2026-09-25.

A component or level that needs a concept not listed here should ask first. Don't coin a
synonym. Concepts not needed yet (charges, tag combinations, neutral NPCs) will be added here
when a level needs them.

## Characters

| Fact | Meaning | Don't write |
|---|---|---|
| `ally(?a)` | the player's hero and the companions; interchangeable in ability (GDD §2, §3.3) | `agent`, `companion`, `role(?a, player)` |
| `enemy(?e)` | a hostile NPC | `isEnemy` |
| `static(?x)` | never moves; can't be lured (a tower, a statue) | `immobile`, `heavy` |

Actors in a strategy are distinct: `ally(?a1), ally(?a2), \==(?a1, ?a2)`. The GDD roles
(primer, catalyst, detonator) are **not facts**. A role is a variable bound in a strategy's
`if()`, and different roles are different allies.

## Places and movement

| Fact | Meaning | Don't write |
|---|---|---|
| `location(?l)` | an area the planner reasons about: a room, not a tile (rubric R7) | `room`, `corridor`, `zone` |
| `at(?who, ?l)` | where a character is | `npcAt`, `objectAt`, `position` |
| `reachable(?from, ?to, ?means)` | provided by the game engine: `?to` can be reached from `?from` by `walk`, `walkDash`, `walkTeleport` or `walkDashTeleport` | `linked`, `connected`, `pathThrough` |

**The HTN never reasons about adjacency or paths.** A character goes to any location in one
step (`goToLocation`), and the engine finds the path. The only question the planner asks is
whether a location is reachable, and by what means, when a strategy depends on it (for
example, it needs a dash).

The name `reachable/3` and the names of the means are this page's proposal; adjust them to the
engine's actual output.

## Skills

| Fact | Meaning | Don't write |
|---|---|---|
| `hasSkill(?who, ?s)` | a character (ally or enemy) holds a skill | `knows`, `signature` |
| `skillAppliesTag(?s, ?tag)` | using the skill puts that tag on the target | `canApplyTag` (a rule, not a fact), `effect/3` |
| `skillHasTag(?s, ?property)` | a property of the skill itself (fireball has `slow`) | `skillElement`, `skillKind` |
| `canGetSkillAtLocation(?l, ?s)` | an ally can learn the skill there (it replaces their current one) | |

Skills are never named in rules (rubric R8). A strategy asks for "a skill that applies stun",
not for `iceBlast`.

## Tags: status of characters and places

| Fact | Meaning | Don't write |
|---|---|---|
| `hasTag(?who, ?tag)` | a character's current status: `wet`, `stun`, `slow`, `fire`, `electrocute`, `frozen`, ... | `condition`, `hasEffect`, `status` |
| `hasTag(?e, dead)` | the enemy is out of the fight | `defeated`, `health(?e, dead)`, `damaged` |
| `hasTag(?e, ?state)` | an enemy behaviour state the FSM exposes: `hasTag(ogre, exhausted)` after a rampage (GDD §4.3) | `fsmState`, `behavior/4` |
| `immune(?who, ?tag)` | the tag can never be put on it | `vulnerableTo`, `vulnerability`, `resists` |
| `locationCanApplyTag(?l, ?tag)` | standing there gives the tag: a lake gives `wet`, an oil slick gives `oily` | `terrain`, `roomHasHazard`, `hazardAppliesTag` |

**Areas that change during a fight change their location tags.** An operator removes or adds
`locationCanApplyTag` facts: burning the oil slick deletes `locationCanApplyTag(l, oily)` and
adds `locationCanApplyTag(l, fire)`.

## Threat

| Fact | Meaning | Don't write |
|---|---|---|
| `aggro(?e, ?target)` | the enemy is after that character and follows it | `hasAggro`, `taunted`, `lured` |

## Shared verbs (methods) and operators

Reuse these before writing new ones. They are in `components/gamehack/` and
`Examples/Combos.htn` (the clean reference).

| Verb | What it achieves |
|---|---|
| `applyTag(?tag, ?t)` | `?t` has the tag, by any way that works (patterns P4, P5) |
| `prepareToUseSkill(?a, ?s, ?t)` | `?a` holds `?s` and stands with `?t` |
| `useSkillOnTarget(?a, ?s, ?t)` | the skill's tags are on `?t` |
| `goToLocation(?a, ?l)` | `?a` is at `?l`; enemies after `?a` follow |
| `goToSameLocation(?a, ?t)` | `?a` stands with `?t` |
| `bringMobToLocation(?t, ?l)` | an enemy is lured to `?l` |
| `bringMobsTogether(?m1, ?m2)` | two characters share a location |

| Operator | Effect |
|---|---|
| `opMoveTo(?who, ?from, ?to)` | moves |
| `opUseSkill(?who, ?s, ?t)` | no state change; the engine plays the skill (its tags follow as `opApplyTag`) |
| `opApplyTag(?tag, ?t)` | adds `hasTag` |
| `opAggro(?e, ?a)`, `opRemoveAggro(?e, ?a)` | sets or clears `aggro` |
| `opGetSkill(?a, ?s)`, `opSwapSkill(?a, ?old, ?s)` | learns a skill |
| `opSynchronize(?a1, ?a2)` | no state change; tells the engine two allies act together |

The older component trees (`components/primitives`, `strategies`, `goals`, `challenges`) and
`Examples/CombatLevel1_GreaseTrap.htn` predate this page and use synonyms (`connected`,
`hasAggro`, `terrain`, `health`, `condition`). Don't copy their vocabulary.
