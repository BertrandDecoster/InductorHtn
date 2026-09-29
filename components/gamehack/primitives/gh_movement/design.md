# GH Movement

## Purpose

One-step movement for GameHack domains: an agent goes to any location in one step, and the game engine finds the path. Enemies after the mover (`hasAggro`) follow it. An agent arriving at a tagged location gets its tag (`landLocationTag`, gh_tags).

## Layer

primitive

## Dependencies

- `gamehack/primitives/gh_tags` (landLocationTag)

## Operators

| Operator | Description |
|----------|-------------|
| `opMoveTo(?who, ?from, ?to)` | An agent walks |
| `opAggroMoveTo(?e, ?from, ?to)` | An enemy follows its target (the engine plays a follow) |
| `opStayInLocation(?a)` | Already there: no state change, the plan shows it |

## Methods

| Method | Description |
|--------|-------------|
| `goToLocation(?a, ?l)` | `?a` is at `?l` and has its tag; enemies after `?a` follow |
| `goToSameLocation(?a, ?t)` | `?a` stands where `?t` is |
| `enemiesFollow(?a, ?from, ?to)` | Every non-static, non-dead enemy after `?a` that stood at `?from` moves to `?to` and gets its tag |

## Required Facts

| Fact | Description |
|------|-------------|
| `location(?l)` | An area |
| `at(?x, ?l)` | Where an agent is |
| `hasAggro(?e, ?a)` | Enemy `?e` is after `?a` (optional) |
| `static(?x)` | Never moves (optional) |
| `locationCanApplyTag(?l, ?tag)` | The tag an arriving agent gets (optional) |

## Examples

### Example 1: Direct movement

**Given:** `at(player, room)`
**When:** `goToLocation(player, hut)`
**Then:** the only plan is `opMoveTo(player, room, hut)`; `at(player, hut)`

### Example 2: Already at destination

**Given:** `at(player, room)`
**When:** `goToLocation(player, room)`
**Then:** the only plan is `opStayInLocation(player)`

### Example 3: Go to same location as target

**Given:** `at(player, room)`, `at(gob, hut)`
**When:** `goToSameLocation(player, gob)`
**Then:** the only plan is `opMoveTo(player, room, hut)`

### Example 4: Already at same location as target

**Given:** `at(player, room)`, `at(gob, room)`
**When:** `goToSameLocation(player, gob)`
**Then:** the only plan is `opStayInLocation(player)`

### Example 5: Enemies after the mover follow

**Given:** `at(player, room)`, `at(gob, room)`, `at(tower, room)`, `hasAggro(gob, player)`, `hasAggro(tower, player)`, `static(tower)`
**When:** `goToLocation(player, lake)`
**Then:** the only plan is `opMoveTo(player, room, lake), opAggroMoveTo(gob, room, lake)`

### Example 6: Not a location

**Given:** `at(player, room)`
**When:** `goToLocation(player, nowhere)`
**Then:** no plan

### Example 7: Dead enemies don't follow

**Given:** `at(player, room)`, `at(gob, room)`, `hasAggro(gob, player)`, `hasTag(gob, dead)`
**When:** `goToLocation(player, lake)`
**Then:** the only plan is `opMoveTo(player, room, lake)`

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Single location | An agent is at exactly one location after a move |
| P2 | Idempotent | Moving to the current location changes no state |
