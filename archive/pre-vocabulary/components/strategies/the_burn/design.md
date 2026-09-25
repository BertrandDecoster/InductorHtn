# The Burn

## Purpose

A tactical strategy that defeats enemies by luring them to a room with oil hazard, then igniting it. The oil burns up after use, applying the burning tag to any enemies present.

From PUZZLE_IDEAS.md Level 1, Plan B: "Explosive Shortcut"

## Layer

strategy

## Dependencies

- `primitives/locomotion` - For player and enemy movement
- `primitives/tags` - For applying burning effect
- `primitives/aggro` - For luring enemies

## Methods

| Method | Description |
|--------|-------------|
| `theBurn(?enemy)` | Main strategy: lure enemy to oil room, ignite |
| `igniteRoom(?room)` | Ignite oil in room, apply burning to entities |
| `consumeHazard(?room, ?hazard)` | Remove hazard after use |

## Operators

| Operator | Description |
|----------|-------------|
| `opConsumeHazard(?room, ?hazard)` | Remove hazard from room |

## Required Facts

| Fact | Description |
|------|-------------|
| `roomHasHazard(?room, ?hazard)` | Room contains a hazard (oil, water, etc.) |
| `canApplyTag(?entity, ?tag)` | Entity has ability to apply this tag |
| `at(?entity, ?room)` | Entity location |

## Parameters

No configurable parameters.

## Examples

### Example 1: Basic burn strategy

**Given:**
- `at(player, roomA)`
- `at(enemy1, roomA)`
- `roomHasHazard(roomB, oil)`
- `canApplyTag(player, burning)`
- `connected(roomA, roomB)`

**When:**
- `theBurn(enemy1)`

**Then:**
- Plan contains: player moves, enemy lured, burning applied
- Final state has: `hasTag(enemy1, burning)`
- Final state has: `hazardConsumed(roomB, oil)`
- Final state does not have: `roomHasHazard(roomB, oil)`

### Example 2: Enemy already in oil room

**Given:**
- `at(player, roomA)`
- `at(enemy1, roomB)`
- `roomHasHazard(roomB, oil)`
- `canApplyTag(player, burning)`
- `connected(roomA, roomB)`

**When:**
- `theBurn(enemy1)`

**Then:**
- Plan contains: player moves to roomB, ignites
- Final state has: `hasTag(enemy1, burning)`

### Example 3: No oil room available

**Given:**
- `at(player, roomA)`
- `at(enemy1, roomA)`
- No `roomHasHazard` with oil

**When:**
- `theBurn(enemy1)`

**Then:**
- Planning fails (precondition not met)

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Consumes hazard | Oil is consumed after ignition |
| P2 | Requires ability | Player must have canApplyTag(player, burning) |
| P3 | Enemy gets burned | Target enemy receives burning tag |
