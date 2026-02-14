# GH Movement

## Purpose

Direct location-to-location movement for GameHack domains. Unlike the puzzle locomotion component (which uses room connections), GameHack movement allows any entity to move to any location directly. Supports static entity checks and "go to same location as target" pattern.

## Layer

primitive

## Dependencies

None (foundational component)

## Operators

| Operator | Description |
|----------|-------------|
| `opMoveTo(?a, ?from, ?to)` | Move entity from one location to another |
| `opAggroMoveTo(?a, ?from, ?to)` | Move entity due to aggro (same effect, distinct operator) |
| `opStayInLocation(?a)` | No-op when entity is already at destination |

## Methods

| Method | Description |
|--------|-------------|
| `goToLocation(?a, ?l)` | Move entity to location. No-op if already there. |
| `goToSameLocation(?a, ?t)` | Move entity to target's location. Fails if entity is static. |

## Required Facts

| Fact | Description |
|------|-------------|
| `at(?entity, ?location)` | Current location of an entity |
| `static(?entity)` | Entity cannot move (optional) |

## Examples

### Example 1: Direct movement

**Given:**
- `at(player, room)`

**When:**
- `goToLocation(player, hut)`

**Then:**
- Plan contains: `opMoveTo(player, room, hut)`
- Final state has: `at(player, hut)`
- Final state does not have: `at(player, room)`

### Example 2: Already at destination

**Given:**
- `at(player, room)`

**When:**
- `goToLocation(player, room)`

**Then:**
- Plan contains: `opStayInLocation(player)`
- No `opMoveTo` in plan

### Example 3: Go to same location as target

**Given:**
- `at(player, room)`, `at(gob, hut)`

**When:**
- `goToSameLocation(player, gob)`

**Then:**
- Plan contains: `opMoveTo(player, room, hut)`
- Final state has: `at(player, hut)`

### Example 4: Already at same location

**Given:**
- `at(player, room)`, `at(gob, room)`

**When:**
- `goToSameLocation(player, gob)`

**Then:**
- Plan contains: `opStayInLocation(player)`
- No `opMoveTo` in plan

### Example 5: Static entity cannot move

**Given:**
- `at(tower, lake)`, `at(gob, hut)`, `static(tower)`

**When:**
- `goToSameLocation(tower, gob)`

**Then:**
- Planning fails (no valid plan)

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Single location | An entity is at exactly one location after movement |
| P2 | Idempotent | Moving to current location produces no state change (beyond opStayInLocation) |
