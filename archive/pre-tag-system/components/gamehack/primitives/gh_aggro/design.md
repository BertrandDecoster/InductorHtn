# GH Aggro

## Purpose

Aggro and luring for GameHack domains. An enemy takes a companion as its target (`getAggro`) and follows it; a lurer brings an enemy to a location (`bringEnemyTo`); two agents end up in the same location (`bringAgentsTogether`). The caller chooses the lurer.

## Layer

primitive

## Dependencies

- `gamehack/primitives/gh_movement` (goToLocation, goToSameLocation)

## Operators

| Operator | Description |
|----------|-------------|
| `opAggro(?e, ?a)` | Enemy `?e` is after `?a` |
| `opRemoveAggro(?e, ?a)` | Enemy `?e` is no longer after `?a` |
| `opTargetAlreadyAggroed(?e, ?a)` | Already true: no state change |
| `opEnemyAlreadyAtLocation(?e, ?l)` | Already true: no state change |
| `opAgentsAlreadyTogether(?a1, ?a2)` | Already true: no state change |

## Methods

| Method | Description |
|--------|-------------|
| `getAggro(?e, ?a)` | `?e` is after `?a`: already, instead of another target, or for the first time |
| `bringEnemyTo(?lurer, ?e, ?l)` | The lurer walks to the enemy, takes its aggro, and walks to `?l`; the enemy follows |
| `bringAgentsTogether(?lurer, ?a1, ?a2)` | Two agents share a location; whichever can move is lured to the other |

## Required Facts

| Fact | Description |
|------|-------------|
| `location(?l)`, `at(?x, ?l)` | Where agents are |
| `enemy(?e)` | Only enemies can be lured |
| `hasAggro(?e, ?a)` | Enemy `?e` is after `?a` (optional) |
| `static(?x)` | Never moves (optional) |

## Examples

### Example 1: New aggro

**Given:** `at(gob, hut)`, `at(player, room)`
**When:** `getAggro(gob, player)`
**Then:** the only plan is `opAggro(gob, player)`; `hasAggro(gob, player)`

### Example 2: Swap aggro

**Given:** `hasAggro(gob, companionE)`
**When:** `getAggro(gob, player)`
**Then:** the only plan is `opRemoveAggro(gob, companionE), opAggro(gob, player)`

### Example 3: Already aggroed

**Given:** `hasAggro(gob, player)`
**When:** `getAggro(gob, player)`
**Then:** the only plan is `opTargetAlreadyAggroed(gob, player)`

### Example 4: Bring an enemy to a location

**Given:** `at(gob, hut)`, `at(player, room)`
**When:** `bringEnemyTo(player, gob, lake)`
**Then:** the only plan is `opMoveTo(player, room, hut), opAggro(gob, player), opMoveTo(player, hut, lake), opAggroMoveTo(gob, hut, lake)`; `at(gob, lake)`

### Example 5: Enemy already at the location

**Given:** `at(gob, lake)`
**When:** `bringEnemyTo(player, gob, lake)`
**Then:** the only plan is `opEnemyAlreadyAtLocation(gob, lake)`

### Example 6: A static enemy can't be lured

**Given:** `at(tower, lake)`, `static(tower)`, `at(player, room)`
**When:** `bringEnemyTo(player, tower, hut)`
**Then:** no plan

### Example 7: Agents already together

**Given:** `at(gob, hut)`, `at(teslaTower, hut)`
**When:** `bringAgentsTogether(player, gob, teslaTower)`
**Then:** the only plan is `opAgentsAlreadyTogether(gob, teslaTower)`

### Example 8: Lure to a static agent

**Given:** `at(gob, hut)`, `at(teslaTower, lake)`, `static(teslaTower)`, `at(player, room)`
**When:** `bringAgentsTogether(player, gob, teslaTower)` or `bringAgentsTogether(player, teslaTower, gob)`
**Then:** the only plan lures gob to the lake (as in Example 4)

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Single aggro | An enemy has at most one aggro target at a time |
