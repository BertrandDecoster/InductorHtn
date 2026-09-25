# GH Aggro

## Purpose

Aggro and mob manipulation system for GameHack domains. Handles targeting enemies onto allies via aggro, luring mobs to specific locations through aggro chains, and bringing two mobs together. Used by the tag application layer to position enemies for location-based or mob-based tag effects.

## Layer

primitive

## Dependencies

- `gamehack/primitives/gh_movement` (goToLocation, opAggroMoveTo)

## Operators

| Operator | Description |
|----------|-------------|
| `opAggro(?t, ?a)` | Set target's aggro to ally |
| `opRemoveAggro(?t, ?a)` | Remove target's aggro on ally |
| `opTargetAlreadyAggroed()` | No-op when target already aggroed |

## Methods

| Method | Description |
|--------|-------------|
| `aggroTarget(?t, ?a)` | Set target's aggro to ally. Handles swap, new, or already-aggroed. |
| `bringMobToLocation(?t, ?l)` | Lure mob to location via aggro chain: ally goes to mob, aggros, moves to destination |
| `bringMobsTogether(?m1, ?m2)` | Bring two mobs to same location. Moves non-static mob to the other. |

## Required Facts

| Fact | Description |
|------|-------------|
| `at(?entity, ?location)` | Current location of an entity |
| `aggro(?target, ?ally)` | Target is aggro'd onto ally (optional) |
| `ally(?entity)` | Entity is an ally (can aggro enemies) |
| `static(?entity)` | Entity cannot move (optional) |

## Examples

### Example 1: New aggro (no prior)

**Given:**
- `at(gob, hut)`, `at(player, room)`
- `ally(player)`

**When:**
- `aggroTarget(gob, player)`

**Then:**
- Plan contains: `opAggro(gob, player)`
- Final state has: `aggro(gob, player)`

### Example 2: Swap aggro

**Given:**
- `aggro(gob, companionE)`
- `ally(player)`

**When:**
- `aggroTarget(gob, player)`

**Then:**
- Plan contains: `opRemoveAggro(gob, companionE)`, `opAggro(gob, player)`

### Example 3: Already aggroed

**Given:**
- `aggro(gob, player)`

**When:**
- `aggroTarget(gob, player)`

**Then:**
- Plan contains: `opTargetAlreadyAggroed()`

### Example 4: Bring mob to location

**Given:**
- `at(gob, hut)`, `at(player, room)`, `ally(player)`

**When:**
- `bringMobToLocation(gob, lake)`

**Then:**
- Plan contains: `goToLocation`, `aggroTarget`, `opAggroMoveTo`
- Final state has: `at(gob, lake)`

### Example 5: Bring mob already at location

**Given:**
- `at(gob, lake)`

**When:**
- `bringMobToLocation(gob, lake)`

**Then:**
- Plan is empty (no operators)

### Example 6: Static mob cannot be moved

**Given:**
- `at(tower, lake)`, `static(tower)`, `at(player, room)`, `ally(player)`

**When:**
- `bringMobToLocation(tower, hut)`

**Then:**
- Planning fails

### Example 7: Bring mobs together (already together)

**Given:**
- `at(gob, hut)`, `at(teslaTower, hut)`

**When:**
- `bringMobsTogether(gob, teslaTower)`

**Then:**
- Plan is empty (no operators)

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Single aggro | A mob has at most one aggro target at a time |
