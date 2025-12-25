# The Slipstream

## Purpose

A tactical strategy that defeats enemies by freezing a path and sliding them into a hazard room. Uses ice physics to push enemies into danger without direct confrontation.

From PUZZLE_IDEAS.md: Uses Arcanist's Freeze ability to create slippery paths.

## Layer

strategy

## Dependencies

- `primitives/locomotion` - For entity movement
- `primitives/tags` - For applying effects

## Methods

| Method | Description |
|--------|-------------|
| `theSlipstream(?enemy)` | Main strategy: freeze path, slide enemy into hazard |
| `freezeCorridor(?corridor)` | Apply frozen tag to corridor |
| `freezeRoom(?room)` | Apply frozen tag to room |
| `pushIntoRoom(?entity, ?room)` | Slide entity into target room |
| `applyHazardEffect(?entity, ?hazard)` | Apply hazard's tag to entity |

## Operators

| Operator | Description |
|----------|-------------|
| `opApplyRoomTag(?room, ?tag)` | Add environmental tag to room |

## Required Facts

| Fact | Description |
|------|-------------|
| `at(?entity, ?room)` | Entity location |
| `roomHasHazard(?room, ?hazard)` | Room contains a hazard |
| `pathThrough(?from, ?to, ?via)` | Path between rooms through corridor |
| `connected(?from, ?to)` | Direct room connection |
| `canApplyTag(?entity, ?tag)` | Entity has ability to apply tag |
| `hazardAppliesTag(?hazard, ?tag)` | What tag a hazard applies |

## Parameters

No configurable parameters.

## Examples

### Example 1: Slide through corridor into hazard

**Given:**
- `at(enemy1, roomA)`
- `roomHasHazard(roomC, fire)`
- `pathThrough(roomA, roomC, corridor)`
- `canApplyTag(arcanist, frozen)`
- `hazardAppliesTag(fire, burning)`

**When:**
- `theSlipstream(enemy1)`

**Then:**
- Plan contains: freeze corridor, push enemy, apply effect
- Final state has: `at(enemy1, roomC)`, `hasTag(enemy1, burning)`

### Example 2: Direct push into adjacent hazard

**Given:**
- `at(enemy1, roomA)`
- `roomHasHazard(roomB, electricity)`
- `connected(roomA, roomB)`
- `canApplyTag(arcanist, frozen)`
- `hazardAppliesTag(electricity, electrified)`

**When:**
- `theSlipstream(enemy1)`

**Then:**
- Final state has: `at(enemy1, roomB)`, `hasTag(enemy1, electrified)`

### Example 3: No path to hazard

**Given:**
- `at(enemy1, roomA)`
- `roomHasHazard(roomC, fire)`
- No path from roomA to roomC

**When:**
- `theSlipstream(enemy1)`

**Then:**
- Planning fails

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Enemy relocated | Enemy ends up in hazard room |
| P2 | Hazard effect applied | Enemy receives tag from hazard |
| P3 | Requires freeze ability | Arcanist must have canApplyTag(arcanist, frozen) |
